from pydantic import BaseModel, Field


class TenantContext(BaseModel):
    tenant_id: str = Field(min_length=1)
    user_id: str | None = Field(default=None, min_length=1)
    session_id: str | None = Field(default=None, min_length=1)
