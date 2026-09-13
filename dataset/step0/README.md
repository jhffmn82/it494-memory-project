# ThreadAtlas Step 0: Documents, Units and Pieces

Every document in the IT 494 memory-backend corpus, split into units, with a piece table that
says what each stretch of a file is, who is speaking there, and when it is from. 24,071
documents, 251,446 units, 252,830 pieces, **every unit dated**, produced in one pass by a public
notebook for $8.24.

This is the input to a memory backend, not a finished analysis. Step 0 answers two questions
about a raw file: **where does this document divide, and what kind of text is each part, from
when?** No entities, no facts, no summaries. Those are later steps.

## What makes this different from chunking

A chunker cuts a file every N tokens. This does not cut on length at all. A language model reads
a numbered list of the file's own lines and says where the front matter ends, where the body
begins, where the notes and the references and the appendix are, where each chapter or scene
starts, and which separate works a volume holds. Units are then built by grouping those natural
parts up to a size cap, cutting only at boundaries the model named.

**That is the 189 books and papers.** The 23,882 chat sessions need no model, because a session
states its own boundaries: each turn is a piece and a unit of its own, named by the line that
opens it, `SESSION <id> TURN <n> <time>`, and dated by its own timestamp.

Three properties follow, and all are verified in this release rather than asserted:

- **Pieces and units tile the document.** Every byte of every file belongs to exactly one piece
  and exactly one unit, with no gaps and no overlaps.
- **A unit never mixes kinds or dates.** A unit is all body, or all references, or all appendix,
  and all from one date. A chat unit is one turn, with one speaker.
- **Every unit is dated, and a document is dated by its earliest unit.** A book or paper unit
  carries the date its work was written, BC and approximate dates included; a chat unit carries
  its turn's time.

## Changes in this version

- **Every unit has a date.** A work is dated by when it was written, not by a translation or an
  edition: the date its page states, or else one found by a web search on its title and author,
  with the source recorded in the document's flags. A volume that holds several works is dated
  work by work, and a unit never spans two of them. 15 units stay undated, each because no source
  gave its work a date.
- **LongMemEval is unpacked into its 500 histories.** Each question's history is its own folder,
  and a session used by several histories is a separate document in each, dated as that history
  dates it. A chat's `source_uri` is `chats/longmemeval/<history>/<session>.json`.
- **Empty sessions and empty turns are skipped** (1,230 sessions, 70 turns) and counted in the
  receipt.
- **`occurred_at` holds more forms**: a signed year before the common era, `~` for an approximate
  date, and `/` for a range. `SCHEMA.md` gives them.

## Files

| file | rows | what it is |
|---|---|---|
| `documents.jsonl` | 24,071 | one row per document: identity, title, author, date, full text |
| `units.jsonl` | 251,446 | the split plan: character ranges into a document's text, each dated |
| `pieces.jsonl` | 252,830 | what each stretch of a document is, who is speaking, and when |
| `attribution.jsonl` | 100 | the CC-BY papers: authors, title, license, DOI and source URL |
| `receipt.json` | — | the run's own totals |

**Every document carries its text.** `SCHEMA.md` gives the fields. `METHOD.md` explains how the
split and the dates are made. `PROVENANCE.md` says where each document came from and under what
license. `LIMITS.md` says what is known to be wrong.

## Quick start

```python
import json

docs = {}
for line in open("/kaggle/input/it494-threadatlas-step0/documents.jsonl", encoding="utf-8"):
    d = json.loads(line)
    docs[d["doc_id"]] = d

# one LongMemEval history: every session of question gpt4_2ba83207, in time order
history = sorted((d for d in docs.values() if d["source_uri"].startswith("chats/longmemeval/gpt4_2ba83207/")),
                 key=lambda d: d["occurred_at"])
print(len(history), history[0]["title"], history[0]["occurred_at"])
```

Units carry ranges, not text. Slice `documents.text` with `start` and `end`. The ranges are
character offsets into that exact string, so read the file as UTF-8 and do not normalise it.

## What is in the corpus

| corpus | documents | units | pieces | characters |
|---|---|---|---|---|
| LongMemEval-S sessions, in 500 histories | 23,882 | 246,860 | 246,860 | 258,880,622 |
| Greek and Roman literature | 31 | 1,601 | 1,674 | 19,450,676 |
| Oz books | 29 | 724 | 733 | 7,362,917 |
| CC-BY papers on knowledge graphs and RAG | 100 | 1,508 | 2,712 | 6,597,287 |
| GraphRAG-Bench novels | 20 | 480 | 576 | 4,819,610 |
| Sherlock Holmes | 9 | 273 | 275 | 3,976,901 |

Piece kinds across the corpus: 124,363 assistant turns, 122,497 user turns, 4,249 body, 602
appendix, 525 notes, 404 front matter, 118 references, 72 license. Body is 81.6% of the 42.2 M
characters read from books and papers.

The dates run from the Iliad, dated −0749/−0724, to the chats of 2021 to 2024. 23 books are dated
before the common era.

## The papers

The 100 papers are full-text research papers on knowledge graphs and retrieval-augmented
generation, gathered from OpenAlex, every one of them Creative Commons Attribution.
**CC-BY requires attribution, and `attribution.jsonl` carries it.** One row per paper, joined to
`documents.jsonl` on `doc_id`. If you show, quote or redistribute a paper's text, render the
authors, the title and the license from that row.

## Provenance and license

The packaging, the schema and the derived rows are MIT. The underlying text is not one license:
the literature is public domain in the United States by expiry of term, the two benchmark
corpora are MIT and keep their own notices, and the papers are CC-BY and require attribution.
`PROVENANCE.md` gives this per corpus. Raw inputs, byte-identical to what each source served, are
in [IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw).

## How this was made

[ThreadAtlas Extractor](https://www.kaggle.com/code/jhffmn/threadatlas-extractor), one pass,
`threadatlas-extractor 1.8`, `gpt-5.6-luna` at low reasoning effort on OpenAI's Flex tier,
escalating to `gpt-5.6-terra` when a document defeats it twice, which happened to 6 of the 189.
$8.24 for the corpus, a median of $0.0081 a read document including its date lookups, and nothing
for the chats. `METHOD.md` has the details.

Part of the IT 494 directed project at Illinois State University, fall 2026.
