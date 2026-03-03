# GitFlow 发布脚本

跨平台 GitFlow 发布工具，固定流程为：`main -> feature -> develop -> release -> main`。

规则：

- `feature/*` 合并到 `develop` 后删除（本地 + 远端）
- `release/*` 合并到 `main` 后保留

## Python 主脚本

`gitflow_release.py` 提供全部子命令：

```bash
python3 scripts/release/gitflow_release.py --help
```

## 平台包装器

- macOS/Linux: `scripts/release/gitflow-release.sh`
- Windows PowerShell: `scripts/release/gitflow-release.ps1`

## 常用命令

```bash
# 1) 初始化 main/develop
python3 scripts/release/gitflow_release.py init

# 2) 从 main 创建 feature
python3 scripts/release/gitflow_release.py start-feature --name provider-routing-improve

# 3) 将 feature 合并到 develop 并删除 feature
python3 scripts/release/gitflow_release.py merge-feature --name provider-routing-improve

# 4) 从 develop 创建 release
python3 scripts/release/gitflow_release.py start-release --version v0.4.0

# 5) 将 release 合并到 main（默认执行 pytest + build）
python3 scripts/release/gitflow_release.py finalize-release --version v0.4.0

# 6) 完整发布（finalize + tag + GitHub Release）
python3 scripts/release/gitflow_release.py publish-release --version v0.4.0 --title "v0.4.0"
```

## Dry Run

```bash
python3 scripts/release/gitflow_release.py --dry-run publish-release --version v0.4.0
```
