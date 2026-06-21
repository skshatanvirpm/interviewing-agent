# Third-Party Notices

## Direct software dependencies

The project uses open-source packages including:

- MIT: Next.js, React, React DOM, FastAPI, Pydantic Settings, pytest, ESLint, and ESLint Config Next.
- Apache-2.0: OpenAI's Python SDK, python-multipart, and TypeScript.
- BSD-3-Clause: HTTPX, PyPDF, and Uvicorn.
- ISC: Lucide React.

Their license texts and transitive dependency notices are distributed through the respective package artifacts installed from `package-lock.json` and `apps/api/uv.lock`. Before producing a standalone binary or container for redistribution, generate and retain a complete software bill of materials and bundled license report.

## ML question-bank provenance

The original product discovery referenced [andrewekhalel/MLQuestions](https://github.com/andrewekhalel/MLQuestions). As reviewed on 2026-06-22, the repository root displayed `README.md` and an `NLP` directory but no license file. Its README also attributes material to additional external sources.

The distributable question-bank source in this project is therefore project-authored at `docs/examples/question-bank-source.md`. The generated `apps/api/data/question_bank.jsonl` must be built from that local source. No text from MLQuestions is intended to be redistributed in the release artifact.

## Example job description

`docs/examples/job-description.md` is a fictional role specification authored for this project.

## Project license

The project-authored source and documentation are released under the repository-level MIT License. Third-party components retain the licenses listed above.
