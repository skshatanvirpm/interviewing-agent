# Codebase Audit

## Audit status

- Audit date: 2026-06-22
- Scope: repository structure, product documents, frontend, backend, data schema, tests, CI, deployment configuration, secrets handling, and local artifacts
- Constraint: this pass does not intentionally change application behavior

## Hardening update — 2026-06-22

Completed after the initial audit:

- removed markdown credential loading,
- made CORS origins and interviewer identity configurable,
- added PDF signature, extension, media-type, and size validation,
- added audio extension, media-type, and size validation,
- added server-side logging and safe provider error responses,
- separated `pytest` into the API development dependency group,
- fixed clean-clone question-bank behavior by falling back to the retained JSONL artifact,
- replaced externally derived distributable question text with 25 project-authored questions and regenerated embeddings,
- upgraded Next.js from 15.5.15 to 15.5.19, removing the high-severity npm advisories,
- expanded the API suite from 21 to 36 passing tests.

## Hosted deployment update — 2026-06-23

- deployed the static Next.js export and FastAPI service on Render;
- configured exact production CORS and a browser-visible API URL;
- added a shared deployment bearer-token gate and global protected-request limit;
- added local tests for access rejection and request limiting;
- verified synthetic PDF parsing, session bootstrap, one model-backed turn, completion scoring, and speech generation in the hosted API;
- verified hosted home, interview, review, and CORS behavior;
- retained Supabase persistence, user authentication, RLS, retention, and operational monitoring as production-hardening work.

The npm audit still reports two moderate findings because Next.js pins PostCSS 8.4.31 as a private build dependency. The upstream project states that this path runs at build time and is relevant when processing untrusted CSS; this project does not process user-supplied CSS. Track the [upstream issue](https://github.com/vercel/next.js/issues/93234) rather than applying npm's suggested breaking downgrade.

## Baseline verification

The following checks passed before repository cleanup:

| Check | Result |
| --- | --- |
| API test suite | 21 passed |
| Web lint | Passed with zero warnings |
| TypeScript typecheck | Passed |
| Next.js production build | Passed |

The current implementation is functional as a local project. The main gaps are production safety, configuration, operational readiness, and documentation consistency.

## Priority 0 — required before production use

### 1. Remove markdown-based credential loading

**Status: completed.**

`Settings` now loads credentials only from environment variables or root `.env` files. Local markdown credential files are ignored private artifacts and are not parsed by the application.

**Affected areas:** `apps/api/src/interviewing_agent/config.py`, configuration tests, `.env.example`.

### 2. Protect costly and sensitive API operations

**Status: partially completed for the hosted demonstration.**

Resume parsing, interview generation, transcription, and speech routes require a shared deployment bearer token when configured. A global in-memory request limit reduces uncontrolled provider usage.

**Remaining outcome:** replace the shared token with user identity, enforce session-level authorization, and add durable per-user limits and provider-cost ceilings.

### 3. Enable database access controls

The Supabase schema creates application tables but does not enable Row Level Security or define policies. The service-role key bypasses RLS and must remain server-only, but database exposure still needs an explicit security model.

**Required outcome:** enable RLS where appropriate, define ownership policies, and verify that no privileged key is exposed to the browser.

### 4. Define resume privacy and retention behavior

Uploaded resumes and parsed candidate information are persisted without a documented retention period, deletion path, consent record, or data-export process.

**Required outcome:** add consent language, retention rules, deletion support, and storage lifecycle handling before collecting real user data in production.

### 5. Complete production deployment configuration

**Status: completed for the bounded hosted demonstration.**

The Render web and API services are live with exact production-origin configuration. Hosted web, CORS, access control, synthetic PDF bootstrap, model response, completion, scoring, and speech checks pass. Durable Supabase persistence and the controls in findings 2–4 remain required for production use.

## Priority 1 — reliability and maintainability

### 6. Validate uploaded files

**Status: completed for resume and audio uploads.**

Resume and audio endpoints now enforce filename, extension, media-type, empty-file, and configurable size rules. Resume uploads also require a PDF signature.

**Implemented outcome:** explicit accepted types, conservative size limits, malformed-file handling, and tests for rejected uploads.

### 7. Standardize error handling and logging

**Status: partially completed.**

Model fallbacks and provider failures now produce server-side logs. Client responses and resume notes use stable messages without raw provider exception text.

**Remaining outcome:** add correlation IDs, structured production log transport, and explicit fallback metrics.

### 8. Make project identity configurable

**Status: completed for interviewer name, target role, and target company.**

The interviewer name, target company, and target role are configurable through runtime settings. Code defaults no longer name a real company.

**Implemented outcome:** interviewer identity is configurable and example-specific company values are opt-in.

### 9. Separate runtime and development dependencies

**Status: completed for `pytest`.**

`pytest` now lives in the API development dependency group instead of the runtime dependency list.

### 10. Strengthen session consistency

The API keeps an in-memory session store and restores from Supabase when needed. Concurrent workers or overlapping requests can create stale state or last-write-wins behavior.

**Required outcome:** define Supabase as the authoritative session store or add explicit versioning and concurrency controls.

### 11. Expand automated quality checks

Current coverage verifies the core fallback interview flow, scoring calibration, question retrieval, configuration, upload validation, safe provider failures, and resume normalization. Missing areas include:

- persistence contract tests,
- authorization and rate limiting,
- full CORS middleware integration,
- hosted deployment smoke tests,
- Python linting and static analysis.

### 12. Verify third-party data usage

**Status: completed for the distributable question bank.**

The external repository remains acknowledged as a historical discovery reference, but release artifacts now use only the project-authored source at `docs/examples/question-bank-source.md`.

## Priority 2 — project quality improvements

### 13. Split large modules

`interview_engine.py`, `interview-shell.tsx`, and persistence/evaluation modules contain multiple responsibilities. Smaller orchestration, state-transition, provider, and presentation units would reduce change risk.

### 14. Add operational observability

The project does not yet define production metrics for provider latency, token or audio cost, fallback rate, parsing failures, interview completion, persistence failures, or evaluation confidence.

### 15. Add migration management

The Supabase schema is a single idempotent SQL file. A migration history is preferable once multiple environments or existing datasets must be upgraded safely.

### 16. Clarify generated assets

The consolidated markdown question bank is reproducible and ignored, while the embedded JSONL artifact is retained for runtime use. This policy should be documented alongside regeneration and validation commands.

## Repository organization changes completed

- Historical discovery documents moved to `docs/archive/discovery/`.
- The target job description moved to `docs/examples/`.
- Local resume and credential files moved to ignored `private/` storage.
- Generated caches, dependency directories, compiled files, and local build artifacts were removed after verification.
- `.gitignore` was expanded for frontend, Python, editor, deployment, and private files.
- Root project documents were reconciled against the implemented feature set.

## Recommended execution order

1. Security and privacy controls.
2. Production configuration and hosted smoke testing.
3. Upload validation, structured errors, and observability.
4. Dependency and module cleanup.
5. Documentation completion and release packaging.
