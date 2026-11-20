# AI-Assisted Development Workflow

This document describes how AI agents are used to build and review InsureTutor. It is a development workflow, not part of the deployed product architecture. The running application remains a modular monolith with one retrieval-and-generation pipeline.

## Why use task-specific agents

Different engineering tasks benefit from different levels of reasoning and independence:

- Exploration should be fast and evidence-seeking. Its job is to inspect the repository, reproduce failures, and surface risks without changing files.
- Planning should spend more reasoning effort on requirements, acceptance criteria, sequencing, and trade-offs before implementation begins.
- Implementation should receive a bounded scope and concrete acceptance criteria, then edit and test only that scope.
- Integration and review should remain independent from the implementation pass. The coordinator owns the final diff, verification, and decision to keep or reject generated work.

Using a more capable or higher-reasoning model does not prove correctness. Correctness comes from source review, deterministic tests, measured evaluation, and human ownership. Lower-effort models can be faster and less expensive for routine work; higher effort is reserved for ambiguity, safety boundaries, architecture, or difficult failure analysis.

## Model and effort routing used on 18 November 2026

The originally suggested Sonnet and Opus models were not available in this workspace. They were not claimed or simulated. The following available configurations were used instead:

- **Exploration agent:** `gpt-6.1-sol`, medium reasoning. Read-only repository inspection, current-test execution, configuration-status checks, and failure reproduction. It identified that per-query lexical score normalisation allowed unrelated questions to pass the evidence gate.
- **Planning agent:** `gpt-6-astra`, high reasoning. Read-only evaluation design, acceptance criteria, risk prioritisation, and honest documentation guidance. It separated mocked pipeline evidence from genuine provider evidence and identified multi-turn, localisation, citation-support, and pending-request risks.
- **Implementation agent:** `gpt-6.1-terra`, high reasoning. Implemented the first offline/live evaluation harness and regression fixtures without committing or pushing.
- **Coordinator:** primary Codex agent; the exact underlying model identifier is not exposed here and is therefore recorded as unavailable. It reviewed the agent outputs, changed the relevance check so it also applies to hybrid and Chinese paths, expanded regression coverage, and owns final verification.

All three subagents were explicitly authorised for this work. Their scopes were separated: exploration and planning were read-only, while implementation owned the evaluation slice. No subagent committed or pushed changes.

## Workflow

1. **Frame the task.** Translate the request into bounded deliverables, constraints, and acceptance criteria.
2. **Explore read-only.** Reproduce current behaviour and collect evidence before proposing a fix.
3. **Plan at higher effort.** Identify critical risks, alternatives, and what must be measured.
4. **Implement within a narrow boundary.** Edit only assigned files and run relevant tests.
5. **Integrate independently.** Review every diff, challenge unsupported claims, and adjust implementation where evidence requires it.
6. **Verify proportionately.** Run unit tests, the offline evaluation suite, Docker checks, and—when credentials are configured—a live-provider and browser evaluation.
7. **Log material changes.** Record Why, Where, How, Impact, Verification, and relevant AI assistance.
8. **Commit only after human approval.** The repository owner decides whether the reviewed working tree is committed or discarded.

## Evidence and honesty rules

- Record only model names and reasoning settings that the environment actually exposes.
- Do not describe development subagents as runtime product features.
- Do not present mocked provider responses as genuine generation quality.
- Do not upgrade “citation label is valid” into “claim is factually supported.”
- Mark unrun checks, unavailable credentials, and known limitations explicitly.
- Keep API keys outside prompts, logs, evaluation output, and version control.

## Development-log format

For work where AI assistance materially influenced implementation or review, add:

```text
AI assistance: role, actual model/configuration when observable, assigned scope,
review performed, and the human/coordinator decision.
```

The other required fields remain Why, Where, How, Impact, and Verification.
