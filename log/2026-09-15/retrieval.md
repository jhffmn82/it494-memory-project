# Retrieval: the query path, as a manual

2026-09-15. PROPOSED, for Justin's ruling before block 20 of `notebooks/threadatlas-global-layer.py`
is written. Every rule below traces to a ruling in `docs/rulings.md` (retrieval, 09-13 and 09-15) or
to a source named in section 8.

## 1. What the path reads

From `threadatlas.sqlite` (schema in block 4 of the notebook; the global side in SCHEMA.md):

| table | columns used | role |
|---|---|---|
| `document` | `doc_id`, `title`, `occurred_at`, `source_uri` | the filter's unit; the date rendered with every item |
| `unit` | `unit_id`, `doc_id`, `position`, `label`, `occurred_at` | the order of items inside a document; a chat turn's time |
| `node` | `doc_id`, `node_id`, `name`, `kind` | the child an item belongs to |
| `fact` | `doc_id`, `fact_id`, `subject`, `predicate`, `object`, `object_is_node`, `qualifiers`, `unit_id`, `quote`, `occurred_at`, `direction`, `provenance` | one item kind; rendered as a line with its quote |
| `cell` | `doc_id`, `node_id`, `unit_id`, `text` | one item kind; a unit's narrative for an entity |
| `abstract` | `doc_id`, `node_id`, `text` | one item kind; a document's or an entity's abstract |
| `parent` | `parent_id`, `name`, `kind`, `summary` | the parent hop's target; the summary is an item kind |
| `instance_of` | `doc_id`, `node_id`, `parent_id` | child to parent, and back to the parent's other children |
| `collection`, `document_in` | `collection_id`, `name`, `doc_id` | the filter can be a collection |
| `vec_row` | `row`, `record`, `doc_id`, `record_id`, `ordinal`, `text` | the map from an array row to its item |
| `fact_fts`, `cell_fts`, `abstract_fts` | FTS5 over `quote`, `text`, `text` | the keyword arm |

From `threadatlas.npy`: one float16 row per `vec_row`, 384 dimensions, unit length.

An **item** is one row of `vec_row`: a fact (one row), a cell sentence, an abstract sentence, or a
parent summary sentence. Its `record_id` names the record; its `doc_id` the document (null for a
parent summary). The unit of packing is the **record** (a whole fact, cell, abstract or parent
summary), never a sentence.

## 2. Inputs

```
question   a string
filter     a set of doc_id (a history, a collection, a book), or all documents
arms       keyword on/off, vector on/off, parent hop on/off, budget in tokens
```

Constants, defaults, all logged with the run:

```
K_ENTRY   = 20      entry hits per arm
K_HOP     = 10      items pulled per hop per entry item
DISCOUNT  = 0.8     per hop
RRF_K     = 60      reciprocal rank fusion constant (Cormack et al. 2009)
BUDGET    = the reader's context budget in its own tokenizer, less 15 percent (BUILD.md)
```

## 3. The two entry scans

### 3.1 Vector arm

```
q = embed(question)                                  bge-small-en-v1.5, unit length
s_v[i] = <q, v_i>                                    cosine, one matrix product over the array
mask rows whose doc_id is outside the filter (a parent row is kept when any of its
children's documents is inside the filter)
V = the K_ENTRY rows with the largest s_v
```

The scan is exact and linear; at the test set 15,000 rows, at the corpus about 1.5 million rows,
one matrix product either way (ruled 09-14: linear, no index).

### 3.2 Keyword arm

FTS5 scores a row against the question with BM25 (Robertson and Zaragoza 2009):

```
BM25(q, d) = sum over terms t in q of
             IDF(t) * f(t, d) * (k1 + 1) / ( f(t, d) + k1 * (1 - b + b * |d| / avgdl) )

IDF(t) = log( (N - n(t) + 0.5) / (n(t) + 0.5) )
k1 = 1.2, b = 0.75                                   SQLite's defaults
f(t, d) = the count of t in row d; |d| its length in tokens; avgdl the mean length;
N the rows in the table; n(t) the rows containing t
```

The question is passed whole: punctuation FTS5 reads as syntax is stripped, the words are joined
with OR, the tokenizer is `unicode61` with no stemming and no stop list. No term is chosen by
code; the IDF term makes a rare word ("Publix", "Tiktok") dominate and a common one ("the",
"want") count near zero.

```
for table in (fact_fts, cell_fts, abstract_fts):
    rows = select rowid, bm25(table) from table where table match q_or order by bm25 limit K_ENTRY
map each rowid to its vec_row rows (a cell or abstract record maps to all its sentence rows)
mask by the filter
W = the K_ENTRY records with the best BM25 across the three tables
```

### 3.3 Fusion

Reciprocal rank fusion over the two lists (Cormack, Clarke and Buettcher 2009):

```
RRF(r) = sum over arms a in which r appears of  1 / (RRF_K + rank_a(r))
E = the records of V and W ordered by RRF, descending
```

A record in both lists scores about twice one in either. With one arm off, E is that arm's list.

## 4. Expansion, one hop

From every entry record e, three edges of the store, each capped at K_HOP and masked by the filter:

