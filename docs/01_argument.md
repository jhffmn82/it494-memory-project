# The paper's argument

**2026-08-27, revised 2026-08-28.** Nine candidate contributions have now been searched
adversarially and **all nine were occupied.** Seven fell on 08-26 and 08-27; covering versus
partition fell on 08-28; the extraction-ordering claim, which this document was previously built
around, fell later the same day.

This document no longer proposes a contribution. It records what was claimed, how each claim died,
and what survives that needs no claim at all. Do not reuse an older draft of it: every version
before 08-28 asserts things that are false.

---

## There is no surviving novelty claim. Read this before anything else.

The claim this document was built around was **pre-determined, unit-level entity salience driving
extraction, versus per-chunk extraction**. It was searched adversarially on 2026-08-28, the same way
the other eight were, and it died the same way.

It failed on three independent grounds, and the first one is the serious one because it is not
about prior art at all.

**1. The contrast is factually wrong. Both baselines are already entity-first.** This was checked
against the full texts in `papers/`, not recalled.

- **GraphRAG.** Its element-instance-generation appendix describes "a multipart LLM prompt that
  first identifies all entities in the text, including their name, type, and description, before
  identifying all relationships between clearly related entities." Entity pass, then relations. The
  paper also pre-empts the duplicate-minting objection directly: GraphRAG "is generally resilient to
  duplicate entities since duplicates are typically clustered together for summarization in
  subsequent steps."
- **Zep.** Its fact-extraction prompt reads `<ENTITIES> {entities} </ENTITIES>`, followed by "Given
  the above MESSAGES and ENTITIES, extract all facts pertaining to the listed ENTITIES." Entities
  are extracted, embedded, hybrid-searched against the existing graph and LLM-resolved **before**
  edge extraction. Zep is entity-first against a persistent global cast, not a four-message one.

So the difference was never the *order*. It was the *scope of the unit the entity pass covers*, and
"run the entity pass over a bigger unit" is not a contribution.

**2. The mechanism is published, repeatedly.** iText2KG (arXiv:2409.03284) accumulates a "Global
Document Entities" set and states that it is "provided as context along with each Semantic Block to
the Incremental Relations Matcher," for the same stated reason: unresolved entities produce
redundant relations. RAKG (arXiv:2504.09823) runs per-chunk recognition, then document-wide
disambiguation, then per-canonical-entity relation construction, explicitly framed against
GraphRAG's ordering, and beats it on MINE. LINK-KG (arXiv:2510.26486) builds a global
alias-to-canonical cache, rewrites every chunk against it, then runs GraphRAG.

**3. The ablation has been run and it came out against us.** iText2KG compared global-cast
conditioning against local-cast conditioning on two datasets. Global-cast conditioning scored
roughly **10 points lower** triplet precision: a richer graph carrying more irrelevant relations.
The related line does report gains, but through pre-extraction *coreference resolution* rather than
a cast list: LINK-KG cuts node duplication from 27.0% to 10.6% on short documents and 36.0% to
17.8% on long ones, and CORE-KG's ablation shows removing its coreference pass costs 28.25% more
node duplication. That is a different mechanism, and it is occupied three times over.

**And the measurement instrument does not work either.** See the LitBank section below.

### What follows from this

Do not repair the claim. Nine consecutive candidates have been searched and nine were occupied,
and the failure mode every time was asserting an absence without searching for it. A tenth
formulation invented at this point, without a search behind it, would be the same error again.

**The decision now is whether there is a project left once the novelty claim is removed, and that
decision is not the assistant's to make.** It belongs to Justin and his advisor. What can be said
is what survives regardless of framing:

- A working backend, built by hand, with a design that is defensible line by line.
- Four cleaned public-domain corpora published as a dataset. Useful reproducibility
  infrastructure, but see the correction below: this is **not** unoccupied ground.
- Measured per-stage cost and tier-sensitivity numbers across a 146-fold provider spread.
- A set of instruments that need no gold data: the quote gate, rejection rate per stage per tier,
  duplicate minting per unit, predicate sprawl, plot-versus-cell consistency.

