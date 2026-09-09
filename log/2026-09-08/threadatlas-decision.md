# ThreadAtlas: naming and architecture decision record

Source: `ThreadAtlas_Project_Notes.docx`, the decision record from the 9 September 2026 project
review (logged 2026-09-08). This is Justin's record, preserved here as the authoritative
development note; consolidated SCHEMA/BUILD/RESEARCH are **not** rewritten yet, by decision (§2).

## Main conclusion

The project is now **ThreadAtlas**: an entity-centric narrative memory system that compiles
ordered, heterogeneous sources into document-local entity narratives, reconciles those entities
across documents without erasing source boundaries, and exposes the result through both semantic
retrieval and a browsable wiki-like portal. Facts and verbatim quotes remain as evidence and
temporal machinery; **narrative cells are the primary retrieval and reading representation.**

## 1. Decisions

| Decision | Position |
|---|---|
| Project name | **ThreadAtlas** for the complete system. |
| FactLedger | May remain the name of the internal fact / quote / temporal-validity / provenance subsystem. |
| Primary memory representation | Ordered entity-specific **narrative cells**, not isolated fact triples. |
| Primary embedding granularity | **Individual sentences** within narrative cells, tied to the entity. |
| Primary retrieval object | The cell (or a short cell sequence); sentence vectors nominate the cell. |
| Wiki role | A generated **read model** over the graph, not a second authoritative database. |
| Global identity | Document-local entities attach to global parents; early uncertainty must never permanently prevent later attachment. |
| Public artifact | Publish non-chat corpora and their portals; keep personal chats private on the same architecture. |

## 2. Documentation drift is expected

Drift between the consolidated docs, the notebooks, and the eval plan is expected in this
exploratory phase: the earlier docs were a plan made before the data's behavior was understood.
**Daily logs are the authoritative record now**; consolidated docs regenerate after the shape
stabilizes. Drift is not evidence of failure. Keep recording decisions and run results in dated
logs. The real blind spot is **retrieval** — the graph is being built before its access behavior
is understood; the likely rebuild boundary is the derived global organization, not raw extraction
(documents, units, offsets, local entities, facts, quotes, cells survive several retrieval
designs).

## 3. Immediate development strategy

Ingest representative source shapes → inspect what Step 1 produces → build global reconciliation,
with **retrieval as a thin vertical slice alongside** the global layer, not postponed.

1. Finish representative packages (literature, papers, benchmark novels, chats).
2. Inspect actual entities, facts, cells, omissions, repetition, temporal behavior.
3. Define a small query fixture (the ideal returned context).
4. Build reversible global attachment (document-local children → global parents).
5. Implement minimal entity lookup, cell retrieval, graph expansion, context construction.
6. Use observed retrieval failures to revise the global representation.
7. Regenerate consolidated build/schema/proposal/eval docs after the structure survives.

## 4. Representative query fixture

Direct fact ("Who is Dorothy's aunt?"); current state ("Who rules Oz now?" — prefer later state,
keep earlier); identity across works ("What happens to Tip?" — connect Tip/Ozma only on evidence);
source disagreement ("Who was Helen's mother?" — keep traditions separate); narrative development
("How does the Scarecrow change?" — ordered cells); conversation revision ("What did I decide about
summer classes?" — earlier plan, revision, speaker, current state); relationship path (traceable
graph path); broad synthesis (abstract + cells + views + disagreements); source-specific (stay in
the document child, no parent contamination); uncertain/negative ("Did this happen?" — distinguish
not-found from did-not-happen).

## 5. Narrative cells vs facts and quotes

Cells are more valuable to readers and likely to retrieval than the fact list; facts atomize and
lose causal/developmental context. Layer responsibilities:

| Layer | Responsibility |
|---|---|
| Narrative cells | Main semantic memory and the readable body of entity pages. |
| Cell sentences | Fine-grained vector targets that nominate a containing cell. |
| Entity abstracts | Orientation, candidate selection, page leads. |
| Facts | Structured constraints, temporal comparison, contradiction detection, direct answers. |
| Quotes | Evidence and audit; normally hidden until needed. |
| Document-local entities | Preserve each source's interpretation and state. |
| Global parents | Organize children across sources without asserting a universal account. |

The Zep HTML made this visible: summaries read well; the full facts-by-entity section was long and
repetitive. That render was an all-records diagnostic, not the portal. The document page should not
expose every fact about every entity.

## 6. Sentence embeddings within cells

