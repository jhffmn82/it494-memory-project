# Fall 2026: backend, evaluation, paper

**2026-08-27, revised 2026-08-28.** Supersedes `archive/08_plan_of_record.md` for the fall. The
spring distributable is a separate document, `06_spring_plan.md`, and a separate project. The cost
model, previously a standalone document, is absorbed here and its arithmetic corrected.

**The framing that governs every decision here:** the output is not a corpus tool. It is **the
backend for a desktop RAG assistant**, evaluated on literature because literature supplies ground
truth that a personal archive cannot. Every design choice should be made as though a single user
will point an AI client at this store, because in the spring they will.

---

## The calendar, which is the binding constraint

Nine usable weeks in two blocks, and they are the only two.

**Open:** August 25 through September 27, with a homework set taking a bite around the 17th.
October 19 through November 15, with a homework set on November 1 and quizzes on the 8th and 15th.

**Dead:** September 28 to October 4, October 5 to 11, October 12 to 18 (three consecutive weeks of
tests, a midterm window, a machine problem and two quizzes), November 16 to 22, and November 30 to
December 13, which is the entire PhD application window.

**Budget: 70 to 100 hours, concentrated September 1 to November 15**, at a ceiling of roughly eight
hours in a normal week and near zero in a dead one. This figure is arithmetic over fixed
commitments, not a measured study log, and it should be corrected rather than trusted.

**Two rules follow, and they are not negotiable.**

- **No milestone may be placed outside the two open blocks.** Any plan whose arithmetic exceeds
  nine weeks at eight hours is rejected on sight.
- **Complete by November 15 or it does not count.** The deliverable must be finished, committed and
  citable by then so it can appear in applications due December 1 to 15 and in the November letter
  brag sheets. A plan that targets December targets nothing.

**Authorship rule.** The student implements. An AI assists in drafting and discussion but is never
the unexamined author, and completion is logged. This is the hardest constraint on the build and it
is the reason hour estimates cannot be priced at assistant speed.

---

## Positioning: what is occupied, and what this plan claims

As of the 08-27 and 08-28 searches, all of the following are occupied by published work:

| Claim | Occupied by |
|---|---|
| Proactive recall, unprompted retrieval | CogniFold 2605.13438, ProactAgent 2604.20572, ENPMR-Bench 2605.27240 |
| Cold-start schema induction | AutoSchemaKG 2505.23628, SCOPE/SCION 2607.21610, EvoTaxo 2603.19711 |
| Narrative threads from conversation | TraceMem 2602.09712, SOTA on LoCoMo |
| Entity-centric summarization | EntSUM ACL 2022, EntSUMv2 EMNLP 2023, back to KDD 2012 |
| Thread disentanglement | Active ACL/SIGIR/LREC task |
| Evaluation gaps, backbone dependence and cost | Anatomy of Agentic Memory 2602.19320 |
| n=1 longitudinal personal corpus | MyLifeBits, and the 08-19 adversarial verdict |
| **Covering versus partition** | **RAPTOR (ICLR 2024) soft-clusters by design; CAM (NeurIPS 2025) does incremental overlapping clustering. Closed 08-28** |
| **A literary memory benchmark** | **NarrativeXL (Findings of EMNLP 2023), MemoryAgentBench, StoryBench. Closed 08-28** |
| **A requirements analysis for assistant memory** | **Partially: Jones et al. CHI EA 2025, and 2606.24775 across twelve systems. Closed 08-28** |
| **Entity-first versus chunk-first extraction** | **iText2KG 2409.03284 (which ran the ablation and got a NEGATIVE result), RAKG 2504.09823, LINK-KG 2510.26486, CORE-KG 2506.21607. And the premise was wrong: both baselines are already entity-first. Closed 08-28** |

Every search this plan previously listed as outstanding is now closed, and every one came back
occupied. **Nine candidate contributions, nine occupied. There is no surviving novelty claim.**
See `01_argument.md` for how each died.

