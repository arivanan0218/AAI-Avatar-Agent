"""
NLP Text Preprocessing Pipeline

Implements the NLP requirement:
  - Text cleaning and normalisation
  - Tokenisation (NLTK word_tokenize)
  - Stop-word removal
  - Lemmatisation (WordNetLemmatizer)
  - Keyword extraction
  - OpenAI text-embedding-3-large for semantic embeddings (3072-dim)
  - Cosine similarity between texts
"""

import re
import string
from collections import Counter
from typing import Any

import numpy as np

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize

import os

from openai import OpenAI

# Ensure required NLTK corpora are present
for _resource, _path in [
    ("punkt_tab", "tokenizers/punkt_tab"),
    ("stopwords", "corpora/stopwords"),
    ("wordnet", "corpora/wordnet"),
    ("omw-1.4", "corpora/omw-1.4"),
]:
    try:
        nltk.data.find(_path)
    except LookupError:
        nltk.download(_resource, quiet=True)


class TextPreprocessor:
    """
    End-to-end NLP preprocessing for interview responses.

    Pipeline:
        raw text
          → clean  (lowercase, strip noise)
          → tokenise
          → remove stop words
          → lemmatise
          → extract keywords
          → (optionally) embed via OpenAI text-embedding-3-large
    """

    def __init__(self) -> None:
        self._lemmatizer = WordNetLemmatizer()
        self._stop_words = set(stopwords.words("english"))
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._embedding_model = "text-embedding-3-large"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def preprocess(self, text: str) -> dict[str, Any]:
        """
        Run the full NLP pipeline on *text*.

        Returns a dict with:
          original, clean_text, tokens, filtered_tokens,
          lemmatized_tokens, sentences, token_count, keywords
        """
        clean = self._clean(text)
        tokens = word_tokenize(clean)
        filtered = self._remove_stopwords(tokens)
        lemmatized = self._lemmatize(filtered)
        sentences = sent_tokenize(clean)

        return {
            "original": text,
            "clean_text": clean,
            "tokens": tokens,
            "filtered_tokens": filtered,
            "lemmatized_tokens": lemmatized,
            "sentences": sentences,
            "token_count": len(tokens),
            "keywords": self._top_keywords(lemmatized),
        }

    def get_embedding(self, text: str) -> list[float]:
        """Generate an OpenAI text-embedding-3-large vector for *text* (3072-dim)."""
        result = self._client.embeddings.create(
            model=self._embedding_model,
            input=text,
        )
        return list(result.data[0].embedding)

    def cosine_similarity(self, text_a: str, text_b: str) -> float:
        """Return cosine similarity [−1, 1] between two texts via embeddings."""
        a = np.array(self.get_embedding(text_a))
        b = np.array(self.get_embedding(text_b))
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        return float(np.dot(a, b) / denom) if denom else 0.0

    def keyword_overlap(self, text_a: str, text_b: str) -> float:
        """Jaccard similarity of keyword sets — fast, no API call."""
        kw_a = set(self.preprocess(text_a)["keywords"])
        kw_b = set(self.preprocess(text_b)["keywords"])
        if not kw_a and not kw_b:
            return 0.0
        return len(kw_a & kw_b) / len(kw_a | kw_b)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _clean(self, text: str) -> str:
        text = text.lower().strip()
        text = re.sub(r"[^\w\s.,?!'\\-]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _remove_stopwords(self, tokens: list[str]) -> list[str]:
        return [
            t for t in tokens
            if t not in self._stop_words and t not in string.punctuation
        ]

    def _lemmatize(self, tokens: list[str]) -> list[str]:
        return [self._lemmatizer.lemmatize(t) for t in tokens]

    def _top_keywords(self, lemmatized: list[str], n: int = 10) -> list[str]:
        freq = Counter(lemmatized)
        return [w for w, _ in freq.most_common(n)]
