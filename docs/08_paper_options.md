# Is there a paper, and what is it?

**2026-08-28, count corrected 2026-08-29.** Written after twelve novelty claims were searched and
all twelve came back occupied. Sections below written on 08-28 say nine, ten or eleven as the count
rose during that day; twelve is the settled figure.
This document answers the question that follows: with no novelty claim, is there an honest paper
here at all?

> **SCOPE DECISION, Justin, 2026-08-28, and it overrides the recommendation below.** The personal
> archive is **not** an evaluation subject. Everything is tested against reproducible public-domain
> data. The deployment is design rationale only, never evidence.
>
> **Consequence, stated plainly: this rules out section 5, the one paper that survived.** The
> corroboration-inflation and over-merge findings exist only as measurements on a private corpus
> that nobody else can rerun. Ruling out the personal backend removes them. That is a defensible
> trade (it avoids a real reviewer objection about reproducibility and a real privacy problem), but
> it is a trade, and the cost is the only shape that came back with daylight.
>
> **The direction that replaces it, under search as of 2026-08-28:** a *lightweight personal-scale
> memory backend*, evaluated on the literary corpora. The thesis is that at personal scale the
> heavyweight machinery is unnecessary and the tradeoff is measurable. See the last section.

> **ANSWER REVISED 2026-08-28, and the revision is the important part of this document.**
> Everything below asks "is it novel?" That was the wrong test. Several of the venues this project
> should target reject it explicitly:
>
> - **PVLDB research track:** novelty "often lies in the design, innovative system architecture, new
>   abstractions, or interesting and effective combination of existing techniques."
> - **NeurIPS 2026 reviewer guidelines:** "Does this work offer a novel combination of existing
>   techniques... originality does not necessarily require introducing an entirely new method."
> - **ISWC In-Use:** novelty "in the application or assessment... their combination/interplay with
>   other technologies."
> - **ACM SIGSOFT Empirical Standards** lists **"This is not the first known solution to the
>   identified problem"** as an **invalid criticism**.
>
> The price is stated by the same source: **"less innovative artifacts require more rigorous
> evaluations."** Novelty and rigour are substitutes, the novelty budget is spent, and the paper is
> therefore paid entirely in measurement. See the final section.

**Short answer: one, and it is a spring project.** Five candidate paper shapes were searched
adversarially. Four are occupied or do not fit the hours. The fifth has genuine daylight, in a
place nobody was looking.

Every verdict below carries its evidence. Nothing here is asserted without a search, because the
absence claims that were asserted without one are what cost this project nine claims and, on
08-28, a tenth (the corpora were described in this repo as "occupied by nobody"; they are not).

---

## The five shapes, and what happened to each

### 1. Stage-wise model-tier sensitivity. OCCUPIED.

Which pipeline stages need a frontier model is a named subfield with accepted papers: LLMSelector
(ICML 2025), SCOPE (KDD 2026), Schnabel et al. (WWW 2025). *Asymmetric Capacity Allocation*
(arXiv:2608.21345) already claims the "first stage-wise model size study" flag and reaches the
operationally identical conclusion, that capacity should not be allocated uniformly.

The format-versus-comprehension split is occupied three times over, including by
`papers/tam2024-format-restrictions.pdf`, already on disk. And the 146-fold cost spread is a
liability rather than a hook: FrugalGPT opened with a two-orders-of-magnitude price spread in 2023,
and this project's own rates are perishable and two months stale.

**What survives:** tier-resolved duplicate-node-minting curves on long-form narrative. CORE-KG
measured that metric against component presence; nobody measured it against model tier. That is a
table in an engineering report, not a paper.

### 2. The corpus as a resource paper. PARTIALLY OCCUPIED, and thin.

- **GraphRAG-Bench** (arXiv:2506.05690) curated Project Gutenberg novels "prioritizing lesser-known
  works to minimize overlap with pretraining data," released for evaluating graph construction end
  to end. Gutenberg curation, contamination control and KG scope, already shipped.