**What this plan is now.** A working backend, a published dataset, and measured cost and tier
numbers. That is an engineering project with measurements and it does not require a novelty claim.
Whether it also becomes a paper, and what that paper would claim, is a decision for Justin and his
advisor, and it belongs in the Phase 0 conversation below alongside the administrative item.

---

## Phase 0: decisions and freeze (now to September 7)

1. **Resolve the administrative item, and treat it as the gate.** The approved April proposal on
   file is a survey of LLM and NLP tools on government documents. Everything below is a different
   project. A new one-semester proposal on the Fang, then Hasselbring and Tang, routing is still
   outstanding, and nothing on record shows the topic change was ever approved. This is the single
   highest-value outcome available and it is administrative rather than intellectual.
2. **Take the positioning question to the advisor, and treat it as a real decision rather than a
   formality.** Nine candidate contributions were searched and all nine are occupied. There is no
   novelty claim left. Present that plainly, present what survives without one (a working backend,
   a published dataset, measured cost and tier numbers), and ask whether the fall deliverable
   should be an engineering project with measurements or something else. The advisor steered
   toward a practical project twice before; this finding points the same way.
3. **Freeze the unit contract** (`04_unit_contract.md`, already frozen). It is the only schema
   element that must be settled before preprocessing.
4. **Decide the backend.** Files (JSONL, npy, SQLite) versus Neo4j. This plan assumes files,
   because brute-force exact cosine is correct below roughly 100K vectors and a personal corpus is
   far under that. Neo4j is a spring call.
5. **Turn on consult-logging**, and note that the logger emitting conforming rows is a separate
   deliverable from switching logging on. The instrument needs about four weeks of collection
   before its number means anything, so it cannot wait for the pipeline.

**Exit:** proposal filed, positioning agreed, contract frozen, logging running.

---

## Phase 1: preprocessing (September, inside the first open block)

Raw corpora to normalised units. The student's code, visible, in a notebook.

- **Eight** per-convention handlers, one output contract, per `04_unit_contract.md`
- Table-of-contents count as the acceptance gate where a TOC exists; a monotonic-marker check where
  it does not; count equal to one for single-unit works such as plays and odes
- Gutenberg producer notes appear *inside* the start marker on some files and must be stripped

**Deliverable:** `data/clean/<corpus>/chapters.jsonl` for all four corpora, published as a public
dataset. That publication is the reproducibility story and is worth more to a reviewer than any
backend choice.

**Note on the existing partial output.** `data/clean/` already holds 351 records covering 16 of 81
works, committed on 08-27 as collateral in an unrelated documentation commit. It **does not meet
the frozen contract**: it has no `unit_type` and no `unit_id`, and it uses `chapter_ordinal` where
the contract says `unit_ordinal`. No script in this repository produced it, so it is not
reproducible. Treat it as a scratch spike, not as progress: Phase 1 regenerates everything from a
committed splitter.

**Scope valve:** Oz alone is sufficient to proceed. Greek and Chinese can follow.

---

## Phase 2: pilot (mid to late September, before the block closes, about $3)

Full pipeline over **Oz book 1 only**, 24 units and roughly 57,000 tokens, across three model
tiers. Produces the sensitivity numbers, the rejection rates and the duplicate-minting curve, and
surfaces schema gaps by contact rather than by reasoning. Freeze the remaining schema against what
it finds.

**This moved.** It was previously scheduled for early October, which falls inside the three dead
weeks of September 28 to October 18. It must land before September 27 or it slips to October 19 and
eats the build block.

Note that book 1 averages about 2,375 tokens per unit, below the 2,800 corpus average, so it is a
cheap pilot rather than a representative one. Book 2 is the hard case: it carries the `bare_title`
convention and the Tip-to-Ozma fixture, and it should be the second thing run.

---

## Phase 3: build (October 19 to November 7)

Pipeline and storage per `03_design.md`, behind the port described there.

