"""Ollama provider — local model serving."""

from __future__ import annotations

import time

import aiohttp

from .base import BaseProvider, CompletionRequest, CompletionResult


class OllamaProvider(BaseProvider):
    """
    Native Ollama provider using the /api/chat endpoint.
    Free / local — cost is always 0.
    """

    def __init__(
        self,
        name: str = "ollama",
        base_url: str = "http://localhost:11434",
        default_model: str = "qwen3:30b",
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model

    async def complete(self, req: CompletionRequest) -> CompletionResult:
        model = req.model or self.default_model
        messages = [{"role": m.role, "content": m.content} for m in req.messages]

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": req.temperature,
                "num_predict": req.max_tokens,
            },
        }

        t0 = time.monotonic()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=900),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        latency_ms = int((time.monotonic() - t0) * 1000)

        content = data.get("message", {}).get("content", "")
        prompt_eval_count = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)

        return CompletionResult(
            content=content,
            input_tokens=prompt_eval_count,
            output_tokens=eval_count,
            cost_usd=0.0,  # Local — free
            latency_ms=latency_ms,
            model=model,
            provider=self.name,
            raw=data,
        )

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        return 0.0  # Local inference is free
