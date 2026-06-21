# Security and Privacy

## Current controls

- Credentials load from environment variables or ignored root environment files.
- Supabase service-role credentials remain server-side.
- CORS origins are explicit and validated.
- Resume and audio uploads enforce extension, media type, non-empty content, and size limits.
- Resume uploads require a PDF signature.
- Provider exceptions are logged server-side and sanitized for clients.
- Private local files and environment files are excluded from version control.
- CI fails on high or critical npm advisories.

## Data handled

The product may process:

- resume files and parsed career information;
- interview transcripts and audio;
- model-generated questions and evaluations;
- optional camera-consent and browser-integrity metadata;
- provider and infrastructure telemetry.

This information can be personal and should be treated as sensitive.

## Required before public production use

### Access control

- Authenticate users or issue bounded anonymous session tokens.
- Authorize every session read/write operation.
- Add rate limits and provider-cost quotas.
- Prevent session enumeration and cross-user access.

### Supabase

- Enable Row Level Security and define ownership policies.
- Confirm the browser never receives the service-role key.
- Use a private resume bucket.
- Add retention and deletion procedures.
- Test access using non-privileged credentials.

### Privacy

- Obtain explicit consent before storing resumes, transcripts, audio, or camera-related signals.
- Publish a retention period.
- Provide deletion and export paths.
- Minimize integrity telemetry and avoid presenting it as definitive cheating detection.
- Document provider data processing and regional requirements.

### Operations

- Add request correlation IDs and centralized log transport.
- Alert on provider failures, unusual request volume, and persistence errors.
- Redact sensitive payloads from logs.
- Rotate secrets and use separate development/production credentials.

## Threats to consider

- unrestricted API use causing provider cost;
- malicious or oversized uploads;
- prompt injection through resume or job-description content;
- horizontal access to another interview session;
- service-role key exposure;
- resume leakage through storage configuration or logs;
- unsupported evaluation claims being treated as objective decisions;
- stale in-memory state in multi-worker deployments.

## Reporting

Use the private reporting process in the repository-level `SECURITY.md`. Do not open public issues containing credentials, real resumes, transcripts, or exploitable details.
