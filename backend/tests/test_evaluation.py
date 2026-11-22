import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys

from app.chat import ChatService
from app.evaluation import CASES, ROOT, evaluate
from app.models import ChatRequest
from app.providers import ModelProviderError
from app.retrieval import RetrievalStore


def test_offline_suite_exercises_chat_pipeline() -> None:
    cases = json.loads(CASES.read_text(encoding="utf-8"))
    store = RetrievalStore(ROOT / "data" / "corpus.json", "")
    results = asyncio.run(evaluate(cases, store))
    assert len(results) == len(cases)
    assert all(result["passed"] for result in results), results
    assert any("provider_not_called" in result["checks"] for result in results)
    assert any("citation_mapping" in result["checks"] for result in results)
    assert any("language_prompt" in result["checks"] for result in results)


def test_failed_expectation_is_reported_and_exits_nonzero(tmp_path: Path) -> None:
    case = [{"id": "wrong-page", "question": "Is the 4% crediting rate guaranteed?",
             "language": "en", "pages": [9999], "expected": "grounded",
             "offline_answer": "This is an answer. [S1]"}]
    case_file = tmp_path / "cases.json"
    case_file.write_text(json.dumps(case), encoding="utf-8")
    env = {**os.environ, "PYTHONPATH": str(ROOT / "backend")}
    completed = subprocess.run([sys.executable, "-m", "app.evaluation", "--cases", str(case_file)],
                               cwd=ROOT, env=env, capture_output=True, text=True)
    report = json.loads(completed.stdout)
    assert completed.returncode == 1
    assert not report["cases"][0]["checks"]["retrieval_page_at_k"]


def test_live_provider_output_is_assessed_and_offline_cases_skipped() -> None:
    class WrongLanguageProvider:
        async def complete(self, messages):
            return "This is English. [S1]"

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    store = RetrievalStore(ROOT / "data" / "corpus.json", "")
    results = asyncio.run(evaluate(cases, store, WrongLanguageProvider()))
    by_id = {result["id"]: result for result in results}
    assert "unknown-citation" not in by_id
    assert not by_id["rate-zh-tw"]["checks"]["language_script"]
    assert by_id["withdrawal-zh-cn"]["checks"]["reviewed_answer_available"]


def test_follow_up_preserves_conversation_in_provider_prompt() -> None:
    history = [
        {"role": "user", "content": "Is the 4% interest rate guaranteed?"},
        {"role": "assistant", "content": "The brochure describes a conditional guarantee. [S1]"},
    ]

    class FollowUpProvider:
        async def complete(self, messages):
            assert messages[1:-1] == history
            assert "What is the guaranteed interest rate after 15 years?" in messages[-1]["content"]
            return "The guarantee is conditional. [S1]"

    store = RetrievalStore(ROOT / "data" / "corpus.json", "")
    service = ChatService(store, FollowUpProvider(), 6, 12)
    response = asyncio.run(service.answer(ChatRequest(
        message="What is the guaranteed interest rate after 15 years?",
        language="en",
        history=history,
    )))

    assert response.grounded
    assert response.citations


def test_provider_failure_is_localised_without_exposing_details() -> None:
    class FailingProvider:
        async def complete(self, messages):
            raise ModelProviderError("secret upstream response")

    cases = [{
        "id": "provider-failure-zh-tw",
        "question": "4% 的派息率是否保證？",
        "language": "zh-TW",
        "expected": "grounded",
        "pages": [16],
    }]
    store = RetrievalStore(ROOT / "data" / "corpus.json", "")

    service = ChatService(store, FailingProvider(), 6, 12)
    response = asyncio.run(service.answer(ChatRequest(
        message=cases[0]["question"], language="zh-TW"
    )))

    assert not response.grounded
    assert response.language == "zh-TW"
    assert "模型服務目前不可用" in response.answer
    assert "secret upstream response" not in response.answer


def test_invalid_citations_receive_one_bounded_repair_attempt() -> None:
    class RepairingProvider:
        def __init__(self) -> None:
            self.calls = 0

        async def complete(self, messages):
            self.calls += 1
            if self.calls == 1:
                return "The guarantee is described here. [S99]"
            return "The guarantee is described here. [S1]"

    store = RetrievalStore(ROOT / "data" / "corpus.json", "")
    provider = RepairingProvider()
    service = ChatService(store, provider, 6, 12)

    response = asyncio.run(service.answer(ChatRequest(
        message="What interest rate is guaranteed?", language="en"
    )))

    assert provider.calls == 2
    assert response.grounded
    assert response.citations
    assert "[S1]" in response.answer
