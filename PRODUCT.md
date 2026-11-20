# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Delegated: React with TypeScript for the browser interface and FastAPI for the API. A multi-stage Docker image builds the frontend and serves it with the API so the submitted demo remains a simple modular monolith.

## Users

Members of the public with no insurance background who are considering a specific insurance plan and need plain-language explanations grounded in approved plan material.

## Product Purpose

InsureTutor helps users understand insurance-plan documents through a bilingual conversation. Success means users can find accurate, comprehensible answers with inspectable page citations while the system refuses unsupported, out-of-scope, or personalised financial advice.

## Positioning

An evidence-first insurance tutor that turns every substantive answer into a path back to the supplied plan document, rather than presenting an opaque chatbot response.

## Operating Context

- Submitted as a public Git repository for an AIDF take-home assignment.
- Evaluated through Docker with an evaluator-provided OpenAI-compatible model endpoint.
- The model provider may not expose an embeddings API.
- The supplied reference is a bilingual English and Traditional Chinese product brochure.

## Capabilities and Constraints

- Conversational chat with retained context.
- Retrieval-augmented answers with accurate source citations.
- English and Simplified Chinese are the supported user-facing languages.
- Local retrieval must not depend on a hosted embeddings endpoint.
- Model base URL, model name, and API key must be configurable.
- Secrets must remain outside version control.
- Guardrails must keep answers safe, accurate, grounded, and within scope.
- The application must build and run with Docker and Docker Compose.

## Brand Commitments

- Product name: InsureTutor, matching the take-home brief.
- Voice: calm, plain-language, precise, non-promotional, and explicit about uncertainty.
- The interface must not imply that it replaces an insurer, adviser, policy contract, or suitability assessment.

## Evidence on Hand

- Assignment brief: `/Users/hazel/Downloads/TakeHomeTask-InsureTutor.pdf` (not part of the product corpus).
- Approved reference corpus: `data/FLEXI-ULife Prime Saver.pdf`.
- No testimonials, production usage claims, or performance benchmarks have been provided and none should be invented.

## Product Principles

1. Evidence before fluency.
2. Explain insurance language without erasing important conditions.
3. Abstain clearly when the brochure does not support an answer.
4. Make the source easy to inspect.
5. Keep the demo architecture proportional to the task.

## Accessibility & Inclusion

Use semantic HTML, keyboard-operable controls, visible focus states, sufficient colour contrast, responsive layouts, and language-aware copy. Avoid relying on colour alone to communicate confidence or warnings.
