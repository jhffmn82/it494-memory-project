# Fall 2026 plan

**2026-08-28.**

## Short version

Build the store. Run it against a benchmark with three arms and one ablation. Post by November 15.
Everything else moves to spring.

---

## The calendar, which is the constraint

**Nine usable weeks, in two blocks, and they are the only two.**

- **Open:** Aug 25 to Sep 27, and Oct 19 to Nov 15.
- **Dead:** Sep 28 to Oct 18 (three straight weeks of tests, a midterm, a machine problem, two
  quizzes), Nov 16 to 22, and Nov 30 to Dec 13, which is the whole PhD application window.

**Budget: 70 to 100 hours total**, at roughly eight a week when a week is open and near zero when it
is not.

**Two rules.** Nothing gets scheduled outside the open blocks. And **finished by November 15 or it
does not count**, because it has to be citable for applications due December 1 to 15.

**Authorship rule.** You implement. AI helps draft and argue, never writes unexamined code. This is
why hours cannot be priced at assistant speed.

---

## The hours do not fit, and here is the arithmetic

The build and measure blocks give **32 hours**. What is currently written into this plan:

| | hours |
|---|---|
| conformance suite, 17 operations | 14-21 |
| ingest, organize, maintain | 20-40 |
| scorer plus three arms | 6-10 |
| four ablation arms | 4-8 |
| LongMemEval session preprocessing | 8-15 |
| **total** | **52-94 against 32** |

**So cut before starting, not under pressure in November:**

- **Skip the conformance suite this fall.** It protects a second adapter that is not being built.
  Saves 14 to 21 hours immediately.
- **Drop LongMemEval and the Zep comparison.** It needs session preprocessing that was never
  scoped, and it is the only piece not on the path to a result. Spring.
- **Run one ablation, not four.** Turn off the per-entity cells, because that is the piece that
  tests the actual design decision.

That is roughly 30 hours and it fits.

---

## Phases

**Phase 0, now to Sep 7.** Ask Fang for an arXiv cs.CL endorsement (one email, and the only thing
depending on another person). File the one-semester proposal form; the topic change itself is
approved. Turn on consult-logging, since that number needs weeks of collection.

**Phase 1, September.** Splitting. Raw text to units, against `04_unit_contract.md`, with all three
gates passing. Publish the cleaned corpora with a DOI.

Note: `data/clean/` already holds 351 records over 16 of 81 works, committed by accident. It does
not meet the contract and no script in this repo produced it. Regenerate everything from committed
code.

**Phase 2, mid-to-late September, about $2.** Full pipeline over one short book across three model
tiers. Surfaces schema gaps by contact rather than by reasoning.

**Phase 3, Oct 19 to Nov 7.** Build: ingest, then organize, then maintain. Files backend only.
Ingest in sequence, never in bulk. Batch the cell calls from the start.

**Phase 4, Nov 8 to 15.** Measure and write.

---

## What gets measured

**Accuracy, on Infinity-Bench En.MC.** Three arms through one scorer: the full system, a no-context
control (random is 25%, and it goes in the headline table), and flat chunk retrieval as the baseline
to beat. Then one ablation with the entity cells switched off.

**Watch the sensitivity.** 229 questions means a difference of roughly 5 to 9 points is needed
before it is real rather than noise, and switching a component off usually moves 2 to 5. Check this
against real arm agreement in October, before committing to the run. LiteraryQA has 3,785 questions
if more power is needed; its metric is noisier but it can see smaller effects.

**Cost, which no benchmark reaches.** These need no gold answers:

- **Read cost.** For an entity appearing in K or more chunks, how much text must you read to follow
  its thread via the entity index versus via the chunk summaries? Report as a curve in K.
- **Refold cost.** Recompute with hash-gating versus a full rebuild, as the corpus grows. Compare
  against MemTree's published figures rather than presenting it as a first.
- **Coverage difference.** Chunk summaries and entity cells describe the same text independently, so
  the difference between what each contains is measurable with no ground truth at all. If the cells
  hold nothing the summaries miss, the entity layer is redundant, and that is a finding.

**Free instruments** that fall out of running anything: rejection rate per stage per tier, duplicate
entities minted per chunk, predicate sprawl, quote-gate pass rate, token cost per arm.

---

## The cut order, decided now

At least one week will vanish: drill weekends at unknown dates, another course's exams, a family
calendar, and a documented pattern of crashing after sustained grind. **A lost week deletes from the
bottom.**

1. The signed proposal. Nothing displaces it.
2. The instruments running on the live prototype in evenings, which need collection time.
3. The design write-up.
4. The pipeline, if and only if the October block survives intact.
5. Everything else.

Note that layer 2 is **not** the paper. That was carried over from an earlier plan and contradicts
the decision that the personal archive is design rationale, not evidence.

---

## Cost

Rates fetched 2026-08-27 and **perishable**; the Anthropic table was already two months stale when
copied. Re-check before any of this enters a budget.

Per chunk the pipeline makes one entity pass, one fact pass, and N cell calls, and **each call
re-sends the chunk text**. Batching the cell calls into one is the difference between 18,900 and
8,100 input tokens per chunk: **2.3x on total input, 5x on the part that dominates.** Build it in
from the start.

Full four-corpus run, batched: **$34 on Haiku, $67 on Sonnet, $168 on Opus, $335 at the top.** The
pilot is about **$2**.

**Money is not the constraint; hours are.** But the 146-fold spread between cheapest and dearest is
why the tier question is worth measuring: if a cheap model holds the early stages, the corpus can be
re-run every time the pipeline changes.

**Two operational notes.** The prototype's fact layer has failed twice on credit balance, so
instrument spend and set a hard stop. And local models fail on output format rather than
comprehension, so measure those two separately; they have different fixes.

---

## What this realistically produces

A working backend, a published dataset, and measured numbers on one corpus. That is a workshop paper
or an arXiv preprint supporting an application. It is not a top-conference submission and planning
for one produces neither.
