# Design: schema, ingestion, retrieval, delivery

**2026-08-27, revised 2026-08-28.** The design worked out in session on 08-26/27, consolidated
from three separate documents (schema, ingestion pipeline, retrieval and delivery). Records the
*what* and the *why*; implementation is the student's, per the authorship rule.

Citations resolve against `07_references.md`, where every source is now complete and citable.
The unit contract is `04_unit_contract.md` and is frozen.

---

## 1. What the store is shaped like

The design records on two axes over the same source text, and neither substitutes for the other.

**Plot axis.** Summaries per unit, attached to work nodes. Complete by construction: every unit
gets one, no threshold, no entity judgment involved.

**Entity axis.** Per-node narrative cells. Sparse by design: only above-threshold nodes, and only
for the units they appear in.

Each covers the other's blind spot. The plot axis loses the individual thread, because a
character appearing in twelve chapters is scattered across twelve summaries, none of which is
about them. The entity axis loses the causal frame: Ozma's thread says she was Tip and became
ruler, but not *why*, because the why is Mombi's enchantment and Jinjur's revolt, which are facts
about other things.

Formally the atom is the **cell**, `(unit × node)`. Plot summaries are the row marginals; entity
narratives are the column marginals. Two complementary views over one matrix.

### Threads are a covering, not a partition

GraphRAG partitions by graph topology, and says so outright: each level of its hierarchy "provides
a community partition that covers the nodes of the graph in a mutually exclusive, collectively
exhaustive way" (Edge et al. 2024, p. 6). TraceMem is equally explicit, its coarse clustering
operation "produces a partition into m topic clusters" (Shu et al. 2026, eq. 4), with a KNN step
reassigning noise points so nothing is left out and nothing lands in two places. HERCULES
recursively applies k-means. Zep uses label propagation. A folder tree assigns by topic path.

Threads do not. A chapter belongs to Tip's thread *and* Jack Pumpkinhead's *and* Mombi's,
simultaneously, at full weight in each. The same text is covered N times from N vantage points.

**This is a design choice, not a novel one, and the distinction matters.** RAPTOR already soft-
clusters: "nodes can belong to multiple clusters without requiring a fixed number of clusters ...
thereby warranting their inclusion in multiple summaries" (Sarthi et al., ICLR 2024, p. 3). CAM
(Li et al., NeurIPS 2025) combines incremental *overlapping* clustering with hierarchical
summarisation and online batch integration, evaluated against RAPTOR, GraphRAG, MemTree and
MemGPT. Covering is settled ground in hierarchical memory. Adopt it because it is right for this
store, and claim nothing for it. See `01_argument.md`.

The prototype deployment shows the same structure outside literature: leaves mentioning one
project sit in six different topic folders, including one in an unrelated personal-health topic.
The routing is not wrong, because that leaf genuinely belongs where it was filed. The thread is
simply orthogonal to the hierarchy, so no assignment of documents to folders can represent it.
That is a structural limit rather than a curation failure.

Consequence: **a thread index is a second index over the same units, not a reorganisation.** The
hierarchy stays. Nothing is re-filed.

---

## 2. Schema

Eight record types, one controlled vocabulary, and three instrumentation records. Field names are
indicative.

### Source layer

**Document**
```
{doc_id, corpus_id, work_id, kind: text|chat, title,
 source_url, sha256, ingested_at,
 provenance: {contributed_by, resources, ts}}
```
Raw text sits beside it on disk and is never edited. Ids are content hashes, so re-ingesting the
same material is a no-op rather than a duplicate.

`provenance` is immutable and exists on every derived record below. It carries who contributed
the record, what resources it drew on, and when. This is the substrate for read-time access
control (Rezazadeh et al. 2025, *Collaborative Memory*).

**Unit**
```
{unit_id, doc_id, unit_type: chapter|book|play|ode|hui|session,
 work_ordinal, unit_ordinal, title, span: [start, end], text}
```
The atom. Every derived record points here. The full contract, including the eight per-convention
handlers and the three acceptance gates, is `04_unit_contract.md`.

`unit_type` carries heterogeneity forward as data rather than erasing it. A Euripides play has no
siblings to fold with; an Oz chapter does. Normalising to one record shape is correct; flattening
the distinction is not.

