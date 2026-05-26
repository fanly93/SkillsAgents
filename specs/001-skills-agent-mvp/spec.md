# Feature Specification: Skills Agent Runnable MVP

**Feature Branch**: `001-skills-agent-mvp`

**Created**: 2026-05-25

**Status**: Draft

**Input**: User description: "Create the formal Spec Kit specification for the runnable MVP of the SkillsAgents platform, using `docs/superpowers/specs/2026-05-25-skills-agent-mvp-brainstorming.md` as upstream reference material."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tenant-Specific Skills Drive Responses (Priority: P1)

As a platform operator, I want the same general customer-service agent to use different skills for different merchants, so that each merchant can receive domain-specific behavior without building a separate agent.

**Why this priority**: This is the core product promise: general agent foundation plus tenant skills produces merchant-specific expert agents.

**Independent Test**: Configure two sample merchants with different skills and knowledge. Ask both merchants the same customer question and verify that each response uses only that merchant's enabled skills and returns different policy-specific guidance.

**Acceptance Scenarios**:

1. **Given** two configured tenants with distinct skill sets, **When** a user sends the same return-policy question to each tenant, **Then** the system selects a tenant-appropriate skill and produces tenant-specific guidance.
2. **Given** a request explicitly names a valid skill for the tenant, **When** the user sends a message, **Then** explicit skill selection takes precedence over automatic matching.
3. **Given** a request names a skill that belongs to another tenant, **When** the user sends a message, **Then** the system rejects or ignores that skill and does not expose cross-tenant skill details.

---

### User Story 2 - Sessions and Tasks Are Persisted Per Tenant (Priority: P2)

As a developer or operator, I want each conversation to preserve session state and a readable task checklist, so that the agent's work can be resumed, inspected, and handed off.

**Why this priority**: The MVP must prove the session and task-tracking loop, not just one-off chat responses.

**Independent Test**: Create a session, send multiple messages, and verify that the session state, task checklist, and task status updates are stored under the correct tenant and can be retrieved later.

**Acceptance Scenarios**:

1. **Given** a new tenant session, **When** a user sends a message, **Then** the system creates or updates the session state for that tenant and session.
2. **Given** a user request that requires multiple observable steps, **When** the system processes the request, **Then** it creates a task checklist and marks completed or failed steps.
3. **Given** two tenants with sessions using different identifiers, **When** an operator retrieves tasks for one tenant, **Then** tasks from the other tenant are not visible.

---

### User Story 3 - High-Risk Requests Enter Human-in-the-loop (Priority: P3)

As a merchant operator, I want high-risk requests to be blocked from automatic execution and prepared for human review, so that the agent cannot perform unsafe business actions.

**Why this priority**: Safe escalation is required before any customer-service MVP can be trusted, even when it does not yet connect to a real support desk.

**Independent Test**: Ask the agent to directly refund, modify an order, change an address, or change account permissions. Verify that the system does not execute the action and instead returns a human-review state with a payload containing context.

**Acceptance Scenarios**:

1. **Given** a user asks for a direct refund, **When** the system evaluates the request, **Then** it marks the request as high risk and creates a human-review payload instead of executing the refund.
2. **Given** a user asks to change an order address, **When** the system evaluates the request, **Then** it records the risk reason and recommends human follow-up.
3. **Given** a high-risk request occurs after prior conversation turns, **When** the payload is generated, **Then** it includes the relevant session summary, activated skills, task status, sources, and risk tags.

---

### User Story 4 - MVP Is Demonstrable Without External Credentials (Priority: P4)

As a contributor, I want the MVP to run in a deterministic local mode without external model credentials, so that the core flows can be tested and reviewed consistently.

**Why this priority**: The specification must support reliable local validation and continuous verification before production providers are configured.

**Independent Test**: Run the primary user flows without external model credentials and verify that skill selection, session persistence, task tracking, retrieval, guardrails, audit events, and handoff behavior still complete.

