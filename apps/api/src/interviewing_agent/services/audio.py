from __future__ import annotations

import logging
from io import BytesIO

from fastapi import HTTPException

from interviewing_agent.config import Settings
from interviewing_agent.services.openai_client import OpenAIProvider


logger = logging.getLogger(__name__)


class AudioService:
    def __init__(self, settings: Settings, openai_provider: OpenAIProvider) -> None:
        self.settings = settings
        self.openai_provider = openai_provider

    def transcribe(self, filename: str, content: bytes) -> str:
        client = self.openai_provider.client
        if client is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Server-side audio transcription is unavailable because OPENAI_API_KEY "
                    "is not configured."
                ),
            )

        audio_buffer = BytesIO(content)
        audio_buffer.name = filename
        try:
            response = client.audio.transcriptions.create(
                model=self.settings.openai_transcribe_model,
                file=audio_buffer,
            )
            return response.text.strip()
        except Exception as exc:  # pragma: no cover - provider path
            logger.exception("Audio transcription provider request failed.")
            raise HTTPException(
                status_code=502,
                detail="Audio transcription is temporarily unavailable.",
            ) from exc

    def synthesize(self, text: str) -> bytes:
        client = self.openai_provider.client
        if client is None:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Server-side speech generation is unavailable because OPENAI_API_KEY "
                    "is not configured."
                ),
            )

        try:
            response = client.audio.speech.create(
                model=self.settings.openai_tts_model,
                voice=self.settings.openai_tts_voice,
                input=text,
                instructions="Speak like a calm, professional interviewer.",
                response_format="wav",
            )
            return response.read()
        except Exception as exc:  # pragma: no cover - provider path
            logger.exception("Speech synthesis provider request failed.")
            raise HTTPException(
                status_code=502,
                detail="Speech generation is temporarily unavailable.",
            ) from exc
