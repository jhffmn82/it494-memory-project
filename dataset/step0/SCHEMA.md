# Schema

Four JSON Lines files and a receipt. One JSON object per line, UTF-8, newline separated.

Character offsets are indices into `documents.text` for the same `doc_id`, as Python string
indices over the decoded UTF-8 text. Read the file without normalising newlines or whitespace
and `text[start:end]` is the piece or unit exactly.

## Dates

`occurred_at`, on documents, units and pieces, is a string in one of these forms: a date as
`YYYY`, `YYYY-MM` or `YYYY-MM-DD`; a chat turn's timestamp as `YYYY-MM-DDThh:mm:ss`; a year before
the common era as a signed year that counts a year zero, so 405 BC is `-0404`; a trailing `~` for
an approximate date, as in `-0404~`; and a range as its two ends joined by `/`, as in
`-0749/-0724`. Sort by the first year, read as a signed integer, not by the string.

## documents.jsonl

One row per distinct document. Two source files with identical bytes are one document; the
receipt's `duplicate_files` names any file that was dropped and the one it matched.

| field | type | meaning |
|---|---|---|
| `doc_id` | string | sha256 of the document's bytes, hex. The join key everywhere else. |
| `source_uri` | string | where the file was read from: the raw dataset and path for a book or paper, and `chats/longmemeval/<history>/<session>.json` for a chat, where `<history>` is the LongMemEval question whose history holds the session. |
| `sha256` | string | the same hash again, as the schema names it separately from the id. |
| `title` | string or null | the source's own name for the document: read off the page for a book or a paper, and the session id for a chat, which is the only name a session file carries. Never a filename. |
| `author` | string or null | the person who wrote it. A publication only when no person is named, and then flagged. Null for a chat. |
| `source_class` | string or null | `canonical`, `published`, `record`, `authored` or `tool-output`. |
| `text` | string | the document as text. Never null. |
| `ingested_at` | string | when this run read the file, ISO 8601 UTC. |
| `occurred_at` | string or null | the earliest of its units' dates. |
| `loader` | string | the extractor version that wrote the row. `threadatlas-extractor 1.8` throughout. |
| `flags` | array of string | notes the run left. Every book and paper carries one `date:` note per work, saying where its date came from; the rest are what the run could not settle. See `LIMITS.md`. |

## units.jsonl

The split plan. A unit is a run of consecutive pieces, cut only at piece boundaries. A chat unit
is exactly one turn.

| field | type | meaning |
|---|---|---|
| `unit_id` | string | sha256 of the document id, how many identical slices came before it, and the slice. |
| `doc_id` | string | the document. |
| `position` | integer | 0-based, dense, in document order. |
| `label` | string | for a book or paper, the heading or opening the model named; for a chat, the line that opens the turn, `SESSION <id> TURN <n> <time>`. Not unique, not a key. |
| `start`, `end` | integer | character range into `documents.text`. |
| `occurred_at` | string or null | for a book or paper, the date of the work the unit belongs to; for a chat, the turn's timestamp. Null only when no source gave the work a date, and then the document's flags say so. |

Guarantees, verified on all 24,071 documents in this release:

- Units of one document tile it, and every unit's slice is non-empty after stripping whitespace.
- `unit_id` is unique across the file, and all 251,446 recompute from the document's own text.
- No unit spans two dates.

## pieces.jsonl

What each stretch of a document is, who is speaking there, and when it is from.

| field | type | meaning |
|---|---|---|
| `doc_id` | string | the document. |
| `unit_id` | string | the unit that contains this piece. Always a unit of the same document. |
| `position` | integer | 0-based, dense, in document order. |
| `kind` | string | `front_matter`, `body`, `notes`, `references`, `appendix`, `license`, `user` or `assistant`. |
| `start`, `end` | integer | character range into `documents.text`. |
| `author` | string or null | the speaker, when the file names one: `user` or `assistant` on a chat turn. Null on every piece of a book or paper; the document's `author` stands there. |
| `occurred_at` | string or null | a chat turn's timestamp; for a book or paper, the date of the work the piece lies in. |

Guarantees, verified on all 24,071 documents:

- Pieces of one document tile it, the same way units do.
- **No unit mixes kinds.** A unit is all body, or all references, or all appendix. In a chat,
  piece and unit coincide: each turn is one piece and one unit.

## attribution.jsonl

The 100 CC-BY papers, and what their license asks of anyone who redistributes them.

| field | type | meaning |
|---|---|---|
| `doc_id` | string | joins to the document row; the sha256 of the PDF's bytes, so it equals `pdf_sha256`. |
| `source_uri` | string | the same path the document row carries. |
| `title` | string | the paper's title as its publisher records it. |
| `authors` | array of string | every author, in order, up to twelve. |
| `year`, `venue` | integer or null, string or null | publication year and venue, when OpenAlex records them. |
| `doi`, `openalex_id` | string or null | the two stable identifiers. |
| `license` | string | the exact license the source reports. `cc-by` for all 100. |
| `source_url` | string | the PDF the text was read from. |
| `pdf_sha256`, `bytes` | string, integer | the PDF's hash and size. |

**Rendering the authors, the title and the license is a condition of the license.**

## receipt.json

The run's own counts, written by the run: documents, units and pieces; counts by kind, characters
by piece kind and flags by kind; `empty_sessions` and `empty_turns`, the chat sessions and turns
that said nothing and were skipped; pointer mismatches, recoveries and misses; units over and
under the size cap; and `cost`, the dollars spent, date lookups included.
