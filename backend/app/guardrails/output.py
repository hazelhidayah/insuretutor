import re
from decimal import Decimal

from .input import looks_like_prompt_injection, redact_sensitive

SOURCE_LABEL = re.compile(r"\[(S\d+)\]")
LABEL_LIKE = re.compile(r"\[\s*\*?\s*s\s*[\dilo]+\s*\]", re.IGNORECASE)
PERCENTAGE = re.compile(r"(?<![\d.])(\d+(?:\.\d+)?)\s*[%％]")
HARMFUL_PHRASES = re.compile(r"\bkill yourself\b|\byou (?:are|worthless) (?:an? )?idiot\b|去死吧", re.IGNORECASE)


def valid_source_labels(answer: str, allowed_labels: set[str]) -> bool:
    labels = set(SOURCE_LABEL.findall(answer))
    return bool(labels) and labels.issubset(allowed_labels) and all(
        SOURCE_LABEL.fullmatch(marker) for marker in LABEL_LIKE.findall(answer)
    )


def unsafe_output(answer: str) -> bool:
    return (
        redact_sensitive(answer) != answer
        or looks_like_prompt_injection(answer)
        or bool(HARMFUL_PHRASES.search(answer))
        or len(answer) > 8_000
    )


def percentages_supported(answer: str, cited_evidence: str) -> bool:
    claimed = {Decimal(value) for value in PERCENTAGE.findall(answer)}
    available = {Decimal(value) for value in PERCENTAGE.findall(cited_evidence)}
    return claimed <= available
