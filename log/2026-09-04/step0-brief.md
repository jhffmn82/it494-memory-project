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
3. `log/2026-09-03/plan.md` section "Step 0" and `log/2026-09-04/README.md`, the decisions
   and open items.

How I work: I implement; you draft and argue. One small change at a time, shown to me as a
diff I can read, and check with me before widening scope. Anything you propose that would
change SCHEMA.md or BUILD.md is marked PROPOSED until I rule. No background review loops, no
rewrites. Simplest code possible: stdlib first, raw HTTP to the model, no frameworks. The
extractor must have no corpus-specific code; the existing splitting notebook
(https://www.kaggle.com/code/jhffmn/it494-narrative-corpora-splitting-and-gates) is a source
of gate code and of fixtures with known unit counts, not a base to extend.

## What the end product will see

The fall runs on literature, but the tool is for a person's own material, so the extractor
is built for these and tested on the ones we have now:

- chat transcripts from an AI assistant (JSONL with roles and timestamps; a session is a
  document, the speaker of every turn is known)
- pasted or dropped files: plain text, markdown with headings, emails, meeting notes
- published works: books with chapters (Gutenberg text with header and footer), plays and
  anthologies, papers and their abstracts (arXiv metadata records)
- later, spring: PDF, docx, HTML, mbox; each is one loader that yields the same two shapes

Every document gets an author and a source class at load (SCHEMA.md lists them). Unknown
author is flagged, never guessed.

## Today's three tasks

**1. One raw dataset on Kaggle holding everything.** Folders `oz/`, `holmes/`, `greek/` from
the existing raw dataset (https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw),
plus `graphrag-bench/` (the 20 public-domain novels in `data/benchmarks/graphrag-bench/novel.json`,
MIT licensed, one document each; this is the primary evaluation corpus), `longmemeval/` (the
JSON from `data/benchmarks/`), and `arxiv/` (abstracts as JSONL for the papers in `papers/`,
built from arXiv metadata; check redistribution terms and note them in the manifest). Each
folder carries a manifest with sha256, source URL, and license. NarrativeQA needs no new text:
its 12 works are already in the literature folders. Local transcripts are not uploaded; they
are a local smoke test only.

**2. The extractor**, as a Kaggle notebook first, with the repo holding the copy. Contract:
`load(path) -> documents, units`. Two paths, chosen by sniffing the bytes: structured inputs
become units directly with no model call; unstructured text goes through marker-and-gates:
code builds a compressed view (every short non-empty line with its number, plus the first
and last two hundred lines), one gpt-5.6-luna call at low reasoning effort returns verbatim
strings for body start, body end, the heading lines in order, a table-of-contents count if
there is one, and the preamble metadata lines (title, author, date), code locates each
string with a whitespace-forgiving match and cuts, the three gates verify (count, coverage
over ranges, round-trip), one retry on gpt-5.6-terra, then fixed windows and a flag. The
split plan is stored per document. Prices: luna $0.20/$1.20 per million tokens in/out,
terra $2/$12; set a spending stop.

**3. Export in the schema.** `documents.jsonl` with the text on the document, `units.jsonl`
as ranges, `split_plans.jsonl`, and a receipt table: documents found, units per document,
gates passed or flagged with the reason, boilerplate share, cost. This becomes the next
version of the units dataset and the input to the ingestion notebook.

## Acceptance

- Every one of the 69 existing works reproduces its known unit count without a per-work
  entry, or is flagged with a reason. The 20 GraphRAG-Bench novels split into chapters or are
  flagged; their unit counts become the fixture for the next run. The eleven works the old splitter left as one unit
  either split or are recorded as one unit by my decision.
- LongMemEval sessions and arXiv abstracts load with zero model calls.
- Every unit's slice of its document text is exactly what the splitter cut; every document's
  sha256 matches its raw file.
- Total model cost for the whole raw dataset under two dollars.

## Decide with me before writing code

- Chat unit granularity: a session as one unit, or turn groups cut by length.
- Whether to cap unit length and sub-split at paragraph openings.
- The exact fields of the receipt.

Start by reading the files, then tell me in one paragraph what you understood and ask the
three questions above.