- **AffilKG** (LREC 2026, arXiv:2505.10798) pairs complete book scans and their OCR text with
  labelled knowledge graphs, with a companion paper on OCR error propagating into graph analyses.
  That is the OCR-tax idea, published, at the venue class this paper would target.
- **STAGE** (arXiv:2601.08510): 151 bilingual screenplays on a provenance-linked narrative
  backbone, with gold annotation this project does not have.
- **CoSER** (ICML 2025): 771 books, alias-to-canonical character mappings.
- **SPGC** (*Entropy* 22(1):126, 2020) and **StonyBook**: cleaned Gutenberg as a resource
  contribution, at roughly 600 times this scale.

What remains is a *composition* of individually occupied parts. "Novel combination of occupied
components" is the argument that killed claims one through twelve.

**What survives, and it is worth doing anyway:** a DOI'd artifact release. Roughly 15 hours, no
novelty claim to shoot down, citable in December. And the cheapest real measurement available is
the OCR tax on Three Kingdoms, where proofread and OCR versions of identical content are already on
disk: one pipeline, two runs, one delta.

### 3. Book-scale replication of the cast-conditioning ablation. DO NOT PURSUE.

Four independent killers:

- **The instrument cannot measure the variable.** BOOKCOREF annotates only character coreference:
  no relations, no non-character entities. iText2KG's ablation metric is human-judged triplet
  precision. Swapping the outcome measure is not a replication.
- **The measurable half is largely predictable.** LINK-KG shows node duplication falling 27.0 to
  10.6 on short documents and 36.0 to 17.8 on long ones, and CORE-KG reports the same direction,
  30.38% to 20.27% against a GraphRAG baseline. **Corrected 2026-08-29:** this bullet previously
  claimed "CORE-KG already shows removing coreference costs +28.25% node duplication." That was
  fabricated; the figure is in no paper, CORE-KG runs no ablation, and its result is a
  between-systems comparison on legal text rather than a component removal on books. The bullet is
  weaker than it was: the direction is established between systems, not within one, and not on this
  corpus type. It is still one of four reasons and the other three stand on their own.
- **The corpus is maximally contaminated.** BOOKCOREF's three gold books are *Pride and Prejudice*,
  *Animal Farm* and *Siddhartha*. The model knows the cast before it sees chunk one, so a null is
  uninterpretable and a positive is confounded.
- **It does not fit.** 72 to 113 hours for the cheap half alone, against a 70-hour budget, on an
  unbuilt pipeline. The alignment layer between emitted entity strings and annotated mention spans
  is itself an entity-resolution system, so you must solve the problem to measure it.

Also: **SLIDE** (arXiv:2503.17952) already varies extraction context on a 160,000-token novel, and
**HAKG** (ICSP 2026) already reports global-prior-beats-local at full-book scale. HAKG is
abstract-only and is the single most likely scoop; read it in full before revisiting this.

Every negative-results venue for 2026 has closed. Insights at EMNLP 2026 shut in June.

### 4. Deployed-system measurement by fault injection. THE FRAMING IS OCCUPIED.

- **AgentChaos** (ASE 2026, arXiv:2608.06790), **AgentChaosBench** (arXiv:2608.14680), and TU
  Delft's observability work all do fault injection on LLM agent systems.
- **SuperLocalMemory** (arXiv:2608.08253) ran eleven fault-injection scenarios against a memory
  system's own invariants, 200 repetitions each, one month ago.
- **When Errors Become Narratives** (arXiv:2606.14589) is a single personal-assistant runtime over
  eight weeks reporting that roughly **70% of silent failures were caught by human observation, not
  by tests or health checks.** That is this project's finding, in print.
- The hedge-stripping mechanism is published as **Manufactured Confidence** (arXiv:2606.29279):
  consolidation rewrites hedged remarks into flat dated assertions.

