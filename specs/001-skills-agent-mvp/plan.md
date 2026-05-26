# Implementation Plan: Skills Agent Runnable MVP

**Branch**: `001-skills-agent-mvp` | **Date**: 2026-05-25 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-skills-agent-mvp/spec.md`

**Note**: This plan is the Spec Kit planning artifact for the runnable MVP. The upstream Superpowers brainstorming document remains reference-only.

## Summary

Build the first runnable MVP of the SkillsAgents platform: a tenant-aware customer-service agent service where the same general agent can load different tenant skills, preserve session and task state, retrieve tenant-local knowledge, audit critical actions, and route high-risk requests into Human-in-the-loop review.

The MVP uses a platform-spine approach: define stable provider and adapter boundaries, then implement local/default providers sufficient to demonstrate and test the complete flow. The feature is intentionally REST API only, with no frontend, no live support-desk integration, no remote skill registry, no streaming chat, and no irreversible business actions.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI for REST service; Pydantic v2 for schemas and validation; `AgentRuntimeAdapter` as the runtime boundary; LangGraph as the default target runtime for a later adapter; LangChain model abstractions for real provider integration; PyYAML or equivalent YAML parser for configuration; pytest and FastAPI TestClient/httpx for automated verification.

**Storage**: Local filesystem for MVP artifacts under `data/tenants/{tenant_id}/...`; JSON for sessions, long-term memory fallback, handoff payloads, and audit JSONL; Markdown for task checklists and sample knowledge files.

**Testing**: pytest with unit, contract, and integration tests. Tests must support deterministic local execution without external LLM credentials through `MockModelProvider`.

**Target Platform**: Local developer machine and generic Linux-compatible service runtime.

**Project Type**: REST API service with internal provider/adapter modules and sample tenant fixtures.

**Performance Goals**: Primary scripted two-tenant demo completes in under 10 minutes; local API calls for primary flows should feel interactive for reviewers; no production throughput target in MVP.

**Constraints**: REST only; no frontend; no SSE/WebSocket; no production auth/RBAC; no remote skill registry; no vector database; no irreversible business actions; scripts default deny; all tenant resources must remain isolated.

**Scale/Scope**: Two sample tenants (`fashion_store`, `electronics_store`); multiple local skill sources per tenant; enough sample skills and knowledge to demonstrate tenant-specific answers, task tracking, audit, local memory, local retrieval, script authorization denial, and Human-in-the-loop payload generation.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Spec Kit source of truth**: PASS. This plan is driven by [spec.md](./spec.md). The Superpowers brainstorming document at `docs/superpowers/specs/2026-05-25-skills-agent-mvp-brainstorming.md` is reference-only and is not treated as the formal specification.
- **Pluggable architecture**: PASS. The plan requires explicit boundaries for `ModelProvider`, `AgentRuntimeAdapter`, `SkillParser`, `SkillRegistry`, `SkillSelector`, `SkillActivationService`, `ResourceResolver`, `ScriptExecutor`, `PermissionPolicy`, `ShortTermMemoryStore`, `LongTermMemoryProvider`, `RetrieverProvider`, `TaskTracker`, `GuardrailProvider`, `HandoffService`, and `AuditSink`.
- **Tenant isolation**: PASS. All persisted artifacts and service operations are scoped by `tenant_id` and, where applicable, `user_id` and `session_id`. Tenant A cannot list, select, retrieve, read, or mutate tenant B resources.
- **Skills as domain boundaries**: PASS. Skills are tenant-scoped packages. `SKILL.md` can guide behavior but cannot override system, safety, tenant, permission, or governance policies. References/assets are read through controlled resource access; scripts require explicit policy authorization.
- **Runnable, auditable, testable MVP**: PASS. The plan includes REST verification paths, mock provider coverage, audit JSONL for critical operations, rule-based guardrails, and Human-in-the-loop payload generation.

Post-design re-check: PASS. Phase 1 design artifacts preserve the same boundaries through the data model, OpenAPI contract, and quickstart validation flow.

## Project Structure

### Documentation (this feature)

```text
specs/001-skills-agent-mvp/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── openapi.yaml
├── checklists/
│   └── requirements.md
└── tasks.md              # Created later by /speckit-tasks
```

### Source Code (repository root)

```text
src/
├── skills_agents/
│   ├── api/
│   │   ├── app.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── core/
│   │   ├── context.py
│   │   └── orchestrator.py
│   ├── models/
│   │   └── mock_provider.py
│   ├── skills/
│   │   ├── parser.py
│   │   ├── registry.py
│   │   ├── selector.py
│   │   ├── activation.py
│   │   └── resources.py
│   ├── memory/
│   │   ├── short_term.py
│   │   └── long_term.py
│   ├── retrieval/
│   │   └── local_documents.py
│   ├── tasks/
│   │   └── tracker.py
│   ├── scripts/
│   │   ├── executor.py
│   │   └── permissions.py
│   ├── safety/
│   │   └── guardrails.py
│   ├── handoff/
│   │   └── service.py
│   ├── audit/
│   │   └── jsonl.py
│   └── storage/
│       ├── paths.py
│       └── atomic.py
├── examples/
│   ├── config/
│   │   └── tenants.yaml
│   ├── skills/
│   │   ├── common/
│   │   ├── tenants/fashion_store/
│   │   └── tenants/electronics_store/
│   └── data/
│       └── tenants/
└── tests/
    ├── contract/
    ├── integration/
    └── unit/
```

**Structure Decision**: Use a single Python service package under `src/skills_agents` with explicit subpackages for each MVP provider/adapter boundary. Keep sample tenants and skills under `examples/` so MVP behavior is demonstrable without mixing fixtures into core code. Use `tests/contract`, `tests/integration`, and `tests/unit` to mirror the specification's verification needs. Future extensions may add concrete LangGraph runtime adapters, OpenAI-compatible providers, remote skill sources, and richer configuration providers behind the existing interfaces.

## Phase 0: Research

Research output: [research.md](./research.md)

Phase 0 resolves technical context choices and confirms the MVP can be implemented without unresolved clarifications. Key outcomes:

- Keep Python/FastAPI/LangGraph/LangChain as defaults while hiding concrete dependencies behind project interfaces.
- Use local filesystem stores for MVP state with atomic writes and tenant path containment.
- Use deterministic mock provider as a first-class verification path.
- Use local Markdown/TXT retrieval for MVP knowledge grounding.
- Treat scripts as denied by default and executable only through policy-controlled paths.

## Phase 1: Design and Contracts

Design outputs:

- [data-model.md](./data-model.md)
- [contracts/openapi.yaml](./contracts/openapi.yaml)
- [quickstart.md](./quickstart.md)

The design defines tenant-scoped entities, state transitions for sessions/tasks/handoff, and REST contracts for session creation, chat turns, task retrieval, skill listing/reload, and health checks.

## Complexity Tracking

No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
