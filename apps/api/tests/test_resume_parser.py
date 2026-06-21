from interviewing_agent.config import Settings
from interviewing_agent.models import ParsedResume
from interviewing_agent.services.openai_client import OpenAIProvider
from interviewing_agent.services.resume_parser import ResumeParser


def make_parser() -> ResumeParser:
    settings = Settings(openai_api_key=None, _env_file=None)
    return ResumeParser(settings, OpenAIProvider(settings))


def test_resume_parser_normalizes_sections_from_extracted_text(monkeypatch) -> None:
    parser = make_parser()
    extracted_text = """
    Summary
    Senior machine learning engineer working on recommendation and ranking systems
    Skills
    Python
    PyTorch
    Multi-armed bandits
    Projects
    Ranking platform for marketplace search
    Experience
    Led experimentation for recommendation pipelines
    Education
    BSc in Computer Science
    """
    monkeypatch.setattr(parser, "_extract_pdf_text", lambda content: extracted_text)

    resume = parser.parse_pdf("candidate_resume.pdf", b"pdf-bytes")

    assert resume.candidate_name == "Candidate Resume"
    assert "Python" in resume.skills
    assert "Ranking platform for marketplace search" in resume.projects
    assert "Recommendation Systems" in resume.inferred_domains
    assert resume.summary


def test_resume_parser_deduplicates_lists_and_keeps_existing_values() -> None:
    parser = make_parser()
    normalized = parser._normalize_resume(
        ParsedResume(
            candidate_name="Candidate",
            headline="ML Engineer",
            summary="",
            skills=["Python", "Python", "PyTorch"],
            projects=["RAG system", "RAG system"],
            inferred_domains=["GenAI"],
        ),
        filename="candidate.pdf",
        source_text="Projects\nRAG system\nSkills\nPython\nPyTorch\n",
    )

    assert normalized.skills == ["Python", "PyTorch"]
    assert normalized.projects == ["RAG system"]
    assert "GenAI" in normalized.inferred_domains
