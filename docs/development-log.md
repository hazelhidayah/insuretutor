# Development Log

## Keep source evidence visible in long conversations

**Why:** The source panel stretched to the full conversation height, leaving its links above the visible area after several answers.

**Where:** Chat citation selection and source panel layout.

**How:** Pin the desktop panel inside the evidence column and scroll long citation lists independently. Scope each selection to its answer because citation labels can repeat. On narrow screens, bring the panel into view when a citation is selected.

**Impact:** Readers can inspect the current or an older answer's sources while browsing the conversation. Replies without citations show an explicit empty state.

**Verification:** Docker build and 72 backend tests passed. Browser checks confirmed a visible desktop panel after four replies, correct page selection when clicking an older citation, and visible, focused evidence on mobile.

## Separate unrelated requests from valid policy paraphrases

**Why:** Generic word overlap let clock and date queries retrieve brochure passages, while valid questions about pausing payments or withdrawing money could lose relevant evidence.

**Where:** Retrieval, chat abstention, reviewed clauses, and regression tests.

**How:** Ignore generic date and time terms in the English evidence check, map a few common policy paraphrases to brochure terminology, and rank passages after checking relevance. Treat the model's insufficient-evidence marker as an uncited refusal. Extend source-verified answers for observed withdrawal and cancellation paraphrases and for premium-pause conditions.

**Impact:** Unsupported questions can stop without citations. The tested English and Chinese policy examples preserve their conditions and source links.

**Verification:** 72 backend tests and 25 offline evaluation cases passed. The rebuilt Docker app in hybrid mode declined clock, date, and directions queries and returned the expected cited answers for four policy questions.

**AI assistance:** The primary Codex agent implemented and checked the changes.

## 2026-11-22 - Reject current-time questions before retrieval

**Why:** A live clock question matched incidental uses of “time” in the brochure and produced a slow refusal with irrelevant citations.

**Where:** Input guardrails, guardrail tests, and evaluation cases.

**How:** Recognise common English and Chinese clock questions before retrieval. Test that neither retrieval nor generation runs and that policy-timing questions remain outside this rule.

**Impact:** Matched clock questions receive an uncited refusal without paying for retrieval or inference.

**Verification:** 64 backend tests and 22 offline evaluation cases passed.

## 2026-11-22 - Round out tests and explain the design choices

**Why:** The existing tests covered the core pipeline. The HTTP boundary, mixed-quality retrieval and reviewer outages needed direct coverage, and the README needed to explain why the design fits the demo.

**Where:** Backend API and guardrail tests, evaluation cases, README, evaluation guide and architecture decision.

**How:** Exercise request validation, reviewed follow-up citations, exclusion of unsafe neighbouring passages, percentage evidence, reviewer failure, and bilingual refusals. Serve the UI at the explicit homepage route and compiled assets through the existing static mount so arbitrary URL paths no longer enter file lookup. Document provider, retrieval, Docker and safety trade-offs in practical language.

**Impact:** Reviewers have clearer setup and decision notes, and tests cover failure paths alongside the happy path.

**Verification:** 59 backend tests and 21 offline cases passed. The Docker smoke test checked the homepage, JavaScript asset, original PDF, unknown-route 404 and reviewed Chinese response. The full live model suite was not rerun.

**AI assistance:** The primary Codex agent implemented the changes and verified them.

## 2026-11-22 - Verify the take-home walkthrough and preserve brochure conditions

**Why:** Live answers previously misstated the cooling-off trigger and omitted separate monthly and annual withdrawal terms.

**Where:** Reviewed-answer module, public passage lookup, chat orchestration, citation checks, evaluation fixtures, and README.

**How:** Read the original PDF pages side by side with live answers. Keep two reviewed clauses in one module with a narrow question match and check the page and source hashes before answering. Keep ordinary questions on the RAG path. Extend the architecture test to prevent the reviewed-answer module from depending on the API, model provider, or chat service. Treat citation lookalikes such as `[SI]` as invalid.

**Impact:** The tested deadline and withdrawal questions preserve their material conditions in both reply languages. A stale source fails closed. Model-generated replies still require claim-level review.

**Verification:** 50 backend tests and all 17 offline evaluation cases passed. The Docker browser walkthrough exercised English generation, Chinese withdrawals, language switching, a Chinese cooling-off follow-up, PDF links, and out-of-scope and personal-advice refusals.

