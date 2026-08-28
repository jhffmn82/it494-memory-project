# Requirements and testing plan

**2026-08-27, revised 2026-08-28.** Supersedes the earlier evaluation plan (now
`archive/20_evaluation.md`), which predates the source flip below and the asymmetric baseline
strategy.

> **The LitBank head-to-head is withdrawn, and with it the GraphRAG comparison.** The claim it
> tested is dead (`01_argument.md`), and LitBank could not have measured it regardless: 96 of its
> 100 documents are exactly two chunks at GraphRAG's default size, so a phenomenon that compounds
> across many chunks has one boundary to appear at.
>
> **What replaces it, settled 2026-08-28: Infinity-Bench En.MC.** 229 questions, gold answers
> public, four-way accuracy by exact match, no judge, text shipped with the benchmark, and its books
> are **entity-substituted** so a model cannot answer from memorised pretraining. Three arms through
> one scorer (full system, no-context control at 25% random, flat chunk retrieval), with the
> ablations as further arms. Reasoning and alternatives in `09_evaluation_corpus.md`; schedule in
> `05_fall_plan.md`.
>
> **LongMemEval is kept, deliberately, as the Zep comparison.** Zep is the closest published system,
> so its numbers are the only ones this work can be measured against directly. That is the
> asymmetric strategy below: compete with Zep on its own metric.
>
> **NovelQA was considered and rejected**: its gold answers are held out behind a Codabench
> leaderboard, so every ablation would be a round-trip through someone else's server.

Every citation in the requirements table was re-verified against full paper text on 08-28, with the
single exception marked `[abstract only]`. Three were wrong and are corrected here. The corrections are marked, because the corrected versions are
weaker than what they replace and nobody should reintroduce the stronger wording from an old draft.

---

## The source flip, and why it matters

An earlier draft derived requirements from a personal deployment and validated them against the
literature. That is a wish list with a case study attached, and a reviewer answers it with *says
who?*

**Requirements are derived from the literature's own stated failures.** The deployment
corroborates; it does not authorise. Every row below cites a published paper saying the problem is
unsolved, and no personal detail appears anywhere. The deployment's entire role is one sentence: *a
two-year deployment of a personal memory system encountered each of these failure modes in
practice.*

**Consequence, stated plainly:** this section is **motivation, not contribution**. Its only job is
to make a reviewer agree the requirements are real before they are shown numbers. The contribution
is the measured comparison in `01_argument.md`.

---

## The seven requirements

| # | Requirement | The field saying it is unsolved |
|---|---|---|
| 1 | **Supersession and fact update** | MemoryAgentBench: on multi-hop fact consolidation, no tested method exceeds **28%**. Memora (ACL 2026 Findings) introduces a forgetting-aware metric that penalises reliance on invalidated memory [abstract only] |
| 2 | **Entity resolution** | Noy et al. 2019: disambiguation is named as *one of* the top challenges, recurring almost across the board in five production knowledge graphs. Bing's single Will Smith entry is composed from 108,000 facts taken from 41 websites |
| 3 | **Faithfulness and provenance** | FABLES: best model **90.9%** faithful; the strongest automatic checker reaches **58.2 F1** with the entire book in hand |
| 4 | **Omission and coverage** | BooookScore: omission errors are the most common error type across both prompting strategies. FABLES separately finds **33.3% to 65.4%** of summaries lack mentions of key events |
| 5 | **Incremental update** | MemTree measures the cost directly: incorporating one new observation takes roughly **3,750 LLM calls for RAPTOR and 3,850 for GraphRAG**, against 3.27 per insertion for MemTree. Talebirad names evolving hierarchies as "the most pressing open problem" for its own theory |
| 6 | **Cost accounting** | Anatomy of Agentic Memory: "system-level costs are frequently overlooked" |
| 7 | **Proactive recall** | Occupied, not open. See the correction below |

### Corrections to this table, made 2026-08-28

**Requirement 1 was overgeneralised.** The 28% is the ceiling on the **multi-hop** FactConsolidation
subtask specifically, not on fact-update tasks in general. On single-hop fact consolidation in the
same table, GPT-5-mini reaches 78.0 and GPT-4o 60.0; on a 6K-token version, o4-mini reaches 100 on
single-hop and 80 on multi-hop. The competency is also named **Selective Forgetting** in the paper,
not "fact update." Quote the multi-hop figure with its qualifier or a reviewer with the paper open
will catch it.

