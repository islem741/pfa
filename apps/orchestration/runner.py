"""
apps/orchestration/runner.py
WorkflowRunner — the orchestration core.

This is the boundary between deterministic and generative logic.
Every step BEFORE gateway.complete() is deterministic.
Everything AFTER is generative and must be validated.
"""
import json
import logging
import time
import uuid
from dataclasses import dataclass, field

from django.contrib.auth.models import User

from apps.gateway.gateway import LLMGateway
from apps.gateway.providers.base import Message, LLMConfig
from apps.prompts.registry import PromptRegistry, PromptNotFoundError
from apps.prompts.budget import ContextBudgetManager, ContextBudgetExceeded
from apps.prompts.engine import TemplateEngine, PromptRenderError
from apps.orchestration.tools.registry import ToolDispatcher, ToolLoopError

# Trigger tool auto-registration by importing them
import apps.orchestration.tools.calculator   # noqa
import apps.orchestration.tools.search       # noqa
import apps.orchestration.tools.fetch        # noqa

logger = logging.getLogger(__name__)


class InputBlockedError(Exception):
    """Raised when the input guardrail blocks the query."""
    def __init__(self, reason: str, guard_name: str = ""):
        self.reason = reason
        self.guard_name = guard_name
        super().__init__(reason)


@dataclass
class WorkflowResult:
    answer: str
    request_id: str
    fallback_used: bool
    truncation_applied: bool
    turns_removed: int
    tool_calls_made: list[str]
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    confidence: float | None
    provider_used: str
    session_id: str = ""


