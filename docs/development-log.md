# Development Log

This is the human-readable record of every material project change. Commit history remains the exact file-level record.

## Logging rule

Before committing a material change, append an entry containing:

- **Why** - the problem, requirement, or evidence that motivated the change.
- **Where** - the files or components affected.
- **How** - the implementation approach and important trade-offs.
- **Impact** - the resulting user, engineering, deployment, or risk effect.
- **Verification** - how the result was checked.

Do not create entries for read-only inspection or inconsequential formatting. Record corrections and failed approaches when they explain an important design decision.

---

## 2026-11-17 - Analyse the assignment and reference material

**Why:** Implementation needed to begin from the evaluator's actual requirements and insurance business context rather than from a preferred technology stack.

**Where:** `TakeHomeTask-InsureTutor.pdf` and `FLEXI-ULife Prime Saver.pdf` during project analysis; no assignment instructions were copied into the runtime application.

**How:** Separated the assignment brief from the insurance corpus, reviewed all required capabilities and deliverables, and inspected the brochure's bilingual structure, conditions, footnotes, rates, fees, and disclosures.

**Impact:** Established chat, cited RAG, guardrails, bilingual behaviour, Docker portability, configurable model access, and documentation as the core evaluation targets.

**Verification:** Compared the extracted text with rendered pages from both PDFs.

## 2026-11-17 - Establish product and architecture boundaries

**Why:** The take-home prioritises reasoning, structure, and ownership. Recording constraints before implementation reduces accidental over-engineering.

**Where:** `PRODUCT.md`, `.env.example`, `.gitignore`, and `docs/decisions/0001-modular-monolith.md`.

**How:** Defined the public user, evidence-first position, provider boundary, local retrieval requirement, accessibility expectations, and modular-monolith deployment. Explicitly documented when future service extraction would become justified.

**Impact:** Subsequent implementation can be reviewed against durable product and architecture decisions instead of undocumented assumptions.

**Verification:** Confirmed the product record covers every requirement in the assignment brief.

## 2026-11-17 - Add the approved insurance source

**Why:** The demo must answer from the reference material attached to the assignment.

**Where:** `data/FLEXI-ULife Prime Saver.pdf`.

**How:** Added the supplied brochure as the only approved retrieval corpus. The assignment PDF was deliberately excluded because it describes how to build the product, not insurance facts users should receive.

**Impact:** The knowledge boundary is explicit and reproducible for evaluators.

**Verification:** Confirmed the stored brochure matches the 20-page supplied PDF.

## 2026-11-17 - Create the initial meaningful commit

**Why:** The assignment specifically requests incremental commits with meaningful messages.

**Where:** Git commit `e72e2ff` (`docs: define InsureTutor product and architecture`).

**How:** Grouped the product record, environment contract, source material, architecture decision, and initial development log into a coherent foundation commit.

**Impact:** The repository history begins with the rationale and constraints that govern later code.

**Verification:** Reviewed the commit contents and confirmed the working tree was clean afterward.

## 2026-11-17 - Build deterministic page-aware ingestion

**Why:** Accurate citations require page metadata to remain outside the language model, and brochure extraction must be reproducible.

**Where:** `scripts/build_corpus.py` and `data/corpus.json`.

**How:** Extracted text page by page, cleaned layout artefacts, split it into bounded overlapping chunks, and assigned stable source, page, section, and chunk identifiers.

**Impact:** Retrieval and UI citations can link answers to real brochure pages without allowing the model to invent page numbers.

**Verification:** Generated 44 chunks covering all 20 brochure pages.

## 2026-11-17 - Add local multilingual hybrid retrieval

**Why:** The evaluator's OpenAI-compatible provider may not expose an embeddings API, while English and Chinese questions still need to retrieve the same bilingual evidence.

**Where:** `backend/app/retrieval/store.py`, `backend/app/settings.py`, `backend/requirements.txt`, and `.env.example`.

**How:** Combined local multilingual dense embeddings with token and character-trigram lexical scoring. Added a lexical-only fallback for offline or model-loading failures.

**Impact:** Retrieval remains provider-independent and supports cross-language and cross-script matching without an external vector database.

**Verification:** Confirmed the guaranteed-interest query retrieves chunks containing the documented 2.5% value; the running application reported `retrieval_mode: hybrid`.

## 2026-11-17 - Add the configurable model provider

