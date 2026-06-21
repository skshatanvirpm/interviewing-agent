from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

from interviewing_agent.models import ParsedResume
from interviewing_agent.config import Settings


QUESTION_PATTERN = re.compile(
    r"^####\s+(?P<ordinal>\d+)\)\s+(?P<question>.+?)(?:\s+\[\[src].*)?$",
    flags=re.MULTILINE,
)

DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "nlp": ("nlp", "language model", "llm", "transformer", "token", "rag"),
    "computer_vision": (
        "computer vision",
        "image",
        "cnn",
        "segmentation",
        "detection",
        "residual network",
        "receptive field",
    ),
    "recommendation_systems": (
        "recommendation",
        "recommender",
        "ranking",
        "bandit",
        "multi-armed bandit",
    ),
    "ml_fundamentals": (
        "bias",
        "variance",
        "overfitting",
        "underfitting",
        "gradient descent",
        "regularization",
        "cross-validation",
        "precision",
        "recall",
        "f1",
    ),
    "genai": ("prompt", "foundation model", "rlhf", "lora", "qlora", "guardrail"),
}


@dataclass
class QuestionBankEntry:
    source: str
    ordinal: int
    question: str
    answer: str
    domain_tags: list[str]
    metadata: dict[str, Any]


@dataclass
class EmbeddedQuestionRecord:
    source: str
    source_ordinal: int
    question: str
    answer: str
    domain_tags: list[str]
    metadata: dict[str, Any]
    embedding: list[float]
    embedding_provider: str
    embedding_model: str


@dataclass
class RetrievedQuestion:
    question: str
    answer: str
    domain_tags: list[str]
    source: str
    source_ordinal: int
    score: float


