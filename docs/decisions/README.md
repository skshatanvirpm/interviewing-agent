# Architecture Decision Records

## ADR-001 — Monorepo with separate web and API applications

- Status: Accepted
- Decision: Keep the Next.js client and FastAPI service in one repository with independent dependency systems.
- Rationale: Shared product changes remain reviewable while frontend and backend deployment stay independent.
- Consequence: CI must validate both ecosystems and developers need Node, Python, and `uv`.

## ADR-002 — Backend-owned AI and persistence integrations

- Status: Accepted
- Decision: OpenAI and Supabase privileged calls remain behind FastAPI.
- Rationale: Provider credentials, prompts, validation, fallbacks, and persistence rules require a controlled server boundary.
- Consequence: The API becomes the operational bottleneck and requires authentication and rate limiting before public use.

## ADR-003 — Turn-based audio as the reliable baseline

- Status: Accepted
- Decision: Treat record-transcribe-submit-respond as the supported audio workflow. Keep browser realtime assistance optional.
- Rationale: Turn-based audio is easier to recover, test, and persist than duplex streaming.
- Consequence: Conversation latency is higher than a full realtime implementation.

## ADR-004 — Deterministic fallbacks

- Status: Accepted
- Decision: Keep local resume extraction, deterministic phase progression, and hashing embeddings.
- Rationale: Core flows remain testable without provider credentials or network access.
- Consequence: Fallback quality is intentionally lower and must be presented as degraded operation.

## ADR-005 — Project-authored distributable question bank

- Status: Accepted
- Decision: Distribute only project-authored question content and derived embeddings.
- Rationale: The external MLQuestions repository used during discovery does not expose a repository license, and its README aggregates material from additional sources.
- Consequence: The local bank is smaller but has a clear provenance and can be expanded through reviewed contributions.

## ADR-006 — MIT License

- Status: Accepted
- Decision: Release the project under the MIT License.
- Rationale: The license is concise, permissive, and familiar for a demonstration-oriented software project.
- Consequence: Reuse, modification, and redistribution are allowed when the copyright and permission notices are preserved.
