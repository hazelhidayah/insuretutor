from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..guardrails.retrieval import public_chunk


# Function words do not demonstrate that a passage addresses a question.
QUERY_STOP_WORDS = frozenset(
    "a an and are as at be can could did do does for from had has have how i if in is it "
    "may me my of on or should the their this to was what when where which who why will with would "
    "actually please tell explain".split()
)
WORD_RE = re.compile(r"[a-z]+|[0-9]+", re.IGNORECASE)
CJK_SEQUENCE_RE = re.compile(r"[\u3400-\u9fff]+")
TOKEN_RE = re.compile(r"[a-z0-9]+|[\u3400-\u9fff]", re.IGNORECASE)
CJK_QUERY_LEAD_INS = ("我想知道", "我想了解", "請問", "请问")
CJK_VARIANT_TRANSLATION = str.maketrans(
    {
        "证": "證",
        "条": "條",
        "么": "麼",
        "这": "這",
        "与": "與",
        "为": "為",
        "于": "於",
        "会": "會",
        "将": "將",
        "应": "應",
        "须": "須",
        "里": "裡",
        "险": "險",
        "据": "據",
        "单": "單",
        "静": "靜",
        "请": "請",
        "产": "產",
        "册": "冊",
        "计": "計",
        "费": "費",
        "风": "風",
    }
)


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
        self.chunks: list[dict] = [chunk for chunk in payload["chunks"] if public_chunk(chunk)]
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

    @staticmethod
    def _query_has_evidence(query: str, text: str) -> bool:
        """Require substantive query content in a passage before trusting its rank.

        This deliberately conservative check supplements relative lexical and dense
        rankings. It reduces obvious out-of-scope matches, but it is not a semantic
        entailment check and can reject valid paraphrases.
        """
        cjk_sequences = CJK_SEQUENCE_RE.findall(query)
        if cjk_sequences:
            compact_query = "".join(cjk_sequences).translate(CJK_VARIANT_TRANSLATION)
            for lead_in in CJK_QUERY_LEAD_INS:
                compact_query = compact_query.removeprefix(lead_in.translate(CJK_VARIANT_TRANSLATION))
            compact_text = "".join(CJK_SEQUENCE_RE.findall(text)).translate(CJK_VARIANT_TRANSLATION)
            query_bigrams = {
                compact_query[index : index + 2]
                for index in range(max(0, len(compact_query) - 1))
            }
            if not query_bigrams:
                return compact_query in compact_text
            matched = sum(bigram in compact_text for bigram in query_bigrams)
            return matched >= 2 and matched / len(query_bigrams) >= 0.3

        terms = set(WORD_RE.findall(query.lower())) - QUERY_STOP_WORDS
        if not terms:
            return False
        document_terms = set(WORD_RE.findall(text.lower()))
        return len(terms & document_terms) / len(terms) >= 0.6

    def search(self, query: str, top_k: int = 6) -> list[RetrievedChunk]:
        lexical = self._lexical_scores(query)
        dense = self._dense_scores(query)
        combined = lexical if self.mode == "lexical" else (0.42 * lexical + 0.58 * dense)
        ranked_indices = np.argsort(-combined)[:top_k]

        results = []
        for index in ranked_indices:
            chunk = self.chunks[int(index)]
            score = float(combined[index])
            if not self._query_has_evidence(query, chunk["text"]):
                score = 0.0
            results.append(
                RetrievedChunk(
                    id=chunk["id"],
                    source=chunk["source"],
                    page=chunk["page"],
                    section=chunk["section"],
                    text=chunk["text"],
                    score=score,
                )
            )
        # Keep passages that satisfy the evidence check ahead of zero-confidence matches.
        results.sort(key=lambda chunk: chunk.score, reverse=True)
        return results

    def public_passage(self, chunk_id: str) -> RetrievedChunk | None:
        for chunk in self.chunks:
            if chunk["id"] == chunk_id:
                return RetrievedChunk(chunk_id, chunk["source"], chunk["page"], chunk["section"], chunk["text"], 1.0)
        return None


def stable_chunk_id(source: str, page: int, text: str) -> str:
    digest = hashlib.sha1(f"{source}:{page}:{text}".encode()).hexdigest()[:10]
    return f"source-{page}-{digest}"

