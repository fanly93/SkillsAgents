<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- PRINCIPLE_1_NAME -> I. Spec Kit Is the Source of Formal Specification
- PRINCIPLE_2_NAME -> II. Pluggable Architecture First
- PRINCIPLE_3_NAME -> III. Tenant Isolation by Default
- PRINCIPLE_4_NAME -> IV. Skills Define Domain Capability Boundaries
- PRINCIPLE_5_NAME -> V. Runnable, Auditable, Testable MVP
Added sections:
- Additional Constraints
- Development Workflow
Removed sections:
- None
Templates requiring updates:
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/tasks-template.md
- ✅ .specify/templates/checklist-template.md (reviewed; no change required)
- ✅ .specify/extensions/git/commands/*.md (reviewed; no change required)
- ✅ AGENTS.md (already documents Spec Kit and Superpowers responsibility split)
Follow-up TODOs:
- None
-->
# SkillsAgents Constitution

## Core Principles

### I. Spec Kit Is the Source of Formal Specification

Formal project specifications MUST be created and maintained by Spec Kit. Superpowers
brainstorming documents, research notes, and design drafts MAY be used as upstream
inputs, but they MUST NOT become the authoritative `spec.md`, `plan.md`, or `tasks.md`.
All implementation work MUST trace back to the current Spec Kit artifacts.

Rationale: The project intentionally combines Superpowers for exploration and execution
with Spec Kit for durable specification governance. Keeping a single formal source of
truth prevents drift between brainstorming output and implementation requirements.

### II. Pluggable Architecture First

Core business logic MUST depend on stable provider and adapter abstractions rather than
concrete implementations. Model providers, agent runtimes, memory providers, retrievers,
skill sources, script executors, audit sinks, guardrails, handoff services, and
configuration stores MUST be replaceable without rewriting unrelated business flows.
Default implementations MAY exist for the MVP, but provider-specific fields MUST NOT
leak into the platform contracts.

Rationale: The system is a general agent platform, not a single-provider application.
The MVP uses local/default providers to run, while preserving future replacement with
Mem0, Zep, Cognee, vector search, remote skill registries, production sandboxes, or
other services.

### III. Tenant Isolation by Default

Every user-facing and provider-facing operation MUST carry explicit `tenant_id`,
`user_id`, and `session_id` context where applicable. Skills, sessions, tasks, memory,
knowledge, audit events, handoff payloads, and configuration MUST be isolated by tenant.
Feature designs MUST show how tenant A is prevented from reading, selecting, or mutating
tenant B resources.

Rationale: The product goal is a common agent foundation that becomes merchant-specific
through tenant skills and knowledge. Tenant isolation is therefore a platform invariant,
not a later production hardening task.

### IV. Skills Define Domain Capability Boundaries

Skills MUST be treated as first-class domain capability packages. `SKILL.md` provides
instructions and metadata, while `references/`, `assets/`, and `scripts/` are controlled
resources. Skill instructions MUST NOT override system, safety, tenant, governance, or
permission policies. Scripts MUST remain non-executable unless explicitly allowed by
`PermissionPolicy` and run through `ScriptExecutor`.

Rationale: The intended product shape is "general agent + tenant skills = domain expert
agent." That only stays safe if skill content is useful context, not an authority that can
grant itself permissions or bypass platform controls.

### V. Runnable, Auditable, Testable MVP

The MVP MUST be runnable through REST APIs and MUST be verifiable without external LLM
credentials by using `MockModelProvider`. Each feature slice MUST include an API-level or
automated test path. Critical operations MUST write audit events, including chat turns,
skill activation, script execution decisions, memory access, task updates, retrieval,
guardrail decisions, and Human-in-the-loop handoff or approval payloads.

Rationale: The first milestone is not production completeness; it is a stable platform
spine that can be demonstrated, inspected, and tested. Deterministic mock execution and
local audit artifacts make the MVP trustworthy enough for later Spec Kit planning.

## Additional Constraints

- The first implementation target is a REST API MVP. Frontend UI, SSE/WebSocket streaming,
  complete agent desktop, and production customer service integrations are out of scope
  unless a later Spec Kit amendment changes this scope.
- The default technical route is Python 3.11+, FastAPI, LangGraph, and LangChain. These
  choices MUST be hidden behind project interfaces where they touch business behavior.
- MVP configuration MUST use YAML for structured settings and environment variables for
  secrets or deployment-specific values. Real credentials MUST NOT be committed.
- Local state MUST default to `data/tenants/{tenant_id}/...` paths for sessions, tasks,
  memory, knowledge, audit, and handoff artifacts.
- Skill sources MUST support multiple local directories per tenant. Remote skill source
  interfaces MAY be defined, but remote registry sync, authentication, and supply-chain
  governance are out of MVP scope.
- MVP retrieval MUST use a local Markdown/TXT keyword retriever behind `RetrieverProvider`.
  Embeddings, vector databases, rerankers, and Graph RAG are out of MVP scope.
- High-risk business actions MUST enter a Human-in-the-loop decision gate. The MVP MUST
  NOT execute refunds, order modifications, address changes, account permission changes,
  or comparable irreversible actions.
- Rules-based guardrails MUST exist in the MVP for high-risk action detection, prompt
  injection indicators, sensitive information handling, and cross-tenant access attempts.
- Script execution MUST default to deny. Allowed execution MUST use structured inputs and
  outputs, path containment, timeout limits, output limits, no secrets by default, and
  audit logging.

## Development Workflow

- Before `speckit-specify` is used for a new feature, Superpowers `brainstorming` MUST be
  used to produce a Markdown reference document when the feature involves project scope,
  architecture, behavior, or boundary decisions.
- `speckit-specify` output MUST be treated as the formal feature specification. Any
  divergence from brainstorming material MUST be resolved in favor of the Spec Kit
  artifacts or corrected by amending those artifacts.
- `spec.md` MUST include independently testable user stories, explicit MVP boundaries,
  non-goals, tenant isolation expectations, Human-in-the-loop behavior, and measurable
  acceptance criteria.
- `plan.md` MUST include a Constitution Check that verifies all five core principles and
  the Additional Constraints relevant to the feature.
- `tasks.md` MUST include traceable work for tests, tenant isolation, audit events,
  guardrails, handoff or approval payloads, mock provider behavior, and REST API
  integration when those concerns apply to the feature.
- New providers, skill runtimes, script executors, or cross-tenant data paths MUST NOT be
  added without tests or acceptance checks proving their boundaries.
- Reviews MUST block changes that bind business logic directly to provider SDKs, bypass
  tenant context, make scripts executable by default, skip audit for critical events, or
  execute high-risk business actions without Human-in-the-loop controls.

## Governance

This constitution supersedes informal practices, brainstorming notes, and ad hoc
implementation preferences for this repository. Spec Kit artifacts remain the formal
source for feature-level requirements, but those artifacts MUST comply with this
constitution.

Amendments MUST be made by updating `.specify/memory/constitution.md`, documenting the
reason for the change, updating dependent Spec Kit templates when needed, and recording
the version change in the Sync Impact Report. User approval is required for any amendment
that changes a core principle, expands MVP scope, weakens tenant isolation, weakens audit
or safety requirements, or changes Spec Kit/Superpowers responsibility boundaries.

Versioning follows semantic versioning:

- MAJOR: Removes or redefines a core principle in a backward-incompatible way.
- MINOR: Adds a principle or materially expands governance, constraints, or workflow
  requirements.
- PATCH: Clarifies language, fixes wording, or updates non-semantic guidance.

Compliance review is required during `speckit-plan` Constitution Check and again before
implementation is considered complete. Any justified violation MUST be documented in the
plan's Complexity Tracking section with the simpler alternative that was rejected.

**Version**: 1.0.0 | **Ratified**: 2026-05-25 | **Last Amended**: 2026-05-25
