"""OpenAI-compatible provider (covers OpenAI, DeepSeek, vLLM, custom gateways)."""

from __future__ import annotations

import time
from typing import Any

from openai import AsyncOpenAI

from .base import BaseProvider, CompletionRequest, CompletionResult

# Rough pricing table (USD per 1M tokens). Extend as needed.
_PRICE_TABLE: dict[str, tuple[float, float]] = {
    # model_prefix: (input_per_1m, output_per_1m)
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (5.00, 15.00),
    "gpt-4-turbo": (10.00, 30.00),
    "gpt-3.5-turbo": (0.50, 1.50),
    "deepseek-chat": (0.07, 0.14),
    "deepseek-reasoner": (0.55, 2.19),
}


class OpenAICompatibleProvider(BaseProvider):
    """
    Works with any OpenAI-compatible endpoint:
    - OpenAI (api.openai.com)
    - DeepSeek (api.deepseek.com)
    - vLLM / TGI self-hosted
    - Custom LLM gateways
    """

    def __init__(self, name: str, base_url: str, api_key: str, default_model: str):
        self.name = name
        self.default_model = default_model
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key or "none")

    async def complete(self, req: CompletionRequest) -> CompletionResult:
        model = req.model or self.default_model
        messages: list[dict[str, Any]] = [
            {"role": m.role, "content": m.content} for m in req.messages
        ]

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
        }
        if req.response_format:
            kwargs["response_format"] = req.response_format

        t0 = time.monotonic()
        resp = await self._client.chat.completions.create(**kwargs)
        latency_ms = int((time.monotonic() - t0) * 1000)

        usage = resp.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        content = resp.choices[0].message.content or ""

        return CompletionResult(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self.estimate_cost(input_tokens, output_tokens, model),
            latency_ms=latency_ms,
            model=model,
            provider=self.name,
            raw=resp,
        )

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        for prefix, (in_price, out_price) in _PRICE_TABLE.items():
            if model.startswith(prefix):
                return (input_tokens * in_price + output_tokens * out_price) / 1_000_000
        # Fallback: assume gpt-4o-mini pricing
        return (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