One low-dimensional embedding **per sentence** (a whole-cell vector dilutes a decisive sentence).
The persistent object is the cell; sentence vectors are entry points. Embed **entity + sentence
text only** — not unit/document labels (they add geometric noise); keep order/provenance as
relational metadata. Store per cell: cell text, entity identity, sentence ordinal + char span,
entity embedding, one embedding per sentence, embedding model + text hash. Score a cell from its
strongest sentence match plus supporting matches plus an entity match; do not average.

## 7. Vector storage and deletion

Vectors are cheap; minimizing count is not the goal — **deletion and rebuildability** are.
Embeddings are deletable derived children of a cell, identified logically (entity / cell+ordinal /
model / text hash), never by physical row. The packed matrix is a **disposable projection** whose
row positions may change freely. Global attachment is a reversible edge owned by the child.

## 8. The unmeasured code-heavy chat case

Long coding conversations (generated code, pasted back, versions, failed approaches, final impl)
may produce severe repetition — but do **not** design special deletion/versioning/dedup before
observing what the current pipeline does. Required experiment: one real coding conversation with a
generated impl, pasted code, modifications, a failed approach, and a final accepted version;
inspect entities, salience, cells, code retention, repetition, and whether sentence retrieval can
answer "what was finally implemented." Until then, behavior here is **unmeasured**.

## 9. Wiki portal as the read model

A reader-facing projection generated from the authoritative records (not a graph dump); a human
browsing and an assistant retrieving exercise the same search/expansion/traversal.

- **Document pages:** abstract lead; ordered unit summaries; entity mentions linked to entity
  pages; metadata + source; related works from shared entities; facts shown only when about the
  document itself (authorship, publication, series, revision, what it evaluates).
- **Entity pages:** abstract lead; ordered narrative cells grouped by document/source order;
  appearances; aliases/related entities; source-specific disagreement and temporal change
  preserved; facts/quotes beneath for verification, not the default surface.
- **Collection portals:** clustering over the document-entity graph generates root/subportals;
  down-weight generic entities (e.g. "large language model") so informative ones (Graphiti,
  LongMemEval, Dorothy, Ozma, Odysseus) dominate. Underlying organization stays a graph; the portal
  presents a tree-like root → community → subcommunity → page traversal with cross-links.

## 10. Planned corpora

| Area | Material | Role |
|---|---|---|
| Research | ~100 verified CC papers on RAG and KG | Public research wiki; replaces the licensing-sensitive paper set. **(gathered 2026-09-08, `data/raw/kg-rag-cc/`)** |
| Greek/Roman | Existing public-domain classics | Cross-source disagreement, recurring figures, translation/OCR stress. |
| Sherlock Holmes | Existing public-domain Holmes | Recurring characters, contradictions, contamination tests. |
| GraphRAG fiction | 20 GraphRAG-Bench novels | Benchmark compatibility, heterogeneous narrative. |
| Oz | Public-domain Oz series | Longitudinal identity, supersession, evolving narratives. |
| Personal chats | Private only | The assistant-memory application; never public. |

Every replacement paper carries an explicit license, source URL, and exact version hash (public
availability != permission to redistribute). Same code runs on public and private corpora.

## 11. Prior art

The broad claim "no one has turned a corpus into a graph-organized wiki with hierarchical portals"
is **not supportable**. Closest systems:

| System | Overlap | Distinction |
|---|---|---|
| **ASKS** (posted 30 Aug 2026) | Source-local wiki pages, doc-local graph changes, cross-doc fusion, embedding-driven hierarchical Hubs, provenance, human/agent navigation. | Organized around scientific pages/concepts/propositions/Hubs; not centered on chronological entity-specific narrative cells with silent global parents. |
| LLM-Wiki | Compiles docs into persistent interlinked wiki pages with search/read/link ops. | Pages are the primary organization; ThreadAtlas derives views from a provenance-preserving narrative graph. |
| Microsoft GraphRAG | Entities/relations, community clustering, hierarchical community summaries, local+global search. | Community reports are retrieval artifacts, not a browsable temporal entity-history portal. |
| KGGen | Builds/clusters cross-document entities and relations. | Dense KG extraction, not ordered cells or wiki projection. |
| PAGER | Builds coherent pages to improve RAG context. | A page per question, not an evolving corpus-wide narrative graph. |

ASKS is central related work: the dated repo logs evidence independent development but do **not**
make an occupied idea novel. Compare ThreadAtlas object-by-object with ASKS **before** implementing
the global layer.

## 12. Differentiation

