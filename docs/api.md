# API Reference

The FastAPI service exposes JSON and multipart endpoints. Interactive OpenAPI documentation is available at `/docs` while the API is running.

## General behavior

- Default local base URL: `http://127.0.0.1:8000`
- Errors use `{ "detail": "message" }`.
- Unexpected provider errors return stable client messages and are logged server-side.
- No authentication is currently enforced.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Report API status and provider configuration |
| `POST` | `/resumes/parse` | Parse and normalize a PDF without creating a session |
| `POST` | `/sessions/bootstrap` | Parse a PDF and create an interview session |
| `POST` | `/sessions/bootstrap-from-parsed` | Create a session from an existing parsed resume |
| `GET` | `/interviews/{session_id}` | Retrieve a cached or persisted session |
| `POST` | `/interviews/{session_id}/begin` | Add the introduction question after the greeting |
| `POST` | `/interviews/{session_id}/turn` | Submit a candidate response and receive the next turn |
| `POST` | `/interviews/{session_id}/complete` | End a session and generate final evaluation |
| `POST` | `/audio/transcribe` | Transcribe an uploaded audio file |
| `POST` | `/audio/speak` | Generate WAV speech from interviewer text |

## Health

```bash
curl http://127.0.0.1:8000/health
```

Example:

```json
{
  "status": "ok",
  "openai_configured": false,
  "supabase_configured": false
}
```

## Resume and session bootstrap

```bash
curl -X POST http://127.0.0.1:8000/sessions/bootstrap \
  -F "resume=@docs/examples/sample-resume.pdf;type=application/pdf"
```

Resume rules:

- `.pdf` extension;
- `application/pdf` media type;
- `%PDF-` file signature;
- non-empty content;
- maximum size from `MAX_RESUME_UPLOAD_BYTES`.

The response contains:

```json
{
  "resume": {
    "candidate_name": "Jordan Lee",
    "headline": "Machine Learning Engineer",
    "summary": "..."
  },
  "session": {
    "id": "uuid",
    "current_phase": "phase_1_intro",
    "messages": []
  }
}
```

## Submit an interview turn

```bash
curl -X POST http://127.0.0.1:8000/interviews/SESSION_ID/turn \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_response": "I built a retrieval pipeline and owned its evaluation.",
    "metadata": {
      "source": "text",
      "transcript_retry_count": 0,
      "tab_switch_count": 0,
      "window_blur_count": 0,
      "used_paste": false,
      "camera_enabled": false,
      "realtime_enabled": false
    }
  }'
```

The response includes the complete updated session and `latest_reply`.

## Audio transcription

Accepted extensions include `.flac`, `.m4a`, `.mp3`, `.mp4`, `.oga`, `.ogg`, `.wav`, and `.webm`. The declared media type must match the extension.

```bash
curl -X POST http://127.0.0.1:8000/audio/transcribe \
  -F "audio=@answer.webm;type=audio/webm"
```

## Speech generation

```bash
curl -X POST http://127.0.0.1:8000/audio/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"Tell me about your strongest machine learning project."}' \
  --output interviewer.wav
```

## Important response models

- `ParsedResume`: candidate summary, skills, projects, experience, education, domains, and notes.
- `InterviewSession`: phase, transcript, scores, evaluations, feedback, modes, and integrity metadata.
- `PhaseEvaluation`: score, dimensions, evidence, strengths, weaknesses, suggestion, and confidence.
- `FinalFeedback`: overall summary, strengths, weaknesses, suggestions, role alignment, and integrity notes.

The authoritative schemas are defined in `apps/api/src/interviewing_agent/models.py`.
