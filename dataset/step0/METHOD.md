# Method

The extractor is one Kaggle notebook of nine blocks:
[ThreadAtlas Extractor](https://www.kaggle.com/code/jhffmn/threadatlas-extractor). This release
is `threadatlas-extractor 1.7`, one pass over the whole corpus, `gpt-5.6-luna` at low reasoning
effort, JSON mode. A document that defeats Luna twice is asked once more on `gpt-5.6-terra`,
which is ten times the price, when it fits in 80,000 tokens. Four of the 189 read documents
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
ebook release date are excluded by the prompt, which is why 46 documents carry no date at all.

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

Chats are split differently, and with no model call at all: a session already states its own
boundaries. Each turn is a piece and a unit of its own, with the role as its author. The text
gives every turn an opening line, `SESSION <id> TURN <n> <date>`, and that line is the unit's
label. There is no header block.

A turn's time is its session's date when the session has exactly one. LongMemEval reuses 3,944
sessions in the histories of different questions and dates each placement for its question, so
those sessions have no single date of their own. They carry none, on the document, its units or
its turns, and are flagged: the date belongs to the question, and an evaluation supplies it.

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

The run reads 19,395 files and writes 19,395 documents for **$6.75**, a median of $0.0133 a read
document and $0.449 at the most expensive, a volume of Diodorus Siculus. The 19,206 chat sessions
cost nothing, because no model is asked about them. Six documents at a time run in parallel, and
a document's own over-cap pieces sub-split eight at a time inside that. Each call is billed to
the document that made it, so per-document cost in the run log is real.

Finished documents are appended to `splits.jsonl` as they complete and skipped when block 8 runs
again in the same session. A new Kaggle session starts with an empty working folder and asks
every document again. Every row in this release was written by 1.7. Running out of API credit is
fatal by design rather than a retry, so a dead key cannot walk the corpus writing empty flagged
records.

## Reproducing it

Fork the notebook, attach
[IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw), add an
OpenAI key, and run all. That one dataset carries every corpus, papers included, so there is
nothing else to attach and no mount to make optional: the run covers all 19,395 documents as it
stands. A model is not deterministic, so a rerun will differ in the split of hard documents; the
receipt is how two runs are compared.
