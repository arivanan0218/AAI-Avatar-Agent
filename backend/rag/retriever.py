"""
RAG Retriever

Thin async wrapper around KnowledgeBase for use inside the LiveKit agent.
Provides domain-scoped retrieval to inform question generation.
"""

from typing import Any
from .knowledge_base import KnowledgeBase


class KnowledgeRetriever:
    """Async retrieval interface for the interview agent."""

    def __init__(self, domain: str) -> None:
        self.domain = domain
        self._kb = KnowledgeBase()

    async def retrieve(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Return top-k knowledge chunks semantically closest to *query*."""
        return self._kb.query(query, self.domain, top_k=top_k)

    async def retrieve_by_concept(self, concept: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Targeted retrieval by concept name."""
        return self._kb.query(concept, self.domain, top_k=top_k)
