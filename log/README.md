# Working log

One folder per entry: what was done, where it is, what it showed, with the notebooks and
their saved outputs as run. Each entry is a snapshot of its day and is never edited; current
truth is in the master documents and `docs/rulings.md`. On 2026-09-13 the test, repro and
review scripts that had sat beside the entries left the public tree (they stay on the author's
machine), so a script an entry names may no longer be in its folder.

- [2026-09-02](2026-09-02/README.md): corpus published; Oz book 1 ingested end to end
  (entities, quote-backed facts, bottom-up reconciliation, predicate consolidation, store,
  graph, abstracts); results and next steps.
- [2026-09-03](2026-09-03/README.md): design session, no code; merge candidate rule and
  disambiguation, raw text layer, retrieval and engine architecture, preprocessor rebuild and
  dataset list, proposed schema additions for ruling, pick-up checklist for the PC.
  Plan: [plan.md](2026-09-03/plan.md), a deficiency review of both notebooks and a step-by-step
  build plan with tools, acceptance tests, sizes, and how users feed it documents.
  Search: [claim-search.md](2026-09-03/claim-search.md), adversarial prior-art search on the
  voice-lineage collision rule; verdict partially occupied, two measurements survive.
- [2026-09-04](2026-09-04/README.md): merge walkthrough after ingestion; community grouping
  removed; document-level salience at the end of ingestion; documents as entities; the
  document holds its text once and units are ranges; the Step 0 inventory and Justin's
  twelve rulings (the extractor sees raw files and nothing else); the extractor chat's
  build and its two date findings (units carry a time range, a day cut); an outside design
  review verified and ruled (voice on the piece, minors stay mentions, two instruments);
  the living docs corrected; a review of the extractor notebook and the proposed rewrite of
  its model path.
  Inventory: [inventory.md](2026-09-04/inventory.md), every source audited, what the brief
  had wrong or missing, the twelve rulings.
  Brief: [step0-brief.md](2026-09-04/step0-brief.md), the extractor chat's opening message.
  Code: `threadatlas_blocks_3_to_9.py` (untracked since 09-13), candidate-index
  selection, gates, one unit rule, piece-table export; proposed, not yet applied.
- [2026-09-05](2026-09-05/README.md): the extractor's wrong turn found (quote matching,
  chunking) and the rebuild under the day's rulings: the model decides every boundary over
  the whole numbered document, every byte kept, regions as labels, units grouped and split
  by the model, no piece dates, no inferred dates; the old design's first full run analysed;
  a 63-agent review and the fix batch; Kaggle import, CLI, and secret notes; open items.
  Review: [review.md](2026-09-05/review.md), the confirmed findings consolidated and the
  measured cost of the run. Docs: `docs-rulings-2026-09-05.patch` (untracked since 09-13),
  the SCHEMA.md and BUILD.md sentences drafted for correction. The old run's log and records
  as `old-design-run.*`; the offline checks as `test_review.py`, `test_verify.py` and `test_run1.py`, and
  `py_to_ipynb.py`, which builds the notebook from the script and checks the round trip.
- [2026-09-06](2026-09-06/README.md): two threads, both kept.
  [extractor.md](2026-09-06/extractor.md): 1.0 to 1.5 and the clean whole-corpus pass, 19,436
  documents, 44,262 units, 227,100 pieces, $7.72, verified against the schema and the text.
  [ingestor.md](2026-09-06/ingestor.md): the document ingestor built in twelve blocks against
  the schema, the quote gate returning classified rejections, within-document reconciliation, a
  six-lens review with 32 findings applied, a 70-check battery.
  Audits: [audit.md](2026-09-06/audit.md) for the ingestor,
  [audit-extractor.md](2026-09-06/audit-extractor.md) for the extractor.
  Decisions: [decisions-ingestor-0.5.md](2026-09-06/decisions-ingestor-0.5.md).
- [2026-09-07](2026-09-07/README.md): the dataset published and then corrected, the ingestor
  audited twice, and the entity design settled. Step 0 shipped
  [ThreadAtlas Step 0](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step0) with five
  documentation files kept in `dataset/step0/` and a packer that reproduces every published
  file byte for byte; seventeen errors in that documentation were then found and fixed, the
  worst being that the README credited a model with finding boundaries in 98.8 percent of a
  corpus it never saw. The ingestor was audited at 0.6 (18 findings surviving a refuter), at
  0.7, and again at 0.8 before its first run. A LongMemEval re-export was asked for, measured,
  and correctly withdrawn once the arithmetic showed grouping does not pay.
  Rulings: [decisions-ingestor-0.7.md](2026-09-07/decisions-ingestor-0.7.md) and
  [audit-answers.md](2026-09-07/audit-answers.md).
  The ingestor thread of the same day is [ingestor.md](2026-09-07/ingestor.md) (0.6 to 0.8 and
  the one-reading path), with [decisions-ingestor-0.8.md](2026-09-07/decisions-ingestor-0.8.md)
  and [build-0.8-worklist.md](2026-09-07/build-0.8-worklist.md); the notebook as run is
  `threadatlas-ingestor-as-run.{py,ipynb}`. Merged to master 2026-09-08.
  Design: the scope question in [entity-resolution.md](../docs/entity-resolution.md) is settled.
  Nothing is ever merged; it is a tree. A parent holds no asserted content, only derived fields
  (a name, a kind and an abstract since the profile was dropped on 09-09), and every sentence on it
  must be reducible to "N of M children say X".
  Insertion becomes append-only, deletion becomes a delete, and provenance becomes total.
