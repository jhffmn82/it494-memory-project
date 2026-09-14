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

## Later on 09-14: ingestor 1.8, the Step 1 dataset's version 2, the notebook build

- The ingestor thread's 1.8 run (all 81 documents, $5.47, 1,784 calls, about 2.8 kernel hours)
  replaced the 09-13 packages. Verified here: 81 complete packages, 324 quote-less document
  facts (title, author, date, source class, history), 1,113 `mentioned` facts, 0 `thing` kinds,
  643 chat entity nodes (from 1,061), 53 chat kinds.
- The packer and the store skip the quote check on a document fact and prove every other quote:
  6,605 checked, all slice. `dataset/step1/` rewritten for 1.8 (version 2 of the dataset), pushed
  to `jhffmn/it494-threadatlas-step1` at Justin's word.
- The store and the sidecar rebuilt from version 2: 6,929 facts, 13,330 vectors. The embedder
  renders a `mentioned` fact with the minor's name as its subject.
- The global layer's own chat salience call was removed from `threadatlas/attach.py`; Step 1
  carries salience now.
- `scripts/build_global_layer_notebook.py` assembles `notebooks/threadatlas-global-layer.ipynb`
  from the four modules (model, embed, store, attach) plus a run cell, for Kaggle with the two
  datasets attached and an `OPENAI_API_KEY` secret; pushed as the kernel
  `jhffmn/threadatlas-global-layer` (private) so the attach step can run where the key is.
- The as-run 1.8 notebook and its receipt are under `log/2026-09-14/ingestor/`; the notebook
  and its script form replaced `notebooks/threadatlas-ingestor.*`.
