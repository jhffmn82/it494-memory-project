# ThreadAtlas: End-to-End Pipeline

ThreadAtlas turns heterogeneous raw documents into a provenance-preserving store designed for
narrative retrieval across documents. The implemented build has three stages, each its own
Kaggle notebook; each reads the published output of the stage before it and no hidden
intermediate state.

```
raw files
   |
   v
1. EXTRACTOR          documents + dated units + pieces
   |
   v
2. INGESTOR           document-local entities, facts, cells, abstracts
   |
   v
3. GLOBAL LAYER       serving store + vectors + global identities + collections
   |
   v
threadatlas.sqlite + threadatlas.npy
   |
   v
4. RETRIEVAL          designed, not yet built (docs/retrieval.md)
```

Detailed specifications: `docs/extractor.md`, `docs/ingestor.md`, `docs/global-layer.md`,
`docs/retrieval.md`; field schemas `dataset/step0/SCHEMA.md`, `dataset/step1/SCHEMA.md`,
SCHEMA.md (the serving store); the rulings and their dates `docs/rulings.md`. Measured numbers
are from extractor 1.8, ingestor 1.8 and the global layer as of 2026-09-15.

## System invariants

**Provenance before inference.** The model never supplies a source offset. When a model
identifies text, code must locate that text in the source before the result is accepted: a
structural boundary must copy source text; a fact's quotation must slice from the document;
metadata copied from a line must occur on that line; a global parent's name must be carried by
one of its instances. Model output proposes structure or interpretation; code verifies its
connection to the source.

**Append rather than overwrite.** Records are not edited after they are written. A correction
becomes a new record or an explicit adjudication rather than destroying the earlier
representation.

**Dates remain attached to evidence.** Documents, units and facts carry dates. There is no
supersession rule in the current build; if two dated facts disagree, both remain available.

**Calls are observable.** All model calls use one interface, `generate(prompt, schema)`, and
every call logs model, service tier, tokens, duration, cost, schema failures and retries. A
response that fails its schema receives one retry with the validation error appended; a second
failure is logged as a rejection. `gpt-5.6-luna` reads, checks and writes prose;
`gpt-5.6-terra` reconciles, folds and adjudicates. Flex tier, priced by the tier that served.
Each run has a spending stop; failure to obtain a usable model connection is fatal rather than
producing a corpus of empty records.

## 1. Extractor: raw bytes to a dated document structure

**Purpose.** What is this file, what text does it contain, and how should that text be divided
into meaningful dated units? No entities, no facts, no summaries; a structural representation for
the ingestor.

**Input.** The raw dataset, one folder per corpus, a manifest with a SHA-256 per file; 24,071
files. The extractor sees each raw file independently: no corpus-specific filename convention,
no publisher-specific rule, no hand-listed chapter names, nothing from another document.

**Output.** `documents.jsonl` (the normalised text and metadata), `units.jsonl` (the ordered
spans passed to the ingestor), `pieces.jsonl` (the structural pieces the units were formed
from), `receipt.json`. All offsets are character indices into `documents.text`, so every later
quotation uses one coordinate system. `doc_id` is the SHA-256 of the source bytes; ingesting the
same file again yields the same identifier.

### 1.1 Format detection

The physical format is sniffed from the bytes: PDF with a text layer (PyMuPDF), chat JSON, UTF-8
text.

**Chats.** No structural call. Each non-empty turn is one piece, one unit and one timestamped
record (`SESSION <id> TURN <n> <time>`, then `role: content`); the session's date is the earliest
turn; title = session id, author null, `source_class` record. Empty sessions and empty turns are
skipped and counted.

**Read documents.** Books, papers and the like are shown as numbered non-blank lines (numbered by
sentence when a PDF puts one word on a line). One Luna call proposes:

```
metadata    source_class, title, author, source
works       the separate works in the file, and the line stating each work's date
toc_count   the number of pieces the contents promise
regions     front_matter | body | notes | references | appendix | license
pieces      chapters, sections, scenes
```

Every proposed location is a line pointer plus copied source text. Flags bring one retry on
Luna; still flagged, one try on Terra when the document is under 80,000 tokens; the answer kept
has a body region and the fewest flags.

### 1.2 Boundary verification

