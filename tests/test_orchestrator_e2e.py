import json
import sqlite3
from pathlib import Path

from idea_refinery.config import GateConfig, RunConfig
from idea_refinery.orchestrator import run_full_pipeline
from idea_refinery.providers.registry import ProviderRegistry
from idea_refinery.providers.base import BaseProvider, CompletionRequest, CompletionResult
from idea_refinery.store import SqliteStore


def _prd(idea: str) -> dict[str, object]:
    return {
        "tldr": f"{idea}-prd",
        "problem_statement": "problem",
        "target_users": ["u1"],
        "goals": ["g1"],
        "non_goals": ["ng1"],
        "user_stories": [],
        "functional_requirements": [],
        "acceptance_criteria": ["ac1"],
        "milestones": [],
        "risks": [],
        "open_questions": ["oq1"],
        "version": "0.1",
    }


def _tech(idea: str) -> dict[str, object]:
    return {
        "overview": f"{idea}-tech",
        "architecture": "layered",
        "components": ["orchestrator"],
        "api_contracts": ["run"],
        "data_model": ["run"],
        "non_functional_requirements": ["stable"],
        "risks": ["none"],
        "milestones": ["m1"],
        "open_questions": ["oq"],
        "version": "0.1",
    }


def _plan(idea: str) -> dict[str, object]:
    return {
        "objective": f"{idea}-plan",
        "scope": ["s1"],
        "milestones": ["m1"],
        "tasks": ["t1"],
        "owners": ["o1"],
        "timeline": ["week1"],
        "dependencies": ["d1"],
        "risks": ["r1"],
        "acceptance_criteria": ["ac1"],
        "version": "0.1",
    }


class SingleProvider(BaseProvider):
    def __init__(self, idea: str) -> None:
        self.name = "stub"
        self.default_model = "stub-model"
        self.idea = idea

    async def complete(self, req: CompletionRequest) -> CompletionResult:
        system = req.messages[0].content
        user = req.messages[1].content
        if "expert product manager" in system:
            payload: dict[str, object] = _prd(self.idea)
            content = json.dumps(payload, ensure_ascii=False)
        elif "senior software architect" in system:
            payload = _tech(self.idea)
            content = json.dumps(payload, ensure_ascii=False)
        elif "delivery manager" in system:
            payload = _plan(self.idea)
            content = json.dumps(payload, ensure_ascii=False)
        elif "structured PRD review" in system:
            content = json.dumps(
                {
                    "hat": "value",
                    "verdict": "PASS",
                    "scores": {
                        "value": 9,
                        "feasibility": 9,
                        "risk": 9,
                        "execution": 9,
                        "clarity": 9,
                    },
                    "summary": "ok",
                    "crs": [],
                },
                ensure_ascii=False,
            )
        elif "senior editor" in system:
            if "TECH_SPEC" in user:
                updated = _tech(self.idea)
            elif "EXEC_PLAN" in user:
                updated = _plan(self.idea)
            else:
                updated = _prd(self.idea)
            content = json.dumps(
                {
                    "updated_artifact": updated,
                    "changelog": "no-op",
                    "cr_resolutions": [],
                },
                ensure_ascii=False,
            )
        else:
            raise RuntimeError("unexpected role")

        return CompletionResult(
            content=content,
            input_tokens=10,
            output_tokens=10,
            cost_usd=0.01,
            latency_ms=1,
            model=self.default_model,
            provider=self.name,
        )

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        return 0.01


def test_run_full_pipeline_non_dry_run_with_stub_provider(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    db_path = tmp_path / "refinery.db"

    provider = SingleProvider("pipeline-e2e")
    registry = ProviderRegistry([provider])
    store = SqliteStore(str(db_path))
    config = RunConfig(
        idea="pipeline-e2e",
        reviewer_hats=["value"],
        gate=GateConfig(max_rounds=2, budget_usd=5.0),
        output_dir=str(out_dir),
        dry_run=False,
    )

    outputs = run_full_pipeline(config=config, registry=registry, store=store)
    store.close()

    assert set(outputs.keys()) == {"PRD", "TECH_SPEC", "EXEC_PLAN"}
    assert Path(outputs["PRD"]).exists()
    assert Path(outputs["TECH_SPEC"]).exists()
    assert Path(outputs["EXEC_PLAN"]).exists()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM runs")
    runs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM rounds")
    rounds = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM artifacts")
    artifacts = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM decisions")
    decisions = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM run_events")
    run_events = cur.fetchone()[0]
    cur.execute("SELECT event_type FROM run_events")
    event_type_rows = cur.fetchall()
    cur.execute("SELECT metadata_json FROM rounds")
    metadata_rows = cur.fetchall()
    conn.close()

    assert runs == 3
    assert rounds == 9
    assert artifacts == 3
    assert decisions == 3
    assert run_events > 0
    assert len(metadata_rows) == 9

    event_types = {row[0] for row in event_type_rows}
    assert "run_started" in event_types
    assert "gate_decision" in event_types
    assert "run_completed" in event_types

    for row in metadata_rows:
        metadata = json.loads(row[0])
        assert metadata["fallback_used"] is False
        assert metadata["attempt_count"] == 1
