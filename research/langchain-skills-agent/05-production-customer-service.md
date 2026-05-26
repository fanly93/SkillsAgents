# 生产可用智能客服 Agents 能力调研

## 1. 结论摘要

生产客服 agent 系统不只是“能聊天”。它需要完整的 API、安全、知识库、人工转接、审计、观测、评测、合规和降级能力。v1 建议做企业 MVP：能真实试点，但不执行高风险写操作。

核心原则：

- 默认多租户安全。
- 默认可审计。
- 默认可降级。
- 默认可转人工。
- 默认不让 agent 自主执行高风险业务操作。

## 2. API 服务能力

v1 API 应至少包括：

- `POST /v1/sessions`：创建会话，返回 `session_id`。
- `POST /v1/chat`：发送用户消息，返回 agent 回复、引用来源、任务状态、是否转人工。
- `GET /v1/sessions/{session_id}`：查询会话摘要。
- `GET /v1/tasks/{session_id}`：查询任务追踪 Markdown。
- `GET /v1/skills`：列出可用 skills。
- `POST /v1/handoff`：触发人工转接。
- `GET /v1/health`：健康检查。

生产要求：

- API versioning。
- 幂等请求 ID。
- 流式响应 SSE/WebSocket。
- 超时、重试、限流。
- tenant/user/session 三层上下文。
- 请求与响应 schema 校验。
- 后台异步任务队列。

来源：

- https://owasp.org/www-project-api-security/

## 3. 知识库与 RAG

客服 RAG 不是简单向量搜索，需要知识生命周期管理。

必备能力：

- 文档导入：FAQ、产品文档、政策文档、工单历史、网页、PDF。
- 文档清洗：去噪、结构化、分段、元数据提取。
- 检索策略：关键词、向量、混合检索、reranking。
- 权限过滤：检索前和检索后都校验 ACL。
- 来源引用：回答带来源，便于确认。
- 版本管理：知识变更可追踪、回滚、重新索引。
- 过期处理：政策、价格、活动信息必须有有效期。
- 低置信度处理：检索不到或冲突时转人工。

风险：

- 未做权限过滤会导致跨租户数据泄露。
- RAG 文档可能包含 prompt injection。
- 检索结果不等于可靠答案。
- 过期文档会导致客服误答。

参考：

- https://www.pinecone.io/learn/retrieval-augmented-generation/
- https://www.pinecone.io/learn/rag-access-control/

## 4. 人工转接

人工转接必须是一等能力。

触发条件：

- 用户明确要求人工。
- 模型低置信度。
- 检索结果不足或冲突。
- 涉及退款、投诉、法务、医疗、金融、高风险业务。
- 用户情绪强烈。
- 安全护栏拦截。
- 多轮无法解决。
- 工具或 skill 调用失败超过阈值。

handoff payload：

- 用户身份和租户。
- 会话摘要。
- 用户原始诉求。
- agent 已尝试步骤。
- RAG 引用来源。
- 已完成、失败、待处理任务。
- 风险标签。
- 推荐给人工客服的下一步。

参考：

- https://support.zendesk.com/hc/en-us/articles/4408824482586-Managing-conversation-handoff-and-handback
- https://www.intercom.com/help/en/articles/10032299-use-fin-ai-agent-in-workflows

## 5. 鉴权与租户隔离

企业客服系统必须默认多租户安全。

v1 必备：

- `tenant_id`、`user_id`、`session_id` 全链路传递。
- API key 或 JWT。
- 后续支持 OAuth2/OIDC 和企业 SSO。
- RBAC/ABAC。
- RAG 检索必须带 tenant/user 权限过滤。
- Memory 读写必须隔离 tenant/user。
- Audit log 按租户隔离。
- 管理操作需要更高权限。

重点风险：

- Broken Object Level Authorization。
- 用户通过修改 `session_id` 读取别人会话。
- agent 工具绕过业务权限访问数据。

参考：

- https://owasp.org/www-project-api-security/
- https://owasp.org/blog/2023/07/03/owasp-api-top10-2023

## 6. 审计日志

建议记录：

- 用户输入。
- agent 输出。
- 模型调用参数摘要。
- RAG 检索 query 和命中文档 ID。
- tool/skill 调用。
- script 执行。
- memory 读写。
- 权限判断结果。
- 安全护栏拦截。
- 人工转接。
- 管理员操作。
- 配置变更。

要求：

