# Evaluation

Run the suite from the repository root:

```bash
PYTHONPATH=backend python -m app.evaluation
```

The command outputs JSON with a result per check and exits nonzero if any case fails. It exercises the real chat service with lexical retrieval and either a reviewed answer or a scripted model response. No network, API key, or embedding download is needed. Cases cover expected pages, source-label mapping, English and Chinese, the cooling-off follow-up, prompt overrides, off-topic requests, and sample personal-advice requests. Use `--cases path/to/cases.json` for an alternative to `backend/app/eval_data/cases.json` or `--corpus` to select another index.

To run the non-fixture-only cases through a configured OpenAI-compatible provider, explicitly opt in:

```bash
PYTHONPATH=backend python -m app.evaluation --live
```

Configure `MODEL_API_KEY`, `MODEL_BASE_URL`, and `MODEL_NAME` in the environment or `.env` first. Live requests can incur charges and send questions and brochure excerpts to the provider. Retrieval still uses lexical search for reproducibility; this does not evaluate the application's hybrid embedding mode. The report omits generated answers and provider settings. Provider unavailability is reflected as failed checks.

## Interpretation and limitations

The reviewed cooling-off and withdrawal cases check the actual application answers and original source anchors without a model call. The other scripted cases still check orchestration with fixture answers. Live evaluation is needed to assess generated answers.

Before submission, run the backend tests and offline suite, then use the README walkthrough against the running Docker app. Check PDF page links, language switching, the cooling-off follow-up, and refusals. The tests cover the reviewed follow-up through the API and check that ordinary conversation history reaches the provider. General context-dependent follow-ups still need manual review.

A passing offline suite validates the pipeline against controlled responses; it does not establish that a real model is accurate, safe, or fluent. Page recall checks whether any specified page appears in the top six, not whether the passage fully answers the question. Citation mapping confirms label and page metadata, not that claims follow from evidence or that all factual paragraphs have citations. The language check detects broad English/Chinese script only: it cannot distinguish Simplified from Traditional Chinese, judge fluency, or verify translation accuracy. Live results require human review of factual support, numeric claims, appropriate refusal of personalised advice, and language quality. The live mode does not print answers, so use the application separately for that review.

Retrieval scores are relative within each query, so a high score alone does not establish relevance. Before a ranked passage is treated as evidence, a conservative coverage check requires at least 60% of substantive English query terms, or at least two Chinese query bigrams covering 30% of the query bigrams, to occur in one passage. This check applies to both lexical and hybrid results. It blocks the included credit-rating, pancake, and weather examples, but it can reject valid paraphrases, Simplified/Traditional variants, or questions whose evidence uses different terminology. Matching words or bigrams also do not establish semantic relevance. These examples therefore do not establish reliable out-of-scope detection. Advice boundaries currently rely on model instructions, not deterministic enforcement. These are open limitations, not guarantees from this suite.

Future evaluation work includes a larger multilingual set, live comparison of lexical and hybrid retrieval, and human checks of claim support. The percentage guard checks presence in cited evidence. It cannot verify that the value was interpreted correctly.

## Latest local verification

On 22 November 2026, the local working tree passed **59 backend tests and 21 offline evaluation cases**. The additions cover invalid API requests, a cited Chinese follow-up over HTTP, mixed-quality retrieval results, percentages found only in uncited evidence, reviewer outages, and English and Chinese refusals.

A Docker smoke test with lexical retrieval confirmed that the app serves the homepage, its compiled JavaScript, and the original PDF. An unknown route returned 404, and the reviewed Chinese cooling-off request returned a citation to PDF page 15.

In the preceding browser walkthrough using the hybrid build and local Ollama `qwen2.5:7b`, the generated English rate answer preserved the 15-year condition. The reviewed Chinese withdrawal and cooling-off answers retained their key conditions, and the browser opened PDF citation links. One free-form Chinese rate answer was withheld after failing citation validation. The full live-provider suite was not rerun for this documentation and test update.
