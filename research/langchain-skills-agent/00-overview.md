# LangChain Skills Agent 客服系统调研总览

## 1. 调研背景

本调研面向一个基于 LangChain/LangGraph 的智能客服 agents 系统。系统需要自动加载目录型 skills，根据 `SKILL.md` 中的指导完成任务，并支持短期记忆、长期记忆、任务追踪、人工转接和生产级客服能力。

本阶段只做调研与文档产出，不实现代码、不安装依赖、不生成正式 Spec Kit 文档。后续正式 `spec.md`、`plan.md`、`tasks.md` 可由 Spec Kit CLI 基于这些调研文档手动生成。

## 2. 核心目标

- 支持标准目录型 skills：`SKILL.md`、`references/`、`scripts/`、`assets/`。
- 支持按 `session_id` 存储短期会话记忆，v1 默认落 JSON 文件。
- 支持可插拔长期记忆 provider，默认推荐 Mem0，但不强绑定 Mem0。
- 支持任务规划与任务追踪，用 Markdown checklist 表示任务状态。
- 支持企业 MVP 级客服能力，包括知识库、人工转接、审计、安全护栏、观测和评测。
- 所有核心组件采用可插拔设计，避免绑定某个模型、memory provider、RAG 引擎、渠道、观测平台或脚本执行器。

## 3. 推荐系统形态

v1 推荐采用 API 服务形态：

- `FastAPI` 作为 HTTP API 层。
- `LangGraph` 作为 agent 编排和状态流转骨架。
- `LangChain` 工具生态作为模型、工具、retriever 等集成层。
- `Skill Loader` 负责发现、解析、选择和激活 skills。
- `Memory Layer` 分为短期记忆和长期记忆。
- `Task Tracker` 按会话生成 Markdown 任务文档。
- `Human Handoff` 作为一等能力，不把转人工当作异常补丁。

## 4. 可插拔架构原则

业务层不直接依赖具体 SDK，而依赖稳定抽象接口。

建议抽象包括：

- `ModelProvider`：模型调用 provider，可接 OpenAI、Anthropic、Gemini、本地模型等。
- `AgentRuntime`：agent 编排运行时，默认 LangGraph，可扩展其他框架。
- `LongTermMemoryProvider`：长期记忆 provider，默认 Mem0，可扩展 LangMem、Zep、Graphiti、Cognee、Supermemory、自定义实现。
- `ShortTermMemoryStore`：短期记忆存储，默认 JSON，后续可替换 Redis、Postgres。
- `RetrieverProvider`：知识库/RAG 检索 provider，可替换向量库、全文检索、混合检索和 reranker。
- `SkillSource`、`SkillParser`、`SkillRegistry`、`SkillSelector`、`SkillRuntime`：skills 子系统的可替换组件。
- `TaskStore`：任务追踪存储，默认 Markdown 文件，后续可替换数据库或工单系统。
- `AuditSink`：审计日志输出，可写文件、数据库、SIEM。
- `TraceProvider`：观测和 tracing，可接 OpenTelemetry、LangSmith、Langfuse 等。
- `GuardrailProvider`：输入输出安全和策略控制。
- `ChannelAdapter`：Web、REST、Slack、Teams、企业微信、Zendesk 等渠道适配。

## 5. v1 推荐范围

建议 v1 做“可上线内测的企业客服 API MVP”，不要一开始做全渠道、全自动业务执行。

v1 包含：

- API 服务。
- 单渠道或 REST/Web Chat 接入。
- LangGraph agent orchestrator。
- 可插拔 provider 架构。
- 短期 JSON session memory。
- 长期 memory provider 抽象，默认 Mem0。
- skills 自动加载与安全激活。
- 知识库问答、引用来源、低置信度转人工。
- Markdown 任务追踪。
- 基础鉴权、租户隔离、审计日志。
- 基础安全护栏和 PII 脱敏策略。
- 基础 tracing、指标、离线评测。

v1 不建议包含：

- 自动退款、改订单、改账号权限等写操作。
- 完整客服坐席前端。
- 全渠道接入。
- 复杂多 agent 协作。
- 自研长期记忆框架。
- 无人工审核的高风险业务执行。

## 6. 文档清单

- `01-memory-frameworks.md`：长期记忆框架调研和选型。
- `02-skills-loading-design.md`：skills 自动加载和运行时安全设计。
- `03-agent-architecture.md`：系统架构和可插拔组件边界。
- `04-task-tracking.md`：短期记忆和任务追踪文档设计。
- `05-production-customer-service.md`：生产客服系统能力清单。
- `06-technology-decisions.md`：技术决策与推荐路线。
- `07-speckit-input-draft.md`：后续可喂给 Spec Kit CLI 的需求草稿。

## 7. 关键来源

- LangGraph Memory: https://docs.langchain.com/oss/python/langgraph/add-memory
- LangMem GitHub: https://github.com/langchain-ai/langmem
- Mem0 OSS: https://docs.mem0.ai/open-source/overview
- Agent Skills Specification: https://agentskills.io/specification
- Claude Skills: https://claude.com/docs/skills/how-to
- OpenAI Skills in ChatGPT: https://help.openai.com/en/articles/20001066-skills-in-chatgpt
- OWASP Top 10 for LLM Applications: https://owasp.org/www-project-top-10-for-large-language-model-applications/
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
