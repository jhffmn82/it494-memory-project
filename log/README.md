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
  document holds its text once and units are ranges in one coordinate system; the Step 0
  inventory and Justin's twelve rulings (the extractor sees raw files and nothing else); the
  extractor chat's build and its two date findings (units carry a time range, a day cut); an
  outside design review verified and ruled (voice on the piece, minors stay mentions, two
  instruments); the living docs corrected; a review of the extractor notebook and the
  proposed rewrite of its model path; the general extractor plan and the all-sources raw
  dataset; open items.
  Inventory: [inventory.md](2026-09-04/inventory.md), every source audited (format, size,
  license, fixtures), what the Step 0 brief had wrong or missing, the twelve rulings.
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
- [2026-09-06](2026-09-06/README.md): the extractor's whole-corpus run landed (19,436
  documents, 44,262 units, loader 1.5, on Kaggle as the kernel's output; a first run's export
  rebuilt locally from its log meanwhile); the document ingestor built against the schema in
  twelve blocks, the quote gate returning offsets with classified rejections, a document
  roster, within-document reconciliation with a scored ledger, the package as one file per
  document, a Kaggle-ready notebook; a six-lens adversarial review before the paid run, 32
  findings confirmed and applied; a 70-check offline battery; the rulings on predicates and
  the roster. Audit: [audit.md](2026-09-06/audit.md), the ingestor against SCHEMA.md,
  BUILD.md and the brief record by record, the decisions taken and the PROPOSED items, and
  the project's documents against each other. Findings: [review-findings.json](2026-09-06/review-findings.json).
