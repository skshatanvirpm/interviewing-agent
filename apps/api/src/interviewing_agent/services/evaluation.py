from __future__ import annotations

from statistics import mean

from interviewing_agent.models import FinalFeedback, InterviewPhase, InterviewSession, PhaseEvaluation


PHASE_LABELS = {
    InterviewPhase.PHASE_1_INTRO: "Introduction",
    InterviewPhase.PHASE_2_DEEP_DIVE: "Deep Dive",
    InterviewPhase.PHASE_3_BREADTH: "Breadth",
    InterviewPhase.PHASE_4_FACTUAL: "Factual",
    InterviewPhase.PHASE_5_BEHAVIORAL: "Behavioral",
}

PHASE_WEIGHTS = {
    InterviewPhase.PHASE_2_DEEP_DIVE: 0.30,
    InterviewPhase.PHASE_3_BREADTH: 0.25,
    InterviewPhase.PHASE_4_FACTUAL: 0.25,
    InterviewPhase.PHASE_5_BEHAVIORAL: 0.20,
}

DIMENSION_MARKERS: dict[InterviewPhase, dict[str, tuple[str, ...]]] = {
    InterviewPhase.PHASE_1_INTRO: {
        "clarity": ("built", "focused", "worked", "experience", "background", "currently"),
        "role_relevance": ("machine learning", "ml", "llm", "retrieval", "recommendation", "genai"),
        "specificity": ("python", "pytorch", "tensorflow", "latency", "evaluation", "production"),
        "ownership": ("i", "led", "owned", "designed", "shipped", "deployed"),
    },
    InterviewPhase.PHASE_2_DEEP_DIVE: {
        "architecture_clarity": ("architecture", "pipeline", "component", "service", "system"),
        "technical_depth": ("model", "feature", "embedding", "retrieval", "training", "inference"),
        "tradeoff_reasoning": ("because", "trade-off", "alternative", "rejected", "constraint"),
        "production_thinking": ("latency", "monitoring", "failure", "production", "scale", "guardrail"),
    },
    InterviewPhase.PHASE_3_BREADTH: {
        "breadth": ("another", "different", "internship", "research", "second", "broader"),
        "ownership": ("owned", "led", "drove", "implemented", "shipped", "responsible"),
        "adaptability": ("learned", "adapted", "picked up", "ambiguity", "changed", "reframed"),
        "measurement": ("metric", "evaluated", "latency", "a/b", "benchmark", "outcome"),
    },
    InterviewPhase.PHASE_4_FACTUAL: {
        "correctness": ("because", "means", "defined", "difference", "trade-off", "therefore"),
        "specificity": ("precision", "recall", "f1", "bandit", "rag", "lora", "transformer"),
        "reasoning": ("if", "when", "would", "depends", "under", "failure"),
        "coverage": ("example", "monitoring", "evaluation", "objective", "metric"),
    },
    InterviewPhase.PHASE_5_BEHAVIORAL: {
        "ownership": ("i", "owned", "took", "decided", "delivered"),
        "collaboration": ("team", "stakeholder", "partner", "manager", "cross-functional"),
        "conflict_resolution": ("disagreed", "resolved", "aligned", "listened", "negotiated"),
        "judgment": ("trade-off", "priority", "risk", "quality", "speed", "decision"),
    },
}

SUGGESTIONS = {
    "clarity": "Open with your role, strongest project area, and the kind of ML systems you have actually shipped.",
    "role_relevance": "Anchor the answer more directly to the target role by naming the ML domains most relevant to the job.",
    "specificity": "Use concrete technologies, metrics, or project details so the introduction sounds less generic.",
    "architecture_clarity": "Break your answer into components, data flow, model choice, and evaluation so the design is easier to follow.",
    "technical_depth": "Go one layer deeper on the implementation details instead of staying at the project-summary level.",
    "tradeoff_reasoning": "State the alternative you considered and why you rejected it.",
    "production_thinking": "Include deployment risks, monitoring, failure modes, and how you would harden the system in production.",
    "breadth": "Use a second example that shows a different problem space or technical stack.",
    "ownership": "Be explicit about what you personally owned instead of describing only team output.",
    "adaptability": "Show how you handled ambiguity or learned something new under time pressure.",
    "measurement": "Anchor the answer in metrics, experiments, or outcomes rather than intuition.",
    "correctness": "Answer the factual question directly before expanding into examples.",
    "specificity": "Use precise ML terminology and concrete examples to show command of the topic.",
    "reasoning": "Explain the conditions under which your answer changes instead of giving a one-size-fits-all answer.",
    "coverage": "Cover definition, trade-off, and practical usage so the answer feels complete.",
    "collaboration": "Name the stakeholders and show how you worked across functions.",
    "conflict_resolution": "Describe the disagreement, your approach, and how alignment was reached.",
    "judgment": "Make the decision criteria explicit so your leadership judgment is visible.",
}


