from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8",
    )

    openai_api_key: str | None = None
    openai_interview_model: str = "gpt-5.4"
    openai_resume_parse_model: str = "gpt-4o"
    openai_transcribe_model: str = "gpt-4o-mini-transcribe"
    openai_tts_model: str = "gpt-4o-mini-tts"
    openai_tts_voice: str = "marin"
    interview_reasoning_effort: str = "low"
    interviewer_name: str = "Alex"
    interview_target_role: str = "Machine Learning Engineer"
    interview_target_company: str = "Example Company"
    cors_allowed_origins: str = "http://127.0.0.1:3000,http://localhost:3000"
    cors_allow_credentials: bool = True
    api_access_token: str | None = None
    api_rate_limit_per_minute: int = Field(default=0, ge=0)
    log_level: str = "INFO"
    max_resume_upload_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    max_audio_upload_bytes: int = Field(default=25 * 1024 * 1024, gt=0)
    question_bank_embedding_dimensions: int = 384
    question_bank_embedding_model: str = "all-MiniLM-L6-v2"
    question_bank_embedding_provider: str = "sentence-transformers"
    supabase_url: str | None = None
    supabase_publishable_key: str | None = None
    supabase_service_role_key: str | None = None
    supabase_resume_bucket: str = "resumes"

    workspace_root: Path = Path(__file__).resolve().parents[4]

    @model_validator(mode="after")
    def validate_cors_configuration(self) -> Self:
        if "*" in self.allowed_origins and self.cors_allow_credentials:
            raise ValueError(
                "CORS wildcard origins cannot be used when credentials are enabled."
            )
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    @property
    def job_description_path(self) -> Path:
        candidate_paths = (
            self.workspace_root / "docs" / "examples" / "job-description.md",
            self.workspace_root / "docs" / "inputs" / "job_description.md",
            self.workspace_root / "job_description.md",
        )
        for candidate_path in candidate_paths:
            if candidate_path.exists():
                return candidate_path
        return self.workspace_root / "job_description.md"

    @property
    def questions_path(self) -> Path:
        return self.workspace_root / "apps" / "api" / "data" / "ml_questions.md"

    @property
    def question_bank_embeddings_path(self) -> Path:
        return self.workspace_root / "apps" / "api" / "data" / "question_bank.jsonl"

    def load_job_description(self) -> str:
        if self.job_description_path.exists():
            return self.job_description_path.read_text(encoding="utf-8")
        return ""


@lru_cache
def get_settings() -> Settings:
    workspace_root = Path(__file__).resolve().parents[4]
    return Settings(
        workspace_root=workspace_root,
        _env_file=(
            workspace_root / ".env",
            workspace_root / ".env.local",
        ),
    )
