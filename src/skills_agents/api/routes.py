from fastapi import APIRouter
from fastapi.responses import JSONResponse

from skills_agents.api.schemas import ErrorResponse, TaskResponse, TaskSummary
from skills_agents.core.context import TenantContext
from skills_agents.tasks.tracker import TaskTracker


def create_task_router(task_tracker: TaskTracker, tenant_ids: set[str] | None = None) -> APIRouter:
    router = APIRouter()

    @router.get("/v1/tasks/{session_id}", response_model=TaskResponse)
    def get_tasks(session_id: str, tenant_id: str):
        if tenant_ids is not None and tenant_id not in tenant_ids:
            error = ErrorResponse(
                error="unknown_tenant",
                message=f"Unknown tenant: {tenant_id}",
            )
            return JSONResponse(status_code=404, content=error.model_dump())
        try:
            context = TenantContext(tenant_id=tenant_id, session_id=session_id)
            markdown = task_tracker.get_markdown(context)
        except ValueError:
            error = ErrorResponse(
                error="invalid_tenant_id",
                message="tenant_id contains unsafe path characters.",
            )
            return JSONResponse(status_code=400, content=error.model_dump())
        if not markdown:
            error = ErrorResponse(
                error="task_not_found",
                message="No task checklist exists for this tenant and session.",
            )
            return JSONResponse(status_code=404, content=error.model_dump())
        return TaskResponse(
            tenant_id=tenant_id,
            session_id=session_id,
            markdown=markdown,
            summary=TaskSummary(**task_tracker.summary(context)),
        )

    return router
