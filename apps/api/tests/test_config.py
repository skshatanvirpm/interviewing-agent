import pytest
from pydantic import ValidationError

from interviewing_agent.config import Settings


def test_settings_do_not_load_markdown_credentials(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    secrets_path = tmp_path / "private" / "secretes.md"
    secrets_path.parent.mkdir()
    secrets_path.write_text("OPENAI_API_KEY=markdown-key", encoding="utf-8")

    settings = Settings(workspace_root=tmp_path, _env_file=None)

    assert settings.openai_api_key is None


def test_settings_parse_configurable_cors_origins() -> None:
    settings = Settings(
        cors_allowed_origins="https://app.example.com/, http://localhost:3000, ",
        _env_file=None,
    )

    assert settings.allowed_origins == [
        "https://app.example.com",
        "http://localhost:3000",
    ]


def test_upload_limits_must_be_positive() -> None:
    settings = Settings(
        max_resume_upload_bytes=1024,
        max_audio_upload_bytes=2048,
        _env_file=None,
    )

    assert settings.max_resume_upload_bytes == 1024
    assert settings.max_audio_upload_bytes == 2048


def test_cors_rejects_wildcard_with_credentials() -> None:
    with pytest.raises(ValidationError):
        Settings(
            cors_allowed_origins="*",
            cors_allow_credentials=True,
            _env_file=None,
        )
