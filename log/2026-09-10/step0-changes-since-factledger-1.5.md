# Step 0: what changed since factledger-extractor 1.5

The ingestor (0.9) was built against the `factledger-extractor 1.5` export of 2026-09-06. Step 0
is now `threadatlas-extractor 1.7`, run on 2026-09-10 and published as a new version of
`jhffmn/it494-threadatlas-step0`. Every number below was counted from the two exports.

## Where it lives

| | 1.5 | 1.7 |
|---|---|---|
| dataset | `jhffmn/it494-factledger-step0` (deleted) | `jhffmn/it494-threadatlas-step0` |
| loader field | `factledger-extractor 1.5` | `threadatlas-extractor 1.7` |
| papers | 141 private reference papers; the public export withheld their text, and it was rebuilt from `jhffmn/it494-reference-papers` through `papers.jsonl` | 100 CC-BY papers with full text in `documents.jsonl`; no `papers.jsonl`, no second mount |
| paper `source_uri` | `it494-reference-papers/<name>.pdf` | `it494-narrative-corpora-raw/kg-rag-cc/pdf/NNN_<slug>.pdf` |
| new file | none | `attribution.jsonl`: each paper's authors, title, license, DOI and source URL. CC-BY requires rendering them wherever a paper's text is shown |

## Counts

| | 1.5 | 1.7 |
|---|---|---|
| documents | 19,436 (89 text, 141 PDF, 19,206 chats) | 19,395 (89 text, 100 PDF, 19,206 chats) |
| units | 44,262 | 204,126, of which 199,641 are chat turns |
| pieces | 227,100 | 205,388 |

The 89 texts and the 19,206 chats keep their `doc_id` (the sha256 of the file bytes) and their
`source_uri`. Every `unit_id` and every chat offset changed. The chat text is rendered
differently now, and the model split the books again.

## Schema

- **units.jsonl:** `occurred_until` is gone (ruling of 2026-09-09). A unit carries one time,
  `occurred_at`.
- **Chat text:** each turn is a block `SESSION <id> TURN <n> <date>`, a newline, `<role>: <content>`
  and a blank line. The old header (`session_id: …`, `date: …`) is gone.
- **Chat units:** one per turn, labelled by the turn's opening line. Before, a chat had 2 units:
  a header, then the whole conversation (`turn 1 .. turn 12`).
- **Chat pieces:** one per turn, with kind and author both `user` or `assistant`. There is no
  `front_matter` header piece any more, so front_matter falls from 19,567 pieces to 283. Piece
  and unit coincide, so a chat unit has exactly one speaker.
- **Chat title:** the session id. It was null.
- **Chat time:** the session's date, on the document, every unit and every piece, when the
  session has exactly one date (15,262 sessions). The 3,944 sessions the benchmark places on
  several dates carry none, flagged `dates: N session dates, none kept`. Before, the earliest
  date was kept everywhere.
- **Books and papers:** same shape as before. Piece `author` and `occurred_at` are null, the
  unit carries the document's date, and voice falls back to `documents.author`.
- **Unchanged:** the document fields, the piece fields, the eight kinds, tiling, no unit mixing
  region kinds, and `unit_id = sha256(doc_id \n n \n slice)`.

## What that means for the ingestor (0.9)

- **The withheld-text path is dead:** `KAGGLE_PAPERS`, `withheld_text`, `pdf_text`,
  `PAPERS_ROWS`, `text_rebuilt`, the header's `papers.jsonl` and "text is null" rows, and the
  instruction to attach `it494-reference-papers`.
- **Block 14 is broken:** it runs "five papers, Zep first" through `rasmussen2025-zep.pdf`, which
  is no longer in the corpus. Pick from the 100 kg-rag-cc papers instead.
- **The chat path assumed one conversation unit per chat.** A chat is now about 10 units (12 is
  the most common count), 199,641 in all, and 105,485 of them are under 100 words. Price the
  multi-unit path on a sample before a full ingest.
- **Quotes no longer cross speakers.** Each chat unit has a single speaker, so a quote cannot
  cross a change of speaker inside a unit.
- **55 chat units hold nothing** but their opening line and `role: `. The turn's content was
  empty, or only a zero-width space. Skip them.
- **3,944 chats have no date anywhere.** The evaluation supplies each question's date, and it
  filters by the question's haystack session ids, never by date.
- **Chats can be found by title now**, since the title is the session id. Titles are still not
  unique (2 are null, and "The Library" and "GRAG: Graph Retrieval-Augmented Generation" each
  appear twice), so join on `doc_id`.
- **The header's kinds table is wrong:** it lists a `turn` kind. The export has only `user` and
  `assistant`.
- **`occurred_until`:** the ingestor already reads only `occurred_at` (commit fa48997).

## Still to update outside the ingestor

- Root `SCHEMA.md` (the day-cut paragraph and the "never a lone turn" rule).
- `BUILD.md` line 12.
- `docs/extractor.md`.

These still describe chat units as runs of turns.
