from pathlib import Path

from click.testing import CliRunner

from idea_refinery.cli import main


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
