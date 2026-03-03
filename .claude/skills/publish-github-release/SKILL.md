---
name: publish-github-release
description: Publish GitHub release from release branch with verify, merge, tag, and gh release steps.
---

Use project script:

```bash
python3 scripts/release/gitflow_release.py publish-release --version <vX.Y.Z> --title "<title>"
```

Policy:

- verify with pytest and build
- keep `release/*`
