# Brief for the document ingestor chat (Step 1)

Paste this as the first message of a new chat. It is self-contained; the chat should read
the repository files it names before proposing anything.

---

You are helping me build one step of my IT 494 project, a memory backend for a desktop
assistant. This step is the **document ingestor**: one document at a time, from the
extractor's output to a document package. It is not the global merge; that is the step
after, and nothing here may reach across documents.

Read these before anything else, in this order, from
https://github.com/jhffmn82/it494-memory-project (local clone:
`C:\Users\jhffm\it494-memory-project`, branch `master`):

1. `SCHEMA.md`, the record contract. Ten record types. Read the whole file; you will be
   writing seven of them.
2. `BUILD.md`, the build rules: two model interfaces, the quote gate, re-runs mint nothing,
   summaries rebuild on a children hash, resolution guards.
3. `log/2026-09-05/README.md` and `log/2026-09-04/README.md`, the rulings behind both, and
   `log/2026-09-03/plan.md` section "Step 1".
4. `docs/entity-resolution.md`, whose guards are binding even though the merge is the next
   step: the per-document dossier this stage writes is what the merge will judge.

How I work: I implement; you draft and argue. One small change at a time, shown to me as a
diff I can read, and check with me before widening scope. Anything you propose that would
change SCHEMA.md or BUILD.md is marked PROPOSED until I rule. No background review loops, no
rewrites of working code. Simplest code possible: stdlib first, raw HTTP to the model, no
frameworks. I must be able to read and defend every line to my advisor. Never read
`C:\Users\jhffm\.kaggle\kaggle.json`; never read or upload my local assistant transcripts.

## What exists already, and what it is worth

- **The extractor** (`notebooks/factledger-extractor.py`, Kaggle `jhffmn/factledger-extractor`)
  is done. It writes `documents.jsonl` (doc_id, source_uri, sha256, title, author,
  source_class, text, ingested_at, occurred_at, loader, flags), `units.jsonl` (unit_id,
  doc_id, position, label, start, end, occurred_at, occurred_until), `pieces.jsonl` (doc_id,
  unit_id, position, kind, start, end, author, occurred_at) and a receipt. **Units are
  ranges, not text**: a unit's text is `document.text[start:end]`. The old ingestion notebook
  read `u["text"]` and must be changed.
- **The chapter-ingestion demo** (`log/2026-09-02/it494-chapter-ingestion-oz-book-1.ipynb`,
  Kaggle `jhffmn/it494-chapter-ingestion-oz-book-1`) is the working proof of the derive,
  reconciliation, predicate consolidation, cells, abstracts and graph over one book. Its real
  runs: v3 at $1.26 (632 local entities, 969 facts, 307 majors reconciled to 114) and v4 at
  $1.72 (644, 859, 357 to 141, with 70 majors seen in only one unit). **Start by revisiting
  it with me**, because it is the last thing that actually produced entities and facts and I
  want to keep what worked. Then rebuild; do not extend it. What it already got right: three
  cheap calls per unit (entities, facts, summary and cells), the quote gate, rolling a minor
  into its parent entity, bottom-up reconciliation with a judge and a ledger, predicate
  consolidation with fork flags in one call, abstracts spanning first unit to last. What it
  predates: the schema. It has no mention record, no piece table, no offsets on facts, no
  profile, no scope, no document-level salience, and its reconciliation is bottom-up inside
  one book rather than the document-package shape the merge now expects.

This stage is a rebuild against the schema, not a port.

## What the ingestor does

