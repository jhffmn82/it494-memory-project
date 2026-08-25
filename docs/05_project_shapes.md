# Three proposals, each with its execution steps

Prepared by the assistant against the scope of record: the prototype is a mock built by directed, unexamined AI execution; the target is a general harness the student implements himself, organized by his five steps: ingest, organize, retrieve, inject, maintain. Constraints: roughly 70 to 100 fall hours in two open blocks (September 1 to 27, October 19 to November 15), PhD applications December 1 to 15, IT 494 continuing through spring. Each proposal below is a complete alternative with its own steps; a recommendation follows.

## Proposal 1. Design first, build the core, prove it (recommended)

The semester produces a defended design, a working harness core organized by the five steps, and a short paper with first measurements. The full schedule with hour boxes, gates, and valves is the plan-of-record document; the execution skeleton:

1. Read for three weeks, each week closing in a written position artifact (fold positions; fact-row schema; metric definitions), so the reading is checkable and feeds Fang the metric sheet early.
2. Write the design document and freeze the stage contracts as JSON schemas: segment, summarize, extract-entities, extract-facts, each with named rejection criteria. Write the segmentation specification, which the mock never had.
3. Build INGEST: corpus adapters for chat transcripts and plain-text documents emitting one document stream; segmentation as a model call against the segment contract, with TextTiling as the deterministic comparison arm.
4. Build ORGANIZE: segment to summary against the contract, filed into the fixed two-level tree; entity extraction with alias ledger and pronoun resolution by model call; dated fact rows with source pointers, the merge from raw tokens to attributes recorded, not silent.
5. Build RETRIEVE: tree routing (read index, read rollup, descend), entity and fact lookup, lexical fallback.
6. Build INJECT: a token-budget accountant composing context three ways: top-k chunks (the control), tree-routed summaries, tree plus facts hybrid.
7. Build MAINTAIN: content-hash staleness, refold of stale nodes only, supersession by subject-predicate collision with later-assertion-wins reads.
8. Build the evaluation spine alongside, never after: question runner, LLM-judge scorer on a different model tier than any writer, calibrated against a hand-labeled sample.
9. Run: archive slice as tenant zero; the certified question set; the three arms; the stage-wise model-sensitivity table.
10. Write the paper from artifacts that already exist (design, positions, run tables); arXiv by early December.

Pays: the December artifact, the defensible design, and the system's weakest point (no metrics) converted into the contribution. Risks: a design semester sliding into a reading semester, held off by step 3 starting on schedule regardless; and implementation velocity, since the student's own estimate puts the full five-step build in the hundreds of hours, which is why the paper anchors on the instruments (the miss rate runs on the live mock without the harness) and the build is a full-year deliverable with fall reaching ingest and organize plus one comparison.

## Proposal 2. Build the full product outright

Skip the defended design; go straight at the distributable system and let the paper wait.

1. Compress reading to two weeks, targeted at build decisions only.
2. Sketch the architecture in a week, undefended, revisable.
3. Build the same five steps, but productized from the start: a storage layer separable from any tenant, a configuration surface, an installation path, and multi-tenant separation.
4. Migrate the mock's raw archive through it as the first tenant.
5. Demonstrate the annual-training pattern: several concurrent consumers against one backend.
6. Install test by a second person; fix what breaks.
7. Write the paper in spring from the running system.

Pays: the strongest demo and the portfolio artifact, sooner. Risks, stated with the calendar math: productization (storage, config, install, isolation) does not fit 40-odd build hours under an authorship rule, so this plan reaches December with a half-built system, no paper, and nothing new in the applications. Honest verdict: this is the spring semester moved to fall, and it costs the December window to do it.

## Proposal 3. One question, studied to the bottom

Skip the system; produce one defensible measured claim about memory systems in general.

1. Pick the question. Candidate A: the counterfactual miss rate (how often a store held the answer and the session never consulted it), which no benchmark can express. Candidate B: content-derived staleness versus write-time flags as a correctness property of human-editable stores.
2. Define the instrument precisely and get Fang's agreement on the definition before measuring.
3. For A: add consult-logging to the live mock, collect four weeks of sessions, hand-label the misses, and report rate with confidence bounds against a cued-recall baseline. For B: hand-edit N stored files out of band, run both staleness schemes, report detection rates.
4. Run the ablation both directions and try to break the result before reporting it.
5. Write a short, narrow paper; arXiv by December.

Pays: the cleanest research identity per hour and an instrument other systems could adopt. Risks: single-shot; a null result is publishable but a harder sell, and the harness goes unbuilt for a semester.

## Recommendation

Proposal 1, with Proposal 3's instruments embedded as its evaluation spine (steps 8 and 9 carry the miss rate and the corrected-facts band), and Proposal 2 as the spring semester it honestly is: distributable packaging, the install test, the cold literature corpora at full and replication depth, and the raw-data migration that retires the mock. The two commitments that keep it honest: the paper is scoped to what exists by November 15, and every fall artifact is written about the general problem with the mock as the running example, so nothing is reframed later.
