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
  document holds its text once and units are ranges in one coordinate system; the general
  extractor plan and the all-sources raw dataset; open items.
  Inventory: [inventory.md](2026-09-04/inventory.md), every source audited (format, size,
  license, fixtures), what the Step 0 brief had wrong or missing, twelve decisions to rule.
  Brief: [step0-brief.md](2026-09-04/step0-brief.md), the opening message for the extractor chat.
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
- [2026-09-06](2026-09-06/README.md): audit day. The saved 0.9 notebook audited against the
  schema and the rulings, then 1.0 to 1.4: the audit applied (grouped chat units restored,
  19,206 against 198,961); the debugging accretions cut (164 lines, a synonym table, a Roman
  numeral parser, a duplicate finder, a union-find); a real regression caught by a run and
  fixed in the resolver; the run parallelised and one kind per unit enforced; and three cost
  defects, including a no-credits 429 that walked the whole corpus and a per-document cost
  that counted every other thread.
  Audit: [audit.md](2026-09-06/audit.md). Changes: [final-run-changes.md](2026-09-06/final-run-changes.md).
  Brief: [ingestor-brief.md](2026-09-06/ingestor-brief.md), the opening message for the ingestor chat.
