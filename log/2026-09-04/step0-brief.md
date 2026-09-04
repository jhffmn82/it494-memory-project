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
3. `log/2026-09-04/inventory.md`, the audited list of every source, its real format, and
   the twelve decisions I have to make. Then `log/2026-09-03/plan.md` section "Step 0" and
   `log/2026-09-04/README.md` for the reasoning behind them.
4. `data/raw/SOURCES.md`, `USAGE.md`, `WANTLIST.md`, the per-work provenance and the
   fixtures (OCR control, translation control, exclusions).

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

- chat transcripts from an AI assistant: a session is a document, the speaker of every
  turn is known. Two shapes exist today: my local assistant logs (JSONL, one typed object
  per line, ISO timestamps, content as a list of blocks; local smoke test only, never
  uploaded) and LongMemEval (one JSON array; turns are role and content with no timestamp;
  the session date lives in a parallel list).
- pasted or dropped files: plain text, markdown with headings, emails, meeting notes. No
  fixture exists for these yet; the extractor is exercised on them with hand-made samples.
- published works: books with chapters (Gutenberg text with header and footer), plays and
  anthologies, OCR scans with no header, footer, or Author line at all, benchmark contexts
  that are a whole book on one line with the Gutenberg markers stripped, papers as arXiv
  metadata records (abstracts).
- later, spring: PDF, docx, HTML, mbox; each is one loader that yields the same two shapes.

Every document gets an author and a source class at load (SCHEMA.md lists them). Unknown
author is flagged, never guessed, and the receipt counts how many documents took that path
(nine Archive.org scans, three GraphRAG-Bench contexts, and every LongMemEval session will).

## Today's three tasks

**1. One raw dataset on Kaggle holding everything.** The folders and their real state are
in `inventory.md`; in short: `oz/` (29), `holmes/` (9), `greek/` (32, one excluded), and
`chinese/` (11; carries the OCR control, the translation-control source, and NarrativeQA's
twelfth work) from the existing raw dataset
(https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw); `graphrag-bench/`
(`novel.json`, 20 contexts in one JSON file, MIT; the primary evaluation corpus);
`longmemeval/` (the oracle file, and the `_s` file if I rule it in; MIT); `arxiv/`
(abstracts as JSONL built from arXiv metadata for the papers with ids; the set, the record
shape, and fall-or-spring are among the decisions). NarrativeQA gold (12 works, 345
questions) sits beside the dataset with its join columns. Every folder carries a manifest
regenerated to one schema: file, sha256, bytes, real source URL, source, license, ordinal,
title, author when known at load, year, quality flags (ocr, bilingual, abridged),
translator, exclude with reason. The dataset description, `SOURCES.md`, `USAGE.md`, and
`WANTLIST.md` carry over; the dataset license is declared mixed, per folder.

**2. The extractor.** Contract: `load(path) -> documents, units`. Two paths, chosen by
sniffing the bytes: structured inputs become units directly with no model call;
unstructured text goes through marker-and-gates: code builds a compressed view (every short
non-empty line with its number, plus the first and last two hundred lines; for a document
that is one line, or whose lines are nearly all short, the view is built from substrings
instead, and that rule is part of the design, not a special case), one gpt-5.6-luna call at
low reasoning effort returns verbatim strings for body start, body end, the heading lines
in order, a table-of-contents count if there is one, and the preamble metadata lines
(title, author, translator, date), code locates each string with a whitespace-forgiving
match and cuts, the three gates verify (count, coverage over ranges, round-trip), one retry
on gpt-5.6-terra, then fixed windows and a flag. The split plan is stored per document.
Preamble lines the model names become quote-backed document facts, not just fields. Prices:
luna $0.20/$1.20 per million tokens in/out, terra $2/$12; set a spending stop. Where the
code lives (Kaggle notebook with a repo copy, or `scripts/extract.py` imported by the
notebook) is decision 10.

**3. Export in the schema.** `documents.jsonl` with the text on the document, `units.jsonl`
as ranges, `split_plans.jsonl`, and a receipt table: documents found, units per document,
gates passed or flagged with the reason, unknown-author count, boilerplate share, cost.
This becomes the next version of the units dataset and the input to the ingestion
notebook, whose loader currently reads unit text and must be changed to read ranges.

## Acceptance

- Every one of the 81 literature files reproduces its known unit count without a per-work
  entry, or is flagged with a reason; the fixture policy (decision 11) says which of the old
  per-work rulings count as matches. The seventeen works the old splitter left as one unit
  (two Oz, the Hesiod anthology, nine Euripides plays, five Archive.org scans) either split
  or are recorded as one unit by my decision. The Thebaid is handled per decision 2.
- The 20 GraphRAG-Bench contexts split or are flagged; nine have no chapter token and
  several are not novels, so a flagged share is expected and the cost line allows for it.
  Their unit counts become the fixture for the next run.
- LongMemEval sessions and arXiv abstracts load with zero model calls; reused sessions are
  stored once.
- Every unit's slice of its document text is exactly what the splitter cut; every document's
  sha256 matches its raw file (for GraphRAG-Bench, the sha256 of `novel.json` plus the record
  index).
- The hand-labeled alias set is built against the unit ids this run mints, after the run.
- Total model cost for the whole raw dataset under two dollars.

## Decide with me before writing code

The twelve decisions in `inventory.md` (chinese/, Thebaid, LongMemEval files and document
boundary, GraphRAG-Bench packaging, arXiv set and status, dataset licensing, manifest
schema, author and source class per folder, export location, extractor location, fixture
policy, LongMemEval fall/spring wording), plus:

- Chat unit granularity: a session as one unit, or turn groups cut by length.
- Whether to cap unit length and sub-split at paragraph openings.
- The exact fields of the receipt.

Start by reading the files, then tell me in one paragraph what you understood and put the
decisions to me one at a time, with your recommendation for each.