**And the n is too small.** 5 of 10 injected faults invisible carries a 95% interval of roughly
19% to 81%. Comparable papers used 250 executions, 65 configurations, or 200 repetitions per
scenario.

---

## 5. Provenance integrity. RULED OUT BY THE SCOPE DECISION ABOVE, kept for the record

**This section is retained because the search behind it was real and the finding may matter later,
for instance if the archive is ever instrumented with a releasable synthetic replica. Under the
2026-08-28 scope decision it is not the fall or spring paper.**

**The contribution is not fault injection. It is two measured provenance failures and the link
between them.**

> **Corroboration inflation launders a silent over-merge into apparent authority.**

**A. Corroboration inflation, measured on a live corpus.** 194 claims carried more than one
recorded source; **77 of them, 40%, were inflated** because a roll-up summary echoing its own child
counted as an independent witness. Consequence: the best-supported-*looking* claims were the
most-summarised, not the most-observed.

The *fix* is published: **Isnad-Rijal** (arXiv:2607.24117, July 2026) implements independent-chain
corroboration for exactly this. **The field measurement is not.** Nobody has reported the rate on a
real deployment, tied causally to a specific downstream defect.

**B. Silent over-merging.** Every check in the system asked whether a claim *resolves*; none asked
whether two entities that collapsed into one *should have*. A search of the LLM entity-resolution
literature returns four papers, all about performing resolution better; none treats over-merging as
a failure mode with a structurally silent validation surface.

Do not oversell B alone. Classical record linkage has known over-merging for decades as precision
loss, and a reviewer will say so. The defensible claim is narrower and is the **A-to-B linkage**:
in LLM-built registries the validation surface only tests resolvability, so over-merges are silent,
and the echo mechanism then manufactures their authority.

**Supporting measurements, all already collected:** 33.4% of stored facts trace to summaries of
summaries rather than to leaves or primary documents; of induced entities, 84% typed `unknown`, 56%
appearing in one fact or none, and 37% carrying names that read as a claim rather than a thing.

### What it would cost, and what must be fixed first

**115 to 140 hours.** That is a spring project. It does not fit the fall's 70.

| Work | Hours |
|---|---|
| Read the threat papers properly, rewrite positioning | 20-25 |
| Enlarge fault injection to 40-60 defects with per-class rates and intervals | 15-20 |
| Grow the 39-claim layer-seam audit to 150-200 with a protocol and a second rater | 25-30 |
| Formalise independent-chain counting against Isnad-Rijal | 10 |
| Turn the false-merge case into a systematic sweep with a detection method | 15 |
| Writing, threats to validity, synthetic replica and artifact package | 30-40 |

**Two threats that must be answered, not avoided:**

- **RAPTOR (ICLR 2024) explicitly reports that hallucinations did not propagate to higher layers**,
  sampled over 150 nodes across 40 stories. The 39-claim result here contradicts a published ICLR
  finding on a smaller sample. This is why the audit has to reach 150-200 claims with a second
  rater, and it is the least negotiable line in the table above.
- **The entailment argument is wrong as currently worded.** "X may be true" does not entail "X is
  true." The real claim is empirical: NLI and LLM-judge checkers are insensitive to epistemic
  modality. State it that way or it dies in one sentence.

**Kill criteria. Two hours of reading that could save 140.** Read **arXiv:2607.24117**
(Isnad-Rijal) and **arXiv:2606.14589** (When Errors Become Narratives) in full before spending
anything else. If Isnad-Rijal already measures inflation on a real corpus, the best asset is gone
and the answer is no. If 2606.14589 covers the memory plane's synthesis layer rather than only the
runtime, the case weakens further. Both are currently snippet or abstract-level reads.

**Privacy is not a blocker.** The ACM SIGSOFT Empirical Standards permit deviation from data
sharing when data is too sensitive. Ship the injection harness, the check code, a redacted schema,
per-fault detection logs, the annotation protocol, and a **synthetic replica corpus**. Do not skip
the replica; it is what reviewers actually want.

