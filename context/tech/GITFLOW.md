# IdeaRefinery Git Flow 规范

## 目标
- 保持 `main` 始终可发布、可回滚。
- 固化 `main -> feature -> develop -> release -> main` 发布路径。
- 让多人协作时分支职责清晰、变更可追溯。

## 分支模型
- `main`：稳定分支，只接受 `release/*` 或 `hotfix/*` 合并。
- `develop`：集成分支，接收多个 `feature/*` 合并后再进入 `release/*`。
- `release/vX.Y.Z`：版本收敛分支，用于联调、验收、发布准备。
- `feature/<scope>-<topic>`：功能分支，从 `main` 拉出，生命周期短，只合并到 `develop`。
- `hotfix/vX.Y.Z-<topic>`：线上紧急修复分支，从 `main` 拉出，最终回合并到 `main`（必要时同步到当前 release）。

## 命名规范
- `feature/idea-refinery-v0.2`
- `feature/provider-routing-improve`
- `release/v0.1.1`
- `hotfix/v0.1.1-cli-crash`

## 标准发布流程（必须）
1. 从 `main` 拉出多个 `feature/*` 开发。
2. 将计划内多个 `feature/*` 通过 PR 合并到 `develop`。
3. 每个 `feature/*` 合并完成后删除（本地与远端）。
4. 从 `develop` 创建 `release/vX.Y.Z`。
5. 在 `release/vX.Y.Z` 完成回归验证（至少 `python3 -m pytest` + `python3 -m build`）。
6. 将 `release/vX.Y.Z` 合并到 `main`。
7. 在 `main` 打标签 `vX.Y.Z` 并推送 tag。
8. 创建 GitHub Release，并附完整 Release Note（必填）。
9. 保留 `release/*` 分支用于追溯和补丁分支来源。

## 提交流程约束
- 提交粒度：一个提交只做一件事（功能/修复/文档不要混杂）。
- 提交信息建议使用 Conventional Commits：`feat: ...` / `fix: ...` / `docs: ...` / `refactor: ...` / `test: ...` / `chore: ...`。
- 禁止直接 push 到 `main`。
- 发布前禁止未验证的临时变更（例如跳过测试、临时注释核心逻辑）。

## PR 约束
- `feature/* -> develop`
  - 需说明变更目的、影响范围、验证结果。
  - 至少 1 个 reviewer。
- `develop -> release/*`
  - 需确认本次 release 范围与特性清单。
  - 需通过基础验证（至少测试和构建）。
- `release/* -> main`
  - 必须附完整发布清单（功能、修复、破坏性变更、验证结果）。
  - 必须确认标签计划（`vX.Y.Z`）。

## 回滚策略
- 首选回滚粒度：`main` 上按 commit `revert`。
- 版本级回滚：回退到上一个稳定 tag（例如 `v0.1.0`）。
- 紧急修复完成后，补充 `context/experience/` 复盘记录。

## 推荐保护规则（GitHub）
- `main` 分支保护：
  - Require pull request before merging
  - Require approvals（>=1）
  - Require status checks to pass（至少测试与构建）
  - Include administrators
- `release/*` 分支保护：
  - Require pull request before merging
  - Require status checks to pass
- `develop` 分支保护：
  - Require pull request before merging
  - Require status checks to pass

## 常用命令模板
```bash
# 1) 初始化 develop（如不存在）
python3 scripts/release/gitflow_release.py init

# 2) 从 main 创建 feature 分支
git checkout main
git pull
git checkout -b feature/provider-routing-improve
git push -u origin feature/provider-routing-improve

# 3) 其他 feature 重复以上步骤（多个 feature 组成一个 release）
# feature/a, feature/b, feature/c ...

# 4) 将 feature 合并到 develop，随后删除 feature
git checkout develop
git pull
git merge --no-ff feature/provider-routing-improve
git push origin develop
git branch -d feature/provider-routing-improve
git push origin --delete feature/provider-routing-improve

# 5) 从 develop 创建 release 分支
git checkout develop
git pull
git checkout -b release/v0.1.1
git push -u origin release/v0.1.1

# 6) 在 release 分支验证
git checkout release/v0.1.1
python3 -m pytest
python3 -m build

# 7) 合并 release 到 main（建议通过 PR）
git checkout main
git pull
git merge --no-ff release/v0.1.1
git push origin main

# 8) 在 main 打标签并推送
git tag v0.1.1
git push origin v0.1.1

# 9) 创建 GitHub Release（Release Note 必填）
gh release create v0.1.1 --title "v0.1.1" --notes-file ./release-notes/v0.1.1.md

# 10) release 分支保留，不删除
```

## 自动化脚本（跨平台）

- Python 主脚本：`scripts/release/gitflow_release.py`
- Bash 包装器：`scripts/release/gitflow-release.sh`
- PowerShell 包装器：`scripts/release/gitflow-release.ps1`

示例：

```bash
# 从 main 创建 feature
python3 scripts/release/gitflow_release.py start-feature --name provider-routing-improve

# feature 合并到 develop 后自动删除 feature
python3 scripts/release/gitflow_release.py merge-feature --name provider-routing-improve

# 创建并发布 release（保留 release 分支，Release Note 必填）
python3 scripts/release/gitflow_release.py publish-release --version v0.1.1 --title "v0.1.1" --notes-file ./release-notes/v0.1.1.md
```

## 与当前项目对齐
- 后续版本统一遵循本文档，不再使用临时分支策略。
