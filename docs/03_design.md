# The design

**2026-08-28.** What gets stored, how it gets built, how it gets read.

## Short version

Text comes in as an ordered run of chunks. For each chunk the system works out who or what is in
it, writes down dated facts with the quote that supports them, and writes a short narrative for each
important thing. Reading is mostly lookup by name, not similarity search.

**Nothing in the schema knows what a novel is.** Books, chat logs and PDFs all arrive the same way.

---

## 1. The shape of the store

Two views over the same text, and neither replaces the other.

- **By chunk.** One summary per chunk. Every chunk gets one.
- **By thing.** One short narrative per important entity, per chunk it appears in.

The first loses the individual thread: a character in twelve chapters is scattered across twelve
summaries, none of which is about them. The second loses the cause: Ozma's thread says she was Tip
and became ruler, not why.

The atom is the **cell**: one entity, one chunk. Chunk summaries are the rows, entity narratives are
the columns.

One chunk can belong to many entity threads at once. That is not novel; RAPTOR and CAM both do it.
It is just right for this store.

---

## 2. Schema

Seven records. Field names indicative.

```
Document  {doc_id, source_uri, sha256, ingested_at, occurred_at?, provenance}
Unit      {unit_id, doc_id, position, text, span, label?}
Node      {node_id, name, kind, created_from_unit, provenance}
Alias     {alias, node_id, first_seen_unit, evidence_quote}
Fact      {fact_id, subject, predicate, object, qualifiers,
           rank: preferred|normal|deprecated,
           unit_id, quote, valid_from, valid_to, tier, provenance}
Cell      {cell_id, node_id, unit_id, scope_id, text, tier, provenance}
Abstract  {node_id, scope_id, text, children_hash, tier, updated_at}
```

Plus instrumentation: `Rejection`, `Run`, `Consult`, and

```
Mention   {mention_id, node_id, unit_id, span, surface, resolved_by}
```

**`Mention` was previously a name with no fields.** It is the record every resolution measurement
reads: duplicate counting needs its node link, cluster purity needs the full set per node, and
coreference scoring against a gold benchmark needs `span`, a character offset into the source
document. Without the span, that class of test needs a full re-ingest to become possible, so it is
specified here rather than discovered later. `resolved_by` names the signal or merge that assigned
it.

**Deliberately generic, changed 2026-08-28.** An earlier version had `unit_type` as an enum of
literary forms (`chapter|book|play|ode|hui|session`) and two ordinals (`work_ordinal`,
`unit_ordinal`) so a character's thread could span volumes of a series. Both were chapter-parsing
concerns that had leaked into the data model.

- **A unit is a unit.** `position` is one integer, ordering units inside their document. Ordering
  documents inside a corpus is the corpus manifest's job. A series is just several documents in
  order; so is a year of chat sessions.
- **`label` is a free string with no meaning to the system.** Keep "chapter" or "session" in it if
  it helps a human read the data. Nothing branches on it.
- **`scope_id`** replaces `corpus_id` on cells and abstracts. Same idea, no assumption about what a
  corpus is: it is whatever set you want salience scoped to.

**What "later" means, settled 2026-08-28.** Supersession handles *the world changed*: a later fact
collides with an earlier one. The ordering key is **`occurred_at` when both facts have one, and
otherwise the pair (document order in the corpus manifest, unit position within that document).**
Position always exists; a date often does not, and leaving it unknown is correct rather than
guessing at it. Feed a series in sequence, book 1 then book 2, and the manifest records that order.

**Both halves of that pair are required.** Tip becomes Ozma across two books, and unit position alone
gets it right only by accident: book 2 unit 47 outranks book 1 unit 3 numerically. Move the reveal to
unit 3 of book 2 and position alone reverses it. This makes the corpus manifest load-bearing for
correctness rather than a convenience for reading order.

This ordering is not a detail. Order by date alone and the novel corpus supersedes nothing at all,
because almost no fact in a novel carries one, and the Tip fixture would pass while doing nothing.
Order by position alone and backfilling an old chat session after a newer one silently reverses the
truth. So: dates win where both sides have them, position carries everything else.

**Why the rest is there.** `rank` covers the case supersession cannot, namely *we were wrong*, where
there is no later event and deleting would break append-only. `qualifiers` carry
role and timing so nobody invents a new predicate for "as Chancellor". `children_hash` says exactly
when an abstract is stale, so refolding touches only what changed.

Predicates come from a small controlled list, with a table of which subject and object kinds each
one may join. That catches the error a quote cannot: a made-up relationship can carry a perfectly
real quote.

---

## 3. Getting text in

### Two seams, and dataset code lives only at them