**AI assistance:** The primary Codex agent checked the source pages, implemented the changes, and ran the walkthrough.

## Add layered guardrails for public brochure chat

**Why:** Live review showed that valid source labels alone could accompany unsupported claims.

**Where:** Guardrail package, chat service, corpus ingestion and index, API validation, provider settings, and tests.

**How:** Mask recognised sensitive inputs, enforce public document metadata before indexing, scan and threshold each selected passage, and reject unsafe output or percentages absent from cited evidence. Add an opt-in model review with a strict pass verdict and log decision categories.

**Impact:** Restricted passages and several risky outputs are withheld. Authenticated tenant access and reliable semantic verification remain separate concerns.

**Verification:** 46 backend tests and all 17 offline evaluation cases passed. The second model call was tested with scripted verdicts.

**AI assistance:** The primary Codex agent audited, implemented, and verified the changes.

## Check Chinese deadline and withdrawal answers

**Why:** Live answers misread the cooling-off start date and omitted or conflated withdrawal terms.

**Where:** Chat retrieval and prompt, evaluation runner, and multilingual fixtures.

**How:** Retry short referential Chinese follow-ups against the previous user topic when standalone retrieval fails. Tell the model to separate deadlines from trigger events and list conditions per option. Add answer-pattern checks for the cooling-off duration and triggers and for both withdrawal terms.

**Impact:** The tested follow-up now finds brochure evidence. Pattern checks detect missing terms but cannot establish that an answer is factually correct.

**Verification:** 36 backend tests and 17 offline cases passed. In live hybrid testing, the local model still misstated the cooling-off start and omitted withdrawal terms. These remain open quality issues.

**AI assistance:** The primary Codex agent implemented and evaluated the changes.

This is the human-readable record of every material project change. Commit history remains the exact file-level record.

## Logging rule

Before committing a material change, append an entry containing:

- **Why** - the problem, requirement, or evidence that motivated the change.
- **Where** - the files or components affected.
- **How** - the implementation approach and important trade-offs.
- **Impact** - the resulting user, engineering, deployment, or risk effect.
- **Verification** - how the result was checked.
- **AI assistance** - when materially relevant, the actual agent role, observable model/reasoning configuration, assigned scope, and coordinator review.

Do not create entries for read-only inspection or inconsequential formatting. Record corrections and failed approaches when they explain an important design decision.

---

## 2026-11-18 - Correct automatic Chinese script detection

**Why:** End-to-end Chinese input checks showed that a clearly Simplified Chinese insurance question was incorrectly routed to Traditional Chinese because the heuristic treated the shared character `保` as Traditional-only.

**Where:** `backend/app/chat.py`, `backend/app/retrieval/store.py`, `backend/tests/test_chat_language.py`, and `backend/tests/test_retrieval.py`.

**How:** Replaced the one-sided marker check with matched Simplified/Traditional character sets, selected the script with stronger evidence, retained Simplified Chinese as the neutral fallback for ambiguous Han text, and passed the resolved language to the model prompt. Normalised a bounded set of script variants before the conservative evidence check and removed common question lead-ins so punctuation and emoji cannot dilute relevant terms. Added regression cases covering Simplified, Traditional, mixed English/Chinese, punctuation, emoji, English, and explicit language overrides.

**Impact:** Automatic language selection no longer routes ordinary Simplified Chinese insurance questions to Traditional Chinese, while explicit user selection remains authoritative. Supported Simplified questions can match the brochure's Traditional Chinese evidence without weakening rejection of unrelated queries. Unicode input and output behaviour is unchanged.

**Verification:** Ran the language regression tests, the complete backend suite, and live API checks against the configured local model; then entered a Traditional Chinese question through the browser interface.

**AI assistance:** The primary implementation agent designed and applied the correction after an end-to-end test matrix exposed the defect; no subagent authored this change.

## 2026-11-18 - Add grounded answer translation controls

**Why:** Users should be able to read an existing answer in English, Simplified Chinese, or Traditional Chinese without retyping the original question.

**Where:** `frontend/src/App.tsx`, `frontend/src/styles.css`, and `README.md`.

**How:** Added an accessible per-answer language switcher. The first selection regenerates the answer from the same original question, conversation context, and brochure pipeline in the requested language; citation validation and guardrails therefore still apply. Successful language variants are cached in browser state so subsequent switches are immediate. Added loading, disabled, error, active-language, cancellation, and responsive states.

