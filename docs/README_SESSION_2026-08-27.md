# Session record, 2026-08-26/27

Index to the documents produced in this session. All carry the 2026-08-27 date and record
current understanding, not final decisions.

## Current

| Doc | Covers |
|---|---|
| `14_novelty_reassessment.md` | Contributions found occupied; competing papers pulled into `papers/` |
| `16_schema_prior_art.md` | Four sources read from `papers/`; six changes; references with per-claim pointers |
| **`17_schema_current.md`** | Seven record types plus instrumentation |
| **`18_ingestion_pipeline.md`** | Two axes, entity-first pass, thresholds, tier-per-stage |
| **`19_retrieval_and_delivery.md`** | Retrieval, triggers, page rendering, two deployments |
| **`20_evaluation.md`** | Datasets, instruments, controls, order of work |
| **`21_cost_and_models.md`** | Rates fetched 2026-08-27, sizing, tier assignment. **Perishable** |
| **`22_project1_fall_plan.md`** | Project 1: backend, evaluation, paper |
| **`23_project2_spring_plan.md`** | Project 2: the distributable. Separate project |
| **`24_unit_contract.md`** | **FROZEN.** The one schema element preprocessing needs |
| **`25_paper_argument.md`** | The spine that survived seven novelty searches. Requirements from deployment, measured coverage gap, borrow openly, measure the design space |

## Superseded, kept for the record

`06_end_product_and_testing` · `08_plan_of_record` · `09_architecture` · `10_data_model` ·
`11_build_plan` · `12_wiki_demo` · `15_schema_and_architecture`

Each carries a banner naming its replacement. `15`'s quality pass remains live and drove `16`.

**Corpus is deliberately not re-documented here.** `data/raw/SOURCES.md`, `WANTLIST.md` and
`USAGE.md` cover provenance, gaps and the built-in controls.

## Positioning is unresolved

Every contribution the plan named is occupied. Searched and confirmed 2026-08-26/27:

| Claim | Occupied by |
|---|---|
| Proactive recall | CogniFold 2605.13438 · ProactAgent 2604.20572 · ENPMR-Bench 2605.27240 |
| Cold-start schema induction | AutoSchemaKG 2505.23628 · SCOPE/SCION 2607.21610 · EvoTaxo 2603.19711 |
| Narrative threads from conversation | **TraceMem 2602.09712** — the closest thing to the whole design |
| Entity-centric summarization | EntSUM ACL 2022 · EntSUMv2 EMNLP 2023 · line back to KDD 2012 |
| Thread disentanglement | Active ACL/SIGIR/LREC task, incl. Dramatic Conversation Disentanglement ACL 2023 |
| Evaluation gaps (backbone dependence, cost) | Anatomy of Agentic Memory 2602.19320 names both |
| n=1 longitudinal corpus | MyLifeBits, per the 08-19 adversarial verdict |

**Not yet searched:** covering-versus-partition (TraceMem clusters, so a trace belongs to one
thread; this design places a unit in N threads at full weight) · the three corpus controls ·
whether per-stage tier sensitivity has been *measured* rather than named.

**A positioning document now exists: `25_paper_argument.md`.** It was not written to fill a gap; it is what was left standing after seven candidate contributions were found occupied. Original note follows.

**No positioning document was written** during the first pass. Inventing a claim would be the failure mode this
session repeatedly corrected for. What the project is called is a decision for Justin and
Dr. Fang, and it is Phase 0 item 1 in `docs/22`.

## Verification status

**Fully verified:** Vrandečić & Krötzsch, CACM 57(10) pp. 78–85, DOI 10.1145/2629489 ·
Rezazadeh et al., arXiv:2505.18279v1 · the thirteen novelty papers, ids in `papers/MANIFEST.md` ·
**LitBank** (100 Gutenberg works 1719–1922, 210,532 tokens, four annotation layers incl.
quotation attribution; ~2,000 words sampled per work, not whole books) · Graphiti does **not** do
community summarisation · GraphRAG chunks first, then extracts per chunk · ISU symposium poster
size 36"×48", one foamboard and easel provided (2025 guidelines).

**`[verify]` — not citable:** Angles venue and year (no venue string in the document; it is the
source of δ) · Rost venue and year · the page for Wikidata ranks · full Hernández citation ·
Gemini pricing page header dated Jan 1 2027, which does not match the fetch date.

**Method caveat:** the ACL-side search used DBLP, which indexes titles only. It confirms the
component tasks are long-established; it cannot rule on the combination.
