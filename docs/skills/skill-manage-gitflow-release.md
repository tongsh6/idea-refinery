# Skill: Manage GitFlow Release

## 功能

按项目约定执行 `main -> feature -> develop -> release -> main` 分支流转，并在 feature 合并后删除 feature 分支、保留 release 分支。

## 输入

```python
class ManageGitFlowInput(BaseModel):
    action: Literal[
        "init",
        "start_feature",
        "merge_feature",
        "start_release",
        "finalize_release",
    ]
    feature_name: str | None = None
    release_version: str | None = None
    remote: str = "origin"
    dry_run: bool = False
```

## 输出

```python
class ManageGitFlowOutput(BaseModel):
    success: bool
    action: str
    branch_before: str | None = None
    branch_after: str | None = None
    operations: list[str]
    deleted_feature_branches: list[str] = []
    kept_release_branches: list[str] = []
```

## 执行策略

1. `init`：确保 `main` 与 `develop` 分支存在并可同步。
2. `start_feature`：从 `main` 创建 `feature/<name>` 分支。
3. `merge_feature`：将 `feature/<name>` 合并到 `develop`，随后删除本地与远端 feature 分支。
4. `start_release`：从 `develop` 创建 `release/vX.Y.Z`。
5. `finalize_release`：将 `release/vX.Y.Z` 合并到 `main`，并保留 release 分支用于追溯。

## 示例

Input:

```json
{
  "action": "merge_feature",
  "feature_name": "provider-routing-improve",
  "remote": "origin",
  "dry_run": false
}
```

Output:

```json
{
  "success": true,
  "action": "merge_feature",
  "branch_before": "feature/provider-routing-improve",
  "branch_after": "develop",
  "operations": [
    "merge feature/provider-routing-improve into develop",
    "push develop",
    "delete local feature/provider-routing-improve",
    "delete remote feature/provider-routing-improve"
  ],
  "deleted_feature_branches": ["feature/provider-routing-improve"],
  "kept_release_branches": []
}
```

## 边界约束

- 不直接推送到 `main` 以外的生产环境分支。
- 不删除任何 `release/*` 分支。
- 不绕过发布前验证（`pytest` 与 `python -m build`）。