- [2026-09-08](2026-09-08/README.md): the housekeeping pass after the tree decision, three reviews,
  and the forward plan. Housekeeping: master fast-forwarded 137 commits, the ingestor 0.9 notebook
  synced, SCHEMA/BUILD brought level with the code and stripped of changelog meta, docs/extractor.md
  and docs/ingestor.md written. [review.md](2026-09-08/review.md) (drift and schema, ten rulings),
  [publishability-review.md](2026-09-08/publishability-review.md) (scope, rigor, feasibility, the
  reviewer's ten questions), [forward-plan.md](2026-09-08/forward-plan.md) (the execution timeline,
  build and write tracks on one calendar). [wiki-projection.md](2026-09-08/wiki-projection.md)
  (Justin's design note: the wiki as a projection of the retrieval structure, the related-work score). [threadatlas-decision.md](2026-09-08/threadatlas-decision.md) (the rename to ThreadAtlas and the narrative-cell / portal architecture direction, from the 9 Sep project review).
- [2026-09-09](2026-09-09/README.md), written 09-13 from the commits: the rename applied to every
  artifact; the profile record dropped and the pair score renormalised; the 100 CC-BY papers
  replacing the private mount, `attribution.jsonl` replacing `papers.jsonl`, raw dataset v3; fold-09
  onto master and the ruling that block 13 runs three Oz books; the Step 0 docs rewritten twice and
  the 1.6 version published; the two rulings (`occurred_until` dropped, a chat's title is its
  session id); the weekly report to Fang.
- [2026-09-10](2026-09-10/chat-rulings.md): the chat design ruled wrong and rebuilt one question at a
  time (a session is a document titled by its session id, a turn is a unit), with the LongMemEval
  measurements behind it; [decisions-ingestor-1.7.md](2026-09-10/decisions-ingestor-1.7.md), the
  Step 1 rulings (`valid_to` dropped, chats on the full path, block 12 one whole history);
  [step0-changes-since-factledger-1.5.md](2026-09-10/step0-changes-since-factledger-1.5.md), the
  counted diff of Step 0 1.5 to 1.7. Extractor 1.7 ran and was published that day.
- [2026-09-11](2026-09-11/README.md), written 09-13: the first full Step 1 run read (63 documents,
  $15.68), the audit answered, twelve rulings (minor-subject facts not stored, six answer sessions
  added, the Flex tier with the judge and fold on Luna for chats, the complexity audit approved,
  the six chat edits confirmed as rulings, skipped flagged facts dropped), the prune steps built,
  the Flex run started.
- [2026-09-12](2026-09-12/README.md), written 09-13: the Flex run read (chats $0.020 a session),
  seven rulings ending in a chat read in one Luna call per session and Step 1 frozen, the two
  chats-only test runs (all 14 answer questions stored at $0.0045 a session).
- [2026-09-13](2026-09-13/README.md): the frozen full run on 1.7; the dates rebuild and extractor
  1.8 (every unit dated, LongMemEval unpacked per history, 24,071 documents, $8.24, published); git
  caught up with everything since fa48997; the first Step 1 run on 1.8; the repository cleanup.
  [project-state.md](2026-09-13/project-state.md) is the audit of what exists and what is
  verified; [academic-audit.md](2026-09-13/academic-audit.md) reviews the proposal and measures
  the project against Justin's goals; [questions.md](2026-09-13/questions.md) the rulings left
  open by the cleanup. The plan that follows from the audit is `docs/execution-plan.md`. Scripts:
  `check_flex_run.py` (the Step 1 answer check) and `extractor/` (the 1.8 build and verification).
- [2026-09-14](2026-09-14/global-layer.md): the global layer built as a batch (bottom-up clustering
  with a judge, parents written once, the mentions pass, collections, the wiki); ingestor 1.8 run
  and published as the Step 1 dataset ([ingestor-1.8.md](2026-09-14/ingestor-1.8.md), the note
  to the ingestor thread).
- [2026-09-15](2026-09-15/global-layer.md): the wiki settled (slate scheme, breadcrumb, the portal
  by relevance), the lean serving store, retrieval built; [retrieval.md](2026-09-15/retrieval.md)
  is the query-path manual as proposed and approved with seven corrections (the master is
  `docs/retrieval.md`); [documentation-review.md](2026-09-15/documentation-review.md) reviews
  every master against the code and the rulings.