### Node layer

**Node**
```
{node_id, canonical_name, kind: person|org|place|thing|topic|event,
 created_from_unit, provenance}
```
**Entities and topics are the same type.** A person is a node, a project is a node, a recurring
event such as the Chunin Exams is a node. `kind` exists because extraction prompts differ per
kind, and because it participates in the delta constraint below, not because storage differs.

**Works are nodes.** "Oz book 2" is a `topic` node. This removes the need for a separate
chapter-summary record type: the plot axis is cells on work nodes, and the book blurb is that
node's abstract.

**Type versus instance is not a kind distinction.** The Chunin Exams is one node whose sequence
holds every exam event; an instance is promoted to its own node only when it accumulates enough
to warrant one. Same promotion mechanism as minor entity to major entity. This matches wiki
practice, where instances appear as sections until they earn a page.

**Alias**
```
{alias, node_id, alias_kind: name|nickname|epithet,
 first_seen_unit, evidence_quote}
```
The surface-form list mapping mentions to one node. Resolution reads it; nothing writes over it.

### Fact layer

**Fact**
```
{fact_id, subject, predicate, object, object_is_node,
 qualifiers, rank: preferred|normal|deprecated,
 unit_id, quote,
 valid_from, valid_to,            # [from, to), upper exclusive
 asserted_at_unit, asserted_at_wallclock,
 tier, contract_version, provenance}
```

**Append-only.** Nothing is overwritten, and there is no stored `superseded_by`: supersession is
computed at read time over a functional-predicate list.

**`rank` fills a gap supersession cannot.** Computed supersession handles *the world changed*, in
which a later assertion collides with an earlier one on a functional predicate. It does not
handle *we were wrong*: an extraction error has no later assertion to supersede it, and deleting
violates append-only. `deprecated` means present, preserved, and excluded from reads by default.

Source note, corrected 2026-08-28: the three-value vocabulary (preferred, normal, deprecated)
comes from Wikidata's *Help:Ranking*, not from Vrandecic and Krotzsch 2014. That paper describes
optional marking as "preferred" or "deprecated" on p. 83 but never uses the word "rank" and never
names a "normal" value. Both sources are in `07_references.md`.

An error of exactly this shape occurred in the prototype deployment, where two distinct people
were merged under one alias and the fix was to append an is-distinct-from assertion rather than
edit the record. Same pattern, done ad hoc.

**`qualifiers` carry n-ary relations, not just timing.** Ozma rules Oz *as restored by Glinda*;
Zhuge Liang serves Liu Bei *in the capacity of Chancellor*. Without qualifiers, role information
becomes either lost detail or invented predicates, and invented predicates are the sprawl that
silently breaks supersession. Source: Wikidata qualifiers, Vrandecic and Krotzsch 2014, p. 82.

**Interval convention is `[from, to)`**, lower bound inclusive and upper exclusive, following
SQL. Stating it prevents the off-by-one that appears wherever two intervals abut. Source: Rost et
al. 2021, pp. 6 to 7. Cite that work as an arXiv preprint and technical report; it has no
conference or workshop venue.

**Fact-level validity subsumes property-level.** Rost puts validity on individual properties
because those vertices carry properties directly. Ours do not, because our facts *are* the
properties, so this is already covered. Recorded so it is not re-opened.

**Predicate registry** (controlled vocabulary, not a record)
```
core:    ~15-20 universal predicates, including every functional one
corpus:  per-corpus vocabulary, namespaced
delta:   allowed (subject_kind, predicate, object_kind) triples
```

**Namespaced predicates**, such as `appearance.height` and `appearance.build`, give attribute
grouping for free. That is how a "Physical description" section assembles itself, and it stays
human-readable.

**Delta is a typing constraint on edges.** A table of allowed
`(subject_kind, predicate, object_kind)` triples, with violations logged as rejections rather
than stored. Source: Angles 2018, *The Property Graph Database Model*, Definition 2, where delta
"defines the edge types allowed between a given pair of node types."

This catches a class of error **the quote gate structurally cannot see**: a fabricated relation
can carry a perfectly genuine quote. `parent_of` between a place and a thing passes every other
check in the system. This is also why the assembled path should be described as fully
*traceable*, not as zero-fabrication. See `01_argument.md`.

