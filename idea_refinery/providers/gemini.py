from __future__ import annotations

import time

import aiohttp

from .base import BaseProvider, CompletionRequest, CompletionResult

_PRICE_TABLE: dict[str, tuple[float, float]] = {
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-1.5-flash": (0.075, 0.30),
    "gemini-1.5-pro": (1.25, 5.00),
}


class GeminiProvider(BaseProvider):
    def __init__(
        self,
        name: str = "gemini",
        base_url: str = "https://generativelanguage.googleapis.com",
        api_key: str = "",
        default_model: str = "gemini-2.0-flash",
    ):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_model = default_model

    async def complete(self, req: CompletionRequest) -> CompletionResult:
        if not self.api_key:
            raise RuntimeError("Gemini API key is missing")

        model = req.model or self.default_model
        system_text = "\n\n".join(m.content for m in req.messages if m.role == "system")
        contents: list[dict[str, object]] = []
        for message in req.messages:
            if message.role == "system":
                continue
            role = "model" if message.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message.content}]})

        payload: dict[str, object] = {
            "contents": contents,
            "generationConfig": {
                "temperature": req.temperature,
                "maxOutputTokens": req.max_tokens,
            },
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}

        url = f"{self.base_url}/v1beta/models/{model}:generateContent?key={self.api_key}"
        t0 = time.monotonic()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=900),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        latency_ms = int((time.monotonic() - t0) * 1000)

        candidates = data.get("candidates", [])
        parts: list[object] = []
        if candidates and isinstance(candidates[0], dict):
            candidate = candidates[0]
            content = candidate.get("content", {})
            if isinstance(content, dict):
                content_parts = content.get("parts", [])
                if isinstance(content_parts, list):
                    parts = content_parts

        texts: list[str] = []
        for part in parts:
            if isinstance(part, dict):
                text = part.get("text")
                if isinstance(text, str):
                    texts.append(text)
        result_text = "\n".join(texts)

        usage = data.get("usageMetadata", {})
        input_tokens = int(usage.get("promptTokenCount", 0)) if isinstance(usage, dict) else 0
        output_tokens = (
            int(usage.get("candidatesTokenCount", 0)) if isinstance(usage, dict) else 0
        )

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
        return (input_tokens * 0.10 + output_tokens * 0.40) / 1_000_000
