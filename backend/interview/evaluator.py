"""
Answer Evaluator

Implements the Chain-of-Thought (CoT) prompting requirement:
  - Breaks evaluation into explicit reasoning steps before scoring
  - Returns structured JSON with per-dimension scores + qualitative feedback
  - Weighted overall score: technical_accuracy×0.5 + completeness×0.3 + communication×0.2
"""

import json
import os
from typing import Any

from openai import OpenAI

from prompts.templates import CHAIN_OF_THOUGHT_EVALUATION_PROMPT


class AnswerEvaluator:
    """
    CoT-based structured evaluator for interview answers.

    Scoring dimensions:
        technical_accuracy  — factual correctness and depth (weight 0.5)
        completeness        — coverage of expected key concepts  (weight 0.3)
        communication       — clarity, structure, conciseness   (weight 0.2)
        overall_score       — weighted composite (computed locally, not by LLM)
    """

    _WEIGHTS = {"technical_accuracy": 0.5, "completeness": 0.3, "communication": 0.2}

    def __init__(self) -> None:
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def evaluate(self, question: str, answer: str, domain: str) -> dict[str, Any]:
        """
        Evaluate *answer* for *question* using chain-of-thought reasoning.

        Returns:
            {
              reasoning, technical_accuracy, completeness, communication,
              key_concepts_covered, key_concepts_missing, feedback, overall_score
            }
        """
        prompt = CHAIN_OF_THOUGHT_EVALUATION_PROMPT.format(
            domain=domain.replace("_", " "),
            question=question,
            answer=answer,
        )

        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=700,
            response_format={"type": "json_object"},
        )

        try:
            result: dict[str, Any] = json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, AttributeError, TypeError):
            result = self._fallback()

        # Clamp scores to [0, 10] then compute weighted overall
        for dim in self._WEIGHTS:
            result[dim] = max(0, min(10, int(result.get(dim, 5))))

        result["overall_score"] = round(
            sum(result[dim] * w for dim, w in self._WEIGHTS.items()), 2
        )
        return result

    # ------------------------------------------------------------------

    @staticmethod
    def _fallback() -> dict[str, Any]:
        return {
            "reasoning": "Evaluation could not be completed.",
            "technical_accuracy": 5,
            "completeness": 5,
            "communication": 5,
            "key_concepts_covered": [],
            "key_concepts_missing": [],
            "feedback": "Unable to evaluate this response automatically.",
        }