**Merge ledger**
```
{attr_id, node_id, attribute, merged_from: [fact_ids in order],
 absorbed_node, evidence, tier}
```
Which rows, in what order, folded into an attribute. The anti-black-box requirement, stored as
data rather than asserted.

### Summary layer

**Cell**
```
{cell_id, node_id, unit_id, corpus_id,
 work_ordinal, unit_ordinal, text, tier, provenance}
```
One node's narrative for one unit. The expensive layer, and the thresholded one.

**Ordered by `(work_ordinal, unit_ordinal)`, never a single integer**, because a node's cells span
multiple works.

Keyed by (node, unit), which flattens two separate scenes involving the same character in one
chapter into a single cell. Accepted deliberately; recorded so it is a decision rather than an
omission.

**Abstract**
```
{node_id, corpus_id, text, children_hash, tier, updated_at, provenance}
```
One paragraph per node **per corpus**. Salience is corpus-scoped: Tip is a major entity in Oz and
a passing citation in a conversation archive. The node is global; its narrative is local.

`children_hash` is computed over the node's cells, so the abstract is stale exactly when its
cells change. Refold is incremental, never a full pass.

**Composition, not storage.** A visual description is not a stored artifact, it is a query over
`appearance.*` fact rows, rendered. Free to regenerate, automatically current, and every clause
traces to a quote. This is also why the Holmes contamination probe passes by construction: there
is no deerstalker fact row, because Doyle never wrote one, so nothing composes.

### Instrumentation

```
Rejection  {rej_id, ts, stage, unit_id, target, contract_version, tier, error}
Run        {run_id, ts, arm, question_id, injected_ids, answer_text, verdict,
            judge_tier, tokens_in, tokens_out, latency_ms}
Consult    {consult_id, ts, cued_node_ids, retrieved_ids, used_ids}
Mention    {mention_id, unit_id, node_id, surface_form, quote, span, tier}
```

Four fields here were carried forward from the module specs now in `archive/impl/`, where they
were identified as gaps and never absorbed:

- **`Rejection.target`** makes "what got rejected twice" a query rather than a manual scan. Without
  it the repeated-failure report cannot be written.
- **`Rejection.unit_id`** makes a failed run resumable. Without it, a crash midway through a corpus
  restarts from the beginning.
- **`Run.answer_text`** lets verdicts be re-judged after a judge-prompt change. Without it, every
  judge revision invalidates every prior run and the runs cannot be re-scored, only re-executed.
- **`Mention`** makes the surface-form-to-node binding a first-class record. Quote verification and
  the hand-check sample both need bindings as data; deriving them after the fact from cells is not
  the same thing.

`Consult` is the proactive-recall instrument. It needs to exist from day one because the rate is
meaningless without weeks of collection. How `used_ids` gets populated is unresolved and is
recorded as such in `02_requirements_and_testing.md`; that requirement is explicitly not promised
this semester. Note that the logger that emits conforming rows is a **separate deliverable** from
turning consult-logging on, and only the latter is currently scheduled.

The node record also needs **`merged_into`**, so a node absorbed by a merge resolves to its
survivor at read time rather than becoming unreachable.

---

## 3. Ingestion

### Stage 0. Preprocessing

Raw text to normalised `Unit` records. Per-corpus handlers, one output contract, specified in
`04_unit_contract.md`. Deliberately outside this pipeline so the heterogeneity is absorbed once.

### Stage 1. High-level pass: identify topics and major entities

One call per unit. Returns the cast: entities and topics present, with a salience signal.

**Entity-first, not chunk-first. This is the project's primary claim.** GraphRAG's pipeline
composes text units first and extracts entities from each text unit *separately*; there is no
document-level entity pass. Zep extracts per episode with a short message lookback, then resolves
against the graph.

That ordering is where duplicate minting comes from. Chunk 3 sees "Tip," chunk 9 sees "the boy,"
chunk 15 sees "Tippetarius": three independent extractions with no shared context, reconciled
afterward if at all. The prototype deployment measured the consequence, a registry that grew to
roughly 1,169 names against a 400-name prompt cap, with active duplicate minting.

