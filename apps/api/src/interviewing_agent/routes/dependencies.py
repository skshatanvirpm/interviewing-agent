from __future__ import annotations

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

    if not request.app.state.api_rate_limiter.allow():
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="The deployment request limit has been reached. Try again shortly.",
            headers={"Retry-After": "60"},
        )
