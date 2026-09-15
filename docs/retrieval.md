# Retrieval

The master for the retrieval pipeline: its own notebook over the serving store's dataset
(`threadatlas.sqlite` and `threadatlas.npy` together) and nothing else of the build. Ruled
2026-09-15 in three passes: the manual (`log/2026-09-15/retrieval.md`, approved with its section
11 corrections), four edge-case rulings, and the typed traversal after GPT's second review; the
ledger in `docs/rulings.md` carries the lines. Part A is the pipeline; Part B the implementation
(constants, equations, log format, harness arms). Every constant is logged with every question.

# Part A. The pipeline

ThreadAtlas retrieval follows the structure the ingestor and the global layer built rather than
treating every stored text as an interchangeable chunk. The store holds a book or paper at
several resolutions:

```
document abstract  ->  entity abstract  ->  narrative cell (per unit, in order)  ->  facts  ->  quotes
```

A document has an abstract of the whole work. Each major entity has a document-local abstract
over the work, and beneath it one narrative cell per unit it appears in, in unit order. The
facts of a unit are atomic claims with verbatim quotes; adjudicated facts consolidate them
within the document and cite the raw facts behind them. Above the document-local entity the
global layer adds one level:

```
global parent  ->  document-local instances of the same entity
```

A parent is cross-document identity only. It owns no claim, is never evidence, and in retrieval
does one thing: connects one source-local representation of an entity to that entity's
representations in other documents.

