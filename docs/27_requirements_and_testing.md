# Requirements and testing plan

**2026-08-27.** Supersedes `20_evaluation.md`, which predates the source-flip below and the
asymmetric baseline strategy.

---

## The source flip, and why it matters

An earlier draft derived requirements from a personal deployment and validated them against
literature. That is a wish list with a case study attached, and a reviewer answers it with
*says who?*

**Requirements are derived from the literature's own stated failures.** The deployment
corroborates; it does not authorise. Every row below cites a published paper saying the problem
is unsolved, and **no personal detail appears anywhere** — incidents are generic ("an incorrect
entity merge," "a stale summary served as current").

The deployment's entire role is one sentence: *a two-year deployment of a personal memory system
encountered each of these failure modes in practice.*

**Consequence, stated plainly:** this section is **motivation, not contribution**. Its only job
is to make a reviewer agree the requirements are real before they are shown numbers. The
contribution remains the measured design space.

---

## The seven requirements

| # | Requirement | The field saying it is unsolved |
|---|---|---|
| 1 | **Supersession / fact update** | MemoryAgentBench: no tested system exceeds **28%** on fact-update tasks |
| 2 | **Entity resolution** | Noy et al. 2019: disambiguation is the top challenge across five production knowledge graphs. Bing's single Will Smith entry was assembled from 108,000 facts across 41 sites |
| 3 | **Faithfulness / provenance** | FABLES: best model **90.9%** faithful; the strongest automatic checker reaches **58.2 F1** with the whole book in hand |
| 4 | **Omission / coverage** | BooookScore: omission dominates the error types; 33–65% of summaries omit key events |
| 5 | **Incremental update** | RAPTOR, GraphRAG and Talebirad all name incremental insertion as unsolved; MemTree measures its own drift |
| 6 | **Cost accounting** | Anatomy of Agentic Memory: system-level costs "frequently overlooked" |
| 7 | **Proactive recall** | Every memory benchmark poses the query, so a store that held the answer and was never consulted fails none of them |

---

## How each is tested

| # | Test | Cost | Status |
|---|---|---|---|
| 2 | LitBank gold entities and coreference; duplicate-minting curve per unit | **free** | gold data, no judge; curve falls out of ingest |
| 3 | Quote gate — every claim must trace to a verbatim string in its unit | **free** | deterministic |
| 6 | Run rows, per stage per tier | **free** | already in the schema |
| 5 | Refold cost and staleness versus full rebuild | cheap | direct comparison; GraphRAG and RAPTOR are batch, Zep is not |
| 1 | LongMemEval knowledge-update band; MemoryAgentBench fact-update ceiling as cited context; Tip→Ozma as a fixture | moderate | |
| 4 | Plot-versus-cell consistency as a cheap proxy; BooookScore only if run | partial | true omission measurement requires knowing what *should* have been included |
| 7 | **No clean test.** The `Consult.used_ids` instrument is unresolved | hard | paired counterfactual doubles every measured query |

**Say #7 is unsolved rather than fudging it.** It is the honest limitation and it is also the
thing the field cannot measure either.

### Requirement 3 is the strongest position, and it is worth noticing why

FABLES reports the best automatic fabrication checker reaching **58.2 F1** with the entire book
available. The check here is exact string matching — not a classifier, not a judge, a `find()`.
On the assembled rendering path it is **100% traceable by construction**, because a claim with no
matching quote is never emitted.

That is not a better classifier. It is a different kind of guarantee, and it should be framed
that way rather than as a score comparison.

---

## Baselines are not symmetric

| Baseline | Compete on | Why |
|---|---|---|
| **Zep** | **its own metric** — LongMemEval | Public benchmark, conversational, has knowledge-update bands, and Zep published numbers: 63.8% (gpt-4o-mini) and 71.2% (gpt-4o) against full-context baselines of 55.4% and 60.2% |
| **GraphRAG** | **our metrics** — LitBank entity F1, duplicate minting | Its evaluation is LLM-judged comprehensiveness and diversity on self-generated questions over podcast and news corpora. Reproducing that means writing your own questions and your own judge, at which point you are comparing against your own reimplementation, not their number. Its **pipeline** is open source and its chunk-first ordering is exactly what is under test |

**DMR:** run it because it is cheap and widely cited, and quote Zep's own caveat — 94.8% against
a 94.4% full-context baseline, so it barely discriminates.

---

## The claim under test

Both published baselines extract **chunk-first**:

- GraphRAG composes text units first and extracts entities from each **separately** (its indexing
  documentation)
- Zep extracts per-episode with a four-message lookback, then resolves (its paper)

This project scans the unit, establishes the cast, and conditions everything downstream on it.
That is the primary claim: **pre-determined unit-level entity salience versus per-chunk
extraction**, measured on gold annotations against two state-of-the-art systems.

**Secondary and unverified: covering versus partition.** Every hierarchical memory system found
partitions — HERCULES uses recursive k-means, TraceMem clusters traces, GraphRAG uses Leiden, Zep
uses label propagation. Treat as a hypothesis until searched properly.

---

## Scope, against 70–100 hours

**Committed core** — no question authoring, no judge calibration, no kappa study:

- LitBank head-to-head (requirement 2)
- The free instruments: quote gate, rejection rate per stage per tier, duplicate minting,
  predicate sprawl, token cost, plot-versus-cell consistency (requirements 3, 4, 6)
- Refold versus rebuild (requirement 5)

**The one paid benchmark worth running:** LongMemEval. It is where the assistant claim lives and
where Zep can be matched or beaten (requirement 1).

**Cited, not run:** MemoryAgentBench and BooookScore. They supply the 28% and the 33–65% omission
context without costing a run.

**Not attempted this semester:** requirement 7. Consult-logging should still start now, because
the rate needs weeks of collection before it means anything — but the measurement is not
promised.

---

## Demonstrations, clearly labelled as such

These produce no comparable numbers. They produce evidence a reader can check by eye, and the
paper must not present them as results.

| Fixture | Corpus | Shows |
|---|---|---|
| Tip → Ozma at the end of book 2 | Oz | Aliasing, merge, supersession and time-scoped truth in one case, at document 2 rather than 14 |
| Watson's wound — shoulder in *A Study in Scarlet*, leg in *The Sign of the Four* | Holmes | Contradiction with no reconciling reading, inside one author |
| The deerstalker probe | Holmes | Free generation versus fact-row composition; the second structurally cannot leak |
| Source disagreement rendered inline | Greek | Helen reached Troy per Homer, never per Euripides |
| OCR tax and translation tax | Chinese | Same content, one variable. Method has prior art in OHRBench and should cite it |
| **This session's own transcript** | — | Ten interleaved, non-contiguous threads with cross-thread supersession. A **figure**, not a result |
