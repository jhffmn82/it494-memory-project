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
