# InsureTutor

InsureTutor is an evidence-first AI tutor for members of the public who are trying to understand the FLEXI-ULife Prime Saver insurance plan. It answers in English or Simplified Chinese, lets users switch an existing answer between those languages and exposes the brochure pages behind each supported answer.

## Run with Docker

You’ll need Docker with Compose and access to an OpenAI-compatible chat model. The brochure and its index come with the repo.

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Set an OpenAI-compatible chat endpoint, API key and model in `.env`.

3. Build and start the application:

   ```bash
   docker compose up --build
   ```

4. Open [http://localhost:8000](http://localhost:8000).

The first start downloads the local multilingual embedding model into the named `model-cache` Docker volume. Later starts reuse it. The configured endpoint handles generation and optional answer review. Retrieval runs locally.

## Architecture

```text
Browser
  │
  ├── React chat interface
  │     └── answer text + structured source cards
  │
  └── POST /api/chat
          │
          ├── input guardrails
          ├── hybrid retrieval
          │     ├── multilingual local embeddings
          │     └── token + character n-gram lexical search
          ├── OpenAI-compatible chat provider
          ├── citation-label validation
          └── structured response
```

I chose a **modular monolith** because this take-home has one brochure and one chat flow. One container is easy for a reviewer to run. The Docker build compiles React, then FastAPI serves the UI and the API. Retrieval, model access and guardrails have their own modules. The tests check that those modules keep their dependency boundaries.

If the corpus grew enough that indexing needed its own schedule, I’d split ingestion and indexing first. I’d separate retrieval if it needed independent scaling, or model access if several apps needed shared provider routing and quotas. Each split would introduce another service to run and monitor.

See [ADR 0001](docs/decisions/0001-modular-monolith.md) for the decision and trade-offs.

## Retrieval and citations

The cooling-off deadline and Chinese periodic-withdrawal examples use reviewed answers for narrowly matched questions. The answers cite the original PDF and are withheld if the indexed source passages change. Other supported questions use model-generated answers with citation checks.

I kept embeddings in the backend with FastEmbed and a multilingual ONNX model. The evaluator can bring a chat-only endpoint. The small corpus fits in memory. The trade-off is a larger runtime image and a first-start model download. A separate embedding container would make sense if I needed to scale embedding work independently.

Hybrid search combines **meaning** from multilingual embeddings with **exact matches** from tokens and character trigrams. That helps when a Simplified Chinese question refers to a brochure passage written in Traditional Chinese, or when a rate or product term needs an exact match. Lexical search is the fallback if embeddings fail to load. The evidence gate is deliberately conservative and can reject a valid paraphrase.

I extract and index the brochure by PDF page so users can check the source themselves. The model receives relevant excerpts with labels like `[S1]`. The API validates the labels, retries a citation failure once and turns accepted labels into page links. Citations use the PDF viewer’s page numbering, which can differ from the number printed on the brochure.

Rebuild the source corpus after replacing the PDF:

```bash
python scripts/build_corpus.py
```

## Guardrails

I chose lightweight checks so obvious off-topic or unsupported requests can stop before a model call.

- **Input and retrieval.** Validate request limits, screen messages and passages for common instruction overrides, mask recognised sensitive data before model calls and admit only relevant, explicitly public passages.
- **Answer.** Ask the model to stay within the brochure and avoid personalised advice. Check citations, recognised sensitive output, a limited set of harmful phrases and whether each stated percentage occurs in the cited evidence. Withhold answers that fail the checks.
- **Optional review.** Set `REVIEW_ANSWERS=true` to add a second model call for claim and policy review. This adds latency and can withhold valid answers. It defaults to off.

The percentage check confirms a number appears in the cited passage. A reader still needs to check whether the answer puts it in the right context and preserves the conditions. The filters cover recognised patterns. Personalised-advice handling also depends on retrieval and model instructions. Private documents would need authenticated users and server-enforced access controls.

## Provider configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `MODEL_BASE_URL` | OpenAI-compatible API root ending before `/chat/completions` | `https://api.openai.com/v1` |
| `MODEL_API_KEY` | Provider API key | none |
| `MODEL_NAME` | Provider model identifier | `gpt-4.1-mini` |
| `MODEL_TEMPERATURE` | Optional generation setting from 0 to 2. Leave blank to use the provider default. | unset |
| `REVIEW_ANSWERS` | Enable a second model call to review generated answers | `false` |
| `EMBEDDING_MODEL` | Local FastEmbed model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| `RETRIEVAL_TOP_K` | Maximum evidence chunks supplied to the model | `6` |

I put model access behind a backend adapter so an evaluator can change the endpoint, key and model in `.env`. The browser calls `POST /api/chat` with the question, reply language and recent conversation history. `GET /api/health` reports the runtime state and `GET /api/brochure` serves the original PDF. Keep provider keys in the ignored `.env` file.

InsureTutor uses a courteous, plain-language voice inspired by the brochure. Answers lead with the explanation and keep important conditions close to the claims they qualify.

### Local Ollama provider

Ollama exposes an OpenAI-compatible endpoint and can be used without a hosted API key. When the application runs inside Docker on macOS, use:

```dotenv
MODEL_BASE_URL=http://host.docker.internal:11434/v1
MODEL_API_KEY=ollama-local
MODEL_NAME=qwen2.5:7b
```

The model must already be installed and the Ollama service must be running on the host. `MODEL_API_KEY` is a non-secret compatibility value ignored by Ollama. The project `.env` remains excluded from Git.

## Development

Backend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
PYTHONPATH=backend pytest backend/tests -q
uvicorn backend.app.main:app --reload
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server proxies `/api` to FastAPI on port 8000.

Run `PYTHONPATH=backend python -m app.evaluation` to check the reviewed answers and the chat pipeline with scripted model responses. See [evaluation](docs/evaluation.md) for live-provider testing and the limits of these checks.

## Demo walkthrough

1. Start the app using [Run with Docker](#run-with-docker). Ask “Is the 4% interest rate guaranteed?” and check whether the answer distinguishes the assumed rate from the conditional guarantee.
2. Select a citation marker, then choose **Open brochure at page …** in the source desk. Compare the answer's numbers and conditions with the original page.
3. Start a new conversation and choose **定期提款有什么条件？**. Check the separate monthly and annual minimum terms, then switch the answer to English and open PDF page 12.
4. In a new conversation, ask **保单的冷静期是多少天？**, then **那从哪一天开始算？**. Check that both replies cite PDF page 15 and include the earlier of the two delivery events.
5. Ask for directions to McDonald's or a personalised buying recommendation. Check that the tutor abstains.

### Optional demo check: Verify a cited claim

Ask “Is the 4% interest rate guaranteed?” Select its citation marker, then open the cited brochure page from the source desk. Compare the answer with the relevant passage:

- Check that the answer describes 4% as the brochure’s assumed base crediting rate, not a guarantee.
- If the answer mentions the separate 2.5% long-term guarantee, check that it specifies the policy must have been in force for at least 15 years and describes the account-value guarantee accurately.
- Check that each claim points to a page that supports it. If the page supports the number but the answer leaves out a condition, flag the answer as incomplete.

During the interview, show the sentence in the answer and the passage side by side. Explain which wording preserves the brochure’s condition.

## Example conversations

### Guaranteed versus assumed interest

**User:** Is the 4% interest rate guaranteed?

**Expected behaviour:** Explain that the brochure's 4% base crediting rate was a current assumption at its January 2022 print date and was not guaranteed. Separately explain the conditional 2.5% long-term guarantee for a policy in force for at least 15 years, with citations to the relevant brochure pages.

### Cross-script Chinese retrieval

**User:** 定期提款有什么条件？

**Expected behaviour:** Answer in Simplified Chinese even though the brochure primarily contains Traditional Chinese and English. Cover the minimum policy duration, minimum withdrawal amount and period and fee waiver, with page citations.

### Advice boundary

**User:** I am 30 with two children. Should I buy this plan or invest in an ETF?

**Expected behaviour:** Decline to decide suitability or compare personalised outcomes. Offer to explain documented plan features, charges, risks and conditions instead.

### Unsupported question

**User:** What is the insurer's current 2026 credit rating?

**Expected behaviour:** Abstain because the supplied brochure does not establish the current rating.

## Known limitations

- The brochure's bilingual layout can produce imperfect extracted reading order.
- Citation-label validation confirms that cited sources were retrieved, not that every clause of the answer is logically entailed.
- Conversation state lives in the browser request history and is not persisted.
- Retrieval thresholds require evaluation against a larger multilingual question set; the coverage checks can reject valid paraphrases and do not prove semantic relevance.
- The local embedding model increases image size and first-start time.

## Project records

- [Product context](PRODUCT.md)
- [Architecture decision](docs/decisions/0001-modular-monolith.md)
- [Development log](docs/development-log.md)
- [Evaluation](docs/evaluation.md)
- [AI-assisted development workflow](docs/ai-development-workflow.md)

