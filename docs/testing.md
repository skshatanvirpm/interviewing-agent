# Testing and Verification

## Local verification

Install dependencies:

```bash
npm ci
(cd apps/api && uv sync --locked --dev)
```

Run all maintained checks:

```bash
npm run test:api
npm run lint:web
npm run typecheck:web
npm run build:web
npm audit --audit-level=high
```

## API test coverage

The test suite covers:

- interview bootstrap, phase progression, early completion, and feedback;
- hint recovery, anxiety handling, and phase guardrails;
- question-bank parsing, embeddings, ranking, and duplicate avoidance;
- evaluation calibration fixtures;
- resume normalization and local parsing fallback;
- environment-only credential behavior and CORS validation;
- resume/audio upload validation and size limits;
- safe provider error handling;
- audio route contracts through stubs.

## Browser smoke test

1. Start the API and web applications.
2. Open `http://127.0.0.1:3000`.
3. Upload `docs/examples/sample-resume.pdf`.
4. Confirm the parsed preview appears.
5. Start the interview and submit one text response.
6. End the interview.
7. Confirm the review page renders an overall score and feedback.

Camera and microphone paths require explicit browser permissions and should be tested separately.

## CI

`.github/workflows/ci.yml` runs on pull requests and pushes to `main`. It:

1. installs locked Node dependencies;
2. fails on high or critical npm advisories;
3. installs locked API and development dependencies;
4. runs web lint, typecheck, and production build;
5. runs the API test suite.

## Known dependency advisory

Next.js 15.5.19 pins PostCSS 8.4.31 as a private build dependency. `npm audit` reports two moderate findings. No high or critical advisories remain. The project does not process untrusted CSS, and the release gate remains `npm audit --audit-level=high` while the upstream issue is tracked.

## Test-data rules

- Use only synthetic resumes and interview responses in committed fixtures.
- Do not record provider responses containing personal resume content.
- Keep real resumes under ignored private storage.
- Calibration fixtures should describe synthetic candidates and avoid real company-confidential information.