**Requirement 2 dropped two hedges.** Noy et al. write that disambiguation "continues to be *one
of* the top challenges in the industry *almost* across the board," and list it alongside scale,
extraction and knowledge evolution as co-equal recurring challenges. The Will Smith numbers are
exact and the company is Bing/Microsoft. Restore the hedges.

**Requirement 4 spliced two papers into one citation.** "Omission dominates the error types" is
BooookScore, correctly. The 33 to 65 percent figure is **FABLES**, not BooookScore. Both halves are
true; the attribution was not. The archived topic narrative had it right and the error entered when
that sentence was compressed into a table row.

**Requirement 5 was two-thirds wrong.** RAPTOR does not name incremental insertion as unsolved
anywhere in its paper, and neither does GraphRAG; the word appears in GraphRAG only in a
bibliography entry. The criticism is real but it comes from **MemTree**, which measured the
rebuild cost of both. Talebirad does name it, though as a limitation of its own theory rather than
a field-wide verdict. MemTree measures a recency and insertion-order bias in itself, quantified as
accuracy rising from 82.1 to 84.2, but never calls it drift. Reattributing to MemTree makes this
row both correct and stronger.

**Requirement 7 was an absence claim, and it is false.** The original wording was that every
memory benchmark poses the query, so a store that held the answer and was never consulted fails
none of them. ENPMR-Bench (arXiv:2605.27240) is a benchmark for proactive memory retrieval;
ProactAgent (arXiv:2604.20572) learns when to retrieve by comparing paired continuations with and
without retrieval, which is the counterfactual miss rate as a learned policy; CogniFold
(arXiv:2605.13438) is an always-on memory that surfaces intents unprompted. The requirement is
still real, and the instrument here is still unresolved, but it must be presented as **hard and
occupied**, not as unclaimed ground. See `01_argument.md`.

---

## How each is tested

| # | Test | Cost | Status |
|---|---|---|---|
| 2 | Infinity-Bench En.MC accuracy across three arms, plus the duplicate-minting curve per unit | **free** | gold answers public, exact match, no judge. The entity substitution defeats the contamination confound |
| 3 | Quote gate: every claim must trace to a verbatim string in its unit | **free** | deterministic |
| 6 | Run rows, per stage per tier | **free** | already in the schema |
| 5 | Refold cost and staleness versus full rebuild | cheap | direct comparison; GraphRAG and RAPTOR are batch, Zep is not, and MemTree published the per-insertion figures to compare against |
| 1 | LongMemEval knowledge-update band; the MemoryAgentBench multi-hop ceiling as cited context; Tip to Ozma as a fixture | moderate | |
| 4 | Plot-versus-cell consistency as a cheap proxy; BooookScore only if run | partial | true omission measurement requires knowing what should have been included |
| 7 | **No clean test.** The `Consult.used_ids` instrument is unresolved | hard | a paired counterfactual doubles every measured query |

**Say #7 is unsolved rather than fudging it.** It is the honest limitation. Note that it is no
longer also a limitation of the field, since ProactAgent measures a version of it, so the framing
is "we did not solve this," not "nobody can."

### Requirement 3 is the strongest position

FABLES reports the best automatic fabrication checker reaching 58.2 F1 with the entire book
available. The check here is exact string matching: not a classifier, not a judge, a `find()`. On
the assembled rendering path it is **100% traceable by construction**, because a claim with no
matching quote is never emitted.

That is not a better classifier, it is a different kind of guarantee, and it should be framed that
way rather than as a score comparison. It is also traceability and not correctness: the
edge-typing constraint exists because a fabricated relation can carry a genuine quote.

---

## Baselines are not symmetric

| Baseline | Compete on | Why |
|---|---|---|
| **Zep** | **its own metric**, LongMemEval | Public, conversational, has knowledge-update bands, and Zep published numbers on it |
| **GraphRAG** | **nothing, for now** | The comparison was going to be LitBank entity F1 and duplicate minting against its "chunk-first ordering." That premise is false: GraphRAG's own appendix says its prompt "first identifies all entities in the text ... before identifying all relationships," so it is already entity-first within a chunk. Its published evaluation is LLM-judged on self-generated questions over podcast and news corpora and cannot be reproduced fairly. There is no honest comparison left to run this semester |

