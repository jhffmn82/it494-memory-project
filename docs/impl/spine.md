# Implementation: Evaluation Spine

The spine runs thin from its first week (08_plan_of_record, Phase 2 step 6); its instruments run against mock rows as well as harness rows, because the December paper's anchor, the counterfactual miss rate, cannot wait for the harness. Hence: `instruments.py` reads run-row JSONL and store files only, importing nothing from the pipeline; and, the mock having no consult logging (cite_log.py, 07_pipeline_anatomy), a thin mock-side logger emitting conforming run rows (injected = consulted leaf ids) is a separate deliverable due before Phase 3 step 2.

## Modules

**`harness/eval/rows.py`** owns the record types from 10_data_model.md and their JSONL persistence; every other module goes through it.
```
config_hash(config: dict) -> str            # stable hash, key-order independent
append_run(path, row: RunRow) -> None       # validate then append one line
load_runs(path, **filters) -> list[RunRow]  # filtered read, e.g. arm=, q_id=
append_rejection(path, rej: Rejection) -> None  # one line per contract rejection
```

**`harness/eval/questions.py`** loads and validates question sets.
```
load_questions(path) -> list[Question]      # schema check every row
validate_band(q) -> None                    # corrected band must cite a superseded fact
author_check(qs) -> Report                  # duplicate ids, dangling evidence_segs
```

**`harness/eval/certify.py`** runs the per-tier closed-book pass; only questions every bare tier fails survive (06_end_product_and_testing, the NovelQA rule), `judge_symmetric` scoring each attempt against the fixed answer on a non-answering tier, unsure counting as pass.
```
closed_book(q, tier) -> str                 # bare model, temperature 0, one attempt
certify_set(qs, tiers, q_path, sidecar_path) -> None  # rewrites questions file; verbatim answers to sidecar
surviving(qs) -> list[Question]             # all tiers fail, and only those
```

**`harness/eval/judge.py`** scores an answer against the fixed answer via `generate` on a tier never used as a writer in that run.
```
judge(q, answer, tier) -> Verdict           # schema-validated call, retry once
judge_symmetric(q, answer, tier) -> Verdict # order-swapped double call; disagreement -> unsure
calibrate(labeled_path, tier) -> KappaReport  # Cohen's kappa vs the 100 hand labels
```

**`harness/eval/runner.py`** executes a question set against one arm and emits run rows. An arm is a passed-in compose callable (question to injected context and ids), so the runner imports nothing from the pipeline; day one's arm is canned.
```
run_set(qs, arm, tiers, budget) -> list[RunRow]  # compose, answer, judge, record
answer_one(q, arm, config) -> (text, injected_ids)  # injected ids kept in order
```

**`harness/eval/instruments.py`** is queries over run rows and the store, nothing else.
```
band_table(runs) -> Table                   # accuracy per band per arm
miss_rate(runs, qs, store) -> Rate          # evidence_segs held by store, never injected
stale_serve(runs, facts) -> Rate            # superseded fact id present in injected
sensitivity(runs) -> Table                  # verdicts grouped by per-stage tier config
cost(runs) -> Table                         # tokens, dollars, latency per arm
```

## Data touched

Reads: Question records (band, fixed_answer, evidence_segs, certified map), Fact rows (for stale_serve), Segments (behind miss_rate). Writes: Run rows, Rejection records, the certified map inside Question records (atomic whole-file rewrite). Two gaps: the Run row lacks answer text, so verdicts cannot be re-judged after a judge-prompt change (add `answer_text` or a run_id-keyed sidecar); certification lacks the earning answer (the `certify_set` sidecar keeps disputed drops auditable).

## Contracts

The judge returns `{"verdict": "pass" | "fail", "rationale": string}`, rationale capped at 50 words. Reject: non-JSON, verdict outside the enum, missing or extra keys, rationale over cap. Retry once with the error appended, then a Rejection record; the run-row verdict becomes `unscored`, counted, never dropped. Run-row verdicts span pass, fail, unsure, unscored; the per-call enum stays pass or fail. Bias mitigations per the judge reading: reference-guided grading (the fixed answer sits in the prompt, so the judge checks rather than answers); the rationale cap and an instruction that length is irrelevant; `judge_symmetric` order-swapping, `unsure` on disagreement, routed to the hand-label queue.

## Build sequence

1. `rows.py`: dataclasses, JSONL append/load, `config_hash`. Test: round-trip property test; hash identical under key reordering.
2. `questions.py`, a ten-question toy set across all four bands, and a toy store fixture (a dozen segments, a few fact rows, one supersession) for steps 6 and 8. Test: a corrected-band question without a superseded fact refuses at load; `author_check` flags a planted dangling evidence_segs id.
3. `runner.py` on a canned fake arm and tier, no network, judging stubbed to `unscored` until step 4. Test: rows land with injected ids in order and a stable config_hash; a same-config rerun matches with run_id and timestamp masked.
4. `judge.py` on the fake tier: validation, retry, rejection. Test: a malformed fake response retries once, then exactly one Rejection and an `unscored` verdict; a verdict flipping under order swap yields `unsure`.
5. Live smoke: ten judge calls per tier on toy answers, `judge_symmetric` on. Test: rejection rate per tier logged.
6. `certify.py` over the toy set on all three tiers. Test: a question any tier answers correctly is absent from `surviving()`.
7. `instruments.py`: band_table, sensitivity, cost. Test: hand-computed expected numbers on a fixture runs file.
8. miss_rate and stale_serve. Test: a fixture with one planted never-injected evidence segment and one superseded-fact injection; each instrument flags exactly its plant. stale_serve reports `n/a`, not zero, when no superseded facts exist yet.
9. Calibration. The toy set cannot yield 100 live answers; the labeled set is the step 5 and 6 answers plus hand-authored perturbations (correct, subtly wrong, verbose, terse) to n=100, hours of hand work. Run `calibrate`; unsure and unscored rows are excluded from kappa, reported as counts. Test: report with n, kappa, percent agreement.

## Risks

Certified questions are hard by construction, so judged answers skew toward fail; kappa is unstable on skewed distributions, so the report carries percent agreement beside kappa and the 100-label sample is balanced across labels. Certification is flaky, a tier can luck into a pass; the rule is one attempt, temperature 0, answer stored verbatim, no retries, accepting a smaller surviving set. stale_serve is meaningless before MAINTAIN writes supersessions, where a zero reads as success; hence step 8's `n/a` guard.

## Done means

`runs.jsonl` with one full pass of every built arm over the surviving toy set; `questions.jsonl` with a certified map covering all three tiers; `rejections.jsonl` with the ten-call live judge smoke per tier and its rejection rate; the calibration report with n=100 and kappa (below 0.6, revise the judge prompt and recalibrate before any scored run stands); and the planted-fault fixture test green for both instruments. With those five artifacts the spine is done; every later stage inherits its scoring.
