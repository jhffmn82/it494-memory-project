# The paper's argument

**2026-08-27, revised 2026-08-28.** What survived an adversarial novelty search in which seven
candidate contributions were found occupied, plus a second pass on 08-28 that killed one more.
This is not a positioning statement written to fill a gap. It is what is left standing.

The revision is narrower than the version it replaces, in four specific ways recorded at the
bottom. Read those before reusing anything from an older draft.

---

## The claim

> **Pre-determined, unit-level entity salience driving extraction, versus per-chunk extraction.**

Both published baselines extract chunk-first, and both were verified against their own papers
rather than recalled:

| System | Extraction order | Verified against |
|---|---|---|
| GraphRAG | splits documents into text units first, then extracts entities from **each unit separately**; there is no document-level entity pass | Edge et al. 2024, sections 3.1.1 and 3.1.2, and Microsoft's indexing documentation |
| Zep | per episode, with the previous **four messages** as context, then resolves candidates against the graph | Rasmussen et al. 2025, section 2.2.1, p. 3 |
| **This project** | scan the unit, establish the cast, condition everything downstream on it | the thing under test |

The claim has a mechanism (a unit-level cast list passed into every downstream call), a measured
consequence (duplicate minting rate, entity F1), and gold data to score against (LitBank: 100
public-domain works, 210,532 tokens, with entity, coreference, event and quotation-attribution
layers over the same fixed texts).

It is one comparison, on one axis, against two shipped systems. That is the whole contribution and
the paper should not reach for more.

---

## What the argument is, in four moves

**1. The requirements are real, and the field says so, not the author.**

Seven requirements, each sourced to a published paper stating the problem is unsolved. They are
set out with their citations and their tests in `02_requirements_and_testing.md`.

This is **motivation, not contribution**, and it must be labelled that way in the paper. An earlier
draft derived the requirements from a two-year personal deployment and validated them against the
literature. That is a wish list with a case study attached, and a reviewer answers it with *says
who?* The deployment corroborates in one sentence and does not authorise.

Labelling it as motivation is also now forced rather than merely prudent. *Are We Ready For An
Agent-Native Memory System?* (arXiv:2606.24775, June 2026) decomposes agent memory into four
modules, then evaluates twelve representative systems plus two baselines across five workloads
spanning eleven datasets, with ablations on representation fidelity, retrieval precision, update
correctness and long-horizon behaviour. That is the requirements-plus-measured-coverage move,
executed empirically and at a scale this project will not match. Cite it as motivation. Do not
compete with it silently.

**2. Nothing in the architecture is claimed as new, and the borrowing is named.**

Hierarchical summaries from GraphRAG and RAPTOR. Temporal facts and invalidation from Zep and,
underneath it, bitemporal modelling. Community summarisation from GraphRAG and, as corrected
below, from Zep as well. Per-document per-entity summarisation from EntSUM. Per-entity chronology
from timeline summarisation. Online maintenance from MemTree and Graphiti. Property graph
structure and the edge-typing constraint from Angles. Ranks and qualifiers from Wikidata.

Naming the borrowing is the strength. A paper that shows only what was built reads as naive; one
that draws the line explicitly reads as someone who did the survey, which is what happened,
adversarially, with the results recorded below.

**3. Measure what one design decision costs and buys.**

Two ablations, ranked by what they cost:

| Ablation | Cost | Notes |
|---|---|---|
| **Entity-first versus chunk-first extraction** | nearly free | LitBank supplies gold entities and coreference: precision, recall, F1, no question authoring, no judge. Head-to-head against GraphRAG's shipped pipeline order. The duplicate-minting curve falls out of ingest for nothing |
| **Tier allocation per stage** | free | Falls out of running anything; the cost arithmetic is in `05_fall_plan.md`. Asymmetric Capacity Allocation (arXiv:2608.21345) covers adjacent ground and must be cited |

Do both. There is no third.

**4. Evaluate on literature, because it has ground truth the assistant case cannot.**

And render the output as a wiki, because a page is auditable in a way a chat answer is not.

| Arm | What it is | What it measures |
|---|---|---|
| Assembled | fact rows and cells, composed mechanically | what the store holds |
| RAG-generated | a model querying the backend | what an assistant built on it would say |
| The gap | claims tracing to neither a fact row nor a cell | the unsupported-claim rate **of this rendering path on this corpus** |

