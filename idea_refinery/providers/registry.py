"""Provider registry — resolves role → provider."""

from __future__ import annotations

from dataclasses import dataclass

from .base import BaseProvider
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai_compat import OpenAICompatibleProvider


@dataclass
class OpenAIProviderSpec:
    name: str
    base_url: str
    api_key: str
    model: str


class ProviderRegistry:
    """Holds all configured providers and routes roles to them."""

    def __init__(self, providers: list[BaseProvider]):
        names = [p.name for p in providers]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate provider names are not allowed")
        self._providers: dict[str, BaseProvider] = {p.name: p for p in providers}
        self._role_map: dict[str, str] = {}  # role → provider name

    def set_role_map(self, role_map: dict[str, str]) -> None:
        self._role_map = role_map

    def get(self, name: str) -> BaseProvider:
        if name not in self._providers:
            raise KeyError(f"Provider '{name}' not found in registry")
        return self._providers[name]

    def resolve(self, role: str) -> BaseProvider:
        """Return the best provider for a given role."""
        candidates = self.resolve_candidates(role)
        if candidates:
            return candidates[0]
        raise RuntimeError("No providers configured")

    def resolve_candidates(self, role: str) -> list[BaseProvider]:
        providers = list(self._providers.values())
        preferred_name = self._role_map.get(role)
        if not preferred_name:
            return providers

        preferred = self._providers.get(preferred_name)
        if preferred is None:
            return providers

        return [preferred] + [p for p in providers if p.name != preferred_name]

    def all(self) -> list[BaseProvider]:
        return list(self._providers.values())


def build_registry(
    openai_api_key: str = "",
    openai_base_url: str = "https://api.openai.com/v1",
    openai_model: str = "gpt-4o-mini",
    ollama_base_url: str = "http://localhost:11434",
    ollama_model: str = "qwen3:30b",
    gemini_api_key: str = "",
    gemini_base_url: str = "https://generativelanguage.googleapis.com",
    gemini_model: str = "gemini-2.0-flash",
    claude_api_key: str = "",
    claude_base_url: str = "https://api.anthropic.com",
    claude_model: str = "claude-3-5-sonnet-latest",
    openai_compat_specs: list[OpenAIProviderSpec] | None = None,
    include_ollama: bool = False,
    include_gemini: bool = False,
    include_claude: bool = False,
) -> ProviderRegistry:
    """Build a default ProviderRegistry from simple parameters."""
    providers: list[BaseProvider] = []

    if openai_api_key:
        providers.append(
            OpenAICompatibleProvider(
                name="openai",
                base_url=openai_base_url,
                api_key=openai_api_key,
                default_model=openai_model,
            )
        )

    if openai_compat_specs:
        for spec in openai_compat_specs:
            if not spec.api_key:
                raise RuntimeError(f"Missing api_key for provider '{spec.name}'")
            providers.append(
                OpenAICompatibleProvider(
                    name=spec.name,
                    base_url=spec.base_url,
                    api_key=spec.api_key,
                    default_model=spec.model,
                )
            )

    if include_ollama:
        providers.append(
            OllamaProvider(name="ollama", base_url=ollama_base_url, default_model=ollama_model)
        )

    if include_gemini:
        if not gemini_api_key:
            raise RuntimeError("Missing GEMINI_API_KEY for Gemini provider")
        providers.append(
            GeminiProvider(
                name="gemini",
                base_url=gemini_base_url,
                api_key=gemini_api_key,
                default_model=gemini_model,
            )
        )

    if include_claude:
        if not claude_api_key:
            raise RuntimeError("Missing CLAUDE_API_KEY for Claude provider")
        providers.append(
            ClaudeProvider(
                name="claude",
                base_url=claude_base_url,
                api_key=claude_api_key,
                default_model=claude_model,
            )
        )

    if not providers:
        raise RuntimeError(
            "No providers configured. Set OPENAI_API_KEY, GEMINI_API_KEY, CLAUDE_API_KEY, or enable Ollama."
        )

    return ProviderRegistry(providers)
