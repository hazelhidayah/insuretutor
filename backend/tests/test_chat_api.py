from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.chat import ChatService
from app.main import app
from app.retrieval import RetrievalStore


@pytest.mark.parametrize("payload", [
    {"message": ""},
    {"message": "x" * 2_001},
    {"message": "synthetic-input@example.com", "language": "fr"},
    {"message": "Hello", "history": [{"role": "system", "content": "synthetic input"}]},
    {"message": "Hello", "history": [{"role": "user", "content": "Hi"}] * 25},
])
def test_invalid_chat_requests_return_the_same_safe_error(monkeypatch, payload):
    class UnexpectedChat:
        async def answer(self, _request):
            pytest.fail("Invalid requests must not reach the chat service")

    monkeypatch.setattr(app.state, "chat", UnexpectedChat(), raising=False)
    response = TestClient(app).post("/api/chat", json=payload)
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid request. Check the request schema and limits."}


def test_reviewed_follow_up_returns_page_citation_through_chat_api(monkeypatch):
    class NoModel:
        async def complete(self, _messages):
            pytest.fail("This reviewed answer must not call the model")

    corpus = Path(__file__).resolve().parents[2] / "data" / "corpus.json"
    service = ChatService(RetrievalStore(corpus, ""), NoModel(), 6, 12)
    monkeypatch.setattr(app.state, "chat", service, raising=False)
    response = TestClient(app).post("/api/chat", json={
        "message": "那从哪一天开始算？",
        "language": "zh-CN",
        "history": [{"role": "user", "content": "保单的冷静期是多少天？"}],
    })
    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] and body["language"] == "zh-CN"
    assert "通知书" in body["answer"] and "以较早者为准" in body["answer"]
    assert [(citation["id"], citation["page"]) for citation in body["citations"]] == [("S1", 15)]
