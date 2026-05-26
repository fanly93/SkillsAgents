from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ModelProvider(Protocol):
    def invoke(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


@runtime_checkable
class AgentRuntimeAdapter(Protocol):
    def run_turn(self, context: dict[str, Any], user_message: str) -> dict[str, Any]: ...


@runtime_checkable
class SkillRegistry(Protocol):
    def list(self, tenant_id: str) -> list[dict[str, Any]]: ...


@runtime_checkable
class SkillSelector(Protocol):
    def select(self, tenant_id: str, message: str, skill_name: str | None = None) -> dict[str, Any] | None: ...


@runtime_checkable
class ShortTermMemoryStore(Protocol):
    def load(self, tenant_id: str, session_id: str) -> dict[str, Any] | None: ...
    def save(self, tenant_id: str, session_id: str, state: dict[str, Any]) -> None: ...


@runtime_checkable
class LongTermMemoryProvider(Protocol):
    def add(self, tenant_id: str, user_id: str, content: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]: ...
    def search(self, tenant_id: str, user_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]: ...


@runtime_checkable
class RetrieverProvider(Protocol):
    def retrieve(self, tenant_id: str, query: str, limit: int = 5) -> list[dict[str, Any]]: ...


@runtime_checkable
class TaskTracker(Protocol):
    def get_markdown(self, tenant_id: str, session_id: str) -> str: ...


@runtime_checkable
class GuardrailProvider(Protocol):
    def evaluate(self, tenant_id: str, message: str) -> dict[str, Any]: ...


@runtime_checkable
class HandoffService(Protocol):
    def create_payload(self, tenant_id: str, session_id: str, payload: dict[str, Any]) -> str: ...


@runtime_checkable
class AuditSink(Protocol):
    def write(self, tenant_id: str, event: dict[str, Any]) -> None: ...