A line number is never trusted alone; the copied text must name the line: the complete line,
its first eight words, a run of at least five words, or a two-line heading copied whole. The
five-word rule keeps `CHAPTER I` from validating a pointer to `CHAPTER II`. Copied text found
nearby under a wrong number is recovered and counted; text found nowhere drops the boundary and
is counted.

### 1.3 Metadata and date verification

Metadata copied from a line must be a substring of that line; a date is accepted from the page
only when its year appears on the cited line. A work's date is when it was written, else first
published; never a translation, edition or ebook release. When the page gives no usable date,
one Luna web-search call by title and author supplies it, the URL kept in the flags. Forms:
`YYYY`, `YYYY-MM`, `YYYY-MM-DD`, a chat timestamp, a signed year with a year zero (`-0404` is
405 BC), `~` for approximate, `a/b` for a range. A piece takes its work's date; a document its
earliest unit's.

### 1.4 Pieces become units

```
split      a piece over CAP_WORDS 4,000 goes back as numbered lines; the model chooses cut points;
           up to three rounds; one it cannot divide stays whole and is flagged
merge      a piece under SHORT_WORDS 100 is offered with its text: it joins the piece before, the
           piece after, or stands alone
group      the outline (kind, heading, word count per piece) goes back; the model groups
           consecutive hierarchical pieces, a section with its subsections, never unrelated peers
           because they fit; code checks order and coverage, dissolves a group over the cap, and
           cuts a group at any change of kind or of date
```

Calls per document: a chat 0; a read document 1 read (up to 3 on flags) + 1 web search per
work not dated from the page + 1 per split round per over-cap piece + 1 merge when any piece is
short + 1 group. Six documents in parallel, splits eight at a time.

### 1.5 Extractor gates

Verified at export on every document: pieces tile the text; units tile the text; no gaps, no
overlaps; every unit non-empty; every unit one kind and one date; `unit_id` unique; every piece
points at a unit of its own document. Structural anomalies are flagged, never dropped: no body
region; piece count differs from the contents; one piece holds most of the body (added after
Metamorphoses left 97 percent of the body in its last unit). No claim of a gold segmentation or
gold date table.

### 1.6 Measured (1.8)

```
24,071 documents: 23,882 chat sessions in 500 histories, 189 read documents
251,446 units
$8.24; $0.0081 median per read document
405 works: 156 dated from the page, 237 by search, 12 undated
6 escalations to Terra; 103 of 189 read documents flagged
135 mismatched pointers, 50 dropped; 15 undated units
```

## 2. Ingestor: one document to one source-local knowledge package

**Purpose.** What does this document say, who or what does it talk about, and how do those
entities develop within this document? One document at a time; it never looks at a second. Every
entity, fact, cell, abstract, contradiction and reconciliation produced here is owned by one
source.

**Input.** `documents.jsonl`, `units.jsonl`, `pieces.jsonl`. **Output.** One package per
document: `node`, `alias`, `edge` (`appears_in` with its units, `has_unit`), `fact`, `cell`,
`abstract`, `adjudicated_fact`, `attribute`, `contradiction`, `rejection`, `ledger`,
`candidate`, `completion` (the counts). Readable ids: `<doc_id[:8]>:doc`, `:n<i>`,
`:u<unit>:f<n>`.

### 2.1 Books and papers

The hierarchy, preserved for retrieval:

```
document
   |-- document abstract
   +-- entity
        |-- entity abstract
        |-- narrative cell per unit
        +-- facts
             +-- source quotations
```

**2.1.1 Triage.** One Luna call names the unit kinds that are not the work; front matter and
license go by rule; an answer that would exclude more than half the document is ignored.

**2.1.2 Per-unit extraction,** four units at a time, three calls per unit:

```
entities   name, kind, salience (major | minor), surface forms; a surface form must occur in
           the unit's text
facts      subject, predicate, object, qualifiers, verbatim quote; the subject must be a listed
           entity; the quote must locate in the unit: exact | normalised | unwrapped | words;
           else rejected and logged as paraphrase | not_found | empty | duplicate |
           self_reference | unlisted_subject
cells      a unit summary and one narrative cell per major: the entity's state, actions or role
           in that unit
```

**2.1.3 Salience.** A unit may call an entity major or minor; major in any unit is major for the
document (ruling 09-07); proper naming and abstract naming do not promote; a major that ends
with neither facts nor cells is demoted. Minors have no node: a fact whose subject is a major is
stored forward, a fact pointing at a major is stored inverse with the minor's name as its value;
a fact between two minors is not stored.