**Venue:** CAIN or ICSE-SEIP, an experience or industry track, not a research track. The model is
*Seven Failure Points When Engineering a RAG System* (CAIN 2024).

---

---

## The thesis as it stands after the 08-28 conversation

**UNVERIFIED. Four searches are in flight. Do not act on this section until they return, and do
not let its confidence fool you: the nine dead claims each began as a paragraph exactly this
tidy.**

Justin's framing, arrived at in conversation, in his terms:

> A lightweight RAG at the user level, installable on a desktop, **and** scaled: test both a
> desktop version on JSON and a Neo4j implementation with Graphiti, on novels as a reproducible
> substrate, motivated by personal assistant use.

Why this is the best-shaped version so far, and each point is checkable:

**The storage port becomes the apparatus.** `03_design.md` already specifies two deployments behind
one logical schema separated by a twelve-operation port. Written as engineering discipline, it is
also a controlled comparison: same schema, same pipeline, same corpora, one variable.

**The corpora are already a size ladder**, on disk and public: Holmes 0.68M words, Oz 1.28M, Chinese
1.52M, Greek 3.36M, all four 6.84M. (Corrected 2026-08-29: Chinese was stated as 1.58M, which is 4%
high and made the components sum to 6.91M against a correctly computed 6.84M total.) Roughly 3,200 units, so on the order of 10,000 to 20,000
vectors at the top.

**The Graphiti arm is de-risked**, verified against source at commit `683a853`: `EpisodeType.text`
ingests plain text, and `add_triplet` accepts pre-extracted entities.

**The framing is design-space, not novelty**, which is the one framing this project has established
survives prior art.

**The likely result, and it should be expected rather than hoped against:** the server arm may never
earn its keep anywhere on the reachable ladder, so **that null is the finding** rather than a
disappointment. **Corrected 2026-08-29:** this paragraph previously justified that with "exact
brute-force cosine is correct below roughly 100K vectors." Faiss puts the threshold at **around
10k**, so the four-corpus run at 10,000 to 20,000 vectors sits just above it rather than far below.
The expectation survives on latency arithmetic (61 MB, one BLAS call), not on being comfortably
underneath a threshold.

**The cost, stated honestly.** Two backends roughly doubles the build against 70 hours with nothing
built, and `03_design.md` section 7 already names the failure mode: "two adapters, twelve
operations, no shared test suite. The realistic failure is that the files adapter is developed
against and the Neo4j adapter rots." One semester almost certainly buys one arm. The split that
follows is fall for the files backend, the instrumentation and the ladder; spring for the Graphiti
arm, the comparison and a system-demonstration paper.

**Venue note not previously surfaced:** ACL and EMNLP run **system demonstration tracks**, four to
six pages plus a video, where the bar is a working useful system rather than a novel mechanism.
That is a materially lower bar than the research track against which everything in this document
was implicitly judged, and it is the natural home for an installable backend. Requirements not yet
verified.

**The proxy argument, and the strong form of it.** Do not argue that personal archives and novels
are structurally similar; that invites four fair objections (novels are authored while archives
accrete, novels end while archives do not, archives carry wall-clock and session metadata that
fiction lacks, and ordering semantics differ, which `03_design.md` section 7 already flags as an
open problem). Argue instead that **the mechanisms under test are invariant to those differences**:
entity resolution across units, supersession on a functional predicate, and non-contiguous thread
interleaving are properties of sequential multi-entity text regardless of whether it was authored
or accreted. Then say plainly what does *not* transfer, which is wall-clock reasoning, session
boundaries, and anything relying on a user asserting facts directly.

---

## Lightweight at personal scale. DEAD, 2026-08-28. This was the eleventh.

