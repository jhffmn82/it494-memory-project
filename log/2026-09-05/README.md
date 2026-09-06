# Working log: 2026-09-05

PC session, from about 01:20, after the browser chat building the extractor lost the thread.
Picked the notebook up from the repository, found the wrong turn, rebuilt it under the rulings
below, analysed the first full run of the old design, reviewed the rebuilt notebook with two
adversarial passes, and applied the fixes. Decisions are Justin's; open items are marked.

## Where it started

- The committed notebook at `e5a04c6` (01:20) was the chunk-and-quote design: the text cut
  into overlapping 14,000-character chunks, the model quoting heading lines, code searching
  for the quotes in the text. Twenty commits between 22:51 and 01:20 each added one more
  matching fallback (whitespace, word-by-word, first line then last, opening words, loose
  word overlap between located neighbours). A second bad call sat on top: chunking meant no
  call could see the whole outline, which forced a separate review call to repair it.
- The chat's own fix existed and was never adopted: `factledger_blocks_3_to_9.py` (00:28 in
  Downloads) numbered candidate lines and had the model answer by number. Eight more commits
  patched the old design after it was written.
- The first full run of the old design was saved as Kaggle version 347497951 (230 documents,
  $5.67; its log and records are in this folder as `old-design-run.*`). What it showed:
  - "End matter" was treated as terminal and everything after it dropped: six Greek documents
    kept 5% to 31% of their file (the first footnote block after Book VIII taken as the end
    of Metamorphoses vol. 2, seven books gone), 2,514 pieces dropped in all, every paper's
    appendices gone (Yang 2026: seven sections, 40% of the file, found by the model and cut
    by the code). The Yellow Knight's 14 dropped pieces were the license's own headings.
  - Two different quoted headings resolved to the same line in 204 of 230 documents (1,113
    collisions): a heading silently lost and the count silently repaired, each time.
  - Over-splitting: Bulfinch 137 pieces against a contents list of 24, Pausanias 160 against
    5, Diodorus 385 (OCR page headers taken as headings), three papers at 140 to 352.
  - Piece dates lifted from section text and smeared forward (SuperLocalMemory: 22 sections
    dated 2026-08-03); 229 of 3,588 paper pieces given an invented "Chapter N:" label; four
    PDFs with zero tries; the five Archive.org OCR Greek files cost 21% of the run and failed.
  - Oz 29 of 29 and Holmes 9 of 9 came out clean: pieces within one of the contents count,
    body 89% to 97% of the file. They are the regression fixture for the new design.
- The LongMemEval unpack was checked end to end after a worry about the file count: 19,206
  session files is exactly the distinct non-empty session count (25,112 haystack slots, 1,230
  empty, 19,829 ids, 623 only ever empty); every file's turns and dates match the source;
  every sha256 matches the manifest; the manifest's source hash matches the 08-28 download.

## Rulings, in the order given

1. **Text and PDF units are not size-packed runs of chapters.** Reverses ruling 4 of 09-04
   for text and PDF; chat turns still pack. (Later superseded by 5.)
2. **No font sizes and no code deciding where a break may be; the model decides.** Code
   numbers every non-blank line (sentences when the file has none) and shows the whole
   document in one call; the model answers with line numbers and the line's text; code checks
   the number against the text and counts mismatch, recovered, unresolved, duplicate. This
   replaces the 09-04 compressed view of short lines, which showed a PDF none of its section
   headings (pymupdf puts no blank line between a heading and its paragraph).
3. **Keep every byte; boundaries are labels, not cuts.** Regions `front_matter`, `body`,
   `notes`, `references`, `appendix`, `license` are values in the piece's `kind`, not a
   schema change. Pieces tile the document from first byte to last. A wrong boundary is a
   mislabel, fixable by relabeling one row, not a loss.
4. Sentences are the address unit for the 20 newline-free GraphRAG-Bench files.
5. **Units are the model's too.** A piece over 4,000 words is split by the model inside
   itself, recursively; then the outline goes back to the model, which groups a piece with
   the pieces under it (a section with its subsections, a play with its notes), never two
   peers. A group over the cap is dissolved and flagged.
6. **No dates on text or PDF pieces** (restating `bbad89e`); a text or PDF unit carries the
   document's date; the date asked for is the original work's, never this edition's,
   translation's, or transcription's.
