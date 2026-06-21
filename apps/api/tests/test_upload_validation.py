import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from interviewing_agent.routes.uploads import read_audio_upload, read_resume_upload


def make_upload(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def test_resume_upload_accepts_pdf_and_sanitizes_filename() -> None:
    upload = make_upload("../candidate.pdf", b"%PDF-1.4 test", "application/pdf")

    validated = asyncio.run(read_resume_upload(upload, max_bytes=1024))

    assert validated.filename == "candidate.pdf"
    assert validated.content.startswith(b"%PDF-")


@pytest.mark.parametrize(
    ("filename", "content", "content_type", "expected_status"),
    [
        ("candidate.txt", b"%PDF-1.4 test", "application/pdf", 415),
        ("candidate.pdf", b"%PDF-1.4 test", "text/plain", 415),
        ("candidate.pdf", b"not-a-pdf", "application/pdf", 400),
        ("candidate.pdf", b"%PDF-1.4 too-large", "application/pdf", 413),
    ],
)
def test_resume_upload_rejects_invalid_files(
    filename: str,
    content: bytes,
    content_type: str,
    expected_status: int,
) -> None:
    upload = make_upload(filename, content, content_type)
    limit = 8 if expected_status == 413 else 1024

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(read_resume_upload(upload, max_bytes=limit))

    assert exc_info.value.status_code == expected_status


def test_audio_upload_requires_matching_extension_and_content_type() -> None:
    upload = make_upload("answer.webm", b"audio", "audio/mpeg")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(read_audio_upload(upload, max_bytes=1024))

    assert exc_info.value.status_code == 415


def test_audio_upload_enforces_size_limit() -> None:
    upload = make_upload("answer.webm", b"audio-content", "audio/webm;codecs=opus")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(read_audio_upload(upload, max_bytes=4))

    assert exc_info.value.status_code == 413