**OCCUPIED, and not partially.** *As We May Search* (Zerhoudi, Roegiest, Mitrovic, Granitzer,
arXiv:2606.29652, **ICTIR 2026**, presented 25 July 2026) proposes "local-first IR, a design
philosophy where indexes, models, and inference reside on user devices, treating remote services as
optional," and runs the same two arms: FAISS exact flat search against HNSW and IVF, plus BM25,
across five benchmarks from 1K to 1M documents on consumer hardware. It reports dense retrieval
holding over 91% nDCG@10 up to 100K documents. Thesis, paper form, crossover number and venue, all
of it, seven weeks before this idea was formulated.

**The premise was also factually false**, and it was asserted without a search by the assistant
rather than by Justin. The claim was that published systems assume infrastructure and do not
evaluate at personal scale. LoCoMo and LongMemEval *are* personal-scale corpora and every one of
those systems evaluates on them; Cognee already defaults to embedded local stores. MemX
(arXiv:2603.16171), vstash (arXiv:2604.15484) and SuperLocalMemory are published local-first
SQLite-plus-FTS5 memory systems. ELITE (arXiv:2505.11908) already discards embeddings *and* graph
construction and beats embedding-based baselines.

**And the direction of the effect runs against the design.** GraphRAG-Bench (arXiv:2506.05690)
measured when graphs help: simple fact retrieval ties (60.9 versus 60.1), but complex reasoning is
53.4 versus 42.9 and contextual summarization 64.4 versus 51.3, both favouring the graph. Those are
this design's headline query shapes. The machinery the thesis wanted to drop is the machinery those
queries need. GAM, ExpGraph and H-Mem publish ablations pointing the same way.

**And it costs more than what it replaced.** A "what can you drop" paper requires building the
heavy arm first, so you have something to drop.

**One real gain from the search, independent of the claim:** the 100K figure in `03_design.md` §5
was stated as design rationale with no source. It is now **corrected to Faiss's published 10k
threshold** and cited there; *As We May Search* is cited separately for the wider local-first
framing rather than for the number. **Corrected 2026-08-29:** this paragraph previously said the
figure "is now cited to *As We May Search*", which was wrong on both the number and the source.

**The narrow seam that remains, recorded and not recommended:** *As We May Search* measures flat
retrieval and does not touch the construction side (entity resolution, community detection,
temporal facts, hierarchical summarisation), and GraphRAG-Bench does not measure on consumer
hardware or account cost per stage. A per-stage construction-cost-versus-per-query-benefit ablation
is untaken. It is also mostly held by GraphRAG-Bench, *Anatomy of Agentic Memory* and *Are We Ready
For An Agent-Native Memory System?*, its likely result is unfavourable, and it requires building
both arms. Not inside 70 hours.

---

## The direction previously under examination, superseded by the section above

Stated as a thesis rather than a claim, because it has not finished being searched:

> At personal corpus scale, the infrastructure the published systems assume is unnecessary, and
> what it costs to drop it can be measured.

Zep and Graphiti require Neo4j. GraphRAG does batch community detection over a graph store. Most
agent-memory systems assume a server or a hosted service. A personal corpus is small: tens of
thousands of units, not millions. This design's deployment B is JSONL as the store of record, a
numpy array with brute-force exact cosine, and SQLite FTS5, with no server and an option to drop
embeddings entirely and resolve entities from an alias table plus lexical search.

Two things make this a better fit than anything above. It is a **design-space measurement**, which
is the framing that survives prior art. And it is evaluated on **corpora anyone can re-download**,
which satisfies the scope decision.

What would have to be true for it to be a paper: that nobody has published the crossover
measurement at personal scale, and that the zero-embedding variant is not already known to be
strong. Both are being searched. Do not write a word of it until those return, and do not treat
this section as a claim until then. The nine dead claims all began as a paragraph exactly this
confident.

---

## The fall plan that actually fits

No research paper this fall. The following produces citable output inside 70 hours.

