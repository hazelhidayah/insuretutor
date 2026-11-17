# InsureTutor

InsureTutor is an evidence-first AI tutor for members of the public who are trying to understand the FLEXI-ULife Prime Saver insurance plan. It answers in English, Simplified Chinese, or Traditional Chinese and exposes the brochure pages behind each supported answer.

This repository is a take-home demo. It is educational software, not a suitability assessment, quotation tool, or replacement for the policy contract or a qualified adviser.

## Run with Docker

1. Copy the environment template:

   ```bash
   cp .env.example .env
   ```

2. Set an OpenAI-compatible chat endpoint, API key, and model in `.env`.

3. Build and start the application:

   ```bash
   docker compose up --build
   ```

4. Open [http://localhost:8000](http://localhost:8000).

The first start downloads the local multilingual embedding model into the named `model-cache` Docker volume. Later starts reuse it. The model endpoint is used only for answer generation; retrieval does not require a provider embeddings API.

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

The application is a modular monolith. React is compiled during the multi-stage Docker build, then FastAPI serves both the API and static interface from one container. Internal modules preserve clear boundaries without introducing deployment overhead that the small demo does not need.

See [ADR 0001](docs/decisions/0001-modular-monolith.md) for the decision and trade-offs.

## Retrieval and citations

The ingestion script extracts the brochure page by page and preserves source, page, section, and chunk identifiers. Retrieval combines:

- local multilingual ONNX embeddings from `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`;
- lexical token matching;
- character trigrams, which improve matching across unsegmented Chinese text.

Retrieved passages receive request-local labels such as `[S1]`. The language model may cite only these labels. The API rejects a generated answer if it contains an unknown label or no valid source label, then maps valid labels back to structured page metadata for the interface.

Rebuild the source corpus after replacing the PDF:

```bash
python scripts/build_corpus.py
```

## Guardrails

Current controls include:

- prompt-injection pattern detection in English and Chinese;
- a retrieval-confidence gate for unsupported questions;
- a system policy limiting answers to the supplied brochure;
- explicit boundaries around personalised recommendations and financial, legal, tax, or underwriting advice;
- instructions to distinguish guaranteed and non-guaranteed values;
- request and conversation-history size limits;
- post-generation citation-label validation;
- a visible ungrounded state when the system withholds an answer.

These controls reduce risk but do not prove that every generated statement is entailed by its citation. Numeric-claim verification and a model-based entailment check are deliberate next steps described under limitations.

## Provider configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `MODEL_BASE_URL` | OpenAI-compatible API root ending before `/chat/completions` | `https://api.openai.com/v1` |
| `MODEL_API_KEY` | Provider API key | none |
| `MODEL_NAME` | Provider model identifier | `gpt-4.1-mini` |
| `EMBEDDING_MODEL` | Local FastEmbed model | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| `RETRIEVAL_TOP_K` | Maximum evidence chunks supplied to the model | `6` |

No secret is required for document retrieval. Never commit `.env`.

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

## Example conversations

### Guaranteed versus assumed interest

**User:** Is the 4% interest rate guaranteed?

**Expected behaviour:** Explain that the brochure's 4% base crediting rate was a current assumption at its January 2022 print date and was not guaranteed. Separately explain the conditional 2.5% long-term guarantee for a policy in force for at least 15 years, with citations to the relevant brochure pages.

### Cross-script Chinese retrieval

**User:** 定期提款有什么条件？

**Expected behaviour:** Answer in Simplified Chinese even though the brochure primarily contains Traditional Chinese and English. Cover the minimum policy duration, minimum withdrawal amount and period, and fee waiver, with page citations.

### Advice boundary

**User:** I am 30 with two children. Should I buy this plan or invest in an ETF?

**Expected behaviour:** Decline to decide suitability or compare personalised outcomes. Offer to explain documented plan features, charges, risks, and conditions instead.

### Unsupported question

**User:** What is the insurer's current 2026 credit rating?

**Expected behaviour:** Abstain because the supplied brochure does not establish the current rating.

## Known limitations

- The source is a product brochure, not the complete policy contract.
- The brochure's bilingual layout can produce imperfect extracted reading order.
- Citation-label validation confirms that cited sources were retrieved, not that every clause of the answer is logically entailed.
- Conversation state lives in the browser request history and is not persisted.
- Retrieval thresholds require evaluation against a larger multilingual question set.
- The local embedding model increases image size and first-start time.

## Project records

- [Product context](PRODUCT.md)
- [Architecture decision](docs/decisions/0001-modular-monolith.md)
- [Development log](docs/development-log.md)
- [Evaluation plan](docs/evaluation.md)

