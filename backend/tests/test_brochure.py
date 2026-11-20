from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_brochure_endpoint_serves_original_pdf_inline() -> None:
    expected = Path(__file__).resolve().parents[2] / "data" / "FLEXI-ULife Prime Saver.pdf"
    response = TestClient(app).get("/api/brochure")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["content-disposition"].startswith("inline;")
    assert response.content.startswith(b"%PDF-")
    assert response.content == expected.read_bytes()
