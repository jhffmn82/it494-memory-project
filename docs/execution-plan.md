# Execution plan: from the 1.8 packages to the paper

PROPOSED 2026-09-13, revised the same night after an adversarial review of its first draft
(`log/2026-09-13/attack-assessment.md`); until Justin rules on the slate in section 1. Replaces
the 09-08 forward plan (`log/2026-09-08/forward-plan.md`). Feasibility is tracked in section 8
and is re-priced weekly with real hours. The audit behind this plan is
`log/2026-09-13/academic-audit.md`.

## 1. The slate (the ruling this plan needs first)

Two benchmarks are on the table. What each costs on the path from the 1.8 packages:

| | GraphRAG-Bench | LongMemEval |
|---|---|---|
| ingest | Step 1 over the 20 novels: 480 units on the full path, tens of dollars, one Kaggle session | Step 1 over chats: $107 and about 48 kernel hours for all 500 histories, or a subset |
| graph | one document per graph, so no global layer is on its path | one history per graph; needs the first-cut global layer (2b) |
| questions and scoring | 2,010 questions with gold answers and evidence, the benchmark's own scorer, nine published baselines under gpt-4o-mini | 500 questions, the benchmark's own GPT-4o evaluator prompt, Zep's published numbers under gpt-4o-mini and gpt-4o |
| judge to build | none | none if the benchmark's evaluator is used as published |
| what it tests of the design | retrieval over cells, facts and abstracts of a book; contamination answered (pre-1900) | retrieval over facts and session abstracts of a chat history (chats have no cells); the benchmark is public since 2024 and inside the model's training window |
| standing with the advisor | the first committed measurement in the filed proposal | a stretch item in the filed proposal, the spine of the last four days' build |

**Ruled 2026-09-13 (Justin, evening):** the global layer is built regardless of which benchmark
needs it, and it comes first because the database schema and the embedding follow from it. The
chain is: the global layer; then the store schema and the embedding sidecar it implies; then the
query path; then a harness that runs the tests against the query path; and only when each has a
solution, the full data, digested in Kaggle batches (about 36 kernel hours for all chats by the
Step 1 thread's estimate, less on the version now running; the other corpora are much smaller
and go first). Until the harness passes, every step works on the test packages already on disk:
the 71 sessions, three Oz books, five papers, the Bacchae and Dandy Dick of the frozen run, and
their 1.8 counterparts when that run lands. Testing begins by the end of September so October is
refinement and dataset building. Both benchmarks stay. Which is scored first is a
sequencing choice, not a slate choice: GraphRAG-Bench needs no global layer and has its own
scorer, so it can be scored the week the query path works; LongMemEval scores as its batches
land. Cut from the fall: NarrativeQA, the wiki, the cells ablation, the resolution ablation (its
signal nominates pairs inside a document; the up-edge it would have measured does not exist).
Reported as instruments, not results: rejection and quote-gate rates, cost per stage and tier,
duplicate parents per history from the candidate log.

The three-tier pilot the filed proposal promised (goal 4, model sensitivity as a result) is not
in this slate; it returns only if the reader-model ruling in section 5 allows a second tier on
one arm.

## 2. What the spine needs, in build order

Prices are revised upward from the first draft, which had halved the 09-08 estimates with no
build in between. Each step names its input, output, hours and gate. The order is the ruled
chain: 2b (global) first, then 2a (the store, whose schema the global layer decides) and 2b2
(embedding), then 2c (query), then 2d (the harness), then 2e and 2f (the full data). The
section numbers are kept from the first draft so the attack reports still read.

### 2a. The store (6 to 10 hours; built after 2b, to the schema 2b decides)

- In: the packages of the 1.8 run.
- Out: one SQLite file per graph, built by one script: document, unit, piece, node, alias, fact,
  abstract, cell, contradiction; FTS5 over abstract text, cell text and fact quotes; every quote
  re-resolved from its offsets at load, the load refused on the first mismatch. A graph is one
  document for GraphRAG-Bench and one history folder (by `source_uri` prefix) for LongMemEval.
