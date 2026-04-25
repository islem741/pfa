"""
apps/orchestration/workflow.py
Workflow definitions — each workflow controls which tools and which prompt to use.
"""
from dataclasses import dataclass, field


@dataclass
class WorkflowDefinition:
    name: str
    prompt_template_name: str           # which prompt to use from the registry
    allowed_tools: list[str]            # tool names allowed in this workflow
    max_tool_iterations: int = 5
    token_budget: int = 4096


# Predefined workflows
WORKFLOWS: dict[str, WorkflowDefinition] = {
    "default": WorkflowDefinition(
        name="default",
        prompt_template_name="knowledge_assistant",
        allowed_tools=["search_knowledge_base", "calculate", "fetch_external_data"],
    ),
    "safe": WorkflowDefinition(
        name="safe",
        prompt_template_name="knowledge_assistant",
        allowed_tools=["search_knowledge_base"],   # no external fetch
        max_tool_iterations=3,
    ),
    "math": WorkflowDefinition(
        name="math",
        prompt_template_name="knowledge_assistant",
        allowed_tools=["calculate"],
        max_tool_iterations=2,
    ),
}
