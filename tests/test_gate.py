from idea_refinery.gate import evaluate_gate


def test_gate_pass_when_score_and_blocking_meet_threshold() -> None:
    decision = evaluate_gate(
        avg_score=8.5,
        blocking_count=0,
        round_number=1,
        max_rounds=6,
        min_avg_score=8.0,
        max_blocking=0,
        budget_usd=5.0,
        total_cost_usd=1.0,
        timed_out=False,
    )
    assert decision.decision == "PASS"
    assert decision.stop_reason == "pass_gate"


def test_gate_fails_when_blocking_exists() -> None:
    decision = evaluate_gate(
        avg_score=9.2,
        blocking_count=1,
        round_number=2,
        max_rounds=6,
        min_avg_score=8.0,
        max_blocking=0,
        budget_usd=5.0,
        total_cost_usd=1.0,
        timed_out=False,
    )
    assert decision.decision == "FAIL"
    assert decision.stop_reason is None


def test_gate_stops_when_budget_exceeded() -> None:
    decision = evaluate_gate(
        avg_score=8.5,
        blocking_count=0,
        round_number=1,
        max_rounds=6,
        min_avg_score=8.0,
        max_blocking=0,
        budget_usd=1.0,
        total_cost_usd=1.1,
        timed_out=False,
    )
    assert decision.decision == "STOP"
    assert decision.stop_reason == "budget_exceeded"
