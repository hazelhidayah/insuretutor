import logging
from typing import TYPE_CHECKING

from .input import looks_like_prompt_injection

if TYPE_CHECKING:
    from ..retrieval import RetrievedChunk

MIN_EVIDENCE_SCORE = 0.08


def public_chunk(chunk: dict) -> bool:
    return chunk.get("visibility") == "public" and "tenant_id" not in chunk and "roles" not in chunk


def safe_evidence(chunks: list["RetrievedChunk"]) -> list["RetrievedChunk"]:
    accepted = []
    for chunk in chunks:
        if any(looks_like_prompt_injection(value) for value in (chunk.text, chunk.section, chunk.source)):
            logging.getLogger(__name__).info("guardrail decision=retrieval_injection")
        elif chunk.score >= MIN_EVIDENCE_SCORE:
            accepted.append(chunk)
    return accepted


def has_useful_evidence(chunks: list["RetrievedChunk"]) -> bool:
    return bool(safe_evidence(chunks))
