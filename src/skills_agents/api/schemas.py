from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class CreateSessionRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionResponse(BaseModel):
    tenant_id: str
    user_id: str
    session_id: str
    status: Literal["active", "handoff_required", "closed"]


class ChatRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    skill_id: str | None = None
    skill_name: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ActivatedSkill(BaseModel):
    skill_id: str
    name: str
    version: str | None = None
    checksum: str | None = None
    selection_reason: Literal["explicit", "keyword", "fallback"]


class TaskSummary(BaseModel):
    total: int = Field(ge=0)
    completed: int = Field(ge=0)
    failed: int = Field(ge=0)
    pending: int = Field(ge=0)


class SourceReference(BaseModel):
    source_id: str
    title: str
    path: str | None = None
    snippet: str
    score: float | None = None


class ApprovalRequest(BaseModel):
    reason: str | None = None
    risk_tags: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    tenant_id: str
    session_id: str
    reply: str
    activated_skills: list[ActivatedSkill] = Field(default_factory=list)
    task_summary: TaskSummary
    sources: list[SourceReference] = Field(default_factory=list)
    risk_level: Literal["low", "medium", "high", "blocked"]
    risk_tags: list[str] = Field(default_factory=list)
    handoff_required: bool
    requires_human_approval: bool | None = None
    approval_request: ApprovalRequest | None = None
    handoff_payload_path: str | None = None


class TaskResponse(BaseModel):
    tenant_id: str
    session_id: str
    markdown: str
    summary: TaskSummary


class SkillEntry(BaseModel):
    skill_id: str
    name: str
    description: str
    source: str
    enabled: bool
    version: str | None = None
    checksum: str | None = None
    warnings: list[str] = Field(default_factory=list)


class SkillListResponse(BaseModel):
    tenant_id: str
    skills: list[SkillEntry] = Field(default_factory=list)


class ReloadSkillsRequest(BaseModel):
    tenant_id: str = Field(min_length=1)


class SkillReloadResponse(BaseModel):
    tenant_id: str
    scanned: int = Field(ge=0)
    registered: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    providers: dict[str, str]


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: dict[str, Any] | None = None
