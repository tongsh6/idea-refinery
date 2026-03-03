---
name: manage-gitflow-release
description: Manage project GitFlow branch operations with main -> feature -> develop -> release -> main.
---

Use project script:

```bash
python3 scripts/release/gitflow_release.py <action> [flags]
```

Policy:

- delete merged `feature/*`
- keep `release/*`
