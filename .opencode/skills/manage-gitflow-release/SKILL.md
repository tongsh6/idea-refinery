---
name: manage-gitflow-release
description: Manage project GitFlow branch operations with main -> feature -> develop -> release -> main and delete merged feature branches while keeping release branches.
---

## Purpose

Execute GitFlow branch operations for this repository with the project policy:

- flow: `main -> feature -> develop -> release -> main`
- delete merged `feature/*` branches
- keep `release/*` branches after publishing

## Use When

- You need to initialize or sync `main` and `develop`
- You need to create/merge feature branches by policy
- You need to create/finalize a release branch without deleting it

## Required Commands

Use the project script:

```bash
python3 scripts/release/gitflow_release.py <action> [flags]
```

Actions:

- `init`
- `start-feature --name <feature-name>`
- `merge-feature --name <feature-name>`
- `start-release --version <vX.Y.Z>`
- `finalize-release --version <vX.Y.Z> [--skip-verify]`

## Guardrails

- Do not delete `release/*` branches.
- Do not bypass verification unless explicitly requested (`--skip-verify`).
- Prefer `--dry-run` before destructive steps.

## Quick Examples

```bash
python3 scripts/release/gitflow_release.py init
python3 scripts/release/gitflow_release.py start-feature --name provider-routing-improve
python3 scripts/release/gitflow_release.py merge-feature --name provider-routing-improve
python3 scripts/release/gitflow_release.py start-release --version v0.4.0
python3 scripts/release/gitflow_release.py finalize-release --version v0.4.0
```
