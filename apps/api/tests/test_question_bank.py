import json

from interviewing_agent.config import Settings
from interviewing_agent.models import ParsedResume
from interviewing_agent.services.question_bank import (
    EmbeddedQuestionRecord,
    QuestionBankService,
)


def make_service() -> QuestionBankService:
    settings = Settings(openai_api_key=None, _env_file=None)
    return QuestionBankService(settings)


def test_parse_markdown_extracts_questions() -> None:
    service = make_service()
    entries = service.load_entries()

    assert entries
    first = entries[0]
    assert first.question
    assert first.source
    assert first.source.startswith("project-authored/")
    assert "machine_learning" in first.domain_tags


def test_embedding_dimensions_match_pgvector_schema() -> None:
    service = make_service()
    vector = service.embed_text("What is overfitting and how do you detect it?")

    assert len(vector) == 384
    assert any(value != 0 for value in vector)


def test_jsonl_output_contains_embedding_metadata(tmp_path) -> None:
    service = make_service()
    output_path = tmp_path / "question_bank.jsonl"

    service.write_jsonl(output_path=output_path)

    first_row = json.loads(output_path.read_text(encoding="utf-8").splitlines()[0])
    assert "embedding" in first_row
    assert len(first_row["embedding"]) == 384
    assert "embedding_provider" in first_row
    assert "domain_tags" in first_row


def make_record(
    service: QuestionBankService,
    question: str,
    answer: str,
    domain_tags: list[str],
    source_ordinal: int,
) -> EmbeddedQuestionRecord:
    embedding = service.embed_text(
        f"question: {question}\nanswer: {answer}\ndomain_tags: {','.join(domain_tags)}"
    )
    return EmbeddedQuestionRecord(
        source="test",
        source_ordinal=source_ordinal,
        question=question,
        answer=answer,
        domain_tags=domain_tags,
        metadata={"source": "test", "source_ordinal": source_ordinal},
        embedding=embedding,
        embedding_provider="test",
        embedding_model="test",
    )


def test_retrieval_prefers_matching_domain_tags() -> None:
    service = make_service()
    recommendation = make_record(
        service,
        "What is the exploration versus exploitation trade-off in recommender systems?",
        "Bandits deliberately balance exploration and exploitation.",
        ["machine_learning", "recommendation_systems"],
        1,
    )
    vision = make_record(
        service,
        "Why do convolutions preserve spatial information in images?",
        "They operate on local neighborhoods and share weights.",
        ["computer_vision", "machine_learning"],
        2,
    )
    service.__dict__["embedded_records"] = [vision, recommendation]

    resume = ParsedResume(
        inferred_domains=["Recommendation systems"],
        skills=["ranking", "bandits"],
        projects=["Recommender system"],
    )
    retrieved = service.retrieve_questions(
        resume=resume,
        target_role="Recommendation Systems ML Engineer",
        job_description="Need deep experience with recommenders and multi-armed bandits.",
        limit=1,
    )

    assert retrieved
    assert "exploration versus exploitation" in retrieved[0].question.lower()


def test_retrieval_skips_excluded_questions() -> None:
    service = make_service()
    first = make_record(
        service,
        "What is overfitting?",
        "It is when the model memorizes noise.",
        ["machine_learning", "ml_fundamentals"],
        1,
    )
    second = make_record(
        service,
        "Explain the bias-variance trade-off.",
        "Bias and variance move in opposite directions as model flexibility changes.",
        ["machine_learning", "ml_fundamentals"],
        2,
    )
    service.__dict__["embedded_records"] = [first, second]

    resume = ParsedResume(inferred_domains=["Classical ML"])
    retrieved = service.retrieve_questions(
        resume=resume,
        target_role="Machine Learning Engineer",
        job_description="Expect strong ML fundamentals.",
        limit=1,
        exclude_questions={first.question},
    )

    assert retrieved
    assert retrieved[0].question == second.question
