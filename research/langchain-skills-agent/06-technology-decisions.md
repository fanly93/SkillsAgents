# 技术决策建议

## 1. 总体技术路线

推荐 v1 技术路线：

- API 服务：FastAPI。
- Agent 编排：LangGraph。
- 工具和模型生态：LangChain。
- 短期记忆：`session_id` -> JSON 文件。
- 长期记忆：`LongTermMemoryProvider` 抽象，默认 Mem0。
- Skills：兼容 Agent Skills 目录结构，支持 `SKILL.md`、`references/`、`scripts/`、`assets/`。
- 任务追踪：`session_id` -> Markdown 文件。
- RAG：`RetrieverProvider` 抽象，默认可先接简单文档检索，后续接向量库、BM25、reranker。
- 观测：OpenTelemetry 抽象，LangSmith/Langfuse 可选。
- 安全：OWASP LLM Top 10 + OWASP API Top 10 作为基线。

## 2. 决策：采用可插拔组件架构

Decision:

系统核心模块全部依赖抽象接口，不直接绑定具体第三方服务。

Rationale:

- 用户明确要求各组件可插拔。
- 长期记忆虽然默认 Mem0，但需要允许自定义 memory provider。
- 生产系统通常会根据合规、成本、性能和部署环境切换 provider。

Implications:

- 需要在规划阶段定义清晰 provider interface。
- 文档和后续实现中要避免把 Mem0、LangGraph store、Zep 等内部字段泄漏到业务层。
- 默认实现可以存在，但不能成为唯一实现。

## 3. 决策：LangGraph 作为默认 agent runtime

Decision:

v1 默认使用 LangGraph 编排客服 agent 流程。

Rationale:

- LangGraph 支持状态图、工具调用、checkpointer、store。
- 与 LangChain 生态集成自然。
- 官方 memory 文档区分短期和长期记忆，适合本项目分层。

Alternatives:

- 纯 LangChain ReAct agent：简单，但复杂状态和流程控制较弱。
- Letta：stateful agent 能力强，但容易接管整体 runtime。
- 自研 orchestration：可控但成本高。

来源：

- https://docs.langchain.com/oss/python/langgraph/add-memory

## 4. 决策：短期记忆 v1 使用 JSON

Decision:

短期记忆按 `session_id` 保存为 JSON 文件。

Rationale:

- 用户明确提出短期记忆可通过 `session_id` 保存到 JSON。
- v1 便于调试和观察。
- 可通过 `ShortTermMemoryStore` 后续替换为 Redis/Postgres/LangGraph checkpointer。

Risks:

- 并发写需要原子写。
- 大规模生产不适合长期使用文件存储。
- JSON 损坏需要恢复策略。

## 5. 决策：长期记忆默认 Mem0，但不强绑定

Decision:

定义 `LongTermMemoryProvider`，默认实现为 Mem0，同时提供自定义 provider 插槽。

Rationale:

- Mem0 OSS 支持自托管、Python/Node SDK、REST server，适合快速落地。
- Mem0 的 add/search 语义接近通用长期记忆接口。
- 用户明确要求不强制绑定 Mem0。

Alternatives:

- LangGraph Store：适合作 fallback，但不是完整智能记忆产品。
- LangMem：适合作 memory manager，不一定是 provider。
- Zep/Graphiti：更适合时间图谱。
- Cognee：更适合企业知识图谱和知识库。
- Letta：更适合完整 stateful agent runtime。

来源：

- https://docs.mem0.ai/open-source/overview
- https://github.com/langchain-ai/langmem
- https://help.getzep.com/docs
- https://docs.cognee.ai/getting-started/introduction
- https://docs.letta.com/guides/core-concepts/stateful-agents

## 6. 决策：Skills 兼容 Agent Skills 规范

Decision:

skills 目录兼容 Agent Skills 规范：

```text
skill-name/
├── SKILL.md
├── references/
├── scripts/
└── assets/
```

Rationale:

- Agent Skills 已形成跨 Claude/OpenAI/Codex 等工具的事实标准趋势。
- `SKILL.md` frontmatter + Markdown instructions 易读、可审计、可迁移。
- progressive loading 可减少上下文污染。

Risks:

- 第三方 skill 可能带来供应链风险。
- scripts 执行风险高，必须默认禁用或白名单沙箱。

来源：

- https://agentskills.io/specification
- https://claude.com/docs/skills/how-to
- https://help.openai.com/en/articles/20001066-skills-in-chatgpt

## 7. 决策：脚本执行默认沙箱白名单

Decision:

`scripts/` 默认不可执行，只有通过 `PermissionPolicy` 授权后才由 `ScriptExecutor` 执行。

Rationale:

- 客服系统处理敏感数据，任意脚本执行风险极高。
- OWASP LLM 风险中包含 insecure plugin/tool design、excessive agency、supply chain 等风险。
- skill 声明只能作为权限请求，不能作为授权依据。

Minimum policy:

- 默认无网络。
- 默认无 secrets。
- 只读 skill 目录。
- 超时和资源限制。
- 参数 schema 校验。
- 审计记录。

## 8. 决策：任务追踪使用 Markdown，但保留结构化接口

Decision:

v1 任务追踪按 `session_id` 生成 Markdown checklist。

Rationale:

- 用户明确要求 Markdown 文档和 `[ ]` 状态更新。
- Markdown 便于人工客服、开发者和后续 Spec Kit 读取。
- 后续可增加结构化 JSON 存储并渲染 Markdown。

状态：

- `[ ]` 未完成。
- `[x]` 完成。
- `[✗]` 失败。

## 9. 决策：生产客服 v1 不做高风险写操作

Decision:

v1 只做知识库问答、skill 指导、任务追踪、人工转接，不做退款、改地址、改订单等写操作。

Rationale:

- 高风险写操作需要审批、幂等、风控、回滚和更强审计。
- 企业 MVP 应先验证 agent 能否稳定解决问题和正确转人工。
- 降低 prompt injection 和 excessive agency 风险。

## 10. 后续可扩展路线

阶段 1：

- API 服务。
- Skills loader。
- JSON short-term memory。
- Mem0 long-term memory provider。
- Markdown task tracker。
- Basic RAG。
- Human handoff。

阶段 2：

- Redis/Postgres short-term memory。
- LangMem memory manager。
- LangSmith/Langfuse online eval。
- 更完整 RAG pipeline。
- 多渠道 adapter。

阶段 3：

- Zep/Graphiti temporal graph memory。
- Cognee enterprise knowledge memory。
- 高风险动作审批流。
- 完整客服坐席 UI。
- 自动化红队评测。