- Gate: a store built from one novel's package and from history gpt4_2ba83207's 53 packages;
  every quote slices to its text; counts equal the completion records.

### 2b. The global layer, first cut (8 to 12 hours; the first step)

- In: the test packages on disk (one history's 53 sessions plus the answer sessions, three Oz
  books, five papers, two plays and novels), read straight from their JSONL.
- Out (the design output, before any code): what a parent is, what draws the up-edge, what a
  parent's name and abstract are computed from, and what the store must hold to answer a
  question through a parent. That decides the store schema in 2a and what gets embedded in 2b2.
- Out (the code): a `parent` table (id, name, kind, abstract) and an `instance_of` edge per node, owned by
  the node's document. First cut: nodes unite under one parent when their case-folded name and
  their case-folded kind string agree; a shared name with a kind conflict stays apart and is
  logged as a candidate; every edge carries its reason. The parent's name is its most frequent
  child name; its abstract is the count sentence until a fold is written. Kind is an open
  vocabulary, so near-synonym kinds will split parents; the split count is an instrument.
- Gate (one that can fail): a hand check of 30 parents drawn at random from the history, with
  the wrong-unite and wrong-split counts recorded; and a second arm in 2d that runs the same
  retrieval with the parent join switched off, so what the tree buys is measured rather than
  asserted.

### 2b2. The embedding sidecar (3 to 5 hours)

- Out: `bge-small-en-v1.5` through fastembed (384 dimensions, ONNX, CPU, fetched once), one
  vector per sentence of every cell and abstract and one per fact quote, in a sidecar keyed by
  record id, sentence ordinal and model name, with a header (model, dimension, built at);
  brute-force cosine at this scale; the store never depends on it and a header mismatch
  rebuilds. `embed(texts)` becomes the second interface BUILD.md names.
- Gate: the sidecar rebuilt from the store byte for byte twice; the row map verified against
  ids on load.

### 2c. Retrieval and context (8 to 10 hours)

- Out: `retrieve(question, graph) -> context`: FTS5 and the sentence vectors over abstracts,
  cells and fact quotes, fused by rank, hits expanded through their parent to sibling facts
  where a parent exists, each item rendered by one
  deterministic function with its document date, packed greedily whole-item by rank within a
  token budget; `answer(question, context)` on the reader model of section 5; a routing and
  admission log per question. Every dated fact is served; no read-time supersession is built
  this fall, and the paper says so.
- Gate: the grocery question answered from history gpt4_2ba83207's store with the four stores
  and amounts in the returned context; one GraphRAG-Bench question answered from one novel's
  store.

### 2d. The harnesses

GraphRAG-Bench (4 to 6 hours): the benchmark's questions and scorer as published; arms:
no-context, flat retrieval over raw units, ThreadAtlas; the plain-RAG parity check first (their
58.76 on fact retrieval at 879 tokens). Gate: the three arms scored on one novel.

LongMemEval (8 to 12 hours): the benchmark's `_s` questions, `question_date`, answers and its
own evaluator prompt as published; arms: full-context (every session of the history, with the
truncation rule stated; 429 of 500 histories exceed 120k tokens at four characters a token),
flat retrieval over raw turns, ThreadAtlas, ThreadAtlas with the parent join off. The 14 questions
used to tune Step 1 are a development set and are excluded from any reported number. A question
is scored only over a history ingested whole. The six abstention questions are reported with the
benchmark's rule. Gate: the four arms scored on ten histories held out from tuning.

### 2e. Kaggle changes before any scaled run (2 to 4 hours)

The cost and time figures in this plan ($0.0042 to $0.0045 a session, 36 to 48 kernel hours
for all chats) are from the frozen version's runs of 09-12 and 09-13 on the 1.7 export. Justin
reports the version now running on the 1.8 export is much cheaper and faster; its receipt
replaces these figures the moment it lands, and every batch estimate below scales with it.

- Packages are written two files per document, 48,000 files for all chats; 25,000 output files
  already made one notebook impossible to list or download. Before the full run: one JSONL per
  history (or a zip per block) in the output.
