from __future__ import annotations

from interviewing_agent.models import InterviewPhase, InterviewSession, ParsedResume


INTERVIEWER_STYLE_RULES = """
You are a professional interviewer for a Machine Learning Engineer / Learning Engineer role.

Rules:
- Be concise, direct, calm, and professional.
- Do not praise the candidate with phrases such as "good answer", "perfect", or "impressive".
- Ask follow-up questions based on the candidate's actual answer.
- When relevant, drill down from high-level project description to technical decisions, trade-offs, and first principles.
- If the candidate seems stuck in phase 2 or phase 3, give a small hint or nudge instead of ending the line of questioning.
- Keep the interview aligned to the job description and the candidate's resume.
- Run the interview like a live conversation, not a scripted questionnaire.
- Use the latest answer to decide whether to probe deeper, challenge a claim, redirect, or advance the phase.
- Mention at least one concrete concept, project, metric, or claim from the candidate's latest answer when you ask the next question.
"""


def format_resume_context(resume: ParsedResume) -> str:
    return f"""
Candidate name: {resume.candidate_name}
Headline: {resume.headline}
Summary: {resume.summary}
Skills: {", ".join(resume.skills) or "n/a"}
Projects: {", ".join(resume.projects) or "n/a"}
Experience: {", ".join(resume.experience) or "n/a"}
Education: {", ".join(resume.education) or "n/a"}
Domains: {", ".join(resume.inferred_domains) or "n/a"}
Notes: {", ".join(resume.notes) or "n/a"}
""".strip()


def resume_parse_prompt() -> str:
    return """
Extract the resume into JSON with this exact shape:
{
  "candidate_name": "string",
  "headline": "string",
  "summary": "string",
  "skills": ["string"],
  "projects": ["string"],
  "experience": ["string"],
  "education": ["string"],
  "inferred_domains": ["string"],
  "notes": ["string"]
}

Rules:
- Return valid JSON only.
- Keep values concise.
- Infer likely technical domains such as NLP, computer vision, recommendation systems, LLMs, RAG, MLOps, or classical ML when evidence exists.
- Put missing fields as empty strings or empty arrays instead of inventing content.
""".strip()


def opening_question(interviewer_name: str, target_company: str, target_role: str) -> str:
    interviewer_identity = (
        f"Hi, I’m {interviewer_name.strip()}"
        if interviewer_name.strip()
        else "Hi, I’m your interviewer"
    )
    company_context = (
        f", and I’m part of the hiring team at {target_company.strip()}"
        if target_company.strip()
        else ""
    )
    return (
        f"{interviewer_identity}{company_context}. "
        f"Today I’ll be conducting your interview for the {target_role} position.\n\n"
        "We’ll start with your background, then move into factual technical questions, "
        "and finish with short behavioral one-liners. If anything is unclear before we begin, "
        "feel free to ask clarifying questions.\n\n"
        "Whenever you’re ready, we can begin."
    )


def background_question(resume: ParsedResume, target_role: str) -> str:
    return (
        "To start, please tell me about yourself and walk me through the parts of your "
        f"background that are most relevant to the {target_role or resume.headline or 'role'} position."
    )


def phase_instruction(phase: InterviewPhase) -> str:
    mapping = {
        InterviewPhase.PHASE_1_INTRO: "Understand the candidate's background and communication style.",
        InterviewPhase.PHASE_2_DEEP_DIVE: "Choose the strongest project and drill down using a Russian Doll / Socratic approach.",
        InterviewPhase.PHASE_3_BREADTH: "Test breadth across other projects, internships, or research.",
        InterviewPhase.PHASE_4_FACTUAL: "Ask factual ML questions with clearer right and wrong answers.",
        InterviewPhase.PHASE_5_BEHAVIORAL: "Assess teamwork, maturity, vision, ownership, and empathy.",
        InterviewPhase.COMPLETE: "The interview is complete.",
    }
    return mapping[phase]


def phase_exit_criteria(phase: InterviewPhase) -> str:
    mapping = {
        InterviewPhase.PHASE_1_INTRO: (
            "Advance only when you understand the candidate's background, strongest role-relevant area, "
            "and which project to drill into next."
        ),
        InterviewPhase.PHASE_2_DEEP_DIVE: (
            "Advance only after the candidate has covered system architecture, their own contribution, "
            "trade-offs, evaluation, and likely failure modes for one strong project."
        ),
        InterviewPhase.PHASE_3_BREADTH: (
            "Advance only after the candidate has shown breadth through a distinct project or experience, "
            "different constraints, and what they would improve."
        ),
        InterviewPhase.PHASE_4_FACTUAL: (
            "Advance only after the candidate has answered enough factual ML questions to assess technical fundamentals "
            "for this role."
        ),
        InterviewPhase.PHASE_5_BEHAVIORAL: (
            "Advance only after you have enough evidence on ownership, disagreement handling, ambiguity, and judgment."
        ),
        InterviewPhase.COMPLETE: "The interview is complete.",
    }
    return mapping[phase]


def turn_prompt(
    session: InterviewSession,
    candidate_response: str,
    job_description: str,
    candidate_signals: str,
    orchestration_context: str,
) -> str:
    history = "\n".join(
        f"{message.role.upper()} [{message.phase.value}]: {message.text}"
        for message in session.messages[-8:]
    )

    return f"""
{INTERVIEWER_STYLE_RULES}

Target role: {session.target_role}
Target company: {session.target_company}

Job description:
{job_description[:6000]}

Resume context:
{format_resume_context(session.resume)}

Current phase: {session.current_phase.value}
Current phase goal: {phase_instruction(session.current_phase)}
Current phase exit criteria: {phase_exit_criteria(session.current_phase)}

Orchestration context:
{orchestration_context}

Recent conversation:
{history}

Latest candidate answer:
{candidate_response}

Candidate signal summary:
{candidate_signals}

Return valid JSON only with this exact shape:
{{
  "phase": "{session.current_phase.value}",
  "reply": "string",
  "hint_used": false,
  "hint_recovery": false,
  "empathy_used": false,
  "factual_questions_added": 0,
  "phase_score": 0.0
}}

Rules:
- Keep the reply to at most 3 sentences.
- The reply must feel like the next natural interview turn, not like a canned phase transition.
- Base the next question directly on the candidate's latest answer and the conversation so far.
- Stay in the current phase if the exit criteria have not been met yet.
- If the orchestration context says the phase turn budget has been reached, you must advance to the next phase now.
- If you move to a later phase, set the new phase in "phase".
- Use a small hint only if the candidate seems stuck.
- If the candidate seems anxious or rushed, briefly steady them before continuing the interview.
- Set "hint_recovery" to true only when the candidate meaningfully recovers after an earlier hint in the same phase.
- "phase_score" should be a 0-10 score estimate for the current phase after this turn.
""".strip()