**Why:** AIDF will evaluate the demo using an OpenAI-compatible provider of its choice.

**Where:** `backend/app/providers/openai_compatible.py`, `backend/app/settings.py`, `.env.example`, and `backend/app/chat.py`.

**How:** Isolated model access behind a provider adapter with configurable base URL, API key, and model name. Kept retrieval independent from generation.

**Impact:** Evaluators can change the generation provider without modifying application code or retrieval behaviour.

**Verification:** Verified that an unconfigured provider produces a controlled, visible error instead of a server failure.

## 2026-11-17 - Add layered guardrails and citation validation

**Why:** Insurance information is consequential, and the assignment explicitly evaluates behaviour under misuse.

**Where:** `backend/app/guardrails.py`, `backend/app/chat.py`, `backend/app/models.py`, and `backend/tests/test_guardrails.py`.

**How:** Added English and Chinese prompt-injection detection, retrieval-confidence gating, advice boundaries, guaranteed-versus-assumed-value instructions, history and input limits, request-local source labels, and post-generation label validation.

**Impact:** Unsupported, manipulative, or uncited answers can be blocked or withheld before reaching the user.

**Verification:** Confirmed a prompt-injection request was blocked before model access and unit-tested valid, missing, and invented source labels.

## 2026-11-17 - Add the FastAPI application boundary

**Why:** The frontend needed a small, typed interface for chat and operational health checks.

**Where:** `backend/app/main.py`, `backend/app/models.py`, and related application modules.

**How:** Added `/api/chat` and `/api/health`, application-lifespan initialisation, CORS for local development, and production static-file serving.

**Impact:** One backend process now owns retrieval, guardrails, provider access, citations, and the compiled frontend.

**Verification:** Called the health endpoint and received 44 corpus chunks, hybrid retrieval status, and model-configuration status.

## 2026-11-17 - Add the retrieval and guardrail evaluation baseline

**Why:** The project needs repeatable evidence beyond manual demonstration.

**Where:** `backend/tests/`, `docs/evaluation.md`, and `backend/requirements-dev.txt`.

**How:** Added deterministic unit tests and a planned multilingual evaluation matrix for retrieval, grounding, abstention, language adherence, and adversarial behaviour.

**Impact:** The project has a testable quality baseline and a clear next step toward broader evaluation.

**Verification:** Ran the backend suite in the built container: 3 tests passed.

## 2026-11-17 - Build the evidence-desk conversation interface

**Why:** Public users need to understand both the answer and where it came from without reading raw retrieval output.

**Where:** `frontend/src/App.tsx`, `frontend/src/styles.css`, `frontend/src/main.tsx`, and frontend configuration files.

**How:** Built a responsive chat workspace with source excerpts beside the conversation, clickable citation markers, grounded and withheld states, response-language selection, example questions, loading and error states, keyboard submission, and an explicit educational-use notice.

**Impact:** Chat, source inspection, multilingual selection, and failure recovery are available in one coherent interface.

**Verification:** Inspected the application at 1440px desktop and 390px mobile widths and exercised the unconfigured-provider state.

## 2026-11-17 - Add a reproducible Docker deployment

**Why:** Docker execution is a required deliverable, and evaluator setup should be one command.

**Where:** `Dockerfile`, `docker-compose.yml`, and `.dockerignore`.

**How:** Added a multi-stage build that compiles React with Node and serves it from the FastAPI image. Added environment forwarding and a persistent local-model cache volume.

**Impact:** `docker compose up --build` starts the complete modular monolith without requiring Node or Python on the evaluator's host.

**Verification:** Built the production image and started it locally on port 8000.

## 2026-11-17 - Correct the frontend TypeScript build configuration

**Why:** The first Docker build exposed an invalid TypeScript option combination in `tsconfig.node.json`.

**Where:** `frontend/tsconfig.node.json`.

**How:** Replaced the incompatible `allowImportingTsExtensions` setting with `noEmit` for the referenced Node configuration.

**Impact:** The production frontend compilation completes successfully instead of failing before image creation.

**Verification:** Re-ran `npm run build` through Docker; TypeScript and Vite completed successfully.

## 2026-11-17 - Replace the heavyweight embedding runtime

**Why:** The initial sentence-transformer dependency began pulling a large GPU/CUDA stack, which was disproportionate for a CPU-only take-home demo.

