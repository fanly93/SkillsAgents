# Phase 0 Research: Skills Agent Runnable MVP

## Decision: Use Python 3.11+ for the MVP service

**Rationale**: Python has the strongest first-party ecosystem fit for the selected agent stack, including FastAPI, LangGraph, LangChain, Pydantic, and pytest. Python 3.11+ gives modern typing and runtime performance suitable for the MVP.

**Alternatives considered**:

- Node.js/TypeScript: strong API ecosystem, but weaker alignment with the current LangGraph/LangChain Python-first planning direction.
- Go: good service runtime, but higher friction for LangChain/LangGraph agent orchestration.

## Decision: Use FastAPI as the REST service boundary

**Rationale**: FastAPI provides a productive REST application model, request/response validation through Python type hints, OpenAPI generation, and testing support suitable for contract-driven MVP verification.

**Alternatives considered**:

- Flask: simpler but less aligned with typed request/response contracts and automatic OpenAPI generation.
- Django: powerful but too heavy for a focused agent service MVP.

**Reference**: https://fastapi.tiangolo.com/

## Decision: Use Pydantic v2 for contracts and data validation

**Rationale**: The MVP has many structured artifacts: tenant context, session state, skill metadata, task items, audit events, retrieval results, and handoff payloads. Pydantic supports validation and JSON serialization, which keeps service contracts explicit.

**Alternatives considered**:

- Dataclasses only: lower dependency surface, but more custom validation and serialization work.
- Ad hoc dictionaries: fastest initially, but conflicts with the constitution's testability and boundary requirements.

**Reference**: https://docs.pydantic.dev/latest/

## Decision: Default runtime is LangGraph behind `AgentRuntimeAdapter`

**Rationale**: LangGraph supports stateful agent workflows, memory/checkpoint concepts, and graph-based orchestration. The official documentation separates short-term memory from long-term memory, matching this project boundary. The concrete LangGraph runtime must remain behind `AgentRuntimeAdapter`.

**Alternatives considered**:

- Direct LangChain ReAct flow: simpler, but weaker for explicit state and workflow control.
- Custom runtime: maximum control, but unnecessary for MVP and higher risk.
- Letta-style complete runtime: interesting later, but too likely to take over the architecture in the MVP.

**Reference**: https://docs.langchain.com/oss/python/langgraph/add-memory

## Decision: Use LangChain model abstractions behind `ModelProvider`

**Rationale**: LangChain model abstractions provide a common integration surface for chat models and tool-calling behavior. The MVP still requires a `ModelProvider` boundary so business code can run with either a real OpenAI-compatible provider or `MockModelProvider`.

**Alternatives considered**:

- Direct provider SDK integration: faster for one model, but violates the pluggable architecture principle.
- Mock-only model behavior: deterministic, but insufficient for later real-agent validation.

**Reference**: https://docs.langchain.com/oss/python/langchain-models

## Decision: Use local filesystem storage for MVP tenant artifacts

**Rationale**: The MVP must be inspectable, deterministic, and easy to validate. Local files under `data/tenants/{tenant_id}/...` make sessions, tasks, memory, knowledge, audit, and handoff artifacts visible to reviewers while proving tenant separation.

**Alternatives considered**:

- SQLite: good local persistence, but less directly inspectable for Markdown task tracking and JSON artifact review.
- Redis/Postgres: more production-like, but unnecessary infrastructure for MVP.

**Implementation constraints**:

- All path resolution must be rooted under the tenant's data directory.
- JSON writes must be atomic.
- Corrupt session/task files must be preserved for inspection and replaced with recoverable state.

## Decision: Use local JSON fallback for long-term memory

**Rationale**: The feature specification requires deterministic operation without external services. A tenant-user JSON store proves the `LongTermMemoryProvider` contract and keeps Mem0/Zep/Cognee/Supermemory integration as later provider work.

**Alternatives considered**:

- Mem0 as default in MVP: closer to future product direction, but adds external configuration and provider semantics too early.
- LangGraph Store as the only memory layer: useful later, but would blur project-owned provider contracts.

## Decision: Use local Markdown/TXT keyword retrieval for MVP knowledge

**Rationale**: The MVP needs tenant-specific source references without taking on vector storage, embeddings, reranking, indexing lifecycle, or knowledge ingestion pipelines. Keyword retrieval is sufficient to verify tenant knowledge separation and source-bearing responses.

**Alternatives considered**:

- Vector database retrieval: too much setup and provider dependency for MVP.
- No retrieval: simpler, but would weaken the customer-service demonstration and source reference requirements.

## Decision: Use explicit selector plus keyword selector for MVP skills

**Rationale**: Explicit skill selection makes tests deterministic. Keyword selection against skill metadata proves tenant-local automatic matching without requiring embeddings or LLM selection. The `SkillSelector` interface leaves room for future `EmbeddingSelector`, `LLMSelector`, `PolicySelector`, and `CompositeSelector`.

**Alternatives considered**:

- LLM skill selector: more agent-like, but harder to test deterministically.
- Embedding selector: useful later, but unnecessary for two sample tenants and metadata-based selection.

## Decision: Treat scripts as denied by default and run only through a controlled executor

**Rationale**: Skill scripts are useful for domain tasks, but they are also a high-risk execution boundary. The MVP should prove `PermissionPolicy` and `ScriptExecutor` contracts with deny/allow paths, without claiming production sandbox strength.

**Alternatives considered**:

- No script execution at all: safer, but does not validate the future script-capable skill model.
- Full container sandbox: safer for production, but over-scoped for MVP.

## Decision: Use rule-based guardrails and Human-in-the-loop payloads

**Rationale**: The MVP must consistently block high-risk business actions without relying on a model classifier. Rules can cover refunds, order changes, address changes, account permission changes, prompt-injection indicators, sensitive information handling, and cross-tenant access attempts.

**Alternatives considered**:

- Model-based safety classification: potentially richer, but non-deterministic and requires external credentials.
- No guardrail implementation: violates the constitution and feature specification.

## Decision: Use JSONL audit events for MVP

**Rationale**: JSONL is append-friendly, easy to inspect, and simple to test. It supports the MVP requirement to audit chat turns, skill activation, script decisions, memory access, task updates, retrieval, guardrail decisions, and handoff payload generation.

**Alternatives considered**:

- Database audit store: better queryability, but unnecessary for MVP.
- Plain text logs: human-readable, but harder to validate structurally.

## Decision: Use pytest with temporary tenant data fixtures

**Rationale**: pytest fixtures and temporary directories support deterministic tests of local state, tenant isolation, and artifact generation without polluting the repository. Contract tests can validate OpenAPI behavior; integration tests can cover end-to-end sample flows.

**Alternatives considered**:

- Manual-only testing: insufficient for constitution requirements.
- External service integration tests by default: too brittle for MVP.

**Reference**: https://docs.pytest.org/

## Resolved Clarifications

All planning questions are resolved. The feature scope is constrained by the approved specification and constitution:

- REST API MVP only.
- Two sample tenants.
- Local skill sources and local knowledge only.
- Deterministic mock provider required.
- Real model provider optional/configurable.
- High-risk actions always enter Human-in-the-loop; no irreversible business action execution.
