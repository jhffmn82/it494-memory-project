# Retrieval: the query path

The master for the retrieval pipeline, its own notebook over the serving store and nothing else
of the build (ruled 2026-09-15; the draft is `notebooks/threadatlas-retrieval.py`). Ruled from the
manual in `log/2026-09-15/retrieval.md` with the seven corrections of its section 11 folded in;
that log is the snapshot, this file carries the rule; four edge-case rulings of the same evening
(an entry against a record; the discount as a bias; deterministic ties; the abstract's document
edge) are folded in where they apply. Every constant here is logged with every question. Sources
are in section 10.

## 1. What the path reads

From `threadatlas.sqlite` (SCHEMA.md, the serving store) and `threadatlas.npy` (one float16 row
per `vec_row`, 384 dimensions, unit length, loaded into memory as float32). The two travel
together in one Kaggle dataset written by the global-layer notebook, and this pipeline reads
that dataset and nothing else of the build (ruled 2026-09-15):

| table | columns used | role |
|---|---|---|
| `document` | `doc_id`, `title`, `occurred_at`, `source_uri` | the filter's unit; the date rendered with every record |
| `unit` | `unit_id`, `doc_id`, `position`, `label`, `occurred_at` | the order of records inside a document; a chat turn's time |
| `node` | `doc_id`, `node_id`, `name` | the entity a record belongs to |
| `fact` | all columns | one record kind; rendered as a clause with its quote |
| `cell` | `doc_id`, `node_id`, `unit_id`, `text` | one record kind; a unit's narrative for an entity |
| `abstract` | `doc_id`, `node_id`, `text` | one record kind; a document's or an entity's abstract |
| `instance_of` | `doc_id`, `node_id`, `parent_id` | child to parent, and back to the parent's other children |
| `collection`, `document_in` | `name`, `doc_id` | the filter can be a collection |
| `vec_row` | `row`, `record`, `doc_id`, `record_id` | the map from an array row to its record |
| `search` | `record`, `doc_id`, `record_id`, `text` (FTS5) | the keyword arm: one row per record |

A **record** is a fact, a cell or an abstract, keyed `(record, doc_id, record_id)`; a cell's
record id is `node_id@unit_id`. A record has one array row per sentence (one for a fact). A
parent summary also has rows (`record` = `parent`, no `doc_id`) and is a **route**: it can be an
entry, never a record the reader sees.

```
entry = a record or a parent route        what the two scans return and fusion ranks
pool  = records only                      what expansion fills, rerank scores and packing reads
```

The unit of packing is the record, never a sentence.

## 2. Inputs

```
question    a string
filter      a set of doc_id (a history, a collection, a book), or None for every document
arms        keyword on/off, vector on/off, parent hop on/off, budget in tokens
```

```
K_ENTRY   = 20      entry records per arm
K_HOP     = 10      neighbours per edge per entry record, by their own score
DISCOUNT  = 0.8     per hop
RRF_K     = 60      reciprocal rank fusion constant
BUDGET    = 6000    reader tokens (tiktoken o200k when present, else four tokens per three words)
PREFIX    = ""      the BGE query instruction, tried against no prefix on the 14 tuning questions, then frozen
```

## 3. The two entry scans

Both arms rank inside the filter and take their top K from that ranking; never rank, cut, then
filter. When the parent hop is off, parent rows are masked from the vector scan too, so the arm
compares the same local store with and without the identity tree.

### 3.1 Vector arm

```
q        = embed(PREFIX + question)                   bge-small-en-v1.5, unit length
s[i]     = <q, v_i>                                   one matrix product over the array
mask     rows whose doc_id is outside the filter; a parent's rows unless the hop is on and
         one of its children's documents is inside
score(r) = max over the rows i of entry r of s[i]
V        = the K_ENTRY entries with the largest score; ties by entry key ascending
```

The scan is exact and linear (ruled 09-14: linear, no index).

### 3.2 Keyword arm

FTS5 scores a `search` row against the question with BM25 (Robertson and Zaragoza 2009):

```
BM25(q, d) = sum over terms t in q of
             IDF(t) * f(t, d) * (k1 + 1) / ( f(t, d) + k1 * (1 - b + b * |d| / avgdl) )
IDF(t)     = log( (N - n(t) + 0.5) / (n(t) + 0.5) )
k1 = 1.2, b = 0.75                                    SQLite's defaults
```

The question's words (`\w+`) are each quoted and joined with OR; no term is chosen by code, the
IDF term makes a rare word dominate and a common one count near zero. One table, so one N and
one average length and one ranking. SQLite's `bm25()` returns the negative of the score, so the
SQL orders ascending; the filter is a `doc_id in (...)` clause in the same query.

```
W = select record, doc_id, record_id from search where search match q_or [and doc_id in filter]
    order by bm25(search), record, doc_id, record_id limit K_ENTRY
```