Input: one document from the extractor's three files. Output: one **document package**, JSONL,
which is the write-ahead log the merge replays. Per document, in unit order (`BUILD.md`:
ingest runs in corpus order, and the store's state after unit 10 differs from unit 20).

Per unit, in order:

1. **Entities.** The model names the entities the unit is about, with their surface forms.
   No hardcoded entity kinds and no per-corpus rules: the prompt must read as naturally over
   a chat session or a paper as over a novel.
2. **Mentions.** Every kept surface form gets a `mention` row with its character span **in
   document offsets**, its surface, and how it resolved. `node_id` is null for a minor
   entity; the mention still exists. Spans cannot be reconstructed later, so they are
   written from day one.
3. **Facts.** Subject, predicate, object, qualifiers, and a **verbatim quote that must appear
   in the unit**, with `quote_start` and `quote_end` as document offsets. A fact whose quote
   does not appear is dropped and logged, never stored. Normalize NFKC, curly quotes and case
   for matching only; the stored offsets index the original text. Rejections are classified
   (not found, paraphrase, normalization, unlisted subject) and counted.
4. **Profiles.** Low-confidence inferred attributes (gender, age band, animacy, role) go to
   `profile`, never to `fact`, because they have no quote and putting them in the fact table
   would make the quote gate a lie. Read by the matcher only.
5. **Cells.** A per-unit summary for each above-threshold entity, plus the unit's own summary
   as a cell on the document node. The previous unit's summary is passed as coreference
   context; a pronoun that still does not resolve stays recorded as unresolved.

Then, once per document:

6. **The document abstract**, folded from its cells: at most half the combined child word
   count, capped at 400 words, and every name it emits must appear in the child content by
   case-insensitive substring. A rejected fold is not stamped.
7. **Document-level salience, reassessed at the end**: an entity named in the document
   abstract is major, with unit count then fact count as tie-breakers. Only document-majors
   carry a dossier into the merge. Minors stay mentions inside the document: a fact from a
   major to a minor becomes a property of the major with the minor's name as its value, and a
   fact between two minors is not stored.
8. **A dossier per major**: the material the merge will judge, plus the embedding it will
   nominate candidates with.
9. **Per-entity abstracts** for majors, folded the same way, with `children_hash` so a rebuild
   happens only when the children change.

## The rules that bind this stage

- **Voice.** A fact's voice is the `author` of the piece holding its quote, else the
  document's `author`, else unknown. The piece table is already written; this is a lookup, not
  a model call. Never write a `speaker` field: the word is `author` at every level.
- **Time.** A fact's ordering time is its `valid_from` when the text states one, else its
  unit's `occurred_at`, else its document's `occurred_at`, else null. Never infer a date from
  prose and never fall back to ingestion time.
- **Ids are content hashes**, so a corrected split changes one id and not every id after it.
  Re-running over unchanged input mints zero new entities and rewrites zero accepted records;
  a stage that completes with zero yield writes an explicit empty-completion record so a
  resumed run can tell done-but-empty from failed.
- **Predicates.** `is_a` is the one reserved predicate and it is declared. There is no
  hardcoded core vocabulary: the predicate list is consolidated from what the corpus produced,
  with fork flags where one predicate is doing two jobs, as the demo did in one call. The
  type table (which subject and object kinds a predicate may join) is built from that
  consolidation, not written in advance. **Open question for me to rule: SCHEMA.md says
  "predicates come from a small controlled list with a table"; say how you read that against
  the no-hardcoded-vocabulary rule before you write any of it.**
- **Every model touch** goes through `generate(prompt, schema)` and `embed(texts)`, recording
  model id, tokens, latency and tier. Schema-invalid output gets one retry with the error
  appended, then a logged rejection. Semantic failure (a quote not in its unit) is rejected
  with no retry and counted separately.
- **Cost.** gpt-5.6-luna $0.20/$1.20 per million tokens in and out, gpt-5.6-terra $2/$12; a
  spending stop. Batch the cell calls: the demo measured 2.3x on total input and 5x on the
  dominant part against one call per entity.

## The test set: a variety of documents

Not one book. A sampling of every source type the extractor produces, run end to end, with
the differences between them reported:

| kind | sample | what it tests |
|---|---|---|
| Oz books 1 to 3 | 3 documents | the regression fixture; the demo's numbers to compare against |
| Holmes, two collections | 2 | many short stories in one document, a recurring cast |
| Greek, two works | 2 | translated names, a bilingual or OCR file, an anthology |
| GraphRAG-Bench, two texts | 2 | one-line files, sentence-addressed units |
| Papers, twenty | 20 | sections as units, the abstract as the first unit, `published` voice |
| LongMemEval sessions, a few hundred | ~300 | two voices inside one unit, dated units, the product's real case |

The paper path and the chat path are first-class, not afterthoughts: the paper path is where
the abstract ingestor gets locked down, and the chat path is what the product actually does.

## Acceptance

- Every fact's `quote_start`/`quote_end` slices out of the document text to exactly its
  quote, and every quote appears in its unit's range. Nothing else is stored.
- Every mention has a span; every minor mention has a null `node_id` and no node.
- The document package replays: re-running over unchanged input mints nothing and rewrites
  nothing.
- Cells exist for every above-threshold entity; the abstract's names all appear in its
  children; a stale abstract is exactly a `children_hash` mismatch.
- A chat unit's facts carry the voice of the turn they came from, demonstrated on a
  LongMemEval session where user and assistant say different things.
- Rejection counts by category, cost per document, and the unit-summary versus cells-set
  agreement check are in a receipt, the same shape as the extractor's.
- Oz book 1 re-derived from the new units, with its rejections classified by hand, at a cost
  within 20 percent of the demo's.

## Decide with me before writing code

1. The predicate question above.
2. The above-threshold rule for a unit cell: what makes an entity worth a cell in a unit,
   stated so it reads the same for a chat turn and a chapter.
3. Where the package is written and what one file per document looks like, given the merge
   replays it.

## The shape of tomorrow

1. Revisit the Oz chapter-1 ingestion with me: what it produced, what was good, what the
   schema now demands instead.
2. Rebuild against the schema, one block at a time, the way the extractor was built.
3. Test over the variety above, the paper and chat paths first-class, not one book.
4. Clean it up, so I can read and defend every line.
5. Produce an ingested set: the document packages the global merge will replay. That set is
   the deliverable, not the notebook.

Start by reading the files and the Oz demo, then tell me in one paragraph what you
understood, and put the three questions to me one at a time with your recommendation for
each. Limited prose.
