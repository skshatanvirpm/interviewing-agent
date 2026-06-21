# Limitations

## Product limitations

- The product is optimized for ML, GenAI, recommendation, and adjacent engineering roles.
- Evaluation is heuristic and model-assisted; scores are practice feedback, not validated hiring decisions.
- Deterministic fallback behavior is useful for testing but less adaptive than the model-backed path.
- The question bank is intentionally compact and should be expanded with reviewed, project-authored content.
- Browser speech recognition support varies by browser.
- Realtime assist is not full duplex model streaming.
- Camera mode is a local preview and does not analyze identity, emotion, attention, or behavior.
- Integrity metadata is weak contextual evidence and must not be treated as proof of misconduct.

## Technical limitations

- In-memory session caching is not concurrency-safe across multiple API workers.
- Supabase persistence uses direct REST calls and a privileged server key.
- The schema is maintained as one idempotent SQL file rather than versioned migrations.
- Authentication, authorization, rate limiting, RLS, retention, and deletion APIs are not implemented.
- Production deployment has not been verified against a hosted environment.
- Provider latency, cost, fallback rate, and evaluation quality are not centrally monitored.
- Some PDF layouts may extract poorly in the local fallback path.

## Evaluation limitations

- Phase scores depend on available transcript evidence.
- Keyword and heuristic dimensions can reward terminology without proving correctness.
- Model-generated questions and feedback can vary.
- Calibration fixtures are synthetic and limited in breadth.
- The system should not be used for autonomous employment decisions.

## Repository limitations

- The project is released under the MIT License; third-party components retain their own licenses.
- Two moderate npm findings remain because Next.js pins a build-time PostCSS version. No high or critical findings remain.
- A live demo URL and hosted deployment evidence are not yet available.
