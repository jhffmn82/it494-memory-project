> **SUPERSEDED 2026-08-27** by docs/17 (schema) and docs/19 (architecture). The quality pass in this file remains live and drove docs/16.
> Kept for the record; do not build from it. Index: `docs/README_SESSION_2026-08-27.md`.

# Schema and architecture

Proposal, 2026-08-27. Covers the storage model, the retrieval design, the trigger design,
and the tools, for two deployments that share one logical schema.

**Deployment A, the research backend.** Neo4j. Used for the corpus experiments and anything a
reviewer needs to reproduce at scale. Vector index and graph in one store.

**Deployment B, the distributable.** JSONL plus numpy plus SQLite, no server, no install beyond
Python. This is the folder a stranger points a desktop client at after scanning a QR code.

The two share every record definition and every operation. Only the adapter differs.

---

## 1. Logical schema

Seven record types. Field names are indicative, not final.

### Document
```
{doc_id, corpus_id, work_id, kind: text|chat, title,
 source_url, sha256, ingested_at}
```
Raw text lives beside it on disk, never edited. Content-hashed, so re-ingesting the same
material is a no-op rather than a duplicate.

### Unit
```
{unit_id, doc_id, unit_type: chapter|book|play|ode|hui|session,
 work_ordinal, unit_ordinal, title, span: [start, end], text}
```
The atom. Everything above points here. `unit_type` carries the heterogeneity forward as data
rather than erasing it: a Euripides play has no siblings to fold with, an Oz chapter does, and
downstream needs to know which it is holding.

### Node
```
{node_id, canonical_name, kind: person|org|place|thing|topic|event,
 created_from_unit}
```
Entities and topics are the same type. Dr. Fang is a node, the IT 494 project is a node, the
Chūnin Exams is a node. `kind` exists because extraction prompts differ and some predicates only
apply to some kinds, not because storage differs.

**Works are nodes too.** "Oz book 2" is a node of kind `topic`. This is what removes the need
for a separate chapter-summary type: the plot axis is simply cells on work nodes, and the book
blurb is that node's abstract.

### Alias
```
{alias, node_id, alias_kind: name|nickname|epithet,
 first_seen_unit, evidence_quote}
```
The keyword list mapping to one node. Resolution reads this; nothing writes over it.

### Fact
```
{fact_id, subject, predicate, object, object_is_node,
 qualifiers, unit_id, quote,
 asserted_at_unit, asserted_at_wallclock,
 tier, contract_version}
```
One dated assertion. Append-only. Nothing is ever overwritten and nothing carries a
`superseded_by` field, because supersession is a read-time computation over a functional-predicate
list, not a stored mutation.

### Cell
```
{cell_id, node_id, unit_id, corpus_id,
 work_ordinal, unit_ordinal, text, tier}
```
One node's narrative for one unit. The expensive layer, and the thresholded one.

Ordering is by `(work_ordinal, unit_ordinal)`, never a single integer, because a node's cells
span multiple works.

### Abstract
```
{node_id, corpus_id, text, children_hash, tier, updated_at}
```
One paragraph per node **per corpus**, because salience is corpus-scoped: Tip is a major entity
in Oz and a passing citation in a conversation archive. `children_hash` is computed over the
node's cells, so the abstract is stale exactly when its cells change and the refold is
incremental rather than a full pass.

### Instrumentation
```
Rejection  {rej_id, ts, stage, contract_version, tier, error}
Run        {run_id, ts, arm, question_id, injected_ids, verdict,
            judge_tier, tokens_in, tokens_out, latency_ms}
Consult    {consult_id, ts, cued_node_ids, retrieved_ids, used_ids}
```
`Consult` is the proactive-recall instrument and needs to exist from day one, because the rate
means nothing without weeks of collection.

---

## 2. The storage port

Twelve operations. Everything above sits on these, and nothing in the pipeline touches an
adapter directly.

```
put_document / get_document
put_unit / get_unit / get_units(work_id) -> ordered
put_node / get_node
resolve_alias(text) -> node_id | None
nearest_nodes(vector, k) -> [(node_id, score)]
put_fact / get_facts(subject, as_of=None)
put_cell / get_cells(node_id, corpus_id) -> ordered
put_abstract / get_abstract(node_id, corpus_id)
search_text(query, scope, k) -> [(id, score)]
log_consult(record)
```

Both adapters implement all twelve. The pipeline is written once.

---

## 3. Retrieval

**Most retrieval is a keyed lookup, not a similarity search.** Embeddings do entity resolution;
they do not fetch content.

| Job | Method |
|---|---|
| Query → nodes | `nearest_nodes` over node-name and alias embeddings, then a cheap judgment over the top few |
| Node → abstract, cells, facts | keyed lookup, ordered |
| Unit → its text | keyed lookup |
| "Where do X and Y meet" | set intersection of their cells' unit ids |
| Exact name, phrase, number | `search_text`, BM25 |
| **Query resolves to no node** | `search_text` over cells and abstracts. The fallback, and it is not optional |

Question shape picks the partition. *Who is X* reads the abstract. *What happened to X* reads
the cell sequence. *Why did X do Y* reads both nodes' cells joined on shared units. Facts index
into the sequence: a `same_as` firing at unit N tells you which cells to fetch rather than all of
them.

**Raw text is reachable but not ranked.** Drill-down is always available; ranked search over raw
exists as the naive-RAG control arm and stays out of the default path, or the arms are not
separable.

### Drill-down
```
cell  -> unit_id -> doc_id -> file, sha256
fact  -> unit_id, then unit.text.find(quote) -> ±500 chars
```
Three dictionary lookups and a string find. Quote is the durable pointer, span is a cache: a
splitter change invalidates every offset but a quote still finds itself, so on mismatch the quote
wins and the span is recomputed.

