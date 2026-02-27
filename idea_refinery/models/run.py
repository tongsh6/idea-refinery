"""Run, Round, Decision domain models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


def _uid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


RunStatus = Literal[
    "pending",
    "running",
    "done",
    "failed",
    "stopped",
]

StopReason = Literal[
    "pass_gate",
    "converged",
    "max_rounds",
    "budget_exceeded",
    "timeout",
    "manual_stop",
    "error",
]


class Run(BaseModel):
    """Top-level run record."""

    id: str = Field(default_factory=_uid)
    idea: str
    config_json: str = ""  # Serialized RunConfig
    status: RunStatus = "pending"
    cost_usd: float = 0.0
    total_rounds: int = 0
    stop_reason: StopReason | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Round(BaseModel):
    """Single LLM invocation within a run."""

    id: str = Field(default_factory=_uid)
    run_id: str
    step: str  # e.g. "draft", "review", "edit"
    role: str  # e.g. "author", "reviewer:risk", "editor"
    provider_name: str
    model: str
    prompt_hash: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    raw_output: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_now)


class Decision(BaseModel):
    """Gate decision for a loop iteration."""

    id: str = Field(default_factory=_uid)
    run_id: str
    round_number: int
    decision: Literal["PASS", "FAIL", "STOP"]
    stop_reason: StopReason | None = None
    avg_score: float | None = None
    blocking_count: int = 0
    reason: str = ""
    created_at: datetime = Field(default_factory=_now)
