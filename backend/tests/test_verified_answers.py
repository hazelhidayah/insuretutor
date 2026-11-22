from pathlib import Path

import pytest

from app.chat import ChatService
from app.models import ChatRequest
from app.retrieval import RetrievalStore
from app.verified_answers import COOLING_OFF, reviewed_clause


CORPUS = Path(__file__).resolve().parents[2] / "data" / "corpus.json"


class NoModel:
    async def complete(self, _messages):
        raise AssertionError("A reviewed answer must not call the model.")


@pytest.mark.asyncio
async def test_switching_reviewed_answer_language_keeps_its_source():
    service = ChatService(RetrievalStore(CORPUS, ""), NoModel(), 6, 12)
    question = "定期提款有什么条件？"
    chinese = await service.answer(ChatRequest(message=question, language="zh-CN"))
    english = await service.answer(ChatRequest(message=question, language="en"))
    assert "最短一年" in chinese.answer and "最短三年" in chinese.answer
    assert "minimum term of one year" in english.answer and "minimum term of three years" in english.answer
    assert chinese.citations == english.citations
    assert chinese.citations[0].page == 12


@pytest.mark.asyncio
async def test_changed_brochure_passage_withholds_reviewed_answer():
    store = RetrievalStore(CORPUS, "")
    chunk = next(item for item in store.chunks if item["id"] == COOLING_OFF.sources[-1][0])
    chunk["text"] += " Changed source."
    response = await ChatService(store, NoModel(), 6, 12).answer(
        ChatRequest(message="保单的冷静期是多少天？", language="zh-CN")
    )
    assert not response.grounded and not response.citations


def test_contextual_match_requires_the_correct_previous_topic():
    assert reviewed_clause("那从哪一天开始算？", "保单的冷静期是多少天？") is COOLING_OFF
    assert reviewed_clause("那从哪一天开始算？", "定期提款有什么条件？") is None
    assert reviewed_clause("我个人应该取消保单吗？", "保单的冷静期是多少天？") is None
