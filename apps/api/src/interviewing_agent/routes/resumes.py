from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from interviewing_agent.config import Settings
from interviewing_agent.models import ParsedResume
from interviewing_agent.routes.dependencies import get_resume_parser, get_settings
from interviewing_agent.routes.uploads import read_resume_upload
from interviewing_agent.services.resume_parser import ResumeParser

router = APIRouter(tags=["resumes"])


@router.post("/resumes/parse", response_model=ParsedResume)
async def parse_resume(
    resume: UploadFile = File(...),
    parser: ResumeParser = Depends(get_resume_parser),
    settings: Settings = Depends(get_settings),
) -> ParsedResume:
    validated = await read_resume_upload(resume, settings.max_resume_upload_bytes)
    return parser.parse_pdf(validated.filename, validated.content)
