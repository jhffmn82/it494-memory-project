# The extractor: algorithm and data contract

`factledger-extractor 1.5`. One Kaggle notebook that turns a folder of raw files into a split
plan: which document each file is, where it divides, and what kind of text each part is. No
entities, no facts, no summaries — those are the ingestor's job (Step 1). This is Step 0.

The field-level schema of the output lives in [`dataset/step0/SCHEMA.md`](../dataset/step0/SCHEMA.md);
the method as published in [`dataset/step0/METHOD.md`](../dataset/step0/METHOD.md); the measured
limits in [`dataset/step0/LIMITS.md`](../dataset/step0/LIMITS.md). This file is the consolidated
narrative: the algorithm, and the input/output contract, in one place.

## The one rule

**The extractor sees a raw file and nothing else.** The format is sniffed from the bytes — no
filename convention, no per-corpus branch, no hand-written rule about where Gutenberg boilerplate
ends. Every boundary in the output is a decision the model made and code verified; code never
decides where a break may go, and the model never returns a character offset.

## Input

A directory of raw files with a manifest per corpus (`data/raw/<corpus>/manifest.json`), each
recording per work its source URL, byte count, and sha256. The manifest is packaging and an
answer key; it is never read by the extractor. Three shapes are sniffed from the bytes:

| Sniffed as | Source in this release | How it is read |
|---|---|---|
| plain text | Gutenberg `.txt` (Oz, Holmes, Greek), GraphRAG-Bench novels | decoded to a string, verbatim |
| chat JSON | LongMemEval sessions, one JSON per session | rendered `role: content`, turn spans kept |
| PDF | the 141 reference papers (a private dataset, license-withheld) | PyMuPDF text layer, pages joined by one newline |

The PDF path matters downstream: because the papers cannot be public, their text is **recreated**
from the PDF (`pymupdf.open(...).get_text()`, pages joined by `\n`) exactly as the extractor read
it, so the same character offsets resolve against the rebuilt string. The published dataset ships
those documents with `text: null` and a `papers.jsonl` row (PDF sha256 + URL) to rebuild them.

## Algorithm

### 1. The address list

A document is shown to the model as its own non-blank lines, numbered. The model points at a line
**by number and copies the line's text**, so the number is verified against the text and, when it
is off by a few, recovered from the copy. A file with no usable lines — a PDF text layer that
puts one word per line — is numbered by sentence instead. This is the whole trick: a boundary
exists only where the model pointed *and* the copy checks out.

### 2. One call per document

The whole document in one `gpt-5.6-luna` call (low reasoning effort, JSON mode), asking for:

- `source_class`, `title`, `author`, `source`, `date` — each a pointer plus the value as it
  should read.
- `toc_count` — how many pieces the table of contents promises, to count the answer against.
- `regions` — where front matter ends, where body begins, and where notes, references, appendix,
  and license sit. These become the `kind` of each piece; they are labels, not cuts, so every
  byte stays in the document.
- `pieces` — the chapters, sections, and scenes.

A document that defeats Luna twice is asked once more on `gpt-5.6-terra` (ten times the price) when
it fits in 80,000 tokens. Two of the 230 read documents escalated. Dates are never inferred: a
year is kept only if it appears on the line the model read it from, a month or day only if the
line names the month; the transcriber's date and the ebook release date are excluded by the
prompt (52 documents carry no date as a result).

### 3. Three calls that decide units, none that measure

1. **Sub-split** — a piece over `CAP_WORDS` (4,000) is shown again as numbered lines; the model
   points at the natural breaks inside it, up to three rounds. A piece it cannot break stays
   whole and is flagged.
2. **Merge short** — every piece under 100 words is offered with its text; the model says it
   joins the piece before, the piece after, or stands alone.
3. **Group** — the outline (every piece with its kind, word count, heading) goes back and the
   model groups consecutive pieces into units: a section with its subsections, a chapter with its
   scenes, never two peers merely because they fit. Code then checks the groups cover the outline
   in order, dissolves a group over the cap, and cuts any group where the kind changes, so a unit
   is all one kind.

### 4. Chats are grouped by code, with no model call

A session already states its own boundaries. Its turns are the pieces, the role is the author.
Units are runs of turns under the cap, never a lone turn, never spanning a change of day, with a
short tail (under `TAIL_FLOOR`, 1,333 words) merged back into the unit before it. The session
header is front matter and a unit of its own. The day rule is in the code for chat formats that
date each turn; LongMemEval dates a session, not a turn, so on this corpus the rule never fires
and every turn carries the session's start date.

