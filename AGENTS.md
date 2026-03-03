# IdeaRefinery AI 指南

这是项目级 AI 协作入口。

语言规则：
- 默认使用中文沟通
- 代码/命令/标识符保持英文

项目：
- 一句话介绍：IdeaRefinery 是开源的方案精炼引擎，通过 CR 闭环与可度量 Gate，把 idea 收敛为可执行的 PRD/TECH/PLAN。
- 核心价值：产出可验收、可追溯、可回放的方案文档，成本可控。

关键约束：
- 使用 Python 3.11+ 与 Pydantic v2 作为核心模型层
- 编排必须遵循 Draft → Review → Edit → Gate 的闭环流程，并执行 CR 关闭规则
- 禁止类型绕过（不使用 "as any" / "@ts-ignore"）
- 产物先结构化 JSON，再导出 Markdown

常用命令：
- build: python -m build
- test: pytest
- run: refinery run --idea "..." --out ./out

上下文入口：
- AIEF Sidecar 主入口：AIEF/context/INDEX.md
- 约定：AIEF 相关文档仅保留在 `AIEF/` 目录

知识库：

| Directory | Purpose | When to Load |
|-----------|---------|-------------|
| AIEF/context/business/ | Business knowledge | Understanding requirements, domain models |
| AIEF/context/tech/ | Technical docs | Architecture, API, conventions |
| AIEF/context/experience/ | Experience library | Avoid repeating mistakes |
| AIEF/workflow/ | Workflows | Complex task phase guides |
| AIEF/docs/standards/ | Standards | Skill/Command/Agent specs (L2) |
| AIEF/docs/standards/patterns/ | Patterns | Phase routing, experience mgmt, context loading (L3) |

开发工具：

| Directory / File | Purpose | When to Load |
|------------------|---------|-------------|
| AIEF/ | AIEF sidecar 资产（base-dir 模式） | 执行模板迁移、对照生成结果时 |
| .specify/ | spec-kit 配置与模板 | 使用 spec-kit 流程开发新功能 |
| .opencode/command/ | spec-kit slash 命令 | AI 编码助手执行 /speckit.* 命令 |
| docs/skills/ | 项目专用 Skill 定义 | 执行 GitFlow 发布、GitHub Release 操作 |
| scripts/release/ | 跨平台 GitFlow 发布脚本 | 需要按规范执行版本发布时 |
