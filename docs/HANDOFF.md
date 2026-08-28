# Handoff: read this first

**Written 2026-08-28 at the end of a long session, replacing the 08-27 handoff entirely.** This is
the one document that reflects where things actually stand. A fresh session should be able to start
from here without reading the rest.

---

## 0. Before anything else, check you are on the current clone

The last session opened a checkout **19 commits behind origin** and concluded, reasonably and
wrongly, that the handoff documents had never been written. They were on origin the whole time. Two
machines are in play and `maintain.py` pushes without ever fetching, so a stale local clone is the
default state here, not an unlikely one.

```bash
git -C ~/it494-memory-project fetch && git -C ~/it494-memory-project status -sb
```

If that says you are behind, pull before reading further. A handoff is useless if the next session
opens the wrong clone.

---

## 1. What this project is

A memory backend for a desktop RAG assistant: a `(unit × entity)` cell store where plot summaries
are the row marginals and per-entity narratives the column marginals, over an append-only temporal
fact layer with read-time supersession. Evaluated on public-domain literature because literature
supplies ground truth a personal archive cannot.

ISU MSCS directed project, Dr. Xing Fang supervising, fall 2026 plus spring 2027. Roughly 70 to 100
usable hours in two blocks, September 1 to 27 and October 19 to November 15. **Complete by November
15 or it does not count**, because December holds the PhD application window.

**Fang approved the topic change in person on 2026-08-28.** That gate is closed. Only the
one-semester proposal form may remain, on the Fang, then Hasselbring and Tang, routing.

---

## 2. The plan, settled. Do not re-open these.

1. **Build the store in `03_design.md`. Files backend only.** The Neo4j and Graphiti arm is **not**
   built this semester: it costs 75 to 120 hours, the comparison it existed for is occupied, and
   **Graphiti cannot satisfy invariants 2 and 3.** `add_triplet` runs node and edge resolution, so a
   supplied entity may be merged rather than stored as given, and it creates no episode node, so
   triplets carry no quote provenance. The two arms would have differed in semantics, not storage.
2. **Keep the storage port**, which keeps that decision reversible, and **write the conformance suite
   against the one adapter that exists**. It is **seventeen** operations, not the twelve this repo
   said until 2026-08-29, so roughly **14 to 21 hours** at one case per operation.
3. **Ingest sequentially, chapter by chapter, never in bulk.** A bulk-loaded book is static and
   exercises nothing temporal. Reading in order exercises both supersession mechanisms, and they are
   different operations: *the world changed* is computed supersession, while *we were wrong* (Tip
   was never a boy, he was Ozma enchanted) has no later event to supersede it and needs
   `rank: deprecated`.
4. **Evaluate on Infinity-Bench En.MC.** 229 questions, gold answers public, four-way exact match,
   no judge and no API cost, text ships with the benchmark, and the books are **entity-substituted**
   so contamination cannot confound the result. Three arms through one scorer: full system,
   no-context control (random is 25%, **and it goes in the headline table, not a footnote**), and
   flat chunk retrieval as the baseline the components must beat.
5. **The ablations are further arms on the same scorer**, which is what makes them nearly free: no
   salience threshold, no entity cells, no fact layer, no hash refold.
6. **Measure the temporal half on cost**, since no static benchmark reaches it: read-cost
   differential, refold cost under change, coverage differential. None of the three needs gold data.
7. **Run LongMemEval as the Zep head-to-head.** Zep is the closest published system and the only one
   whose numbers this work can be measured against directly. It is conversational, so the `session`
   value of `unit_type` has to actually work rather than merely exist in the enum.
8. **When a week disappears, cut from the bottom of the order in `05_fall_plan.md`**, decided in
   advance precisely so it is not decided under pressure.

**The four literary corpora are no longer load-bearing.** Infinity-Bench supplies the evaluation, so
they become an optional DOI'd dataset artifact that can ship or be deferred.

---

## 3. The thing a fresh session is most likely to get wrong

**Twelve candidate contributions were searched adversarially on 08-27 and 08-28. All twelve came
back occupied.** A thirteenth was invented by the assistant itself mid-session (the corpora
described as "occupied by nobody"), and it was also false.

**Do not generate claim thirteen.** Every one died the same way, by asserting an absence without
searching for it, and three were refuted by papers already sitting in `papers/`.

**And do not re-run the novelty test, because it was the wrong test.** The venues this project
should target waive method novelty in writing:

- **PVLDB:** novelty "often lies in the design, innovative system architecture, new abstractions, or
  interesting and effective combination of existing techniques."
- **NeurIPS 2026 reviewer guidelines:** "originality does not necessarily require introducing an
  entirely new method."
