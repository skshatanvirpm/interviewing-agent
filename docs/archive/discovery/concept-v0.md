# Interviewing Agent PRD

## 1. Product Summary

Build an audio-first mock interviewing agent for Machine Learning / Learning Engineer candidates. The system should behave like a professional human interviewer, conduct a structured interview based on the candidate's resume and target job description, go deep into the candidate's projects using a Russian Doll / Socratic questioning style, ask factual and behavioral questions, and generate phase-wise scores plus a final combined score.

This should be built in phases, starting with a focused MVP and leaving video analysis, anti-cheating, CI/CD, and cloud deployment for later versions.

## 2. Core Goal

The product should not just ask generic interview questions. It should:

- parse the candidate's resume,
- understand the candidate's likely domain and strengths,
- run a realistic interview,
- keep drilling into answers until the candidate either demonstrates genuine understanding or reaches the limit of their knowledge,
- align questions and evaluation to the target Machine Learning Engineer / Learning Engineer job description,
- provide hints when the candidate gets stuck,
- evaluate performance with a robust scoring framework,
- maintain a professional, concise, and interviewer-like tone throughout.

## 3. Target User

The primary user is a student or job seeker preparing for Machine Learning Engineer / Learning Engineer interviews.

## 4. MVP Scope

### In scope for V1

- Resume upload through PDF
- Resume parsing and section extraction
- Supabase-backed storage for structured candidate data
- Audio conversation between candidate and interviewer
- Five-phase interview flow
- Deep follow-up questioning for project-based phases
- Hints when the candidate is stuck
- Factual ML question retrieval from a curated question bank
- Behavioral interview round
- Phase-wise scoring and final overall score
- Final feedback report

### Explicitly out of scope for V1

- Video interview
- Facial analysis
- Anti-cheating / face recognition
- CI/CD
- GitHub-to-AWS deployment pipeline
- Advanced proctoring

These should be treated as later-version features, not part of the first build.

## 5. Candidate Journey

### Step 1. Resume Upload

The candidate uploads a resume PDF.

### Step 2. Resume Parsing

The system sends the PDF to OpenAI for parsing, extracts structured sections, and stores them in Supabase. The extracted structure should include:

- personal basics if available,
- education,
- work experience,
- internships,
- projects,
- research,
- skills,
- tools and technologies,
- inferred domains such as NLP, computer vision, recommendation systems, LLMs, or classical ML.

### Step 3. Interview Starts

Once the resume is parsed, the audio interview begins. The interviewer should speak and listen like a professional interviewer, not like an eager assistant.

### Step 4. Interview Proceeds Through Five Phases

The interview is divided into five phases with clear intent and evaluation behavior.

### Step 5. Final Evaluation

At the end, the system should generate:

- a score for each scored phase,
- a final weighted score,
- qualitative feedback,
- strengths,
- weaknesses,
- improvement suggestions,
- examples of where the candidate showed depth versus surface-level understanding.

## 6. Interview Design

### Phase 1. Introduction / Tell Me About Yourself

Purpose:

- help the candidate settle in,
- understand how they present themselves,
- gather context beyond the resume.

Behavior:

- start with "Tell me about yourself" or a similar opener,
- allow the candidate to explain their background,
- use this phase to understand communication style, confidence, and what themes to probe later.

Evaluation:

- no formal numeric score in V1,
- capture qualitative notes only.

### Phase 2. Deep Dive on the Most Important Project

Purpose:

- identify the candidate's strongest or most important project,
- use that project as the main proxy for technical depth.

Behavior:

- choose the strongest project from resume or ask the candidate which project is most important,
- align the follow-up depth to the target job description,
- start at a high level,
- keep drilling down into architecture, decisions, methods, trade-offs, and fundamentals,
- use a Russian Doll / Socratic method,
- generate follow-up questions directly from the candidate's answer.

Example drill-down pattern:

- What did you build?
- How does it work end to end?
- Why did you choose this approach?
- What trade-offs did you make?
- What specific algorithms or components were used?
- Why not an alternative approach?
- How would this fail in production?
- How would you improve it?

For ML / LLM / RAG-style answers, the interviewer should go into details such as:

- chunking strategy,
- embeddings,
- vector indexing,
- HNSW vs IVF Flat trade-offs,
- cosine similarity,
- retrieval quality,
- reranking,
- evaluation,
- why RAG instead of fine-tuning,
- disadvantages of the chosen approach.

Evaluation:

- this is one of the most important scored phases,
- depth matters more than polished wording,
- the system should measure how far the candidate can go from surface explanation to first principles.

### Phase 3. Deep Dive on Other Projects / Internship / Research

Purpose:

- validate whether depth exists across more than one example,
- test breadth, transfer of knowledge, and consistency.

Behavior:

- ask about other projects, internships, or research work,
- keep the questioning aligned with the target role and required skill areas from the job description,
- use the same Russian Doll / Socratic approach,
- compare whether the candidate demonstrates repeated depth or only depth in one prepared area.

