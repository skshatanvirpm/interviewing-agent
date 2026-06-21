from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Any
from urllib.parse import quote
from uuid import uuid4

import httpx

from interviewing_agent.config import Settings
from interviewing_agent.models import (
    FinalFeedback,
    InterviewMessage,
    InterviewPhase,
    InterviewSession,
    ParsedResume,
    PhaseEvaluation,
    PhaseScores,
    ProctoringSummary,
)


class SupabasePersistenceService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def configured(self) -> bool:
        return bool(
            self.settings.supabase_url
            and self.settings.supabase_publishable_key
            and self.settings.supabase_service_role_key
        )

    @cached_property
    def _service_headers(self) -> dict[str, str]:
        key = self.settings.supabase_service_role_key or ""
        return {
            "Authorization": f"Bearer {key}",
            "apikey": key,
            "Content-Type": "application/json",
        }

    @cached_property
    def _base_url(self) -> str:
        return (self.settings.supabase_url or "").rstrip("/")

    def persist_bootstrap(
        self,
        session: InterviewSession,
        resume_filename: str | None = None,
        resume_content: bytes | None = None,
    ) -> InterviewSession:
        if not self.configured:
            return session

        candidate_id = session.candidate_id or str(uuid4())
        resume_id = session.resume_id or str(uuid4())
        storage_path = self._upload_resume(candidate_id, resume_id, resume_filename, resume_content)

        session.candidate_id = candidate_id
        session.resume_id = resume_id

        self._upsert(
            "candidates",
            [
                {
                    "id": candidate_id,
                    "full_name": session.resume.candidate_name,
                    "headline": session.resume.headline,
                    "summary": session.resume.summary,
                }
            ],
        )
        self._upsert(
            "resumes",
            [
                {
                    "id": resume_id,
                    "candidate_id": candidate_id,
                    "storage_path": storage_path,
                    "raw_filename": resume_filename or f"{resume_id}.pdf",
                    "parsed_json": session.resume.model_dump(mode="json"),
                }
            ],
        )
        self._replace_resume_sections(resume_id, session.resume)
        self.persist_session(session)
        return session

    def persist_session(self, session: InterviewSession) -> InterviewSession:
        if not self.configured or not session.candidate_id:
            return session

        self._upsert(
            "interviews",
            [
                {
                    "id": session.id,
                    "candidate_id": session.candidate_id,
                    "resume_id": session.resume_id,
                    "target_company": session.target_company,
                    "target_role": session.target_role,
                    "current_phase": session.current_phase.value,
                    "hint_count": session.hint_count,
                    "hint_recovery_count": session.hint_recovery_count,
                    "empathy_prompt_count": session.empathy_prompt_count,
                    "factual_question_count": session.factual_question_count,
                    "phase_scores": session.scores.model_dump(mode="json"),
                    "overall_score": session.scores.overall,
                    "final_feedback": (
                        session.final_feedback.model_dump(mode="json")
                        if session.final_feedback
                        else None
                    ),
                    "realtime_mode_enabled": session.realtime_mode_enabled,
                    "video_mode_enabled": session.video_mode_enabled,
                    "proctoring_summary": session.proctoring.model_dump(mode="json"),
                }
            ],
        )
        self._upsert(
            "interview_messages",
            [
                {
                    "id": message.id,
                    "interview_id": session.id,
                    "role": message.role,
                    "phase": message.phase.value,
                    "message_text": message.text,
                    "hint_used": message.hint_used,
                    "hint_recovery": message.hint_recovery,
                    "empathy_used": message.empathy_used,
                    "created_at": message.created_at,
                }
                for message in session.messages
            ],
        )
        self._replace_evaluations(session)
        return session

    def load_session(self, session_id: str) -> InterviewSession | None:
        if not self.configured:
            return None

        interviews = self._select("interviews", {"id": f"eq.{session_id}"})
        if not interviews:
            return None

        interview = interviews[0]
        resumes = (
            self._select("resumes", {"id": f"eq.{interview['resume_id']}"})
            if interview.get("resume_id")
            else []
        )
        resume_payload = resumes[0]["parsed_json"] if resumes else {}
        messages = self._select(
            "interview_messages",
            {"interview_id": f"eq.{session_id}", "order": "created_at.asc"},
        )
        evaluations = self._select(
            "evaluations",
            {"interview_id": f"eq.{session_id}", "order": "phase.asc"},
        )

        phase_evaluations = {
            item["phase"]: PhaseEvaluation(
                phase=InterviewPhase(item["phase"]),
                label=item.get("label") or self._phase_label(item["phase"]),
                score=float(item["score"]) if item.get("score") is not None else None,
                dimensions=item.get("dimensions") or {},
                evidence=item.get("evidence") or [],
                strengths=item.get("strengths") or [],
                weaknesses=item.get("weaknesses") or [],
                suggestion=item.get("suggestion") or "",
                confidence=float(item["confidence"]) if item.get("confidence") is not None else None,
            )
            for item in evaluations
        }

        phase_scores_payload = interview.get("phase_scores") or {}
        if interview.get("overall_score") is not None:
            phase_scores_payload["overall"] = float(interview["overall_score"])

        return InterviewSession(
            id=interview["id"],
            current_phase=InterviewPhase(interview["current_phase"]),
            target_company=interview.get("target_company") or "",
            target_role=interview.get("target_role") or "",
            resume=ParsedResume.model_validate(resume_payload or {}),
            candidate_id=interview.get("candidate_id"),
            resume_id=interview.get("resume_id"),
            messages=[
                InterviewMessage(
                    id=item["id"],
                    role=item["role"],
                    phase=InterviewPhase(item["phase"]),
                    text=item["message_text"],
                    hint_used=bool(item.get("hint_used")),
                    hint_recovery=bool(item.get("hint_recovery")),
                    empathy_used=bool(item.get("empathy_used")),
                    created_at=item["created_at"],
                )
                for item in messages
            ],
            scores=PhaseScores.model_validate(phase_scores_payload),
            phase_evaluations=phase_evaluations,
            final_feedback=(
                FinalFeedback.model_validate(interview["final_feedback"])
                if interview.get("final_feedback")
                else None
            ),
            hint_count=interview.get("hint_count") or 0,
            hint_recovery_count=interview.get("hint_recovery_count") or 0,
            empathy_prompt_count=interview.get("empathy_prompt_count") or 0,
            factual_question_count=interview.get("factual_question_count") or 0,
            realtime_mode_enabled=bool(interview.get("realtime_mode_enabled")),
            video_mode_enabled=bool(interview.get("video_mode_enabled")),
            proctoring=ProctoringSummary.model_validate(
                interview.get("proctoring_summary") or {}
            ),
        )

    def _replace_resume_sections(self, resume_id: str, resume: ParsedResume) -> None:
        self._delete("resume_sections", {"resume_id": f"eq.{resume_id}"})
        section_rows: list[dict[str, Any]] = []
        section_rows.extend(self._section_rows(resume_id, "skills", resume.skills))
        section_rows.extend(self._section_rows(resume_id, "projects", resume.projects))
        section_rows.extend(self._section_rows(resume_id, "experience", resume.experience))
        section_rows.extend(self._section_rows(resume_id, "education", resume.education))
        section_rows.extend(self._section_rows(resume_id, "notes", resume.notes))
        if section_rows:
            self._upsert("resume_sections", section_rows)

    def _replace_evaluations(self, session: InterviewSession) -> None:
        self._delete("evaluations", {"interview_id": f"eq.{session.id}"})
        rows = []
        for evaluation in session.phase_evaluations.values():
            rows.append(
                {
                    "id": str(uuid4()),
                    "interview_id": session.id,
                    "phase": evaluation.phase.value,
                    "label": evaluation.label,
                    "score": evaluation.score,
                    "rationale": evaluation.suggestion,
                    "evidence": evaluation.evidence,
                    "dimensions": evaluation.dimensions,
                    "strengths": evaluation.strengths,
                    "weaknesses": evaluation.weaknesses,
                    "suggestion": evaluation.suggestion,
                    "confidence": evaluation.confidence,
                }
            )
        if rows:
            self._upsert("evaluations", rows)

    def _section_rows(self, resume_id: str, section_type: str, values: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "id": str(uuid4()),
                "resume_id": resume_id,
                "section_type": section_type,
                "content": value,
                "metadata": {"index": index},
            }
            for index, value in enumerate(values)
        ]

    def _upload_resume(
        self,
        candidate_id: str,
        resume_id: str,
        resume_filename: str | None,
        resume_content: bytes | None,
    ) -> str:
        filename = (resume_filename or "resume.pdf").replace("/", "-")
        storage_path = f"{candidate_id}/{resume_id}-{filename}"
        if not resume_content:
            return storage_path

        self._ensure_bucket()
        encoded_path = quote(storage_path, safe="/-_.")
        url = f"{self._base_url}/storage/v1/object/{self.settings.supabase_resume_bucket}/{encoded_path}"
        headers = {
            "Authorization": self._service_headers["Authorization"],
            "apikey": self._service_headers["apikey"],
            "x-upsert": "true",
            "content-type": "application/pdf",
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, content=resume_content)
            response.raise_for_status()
        return storage_path

    def _ensure_bucket(self) -> None:
        bucket = self.settings.supabase_resume_bucket
        url = f"{self._base_url}/storage/v1/bucket/{bucket}"
        with httpx.Client(timeout=20.0) as client:
            response = client.get(url, headers=self._service_headers)
            if response.status_code == 200:
                return
            create_response = client.post(
                f"{self._base_url}/storage/v1/bucket",
                headers=self._service_headers,
                json={"id": bucket, "name": bucket, "public": False},
            )
            if create_response.status_code not in (200, 201, 409):
                create_response.raise_for_status()

    def _upsert(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        headers = {
            **self._service_headers,
            "Prefer": "resolution=merge-duplicates,return=minimal",
        }
        self._request(
            "POST",
            f"/rest/v1/{table}",
            json=rows,
            params={"on_conflict": "id"},
            headers=headers,
        )

    def _delete(self, table: str, params: dict[str, str]) -> None:
        self._request("DELETE", f"/rest/v1/{table}", params=params)

    def _select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        query = {"select": "*", **params}
        response = self._request("GET", f"/rest/v1/{table}", params=query)
        return response.json()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        request_headers = headers or self._service_headers
        with httpx.Client(timeout=30.0) as client:
            response = client.request(
                method,
                f"{self._base_url}{path}",
                params=params,
                json=json,
                headers=request_headers,
            )
            response.raise_for_status()
            return response

    @staticmethod
    def _phase_label(phase: str) -> str:
        return {
            "phase_2_deep_dive": "Deep Dive",
            "phase_3_breadth": "Breadth",
            "phase_4_factual": "Factual",
            "phase_5_behavioral": "Behavioral",
        }.get(phase, phase.replace("_", " ").title())
