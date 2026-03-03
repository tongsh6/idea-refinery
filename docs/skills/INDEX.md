# 项目 Skills 索引

本目录存放 IdeaRefinery 的项目专用 Skill 定义，主要面向工程协作与发布自动化。

## 列表

| Skill | 说明 | 对应场景 |
|------|------|---------|
| [skill-manage-gitflow-release.md](skill-manage-gitflow-release.md) | 管理 `main -> feature -> develop -> release -> main` 分支流转 | 日常分支创建、合并、分支清理 |
| [skill-publish-github-release.md](skill-publish-github-release.md) | 从 `release/*` 发布到 GitHub（tag + Release） | 版本发布、发布说明生成 |

## OpenCode 可调用映射

以下 skill 已映射为 OpenCode 项目技能文件：

- `manage-gitflow-release` -> `.opencode/skills/manage-gitflow-release/SKILL.md`
- `publish-github-release` -> `.opencode/skills/publish-github-release/SKILL.md`

## 关联脚本

- 跨平台发布脚本：`scripts/release/gitflow_release.py`
- Bash 包装器：`scripts/release/gitflow-release.sh`
- PowerShell 包装器：`scripts/release/gitflow-release.ps1`
