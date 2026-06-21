from interviewing_agent.config import Settings
from interviewing_agent.models import InterviewPhase, ParsedResume, TurnMetadata
from interviewing_agent.services.interview_engine import InterviewEngine, MemorySessionStore
from interviewing_agent.services.openai_client import OpenAIProvider
from interviewing_agent.services.question_bank import QuestionBankService, RetrievedQuestion


class StubResponse:
    def __init__(self, output_text: str) -> None:
        self.output_text = output_text


class StubbornPhaseClient:
    def __init__(self, phase: str) -> None:
        self.phase = phase
        self.responses = self

    def create(self, **kwargs) -> StubResponse:
        return StubResponse(
            (
                "{"
                f"\"phase\":\"{self.phase}\","
                "\"reply\":\"Tell me more about that.\","
                "\"hint_used\":false,"
                "\"hint_recovery\":false,"
                "\"empathy_used\":false,"
                "\"factual_questions_added\":0,"
                "\"phase_score\":6.0"
                "}"
            )
        )


def make_engine() -> InterviewEngine:
    settings = Settings(
        openai_api_key=None,
        interviewer_name="Jordan",
        interview_target_company="PayPal",
        interview_target_role="Machine Learning Engineer",
        _env_file=None,
    )
    return InterviewEngine(
        settings,
        OpenAIProvider(settings),
        MemorySessionStore(),
        QuestionBankService(settings),
    )


def test_bootstrap_creates_intro_question() -> None:
    engine = make_engine()
    resume = ParsedResume(candidate_name="Candidate", headline="ML Engineer")

    bootstrap = engine.bootstrap(resume)

    assert bootstrap.session.current_phase == InterviewPhase.PHASE_1_INTRO
    assert bootstrap.session.messages[0].role == "interviewer"
    opening_text = bootstrap.session.messages[0].text.lower()
    assert "jordan" in opening_text
    assert "paypal" in opening_text
    assert "machine learning engineer position" in opening_text
    assert "clarifying questions" in opening_text


def test_begin_intro_adds_background_question_once() -> None:
    engine = make_engine()
    resume = ParsedResume(candidate_name="Candidate", headline="ML Engineer")

    bootstrap = engine.bootstrap(resume)
    started = engine.begin_intro(bootstrap.session.id)
    started_again = engine.begin_intro(bootstrap.session.id)

    assert len(started.messages) == 2
    assert started.messages[-1].role == "interviewer"
    assert started.messages[-1].phase == InterviewPhase.PHASE_1_INTRO
    assert "tell me about yourself" in started.messages[-1].text.lower()
    assert len(started_again.messages) == 2


def test_fallback_progresses_into_phase_two() -> None:
    engine = make_engine()
    resume = ParsedResume(candidate_name="Candidate", headline="ML Engineer", projects=["RAG platform"])
    bootstrap = engine.bootstrap(resume)

    turn = engine.process_turn(bootstrap.session.id, "I work on ML systems and LLM applications.")

    assert turn.latest_reply.phase == InterviewPhase.PHASE_2_DEEP_DIVE


def test_hint_recovery_is_tracked_in_phase_two() -> None:
    engine = make_engine()
    resume = ParsedResume(
        candidate_name="Candidate",
        headline="ML Engineer",
        projects=["RAG platform", "Ranking service"],
    )
    bootstrap = engine.bootstrap(resume)

    engine.process_turn(
        bootstrap.session.id,
        "I build ML systems and platform components for retrieval and evaluation.",
    )
    hinted_turn = engine.process_turn(bootstrap.session.id, "I am not sure.")
    recovery_turn = engine.process_turn(
        bootstrap.session.id,
        (
            "The system ingests documents, chunks them by section, creates embeddings, "
            "evaluates retrieval quality, and monitors latency because production failures "
            "usually start in the retrieval layer."
        ),
    )

    assert hinted_turn.latest_reply.hint_used is True
    assert hinted_turn.session.hint_count == 1
    assert recovery_turn.latest_reply.hint_recovery is True
    assert recovery_turn.session.hint_recovery_count == 1
    assert recovery_turn.latest_reply.phase == InterviewPhase.PHASE_2_DEEP_DIVE


def test_anxiety_prompt_slows_the_interview_down() -> None:
    engine = make_engine()
    resume = ParsedResume(candidate_name="Candidate", headline="ML Engineer")
    bootstrap = engine.bootstrap(resume)

    turn = engine.process_turn(
        bootstrap.session.id,
        "Sorry, I am nervous, um, and I need a moment before I continue.",
    )

    assert turn.latest_reply.empathy_used is True
    assert turn.latest_reply.phase == InterviewPhase.PHASE_1_INTRO
    assert "Take a breath" in turn.latest_reply.text
    assert turn.session.empathy_prompt_count == 1


def test_generated_factual_question_is_used_when_retrieval_is_weak() -> None:
    engine = make_engine()
    engine.question_bank_service.retrieve_questions = lambda **kwargs: [
        RetrievedQuestion(
            question="What is overfitting?",
            answer="",
            domain_tags=["machine_learning", "ml_fundamentals"],
            source="test",
            source_ordinal=1,
            score=0.2,
        )
    ]
    engine._generated_factual_question = lambda session, asked_questions: (
        "How would you compare RLHF, DPO, and LoRA when adapting a foundation model?"
    )
    resume = ParsedResume(
        candidate_name="Candidate",
        headline="GenAI Engineer",
        inferred_domains=["GenAI"],
        projects=["LLM assistant", "Ranking system"],
    )
    bootstrap = engine.bootstrap(resume)
    session = bootstrap.session
    session.current_phase = InterviewPhase.PHASE_4_FACTUAL

    question = engine._factual_question(session)

    assert "RLHF" in question


def test_turn_metadata_updates_integrity_and_mode_flags() -> None:
    engine = make_engine()
    resume = ParsedResume(candidate_name="Candidate", headline="ML Engineer")
    bootstrap = engine.bootstrap(resume)

    turn = engine.process_turn(
        bootstrap.session.id,
        "I work on machine learning systems and evaluation pipelines.",
        TurnMetadata(
            source="audio",
            transcript_retry_count=3,
            tab_switch_count=3,
            window_blur_count=3,
            used_paste=True,
            camera_enabled=True,
            realtime_enabled=True,
        ),
    )

    assert turn.session.video_mode_enabled is True
    assert turn.session.realtime_mode_enabled is True
    assert turn.session.proctoring.suspicious_flags


def test_guardrail_forces_progress_when_model_stalls_in_intro() -> None:
    engine = make_engine()
    engine.openai_provider.__dict__["client"] = StubbornPhaseClient("phase_1_intro")
    resume = ParsedResume(
        candidate_name="Candidate",
        headline="ML Engineer",
        projects=["Bias mitigation system", "Speech synthesis platform"],
    )
    bootstrap = engine.bootstrap(resume)

    first = engine.process_turn(
        bootstrap.session.id,
        "My strongest work is bias mitigation for language models in production.",
    )
    second = engine.process_turn(
        bootstrap.session.id,
        "The project reduced harmful bias while preserving model quality and latency in production.",
    )

    assert first.latest_reply.phase == InterviewPhase.PHASE_1_INTRO
    assert second.latest_reply.phase == InterviewPhase.PHASE_2_DEEP_DIVE
    assert "architecture" in second.latest_reply.text.lower() or "strongest" in second.latest_reply.text.lower()