```
node(e)      the other facts and cells of e's child (same doc_id, node_id)
document(e)  the other records of e's unit, and the adjacent units' records (position +-1)
parent(e)    if the parent hop is on: the parent of e's child, its summary record, and the
             facts and cells of the parent's other children whose doc_id is in the filter
```

Every pulled record carries `hops = 1` and the entry record it came from; a record reached
twice keeps its best route. Entry records have `hops = 0`.

## 5. Rerank

Every record in the pool is scored against the question by its own vector:

```
s(r) = max over sentence rows i of r of  <q, v_i>  *  DISCOUNT ^ hops(r)
```

A direct hit outranks what it pulled in, and a pulled record scores on its own content, not
its route. Records are sorted by s(r), descending; duplicates by record id keep one row.

## 6. Packing

```
context = []
used = 0
for r in pool by s(r) descending:
    text = render(r)                                 one deterministic function per record kind
    n = tokens(text)                                 the reader's tokenizer
    if used + n > BUDGET: log r as cut; continue
    context.append(text); used += n; log r as packed
```

Whole records only; nothing truncated; the strongest first (BUILD.md). `render` produces, per
kind:

```
fact      "<date> | <document title or session id> | <subject> <predicate> <object> (<qualifiers>)
           quote: <quote>"
cell      "<date> | <document> | <unit label> | <entity>: <text>"
abstract  "<date> | <document> | <entity or document>: <text>"
parent    "<parent name> (<kind>), in <n> documents: <summary lines whose child is in the filter>"
```

The date is the record's `occurred_at` (a fact's own; a cell's or abstract's unit or document);
every dated fact is served and nothing supersedes anything (ruled 09-13, no supersession this
fall).

## 7. The log

One JSON line per question, written beside the store:

```
question, filter, arms, constants, q_tokens
entries:    [{record_id, arm(s), rank_v, rank_w, rrf}]
pool:       [{record_id, hops, route (entry record and edge), s, packed | cut}]
context:    the packed texts in order, and used tokens
```

A miss then divides into never a candidate (not in `pool`) against cut by the budget (in `pool`
with `cut`), and the context rebuilds byte for byte from the log (BUILD.md).

## 8. Sources

- BM25: Robertson, S. and Zaragoza, H. 2009. The Probabilistic Relevance Framework: BM25 and
  Beyond. Foundations and Trends in Information Retrieval 3(4), 333 to 389. SQLite's `bm25()`
  implements it with k1 = 1.2, b = 0.75 (SQLite FTS5 documentation, section 6.1).
- Reciprocal rank fusion: Cormack, G. V., Clarke, C. L. A. and Buettcher, S. 2009. Reciprocal
  Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods. SIGIR 2009, 758 to 759.
  k = 60 as in the paper.
- Hybrid keyword and vector retrieval beating either alone on exact-name-heavy questions:
  Anthropic, Introducing Contextual Retrieval, 2024 (BM25 added to embeddings); the same finding
  in the Weaviate and Elastic hybrid-search evaluations.
- The embedder: Xiao, S., Liu, Z., Zhang, P. and Muennighoff, N. 2023. C-Pack: Packaged
  Resources To Advance General Chinese Embedding (the BGE models); `bge-small-en-v1.5`, 384
  dimensions, 512-token input.
- Expansion from entry hits through graph edges, then rerank: Gutierrez, B. J. et al. 2024.
  HippoRAG (personalized PageRank from entry nodes); Edge, D. et al. 2024. From Local to Global:
  A Graph RAG Approach (local search: entities, neighbours, community summaries). This path
  takes one hop with a fixed discount rather than PageRank, so that a miss is attributable to
  one edge.
- Whole-item packing by rank within a budget and byte-for-byte replay: BUILD.md, "Exact match,
  whole items, byte-for-byte replay".

## 9. Pseudocode

```
retrieve(question, filter, arms):
    q = embed(question)
    V = vector_entries(q, filter, K_ENTRY)               if arms.vector else []
    W = keyword_entries(question, filter, K_ENTRY)       if arms.keyword else []
    E = rrf(V, W, RRF_K)
    pool = {r: (0, "entry") for r in E}
    for e in E:
        for r in node_neighbours(e, filter, K_HOP):       pool.setdefault(r, (1, ("node", e)))
        for r in document_neighbours(e, filter, K_HOP):   pool.setdefault(r, (1, ("document", e)))
        if arms.parent:
            for r in parent_neighbours(e, filter, K_HOP): pool.setdefault(r, (1, ("parent", e)))
    for r in pool: s[r] = own_score(r, q) * DISCOUNT ** hops[r]
    context, log = pack(sorted(pool, by s descending), BUDGET)
    write_log(question, filter, arms, E, pool, s, context)
    return context

answer(question, context):
    one call to the reader model with the rendered context and the question; the reply and
    the call's cost logged with the retrieval log line
```

## 10. Arms for the harness

```
keyword only        V off
vector only         W off
fused               both on, parent hop on            the full system
fused, parent off   both on, parent hop off           what the tree buys
```

The 14 tuning questions are excluded from every reported number (ruled 09-13); a question is
scored only over a history ingested whole.
