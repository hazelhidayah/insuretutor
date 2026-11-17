# Development Log

This log records material implementation decisions. Commit history remains the detailed change record.

## 2026-11-17 - Establish product and architecture boundaries

**Why:** The take-home prioritises reasoning, structure, and ownership. Recording the constraints before implementation prevents accidental over-engineering.

**Where:** `PRODUCT.md`, `.env.example`, and `docs/decisions/0001-modular-monolith.md`.

**How:** Defined the public user, evidence-first product position, configurable provider boundary, local retrieval requirement, and modular-monolith deployment.

**Impact:** Subsequent implementation can be reviewed against explicit product and architecture decisions.

## 2026-11-17 - Add page-aware local retrieval and chat API

**Why:** The evaluator may provide a chat model without an embeddings API, while accurate citations require deterministic source metadata outside the model.

**Where:** `scripts/build_corpus.py` and `backend/app/`.

**How:** Added page-aware PDF ingestion, hybrid local retrieval with a lexical fallback, an OpenAI-compatible provider adapter, layered request guardrails, and post-generation citation-label validation.

**Impact:** Generation providers can be changed through environment variables without changing retrieval or citation behaviour.

## 2026-11-17 - Add the evidence-desk conversation interface

**Why:** Public users need to understand both the answer and where it came from without navigating raw retrieval output.

**Where:** `frontend/`, `Dockerfile`, and `docker-compose.yml`.

**How:** Built a responsive chat workspace that keeps cited source excerpts visible beside the conversation, includes explicit grounded and withheld states, and provides manual response-language selection.

**Impact:** The core chat, source inspection, multilingual selection, and failure states are accessible from a single Docker-served interface.
