# The extractor: algorithm and data contract

`threadatlas-extractor 1.8`. One Kaggle notebook that turns a folder of raw files into a split
plan: which document each file is, where it divides, what kind of text each part is, and from
when. No entities, no facts, no summaries; those are the ingestor's job (Step 1). This is Step 0.

The field-level schema of the output lives in [`dataset/step0/SCHEMA.md`](../dataset/step0/SCHEMA.md);
the method as published in [`dataset/step0/METHOD.md`](../dataset/step0/METHOD.md); the measured
limits in [`dataset/step0/LIMITS.md`](../dataset/step0/LIMITS.md). This file is the consolidated
narrative: the algorithm, and the input/output contract, in one place.

## The one rule

**The extractor sees a raw file and nothing else.** The format is sniffed from the bytes: no
filename convention, no per-corpus branch, no hand-written rule about where a publisher's
boilerplate ends. Every boundary in the output is a decision the model made and code verified;
code never decides where a break may go, and the model never returns a character offset. The
manifests are packaging and an answer key, read once in block 1 to prove the mounted bytes are
the uploaded bytes, and never again.

## Input

One mount, the public raw dataset `jhffmn/it494-narrative-corpora-raw` (version 4), one folder
per corpus, each with a `manifest.json` recording every file's source URL, byte count and sha256:

| corpus | files | what it is |
|---|---|---|
| `longmemeval` | 19,206 session files plus `longmemeval_s.json` | block 0 unpacks the benchmark file into 25,112 session files in 500 history folders under `/kaggle/temp/chats`, every turn timestamped; the extractor reads those, not the 19,206 |
| `kg-rag-cc` | 100 | CC-BY papers on knowledge graphs and RAG, PDFs under `pdf/` |
| `greek` | 31 | Greek and Roman literature, including OCR'd institutional scans |
| `oz` | 29 | the Oz books |
| `graphrag-bench` | 20 | GraphRAG-Bench novel contexts |
| `holmes` | 9 | the Sherlock Holmes volumes |

LongMemEval ships as one file of 500 questions, each with its own history of dated sessions.
Block 0 unpacks `longmemeval_s.json` into the shape a chat archive has: one folder per history,
`chats/longmemeval/<question_id>/<session_id>.json`, every turn carrying that history's timestamp
for the session. A session used by several histories is written once in each, with each history's
date; a history that lists one session twice gets `<session_id>.2.json`. No question, answer,
answer sessions or evidence marks are written. Empty sessions are written; the extractor skips them.

Three shapes are sniffed from the first bytes, and nothing else about a file is consulted:

| sniffed as | how it is read |
|---|---|
| PDF | the text layer, pages joined by one newline (PyMuPDF, the one dependency) |
| chat JSON | one block per turn that says something: a `SESSION <id> TURN <n> <time>` line, then `role: content`; turn spans and times kept |
| plain text | the bytes decoded as UTF-8, unchanged |

## Algorithm for a document that must be read

### 1. The address list

A document is shown to the model as its own non-blank lines, numbered. The model points at a line
**by number and copies the line's text**, so the number is verified against the text and, when it
is off by a few, recovered from the copy. A file with no usable lines (a PDF text layer that puts
one word on a line) is numbered by sentence instead. A boundary exists only where the model
pointed and the copy checks out.

### 2. One call per document

The whole document in one `gpt-5.6-luna` call (low reasoning effort), asking for:

- `source_class`, `title`, `author`, `source`: each a pointer plus the value as it should read.
- `works`: every separate work the document holds, each at the line where it begins, with the
  line stating when it was written.
- `toc_count`: how many pieces the contents list promises, to count the answer against.
- `regions`: where front matter ends, where body begins, and where notes, references, appendix
  and license sit. These become the `kind` of each piece; they are labels, not cuts.
- `pieces`: the chapters, sections and scenes.

On a flag the same model is asked once more; a document that defeats Luna twice is asked once
more on `gpt-5.6-terra` (ten times the price) when it fits in `RETRY_MAX_TOKENS` (80,000). The
answer kept has a body region and the fewest flags. Six of the 189 read documents escalated.

### 3. The gates

- **Pointer gate.** A pointer resolves only when the copied text names the line: the line itself,
  its first eight words, a run of five or more of its words, or a two-line heading copied whole.
  Five words keeps a short heading strict, so `CHAPTER I` cannot answer for `CHAPTER II`. Wrong
  number but text found nearby: recovered and counted. Text nowhere: dropped and counted.
- **Metadata pointers.** Title, author, source and each work's date go through the same check,
  loosened to a substring of the line for a title, author or date, which are a few words inside
  a longer line; a date's year must appear on its line. A failure is nulled and flagged, never
  retried.
- **Tiling.** Pieces cover the document with no gaps and no overlaps; the export asserts every
  unit's slice is non-empty before writing.

Nothing the model asserted without a verified pointer reaches the output. A failed shape gate (no
body region, a piece count disagreeing with the contents, one piece holding most of the body) is
a flag, never a drop.

### 4. Dating