Evaluation:

- similar scoring style to Phase 2,
- slightly more focused on consistency and transfer across experiences.

### Phase 4. Factual Machine Learning Questions

Purpose:

- verify core ML knowledge with questions that have clearer right and wrong answers.

Behavior:

- build a question bank from the GitHub source: [MLQuestions](https://github.com/andrewekhalel/MLQuestions),
- download and convert the question set into a markdown knowledge file,
- create embeddings using a simple 384-dimensional embedding model,
- infer the candidate's likely domain from the resume and earlier interview phases,
- bias retrieval toward both the candidate's domain and the target role requirements from the job description,
- retrieve domain-relevant factual questions first,
- if the bank does not have enough suitable questions, generate additional factual questions on the fly,
- ask at least 4 to 5 factual questions.

Recommended implementation for embeddings:

- use a lightweight 384-dimensional sentence embedding model such as `all-MiniLM-L6-v2`,
- store the vectors and metadata in Supabase with `pgvector`.

Evaluation:

- mostly correctness-based,
- track how many answers were correct, partially correct, incorrect, or vague.

### Phase 5. Behavioral Interview

Purpose:

- assess team fit, judgment, maturity, empathy, and long-term thinking.

Example behavioral prompts:

- Why do you want this job?
- How do you work in a team?
- Tell me about a time you had to disagree with your manager or senior.
- How do you see yourself in five years?
- Do you have any questions for me?

Evaluation focus:

- teamwork,
- ownership,
- grounded judgment,
- empathy,
- vision,
- realism,
- ability to work toward meaningful outcomes.

## 7. Hints and Candidate Support

In Phases 2 and 3, if the candidate gets stuck, the interviewer should provide a small nudge rather than immediately moving on.

The system should then evaluate two things:

- whether the hint helped the candidate move toward the right answer,
- whether the candidate could recover and continue reasoning after the hint.

This hint-recovery signal should be part of the score.

## 8. Interviewer Tone and Prompt Rules

The interviewer should sound like a real interviewer:

- professional,
- concise,
- calm,
- direct,
- empathetic but not overly emotional,
- neutral in tone.

Prompt rules:

- do not use exaggerated praise,
- do not say things like "good answer," "perfect answer," or "impressive",
- do not simply agree with the candidate,
- do not sound like a chatbot trying to please the user,
- keep the English simple and clear,
- ask follow-up questions based on what the candidate actually said,
- continue asking until the concept is clear or the candidate's depth limit is reached.

The interviewer should not prematurely move on just because the candidate gave a plausible answer.

## 9. Audio Interaction Design

The interface should be audio-first, not video-first.

### V1 audio behavior

- candidate speaks through microphone,
- speech is transcribed,
- interviewer responds with generated speech,
- transcript is stored alongside the interview state.

### Anxiety-aware behavior

If the candidate is speaking too fast or appears anxious based on speaking pace and repeated hesitation patterns, the interviewer should respond with empathy, for example:

"Take a moment. You can pause, drink some water, and continue when you're ready."

Then the interview should resume from the current context.

### Note on OpenAI audio models

Whisper is a speech-to-text model, not a text-to-speech model. For V1:

- use an OpenAI transcription model for candidate audio input,
- use an OpenAI text-to-speech model for interviewer audio output.

## 10. Evaluation Framework

Phase 1 should remain qualitative only.

The scored phases should be:

- Phase 2
- Phase 3
- Phase 4
- Phase 5

### Suggested weighting

- Phase 2: 30%
- Phase 3: 25%
- Phase 4: 25%
- Phase 5: 20%

### Phase 2 scoring dimensions

- depth of technical understanding,
- first-principles reasoning,
- ability to explain architecture clearly,
- ability to discuss trade-offs,
- correctness under drill-down,
- hint recovery.

### Phase 3 scoring dimensions

- consistency across other experiences,
- ability to transfer concepts,
- depth outside the main showcase project,
- hint recovery.

### Phase 4 scoring dimensions

- factual correctness,
- precision,
- confidence calibration,
- ability to distinguish concepts clearly.

### Phase 5 scoring dimensions

- teamwork,
- ownership,
- maturity,
- empathy,
- long-term vision,
- grounded decision-making.

### Final score

The final score should be a weighted combination of Phases 2 to 5 and should also produce a written explanation of why the candidate received that score.

## 11. Recommended Technical Architecture

### Frontend

- Next.js + TypeScript
- Audio-first interview interface
- Resume upload UI
- Live transcript display
- Phase progress indicator
- Final feedback dashboard

### Backend / Orchestration

- Python + FastAPI
- Interview state machine
- Prompt orchestration
- Resume parsing pipeline
- Question retrieval pipeline
- Evaluation pipeline

### Database

- Supabase Postgres
- Supabase Storage for uploaded resumes and possibly generated artifacts
- `pgvector` for factual question retrieval

### LLM and AI services

- OpenAI reasoning-capable model for the interview brain and evaluation logic
- OpenAI PDF input handling for resume parsing
- OpenAI speech-to-text for candidate audio
- OpenAI text-to-speech for interviewer voice

### Retrieval and question bank

- GitHub source converted into markdown
- domain tags on each question
- 384-dimensional embeddings
- similarity search over stored question vectors

## 12. Suggested Data Model

Recommended core tables:

- `candidates`
- `resumes`
- `resume_sections`
- `interviews`
- `interview_phases`
- `messages`
- `evaluations`
- `question_bank`
- `question_embeddings`

This gives a clean separation between uploaded documents, parsed structure, interview transcripts, and scoring.

## 13. Recommended Implementation Strategy

Build the system in the following order:

### Stage 1. PRD Finalization

- finalize interview flow,
- finalize scoring dimensions,
- finalize missing product inputs,
- approve stack and architecture.

### Stage 2. Foundation Setup

- create repo structure,
- set up environment variables,
- connect Supabase,
- create schema,
- create local development setup.

### Stage 3. Resume Ingestion

- upload PDF,
- parse with OpenAI,
- normalize resume sections,
- store in Supabase.

### Stage 4. Interview Engine

- build state machine for five phases,
- create prompt templates,
- create follow-up logic,
- add hint behavior,
- persist transcript and phase progress.

### Stage 5. Question Bank + Retrieval

- ingest GitHub ML questions,
- convert to markdown,
- create embeddings,
- store vectors,
- retrieve candidate-relevant factual questions.

### Stage 6. Evaluation Engine

- score Phases 2 to 5,
- generate written evidence-based feedback,
- compute final weighted score.

### Stage 7. Audio UX

- microphone capture,
- transcription,
- interviewer voice output,
- pause / resume behavior,
- anxiety-aware empathetic messaging.

### Stage 8. Testing and Refinement

- test with real resumes,
- test different candidate domains,
- tune prompts,
- tune retrieval,
- calibrate scoring.

## 14. Development Timeline

### Week 1

- finalize PRD,
- confirm inputs and credentials,
- design schema,
- set up project skeleton.

### Week 2

- implement resume upload and parsing,
- store structured resume sections in Supabase.

### Week 3

- implement interview state machine,
- implement Phases 1 to 3,
- add follow-up and hint logic.

### Week 4

- ingest ML question bank,
- build embeddings + retrieval,
- implement Phase 4.

### Week 5

- implement Phase 5,
- implement scoring engine,
- generate final evaluation report.

### Week 6

- integrate audio interaction,
- improve interviewer behavior,
- test end-to-end,
- fix edge cases,
- prepare for implementation review.

## 15. Initial Task List

- [ ] Finalize PRD
- [ ] Confirm missing inputs
- [ ] Create project structure
- [ ] Configure environment variables
- [ ] Create Supabase schema
- [ ] Build resume upload flow
- [ ] Build resume parsing pipeline
- [ ] Store structured resume sections
- [ ] Build interview phase controller
- [ ] Write interviewer system prompts
- [ ] Implement Phase 1
- [ ] Implement Phase 2
- [ ] Implement Phase 3
- [ ] Build ML question bank markdown file
- [ ] Add embeddings and similarity search
- [ ] Implement Phase 4
- [ ] Implement Phase 5
- [ ] Build scoring engine
- [ ] Build final evaluation report
- [ ] Add audio input and output
- [ ] Add anxiety-aware empathy behavior
- [ ] Test with sample resume
- [ ] Tune prompts and scoring

## 16. Inputs Still Needed Before Build Starts

The following inputs are required or strongly recommended before implementation begins:

- OpenAI API key
- Supabase project URL
- Supabase API key(s)
- the target Machine Learning Engineer / Learning Engineer job description
- confirmation of whether V1 should be web-only or mobile-responsive web only
- confirmation of whether the first version should be turn-based audio or full realtime conversational audio

### Important security note

Secrets should not remain in a markdown file once implementation starts. Before any GitHub push:

- move credentials into environment variables such as `.env.local` or `.env`,
- add those files to `.gitignore`,
- never expose keys in code, logs, or committed files.

## 17. Future Versions

These items should be explicitly treated as later versions:

### Version 2

- CI/CD pipeline
- GitHub integration
- AWS deployment

### Version 3

- anti-cheating system
- face recognition checks
- other blocking or proctoring mechanisms

### Later research opportunities

- video-based interview analysis
- multimodal behavioral analysis
- cheating-risk scoring
- stronger production analytics

## 18. Final Build Direction

This product should be built first as a serious, audio-first, ML interview simulator with strong interview orchestration and evaluation depth. The strongest part of the product should be the ability to follow the candidate's answer, identify the most important technical thread, and keep drilling down intelligently instead of asking disconnected generic questions.

That is the central value of the product and should remain the design priority for V1.