The last row is why the wiki belongs in the paper rather than only on a poster. State it narrowly.
It is not "the assistant's fabrication rate"; it is one rendering path on one corpus, and the
generalisation from there to assistants at large is exactly the step a reviewer will refuse.

Nor is the assembled arm zero-fabrication. It is **100% traceable by construction**, because a
claim with no matching quote is never emitted. Traceable is not the same as true: the edge-typing
constraint exists precisely because a fabricated relation can carry a perfectly genuine quote, and
`parent_of` between a place and a thing passes every other check in the system. Claim traceability,
which is defensible and unusual, and do not claim correctness, which is neither.

Requirement 3 is the strongest position in the paper and it is worth being precise about why.
FABLES reports the best automatic faithfulness checker reaching 58.2 F1 with the entire book
available. The check here is exact string matching: not a classifier, not a judge, a `find()`. That
is not a better classifier, it is a different kind of guarantee, and it should be framed that way
rather than as a score comparison.

---

## The framing, and it is load-bearing

*"Here is our backend, and we measured it"* is a system paper and dies on prior art.

*"Here are measured tradeoffs in this design space, demonstrated on a working backend"* is an
empirical study and survives, because the contribution is the measurement.

The difference appears in the first paragraph, so it has to be decided before one is written.

**This framing was checked, and it places.** Empirical and design-space studies appear at the
venues this work would target: *How Memory Management Impacts LLM Agents: An Empirical Study of
Experience-Following Behavior* (ACL 2026), *Searching for Best Practices in Retrieval-Augmented
Generation* (EMNLP 2024), *The Power of Noise: Redefining Retrieval for RAG Systems* (SIGIR 2024),
*Seven Failure Points When Engineering a Retrieval Augmented Generation System* (CAIN 2024), and
the VLDB Experiment, Analysis and Benchmark track as the data-management template. Benchmarks place
too: MemoryAgentBench at ICLR 2026.

The flip side of the same finding is the real constraint. This niche is being occupied right now by
studies larger than this one. The differentiator cannot be breadth of systems compared. It has to
be the instrument: gold-annotation, entity-level scoring of extraction ordering, which none of the
large comparisons do.

---

## The novelty record

Adversarial full-text queries against the arXiv API, written to find the paper that scoops the
project rather than to map the field. The August 19 survey ran seven agents and verified 33
citations, and missed nearly all of the papers below. A survey asking "what is this field" and a
search asking "what kills this claim" return different sets, and only the second one protects a
contribution. That is a methods finding independent of the result.

**Proactive recall. Taken.** The original claim was that every published memory benchmark
presupposes a question is asked, so a memory that is complete, indexed and never consulted fails no
existing benchmark. That sentence is false as of May 2026. CogniFold (arXiv:2605.13438) presents an
always-on agent memory that continuously folds fragmented event streams into self-emerging
structures, extends Complementary Learning Systems theory, and surfaces intents on concept-cluster
density; it ships code and evaluates on LoCoMo and LongMemEval. ProactAgent (arXiv:2604.20572)
takes the measurement, learning when to retrieve by comparing paired continuations from identical
prefixes with and without retrieval, which is the counterfactual miss rate as a learned policy.
ENPMR-Bench (arXiv:2605.27240) is a benchmark for proactive memory retrieval, and its existence
alone falsifies the "no benchmark can express this" framing. Also nearby: ProMem (2601.04463), PASK
(2604.08000), VitaBench 2.0 (2605.27141), Proactive Memory Agent (2607.08716).

**Cold-start structure induction. Taken.** AutoSchemaKG (arXiv:2505.23628) is fully autonomous KG
construction that induces schemas directly from text, at fifty million documents, reporting 92
percent semantic alignment with human-crafted schemas at zero manual intervention. SCOPE and SCION
(arXiv:2607.21610) make schema induction a measured benchmark with released baselines. EvoTaxo
(arXiv:2603.19711) builds and evolves taxonomies from temporally ordered streams, which is the
living-tree idea applied to taxonomy. From Strings to Things (arXiv:2607.00003) builds personal
knowledge graphs from unstructured conversational data. BoostTaxo (2605.12520) does zero-shot
taxonomy induction, and Bian et al. (2510.20345) survey the whole space.

