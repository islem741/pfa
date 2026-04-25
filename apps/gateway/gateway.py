"""
apps/gateway/gateway.py
Main LLM Gateway — single entry point for all LLM calls.

STATUS: STUB — works without real API keys using MockProvider.
When Student 1 delivers the real providers, replace MockProvider with
OpenAIProvider + AnthropicProvider (one import change).
"""
import json
import logging
from django.conf import settings
from apps.gateway.providers.base import Message, LLMConfig, LLMResponse, TokenUsage

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────
# STUB PROVIDER — remove when Student 1 delivers real code
# ─────────────────────────────────────────────────────────
class MockProvider:
    """
    Simulates an LLM response without making any API calls.
    Produces a valid KnowledgeAnswer JSON so the full pipeline can run.
    Replace this with OpenAIProvider once S1's code arrives.
    """
    def complete(self, messages: list[Message], config: LLMConfig) -> LLMResponse:
        user_msg = next((m.content for m in reversed(messages) if m.role == "user"), "")
        # Simulate a structured JSON answer (matches KnowledgeAnswer schema)
        answer_text = f"This is a mock answer to: {user_msg[:80]}"
        mock_json = json.dumps({
            "answer": answer_text,
            "confidence": 0.85,
            "sources": ["mock_source_1"],
        })
        return LLMResponse(
            content=mock_json,
            usage=TokenUsage(input_tokens=50, output_tokens=30),
            model=config.model,
            provider="mock",
            tool_calls=[],
            raw={},
        )

    def stream(self, messages, config):
        words = "This is a streaming mock response.".split()
        for word in words:
            yield word + " "

    def count_tokens(self, messages, model):
        return sum(len(m.content.split()) for m in messages)
# ─────────────────────────────────────────────────────────


class LLMGateway:
    """
    Public interface for all LLM calls.

    Usage:
        gateway = LLMGateway()
        response = gateway.complete(messages, config, query="user query text")

    SWAP POINT: When Student 1 delivers providers, change _provider to:
        from apps.gateway.providers.openai import OpenAIProvider
        self._provider = OpenAIProvider()
    """

    def __init__(self):
        # TODO (S1): replace MockProvider with real providers + FallbackChain
        self._provider = MockProvider()

    def complete(
        self,
        messages: list[Message],
        config: LLMConfig | None = None,
        query: str = "",
    ) -> LLMResponse:
        if config is None:
            config = LLMConfig(model=getattr(settings, 'LLM_DEFAULT_MODEL', 'gpt-4o-mini'))
        logger.info("gateway_complete provider=%s model=%s", self._provider.__class__.__name__, config.model)
        return self._provider.complete(messages, config)

    def stream(self, messages: list[Message], config: LLMConfig | None = None):
        """Yield tokens for WebSocket streaming."""
        if config is None:
            config = LLMConfig(model=getattr(settings, 'LLM_DEFAULT_MODEL', 'gpt-4o-mini'), stream=True)
        yield from self._provider.stream(messages, config)
