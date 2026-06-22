from __future__ import annotations

import logging

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from interviewing_agent.config import get_settings
from interviewing_agent.routes.audio import router as audio_router
from interviewing_agent.routes.dependencies import require_api_access
from interviewing_agent.routes.health import router as health_router
from interviewing_agent.routes.interviews import router as interview_router
from interviewing_agent.routes.resumes import router as resume_router
from interviewing_agent.services.audio import AudioService
from interviewing_agent.services.access_control import SlidingWindowRateLimiter
from interviewing_agent.services.evaluation import EvaluationService
from interviewing_agent.services.interview_engine import InterviewEngine, MemorySessionStore
from interviewing_agent.services.openai_client import OpenAIProvider
from interviewing_agent.services.persistence import SupabasePersistenceService
from interviewing_agent.services.question_bank import QuestionBankService
from interviewing_agent.services.resume_parser import ResumeParser

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)
openai_provider = OpenAIProvider(settings)
session_store = MemorySessionStore()
persistence_service = SupabasePersistenceService(settings)
evaluation_service = EvaluationService()

app = FastAPI(
    title="Interviewing Agent API",
    description="Resume parsing, interview orchestration, and audio services.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled API error.",
        extra={"request_method": request.method, "request_path": request.url.path},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Unexpected server error."},
    )


app.state.settings = settings
app.state.api_rate_limiter = SlidingWindowRateLimiter(
    settings.api_rate_limit_per_minute
)
app.state.resume_parser = ResumeParser(settings, openai_provider)
app.state.interview_engine = InterviewEngine(
    settings,
    openai_provider,
    session_store,
    QuestionBankService(settings),
    persistence_service,
    evaluation_service,
)
app.state.audio_service = AudioService(settings, openai_provider)

app.include_router(health_router)
protected_dependencies = [Depends(require_api_access)]
app.include_router(resume_router, dependencies=protected_dependencies)
app.include_router(interview_router, dependencies=protected_dependencies)
app.include_router(audio_router, dependencies=protected_dependencies)
