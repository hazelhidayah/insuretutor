from pathlib import Path

from app.retrieval import RetrievalStore


def test_retrieves_with_lexical_fallback() -> None:
    root = Path(__file__).resolve().parents[2]
    store = RetrievalStore(root / "data" / "corpus.json", "")

    results = store.search("What is the guaranteed interest rate?", top_k=3)

    assert results
    assert any("2.5%" in result.text for result in results)
