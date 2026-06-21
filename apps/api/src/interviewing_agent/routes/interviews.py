from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from interviewing_agent.config import Settings
from interviewing_agent.models import (
    BootstrapResponse,
    InterviewSession,
    InterviewTurnRequest,
    InterviewTurnResponse,
    ParsedResumeBootstrapRequest,
)
from interviewing_agent.routes.dependencies import get_interview_engine, get_resume_parser, get_settings
from interviewing_agent.routes.uploads import read_resume_upload
from interviewing_agent.services.interview_engine import InterviewEngine
from interviewing_agent.services.resume_parser import ResumeParser

router = APIRouter(tags=["interviews"])


@router.post("/sessions/bootstrap", response_model=BootstrapResponse)
async def bootstrap_interview(
    resume: UploadFile = File(...),
    parser: ResumeParser = Depends(get_resume_parser),
    interview_engine: InterviewEngine = Depends(get_interview_engine),
    settings: Settings = Depends(get_settings),
) -> BootstrapResponse:
    validated = await read_resume_upload(resume, settings.max_resume_upload_bytes)
    parsed_resume = parser.parse_pdf(validated.filename, validated.content)
    return interview_engine.bootstrap(parsed_resume, validated.filename, validated.content)


@router.post("/sessions/bootstrap-from-parsed", response_model=BootstrapResponse)
def bootstrap_from_parsed_resume(
    payload: ParsedResumeBootstrapRequest,
    interview_engine: InterviewEngine = Depends(get_interview_engine),
) -> BootstrapResponse:
    return interview_engine.bootstrap(
        payload.resume,
        payload.resume_label,
        None,
        payload.candidate_id,
        payload.resume_id,
    )


@router.get("/interviews/{session_id}", response_model=InterviewSession)
def get_interview(
    session_id: str,
    interview_engine: InterviewEngine = Depends(get_interview_engine),
) -> InterviewSession:
    return interview_engine.get_session(session_id)


@router.post("/interviews/{session_id}/begin", response_model=InterviewSession)
def begin_interview(
    session_id: str,
    interview_engine: InterviewEngine = Depends(get_interview_engine),
) -> InterviewSession:
    return interview_engine.begin_intro(session_id)


@router.post("/interviews/{session_id}/complete", response_model=InterviewSession)
def complete_interview(
    session_id: str,
    interview_engine: InterviewEngine = Depends(get_interview_engine),
) -> InterviewSession:
    return interview_engine.complete_session(session_id)


@router.post("/interviews/{session_id}/turn", response_model=InterviewTurnResponse)
def interview_turn(
    session_id: str,
    payload: InterviewTurnRequest,
    interview_engine: InterviewEngine = Depends(get_interview_engine),
) -> InterviewTurnResponse:
    return interview_engine.process_turn(session_id, payload.candidate_response, payload.metadata)
