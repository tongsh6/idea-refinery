# Contributing to IdeaRefinery

欢迎参与贡献。本文件说明开发环境搭建、分支规范、PR 流程与发布检查清单。

---

## 开发环境

```bash
# 1. 克隆仓库
git clone https://github.com/tongsh6/idea-refinery.git
cd idea-refinery

# 2. 安装依赖（含开发工具）
python3 -m pip install -e ".[dev]"

# 3. 复制环境变量模板
cp .env.example .env
# 按需填写 API_KEY 等配置

# 4. 运行测试
python3 -m pytest

# 5. 构建验证
python3 -m build
```

依赖要求：Python 3.11+

---

## Git 工作流

完整规范见 `context/tech/GITFLOW.md`，核心如下：

```
main（稳定）
 ├── feature/xxx    # 从 main 拉出，开发完成后合并到 develop
 ├── feature/yyy
 ├── develop        # 集成分支，承接多个 feature
 └── release/vX.Y.Z # 从 develop 拉出，验证通过后合并到 main 并打标签
```

**快速上手：**

```bash
# 1. 从 main 创建 feature 分支
git checkout main && git pull
git checkout -b feature/<your-topic>

# 2. 开发完成后推送并发起 PR（目标：develop 分支）
git push -u origin feature/<your-topic>
```

---

## PR 规范

### feature -> develop PR
- 标题格式：`feat: <简要描述>` / `fix: <简要描述>` / `docs: <简要描述>`
- 描述需包含：
  - **变更目的**：解决什么问题
  - **影响范围**：修改了哪些模块
  - **验证结果**：pytest 是否通过，是否手动测试

### release -> main PR（发布 PR）
发布前必须确认以下清单全部通过：

- [ ] `python3 -m pytest` 全部通过
- [ ] `python3 -m build` 成功产出 sdist/wheel
- [ ] `pyproject.toml` 版本号已更新
- [ ] `context/tech/GITFLOW.md` 发布流程已遵循
- [ ] release 分支验证通过后，计划在 main 打标签 `vX.Y.Z`
- [ ] GitHub Release 草稿已准备好

---

## 提交信息规范

遵循 Conventional Commits：

| 类型 | 场景 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `refactor` | 重构（不影响功能） |
| `test` | 测试 |
| `chore` | 构建/依赖/工具 |

示例：
```
feat: add gemini native provider
fix: handle provider timeout in registry fallback
docs: update quick-start example in README
```

---

## 发布流程（维护者）

1. 确认所有目标 feature 已合并到 `develop`
2. 从 `develop` 创建 `release/vX.Y.Z`
3. 在 `release/vX.Y.Z` 执行完整验证（pytest + build）
4. 将 `release/vX.Y.Z` 合并到 `main`
5. 打标签并推送：
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```
6. 创建 GitHub Release
7. 删除已合并的 `feature/*` 分支，保留 `release/*` 分支：
   ```bash
   git branch -d feature/xxx && git push origin --delete feature/xxx
   ```

---

## 代码规范

- 类型检查：`mypy`（strict=false）
- Lint：`ruff`（line-length=100）
- 禁止 `type: ignore` 绕过类型系统
- 产物先结构化 JSON，再导出 Markdown

---

## 问题反馈

- Bug / Feature Request：请在 [GitHub Issues](https://github.com/tongsh6/idea-refinery/issues) 提交
- 提交前请先搜索是否有相关 issue