**Where:** `backend/requirements.txt`, `backend/app/retrieval/store.py`, settings, Docker configuration, README, and `.env.example`.

**How:** Replaced the PyTorch-based runtime with FastEmbed and the ONNX-based multilingual MiniLM model. Redirected the model cache into the persistent Docker volume.

**Impact:** The image is smaller, CPU-focused, and faster to build while retaining local multilingual dense retrieval.

**Verification:** Rebuilt the image and confirmed the application initialised in hybrid retrieval mode.

## 2026-11-17 - Improve interface typography after automated review

**Why:** An interface-quality scan flagged Inter as an overused default that weakened the product's visual character.

**Where:** `frontend/package.json`, `frontend/src/main.tsx`, and `frontend/src/styles.css`.

**How:** Replaced Inter with self-hosted IBM Plex Sans while retaining Source Serif 4 for evidence-oriented editorial hierarchy.

**Impact:** The interface remains readable and self-contained while gaining a more deliberate, less generic voice.

**Verification:** Rebuilt the production frontend successfully with the new bundled font assets.

## 2026-11-17 - Lock frontend dependencies

**Why:** Evaluators should receive reproducible dependency resolution rather than whatever package versions are current on build day.

**Where:** `frontend/package-lock.json` and `Dockerfile`.

**How:** Generated the lockfile and changed the Docker build from `npm install` to `npm ci`.

**Impact:** Frontend installations are deterministic and fail clearly if the manifest and lockfile diverge.

**Verification:** Rebuilt the complete Docker image using `npm ci`; the build passed.

## 2026-11-18 - Document setup, architecture, examples, and limitations

**Why:** Clear documentation is a scored deliverable and will also support the follow-up presentation.

**Where:** `README.md`, `docs/evaluation.md`, and this development log.

**How:** Documented Docker setup, architecture, retrieval and citations, guardrails, provider variables, local development, representative conversations, known limitations, and evaluation dimensions.

**Impact:** Reviewers can run the demo, understand its decisions, and see both strengths and honest limitations without reverse-engineering the code.

**Verification:** Checked all referenced paths and commands against the implemented repository structure.

## 2026-11-18 - Create the backend feature commit

**Why:** Retrieval, generation boundaries, guardrails, tests, and ingestion form one reviewable backend capability.

**Where:** Git commit `38bc457` (`feat: add page-aware retrieval and guarded chat API`).

**How:** Grouped all backend and corpus-generation work into one feature commit separate from the interface and deployment layer.

**Impact:** Reviewers can inspect the evidence and safety pipeline independently from presentation concerns.

**Verification:** Audited the commit's 18 files and confirmed its subject accurately describes its scope.

## 2026-11-18 - Create the interface and Docker feature commit

**Why:** The user-facing workspace and evaluator-facing runtime together complete the first vertical slice.

**Where:** Git commit `477d316` (`feat: add evidence-focused chat interface and Docker runtime`).

**How:** Grouped the React interface, Docker runtime, dependency lock, README, and development-log updates into a second feature commit.

**Impact:** The repository history progresses from product decisions, to backend capability, to a runnable full-stack demo.

**Verification:** Audited the commit's 15 files, built the image, ran tests, and inspected desktop and mobile layouts.

## 2026-11-18 - Publish and verify the public GitHub repository

**Why:** Submission requires a publicly accessible Git repository.

**Where:** `https://github.com/hazelhidayah/insuretutor` and local Git remote `origin`.

**How:** Created a public repository, pushed `main`, configured upstream tracking, and checked the remote contents and visibility.

**Impact:** The project is accessible for AIDF review and ready to include in the submission email.

**Verification:** Confirmed public visibility, the `main` default branch, remote commit `477d316`, a clean local working tree, and that `.env` was not published while `.env.example` was included.

## 2026-11-18 - Expand the implementation development log

**Why:** The original log recorded only broad milestones and did not expose enough of the reasoning, corrections, and verification behind individual material changes.

**Where:** `docs/development-log.md`.

**How:** Reconstructed the chronological implementation record from the assignment analysis, Git history, build output, tests, responsive review, and GitHub publication checks. Added a durable logging rule and verification field for future contributors and coding agents.

**Impact:** Reviewers can trace not only what was built, but why each decision was made, where it was implemented, how it works, and what it changed.

**Verification:** Cross-checked every entry against the current repository, the three existing commits, and completed validation results.
