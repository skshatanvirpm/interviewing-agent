# Deployment Guide

## Current deployment model

The repository contains:

- a Vercel deployment step for the Next.js application;
- an API deploy-hook integration point for a separately hosted FastAPI service.

The workflow is scaffolding until real hosting targets and secrets are configured and a hosted smoke test passes.

## Recommended topology

```text
Browser
  -> Vercel-hosted Next.js application
  -> HTTPS FastAPI service
  -> OpenAI APIs
  -> Supabase Postgres and private Storage
```

## Web deployment

Configure these GitHub Actions secrets:

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`

Configure `NEXT_PUBLIC_API_URL` in the Vercel project before building. It must reference the public HTTPS API URL.

## API deployment

Choose a Python hosting platform that supports:

- Python 3.12 or later;
- ASGI applications;
- environment secrets;
- health checks;
- request-size controls;
- HTTPS;
- persistent logs.

Example start command:

```bash
PYTHONPATH=src uv run uvicorn interviewing_agent.main:app --host 0.0.0.0 --port "$PORT"
```

Set `API_DEPLOY_HOOK_URL` in GitHub Actions if the provider supports deploy hooks.

## Required production environment

- all OpenAI variables required by enabled features;
- Supabase URL and keys for persistence;
- exact production `CORS_ALLOWED_ORIGINS`;
- production interviewer, role, and company values;
- conservative upload limits and log level;
- `NEXT_PUBLIC_API_URL` in the web build environment.

## Database setup

Apply `supabase/schema.sql` to the target project. Before public production use, add and verify:

- Row Level Security policies;
- backup and recovery configuration;
- storage lifecycle and deletion behavior;
- migration management;
- least-privilege service access.

## Hosted smoke test

After deployment:

1. `GET /health` returns `200`.
2. The web application loads without mixed-content or CORS errors.
3. A synthetic PDF completes bootstrap.
4. One interview turn succeeds.
5. A completed session renders the review page.
6. Persistence survives API restart when Supabase is enabled.
7. Provider errors do not expose credentials or internal exception text.

## Rollback

- Vercel: promote the previous successful deployment.
- API: redeploy the previous image or release revision.
- Database: prefer forward-compatible migrations; do not rely on destructive rollback scripts.
- Provider configuration: keep prior secret values available only for controlled emergency rollback, then rotate them.