class QuestionBankService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @cached_property
    def _sentence_transformer(self) -> Any | None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return None

        model_name = self.settings.question_bank_embedding_model
        return SentenceTransformer(model_name)

    def load_entries(self, markdown_path: Path | None = None) -> list[QuestionBankEntry]:
        source_path = markdown_path or self.settings.questions_path
        if source_path.exists():
            markdown = source_path.read_text(encoding="utf-8")
            return self.parse_markdown(markdown)

        embedded_path = self.settings.question_bank_embeddings_path
        if markdown_path is None and embedded_path.exists():
            return [
                QuestionBankEntry(
                    source=record.source,
                    ordinal=record.source_ordinal,
                    question=record.question,
                    answer=record.answer,
                    domain_tags=record.domain_tags,
                    metadata=record.metadata,
                )
                for record in self._load_embedded_records(embedded_path)
            ]

        raise FileNotFoundError(
            f"Question-bank source not found at {source_path}. "
            "Run scripts/build_ml_question_bank.py before rebuilding embeddings."
        )

    def parse_markdown(self, markdown: str) -> list[QuestionBankEntry]:
        source_name = "unknown"
        entries: list[QuestionBankEntry] = []
        current_question: str | None = None
        current_answer_lines: list[str] = []
        current_ordinal = 0

        def flush() -> None:
            nonlocal current_question, current_answer_lines, current_ordinal
            if current_question is None:
                return

            answer = self._clean_answer("\n".join(current_answer_lines).strip())
            domain_tags = self._infer_domain_tags(source_name, current_question, answer)
            entries.append(
                QuestionBankEntry(
                    source=source_name,
                    ordinal=current_ordinal,
                    question=current_question,
                    answer=answer,
                    domain_tags=domain_tags,
                    metadata={
                        "source": source_name,
                        "source_ordinal": current_ordinal,
                        "has_answer": bool(answer),
                    },
                )
            )
            current_question = None
            current_answer_lines = []
            current_ordinal = 0

        for raw_line in markdown.splitlines():
            line = raw_line.rstrip()

            if line.startswith("## Source: "):
                flush()
                source_name = line.removeprefix("## Source: ").strip()
                continue

            match = QUESTION_PATTERN.match(line)
            if match:
                flush()
                current_ordinal = int(match.group("ordinal"))
                current_question = self._clean_question(match.group("question"))
                continue

            if current_question is not None:
                current_answer_lines.append(line)

        flush()
        return entries

    def build_records(self, markdown_path: Path | None = None) -> list[EmbeddedQuestionRecord]:
        entries = self.load_entries(markdown_path)
        provider, model_name = self._embedding_identity()
        records: list[EmbeddedQuestionRecord] = []

        for entry in entries:
            text_for_embedding = self._embedding_text(entry)
            embedding = self.embed_text(text_for_embedding)
            records.append(
                EmbeddedQuestionRecord(
                    source=entry.source,
                    source_ordinal=entry.ordinal,
                    question=entry.question,
                    answer=entry.answer,
                    domain_tags=entry.domain_tags,
                    metadata=entry.metadata,
                    embedding=embedding,
                    embedding_provider=provider,
                    embedding_model=model_name,
                )
            )

        return records

    @cached_property
    def embedded_records(self) -> list[EmbeddedQuestionRecord]:
        path = self.settings.question_bank_embeddings_path
        if path.exists():
            return self._load_embedded_records(path)
        return self.build_records()

    def write_jsonl(
        self,
        output_path: Path | None = None,
        markdown_path: Path | None = None,
    ) -> Path:
        destination = output_path or self.settings.question_bank_embeddings_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        with destination.open("w", encoding="utf-8") as handle:
            for record in self.build_records(markdown_path):
                payload = asdict(record)
                handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

        return destination

    def retrieve_questions(
        self,
        resume: ParsedResume,
        target_role: str,
        job_description: str,
        limit: int = 3,
        exclude_questions: set[str] | None = None,
    ) -> list[RetrievedQuestion]:
        records = self.embedded_records
        excluded = {question.strip() for question in (exclude_questions or set())}
        target_tags = self._target_tags(resume, target_role, job_description)
        query_text = self._query_text(resume, target_role, job_description, target_tags)
        query_embedding = self.embed_text(query_text)
        query_terms = self._keyword_terms(query_text)

        scored: list[RetrievedQuestion] = []
        for record in records:
            if record.question in excluded:
                continue

            score = self._score_record(record, query_embedding, query_terms, target_tags)
            scored.append(
                RetrievedQuestion(
                    question=record.question,
                    answer=record.answer,
                    domain_tags=record.domain_tags,
                    source=record.source,
                    source_ordinal=record.source_ordinal,
                    score=round(score, 4),
                )
            )

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def embed_text(self, text: str) -> list[float]:
        transformer = self._sentence_transformer
        if transformer is not None:
            vector = transformer.encode(text, normalize_embeddings=True).tolist()
            dimensions = self.settings.question_bank_embedding_dimensions
            if len(vector) == dimensions:
                return [round(float(value), 6) for value in vector]

        return self._hash_embedding(text)

    def _hash_embedding(self, text: str) -> list[float]:
        dimensions = self.settings.question_bank_embedding_dimensions
        vector = [0.0] * dimensions
        tokens = re.findall(r"[a-z0-9]+", text.lower())

        for token in tokens:
            token_hash = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(token_hash[:8], "big") % dimensions
            sign = 1.0 if token_hash[8] % 2 == 0 else -1.0
            magnitude = 1.0 + (token_hash[9] / 255.0)
            vector[index] += sign * magnitude

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector

        return [round(value / norm, 6) for value in vector]

    def _embedding_identity(self) -> tuple[str, str]:
        transformer = self._sentence_transformer
        if transformer is not None:
            return (
                self.settings.question_bank_embedding_provider,
                self.settings.question_bank_embedding_model,
            )
        return ("hashing", f"hashing-{self.settings.question_bank_embedding_dimensions}-v1")

    @staticmethod
    def _load_embedded_records(path: Path) -> list[EmbeddedQuestionRecord]:
        records: list[EmbeddedQuestionRecord] = []
        with path.open(encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                records.append(EmbeddedQuestionRecord(**json.loads(line)))
        return records

    @staticmethod
    def _embedding_text(entry: QuestionBankEntry) -> str:
        answer = entry.answer or "No reference answer provided."
        tags = ", ".join(entry.domain_tags)
        return (
            f"source: {entry.source}\n"
            f"question: {entry.question}\n"
            f"answer: {answer}\n"
            f"domain_tags: {tags}"
        )

    @staticmethod
    def _clean_question(text: str) -> str:
        cleaned = re.sub(r"\s+\[\[.*$", "", text).strip()
        return cleaned

    @staticmethod
    def _clean_answer(text: str) -> str:
        cleaned = re.sub(r"\[\[src\d*\]\]\(.*?\)", "", text)
        cleaned = re.sub(r"\[\[src\]\]\(.*?\)", "", cleaned)
        cleaned = re.sub(r"\[\[Answer\]\]\(.*?\)", "", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned

    def _infer_domain_tags(self, source: str, question: str, answer: str) -> list[str]:
        haystack = f"{source} {question} {answer}".lower()
        tags = {"machine_learning"}

        if "nlp" in source.lower():
            tags.add("nlp")

        for tag, keywords in DOMAIN_KEYWORDS.items():
            if any(keyword in haystack for keyword in keywords):
                tags.add(tag)

        return sorted(tags)

    def _target_tags(
        self,
        resume: ParsedResume,
        target_role: str,
        job_description: str,
    ) -> set[str]:
        tags = {"machine_learning"}
        texts = [
            target_role,
            job_description,
            resume.headline,
            resume.summary,
            " ".join(resume.inferred_domains),
            " ".join(resume.skills[:10]),
            " ".join(resume.projects[:5]),
        ]
        haystack = " ".join(texts).lower()

        for tag, keywords in DOMAIN_KEYWORDS.items():
            if any(keyword in haystack for keyword in keywords):
                tags.add(tag)

        return tags

    def _query_text(
        self,
        resume: ParsedResume,
        target_role: str,
        job_description: str,
        target_tags: set[str],
    ) -> str:
        return "\n".join(
            [
                f"target_role: {target_role}",
                f"target_tags: {', '.join(sorted(target_tags))}",
                f"resume_domains: {', '.join(resume.inferred_domains)}",
                f"resume_skills: {', '.join(resume.skills[:10])}",
                f"resume_projects: {', '.join(resume.projects[:5])}",
                f"job_description_excerpt: {job_description[:1600]}",
            ]
        )

    def _score_record(
        self,
        record: EmbeddedQuestionRecord,
        query_embedding: list[float],
        query_terms: set[str],
        target_tags: set[str],
    ) -> float:
        similarity = self._cosine_similarity(query_embedding, record.embedding)
        verified_tags = self._verified_domain_overlap(record, target_tags)
        domain_overlap = len(verified_tags)
        domain_boost = 0.28 * domain_overlap
        record_terms = self._keyword_terms(
            f"{record.question} {record.answer} {' '.join(record.domain_tags)}"
        )
        lexical_overlap = len(query_terms.intersection(record_terms))
        lexical_boost = min(0.32, lexical_overlap * 0.02)
        unsupported_specialist_tags = (
            target_tags.intersection(record.domain_tags) - verified_tags - {"machine_learning"}
        )
        mismatch_penalty = 0.35 * len(unsupported_specialist_tags)
        fundamentals_penalty = (
            0.08
            if "ml_fundamentals" in record.domain_tags
            and target_tags != {"machine_learning"}
            and not verified_tags.intersection(record.domain_tags)
            else 0.0
        )
        return similarity + domain_boost + lexical_boost - fundamentals_penalty - mismatch_penalty

    @staticmethod
    def _keyword_terms(text: str) -> set[str]:
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower())
            if len(token) > 2
        }

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right:
            return 0.0

        limit = min(len(left), len(right))
        dot = sum(left[index] * right[index] for index in range(limit))
        left_norm = math.sqrt(sum(value * value for value in left[:limit]))
        right_norm = math.sqrt(sum(value * value for value in right[:limit]))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    def _verified_domain_overlap(
        self,
        record: EmbeddedQuestionRecord,
        target_tags: set[str],
    ) -> set[str]:
        record_terms = self._keyword_terms(f"{record.question} {record.answer}")
        verified: set[str] = set()
        for tag in target_tags.intersection(record.domain_tags):
            if tag == "machine_learning":
                verified.add(tag)
                continue
            keywords = DOMAIN_KEYWORDS.get(tag, ())
            if any(keyword.replace("-", " ") in " ".join(sorted(record_terms)) for keyword in keywords):
                verified.add(tag)
        return verified
