# Method

The extractor is one Kaggle notebook of ten blocks:
[ThreadAtlas Extractor](https://www.kaggle.com/code/jhffmn/threadatlas-extractor). This release
is `threadatlas-extractor 1.8`, one pass over the whole corpus, `gpt-5.6-luna` at low reasoning
effort on OpenAI's Flex tier. A document that defeats Luna twice is asked once more on
`gpt-5.6-terra` when it fits in 80,000 tokens; six of the 189 read documents escalated.

The design rule behind the split: **the extractor sees a raw file and nothing else.** No filename
convention, no per-corpus branch. The format is sniffed from the bytes. Everything after that is
the model's decision, and code's job is to check it.

## LongMemEval, unpacked

LongMemEval ships as one file of 500 questions, each with its own history of chat sessions, each
session dated within that history. Block 0 writes it as a chat archive would look: one folder per
history, one file per session holding its turns, every turn carrying that history's timestamp for
the session. A session used by several histories is written into each, with each history's date;
a history that lists one session twice gets a second file. Nothing from the test itself is
written: no question, answer, answer sessions or evidence marks. Empty sessions are written too
and skipped by the extractor, which reads the result like any other chat.

## Chats

A session states its own boundaries, so a chat needs no model call. Each turn that says something
is a piece and a unit of its own, with the role as its author and its own timestamp as its time,
labelled by the line that opens it, `SESSION <id> TURN <n> <time>`. A turn with no content is
skipped, and its number is left as a gap.

## Books and papers: the split

A document is shown to the model as its own non-blank lines, numbered. The model points at a line
by number **and copies the line's text**, so the number can be verified against the text and,
when it is off by a few, recovered from it. One call per document asks for the title, author and
source, how many pieces the contents list promises, the regions (front matter, body, notes,
references, appendix, license), the pieces (chapters, sections, scenes), and **the works**: every
separate work the document holds, each at the line where it begins, with the line stating when
it was written.

Three more calls decide the units: a piece over 4,000 words is split at breaks the model points
at; every piece under 100 words is joined to a neighbour or left alone as the model says; and the
outline is grouped into units, a section with its subsections, never two peers merely because they
fit. Code checks that the groups cover the outline in order, dissolves a group over the cap, and
cuts a group wherever the kind or the date changes.

## Books and papers: the dates

Every piece takes the date of the work it lies in, and a document is dated by its earliest unit.
A work's date is the date it was written, or first published when that is all a source gives,
never a translation, an edition, a transcription or an ebook release. It comes from:

1. **The page**, when the model points at a line stating it and the year is on that line as the
   line prints it (405 for the signed year −0404). 156 of the 405 works were dated this way.
2. **A web search** on the work's title and author, when the page states no date: one Responses
   API call on Luna with OpenAI's web search tool, answering with the date and the URL it came
   from. 237 works were dated this way.
3. **Nothing**, when the search found no date. 12 works, 15 units.

The source of every work's date is written into the document's flags, as
`date: <work>: <value> from <the page or the URL>`, or `date: <work>: none, <why>`.

## The gates

- **The pointer gate.** A pointer resolves only when the copied text names the line; when the
  number is wrong but the text is found nearby, it is recovered and counted; when the text is
  nowhere, it is dropped and counted.
- **Tiling.** Pieces cover the document with no gaps and no overlaps, and every unit's slice is
  asserted non-empty before it is written.

## Cost and scale

The run writes 24,071 documents for **$8.24**, a median of $0.0081 a read document with its date
lookups, and $1.13 at the most for a Scientific American Supplement whose articles were each
looked up. Chats cost nothing. Every call runs on the Flex tier at half the standard price; a web
search adds $10 per 1,000 searches.

## Reproducing it

Fork the notebook, attach
[IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw) (version 4
or later, which carries the LongMemEval benchmark file), add an OpenAI key, turn Internet on, and
run all. A model and a web search are not deterministic, so a rerun will differ in the split of
hard documents and in some looked-up dates; the receipt is how two runs are compared.
