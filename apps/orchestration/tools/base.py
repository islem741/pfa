"""
apps/orchestration/tools/base.py
Abstract base that every tool must implement.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    success: bool
    data: Any           # any JSON-serializable value
    error: str = ""     # error message if success=False


class BaseTool(ABC):
    name: str           # e.g., "search_knowledge_base"
    description: str    # shown to the LLM so it knows when to call this tool
    parameters: dict    # JSON Schema describing the tool's arguments

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool.
        NEVER raise — catch internally and return ToolResult(success=False, error=...).
        """
        ...

    def to_openai_schema(self) -> dict:
        """Convert this tool to OpenAI function-calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }
