from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from fastapi import HTTPException

from interviewing_agent.config import Settings
from interviewing_agent.models import (
    BootstrapResponse,
    InterviewMessage,
    InterviewPhase,
    InterviewSession,
    InterviewTurnResponse,
    ParsedResume,
    TurnMetadata,
)
from interviewing_agent.prompts import background_question, opening_question, turn_prompt
from interviewing_agent.services.access_control import (
    generate_session_access_token,
    hash_session_access_token,
    verify_session_access_token,
)
from interviewing_agent.services.evaluation import EvaluationService
from interviewing_agent.services.openai_client import OpenAIProvider
from interviewing_agent.services.persistence import SupabasePersistenceService
from interviewing_agent.services.question_bank import QuestionBankService


logger = logging.getLogger(__name__)


PHASE_ORDER = [
    InterviewPhase.PHASE_1_INTRO,
    InterviewPhase.PHASE_2_DEEP_DIVE,
    InterviewPhase.PHASE_3_BREADTH,
    InterviewPhase.PHASE_4_FACTUAL,
    InterviewPhase.PHASE_5_BEHAVIORAL,
]

PHASE_TURN_BUDGETS = {
    InterviewPhase.PHASE_1_INTRO: 2,
    InterviewPhase.PHASE_2_DEEP_DIVE: 3,
    InterviewPhase.PHASE_3_BREADTH: 3,
    InterviewPhase.PHASE_4_FACTUAL: 2,
    InterviewPhase.PHASE_5_BEHAVIORAL: 2,
}

DEPTH_SIGNAL_WORDS = {
    "because",
    "trade-off",
    "latency",
    "precision",
    "recall",
    "embedding",
    "evaluation",
    "monitoring",
    "failure",
    "production",
    "guardrail",
}

ANXIETY_PHRASES = (
    "i am nervous",
    "i'm nervous",
    "a bit nervous",
    "little nervous",
    "speaking too fast",
    "talking too fast",
    "need a second",
    "need a moment",
    "give me a second",
    "give me a moment",
    "sorry",
)

STUCK_PHRASES = (
    "not sure",
    "don't know",
    "do not know",
    "can't remember",
    "cannot remember",
    "forgot",
    "blanking",
    "unsure",
)


@dataclass
class MemorySessionStore:
    sessions: dict[str, InterviewSession] = field(default_factory=dict)

    def save(self, session: InterviewSession) -> InterviewSession:
        self.sessions[session.id] = session
        return session

    def get(self, session_id: str) -> InterviewSession:
        if session_id not in self.sessions:
            raise HTTPException(status_code=404, detail="Interview session not found.")
        return self.sessions[session_id]

    def delete_session_data(self, session: InterviewSession) -> None:
        if session.candidate_id:
            session_ids = [
                session_id
                for session_id, stored_session in self.sessions.items()
                if stored_session.candidate_id == session.candidate_id
            ]
        else:
            session_ids = [session.id]

        for session_id in session_ids:
            self.sessions.pop(session_id, None)


@dataclass(frozen=True)
class CandidateSignals:
    appears_stuck: bool
    appears_anxious: bool
    recovery_after_hint: bool
    answer_token_count: int
    depth_marker_hits: int

    def to_prompt_summary(self) -> str:
        return (
            f"appears_stuck={self.appears_stuck}, "
            f"appears_anxious={self.appears_anxious}, "
            f"recovery_after_hint={self.recovery_after_hint}, "
            f"answer_token_count={self.answer_token_count}, "
            f"depth_marker_hits={self.depth_marker_hits}"
        )


class InterviewEngine:
    def __init__(
        self,
        settings: Settings,
        openai_provider: OpenAIProvider,
        session_store: MemorySessionStore,
        question_bank_service: QuestionBankService,
        persistence_service: SupabasePersistenceService | None = None,
        evaluation_service: EvaluationService | None = None,
    ) -> None:
        self.settings = settings
        self.openai_provider = openai_provider
        self.session_store = session_store
        self.question_bank_service = question_bank_service
        self.persistence_service = persistence_service
        self.evaluation_service = evaluation_service or EvaluationService()
        self.job_description = settings.load_job_description()

    def bootstrap(
        self,
        resume: ParsedResume,
        resume_filename: str | None = None,
        resume_content: bytes | None = None,
        candidate_id: str | None = None,
        resume_id: str | None = None,
    ) -> BootstrapResponse:
        session_access_token = generate_session_access_token()
        opening = InterviewMessage(
            role="interviewer",
            phase=InterviewPhase.PHASE_1_INTRO,
            text=opening_question(
                self.settings.interviewer_name,
                self.settings.interview_target_company,
                self.settings.interview_target_role,
            ),
        )
        session = InterviewSession(
            session_access_token_hash=hash_session_access_token(session_access_token),
            target_company=self.settings.interview_target_company,
            target_role=self.settings.interview_target_role,
            resume=resume,
            candidate_id=candidate_id,
            resume_id=resume_id,
            messages=[opening],
        )
        self.session_store.save(session)
        if self.persistence_service is not None:
            self.persistence_service.persist_bootstrap(session, resume_filename, resume_content)
        return BootstrapResponse(
            resume=resume,
            session=session,
            session_access_token=session_access_token,
        )

    def begin_intro(self, session_id: str) -> InterviewSession:
        session = self.get_session(session_id)
        if session.current_phase != InterviewPhase.PHASE_1_INTRO:
            return session

        if any(message.role == "candidate" for message in session.messages):
            return session

        if any(
            message.role == "interviewer"
            and message.phase == InterviewPhase.PHASE_1_INTRO
            and "tell me about yourself" in message.text.lower()
            for message in session.messages
        ):
            return session

        session.messages.append(
            InterviewMessage(
                role="interviewer",
                phase=InterviewPhase.PHASE_1_INTRO,
                text=background_question(session.resume, session.target_role),
            )
        )
        self.session_store.save(session)
        if self.persistence_service is not None:
            self.persistence_service.persist_session(session)
        return session

    def get_session(self, session_id: str) -> InterviewSession:
        try:
            return self.session_store.get(session_id)
        except HTTPException:
            if self.persistence_service is not None:
                restored = self.persistence_service.load_session(session_id)
                if restored is not None:
                    self.session_store.save(restored)
                    return restored
            raise

    def verify_session_access(self, session_id: str, supplied_token: str) -> bool:
        session = self.get_session(session_id)
        return verify_session_access_token(
            supplied_token,
            session.session_access_token_hash,
        )

    def delete_session_data(self, session_id: str) -> None:
        session = self.get_session(session_id)
        if self.persistence_service is not None:
            self.persistence_service.delete_session_data(session_id)
        self.session_store.delete_session_data(session)

    def complete_session(self, session_id: str) -> InterviewSession:
        session = self.get_session(session_id)
        if session.current_phase != InterviewPhase.COMPLETE:
            session.messages.append(
                InterviewMessage(
                    role="interviewer",
                    phase=InterviewPhase.COMPLETE,
                    text=(
                        "The interview has ended. Your performance review is ready, "
                        "including phase-by-phase feedback and the combined score."
                    ),
                )
            )
            session.current_phase = InterviewPhase.COMPLETE

        self.evaluation_service.evaluate_session(session)
        self.session_store.save(session)
        if self.persistence_service is not None:
            self.persistence_service.persist_session(session)
        return session

    def process_turn(
        self,
        session_id: str,
        candidate_response: str,
        metadata: TurnMetadata | None = None,
    ) -> InterviewTurnResponse:
        session = self.get_session(session_id)
        turn_metadata = metadata or TurnMetadata()
        self._record_turn_metadata(session, turn_metadata)
        candidate_signals = self._analyze_candidate_response(session, candidate_response)

        candidate_message = InterviewMessage(
            role="candidate",
            phase=session.current_phase,
            text=candidate_response,
        )
        session.messages.append(candidate_message)

        latest_reply = self._generate_next_reply(session, candidate_response, candidate_signals)
        session.messages.append(latest_reply)
        session.current_phase = latest_reply.phase
        if latest_reply.hint_recovery:
            session.hint_recovery_count += 1
        if latest_reply.empathy_used:
            session.empathy_prompt_count += 1
        self.evaluation_service.evaluate_session(session)
        self.session_store.save(session)
        if self.persistence_service is not None:
            self.persistence_service.persist_session(session)
        return InterviewTurnResponse(session=session, latest_reply=latest_reply)

    def _generate_next_reply(
        self,
        session: InterviewSession,
        candidate_response: str,
        candidate_signals: CandidateSignals,
    ) -> InterviewMessage:
        client = self.openai_provider.client
        if client is not None:
            try:
                response = client.responses.create(
                    model=self.settings.openai_interview_model,
                    reasoning={"effort": self.settings.interview_reasoning_effort},
                    input=turn_prompt(
                        session,
                        candidate_response,
                        self.job_description,
                        candidate_signals.to_prompt_summary(),
                        self._build_orchestration_context(session),
                    ),
                )
                payload = self._extract_json_object(response.output_text)
                phase = InterviewPhase(payload["phase"])
                reply_text = payload["reply"].strip()
                if payload.get("hint_used"):
                    session.hint_count += 1
                session.factual_question_count += int(payload.get("factual_questions_added", 0))
                self._write_phase_score(session, phase, float(payload.get("phase_score", 0.0)))
                if self._should_force_progression(session, phase):
                    return self._fallback_reply(session, candidate_response, candidate_signals)
                return InterviewMessage(
                    role="interviewer",
                    phase=phase,
                    text=reply_text,
                    hint_used=bool(payload.get("hint_used")),
                    hint_recovery=bool(payload.get("hint_recovery")),
                    empathy_used=bool(payload.get("empathy_used")),
                )
            except Exception:
                logger.warning(
                    "Interview model generation failed; using deterministic fallback.",
                    exc_info=True,
                )

        return self._fallback_reply(session, candidate_response, candidate_signals)

    def _build_orchestration_context(self, session: InterviewSession) -> str:
        primary_project = (
            session.resume.projects[0] if session.resume.projects else "the candidate's strongest project"
        )
        secondary_project = (
            session.resume.projects[1]
            if len(session.resume.projects) > 1
            else "a distinct project or experience from the resume"
        )
        candidate_turns = self._candidate_turns_in_phase(session, session.current_phase)
        last_interviewer_question = next(
            (
                message.text
                for message in reversed(session.messages)
                if message.role == "interviewer"
            ),
            "No interviewer question yet.",
        )
        asked_factual_questions = [
            message.text.strip()
            for message in session.messages
            if message.role == "interviewer" and message.phase == InterviewPhase.PHASE_4_FACTUAL
        ]

        factual_candidates = self.question_bank_service.retrieve_questions(
            resume=session.resume,
            target_role=session.target_role,
            job_description=self.job_description,
            limit=3,
            exclude_questions=set(asked_factual_questions),
        )
        factual_candidate_lines = (
            "\n".join(
                f"- {question.question} [{', '.join(question.domain_tags)}]"
                for question in factual_candidates
            )
            if factual_candidates
            else "- No retrieved factual question candidates available."
        )

        return (
            f"Primary deep-dive project: {primary_project}\n"
            f"Secondary breadth project: {secondary_project}\n"
            f"Candidate turns already spent in this phase: {candidate_turns}\n"
            f"Phase turn budget before forced progression: {self._phase_turn_budget(session.current_phase)}\n"
            f"Last interviewer question: {last_interviewer_question}\n"
            f"Already asked factual questions: {asked_factual_questions or ['none']}\n"
            "Suggested factual question candidates if you need them:\n"
            f"{factual_candidate_lines}"
        )

    def _should_force_progression(
        self,
        session: InterviewSession,
        proposed_phase: InterviewPhase,
    ) -> bool:
        current_phase = session.current_phase
        if current_phase == InterviewPhase.COMPLETE:
            return False
        if proposed_phase != current_phase:
            return False
        return self._candidate_turns_in_phase(session, current_phase) >= self._phase_turn_budget(
            current_phase
        )

    @staticmethod
    def _phase_turn_budget(phase: InterviewPhase) -> int:
        return PHASE_TURN_BUDGETS.get(phase, 2)

    def _fallback_reply(
        self,
        session: InterviewSession,
        candidate_response: str,
        candidate_signals: CandidateSignals,
    ) -> InterviewMessage:
        current_phase = session.current_phase
        candidate_turns_in_phase = self._candidate_turns_in_phase(session, current_phase)
        top_project = session.resume.projects[0] if session.resume.projects else "your most important project"
        second_project = (
            session.resume.projects[1]
            if len(session.resume.projects) > 1
            else "another project or internship"
        )
        hint_already_used = self._phase_has_flag(session, current_phase, "hint_used")

        if (
            current_phase != InterviewPhase.COMPLETE
            and candidate_signals.appears_anxious
            and not self._phase_has_flag(session, current_phase, "empathy_used")
        ):
            guidance_topic = {
                InterviewPhase.PHASE_1_INTRO: "walk me through the parts of your background that matter most here",
                InterviewPhase.PHASE_2_DEEP_DIVE: f"walk me through {top_project} step by step",
                InterviewPhase.PHASE_3_BREADTH: f"explain one concrete decision from {second_project}",
                InterviewPhase.PHASE_4_FACTUAL: "reason through the concept carefully and take it one step at a time",
                InterviewPhase.PHASE_5_BEHAVIORAL: "answer with one situation, your action, and the outcome",
            }.get(current_phase, "continue when you are ready")
            return InterviewMessage(
                role="interviewer",
                phase=current_phase,
                text=(
                    "Take a breath. We can pause for a moment. "
                    f"When you are ready, {guidance_topic}."
                ),
                empathy_used=True,
            )

        if current_phase == InterviewPhase.PHASE_1_INTRO:
            next_phase = InterviewPhase.PHASE_2_DEEP_DIVE
            text = (
                f"Let us go deeper. Which project would you consider your strongest, "
                f"and please explain the architecture of {top_project} from end to end."
            )
            hint_used = False
            hint_recovery = False
        elif current_phase == InterviewPhase.PHASE_2_DEEP_DIVE and candidate_signals.appears_stuck and not hint_already_used:
            next_phase = InterviewPhase.PHASE_2_DEEP_DIVE
            session.hint_count += 1
            text = (
                f"Take a moment and anchor your answer in concrete components. "
                f"As a hint, describe the data flow, model choice, evaluation, "
                f"and one trade-off you made in {top_project}."
            )
            hint_used = True
            hint_recovery = False
        elif (
            current_phase == InterviewPhase.PHASE_2_DEEP_DIVE
            and hint_already_used
            and candidate_signals.recovery_after_hint
            and candidate_turns_in_phase <= 3
        ):
            next_phase = InterviewPhase.PHASE_2_DEEP_DIVE
            text = (
                f"That is clearer. Now go one layer deeper on {top_project}: "
                "why did you choose that design, what alternatives did you reject, "
                "and where would it fail in production?"
            )
            hint_used = False
            hint_recovery = True
        elif current_phase == InterviewPhase.PHASE_2_DEEP_DIVE and candidate_turns_in_phase < 3:
            next_phase = InterviewPhase.PHASE_2_DEEP_DIVE
            text = (
                f"Why did you choose that design for {top_project}, what were the main "
                f"trade-offs, and where would this system fail in production?"
            )
            hint_used = False
            hint_recovery = False
        elif current_phase == InterviewPhase.PHASE_2_DEEP_DIVE:
            next_phase = InterviewPhase.PHASE_3_BREADTH
            text = (
                f"Now let us test breadth. Tell me about {second_project} and explain "
                f"how your role, technical depth, and decisions differed from the first project."
            )
            hint_used = False
            hint_recovery = False
        elif current_phase == InterviewPhase.PHASE_3_BREADTH and candidate_signals.appears_stuck and not hint_already_used:
            next_phase = InterviewPhase.PHASE_3_BREADTH
            session.hint_count += 1
            text = (
                "Give me one concrete technical decision from that work. "
                "As a hint, focus on the objective, the approach you chose, "
                "and what alternatives you rejected."
            )
            hint_used = True
            hint_recovery = False
        elif (
            current_phase == InterviewPhase.PHASE_3_BREADTH
            and hint_already_used
            and candidate_signals.recovery_after_hint
            and candidate_turns_in_phase <= 3
        ):
            next_phase = InterviewPhase.PHASE_3_BREADTH
            text = (
                "That gives me enough to continue. "
                "What did you measure, what constraints shaped your choices, "
                "and what would you improve if you rebuilt that work today?"
            )
            hint_used = False
            hint_recovery = True
        elif current_phase == InterviewPhase.PHASE_3_BREADTH and candidate_turns_in_phase < 3:
            next_phase = InterviewPhase.PHASE_3_BREADTH
            text = (
                "What did you measure, what constraints shaped your choices, "
                "and what would you improve if you rebuilt that work today?"
            )
            hint_used = False
            hint_recovery = False
        elif current_phase == InterviewPhase.PHASE_3_BREADTH:
            next_phase = InterviewPhase.PHASE_4_FACTUAL
            session.factual_question_count += 1
            text = self._factual_question(session)
            hint_used = False
            hint_recovery = False
        elif current_phase == InterviewPhase.PHASE_4_FACTUAL and candidate_turns_in_phase < 2:
            next_phase = InterviewPhase.PHASE_4_FACTUAL
            session.factual_question_count += 1
            text = self._factual_question(session, follow_up_index=session.factual_question_count)
            hint_used = False
            hint_recovery = False
        elif current_phase == InterviewPhase.PHASE_4_FACTUAL:
            next_phase = InterviewPhase.PHASE_5_BEHAVIORAL
            text = (
                "Let us move to behavioral questions. Tell me about a time you disagreed "
                "with a senior stakeholder or manager and how you handled it."
            )
            hint_used = False
            hint_recovery = False
        elif current_phase == InterviewPhase.PHASE_5_BEHAVIORAL and candidate_turns_in_phase < 2:
            next_phase = InterviewPhase.PHASE_5_BEHAVIORAL
            text = (
                "How do you work in teams when there is ambiguity, and how do you balance "
                "speed with quality when expectations are changing?"
            )
            hint_used = False
            hint_recovery = False
        else:
            next_phase = InterviewPhase.COMPLETE
            self.evaluation_service.evaluate_session(session)
            text = (
                "The interview is complete. Your overall performance summary is now available, "
                "including phase-by-phase signals and the combined score."
            )
            hint_used = False
            hint_recovery = False

        return InterviewMessage(
            role="interviewer",
            phase=next_phase,
            text=text,
            hint_used=hint_used,
            hint_recovery=hint_recovery,
        )

    def _factual_question(self, session: InterviewSession, follow_up_index: int = 1) -> str:
        asked_questions = {
            message.text.strip()
            for message in session.messages
            if message.role == "interviewer" and message.phase == InterviewPhase.PHASE_4_FACTUAL
        }
        retrieved = self.question_bank_service.retrieve_questions(
            resume=session.resume,
            target_role=session.target_role,
            job_description=self.job_description,
            limit=max(3, follow_up_index + 1),
            exclude_questions=asked_questions,
        )
        if retrieved and not self._needs_generated_fallback(session, retrieved):
            index = min(follow_up_index - 1, len(retrieved) - 1)
            return retrieved[index].question

        generated = self._generated_factual_question(session, asked_questions)
        if generated:
            return generated
        return self._fallback_factual_question(session, follow_up_index)

    def _needs_generated_fallback(self, session: InterviewSession, retrieved: list) -> bool:
        if not retrieved:
            return True

        target_text = " ".join(
            [
                session.target_role,
                self.job_description,
                " ".join(session.resume.inferred_domains),
            ]
        ).lower()
        specialist_requested = any(
            token in target_text
            for token in ("genai", "llm", "rag", "recommend", "bandit", "agentic", "guardrail")
        )
        top_score = retrieved[0].score
        top_tags = set(retrieved[0].domain_tags)
        weak_specialization = top_tags <= {"machine_learning", "ml_fundamentals"}
        return top_score < 0.55 or (specialist_requested and weak_specialization)

    def _generated_factual_question(
        self,
        session: InterviewSession,
        asked_questions: set[str],
    ) -> str | None:
        client = self.openai_provider.client
        if client is None:
            return None

        try:
            prompt = (
                "Generate one role-aligned factual interview question for a machine learning candidate.\n"
                f"Target role: {session.target_role}\n"
                f"Target company: {session.target_company}\n"
                f"Resume domains: {', '.join(session.resume.inferred_domains)}\n"
                f"Resume skills: {', '.join(session.resume.skills[:10])}\n"
                f"Resume projects: {', '.join(session.resume.projects[:3])}\n"
                f"Job description excerpt: {self.job_description[:2000]}\n"
                f"Avoid repeating any of these questions: {sorted(asked_questions)}\n\n"
                "Return only the question text. The question must be factual, technically evaluable, and concise."
            )
            response = client.responses.create(
                model=self.settings.openai_resume_parse_model,
                input=prompt,
            )
            question = response.output_text.strip().strip('"')
            if question and question not in asked_questions:
                return question
        except Exception:
            logger.warning(
                "Generated factual question failed; using retrieved or deterministic fallback.",
                exc_info=True,
            )
            return None
        return None

    @staticmethod
    def _fallback_factual_question(session: InterviewSession, follow_up_index: int = 1) -> str:
        domains = {domain.lower() for domain in session.resume.inferred_domains}

        if {"rag", "llms", "nlp"} & domains:
            prompts = [
                "Define vector indexing and explain the trade-offs between HNSW and IVF Flat.",
                "When would you prefer retrieval optimization over fine-tuning in a RAG system?",
                "How do you evaluate retrieval quality before blaming the generation model?",
            ]
        elif {"recommendation systems", "recommendations"} & domains:
            prompts = [
                "What is the exploration versus exploitation trade-off in recommender systems?",
                "How would you evaluate a recommender offline versus online?",
                "Where would a multi-armed bandit be more useful than a static ranker?",
            ]
        else:
            prompts = [
                "What is overfitting, and how would you detect it during model development?",
                "Explain the bias-variance trade-off in practical terms.",
                "What is the difference between precision, recall, and F1, and when would you optimize each?",
            ]

        index = min(follow_up_index - 1, len(prompts) - 1)
        return prompts[index]

    @staticmethod
    def _candidate_turns_in_phase(session: InterviewSession, phase: InterviewPhase) -> int:
        return sum(
            1 for message in session.messages if message.role == "candidate" and message.phase == phase
        )

    @staticmethod
    def _phase_has_flag(
        session: InterviewSession,
        phase: InterviewPhase,
        flag_name: str,
    ) -> bool:
        return any(
            message.role == "interviewer"
            and message.phase == phase
            and bool(getattr(message, flag_name, False))
            for message in session.messages
        )

    @staticmethod
    def _record_turn_metadata(session: InterviewSession, metadata: TurnMetadata) -> None:
        session.realtime_mode_enabled = session.realtime_mode_enabled or metadata.realtime_enabled
        session.video_mode_enabled = session.video_mode_enabled or metadata.camera_enabled
        session.proctoring.tab_switch_count = max(
            session.proctoring.tab_switch_count,
            metadata.tab_switch_count,
        )
        session.proctoring.window_blur_count = max(
            session.proctoring.window_blur_count,
            metadata.window_blur_count,
        )
        session.proctoring.transcript_retry_count = max(
            session.proctoring.transcript_retry_count,
            metadata.transcript_retry_count,
        )
        if metadata.used_paste:
            session.proctoring.paste_count += 1

        flags: list[str] = []
        if session.proctoring.tab_switch_count >= 3:
            flags.append("Candidate switched away from the interview tab repeatedly.")
        if session.proctoring.window_blur_count >= 3:
            flags.append("Interview window lost focus several times during answers.")
        if session.proctoring.transcript_retry_count >= 3:
            flags.append("Multiple transcript retries suggest unstable or repeated answer capture.")
        if session.proctoring.paste_count >= 2:
            flags.append("Pasted answers were detected more than once.")
        if session.video_mode_enabled:
            flags.append("Candidate opted into camera mode for stronger interview integrity.")
        session.proctoring.suspicious_flags = flags

    def _analyze_candidate_response(
        self,
        session: InterviewSession,
        candidate_response: str,
    ) -> CandidateSignals:
        normalized = candidate_response.lower()
        answer_tokens = re.findall(r"[A-Za-z0-9\-]+", normalized)
        depth_marker_hits = sum(1 for token in answer_tokens if token in DEPTH_SIGNAL_WORDS)
        filler_hits = sum(
            normalized.count(token)
            for token in (" um ", " uh ", " erm ", " hmm ", "like, like", "you know")
        )
        appears_stuck = (
            len(answer_tokens) < 18
            or any(phrase in normalized for phrase in STUCK_PHRASES)
        )
        appears_anxious = (
            filler_hits > 0
            or any(phrase in normalized for phrase in ANXIETY_PHRASES)
        )
        hint_in_phase = self._phase_has_flag(session, session.current_phase, "hint_used")
        recovery_after_hint = (
            hint_in_phase
            and not appears_stuck
            and (len(answer_tokens) >= 28 or depth_marker_hits >= 2)
        )
        return CandidateSignals(
            appears_stuck=appears_stuck,
            appears_anxious=appears_anxious,
            recovery_after_hint=recovery_after_hint,
            answer_token_count=len(answer_tokens),
            depth_marker_hits=depth_marker_hits,
        )

    @staticmethod
    def _write_phase_score(session: InterviewSession, phase: InterviewPhase, value: float) -> None:
        bounded = round(max(0.0, min(10.0, value)), 1)
        if phase == InterviewPhase.PHASE_2_DEEP_DIVE:
            session.scores.phase_2 = bounded
        elif phase == InterviewPhase.PHASE_3_BREADTH:
            session.scores.phase_3 = bounded
        elif phase == InterviewPhase.PHASE_4_FACTUAL:
            session.scores.phase_4 = bounded
        elif phase == InterviewPhase.PHASE_5_BEHAVIORAL:
            session.scores.phase_5 = bounded

    @staticmethod
    def _extract_json_object(text: str) -> dict:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found.")
        return json.loads(match.group(0))