`W` holds records only: the `search` table has no parent rows, so a parent enters through the
vector arm alone.

### 3.3 Fusion

Reciprocal rank fusion (Cormack, Clarke and Buettcher 2009):

```
RRF(r) = sum over arms a listing r of  1 / (RRF_K + rank_a(r))        ranks are 1-based
E      = the entries of V and W ordered by RRF descending, ties by entry key ascending
```

An entry in both lists scores about twice one in either. With one arm off, E is the other's list.

## 4. Expansion, one hop

From every entry record, three edges, each masked by the filter. Every eligible neighbour is
scored on its own vector against the question (section 5's `score`); the top K_HOP per edge are
taken, ties by record key; the count of eligible neighbours per edge is logged.

```
node(e)      the facts, cells and abstract of e's entity (same doc_id, node_id)
document(e)  the facts and cells of e's unit and of the units at position +-1
parent(e)    if the hop is on: the facts, cells and abstracts of the other children of e's
             parent whose doc_id is inside the filter

fact or cell entry   node, document, parent
abstract entry       node, parent (no unit, so no document edge)
parent entry         parent only: the records of its children inside the filter
```

A parent entry never enters the pool. Record entries have `hops = 0`; a pulled record has
`hops = 1` and keeps the first route that reached it.

## 5. Rerank

```
score(r) = max over the rows i of r of <q, v_i>  *  DISCOUNT ^ hops(r)
```

The discount biases the order toward direct hits; a pulled record scores on its own content,
not its route, and a strong pulled record can outrank a weak direct hit (0.80 * 0.8 = 0.64 beats
0.35). Ties by record key ascending.

## 6. Packing

```
context = []; used = 0
for r in pool by score descending:
    text = render(r); n = tokens(text)
    if used + n > BUDGET: mark r cut; continue
    context.append(text); used += n; mark r packed
```

Whole records only, nothing truncated (BUILD.md). `render` is one function shared with the log:

```
fact      "<date> | <document> | <unit label> | <subject> <predicate> <object> (<qualifiers>)
             quote: "<quote>""
cell      "<date> | <document> | <unit label> | <entity>: <text>"
abstract  "<date> | <document> | abstract | <entity or document>: <text>"
```

The date is the fact's own, else its unit's, else its document's; a chat's document is shown by
its id's first eight characters, a titled document by its title. Every dated record is served
and nothing supersedes anything (ruled 09-13: no supersession this fall). The reader sees
source-owned records only.

## 7. The log

One JSON line per question in `questions.jsonl` beside the store:

```
asked_at, question, filter, arms, constants
entries:   [{record, rank_v, rank_w, rrf}]
eligible:  [{entry, edge, eligible}]
pool:      [{record, hops, route, score, packed}]
context:   the packed texts in order; tokens
```

A miss then divides into: never a candidate (not in `pool`); connected but cut at the hop (its
edge's `eligible` exceeds K_HOP and it is absent); in the pool but cut by the budget (`packed`
false); packed and misread by the reader. Every order in the path is total (score, then key), so
the context rebuilds byte for byte from the log.

## 8. The reader

One call with the packed context and the question, asked to answer from the records and nothing
else, and to say when they do not answer. The reply and the call's cost are logged with the
question.

## 9. Arms for the harness

```
keyword only        vector off
vector only         keyword off
fused               both on, parent hop on            the full system
fused, parent off   both on, parent hop off           what the tree buys
```

The 14 tuning questions are excluded from every reported number (ruled 09-13); a question is
scored only over a history ingested whole. Nothing else is added this fall: no cross-encoder,
no query rewriting, no multi-hop agent, no model reranking, no PageRank.

## 10. Sources

- BM25: Robertson, S. and Zaragoza, H. 2009. The Probabilistic Relevance Framework: BM25 and
  Beyond. Foundations and Trends in Information Retrieval 3(4), 333 to 389. SQLite FTS5's
  `bm25()`, k1 = 1.2, b = 0.75.
- Reciprocal rank fusion: Cormack, G. V., Clarke, C. L. A. and Buettcher, S. 2009. Reciprocal
  Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods. SIGIR 2009. k = 60.
- Hybrid keyword and vector retrieval: Anthropic, Introducing Contextual Retrieval, 2024; the
  Weaviate and Elastic hybrid-search evaluations.
- The embedder: Xiao, S., Liu, Z., Zhang, P. and Muennighoff, N. 2023. C-Pack (the BGE models);
  `bge-small-en-v1.5`, 384 dimensions, 512-token input.
- Expansion from entry hits through graph edges, then rerank: Gutierrez, B. J. et al. 2024,
  HippoRAG; Edge, D. et al. 2024, From Local to Global (Graph RAG local search). This path takes
  one hop with a fixed discount rather than PageRank, so a miss is attributable to one edge.
- Whole-record packing by rank within a budget and byte-for-byte replay: BUILD.md.
