# Interviewing Agent API

FastAPI service for resume parsing, interview orchestration, question retrieval, evaluation, persistence, transcription, and speech synthesis.

## Run

From this directory:

```bash
uv sync
PYTHONPATH=src uv run uvicorn interviewing_agent.main:app --reload
```

The API runs at `http://127.0.0.1:8000` by default. Interactive API documentation is available at `/docs`.

## Test

```bash
uv run pytest
```

Runtime settings are documented in the repository-level `.env.example`. Provider-backed features require the corresponding OpenAI and Supabase environment variables.

The API validates resume and audio filenames, media types, PDF signatures, and upload sizes before invoking provider services. Unexpected provider failures are logged server-side and returned to clients using safe error messages.