**Acceptance Scenarios**:

1. **Given** no external model credentials are configured, **When** the sample tenant flows are executed, **Then** the system returns deterministic responses sufficient to verify the MVP behaviors.
2. **Given** external model credentials are later configured, **When** the same flows are executed, **Then** the core tenant, skill, task, audit, and handoff outcomes remain compatible.

---

### Edge Cases

- A tenant has no enabled skills: the system returns a clear no-skill-available result and records the event.
- A skill has invalid metadata or a missing description: the system excludes it from selection and reports the validation issue.
- Two skills with the same name are enabled for one tenant: the system reports a conflict and requires disambiguation.
- A user attempts to select a skill from another tenant: the system prevents cross-tenant access.
- A session state file or task file is corrupted: the system preserves the damaged artifact for inspection and safely starts a recoverable state.
- The local knowledge base has no relevant match: the system avoids unsupported claims and may recommend human review.
- A script resource exists but is not authorized: the system denies execution and records the decision.
- A high-risk request is phrased indirectly: the system still identifies the risk when it matches configured guardrail rules.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support multiple tenants, each with independently configured skill sources, knowledge sources, session records, task records, memory records, audit records, and human-review payloads.
- **FR-002**: The system MUST scan multiple local skill sources for a tenant and register only valid skill packages that include a `SKILL.md` file.
- **FR-003**: The system MUST record each registered skill's name, description, version when available, source, enabled state, and integrity identifier.
- **FR-004**: The system MUST support explicit skill selection by request when the named skill is enabled for the current tenant.
- **FR-005**: The system MUST support automatic skill selection using tenant-local skill metadata when no explicit skill is requested.
- **FR-006**: The system MUST activate selected skills only on demand and MUST record each activation as an audit event.
- **FR-007**: The system MUST prevent skill instructions from overriding system, safety, tenant, governance, or permission policies.
- **FR-008**: The system MUST expose controlled access to skill references and assets while preventing resource access outside the skill boundary.
- **FR-009**: The MVP MUST deny script execution by default, record a structured script authorization decision, and keep real authorized script execution out of scope until a later Spec Kit feature defines the sandbox and allow policy.
- **FR-010**: The system MUST store short-term session state for each tenant and session, including messages, summary, activated skills, recent sources, risk tags, and handoff state.
- **FR-011**: The system MUST create and update a human-readable task checklist for each tenant session.
- **FR-012**: The system MUST represent task status as not started, completed, or failed and preserve failure reasons when available.
- **FR-013**: The system MUST store lightweight long-term memory per tenant and user for reusable information such as preferences, prior issue summaries, and common intent tags.
- **FR-014**: The system MUST retrieve relevant local knowledge for the current tenant and return source references when matches are used in a response.
- **FR-015**: The system MUST record audit events for session creation, chat turns, skill activation, script authorization decisions, memory access, task updates, retrieval, guardrail decisions, and human-review payload generation.
- **FR-016**: The system MUST identify configured high-risk customer-service requests and route them to Human-in-the-loop review instead of executing the requested action.
- **FR-017**: The system MUST produce a human-review payload for high-risk, low-confidence, user-requested escalation, or failed-tool situations.
- **FR-018**: The system MUST include session summary, relevant messages or summaries, activated skills, task status, sources, risk tags, and recommended human next steps in the human-review payload.
- **FR-019**: The system MUST support deterministic operation without external model credentials for local validation.
- **FR-020**: The system MUST allow a real model provider to be configured later without changing the observable tenant, skill, task, audit, and handoff contracts.
- **FR-021**: The system MUST provide a programmatic service interface for creating sessions, sending chat messages, listing tenant skills, reloading tenant skills, retrieving task checklists, and checking health.
- **FR-022**: The system MUST reject or safely degrade requests that reference unknown tenants, unknown sessions, disabled skills, invalid skills, unauthorized scripts, or missing knowledge.
- **FR-023**: The system MUST include two sample tenants that demonstrate different merchant domains and different behavior for the same customer question.
- **FR-024**: The system MUST keep the MVP scope limited to the documented service interface and sample flows; a customer-service staff UI, live support-desk integration, remote skill registry, streaming chat, and irreversible business actions are out of scope.

