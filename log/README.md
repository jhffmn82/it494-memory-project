# Working log

One folder per entry: what was done, where it is, what it showed, with the notebooks and
their saved outputs as run.

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
  Code: [factledger_blocks_3_to_9.py](2026-09-04/factledger_blocks_3_to_9.py), candidate-index
  selection, gates, one unit rule, piece-table export; proposed, not yet applied.
- [2026-09-05](2026-09-05/README.md): the extractor's wrong turn found (quote matching,
  chunking) and the rebuild under the day's rulings: the model decides every boundary over
  the whole numbered document, every byte kept, regions as labels, units grouped and split
  by the model, no piece dates, no inferred dates; the old design's first full run analysed;
  a 63-agent review and the fix batch; Kaggle import, CLI, and secret notes; open items.
  Review: [review.md](2026-09-05/review.md), the confirmed findings consolidated and the
  measured cost of the run. Docs: [docs-rulings-2026-09-05.patch](2026-09-05/docs-rulings-2026-09-05.patch),
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
  [FactLedger Step 0](https://www.kaggle.com/datasets/jhffmn/it494-factledger-step0) with five
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
  `factledger-ingestor-as-run.{py,ipynb}`. Merged to master 2026-09-08.
  Design: the scope question in [entity-resolution.md](../docs/entity-resolution.md) is settled.
  Nothing is ever merged; it is a tree. A parent holds no asserted content, only a derived name,
  profile and abstract, and every sentence on it must be reducible to "N of M children say X".
  Insertion becomes append-only, deletion becomes a delete, and provenance becomes total.
- [2026-09-08](2026-09-08/review.md): the housekeeping pass after the tree decision, three reviews,
  and the forward plan. Housekeeping: master fast-forwarded 137 commits, the ingestor 0.9 notebook
  synced, SCHEMA/BUILD brought level with the code and stripped of changelog meta, docs/extractor.md
  and docs/ingestor.md written. [review.md](2026-09-08/review.md) (drift and schema, ten rulings),
  [publishability-review.md](2026-09-08/publishability-review.md) (scope, rigor, feasibility, the
  reviewer's ten questions), [forward-plan.md](2026-09-08/forward-plan.md) (the execution timeline,
  build and write tracks on one calendar). [wiki-projection.md](2026-09-08/wiki-projection.md)
  (Justin's design note: the wiki as a projection of the retrieval structure, the related-work score). [threadatlas-decision.md](2026-09-08/threadatlas-decision.md) (the rename to ThreadAtlas and the narrative-cell / portal architecture direction, from the 9 Sep project review).