A chat session has a different shape: a session abstract, major entity nodes, and quote-backed
facts (a minor's facts on the session node, direction `mentioned`); no cells, no entity
abstracts. Nothing branches on the source: the same operations follow whatever the store holds,
and where a representation is absent its edge is empty.

```
SEARCH        hybrid lexical and vector entry inside the filter, fused by rank
ROUTE         to the representation above the entry, and across the identity tree
TRAVERSE      along the entity's narrative in unit order
SUBSTANTIATE  down to facts and their quotes
PACK          coherent bundles, whole, by score, to the budget
ANSWER        the reader sees source-owned evidence only
```

## A1. Search

The question enters through both arms at once: BM25 over one full-text table with a row per
record, and cosine over the sentence vectors, each ranked inside the document filter, fused by
reciprocal rank. An entry is a document abstract, an entity abstract, a narrative cell, a fact,
or a parent summary (a route, never evidence; only when the parent hop is on). The stage decides
where to enter the structure, not what the reader sees. A question about how an entity changes
tends to enter through its abstract or a cell; a question about one claim through a fact. No
code chooses: the two arms rank, the fusion orders.

## A2. Route

From the entry, up to the representation above it and across the tree, one hop:

```
fact       -> its entity's cell in that unit; its entity's abstract
cell       -> its entity's abstract
any child  -> its parent's other children's abstracts inside the filter   (parent hop on)
parent     -> its children's abstracts inside the filter; the parent itself enters no pool
```

## A3. Traverse

Along the entity's narrative, by unit position, one hop:

```
cell       -> the previous and the next cell of the same entity
abstract   -> that entity's cells in unit order; a document's abstract -> the document node's
              cells, the unit summaries in order
```

The edges are the entity's own trajectory, never the unit's neighbourhood: a chapter's cast is
not evidence about one of its members; where that member was just before and just after is.
Every edge fires from every entry of its kind; none is conditional on the question.

## A4. Substantiate

Down to the evidence, one hop:

```
cell       -> its entity's facts in that unit: adjudicated facts first, raw facts with quotes
abstract   -> that entity's facts
fact       -> nothing further; its quote travels with it
```

## A5. Pack

The packing unit is the bundle, a coherent evidence unit rather than a row:

```
cell bundle   the cell, then the facts of the same entity in the same unit that were pulled,
              each with its quote; headed by document, date, unit label, entity
abstract      alone
fact          alone with its quote, when its cell is not in the pool
```

Bundles are ranked by the score of their head record (each record scored on its own vector,
discounted once per hop) and packed whole until the budget is spent. A parent summary is never
packed.

## A6. Three questions, traced

```
How does Tip become Ozma?
  Tip's abstract or a late Tip cell (search)
  -> the cell of the reversal (traverse: next)
  -> the facts and quote that Tip is Princess Ozma (substantiate)
  -> the Ozma parent -> the Ozma instance in the next book, its abstract (route)
  packed: the Tip cells with their facts, then Ozma's abstract

How does Ozma's role change between the two books?
  an Ozma or Tip entry in either book (search)
  -> its abstract and neighbouring cells (route, traverse)
  -> the parent -> the other book's instance, its abstract (route)
  the parent supplies continuity; the two documents supply the claims

Who is Ozma's father?
  a fact naming Pastoria, or Ozma's abstract (search)
  -> the claim with its quote (substantiate)
  no narrative is dragged in; the rerank leaves it below the budget
```

A chat: `session abstract or fact or entity node -> the session's facts -> the quoted turn`; the
parent still connects a chat entity to the same entity elsewhere when the hop is on.

## A7. Why this shape

Search decides where to enter; the store's structure decides where to move; facts and quotes
decide what counts as evidence. Navigation and evidence stay distinct, as everywhere else in the
system. The parent-off arm is the same pipeline with the identity edges removed and the parent
rows masked from search, so what the tree buys is measured as narrative continuity across
documents and nothing else. And a miss divides in the order the path runs: the entity was never
found; the episode was never reached; the other document was never reached; the evidence was
never recovered; cut by the budget; misread by the reader.

# Part B. Implementation

## B1. What the path reads

From `threadatlas.sqlite` (SCHEMA.md, the serving store) and `threadatlas.npy` (one float16 row
per `vec_row`, 384 dimensions, unit length, loaded into memory as float32), both from the one
dataset the global-layer notebook writes:

| table | columns used | role |
|---|---|---|
| `document` | `doc_id`, `title`, `occurred_at`, `source_uri` | the filter's unit; the date rendered with every bundle |
| `unit` | `unit_id`, `doc_id`, `position`, `label`, `occurred_at` | narrative order; a chat turn's time |
| `node` | `doc_id`, `node_id`, `name` | the entity a record belongs to |
| `fact` | all columns | atomic claims with quotes |
| `adjudicated_fact` | `doc_id`, `node_id`, `predicate`, `object`, `qualifiers`, `from_facts` | consolidated claims citing raw facts |
| `cell` | `doc_id`, `node_id`, `unit_id`, `text` | the narrative state per unit |
| `abstract` | `doc_id`, `node_id`, `text` | an entity's or a document's abstract |
| `instance_of` | `doc_id`, `node_id`, `parent_id` | child to parent and back to its other children |
| `collection`, `document_in` | `name`, `doc_id` | a filter can be a collection |
| `vec_row` | `row`, `record`, `doc_id`, `record_id` | array row to record |
| `search` | `record`, `doc_id`, `record_id`, `text` (FTS5) | the keyword arm, one row per record |

A **record** is a fact, a cell or an abstract, keyed `(record, doc_id, record_id)`; a cell's
record id is `node_id@unit_id`; a record has one array row per sentence, one for a fact. A
parent summary has rows too (`record` = `parent`, no `doc_id`) and is a **route**.

```
entry  = a record or a parent route        what the two scans return and fusion ranks
pool   = records only                      what traversal fills, rerank scores and packing reads
bundle = a cell with its pulled facts | an abstract | a fact without its cell
```

## B2. Inputs and constants

```
question    a string
filter      a set of doc_id (a history, a collection, a book), or None for every document
arms        keyword on/off, vector on/off, parent hop on/off, budget in tokens

K_ENTRY   = 20      entries per arm
K_HOP     = 10      records per edge per entry, by their own score
DISCOUNT  = 0.8     per hop
RRF_K     = 60      reciprocal rank fusion constant
BUDGET    = 6000    reader tokens (tiktoken o200k when present, else four tokens per three words)
PREFIX    = ""      the BGE query instruction, tried against no prefix on the 14 tuning questions, then frozen
```

## B3. The entry scans

Both arms rank inside the filter and take their top K from that ranking; never rank, cut, then
filter. With the parent hop off, parent rows are masked from the vector scan too.

Vector arm:

```
q        = embed(PREFIX + question)                   bge-small-en-v1.5, unit length
s[i]     = <q, v_i>                                   one matrix product over the array
mask     rows whose doc_id is outside the filter; a parent's rows unless the hop is on and one
         of its children's documents is inside
score(r) = max over the rows i of entry r of s[i]
V        = the K_ENTRY entries with the largest score; ties by entry key ascending
```

Keyword arm, BM25 (Robertson and Zaragoza 2009) as FTS5 computes it:

```
BM25(q, d) = sum over terms t in q of
             IDF(t) * f(t, d) * (k1 + 1) / ( f(t, d) + k1 * (1 - b + b * |d| / avgdl) )
IDF(t)     = log( (N - n(t) + 0.5) / (n(t) + 0.5) )        k1 = 1.2, b = 0.75

W = select record, doc_id, record_id from search where search match q_or [and doc_id in filter]
    order by bm25(search), record, doc_id, record_id limit K_ENTRY
```

The question's words (`\w+`) are each quoted and joined with OR; no term is chosen by code; one
table, one N, one ranking; `bm25()` is negative so ascending is best first. `W` holds records
only: `search` has no parent rows, so a parent enters through the vector arm alone.

Fusion (Cormack, Clarke and Buettcher 2009):

```
RRF(r) = sum over arms a listing r of  1 / (RRF_K + rank_a(r))        ranks 1-based
E      = the entries of V and W by RRF descending, ties by entry key ascending
```

## B4. Traversal

For every entry in E, the edges of A2 to A4 by entry kind; each edge masked by the filter;
every eligible record scored by `score` (B5) on its own vector; the top K_HOP per edge, ties by
record key; the eligible count per edge logged. One hop; a pulled record is not expanded.

```
fact entry       route: cell, abstract, children of its parent    traverse: none         substantiate: none
cell entry       route: abstract, children of its parent          traverse: prev, next   substantiate: facts in the unit
abstract entry   route: children of its parent                    traverse: its cells    substantiate: its facts
parent entry     route: its children's abstracts                  traverse: none         substantiate: none
```

Edge names in the log: `cell`, `abstract`, `parent` (the other children's abstracts),
`children` (a parent entry's), `previous`, `next`, `cells`, `facts`. A chat's session abstract:
`cells` empty, `facts` the session's facts including the mentioned ones. Entry records have
`hops = 0`; a pulled record `hops = 1`, its edge and the entry it came from; a record reached
twice keeps the first route. The parent-off arm removes `parent` and `children`.

## B5. Rerank

```
score(r) = max over the rows i of r of <q, v_i>  *  DISCOUNT ^ hops(r)
```

The discount biases toward direct hits without guaranteeing them: a pulled record at 0.80
scores 0.64 and beats a direct hit at 0.35. Ties by record key ascending. A bundle's score is
its head record's.

## B6. Packing and rendering

```
bundles = for each cell in the pool: (cell, the pool's facts of the same entity in the same unit)
          for each abstract in the pool: (abstract)
          for each fact in the pool whose cell is not in the pool: (fact)
context = []; used = 0
for b in bundles by score descending, ties by head key:
    text = render(b); n = tokens(text)
    if used + n > BUDGET: mark b cut; continue
    context.append(text); used += n; mark b packed
```

Whole bundles, nothing truncated; a fact inside a packed bundle is packed through it and never
twice. `render` is one function shared with the log:

```
cell bundle   "<date> | <document> | <unit label> | <entity>: <cell text>
                 - <subject> <predicate> <object> (<qualifiers>)   quote: "<quote>"
                 - ..."
abstract      "<date> | <document> | abstract | <entity or document>: <text>"
fact          "<date> | <document> | <unit label> | <subject> <predicate> <object> (<qualifiers>)
                 quote: "<quote>""
```

The date is the fact's own, else its unit's, else its document's; a chat is shown by the first
eight characters of its id, a titled document by its title. Every dated record is served and
nothing supersedes anything (ruled 09-13). The reader sees source-owned records only.

## B7. The log

One JSON line per question in `questions.jsonl` beside the store:

```
asked_at, question, filter, arms, constants
entries:   [{record, rank_v, rank_w, rrf}]
eligible:  [{entry, edge, eligible}]
pool:      [{record, hops, edge, from, score, bundle, packed}]
context:   the packed texts in order; tokens
```

Every order in the path is total (score, then key), so the context rebuilds byte for byte from
the log, and a miss divides as A7 says.

## B8. The reader

One call with the packed context and the question, asked to answer from the records and nothing
else and to say when they do not answer. The reply and the call's cost are logged with the
question.

## B9. Arms for the harness

```
keyword only        vector off
vector only         keyword off
fused               both on, parent hop on                          the full system
fused, parent off   parent and children edges off, parent rows masked    what the tree buys
```

The 14 tuning questions are excluded from every reported number (ruled 09-13); a question is
scored only over a history ingested whole. Not this fall: a cross-encoder, query rewriting, a
multi-hop agent, model reranking, PageRank, the same-unit co-occurrence edge.

## B10. Sources

- BM25: Robertson, S. and Zaragoza, H. 2009. The Probabilistic Relevance Framework: BM25 and
  Beyond. Foundations and Trends in Information Retrieval 3(4). SQLite FTS5's `bm25()`.
- Reciprocal rank fusion: Cormack, G. V., Clarke, C. L. A. and Buettcher, S. 2009. SIGIR 2009.
- Hybrid keyword and vector retrieval: Anthropic, Introducing Contextual Retrieval, 2024; the
  Weaviate and Elastic hybrid-search evaluations.
- The embedder: Xiao, S. et al. 2023. C-Pack (the BGE models); `bge-small-en-v1.5`.
- Entry then traversal then rerank: Gutierrez, B. J. et al. 2024, HippoRAG; Edge, D. et al.
  2024, From Local to Global (Graph RAG local search). This path takes one typed hop with a
  fixed discount rather than PageRank, so a miss is attributable to one edge.
- Whole-item packing by rank within a budget and byte-for-byte replay: BUILD.md.
