# SPRINTS: Interviewing Agent

## Planning Model

This project is being tracked in version-based sprints. Each version groups work that should produce a visible product step forward rather than a purely internal checklist.

## v0.1 Foundation Scaffold

- Status: Completed
- Objective: Stand up the repo, web shell, API shell, starter schema, and the first end-to-end local development loop.
- Included task IDs: `IA-101`, `IA-102`, `IA-103`, `IA-104`, `IA-105`, `IA-201`, `IA-202`, `IA-301`, `IA-401`, `IA-601`, `IA-602`
- Exit criteria:
  - monorepo structure exists,
  - web and API apps boot locally,
  - resume upload bootstrap flow exists,
  - interview session engine exists,
  - starter schema and question-bank assets exist.

## v0.2 Persistent Resume-to-Interview Core

- Status: Completed
- Objective: Turn the current scaffold into a persistent product loop where parsed resumes, interview sessions, and transcript state survive beyond local process memory.
- Included task IDs: `IA-203`, `IA-204`, `IA-302`, `IA-303`, `IA-603`, `IA-701`, `IA-702`
- Follow-up note: the environment-variable runtime path was delivered here; complete removal of the compatibility markdown loader was reopened under v0.6.
- Exit criteria:
  - parsed resume data persists to Supabase,
  - interview transcript and phase progress persist to Supabase,
  - all five phases are explicitly aligned to the PRD behavior,
  - the app no longer depends on markdown-secret fallback for normal runtime use.

## v0.3 Role-Aligned Retrieval and Scoring

- Status: Completed
- Objective: Make the interviewer role-aware, evidence-based, and capable of producing credible performance feedback.
- Included task IDs: `IA-304`, `IA-305`, `IA-402`, `IA-403`, `IA-404`, `IA-501`, `IA-502`, `IA-503`
- Completed in this sprint so far: `IA-304`, `IA-305`, `IA-402`, `IA-403`, `IA-404`, `IA-501`, `IA-502`, `IA-503`
- Exit criteria:
  - hints and recovery are supported in project phases,
  - factual question retrieval uses embeddings and role/domain tags,
  - fallback question generation exists,
  - phases 2 through 5 are scored with evidence,
  - final feedback screen shows overall interview performance and improvement guidance.

## v0.4 Audio Polish and MVP Hardening

- Status: Completed
- Objective: Make the V1 experience resilient enough for repeated realistic practice sessions.
- Included task IDs: `IA-604`, `IA-703`, `IA-704`
- Completed in this sprint so far: `IA-604`, `IA-703`, `IA-704`
- Exit criteria:
  - candidate can recover from failed audio turns,
  - core flows have end-to-end coverage,
  - evaluation behavior is checked against fixed examples for regression control.

## v0.5 Expansion Modes and Delivery

- Status: Completed
- Objective: Expand the MVP with optional interaction modes, deployment scaffolding, and lightweight integrity telemetry.
- Included task IDs: `IA-801`, `IA-802`, `IA-803`, `IA-804`
- Completed: `IA-801`, `IA-802`, `IA-803`, `IA-804`
- Exit criteria:
  - browser realtime-assist mode exists with interruption handling,
  - optional camera preview exists without video analysis,
  - CI runs automatically,
  - deployment paths are configured and validated in a hosted environment,
  - lightweight integrity signals are surfaced without claiming identity verification.

## v0.6 Repository Readiness and Hardening

- Status: Completed
- Objective: Make the project structurally clear, safe to version, and ready for production-hardening work.
- Included task IDs: `IA-702`, `IA-803`, `IA-805`, `IA-806`, `IA-807`, `IA-808`, `IA-903`, `IA-904`
- Completed: `IA-702`, `IA-803`, `IA-805`, `IA-806`, `IA-807`, `IA-808`, `IA-903`, `IA-904`
- Exit criteria:
  - private and generated files cannot enter version control accidentally,
  - maintained documents agree with implemented behavior,
  - the legacy markdown-secret path is removed,
  - CORS, interviewer identity, upload limits, and provider errors are hardened,
  - distributable question-bank content has clear project-owned provenance,
  - session authorization, per-client limiting, RLS schema policies, and retention/deletion controls are implemented,
  - hosted deployment passes an end-to-end smoke test,
  - maintained project documentation covers architecture, operations, testing, deployment, and limitations.
