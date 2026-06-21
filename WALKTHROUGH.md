# WALKTHROUGH: Interviewing Agent

## Current architecture

The project is a small monorepo with a Next.js client, FastAPI service, Supabase data layer, and OpenAI-backed model and audio integrations.

- `apps/web`: resume upload, interview workspace, audio capture, optional camera preview, and final review UI.
- `apps/api`: resume parsing, interview orchestration, question retrieval, scoring, persistence, transcription, and speech output.
- `supabase/schema.sql`: candidate, resume, interview, transcript, evaluation, and question-bank tables.
- `docs/examples/job-description.md`: example role input used for role alignment.
- `apps/api/data/question_bank.jsonl`: embedded factual-question artifact used by the retrieval service.

## Core flow

1. The candidate uploads a PDF or reuses a previously parsed local snapshot.
2. The API parses and normalizes the resume.
3. The interview engine creates a session and begins the introduction phase.
4. Candidate turns are captured as text, recorded audio, or optional browser realtime input.
5. The engine advances through project depth, secondary experience, factual ML, and behavioral phases.
6. Session state, messages, evaluations, and feedback are persisted when Supabase is configured.
7. The candidate ends the interview and opens the review route for phase scores and final feedback.

## Main modules

| Module | Responsibility |
| --- | --- |
| `services/interview_engine.py` | Session state, phase transitions, questioning, hints, integrity metadata, and orchestration |
| `services/resume_parser.py` | OpenAI PDF parsing, local extraction fallback, normalization, and domain inference |
| `services/question_bank.py` | Question parsing, embedding metadata, ranking, and duplicate avoidance |
| `services/evaluation.py` | Phase evaluation, evidence extraction, final score, and feedback |
| `services/persistence.py` | Supabase storage and restoration |
| `services/audio.py` | Transcription and interviewer speech |
| `components/interview-shell.tsx` | Main interview interaction and client state |
| `components/review-shell.tsx` | Completed-session review |
| `components/realtime-listener.tsx` | Browser realtime-assist behavior |
| `components/video-preview.tsx` | Optional local camera preview |

## Runtime behavior

- OpenAI-backed behavior is used when an API key is configured.
- Deterministic fallbacks keep the core local flow testable without provider access.
- Supabase is optional for local exploration and required for durable persistence.
- Environment variables and root `.env` files are the supported configuration path.
- Interviewer identity, target role/company, allowed web origins, upload limits, and log level are configurable.
- Resume uploads require a PDF extension, PDF media type, valid PDF signature, and compliance with the configured size limit.
- Audio uploads require a supported extension, matching media type, and compliance with the configured size limit.
- Provider exceptions are logged server-side while clients receive stable, non-sensitive errors.
- Sessions are cached in memory and can be restored from Supabase.
- Browser integrity telemetry records events such as focus loss, tab changes, paste activity, retries, and camera consent.
- Camera preview does not analyze facial expressions, identity, or behavior.
- Realtime assist is browser based and is not full duplex model streaming.

## Repository-readiness changes

- Historical discovery files are archived under `docs/archive/discovery`.
- The example role input is under `docs/examples`.
- A synthetic PDF resume is available for repeatable local walkthroughs.
- Project-authored question content replaces externally derived distributable data.
- Real resumes and credentials are isolated under ignored `private/` storage.
- Repository hygiene rules now cover build output, caches, editor files, deployment state, environment files, and private material.
- Product, task, sprint, and walkthrough documents now distinguish implemented behavior from deferred production work.
- The prioritized engineering assessment is available in `docs/audits/codebase-audit.md`.
- Runtime and development Python dependencies are separated, and clean-clone question-bank tests use the retained JSONL artifact.
- Maintained architecture, API, configuration, testing, deployment, security, limitations, decision, contribution, and release documents are cross-linked from the README.
- Four synthetic-data screenshots document the home, parsed-resume, interview, and review states.

## Current limitations

- Authentication, rate limiting, RLS policies, and retention/deletion behavior are not implemented.
- Production allowed origins must be supplied through configuration.
- The deployment workflow is scaffolding until hosted web and API paths pass an end-to-end smoke test.

## Verification commands

```bash
npm run test:api
npm run lint:web
npm run typecheck:web
npm run build:web
```
