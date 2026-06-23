# Release Checklist

## Repository

- [x] Repository structure is organized.
- [x] Private files, environments, builds, and caches are ignored.
- [x] README and maintained project documents agree.
- [x] Architecture, API, configuration, testing, deployment, security, and limitations are documented.
- [x] Synthetic sample resume and project-authored question-bank source are included.
- [x] Screenshots use synthetic data.
- [x] Contribution and security-reporting guidance exist.
- [x] Third-party notices are documented.
- [x] MIT `LICENSE` is included.
- [x] Git repository is initialized on `main`.
- [x] GitHub owner `skshatanvirpm`, repository `interviewing-agent`, public visibility, description, and topics are selected.
- [x] The repository is published and synchronized with `origin/main`.

## Quality

- [x] API tests pass.
- [x] Web lint passes.
- [x] TypeScript typecheck passes.
- [x] Production web build passes.
- [x] Clean install from lockfiles passes.
- [x] No high or critical npm advisories remain.
- [x] Credential and personal-path scans pass.
- [x] Local browser smoke test passes.

## Data and attribution

- [x] Real resumes remain outside version control.
- [x] Distributed question-bank text is project-authored.
- [x] External discovery sources are acknowledged without redistributing their text.
- [x] Generated artifacts have documented regeneration paths.
- [x] Example job description is fictional and safe to distribute.

## Production release

- [x] Bounded anonymous session authorization is implemented.
- [x] In-memory per-client rate limits are implemented.
- [ ] Full user-account authentication is implemented.
- [ ] Durable provider-cost quotas are implemented.
- [x] Shared hosted access token and per-client request limit are configured.
- [x] Supabase RLS policies are defined in the schema.
- [x] Resume/interview deletion and retention cleanup behavior are implemented.
- [ ] Supabase RLS policies are tested against a deployed project with non-privileged credentials.
- [ ] Data export behavior is implemented.
- [x] Hosting provider and free demonstration services are selected.
- [ ] Production environment variables are configured.
- [x] Hosted protected API and web/CORS smoke tests pass.
- [ ] Monitoring, alerting, backup, and rollback procedures are verified.

## GitHub repository

- Repository: [skshatanvirpm/interviewing-agent](https://github.com/skshatanvirpm/interviewing-agent)
- Default branch: `main`
- Visibility: public
- License: MIT
- Continuous integration: enabled
- Live application: [interviewing-agent-skshatanvirpm.onrender.com](https://interviewing-agent-skshatanvirpm.onrender.com)
- API health: [interviewing-agent-api-skshatanvirpm.onrender.com/health](https://interviewing-agent-api-skshatanvirpm.onrender.com/health)