- **ACM SIGSOFT Empirical Standards** lists **"This is not the first known solution to the
  identified problem"** as an **invalid criticism**.

The price, from the same source: **"less innovative artifacts require more rigorous evaluations."**
Novelty and rigour are substitutes, and the novelty budget is spent. **The contribution is which
mechanisms carry the win, measured**, which requires building the system anyway. The degree project
and the paper are the same work. Venue is a system-demonstration track; full analysis in
`08_paper_options.md`.

---

## 4. What was wrong, and what each error propagated into

Kept because the pattern matters more than the individual fixes: each was load-bearing somewhere
else, so correcting the sentence did not correct the argument resting on it.

| Error | What it propagated into |
|---|---|
| Zep said to lack community summarisation, read from a README | The entire gap argument. Zep does have a community subgraph with hierarchical summarisation and incremental label-propagation maintenance |
| The correction to it was itself overstated | "Without full refresh" became "delays but does not eliminate it." The paper says periodic refreshes remain necessary |
| "Best single system covers five or six of nine" | Never computed. Deleted rather than repaired. There are seven requirements, not nine |
| Covering versus partition asserted as unoccupied | RAPTOR soft-clusters by design and this repo's own one-pager said so; CAM does incremental overlapping clustering |
| MemoryAgentBench "28% on fact update" | It is the multi-hop ceiling only. Single-hop reaches 78.0 at full length and 100 only on the 6K version, so the "78 to 100" range in earlier drafts spliced two context lengths; at full length most systems are far lower, Zep at 7.0 |
| "33 to 65% omit key events" attributed to BooookScore | It is FABLES. Both halves true, the attribution was not |
| "RAPTOR and GraphRAG name incremental insertion as unsolved" | Neither does. MemTree measured it and is the real source |
| Requirement 7 as "no benchmark can express this" | False. ENPMR-Bench is exactly that benchmark |
| **"Both baselines extract chunk-first"** | **The whole surviving claim.** Neither does: GraphRAG's prompt does entities then relations, and Zep's fact extraction is conditioned on a resolved entity list. Both papers were on disk the entire time |
| Cost model: 70x spread, 1.5M batched output, 3x saving | Real figures are 146x, 1.29M (unchanged by batching), and 2.33x on total input |
| "The corpora are occupied by nobody" | Asserted by the assistant with no search. GraphRAG-Bench, AffilKG, STAGE, CoSER and SPGC all bear on it |
| The 100K vector threshold, stated as rationale | Faiss's own paper puts it at **10k**, an order of magnitude lower. The decision still holds, on latency arithmetic |

### A second round of corrections, 2026-08-29, from a cold audit of the 08-28 work

The 08-28 revision was audited in a fresh context that was given no conclusions from it. It found
fifteen items. The five that mattered:

| Error | What it propagated into |
|---|---|
| **"CORE-KG's ablation shows removing its coreference pass costs 28.25% more node duplication"** | **Fabricated.** The figure is in no paper, and CORE-KG runs no ablation: its Table 1 is a between-systems comparison against a GraphRAG baseline (30.38% to 20.27%, a 33.28% relative improvement) on legal text. Taken from a subagent report and written into two documents without opening the PDF. It was one of four "independent killers" of the book-scale replication |
| **The A/B labels were inverted in the backend decision** | `03_design.md` §5 argued about Graphiti (deployment A) while saying "deployment B", and concluded "Drop B. Build A." Read with the document's own definitions that says drop the distributable and build Neo4j, the exact inverse of the decision. Two documents point readers there for it |
| The claim count contradicted itself four ways | Nine, ten, eleven and twelve, with one document managing all four. Twelve is right, derivable from the eleven-row table in `05_fall_plan.md` plus the self-asserted corpus claim |
| The 100K correction never propagated | Fixed in `03_design.md`, still asserted as rationale in two other documents, one of which also mis-stated where the corrected figure was cited |
| Two live documents did not ship in the package | `08_paper_options.md` and `09_evaluation_corpus.md` were never added to `SECTIONS` |

Also corrected: three documents disagreed on whether to run DMR; the storage port is **seventeen**
operations, not twelve, so the conformance suite is 14 to 21 hours rather than 10 to 15; "the number
nobody publishes" about refold cost is an undocumented absence claim that MemTree refutes with a
figure cited elsewhere in the same doc set; the `Run` record had lost `config_hash`, `tiers` and
`dollars`, so spend accounting was not the query the plan claimed; the cut order still called the
prototype instruments "the paper" after the scope decision ruled the prototype out as evidence; the
Chinese corpus figure was 4% high; and the pilot is about $2, not $3.