Six datasets have to go through this: GraphRAG-Bench novels, LongMemEval chat sessions, BookCoref
books with gold clusters, a hand-labelled alias set, the personal archive, and whatever comes next.
They stay cheap to add only if nothing dataset-shaped reaches the middle of the system.

```
loader  ->  Documents + Units  ->  [ the system ]  ->  store  ->  evaluator
```

- **A loader** turns one source into documents and units and nothing else. It may fill `occurred_at`
  and `label`. It may not add fields, and the system may not branch on which loader ran.
- **An evaluator** reads the finished store and computes one metric. It never reaches into the
  pipeline, so a new metric is a new reader, not a change to ingest.

Adding a dataset is then one loader plus one evaluator. Anything that cannot be expressed that way is
a signal the schema is missing a field, which is how `occurred_at` and `Mention.span` were found.

**Homogenise the ingest side, and nothing else.** Every loader emits the same two tables,
`documents` and `units`, because the system must not be able to tell which dataset it is reading.
That is the entire contract.

Gold files, question files and harnesses are **not** standardised. Each dataset keeps whatever shape
it already ships in: BookCoref stays in its HuggingFace format, GraphRAG-Bench's questions stay JSON,
the alias set is whatever is convenient to write by hand. Each evaluator is dataset-specific by
definition, so converting them all to a shared layout is work that buys nothing and produces mostly
null columns.

Not even the join needs a format. A loader already knows which source it read and which `doc_id` it
minted, so it returns that mapping and the evaluator uses it in memory.

Open, and a loader decision rather than a schema one: **what counts as a document in LongMemEval**, a
single session or the whole haystack behind one question. It sets what `doc_id` means there and
therefore what its gold file joins to, so it gets decided before that loader is written.

**Stage 0. Split.** Raw text to ordered units. How boundaries are found is a preprocessing problem
and stays out of the schema. See `04_unit_contract.md`.

**Ingest in order, never in bulk.** A book loaded all at once is static and tests nothing temporal.
Read in sequence and the store's state after chunk 10 differs from chunk 20, which is what
supersession is for.

**Stage 1. Who is in this chunk.** One call, returns the cast. Passing that cast into every later
call for the chunk stops the same character being minted three times as "Tip", "the boy" and
"Tippetarius".

**Stage 2. Match the cast against what you already know.** This is the step the prototype failed at
scale. Once the name list outgrows a prompt it becomes retrieval-then-prompt: embed the mention,
pull the nearest few known names, decide among those. Topics are harder than people, because a
person has a name and a topic has whatever the speaker called it that day.

**Stage 3. Facts.** Dated subject-predicate-object rows, each with a verbatim quote and a pointer to
its unit. Rejections logged. Dedup must come first or facts attach to duplicates.

**Stage 4. Cells.** One per above-threshold entity per chunk. This is where the money goes, so emit
all of a chunk's cells in one call rather than re-sending the chunk text once per entity.

**Stage 5. Refold.** An abstract is a fold over its cells, so recompute only entities whose cells
changed.

**The threshold.** Everything gets facts. Only important things get narratives. So a search never
comes back empty (the one-paragraph abstract is the floor) and nothing is lost when something falls
below the line, because the chunk summary still recorded it. Importance is scoped to the set, not
baked into the entity: a character can be major in one corpus and a footnote in another.

**Free consistency check.** Chunk summaries and entity cells are independent summaries of identical
text. If a chunk summary mentions an event no cell does, either it was invented or stage 1 missed
someone. Set comparison, no judge, no ground truth.

**Where to spend the expensive model.** Not "more abstraction, better model." **Spend where errors
spread, economise where they are recoverable.** A mediocre summary costs one call to redo. A
corrupted name registry costs a full re-ingest. So coreference and alias resolution get the good
model; cell generation, which dominates volume, does not.

---

## 4. Getting text out

**Most reads are lookups, not searches.** Standard RAG embeds the question and finds similar text.
Here the store is indexed by entity, so the first job is "which entity is this about". Embeddings do
that matching; they do not fetch the content. The name index is a few thousand short strings, not
millions of chunks.

| Question | Path |
|---|---|
| Who is X | the abstract |
| What happened to X | the cell sequence |
| What happened in chunk 5 | the chunk summary |
| Where do X and Y meet | intersect their cells' unit ids |
| Exact name or phrase | full-text search |
| Nothing matches a known entity | full-text fallback, which must be good, not vestigial |

**Two honest weaknesses.** The whole path depends on resolving the question to an entity; "the boy
who became a princess" names nothing, and then you are on the fallback. And what gets ranked is
generated text, not source text, though every piece of it points back to its chunk.