- Block 12 stops at its $15 budget, about 3,300 sessions at $0.0045; the full run needs the
  budget raised and the resume tested across sessions. A 12-hour session at 16 sessions at a time
  ingests about 5,900 sessions, so all 500 histories are four to five sessions and each is a
  manual launch. `CHAT_AT_ONCE` is a constant, not a limit; raising it is a ruling (rate limits
  on Flex are the risk).

### 2f. Scale and variance (Kaggle time; 2 hours of build)

- GraphRAG-Bench: all 20 novels, all 2,010 questions, one stated run; the band from three
  reruns of the questions over one fixed store (the reader's variance) and, if hours allow, from
  three re-ingests of two novels (the pipeline's variance).
- LongMemEval: 50 held-out histories first (about 2,400 sessions, $11, one session); that is a
  pilot, with a standard error near 7 points on a 500-question benchmark, not a positioning
  claim. All 500 only if the exam block's sessions complete. State the denominator.

### 2g. Instruments and tables (4 to 6 hours)

One script over receipts, packages and the candidate log; the paper's tables written from it.

### Debugging, Kaggle friction, downloads (6 to 8 hours)

Priced explicitly because the first draft priced none of it.

## 3. Totals and hours

The design lock (2a, 2b, 2b2, 2c): 25 to 37 hours, all of it before the end of September under
the ruling. The two harnesses (2d), 2e, 2f, 2g and debugging: 26 to 38 more. The paper: 10 to 15 hours, of which the results-independent
skeleton can be written in the exam block.

Hours available at the plan's 8 a week: 16 in weeks 1 and 2, 0 to 8 in the exam block, 32 in
weeks 3 to 6, of which weeks 5 and 6 are writing. So 32 to 40 build hours at the planned pace.
The planned pace is contradicted by the repository's own record (commits on 17 of 22 days from
August 23 to September 13, 55 commits on September 6, Kaggle launches past midnight), so the
real pace is likely several times 8 a week; the plan is re-priced after week 1's real hours and
not before.

At 8 a week the design lock alone takes past September 27. The ruling's target (testing by the
end of September) assumes the measured pace, and the gates below say by Sep 20 whether it holds.

## 4. Calendar

