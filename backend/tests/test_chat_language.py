import pytest

from app.chat import response_language
from app.models import ChatRequest


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("保单的冷静期是多少天？", "zh-CN"),
        ("保單的冷靜期是多少天？", "zh-TW"),
        ("请 explain 4% 派息率是否保证？", "zh-CN"),
        ("我想知道💡「定期提款」有什麼條件？", "zh-TW"),
        ("What is the cooling-off period?", "en"),
    ],
)
def test_auto_language_detection(message: str, expected: str) -> None:
    assert response_language(ChatRequest(message=message, language="auto")) == expected


@pytest.mark.parametrize("language", ["en", "zh-CN", "zh-TW"])
def test_explicit_language_overrides_detection(language: str) -> None:
    request = ChatRequest(message="保單的冷靜期是多少天？", language=language)

    assert response_language(request) == language
