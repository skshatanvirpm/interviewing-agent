# TASKS: Interviewing Agent

## Status Legend

- `done`: built and present in the repo
- `in_progress`: partially built or scaffolded but not complete against the PRD
- `blocked`: ready to continue, but external input or credentials are missing
- `todo`: not started yet

## Runtime Inputs

- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- Runtime values can be resolved from a Supabase PAT with `scripts/bootstrap_supabase_runtime.py`.

## Active Execution Checklist

1. `done` — IA-805 Organize repository files and project documents.
2. `done` — IA-806 Complete the repository and codebase audit.
3. `done` — IA-702 Remove the legacy markdown-secret runtime path.
4. `done` — IA-807 Harden configuration, uploads, and provider error handling.
5. `done` — IA-803 Validate CI/CD and hosted deployment.
6. `done` — IA-903 Add production security and privacy controls.
7. `done` — IA-904 Complete the maintained project documentation suite.
8. `done` — IA-808 Replace externally derived question data with project-authored content.

## Milestone 0. Product and Planning

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-001 | done | PM | - | Create the project PRD | `PRD.md` exists with problem, persona, scope, requirements, metrics, risks, and out-of-scope items. |
| IA-002 | done | PM | IA-001 | Capture the target role in structured form | `docs/examples/job-description.md` contains the example role details and interview focus areas. |
| IA-003 | done | PM | IA-001 | Lock V1 product decisions | Turn-based audio and responsive web-only scope are explicitly documented. |

## Milestone 1. Foundation and Repo Setup

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-101 | done | Full-stack | - | Create monorepo scaffold | Root workspace, web app, API app, schema folder, and helper scripts exist and run locally. |
| IA-102 | done | Backend | IA-101 | Create FastAPI service shell | API app boots with routes, settings, and domain model structure. |
| IA-103 | done | Frontend | IA-101 | Create Next.js app shell | Web app boots with typed routes and base UI structure. |
| IA-104 | done | Infra | IA-101 | Add local environment template | `.env.example` documents the expected runtime configuration. |
| IA-105 | done | Data | IA-101 | Draft Supabase schema | `supabase/schema.sql` exists with the initial interview-domain tables. |

## Milestone 2. Resume Ingestion

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-201 | done | Frontend | IA-103 | Build resume upload UI | The web app exposes a resume upload flow the candidate can use to start the process. |
| IA-202 | done | Backend | IA-102 | Implement resume parsing pipeline | Backend service accepts resume input and returns structured resume data. |
| IA-203 | done | Backend | IA-202, IA-105 | Persist parsed resume data in Supabase | Resume metadata, parsed sections, and storage references are saved in Supabase, not only held in process memory. |
| IA-204 | done | Backend | IA-202 | Harden parsing and normalization | Resume parser handles common PDF edge cases and preserves consistent section output. |

## Milestone 3. Interview Orchestration

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-301 | done | Backend | IA-102 | Create interview session engine | The API can start and advance an interview session across phases. |
| IA-302 | done | Backend | IA-301, IA-002 | Align all five phases to the PRD | Each phase now follows the documented purpose, role alignment, scoring behavior, and end-of-interview feedback expectations from `PRD.md`. |
| IA-303 | done | Backend | IA-301, IA-105 | Persist transcript and phase progress | Messages, phase transitions, and interview state survive process restarts through Supabase storage. |
| IA-304 | done | Backend | IA-302 | Implement hint-and-recovery behavior | The interviewer can issue hints in project phases and the engine records recovery evidence. |
| IA-305 | done | Backend | IA-302 | Add anxiety-aware interviewer responses | The interviewer can slow pacing or offer calm prompts when hesitation patterns indicate stress. |

## Milestone 4. Question Bank and Retrieval

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-401 | done | Data | IA-101 | Ingest curated ML question source | The source-ingestion script can regenerate the markdown bank and the repository contains the embedded JSONL runtime artifact. |
| IA-402 | done | Data | IA-401, IA-105 | Create embeddings and vector storage | Question-bank entries are parsed, tagged, embedded into 384-dimensional vectors, and exported in a storage-ready format that matches the `pgvector` schema. |
| IA-403 | done | Backend | IA-402, IA-002 | Build role-aware question retrieval | The engine retrieves factual questions from the embedded bank using resume domains, job-description signals, duplicate avoidance, and scored ranking over stored vectors and tags. |
| IA-404 | done | Backend | IA-403 | Add generated fallback questions | The system can synthesize factual questions when retrieval coverage is weak. |