Every piece takes the date of the work it lies in, and a document takes its earliest unit's date.
A work is dated by when it was written, or first published when that is all a source gives, never
a translation, an edition, a transcription or an ebook release. The date comes from the page when
the model pointed at a line stating it and the year is on that line; otherwise one Responses API
call on Luna with OpenAI's web search tool looks the work up by title and author, answering with
the date and the URL it came from (Flex tier, falling back to standard when Flex is refused). In
1.8, 156 of the 405 works were dated from the page, 237 by search, and 12 got none. Every date's
source is written into the document's flags, as `date: <work>: <value> from <the page or the
URL>`, or `date: <work>: none, <why>`.

### 5. Three calls that decide units, none that measure

1. **Sub-split.** A piece over `CAP_WORDS` (4,000) goes back as numbered lines and is cut at the
   breaks the model points at, up to three rounds. One it cannot break stays whole and is flagged.
2. **Merge short.** A piece under `SHORT_WORDS` (100) is offered with its text: it joins the piece
   before, the piece after, or stands alone.
3. **Group.** The outline (every piece with its kind, word count and heading) goes back and the
   model groups consecutive pieces into units: a section with its subsections, never two peers
   merely because they fit. Code then checks the groups cover the outline in order, dissolves a
   group over the cap, and cuts any group where the kind or the date changes.

## Algorithm for a chat session

No call. A session already states its own boundaries. Each turn that says something is one piece
and one unit, labelled by the line that opens it, `SESSION <id> TURN <n> <time>`, with the role as
its author and its kind (`user` or `assistant`) and its own timestamp as its time; the document
takes the earliest. An empty session and a turn that says nothing are skipped and counted in the
receipt (1,230 sessions and 70 turns in 1.8), so a session's turn numbers can have gaps. A chat's
title is its session id, its author is null, and its `source_class` is `record`.

## The date forms

`occurred_at` is the only date field, on documents, units and pieces: `YYYY`, `YYYY-MM` or
`YYYY-MM-DD`; a chat turn's timestamp `YYYY-MM-DDThh:mm:ss`; a year before the common era as a
signed year counting a year zero, so 405 BC is `-0404`; a trailing `~` for an approximate date;
and a range as its two ends joined by `/`, as in `-0749/-0724`. No row carries a range field; sort
by the first year read as a signed integer.

## Running it

Every model call runs on OpenAI's Flex tier at half the standard price, priced by the tier that
served it. Six documents run in parallel (`DOCUMENTS`), a document's over-cap pieces sub-split
eight at a time (`FANOUT`); each call is billed to the document that made it. A hard spending stop
(`SPEND_STOP`, $25) halts the run; running out of API credit is fatal by design, so a dead key
cannot walk the corpus writing empty flagged records. Finished documents are appended to
`/kaggle/working/splits.jsonl` and skipped when block 8 is run again in the same session; a new
session asks every document again. `REDO_ALL` re-asks clean records an older loader wrote.

## Output

Four JSON Lines files plus a receipt, in `export/`. All offsets everywhere are **document
offsets**: character indices into `documents.text` for the same `doc_id`, one coordinate system,
so any piece, unit or later fact quote resolves with a single slice. Read the files as UTF-8
without normalising.

| file | rows (1.8) | one row is |
|---|---|---|
| `documents.jsonl` | 24,071 | a document: `doc_id` (sha256 of the bytes), `source_uri`, `sha256`, `title`, `author`, `source_class`, `text` (the whole decoded string, never null), `ingested_at`, `occurred_at`, `loader`, `flags` |
| `units.jsonl` | 251,446 | a unit: `unit_id`, `doc_id`, `position` (0-based, dense), `label`, `start`/`end`, `occurred_at` |
| `pieces.jsonl` | 252,830 | a piece: `doc_id`, `unit_id`, `position`, `kind`, `start`/`end`, `author`, `occurred_at` |
| `attribution.jsonl` | 100 | a CC-BY paper's authors, title, year, venue, DOI, OpenAlex id, license and source URL, joined on `doc_id` |
| `receipt.json` | | the run's own counts and cost, written by the run |

The 24,071 documents are 23,882 chats in 500 histories and 189 books and papers (89 texts, 100
PDFs). The pass cost $8.24, a median of $0.0081 a read document with its date lookups, and nothing
for the chats. `kind` is one of eight values: six regions of a written document (`front_matter`,
`body`, `notes`, `references`, `appendix`, `license`) and two turns of a conversation (`user`,
`assistant`). `source_class` is `record` for a chat, `published` for a PDF, and the model's answer
for plain text. A book or paper piece has `author` null; the document's author stands.

Guarantees verified on all 24,071 documents at export, not asserted:

- **Units and pieces each tile their document.** Sorted by position, the first starts at 0, the
  last ends at `len(text)`, each start equals the previous end.
- **A unit never mixes kinds or dates.** It is all body, or all references, or all appendix, and
  all from one date. In a chat, piece and unit coincide.
- **`unit_id` is unique**, every unit's slice is non-empty, and every piece points at a unit of its
  own document.

## What it does not claim

It is not ground truth: there is no gold segmentation and no gold date table. What is verified is
internal (tiling, ids, kind and date purity, and that every boundary's pointer matched real text).
Labels are the model's words, not a controlled vocabulary. A rerun differs on hard documents and
in some looked-up dates, because neither the model nor the web search is deterministic; two runs
are compared by their receipts. Known wrong dates: the Plays of Sophocles carry `1912`, the
translation's year, from a line the model pointed at; three articles of a Scientific American
Supplement were dated by a search that matched the wrong publication. 15 units in 12 works carry
no date, each explained in its document's flags; no document is undated. The full measured limits
(103 of 189 read documents flagged, 135 mismatched pointers of which 50 were dropped, coverage of
the body) are in [`dataset/step0/LIMITS.md`](../dataset/step0/LIMITS.md).

## Where the ingestor picks up

The ingestor (Step 1, [`docs/ingestor.md`](ingestor.md)) reads `documents.jsonl`, `units.jsonl`
and `pieces.jsonl`, ingests one document at a time, and writes one package per document: entities,
quote-backed facts at document offsets, cells, an abstract, and an abstract per major. A chat is
read in one call over its turns, each fact tied to the turn its quote is found in.