A unit-level cast list passed into each downstream call fixes it before it happens. The same pass
does three jobs at once: de-duplication, cross-chunk coreference resolution, and **determining
which cells exist**, which is what makes the sparse matrix tractable rather than requiring every
entity against every unit.

### Stage 2. Dedup against the existing registry

Resolve the cast against known nodes and aliases. **This is on the critical path and it is the
step the prototype already failed.**

Once the registry exceeds what fits in a prompt, this stops being a prompt and becomes
retrieval-then-prompt: embed the mention, pull top-k candidates from the node store, resolve
against those few.

**Topic dedup is harder than person dedup.** A person has a name; a topic has whatever
description the speaker reached for. Person aliases converge; topic aliases proliferate, because
each mention invents its own label.

**Topic granularity has no natural boundary.** The prototype's hand-curated boundary rules exist
because automatic topic boundaries drifted and had to be adjudicated. Expect the same here: a
curated layer over the induced one.

### Stage 3. Fact extraction

Dated subject-predicate-object rows with verbatim quotes and unit pointers, validated against the
fact contract and the delta table. Rejections logged.

Order matters: **dedup precedes facts**, or facts bind to duplicate nodes.

### Stage 4. Narrative cells

One cell per above-threshold node per unit. **The dominant cost, and the batching decision lives
here.** Emit all N cells for a unit in one call rather than N calls, or the unit text is re-sent N
times. Costed in `05_fall_plan.md`.

### Stage 5. Maintenance: abstracts refold

An abstract is a fold over its node's cells, so `children_hash` says exactly when it is stale.
Refold only nodes whose cells changed: **O(nodes touched)**, not O(all nodes). That is the
difference between an affordable nightly pass and an unaffordable one.

Supersession and merges also resolve here, at read time rather than by rewriting rows.

### The threshold

**All nodes enter the fact layer. Only above-threshold nodes get narrative cells.** That places
the threshold between a cheap layer and an expensive one rather than between having something and
having nothing.

Three tiers, matching wiki practice (confirmed against the Naruto and Harry Potter wikis via
their MediaWiki APIs):

| Tier | On a wiki page | Scope | Cost |
|---|---|---|---|
| Facts | infobox (`born`, `died`, `alias`) | every node | cheap |
| Abstract | lead paragraph; Background, Personality, Appearance | every node | O(nodes) |
| Cells | Biography, per-year, named events; arcs | above threshold | O(nodes x units) |

