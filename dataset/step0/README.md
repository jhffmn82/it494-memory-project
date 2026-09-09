# ThreadAtlas Step 0: Documents, Units and Pieces

Every document in the IT 494 memory-backend corpus, split into units, with a piece table that
says what each stretch of a file is and who is speaking there. 19,436 documents, 44,262 units,
227,100 pieces, produced in one pass by a public notebook for $7.72.

This is the input to a memory backend, not a finished analysis. Step 0 answers one question
about a raw file: **where does this document divide, and what kind of text is each part?** No
entities, no facts, no summaries. Those are later steps.

## What makes this different from chunking

A chunker cuts a file every N tokens. This does not cut on length at all. A language model reads
a numbered list of the file's own lines and says where the front matter ends, where the body
begins, where the notes and the references and the appendix are, and where each chapter or scene
starts. Units are then built by grouping those natural parts up to a size cap, cutting only at
boundaries the model named.

**That is the 230 books and papers.** The 19,206 chat sessions need no model to find their
boundaries, because a session states them: a turn is a piece, and code groups turns into units
under the same cap. So a model was asked about 230 of the 19,436 documents, and the other
19,206 are split on the structure their own format carries.

Two properties follow, and both are verified in this release rather than asserted:

- **Pieces and units tile the document.** Every byte of every file belongs to exactly one piece
  and exactly one unit, with no gaps and no overlaps. Nothing is dropped, nothing is counted twice.
- **A unit never mixes kinds.** A unit is all body, or all references, or all appendix. It never
  runs from the end of a chapter into the footnotes.

The piece table also carries the speaker. In a chat log a piece is one turn and its author is
`user` or `assistant`; in a book the author is the document's author. A quote's voice is the
author of the piece that holds it, which is what lets a later step tell "Watson wrote it" from
"the model said it".

## Files

| file | rows | what it is |
|---|---|---|
| `documents.jsonl` | 19,436 | one row per document: identity, title, author, date, full text |
| `units.jsonl` | 44,262 | the split plan: character ranges into a document's text |
| `pieces.jsonl` | 227,100 | what each stretch of a document is, and who is speaking |
| `papers.jsonl` | 141 | the withheld papers, with a URL and a hash so you can rebuild them |
| `receipt.json` | — | the run's own totals |

`SCHEMA.md` gives the fields. `METHOD.md` explains how the split is made. `PROVENANCE.md` says
where each document came from and under what license. `LIMITS.md` says what is known to be wrong.

## Quick start

```python
import json, collections

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
| LongMemEval-S sessions | 19,206 | 38,412 | 218,847 | 201,075,057 |
| Greek and Roman literature | 31 | 2,039 | 2,099 | 19,450,676 |
| Oz books | 29 | 708 | 709 | 7,362,917 |
| GraphRAG-Bench novels | 20 | 504 | 593 | 4,819,610 |
| Sherlock Holmes | 9 | 271 | 271 | 3,976,901 |
| reference papers (text withheld) | 141 | 2,328 | 4,581 | — |

Three shapes on purpose. Clean Gutenberg e-texts, scanned books with OCR damage and heavy
apparatus, and 19,206 assistant chat logs. A splitter that only works on tidy books is not a
result.

Piece kinds across the corpus: 100,522 assistant turns, 99,119 user turns, 19,567 front matter,
5,900 body, 1,062 appendix, 642 notes, 209 references, 79 license. Body is 82% of the 48.6 M
characters read from books and papers.

## Reference papers

The 141 papers keep their publishers' licenses and most may not be redistributed, so **their
text is withheld**: the document row is here with `"text": null` and the flag
`text withheld: license`, and its units and pieces are here in full. To rebuild the text, take
the row in `papers.jsonl`, fetch `source_url`, check the PDF against `pdf_sha256`, and run the
text extraction in block 2 of the notebook, which is PyMuPDF page text joined by newlines. The
offsets then resolve. The notebook as published mounts the private papers dataset in block 1 and
stops without it, so running it on the public corpus alone needs that mount made optional.

## Provenance and license

The packaging, the schema and the derived rows are MIT. The underlying text is not one license:
the literature is public domain in the United States by expiry of term, the two benchmark
corpora are MIT and keep their own notices, and the papers are withheld. `PROVENANCE.md` gives
this per corpus. Raw inputs, byte-identical to what each source served, are in
[IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw).

## How this was made

[ThreadAtlas Extractor](https://www.kaggle.com/code/jhffmn/threadatlas-extractor), one pass,
`threadatlas-extractor 1.5`, `gpt-5.6-luna` at low reasoning effort, escalating to
`gpt-5.6-terra` when a document defeats it twice, which happened to 2 of the 230. $7.72 for the
corpus, median $0.013 a read document. A rerun reproduces the shape but not the split of every
hard document, since the model is not deterministic. `METHOD.md` has the details.

Part of the IT 494 directed project at Illinois State University, fall 2026.
