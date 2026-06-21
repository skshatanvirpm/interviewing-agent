from __future__ import annotations

from fastapi import Request

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
