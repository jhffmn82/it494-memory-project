# Schema

Four JSON Lines files and a receipt. One JSON object per line, UTF-8, newline separated.

Character offsets are indices into `documents.text` for the same `doc_id`, as Python string
indices over the decoded UTF-8 text. Read the file without normalising newlines or whitespace
and `text[start:end]` is the piece or unit exactly.

## documents.jsonl

One row per distinct document. Two source files with identical bytes are one document; the
receipt's `duplicate_files` names the file that was dropped and the one it matched.

| field | type | meaning |
|---|---|---|
| `doc_id` | string | sha256 of the document's bytes, hex. The join key everywhere else. |
| `source_uri` | string | dataset and path of the file it was read from. |
| `sha256` | string | the same hash again, as the schema names it separately from the id. |
| `title` | string or null | the source's own name for the document: read off the page for a book or a paper, and the session id for a chat, which is the only name a session file carries. Never a filename. Null when the source gives no name at all. |
| `author` | string or null | the person who wrote it. A publication only when no person is named, and then flagged. |
| `source_class` | string or null | `canonical`, `published`, `record`, `authored` or `tool-output`. |
| `text` | string | the document as text. **Never null in this release**; every document carries its own. |
| `ingested_at` | string | when this run read the file, ISO 8601 UTC. |
| `occurred_at` | string or null | when the document is from, as a year, a year and month, or a full date. Null when the page does not say. For a chat, the session's date when it has exactly one, else null. |
| `loader` | string | the extractor version that wrote the row. `threadatlas-extractor 1.7` throughout. |
| `flags` | array of string | what the run could not settle. Empty when nothing. See `LIMITS.md`. |

`source_class` is fixed by kind for two of the three: a chat log is a `record` and a PDF is
`published`. A plain text document takes the model's answer, which is `canonical` for the
literature.

## units.jsonl

The split plan. A unit is a run of consecutive pieces, cut only at piece boundaries. A chat unit
is exactly one turn.

| field | type | meaning |
|---|---|---|
| `unit_id` | string | sha256 of the document id, how many identical slices came before it, and the slice. |
| `doc_id` | string | the document. |
| `position` | integer | 0-based, dense, in document order. |
| `label` | string | for a book or paper, the heading or opening the model named for this unit; for a chat, the line that opens the turn, `SESSION <id> TURN <n> <date>`, the date only when the session has exactly one. Not unique, not a key. |
| `start`, `end` | integer | character range into `documents.text`. |
| `occurred_at` | string or null | when the unit is from: the document's date for a book or paper; for a chat, the session's date when it has exactly one, else null. |

Guarantees, verified on all 19,395 documents in this release:

- Units of one document tile it. Sorted by position, the first starts at 0, the last ends at the
  length of the text, and each start equals the previous end.
- Every unit's slice is non-empty after stripping whitespace.
- `unit_id` is unique across the file, and all 204,126 recompute from the document's own text.

## pieces.jsonl

What each stretch of a document is, and, where the file names one, who is speaking there. This
is where a fact's voice comes from; when a piece names no speaker, the voice is the document's
`author`.

| field | type | meaning |
|---|---|---|
| `doc_id` | string | the document. |
| `unit_id` | string | the unit that contains this piece. Always a unit of the same document. |
| `position` | integer | 0-based, dense, in document order. |
| `kind` | string | `front_matter`, `body`, `notes`, `references`, `appendix`, `license`, `user` or `assistant`. |
| `start`, `end` | integer | character range into `documents.text`. |
| `author` | string or null | the speaker, when the file names one: `user` or `assistant` on a chat turn. Null on every piece of a book or paper; the document's `author` stands there. |
| `occurred_at` | string or null | when this piece is from. A chat turn carries its session's date when the session has exactly one, else null; the source gives no per-turn time. Null on every piece of a book or paper, whose date is on the document and its units. |

Guarantees, verified on all 19,395 documents:

- Pieces of one document tile it, the same way units do.
- Every piece points at a unit that exists and belongs to the same document.
- **No unit mixes kinds.** A unit is all body, or all references, or all appendix. It never runs
  from the end of a chapter into the footnotes.

In a chat, piece and unit coincide: each turn is one piece and one unit, with one speaker.
199,641 of the 204,126 units are chat turns.

The eight kinds are two families. Six are regions of a written document. The other two are turns
of a conversation, and appear only in the LongMemEval sessions.

## attribution.jsonl

The 100 CC-BY papers, and what their license asks of anyone who redistributes them. Not a
rebuild key: every paper's text is already in `documents.jsonl`.

| field | type | meaning |
|---|---|---|
| `doc_id` | string | joins to the document row. It is the sha256 of the PDF's bytes, so it equals `pdf_sha256`. |
| `source_uri` | string | the same path the document row carries. |
| `title` | string | the paper's title as its publisher records it, not as the extractor read it. |
| `authors` | array of string | every author, in order, up to twelve. |
| `year`, `venue` | integer or null, string or null | publication year and venue, when OpenAlex records them. |
| `doi`, `openalex_id` | string or null | the two stable identifiers. |
| `license` | string | the exact license the source reports. `cc-by` for all 100. |
| `source_url` | string | the PDF the text was read from. |
| `pdf_sha256`, `bytes` | string, integer | the PDF's hash and size. |

**Rendering the authors, the title and the license is a condition of the license**, not a
courtesy. The title and authors here come from the publisher's own record, so prefer them over
`documents.title` and `documents.author`, which are what the model read off the first page.

## receipt.json

The run's own counts, written by the run. The totals in `README.md` and `LIMITS.md` come from
here; the per-corpus and per-piece-kind tables are counted from the released rows. `flagged`
lists each flagged document by source; `by_kind`, `chars_by_kind` and `flags_by_kind` are the
totals; `cost` is dollars spent, counting calls whose records were later replaced.