**The pattern in both rounds:** claims verified directly against a source held up, and roughly
thirty verbatim quotes survived the audit exactly. What broke was anything asserted from a
subagent's summary rather than a source, and cross-document consistency after rewriting eleven files
in one pass.

---

## 5. Open, in priority order

1. **Ask Fang for an arXiv cs.CL endorsement.** One email, and the only item depending on another
   person. First-time submitters cannot post without one and an institutional address does not grant
   it. Latest safe submission for December 1 visibility is **November 16**; avoid November 23 to 27,
   since arXiv defers around Thanksgiving.
2. **Read Story Ribbons in full** (IEEE VIS 2025, arXiv:2508.06772, now in `papers/`). The nearest
   peer-reviewed work: a scene-by-character cell matrix with **both marginals** composed from it,
   quote gate included, on 30 Gutenberg works. The real difference is that **it has no retrieval
   layer**, and that belongs in your introduction rather than in a reviewer's report.
3. **Read Narrative World Model** (arXiv:2607.05577, in `papers/`). Same niche, same baselines, same
   corpus type, six weeks old. Currently an abstract-only read.
4. **`data/clean/` violates the frozen contract and has no producing script.** 351 records over 16 of
   81 works, committed 08-27 as collateral inside an unrelated docs commit. No `unit_type`, no
   `unit_id`, and `chapter_ordinal` where the contract says `unit_ordinal`. Nothing in the repo or
   its history produced it, so it is not reproducible. Treat it as a scratch spike.
5. **Two unrevoked tokens: check which repository.** `06_spring_plan.md` attributes this to "the
   live archive", a different system. A pattern and filename scan of *this* repository's full
   history found zero matches, with a positive control confirming the search worked. Treat it as an
   open item **for the archive repo**, not this one, and verify there rather than here.
6. **`papers/MANIFEST.md` needs rebuilding.** It predates roughly half the current corpus.
7. **Make the repo public on September 1** if the JOSS route is ever wanted, since it needs six
   months of public history. Costs nothing now.

---

## 6. Standing method rules, each written after a specific failure here

- **An absence claim requires a documented search.** Never write that nobody has done X without
  reporting how you looked. Twelve contributions died to this, and three were refuted by papers
  already on disk.
- **Run a control query before trusting an empty result set.** Two corpora were reported unavailable
  when they were on Project Gutenberg the whole time, behind bad queries.
- **State the source type for every factual claim:** full text, abstract, README, or memory. A
  README is not the paper.
- **Never emit a number you did not compute.**
- **Extract and read the PDF. Never trust a fetched summary of a paper.** Five separate searches on
  08-28 caught their own tools **fabricating**: an invented venue for ENGRAM, an invented
  architecture for MEMTIER, invented conversation counts for a WildChat analysis, and a quote echoed
  back from the prompt that had requested it. Every one was caught only by extracting the source
  locally.

**The structural version, which is the only thing that has reliably worked here:** generate in one
context and refute in another that has not been softened by the conversation that produced the
claim.

---

## 7. Document map and repository state

| Document | What it is |
|---|---|
| `README.md` | The index, plus the standing style and voice rules |
| `01_argument.md` | Why there is no novelty claim, how all twelve died, what survives without one |
| `02_requirements_and_testing.md` | Seven requirements sourced to literature, and how each is tested |
| `03_design.md` | Schema, ingestion, retrieval, rendering, delivery |
| `04_unit_contract.md` | **FROZEN.** Eight convention handlers, three acceptance gates |
| `05_fall_plan.md` | Calendar, phases, cut order, cost model |
| `06_spring_plan.md` | The distributable |
| `07_references.md` | Schema prior art, every citation verified |
| `08_paper_options.md` | Whether there is a paper, and the venue analysis that reframes the question |
| `09_evaluation_corpus.md` | Infinity-Bench, LiteraryQA, the Zep comparison, why NovelQA is out |

`reference/` holds ten background files that were never superseded, including the only source for
the hour budget, the dead weeks and the risk register. `archive/` holds twenty-seven superseded
files, each with a banner naming its successor.

**State as of this handoff:** 130 papers on disk, all referenced, 7 retired to `papers/_unused/`.
87 one-pagers. The package builds to 206 pages with its contents verified entry by entry against
real section starts. Working tree clean, in sync with origin.

---

## 8. What to do first

**Not more research.** Build Phase 1: the splitter, against `04_unit_contract.md`, with
`data/clean/` regenerated from committed code so it meets the frozen contract. That is the gate on
everything downstream, it is first in the calendar, and after two days of literature search it is
the thing most at risk of being deferred again.
