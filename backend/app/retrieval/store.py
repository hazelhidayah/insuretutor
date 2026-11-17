from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np


TOKEN_RE = re.compile(r"[a-z0-9]+|[\u3400-\u9fff]", re.IGNORECASE)


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    source: str
    page: int
    section: str
    text: str
    score: float


class RetrievalStore:
    """Hybrid retriever with local multilingual embeddings and lexical fallback."""

    def __init__(
        self,
        corpus_path: Path,
        embedding_model: str,
        embedding_cache_path: Path | None = None,
    ) -> None:
        payload = json.loads(corpus_path.read_text(encoding="utf-8"))
        self.chunks: list[dict] = payload["chunks"]
        self._documents = [chunk["text"] for chunk in self.chunks]
        self._token_counts = [Counter(self._tokens(text)) for text in self._documents]
        self._document_frequency = Counter(
            token for counts in self._token_counts for token in counts
        )
        self._embedding_model_name = embedding_model
        self._model = None
        self._embeddings: np.ndarray | None = None
        self.mode = "lexical"

        if not embedding_model:
            return

        try:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(
                model_name=embedding_model,
                cache_dir=str(embedding_cache_path) if embedding_cache_path else None,
            )
            self._embeddings = self._normalise(
                np.asarray(
                    list(self._model.embed(self._documents)),
                    dtype=np.float32,
                )
            )
            self.mode = "hybrid"
        except Exception as exc:  # pragma: no cover - exercised in minimal/offline images
            self.embedding_error = f"{type(exc).__name__}: {exc}"

    @staticmethod
    def _tokens(text: str) -> list[str]:
        compact = re.sub(r"\s+", " ", text.lower())
        word_tokens = TOKEN_RE.findall(compact)
        compact_no_space = re.sub(r"\s+", "", compact)
        char_ngrams = [compact_no_space[i : i + 3] for i in range(max(0, len(compact_no_space) - 2))]
        return word_tokens + char_ngrams

    @staticmethod
    def _normalise(matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        return matrix / np.maximum(norms, 1e-12)

    def _lexical_scores(self, query: str) -> np.ndarray:
        query_counts = Counter(self._tokens(query))
        scores = np.zeros(len(self.chunks), dtype=np.float32)
        document_count = len(self.chunks)
        for index, counts in enumerate(self._token_counts):
            score = 0.0
            length = max(sum(counts.values()), 1)
            for token, query_frequency in query_counts.items():
                frequency = counts.get(token, 0)
                if not frequency:
                    continue
                inverse_document_frequency = math.log(
                    1 + (document_count - self._document_frequency[token] + 0.5)
                    / (self._document_frequency[token] + 0.5)
                )
                score += query_frequency * inverse_document_frequency * frequency / (frequency + 1.2 * length / 500)
            scores[index] = score
        maximum = float(scores.max()) if scores.size else 0.0
        return scores / maximum if maximum > 0 else scores

    def _dense_scores(self, query: str) -> np.ndarray:
        if self._model is None or self._embeddings is None:
            return np.zeros(len(self.chunks), dtype=np.float32)
        query_embedding = np.asarray(list(self._model.query_embed(query)), dtype=np.float32)
        query_embedding = self._normalise(query_embedding)[0]
        return self._embeddings @ query_embedding

    def search(self, query: str, top_k: int = 6) -> list[RetrievedChunk]:
        lexical = self._lexical_scores(query)
        dense = self._dense_scores(query)
        combined = lexical if self.mode == "lexical" else (0.42 * lexical + 0.58 * dense)
        ranked_indices = np.argsort(-combined)[:top_k]

        results = []
        for index in ranked_indices:
            chunk = self.chunks[int(index)]
            results.append(
                RetrievedChunk(
                    id=chunk["id"],
                    source=chunk["source"],
                    page=chunk["page"],
                    section=chunk["section"],
                    text=chunk["text"],
                    score=float(combined[index]),
                )
            )
        return results


def stable_chunk_id(source: str, page: int, text: str) -> str:
    digest = hashlib.sha1(f"{source}:{page}:{text}".encode()).hexdigest()[:10]
    return f"source-{page}-{digest}"

