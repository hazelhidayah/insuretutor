"""Run small, transparent checks against the real chat and retrieval pipeline."""
from __future__ import annotations

import argparse
import asyncio
import json
import re
from pathlib import Path
from typing import Any

from .chat import ChatService, LANGUAGE_NAMES
from .models import ChatRequest
from .providers import OpenAICompatibleProvider
from .retrieval import RetrievalStore

ROOT = Path(__file__).resolve().parents[2]
CASES = Path(__file__).parent / "eval_data" / "cases.json"


class FixtureProvider:
    """Returns a prescribed response and records the prompt, without network access."""

    def __init__(self, answer: str = "") -> None:
        self.answer = answer
        self.messages: list[dict[str, str]] = []
        self.calls = 0

    async def complete(self, messages: list[dict[str, str]]) -> str:
        self.calls += 1
        self.messages = messages
        return self.answer


def language_signal(answer: str, language: str) -> bool:
    """A coarse script check, not a language or translation quality assessment."""
    if language == "en":
        return bool(re.search(r"[A-Za-z]{3}", answer)) and not re.search(r"[\u3400-\u9fff]", answer)
    if language in {"zh-CN", "zh-TW"}:
        return bool(re.search(r"[\u3400-\u9fff]", answer))
    return True


async def evaluate(cases: list[dict[str, Any]], store: RetrievalStore, provider: Any | None = None,
                   top_k: int = 6) -> list[dict[str, Any]]:
    """Evaluate independently; only report check results, never provider output or settings."""
    results = []
    for case in cases:
        if provider is not None and case.get("offline_only"):
            continue
        fixture = FixtureProvider(case.get("offline_answer", "")) if provider is None else None
        service = ChatService(store, fixture or provider, top_k, 12)
        request = ChatRequest(
            message=case["question"],
            language=case["language"],
            history=case.get("history", []),
        )
        chunks = service.retrieve(request) if case["expected"] == "grounded" else []
        response = await service.answer(request)
        expected = case["expected"]
        checks: dict[str, bool] = {}
        if "pages" in case:
            checks["retrieval_page_at_k"] = bool(set(case["pages"]) & {c.page for c in chunks})
        if expected == "grounded":
            checks["grounded"] = response.grounded
            # Validate source metadata against exactly the chunks retrieved for this request.
            by_label = {f"S{i}": c for i, c in enumerate(chunks, 1)}
            checks["citation_mapping"] = bool(response.citations) and all(
                c.id in by_label and c.page == by_label[c.id].page
                and c.source == by_label[c.id].source and c.section == by_label[c.id].section
                and f"[{c.id}]" in response.answer for c in response.citations
            )
            checks["language_script"] = language_signal(response.answer, request.language)
            if "required_answer_patterns" in case:
                checks["required_answer_patterns"] = all(
                    re.search(pattern, response.answer) is not None
                    for pattern in case["required_answer_patterns"]
                )
            if case.get("reviewed_answer"):
                checks["reviewed_answer_available"] = service.reviewed_clause(request) is not None and response.grounded
                if fixture:
                    checks["provider_not_called"] = fixture.calls == 0
            elif fixture:
                checks["language_prompt"] = bool(fixture.messages) and (
                    f"Reply in {LANGUAGE_NAMES[request.language]}." in fixture.messages[-1]["content"]
                )
        else:
            notices = {"injection": "Request blocked by the prompt-injection guardrail.",
                       "insufficient": "Insufficient retrieval confidence.",
                       "invalid_citation": "Citation validation failed."}
            checks["expected_guardrail"] = not response.grounded and response.notice == notices[expected] and not response.citations
            if request.language != "auto":
                checks["language_script"] = language_signal(response.answer, request.language)
            if fixture and expected in {"injection", "insufficient"}:
                checks["provider_not_called"] = fixture.calls == 0
        results.append({"id": case["id"], "checks": checks, "passed": all(checks.values())})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Use the configured provider; requests may incur charges")
    parser.add_argument("--corpus", type=Path, default=ROOT / "data" / "corpus.json")
    parser.add_argument("--cases", type=Path, default=CASES)
    args = parser.parse_args()
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    store = RetrievalStore(args.corpus, "")  # Deterministic and offline, including in live-provider mode.
    provider = None
    if args.live:
        from .settings import Settings
        settings = Settings()
        provider = OpenAICompatibleProvider(
            settings.model_base_url,
            settings.model_api_key,
            settings.model_name,
            temperature=settings.model_temperature,
        )
        if not provider.configured:
            parser.error("Live evaluation requires a configured MODEL_API_KEY, MODEL_BASE_URL and MODEL_NAME.")
    results = asyncio.run(evaluate(cases, store, provider))
    print(json.dumps({"mode": "live" if args.live else "offline", "retrieval_mode": store.mode,
                      "passed": sum(r["passed"] for r in results), "total": len(results),
                      "cases": results}, ensure_ascii=False, indent=2))
    return 0 if results and all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
