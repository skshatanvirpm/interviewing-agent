from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, UploadFile, status


PDF_CONTENT_TYPES = {"application/pdf"}
AUDIO_CONTENT_TYPES_BY_EXTENSION = {
    ".flac": {"audio/flac", "audio/x-flac"},
    ".m4a": {"audio/mp4", "audio/x-m4a"},
    ".mp3": {"audio/mpeg", "audio/mp3"},
    ".mp4": {"audio/mp4", "video/mp4"},
    ".oga": {"audio/ogg", "application/ogg"},
    ".ogg": {"audio/ogg", "application/ogg"},
    ".wav": {"audio/wav", "audio/x-wav"},
    ".webm": {"audio/webm", "video/webm"},
}


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    content: bytes


def _safe_filename(filename: str | None, label: str) -> str:
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} filename is required.",
        )

    normalized = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not normalized:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} filename is required.",
        )
    return normalized


def _normalized_content_type(upload: UploadFile) -> str:
    return (upload.content_type or "").split(";", 1)[0].strip().lower()


async def _read_with_limit(upload: UploadFile, max_bytes: int, label: str) -> bytes:
    content = await upload.read(max_bytes + 1)
    await upload.close()

    if len(content) > max_bytes:
        max_megabytes = max_bytes / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"{label} exceeds the {max_megabytes:g} MB upload limit.",
        )
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} file is empty.",
        )
    return content


async def read_resume_upload(upload: UploadFile, max_bytes: int) -> ValidatedUpload:
    filename = _safe_filename(upload.filename, "Resume")
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Resume must use the .pdf file extension.",
        )
    if _normalized_content_type(upload) not in PDF_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Resume content type must be application/pdf.",
        )

    content = await _read_with_limit(upload, max_bytes, "Resume")
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume does not contain a valid PDF signature.",
        )
    return ValidatedUpload(filename=filename, content=content)


async def read_audio_upload(upload: UploadFile, max_bytes: int) -> ValidatedUpload:
    filename = _safe_filename(upload.filename, "Audio")
    filename_lower = filename.lower()
    extension = next(
        (
            candidate
            for candidate in AUDIO_CONTENT_TYPES_BY_EXTENSION
            if filename_lower.endswith(candidate)
        ),
        "",
    )
    if not extension:
        allowed_extensions = ", ".join(sorted(AUDIO_CONTENT_TYPES_BY_EXTENSION))
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Audio file extension must be one of: {allowed_extensions}.",
        )

    content_type = _normalized_content_type(upload)
    if content_type not in AUDIO_CONTENT_TYPES_BY_EXTENSION[extension]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Audio content type {content_type} does not match {extension}."
                if content_type
                else "Audio content type is required."
            ),
        )

    content = await _read_with_limit(upload, max_bytes, "Audio")
    return ValidatedUpload(filename=filename, content=content)
