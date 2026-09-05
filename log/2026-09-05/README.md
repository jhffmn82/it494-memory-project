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
- A second, smaller pass over the batch (four lenses, one reproducing refuter per finding)
  was running when this was written; its result goes below when it lands.

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

## Open

- Luna's context window against the 13 documents over 200k listing tokens.
- The docs patch: correct and apply, then `SCHEMA.md` and `BUILD.md` match the code.
- The second verification pass (pending).
- The first full run of the new design, and its receipt against the old run's numbers.
- From 09-04, unchanged: cells for entities promoted after being unit-minor; the set node;
  the vector table inside SQLite; raw bytes as a blob table.

## Still not done (carried from 09-04)

- Fang endorsement email; the names to Fang (Palimpsest, FactLedger); repository visibility.
