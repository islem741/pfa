"""
apps/orchestration/tools/registry.py
Tool registry and dispatcher. Maps tool names → tool instances.
"""
import logging
from apps.orchestration.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, BaseTool] = {}


class ToolNotFoundError(Exception):
    """LLM requested a tool that isn't registered."""


class ToolLoopError(Exception):
    """Tool call loop exceeded max iterations."""


def register(tool: BaseTool) -> None:
    """Register a tool instance by its name."""
    _REGISTRY[tool.name] = tool
    logger.debug("tool_registered name=%s", tool.name)


def get_all_schemas() -> list[dict]:
    """Return OpenAI-format schemas for all registered tools."""
    return [t.to_openai_schema() for t in _REGISTRY.values()]


class ToolDispatcher:
    MAX_ITERATIONS = 5  # prevent infinite tool call loops

    def dispatch(self, tool_name: str, arguments: dict, iteration: int) -> ToolResult:
        """
        Execute a tool by name with the given arguments.
        Rejects unknown tool names (LLM can hallucinate tool names).
        Wraps ALL exceptions — tool errors are ToolResult, never raised.
        """
        if iteration > self.MAX_ITERATIONS:
            raise ToolLoopError(
                f"Tool call loop exceeded {self.MAX_ITERATIONS} iterations."
            )
        if tool_name not in _REGISTRY:
            raise ToolNotFoundError(
                f"LLM requested tool '{tool_name}' which is not registered. "
                f"Available: {list(_REGISTRY.keys())}"
            )
        tool = _REGISTRY[tool_name]
        try:
            return tool.execute(**arguments)
        except Exception as e:
            logger.error("tool_execution_error name=%s: %s", tool_name, e, exc_info=True)
            return ToolResult(success=False, error=str(e))