class WorkflowRunner:
    """
    Drives a single user query through the full LLM pipeline.

    Step diagram:
      INPUT GUARD → PROMPT BUILD → CONTEXT BUDGET →
      LLM CALL (with tool dispatch loop) → OUTPUT GUARD → AUDIT LOG

    The boundary between deterministic and generative logic is
    explicitly marked with comments below.
    """

    MAX_TOOL_ITERATIONS = 5

    def __init__(self, workflow_name: str = "default"):
        from apps.orchestration.workflow import WORKFLOWS
        self._workflow = WORKFLOWS.get(workflow_name, WORKFLOWS["default"])
        self._gateway  = LLMGateway()
        self._registry = PromptRegistry()
        self._budget   = ContextBudgetManager()
        self._engine   = TemplateEngine()
        self._dispatcher = ToolDispatcher()

    def run(
        self,
        query: str,
        user: User | None = None,
        session_id: str | None = None,
    ) -> WorkflowResult:
        start_time    = time.monotonic()
        request_id    = str(uuid.uuid4())
        tool_calls_made: list[str] = []

        # ── DETERMINISTIC ZONE ─────────────────────────────────────────────
        # Everything here is deterministic: same input → same output.
        # No LLM calls. No randomness.

        # Step 1: Input guard — block injection, PII, empty queries
        from apps.guardrails.pipeline import GuardrailPipeline
        guard_result = GuardrailPipeline().check_input(query)
        if not guard_result.passed:
            self._log_blocked_request(
                request_id=request_id,
                query=query,
                user=user,
                reason=guard_result.reason,
                guard_name=guard_result.guard_name,
            )
            raise InputBlockedError(guard_result.reason, guard_result.guard_name)

        # Step 2: Load active prompt template from registry (Redis cache → DB)
        try:
            prompt_version = self._registry.get_active(
                self._workflow.prompt_template_name
            )
        except PromptNotFoundError:
            logger.warning(
                "prompt_not_found name=%s — using fallback system prompt",
                self._workflow.prompt_template_name,
            )
            # Fallback: use a hardcoded system prompt so we don't crash
            from apps.prompts.models import PromptVersion, PromptTemplate
            fallback_template, _ = PromptTemplate.objects.get_or_create(
                name=self._workflow.prompt_template_name,
                defaults={"description": "Auto-created fallback"},
            )
            prompt_version = PromptVersion(
                template=fallback_template,
                version_number=0,
                template_body=(
                    "You are a helpful research assistant. "
                    "Answer the user's question based on the provided context. "
                    "If the context does not contain the answer, say so clearly.\n\n"
                    "Context:\n{{ context }}\n\n"
                    "Respond ONLY in valid JSON with this exact structure:\n"
                    '{"answer": "...", "confidence": 0.0-1.0, "sources": ["..."]}'
                ),
                role="system",
                token_budget=self._workflow.token_budget,
                is_active=False,
            )

        # Step 3: Render the system prompt with Jinja2
        try:
            system_text = self._engine.render(
                prompt_version.template_body,
                {"user_query": query, "context": ""},
            )
        except PromptRenderError as e:
            logger.error("prompt_render_error: %s", e)
            system_text = f"You are a helpful assistant. Answer: {query}"

        # Step 4: Build the initial messages list
        messages = [
            Message(role="system", content=system_text),
            Message(role="user",   content=query),
        ]

        # Step 5: Enforce context budget (truncate history if needed)
        budget = getattr(prompt_version, 'token_budget', self._workflow.token_budget)
        try:
            budget_result = self._budget.fit(messages, budget=budget)
            messages = budget_result.messages
        except ContextBudgetExceeded as e:
            logger.error("context_budget_exceeded: %s", e)
            # Fall back to just system + user with truncated query
            budget_result_truncation = False
            budget_result_turns = 0
            class _BudgetFallback:
                truncation_applied = False
                turns_removed = 0
            budget_result = _BudgetFallback()

        config = LLMConfig(
            model=self._workflow.prompt_template_name and "gpt-4o-mini" or "gpt-4o-mini",
            max_tokens=1024,
        )

        # ── GENERATIVE ZONE ────────────────────────────────────────────────
        # From here, outputs are non-deterministic.
        # Every output MUST be validated before being trusted.

        iteration   = 0
        llm_response = None

        while iteration < self.MAX_TOOL_ITERATIONS:
            iteration += 1
            llm_response = self._gateway.complete(messages, config, query=query)

            # If no tool calls → LLM produced its final answer
            if not llm_response.tool_calls:
                break

            # Dispatch each tool call the LLM requested
            for tc in llm_response.tool_calls:
                tool_name = tc.function.name if hasattr(tc, 'function') else tc.get('name', '')
                arguments = (
                    tc.function.arguments
                    if hasattr(tc, 'function')
                    else tc.get('arguments', {})
                )
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                # Only dispatch tools allowed by this workflow
                if tool_name not in self._workflow.allowed_tools:
                    logger.warning("tool_not_allowed name=%s workflow=%s", tool_name, self._workflow.name)
                    tool_content = f"Error: tool '{tool_name}' is not allowed in this workflow."
                else:
                    try:
                        tool_result = self._dispatcher.dispatch(tool_name, arguments, iteration)
                        tool_calls_made.append(tool_name)
                        tool_content = (
                            json.dumps(tool_result.data)
                            if tool_result.success
                            else f"Error: {tool_result.error}"
                        )
                    except ToolLoopError as e:
                        logger.error("tool_loop_error: %s", e)
                        break

                # Feed result back to the LLM for the next pass
                tool_call_id = (
                    tc.id if hasattr(tc, 'id')
                    else tc.get('id', f"call_{tool_name}_{iteration}")
                )
                messages.append(Message(
                    role="tool",
                    content=tool_content,
                    tool_call_id=tool_call_id,
                ))
        else:
            logger.warning("max_tool_iterations_reached query=%s", query[:50])

        # ── DETERMINISTIC ZONE (RESUMED) ───────────────────────────────────
        # LLM output is back on the deterministic side — validate and audit.

        # Step 6: Output guard — parse and validate JSON schema
        answer_text = llm_response.content if llm_response else "No answer generated."
        confidence  = None

        from apps.guardrails.output_guards import OutputGuard, OutputParseError
        try:
            validated = OutputGuard().validate(answer_text)
            answer_text = validated.answer
            confidence  = validated.confidence
            if validated.disclaimer:
                answer_text = f"{answer_text}\n\n{validated.disclaimer}"
        except OutputParseError:
            # LLM didn't return valid JSON — use raw text as answer
            logger.warning("output_parse_failed — using raw LLM text")

        # Step 7: Calculate cost
        from apps.instrumentation.cost import CostCalculator
        provider = llm_response.provider if llm_response else "none"
        model    = llm_response.model    if llm_response else "none"
        cost_usd = CostCalculator().calculate(
            provider,
            model,
            llm_response.usage.input_tokens  if llm_response else 0,
            llm_response.usage.output_tokens if llm_response else 0,
        )

        latency_ms = int((time.monotonic() - start_time) * 1000)

        # Step 8: Persist audit log
        self._log_completed_request(
            request_id      = request_id,
            query           = query,
            user            = user,
            answer          = answer_text,
            prompt_version  = prompt_version,
            llm_response    = llm_response,
            tool_calls_made = tool_calls_made,
            cost_usd        = cost_usd,
            latency_ms      = latency_ms,
            truncation_applied = budget_result.truncation_applied,
            turns_removed      = budget_result.turns_removed,
        )

        return WorkflowResult(
            answer              = answer_text,
            request_id          = request_id,
            fallback_used       = (provider == "degraded"),
            truncation_applied  = budget_result.truncation_applied,
            turns_removed       = budget_result.turns_removed,
            tool_calls_made     = tool_calls_made,
            input_tokens        = llm_response.usage.input_tokens  if llm_response else 0,
            output_tokens       = llm_response.usage.output_tokens if llm_response else 0,
            cost_usd            = cost_usd,
            latency_ms          = latency_ms,
            confidence          = confidence,
            provider_used       = provider,
            session_id          = session_id or "",
        )

    # ── Private helpers ───────────────────────────────────────────────────

    def _log_blocked_request(self, request_id, query, user, reason, guard_name):
        try:
            from apps.instrumentation.models import LLMRequestLog
            LLMRequestLog.objects.create(
                id                 = request_id,
                user               = user,
                status             = "BLOCKED",
                raw_query          = query,
                input_blocked      = True,
                input_block_reason = reason,
            )
        except Exception as e:
            logger.error("log_blocked_request_failed: %s", e)

    def _log_completed_request(
        self, request_id, query, user, answer, prompt_version,
        llm_response, tool_calls_made, cost_usd, latency_ms,
        truncation_applied, turns_removed,
    ):
        try:
            from apps.instrumentation.models import LLMRequestLog, ToolCallLog
            log = LLMRequestLog.objects.create(
                id                    = request_id,
                user                  = user,
                status                = "COMPLETED" if llm_response else "FAILED",
                prompt_template_name  = getattr(prompt_version, 'template', None) and
                                        prompt_version.template.name or "",
                prompt_version_number = getattr(prompt_version, 'version_number', 0),
                raw_query             = query,
                raw_response          = llm_response.content if llm_response else "",
                provider              = llm_response.provider if llm_response else "none",
                model                 = llm_response.model    if llm_response else "none",
                fallback_used         = (llm_response.provider == "degraded") if llm_response else True,
                input_tokens          = llm_response.usage.input_tokens  if llm_response else 0,
                output_tokens         = llm_response.usage.output_tokens if llm_response else 0,
                cost_usd              = cost_usd,
                latency_ms            = latency_ms,
                truncation_applied    = truncation_applied,
                turns_removed         = turns_removed,
            )
            # Log each tool call
            for tool_name in tool_calls_made:
                ToolCallLog.objects.create(
                    request   = log,
                    tool_name = tool_name,
                    arguments = {},
                    success   = True,
                )
        except Exception as e:
            logger.error("log_completed_request_failed: %s", e)