Build order: ingest, then organize, then maintain, with the evaluation spine alongside. **Batch the
cell calls from the start.** See the cost model below: batching cuts total input by about 2.3 times
and the dominant cell-input term by 5 times.

**The assembled renderer is built here, not later.** It is a development instrument. A thin
assembled page is a visible bug report, and it is the only way to see pipeline defects that a JSONL
file hides.

---

## Phase 4: measure and write (November 8 to 15)

**The paper posts by November 15.** December holds four graded events in another course, an exam
window, and eight to ten PhD applications.

Committed measurements, in order of certainty:

1. **The free instruments.** Rejection rate per stage per tier, duplicate minting per unit,
   predicate sprawl, quote gate pass rate, token cost per arm, plot-versus-cell consistency. These
   fall out of running the pipeline and need no dataset.
2. **Per-stage tier sensitivity.** Which stages need a frontier model and which run on a cheap one,
   measured per question band. This is the measurement with a real spread behind it.
3. **The two corpus controls.** OCR tax and translation tax, both carried by Three Kingdoms.
4. **The contamination probe.** Free generation versus fact-row composition, deerstalker incidence.

**Withdrawn 2026-08-28: the LitBank head to head**, which was item 2 and the anchor of this phase.
The claim it tested is occupied and its premise was factually wrong, and LitBank could not have
measured it in any case: 96 of its 100 documents are exactly two chunks at GraphRAG's default, and
the effect compounds across many chunks. Nothing replaces it this semester.

**The one paid benchmark worth running is LongMemEval**, because it is where the assistant claim
lives and where Zep published comparable numbers. It was missing from the previous version of this
plan, which is a reconciliation error against `02_requirements_and_testing.md`.

**Cut, not stretched.** NarrativeQA across three injection arms and the four-arm ablation are
removed. They were listed as stretch goals in the previous version and are not in the committed
scope; carrying them as aspirations is how the schedule became a factor of three oversubscribed.

**The overlap is real and is stated rather than hidden.** Three weeks of build and one week of
measurement, with a homework set on November 1 and quizzes on the 8th and 15th, is tight to the
point of implausibility. That is what the cut order below is for.

---

## The cut order, decided in advance

The calendar guarantees at least one real week will disappear: four or more drill weekends at
unknown positions, another course's midterm and final on unknown dates worth nearly half that
grade, an unread family calendar, and a documented pattern of crashes after sustained grind. **A
lost week deletes from the bottom.**

1. The signed proposal and the meeting package. Survives anything; nothing may displace it.
2. The instruments on the live prototype: consult-logging, miss rate, stale-serve rate,
   corrected-facts band. These run in evenings while coursework owns the weeks, and they are the
   paper.
3. The design document and the segmentation spec. These fit campus gaps and dead stretches by
   construction.
4. The pipeline slice (interfaces, adapters, splitter, ingest and organize on one corpus), if and
   only if the October 19 to November 15 block survives intact.
5. Everything else, in any order, because none of it is load-bearing this fall.

When a week vanishes, layer 5 is already gone, layer 4 shrinks stage by stage in reverse build
order (organize before ingest), and layers 1 through 3 do not move. Phase 3 as written quietly
depends on layer 4 existing; under this order the paper depends only on layers 1 through 3.
Anything cut is cut in the log the day it is cut.

---

## Cost model

Rates were fetched 2026-08-27 and are **perishable**. One caveat carried from the source document:
the Anthropic rates came from a table cached 2026-06-24, two months older than the stated fetch
date, and the Google page rendered a header dated in the future. Re-check every figure before it
enters a budget or a paper.

Per unit the pipeline makes one entity pass, one fact pass, and N cell calls where N is the number
of above-threshold nodes in that unit. **Each call re-sends the unit text.** Oz sizing: about 600
units, 1.27M words, roughly 1.7M tokens, about 2,800 tokens per unit, about 5 major nodes per unit.