### 5. The gates — every answer checked before it becomes data

- **Pointer gate.** A pointer resolves only when the copied text names the line: the line itself,
  its first eight words, a run of five or more of its words, or a two-line heading copied whole.
  Five words keeps a short heading strict, so `CHAPTER I` cannot answer for `CHAPTER II`. Wrong
  number but text found nearby → recovered and counted; text nowhere → dropped and counted.
- **Tiling.** Pieces cover the document with no gaps and no overlaps; the export asserts every
  unit's slice is non-empty before writing.
- **Metadata pointers** are checked loosely, as a substring of the pointed line or its neighbours,
  because a title/author/date is one to four words and the five-word rule would reject them all. A
  failure is nulled and flagged, never retried (a retry costs a whole document call and the field
  is already null).

Nothing the model asserted without a verifiable pointer reaches the output. Where a check fails,
the row carries a flag rather than a guess.

### 6. Running it

`gpt-5.6-luna` throughout, six documents in parallel, a document's own over-cap pieces sub-split
eight at a time. Each call is billed to the document that made it, so per-document cost is real.
A hard spending stop (`$25`) halts the run; running out of API credit is fatal by design, so a
dead key cannot walk the corpus writing empty flagged records. Resumable: finished documents are
appended and skipped on restart; `REDO_ALL` re-exports everything under the current loader version
(this release was produced with it on, so every row is 1.5). One pass over 19,437 files → 19,436
documents for **$7.72**.

## Output

Four JSON Lines files plus a receipt. All offsets everywhere are **document offsets** — character
indices into `documents.text` for the same `doc_id`, one coordinate system, so any piece, unit, or
(later) fact quote resolves with a single slice. Read the files as UTF-8 without normalising.

| file | rows (1.5) | one row is |
|---|---|---|
| `documents.jsonl` | 19,436 | a document: `doc_id` (sha256 of the bytes), `source_uri`, `sha256`, `title`, `author`, `source_class`, `text` (the decoded string, `null` for the 141 papers), `ingested_at`, `occurred_at`, `loader`, `flags` |
| `units.jsonl` | 44,262 | a unit: `unit_id`, `doc_id`, `position` (0-based, dense), `label`, `start`/`end` (char range), `occurred_at`/`occurred_until` |
| `pieces.jsonl` | 227,100 | a piece: `doc_id`, `unit_id`, `position`, `kind`, `start`/`end`, `author`, `occurred_at` |
| `papers.jsonl` | 141 | a withheld document's rebuild key: `doc_id`, `file`, `pdf_sha256`, `bytes`, `source_url`, `title`, `author` |
| `receipt.json` | — | the run's own counts and cost, written by the run |

`kind` is one of eight values in two families: six regions of a written document (`front_matter`,
`body`, `notes`, `references`, `appendix`, `license`) and two turns of a conversation (`user`,
`assistant`). `source_class` is fixed by format for two of three — a chat is `record`, a PDF is
`published` — and the model's answer for plain text (`canonical` for the literature).

Guarantees verified on all 19,436 documents (not asserted — checked at export):

- **Units and pieces each tile their document.** Sorted by position, the first starts at 0, the
  last ends at `len(text)`, each start equals the previous end. No gaps, no overlaps, nothing
  dropped or double-counted.
- **A unit never mixes kinds.** It is all body, or all references, or all appendix — never running
  from the end of a chapter into the footnotes.
- **`unit_id` is unique**, and every piece points at a unit of its own document.

## What it does not claim

It is not ground truth — there is no gold segmentation to score against; what is verified is
internal (tiling, ids, kind purity, and that every boundary's pointer matched real text). Labels
are the model's words, not a controlled vocabulary. A rerun differs on hard documents because the
model is not deterministic; two runs are compared by their receipts. The paper rows have no text
until rebuilt from the source PDF. Full measured limits (the 72 real flags, the 79 dropped
pointers and why, coverage, the null dates) are in [`dataset/step0/LIMITS.md`](../dataset/step0/LIMITS.md).

## Where the ingestor picks up

The ingestor (Step 1) reads `documents.jsonl`, `units.jsonl`, and `pieces.jsonl`, ingests one
document at a time, and writes one package per document — entities, quote-backed facts located at
document offsets, cells, an abstract, and a dossier per major entity. Its algorithm and package
schema get their own summary once the algorithm is finalised. The raw-text-vs-offsets question and
dropping the redundant fact `quote` string are settled to belong at the SQL-import step (Step 2),
not here.