- append-only。
- 敏感字段脱敏或加密。
- 原始 prompt 是否保存由合规策略决定。
- 设置 retention policy。
- 审计日志和调试 trace 分开。

## 7. 安全护栏

主要风险：

- prompt injection。
- sensitive information disclosure。
- supply chain risk。
- excessive agency。
- insecure plugin/tool design。
- system prompt leakage。
- vector/embedding weakness。
- unbounded consumption。

v1 护栏：

- 输入分类：恶意请求、越权请求、敏感请求、投诉升级。
- 输出过滤：PII、违规承诺、幻觉。
- Tool allowlist。
- 高风险动作 human-in-the-loop。
- RAG 文档作为不可信输入。
- 禁止输出 secret、token、系统 prompt。
- 工具参数 schema 校验。
- 外部 URL、附件、HTML 安全扫描。

参考：

- https://owasp.org/www-project-top-10-for-large-language-model-applications/
- https://www.nist.gov/itl/ai-risk-management-framework
- https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf

## 8. PII 与合规

v1 应具备：

- PII 识别：姓名、电话、邮箱、地址、订单号、证件号等。
- PII 脱敏：日志、trace、评测数据默认脱敏。
- 数据最小化：只保存完成客服任务必要的信息。
- 用户删除：按 user/session 删除会话、memory、任务。
- 数据保留期：不同数据类型不同 retention。
- 第三方模型调用策略记录。
- 敏感行业场景转人工。

参考：

- https://www.nist.gov/privacy-framework
- https://commission.europa.eu/law/law-topic/data-protection/reform/what-does-general-data-protection-regulation-gdpr-govern_en

## 9. 可观测性

建议观测：

- 请求链路 trace。
- LLM 调用。
- tool/skill 调用。
- RAG 检索结果。
- memory recall/write。
- handoff 触发原因。
- token、成本、延迟。
- 安全拦截率。
- 用户满意度。
- 人工转接率。
- 首次解决率。

推荐：

- OpenTelemetry 作为通用标准。
- LangSmith 或 Langfuse 做 LLM trace/eval。
- Prometheus/Grafana 做系统指标。
- 结构化 JSON 日志。

参考：

- https://opentelemetry.io/docs/
- https://docs.langchain.com/langsmith/observability-concepts
- https://docs.langchain.com/langsmith/evaluation
- https://langfuse.com/docs

## 10. 评测体系

v1 评测集：

- 常见 FAQ。
- 复杂多轮问题。
- 低置信度问题。
- 需要转人工的问题。
- 敏感/越权问题。
- RAG 文档冲突问题。
- prompt injection 样例。
- 跨租户数据泄露样例。

指标：

- 回答准确率。
- groundedness / faithfulness。
- 引用来源正确率。
- 拒答正确率。
- 转人工正确率。
- 工具调用成功率。
- 任务完成率。
- PII 泄露率。
- 平均延迟和成本。

工具：

- LangSmith。
- Langfuse。
- Promptfoo。
- DeepEval/RAGAS。

参考：

- https://docs.langchain.com/langsmith/evaluation
- https://www.promptfoo.dev/docs/intro/
- https://deepeval.com/docs/metrics-introduction
- https://arxiv.org/abs/2309.15217

## 11. 降级与失败处理

常见失败：

- LLM 超时。
- RAG 无结果。
- RAG 多来源冲突。
- tool/skill 调用失败。
- memory provider 不可用。
- 安全护栏拦截。
- 第三方渠道 webhook 重试。
- 用户请求超过权限。
- 模型成本或速率限制触发。

推荐策略：

- 超时后给出简短说明并转人工。
- RAG 无结果时不编造。
- 高风险工具失败后停止重试并记录。
- memory provider 失败不阻断主流程。
- LLM provider 支持 fallback。
- 渠道消息发送失败进入重试队列。
- 所有失败写入任务追踪和审计日志。

## 12. 渠道接入

不要让 agent 直接依赖某个渠道 SDK。应设计 `ChannelAdapter`。

v1 推荐：

- REST API。
- Web Chat。
- 企业内部测试渠道可选 Slack/Teams。

后续：

- Email。
- WhatsApp/Twilio。
- 企业微信。
- 飞书。
- Zendesk/Intercom/Salesforce Service Cloud。

ChannelAdapter 负责：

- 消息格式归一化。
- 用户身份映射。
- 附件处理。
- 渠道限制处理。
- webhook 签名校验。
- 消息幂等。
- 发送失败重试。
- 人工客服系统对接。
