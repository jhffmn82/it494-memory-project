# Retrieval and delivery

**CORRECTION 2026-08-27 (later):** an earlier claim in this repo that Graphiti/Zep does
not perform community detection or hierarchical summarisation was **WRONG**. It was based on the
Graphiti repository README, not the paper. Zep's paper defines a **community subgraph** as the
highest tier of its graph, whose nodes "contain high-level summarizations of these clusters,"
built with community detection that "builds upon the technique described in GraphRAG" using
label propagation instead of Leiden **specifically so it extends dynamically** without full
refresh. Zep therefore covers hierarchical summarisation AND incremental maintenance. The error
was treating an absence in a README as a capability finding.

**2026-08-27.** How a query is served, what triggers one, how pages render, and how the thing
reaches a user. Schema references point at `docs/17_schema_current.md`.

---

## 1. Retrieval

**The central claim: most retrieval here is a keyed lookup, not a similarity search.** Standard
RAG embeds the query and cosines against chunks. This store is indexed by node, so the first job
is not "find similar text" but "which node is this about." **Embeddings do entity resolution;
they do not fetch content.**

| Job | Method |
|---|---|
| Query → nodes | `nearest_nodes` over node-name and alias embeddings, then a cheap judgment over the top few |
| Node → abstract / cells / facts | keyed lookup, ordered |
| Unit → its text | keyed lookup |
| "Where do X and Y meet" | set intersection of their cells' unit ids |
| Exact name, phrase, number | `search_text`, BM25 |
| **Query resolves to no node** | `search_text` over cells and abstracts — the fallback, and it is not optional |

The node-name index is a few thousand short strings, not millions of chunks. This is entity
linking, not passage retrieval, and it reuses the ingest step-2 machinery.

### Question shape picks the partition

*Who is X* reads the abstract. *What happened to X* reads the cell sequence. *What happened in
chapter 5* reads the unit summary. *Why did X do Y* reads both nodes' cells, joined on shared
units.

**Facts index into the sequence.** A `same_as` firing at unit N tells you which cells to fetch
rather than all of them. That join is why both axes are kept.

### Two honest weak points

The whole path rests on **query-side entity resolution**. "The boy who became a princess" names
no node, the front end fails, and you are on the similarity fallback — which must therefore be
good, not vestigial. Wang et al.'s RAG best-practices work found hybrid sparse-plus-dense with
HyDE strongest; the live archive's own R4 failure was a *query* failure fixed by multi-query, not
a storage failure, which argues the fallback needs query expansion more than a better index.

And what gets ranked is **generated text**. Cells and abstracts are summaries. Every one points
back to its unit, so drilling to source works, but the thing you rank is not the thing that is
true.

### Raw text: reachable, not ranked

Drill-down is always available. **Ranked search over raw is the naive-RAG control arm** and stays
out of the default path — blend it in and the arms stop being separable.

Worth noting the precedent: the failure that motivated the v2 rebuild was a confident wrong
answer because content was never leafed *and* the search tools only read summaries. The fix
chosen then was coverage plus multi-query — repairing the derived layer rather than reaching past
it.

### Drill-down, at execution

```
cell -> unit_id -> doc_id -> file, sha256
fact -> unit_id, then unit.text.find(quote) -> ±500 chars
```

Three dictionary lookups and a string find. No search, no ranking — the pointer was written at
ingest time, so all the difficulty is in *storing* it correctly.

**Quote-primary, span-as-cache.** Span is fast, quote is durable. Any splitter change re-derives
units and invalidates every offset, but a quote still finds itself: on mismatch the quote wins
and the span is recomputed.

**Drill-down and the anti-fabrication gate are the same mechanism.** Following a quote to its unit
and checking it lands is a drill-down; doing it for every assertion at once is the gate. A `find`
returning `-1` means either the quote was fabricated or preprocessing moved — same check, both
failures.

---

## 2. Triggers

Three, and the distinction between them is where the design lives.

1. **Boundary hooks.** SessionStart and UserPromptSubmit, firing on new chat, topic shift, idle
   gap. Unconditional, no question required. **Already built and running.**
2. **Explicit question.** Standard path.
3. **Agent-initiated.** Mid-task lookup.

### The hook cues; it does not retrieve

It injects pointers and an instruction. Whether anything is read is a discretionary second step,
and that step demonstrably fails.