1. **This week: ask Dr. Fang for an arXiv endorsement in cs.CL.** First-time submitters require it,
   and an institutional email alone does not grant it. One endorser suffices and arXiv explicitly
   recommends the thesis advisor. This is the longest human-dependency in the plan and it blocks
   everything downstream.
2. **September 1: make the repository public.** Free, and it starts the six-month public-history
   clock that JOSS requires, making that route viable from roughly March 2027.
3. **Build the backend.** It is the degree project, and it needs no novelty claim.
4. **November 10: publish the DOI'd artifact.** Zenodo mints on publish with no review gate;
   Hugging Face has a one-click DOI. Mint it only when final, because the repo then locks.
5. **November 16: submit to arXiv**, primary category cs.CL, framed as a resource and experience
   paper. **Not** as a survey or position paper: arXiv CS has required prior peer-reviewed
   acceptance for those since 2025-10-31. Announcement runs one to four days with a long tail, and
   arXiv defers around Thanksgiving, so avoid November 23 to 27.

**ARR's October 12 cycle was considered and rejected.** October 12 falls inside the dead window of
September 28 to October 18, so hitting it means finishing a paper by September 27, in direct
competition with preprocessing. Take the February cycle in spring, with the provenance paper, which
is when it would actually exist.

**On how much a preprint helps, stated honestly:** a solo, non-refereed preprint from an applicant
with no publication record is weak evidence on its own. Its value is instrumental. It gives the
research letter writer something specific to describe, and it demonstrates the ability to finish
and ship a paper-shaped object. List it under **Preprints**, never under Publications, and list the
dataset under Research Artifacts. Miscategorising a preprint as a publication is the most common CV
error and committees notice it.


---

# The answer, arrived at 2026-08-28 after twelve dead claims

**There is a paper. It is a system paper, and the contribution is not the architecture.**

The composition (cell matrix, threshold gate, wiki tiers, append-only temporal facts, hash refold,
entity-keyed retrieval) is **unoccupied as a six-way conjunction and occupied in every individual
element**. That gap is exactly the "novel combination of occupied components" argument that killed
claims one through twelve, and it must not be the pitch.

**The contribution is which mechanisms carry the win and which do not, measured.** That is an
ablation study over this architecture, and its decisive property for this project is that **it
requires building the system anyway.** The degree project and the paper stop competing for the same
70 hours and become the same work.

## What it must contain, per the venue analysis

- Head-to-head against **Mem0, Zep, MemGPT/Letta, A-MEM, plain RAG, and full-context**.
- **Per-mechanism ablations**: drop the salience threshold, drop the cells, drop the fact layer,
  drop the hash refold, and report what each costs.
- At least one **non-accuracy axis**. The sharpest available here is **recompute cost under edit
  churn**, because incremental refolding is the mechanism this design actually invests in.
  **Corrected 2026-08-29:** this previously added "and nobody publishes the number," which was an
  undocumented absence claim and is false. MemTree publishes 3,750 LLM calls per insertion for
  RAPTOR and 3,850 for GraphRAG against 3.27 for itself. Position the measurement against that
  number rather than as a first.
- A **DOI'd artifact** and at least one **honest negative result**.
- **Concede all six mechanisms as occupied in the introduction**, with citations, before a reviewer
  does it in the review.

## Venue

**ACL / EMNLP / NAACL System Demonstrations.** Six pages, single-blind, prototypes explicitly in
scope, entry is a live link plus a roughly 2.5-minute screencast. Structural precedent: **FlexRAG
(ACL 2025 Demo)**, an open-source framework with zero algorithmic claims.

**CAIN 2027, deadline 30 October 2026**, falls inside the open block and is a stretch rather than a
plan; note CAIN does not waive novelty.

**Effectively closed:** VLDB Industrial (needs a non-academic author), ICSE-SEIP (built around an
organisation), KDD ADS and CIKM Applied (both desk-reject systems without live users and post-launch
usage metrics), ISWC In-Use and Resources (want uptake outside the developing group).

