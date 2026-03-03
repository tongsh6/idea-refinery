# Skill: Publish GitHub Release

## 功能

基于 `release/*` 分支完成版本发布：合并到 `main`、打 tag、创建 GitHub Release。

## 输入

```python
class PublishGitHubReleaseInput(BaseModel):
    release_branch: str  # 例如: release/v0.4.0
    tag_name: str        # 例如: v0.4.0
    title: str           # Release 标题
    notes: str  # Release Note（必填）
    create_github_release: bool = True
    remote: str = "origin"
    verify: bool = True
```

## 输出

```python
class PublishGitHubReleaseOutput(BaseModel):
    success: bool
    merged_to_main: bool
    tag_pushed: bool
    github_release_url: str | None = None
    kept_release_branch: str | None = None
    checks: list[str]
```

## 执行策略

1. 在 `release/*` 分支执行验证（默认 `python3 -m pytest`、`python3 -m build`）。
2. 将 `release/*` 合并到 `main` 并推送。
3. 打版本 tag 并推送到远端。
4. 使用 `gh release create` 创建 GitHub Release（必须包含 Release Note）。
5. 保留 `release/*` 分支，不做删除。

## 示例

Input:

```json
{
  "release_branch": "release/v0.4.0",
  "tag_name": "v0.4.0",
  "title": "v0.4.0",
  "notes": "Release note content...",
  "create_github_release": true,
  "verify": true
}
```

Output:

```json
{
  "success": true,
  "merged_to_main": true,
  "tag_pushed": true,
  "github_release_url": "https://github.com/tongsh6/idea-refinery/releases/tag/v0.4.0",
  "kept_release_branch": "release/v0.4.0",
  "checks": [
    "python3 -m pytest",
    "python3 -m build"
  ]
}
```

## 边界约束

- 不在未通过验证时创建 tag 或 GitHub Release。
- 不允许缺少 Release Note 就发版。
- 不覆盖已存在 tag。
- 不删除 `release/*` 分支。
