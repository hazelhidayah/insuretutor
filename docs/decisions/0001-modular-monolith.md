# ADR 0001: Use a modular monolith

## Status

Accepted

## Context

The demo has one primary chat flow, one small source collection, and one evaluator-facing deployment. The model provider is configurable and may not expose an embeddings API.

## Decision

Build a modular monolith with a React frontend and FastAPI backend. Use a multi-stage Docker build so the API serves the compiled frontend. Keep chat orchestration, retrieval, provider integration, ingestion, and guardrails as explicit internal modules.

Generate embeddings locally. Do not require an external vector database, message broker, cache, or embeddings API for the take-home.

## Why

- One command starts the complete application.
- Fewer moving parts make evaluator setup and debugging easier.
- Internal boundaries keep the code readable and independently testable.
- Local retrieval satisfies provider portability.

## Consequences

- The application scales as one unit for now.
- The API image includes local retrieval dependencies and model weights.
- Ingestion/indexing, retrieval, model gateway, and conversation persistence can become separate services later if their scaling, ownership, or release requirements diverge.