## The nearest peer-reviewed threat, which must be read and cited

**Story Ribbons** (Yeh et al., **IEEE VIS 2025**, arXiv:2508.06772). 36 works, 30 from Project
Gutenberg. Its pipeline extracts characters per scene with "a direct quote from the text as
evidence," then composes **both** chapter summaries and character summaries from that layer, with an
exact-string-match check and an alias-dedup loop. That is the cell matrix with both marginals, plus
the quote gate, published and peer-reviewed.

**The difference is real and must be stated rather than hoped past: Story Ribbons is a visualisation
system with no retrieval layer.** Also close: **ReverieMem** (arXiv:2606.25632), per-character
per-scene retrospective summaries over 8 novels including the Sherlock Holmes canon.

## The largest gap in this repo's prior-art coverage

**An entire 2026 "LLM Wiki" line is absent from `papers/`, `docs/` and `summaries/`.** It occupies
the wiki-tier rendering (section 5 of `03_design.md`) and the entity-keyed retrieval table outright:

- Ming et al., arXiv:2605.25480: one page per entity, 5,825 knowledge pages, YAML frontmatter with
  aliases and tags, a one-line summary, structured key facts, bidirectional wikilinks, source refs.
- Cochran, arXiv:2607.04576: a real 709-page LLM-maintained wiki, lead paragraph plus a Connections
  section.
- Cochran, arXiv:2605.18490: a **preregistered** head-to-head of vector RAG against an LLM-compiled
  wiki. This is the comparison this project would want to run.
- WiCER (arXiv:2605.07068), LLMpedia (arXiv:2603.24080), and Karpathy's April 2026 gist.

Also absent and relevant: NKW (2606.05724), StateFuse (2607.05844), MOSS (2607.04391), xmemory
(2604.27906), Streaming Knowledge Compilation (2606.09877).

## A method warning carried out of this search

The searching agent caught **four fabrications** produced by fetched PDF summaries during this
session: an invented tiered architecture attributed to MEMTIER (2605.03675), the same for
2606.09877, a venue invented for ENGRAM (2606.09900) whose arXiv comments field names none, and a
novelty policy misattributed between two conferences. Each was caught only by extracting the PDF
locally and reading it.

**Do not trust a fetched summary of a paper. Extract and read it.** That is the same failure that
produced the Zep README error, and it is now documented three times in this repository.


---

# Using novels as the substrate: what it costs, and the one rule

**2026-08-28.** Searched. The proxy argument is **standard as a practice and unjustified as an
argument**. Papers do use narrative corpora for memory work, but almost none argue that narrative
substitutes for conversation. They either say nothing, or they quietly reshape the books into a
dialogue stream first.

## The rule, and it governs any quality measurement here

**Report a no-memory baseline as a headline number, not a footnote.** Ask the questions with the
store switched off entirely and report what the model gets right from pretraining alone. Without it,
a reviewer cannot tell memory from recall of the training set.

**Contamination is the strongest objection and it lands hardest on exactly this corpus.** GPT-4
scores **60.94% on NovelQA multiple choice with no novel in context**. BooookScore names the source
directly: BookSum texts "from the Project Gutenberg public-domain repository ... are in the
pretraining data of existing LLMs." Chang et al., *Speak, Memory* (EMNLP 2023) found the most
memorised books include "popular works in the public domain," and that "disparity in memorization
leads to disparity in downstream tasks." NoCha names this exact design as the failure mode.

The asymmetry the proxy needs is that the model has read the novel but not the user's life. That is
the axis on which the two corpora differ most, and it runs against the argument.

