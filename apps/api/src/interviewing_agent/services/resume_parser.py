from __future__ import annotations

import json
import logging
import re
from io import BytesIO

from interviewing_agent.config import Settings
from interviewing_agent.models import ParsedResume
from interviewing_agent.prompts import resume_parse_prompt
from interviewing_agent.services.openai_client import OpenAIProvider


logger = logging.getLogger(__name__)


class ResumeParser:
    def __init__(self, settings: Settings, openai_provider: OpenAIProvider) -> None:
        self.settings = settings
        self.openai_provider = openai_provider

    def parse_pdf(self, filename: str, content: bytes) -> ParsedResume:
        extracted_text = self._extract_pdf_text(content)
        client = self.openai_provider.client
        if client is None:
            return self._fallback_resume(filename, extracted_text)

        file_buffer = BytesIO(content)
        file_buffer.name = filename

        try:
            uploaded = client.files.create(file=file_buffer, purpose="user_data")
            response = client.responses.create(
                model=self.settings.openai_resume_parse_model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_file", "file_id": uploaded.id},
                            {"type": "input_text", "text": resume_parse_prompt()},
                        ],
                    }
                ],
            )
            payload = self._extract_json_object(response.output_text)
            return self._normalize_resume(
                ParsedResume.model_validate(payload),
                filename=filename,
                source_text=extracted_text,
            )
        except Exception:  # pragma: no cover - network path
            logger.warning(
                "OpenAI resume parsing failed; using local extraction fallback.",
                exc_info=True,
            )
            fallback = self._fallback_resume(filename, extracted_text)
            fallback.notes.append(
                "OpenAI resume parsing was unavailable; local extraction fallback was used."
            )
            return fallback

    def _fallback_resume(self, filename: str, extracted_text: str = "") -> ParsedResume:
        stem = filename.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").strip()
        candidate_name = stem.title() if stem else "Candidate"
        fallback = ParsedResume(
            candidate_name=candidate_name,
            headline="Resume uploaded, parser fallback active",
            summary=(
                "OpenAI-backed PDF parsing is not active yet, so this summary was generated "
                "from local PDF text extraction."
            ),
            notes=[],
        )
        return self._normalize_resume(fallback, filename=filename, source_text=extracted_text)

    def _normalize_resume(
        self,
        resume: ParsedResume,
        *,
        filename: str,
        source_text: str,
    ) -> ParsedResume:
        sections = self._extract_sections(source_text)
        stem = filename.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").strip()
        candidate_name = self._cleanup_line(resume.candidate_name) or stem.title() or "Candidate"
        headline = self._cleanup_line(resume.headline)
        summary = self._cleanup_text(resume.summary)

        skills = self._normalize_list(
            resume.skills
            or self._split_items(sections.get("skills", ""))
        )
        projects = self._normalize_list(
            resume.projects
            or self._split_items(sections.get("projects", ""))
        )
        experience = self._normalize_list(
            resume.experience
            or self._split_items(sections.get("experience", ""))
        )
        education = self._normalize_list(
            resume.education
            or self._split_items(sections.get("education", ""))
        )

        if not headline and experience:
            headline = experience[0]
        if not summary:
            summary = self._build_summary(headline, projects, experience, source_text)

        inferred_domains = self._infer_domains(
            " ".join(
                [
                    summary,
                    sections.get("skills", ""),
                    sections.get("projects", ""),
                    sections.get("experience", ""),
                ]
            )
        )
        merged_domains = self._normalize_list(resume.inferred_domains + inferred_domains)

        notes = self._normalize_list(resume.notes)
        if not self.openai_provider.client:
            notes.append("Resume normalization used local PDF extraction because OpenAI parsing is unavailable.")

        return ParsedResume(
            candidate_name=candidate_name,
            headline=headline,
            summary=summary,
            skills=skills,
            projects=projects,
            experience=experience,
            education=education,
            inferred_domains=merged_domains,
            notes=self._normalize_list(notes),
        )

    @staticmethod
    def _cleanup_line(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    @staticmethod
    def _cleanup_text(value: str) -> str:
        return re.sub(r"\s+", " ", value or "").strip()

    def _extract_pdf_text(self, content: bytes) -> str:
        try:
            from pypdf import PdfReader
        except ImportError:
            return ""

        try:
            reader = PdfReader(BytesIO(content))
            parts = [page.extract_text() or "" for page in reader.pages]
        except Exception:
            logger.warning("Local PDF text extraction failed.", exc_info=True)
            return ""

        return "\n".join(part.strip() for part in parts if part.strip())

    def _extract_sections(self, text: str) -> dict[str, str]:
        if not text.strip():
            return {}

        heading_map = {
            "summary": ("summary", "profile", "about"),
            "experience": ("experience", "work experience", "employment"),
            "projects": ("projects", "project experience", "research"),
            "skills": ("skills", "technical skills", "technologies", "tools"),
            "education": ("education", "academics"),
        }
        normalized_lines = [self._cleanup_line(line) for line in text.splitlines()]
        sections: dict[str, list[str]] = {}
        current_key = "summary"

        for line in normalized_lines:
            if not line:
                continue
            lower_line = line.lower().rstrip(":")
            matched_key = next(
                (
                    key
                    for key, variants in heading_map.items()
                    if any(lower_line == variant for variant in variants)
                ),
                None,
            )
            if matched_key:
                current_key = matched_key
                sections.setdefault(current_key, [])
                continue
            sections.setdefault(current_key, []).append(line)

        return {key: "\n".join(value).strip() for key, value in sections.items() if value}

    def _split_items(self, block: str) -> list[str]:
        if not block:
            return []

        if "|" in block and "\n" not in block:
            raw_items = block.split("|")
        else:
            raw_items = re.split(r"\n|•|- |\u2022|, (?=[A-Z0-9])|; ", block)
        return [self._cleanup_line(item) for item in raw_items if self._cleanup_line(item)]

    @staticmethod
    def _normalize_list(values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            cleaned = re.sub(r"\s+", " ", value or "").strip(" -•\u2022\t")
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            normalized.append(cleaned)
        return normalized[:12]

    def _build_summary(
        self,
        headline: str,
        projects: list[str],
        experience: list[str],
        source_text: str,
    ) -> str:
        summary_parts = [headline] if headline else []
        summary_parts.extend(projects[:1])
        summary_parts.extend(experience[:1])
        summary = " | ".join(part for part in summary_parts if part)
        if summary:
            return summary
        cleaned_text = self._cleanup_text(source_text)
        return cleaned_text[:280] if cleaned_text else "Structured resume summary unavailable."

    @staticmethod
    def _infer_domains(text: str) -> list[str]:
        haystack = text.lower()
        domains: list[str] = []
        if any(keyword in haystack for keyword in ("llm", "rag", "transformer", "prompt")):
            domains.append("GenAI")
            domains.append("NLP")
        if any(keyword in haystack for keyword in ("recommend", "ranking", "bandit")):
            domains.append("Recommendation Systems")
        if any(keyword in haystack for keyword in ("image", "vision", "cnn", "segmentation")):
            domains.append("Computer Vision")
        if any(keyword in haystack for keyword in ("mlops", "monitoring", "airflow", "deployment")):
            domains.append("MLOps")
        if not domains and haystack:
            domains.append("Machine Learning")
        return domains

    @staticmethod
    def _extract_json_object(text: str) -> dict:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in model output.")
        return json.loads(match.group(0))