**Drill-down and the anti-fabrication gate are the same mechanism.** Running it over every
assertion at once is the gate.

---

## 4. Triggers

Three, and the distinction between them is where the design lives.

1. **Boundary hooks.** SessionStart and UserPromptSubmit, firing on new chat, topic shift, idle
   gap. Unconditional, no question required. Already built.
2. **Explicit question.** Standard path.
3. **Agent-initiated.** Mid-task lookup.

**The hook cues; it does not retrieve.** It injects pointers and an instruction, and whether
anything is read is a discretionary second step that demonstrably fails. Whether the hook should
inject pointers or content is a two-arm experiment that needs no corpus work.

---

## 5. Tools

| Layer | Choice | Notes |
|---|---|---|
| Embeddings | `sentence-transformers` | Local, small models adequate for short name strings |
| Vector top-k (B) | numpy dot product | Correct below ~100K vectors, per the vector survey |
| Vector top-k (A) | Neo4j native vector index | Co-located with the graph, one query |
| Text search (B) | SQLite FTS5 via stdlib `sqlite3` | BM25, no install. Fallback `rank_bm25` if FTS5 is absent |
| Text search (A) | Neo4j full-text index | Lucene-backed |
| Structured output | `outlines` or Ollama grammar mode; `pydantic` to validate | Grammar constraint makes malformed JSON structurally impossible |
| Graph (A) | `neo4j` driver, optionally `graphiti-core` | Graphiti supplies the temporal layer if not hand-written |
| Client integration | `mcp` Python SDK | The tool list is the capability contract. This is how the folder snaps onto a desktop client |

**Deliberately not adopted:** LangChain and LlamaIndex. They take ownership of chunking,
retrieval strategy and prompt templates, which is exactly the surface that has to be built and
defended here.

---

## 6. Invariants

1. Raw is immutable. Ids are content hashes.
2. Nothing is overwritten. Supersession and merges resolve at read time.
3. Every assertion carries a verbatim quote that must appear in its unit. Unverifiable claims
   are flagged or dropped, never asserted.
4. Every model call goes through the two interfaces and records its tier.
5. Every contract rejection is logged, so rejection rate per stage per tier is a query.
6. The abstract is a fold over cells; staleness is a hash comparison, never a wall-clock guess.

---

# Quality pass

Errors and gaps found on review, worst first.

### 1. Multi-tenancy is absent from the schema

Deployment B's stated end state is a backend that scales from one user to an organisation, and
there is no `tenant_id` anywhere. Retrofitting it touches every record type and every one of the
twelve operations. **Add it now or state explicitly that B is single-tenant and the
organisational version is a different schema.** Related: Rezazadeh's Collaborative Memory
(2505.18279) stamps provenance per fragment and checks it against time-varying permission graphs
at read time. If shared memory is ever in scope, access control belongs in the record, not around it.

### 2. Mixed corpora have no defined ordering

`asserted_at_unit` orders literature by narrative position. `asserted_at_wallclock` orders chat.
A user archive containing both books and conversations has **no defined sequence**, and the cell
ordering `(work_ordinal, unit_ordinal)` silently interleaves incomparable things. Needs an
explicit rule: either corpora never mix in one sequence, or a per-corpus sort key is declared.

### 3. The vector index and the node table can desynchronise

In deployment B the embeddings are a flat `.npy` and the mapping from row index to `node_id` is a
separate file. Any partial write leaves them inconsistent, and the failure is silent — you get
plausible wrong entities rather than an error. Needs either a single file holding both, or a
checksum verified at load.

### 4. SQLite FTS5 is not guaranteed

The zero-dependency claim rests on FTS5 being compiled into the local Python. It usually is, and
it sometimes is not. The distributable needs a capability check at startup and a `rank_bm25`
fallback, or the QR-code artifact fails on a stranger's machine, which is the one place it must not.

### 5. "Answer used the memory" has no reliable signal

The `Consult` record's `used_ids` is the whole proactive-recall instrument, and there is no sound
way to populate it. Model self-report is unreliable. The defensible version is a paired
counterfactual — run the same question with and without the memory injected and diff the answers
— which is what ProactAgent (2604.20572) does, and it doubles the cost of every measured query.
Decide which, and price it.

### 6. Nothing demotes or retires

Entities are promoted minor → major and threads accrete. Nothing goes the other way, and nothing
retires a node that stopped mattering. The live archive already carries 82 orphaned sheets from
exactly this. Cheaper to design now than to retrofit against a large registry.

### 7. One cell per (node, unit) flattens multiple appearances

A chapter with two separate scenes involving the same character produces one cell. Probably
acceptable, but it is a modelling decision being made by omission rather than on purpose, and it
should be written down.

### 8. Corpus-scoped abstracts, globally-scoped nodes

A node is global; its abstract and cells are corpus-scoped. That is correct, but it means
`get_node` and `get_abstract` have different scoping rules, which is the kind of asymmetry that
produces bugs six months later. Worth a note in the port documentation rather than leaving it
implicit in the signatures.

### 9. `kind` is doing two jobs

It routes extraction prompts *and* constrains which predicates apply. Those are different
concerns and they will want to diverge — `event` and `topic` need the same predicates but very
different prompts. Consider separating `kind` from `predicate_class` before either is entrenched.

### 10. Deployment A and B will drift unless the port is tested against both

Twelve operations, two adapters, and no stated conformance test. The realistic failure is that
the files adapter is developed against and the Neo4j adapter rots. **One shared test suite run
against both adapters** is the only thing that prevents it, and it is cheap to write early and
expensive to retrofit.
