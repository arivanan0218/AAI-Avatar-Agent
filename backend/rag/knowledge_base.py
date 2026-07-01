"""
Domain Knowledge Base

Implements the Transformer/LLM + RAG requirement:
  - Loads structured domain knowledge from JSON files in backend/data/
  - Generates OpenAI text-embedding-3-large vectors (3072-dim) for each knowledge chunk
  - Upserts vectors into a Pinecone serverless index
  - Exposes a query() method for semantic search (top-k retrieval)
"""

import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec


_DATA_DIR = Path(__file__).parent.parent / "data"
_INDEX_NAME = "interview-knowledge"
_EMBED_MODEL = "text-embedding-3-large"
_EMBED_DIM = 3072  # text-embedding-3-large dimension


class KnowledgeBase:
    """
    Pinecone-backed vector store for interview domain knowledge.

    Usage:
        kb = KnowledgeBase()
        kb.load_domain("software_engineering")   # one-time ingestion
        results = kb.query("explain REST vs GraphQL", domain="software_engineering")
    """

    def __init__(self) -> None:
        self._pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._index = self._get_or_create_index()

    # ------------------------------------------------------------------
    # Ingestion
    # ------------------------------------------------------------------

    def load_domain(self, domain: str) -> int:
        """
        Load all knowledge chunks for *domain* into Pinecone.
        Returns the number of vectors upserted.
        Idempotent — safe to call multiple times.
        """
        path = _DATA_DIR / f"{domain}.json"
        if not path.exists():
            raise FileNotFoundError(f"No knowledge file for domain '{domain}' at {path}")

        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)

        vectors = []
        for i, topic in enumerate(data["topics"]):
            text = f"{topic['concept']}: {topic['explanation']}"
            vectors.append({
                "id": f"{domain}_{i}",
                "values": self._embed(text),
                "metadata": {
                    "domain": domain,
                    "concept": topic["concept"],
                    "explanation": topic["explanation"],
                    "difficulty": topic.get("difficulty", "medium"),
                    "sample_questions": json.dumps(topic.get("sample_questions", [])),
                    "tags": json.dumps(topic.get("tags", [])),
                },
            })

        # Upsert in batches of 100 (Pinecone limit)
        for start in range(0, len(vectors), 100):
            self._index.upsert(vectors=vectors[start : start + 100])

        return len(vectors)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def query(self, query_text: str, domain: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Semantic search: returns top-k knowledge chunks most relevant to *query_text*.
        Filtered to *domain* so cross-domain noise is avoided.
        """
        results = self._index.query(
            vector=self._embed(query_text),
            top_k=top_k,
            filter={"domain": {"$eq": domain}},
            include_metadata=True,
        )
        return [
            {
                "concept": m.metadata["concept"],
                "explanation": m.metadata["explanation"],
                "difficulty": m.metadata["difficulty"],
                "sample_questions": json.loads(m.metadata.get("sample_questions", "[]")),
                "tags": json.loads(m.metadata.get("tags", "[]")),
                "relevance_score": round(m.score, 4),
            }
            for m in results.matches
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _embed(self, text: str) -> list[float]:
        result = self._client.embeddings.create(model=_EMBED_MODEL, input=text)
        return list(result.data[0].embedding)

    def _get_or_create_index(self):
        existing = {idx.name for idx in self._pc.list_indexes()}
        if _INDEX_NAME not in existing:
            self._pc.create_index(
                name=_INDEX_NAME,
                dimension=_EMBED_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        return self._pc.Index(_INDEX_NAME)
