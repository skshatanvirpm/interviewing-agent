from fastapi.testclient import TestClient

from interviewing_agent.main import app
from interviewing_agent.models import InterviewPhase, ParsedResume
from interviewing_agent.services.interview_engine import InterviewEngine, MemorySessionStore
from interviewing_agent.services.openai_client import OpenAIProvider
from interviewing_agent.services.question_bank import QuestionBankService
from interviewing_agent.config import Settings


class StubResumeParser:
    def parse_pdf(self, filename: str, content: bytes) -> ParsedResume:
        return ParsedResume(
            candidate_name="Candidate",
            headline="Machine Learning Engineer",
            summary="Built recommendation and retrieval systems.",
            skills=["Python", "PyTorch", "Retrieval", "Bandits"],
            projects=["RAG assistant", "Recommendation engine"],
            experience=["Led experimentation and evaluation work."],
            inferred_domains=["GenAI", "Recommendation Systems"],
        )


class StubAudioService:
    def transcribe(self, filename: str, content: bytes) -> str:
        return "This is a transcribed answer."

    def synthesize(self, text: str) -> bytes:
        return b"RIFFfakewav"


def make_engine() -> InterviewEngine:
    settings = Settings(openai_api_key=None, interviewer_name="Alex", _env_file=None)
    return InterviewEngine(
        settings,
        OpenAIProvider(settings),
        MemorySessionStore(),
        QuestionBankService(settings),
    )


def test_api_flow_covers_bootstrap_turns_feedback_and_audio() -> None:
    app.state.resume_parser = StubResumeParser()
    app.state.interview_engine = make_engine()
    app.state.audio_service = StubAudioService()

    with TestClient(app) as client:
        bootstrap_response = client.post(
            "/sessions/bootstrap",
            files={"resume": ("candidate.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert bootstrap_response.status_code == 200
        session = bootstrap_response.json()["session"]
        session_id = session["id"]

        answers = [
            "I build machine learning systems focused on retrieval and recommendation.",
            "The RAG assistant used a chunking pipeline, embeddings, retrieval evaluation, and latency monitoring because production failures usually start in retrieval.",
            "I also built a recommendation engine where bandits handled exploration versus exploitation.",
            "We measured CTR lift, offline ranking metrics, and stakeholder impact before launch.",
            "Precision, recall, and F1 should be optimized differently depending on business cost and coverage.",
            "Offline metrics show candidate quality, but online evaluation validates user impact and business trade-offs.",
            "A multi-armed bandit is useful when you need continuous exploration under changing reward signals.",
            "I disagreed with a manager on launch scope, proposed a staged rollout, and aligned the team with data.",
            "I handle ambiguity by defining the decision criteria, shipping the smallest credible slice, and reviewing risk weekly.",
            "When expectations change, I restate the goal, protect the critical quality bar, and renegotiate scope with stakeholders.",
        ]

        latest_phase = InterviewPhase.PHASE_1_INTRO.value
        answer_index = 0
        while latest_phase != InterviewPhase.COMPLETE.value and answer_index < 16:
            answer = answers[min(answer_index, len(answers) - 1)]
            turn_response = client.post(
                f"/interviews/{session_id}/turn",
                json={
                    "candidate_response": answer,
                    "metadata": {
                        "source": "text",
                        "transcript_retry_count": 0,
                        "tab_switch_count": 0,
                        "window_blur_count": 0,
                        "used_paste": False,
                        "camera_enabled": False,
                        "realtime_enabled": False,
                    },
                },
            )
            assert turn_response.status_code == 200
            latest_phase = turn_response.json()["session"]["current_phase"]
            answer_index += 1

        interview_response = client.get(f"/interviews/{session_id}")
        assert interview_response.status_code == 200
        restored = interview_response.json()
        assert restored["messages"]
        assert restored["scores"]["overall"] is not None
        assert restored["final_feedback"] is not None
        assert latest_phase == InterviewPhase.COMPLETE.value

        transcript_response = client.post(
            "/audio/transcribe",
            files={"audio": ("answer.webm", b"fake-audio", "audio/webm")},
        )
        assert transcript_response.status_code == 200
        assert transcript_response.json()["transcript"]

        speak_response = client.post("/audio/speak", json={"text": "Speak this back."})
        assert speak_response.status_code == 200
        assert speak_response.headers["content-type"] == "audio/wav"


def test_api_can_bootstrap_from_cached_parsed_resume() -> None:
    app.state.resume_parser = StubResumeParser()
    app.state.interview_engine = make_engine()
    app.state.audio_service = StubAudioService()

    with TestClient(app) as client:
        response = client.post(
            "/sessions/bootstrap-from-parsed",
            json={
                "resume": {
                    "candidate_name": "Cached Candidate",
                    "headline": "Machine Learning Engineer",
                    "summary": "Built retrieval and ranking systems.",
                    "skills": ["Python", "PyTorch"],
                    "projects": ["Retrieval platform"],
                    "experience": ["Led applied ML delivery"],
                    "education": ["BSc in Computer Science"],
                    "inferred_domains": ["GenAI"],
                    "notes": ["Loaded from cached parsed resume."],
                },
                "resume_label": "cached-resume.pdf",
                "candidate_id": "candidate-123",
                "resume_id": "resume-123",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["resume"]["candidate_name"] == "Cached Candidate"
        assert payload["session"]["candidate_id"] == "candidate-123"
        assert payload["session"]["resume_id"] == "resume-123"
        assert payload["session"]["messages"][0]["role"] == "interviewer"


def test_api_can_begin_intro_after_greeting() -> None:
    app.state.resume_parser = StubResumeParser()
    app.state.interview_engine = make_engine()
    app.state.audio_service = StubAudioService()

    with TestClient(app) as client:
        bootstrap = client.post(
            "/sessions/bootstrap",
            files={"resume": ("candidate.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        session_id = bootstrap.json()["session"]["id"]

        started = client.post(f"/interviews/{session_id}/begin")
        payload = started.json()

        assert started.status_code == 200
        assert len(payload["messages"]) == 2
        assert "alex" in payload["messages"][0]["text"].lower()
        assert "tell me about yourself" in payload["messages"][1]["text"].lower()


def test_api_can_end_interview_and_return_review_session() -> None:
    app.state.resume_parser = StubResumeParser()
    app.state.interview_engine = make_engine()
    app.state.audio_service = StubAudioService()

    with TestClient(app) as client:
        bootstrap = client.post(
            "/sessions/bootstrap",
            files={"resume": ("candidate.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        session_id = bootstrap.json()["session"]["id"]

        client.post(
            f"/interviews/{session_id}/turn",
            json={
                "candidate_response": "I led retrieval and recommendation work in production ML systems.",
                "metadata": {
                    "source": "text",
                    "transcript_retry_count": 0,
                    "tab_switch_count": 0,
                    "window_blur_count": 0,
                    "used_paste": False,
                    "camera_enabled": False,
                    "realtime_enabled": False,
                },
            },
        )

        completed = client.post(f"/interviews/{session_id}/complete")
        payload = completed.json()

        assert completed.status_code == 200
        assert payload["current_phase"] == InterviewPhase.COMPLETE.value
        assert payload["messages"][-1]["phase"] == InterviewPhase.COMPLETE.value
        assert payload["scores"]["overall"] is not None
        assert payload["final_feedback"] is not None
