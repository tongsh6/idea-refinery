# IdeaRefinery

IdeaRefinery 是开源的“方案精炼引擎”内核，通过 CR 闭环与可度量 Gate，把 idea 收敛为可执行的 PRD/TECH_SPEC/EXEC_PLAN。

## 目标
- 输入 idea 自动输出三件套（PRD/TECH_SPEC/EXEC_PLAN）
- 支持 OpenAI-compatible 端点与 Ollama 原生
- 多轮 CR 闭环与 Gate 停机
- 成本与上下文治理（预算/摘要/裁剪）
- 全链路可回放
- 提供 GUI 工作台（先 MVP）用于可视化 run 状态、CR 处理与 Gate 决策

## 开发
```bash
python3 -m pip install -e ".[dev]"
pytest
```

## Git 工作流
- 项目统一采用 `main -> feature` 开发，`多个 feature -> 一个 release -> main` 发布。
- 发布完成后删除已合并的 `feature/*` 与 `release/*` 分支。
- 详细规范见：`context/tech/GITFLOW.md`
- 发布前最少执行：`pytest` 和 `python -m build`

## 运行
```bash
refinery run --idea "..." --out ./out
```

默认会执行三阶段流水线并输出：
- `out/PRD.md`
- `out/TECH_SPEC.md`
- `out/EXEC_PLAN.md`

如果只做本地验证，可加 `--dry-run --ollama`。

## GUI 计划与预览（草案）
- GUI 已纳入项目计划（见 `context/business/DOMAIN.md` 的里程碑与验收标准）。
- 当前提供一个可审阅页面原型：`prototypes/gui/review-workbench-v3.html`
- 打开方式（macOS）：`open prototypes/gui/review-workbench-v3.html`
- v3 交互重点：Panel 0 先输入 idea（必填），文件上传作为可选补充材料。

## 多供应商接入

支持两种方式：

1. OpenAI-compatible 兼容端点（推荐）
2. 原生插件（不兼容协议时）

原生插件当前内置：`Gemini`、`Claude`、`Ollama`

### CLI 方式（并存多个供应商）

```bash
refinery run \
  --idea "..." \
  --openai-provider "kimi,https://api.moonshot.cn/v1,moonshot-v1-8k,KIMI_API_KEY" \
  --openai-provider "glm,https://open.bigmodel.cn/api/paas/v4,glm-4.5,GLM_API_KEY" \
  --role-provider "author=kimi" \
  --role-provider "editor=glm" \
  --out ./out
```

### 环境变量方式

```bash
export OPENAI_COMPAT_PROVIDERS_JSON='[
  {"name":"kimi","base_url":"https://api.moonshot.cn/v1","model":"moonshot-v1-8k","api_key_env":"KIMI_API_KEY"},
  {"name":"glm","base_url":"https://open.bigmodel.cn/api/paas/v4","model":"glm-4.5","api_key_env":"GLM_API_KEY"}
]'

export ROLE_PROVIDER_MAP_JSON='{
  "author":"kimi",
  "editor":"glm",
  "reviewer:value":"glm"
}'
```

说明：
- `--openai-provider` 可重复，按注册顺序作为 fallback 候选。
- `--role-provider` 可重复，用于给特定角色指定优先 provider。
- 未命中 role 映射时，按候选顺序进行 fallback。

### 原生 Provider 快速启用

```bash
export GEMINI_API_KEY=...
export CLAUDE_API_KEY=...

refinery run --idea "..." --gemini --claude --out ./out
```
