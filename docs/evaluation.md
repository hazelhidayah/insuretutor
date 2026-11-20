# Evaluation

Run the committed suite from the repository root:

```bash
PYTHONPATH=backend python -m app.evaluation
```

The command outputs JSON with a pass/fail result per check and exits nonzero if any case fails. It runs the real chat service and brochure retrieval with lexical search, using scripted responses instead of a model. No network, API key, or embedding download is needed. The fixtures cover expected retrieval pages, injection and no-match gates, valid citation mapping, rejection of missing or unknown citation labels, and language instructions and basic script signals. The cases are in `backend/app/eval_data/cases.json` and can be replaced with `--cases path/to/cases.json`; `--corpus` selects another corpus.

To run the non-fixture-only cases through a configured OpenAI-compatible provider, explicitly opt in:

```bash
PYTHONPATH=backend python -m app.evaluation --live
```

Configure `MODEL_API_KEY`, `MODEL_BASE_URL`, and `MODEL_NAME` in the environment or `.env` first. Live requests can incur charges and send questions and brochure excerpts to the provider. Retrieval still uses lexical search for reproducibility; this does not evaluate the application's hybrid embedding mode. The report omits generated answers and provider settings. Provider unavailability is reflected as failed checks.

## Interpretation and limitations

Before submission, run the backend tests and offline suite, then use the README walkthrough against the running Docker app. Check that citation links open the correct PDF page, switching languages retains key conditions, a context-dependent follow-up makes sense, and unsupported or personalised questions receive an appropriate response. The automated follow-up test checks history forwarding with a scripted provider. Live follow-ups that rely on earlier turns still need manual review because retrieval uses the latest question.

A passing offline suite validates the pipeline against controlled responses; it does not establish that a real model is accurate, safe, or fluent. Page recall checks whether any specified page appears in the top six, not whether the passage fully answers the question. Citation mapping confirms label and page metadata, not that claims follow from evidence or that all factual paragraphs have citations. The language check detects broad English/Chinese script only: it cannot distinguish Simplified from Traditional Chinese, judge fluency, or verify translation accuracy. Live results require human review of factual support, numeric claims, appropriate refusal of personalised advice, and language quality. The live mode does not print answers, so use the application separately for that review.

Retrieval scores are relative within each query, so a high score alone does not establish relevance. Before a ranked passage is treated as evidence, a conservative coverage check requires at least 60% of substantive English query terms, or at least two Chinese query bigrams covering 30% of the query bigrams, to occur in one passage. This check applies to both lexical and hybrid results. It blocks the included credit-rating, pancake, and weather examples, but it can reject valid paraphrases, Simplified/Traditional variants, or questions whose evidence uses different terminology. Matching words or bigrams also do not establish semantic relevance. These examples therefore do not establish reliable out-of-scope detection. Advice boundaries currently rely on model instructions, not deterministic enforcement. These are open limitations, not guarantees from this suite.

Potential future evaluation work includes a larger independently annotated multilingual set, hybrid retrieval comparisons, numeric and claim-level support checks, and human-labelled advice and out-of-scope cases. Add cases with documented expected pages and clear acceptance criteria before treating aggregate scores as evidence of quality.

## Latest local verification

On 18 November 2026, the uncommitted working tree was evaluated with local Ollama `qwen2.5:7b`:

- Backend tests: 16 passed.
- Offline scripted-provider evaluation: 15/15 cases passed.
- Live local-provider evaluation: 13/13 applicable cases passed after adding one bounded citation-repair retry.
- Hybrid application smoke tests returned grounded English and Simplified Chinese answers with structured citations.

The first live run passed 12/13 because the model intermittently produced an invalid Chinese citation label even though the expected page was retrieved. Stronger allowed-label instructions, temperature zero, and one repair attempt produced three consecutive passes for the failing case before the full 13/13 rerun. These results demonstrate the tested local configuration only; they are not a statistical safety or accuracy guarantee and do not replace human review of generated claims.
