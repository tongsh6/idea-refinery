---
name: publish-github-release
description: Publish a GitHub release from a release branch, including verification, merge to main, tag push, and gh release creation.
---

## Purpose

Publish a release from `release/*` with consistent verification and GitHub metadata.

Policy in this project:

- merge `release/*` into `main`
- create and push tag `vX.Y.Z`
- create GitHub Release
- keep `release/*` branch

## Use When

- A release branch is ready and validated
- You need one command path to publish with `gh`

## Required Commands

Use the project script:

```bash
python3 scripts/release/gitflow_release.py publish-release --version <vX.Y.Z> --title "<title>" [--notes "..."]
```

Related finalize-only action:

```bash
python3 scripts/release/gitflow_release.py finalize-release --version <vX.Y.Z>
```

## Verification

Default verification before merge/tag:

- `python3 -m pytest`
- `python3 -m build`

## Guardrails

- Do not publish when verification fails.
- Do not overwrite existing tags.
- Do not delete `release/*` branches.

## Quick Example

```bash
python3 scripts/release/gitflow_release.py publish-release --version v0.4.0 --title "v0.4.0" --notes "Release notes"
```