**Zep's published LongMemEval numbers**, from Table 2 of its paper: 63.8% with gpt-4o-mini against
a 55.4% full-context baseline, and 71.2% with gpt-4o against 60.2%. Two qualifiers that must travel
with those figures. They are **LongMemEval_s**, the small variant whose conversations average about
115,000 tokens, not the full benchmark. And the stronger half of Zep's result is not the accuracy:
it served those numbers from about 1,600 tokens of context against the baseline's 115,000, with
roughly a tenfold latency reduction. If this project competes on LongMemEval it is competing on
that frontier, not on accuracy alone.

**DMR:** run it because it is cheap and widely cited, and quote Zep's own caveat. Zep scored 94.8%
against a 94.4% full-conversation baseline with gpt-4-turbo. The gpt-4o-mini row is the sharper
illustration and is currently unused: 98.2% against 98.0%, a margin of two tenths of a point. Zep's
paper calls the benchmark inadequate in its own words, noting each conversation is only 60 messages
and "easily fitting within current LLM context windows." Cite Table 1 rather than the abstract,
because the abstract's headline compares Zep to MemGPT rather than to full context.

**One precision note on GraphRAG.** Its evaluation uses four criteria, not two: comprehensiveness,
diversity, empowerment, and directness as a deliberate control. The headline wins are in
comprehensiveness and diversity, and empowerment showed mixed results, so say "primarily
comprehensiveness and diversity" rather than implying there are only two.

---

## Scope, against 70 to 100 hours

**Committed core**, with no question authoring, no judge calibration and no kappa study:

- The free instruments: quote gate, rejection rate per stage per tier, duplicate minting, predicate
  sprawl, token cost, plot-versus-cell consistency (requirements 3, 4, 6)
- Refold versus rebuild (requirement 5)
- Per-stage tier sensitivity, which is the one measurement with a real spread behind it (146-fold
  across providers, costed in `05_fall_plan.md`)

**Withdrawn 2026-08-28:** the LitBank head-to-head, which was the anchor of this list. It tested a
claim that turned out to be occupied and mis-stated, on a corpus that could not have measured it.
Nothing replaces it, and inventing a replacement without a search behind it would repeat the exact
error that killed nine consecutive claims.

If a book-scale version is ever wanted, the resource is BOOKCOREF (ACL 2025), not LitBank, and it
needs its own prior-art search first.

**The one paid benchmark worth running:** LongMemEval. It is where the assistant claim lives and
where Zep can be matched or beaten (requirement 1).

**Cited, not run:** MemoryAgentBench and BooookScore. They supply the multi-hop ceiling and the
omission context without costing a run. Note that the 33 to 65 percent figure comes from FABLES,
which is also cited and not run.

**Not attempted this semester:** requirement 7. Consult-logging should still start now, because the
rate needs weeks of collection before it means anything, but the measurement is not promised. The
logger that emits conforming run rows is a separate deliverable from switching logging on, and only
the latter is currently scheduled.

---

## Demonstrations, clearly labelled as such

These produce no comparable numbers. They produce evidence a reader can check by eye, and the paper
must not present them as results.

| Fixture | Corpus | Shows |
|---|---|---|
| Tip becoming Ozma at the end of book 2 | Oz | Aliasing, merge, supersession and time-scoped truth in one case, at document 2 rather than document 14 |
| Watson's wound, shoulder in *A Study in Scarlet* and leg in *The Sign of the Four* | Holmes | Contradiction with no reconciling reading, inside one author |
| The deerstalker probe | Holmes | Free generation versus fact-row composition; the second structurally cannot leak, because Doyle never wrote the detail so no fact row exists to compose |
| Source disagreement rendered inline | Greek | Helen reached Troy per Homer, never per Euripides, both live and both cited |
| OCR tax and translation tax | Chinese | Same content, one variable. Cite **OHRBench** (Zhang et al., *OCR Hinders RAG: Evaluating the Cascading Impact of OCR on Retrieval-Augmented Generation*, arXiv:2412.02592, on disk as `papers/zhang2024-ocr-hinders-rag.pdf`) as the original prior art, and Sun et al. 2026 (arXiv:2605.00911, `papers/sun2026-ocr-robustness-rag.pdf`) as the follow-up |
| The design session's own transcript | none | Ten interleaved, non-contiguous threads with cross-thread supersession. A **figure**, not a result |
