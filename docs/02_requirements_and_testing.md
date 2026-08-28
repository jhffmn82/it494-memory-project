# What memory systems need to do

**2026-08-28.**

## Short version

Seven things a memory backend has to get right. Each one comes from a published paper saying it is
still unsolved, not from a wish list. This section is **motivation, not contribution**: its only job
is to make a reader agree the problems are real before you show them numbers.

Your own two years of running one corroborates in a sentence. It does not authorise anything, and no
personal detail belongs here.

---

## The seven

| # | What | Who says it is unsolved |
|---|---|---|
| 1 | **Updating a fact when it changes** | MemoryAgentBench: on multi-hop fact consolidation no tested system beats 28%. Memora (ACL 2026 Findings) adds a metric that penalises using stale memory |
| 2 | **Knowing two names mean one thing** | Noy et al. 2019: disambiguation is *one of* the top challenges across five production knowledge graphs. Bing's single Will Smith entry was assembled from 108,000 facts across 41 sites |
| 3 | **Not making things up** | FABLES: the best model is 90.9% faithful, and the best automatic checker reaches 58.2 F1 with the whole book in hand |
| 4 | **Not leaving things out** | BooookScore: omission is the most common error type. FABLES separately finds 33% to 65% of summaries miss key events |
| 5 | **Adding new material cheaply** | MemTree measures it: one new item costs ~3,750 model calls for RAPTOR and ~3,850 for GraphRAG, against 3.27 for MemTree |
| 6 | **Knowing what it costs** | Anatomy of Agentic Memory: system-level costs are "frequently overlooked" |
| 7 | **Speaking up unprompted** | Real, but occupied. ENPMR-Bench benchmarks it, ProactAgent learns it, CogniFold does it |

Two of these were overstated in earlier drafts. The 28% is the multi-hop ceiling only; single-hop
reaches 78% at full length. And requirement 7 was written as "no benchmark can express this", which
is false.

---

## How each gets tested

| # | Test | Cost |
|---|---|---|
| 2 | Duplicate entities minted per chunk, plus accuracy across arms | free |
| 3 | Quote gate: every claim must match a verbatim string in its chunk | free, deterministic |
| 6 | Run records, per stage per tier | free |
| 5 | Refold versus full rebuild, against MemTree's published figures | cheap |
| 4 | Chunk summary versus entity cells, compared as sets | free |
| 1 | Fixtures where a fact changes mid-book, e.g. Tip becoming Ozma | moderate |
| 7 | **No clean test.** Say so | hard |

**Requirement 3 is the strongest position and it is worth knowing why.** FABLES reports the best
automatic checker at 58.2 F1 with the entire book available. The check here is exact string
matching: not a classifier, not a judge, a `find()`. On the assembled output it is **100% traceable
by construction**, because a claim with no matching quote is never written.

That is not a better classifier. It is a different kind of guarantee, and it should be framed that
way rather than as a score comparison. It is also traceability, not correctness.

---

## Baselines are not symmetric

**Zep:** compete on its metric, LongMemEval, because it never ran on books and a comparison invented
here would be against your own reimplementation. Zep published 63.8% with gpt-4o-mini against a
55.4% full-context baseline, and 71.2% with gpt-4o against 60.2%.

Two things must travel with those numbers. They are **LongMemEval_s**, the small variant. And
accuracy is the weaker half of Zep's result: it served those scores from about 1,600 tokens of
context against the baseline's 115,000, with roughly a tenfold latency cut. **Matching Zep's
accuracy while reading far more context is a loss.** Report context size next to accuracy.

**Do not run DMR.** Zep's own paper calls it inadequate: 94.8% against a 94.4% baseline, and
98.2% against 98.0% on another row, with 60-message conversations that fit in a context window
anyway. Cite the caveat instead of spending a run.

**GraphRAG:** no honest comparison is available this semester. Its evaluation is LLM-judged on
questions it wrote itself, over podcasts and news.

---

## Scope

**This fall:** the free instruments, the accuracy arms, one ablation, the cost measurements.

**Spring:** LongMemEval and the Zep comparison. It needs conversational preprocessing that was never
costed.

**Cited, not run:** MemoryAgentBench, BooookScore, FABLES. They supply context without costing a
run.

**Not attempted:** requirement 7. Consult-logging should still start now, because the number needs
weeks of collection, but the measurement is not promised.

---

## Demonstrations, which are not results

These produce evidence a reader can check by eye. The paper must not present them as measurements.

| Fixture | Shows |
|---|---|
| Tip becomes Ozma at the end of Oz book 2 | Renaming, merging and a fact changing, all in one case, early |
| Watson's wound: shoulder in one book, leg in another | A contradiction with no resolution, inside one author |
| The deerstalker | Doyle never wrote it, so there is no fact row, so the composed output structurally cannot say it |
| Helen reached Troy per Homer, never per Euripides | Sources disagreeing, both kept, neither overwritten |
| The same Chinese text as clean copy and as OCR scan | One variable changed. Cite OHRBench (arXiv:2412.02592) |
