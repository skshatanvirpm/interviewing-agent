from __future__ import annotations

from fastapi import APIRouter, Depends

from interviewing_agent.config import Settings
from interviewing_agent.models import HealthResponse
from interviewing_agent.routes.dependencies import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        openai_configured=bool(settings.openai_api_key),
        supabase_configured=bool(
            settings.supabase_url
            and settings.supabase_publishable_key
            and settings.supabase_service_role_key
        ),
    )
