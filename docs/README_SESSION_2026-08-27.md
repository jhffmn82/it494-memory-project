# Session record, 2026-08-26/27

Index to the documents produced in this session. All five carry the 2026-08-27 date and record
current understanding, not final decisions.

| Doc | Covers | Status |
|---|---|---|
| `14_novelty_reassessment.md` | Both named contributions found occupied; 13 competing papers pulled into `papers/` | Finding, dated |
| `15_schema_and_architecture.md` | First schema proposal plus a ten-item quality pass | **Superseded** on schema by 17; architecture superseded by 19 |
| `16_schema_prior_art.md` | Four sources read from `papers/`; six changes proposed; full references with per-claim pointers | Current |
| **`17_schema_current.md`** | Seven record types plus instrumentation, incorporating 16's changes | **Current** |
| **`18_ingestion_pipeline.md`** | Two axes, entity-first pass, thresholds, tier-per-stage | **Current** |
| **`19_retrieval_and_delivery.md`** | Retrieval, triggers, page rendering, two deployments | **Current** |
| **`20_evaluation.md`** | Datasets, instruments, controls, order of work | **Current** |
| **`21_cost_and_models.md`** | Rates fetched 2026-08-27, sizing, tier assignment | **Current, perishable** |

**Corpus is deliberately not re-documented here.** `data/raw/SOURCES.md`, `WANTLIST.md` and
`USAGE.md` already cover provenance, gaps and the built-in controls. A sixth document would only
create drift.

## Verification status

Only claims read directly from a source during this session are stated as fact. Items marked
`[verify]` are design input and are **not citable**:

- Angles, *The Property Graph Database Model* — no venue or year in the document; the filename's
  2018 is unverified. This is the source of δ
- Rost et al., *Bitemporal Property Graphs* — no DOI, venue or year in the document
- Wikidata **ranks** — the qualifier passage is confirmed; the rank discussion was not in the
  extracted span
- Hernández et al. — full citation not extracted
- **LitBank** — contents, licensing and availability unconfirmed. The cheapest experiment in
  `docs/20` depends on it
- Gemini pricing page — rendered a header dated Jan 1 2027, which does not match the fetch date

Fully verified: Vrandečić & Krötzsch, CACM 57(10) pp. 78–85, DOI 10.1145/2629489 · Rezazadeh et
al., arXiv:2505.18279v1 · the thirteen novelty-reassessment papers, arXiv IDs in
`papers/MANIFEST.md` · Graphiti's feature set, checked against its repository 2026-08-27 ·
GraphRAG's pipeline order, checked against its documentation.

## The open question that gates everything

**An ACL Anthology search on interleaved-thread summarisation has not been run.** Every novelty
search this session was arXiv-only, which is the wrong index for computational literary studies.
The design in `docs/18` rests on that gap being real. Until it is checked, treat the direction as
unvalidated.