**Drilling down and the anti-fabrication check are the same mechanism.** Follow a quote to its unit
and see if it lands. Doing that for one claim is a drill-down; doing it for all of them is the gate.
A failed match means either the quote was invented or the splitter moved.

---

## 5. Where it runs

**One backend: files.** JSONL as the record of truth, a numpy array for embeddings, SQLite full-text
search. No server. Human-readable, git-diffable, and the two indexes are disposable because they
rebuild.

Exact search over the whole embedding array is fine here on latency grounds: 20,000 vectors at 768
dimensions is about 61 MB and one matrix multiply per query. Faiss's own paper puts the point where
you *start* wanting an approximate index at around 10k vectors, so this sits just above that
threshold rather than far below it, and buys exact recall with no index to keep in sync.

**Neo4j and Graphiti are not being built this semester.** Beyond the hours, Graphiti cannot satisfy
two of the invariants below: `add_triplet` runs its own entity resolution, so a supplied entity may
be silently merged, and it creates no episode node, so nothing carries quote provenance. The arms
would have differed in meaning, not just storage.

**Keep the storage port anyway.** Seventeen operations, nothing calls a backend directly. It costs
almost nothing now and makes a second backend cheap later.

```
put_document / get_document        put_fact / get_facts(subject, as_of)
put_unit / get_unit / get_units    put_cell / get_cells(node_id, scope_id)
put_node / get_node                put_abstract / get_abstract
resolve_alias(text)                search_text(query, scope, k)
nearest_nodes(vector, k)           log_consult(record)
```

**Reaching a desktop client is MCP:** a Python server over stdio, where the tool list is the
capability contract.

**Not adopted:** LangChain and LlamaIndex, because they take ownership of chunking, retrieval and
prompting, which is exactly the surface that has to be defended here.

---

## 6. Invariants

1. Raw text is never edited. Ids are content hashes.
2. Nothing is overwritten. Supersession and merges resolve at read time.
3. Every assertion carries a verbatim quote that must appear in its unit.
4. Every model call goes through `embed()` and `generate()` and records its tier.
5. Every contract rejection is logged.
6. An abstract is a fold over its cells; staleness is a hash comparison, never a guess.
7. A relationship that violates the type table is a rejection, not a stored row.

---

## 7. Open

- **Two clocks, partly settled 2026-08-28.** Books order by narrative position, chats by wall clock.
  `Document.occurred_at` now carries source time and is nullable: a chat log fills it from the
  session date, a published work from its publication date, a novel with neither leaves it null and
  orders by `position`.

  **It has exactly one meaning: when the source was produced.** Not when the story is set. In-story
  time is `Fact.valid_from` and `valid_to`, which is where it has to live, because it is not constant
  within a document: a novel spans years, a flashback runs backward, and "Tip is a boy" stops holding
  partway through book 2. Letting one field mean either would make a temporal query's answer depend
  silently on which loader ran. The fixtures already separate the two: Homer against Euripides on
  Helen is two sources disagreeing, which is `occurred_at`; Tip becoming Ozma is the world changing,
  which is `valid_from`. `ingested_at` stays what it was, the day
  the system read the file, which is not the day the conversation happened. Without this a batch
  ingest flattens a year of chat into one timestamp and every temporal question becomes
  unanswerable. **Still open:** what a single defined order means for a store holding both at once.
  Nothing forces that question until a corpus mixes them, so it waits for one that does.
- **No export gate exists, and the personal archive needs one before it can ever be an input.**
  The eventual goal is to re-ingest the archive under this system (Justin, 2026-08-28, parked, not
  this fall). That archive carries quarantine semantics this schema has no concept of: whole eras are
  local-only and never pushed, one user's sessions are walled out of another's, and a holds ledger
  tracks what must not travel. `provenance` and read-time permissions do not cover it. Quarantine is
  an **export** gate, "readable here, never leaves the machine", and the current nightly auto-pushes
  cleared content to a remote, so a system lacking that concept would push protected material the
  first time it ran. Design it before the archive is ever loaded, not during the migration.
- **Nothing ever demotes.** Promotion is one-way, and the prototype accumulated 82 orphaned records
  from exactly this.
- **No conformance test across adapters yet.** Only one adapter exists, so write the suite against
  it; that is what stops a second one rotting later.
- **Embeddings can silently desync from the entity table.** The numpy array and the node list are
  written separately with no checksum tying them, so a partial write returns the wrong entity and
  nothing complains. Store a row count and a hash of the id ordering, and verify on load.
- **Full-text search is assumed, not checked.** SQLite is not always compiled with FTS5. Probe at
  startup and fall back, or the distributable fails on a stranger's machine.
