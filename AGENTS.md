# InsureTutor Agent Instructions

## Start here

- Read `PRODUCT.md`, `README.md`, `docs/decisions/0001-modular-monolith.md`, `docs/evaluation.md`, and `docs/ai-development-workflow.md` before material work.
- Treat the take-home brief as build requirements and `data/FLEXI-ULife Prime Saver.pdf` as the insurance knowledge source. Never ingest assignment instructions into the user-facing corpus.
- Preserve the modular-monolith scope unless measured scaling, ownership, release, or failure-isolation needs justify another service.

## Safety and source grounding

- Insurance answers must be supported by the supplied brochure and structured citations.
- Distinguish guaranteed values from assumed or non-guaranteed values and retain important conditions.
- Do not add personalised suitability, investment, legal, tax, underwriting, or purchase advice.
- A valid citation label proves only that the source was retrieved; it does not prove semantic entailment. State verification limits honestly.
- Keep `.env`, API keys, provider responses containing secrets, and other credentials out of Git, prompts, logs, and test artifacts.

## Development workflow

- Inspect and reproduce before editing. Prefer a small verified change over speculative architecture.
- Development subagents are not runtime product features. Use them only when explicitly authorised, with disjoint roles such as read-only exploration, high-effort planning, bounded implementation, and independent review.
- Match reasoning effort to task risk. Record only model names and settings actually exposed by the environment; never claim Sonnet, Opus, or another unavailable model.
- The coordinator must review every agent-produced diff and owns final integration and verification.
- Postman CLI is installed and may be used for API-engineering checks when useful.

## Required change log

- Before requesting approval for a material change, append to `docs/development-log.md`.
- Every entry must include **Why**, **Where**, **How**, **Impact**, and **Verification**.
- Add **AI assistance** when agents materially influenced implementation or review.
- Record failed approaches when they explain an important decision; do not log read-only inspection or inconsequential formatting.

## Verification

- Run backend tests: `PYTHONPATH=backend pytest backend/tests -q` inside the project environment.
- Run offline evaluation: `PYTHONPATH=backend python -m app.evaluation`.
- Run live evaluation only with an intentionally configured provider: `PYTHONPATH=backend python -m app.evaluation --live`.
- Build and smoke-test the production path with `docker compose up -d --build`.
- Clearly separate mocked, lexical-only, hybrid, and genuine-provider results. Never present an unrun check as passed.

## Git and external actions

- Never commit, amend, push, create a pull request, deploy, or rewrite history without the user's explicit approval for that action.
- Preserve unrelated user changes and keep the working tree reviewable.
- Before proposing a commit, run `git diff --check`, inspect `git status`, and confirm `.env` is ignored.
