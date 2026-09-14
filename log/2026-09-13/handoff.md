# Handoff to the global-merge thread, 2026-09-13

Read in this order, nothing else is needed: `docs/execution-plan.md` (the chain, the calendar,
the ten rulings still open), `docs/rulings.md` (every ruling, latest line wins), `SCHEMA.md` and
`BUILD.md`, `docs/entity-resolution.md` (the settled section: the tree, the class-and-instance
framing, what the parent holds), `docs/ingestor.md` (the package records), then
`log/2026-09-13/academic-audit.md` sections 4 and 7 for what the paper needs from you.

## Where things stand

- Step 0 1.8 is published; Step 1 1.7 is frozen and its first run on the 1.8 export finished
  tonight: 81 packages, $5.49, in per-history folders, downloaded to `%TEMP%/fr18/packages`
  (53 sessions of history gpt4_2ba83207, 18 answer sessions of 13 other questions, 3 Oz books,
  5 papers, one Greek play, one GraphRAG-Bench novel). These are your test input. The 1.8
  export itself is at the a3b08f2d scratchpad `dates/kout18/export` and on Kaggle.
- The repository holds only what a person reads; tooling (the battery under `tests/ingestor/`,
  `tests/check_flex_run.py`, `tests/verify_export.py`, `archive/`) is on disk, untracked. One
  thread does git; hand your commits to it or take that role explicitly.
- The paper goes to the ECIR 2027 resource track on Nov 2; build stop Oct 25; first draft
  mid-October. Every week is priced in the plan's section 8; put real hours in on Sundays.

## The chain you are building, in order (ruled 09-13)

1. **The global layer, design note first (one page), then the first cut.** What a parent is
   (name, kind, abstract, nothing asserted); what draws the up-edge: case-folded name and kind,
   then co-occurrence (the cast the child appears beside, against the cast the parent's children
   appear beside), both scores logged per candidate so the attachment can be replayed name-only
   and name plus co-occurrence; a shared name with a kind conflict stays apart and is logged;
   every edge carries its reason; a graph is one history folder or one novel, by `source_uri`
   prefix. The same graph, documents joined by shared parents weighted by co-occurrence, is what
   clusters documents for the wiki pages. Gate: a hand check of 30 parents with the wrong-unite
   and wrong-split counts.
2. **The store**, to the schema the global layer decides: SQLite, one file per graph, built from
   packages, FTS5 over abstracts, cells and fact quotes, every quote re-resolved from offsets at
   load. Fix the 8-character `doc_tag` collision here.
3. **The embedding sidecar**: bge-small-en-v1.5 through fastembed, one vector per sentence of
   cells and abstracts and one per fact quote, keyed by record id, brute-force cosine, rebuildable.
4. **The query path**: FTS5 and vectors fused, expansion through parents, whole items rendered
   with their dates, greedy packing; every dated fact served, no supersession mechanism.
5. **The harness**: each benchmark's own questions and evaluator (GraphRAG-Bench's scorer; the
   LongMemEval evaluator prompt); arms no-context, flat, full system, and full system with the
   parent join off; the 14 tuning questions excluded; one reader model per benchmark; check in
   the first hour whether gpt-4o-mini is callable, and write the full-context truncation rule.
6. Only then the full data, in Kaggle batches, after 2e's fixes (one JSONL per history in the
   output; the block budget).

Gates: Sep 20, parents, store and vectors over the test packages and the schema written down;
Sep 27, the harness runs a question end to end on a novel and on the history. The Oz alias set
(one hour of labels over the three Oz packages) is written in week 2.

## Rulings to bring Justin, one at a time, with a recommendation

The plan's section 5: the reader model; the benchmark's own evaluator with a 30-verdict hand
check; the dev-set exclusion; no supersession claim this fall; the first-cut attach rule and its
gate; the Kaggle output shape and budget; a tracked `tests/` with the three verification scripts;
whether the one-semester form was filed; the authorship sentence. And from `questions.md`: a root
LICENSE (MIT recommended) and the NarrativeQA CSVs.

## Rules that bit this fortnight

Logs are snapshots, never edited; the masters and `docs/rulings.md` carry truth; write the day's
log on the day. No em dashes anywhere; no copyrighted modern fiction named in public files; no
lambdas in drafted code. One question at a time, with what it contains and what each answer does.
A ruling stands; a rejected idea does not come back.
