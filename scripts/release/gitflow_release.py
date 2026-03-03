#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class RepoConfig:
    remote: str
    main: str
    develop: str
    dry_run: bool


def run(cmd: list[str], *, dry_run: bool = False) -> None:
    printable = " ".join(shlex.quote(part) for part in cmd)
    print(f"$ {printable}")
    if dry_run:
        return
    _ = subprocess.run(cmd, check=True)


def output(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def local_branch_exists(branch: str) -> bool:
    code = subprocess.run(
        ["git", "show-ref", "--verify", f"refs/heads/{branch}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode
    return code == 0


def remote_branch_exists(remote: str, branch: str) -> bool:
    code = subprocess.run(
        ["git", "ls-remote", "--heads", remote, branch],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode
    if code != 0:
        return False
    out = output(["git", "ls-remote", "--heads", remote, branch])
    return bool(out)


def ensure_on_branch(branch: str, cfg: RepoConfig) -> None:
    if local_branch_exists(branch):
        run(["git", "checkout", branch], dry_run=cfg.dry_run)
    else:
        run(["git", "checkout", "-b", branch], dry_run=cfg.dry_run)


def pull_branch(cfg: RepoConfig, branch: str) -> None:
    run(["git", "checkout", branch], dry_run=cfg.dry_run)
    run(["git", "pull", cfg.remote, branch], dry_run=cfg.dry_run)


def normalize_feature(name: str) -> str:
    return name if name.startswith("feature/") else f"feature/{name}"


def normalize_release(version: str) -> tuple[str, str]:
    ver = version[1:] if version.startswith("v") else version
    return f"release/v{ver}", f"v{ver}"


def init_flow(cfg: RepoConfig) -> None:
    pull_branch(cfg, cfg.main)
    if local_branch_exists(cfg.develop):
        run(["git", "checkout", cfg.develop], dry_run=cfg.dry_run)
        run(["git", "pull", cfg.remote, cfg.develop], dry_run=cfg.dry_run)
    elif remote_branch_exists(cfg.remote, cfg.develop):
        run(["git", "checkout", "-b", cfg.develop, f"{cfg.remote}/{cfg.develop}"], dry_run=cfg.dry_run)
    else:
        run(["git", "checkout", "-b", cfg.develop, cfg.main], dry_run=cfg.dry_run)
        run(["git", "push", "-u", cfg.remote, cfg.develop], dry_run=cfg.dry_run)


def start_feature(cfg: RepoConfig, feature_name: str) -> None:
    feature = normalize_feature(feature_name)
    pull_branch(cfg, cfg.main)
    run(["git", "checkout", "-b", feature, cfg.main], dry_run=cfg.dry_run)
    run(["git", "push", "-u", cfg.remote, feature], dry_run=cfg.dry_run)


def merge_feature(cfg: RepoConfig, feature_name: str) -> None:
    feature = normalize_feature(feature_name)
    pull_branch(cfg, cfg.develop)
    run(["git", "merge", "--no-ff", feature], dry_run=cfg.dry_run)
    run(["git", "push", cfg.remote, cfg.develop], dry_run=cfg.dry_run)
    run(["git", "branch", "-d", feature], dry_run=cfg.dry_run)
    run(["git", "push", cfg.remote, "--delete", feature], dry_run=cfg.dry_run)


def start_release(cfg: RepoConfig, version: str) -> None:
    release_branch, _ = normalize_release(version)
    pull_branch(cfg, cfg.develop)
    run(["git", "checkout", "-b", release_branch, cfg.develop], dry_run=cfg.dry_run)
    run(["git", "push", "-u", cfg.remote, release_branch], dry_run=cfg.dry_run)


def finalize_release(cfg: RepoConfig, version: str, verify: bool) -> None:
    release_branch, _ = normalize_release(version)
    pull_branch(cfg, release_branch)
    if verify:
        run([sys.executable, "-m", "pytest"], dry_run=cfg.dry_run)
        run([sys.executable, "-m", "build"], dry_run=cfg.dry_run)
    pull_branch(cfg, cfg.main)
    run(["git", "merge", "--no-ff", release_branch], dry_run=cfg.dry_run)
    run(["git", "push", cfg.remote, cfg.main], dry_run=cfg.dry_run)


def publish_release(cfg: RepoConfig, version: str, title: str | None, notes: str, verify: bool) -> None:
    release_branch, tag = normalize_release(version)
    finalize_release(cfg, version, verify)
    run(["git", "tag", tag], dry_run=cfg.dry_run)
    run(["git", "push", cfg.remote, tag], dry_run=cfg.dry_run)

    release_title = title or tag
    run(["gh", "release", "create", tag, "--title", release_title, "--notes", notes], dry_run=cfg.dry_run)
    print(f"Release branch kept: {release_branch}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cross-platform GitFlow helper for IdeaRefinery releases",
    )
    _ = parser.add_argument("--remote", default="origin")
    _ = parser.add_argument("--main", default="main")
    _ = parser.add_argument("--develop", default="develop")
    _ = parser.add_argument("--dry-run", action="store_true")

    subparsers = parser.add_subparsers(dest="action", required=True)

    _ = subparsers.add_parser("init", help="Initialize main/develop branches")

    feature_parser = subparsers.add_parser("start-feature", help="Create a feature branch from main")
    _ = feature_parser.add_argument("--name", required=True)

    merge_feature_parser = subparsers.add_parser(
        "merge-feature",
        help="Merge feature into develop, then delete feature branch",
    )
    _ = merge_feature_parser.add_argument("--name", required=True)

    release_parser = subparsers.add_parser("start-release", help="Create a release branch from develop")
    _ = release_parser.add_argument("--version", required=True)

    finalize_parser = subparsers.add_parser("finalize-release", help="Merge release into main and keep release branch")
    _ = finalize_parser.add_argument("--version", required=True)
    _ = finalize_parser.add_argument("--skip-verify", action="store_true")

    publish_parser = subparsers.add_parser("publish-release", help="Finalize release and publish GitHub release")
    _ = publish_parser.add_argument("--version", required=True)
    _ = publish_parser.add_argument("--title")
    notes_group = publish_parser.add_mutually_exclusive_group(required=True)
    _ = notes_group.add_argument("--notes", help="Inline release notes content")
    _ = notes_group.add_argument("--notes-file", help="Path to release notes file")
    _ = publish_parser.add_argument("--skip-verify", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    action = str(getattr(args, "action"))
    cfg = RepoConfig(
        remote=str(getattr(args, "remote")),
        main=str(getattr(args, "main")),
        develop=str(getattr(args, "develop")),
        dry_run=bool(getattr(args, "dry_run")),
    )

    try:
        if action == "init":
            init_flow(cfg)
        elif action == "start-feature":
            start_feature(cfg, str(getattr(args, "name")))
        elif action == "merge-feature":
            merge_feature(cfg, str(getattr(args, "name")))
        elif action == "start-release":
            start_release(cfg, str(getattr(args, "version")))
        elif action == "finalize-release":
            finalize_release(
                cfg,
                str(getattr(args, "version")),
                not bool(getattr(args, "skip_verify")),
            )
        elif action == "publish-release":
            notes = getattr(args, "notes", None)
            notes_file = getattr(args, "notes_file", None)
            if notes is None and notes_file is not None:
                notes = Path(str(notes_file)).read_text(encoding="utf-8")
            if notes is None:
                parser.error("publish-release requires --notes or --notes-file")

            publish_release(
                cfg,
                str(getattr(args, "version")),
                getattr(args, "title", None),
                str(notes),
                not bool(getattr(args, "skip_verify")),
            )
        else:
            parser.error(f"Unknown action: {action}")
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with code {exc.returncode}", file=sys.stderr)
        return exc.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