### Key Entities *(include if feature involves data)*

- **Tenant**: A merchant or business context that owns its enabled skills, knowledge, sessions, tasks, memory, audit events, and human-review payloads.
- **User**: A customer or operator participating in a tenant-scoped session.
- **Session**: A tenant-scoped conversation record containing messages, summaries, activated skills, recent sources, risk tags, and handoff state.
- **Skill Package**: A tenant-enabled capability package with `SKILL.md` metadata and optional references, assets, and scripts.
- **Skill Registry Entry**: The validated tenant-local record used for listing, selecting, and activating a skill.
- **Task Checklist**: A tenant-session work record that tracks observable steps and their completion or failure state.
- **Long-term Memory Record**: A tenant-user record for reusable information that may improve later conversations.
- **Knowledge Source**: Tenant-local policy or FAQ content that can support grounded customer responses.
- **Audit Event**: An append-only record of critical platform behavior.
- **Human-review Payload**: A context package created when a request requires human judgment or approval.

### Constitution Alignment *(mandatory)*

- **Formal Source**: This `spec.md` is the authoritative feature specification. `docs/superpowers/specs/2026-05-25-skills-agent-mvp-brainstorming.md` is reference-only upstream material.
- **Pluggable Boundaries**: The feature requires replaceable boundaries for model behavior, agent runtime, skill sources and selection, short-term memory, long-term memory, retrieval, script execution, permissions, guardrails, audit, handoff, and configuration.
- **Tenant Isolation**: All user-visible and stored artifacts are scoped by tenant. Selection, retrieval, memory access, task lookup, audit writing, and human-review generation must not cross tenant boundaries.
- **Skill Boundaries**: Skills may guide domain behavior but cannot grant themselves permissions, execute scripts by default, access resources outside their boundary, or override safety and governance rules.
- **Human-in-the-loop**: Refunds, order modification, address changes, account permission changes, cross-tenant access attempts, and comparable high-risk requests are blocked from automatic execution and converted into human-review outcomes.
- **Audit and Testability**: Required audit events cover the critical lifecycle. The MVP must be testable with deterministic local behavior and with sample tenant flows that can be exercised through the service interface.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A reviewer can complete the primary sample flow for two tenants in under 10 minutes using documented service calls.
- **SC-002**: The same customer question asked under the two sample tenants produces tenant-specific skill selection and tenant-specific policy guidance in 100% of scripted demo runs.
- **SC-003**: 100% of scripted high-risk requests produce a human-review outcome and do not execute the requested business action.
- **SC-004**: 100% of scripted tenant-isolation checks prevent tenant A from reading or selecting tenant B resources.
- **SC-005**: 100% of scripted primary flows create or update session state, task checklist, audit events, and, when applicable, human-review payloads.
- **SC-006**: The primary sample flows complete without external model credentials in 100% of local validation runs.
- **SC-007**: At least 90% of expected audit event types are present in the scripted end-to-end run, with any missing event explicitly documented before planning continues.
- **SC-008**: Every priority user story has at least one independent acceptance scenario that can be verified without relying on another story's completion beyond shared setup.

## Assumptions

- The first feature is a runnable MVP, not a production deployment.
- The sample merchant domains are fashion retail and electronics retail.
- Tenant identity, user identity, and session identity are provided by the caller for MVP validation.
- The MVP uses local sample skills and knowledge sources; remote registry and production knowledge ingestion are later features.
- The MVP does not integrate with a real support desk; human-review payloads are sufficient for this phase.
- High-risk actions are detected by configured rules during this phase.
- A deterministic local model mode is acceptable for validating agent behavior when external model credentials are absent.
