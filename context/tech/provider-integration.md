# Provider 接入指南

## 目标

为 IdeaRefinery 提供统一的多供应商接入规范，保证：
- 接入成本低（优先零代码）
- 运行稳定（重试 + fallback）
- 指标可观测（provider/model/tokens/latency/cost）

## 接入路径

### 路径 A：OpenAI-compatible（推荐）

适用条件：供应商提供兼容 `/v1/chat/completions` 的端点。

接入步骤：
1. 配置 `OPENAI_BASE_URL` 为供应商兼容网关
2. 配置 `OPENAI_API_KEY`
3. 配置 `DEFAULT_MODEL` 或 CLI 参数 `--openai-model`
4. 执行 `refinery run ...` 验证

多供应商并存（推荐）：
- 环境变量：`OPENAI_COMPAT_PROVIDERS_JSON`
- CLI：重复传 `--openai-provider name,base_url,model,api_key_env`
- 角色优先映射：`ROLE_PROVIDER_MAP_JSON` 或重复传 `--role-provider role=provider`
- fallback 顺序：按 provider 注册顺序执行（优先 provider 失败后按候选顺序依次尝试）

优点：
- 不需要修改业务编排代码
- 复用现有 `OpenAICompatibleProvider`

### 路径 B：原生插件接入

适用条件：供应商不提供 OpenAI-compatible 端点。

接入步骤：
1. 新建 provider 文件（例如 `idea_refinery/providers/vendor_x.py`）
2. 实现 `BaseProvider`：
   - `complete(req: CompletionRequest) -> CompletionResult`
   - `estimate_cost(input_tokens, output_tokens, model) -> float`
3. 在 registry 中注册 provider 并加入候选路由
4. 增加对应联调测试

内置原生插件：
- Gemini（`--gemini`，`GEMINI_API_KEY`）
- Claude（`--claude`，`CLAUDE_API_KEY`）
- Ollama（`--ollama`）

## 目标供应商映射

- Gemini：优先接兼容网关；无兼容网关走插件
- Claude：优先接兼容网关；无兼容网关走插件
- GLM：优先接兼容网关；无兼容网关走插件
- MiniMax：优先接兼容网关；无兼容网关走插件
- Kimi：优先接兼容网关；无兼容网关走插件

## 配置示例

```bash
# OpenAI-compatible
OPENAI_BASE_URL=https://<vendor-compatible-endpoint>/v1
OPENAI_API_KEY=sk-...
DEFAULT_MODEL=<vendor-model>

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

## 路由与容错

- 使用 role map 指定优先 provider
- 使用 candidate 顺序做 fallback
- 同 provider 失败时执行有限重试（退避）

建议：
- Draft/Review 使用低成本模型
- Edit/Gate 关键阶段使用高质量模型

## 验收清单

- [ ] 能成功完成单阶段 run（PRD）
- [ ] 能成功完成三阶段 run（PRD/TECH_SPEC/EXEC_PLAN）
- [ ] 数据库可看到 provider/model/tokens/latency/cost
- [ ] 触发故障时可自动 fallback 并不中断 run
- [ ] `pytest` 与 `build` 通过

## 风险说明

- 若依赖兼容网关行为，存在跨版本差异风险
- 非兼容原生插件维护成本更高，建议优先兼容协议接入
