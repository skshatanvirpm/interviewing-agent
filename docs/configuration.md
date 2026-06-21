# Configuration

The API reads process environment variables plus `.env` and `.env.local` files at the repository root. Never commit real environment files.

## Variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Web deployment | `http://127.0.0.1:8000` | Browser-visible API base URL |
| `OPENAI_API_KEY` | Model/audio features | empty | Server-side OpenAI credential |
| `OPENAI_INTERVIEW_MODEL` | No | `gpt-5.4` | Interview orchestration model |
| `OPENAI_RESUME_PARSE_MODEL` | No | `gpt-4o` | Resume parsing and fallback-question model |
| `OPENAI_TRANSCRIBE_MODEL` | No | `gpt-4o-mini-transcribe` | Speech-to-text model |
| `OPENAI_TTS_MODEL` | No | `gpt-4o-mini-tts` | Text-to-speech model |
| `OPENAI_TTS_VOICE` | No | `marin` | Interviewer voice |
| `INTERVIEW_REASONING_EFFORT` | No | `low` | Reasoning effort sent to the interview model |
| `INTERVIEWER_NAME` | No | `Alex` | Name used in the opening greeting |
| `INTERVIEW_TARGET_ROLE` | No | `Machine Learning Engineer` | Role-alignment context |
| `INTERVIEW_TARGET_COMPANY` | No | `Example Company` | Company-alignment context |
| `CORS_ALLOWED_ORIGINS` | Production | local origins | Comma-separated allowed browser origins |
| `CORS_ALLOW_CREDENTIALS` | No | `true` | CORS credential behavior |
| `MAX_RESUME_UPLOAD_BYTES` | No | `10485760` | Resume upload limit |
| `MAX_AUDIO_UPLOAD_BYTES` | No | `26214400` | Audio upload limit |
| `LOG_LEVEL` | No | `INFO` | Python log level |
| `SUPABASE_URL` | Persistence | empty | Supabase project URL |
| `SUPABASE_PUBLISHABLE_KEY` | Persistence | empty | Supabase publishable key used for configuration completeness |
| `SUPABASE_SERVICE_ROLE_KEY` | Persistence | empty | Server-only privileged persistence key |

## Local setup

```bash
cp .env.example .env
```

The core deterministic interview flow works without provider credentials. Transcription and speech endpoints return `503` when `OPENAI_API_KEY` is missing. Persistence is skipped when Supabase configuration is incomplete.

## Production rules

- Set `NEXT_PUBLIC_API_URL` before building the web application.
- Set `CORS_ALLOWED_ORIGINS` to exact HTTPS web origins.
- Do not combine wildcard CORS origins with credentials.
- Store service credentials in the hosting provider's secret manager.
- Never expose `SUPABASE_SERVICE_ROLE_KEY` through a `NEXT_PUBLIC_` variable.
- Use separate provider projects and credentials for development and production.
- Rotate any credential that has entered a log, screenshot, commit, or support channel.

## Supabase bootstrap helper

`scripts/bootstrap_supabase_runtime.py` can resolve runtime keys from a Supabase personal access token and optionally apply the schema. It prints credentials to standard output, so use it only in a controlled local shell and avoid saving output to committed files.
