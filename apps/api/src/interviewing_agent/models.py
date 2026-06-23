from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class InterviewPhase(str, Enum):
    PHASE_1_INTRO = "phase_1_intro"
    PHASE_2_DEEP_DIVE = "phase_2_deep_dive"
    PHASE_3_BREADTH = "phase_3_breadth"
    PHASE_4_FACTUAL = "phase_4_factual"
    PHASE_5_BEHAVIORAL = "phase_5_behavioral"
    COMPLETE = "complete"


class ParsedResume(BaseModel):
    candidate_name: str = "Candidate"
    headline: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    inferred_domains: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class InterviewMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    role: Literal["interviewer", "candidate"]
    phase: InterviewPhase
    text: str
    hint_used: bool = False
    hint_recovery: bool = False
    empathy_used: bool = False
    created_at: str = Field(default_factory=now_iso)


class PhaseScores(BaseModel):
    phase_2: float | None = None
    phase_3: float | None = None
    phase_4: float | None = None
    phase_5: float | None = None
    overall: float | None = None


class PhaseEvaluation(BaseModel):
    phase: InterviewPhase
    label: str
    score: float | None = None
    dimensions: dict[str, float] = Field(default_factory=dict)
    evidence: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestion: str = ""
    confidence: float | None = None


class FinalFeedback(BaseModel):
    overall_score: float | None = None
    overall_summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    role_alignment: list[str] = Field(default_factory=list)
    integrity_notes: list[str] = Field(default_factory=list)


class ProctoringSummary(BaseModel):
    tab_switch_count: int = 0
    window_blur_count: int = 0
    paste_count: int = 0
    transcript_retry_count: int = 0
    suspicious_flags: list[str] = Field(default_factory=list)


class InterviewSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    session_access_token_hash: str | None = Field(default=None, exclude=True)
    current_phase: InterviewPhase = InterviewPhase.PHASE_1_INTRO
    target_company: str
    target_role: str
    resume: ParsedResume
    candidate_id: str | None = None
    resume_id: str | None = None
    messages: list[InterviewMessage] = Field(default_factory=list)
    scores: PhaseScores = Field(default_factory=PhaseScores)
    phase_evaluations: dict[str, PhaseEvaluation] = Field(default_factory=dict)
    final_feedback: FinalFeedback | None = None
    hint_count: int = 0
    hint_recovery_count: int = 0
    empathy_prompt_count: int = 0
    factual_question_count: int = 0
    realtime_mode_enabled: bool = False
    video_mode_enabled: bool = False
    proctoring: ProctoringSummary = Field(default_factory=ProctoringSummary)


class BootstrapResponse(BaseModel):
    resume: ParsedResume
    session: InterviewSession
    session_access_token: str


class ParsedResumeBootstrapRequest(BaseModel):
    resume: ParsedResume
    resume_label: str | None = None
    candidate_id: str | None = None
    resume_id: str | None = None


class TurnMetadata(BaseModel):
    source: Literal["text", "audio", "realtime"] = "text"
    answer_duration_seconds: float | None = None
    transcript_retry_count: int = 0
    tab_switch_count: int = 0
    window_blur_count: int = 0
    used_paste: bool = False
    camera_enabled: bool = False
    realtime_enabled: bool = False


class InterviewTurnRequest(BaseModel):
    candidate_response: str
    metadata: TurnMetadata = Field(default_factory=TurnMetadata)


class InterviewTurnResponse(BaseModel):
    session: InterviewSession
    latest_reply: InterviewMessage


class TranscriptResponse(BaseModel):
    transcript: str


class SpeechRequest(BaseModel):
    text: str


class HealthResponse(BaseModel):
    status: str
    openai_configured: bool
    supabase_configured: bool
