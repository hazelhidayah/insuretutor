import json

import httpx
import pytest

from app.providers import ModelProviderError, OpenAICompatibleProvider
from app.settings import Settings


@pytest.mark.asyncio
@pytest.mark.parametrize("setting, expected", [("", {}), ("0", {"temperature": 0})])
async def test_temperature_is_only_sent_when_configured(monkeypatch, setting, expected):
    def handle(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content) == {
            "model": "test-model",
            "messages": [{"role": "user", "content": "你好"}],
            **expected,
        }
        return httpx.Response(200, json={"choices": [{"message": {"content": "答案"}}]})

    monkeypatch.setenv("MODEL_TEMPERATURE", setting)
    transport = httpx.MockTransport(handle)
    client = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: client(transport=transport, **kwargs))
    provider = OpenAICompatibleProvider(
        "https://provider.invalid/v1", "test-key", "test-model",
        temperature=Settings(_env_file=None).model_temperature,
    )
    assert await provider.complete([{"role": "user", "content": "你好"}]) == "答案"


@pytest.mark.parametrize(
    "payload",
    (
        {},
        {"choices": []},
        {"choices": [{"message": {}}]},
        {"choices": [{"message": {"content": None}}]},
        {"choices": [{"message": {"content": "   "}}]},
    ),
)
def test_rejects_malformed_or_empty_provider_content(payload: object) -> None:
    with pytest.raises(ModelProviderError):
        OpenAICompatibleProvider._extract_content(payload)


def test_extracts_valid_provider_content() -> None:
    payload = {"choices": [{"message": {"content": "  Supported answer [S1]  "}}]}

    assert OpenAICompatibleProvider._extract_content(payload) == "Supported answer [S1]"
