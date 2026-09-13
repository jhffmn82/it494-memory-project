# Execution plan: from the 1.8 packages to the paper

PROPOSED 2026-09-13, until Justin rules on the slate in section 1. Replaces the 09-08 forward
plan (`log/2026-09-08/forward-plan.md`), which made LongMemEval the first benchmark to cut; the
build since then made it the spine. Feasibility is tracked in section 7 and is to be updated
weekly with real hours. The audit behind this plan is `log/2026-09-13/academic-audit.md`.

## 1. The slate (the ruling this plan needs)

| item | status | recommendation |
|---|---|---|
| LongMemEval: full-context parity arm, flat-retrieval arm, ThreadAtlas arm; the knowledge-update band | the spine | **committed** |
| The free instruments: rejection and quote-gate rates per stage and tier, cost per stage, duplicate mints per unit, unit-versus-abstract agreement | from receipts and packages | **committed** |
| The dataset and the two-stage method, with measured limits | in hand | **committed** |
| The merge-free tree as a design position, with its query-time cost measured on the LongMemEval arm | needs the global layer | **committed** |
| GraphRAG-Bench: three arms over the 20 novels against the nine published baselines | needs Step 1 over the novels plus the same harness | **stretch**: built only if the store and retrieval land by October 25 |
| The resolution ablation (co-occurrence off) | the signal now nominates pairs inside a document only; the up-edge does not exist | **cut**, restated as attachment accuracy on Oz if the alias set is written and Oz is ingested; otherwise reported as an instrument |
| NarrativeQA | secondary | **cut** |
| The wiki (Tip and Ozma, Holmes, Helen pages; assembled versus generated) | the visible artifact | **cut from the fall paper**; one assembled entity page from `render_package.py` if a spare hour appears, for the symposium board |
| The cells ablation | chats have no cells | **cut** |

Reasoning: 33 to 46 build hours remain (section 7); the spine costs 24 to 34; nothing else fits
beside it. The August calibration named exactly this reach: ingest and organize plus one
comparison.

## 2. What the spine needs, in build order

Each step names its input, its output, its hours, and the gate that says it is done. Every step
runs on one LongMemEval history first (`gpt4_2ba83207`, 53 sessions, four answer sessions
dated), because a path that answers one question end to end is what every later number runs
through.

### Step 2a. The store (4 to 6 hours)

- In: the packages of the 1.8 run (`packages/longmemeval/<history>/<session>/`).
- Out: one SQLite file per graph, built from packages by one script: tables for document, unit,
  piece, node, alias, fact, abstract, cell, contradiction, with FTS5 over abstract text, cell
  text and fact quotes; every quote re-resolved from its offsets at load and the load refused on
  the first mismatch. The scope rule: a graph is one history folder, selected by `source_uri`
  prefix (ruling of 09-13).
- Gate: the store built from the 53 packages; every fact's quote slices to its text; row counts
  equal the packages' completion records.

### Step 2b. The global layer, first cut (6 to 10 hours)

- In: the store's document-local nodes.
- Out: a `parent` table (id, name, kind, abstract) and an `instance_of` edge per node, owned by
  the node's document. First cut: nodes unite under one parent when their case-folded name and
  kind agree; a shared name with a kind conflict stays apart and is logged as a candidate; no
  judge yet. The parent's name is its most frequent child name; its abstract is the count
  sentence ("appears in N sessions as a K") until a fold is written. Every edge carries its
  reason. This is the ruling-1 signal question of the 09-08 plan made concrete: log what an
  attach decided on, so a stronger signal can be replayed later.
- Gate: the four answer sessions' subjects (the stores and amounts of the grocery question) sit
  under one parent each; the candidate log lists the conflicts; no parent asserts a fact.

### Step 2c. Retrieval and context (6 to 8 hours)

- In: the store, a question.
- Out: `retrieve(question, history) -> context`: FTS5 over abstracts, cells and fact quotes, the
  hits expanded through their parent to sibling facts, each item rendered by one deterministic
  function with its document date, packed greedily whole-item by rank within a token budget;
  `answer(question, context)` on Luna; the routing and admission log per question (BUILD.md's
  "never a candidate" versus "cut by the budget"). Facts are served with their dates and, on a
  functional predicate, the later fact first; the predicate list is the ruling in 4.3, and until
  it exists every fact is served and the model chooses.
- Gate: the grocery question answered correctly from the store, with the four stores and amounts
  in the returned context and nothing from outside the history.

### Step 2d. The harness (6 to 8 hours)

- In: `longmemeval_s.json` (questions, `question_date`, answers, `answer_session_ids`), the
  store per history.
- Out: three arms over N histories: full-context (every session of the history in the window,
  the parity arm), flat retrieval (FTS5 over raw turns, no store), ThreadAtlas (2c); a judge on
  Terra with the benchmark's answer, calibrated on thirty hand-labeled items first; per-question
  cost and token counts per arm; the knowledge-update band reported with its denominator.
- Check in the first hour: whether gpt-4o-mini is callable. If yes, the parity arm reproduces
  Zep's 55.4 full-context baseline on the original `_s` before anything else is claimed. If no,
  every number is a ratio between the three arms and Zep's table is cited as context only.
- Gate: the 14 known questions scored by the judge on all three arms; the judge agrees with the
  thirty hand labels at 0.7 kappa or better.

### Step 2e. Scale and variance (Kaggle time, few build hours)

- Step 1 over 50 histories first (about 2,400 sessions, $11, 5 hours of kernel time), then all
  500 in four or five 12-hour sessions with the previous output attached (about $107, 48 hours
  of kernel time), during the exam block.
- The three arms over every history ingested; the band from three reruns of one 50-history
  subset.
- Gate: one stated run over the largest set that completed, with the band, by October 25.