| week | dates | build | write | gate |
|---|---|---|---|---|
| 1 | Sep 14 to 20 | read the 1.8 run's receipt; 2b (the global layer: the design, then the first cut) on the test packages; 2a (the store) to the schema 2b decides; 2b2 (the embedding sidecar) | the addendum to Dr. Fang; the endorsement email if unsent; ask what IT 494 grades | **Sep 20**: parents, store and vectors exist over the test packages, and the schema is written down |
| 2 | Sep 21 to 27 | 2c (the query path) to the first answered question on a novel and on the history; 2d (the harness) on the 14 known questions and one novel, with the parity check; 2e (the Kaggle output shape and budget) | nothing | **Sep 27, the design lock**: the harness runs the tests end to end through store, parents, vectors and query on both corpora; testing can start, and the full data may run |
| exams | Sep 28 to Oct 18 | Kaggle in batches, unattended, only after the Sep 27 gate: the 20 novels, then the chat histories; refinement of the query path on what the batches show, in evenings | the skeleton: introduction, related work, method, dataset, contamination; the ASKS comparison and the tree search first (2 hours of reading) | **Oct 18**: skeleton drafted; the packages on disk; the GraphRAG-Bench arms scored on all 20 novels |
| 3 | Oct 19 to 25 | 2d LongMemEval over every history ingested; 2f the bands | tables as they land | **Oct 25**: both numbers exist, each with its denominator |
| 4 | Oct 26 to 31 | 2g; the parent-off arm; what the batches showed folded into the dataset | results | **Oct 31: build stop** |
| 5 | Nov 1 to 8 | none | full draft to Dr. Fang by **Nov 5** (the first draft's Nov 3 had no writing hours behind it) | draft sent |
| 6 | Nov 9 to 15 | none | revise; DOI by Nov 10; freeze Nov 15 | **Nov 16**: arXiv cs.CL |

Release valves, decided at the gates: if Sep 20 fails, the paper is the floor (dataset, method,
instruments, the tree as a position) and weeks 3 and 4 go to instruments and writing; if Oct 25
fails, the number is reported on the novels that completed with the denominator stated; if
LongMemEval does not reach the pilot, it is reported as ingest cost and the presence check only,
labelled as such.

## 5. Rulings the plan needs, one at a time

1. The slate in section 1.
2. The reader model: one model for every arm of a benchmark. Parity with the published baselines
   needs gpt-4o-mini for both benchmarks; if it is not callable, every number is a ratio between
   your own arms and the published tables are context only. Check before ruling.
3. The evaluator: the benchmark's own published scorer and prompt, not a custom judge; a hand
   check of 30 of its verdicts after the first scored run, as a sanity check, not a gate.
4. The 14 tuning questions are excluded from every reported number; any scored history is
   ingested whole.
5. The knowledge-update band is reported as accuracy only; the paper claims no supersession
   mechanism this fall (every dated fact is served). The functional-predicate list and the
   read-time view are spring.
6. The first-cut attach rule (case-folded name and kind) and its hand-checked gate.
7. The Kaggle output shape (one JSONL per history) and the block budget for the full run.
8. Which verification artifacts are public: the offline battery, the export verifier and the
   answer check left the tree tonight as working tooling, but they are what lets a reader check
   "94 of 94" and "0 quotes off". Recommendation: a tracked `tests/` with those three and
   nothing else, or the same files attached to the Kaggle kernels.
9. Whether the one-semester form was filed (the proposal says it was the remaining paperwork).
10. The authorship sentence, in the paper and in README (which still says "the author writes the
    code").

## 6. Mechanics with lead time

- The arXiv cs.CL endorsement: status unknown since 09-08. Ask this week.
- What IT 494 grades: not recorded. Ask this week, before the addendum, since a report or a
  talk changes November.
- The addendum to Dr. Fang, one page: the corpus as it is, the slate as a question with this
  plan's recommendation, the September 27 milestone slip, the authorship sentence.
- Zenodo DOI for the Step 0 dataset by Nov 10.
- Kaggle housekeeping (questions 3 and 4 of `log/2026-09-13/questions.md`).

## 7. Risks

| risk | effect | answer |
|---|---|---|
| the pace is really 8 a week | LongMemEval is gone; the spine is tight | week 1's real hours re-price the plan on Sep 20 |
| gpt-4o-mini is not callable | no parity; ratios only | check in week 1; say so in the paper |
| the 1.8 Step 1 run fails or its packages differ from the 1.7 runs | week 1 starts with a debug | read its receipt first |
| Kaggle output files and the block budget | the full chat ingest cannot be downloaded or stops early | 2e before any scaled run |
| the benchmark's evaluator disagrees with a hand check | the number carries a caveat, not a fix | 30 verdicts checked after the first run |
| the tree buys nothing on chats (exact-name parents over one user's history) | the tree is a position, not a result | the parent-off arm measures it either way |
| LongMemEval is inside the training window | arm-versus-arm survives; the comparison to Zep's run does not | state it; the pre-1900 novels carry the contamination answer |
| the exam block yields no writing hours | November is results and writing together | the skeleton is the one thing the exam block must produce |
| the advisor wants the filed slate | GraphRAG-Bench first honours it; LongMemEval becomes the stretch he was told it was | the addendum asks, week 1 |

## 8. Feasibility tracker

Update weekly: real hours, what landed, the re-priced remainder. The build stop does not move.

| week ending | planned hours | real hours | landed | remaining build (priced) | note |
|---|---|---|---|---|---|
| Sep 13 | | | Step 0 1.8; Step 1 frozen; the cleanup; this plan | spine 30 to 42; LongMemEval 18 to 28 | baseline |
| Sep 20 | 8 | | | | re-price here |
| Sep 27 | 8 | | | | |
| Oct 18 | 0 to 8 | | | | |
| Oct 25 | 8 | | | | |
| Oct 31 | 8 | | | | build stop |
| Nov 8 | 8 | | | | draft to Fang Nov 5 |
| Nov 15 | 8 | | | | freeze |
