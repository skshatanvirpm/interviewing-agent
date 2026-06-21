from fastapi import HTTPException
import pytest

from interviewing_agent.config import Settings
from interviewing_agent.services.audio import AudioService
from interviewing_agent.services.resume_parser import ResumeParser


class FailingTranscriptions:
    def create(self, **kwargs):
        raise RuntimeError("provider-internal-detail")


class FailingSpeech:
    def create(self, **kwargs):
        raise RuntimeError("provider-internal-detail")


class FailingAudioClient:
    def __init__(self) -> None:
        self.audio = type(
            "AudioNamespace",
            (),
            {
                "transcriptions": FailingTranscriptions(),
                "speech": FailingSpeech(),
            },
        )()


class FailingFiles:
    def create(self, **kwargs):
        raise RuntimeError("provider-internal-detail")


class FailingResumeClient:
    def __init__(self) -> None:
        self.files = FailingFiles()


class StubProvider:
    def __init__(self, client) -> None:
        self.client = client


def test_audio_provider_errors_return_safe_messages() -> None:
    settings = Settings(openai_api_key="configured", _env_file=None)
    service = AudioService(settings, StubProvider(FailingAudioClient()))

    with pytest.raises(HTTPException) as transcription_error:
        service.transcribe("answer.webm", b"audio")
    with pytest.raises(HTTPException) as speech_error:
        service.synthesize("Question")

    assert transcription_error.value.status_code == 502
    assert transcription_error.value.detail == "Audio transcription is temporarily unavailable."
    assert speech_error.value.status_code == 502
    assert speech_error.value.detail == "Speech generation is temporarily unavailable."


def test_resume_provider_error_does_not_expose_exception_text(monkeypatch) -> None:
    settings = Settings(openai_api_key="configured", _env_file=None)
    parser = ResumeParser(settings, StubProvider(FailingResumeClient()))
    monkeypatch.setattr(parser, "_extract_pdf_text", lambda content: "Skills\nPython")

    resume = parser.parse_pdf("candidate.pdf", b"%PDF-1.4")

    assert any("local extraction fallback" in note.lower() for note in resume.notes)
    assert all("provider-internal-detail" not in note for note in resume.notes)