**2.1.4 Reconciliation within one document.** Extraction is unit-local, so one entity may appear
as several locals. Two locals with the same proper name and kind merge with no call unless their
`is_a` conflict (a ledger row `unsure`). Other candidates arise from:

```
shared_surface   tier 1.00
is_a_link        tier 0.85
shared_word      tier 0.50

name   = 1.0 for shared_surface, else the difflib ratio of the normalised names
cooc   = |cast(a) & cast(b)| / |cast(a) | cast(b)|     cast = the other entities' names in the
                                                        local's own unit
score  = 0.7 * name + 0.3 * cooc                        dropped under SIMILAR_ENOUGH 0.35
```

Never proposed: two locals of one unit; a pair already ruled different, transitively over
clusters (decisions 44 and 51); a pair with no unit-major in it; an unnamed possession or part
against the entity its parenthetical anchors it to. Round by round, strongest first by (tier,
score), each entity in at most one pair per round; Terra judges ten pairs a call with each
cluster's dossier sent once: `same` unites, `different` becomes a persistent cannot-link,
`unsure` gets one final look and then means apart. Every candidate and every verdict is a
ledger row.

**2.1.5 Folding.** One Terra call folds the unit summaries into the document abstract (up to
400 words). Each major gets one Terra call folding its ordered cells into its entity abstract:
a cell is the entity in one unit; the abstract is the entity across the document.

**2.1.6 Adjudication and evidence.** A major with ADJUDICATE_MIN_FACTS 4 or more raw facts gets
one Terra call that returns consolidated facts, attributes and contradictions, each citing the
raw facts behind it; the raw facts stay the evidence layer. Every other raw fact is checked
against its passage, VERIFY_BATCH 60 a call. A flagged fact gets one Luna review: stand, reword
to what the passage states, or drop; a rewording is checked once more; a fact with no valid
verdict is dropped.

**2.1.7 The document node** carries record facts written from Step 0 with no call and no quote:
`has_title`, `has_author`, `has_date`, `has_source_class`, `belongs_to_history`.

Calls per book or paper: 1 triage + 3 per kept unit + ceil(pairs / 10) per reconcile round + 1
fold + 1 per major + 1 per major with 4+ facts + ceil(facts / 60) + the corrections; about
twenty-five for a short book. A document of one unit: no triage, entities then facts and cells
together, nothing to reconcile, the unit summary is the abstract, a major's own cell its
abstract, one support call; about four calls.

### 2.2 Chat sessions

A different shape: a session abstract, major entity nodes, quote-backed facts; no narrative
cells, no entity abstracts.

```
read       one Luna call (medium effort) over the turns, in windows of whole turns up to
           SESSION_WINDOW 40,000 characters: what the user states of their own life, one stated
           fact per user sentence that states a detail, the concrete information the assistant
           supplies (names, numbers, amounts, steps, options), and a summary; every fact names
           its turn and its quote must locate in that turn
entities   one per name the reading used; the same name across turns is one entity, no judge
salience   one Luna call: a one-word lowercase kind (never thing; a thing is refused and left
           null) and major | minor; the user stays a major person; an entity the reply omits
           is minor
nodes      a major becomes a node with its facts; a minor's facts stay on the session's document
           node with direction mentioned and provenance.subject_name
abstract   the reading's summary, no fold call
support    ceil(facts / 60) calls; verify; write
```

Calls per session: 1 read per window + 1 salience + support and corrections; about half a cent
a session, about $110 for all 23,882.

### 2.3 Measured (1.8, the 81 test documents, 09-14)

```
$5.47; 1,784 calls; 1 schema retry
6,929 facts; 6,605 quoted, every quote verified at its offsets
324 record facts; 1,113 mentioned facts
1,534 nodes; 643 chat nodes in 53 kinds
```

## 3. Global layer: source-local packages to a shared serving store

**Purpose.** Which document-local entities refer to the same identity across sources? It does
not merge their facts. Facts belong to documents; identity may cross documents. The global layer
connects source-local entities while leaving their claims, abstracts, cells, dates and quotations
with their source.

**Input.** The Step 1 dataset and Step 0's `documents.jsonl` (the text, used at load to verify
quotations and not retained). **Output.** `threadatlas.sqlite` (the serving store),
`threadatlas.npy` (the vector sidecar), `build.sqlite` (candidate pairs and unions),
`receipt.json`, the wiki pages.

