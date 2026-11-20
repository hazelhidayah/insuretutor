from pathlib import Path

import numpy as np

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
    )

    for query in unrelated:
        assert store.search(query, top_k=3)[0].score == 0.0

    store.mode = "hybrid"
    store._dense_scores = lambda query: np.ones(len(store.chunks), dtype=np.float32)  # type: ignore[method-assign]

    for query in unrelated:
        assert store.search(query, top_k=3)[0].score == 0.0


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
