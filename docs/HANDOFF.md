# Start here

**2026-08-28.**

## First, check you have the current code

```bash
git -C ~/it494-memory-project fetch && git -C ~/it494-memory-project status -sb
```

A previous session opened a clone 19 commits behind and concluded the handoff had never been
written. It had. Two machines are in play and `maintain.py` pushes without fetching, so being behind
is the normal state, not a surprise.

---

## What this is

A memory backend for a desktop AI assistant. Text goes in as ordered chunks; the system records
dated facts with the quote that supports each one, plus a short narrative per important entity.
Tested on public-domain books, because books have answers you can check and a private archive does
not.

ISU MSCS directed project, Dr. Fang supervising, fall 2026 and spring 2027. **Fang approved the
topic change in person on 2026-08-28.** Only the one-semester form may still need filing.

---

## The plan

1. **Build the store.** Files backend only, per `03_design.md`. No Neo4j, no Graphiti.
2. **Ingest in sequence**, chunk by chunk. Never load a whole book at once, or nothing temporal gets
   tested.
3. **Measure accuracy** on Infinity-Bench En.MC: full system, no-context control, flat retrieval,
   plus one ablation with entity cells switched off.
4. **Measure cost**, which no benchmark covers: read cost, refold cost, coverage difference. None
   needs gold answers.
5. **Post by November 15.**

**Cut before starting:** skip the conformance suite, drop LongMemEval and the Zep comparison to
spring, run one ablation rather than four. Without those cuts the plan needs 52 to 94 hours against
32 available. `05_fall_plan.md` has the arithmetic.

---

## Two things a fresh session will get wrong

**Do not look for a new idea.** Twelve were searched and all twelve are already published. The
paper does not need one: the venues waive novelty and charge measurement instead. See
`01_argument.md`. If you do propose a thirteenth, search it first; all twelve died by assuming
nobody had done it, and three were disproved by papers already in `papers/`.

**Do not trust a summary of a paper.** Extract the PDF and read it. Five separate searches caught
their own tools inventing quotes, venues and numbers, and one fabricated statistic made it into two
documents before a cold audit caught it.

---

## Open

1. **Ask Fang for an arXiv cs.CL endorsement.** One email, and the only item depending on another
   person. First-time submitters cannot post without one.
2. **Read two papers in full:** Story Ribbons (arXiv:2508.06772) and Narrative World Model
   (arXiv:2607.05577). Both sit very close to this work.
3. **`data/clean/` is not progress.** 351 records over 16 of 81 works, committed by accident, does
   not meet the contract, and no script here produced it. Regenerate from committed code.
4. **Verify the hour budget.** Every schedule number in `05_fall_plan.md` rests on an assumed 8
   hours a week that was never checked against a real week. Confirm it before trusting the calendar.
   (Power is no longer an open item: GraphRAG-Bench's 2,010 questions detect about 2.4 points, and
   ablations move 2 to 5. The old 229-question worry was for the dropped benchmark.)
5. **Rebuild `papers/MANIFEST.md`.** It predates half the current corpus. Three entries were
   corrected on 2026-08-28 (CORE-KG, WiCER, iText2KG); assume others are wrong until checked.
6. **Unrevoked tokens** belong to the archive repo, not this one. A full-history scan here found
   nothing.
7. **Pick which ablations actually run.** Five are now designable (cells, resolution, threshold, fact
   layer, refold) and there is not room for five. `10_entity_resolution.md` argues resolution has
   published reference numbers and cells do not.

---

## House rules

- An absence claim needs a documented search. Never write "nobody has done X" without saying how you
  looked.
- Run a control query before believing an empty result.
- Say where a fact came from: full text, abstract, README, or memory.
- Never state a number you did not compute.
- No em dashes. One page per document unless there is a reason.
- **Anything designed here must work unchanged on chat logs, email and source code.** If it needs a
  special case for books, that case belongs in preprocessing, not in the data model.

---

## The documents

| File | What it covers |
|---|---|
| `01_argument.md` | What the project claims, and the twelve ideas that were already taken |
| `02_requirements_and_testing.md` | What memory systems need to do, and how each gets tested |
| `03_design.md` | The store: schema, ingest, retrieval, where it runs |
| `04_unit_contract.md` | **Frozen.** What splitting must produce |
| `05_fall_plan.md` | Calendar, hours, phases, cut order, cost |
| `06_spring_plan.md` | The installable version |
| `07_references.md` | Sources behind the schema decisions |
| `08_paper_options.md` | What kind of paper, and where it goes |
| `09_evaluation_corpus.md` | Which benchmark, and why |
| `10_entity_resolution.md` | Deciding when two names mean one thing |

`reference/` is background that still holds. `archive/` is superseded, each file labelled with what
replaced it. Correction history is in `git log`, not in the documents.