Observed directly during the 08-26/27 session: memory cues fired on nearly every turn, each
naming three leaves, and almost none were followed. The store held the content, the trigger fired
correctly, the pointers were in context, and nothing was read.

**The trigger is not the broken part. The step after it is.**

### The fork worth measuring

Does the hook inject **pointers** or **content**? Pointers are cheap and leave a discretionary
step that fails; content is expensive in tokens and removes the discretion. Two arms, no corpus
work required — the hook, the leaves and a live agent all already exist.

---

## 3. Page rendering

A wiki page is **largely assembly of content that already exists**:

| Element | Source | Cost |
|---|---|---|
| Lead paragraph | stored abstract | zero |
| Biography sections | stored cells, ordered | zero |
| Infobox | fact rows | zero |
| Categories / groupings | query over facts | zero |

Only three parts need generation, and all three are **low-volume folds**: grouping cells into
arcs (24 chapter-cells become 5 sections), prose smoothing, and contradiction presentation.

**If rendering needs a frontier model every time, the store is not doing its job.** Distillation
happens once at write time so reads are cheap; a frontier call per page view inverts that.

### Two views of one page

- **Provenance view** — appended cells, coloured by source work. Pure assembly, free, always.
- **Article view** — the readable synthesis. One fold per node, **cached by `children_hash`**, so
  it regenerates only when its cells change.

That split is not new machinery. It is the leaf/rollup architecture rendered: the coloured append
view *is* the leaf layer, the readable article *is* the rollup. And it inherits the finding that
defects concentrate in the synthesised layer — 39 node claims traced to raw gave 31 confirmed, 4
wrong, 4 unsupported, with every defect in the synthesis and all 31 leaf checks clean. **The
provenance view is the audit tool for the article view**, visible to a reader instead of
requiring a rotating audit.

### What colour-by-source buys

Real wikis partition by source authority because they must — `Behind the scenes`, `In Other
Media`, and Naruto's `Original Anime Arcs` separated from manga canon. Doing it structurally
means the **Baum-to-Thompson authorial handover is visible on the entity page itself**, and for
the Greek corpus, source disagreement renders inline: Helen reached Troy per Homer, never reached
Troy per Euripides, both live, both cited, neither overwritten.

No existing mythology wiki does that, because a human writing one article cannot hold five
contradicting sources in the prose. It is the one place where provenance and supersession stop
being architecture claims and become something a visitor sees in four seconds.

---

## 4. Delivery

Two deployments, one logical schema, separated by a storage port of twelve operations.

### A — research backend

Neo4j. Vector index and graph in one store, temporal traversal as a query.

Graphiti (Zep's engine) runs on Neo4j and supplies temporal facts, provenance to raw episodes,
incremental writes, and hybrid retrieval — all specified independently in this design. **Corrected 2026-08-27: Zep DOES perform community detection and hierarchical summarisation**,
via label propagation chosen for dynamic extension. The remaining gap is narrower than first
stated: per-entity narrative sequences, unprompted firing, and per-stage cost accounting.

Note also that Graphiti ships "prescribed and learned ontology," i.e. schema induction as a
config flag.

### B — the distributable

JSONL as the store of record, `.npy` for embeddings, SQLite FTS5 for text search. No server.

The canonical data is entirely JSONL — human-readable, git-diffable, one record per line. The two
indexes are **derived and disposable**: delete them and they rebuild.

Justified rather than merely convenient: the vector survey found brute-force exact cosine correct
below roughly 100K vectors, and a personal corpus is nowhere near that.

**Reaching a desktop client is MCP.** A Python server over stdio plus a config entry; the tool
list is the capability contract. Two such servers already run against the live archive.

**One dependency decision outstanding.** `sentence-transformers` pulls torch, roughly 2GB, which
is not a folder someone scans a QR code for. Either ship precomputed embeddings with a small ONNX
runtime for the query vector, or **drop embeddings from the distributable entirely** — for a
fixed corpus with a built alias table, resolving a name is a dictionary hit plus fuzzy match and
FTS5 covers the rest. The second gives zero ML dependencies and costs recall only on phrasings
sharing no vocabulary with any alias.

**Not asserted:** current OpenAI and Gemini desktop MCP support. Check before promising
cross-client in a proposal.

### Not adopted

LangChain and LlamaIndex. They take ownership of chunking, retrieval strategy and prompt
templates — exactly the surface that has to be built and defended here.
