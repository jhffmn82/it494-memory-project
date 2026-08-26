# Implementation: Evaluation Spine

Prepared by the assistant.

The spine is the component that never waits: it runs thin from the first week it exists (08_plan_of_record, Phase 2 step 6), and its instruments must run against mock rows as well as harness rows, because the December paper's anchor (the counterfactual miss rate) cannot depend on the harness finishing. Two rules follow: `instruments.py` reads run-row JSONL and store files only, importing nothing from the pipeline; and since the mock has no consult logging (cite_log.py died unwired, 07_pipeline_anatomy), a thin mock-side logger emitting conforming run rows (injected = consulted leaf ids) is a separate deliverable, due before Phase 3 step 2.

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

**`harness/eval/certify.py`** runs the per-tier closed-book pass; only questions every bare tier fails survive (06_end_product_and_testing, the NovelQA rule). Pass or fail comes from `judge_symmetric` against the fixed answer on a non-answering tier; unsure counts as pass, the conservative direction.
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

Six modules.

## Data touched

Reads: Question records (band, fixed_answer, evidence_segs, certified map), Fact rows (supersession status, for stale_serve), Segments (existence check behind miss_rate). Writes: Run rows, Rejection records, the certified map inside Question records (an atomic whole-file rewrite; an append cannot update a record in place). Two schema gaps. The Run row stores `verdict` but not answer text, so verdicts cannot be re-judged after a judge-prompt change; add `answer_text` (or a run_id-keyed sidecar). Certification stores pass/fail but not the answer that earned it; the sidecar in `certify_set` keeps disputed drops auditable.

## Contracts

The judge call returns `{"verdict": "pass" | "fail", "rationale": string}` with rationale capped at 50 words. Rejection criteria: non-JSON output, verdict outside the enum, missing or extra keys, rationale over cap. Retry rule from 11_build_plan: retry once with the validation error appended, then write a Rejection record; the run row's verdict becomes `unscored`, counted and reported, never silently dropped. Run-row verdicts span pass, fail, unsure, unscored; the per-call enum stays pass or fail. Bias mitigations from the judge reading: reference-guided grading (the fixed answer is always in the prompt, so the judge checks rather than answers); the rationale cap plus an instruction that answer length is irrelevant (verbosity); and `judge_symmetric`, two calls with candidate and reference order swapped (position), `unsure` on disagreement, unsure rows routed to the hand-label queue.

## Build sequence

1. `rows.py`: dataclasses, JSONL append/load, `config_hash`. Test: round-trip property test; hash identical under key reordering.
2. `questions.py` plus a ten-question toy set written by hand across all four bands, and a toy store fixture (a dozen segments, a few fact rows, one supersession) for steps 6 and 8. Test: a corrected-band question without a superseded fact in evidence is refused at load; `author_check` flags a planted dangling evidence_segs id.
3. `runner.py` against a canned fake arm and fake tier (no network), judging stubbed to `unscored` until step 4 wires `judge.py`. Test: rows land with injected ids in order and a stable config_hash; a rerun with the same config matches once run_id and timestamp are masked.
4. `judge.py` against the fake tier: schema validation, retry, rejection path. Test: a malformed fake response retries once, then produces exactly one Rejection and an `unscored` verdict; a fake tier flipping verdict under order swap yields `unsure`.
5. Live smoke: ten judge calls per tier on toy answers, `judge_symmetric` on. Test: rejection rate per tier logged to the rejections file.
6. `certify.py` over the toy set on all three tiers. Test: a question any tier answers correctly is absent from `surviving()`.
7. `instruments.py`: band_table, sensitivity, and cost. Test: hand-computed expected numbers on a fixture runs file.
8. miss_rate and stale_serve. Test: a fixture with one planted never-injected evidence segment and one superseded-fact injection; each instrument flags exactly its plant and nothing else. stale_serve reports `n/a`, not zero, when the store holds no superseded facts yet.
9. Calibration: the toy set cannot yield 100 live answers; the labeled set is the step 5 and 6 answers plus hand-authored perturbations (correct, subtly wrong, verbose, terse) to n=100, hours of hand work, budgeted as such. Run `calibrate`, unsure and unscored rows excluded from kappa, reported as counts. Test: report exists with n, kappa, percent agreement.

## Sanity risks

Certified questions are hard by construction, so judged answers skew toward fail; kappa is unstable on skewed label distributions, so the report carries percent agreement beside kappa and the 100-label sample is balanced across labels, not random. Second, certification is flaky: a tier can luck into a pass; the rule is one attempt, temperature 0, answer stored verbatim, no retries; accept that the surviving set shrinks. Third, stale_serve is meaningless before the maintain stage writes supersessions, and a zero there reads as success; hence step 8's `n/a` guard; that misreading is cheap to make and expensive to publish.

## Done means

From 11_build_plan made concrete: `runs.jsonl` holding at least one full pass of every built arm over the surviving toy set; `questions.jsonl` with a certified map covering all three tiers on every question; `rejections.jsonl` showing the ten-call live judge smoke per tier with its rejection rate; the calibration report with n=100 and kappa (below 0.6, revise the judge prompt and recalibrate before any scored run stands); and the planted-fault fixture test green for both instruments. When those five artifacts exist, the spine is done and every later pipeline stage inherits its scoring for free.

## Sanity check

Challenged every signature, dependency, and test against 10_data_model, 07_pipeline_anatomy, and 11_build_plan. Held: the module split, the judge contract and retry rule, the one-attempt certification rule, the `n/a` guard, the five done artifacts. Changed: the mock has no consult logging (cite_log.py died unwired), so a conforming-row logger is now a named separate deliverable; `certify_set` gained persistence paths and a stated pass/fail mechanism (judge_symmetric, unsure drops the question); the runner takes the arm as a callable so it runs before any pipeline stage, judging stubbed until step 4; `miss_rate` now takes the store it reads; step 2 now builds the fixtures steps 6 and 8 consumed; byte-comparability was false with fresh run_ids; `sensitivity` and the order-swap behavior had no build step or test; n=100 was unreachable from ten questions, so calibration authors perturbations, priced as hand work.
