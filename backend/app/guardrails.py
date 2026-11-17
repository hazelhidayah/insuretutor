from __future__ import annotations

import re

from .retrieval import RetrievedChunk


INJECTION_PATTERNS = (
    r"ignore (all|any|the|your) (previous|prior|system) instructions",
    r"reveal (the )?(system|developer) prompt",
    r"act as (a|an) ",
    r"忽略.*指令",
    r"显示.*系统.*提示",
    r"顯示.*系統.*提示",
)


def looks_like_prompt_injection(message: str) -> bool:
    lowered = message.lower()
    return any(re.search(pattern, lowered, re.IGNORECASE) for pattern in INJECTION_PATTERNS)


def has_useful_evidence(chunks: list[RetrievedChunk]) -> bool:
    return bool(chunks and chunks[0].score >= 0.08)


def valid_source_labels(answer: str, allowed_labels: set[str]) -> bool:
    labels = set(re.findall(r"\[(S\d+)\]", answer))
    return bool(labels) and labels.issubset(allowed_labels)

