# Brief for the Step 0 chat: raw dataset, general extractor, schema export

Paste this as the first message of a new chat. It is self-contained; the chat should read
the repository files it names before proposing anything.

---

You are helping me build one step of my IT 494 project, a memory backend for a desktop
assistant. Read these before anything else, in this order, from
https://github.com/jhffmn82/it494-memory-project (local clone: `C:\Users\jhffm\it494-memory-project`):

1. `SCHEMA.md`, the record shapes. The document holds its text once; units are ranges
   `(unit_id, doc_id, position, label, start, end)` in character offsets into that text.
2. `BUILD.md`, the loader rule: sniff the format from bytes, structured inputs need no model
   call, unstructured text is split by one model call per document proposing verbatim marker
   lines, three gates verify, no per-work or per-corpus rules, a rejected document is stored
   as one unit and flagged.
3. `log/2026-09-04/inventory.md`, the audited list of every source and, at the end, my
   rulings on all of it. Then `log/2026-09-04/README.md` and `log/2026-09-03/plan.md`
   section "Step 0" for the reasoning.
4. `data/raw/SOURCES.md` and `USAGE.md` for per-work provenance.

How I work: I implement; you draft and argue. One small change at a time, shown to me as a
diff I can read, and check with me before widening scope. Anything you propose that would
change SCHEMA.md or BUILD.md is marked PROPOSED until I rule. No background review loops, no
rewrites. Simplest code possible: stdlib first, raw HTTP to the model, no frameworks. The
extractor must have no corpus-specific code; the existing splitting notebook
(https://www.kaggle.com/code/jhffmn/it494-narrative-corpora-splitting-and-gates) is a source
of gate code and of reference unit counts, not a base to extend.

## The governing rule

The extractor sees raw files and nothing else. No metadata beside a file, no manifest, no
question set. It reads the bytes, decides what the file is, and writes document and unit
JSON. Author, title, date, and speaker come from the file itself, quote-backed, or are
flagged unknown. Source class follows the sniffed format: book to canonical, chat session to
record, paper to published.

## What the end product will see

The fall runs on literature and benchmarks, but the tool is for a person's own material.
The extractor handles these kinds of file, and the dataset has real examples of each:

- **chat sessions**, one file per session, roles and a date inside the file. A session is a
  document. This is how the product is meant to be used, so this loader is the one to get
  exactly right. On hand: about 18,800 LongMemEval sessions as JSON (session id, date, turns
  of role and content, no per-turn timestamps); my local assistant logs (JSONL, one typed
  object per line, ISO timestamps; local smoke test only, never uploaded).
- **books**: Gutenberg text with header and footer (oz 29, holmes 9, most of greek 31), plays
  and anthologies, Archive.org OCR scans with no header, footer, or Author line at all (6 in
  greek), and 20 GraphRAG-Bench texts that are a whole book on one line with the Gutenberg
  markers stripped (9 without a chapter token, several not novels).
- **papers as PDF**: 142 in a private dataset. One dependency for the text layer (PyMuPDF or
  pdfplumber). The document is the whole paper, units are sections, the abstract is the
  first unit; author, title, and date are read from the first page.
- **pasted or dropped files**: plain text, markdown with headings, emails, meeting notes. No
  fixture exists; exercise the extractor on hand-made samples.
- later, spring: docx, HTML, mbox; each is one loader that yields the same two shapes.

## Units, everywhere

A unit is a size-bounded run of the document's natural pieces: chapters in a book, turns in a
chat, sections in a paper. Never a cut inside a piece, never a turn alone, a short tail
merged into the unit before it. Propose the cap and the tail floor in words, with the
reasoning; I rule. For reference, the average literature unit is about 4,000 words and the
average LongMemEval session about 1,700, so most sessions will be one unit and long ones
split.

## Today's three tasks

**1. Two raw datasets on Kaggle.** Public, MIT, attribution in the description and per-folder
manifests: `oz/`, `holmes/`, `greek/` (31; the Thebaid removed) carried over from
https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw without `chinese/`;
`graphrag-bench/` (20 text files unpacked from `data/benchmarks/graphrag-bench/novel.json`,
with its LICENSE); `longmemeval/` (one JSON per distinct non-empty session unpacked from
`data/benchmarks/longmemeval/longmemeval_s.json`, the `has_answer` flag dropped). Private:
`papers/` (the PDFs). The unpack and fetch scripts live in the repository and also write
the manifests (file, sha256, bytes, source, real source URL, license, and the answer-key
fields title, author, year, translator, ordinal, quality flags). The manifests are for us;
the extractor never reads them. Question sets, gold, and scorers stay in the repository for
the evaluation step.

**2. The extractor, as a Kaggle notebook** with the repository holding the copy (later it
becomes a GitHub tool that runs on the desktop). Contract: `load(path) -> documents, units`.
Sniff the bytes. Structured files (a chat session, a transcript) become units with no model
call. PDF goes through the text layer and then the unstructured path. Unstructured text goes
through marker-and-gates: code builds a compressed view (short non-empty lines numbered plus
the first and last two hundred lines; for a one-line document or one whose lines are nearly
all short, a substring-based view, and that rule is part of the design), one gpt-5.6-luna
call at low reasoning effort returns verbatim strings for body start, body end, the heading
lines in order, a table-of-contents count if there is one, and the metadata lines (title,
author, translator, date), code locates each string with a whitespace-forgiving match and
cuts, the three gates verify (count, coverage over ranges, round-trip), one retry on
gpt-5.6-terra, then fixed windows and a flag. Then the size rule groups pieces into units.
The split plan is stored per document. Prices: luna $0.20/$1.20 per million tokens in/out,
terra $2/$12; set a spending stop.

**3. Export in the schema.** `documents.jsonl` with the text on the document, `units.jsonl`
as ranges, `split_plans.jsonl`, and a receipt table: documents found, units per document,
gates passed or flagged with the reason, unknown-author count, boilerplate share, cost. This
becomes the next version of the units dataset and the input to the ingestion notebook, whose
loader currently reads unit text and must be changed to read ranges.

## Acceptance

- Every literature file produces units without a per-work entry, or is flagged with a
  reason. The old splitter's counts are a reference: I review every difference and my
  rulings become the new fixture. Seventeen works were single before (two Oz, the Hesiod
  anthology, nine Euripides plays, five Archive.org scans); each splits or is recorded as
  one unit by my decision.
- The 20 GraphRAG-Bench texts split or are flagged; a flagged share is expected.
- Every LongMemEval session loads with zero model calls, as one document with size-bounded
  turn-group units and the speaker recoverable from the text; a session reused across
  questions exists once.
- A sample of the PDFs yields sections with the abstract first and the author, title, and
  date read from page one; the rest are flagged, not dropped.
- Every unit's slice of its document text is exactly what the splitter cut; every
  document's sha256 matches its raw file.
- Unknown-author documents are counted in the receipt, not guessed (six Archive.org scans,
  three GraphRAG-Bench texts, every LongMemEval session).
- Total model cost for the whole raw dataset under two dollars.

## Decide with me before writing code

- The unit cap and the tail floor.
- The substring-based compressed view for one-line documents.
- The exact fields of the receipt.

Start by reading the files, then tell me in one paragraph what you understood and put the
three questions to me one at a time, with your recommendation for each.
