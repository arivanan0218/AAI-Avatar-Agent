"""
Interview Session Manager

Tracks the full state of one interview session:
  - Which question is currently active
  - History of (question, answer, evaluation) triples
  - Progression through difficulty levels
  - Final performance report generation
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


class InterviewSessionManager:
    """
    Finite-state manager for a single interview session.

    State transitions:
        idle  →  question_pending  →  awaiting_answer  →  (repeat or done)
    """

    DIFFICULTY_CURVE = ["easy", "easy", "medium", "medium", "medium", "hard", "hard", "expert"]

    def __init__(self, domain: str, max_questions: int = 8) -> None:
        self.domain = domain
        self.max_questions = max_questions
        self.is_active = True
        self.question_count = 0
        self.start_time = datetime.now()
        self._current_question: str | None = None
        self._followups_asked = 0
        self._answer_parts: list[str] = []
        self._qa_log: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Question lifecycle
    # ------------------------------------------------------------------

    def get_current_question(self) -> str | None:
        return self._current_question

    def set_current_question(self, question: str) -> None:
        self._current_question = question
        self._followups_asked = 0
        self._answer_parts = []
        self.question_count += 1

    def current_difficulty(self) -> str:
        idx = min(self.question_count, len(self.DIFFICULTY_CURVE) - 1)
        return self.DIFFICULTY_CURVE[idx]

    # ------------------------------------------------------------------
    # Follow-up tracking (lets the interviewer probe deeper on one topic)
    # ------------------------------------------------------------------

    @property
    def followups_asked(self) -> int:
        return self._followups_asked

    def register_followup(self) -> None:
        self._followups_asked += 1

    def add_answer_part(self, text: str) -> None:
        """Accumulate answer text for the current question (initial answer + follow-up replies)."""
        if text:
            self._answer_parts.append(text)

    def current_answer_text(self) -> str:
        return " ".join(self._answer_parts)

    # ------------------------------------------------------------------
    # Answer recording
    # ------------------------------------------------------------------

    def record_answer(self, evaluation: dict[str, Any]) -> None:
        self._qa_log.append({
            "question_number": len(self._qa_log) + 1,
            "question": self._current_question,
            "answer": self.current_answer_text(),
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat(),
        })
        self._current_question = None
        self._followups_asked = 0
        self._answer_parts = []

    # ------------------------------------------------------------------
    # Termination
    # ------------------------------------------------------------------

    def should_end_interview(self) -> bool:
        return (
            self.question_count >= self.max_questions
            and self._current_question is None
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_average_score(self) -> float:
        if not self._qa_log:
            return 0.0
        scores = [e["evaluation"].get("overall_score", 0) for e in self._qa_log]
        return round(sum(scores) / len(scores), 2)

    def generate_report(self) -> dict[str, Any]:
        avg = self.get_average_score()
        duration = int((datetime.now() - self.start_time).total_seconds())

        strengths = [
            e["question"]
            for e in self._qa_log
            if e["evaluation"].get("overall_score", 0) >= 7
        ]
        improvements = [
            e["question"]
            for e in self._qa_log
            if e["evaluation"].get("overall_score", 0) < 6
        ]

        dimension_avgs = self._dimension_averages()

        return {
            "domain": self.domain,
            "total_questions": self.question_count,
            "average_score": avg,
            "recommendation": _recommendation(avg),
            "duration_seconds": duration,
            "dimension_scores": dimension_avgs,
            "strengths": strengths,
            "areas_for_improvement": improvements,
            "qa_log": self._qa_log,
        }

    def _dimension_averages(self) -> dict[str, float]:
        if not self._qa_log:
            return {}
        dims = ["technical_accuracy", "completeness", "communication"]
        result = {}
        for d in dims:
            vals = [e["evaluation"].get(d, 0) for e in self._qa_log]
            result[d] = round(sum(vals) / len(vals), 2)
        return result


def _recommendation(score: float) -> str:
    if score >= 8.0:
        return "Highly Recommended"
    if score >= 6.5:
        return "Recommended"
    if score >= 5.0:
        return "Borderline — Needs Improvement"
    return "Not Recommended"
