"""
apps/gateway/providers/base.py
Abstract base class and shared data structures for all LLM providers.
Student 1 owns this file — do NOT modify without coordinating with them.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class Message:
    role: str           # "system", "user", "assistant", "tool"
    content: str
    tool_call_id: str | None = None
    tool_calls: list | None = None


@dataclass
class LLMConfig:
    model: str
    max_tokens: int = 1024
    temperature: float = 0.7
    timeout_seconds: int = 30
    stream: bool = False


@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int

    @property
    def total(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class LLMResponse:
    content: str
    usage: TokenUsage
    model: str
    provider: str
    tool_calls: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)


class AbstractLLMProvider(ABC):

    @abstractmethod
    def complete(self, messages: list[Message], config: LLMConfig) -> LLMResponse:
        """Send messages and return a complete response."""
        ...

    @abstractmethod
    def stream(self, messages: list[Message], config: LLMConfig) -> Iterator[str]:
        """Yield response tokens one by one."""
        ...

    @abstractmethod
    def count_tokens(self, messages: list[Message], model: str) -> int:
        """Count tokens without calling the API."""
        ...
