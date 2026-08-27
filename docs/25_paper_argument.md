# The paper's argument

**CORRECTION 2026-08-27 (later):** an earlier claim in this repo that Graphiti/Zep does
not perform community detection or hierarchical summarisation was **WRONG**. It was based on the
Graphiti repository README, not the paper. Zep's paper defines a **community subgraph** as the
highest tier of its graph, whose nodes "contain high-level summarizations of these clusters,"
built with community detection that "builds upon the technique described in GraphRAG" using
label propagation instead of Leiden **specifically so it extends dynamically** without full
refresh. Zep therefore covers hierarchical summarisation AND incremental maintenance. The error
was treating an absence in a README as a capability finding.

**2026-08-27.** Arrived at after a full day of adversarial novelty searching in which seven
candidate contributions were found occupied. This is the spine that survived. It is not a
positioning statement written to fill a gap; it is what was left standing.

---

## The argument in five moves

**1. Requirements come from a deployment, not a benchmark.**

Two years of running a personal AI assistant produced a concrete list of what its memory backend
must do. Each requirement exists because a wall was hit, not because a paper proposed it.

This is a legitimate use of the personal archive that sidesteps the n=1 verdict entirely. The
archive is **not the subject** and **not the evidence**. It is where the requirements came from.
"Here is what a personal assistant's memory actually needs, derived from two years of running
one" is a different claim from "here is my system and it works well," and only the second one was
taken by MyLifeBits.

It also answers something the field says about itself. *Anatomy of Agentic Memory*
(arXiv:2602.19320) reports that evaluation metrics are misaligned with semantic utility — that
benchmarks measure things which do not correspond to what the systems are for. A requirements
analysis derived from a real deployment is a direct response to that.

**2. No existing system covers those requirements, and this is measurable rather than asserted.**

A coverage matrix: requirements down the side, published systems across the top. GraphRAG, Zep
and Graphiti, RAPTOR, MemTree, TraceMem, EntSUM, timeline summarization.

If the best single system covers five or six of nine, that is a **measured** motivation. It is
also falsifiable — a reviewer can dispute a cell, and disputing a cell is a conversation won with
a citation rather than an argument lost.

Several cells were verified during this session rather than recalled:

| System | Verified finding | How |
|---|---|---|
| GraphRAG | chunks first, extracts entities from each text unit **separately** | its own indexing documentation |
| Graphiti / Zep | **CORRECTED: it DOES have a community subgraph with high-level summarisations, and incremental label-propagation maintenance.** The earlier claim came from the README, not the paper | the Zep paper, read directly |
| MemTree | online, but measures its own drift; ancestors depend on insertion order | abstract |
| EntSUM | a task on single documents, on request; does not accumulate | abstract |
| Timeline summarization | per-entity chronology, news domain, no persistence layer | 2020 survey + 2024–2026 work |

**3. So build the composition that does cover them, and say plainly what is borrowed.**

Hierarchical summaries from GraphRAG and RAPTOR. Temporal facts and invalidation from Zep and,
underneath it, Snodgrass. Per-document per-entity summarisation from EntSUM. Per-entity
chronology from timeline summarisation. Online maintenance from MemTree and Graphiti. Property
graph structure and the δ constraint from Angles. Ranks and qualifiers from Wikidata.

**Naming the borrowing is the strength, not the weakness.** A board or a paper that only shows
what was built reads as naive. One that draws the line explicitly reads as someone who did the
survey — which is exactly what happened, adversarially, with the results recorded in `docs/14`.

**4. Measure what each design decision inside the backend costs and buys. This is the
contribution.**

Not any single idea — the **map** of the design space. Three ablations, ranked by what they cost:

| Ablation | Cost | Notes |
|---|---|---|
| **Entity-first vs chunk-first extraction** | nearly free | LitBank gives gold entities and coreference: precision, recall, F1, no question authoring, no judge. Head-to-head against GraphRAG's actual shipped pipeline order. The duplicate-minting curve falls out of ingest for nothing |
| **Tier allocation per stage** | free | Falls out of running anything; cost arithmetic already in `docs/21`. Note Asymmetric Capacity Allocation (arXiv:2608.21345) covers adjacent ground and must be cited |
| **Covering vs partition** | needs a question set | The live claim. Every hierarchical-memory system found partitions — HERCULES is recursive k-means, TraceMem clusters, GraphRAG uses Leiden. Unverified and the only candidate still standing |

Do the first two regardless. Add the third if the October block survives.

**5. Evaluate on literature, because it has ground truth the assistant case cannot.**

And render the output as a wiki, because a page is **auditable** in a way a chat answer is not.

| Arm | What it is | What it measures |
|---|---|---|
| Assembled | fact rows and cells, mechanically | what the store holds. 0% fabrication by construction — the floor |
| RAG-generated | model querying the backend | what the assistant would actually say |
| **The gap** | claims tracing to neither a fact row nor a cell | **the assistant's fabrication rate** |

That last row is why the wiki belongs in the paper rather than only on a poster: it is how you
get a fabrication number for an assistant at all.

---

## The framing that keeps it a study rather than a system description

*"Here is our backend, and we measured it"* is a system paper and gets killed on prior art.

*"Here are measured tradeoffs in this design space, demonstrated on a working backend"* is an
empirical study and survives, because the contribution is the map.

Same content. The difference appears in the first paragraph, so it has to be decided before one
is written.

---

## What could still kill this

- **Someone has already published the requirements analysis.** Not searched. Given a record of
  seven for seven, check before committing.
- **Someone has already released a literary memory benchmark.** Not searched.
- **The covering ablation fails or turns out to be occupied.** Survivable — the paper loses a
  finding, not its spine.
- **The coverage matrix is disputed.** That is the good failure mode; it is a citation argument,
  not a structural one.

## What this requires that is not yet done

The requirement list itself has never been written down. It is the first artifact of this
argument and it does not exist yet — it lives in two years of hitting walls and in this session's
transcript. **Writing it is the next task**, and it is Justin's to write, because its authority
comes entirely from being derived from his own deployment rather than from a literature review.