7. **No inferred dates.** A document whose file states no date stays null (Bulfinch, The
   Valley of Fear); the receipt counts them.
8. The chat header block 2 writes is a `front_matter` piece, so chats tile too.
9. A `source` pointer (a publication or organization the text names, never the transcriber)
   becomes the document's author when no person is named, flagged. Title and author carry a
   rendered `title` and `name` beside the pointer (the Pausanias file's own Author line reads
   "active approximately 150-175 Pausanias").
10. The docs are drafted for Justin to correct: `docs-rulings-2026-09-05.patch` in this
    folder, against SCHEMA.md and BUILD.md, not applied.
11. **Retry on a flag: Luna again; Terra only for a document under 80,000 listing tokens.**
    Terra on every flagged document was estimated at $10 to $18 against the $8 stop.
12. The review's twelve mechanical fixes applied as one batch (below).

## What was built

`notebooks/factledger-extractor.py` (script form, `# %%` cells) and `.ipynb` regenerated from
it; the two round-trip to identical bytes. Blocks 1 and 2 are the committed code unchanged,
except that block 2 imports `fitz as pymupdf` when the image's PyMuPDF predates the new name
(Kaggle's does). Blocks 3 to 9:

- 3: the model call; `TooLong` on a context-length 400; `SpendStop` at the stop; a client
  timeout counted as spent input; an unattached secret is a one-line message.
- 4: every non-blank line numbered; sentences for a one-string file.
- 5: one call per document; regions and pieces by line number; title, author, source, date
  as pointers with a rendered value; `toc_count`.
- 6: `resolve` (exact, the line's first eight words, or a prefix of five words or more;
  nearest-first recovery; an empty copy verifies nothing); `verify_meta` for the four document
  pointers, the date's year required on its line; pieces from region and piece starts, tiling
  asserted; gates: body present, headed pieces against the contents count, coverage, pointers
  resolved, region kinds known, first region at line 0; `split` with the retry policy and the
  best answer ranked by body-present then fewest flags.
- 7: `subsplit` (recursive, three rounds, one more ask when no break resolved); `group` with
  coverage and cap checks; chat pieces and runs (at least two turns per unit, never across a
  day change, short tail merged).
- 8: every document, resumable by file name before reading; the spend stop ends the loop
  without writing the document in flight; over-cap leftovers and new unresolved breaks flagged;
  `manifest.json` excluded from the chat glob.
- 9: export in the schema, files read 32 at a time, `source_class` validated, receipt cost
  over every record, `unit_id` unique for identical slices; `chars_by_kind` and `body_share`.

Offline checks with a stubbed model (no network), `test_review.py` in this folder: Oz with a
canned outline tiles into front matter, body, license with 24 headed chapters against a
contents count of 24; a fake author and date pointer are nulled and flagged; a one-string
novel of 30,000 words is split by the stub recursively into 20 pieces and 13 units, none over
the cap; 2,000 real LongMemEval sessions tile byte for byte; two documents through blocks 8
and 9 with the spend stop firing between them and a resume that skips the finished one by
name. 39 of 39.

Sizes, from the script's own `addresses()` over the local mirror: Oz about 63k tokens a
book, a paper about 20k, 12 documents between 128k and 200k, 13 over 200k (11 Greek,
Snodgrass 1999 at 666k, Weikum 2021). Whether Luna takes the largest in one call is unknown
until the run; a document too long for one call lands as one `whole` piece with a flag.

## Reviews

- A 63-agent review of the rebuilt notebook (seven lenses, two refuters per finding): 77
  findings, 26 confirmed, 2 contested, 0 refuted; consolidated in [review.md](review.md).
  The blockers: the four document-level pointers were never verified (a fabricated author
  and date exported with mismatch 0); the coverage gate skipped a single body piece; the
  LongMemEval manifest went through the model. The cost lens measured the run: Luna over
  everything about $2.12; Terra on every flag $10 to $18.
- The batch applied for those findings: 248 lines in, 131 out, in the script's git diff.
- A second pass over the batch (24 agents: four lenses, one reproducing refuter per finding):
  20 confirmed, 0 refuted, listed in [review.md](review.md). Two were regressions of the
  batch itself: `clean()` stripped a leading "[n] " and a trailing ellipsis from the model's
  copy before comparing it with a line that still had them, so an exact copy of 6,569 corpus
  lines (footnotes, reference-list entries in most papers, short lines ending in "...")
  could no longer resolve. The fix tries the copy as given before the cleaned one; every
  exact copy in the corpus resolves again. The rest: a lone last turn over the tail floor
  stayed its own unit (merged into the unit before it); a region of unknown kind lost its
  boundary (kept under the model's own word, flagged); a non-dict title, author, source or
  date was nulled without a count (counted, and in the receipt); an integer where a list
  belonged was a run error (degrades to a flag); records from the previous notebook carried
  no file name, so the first run after upgrading would have re-billed every clean document
  (the name is derived from the path); the 3,944 multi-date chats were re-read every session
  because their flag can never clear (chats are final); a flagged document was re-asked in
  every session (two sessions, then done); two papers with identical bytes collapsed to one
  record and one was re-asked every session (records keyed by file; identical bytes exported
  once and listed in the receipt); an unreadable file ended the run (a run-error record, the
  loop continues); the spend stop discarded the in-flight document's paid calls (written
  flagged, redone next session); a title page giving the year in Roman numerals (MCMXXI,
  three Greek files) failed the date check (accepted); a verified year let an unverified
  month and day through (kept only when the line shows the month). Applied as
  `factledger-extractor 0.5`; the checks for it are `test_verify.py` in this folder, 25 of
  25, with the first battery still 39 of 39.

## Kaggle

- Kaggle's File > Import Notebook neither replaced the open draft nor created a new one;
  the notebook was rebuilt with cell ids (nbformat 4.5 requires them) and went in on the
  second try. The Kaggle CLI (2.2.4, token from 08-31) is set up on this PC; a push folder
  with the kernel metadata is staged, but `kernels push` is Save & Run All and spends, so it
  was not run.
- The saved draft's secret attachment does not carry over to a fresh draft: `get_secret`
  returned 400 until OPENAI_API_KEY was attached under Add-ons > Secrets.
- A Holmes document (The Adventures, 03_1661) run on the rebuilt notebook before the batch
  showed the cap working (18 sub-splits, parts of 650 to 3,900 words) and one failure the
  batch addresses: four break pointers for The Beryl Coronet did not resolve, and the piece
  stayed whole at 9,686 words with no flag.

## The first run of the new design (afternoon)

Kaggle version 347543245, a Quick Save of the interactive session, so the rendered log was
read from the results page and the working files (`splits.jsonl`, the export) stayed in the
session. It reached 87 of the 231 text and PDF documents (Oz, Holmes, Greek, and most of
GraphRAG-Bench) at $7.71 of the $8 stop; the papers and the chats never ran.

What it showed, with the patch that followed (`factledger-extractor 0.6`):

- **Sub-splitting ran (16 to 36 calls on the big books) and its pointers failed**: 191 break
  pointers matched no line, and 32 pieces stayed over the cap (Holmes' *Return* at 9,213
  words, the Argonautica's Book I at 13,721). The main call points at headings, whole short
  lines, so its copies match; the split call points into wrapped prose, where the model copies
  the sentence that opens the new part, and that sentence runs past the end of its line.
  Patch: a copy may run on into the next two lines; the split prompt says a break is the first
  line of a paragraph; the first six unresolved pointers of a document are kept verbatim in
  its record and printed, so the next run shows what the model actually sent.
- **67 pieces under 20 words**, almost all one of two shapes: an "opening" sliver where the
  body region begins at the title line a few words before `Chapter I`, and a bare `PART I.`
  pointed at separately from the chapter under it. Justin's ruling: every piece under 100
  words is offered to the model, which decides whether it joins the piece before, the piece
  after, or stands alone. Patch: a `merge_short` call per document with those pieces' text; a
  heading that joins what follows keeps its words in the label. A two-line heading is one
  piece, said in the main prompt.
- **Money**: every single-piece play (Alcestis, Medea, the Euripides set) was flagged twice,
  by the coverage gate (one piece holding a body that has no divisions, which sub-splitting
  then handled) and by a title, author or date pointer that failed, and each flag bought two
  more attempts including Terra: $0.10 to $0.13 a play against $0.02. Patch: coverage fires
  only when a contents list says there are divisions; a failed document pointer is nulled and
  flagged but buys no retry. Six of the 87 kept answers came from Terra.
- **Grouping rejoined sub-split parts** (eight dissolves on *His Last Bow* alone). Patch: the
  outline marks parts with the piece they came from and the prompt says they stay apart.
- A heading that is a line of dashes (scene breaks in Novel-58553) takes the next line's words
  as its label.
- Oz and Holmes came out as the fixture expects: pieces at the contents count, body 89% to
  97%, no unresolved main pointers on 26 of 29 Oz books.

A third adversarial pass (19 agents, three lenses, one reproducing refuter each) then found 15
confirmed and 1 refuted against that patch, and two of them were in the new merging code:

- **Merging applied each answer against the list the previous answer had already changed.**
  When two adjacent short pieces pointed at each other (a two-line heading answering "next"
  then "previous", the natural reply), the second merge ran first and the first then reached
  past it and swallowed the following piece, which the model had never named. Merging now
  reads the answers as edges between original pieces, unions the runs, and rebuilds once, so
  the result is the model's answer and nothing else.
- **A merge across a region boundary moved the boundary.** A short piece joining a neighbour
  took the neighbour's kind, so the last body chapter of Oz book 1 came out as `license` and
  426 bytes changed region. The model decides region boundaries in the main call; a
  cross-kind join is now left alone and flagged.
- A merge that would carry a piece past the cap is left alone and flagged; the over-cap check
  now runs after merging rather than before it.
- The retry ranking kept the attempt whose metadata had failed when the retryable flags tied,
  throwing away a paid call's good title and author. Flag count now breaks the tie.
- A metadata-only flag still bought a whole re-ask in the next session; the resume test now
  treats a record with only advisory flags (`metadata:`, `shape:`) as done.
- The coverage check came back for documents with no contents list, as an advisory `shape:`
  flag: visible in the log and the receipt, but it buys no calls. 54 of the 89 local text
  files have no contents line, so without it a missing-pieces answer was invisible for most
  of the corpus.
- `previous`, `before`, `prev`, `next`, `after`, `alone`, `keep` and `none` are all understood,
  case ignored; anything else is counted and flagged.
- Labels: a rule of dashes is recognised by any letter or digit in any script, not ASCII only
  (7 Greek files carry thousands of non-Latin short lines), and the same helper now labels
  sub-split parts, which had kept the rule itself as the label. A two-line heading copied whole
  resolves at its first line.
- Metadata pointers no longer take the six sample slots meant for sub-split breaks.

Offline checks: 91 in three batteries, all passing (`test_review.py` 40, `test_verify.py` 25,
`test_run1.py` 26). `py_to_ipynb.py` in this folder rebuilds the notebook from the script and
verifies the round trip. The next run resumes from `splits.jsonl` if the session kept it; the
87 clean records are skipped by name and the flagged ones get their second try under the new
gates.

## The whole-corpus run, and 0.8 and 0.9 (evening, after the last commit)

Two more builds went in after `91df457`, neither committed to the branch; the Kaggle draft is
where they live and is what was finally saved. Recovered for this log from the Kaggle copy and
from the thread's own test batteries and workflow outputs.

**0.8**, tested by `test_run2.py` (40 checks): a break pointer that names a sentence starting
mid line cuts at the sentence through `find_text`, counted as `by_text`; a wrong index still
resolves when the copy names exactly one line in the document; outcome flags are advisory and
buy no call; the unrecognised merge word is named in its flag. **And chat units became single
turns**, which is finding 1 of the audit below: it was never ruled, it contradicts SCHEMA.md
and the docs patch this same thread drafted, and it orphaned the check that guarded it.

**A whole-corpus run** then went through a seven-lens diagnosis, every flag class root-caused
and ruled (67 verdicts, 23 kept): 12 correct behaviour, 3 real defects, 6 that the pointer fix
already covers, 1 data problem, 1 unclear. What it settled:

- The **count gate was two-sided and should not be**: more headed pieces than the contents
  list is normal (Bulfinch, 32 against 24, is right; the contents list is partial), fewer means
  the model skipped divisions. Made one-sided in 0.9, and 28 count flags mostly disappear.
- The **`shape:` advisory is working**: the Euripides plays that trip it are genuinely one
  undivided body, correctly costing no retry. Bacchae measured 67.5% body against 14.6% notes
  and 14.1% Gutenberg boilerplate, which is the file, not a defect.
- **Two real coverage failures** where the model's own answer was poor, not the code's: the
  Loeb Apollodorus (one piece holding 77% of the body) and Weikum 2021 (95% of 50 pieces).
  Both paid for a retry that did not help. No small fix; the answer is the model's.
- **`no body region` on Novel-26183** (Thayer, *Laurence Sterne in Germany*) with 17 unresolved
  pointers, expected to fall to two to four with the pointer fix but not to clear.
- The 30 over-cap flags and 131 heading-pointer failures are mostly downstream of the pointer
  fix; the estimate was 8 to 10 over-cap left, the residue in the Archive.org scans.

**0.9**, tested by `test_diag.py` (22 checks), fixed the eleven defects that diagnosis
confirmed: a record carries its `loader` and a rerun redoes what an older loader wrote; a
document is addressed by sentence when its lines are one word each (the Snodgrass PDF, whose
text layer breaks every word onto its own line, went from unusable to a listing that fits a
call); the count gate one-sided; four metadata values inside one long address all verify while
an author not on the line is still nulled; a merge is refused for the cap only when the cap is
not already broken; a chat takes the earliest of its dates, sorted, in blocks 7 and 9 alike;
the reused-date counter reads the flag key rather than a prefix; short and over-cap units are
counted by side; a publication becomes the author only when no person was named.

The Kaggle notebook was saved at 0.9 and is now committed here as
`notebooks/factledger-extractor.{py,ipynb}`; the two round-trip to identical code.

## The audit (2026-09-06)

A full audit of the saved 0.9 notebook, run against the real corpus rather than read:
[audit.md](audit.md), with the changes it proposes in
[final-run-changes.md](final-run-changes.md). In short: the design is right and most of it is
sound, with one blocker.

- **Blocker.** Chat units are one per turn. Measured over 3,000 real sessions and scaled:
  198,961 units against 19,206, 90% of them a single turn, median 76 words, 106,913 of them
  under the hundred-word floor the text path spends three model calls to avoid, and 596,884
  downstream derive calls against 57,618. SCHEMA.md forbids a lone turn in the sentence that
  defines the day cut, and the thread's own unapplied docs patch says "a run of at least two
  turns". The author problem that grouping used to raise is already solved by the piece table:
  every turn is its own piece with its own `author`, and a fact's voice is the author of the
  piece holding its quote. Fix: restore the thirteen-line 0.7 `chat_runs`.
- **Major.** Two of the five offline batteries no longer run: `test_review.py` and
  `test_verify.py` crash on the `chat_runs` signature, and the check that crashes is titled
  "never a lone turn". `test_run1.py` is 24 of 26, both stale rather than broken. The log's
  "91 in three batteries, all passing" is stale; with the blocker reverted it is 153 in five.
- **Major.** The run cannot finish under `SPEND_STOP`: 231 text and PDF documents at the first
  run's $0.089 each is about $20.50 against an $8 stop. Raise it to $25 for the final run.
- **Minor.** `flags` on the document record is not in SCHEMA.md, which BUILD.md forbids a
  loader to add. Declare it, or move it out of the export.
- **Minor.** `ids[p.get("unit", 0)]` in block 9 silently attaches an ungrouped piece to unit 0.

Verified as right, by reproduction rather than reading: pieces tile with zero gaps over 3,000
sessions; the merge and group repairs hold against the mutual-point, cross-region, gap and
overlap cases; the exported `unit` and `piece` records match the schema field for field.

## Open


- Luna's context window against the 13 documents over 200k listing tokens (none of the 87
  came back `too long`; the largest so far were the two Diodorus files at about 500k).
- `SPEND_STOP` at $8 stops the corpus at about a third; the rest is the papers (cheap) and
  the chats (free).
- The docs patch: correct and apply, then `SCHEMA.md` and `BUILD.md` match the code. Note
  its chat-unit sentence says "a run of at least two turns", which the 0.9 code does not do.
- The final run, over the whole corpus, with the audit's changes applied and the stop raised.
- The two identical papers (`novelqa-2024.pdf`, `wang2024-novelqa.pdf`): drop one from the
  private dataset, or leave the receipt to note it each run.
- From 09-04, unchanged: cells for entities promoted after being unit-minor; the set node;
  the vector table inside SQLite; raw bytes as a blob table.

## Next

The document ingestor (Step 1). Its brief is [ingestor-brief.md](ingestor-brief.md):
rebuilt against the schema, not ported from the chapter demo, and tested over a sampling of
every source type rather than one book.

## Still not done (carried from 09-04)

- Fang endorsement email; the names to Fang (Palimpsest, FactLedger); repository visibility.
