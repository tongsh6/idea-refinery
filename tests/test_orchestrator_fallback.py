import json
import sqlite3
from pathlib import Path

from idea_refinery.config import GateConfig, RunConfig
from idea_refinery.orchestrator import run_refinery
from idea_refinery.providers.base import BaseProvider, CompletionRequest, CompletionResult
from idea_refinery.providers.registry import ProviderRegistry
from idea_refinery.store import SqliteStore


def _mock_prd(idea: str) -> dict[str, object]:
    return {
        "tldr": f"{idea}-tldr",
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


class FailingProvider(BaseProvider):
    def __init__(self) -> None:
        self.name = "fail"
        self.default_model = "fail-model"
        self.calls = 0

    async def complete(self, req: CompletionRequest) -> CompletionResult:
        self.calls += 1
        raise RuntimeError("provider failure")

    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        return 0.0


class StubProvider(BaseProvider):
    def __init__(self, idea: str) -> None:
        self.name = "stub"
        self.default_model = "stub-model"
        self.calls = 0
        self.idea = idea

    async def complete(self, req: CompletionRequest) -> CompletionResult:
        self.calls += 1
        system = req.messages[0].content
        if "expert product manager" in system:
            content = json.dumps(_mock_prd(self.idea), ensure_ascii=False)
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
            content = json.dumps(
                {
                    "updated_prd": _mock_prd(self.idea),
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


def test_orchestrator_fallback_to_second_provider(tmp_path: Path) -> None:
    idea = "fallback-test"
    fail = FailingProvider()
    stub = StubProvider(idea)
    registry = ProviderRegistry([fail, stub])
    registry.set_role_map(
        {
            "author": "fail",
            "reviewer:value": "fail",
            "editor": "fail",
        }
    )

    db_path = tmp_path / "refinery.db"
    out_dir = tmp_path / "out"
    store = SqliteStore(str(db_path))
    config = RunConfig(
        idea=idea,
        reviewer_hats=["value"],
        gate=GateConfig(max_rounds=2, budget_usd=5.0),
        output_dir=str(out_dir),
        dry_run=False,
    )

    output_path = run_refinery(config=config, registry=registry, store=store)
    store.close()

    assert Path(output_path).exists()
    assert fail.calls >= 3
    assert stub.calls >= 3

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM rounds")
    rounds = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM artifacts")
    artifacts = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM decisions")
    decisions = cur.fetchone()[0]
    conn.close()

    assert rounds == 3
    assert artifacts == 1
    assert decisions == 1
