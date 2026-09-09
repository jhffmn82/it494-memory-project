# Publishability review: scope, rigor, feasibility, and the paper a reviewer can't dismiss

2026-09-08. An adversarial read of the project as a fall paper, written to find what a hostile
reviewer breaks first and what survives. Assistant review; recommendations are PROPOSED.

## Bottom line

**There is a publishable paper, and there is a floor that de-risks "no paper at all."** The floor
is the ThreadAtlas Step 0 dataset — MIT, public, reproducible, 19,436 documents with a verified
tiling contract — which is a resource contribution already in hand. The ceiling is a systems /
experience paper: *a provenance-total, merge-free memory backend, and a measurement of what each
mechanism buys.* The risk is not that the work is unpublishable. The risk is **scope overrun**: the
numbers the strong paper needs depend on parts not yet built, against a calendar that already does
not close. The move is to pick the defensible spine now and cut to it.

The single most important correction: **your headline measurement describes a system you deleted.**
Fix that first; everything else is downstream.

## 1. What kind of paper this is

Settled correctly on 2026-08-28: twelve candidate contributions searched, all occupied, so novelty
is not the claim. The venues that fit say so in writing (PVLDB "interesting and effective
combination"; NeurIPS "originality does not require a new method"; SIGSOFT lists "not the first
solution" as an invalid criticism) and name the price in the same sentence: **less novelty demands
more rigorous evaluation.** So this is a systems-and-experience paper for a resource / in-use /
demonstration track, not a novel-method paper for a main track. That decision is right and should
be stated in the introduction before a reviewer states it for you.

Two consequences a reviewer will hold you to:
- Every mechanism is borrowed; concede it up front, with citations (hierarchical summaries from
  GraphRAG/RAPTOR, dated facts from Zep/Snodgrass, per-character summaries from EntSUM, incremental
  update from MemTree, ranking from Wikidata). You already have this list.
- Rigor is now the entire grade. A thin or single-run evaluation is fatal in a way it would not be
  for a novel-method paper, because rigor is the thing you traded novelty for.

## 2. The one contribution to own, restated for the tree

The old position — "resolution scores name + co-occurrence + profile, and I measure whether the
relational signal pays" — is dead, because the September tree decision removed the weighted scorer.
The system no longer merges: it attaches a child to a parent by a re-pointable up-edge, and
within a document it nominates pairs and asks a judge. A reviewer who reads the code and then the
old slate sees a paper measuring a component that does not exist. This is the first thing to fix.

**The restatement is stronger than what it replaces.** The ownable contribution is now:

> We do not merge. Identity is a forest of per-document children under parents that assert nothing.
> Here is what that costs at query time (a one-hop traversal instead of a stored answer), and here
> is what it buys that a merged store cannot have: append-only insertion, correct deletion, total
> provenance, and disagreement kept visible.

That is a systems claim with measurable costs and benefits, and it dissolves three problems the
literature calls open (incremental insertion, deletion/forgetting, the synthesized-layer faithfulness
gap) rather than beating anyone on a leaderboard. The honest metric is **attachment accuracy**: how
often the up-edge puts a child under the right parent, scored against gold coreference (BookCoref,
not LitBank — LitBank's books are two chunks). That is a cleaner question than "did the merge lose
something," and it needs no judge model to score.

**Ruling this forces (the open one from the doc review):** restate the resolution ablation at the
up-edge — name-only vs name+co-occurrence vs name+profile as inputs to the attachment decision,
scored as attachment accuracy — rather than dropping it. Co-occurrence and profile survive as
signals; the citations (Bhattacharya-Getoor 2007, the black-hole guards) still hold; and the tree
makes the replay honest, because re-pointing an edge is not a destructive merge. Recommendation:
restate, do not drop. The measurement is the paper's spine.

**One unsearched claim to close before the paper.** The tree formulation — a parent that holds
nothing, edges all document-owned — is recorded in `docs/entity-resolution.md` as *unsearched*.
Given that twelve of twelve prior claims died on the assumption nobody had done it, and the one
claim nobody searched is the one that survived and later fell, this must be searched before it goes
near the paper. Likely-occupied terms: singleton/canopy entity resolution, cluster representatives
without a centroid, Wikidata referenced statements, provenance-preserving ER, document-scoped
mention clustering with cross-document linking. Assume it is occupied and frame it as a design
position, not a novelty.

## 3. Rigor — what is genuinely strong, and what gets ripped

Strong, and rare for a student project:
- **The quote gate.** Every stored fact resolves to verbatim source at document offsets. A reviewer
  who spot-checks a quote finds it. This is the backbone of the provenance claim and it holds.
- **Verified data contract.** Tiling, kind purity, unique ids, offset round-trip — all checked at
  export on all 19,436 documents, not asserted.
- **Per-tier cost, measured from call logs**, not estimated. The three-tier report is a real
  finding (accuracy per token) and it is the argument for a serverless design.
- **The correction/verify pass and classified rejections.** Unsupported facts are reworded or
  dumped, not shipped with a flag. That is a stronger honesty discipline than most extraction
  papers show.
- **A mutation-testing habit** (a gate must be proved to fail on an injected defect before it is
  trusted) that most reviewers never see in a systems artifact.

What a reviewer rips, each with the fix:

| Attack | Reality | Fix |
|---|---|---|
| "Your numbers aren't reproducible — the same document came back 57, then 72, then 61 entities." | The model is non-deterministic; run-to-run variance is real and you recorded it. | Report every headline number from one stated run **with a variance band** over k reruns on a sample. Never quote a bare number. This is non-negotiable for the rigor-priced track. |
| "A quarter of your stored facts were not stated by their own quote." | 20.4% unsupported after the framing fix; the correction pass now rescues or drops them. | Report the rescue/drop split per corpus per tier as an **instrument**, not a defect. Unreported, it is the first thing a checker finds. |
| "Supersession fires on nothing — there's no functional-predicate list." | True today; predicates are stored as the model wrote them. | Hand-write the functional list for the benchmark predicates, and report supersession beside its denominator (which predicates, what fraction of scored questions touch one). Without this, the knowledge-update band measures nothing. |
| "Cross-document 'what is true now' has no mechanism — parents don't adjudicate." | The read-time view over a parent's children is designed but unspecified. | Specify it as a read rule (collect the children's facts on a functional predicate, apply voice then time, serve all with ordering). This is the second open ruling. |
| "No gold segmentation — your split is unvalidated." | Correct; there is no gold. | Do not claim segmentation quality. Claim the internal contract (tiling, offsets, kind purity) and cite BookCoref for the one thing that has gold: coreference/attachment. |
| "Terra cost is inferred." | Its output price was 71% of a run's reported cost and is not read from the page. | Read it, or state every terra-heavy figure as an upper bound. Trivial to fix; embarrassing if caught. |

## 4. Feasibility — the calendar does not close, and the critical path is unbuilt

This is the hardest truth in the review. The slate is priced at **69–118 hours against 64
available**, and the 8-hour week is itself unverified. Worse, the gap is not in the optional items —
it is on the critical path to a single publishable number.

**Built and run:** the extractor (1.5, whole corpus, $7.72) and the ingestor (0.9, sample runs,
$11.47 / $1.91). These produce **packages** — per-document JSONL — not a queryable store.

**Not built, and every benchmark arm depends on all of it:** the SQLite store, the global tree
(Step 2 attachment across documents), search/retrieval, and the GraphRAG-Bench / LongMemEval /
NarrativeQA arms. The wiki and the alias set are also unbuilt. So the distance from where you are to
"one GraphRAG-Bench number exists" is the store **plus** the global tree **plus** retrieval **plus**
the arm — the four largest unbuilt pieces — and the arm is what the paper's central table needs.

The cut order in the README is right in spirit but should be made sharper against this reality:

- **Protected core (the paper cannot exist without these):** the store, the global tree-attach, one
  retrieval path, the GraphRAG-Bench arms with the plain-RAG parity check, the attachment-accuracy
  measurement (the restated resolution contribution), the free cost/coverage instruments, and the
  paper. That alone is most of the 64 hours.
- **Cut early and without regret if a week is lost:** LongMemEval (needs the functional list and a
  loader; it is the arm most likely to measure nothing), the cells ablation, the wiki beyond one
  showpiece page, NarrativeQA. These are additive, not spine.
- **The dataset resource paper is the floor** and it is already shipped. If the store-plus-arms
  path slips past November, the publishable output is the dataset + the extractor/ingestor
  experience report + the merge-free architecture position, with the measured cost curves. That is
  a real resource/experience paper and it does not depend on the unbuilt half.

Recommendation: **decide the floor explicitly now.** If the honest read of the hours says the four
unbuilt pieces will not all land clean, aim the paper at the dataset + architecture + cost story
(which is in hand) and treat one GraphRAG-Bench arm as the stretch, not the spine. A thin version of
the ambitious paper loses; a complete version of the modest paper wins.

## 5. Publishability — venue, posture, and the mechanics

- **Track:** resource / experience / in-use / demonstration. Not a main research track.
- **The contamination answer travels with every result** and is sound: GraphRAG-Bench chose
  pre-1900 novels to limit pretraining overlap; every committed comparison is arm-vs-arm over
  identical text so both arms are equally contaminated; NovelQA shows models know famous plots but
  fail on depth and minor characters, which is where the store competes; the deerstalker probe
  catches weight leakage directly. Keep all four.
- **The judge discipline** (the scoring model never shares a tier with a writer, calibrated on a
  hand-labeled sample) is correct and must be stated.
- **Mechanics with lead time, in order:** the arXiv cs.CL **endorsement email to Dr. Fang is still
  unsent** and is the single longest human dependency — first-time submitters cannot post without
  it and an ISU address does not grant it. Send it now. Repo public (done). Dataset DOI via Zenodo
  by mid-November. Preprint to arXiv as a resource-and-experience paper, avoiding the Nov 23–27
  window. On the CV it goes under preprints with the dataset under research artifacts; do not
  miscategorize a preprint as a publication.

## 6. The reviewer's first ten questions, and your answer to each

1. *What is new?* Nothing, by design; the contribution is a working merge-free backend and a
   measurement of what each mechanism buys. (Concede novelty in the intro.)
2. *Then why should this be published?* Rigor over novelty, per this track's own guidelines; and a
   reusable public dataset.
3. *Your ablation measures a signal the system doesn't use.* — Fixed: restated at the up-edge as
   attachment accuracy. **(Do this or the paper fails here.)**
4. *Which run are these numbers from?* One stated run, with a variance band over k reruns.
5. *A quarter of facts aren't supported by their quote?* Reported as a rescue/drop instrument per
   corpus and tier; the correction pass is part of the pipeline.
6. *Where is "what is true now" computed if parents don't adjudicate?* A specified read-time view
   over a parent's children.
7. *Which predicates are functional, and how many questions touch one?* Named list, reported beside
   the denominator.
8. *No gold segmentation?* Correct; the claim is the internal contract plus BookCoref for coreference.
9. *Famous books — the model already knows them.* The four-part contamination answer.
10. *Is a parent that holds nothing actually new?* Searched before writing; framed as a design
    position, not a novelty.

Every one of these has an answer today or a cheap fix. None is fatal. The only fatal path is
leaving #3 as written and shipping the ambitious paper thin.

## 7. Decisions this forces

1. **Restate the resolution ablation at the up-edge** (attachment accuracy), do not drop it. Then
   the doc reconciliation of RESEARCH.md, docs/proposal.md, docs/entity-resolution.md and the README
   "borrow / measure" row follows in one pass.
2. **Specify cross-document supersession** as a read-time view over a parent's children.
3. **Decide the floor:** dataset + architecture + cost as the guaranteed paper; the GraphRAG-Bench
   arm as spine only if the store-plus-tree-plus-retrieval path is honestly reachable in the hours.
4. **Hand-write the functional predicate list** for the benchmark predicates.
5. **Send the arXiv endorsement email to Dr. Fang.** Longest lead, single human dependency, unsent.
6. **Search the tree formulation** before it goes in the paper.
7. **Read the terra output price.**

Items 1, 2, 4, 6, 7 are cheap. Item 3 is the one that decides whether November is calm or a
scramble, and it is a scoping call only you can make.
