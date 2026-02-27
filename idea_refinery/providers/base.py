"""Base provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class CompletionRequest:
    messages: list[Message]
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    response_format: dict[str, Any] | None = None  # e.g. {"type": "json_object"}
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletionResult:
    content: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    model: str
    provider: str
    raw: Any = None  # Raw API response for debugging


class BaseProvider(ABC):
    """Abstract LLM provider."""

    name: str

    @abstractmethod
    async def complete(self, req: CompletionRequest) -> CompletionResult:
        """Execute a chat completion."""
        ...

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate cost in USD."""
        ...
