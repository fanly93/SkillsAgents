# 后续 Spec Kit 输入草稿

下面内容可作为后续手动运行 Spec Kit CLI 时的需求输入草稿。它不是正式 Spec Kit 文档，只是把本阶段调研结论整理成可复制的需求描述。

## Feature Description Draft

构建一个基于 Python/FastAPI、LangChain/LangGraph 的智能客服 agents API 服务。系统需要支持自动加载目录型 skills，并根据每个 skill 中的 `SKILL.md` 指导完成客服任务。skills 采用标准目录结构：必需 `SKILL.md`，可选 `references/`、`scripts/`、`assets/`。系统需要按需发现、选择、激活 skill，不应一次性把所有 skill 内容注入模型上下文。`scripts/` 默认不可执行，必须通过沙箱白名单和权限策略授权。

系统需要支持短期记忆和长期记忆。短期记忆按 `session_id` 保存为 JSON 文件，用于会话内多轮上下文恢复。长期记忆必须通过可插拔 `LongTermMemoryProvider` 接口接入，默认实现可使用 Mem0，但不能强绑定 Mem0；用户应能自定义长期记忆方案。未来可扩展 LangGraph Store、LangMem、Zep/Graphiti、Cognee、Supermemory 或其他 provider。

系统需要支持任务追踪。Agent 在处理用户请求时能够规划任务并生成 Markdown 任务文档。任务文档按 `session_id` 保存，任务状态使用 `[ ]` 表示未完成，`[x]` 表示完成，`[✗]` 表示失败。每完成或失败一项任务，系统更新任务文档并记录审计日志。

系统 v1 形态为 API 服务，不要求完整客服坐席前端。v1 客服能力包括知识库问答、skill 指导、短期/长期记忆、任务追踪、人工转接、基础鉴权、租户隔离、审计日志、基础安全护栏、可观测性和离线评测。v1 不执行退款、改订单、改地址等高风险业务写操作；遇到高风险或低置信度场景应转人工。

系统必须采用可插拔架构，核心业务不能直接依赖具体模型、memory provider、RAG 引擎、渠道、观测平台或脚本执行器。建议定义 `ModelProvider`、`AgentRuntimeAdapter`、`ShortTermMemoryStore`、`LongTermMemoryProvider`、`RetrieverProvider`、`SkillSource`、`SkillParser`、`SkillRegistry`、`SkillSelector`、`SkillRuntime`、`TaskTracker`、`HandoffService`、`GuardrailProvider`、`AuditSink`、`TraceProvider`、`ChannelAdapter` 等抽象。

## Suggested User Stories

### US1: 自动加载和使用 skills

作为系统管理员，我希望系统能扫描配置目录中的 skills，读取 `SKILL.md` 元数据，并在用户请求匹配时按需激活对应 skill，以便 agent 能遵循可复用工作流完成客服任务。

Acceptance:

- 给定合法 skill 目录，系统能识别 name、description、version。
- 给定用户请求，系统能选择相关 skill。
- 未激活 skill 时不加载完整正文和资源。
- 脚本默认不可执行。

### US2: 维护会话短期记忆

作为客服系统用户，我希望同一 `session_id` 下的多轮对话能保留上下文，以便不用重复说明问题。

Acceptance:

- 同一 `session_id` 可恢复历史消息和摘要。
- 不同 `session_id` 数据隔离。
- JSON 文件损坏时系统安全降级。

### US3: 接入可插拔长期记忆

作为系统集成方，我希望长期记忆通过统一 provider 接口接入，默认使用 Mem0，但可以替换为自定义方案，以便满足不同部署和合规要求。

Acceptance:

- 业务层只依赖 `LongTermMemoryProvider`。
- Mem0 provider 可作为默认实现。
- provider 不可用时主客服流程可降级。
- 支持按 tenant/user 删除记忆。

### US4: 追踪任务计划

作为客服主管，我希望 agent 处理问题时能生成任务计划并更新完成状态，以便人工客服或开发者审查处理过程。

Acceptance:

- 每个 `session_id` 有对应 Markdown 任务文档。
- 任务可从 `[ ]` 更新为 `[x]` 或 `[✗]`。
- 失败任务记录原因。
- 人工转接时附带任务摘要。

### US5: 生产客服安全与转人工

作为企业管理员，我希望系统能在低置信度、高风险、越权或用户要求人工时转人工，并保留审计记录，以便降低客服自动化风险。

Acceptance:

- 高风险请求不由 agent 自主执行。
- 低置信度回答触发转人工。
- RAG 无依据时不编造。
- 关键事件写审计日志。

## Suggested Functional Requirements

- 系统必须支持扫描多个 skill source。
- 系统必须解析 `SKILL.md` YAML frontmatter 和 Markdown body。
- 系统必须支持 `references/`、`scripts/`、`assets/` 资源清单。
- 系统必须默认禁止执行 skill scripts，除非权限策略允许。
- 系统必须按 `session_id` 保存短期 JSON memory。
- 系统必须提供长期记忆抽象接口。
- 系统必须默认提供 Mem0 长期记忆适配方案。
- 系统必须允许用户自定义长期记忆 provider。
- 系统必须按 `session_id` 生成 Markdown 任务文档。
- 系统必须支持任务状态 `[ ]`、`[x]`、`[✗]`。
- 系统必须支持知识库检索和来源引用。
- 系统必须支持人工转接。
- 系统必须记录 skill、memory、RAG、handoff、guardrail 等审计事件。
- 系统必须支持 tenant/user/session 上下文隔离。
- 系统必须支持基础安全护栏和 PII 脱敏策略。

## Suggested Non-Goals

- v1 不实现完整客服坐席 UI。
- v1 不做自动退款、改订单、改地址等业务写操作。
- v1 不强绑定 Mem0、Zep、Cognee 或任何单一 provider。
- v1 不要求全渠道接入。
- v1 不自研长期记忆框架。

## Suggested Success Criteria

- 系统能加载至少 5 个标准 skill 目录并正确选择相关 skill。
- 同一 `session_id` 的多轮会话能恢复上下文。
- 长期记忆 provider 可从默认 Mem0 替换为自定义实现而不改业务逻辑。
- 每次客服任务都能生成和更新 Markdown checklist。
- 高风险写操作请求能被拒绝或转人工。
- RAG 无依据时不编造答案。
- 关键操作均有审计事件。

## Suggested Architecture Defaults

- Language: Python 3.11+。
- API: FastAPI。
- Agent runtime: LangGraph。
- Agent/tool ecosystem: LangChain。
- Short-term memory: JSON file store。
- Long-term memory: provider interface with Mem0 default.
- Skills format: Agent Skills compatible directory structure。
- Task tracking: Markdown file store。
- Observability: OpenTelemetry abstraction; LangSmith/Langfuse optional。
- Security baseline: OWASP LLM Top 10 and OWASP API Top 10。
