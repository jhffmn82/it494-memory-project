# Handoff: where things stand

**Written 2026-08-28, replacing the 08-27 handoff.** Read this first. It records what is settled,
what was wrong, and what is still open. The document index is `README.md`.

---

## Read this before opening anything

**Check you are on the current clone.** This session opened a checkout that was 19 commits behind
origin and concluded, reasonably and wrongly, that the handoff documents had never been written.
They were on origin the whole time. Two machines are in play and the maintenance script pushes
without fetching, so a stale local checkout is the default failure mode here, not an unlikely one.

```bash
git -C ~/it494-memory-project fetch && git -C ~/it494-memory-project status -sb
```

If that shows you behind, pull before reading further. A handoff document is useless if the next
session opens the wrong clone.

---

## The plan of attack, locked

**A working backend, a published dataset, measured cost and tier numbers, by November 15.** The
novelty claim this plan used to carry is gone; see the next section. The build below is unchanged
by that, because none of it depended on the claim being true.

1. **Clear the administrative gate first.** The approved proposal on file is a survey of LLM and
   NLP tools on government documents. Everything in this repository is a different project, and
   nothing on record shows the topic change was ever approved. This blocks everything and is not
   an intellectual problem.
2. **Preprocess in September**, inside the first open block, and publish the cleaned corpora as a
   dataset. That publication is the reproducibility story.
3. **Pilot on Oz book 1 before September 27**, across three tiers, for about three dollars.
4. **Build October 19 to November 7.** Batch the cell calls from the start.
5. **Measure and write November 8 to 15.** The free instruments, per-stage tier sensitivity, the
   two corpus controls, the contamination probe, and LongMemEval as the one paid benchmark. The
   LitBank head to head is withdrawn.
6. **When a week disappears, cut from the bottom of the order in `05_fall_plan.md`**, which is
   decided in advance precisely so it is not decided under pressure.

The full calendar, hour budget, cost model and cut order are in `05_fall_plan.md`.

---

## The headline: there is no novelty claim left

Nine candidate contributions have now been searched adversarially. **All nine were occupied.** The
last one fell on 08-28, after this pass had already rewritten the argument document around it.

The surviving claim was *pre-determined, unit-level entity salience driving extraction, versus
per-chunk extraction*. It failed three ways, and the first is not about prior art:

1. **The contrast was factually wrong.** GraphRAG's own appendix says its extraction prompt "first
   identifies all entities in the text ... before identifying all relationships." Zep's
   fact-extraction prompt takes an `<ENTITIES>` block and extracts facts pertaining to them. **Both
   baselines are already entity-first.** The only difference was the size of the unit the entity
   pass covers, and that is not a contribution.
2. **The mechanism is published three times over.** iText2KG (2409.03284) accumulates a Global
   Document Entities set and feeds it to relation extraction. RAKG (2504.09823) does document-wide
   disambiguation then per-entity relation construction, explicitly against GraphRAG's ordering.
   LINK-KG (2510.26486) builds a global alias cache and rewrites every chunk against it.
3. **The ablation has been run, and it came out negative.** iText2KG compared global-cast against
   local-cast conditioning: global scored about **10 points lower** triplet precision.

**And LitBank could not have measured it.** Computed, with the parse validated by reproducing
LitBank's published 210,532 tokens and 29,103 mentions exactly: **96 of 100 documents are exactly
two chunks** at GraphRAG's default size. One boundary per document, against an effect that
compounds across many. LitBank also has no relation annotation at all. BOOKCOREF (ACL 2025) exists
precisely because LitBank is too short for book-scale work.

### What this means, and what it does not

It does not mean the project is dead. It means the project is **an engineering project with
measurements**, which is what the advisor steered toward twice, and which needs no novelty claim.
What survives regardless of framing:

- A working backend, built by hand, defensible line by line.
- Four cleaned public-domain corpora published as a dataset. Nobody occupies that.
- Measured per-stage cost and tier sensitivity across a 146-fold provider spread.
- Instruments that need no gold data: quote gate, rejection rate per stage per tier, duplicate
  minting, predicate sprawl, plot-versus-cell consistency.

**Do not invent a tenth claim.** Every one of the nine died the same way, by asserting an absence
without searching for it, and three of them were refuted by evidence already sitting in `papers/`.
A fresh formulation with no search behind it would be the same error a tenth time.

**One question is genuinely unsearched**, and it is written down as a question, not a claim:
iText2KG's negative result was on short semantic blocks and LINK-KG's gains came from a different
mechanism, so whether cast conditioning helps or hurts **at book scale**, across a hundred-plus
chunks, is unsettled. It would need its own adversarial search and a book-scale gold resource
before anyone builds on it.

**Read `Narrative World Model` (arXiv:2607.05577) in full before deciding anything.** It is writer
memory for long-form fiction, evaluated on a fiction corpus against Graphiti/Zep and GraphRAG with
the reader held constant, and it isolates extraction quality from representation by rebuilding the
baseline with its own extractor. That is this project's niche, baselines and corpus type, published
six weeks ago. It is currently an abstract-only read, and it is the single most important unread
paper on the list.

---

## What was wrong, and what it propagated into

The point of this list is not the individual errors. It is that each one was load-bearing
somewhere else, and fixing the sentence does not fix the argument that rested on it.

