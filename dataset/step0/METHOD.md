# Method

The extractor is one Kaggle notebook of nine blocks:
[ThreadAtlas Extractor](https://www.kaggle.com/code/jhffmn/threadatlas-extractor). This release
is `threadatlas-extractor 1.5`, one pass over the whole corpus, `gpt-5.6-luna` at low reasoning
effort, JSON mode. A document that defeats Luna twice is asked once more on `gpt-5.6-terra`,
which is ten times the price, when it fits in 80,000 tokens. Two of the 230 read documents
escalated.

The design rule behind all of it: **the extractor sees a raw file and nothing else.** No
filename convention, no per-corpus branch, no hand-written rule about where Gutenberg boilerplate
ends. The format is sniffed from the bytes. Everything after that is the model's decision, and
code's job is to check it.

## The address list

A document is shown to the model as its own non-blank lines, numbered. The model points at a
line by number **and copies the line's text**, so the number can be verified against the text
and, when it is off by a few, recovered from it. A file with no usable lines, such as a PDF text
layer that puts one word on each line, is numbered by sentence instead.

This is the whole trick. The model never returns a character offset, and code never decides
where a break may go. A boundary exists only where the model pointed and the copy checks out.

## The question

One call per document, with the whole document in it, asking for:

- `source_class`, `title`, `author`, `source`, `date`, each as a pointer plus the value as it
  should read.
- `toc_count`, how many pieces the contents list promises, so the answer can be counted against
  the document's own table of contents.
- `regions`: where the front matter ends, where the body begins, and where notes, references,
  appendix and license text sit.
- `pieces`: the chapters, sections and scenes.

Dates are never inferred. A date is kept only when its year appears on the line the model read
it from, and a month or day only when the line names the month. The transcriber's date and the
ebook release date are excluded by the prompt, which is why 52 documents carry no date at all.

## Units

Three more calls, all deciding, none measuring:

1. **Sub-split.** A piece over 4,000 words is shown again as numbered lines and the model points
   at the natural breaks inside it. Repeated up to three times. A piece it cannot break stays
   whole and is flagged.
2. **Merge short.** Every piece under 100 words is offered with its text, and the model says it
   joins the piece before, the piece after, or stands alone.
3. **Group.** The outline, every piece with its kind, word count and heading, goes back and the
   model groups consecutive pieces into units: a section with its subsections, a chapter with
   its scenes, never two peers merely because they fit.

Code then checks that the groups cover the outline in order, dissolves a group over the cap, and
cuts any group where the kind changes, so a unit is all one kind.

Chats are grouped differently, and deliberately, and with no model call at all: a session
already states its own boundaries. A session's turns are the pieces, with the role as author.
Units are runs of turns under the cap, never a lone turn, never spanning a change of day, with a
short tail merged back into the unit before it. The session header is front matter and is a unit
of its own.

The day rule is in the code for chat formats that date each turn. LongMemEval is not one: it
dates a session, not its turns, so on this corpus the rule never fires and every turn of a
session carries the date the session started on.

## The gates

Every answer is checked before it becomes data:

- **The pointer gate.** A pointer resolves only when the copied text names the line. The line
  itself, its first eight words, a run of five or more of its words, or a two-line heading
  copied whole. Five words keeps a short heading strict, so "CHAPTER I" cannot answer for
  "CHAPTER II". When the number is wrong but the text is found nearby, the pointer is recovered
  and counted; when the text is nowhere, the pointer is dropped and counted.
- **Tiling.** Pieces are made to cover the document with no gaps and no overlaps, and the export
  asserts that every unit's slice is non-empty before writing it.
- **Metadata pointers** are checked more loosely, as a substring of the line pointed at or its
  near neighbours, because a title, an author or a date is one to four words and the five-word
  rule above would reject every one of them. A failure is nulled and flagged rather than
  retried, because a retry costs a whole document call and the field is already null.

Nothing the model asserted without a verifiable pointer reaches this dataset. Where a check
fails, the row carries a flag saying so rather than a guess.

## Cost and scale

The run reads 19,437 files and writes 19,436 documents for **$7.72**, a median of $0.013 a read
document and $0.421 at the most expensive, a volume of Diodorus Siculus. Six documents at a time
run in parallel, and a document's own over-cap pieces sub-split eight at a time inside that.
Each call is billed to the document that made it, so per-document cost in the run log is real.

The run is resumable: finished documents are appended as they complete and skipped on a restart.
A record written by an older loader version is kept and re-exported unless `REDO_ALL` is set,
which is the switch that makes a code change propagate; this release was produced with it on, so
every row was written by 1.5. Running out of API credit is fatal by design rather than a retry, so a dead key
cannot walk the corpus writing empty flagged records.

## Reproducing it

Fork the notebook, attach
[IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw), add an
OpenAI key, and run all. The papers are a private dataset for license reasons, and block 1
mounts it unconditionally, so without it the run stops before reading anything: make that mount
optional and the run covers 19,295 of the 19,436 documents. A model is not deterministic, so a rerun will differ
in the split of hard documents; the receipt is how two runs are compared.