### Step 2f. Instruments (2 hours)

- One script over receipts and packages: rejection categories per stage and tier, quote-gate
  rate, cost per stage per document kind, duplicate parents per history from the candidate log,
  agreement between unit summaries and the session abstract where both exist.

### Stretch: GraphRAG-Bench (8 to 12 hours plus its ingest)

Only if 2a to 2d are green by October 25. Step 1 over the 20 novels (already in the 1.8 export,
480 units; tens of dollars), the same store and retrieval, the benchmark's own 2,010 questions
and scorer, the plain-RAG parity check at 879 tokens a question.

## 3. Calendar

| week | dates | hours | build | write | gate |
|---|---|---|---|---|---|
| 1 | Sep 14 to 20 | 8 | read the 1.8 run; 2a on one history; 2b first cut; the grocery question through 2c | the addendum to Dr. Fang; the endorsement email if unsent | **Sep 16**: the store and the first-cut parents exist on one history. **Sep 20**: one question answered end to end, or the floor paper is declared |
| 2 | Sep 21 to 27 | 8 | 2c finished; 2d on the 14 questions; the thirty judge labels; the gpt-4o-mini check | nothing | **Sep 27**: the 14 questions scored on three arms |
| exams | Sep 28 to Oct 18 | 0 to 8 | Kaggle only: Step 1 over 50 histories, then all 500, unattended | the results-independent skeleton: introduction, related work from `reading/related-work/`, method (the two stages, the tree), dataset, contamination; the ASKS comparison and the tree search (2 hours of reading) | **Oct 18**: skeleton drafted; packages for at least 50 histories on disk |
| 3 | Oct 19 to 25 | 8 | 2e: the arms over every history ingested; the band; 2f | tables slotted as they land | **Oct 25**: the LongMemEval number and the band exist |
| 4 | Oct 26 to 31 | 8 | GraphRAG-Bench if green; else the knowledge-update band analysis and the query-time cost of the tree | results section | **Oct 31: build stop** |
| 5 | Nov 1 to 8 | 8 | none | full draft to Dr. Fang by Nov 3; Zenodo record prepared | **Nov 3**: draft sent |
| 6 | Nov 9 to 15 | 8 | none | revise on comments; DOI by Nov 10; freeze Nov 15 | **Nov 16**: arXiv cs.CL |

Two release valves, decided at the gates, never later: if Sep 20 fails, the paper is the floor
(dataset, method, instruments, the tree as a position) and weeks 3 and 4 go to the instruments
and the writing; if Oct 25 fails, the number is reported on whatever subset completed with its
denominator stated.

## 4. Rulings the plan needs, one at a time

1. The slate in section 1.
2. The scope rule is ruled (one history per graph); the first-cut attach rule in 2b (case-folded
   name and kind) needs a yes, since it is the up-edge signal the paper will describe.
3. The functional-predicate list for the knowledge-update band, or the rule that every dated fact
   is served and the model chooses. Recommendation: the second for the fall, the list named as
   spring work; state the denominator either way.
4. Whether Oz is ingested and the alias set written this fall (1 hour of labels, plus the three
   Oz packages that already exist). Recommendation: no, unless week 2 finishes early; it is the
   symposium's fixture, not the paper's number.
5. The paper's authorship sentence (section 4.6 of the audit).

## 5. Mechanics with lead time

- The arXiv cs.CL endorsement: status unknown since 09-08. Ask this week.
- What IT 494 grades (report, presentation, symposium board): not recorded. Ask this week.
- The addendum to Dr. Fang: the corpus as it is, the slate, the milestone slip, the authorship
  sentence. One page, with the next weekly.
- Zenodo DOI for the Step 0 dataset by Nov 10; the Kaggle dataset stays the working copy.
- Kaggle housekeeping (questions 3 and 4 of `log/2026-09-13/questions.md`): the stale units
  dataset marked superseded, the private papers dataset deleted, the Step 0 docs republished.

## 6. Risks, and what each does to the plan

| risk | effect | answer |
|---|---|---|
| the 8-hour week is really 4 | the spine slips a week; GraphRAG-Bench is gone | verify against week 1's real hours; re-price on Sep 20 |
| gpt-4o-mini is not callable | no parity with Zep; ratios only | check in the first hour of 2d; say so in the paper |
| the 1.8 Step 1 run fails or its packages differ from the 1.7 runs | week 1 starts with a debug | the run is in progress; read its receipt first thing |
| Kaggle 12-hour sessions and resume | the full ingest takes five sessions across the exam block | the 50-history subset is the fallback and is enough for a number |
| the judge disagrees with the labels | the scoring design changes (a second judge, or exact-match where the benchmark allows) | the thirty labels are the first thing in 2d |
| the first-cut attach unites wrong things (homonyms in one history) | the candidate log shows it; the kind conflict rule catches the measured case | log every attach with its reason; re-point, never rewrite |
| the exam block yields no writing hours | November is results and writing together; the review window shrinks | the skeleton is the one thing the exam block must produce; two evenings |

## 7. Feasibility tracker

Update weekly: real hours, what landed, the re-priced remainder. The build stop does not move.

| week ending | planned hours | real hours | landed | remaining build (priced) | note |
|---|---|---|---|---|---|
| Sep 13 | | | Step 0 1.8; Step 1 frozen; the cleanup | 24 to 34 for the spine; 8 to 12 stretch | baseline |
| Sep 20 | 8 | | | | |
| Sep 27 | 8 | | | | |
| Oct 18 | 0 to 8 | | | | |
| Oct 25 | 8 | | | | |
| Oct 31 | 8 | | | | build stop |
| Nov 8 | 8 | | | | draft to Fang |
| Nov 15 | 8 | | | | freeze |
