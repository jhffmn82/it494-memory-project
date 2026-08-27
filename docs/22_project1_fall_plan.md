# Project 1 — Fall 2026: backend, evaluation, paper

**2026-08-27.** Supersedes `08_plan_of_record` for the fall. Project 2 (the distributable) is a
separate document, `docs/23`, and a separate project.

**The framing that governs every decision here:** Project 1's output is not a corpus tool. It is
**the backend for a desktop RAG assistant**, evaluated on literature because literature supplies
ground truth that a personal archive cannot. Every design choice should be made as though a
single user will point an AI client at this store — because in Project 2 they will.

---

## Positioning is unresolved and this plan does not assume one

As of `docs/14` and the 2026-08-27 searches, the following are occupied by published work:

| Claim | Occupied by |
|---|---|
| Proactive recall / unprompted retrieval | CogniFold 2605.13438, ProactAgent 2604.20572, ENPMR-Bench 2605.27240 |
| Cold-start schema induction | AutoSchemaKG 2505.23628, SCOPE/SCION 2607.21610, EvoTaxo 2603.19711 |
| Narrative threads from conversation | **TraceMem 2602.09712** — segmentation, episodic consolidation, hierarchical clustering into time-evolving narrative threads, memory cards, agentic search. SOTA on LoCoMo |
| Entity-centric summarization | EntSUM ACL 2022, EntSUMv2 EMNLP 2023, and a line back to KDD 2012 |
| Thread disentanglement | Active ACL/SIGIR/LREC task, incl. Dramatic Conversation Disentanglement ACL 2023 |
| Evaluation gaps (backbone dependence, cost) | Anatomy of Agentic Memory 2602.19320 names both |
| n=1 longitudinal personal corpus | MyLifeBits, and the 08-19 adversarial verdict |

**What is not yet searched:** the covering-versus-partition distinction (TraceMem clusters, so a
trace belongs to one thread; this design places a unit in N threads at full weight), the three
corpus controls (OCR tax, translation tax, contamination probe), and whether per-stage tier
sensitivity has been *measured* rather than named.

**Nothing in this plan requires a novelty claim to be worth doing.** The work below produces a
working backend, a reproducible dataset, and measured numbers. What it is *called* is a decision
for Justin and Dr. Fang, and it should be made after the searches above are closed, not before.

---

## Phase 0 — decisions and freeze (now → 2026-09-07)

1. **Take the positioning question to Dr. Fang.** Both plan contributions are occupied; the
   project is not. Present the finding, the remaining unsearched items, and ask what shape the
   fall deliverable should take. This is the gate on everything below.
2. **Resolve the administrative item.** The approved April proposal is a government-document tool
   survey. A new one-semester proposal on the Fang → Hasselbring → Tang routing is still
   outstanding.
3. **Freeze the unit contract** (`docs/24`). It is the only schema element that must be settled
   before preprocessing; the rest is settled by contact.
4. **Decide the backend.** Files (JSONL + npy + SQLite) versus Neo4j. This plan assumes **files**,
   on the grounds that the vector survey puts brute-force cosine correct below ~100K vectors and
   a personal corpus is far under that. Neo4j is Project 2's call.
5. **Turn on consult-logging** on the live mock. The proactive-recall instrument needs ~4 weeks of
   collection before its number means anything, so this cannot wait for the pipeline.

**Exit:** positioning direction agreed, proposal filed, unit contract frozen, logging running.

---

## Phase 1 — preprocessing (September)

Raw corpora → normalised units. Justin's code, visible, in a Kaggle notebook.

- Five per-convention handlers, one output contract
- TOC count as the acceptance gate where a TOC exists; monotonic-marker check where it does not;
  count == 1 for single-unit works (plays, odes)
- Known variants: `CHAPTER I. TITLE` all-caps · `I.  Title` indented under Contents · `BOOK I.` ·
  `第N回` · bare title lines with no marker
- Gutenberg producer notes appear *inside* the START marker on some files and must be stripped

**Deliverable:** `data/clean/<corpus>/chapters.jsonl` for all four corpora, published as a public
Kaggle Dataset. That publication is the reproducibility story and is worth more to a reviewer
than any backend choice.

**Scope valve:** Oz alone is sufficient to proceed. Greek and Chinese can follow.

---

## Phase 2 — pilot (early October, ~$3)

Full pipeline over **Oz book 1 only** — 24 units, ~57k tokens — across three model tiers.

Produces the sensitivity numbers, the rejection rates, and the duplicate-minting curve, and
surfaces schema gaps by contact rather than by reasoning. Freeze the remaining schema against
what it finds.

---

## Phase 3 — build (October 19 → November 15)

Pipeline per `docs/18`, storage per `docs/17`, behind the port in `docs/19`.

Build order: ingest → organize → maintain, with the evaluation spine alongside. Batch the cell
calls from the start; it is worth ~3× on the dominant cost term.

**The assembled renderer is built here, not later.** It is a development instrument — a thin
assembled page is a visible bug report, and it is the only way to see pipeline defects that a
JSONL file hides.

---

## Phase 4 — measure and write (November 1–15)

All measurement lands inside this window. **The paper posts by November 15**, not December —
December holds four graded CS 425 events, an exam window, and 8–10 PhD applications.

Committed measurements, in order of certainty:

1. **The free instruments** — rejection rate per stage per tier, duplicate minting per unit,
   predicate sprawl, quote gate pass rate, token cost per arm, plot-vs-cell consistency. These
   fall out of running the pipeline and need no dataset.
2. **LitBank head-to-head** — entity-first versus chunk-first, scored against gold. Confirmed
   available: 100 public-domain Gutenberg works, four annotation layers including quotation
   attribution. **Caveat: ~2,000 words sampled per work, not whole books**, so this scores
   extraction on excerpts.
3. **The two corpus controls** — OCR tax and translation tax, both carried by Three Kingdoms.
4. **The contamination probe** — free generation versus fact-row composition, deerstalker
   incidence.

**Stretch, only if the block survives:** NarrativeQA across three injection arms, and the
four-arm ablation (facts only / plot only / entity only / both) that would test whether the
two-axis design earns its cost. That ablation is the one experiment that tests the actual design
rather than a prerequisite, and it is the first thing to protect if hours appear.

---

## What "ultimately a desktop RAG backend" changes here

Four decisions that would otherwise be arbitrary:

- **The storage port exists from day one.** Project 2 swaps the adapter; Project 1 must not call
  one directly.
- **Files, not Neo4j.** Project 2's distributable is a folder someone points a client at. A
  server dependency in Project 1 becomes a port in Project 2.
- **MCP shape informs the retrieval API.** The twelve port operations should map cleanly onto
  tools a desktop client can call. If they don't, Project 2 rewrites them.
- **Single-user, single-workspace assumptions are fine.** Multi-workspace partitioning is
  filesystem separation in Project 2, not a policy layer in Project 1.

---

## Realistic outcome

**One instrument, measured on one corpus, plus a published dataset.** That is a workshop paper or
an arXiv preprint supporting an application. It is not an ICLR submission, and planning for one
produces neither.

The feasibility review priced the honest demand at 225–375 hours against 70–100 available and
dated the first unrecoverable break at September 15–21. Nothing since has changed that
arithmetic. What has changed is that the cost side is now known and small: the full four-corpus
run is $34–67 batched, and the pilot is $3.

**Hours are the binding constraint. Cut scope, not measurement.**