That is an engineering project with measurements, which is what the advisor originally steered
toward twice, and it needs no novelty claim to be worth a semester. Whether it also wants a paper,
and what that paper claims, is the open question in `HANDOFF.md`.

**One genuinely unsearched question survives**, and it is recorded here as a question rather than a
claim: iText2KG's negative result was measured on short semantic blocks, and LINK-KG's positive
results came from a different mechanism. Whether cast conditioning helps or hurts **at book scale**,
across a hundred-plus chunks rather than two, is not settled by either. That question would need its
own adversarial search before anyone builds on it, and it would need a book-scale gold resource,
which LitBank is not.

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

**3. Measure what the design decisions cost and buy.**

The entity-first versus chunk-first ablation is **withdrawn**, for the three reasons at the top of
this document and because LitBank cannot carry it. What is left is free and still worth reporting:

| Measurement | Cost | Notes |
|---|---|---|
| **Tier allocation per stage** | free | Falls out of running anything; the cost arithmetic is in `05_fall_plan.md`. Asymmetric Capacity Allocation (arXiv:2608.21345) covers adjacent ground and must be cited |
| **Duplicate minting per unit, as a descriptive curve** | free | Falls out of ingest. Without gold and without a baseline arm it is a description of this pipeline's behaviour, not a comparison, and must be reported as such |
| **Rejection rate per stage per tier, predicate sprawl, quote gate pass rate** | free | Contract instrumentation; no dataset needed |
| **Plot-versus-cell consistency** | free | Two independent summaries over identical text, compared as sets. No judge, no ground truth |

### LitBank cannot measure extraction ordering, and this was computed rather than estimated

The parse was validated by reproducing LitBank's published totals exactly, 210,532 tokens and
29,103 mentions, before any of the numbers below were taken from it.

| Per document (n=100) | mean | median | range |
|---|---|---|---|
| tokens | 2,105 | 2,043 | 1,999 to 3,419 |
| **chunks at GraphRAG's 1,200-token default** | **2.0** | **2** | **2 to 3** |
| coreference clusters crossing a chunk boundary | 6.9 | 6.5 | 1 to 16 |
| cross-chunk clusters with more than one proper-name form | 3.6 | 3 | 0 to 10 |

**96 of 100 LitBank documents are exactly two chunks.** There is one boundary per document. Cast
drift and duplicate minting compound *across many* chunks, so on this corpus the phenomenon has
about three to six chances to appear and exactly one place to appear in. A null result would be
uninterpretable rather than informative.

Two further limits: LitBank's entity layer carries the same 2,000-word ceiling, and LitBank has **no
relation or triple annotation at all**, so there is no gold analogue for what a knowledge-graph
extractor actually emits. This is known ground: BOOKCOREF (ACL 2025, arXiv:2507.12075) exists
because "existing benchmarks, such as LitBank, remain limited in length and do not adequately assess
system capabilities at the book scale."

If a book-scale ordering experiment is ever wanted, BOOKCOREF is the resource (averaging over
200,000 tokens per document, roughly 170 chunks), with the caveat that its annotations are
pipeline-produced rather than fully manual. DocRED is **worse** than LitBank here, not better: it
has gold relations but its documents are roughly 200-word abstracts.

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

**Source types for everything added on 08-28**, per the standing rule that a claim must say how it
was read. Full text: RAPTOR (the PDF is in `papers/`), and the CHI EA 2025 interview study. Machine
extracted full text, not verbatim checked line by line: CAM. **Abstract only:** NarrativeXL,
StoryBench, Memora, *Are We Ready For An Agent-Native Memory System?*, ENPMR-Bench, CogniFold,
ProactAgent, AutoSchemaKG, SCOPE/SCION, EvoTaxo, and the rest of the occupied-contribution
citations below. Venues were confirmed through DBLP or the ACL Anthology rather than assumed.

An abstract-only read is enough to establish that a paper *exists and claims a thing*, which is all
an occupancy finding needs. It is not enough to quote a number from. Nothing in this document
quotes a number from an abstract-only source.

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