| Per unit | Input | Output |
|---|---|---|
| entity pass | 2,700 | 300 |
| fact pass | 2,700 | 600 |
| 5 **separate** cell calls | 13,500 | 1,250 |
| total, separate | **18,900** | **2,150** |
| total, **batched** (one cell call) | **8,100** | **2,150** |

Over 600 Oz units that is **11.3M input separate against 4.9M batched**, with output unchanged at
**1.29M** either way, because batching changes how often the unit text is sent, not how much text
comes back. Across all four corpora, roughly 3,200 units, batched: about **26M input and 6.9M
output**.

**Three numbers in the previous version were wrong and are corrected here.** Batched Oz output was
given as 1.5M; it is 1.29M, and it is identical to the unbatched figure. The saving was described
as "roughly 3 times"; it is 2.33 times on total input and 5 times on the dominant cell-input term.
And the provider spread was called "roughly 70 times"; the same table's endpoints are $335 and
$2.30, which is **146 times**.

Full four-corpus run, batched where a batch discount exists:

| Provider | Model | Full run |
|---|---|---|
| Anthropic | Fable 5 | $335 |
| Anthropic | Opus 5 | $168 |
| OpenAI | gpt-5.6-sol | $134 |
| Google | Gemini 3.1 Pro | $126 |
| xAI | grok-4.6 (no batch) | $102 |
| Anthropic | Sonnet 5 | $67 |
| Google | Gemini 3.5 Flash | $56 |
| Anthropic | Haiku 4.5 | $34 |
| Google | Gemini 2.5 Flash | $14 |
| OpenAI | gpt-4o-mini | $4.40 |
| OpenAI | gpt-5-nano | $2.30 |

**Oz alone, batched:** about $6 on Haiku, $13 on Sonnet 5, $32 on Opus 5. **The pilot is about $3**
for all three tiers over Oz book 1.

**What the spread changes.** A 146-fold gap is not an academic question about which stages need a
frontier model, it is the difference between a corpus that can be re-run every time the pipeline
changes and one where iteration is rationed. **And the binding constraint remains hours, not
dollars**, which the feasibility review concluded from the other side.

**Why not run everything on the top tier.** The cost is survivable; the methodology is not. The
contribution is measurement, and "we ran it on the best model available" reports a ceiling and
gives a reader nothing to act on. The spread is the finding. Iterate on the cheapest tier that
works, report at minimum two tiers, and reserve the top tier for the judge, which must differ from
every writer anyway and is cheap because judging is far fewer tokens than generating.

**Two operational constraints.** The prototype's fact layer has failed twice on credit balance, so
instrument spend per run and set a hard stop before starting a full pass; the `Run` record already
carries the token counts, so this is a query rather than new logging. And local models will fail on
format rather than comprehension: the feasibility review predicts 30 to 40 percent rejection on
strict nested JSON from 7B instruct models, and grammar-constrained decoding makes malformed output
structurally impossible. Measure format failure and comprehension failure separately, because they
have different remedies.

---

## What "ultimately a desktop RAG backend" changes

- **The storage port exists from day one.** The spring swaps the adapter; the fall must not call one
  directly.
- **Files, not Neo4j.** The distributable is a folder someone points a client at. A server
  dependency now becomes a port later.
- **The MCP shape informs the retrieval API.** The twelve port operations should map cleanly onto
  tools a desktop client can call.
- **Single-user, single-workspace assumptions are fine.** Multi-workspace partitioning is filesystem
  separation in the spring, not a policy layer now.

---

## Realistic outcome

**One instrument, measured on one corpus, plus a published dataset.** That is a workshop paper or
an arXiv preprint supporting an application. It is not a top-conference submission, and planning
for one produces neither.

The feasibility review priced the honest demand at 225 to 375 hours against 70 to 100 available,
and dated the first unrecoverable break at September 15 to 21. Nothing since has changed that
arithmetic. What has changed is that the cost side is now known and small: the full four-corpus run
is $34 to $67 batched, and the pilot is $3.

**Hours are the binding constraint. Cut scope, not measurement.**
