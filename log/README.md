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
