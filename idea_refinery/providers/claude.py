from __future__ import annotations

import time

import aiohttp

from .base import BaseProvider, CompletionRequest, CompletionResult

_PRICE_TABLE: dict[str, tuple[float, float]] = {
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-opus": (15.00, 75.00),
}


class ClaudeProvider(BaseProvider):
    def __init__(
        self,
        name: str = "claude",
        base_url: str = "https://api.anthropic.com",
        api_key: str = "",
        default_model: str = "claude-3-5-sonnet-latest",
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model

    async def complete(self, req: CompletionRequest) -> CompletionResult:
        if not self.api_key:
            raise RuntimeError("Claude API key is missing")

        model = req.model or self.default_model
        system_text = "\n\n".join(m.content for m in req.messages if m.role == "system")
        messages: list[dict[str, object]] = []
        for message in req.messages:
            if message.role == "system":
                continue
            role = "assistant" if message.role == "assistant" else "user"
            messages.append({"role": role, "content": [{"type": "text", "text": message.content}]})

        payload: dict[str, object] = {
            "model": model,
            "messages": messages,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
        }
        if system_text:
            payload["system"] = system_text

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        t0 = time.monotonic()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/v1/messages",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=900),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        latency_ms = int((time.monotonic() - t0) * 1000)

        content_items = data.get("content", [])
        texts: list[str] = []
        if isinstance(content_items, list):
            for item in content_items:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        texts.append(text)
        result_text = "\n".join(texts)

        usage = data.get("usage", {})
        input_tokens = int(usage.get("input_tokens", 0)) if isinstance(usage, dict) else 0
        output_tokens = int(usage.get("output_tokens", 0)) if isinstance(usage, dict) else 0

        return CompletionResult(
            content=result_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self.estimate_cost(input_tokens, output_tokens, model),
            latency_ms=latency_ms,
            model=model,
            provider=self.name,
            raw=data,
        )

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        for prefix, (in_price, out_price) in _PRICE_TABLE.items():
            if model.startswith(prefix):
                return (input_tokens * in_price + output_tokens * out_price) / 1_000_000
        return (input_tokens * 3.00 + output_tokens * 15.00) / 1_000_000
