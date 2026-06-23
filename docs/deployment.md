# Deployment Guide

## Current deployment model

The project is deployed from `main` using the infrastructure defined in `render.yaml`:

- Static Next.js export: [interviewing-agent-skshatanvirpm.onrender.com](https://interviewing-agent-skshatanvirpm.onrender.com)
- FastAPI service: [interviewing-agent-api-skshatanvirpm.onrender.com](https://interviewing-agent-api-skshatanvirpm.onrender.com)
- Health endpoint: [interviewing-agent-api-skshatanvirpm.onrender.com/health](https://interviewing-agent-api-skshatanvirpm.onrender.com/health)

Both services use Render's free plan. Render automatically rebuilds them when `main` changes. GitHub Actions runs a hosted availability and CORS check after each push.

## Topology

```text
Browser
  -> Render static Next.js export
  -> Render FastAPI web service
  -> OpenAI APIs
  -> Optional Supabase Postgres and private Storage
```

The hosted environment currently uses in-memory sessions because Supabase is not configured. Durable persistence remains available in the codebase but requires valid Supabase runtime credentials and schema setup.

## Blueprint

Validate the infrastructure definition with the Render CLI:

```bash
render blueprints validate render.yaml
```

The Blueprint defines:

- a Python web service rooted at `apps/api`;
- a static web build published from `apps/web/out`;
- the exact production web origin for API CORS;
- a browser-visible API base URL;
- required secret placeholders for `OPENAI_API_KEY` and `API_ACCESS_TOKEN`;
- a per-client API request limit.

Secret values must be configured in Render. They must never be added to `render.yaml` or GitHub.

## Web build

The production static export uses:

```bash
NEXT_OUTPUT_EXPORT=true npm run build:web
```

The hosted build also sets:

- `NEXT_PUBLIC_API_URL=https://interviewing-agent-api-skshatanvirpm.onrender.com`
- `NEXT_PUBLIC_REQUIRE_ACCESS_TOKEN=true`

The deployment access token value is entered at runtime and stored only in browser `sessionStorage`. It is not a `NEXT_PUBLIC_` build variable. Interview bootstrap responses also issue a per-session token that is sent as `X-Interview-Session-Token` for session state routes.

## API runtime

Render starts the API with:

```bash
PYTHONPATH=src uv run --no-sync uvicorn interviewing_agent.main:app \
  --host 0.0.0.0 --port "$PORT" --proxy-headers
```

The hosted API requires:

- `OPENAI_API_KEY`
- `API_ACCESS_TOKEN`
- `API_RATE_LIMIT_PER_MINUTE`
- `INTERVIEW_DATA_RETENTION_DAYS`
- `INTERVIEW_RETENTION_CLEANUP_ENABLED`
- exact `CORS_ALLOWED_ORIGINS`

Supabase variables are additionally required for durable persistence.

## Hosted verification

Run the non-secret web and CORS checks:

```bash
API_BASE_URL="https://interviewing-agent-api-skshatanvirpm.onrender.com" \
WEB_ORIGIN="https://interviewing-agent-skshatanvirpm.onrender.com" \
node scripts/hosted_web_smoke_test.mjs
```

Run the protected end-to-end API flow with a deployment token supplied through the environment:

```bash
API_BASE_URL="https://interviewing-agent-api-skshatanvirpm.onrender.com" \
WEB_ORIGIN="https://interviewing-agent-skshatanvirpm.onrender.com" \
API_ACCESS_TOKEN="..." \
node scripts/hosted_smoke_test.mjs
```

The protected smoke test verifies:

1. health and provider configuration;
2. anonymous request rejection;
3. synthetic PDF parsing, session bootstrap, and session-token issuance;
4. one model-backed interview turn;
5. interview completion, scoring, and feedback;
6. WAV speech generation.

## Free-plan behavior

- The API may spin down after inactivity and take longer on the next request.
- In-memory sessions are lost when the API restarts.
- Free hosting is suitable for project demonstration and testing, not a production SLA.
- Provider usage still consumes OpenAI credits; the deployment access token, session tokens, and request limit reduce unintended use.

## Database setup

Apply `supabase/schema.sql` to the target project. It defines the product tables, token-hash column, private-storage policy, RLS enablement, and service-role-only table policies. Before enabling durable public use, verify:

- Row Level Security behavior with non-privileged credentials;
- backup and recovery configuration;
- storage lifecycle and deletion behavior in the target project;
- migration management;
- least-privilege service access.

## Rollback

- Render: redeploy one of the retained successful deployments.
- Git: revert the change on `main`; Render will rebuild automatically.
- Database: prefer forward-compatible migrations and avoid destructive rollback scripts.
- Secrets: restore a controlled prior value only when necessary, then rotate it.