**Two measurements are immune and should therefore come first:** the read-cost differential (tokens
read to cover the same content, a cost measurement) and the coverage differential (two of this
system's own outputs compared against each other). Neither involves model knowledge.

## How to justify the substrate, in order of defensibility

1. **Reproducibility, not realism.** Narrative World Model (arXiv:2607.05577) pairs a public corpus
   with a private one: "The public corpus makes the protocol reproducible while the private
   five-book corpus tests the same systems on longer, production-style serialized stories." This is
   the cleanest available framing and it does not make a realism claim that can be attacked.
2. **Reshape the book into an incremental multi-turn stream, and say so.** This is the ICLR 2026
   precedent. MemoryAgentBench criticises static book QA, then uses books anyway after restructuring:
   "we wrap all input chunks within a simulated User-Assistant dialogue to explicitly trigger the
   agent's memory mechanism."
3. **The supporting argument, from the other direction.** TraceMem (arXiv:2602.09712) argues a
   personal chat archive *is* narrative, organising "disjointed interaction traces into evolving
   narrative threads that represent the user's ongoing life story."

**Do not cite CAM as precedent**: it is framed as reading comprehension, not assistant memory, and
offers no proxy justification.

## The objections, sourced, that a reviewer will raise

- **Contamination**, above. Fatal as specified unless the no-memory baseline is reported.
- **The published warning that book QA is not a memory-agent proxy**, from MemoryAgentBench itself.
  A reviewer can paste that sentence and stop.
- **Bounded versus unbounded.** ConvoMem: memory systems "start from zero and grow progressively."
  A novel is complete at t=0, so compaction and forgetting policy, which is the actual engineering
  problem, is untestable on it.
- **Narrative time versus wall clock.** Narrative World Model models event order and reveal order as
  separate fields precisely because generic memory cannot.
- **Entity density.** BOOKCOREF reports roughly 27 consistently-named characters per book. An open
  personal cast referred to by first name or "that thing we talked about" is harder, so the proxy
  makes entity tracking artificially tractable.
- **Fact change is a different operation.** In fiction a fact changes by *revelation*, where reader
  access changes and the world does not; in an archive the same predicate takes a new value. Noted
  as **unsourced as a named contrast**, assembled from halves.

## Do not spend the project measuring the proxy

Nobody has built the same system over a narrative and a conversational corpus to ask which
measurements transfer. But the framing is occupied twice within four months: **AMA-Bench**
(arXiv:2602.22769) already reports a cross-substrate ranking flip, and **Cross-Scenario Generality
of Agentic Memory Systems** (arXiv:2606.04315) already concludes "winning on one does not imply
winning on others." A reviewer would call it AMA-Bench applied to a new pair of corpora.

## Conversational corpora, if a second substrate is ever wanted

| Corpus | Size | Ground truth | License |
|---|---|---|---|
| LongMemEval | 500 Q | knowledge-update category, evidence-session labels, timestamps | **MIT** |
| MemoryAgentBench FactConsolidation | 146 rows | explicit fact supersession, **exact match, no judge** | **MIT** |
| MEME (arXiv:2605.12477) | 100 episodes, 694 Q | entity KG, 90 entities | **CC BY 4.0** |
| MTRAG | 110 human conversations | per-turn answerability, relevant passages | **Apache-2.0** |
| LoCoMo | **10 released**, not the 50 the paper claims | evidence dialog ids | CC BY-NC 4.0 |
| MSC + personal-facts-MSC | 17.9k episodes, 2,779 annotated facts | **real human** dialogue | **license unstated** |

**LongMemEval is assembled, not real** (roughly 25% ShareGPT, 25% UltraChat, 50% model self-chat).
**Avoid DialSim**: unlicensed copyrighted TV scripts, LICENSE returns 404. **Avoid HaluMem**:
NoDerivatives.

## Integrity note from this search

The searching agent caught **two hallucinations mid-run**: a search engine attributed a quote about
synthetic datasets to Narrative World Model, in which the word "synthetic" does not occur; and a
WebFetch echoed the prompt's own wording back as a verbatim quote. Both were caught by re-extracting
the source. Two secondhand figures are flagged as unverified: the Mem0 ECAI 2025 acceptance (vendor
blog only) and the MemGym fictionalization numbers.
