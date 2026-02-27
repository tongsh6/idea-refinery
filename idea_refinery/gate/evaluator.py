from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GateDecision:
    decision: str
    reason: str
    stop_reason: str | None
    avg_score: float
    blocking_count: int


def evaluate_gate(
    *,
    avg_score: float,
    blocking_count: int,
    round_number: int,
    max_rounds: int,
    min_avg_score: float,
    max_blocking: int,
    budget_usd: float,
    total_cost_usd: float,
    timed_out: bool,
) -> GateDecision:
    if timed_out:
        return GateDecision("STOP", "timeout reached", "timeout", avg_score, blocking_count)
    if total_cost_usd >= budget_usd:
        return GateDecision("STOP", "budget exceeded", "budget_exceeded", avg_score, blocking_count)
    if round_number >= max_rounds:
        return GateDecision("STOP", "max rounds reached", "max_rounds", avg_score, blocking_count)
    if blocking_count <= max_blocking and avg_score >= min_avg_score:
        return GateDecision("PASS", "gate passed", "pass_gate", avg_score, blocking_count)
    return GateDecision("FAIL", "gate failed", None, avg_score, blocking_count)