**Impact:** A user can move between English, Simplified Chinese, and Traditional Chinese versions of an answer while retaining inspectable source citations. The control does not present an unverified client-side or literal machine translation as grounded evidence.

**Verification:** The production Docker build completed, the interface-quality detector returned no findings, and a live browser flow generated an English cited answer, regenerated it in Simplified Chinese with citations, and switched back to the cached English version immediately. The complete backend suite remained green. The direct host build could not start because the local Homebrew Node binary is missing `libsimdjson.33.dylib`; Docker's pinned Node build verified the production frontend instead.

**AI assistance:** The primary implementation agent designed, implemented, and visually reviewed the control; no subagent authored this change.

## 2026-11-18 - Narrow the interface to English and Simplified Chinese

**Why:** The product owner confirmed that Traditional Chinese is not needed in the user-facing chatbot.

**Where:** `frontend/src/App.tsx`, `README.md`, and `PRODUCT.md`.

**How:** Removed Traditional Chinese from the reply selector and per-answer translation controls, changed the Chinese starter question and interface copy to Simplified Chinese, and retained the backend-compatible language type to avoid an unnecessary API migration.

**Impact:** Users now see a simpler bilingual experience with only English and Simplified Chinese choices. Existing backend compatibility is preserved but no Traditional Chinese option is advertised or selectable in the interface.

**Verification:** Rebuilt the production Docker image, reran the interface-quality detector, and checked the refreshed browser controls and bilingual translation flow.

**AI assistance:** The primary implementation agent applied and reviewed this scoped interface simplification; no subagent authored the change.

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

## 2026-11-18 - Add task-specific agent workflow and evaluation harness

**Why:** The next milestone required stronger evaluation evidence and the user explicitly requested development subagents with reasoning effort matched to task complexity.

**Where:** `backend/app/evaluation.py`, `backend/app/eval_data/cases.json`, `backend/tests/test_evaluation.py`, `backend/app/retrieval/store.py`, `docs/evaluation.md`, `docs/ai-development-workflow.md`, and `README.md`.

**How:** Used separate read-only exploration and planning agents plus a bounded implementation agent. Added an offline evaluation runner with scripted provider responses, an opt-in live-provider path, multilingual and adversarial fixtures, citation and language checks, and regression cases for unrelated questions. Replaced reliance on relative retrieval score alone with conservative English-term and Chinese-bigram evidence coverage applied to lexical and hybrid results. Localised guardrail and provider-failure responses, inspected history for injection attempts, bounded submitted history, rejected malformed provider payloads, and cancelled in-flight browser requests when starting a new conversation.

**Impact:** The project can now exercise the real chat orchestration without a paid provider, explicitly distinguishes mocked from live evidence, blocks the reproduced credit-rating, recipe, and weather false positives more conservatively, and handles several failure paths without leaking upstream details or contaminating a reset conversation. Valid paraphrases can now be rejected, so broader multilingual calibration remains necessary.

**Verification:** The complete backend suite passed 15 tests and the offline evaluation passed 15/15 cases. A rebuilt hybrid Docker service rejected five unrelated English/Chinese questions while four supported English/Chinese questions reached the provider boundary. No genuine provider generation was run because `.env` is absent.

**AI assistance:** Exploration used `gpt-6.1-sol` at medium reasoning; planning used `gpt-6-astra` at high reasoning; implementation used `gpt-6.1-terra` at high reasoning. The primary coordinator reviewed and amended the implementation. No agent committed or pushed changes.

## 2026-11-18 - Configure and evaluate a local generation provider

**Why:** Retrieval and mocked orchestration were verified, but genuine answer generation remained untested because no provider was configured.

**Where:** Ignored local `.env`, `backend/app/chat.py`, `backend/app/providers/openai_compatible.py`, `docs/evaluation.md`, and `README.md`.

**How:** Configured Docker to reach the existing host Ollama OpenAI-compatible endpoint at `host.docker.internal` using `qwen2.5:7b`. Set generation temperature to zero, repeated the allowed citation labels immediately before the source excerpts, and added one bounded repair attempt when the first answer contains missing or unknown labels. The second response is still validated and withheld if invalid.

**Impact:** The application can now generate real local English and Chinese answers without a hosted API key. Intermittent citation-label mistakes are corrected once without relaxing validation or silently accepting unsupported labels.

