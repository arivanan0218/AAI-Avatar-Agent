"""
Interview Question Generator

Implements the Few-Shot Learning + Prompt Engineering requirements:
  - Retrieves RAG context (domain knowledge) to ground each question
  - Injects few-shot examples matched to the current difficulty level
  - Maintains a seen-questions buffer to avoid repetition
  - Progresses through difficulty curve: easy → medium → hard → expert
"""

import os
from typing import Any

from openai import OpenAI

from prompts.templates import QUESTION_GENERATION_PROMPT, get_few_shot_text


class QuestionGenerator:
    """
    Generates contextually relevant, difficulty-progressive interview questions
    using few-shot learning and RAG-retrieved domain knowledge.
    """

    def __init__(self, domain: str) -> None:
        self.domain = domain
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._asked: list[str] = []

    async def generate_next(
        self,
        session,           # InterviewSessionManager
        context: list[dict[str, Any]],
    ) -> str | None:
        """
        Generate the next question for *session* informed by *context*.
        Returns None if the interview quota is exhausted.
        """
        if session.question_count >= session.max_questions:
            return None

        difficulty = session.current_difficulty()
        few_shot = get_few_shot_text(self.domain, difficulty, n=2)
        context_text = _format_context(context)
        asked_text = (
            "\n".join(f"  - {q}" for q in self._asked[-5:]) if self._asked else "  None yet."
        )

        prompt = QUESTION_GENERATION_PROMPT.format(
            domain=self.domain.replace("_", " "),
            difficulty=difficulty,
            context=context_text,
            few_shot_examples=few_shot,
            previously_asked=asked_text,
            question_number=session.question_count + 1,
            total_questions=session.max_questions,
        )

        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.75,
            max_tokens=200,
        )

        question = response.choices[0].message.content.strip()
        self._asked.append(question)
        return question


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_context(context: list[dict[str, Any]]) -> str:
    if not context:
        return "  No specific context retrieved."
    lines = []
    for c in context:
        snippet = c["explanation"][:180].rstrip()
        lines.append(f"  [{c['difficulty']}] {c['concept']}: {snippet}…")
    return "\n".join(lines)