**The corpus as a resource. Also largely taken, and this one was asserted by me without a
search on 2026-08-28.** An earlier version of this document and of `HANDOFF.md` said the cleaned
corpora were "occupied by nobody." That was an undocumented absence claim, made while writing the
rule against undocumented absence claims, and it is false. Searched properly on 08-28:

- **GraphRAG-Bench** (arXiv:2506.05690) curated "pre-20th-century novels (narrative fictions) from
  the Project Gutenberg library, prioritizing lesser-known works to minimize overlap with
  pretraining data," explicitly to evaluate the whole pipeline "from graph construction and
  knowledge retrieval to final generation." Released, MIT licensed, 4,072 questions. That is
  Gutenberg curation plus contamination control plus KG-construction scope, already on the shelf.
  Its GitHub claims ICLR 2026; the arXiv Comments field names no venue, so treat that as
  unverified.
- **AffilKG** (Cai et al., **LREC 2026 main**, arXiv:2505.10798) ships six datasets pairing complete
  book scans and their OCR text with large labeled knowledge graphs, with a companion paper on how
  OCR and extraction error propagate into graph-level analyses. That is the OCR-tax idea, over
  books, at the venue class this paper would target.
- **STAGE** (arXiv:2601.08510) is 151 full-length English *and Chinese* screenplays on a
  "provenance-linked narrative backbone that recovers the state and epistemic access of each
  character," releasing cleaned scripts and curated graphs. Bilingual axis, provenance axis and
  supersession axis in one artifact, with gold annotation this project does not have.
- **CoSER** (arXiv:2502.09082, ICML 2025) covers 771 books and 17,966 characters, building
  character knowledge bases by "establishing name mappings between aliases and canonical names."
  The Tip-to-Ozma fixture is one instance of a problem that already has a 771-book resource.
- **The Standardized Project Gutenberg Corpus** (Gerlach and Font-Clos, *Entropy* 22(1):126, 2020)
  and **StonyBook** (arXiv:2311.03614) both established "cleaned Gutenberg as a resource
  contribution," at roughly 600 times this scale.

None of these were in `papers/`, `docs/` or `summaries/` before 08-28. What is left unoccupied is a
*composition* of individually occupied parts, and "novel combination of occupied components" is the
argument that killed claims one through nine.

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

## What already killed it, and what remains a risk

The first item is no longer a risk. It happened.

- **The extraction-ordering claim is dead.** Both baselines are entity-first, the mechanism is
  published three times over, the ablation has been run and came out negative, and the instrument
  cannot measure it. See the top of this document.
- **The surrounding niche is also occupied, and closely.** *Narrative World Model*
  (arXiv:2607.05577, July 2026) is writer memory for long-form fiction with a typed temporal-state
  graph, evaluated on a public fiction corpus against **Graphiti/Zep and GraphRAG** with a reader
  held constant, and it isolates extraction quality from representation by rebuilding the baseline
  with its own extractor. That is this project's niche, its baselines and its corpus type, published
  six weeks ago. Read it in full before any re-scoping decision; it is currently an abstract-only
  read and it is the most important paper on this list.
- **Any novelty check goes stale in about three months.** CogniFold was three months old and
  invisible both to a seven-agent survey and to an assistant whose training data predates it.
  Whatever the project ends up claiming, re-check adversarially immediately before posting.
- **One search hole is unfilled.** The Semantic Scholar API returned HTTP 429 on every attempt
  during the 08-28 pass, so that source contributed nothing. Everything above rests on arXiv, DBLP,
  the ACL Anthology, web search, and the PDFs on disk.

### Standing note on how these were found

Every one of the nine dead claims died to the same rule: **an absence claim requires a documented
search.** In three cases the refuting evidence was already on disk in this repository, in `papers/`
or in the project's own one-pagers. The searches that killed them were run adversarially, in a
context that had not been softened by the conversation that produced the claim, which is the only
method that has reliably worked here.
