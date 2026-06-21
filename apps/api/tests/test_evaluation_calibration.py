import json
from pathlib import Path

from interviewing_agent.models import InterviewMessage, InterviewPhase, InterviewSession, ParsedResume
from interviewing_agent.services.evaluation import EvaluationService


def test_evaluation_calibration_cases() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "evaluation_cases.json"
    cases = json.loads(fixture_path.read_text(encoding="utf-8"))
    service = EvaluationService()

    for case in cases:
        phase = InterviewPhase(case["phase"])
        session = InterviewSession(
            target_company="PayPal",
            target_role="Machine Learning Engineer",
            resume=ParsedResume(candidate_name="Candidate"),
            messages=[
                InterviewMessage(role="candidate", phase=phase, text=message)
                for message in case["messages"]
            ],
        )

        evaluation = service.evaluate_phase(session, phase)
        assert evaluation is not None

        if "expected_min_score" in case:
            assert evaluation.score is not None
            assert evaluation.score >= case["expected_min_score"], case["name"]
        if "expected_max_score" in case:
            assert evaluation.score is not None
            assert evaluation.score <= case["expected_max_score"], case["name"]