**Verification:** Docker reported hybrid retrieval, 44 chunks, and a configured provider. Backend tests passed 16 checks; offline evaluation passed 15/15; the final live local-model evaluation passed 13/13. The initially failing Chinese case passed three consecutive targeted reruns after the prompt change. Hybrid smoke tests returned a grounded English answer citing pages 8 and 16 and a grounded Simplified Chinese answer citing pages 10, 12, and 18. `.env` is ignored by Git.

**AI assistance:** The primary coordinator reproduced and diagnosed the live-model failure after the earlier exploration, planning, and implementation agents completed their assigned scopes. No commit or push was performed.

## 2026-11-18 - Add persistent repository agent instructions

**Why:** Future coding agents need the same product boundaries, grounding standards, verification expectations, logging format, model-routing honesty, and Git approval rule established during this implementation session.

**Where:** `AGENTS.md`.

**How:** Added repository-wide instructions covering required context, insurance safety, source grounding, task-specific development agents, mandatory Why/Where/How/Impact/Verification logging, Docker and evaluation commands, secret handling, and explicit approval before commits or external actions.

**Impact:** Subsequent agents receive consistent project guidance automatically and are less likely to over-engineer the runtime, misstate evaluation evidence, omit the development log, expose credentials, or commit without approval.

**Verification:** Confirmed `AGENTS.md` is repository-scoped, references existing project files and working commands, includes the installed Postman CLI note, and preserves the user's no-commit/no-push rule.

**AI assistance:** The primary coordinator distilled confirmed project decisions and the user's explicit instructions. No commit or push was performed.

## 2026-11-20 - Link brochure citations and add submission checks

**Why:** Reviewers need to inspect the original evidence and reproduce the chatbot's key flows.

**Where:** The brochure API route, source cards, backend tests, README, and evaluation guide.

**How:** Serve the bundled PDF inline and link each source card to its PDF page. Add regression tests for PDF delivery and conversation history forwarding, plus a manual walkthrough for bilingual answers, citations, follow-ups, and abstention.

**Impact:** Reviewers can verify evidence from the chat and repeat the demo without guessing which questions to ask.

**Verification:** 28 backend tests and 15 offline evaluation cases passed. Docker rebuilt and served the frontend and an exact copy of the original PDF. Browser PDF page navigation and live follow-up answer quality were not verified in this run.

**AI assistance:** The primary Codex agent implemented and checked the changes.

## Make model temperature optional and refine the product voice

**Why:** Some compatible models reject explicit temperature values. The chatbot and website also need a consistent educational voice.

**Where:** Provider settings and request adapter, live evaluator, environment template, chatbot prompt, website copy, and README.

**How:** Omit temperature by default and send an explicit value when configured. Use a courteous, measured style in every reply language, with plain explanations and material conditions beside the relevant claims. Apply the same tone to the welcome and error copy.

**Impact:** Providers can use their own generation defaults, and readers get a clearer explanation of what the tutor can help them understand.

**Verification:** Docker build, 30 backend tests, and 15 offline evaluation cases passed. Mocked requests covered blank temperature and explicit zero. Live voice quality was not assessed.

**AI assistance:** The primary Codex agent implemented and verified the changes.

## Add an optional citation check to the demo

**Why:** Demonstrate how to verify that an answer preserves material brochure conditions.

**Where:** README demo walkthrough.

**How:** Add a checklist for comparing the two rates, the eligibility period, and the cited passages.

**Impact:** Provides a repeatable manual check for the follow-up interview.

**Verification:** Reviewed the checklist against the existing walkthrough and ran `git diff --check`. No live demo was run for this documentation change.

## Enforce adapter boundaries and isolate answer translation

**Why:** The Dune method calls for mechanically enforced dependencies and clear feature ownership.

**Where:** Backend architecture tests, the React chat shell, and the answer translation feature.

**How:** Check static Python imports for adapter dependencies on higher layers or sibling adapters. Move translation requests, cached variants, and controls into a feature module. The chat shell owns original conversation history, and the feature owns displayed variants.

**Impact:** Invalid imports fail with guidance on where to wire the dependency. Switching answer languages keeps the original conversation history stable. If regeneration withholds a previously grounded answer, the original stays visible and the user can retry.

**Verification:** 36 backend tests and 15 offline evaluation cases passed. The Docker build compiled the frontend. Browser interaction and live generation were not exercised in this pass.

**AI assistance:** The primary Codex agent implemented and verified the changes.