**Covering versus partition. Taken, on 08-28.** This was carried as the surviving secondary claim
on the strength of an assertion that every hierarchical memory system partitions. That assertion is
false, and the refutation was on disk in this repository the entire time. RAPTOR: "nodes can belong
to multiple clusters without requiring a fixed number of clusters ... thereby warranting their
inclusion in multiple summaries" (ICLR 2024, p. 3), and this project's own one-pager for it already
said so. CAM (Li et al., NeurIPS 2025, arXiv:2510.05520) combines incremental overlapping
clustering with hierarchical summarisation and online batch integration in agentic memory,
evaluated against RAPTOR, GraphRAG, HippoRAG, MemTree, MemGPT and ReadAgent on NovelQA, QMSum,
FABLES and MultiHop-RAG. The only daylight was that CAM and RAPTOR derive overlap from
embedding-space similarity while this design derives it from a pre-determined entity cast. That is
a variant of an occupied idea, and it is the same class of narrow distinction this project already
downgraded once. **Keep the covering design, claim nothing for it.**

**A literary memory benchmark. Largely taken.** NarrativeXL (Findings of EMNLP 2023) is 1,500
hand-curated Gutenberg fiction books with 990,595 questions carrying an explicit retention demand,
purpose-built as a long-term-memory dataset. MemoryAgentBench includes temporal recall over novels.
CAM scores memory backends on NovelQA and FABLES. StoryBench (2506.13356) builds a long-term-memory
benchmark on interactive fiction. The corpus-as-a-resource angle should shrink to one sentence.
What is genuinely left is narrow and worth stating precisely: no benchmark found pairs gold
structural annotation over literary works with a persistent, incrementally updated backend and
supersession scoring. That is a test-instrument gap, not an unused corpus.

---

## Corrections carried into this revision

Four things in the previous version of this document were wrong. They are recorded rather than
quietly fixed, because the pattern matters more than the individual errors.

1. **Zep was said to lack community detection and hierarchical summarisation.** False. Its
   community subgraph nodes "contain high-level summarizations of these clusters," built with
   detection that "builds upon the technique described in GraphRAG" using label propagation rather
   than Leiden. The claim came from reading the Graphiti README instead of the Zep paper. The
   correction was then itself overstated as "extends dynamically without full refresh"; the paper
   says communities gradually diverge and "periodic community refreshes remain necessary."
2. **"The best single system covers five or six of nine" was never computed.** The coverage matrix
   was drawn with empty cells and a score asserted over them. The sentence is **deleted**, not
   repaired. Filling forty-nine cells to a standard that survives a reviewer is a research project
   in itself, and 2606.24775 has already done the defensible version. There are also seven
   requirements, not nine.
3. **The assembled-versus-RAG gap was called "the assistant's fabrication rate."** Narrowed above
   to one rendering path on one corpus.
4. **The requirement list was said not to exist yet, and to be the author's to write from his own
   deployment.** It exists, in `02_requirements_and_testing.md`, sourced to literature.

The standing method rules that came out of these, and out of two occasions where "no records
found" was read as absence when the material was on Project Gutenberg the whole time:

- An absence claim requires a documented search. Never assert that nobody has done X without
  reporting how you looked.
- Run a control query before trusting an empty result set.
- State the source type for every factual claim: full text, abstract, README, or memory. A README
  is not the paper.
- Never emit a number you did not compute.

Both original contributions were absence claims, and both were false. The third, covering versus
partition, was also an absence claim, and it was false too. Absence claims are the weakest thing
this project can assert and should be the first thing an outside reader attacks.

---

## What could still kill this

- **The extraction-ordering result comes back null.** Entity-first may simply not beat chunk-first
  on LitBank at the corpus sizes reachable this semester. This is the real risk and it is a real
  finding either way, provided the paper is framed as a measurement rather than as a system.
- **A larger design-space study lands on this axis first.** The field is publishing fast enough that
  any novelty check goes stale in about three months. CogniFold was three months old and invisible
  to both a seven-agent survey and to an assistant whose training data predates it. Re-check
  immediately before posting, adversarially, not as a field survey.
- **The comparison is judged unfair.** GraphRAG's own evaluation is LLM-judged on self-generated
  questions over podcast and news corpora, so it cannot be reproduced fairly; this project competes
  with it on gold-annotation metrics instead, and must say plainly that this is a different
  measurement rather than a better score on theirs.