| Error | What it propagated into |
|---|---|
| Zep said to lack community summarisation, read from a README | The entire gap argument. If Zep already does hierarchical summarisation and incremental maintenance, "build the composition that covers the requirements" loses most of its force. The argument is now "nothing here is claimed as new," which is honest and much smaller |
| The correction to it was itself overstated | "Extends dynamically without full refresh" became "delays but does not eliminate full refresh." The weaker version is better for us: it means Zep also carries a batch refold |
| "Best single system covers five or six of nine" | Never computed. Deleted rather than repaired, because a defensible version of that coverage argument already exists across twelve systems (arXiv:2606.24775), and there are seven requirements, not nine |
| Covering versus partition asserted as unoccupied | Was the surviving secondary claim. RAPTOR soft-clusters by design and this repo's own one-pager said so; CAM does incremental overlapping clustering. The design stays, the claim goes |
| MemoryAgentBench "28% on fact update" | Requirement 1's urgency. It is the multi-hop ceiling only; single-hop reaches 78 to 100. Supersession is less obviously unsolved than the row implied |
| "33 to 65% omit key events" attributed to BooookScore | Requirement 4. It is FABLES. Both halves were true, the attribution was not |
| "RAPTOR, GraphRAG name incremental insertion as unsolved" | Requirement 5. Neither does. MemTree measured it and is the real source, which makes the row stronger than the version that was wrong |
| Requirement 7 as "no benchmark can express this" | An absence claim, and false. ENPMR-Bench is exactly that benchmark. Same failure mode, third instance |
| "Both baselines extract chunk-first" | The whole surviving claim, and the committed core measurement. Neither baseline extracts chunk-first: GraphRAG's prompt does entities then relations, and Zep's fact extraction is conditioned on a resolved entity list. This was in both papers, on disk, the entire time |
| Cost model: 70x spread, 1.5M batched output, 3x saving | The tier-sensitivity argument. Real figures are 146x, 1.29M (unchanged by batching), and 2.33x on total input, 5x on the dominant term |

All seven of the previous handoff's "unverified assumptions" are now discharged. Both Graphiti
questions came back usable: `EpisodeType.text` ingests plain text, and `add_triplet` accepts
pre-extracted entity instances, verified against source at commit `683a853`. All four uncertain
citations are resolved and citable.

---

## Open, in priority order

1. **What the project is now, given that there is no novelty claim.** This is the decision to walk
   into the advisor meeting with, and it is not the assistant's to make. See above.
2. **The administrative gate.** The approved proposal on file is still the government-document tool
   survey, and nothing on record shows the topic change was approved. Unresolved and blocking. See
   Phase 0 in `05_fall_plan.md`.
3. **Read Narrative World Model in full.** See above.
4. **`data/clean/` does not meet the frozen contract and has no producing script.** It holds 351
   records covering 16 of 81 works, committed on 08-27 as collateral inside an unrelated
   documentation commit. It has no `unit_type` and no `unit_id`, and uses `chapter_ordinal` where
   `04_unit_contract.md` says `unit_ordinal`. Nothing in the repository or its history produced it,
   so it is not reproducible. Treat it as a scratch spike and regenerate from a committed splitter.
5. **Two unrevoked tokens in pushed history.** Recorded in the risk register in
   `reference/00_design_brief.md` and again in `06_spring_plan.md`. Revoking is the fix; deleting
   the file is not, because the history still carries it. This is unrelated to the project's
   argument and should be closed anyway.
6. **`papers/MANIFEST.md` is incomplete**, 72 rows against 89 PDFs, and missing all four sources
   that `07_references.md` now depends on. Its header is corrected but the table is not rebuilt.
7. **The `Consult` logger** is a separate deliverable from switching consult-logging on, and only
   the latter is scheduled. The rate needs weeks of collection, so if it is going to happen at all
   it has to start early.

---

## What this pass changed

`docs/` went from 45 markdown files to nine live ones, plus `reference/` (still valid, never
superseded) and `archive/` (27 files, each carrying a banner naming its successor). Nothing was
deleted.

Seven parallel audits re-verified every factual claim against full paper text, source code, or the
publisher's page. The corrections are listed above and recorded inside the documents that carried
the errors, rather than quietly patched, because the pattern is more useful than the individual
fixes.

The build script shipped six superseded documents, missed every current one, and merged the
*previous* run's table of contents, so every page number after the fourth entry was wrong. Fixed
and verified: 201 pages, contiguous part numbering, and all 16 contents entries checked against
real section starts.

`SOURCES.md` still claimed Apollodorus and Water Margin were unavailable when both are on disk.
Corrected in place, with the wrong text struck through rather than removed, since they are the same
false-absence failure the method rules exist to prevent.

Three of 92 papers are genuinely unreferenced and moved to `papers/_unused/` with their one-pagers.
An initial pass said 23; that matched filename slugs only and produced a false positive for every
paper cited by project name or arXiv identifier. The corpus is almost entirely in use.

---

## The method rules, which are the actual deliverable

Every substantive error in this project has had the same shape: asserted without checking. These
are mechanical and checkable, and they belong in front of the next session.

- **An absence claim requires a documented search.** Never write that nobody has done X without
  reporting how you looked. Three contributions died to this rule and all three had been asserted
  without one.
- **Run a control query before trusting an empty result set.**
- **State the source type for every factual claim:** full text, abstract, README, or memory.
- **Never emit a number you did not compute.**

The stronger version is structural rather than dispositional. Generate in one context and refute in
another that has not been softened by the conversation. That is what the cold audit does in the
prototype, it is what the seven parallel audits did here, and it is the only thing that has
reliably caught this class of error.
