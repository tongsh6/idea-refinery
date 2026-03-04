from pathlib import Path

from idea_refinery.models import Artifact, CR, Decision, Review, ReviewScores, Round, Run, RunEvent
from idea_refinery.store import SqliteStore


def test_store_read_apis_roundtrip(tmp_path: Path) -> None:
    db_path = tmp_path / "refinery.db"
    store = SqliteStore(str(db_path))

    run = Run(idea="store test", config_json="{}", status="running")
    store.insert_run(run)

    rnd = Round(
        run_id=run.id,
        step="draft",
        role="author",
        provider_name="stub",
        model="stub-model",
        input_tokens=12,
        output_tokens=34,
        cost_usd=0.01,
        latency_ms=2,
        raw_output='{"ok":true}',
        metadata={"attempt_count": 1, "fallback_used": False},
    )
    store.insert_round(rnd)

    art1 = Artifact(
        run_id=run.id,
        artifact_type="PRD",
        version=1,
        content={"tldr": "v1"},
        raw_text="# v1",
    )
    store.insert_artifact(art1)

    art2 = Artifact(
        run_id=run.id,
        artifact_type="PRD",
        version=2,
        content={"tldr": "v2"},
        raw_text="# v2",
        previous_artifact_id=art1.id,
        diff_summary="upgrade",
    )
    store.insert_artifact(art2)

    cr = CR(
        artifact_id=art2.id,
        round_id=rnd.id,
        problem="missing acceptance",
        rationale="cannot verify",
        change="add measurable acceptance",
        acceptance="ac exists",
        severity="major",
        dimension="clarity",
    )
    review = Review(
        round_id=rnd.id,
        artifact_id=art2.id,
        hat="value",
        verdict="PASS",
        scores=ReviewScores(value=9, feasibility=8, risk=8, execution=8, clarity=9),
        blocking_count=0,
        crs=[cr],
        summary="ok",
    )
    store.insert_review(review)
    store.insert_cr(cr)

    decision = Decision(
        run_id=run.id,
        round_number=1,
        decision="PASS",
        stop_reason="pass_gate",
        avg_score=8.5,
        blocking_count=0,
        reason="pass",
    )
    store.insert_decision(decision)

    event = RunEvent(
        run_id=run.id,
        step="gate",
        event_type="gate_decision",
        round_number=1,
        detail="pass",
        payload={"decision": "PASS", "avg_score": 8.5},
    )
    store.insert_run_event(event)

    got_run = store.get_run(run.id)
    assert got_run is not None
    assert got_run.id == run.id

    got_round = store.get_round(rnd.id)
    assert got_round is not None
    assert got_round.metadata["attempt_count"] == 1

    got_art = store.get_artifact(art2.id)
    assert got_art is not None
    assert got_art.previous_artifact_id == art1.id

    latest = store.get_latest_artifact(run.id, "PRD")
    assert latest is not None
    assert latest.id == art2.id

    rounds = store.list_rounds(run.id)
    assert len(rounds) == 1

    artifacts = store.list_artifacts(run.id, artifact_type="PRD")
    assert [a.id for a in artifacts] == [art1.id, art2.id]

    chain = store.list_artifact_chain(art2.id)
    assert [a.id for a in chain] == [art1.id, art2.id]

    reviews = store.list_reviews(run.id)
    assert len(reviews) == 1
    assert reviews[0].scores.average > 0

    crs = store.list_crs(run.id)
    assert len(crs) == 1
    assert crs[0].problem == "missing acceptance"

    decisions = store.list_decisions(run.id)
    assert len(decisions) == 1
    assert decisions[0].decision == "PASS"

    events = store.list_run_events(run.id)
    assert len(events) == 1
    assert events[0].event_type == "gate_decision"
    assert events[0].payload["decision"] == "PASS"

    store.close()