Scabbers before the reveal gets facts and a paragraph (Ron's pet rat, unusually long-lived) and
no biography, because he is not doing anything. After the reveal, Pettigrew has a full segmented
one.

**A search therefore never returns null.** The abstract is the floor. Below-threshold nodes
degrade gracefully instead of disappearing. And nothing is lost when a node falls below
threshold, because the plot axis records that unit regardless. What is missing is the
entity-indexed *access path*, not the content, which makes it measurable rather than silent: ask
the same question against each axis and the difference is what the entity layer buys.

**What the threshold must not be.** Salience-by-action would demote exactly the entities that
carry an argument. Tip/Ozma and Scabbers/Pettigrew are the most-referenced concrete examples in
this project's own design discussion and they never act: they are cited, not participants.

**Major and minor are scoped per corpus, not properties of the node.** Tip is major in Oz and
minor in a chat archive. Same node, different salience. This falls out of the keying for free,
since cells are keyed by (node, unit) and units belong to corpora.

**Promotion** candidates, and they are not equivalent: cross-unit recurrence; within-unit
salience; retroactive promotion via a `same_as` merge; on demand when a query targets the node.

**Record "considered, below threshold" as distinct from "never considered."** The two are
indistinguishable later otherwise.

**Retroactive promotion is re-narration, not backfill.** A wiki's Pettigrew biography covers 1981
to 1993 as "hiding as a rat," a framing unavailable to anyone reading those chapters at the time.
Cells generated retroactively are written from an epistemic position the source did not have, a
second-order supersession where both accounts are valid from different vantage points.

### A free consistency gate

The plot-axis summary and the entity cells are **independent summaries over identical text**. If
the plot summary carries an event that no cell mentions, either it was invented or stage 1 missed
a thread. Set comparison, no ground truth, no judge model, catches both directions.

### Model tier per stage

The intuition that higher abstraction deserves a higher tier is **half right**, and the wrong
half is expensive.

| Stage | Volume | Difficulty | Errors | Tier |
|---|---|---|---|---|
| Entity spotting | 1/unit | easy, NER is solved | local | cheap |
| **Coreference and alias resolution** | per ambiguous mention | **hard** | **propagate** | **high** |
| Fact extraction | 1/unit | medium | local, quote-gated | mid |
| Cell generation | **N/unit, dominates cost** | medium | recoverable | cheap to mid |
| Abstract refold | 1/node when stale | high | recoverable | high |
| Judge | low | high | n/a | high, and never the writer's tier |

**The rule is not "spend more at higher abstraction." It is: spend where errors propagate,
economise where they are recoverable.** A mediocre abstract costs one call to regenerate. A
corrupted entity registry costs a re-ingest. In the prototype, two entities whose names share a
substring cannot currently be told apart, and no amount of frontier-model summarisation fixes
that: a top-tier abstract over a merged node just writes a confident paragraph about a hybrid
that does not exist.

Both expensive categories are low-volume, so this is affordable. The cost driver is cell
generation, which is also the layer where a bad output is one cheap regeneration away.

### Risks carried forward

- **Stage 2 is the critical path** and the prototype already failed it at scale.
- **Predicate sprawl** breaks supersession silently, because `is_a`, `species` and `form` never
  collide. Count distinct predicates per unit; linear growth means the contract needs a
  controlled vocabulary.
- **Duplicate minting.** Count nodes minted per unit. A rising line is the failure.
- **Contract rejection on cheap tiers** is a format failure, not a comprehension failure, and has
  a different remedy (grammar-constrained decoding). Measure the two separately.

---

## 4. Retrieval

**Most retrieval here is a keyed lookup, not a similarity search.** Standard RAG embeds the query
and cosines against chunks. This store is indexed by node, so the first job is not "find similar
text" but "which node is this about." **Embeddings do entity resolution; they do not fetch
content.**

| Job | Method |
|---|---|
| Query to nodes | `nearest_nodes` over node-name and alias embeddings, then a cheap judgment over the top few |
| Node to abstract, cells, facts | keyed lookup, ordered |
| Unit to its text | keyed lookup |
| "Where do X and Y meet" | set intersection of their cells' unit ids |
| Exact name, phrase, number | `search_text`, BM25 |
| **Query resolves to no node** | `search_text` over cells and abstracts, the fallback, and it is not optional |

The node-name index is a few thousand short strings, not millions of chunks. This is entity
linking, not passage retrieval, and it reuses the stage-2 machinery.

**Question shape picks the partition.** *Who is X* reads the abstract. *What happened to X* reads
the cell sequence. *What happened in chapter 5* reads the unit summary. *Why did X do Y* reads
both nodes' cells, joined on shared units. Facts index into the sequence: a `same_as` firing at
unit N tells you which cells to fetch rather than all of them. That join is why both axes are
kept.

**Two honest weak points.** The whole path rests on query-side entity resolution. "The boy who
became a princess" names no node, the front end fails, and you are on the similarity fallback,
which must therefore be good rather than vestigial. The prototype's own worst retrieval failure
was a *query* failure fixed by multi-query, not a storage failure, which argues the fallback needs
query expansion more than a better index. And what gets ranked is **generated text**: cells and
abstracts are summaries, and every one points back to its unit, so drilling to source works, but
the thing you rank is not the thing that is true.

**Raw text is reachable, not ranked.** Drill-down is always available. Ranked search over raw is
the naive-RAG control arm and stays out of the default path; blend it in and the arms stop being
separable.

**Drill-down, at execution:**
```
cell -> unit_id -> doc_id -> file, sha256
fact -> unit_id, then unit.text.find(quote) -> +/-500 chars
```
Three dictionary lookups and a string find. No search, no ranking, because the pointer was
written at ingest time, so all the difficulty is in *storing* it correctly.

**Quote-primary, span-as-cache.** Span is fast, quote is durable. Any splitter change re-derives
units and invalidates every offset, but a quote still finds itself: on mismatch the quote wins and
the span is recomputed.

**Drill-down and the anti-fabrication gate are the same mechanism.** Following a quote to its unit
and checking that it lands is a drill-down; doing it for every assertion at once is the gate. A
`find` returning `-1` means either the quote was fabricated or preprocessing moved, and it is the
same check either way.

### Triggers

Three, and the distinction between them is where the design lives.

1. **Boundary hooks.** Session start and prompt submit, firing on new chat, topic shift, idle gap.
   Unconditional, no question required. Already built and running in the prototype.
2. **Explicit question.** The standard path.
3. **Agent-initiated.** Mid-task lookup.

**The hook cues; it does not retrieve.** It injects pointers and an instruction. Whether anything
is read is a discretionary second step, and that step demonstrably fails: during the 08-26/27
session, memory cues fired on nearly every turn, each naming three leaves, and almost none were
followed. The store held the content, the trigger fired correctly, the pointers were in context,
and nothing was read. **The trigger is not the broken part. The step after it is.**

**The fork worth measuring.** Does the hook inject **pointers** or **content**? Pointers are cheap
and leave a discretionary step that fails; content is expensive in tokens and removes the
discretion. Two arms, no corpus work required, since the hook, the store and a live agent all
already exist.

---

## 5. Rendering and delivery

A wiki page is **largely assembly of content that already exists**:

| Element | Source | Cost |
|---|---|---|
| Lead paragraph | stored abstract | zero |
| Biography sections | stored cells, ordered | zero |
| Infobox | fact rows | zero |
| Categories and groupings | query over facts | zero |

Only three parts need generation, and all three are low-volume folds: grouping cells into arcs
(24 chapter-cells become 5 sections), prose smoothing, and contradiction presentation. **If
rendering needs a frontier model every time, the store is not doing its job.** Distillation
happens once at write time so reads are cheap; a frontier call per page view inverts that.

**Two views of one page.** The *provenance view* is appended cells coloured by source work: pure
assembly, free, always available. The *article view* is the readable synthesis: one fold per node,
cached by `children_hash`, so it regenerates only when its cells change. That split is not new
machinery, it is the leaf-and-rollup architecture rendered. It also inherits the prototype's
measured finding that defects concentrate in the synthesised layer, where 39 node claims traced
back to raw gave 31 confirmed, 4 wrong and 4 unsupported, with every defect in the synthesis and
all 31 leaf checks clean. **The provenance view is the audit tool for the article view**, visible
to a reader instead of requiring a rotating audit.

**What colour-by-source buys.** Real wikis partition by source authority because they must, with
sections such as "Behind the scenes" and "In Other Media" kept separate from canon. Doing it
structurally means the Baum-to-Thompson authorial handover is visible on the entity page itself,
and for the Greek corpus source disagreement renders inline: Helen reached Troy per Homer, never
reached Troy per Euripides, both live, both cited, neither overwritten. No existing mythology wiki
does that, because a human writing one article cannot hold five contradicting sources in the
prose.

### Two deployments, one logical schema

Separated by a storage port of twelve operations.

**A, the research backend.** Neo4j, with the vector index and the graph in one store and temporal
traversal as a query. Graphiti (Zep's engine) runs on Neo4j and supplies temporal facts,
provenance to raw episodes, incremental writes, and hybrid retrieval, all specified independently
in this design.

**Zep does perform community detection and hierarchical summarisation.** Its community subgraph is
the highest level of the graph, and its nodes "contain high-level summarizations of these
clusters" (Rasmussen et al. 2025, p. 2). Community detection "builds upon the technique described
in GraphRAG" but uses label propagation rather than Leiden (p. 4), chosen for its straightforward
dynamic extension. An earlier claim in this repo that Zep lacks this was based on the Graphiti
README rather than the paper, and was wrong.

Two precision notes, because the correction was itself overstated once. Label propagation
**delays full refresh, it does not eliminate it**: the paper says the communities "gradually
diverge from those that would be generated by a complete label propagation run. Therefore,
periodic community refreshes remain necessary" (p. 4). That concession is useful rather than
damaging, since it means Zep also carries a batch refold. The remaining gap is narrower than first
stated: per-entity narrative sequences, unprompted firing, and per-stage cost accounting.

Two Graphiti capabilities were checked directly against source at commit `683a853` (v0.29.3) and
both came back usable:

- It ingests plain text, not only chat messages. `EpisodeType.text` is a first-class episode type,
  so a chapter goes in as one episode. There is no document abstraction, no loader and no
  splitter on the ingestion path, so unit splitting stays ours, and each episode body must fit the
  extraction model's context window. A `content_chunking` module exists but has zero callers in
  `graphiti_core` at that commit.
- It accepts pre-extracted entities. `add_triplet(source_node, edge, target_node)` takes
  constructed `EntityNode` and `EntityEdge` objects with no extraction call. Two caveats: it still
  runs node and edge resolution, so a supplied entity may be merged rather than stored as-is, and
  it creates no episode node, so triplets added this way carry no episode provenance.

Consequence: the Zep-as-baseline comparison stands on the literary corpora, and the spring product
does not need to build its own graph layer.

**B, the distributable.** JSONL as the store of record, `.npy` for embeddings, SQLite FTS5 for
text search, no server. The canonical data is entirely JSONL: human-readable, git-diffable, one
record per line. The two indexes are derived and disposable; delete them and they rebuild. This is
justified rather than merely convenient, since brute-force exact cosine is correct below roughly
100K vectors and a personal corpus is nowhere near that.

**Reaching a desktop client is MCP:** a Python server over stdio plus a config entry, where the
tool list is the capability contract. Two such servers already run against the prototype.

**One dependency decision outstanding.** `sentence-transformers` pulls torch, roughly 2GB, which
is not a folder someone scans a QR code for. Either ship precomputed embeddings with a small ONNX
runtime for the query vector, or drop embeddings from the distributable entirely: for a fixed
corpus with a built alias table, resolving a name is a dictionary hit plus fuzzy match, and FTS5
covers the rest. The second option gives zero ML dependencies and costs recall only on phrasings
that share no vocabulary with any alias.

**Not asserted:** current OpenAI and Gemini desktop MCP support. Check before promising
cross-client anywhere.

**Not adopted:** LangChain and LlamaIndex. They take ownership of chunking, retrieval strategy and
prompt templates, which is exactly the surface that has to be built and defended here.

---

## 6. Invariants

1. Raw is immutable. Ids are content hashes.
2. Nothing is overwritten. Supersession, merges and permissions all resolve at read time.
3. Every assertion carries a verbatim quote that must appear in its unit. Unverifiable claims are
   flagged or dropped, never asserted.
4. Every model call goes through the two interfaces, `embed(texts)` and
   `generate(prompt, schema, tier)`, and records its tier.
5. Every contract rejection is logged, so rejection rate per stage per tier is a query.
6. The abstract is a fold over cells; staleness is a hash comparison, never a wall-clock guess.
7. Every delta violation is a rejection, not a stored row.

---

## 7. Open questions

- **Mixed-corpus ordering.** Books order by narrative position, chats by wall clock. A store
  containing both has no defined sequence, and `(work_ordinal, unit_ordinal)` silently interleaves
  incomparable things.
- **Nothing demotes or retires.** Promotion is one-way, and the prototype already carries 82
  orphaned sheets from exactly this.
- **`kind` does two jobs**, routing extraction prompts and constraining delta. Those will want to
  diverge, because `event` and `topic` need the same predicates and very different prompts.
- **Conformance testing.** Two adapters, twelve operations, no shared test suite. The realistic
  failure is that the files adapter is developed against and the Neo4j adapter rots.
- **Embedding-to-node desync has no detector.** The `.npy` matrix and the node table are written
  separately, so a partial write leaves row *i* of the matrix pointing at the wrong node. There is
  no checksum tying them together, and the failure is silent: retrieval simply returns the wrong
  entity. Store a row count and a hash of the node-id ordering alongside the matrix and verify on
  load. Carried from the doc 15 quality pass, item 3, never absorbed.
- **FTS5 is assumed, not checked.** The distributable's text search depends on SQLite being
  compiled with FTS5, which is not universal. Probe for it at startup and fall back to an in-process
  BM25 if it is missing, or the distributable fails on a stranger's machine in the one way that
  cannot be debugged remotely. Carried from the doc 15 quality pass, item 4, never absorbed.
