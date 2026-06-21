# Contributing

## Development setup

```bash
npm ci
(cd apps/api && uv sync --locked --dev)
cp .env.example .env
```

Run the API and web application in separate terminals:

```bash
npm run dev:api
npm run dev:web
```

## Before submitting a change

```bash
npm run test:api
npm run lint:web
npm run typecheck:web
npm run build:web
npm audit --audit-level=high
```

## Change expectations

- Keep behavior and documentation in the same change.
- Add tests for API contracts, fallbacks, validation, and scoring changes.
- Keep frontend and backend types synchronized.
- Use synthetic resumes and interview content.
- Do not commit credentials, `.env` files, real resumes, transcripts, generated builds, or local caches.
- Add question-bank content only when it is original or has explicit compatible licensing and attribution.
- Update `TASKS.md`, `SPRINTS.md`, and `WALKTHROUGH.md` when implementation status changes.

## Pull requests

Describe:

- the problem and intended outcome;
- affected frontend, backend, data, or provider contracts;
- verification performed;
- security, privacy, latency, cost, or evaluation trade-offs;
- remaining limitations.
