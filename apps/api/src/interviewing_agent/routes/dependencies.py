from __future__ import annotations

from hashlib import sha256
from secrets import compare_digest

from fastapi import HTTPException, Request, status
from fastapi.security.utils import get_authorization_scheme_param

from interviewing_agent.config import Settings
from interviewing_agent.services.audio import AudioService
from interviewing_agent.services.interview_engine import InterviewEngine
from interviewing_agent.services.resume_parser import ResumeParser


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_resume_parser(request: Request) -> ResumeParser:
    return request.app.state.resume_parser


def get_interview_engine(request: Request) -> InterviewEngine:
    return request.app.state.interview_engine


def get_audio_service(request: Request) -> AudioService:
    return request.app.state.audio_service


def require_api_access(request: Request) -> None:
    settings: Settings = request.app.state.settings
    expected_token = settings.api_access_token
    supplied_token = ""

    if expected_token:
        scheme, supplied_token = get_authorization_scheme_param(
            request.headers.get("Authorization")
        )
        if scheme.lower() != "bearer" or not supplied_token or not compare_digest(
            supplied_token,
            expected_token,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A valid deployment access token is required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if not request.app.state.api_rate_limiter.allow(_rate_limit_key(request, supplied_token)):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The request limit has been reached. Try again shortly.",
            headers={"Retry-After": "60"},
        )


def require_session_access(session_id: str, request: Request) -> None:
    settings: Settings = request.app.state.settings
    supplied_token = request.headers.get(settings.session_access_header, "")
    interview_engine: InterviewEngine = request.app.state.interview_engine

    if not interview_engine.verify_session_access(session_id, supplied_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A valid interview session token is required.",
        )


def _rate_limit_key(request: Request, supplied_token: str) -> str:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_host = (
        forwarded_for.split(",", 1)[0].strip()
        or (request.client.host if request.client else "")
        or "unknown"
    )
    if supplied_token:
        token_fingerprint = sha256(supplied_token.encode("utf-8")).hexdigest()[:16]
    else:
        token_fingerprint = "anonymous"
    return f"{client_host}:{token_fingerprint}"
