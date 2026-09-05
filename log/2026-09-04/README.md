# Working log: 2026-09-04

PC session, morning to past midnight. Picked up the laptop's 09-03 notes (`log/2026-09-03/`),
walked through the merge after document ingestion, inventoried every source Step 0 must
handle, ruled the twelve decisions that inventory raised, opened the extractor chat, ruled
on what it found, absorbed an outside design review, corrected the living docs, and
reviewed the extractor notebook the chat had built. Decisions are Justin's; open items are
marked. Files in this folder: [inventory.md](inventory.md) (the audit and the twelve
rulings), [step0-brief.md](step0-brief.md) (the extractor chat's opening message),
[factledger_blocks_3_to_9.py](factledger_blocks_3_to_9.py) (the proposed rewrite of the
extractor's model path, delivered at the end of the day, not yet applied).

## Morning: decisions from the 09-03 notes

- **Community grouping is out.** Not deferred, removed. It pays only for thematic questions
  over a group nobody declared, which nothing this project asks. Declared groupings (a
  series, a thread) exist only for supersession ordering and disambiguation scope, and
  nothing is clustered. SCHEMA.md says so.
- **Document-level salience is reassessed at the end of ingestion**, once the document
  abstract exists: named in the abstract means major; unit count, then fact count, break
  ties. Only document-majors carry dossiers into the merge. Unit-level salience still
  decides who gets a cell.
- **Abstracts refold whenever their children change** (confirmed; the hash rule in BUILD).
- **Documents are entities** (confirmed): a node with unit summaries as cells, an abstract,
  `has_unit`, `produced_by`, and `appears_in` edges. Documents never merge with each other.
- **The document holds its text, once; units are ranges.** The source is decoded to a string
  at load and stored on the document record with the sha256 of the original bytes. A unit is
  `(doc_id, position, label, start, end)`. Every offset in the store, on units, mentions, and
  fact quotes, is a document offset in that one coordinate system. In SQLite this is a text
  column on the document table and a range table for units; FTS5 reads through the offsets;
  `get_source` is one slice; the stored quote audit is one SQL statement.
- **Next build step: the general extractor** (plan.md Step 0), simplest code, no per-corpus
  regex. Contract `load(path) -> documents, units`. Structured inputs become units with no
  model call; unstructured text gets one Luna call per document, code cuts, the three gates
  verify, retry once on Terra, then fixed windows and a flag. Outputs: `documents.jsonl`
  (with text), `units.jsonl` (ranges), `split_plans.jsonl`, a receipt.
- **All raw text goes into one Kaggle dataset and the extractor runs over all of it.** The
  morning list (`oz/`, `holmes/`, `greek/`, `chinese/`, `graphrag-bench/`, `longmemeval/`,
  `arxiv/`) was superseded by the evening rulings below: chinese/ out, the papers as PDFs
  in a private dataset rather than `arxiv/` abstracts. Test set for the ingestor afterward,
  a sampling of every source type: three Oz books, two Greek works, two Holmes collections,
  a few GraphRAG-Bench texts, a handful of LongMemEval sessions, twenty or so papers.
- **NarrativeQA stays our owned subset.** NarrativeQA holds 1,572 works of its own; we do
  not pull them. Ruled at noon as 12 works and 345 questions; the evening's chinese/ ruling
  made it 11 works and 319. NarrativeQA's own copies were different Gutenberg fetches of the
  same ids (sizes differ), so edition alignment is checked when the arm is scored.
- **Order of work from here:** (1) the raw extractor solid against every source in the
  dataset; (2) the document ingestor against a sampling of each source type, with the
  paper path as a first-class case; (3) the global merge. Each gets its own chat with a
  brief from this log.

## The merge, as walked through (no change to the 09-03 rules)

Raw layer first (document and units by content hash, idempotent); resolve the author to a
node before any fact; nominate candidates for document-majors only (nearest-k by dossier
embedding plus exact surface hits, exact hits nominate a judge and never auto-union); judge
on the strong tier with dossiers recorded per verdict, disambiguators on a judged-different
name collision, kept-apart pairs persisted, `different` never vetoes a later verdict on a
larger dossier; commit facts unit by unit in position order with the voice-lineage collision
rule on functional predicates; cells appended; abstracts refolded where the children hash
changed; vectors and alias FTS refreshed; package marked applied.

## Afternoon: the inventory

The first draft of the Step 0 brief was checked against the repository, the disk, and Kaggle
by five sweeps; the findings are in [inventory.md](inventory.md). It had eleven statements
wrong (among them: NarrativeQA's twelfth work is in `chinese/`; seventeen works were left
single, not eleven; nine Archive.org scans have no Gutenberg markers or Author line; the
GraphRAG-Bench contexts are one line each with markers stripped and nine lack a chapter
token; the manifests have no license field and `cached` for a URL; LongMemEval is three
files with no per-turn timestamps; the abstracts were ruled spring on 09-03) and left out
twenty things, from the `chinese/` folder and the Thebaid exclusion mechanism to the
ingestion notebook's dependence on unit text. Lesson recorded: inventory first, then the
brief, and never offer a narrower option because it is what is on hand.

## Evening: the twelve rulings

Justin ruled all twelve, one at a time; the full text is at the end of
[inventory.md](inventory.md). The governing rule: **the extractor sees raw files and nothing
else.** In short: chinese/ out (NarrativeQA 11 works, 319 questions; the OCR and translation
controls leave the slate and return only with the folder); the Thebaid file removed;
LongMemEval `_s` unpacked to one JSON file per session and a session is a document; units
everywhere are size-bounded runs of natural pieces cut only at piece boundaries;
GraphRAG-Bench unpacked to 20 text files; papers as the raw PDFs in a private dataset with
the PDF loader moved from spring to fall; public dataset MIT; manifests are packaging and
the answer key, never an input; source class follows the sniffed format; Kaggle now, a
desktop tool later; the old unit counts are a reference and Justin's review of the
differences becomes the fixture; LongMemEval is fall. Question sets are not part of Step 0.
The brief was rewritten to this and the extractor chat opened from it.

## Evening: the extractor chat

Opened from the brief as its own session on branch `claude/step0-raw-dataset` (not merged
to master as of this log). What it built:

- `scripts/unpack_benchmarks.py`: GraphRAG-Bench `novel.json` to 20 text files with the MIT
  LICENSE beside them; LongMemEval `_s` to one JSON per distinct non-empty session (session
  id, `dates`, turns as role and content; `has_answer` dropped). Its dedupe key, asked for
  and answered: session id over non-empty slots. 25,112 slots, 1,230 empty, 19,829 distinct
  ids of which 623 only ever appear empty, so 19,206 session files; 18,474 distinct by
  role-and-content hash. The session files are gitignored; the folder and manifest are not.
- `data/raw/`: chinese/ and the Thebaid removed; manifests regenerated for greek/ and the two
  unpacked folders; `scripts/papers_manifest.py` writes the manifest for the 142 PDFs.
- Kaggle: `it494-narrative-corpora-raw` republished from `data/raw/` and a private
  `it494-reference-papers` holding the PDFs; both are the notebook's inputs.
- `notebooks/factledger-extractor.ipynb`, the Kaggle notebook `jhffmn/factledger-extractor`,
  nine blocks built one at a time across some thirty-five commits: inputs and sha256 check,
  file kind and raw text (PyMuPDF for PDF, `role: content` rendering for chats with turn
  spans kept), the model call, the split call over overlapping 14,000-character chunks, the
  quote locator, the cutter, a resumable corpus run with a per-document log, a replay block,
  and the schema export with a receipt.

Its two findings and the rulings on them, mid-evening: (a) a reused LongMemEval session
keeps every date it was assigned, as a `dates` list in first-seen order; one date fills the
document's `occurred_at` (15,262 sessions), several leave it null and flag the document
ambiguous (3,944). Splitting a session per date was rejected: identical text duplicated,
and the date is question data anyway. (b) **Units carry a time range**, `occurred_at` to
`occurred_until`, filled only when the file carries times; a unit never spans a day change;
a fact's time is the date its text states, else its unit's, else its document's, else null.
Facts were always meant to have dates; novels hid that, chats bring it back. Unknown dates
are null and flagged, never inferred from prose and never filled from ingestion time.

## Late evening: an outside design review

A review Justin brought in raised six points; five held against the files and one partly,
verified line by line before anything changed. Rulings: (A) **voice lives on the piece.**
The split plan is the piece table (kind, range, unit, `author` when the file names a
speaker, time when it carries one); a fact's voice at read time is its piece's author, else
the document's; one word, `author`, at every level, no `speaker`. Turn-as-unit was weighed
and declined: 246,930 units and 740,000 derive calls against 19,000 and 57,000, and the
exchange context lost. (B) **Minor entities stay mentions** inside their document, `node_id`
null, never merged: a minor is minor because the text gave too little to disambiguate it,
and hundreds per work make a global merge on no evidence not worth its cost. A
minor-to-minor fact is not stored. (C) Two instruments added: the long-tail count of
surfaces recurring across N documents with no node, and gold-pair candidate recall before
merge precision and recall. (D) plan.md corrected: the resolution ablation is the
benchmark's fourth arm, and the combined-store estimate (4,000 to 5,000 units) is
superseded by the 09-04 counts, roughly 21,000 to 24,000 units and 35 million words.

The living docs were corrected to all of the day's rulings in three commits (README.md,
SCHEMA.md, BUILD.md, RESEARCH.md, docs/proposal.md, docs/evaluation-corpus.md,
docs/entity-resolution.md, data/raw/SOURCES.md, USAGE.md, WANTLIST.md, log/2026-09-03/plan.md):
87 verified edits from a sweep of every living markdown file, each checked against the
rulings by a second reader, then the schema changes above. Dated logs and the paper
one-pagers were left as historical record.

## Past midnight: review of the extractor notebook

Justin asked for a review of `factledger-extractor` ("this is getting all kinds of ugly").
The run output was not reachable from outside his editor session, so the review is of the
code on the branch (667 lines, nine cells) and its commit history. Findings, ranked:

1. **Matching by quote is the mess, and it is concentrated.** The model quotes lines
   verbatim and code searches for them; fifteen of the thirty-odd commits are that fight
   (case folding, multi-line quotes within a 100-character window, first-line and last-line
   fallbacks, "owns its line", closing punctuation for run-in headings, a skip span for the
   contents list, chunk-scoped search, feedback retries). About 150 lines, and every new
   document kind adds a rule. The brief's "verbatim strings, whitespace-forgiving match"
   invited it; the chat's switch from a compressed view to raw slices made it unbounded.
2. **Cost.** One call per 14,000 characters, doubled on retry: over a hundred calls for one
   Oz book, thousands for the corpus, against the brief's one call per document.
3. **Units.** For texts every piece was a unit and the size rule sat in the prompt ("aim for
   pieces under 4,000 words"); chats were grouped in code. The ruling is one grouping
   function for every kind.
4. **Gates.** None of the three existed; the only flag was a missing quote.
5. **Export.** `split_plans.jsonl` was a debugging dump, not the piece table.
6. **Not ruled.** Undated pieces inheriting the previous stated date; a dedupe sentence
   hardcoded into the receipt.

Kept as good: the integrity check, the byte sniffing and chat rendering with turn spans, the
resumable per-document log, the ambiguous-date handling, the receipt fields.

**The proposed fix, delivered as blocks 3 to 9** ([factledger_blocks_3_to_9.py](factledger_blocks_3_to_9.py),
390 lines for the range that was 560; blocks 1 and 2 unchanged): code builds the candidate
list and the model only chooses. The text is read as blocks between blank lines; a block of
at most three short lines is a candidate (a chapter heading, a two-line heading, a scene
marker), a longer block is prose; the first 200 and last 60 lines are candidates regardless;
a one-line book is cut into sentences and the short ones of two or more words are
candidates. One call per document. Every pointer is an index plus the line's text, checked
and recovered from the five neighbors when they disagree; the three gates are real (count
against the contents list, no piece over 60 percent of the body, every pointer resolved);
one retry on Terra keeps the answer with fewer flags; over 2,500 candidates means fixed
windows and a flag. One `units_from` for every kind, with the day cut and the tail merge.
Export adds `pieces.jsonl`, the piece table. The receipt counts index mismatches,
recoveries, and unresolved pointers, which is the number that says whether index selection
holds. Offline smoke on the real files with fake answers, every fifth index off by one:

| document | candidates | characters sent |
|---|---|---|
| Oz 1 | 999 | 65,643 |
| Hesiod anthology (greek 03) | 1,090 | 63,386 |
| Apollodorus scan (greek 27) | 2,106 | 76,188 |
| GraphRAG one-line text | 1,004 | 46,249 |

Oz 1: 22 pieces, all five bad indexes recovered from their text, no flags, 11 units of
3,100 to 3,700 words. A LongMemEval session: one dated unit, both authors on its pieces. A
synthetic two-day chat split at the day change. The model path is untested until it runs on
Kaggle. Provisional numbers in the file, Justin's to rule: `SHORT` 80 characters,
`BLOCK_LINES` 3, `HEAD`/`TAIL` 200/60, `MAX_CANDIDATES` 2,500, `CAP_WORDS` 4,000,
`TAIL_FLOOR` 1,333. The builder chat, meanwhile, kept patching the quote matcher (its last
commits: words matched in order across any whitespace, answers of the wrong shape caught,
the end-matter answer read as a number); Justin opened a fresh chat to carry the rewrite.

## Open

- The unit cap and the tail floor: 4,000 and 1,333 words as written in the delivered blocks,
  to be ruled after the first full run.
- The candidate rule (blocks of at most three short lines, the head and tail lines, sentence
  mode for one-line documents) and its numbers, to be ruled on the same run.
- Cells for entities promoted to document-major after being unit-minor: accept the missing
  cells, or one extra cells call per promoted entity over the units it lacked.
- From 09-03, still to rule: the set node, the vector table inside SQLite instead of a
  sidecar, raw bytes as a blob table.

## Still not done

- Apply blocks 3 to 9 to the notebook, run the whole dataset, and put the receipt and the
  per-document log in the next day's folder; Justin reviews the unit-count differences
  against the old splitter and his rulings become the fixture.
- Merge `claude/step0-raw-dataset` into master. Until then master's `data/raw/` still holds
  chinese/ and the Thebaid, and master has no copy of the extractor notebook or the unpack
  scripts.
- The ingestion notebook's loader still reads unit text; it must read ranges before the
  ingestor chat opens.
- Fang endorsement email (draft in the 09-02 session; add the repository link).
- Say the names to Fang: Palimpsest (paper, architecture), FactLedger (tool).
- Repository visibility: still private unless changed in the GitHub UI.