ThreadAtlas is differentiated by **the object that accumulates**: GraphRAG accumulates relations
and community summaries; ASKS accumulates concepts/propositions/pages/Hubs; LLM-Wiki accumulates
linked pages; **ThreadAtlas accumulates source-local narrative states of entities through ordered
units.** Ordered units are narrative progression, not interchangeable chunks; each entity gets a
cell per unit; cells accumulate in source order into an entity history; local entities preserve
source interpretation; global parents organize without owning one universal truth; disagreement is
preserved; facts carry evidence/temporal machinery beneath; one representation serves literature,
papers, and longitudinal conversation.

> ThreadAtlas compiles ordered documents and conversations into provenance-preserving entity
> narratives, reconciles those narratives across sources through a reversible global identity
> structure, and exposes the result as both a browsable knowledge atlas and an assistant memory
> interface.

## 13. Naming

Thread = an entity's ordered sequence of cells through documents; Atlas = the navigable
organization when shared entities connect works and clustering forms regions. The name avoids
overcommitting to a literal tree or wiki. **ThreadAtlas** = complete system / public portal /
retrieval architecture / project name. **FactLedger** = optional internal evidence subsystem.

Working title: *ThreadAtlas — Entity-Centric Narrative Memory over Heterogeneous Ordered Sources.*

## 14. Architectural layers

| Layer | Objects | Responsibility |
|---|---|---|
| Source | documents, units, pieces, authors, dates, offsets | Preserve received material and order without addressing-breaking normalization. |
| Local interpretation | local entities, facts, quotes, cells, abstracts | Interpret one document, keeping its identity and voice. |
| Global identity | silent parents, reversible child attachments | Connect corresponding local entities without erasing source records. |
| Semantic access | entity + sentence embeddings owned by cells | Find precise narrative entry points, return containing cells. |
| Organization | shared-entity links, communities, portal hierarchy | Navigable bodies of work; controlled cross-document expansion. |
| Read model | document pages, entity pages, collection portals | Present the graph as a coherent wiki for people and agents. |
| Evidence | FactLedger facts, validity, contradictions, quotes | Verify claims; support temporal/direct-fact queries without overwhelming reading. |

## 15. Open questions

Attachment evidence/thresholds; how retrieval combines sentence + entity + cell-reinforcement +
graph proximity + time + source restriction; when a hit expands to neighboring cells / related
entities / same-parent documents; how current state is computed across children while the parent
stays non-assertive; which predicates are functional (and mapping model-written variants); how
portal communities overlap/split/change; whether clustering uses majors / weighted minors / cells /
facts; how hard deletion propagates through text, cells, vectors, attachments, summaries, portals,
caches, logs; how the pipeline represents code-heavy chats; which claims survive comparison with
ASKS/LLM-Wiki/GraphRAG.

## 16. Near-term worklist

1. Adopt **ThreadAtlas** in new daily logs; postpone mechanical renaming until stable.
2. Preserve **FactLedger** as a candidate name for the evidence subsystem.
3. Replace the paper archive with ~100 individually-license-verified papers. **(done 2026-09-08)**
4. Ingest representative public corpora + a private sample of varied chats.
5. Add the real code-heavy chat experiment; record what the pipeline produces before special handling.
6. Define expected outputs for the query fixture.
7. Read ASKS closely; write an object-by-object comparison **before** designing the global layer.
8. Implement global attachment as a reversible derived layer over document-local packages.
9. Embed each entity and each cell sentence; store provenance/order as metadata, not embedded text.
10. Build a minimal portal (document pages, entity pages, related works, one level of collections).
11. Exercise the same retrieval functions through the portal and an assistant context constructor.
12. Use failures to revise the global layer, then regenerate consolidated docs and the eval plan.

## 17. Guardrails

- Do not convert insufficient early evidence into a permanent cannot-link.
- Keep source-local records intact when global organization changes.
- Treat generated pages and indexes as rebuildable projections.
- Keep facts/quotes available for evidence, not as the default reading surface.
- Do not infer behavior for hard source shapes before running representative examples.
- Do **not** claim novelty for graph-generated wiki portals or hierarchical Hubs; position around
  entity-centric evolving narratives and evaluate that distinction.
- Keep public and private corpora operationally compatible but strictly separated in publication.

## 18. PhD potential

ThreadAtlas strengthens a PhD application (IR, NLP, KR, data systems, digital humanities,
human-centered AI) if it produces **one narrow empirical contribution** rather than claiming
system-wide novelty. Candidate centers: whether ordered entity cells beat facts/flat chunks for
retrieval; whether silent global parents preserve conflicting/evolving accounts better than global
fusion; whether sentence-indexed narratives improve longitudinal QA. Principal risk: scope
expanding faster than evaluation — a smaller completed study with a clear result beats a broad
portal with untested claims.