class EvaluationService:
    def evaluate_session(self, session: InterviewSession) -> InterviewSession:
        phase_evaluations: dict[str, PhaseEvaluation] = {}
        for phase in PHASE_WEIGHTS:
            evaluation = self.evaluate_phase(session, phase)
            if evaluation:
                phase_evaluations[phase.value] = evaluation

        intro_evaluation = self.evaluate_phase(session, InterviewPhase.PHASE_1_INTRO)
        if intro_evaluation and not phase_evaluations:
            phase_evaluations[InterviewPhase.PHASE_1_INTRO.value] = intro_evaluation

        session.phase_evaluations = phase_evaluations
        session.scores.phase_2 = self._score_for_phase(phase_evaluations, InterviewPhase.PHASE_2_DEEP_DIVE)
        session.scores.phase_3 = self._score_for_phase(phase_evaluations, InterviewPhase.PHASE_3_BREADTH)
        session.scores.phase_4 = self._score_for_phase(phase_evaluations, InterviewPhase.PHASE_4_FACTUAL)
        session.scores.phase_5 = self._score_for_phase(phase_evaluations, InterviewPhase.PHASE_5_BEHAVIORAL)
        session.scores.overall = self.compute_overall_score(session)
        session.final_feedback = self.build_final_feedback(session)
        return session

    def evaluate_phase(
        self,
        session: InterviewSession,
        phase: InterviewPhase,
    ) -> PhaseEvaluation | None:
        candidate_messages = [
            message.text
            for message in session.messages
            if message.role == "candidate" and message.phase == phase
        ]
        if not candidate_messages:
            return None

        combined_text = " ".join(candidate_messages).lower()
        token_count = len(combined_text.split())
        dimensions: dict[str, float] = {}

        for dimension, markers in DIMENSION_MARKERS[phase].items():
            hits = sum(combined_text.count(marker) for marker in markers)
            length_bonus = min(2.4, token_count / 55)
            score = min(10.0, 3.6 + hits * 1.1 + length_bonus)
            dimensions[dimension] = round(score, 1)

        score = round(mean(dimensions.values()), 1)
        ordered_dimensions = sorted(dimensions.items(), key=lambda item: item[1], reverse=True)
        strengths = [
            self._humanize_dimension(name)
            for name, value in ordered_dimensions
            if value >= 7.0
        ][:2]
        weaknesses = [
            self._humanize_dimension(name)
            for name, value in reversed(ordered_dimensions)
            if value < 6.2
        ][:2]
        weakest_dimension = min(dimensions, key=dimensions.get)
        evidence = [message[:160] for message in candidate_messages[-2:]]
        confidence = round(min(0.95, 0.45 + 0.08 * len(candidate_messages) + token_count / 500), 2)

        return PhaseEvaluation(
            phase=phase,
            label=PHASE_LABELS[phase],
            score=score,
            dimensions=dimensions,
            evidence=evidence,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestion=SUGGESTIONS[weakest_dimension],
            confidence=confidence,
        )

    def compute_overall_score(self, session: InterviewSession) -> float | None:
        if not session.phase_evaluations:
            return None

        weighted_total = 0.0
        total_weight = 0.0
        for phase, weight in PHASE_WEIGHTS.items():
            evaluation = session.phase_evaluations.get(phase.value)
            if evaluation and evaluation.score is not None:
                weighted_total += evaluation.score * weight
                total_weight += weight

        if total_weight == 0:
            intro_evaluation = session.phase_evaluations.get(InterviewPhase.PHASE_1_INTRO.value)
            return round(intro_evaluation.score, 1) if intro_evaluation and intro_evaluation.score is not None else None
        return round(weighted_total / total_weight, 1)

    def build_final_feedback(self, session: InterviewSession) -> FinalFeedback | None:
        if not session.phase_evaluations:
            return None

        strengths: list[str] = []
        weaknesses: list[str] = []
        suggestions: list[str] = []
        for evaluation in session.phase_evaluations.values():
            strengths.extend(evaluation.strengths)
            weaknesses.extend(evaluation.weaknesses)
            if evaluation.suggestion:
                suggestions.append(evaluation.suggestion)

        strengths = self._dedupe(strengths)[:4]
        weaknesses = self._dedupe(weaknesses)[:4]
        suggestions = self._dedupe(suggestions)[:4]

        role_alignment = self._role_alignment_notes(session)
        integrity_notes = session.proctoring.suspicious_flags[:]
        overall = session.scores.overall or self.compute_overall_score(session)
        if overall is None:
            return None

        summary = (
            f"Overall score: {overall}/10. "
            f"The interview was strongest in {strengths[0].lower() if strengths else 'core delivery'} "
            f"and weakest in {weaknesses[0].lower() if weaknesses else 'consistency under pressure'}."
        )
        if integrity_notes:
            summary += " Integrity signals suggest some answers should be interpreted with caution."

        return FinalFeedback(
            overall_score=overall,
            overall_summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            role_alignment=role_alignment,
            integrity_notes=integrity_notes,
        )

    @staticmethod
    def _score_for_phase(
        phase_evaluations: dict[str, PhaseEvaluation],
        phase: InterviewPhase,
    ) -> float | None:
        evaluation = phase_evaluations.get(phase.value)
        return evaluation.score if evaluation else None

    @staticmethod
    def _humanize_dimension(name: str) -> str:
        return name.replace("_", " ").title()

    @staticmethod
    def _dedupe(values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            key = value.lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            unique.append(value)
        return unique

    @staticmethod
    def _role_alignment_notes(session: InterviewSession) -> list[str]:
        notes: list[str] = []
        role = session.target_role.lower()
        domains = {item.lower() for item in session.resume.inferred_domains}
        if "genai" in role or "llm" in role or {"genai", "nlp"} & domains:
            notes.append("Role alignment: the interview covered GenAI / LLM signals from the target role.")
        if "recommend" in role or "recommendation systems" in domains:
            notes.append("Role alignment: factual retrieval emphasized recommendation-system topics.")
        if "payments" in session.target_company.lower():
            notes.append("Company alignment: behavioral prompts favored production judgment and stakeholder communication.")
        if not notes:
            notes.append("Role alignment: the interview remained anchored to the ML engineer target role.")
        return notes
