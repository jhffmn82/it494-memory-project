# ThreadAtlas Step 0: Documents, Units and Pieces

Every document in the IT 494 memory-backend corpus, split into units, with a piece table that
says what each stretch of a file is and who is speaking there. 19,395 documents, 204,126 units,
205,388 pieces, produced in one pass by a public notebook for $6.75.

This is the input to a memory backend, not a finished analysis. Step 0 answers one question
about a raw file: **where does this document divide, and what kind of text is each part?** No
entities, no facts, no summaries. Those are later steps.

## What makes this different from chunking

A chunker cuts a file every N tokens. This does not cut on length at all. A language model reads
a numbered list of the file's own lines and says where the front matter ends, where the body
begins, where the notes and the references and the appendix are, and where each chapter or scene
starts. Units are then built by grouping those natural parts up to a size cap, cutting only at
boundaries the model named.

**That is the 189 books and papers.** The 19,206 chat sessions need no model, because a session
states its own boundaries: each turn is a piece and a unit of its own, named by the line that
opens it, `SESSION <id> TURN <n> <date>`. So a model was asked about 189 of the 19,395
documents, and the other 19,206 are split on the structure their own format carries.

Two properties follow, and both are verified in this release rather than asserted:

- **Pieces and units tile the document.** Every byte of every file belongs to exactly one piece
  and exactly one unit, with no gaps and no overlaps. Nothing is dropped, nothing is counted twice.
- **A unit never mixes kinds.** A unit is all body, or all references, or all appendix. It never
  runs from the end of a chapter into the footnotes. A chat unit is one turn, with one speaker.

The piece table also carries the speaker, where the file names one. In a chat log a piece is one
turn and its author is `user` or `assistant`. A book or paper names no speaker piece by piece, so
its pieces carry a null author and the document's author stands. A quote's voice is the author of
the piece that holds it, else the document's author, which is what lets a later step tell "Watson
wrote it" from "the model said it".

## Changes in this version

- A chat unit is one turn, labelled `SESSION <id> TURN <n> <date>`. It was a run of turns under
  a session header; the header is gone.
- A chat's title is its session id. It was null.
- A chat carries its session's date only when the session has exactly one. The 3,944 sessions the
  benchmark places on several dates carry none; the earliest was kept before.
- `occurred_until` is gone from the units. A unit carries one time, `occurred_at`.
- The books and papers were split again in this run, so their unit ids and ranges differ from the
  previous version's.

## Files

| file | rows | what it is |
|---|---|---|
| `documents.jsonl` | 19,395 | one row per document: identity, title, author, date, full text |
| `units.jsonl` | 204,126 | the split plan: character ranges into a document's text |
| `pieces.jsonl` | 205,388 | what each stretch of a document is, and who is speaking |
| `attribution.jsonl` | 100 | the CC-BY papers: authors, title, license, DOI and source URL |
| `receipt.json` | — | the run's own totals |

**Every document carries its text.** Nothing in this release is withheld, and no row needs
rebuilding from a source file.

`SCHEMA.md` gives the fields. `METHOD.md` explains how the split is made. `PROVENANCE.md` says
where each document came from and under what license. `LIMITS.md` says what is known to be wrong.

## Quick start

```python
import json

docs = {}
for line in open("/kaggle/input/it494-threadatlas-step0/documents.jsonl", encoding="utf-8"):
    d = json.loads(line)
    docs[d["doc_id"]] = d

# the text of every unit of one book, in order
book = next(d for d in docs.values() if d["title"] == "The Marvelous Land of Oz")
units = [json.loads(l) for l in open("/kaggle/input/it494-threadatlas-step0/units.jsonl", encoding="utf-8")]
mine = sorted((u for u in units if u["doc_id"] == book["doc_id"]), key=lambda u: u["position"])
for u in mine[:5]:
    print(u["position"], u["label"], "|", book["text"][u["start"]:u["end"]][:60].replace("\n", " "))
```

Units carry ranges, not text. Slice `documents.text` with `start` and `end`. The ranges are
character offsets into that exact string, so read the file as UTF-8 and do not normalise it.

## What is in the corpus

| corpus | documents | units | pieces | characters |
|---|---|---|---|---|
| LongMemEval-S sessions | 19,206 | 199,641 | 199,641 | 209,366,971 |
| Greek and Roman literature | 31 | 1,470 | 1,485 | 19,450,676 |
| Oz books | 29 | 709 | 711 | 7,362,917 |
| CC-BY papers on knowledge graphs and RAG | 100 | 1,540 | 2,748 | 6,597,287 |
| GraphRAG-Bench novels | 20 | 507 | 544 | 4,819,610 |
| Sherlock Holmes | 9 | 259 | 259 | 3,976,901 |

Three shapes on purpose. Clean Gutenberg e-texts, scanned books with OCR damage and heavy
apparatus, and 19,206 assistant chat logs. A splitter that only works on tidy books is not a
result.

Piece kinds across the corpus: 100,522 assistant turns, 99,119 user turns, 4,239 body, 692
appendix, 322 notes, 283 front matter, 134 references, 77 license. Body is 80.1% of the 42.2 M
characters read from books and papers.

## The papers

The 100 papers are full-text research papers on knowledge graphs and retrieval-augmented
generation, gathered from OpenAlex, every one of them Creative Commons Attribution. Their text
is here in full, like every other document.

**CC-BY requires attribution, and `attribution.jsonl` carries it.** One row per paper, joined to
`documents.jsonl` on `doc_id`, with the authors, title, year, venue, DOI, OpenAlex id, exact
license and the URL the PDF came from. If you show, quote or redistribute a paper's text, render
the authors, the title and the license from that row.

## Provenance and license

The packaging, the schema and the derived rows are MIT. The underlying text is not one license:
the literature is public domain in the United States by expiry of term, the two benchmark
corpora are MIT and keep their own notices, and the papers are CC-BY and require attribution.
`PROVENANCE.md` gives this per corpus. Raw inputs, byte-identical to what each source served, are
in [IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw).

## How this was made

[ThreadAtlas Extractor](https://www.kaggle.com/code/jhffmn/threadatlas-extractor), one pass,
`threadatlas-extractor 1.7`, `gpt-5.6-luna` at low reasoning effort, escalating to
`gpt-5.6-terra` when a document defeats it twice, which happened to 4 of the 189. $6.75 for the
corpus, median $0.0133 a read document, and nothing at all for the 19,206 chats. A rerun
reproduces the shape but not the split of every hard document, since the model is not
deterministic. `METHOD.md` has the details.

Part of the IT 494 directed project at Illinois State University, fall 2026.
