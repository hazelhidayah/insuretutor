from pathlib import Path

import numpy as np
import pytest

from app.retrieval import RetrievalStore


def test_retrieves_with_lexical_fallback() -> None:
    root = Path(__file__).resolve().parents[2]
    store = RetrievalStore(root / "data" / "corpus.json", "")

    results = store.search("What is the guaranteed interest rate?", top_k=3)

    assert results
    assert any("2.5%" in result.text for result in results)


def test_unrelated_queries_are_zero_confidence_in_lexical_and_hybrid_modes() -> None:
    root = Path(__file__).resolve().parents[2]
    store = RetrievalStore(root / "data" / "corpus.json", "")
    unrelated = (
        "What is the weather today?",
        "How do I make pancakes?",
        "What is the insurer's current 2026 credit rating?",
        "今天天气怎么样？",
        "怎樣製作班戟？",
        "What is today's date?",
        "Can you help me?",
        "How much time do I have to get there?",
    )

    for query in unrelated:
        assert store.search(query, top_k=3)[0].score == 0.0

    store.mode = "hybrid"
    store._dense_scores = lambda _query: np.ones(len(store.chunks), dtype=np.float32)
    for query in unrelated:
        assert store.search(query, top_k=3)[0].score == 0.0


@pytest.mark.parametrize(("question", "page"), [
    ("Can I stop paying premiums temporarily?", 10),
    ("Can I pause premium payments?", 10),
    ("How much time do I have to cancel my policy?", 15),
    ("When can I withdraw money?", 10),
    ("我可以暂停交保费吗？", 10),
    ("我能定期取钱吗？", 12),
])
def test_policy_paraphrases_retain_relevant_evidence(question, page):
    root = Path(__file__).resolve().parents[2]
    store = RetrievalStore(root / "data" / "corpus.json", "")
    assert any(c.page == page and c.score >= 0.08 for c in store.search(question))

    store.mode = "hybrid"
    store._dense_scores = lambda _query: np.full(len(store.chunks), 0.6, dtype=np.float32)
    assert any(c.page == page and c.score >= 0.08 for c in store.search(question))

def test_supported_chinese_query_retains_evidence() -> None:
    root = Path(__file__).resolve().parents[2]
    store = RetrievalStore(root / "data" / "corpus.json", "")

    results = store.search("定期提款有什么条件？", top_k=6)

    assert results[0].score > 0.0
    assert any(result.page == 12 for result in results)


def test_simplified_chinese_matches_traditional_source_evidence() -> None:
    root = Path(__file__).resolve().parents[2]
    store = RetrievalStore(root / "data" / "corpus.json", "")

    results = store.search("保单的冷静期是多少天？", top_k=6)

    assert results[0].score > 0.0
    assert any(result.page in {15, 16} and result.score > 0.0 for result in results)


def test_chinese_lead_in_and_emoji_do_not_hide_supported_terms() -> None:
    root = Path(__file__).resolve().parents[2]
    store = RetrievalStore(root / "data" / "corpus.json", "")

    results = store.search("我想知道💡「定期提款」有什麼條件？", top_k=6)

    assert results[0].score > 0.0
    assert any(result.page in {6, 10} and result.score > 0.0 for result in results)
