# The global layer, 2026-09-14: the Step 1 dataset, two reviews, three rulings

Continues `log/2026-09-13/global-layer.md`.

## The Step 1 dataset

Published early on 09-14 as `jhffmn/it494-threadatlas-step1`, public: the 1.8 run's 81 packages
regrouped one file per record type by `scripts/pack_step1_public.py`, every row keyed by the full
document hash, every one of the 6,576 quotes sliced from the Step 0 export at its offsets before
upload, all matching. Documented in `dataset/step1/` (README, SCHEMA, METHOD, PROVENANCE, LIMITS,
metadata) as the test set, not the corpus. Justin ruled the global thread pushes it itself.

## The pseudocode and two adversarial reviews

The thread gave Justin the pipeline as pseudocode (build: load, embed, chat salience call,
nomination, judge, found or attach, parent rewrite; score against the key; retrieve: two scans,
one hop, rerank, pack). Two reviewers who had the project but not the night's discussion read it.
Taken, with the thread's answer where it differed:

- An offer floor before the judge (both reviews): without it every child after the first is judged,
  about $4 at test size and $600 at the corpus. Taken.
- The document filter at every hop and on summary lines (review 1): without it a LongMemEval
  context leaks other users' sessions. Taken as a validity rule.
- The judge sees texts, not scores, so verdicts replay (review 1). Taken, with the parent's
  version logged beside each verdict.
- Identity facts point at parents that may not exist yet (both): taken as a second pass over
  founders after every package is loaded; the `object_is_node` link replaces any predicate list.
- Cap the expansion; case-fold casts; process children by first unit; atomic row map (review 1).
  Taken.
- Entity-only prefix on sentences (review 1): half taken; a book or paper title stays, a session
  id goes.
- Re-ingest of a changed package is spring; deletion's twin measurement (review 1). Taken.
- The key's matching step reported (review 1). Taken.
- Graph scope should be one history (review 2): declined; Justin ruled one graph over everything
  on 09-13, the one-history rule is a retrieval filter, and the leak is closed by the filter rule.
- Ablation arms as full rebuilds (review 2): half taken; the replay is the screen, rebuilds give
  the number, and only over the scored subset (below).
- FTS5 and dates missing from the pseudocode (review 2): omissions, taken; both were in the note.
- The 30-parent hand check (review 2): already in the note; the scorer writes the sample.

## Ruled by Justin, 09-14

1. Two entities of one document are never offered to each other as a pair; each is offered
   parents and both may land under the same parent, in the first pass or the second.
2. Packages are ingested in order (date, then `source_uri`), and the solution must handle
   documents arriving out of order.
3. The ablation is built into the pipeline as arms, tested on chosen test sets later, not over
   the entire corpus; which sets is a later ruling.
4. "The real test is going to be grouping document clusters accurately." The thread recommended
   LongMemEval's multi-session questions as the cluster gold (their answer sessions form labelled
   clusters inside a history). Justin: "let's revisit that because I am not sure right now."
   Parked, open.

The design note carries these as its amendments section.

## Built the same night (the thread runs local code from here on, at Justin's word)

- `threadatlas/store.py`: the store from the Step 1 dataset folder and the Step 0 text. Run:
  81 documents, 6,576 quotes checked, all slice to their text; FTS5 built; facts and cells per
  document equal the completion records. The whole schema is declared there, including the
  parent, up-edge, offer, leaf and sidecar tables the later steps fill.
- `threadatlas/embed.py`: the sidecar, bge-small-en-v1.5 through fastembed, float16 `.npy`
  beside the store, row map and header inside it in one transaction. Run: 12,876 vectors
  (6,576 fact lines, 3,861 cell sentences, 2,439 abstract sentences); rebuilt twice with the same
  bytes; a scan of the Tip question puts the book 2 Tip abstract and cells first.
