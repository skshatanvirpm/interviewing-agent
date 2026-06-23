# Configuration

The API reads process environment variables plus `.env` and `.env.local` files at the repository root. Never commit real environment files.

## Variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Web deployment | `http://127.0.0.1:8000` | Browser-visible API base URL |
| `NEXT_PUBLIC_REQUIRE_ACCESS_TOKEN` | Hosted demo | `false` | Show and enforce the browser access-token input |
| `NEXT_OUTPUT_EXPORT` | Static hosting | `false` | Export the Next.js application as static files |
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
| `API_ACCESS_TOKEN` | Hosted demo | empty | Server-side bearer token for protected API routes |
| `API_RATE_LIMIT_PER_MINUTE` | Hosted demo | `0` | In-memory per-client protected-request limit; zero disables limiting |
| `SESSION_ACCESS_HEADER` | No | `X-Interview-Session-Token` | Header used for interview-session authorization |
| `INTERVIEW_DATA_RETENTION_DAYS` | Production | `30` | Number of days persisted interview data is retained before cleanup |
| `INTERVIEW_RETENTION_CLEANUP_ENABLED` | No | `true` | Run retention cleanup when the API starts |
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
- Set `NEXT_PUBLIC_REQUIRE_ACCESS_TOKEN=true` for a protected hosted build.
- Set `CORS_ALLOWED_ORIGINS` to exact HTTPS web origins.
- Do not combine wildcard CORS origins with credentials.
- Store `API_ACCESS_TOKEN` only in the API host's secret manager and distribute it separately from the public site.
- Set a nonzero `API_RATE_LIMIT_PER_MINUTE` whenever provider-backed routes are internet accessible.
- Keep the session access header private to the browser flow; bootstrap returns the token and the API stores only its hash.
- Set `INTERVIEW_DATA_RETENTION_DAYS` to match the published data-retention policy.
- Store service credentials in the hosting provider's secret manager.
- Never expose `SUPABASE_SERVICE_ROLE_KEY` through a `NEXT_PUBLIC_` variable.
- Use separate provider projects and credentials for development and production.
- Rotate any credential that has entered a log, screenshot, commit, or support channel.

## Supabase bootstrap helper

`scripts/bootstrap_supabase_runtime.py` can resolve runtime keys from a Supabase personal access token and optionally apply the schema. It prints credentials to standard output, so use it only in a controlled local shell and avoid saving output to committed files.
