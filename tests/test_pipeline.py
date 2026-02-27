import sqlite3
from pathlib import Path

from idea_refinery.config import GateConfig, RunConfig
from idea_refinery.orchestrator import run_full_pipeline
from idea_refinery.providers import build_registry
from idea_refinery.store import SqliteStore


def test_run_full_pipeline_dry_run_outputs_three_artifacts(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    db_path = tmp_path / "refinery.db"

    registry = build_registry(include_ollama=True)
    store = SqliteStore(str(db_path))
    config = RunConfig(
        idea="pipeline dry-run",
        gate=GateConfig(max_rounds=2, budget_usd=3.0),
        output_dir=str(out_dir),
        dry_run=True,
    )

    outputs = run_full_pipeline(config=config, registry=registry, store=store)
    store.close()

    assert set(outputs.keys()) == {"PRD", "TECH_SPEC", "EXEC_PLAN"}
    assert Path(outputs["PRD"]).exists()
    assert Path(outputs["TECH_SPEC"]).exists()
    assert Path(outputs["EXEC_PLAN"]).exists()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    _ = cur.execute("SELECT COUNT(*) FROM artifacts")
    artifacts = cur.fetchone()[0]
    _ = cur.execute("SELECT COUNT(*) FROM decisions")
    decisions = cur.fetchone()[0]
    _ = cur.execute("SELECT COUNT(*) FROM runs")
    runs = cur.fetchone()[0]
    conn.close()

    assert artifacts == 3
    assert decisions == 3
    assert runs == 3
