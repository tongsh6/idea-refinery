"""Runtime configuration for a Refinery run."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Single provider / model configuration."""

    name: str  # Logical name, e.g. "openai", "deepseek", "ollama-mistral"
    kind: Literal["openai_compatible", "ollama"] = "openai_compatible"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"

    # Role affinity: which orchestration roles this provider is preferred for
    roles: list[str] = Field(default_factory=list)  # empty = all roles


class RouterConfig(BaseModel):
    """Model routing strategy."""

    providers: list[ProviderConfig] = Field(default_factory=list)
    # Role → provider name mapping (overrides affinity)
    role_map: dict[str, str] = Field(default_factory=dict)


class GateConfig(BaseModel):
    """Gate / stop criteria."""

    min_avg_score: float = 8.0
    max_blocking: int = 0  # blocking CRs remaining to PASS
    convergence_rounds: int = 2  # consecutive rounds with no new Blocking → STOP
    max_rounds: int = 6
    budget_usd: float = 1.0
    timeout_seconds: int = 600


REVIEWER_HATS = ["value", "feasibility", "risk", "execution", "devil"]


class RunConfig(BaseModel):
    """Full configuration for one Refinery run."""

    idea: str
    artifact_types: list[Literal["PRD", "TECH_SPEC", "EXEC_PLAN"]] = Field(
        default=["PRD"]
    )
    router: RouterConfig = Field(default_factory=RouterConfig)
    gate: GateConfig = Field(default_factory=GateConfig)
    output_dir: str = "./out"
    reviewer_hats: list[str] = Field(default_factory=lambda: list(REVIEWER_HATS))
    dry_run: bool = False  # If True, no actual LLM calls; use mock responses
