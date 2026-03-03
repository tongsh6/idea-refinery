---
name: publish-github-release
description: Publish a validated release to GitHub from release branch.
---

Primary command:

```bash
python3 scripts/release/gitflow_release.py publish-release --version <vX.Y.Z> --title "<title>"
```

Verification and tag steps are included by default.
