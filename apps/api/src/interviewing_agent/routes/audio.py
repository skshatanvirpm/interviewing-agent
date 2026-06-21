from __future__ import annotations

from fastapi import APIRouter, Depends, File, Response, UploadFile

from interviewing_agent.config import Settings
from interviewing_agent.models import SpeechRequest, TranscriptResponse
from interviewing_agent.routes.dependencies import get_audio_service, get_settings
from interviewing_agent.routes.uploads import read_audio_upload
from interviewing_agent.services.audio import AudioService

router = APIRouter(tags=["audio"])


@router.post("/audio/transcribe", response_model=TranscriptResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    audio_service: AudioService = Depends(get_audio_service),
    settings: Settings = Depends(get_settings),
) -> TranscriptResponse:
    validated = await read_audio_upload(audio, settings.max_audio_upload_bytes)
    transcript = audio_service.transcribe(validated.filename, validated.content)
    return TranscriptResponse(transcript=transcript)


@router.post("/audio/speak")
def speak_text(
    payload: SpeechRequest,
    audio_service: AudioService = Depends(get_audio_service),
) -> Response:
    audio_bytes = audio_service.synthesize(payload.text)
    return Response(content=audio_bytes, media_type="audio/wav")
