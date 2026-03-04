from pathlib import Path

from click.testing import CliRunner

from idea_refinery.cli import main
from idea_refinery.models import Run, RunEvent
from idea_refinery.store import SqliteStore


def test_cli_run_dry_run_with_ollama_flag() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            main,
            [
                "run",
                "--idea",
                "cli smoke",
                "--dry-run",
                "--ollama",
                "--out",
                "./out",
            ],
        )
        assert result.exit_code == 0
        assert "PRD written to" in result.output
        assert "TECH_SPEC written to" in result.output
        assert "EXEC_PLAN written to" in result.output
        assert Path("out/PRD.md").exists()
        assert Path("out/TECH_SPEC.md").exists()
        assert Path("out/EXEC_PLAN.md").exists()


def test_cli_run_with_multi_openai_provider_options() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        env = {"KIMI_API_KEY": "test-key", "DB_PATH": "./test.db"}
        result = runner.invoke(
            main,
            [
                "run",
                "--idea",
                "cli multi provider",
                "--dry-run",
                "--openai-provider",
                "kimi,https://api.moonshot.cn/v1,moonshot-v1-8k,KIMI_API_KEY",
                "--role-provider",
                "author=kimi",
                "--out",
                "./out",
            ],
            env=env,
        )
        assert result.exit_code == 0
        assert Path("out/PRD.md").exists()


def test_cli_run_with_native_provider_flags_in_dry_run() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        env = {
            "GEMINI_API_KEY": "g-test-key",
            "CLAUDE_API_KEY": "c-test-key",
            "DB_PATH": "./test.db",
        }
        result = runner.invoke(
            main,
            [
                "run",
                "--idea",
                "cli native providers",
                "--dry-run",
                "--gemini",
                "--claude",
                "--out",
                "./out",
            ],
            env=env,
        )
        assert result.exit_code == 0
        assert Path("out/PRD.md").exists()
        assert Path("out/TECH_SPEC.md").exists()
        assert Path("out/EXEC_PLAN.md").exists()


def test_cli_observe_prints_timeline_table() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        db_path = "./observe.db"
        store = SqliteStore(db_path)
        run = Run(idea="observe test", config_json="{}", status="running")
        store.insert_run(run)
        store.insert_run_event(
            RunEvent(
                run_id=run.id,
                step="run",
                event_type="run_started",
                round_number=0,
                payload={"artifact_type": "PRD"},
            )
        )
        store.insert_run_event(
            RunEvent(
                run_id=run.id,
                step="gate",
                event_type="gate_decision",
                round_number=1,
                detail="pass_gate",
                payload={"decision": "PASS"},
            )
        )
        store.close()

        result = runner.invoke(main, ["observe", "--run-id", run.id], env={"DB_PATH": db_path})

        assert result.exit_code == 0
        assert "Run timeline:" in result.output
        assert "run_started" in result.output
        assert "gate_decision" in result.output
        assert "artifact_type" in result.output


def test_cli_observe_latest_prints_latest_run_timeline() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        db_path = "./observe.db"
        store = SqliteStore(db_path)

        run1 = Run(idea="run1", config_json="{}", status="done")
        store.insert_run(run1)
        store.insert_run_event(
            RunEvent(
                run_id=run1.id,
                step="run",
                event_type="run_started",
                round_number=0,
                payload={"name": "run1"},
            )
        )

        run2 = Run(idea="run2", config_json="{}", status="done")
        store.insert_run(run2)
        store.insert_run_event(
            RunEvent(
                run_id=run2.id,
                step="run",
                event_type="run_started",
                round_number=0,
                payload={"name": "run2"},
            )
        )
        store.close()

        result = runner.invoke(main, ["observe", "--latest"], env={"DB_PATH": db_path})

        assert result.exit_code == 0
        assert f"Run timeline: {run2.id}" in result.output
        assert "run_started" in result.output


def test_cli_observe_filters_by_step_event_type_and_limit() -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        db_path = "./observe.db"
        store = SqliteStore(db_path)
        run = Run(idea="observe filter", config_json="{}", status="done")
        store.insert_run(run)
        store.insert_run_event(
            RunEvent(
                run_id=run.id,
                step="run",
                event_type="run_started",
                round_number=0,
                payload={"seq": 1},
            )
        )
        store.insert_run_event(
            RunEvent(
                run_id=run.id,
                step="gate",
                event_type="gate_decision",
                round_number=1,
                payload={"seq": 2},
            )
        )
        store.insert_run_event(
            RunEvent(
                run_id=run.id,
                step="gate",
                event_type="stage_completed",
                round_number=1,
                payload={"seq": 3},
            )
        )
        store.close()

        result_by_step = runner.invoke(
            main,
            ["observe", "--run-id", run.id, "--step", "gate"],
            env={"DB_PATH": db_path},
        )
        assert result_by_step.exit_code == 0
        assert "gate_decision" in result_by_step.output
        assert "stage_completed" in result_by_step.output
        assert "run_started" not in result_by_step.output

        result_by_type_limit = runner.invoke(
            main,
            [
                "observe",
                "--run-id",
                run.id,
                "--event-type",
                "stage_completed",
                "--limit",
                "1",
            ],
            env={"DB_PATH": db_path},
        )
        assert result_by_type_limit.exit_code == 0
        assert "stage_completed" in result_by_type_limit.output
        assert "gate_decision" not in result_by_type_limit.output
        assert "run_started" not in result_by_type_limit.output