### 3.1 Serving-store load

Every retained Step 1 record into SQLite; every quotation re-sliced from the Step 0 text at its
offsets, the load stopped on the first mismatch; counts checked against the completion records.
One `search` row (FTS5) per retrievable record: a fact's clause and quote, a cell's text, an
abstract's text. This is the lexical side of retrieval.

### 3.2 Vector sidecar

`BAAI/bge-small-en-v1.5`, 384 dimensions, float16, one row per sentence: rendered facts (clause,
date, document), cell sentences and abstract sentences prefixed with their entity and document
title, and, after the parents are written, parent-summary sentences. The children's identity
texts are embedded for nomination and not stored in the sidecar.

### 3.3 Children

A child is a document-local entity eligible for global identity: every node except the
document's own node and a chat's user node. Its identity text is name, kind, aliases, document
title and entity abstract (up to twelve facts when there is no abstract). It is immutable during
resolution: no model-written prose feeds back into identity.

### 3.4 Relational context

Each child's cast is the folded names of the other children that share at least one unit with
it, from the Step 1 `appears_in` edges. Name rarity is `log((N + 1) / (df + 1))`, N the documents
loaded, df the documents holding the name. The cast is contextual evidence for the judge; it
asserts nothing itself.

### 3.5 Candidate nomination

Three routes, each pair once:

```
vector     each child's NEAREST 8 other-document children by cosine, block matrix products of
           2,048 rows; two children of one document never pair by vector
lexical    two children of different documents sharing a name or a naming alias (a word after
           any leading article capitalised), through one index
identity   an is_a link between two children of one document
```

### 3.6 Pair signals

```
lexical     1 when the names or naming aliases intersect, else 0
vector      cosine of the two identity texts
cast        Jaccard of the two casts
cast_rare   the same with each name weighted by rarity
identity    1 for an is_a link
offered     lexical == 1 or identity == 1 or vector >= VECTOR_FLOOR 0.75
```

The floor was frozen on 2026-09-14 from the cosine distribution over the test store and pairs
read by eye, before any key is scored.

### 3.7 Bottom-up identity clustering

Every child starts in its own cluster (a union-find). Offered pairs are sorted by the tuple
(identity, lexical, vector) descending. In each round: pairs are walked strongest first; a pair
is taken only when neither of its clusters is taken this round (pairs disjoint, at most one per
cluster); the round is judged in parallel (16 in flight); `same` unites; `different` becomes a
cross-cluster constraint; the next round is drawn from the new state. A pair is skipped when its
children already share a cluster and blocked when any member of one cluster was ruled different
from any member of the other. The process stops when a round finds no eligible pair.

Why rounds and not a scan: the candidate count is bounded by nomination, not n squared; every
child starts on equal footing and order does not decide correctness; one wrong `same` chains
two entities, so only judged pairs join and every cluster's size is an instrument. Showing the
judge whole clusters chained 21 of 54 clusters in the first run; the pair-focused prompt brought
that to 0.

### 3.8 Identity judge

One call per pair: Luna when either side is a chat, Terra otherwise, medium effort. Each side
shows the nominated instance's text, then up to five instances already united with it (most
facts first) as context only, and "appears beside" as cast names when the arm includes the
cast. The judge sees texts and names, never a score. Verdicts: `same` or `different` with a
one-sentence reason about the two instances themselves. A difference in role or kind is not
evidence of different identity; a contradiction in identity is; a part, possession, place or
event of an entity is not the entity.

### 3.9 Document mentions

Titled documents' own nodes stay out of the clustering. After the clusters are complete, each
cluster is offered at most one document: by a member's name or naming alias equal to the title,
else by the member text nearest the document's abstract at DOCUMENT_FLOOR 0.85. The judge rules
with the document as the other side; a cluster ruled a mention becomes the document's children,
the document's node its anchor, the parent named by the title with kind `document`.

### 3.10 Global parents

Each finished cluster becomes one parent: name, kind, aliases, one summary line per instance,
the instance list. A singleton is copied from its child with no call. A cluster of two or more
gets one Luna call over up to twenty instances (most facts first) that picks a name an instance
carries (any other is refused), a kind, and one line per instance. The parent owns no claim; it
answers which source-local entities are one identity. Every child gets one `instance_of` edge.
Every candidate pair with its signals and verdict and every union in order go to `build.sqlite`.
Two invariants stop the run: every up-edge points at a written parent; every child has one.