## Milestone 5. Evaluation and Feedback

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-501 | done | Backend | IA-302, IA-403 | Build phase scoring engine | Phases 2 through 5 produce structured scores with evidence and phase-specific dimensions. |
| IA-502 | done | Backend | IA-501 | Compute weighted final score | Final score follows the PRD weights and includes a written explanation. |
| IA-503 | done | Frontend | IA-502 | Build final feedback UI | Candidate can see overall performance, phase scores, strengths, weaknesses, and suggestions at the end. |

## Milestone 6. Audio Experience

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-601 | done | Frontend | IA-103 | Add microphone capture component | The client can record candidate audio in the interview flow. |
| IA-602 | done | Backend | IA-102 | Add transcription and speech output routes | The API exposes speech-to-text and text-to-speech endpoints for interview turns. |
| IA-603 | done | Full-stack | IA-601, IA-602, IA-301 | Connect audio loop to interview state | The UI and API support a reliable turn-based talk-listen-respond loop with transcript updates, session restore, and optional realtime assist mode. |
| IA-604 | done | Frontend | IA-603 | Add pause, retry, and recovery UX | Candidate can retry a failed audio turn and resume the interview without losing context. |

## Milestone 7. Persistence, Config, and Hardening

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-701 | done | Backend | IA-105 | Wire real Supabase runtime configuration | Backend uses supplied Supabase URL and keys for live persistence paths. |
| IA-702 | done | Full-stack | IA-701 | Remove markdown-secret dependency from app flow | Environment variables are the only supported credential source and the legacy markdown loader and test are removed. |
| IA-703 | done | QA / Full-stack | IA-203, IA-303, IA-503, IA-603 | Add end-to-end MVP tests | Core flows are covered from resume upload to final feedback generation. |
| IA-704 | done | QA / Backend | IA-501 | Add evaluation calibration fixtures | Example interviews exist to sanity-check scoring consistency and feedback quality. |

## Milestone 8. Expansion and Repository Readiness

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-801 | done | Full-stack | IA-603 | Add browser realtime-assist mode | Browser speech recognition, speech playback, and interruption handling provide an optional lower-friction interaction mode. |
| IA-802 | done | Frontend | IA-503 | Add optional camera preview | Candidate can enable a local camera preview without facial or behavioral analysis. |
| IA-803 | done | Infra | IA-703 | Add CI/CD and validate deployment | CI passes automatically; Render hosts the static web app and FastAPI service; protected API, model, audio, web-route, and CORS smoke tests pass. |
| IA-804 | done | Risk / Product | IA-703 | Add lightweight integrity telemetry | Tab switches, focus loss, paste events, camera consent, and retry signals are recorded and surfaced without claiming identity verification. |
| IA-805 | done | PM / Full-stack | IA-703 | Organize repository files and documents | Historical, example, private, generated, and maintained project files have clear locations and ignore rules. |
| IA-806 | done | PM / Full-stack | IA-805 | Audit the repository and codebase | `docs/audits/codebase-audit.md` records evidence, risks, priorities, and the recommended execution order. |
| IA-807 | done | Backend / Full-stack | IA-702, IA-806 | Harden configuration, uploads, and provider errors | CORS and interviewer identity are configurable; uploads enforce type and size rules; provider failures use safe responses and server logs; test dependencies are separated. |
| IA-808 | done | Data / Full-stack | IA-806 | Replace externally derived question data | The distributable source and 384-dimensional JSONL artifact contain project-authored questions with documented provenance. |
| IA-903 | done | Backend / Infra | IA-806, IA-807 | Add production security and privacy controls | Session authorization, per-client rate limiting, RLS schema policies, and retention/deletion behavior are implemented and tested. |
| IA-904 | done | PM / Full-stack | IA-806, IA-808 | Complete maintained project documentation | Architecture, API, configuration, testing, deployment, security, limitations, decisions, release guidance, examples, and screenshots are complete and cross-linked. |

## Deferred Product Backlog

| ID | Status | Owner | Depends On | Task | Done Criteria |
| --- | --- | --- | --- | --- | --- |
| IA-901 | todo | Full-stack | IA-801 | Add full duplex model-streaming audio | The system supports server-controlled streaming audio, turn detection, and interruption recovery with measured latency. |
| IA-902 | todo | Product / Risk | IA-802, IA-903 | Evaluate advanced video analysis | A separate privacy and value assessment justifies any video-derived signals before implementation. |
