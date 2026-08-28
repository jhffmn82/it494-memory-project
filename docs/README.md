# IT 494 memory project

**Start with [`HANDOFF.md`](HANDOFF.md).** It has the plan, what is open, and what to do first.

A memory backend for a desktop AI assistant. Text goes in as ordered chunks; the system records
dated facts with the quote supporting each one, plus a short narrative per important entity. Tested
on public-domain books, because books have checkable answers and a private archive does not.

---

## Documents

| File | What it covers |
|---|---|
| [`HANDOFF.md`](HANDOFF.md) | The plan, what is open, what to do first |
| [`01_argument.md`](01_argument.md) | What the project claims, and the twelve ideas already taken |
| [`02_requirements_and_testing.md`](02_requirements_and_testing.md) | What memory systems must do, and how each gets tested |
| [`03_design.md`](03_design.md) | The store: schema, ingest, retrieval, where it runs |
| [`04_unit_contract.md`](04_unit_contract.md) | **Frozen.** What splitting must produce |
| [`05_fall_plan.md`](05_fall_plan.md) | Calendar, hours, phases, cut order, cost |
| [`06_spring_plan.md`](06_spring_plan.md) | The installable version |
| [`07_references.md`](07_references.md) | Sources behind the schema decisions |
| [`08_paper_options.md`](08_paper_options.md) | What kind of paper, and where it goes |
| [`09_evaluation_corpus.md`](09_evaluation_corpus.md) | **The handle.** Every dataset, what it tests, what the build must support |
| [`10_entity_resolution.md`](10_entity_resolution.md) | Deciding when two names mean one thing |

`reference/` is background that still holds, including the only record of the hour budget and the
risk register. `archive/` is superseded, each file labelled with what replaced it.

---

## House rules

**On claims.**

- An absence claim needs a documented search. Never write "nobody has done X" without saying how you
  looked.
- Run a control query before believing an empty result.
- Say where a fact came from: full text, abstract, README, or memory. A README is not the paper.
- Never state a number you did not compute.
- **Extract and read the PDF.** Do not trust a tool's summary of one.

**On design.**

- Anything designed here must work unchanged on chat logs, email and source code. If it needs a
  special case for books, that case belongs in preprocessing, not in the data model.

**On writing.**

- One page per document unless there is a reason. Plain words. No term used before it is defined.
- No em dashes.
- Correction history lives in `git log`, not in the documents.

**On voice.** Three buckets, never mixed: Justin's own words and work, what his records show, and
survey output. Survey output never wears his voice.