### 3.11 Collections

Every parent held by two or more documents seeds a group of those documents; groups merge when
the smaller shares at least half its documents with the other; a document may belong to several.
One Luna call per collection names it and writes its abstract from the documents' abstracts and
the shared parents. An overlapping organisational layer, not a merge of the documents.

### 3.12 Wiki projection

Rendered from the serving store and nothing else; a human-readable projection of the
representation retrieval will use.

```
entity page        global parent -> source-local instance -> entity abstract -> ordered cells
                   -> adjudicated facts -> raw facts -> quotations
document page      metadata, abstract, ordered unit summaries, the document's entities
collection portal  abstract, documents, every entity the documents hold, ordered by the
                   documents holding it then by facts
collection figure  collections as hubs, documents as leaves
```

File names carry record ids, so two parents with one display name never collide.

### 3.13 Measured (the keyed test-store run)

```
about $2.40; about 2,700 judged pairs in about 30 rounds; 20 to 45 minutes
about 1,313 parents; about 80 unions
Tip and Ozma united; Toto and Billina apart; no chained cluster
15,758 vectors; 4 collections named by the call, "Oz series" among them
```

Calls per build: one judge call per pair reaching a round + one per cluster offered a document
+ one per parent of two or more + one per collection.

### 3.14 Global identity ablation

Nomination and the floor are fixed; the arm is what the judge sees. Two full builds: L+V+I (the
pair's texts alone) and L+V+I+C (the same plus the cast). A replay of one arm's verdicts under
the other is a fixed-verdict sensitivity check only, because a verdict was given with the
clusters as they stood. Attachment accuracy is scored against Wikipedia's list of Baum's Oz
characters (CC BY-SA 4.0), matched to children by alias, the hand-matched remainder counted.

## 4. Retrieval (PROPOSED): serving the stored representation

PROPOSED, ruled in design on 2026-09-15 and not built (`docs/retrieval.md` is the master). Its own pipeline; it reads `threadatlas.sqlite` and
`threadatlas.npy` and never returns to Step 0 or Step 1. It follows the structure the ingestor
built rather than flattening every stored text into interchangeable chunks:

```
document abstract -> entity abstract -> ordered narrative cells -> adjudicated claims -> raw facts -> quotes
source-local entity  <-  global parent  ->  the same entity's instance in another document
```

The parent supplies identity continuity; the documents supply the evidence.

```
SEARCH        hybrid lexical and vector entry inside the filter, fused by rank: where to enter
ROUTE         from the entry up to the representation above it (a fact to its cell and abstract)
              and across the tree (a child to its parent's other instances; the parent enters no
              pool)
TRAVERSE      a cell to the same entity's previous and next cell; an abstract to its cells in
              order; the entity's own trajectory, never the unit's neighbourhood
SUBSTANTIATE  a cell to that entity's facts in the unit, adjudicated first, raw with quotes
PACK          bundles, whole, by score, to the budget: a cell with its facts and quotes; an
              abstract alone; a fact alone when its cell is absent
ANSWER        the reader sees source-owned evidence only
```

The same operations from every entry; nothing branches on the question or the corpus. A chat's
session abstract has no cells, so its traverse is empty and its substantiate is the session's
facts; the parent still connects a chat entity to its instances elsewhere. The core ablation is
the same pipeline with the identity edges off and the parent rows masked from search: does
cross-document identity improve retrieval when the answer is still grounded in source-local
evidence? A miss divides in path order: the entity never found; the episode never reached; the
other document never reached; the evidence never recovered; cut by the budget; misread.

## 5. Current status

```
implemented   extractor; ingestor; global layer; the serving store; the vector sidecar; global
              parents; document mentions; collections; the wiki projection
designed      the retrieval pipeline
not built     the Wikipedia Oz key and scorer; the harnesses; the nightly path for new
              documents; a second partner search after a merge; supersession; parent refolding
              when children change
```

The system ends today with a serving representation that carries source-local provenance,
narrative structure, atomic evidence, document-local entity trajectories, cross-document
identity, collection structure, lexical search rows and vector representations. Retrieval is
meant to consume that structure directly rather than reconstruct it from flattened chunks.
