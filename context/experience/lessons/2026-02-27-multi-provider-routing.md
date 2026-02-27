# 经验：多供应商路由与 fallback 的最小可用落地

> 多供应商接入时，先解决“配置入口统一 + 路由顺序可控 + 失败可回退”，再谈高级策略。

## 背景

需要把 Gemini/Claude/GLM/MiniMax/Kimi 等供应商纳入统一接入体系，并保证运行稳定。

## 问题

单一 provider 配置无法满足多供应商并存与按角色路由的需求。

## 原因

- 早期 registry 仅支持单 openai provider + 可选 ollama。
- 路由配置入口分散，不利于 CI 和多环境复用。

## 解决方案

- 新增统一 provider 规格对象与批量注册能力。
- 同时支持两类配置入口：
  - CLI：`--openai-provider`、`--role-provider`
  - ENV：`OPENAI_COMPAT_PROVIDERS_JSON`、`ROLE_PROVIDER_MAP_JSON`
- 路由策略：
  - role 命中优先 provider
  - 失败后按候选顺序 fallback

## 教训

- 应该做：把“接入方式”文档化并给可复制示例。
- 不应该做：只在代码中隐式支持，不暴露配置契约。

## 相关

- `context/tech/provider-integration.md`
- `idea_refinery/providers/registry.py`
- `idea_refinery/cli.py`
- `tests/test_registry_multi_provider.py`

---

**关键词**：`multi-provider`, `role-routing`, `fallback`, `openai-compatible`, `config-contract`

**类别**：设计决策
