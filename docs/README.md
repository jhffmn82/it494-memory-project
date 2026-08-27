# IT 494 memory project: document index

**Last revised 2026-08-28.** Start with `HANDOFF.md` if you are picking this up cold. It records
where things actually stand, including what is unresolved.

The project is a memory backend for a desktop RAG assistant, designed and measured in the fall and
turned into something a stranger can install in the spring. It is evaluated on public-domain
literature because literature supplies ground truth a personal archive cannot.

---

## The working set

Ten documents. Everything else is background or superseded.

| Document | What it is |
|---|---|
| [`HANDOFF.md`](HANDOFF.md) | Where things stand, what is verified, what is open. Read first |
| [`01_argument.md`](01_argument.md) | Why there is no novelty claim left, how all nine died, and what survives without one |
| [`02_requirements_and_testing.md`](02_requirements_and_testing.md) | Seven requirements sourced to literature, how each is tested, the asymmetric baseline strategy, and the scope cut |
| [`03_design.md`](03_design.md) | Schema, ingestion, retrieval, rendering and delivery, in one document |
| [`04_unit_contract.md`](04_unit_contract.md) | **FROZEN.** The preprocessing output contract: eight convention handlers, three acceptance gates |
| [`05_fall_plan.md`](05_fall_plan.md) | The calendar, the phases, the cut order, and the cost model |
| [`06_spring_plan.md`](06_spring_plan.md) | The distributable, its risks, and its administrative gates |
| [`07_references.md`](07_references.md) | Schema prior art with complete, verified citations |
| [`08_paper_options.md`](08_paper_options.md) | Whether there is an honest paper here. Five shapes searched, four dead; the surviving one is a spring project with a two-hour kill check |

`04_unit_contract.md` is frozen and code is meant to build against it. Change it only with a note
saying why.

---

## reference/

Background that is **still valid and was never superseded**. It is out of the working set because
it is not being actively revised, not because it is wrong. Several of these hold content that
exists nowhere else:

- `reference/00_design_brief.md` is the only source for the hour budget, the five dead stretches, the
  November 15 rule and the eleven-risk register.
- `reference/02_proposal_draft.md` is the only statement of the project's intent in Justin's own voice.
- `reference/04_elevation_options.md` carries roughly seven citations that appear nowhere else here.
- `reference/07_pipeline_anatomy.md` is the specification baseline the harness is built against, with
  file-and-line receipts for every claim about the running prototype.
- `reference/13_feasibility_review.md` is the antagonistic review whose conclusions held up all the way
  through; its cut order is carried into `05_fall_plan.md`.

Also here: `reference/01_topic_narrative.md` (the field by problem), `reference/03_digest.md` (the working
bibliography), and the three survey JSON files behind them.

## archive/

Twenty-seven files that **have been superseded**. Every one carries a banner naming its successor.
Kept for provenance; do not build from any of them. `archive/impl/` holds six module specs written
against the old data model, and `archive/narrative_sections/` holds the eight source sections that
were tightened into `reference/01_topic_narrative.md`.

---

## Standing rules

These govern every document here and have been violated at least once each.

**On sources and claims.** Four method rules, each written after a specific failure:

- **An absence claim requires a documented search.** Never assert that nobody has done X without
  reporting how you looked. Three contributions were killed by this rule, and all three had been
  asserted without one.
- **Run a control query before trusting an empty result set.** Two corpora were reported
  unavailable when they were on Project Gutenberg the whole time, behind bad queries.
- **State the source type for every factual claim:** full text, abstract, README, or memory. A
  README is not the paper. Twenty-six of the one-pagers in `summaries/one-pagers/` are
  abstract-only reads and say so; treat a number that traces only to one as second-hand.
- **Never emit a number you did not compute.** One invented figure survived several drafts before
  it was caught.

**On voice.** Three buckets, never mixed: Justin's own words and work; what his records show; LLM
survey output. Survey output never wears his voice.

**On style.** No em dashes. No AI-tell vocabulary or formula phrasing. Headers that say something
rather than label a category. Paragraphs carrying the argument, with lists reserved for genuinely
enumerable things. No emoji, no generation stamps, no tool attributions.

---

## Verification status, as of 2026-08-28

**Verified against full paper text:** Zep's LongMemEval and DMR numbers, its four-message lookback,
and its community-subgraph summarisation; GraphRAG's chunk-first ordering, its use of Leiden, and
its four evaluation criteria; HERCULES on recursive k-means; TraceMem's explicit partition; LitBank
at 210,532 tokens over 100 works with four layers on the same texts; FABLES at 90.9 percent and
58.2 F1; the Anatomy cost quote; both arXiv identifiers.

**Verified against source code**, at Graphiti commit `683a853`: plain-text episode ingestion, and
`add_triplet` accepting pre-extracted entities.

**Corrected on 08-28, having been wrong:** the MemoryAgentBench 28 percent (multi-hop only), the
Noy characterisation (hedges dropped), the BooookScore attribution (the 33 to 65 percent is
FABLES), the incremental-insertion attribution (RAPTOR and GraphRAG do not name it; MemTree
measured it), requirement 7's absence claim, the Zep correction's own overstatement about full
refresh, and three arithmetic errors in the cost model.

**Deleted rather than repaired:** the coverage-matrix claim that "the best single system covers
five or six of nine." It was never computed and there are seven requirements, not nine.

**Withdrawn 2026-08-28:** the entity-first versus chunk-first claim and the LitBank head-to-head
that was meant to measure it. Nine candidate contributions have now been searched adversarially and
all nine are occupied. The premise was also wrong: both baselines are already entity-first, by their
own papers. There is no novelty claim left, and inventing a tenth without a search behind it would
repeat the error that killed the other nine. What the project becomes instead is a decision for
Justin and his advisor. See `HANDOFF.md`.

**Open:** see `HANDOFF.md`.
