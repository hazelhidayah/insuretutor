from __future__ import annotations

import json
import re
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "FLEXI-ULife Prime Saver.pdf"
OUTPUT = ROOT / "data" / "corpus.json"
SOURCE_NAME = "FLEXI-ULife Prime Saver"
MAX_CHARS = 1_100
OVERLAP_PARAGRAPHS = 1


def clean_text(text: str) -> str:
    text = text.replace("\u0000", " ").replace("\ufffd", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_page(text: str) -> list[str]:
    paragraphs = [part.strip() for part in re.split(r"\n(?=\S)", text) if part.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for paragraph in paragraphs:
        if current and current_length + len(paragraph) > MAX_CHARS:
            chunks.append("\n".join(current))
            current = current[-OVERLAP_PARAGRAPHS:]
            current_length = sum(len(item) for item in current)
        current.append(paragraph)
        current_length += len(paragraph)
    if current:
        chunks.append("\n".join(current))
    return chunks


def section_name(text: str, page: int) -> str:
    first_lines = [line.strip() for line in text.splitlines()[:5] if line.strip()]
    heading = " / ".join(first_lines[:2])
    return heading[:120] or f"Page {page}"


def main() -> None:
    chunks = []
    with pdfplumber.open(SOURCE) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            text = clean_text(page.extract_text(x_tolerance=2, y_tolerance=3) or "")
            for chunk_number, chunk_text in enumerate(split_page(text), 1):
                chunks.append(
                    {
                        "id": f"prime-saver-p{page_number}-c{chunk_number}",
                        "source": SOURCE_NAME,
                        "page": page_number,
                        "section": section_name(text, page_number),
                        "visibility": "public",
                        "text": chunk_text,
                    }
                )
    OUTPUT.write_text(
        json.dumps({"version": 1, "chunks": chunks}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {len(chunks)} chunks to {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

