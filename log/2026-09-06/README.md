# Working log: 2026-09-06

Audit day. The extractor was finished and saved on Kaggle at loader 0.9; this session audited
it, applied the findings, cut the code back, and then chased three defects the real runs
exposed. Six versions, 1.0 through 1.4. Decisions are Justin's; the code is his to run.

Files here: [audit.md](audit.md), the audit against the saved 0.9 notebook;
[final-run-changes.md](final-run-changes.md), what changed and why, updated as each version
landed; [ingestor-brief.md](ingestor-brief.md), the opening message for the ingestor chat.
The offline batteries and `py_to_ipynb.py` stay in `log/2026-09-05/`, where they were written.

## The audit

The artefact was the notebook **as saved on Kaggle**, which was ahead of the branch: the branch
tip was 0.7 and Kaggle held 0.9. Pulled with the CLI, committed, and audited against SCHEMA.md,
BUILD.md and the rulings. Everything below was produced by running code against the real corpus,
not by reading.

What was right, and worth saying first: the design. Code numbers the lines, the model points by
number and copies the line, code checks the copy and recovers from the neighbours. That replaced
fifteen commits of quote-matching fallbacks with one verifiable contract. Pieces tile with zero
gaps over 3,000 real LongMemEval sessions. The merge and group repairs from the 09-05 reviews
hold against the mutual-point, cross-region, gap and overlap cases. The exported `unit` and
`piece` records match the schema field for field.

One blocker and four smaller findings:

- **Chat units had become one per turn** in 0.8, reversing the 09-04 ruling, contradicting the
  SCHEMA.md sentence that forbids a lone turn, and contradicting the docs patch the same thread
  had drafted, which says "a run of at least two turns". Measured over 3,000 sessions and scaled
  to 19,206: **198,961 units against 19,206**, 90% of them a single turn, median 76 words,
  106,913 below the hundred-word floor the text path spends three model calls to avoid, and
  596,884 downstream derive calls against 57,618. The author problem that grouping used to raise
  was already solved by the piece table, so grouping costs nothing in voice fidelity.
- **Two of the five offline batteries no longer ran**, crashing on the `chat_runs` signature.
  The check that crashed is titled "never a lone turn": the guard for the blocker was orphaned
  by the change it should have caught.
- **The run could not finish** under an $8 stop: 231 text and PDF documents at the first run's
  $0.089 each is about $20.50.
- `flags` on the document record is not in SCHEMA.md, which BUILD.md forbids a loader to add.
  Still PROPOSED, unapplied.
- `ids[p.get("unit", 0)]` silently attached an ungrouped piece to unit 0.

## 1.0, the audit applied

Grouped chat units restored, the spending stop raised to $25, `ids[p["unit"]]`. Measured after:
19,206 chat units, zero tiling defects, six lone-turn units (sessions with one turn in total),
one over-cap unit (a single long turn), median 1,704 words.

Re-baselining the batteries surfaced **six checks that had been failing unnoticed** while two of
them crashed, so 0.8 and 0.9 changed behaviour nothing was watching: the count gate became
one-sided, the resume began redoing older-loader records, a five-word copy started matching
anywhere in its line, and a flag was reworded. All six were stale expectations, not defects.
All five batteries passed together for the first time since 0.7.

## 1.1, the accretions cut

Justin: "things like merge words don't make any sense. It's just supposed to make an AI call.
There are lots of silly things that were added to the code as that chat tried to fix things."
164 lines deleted, 98 rewritten. The pattern was one thing: the code had accumulated **guesses
about what the model might get wrong, and each guess was a branch**.

Deleted: `MERGE_WORDS`, a nine-entry synonym table guessing at wording the prompt already names
(three words; anything else is now counted and named in the flag). `roman()` and `year_on()`, a
hand-rolled numeral parser rescuing four title pages, three of them for the edition date the
prompt says not to keep; the cost is one document, an 1879 George Eliot edition, which now has
no date and is counted unknown. `find_text()`, a second way to find a copy anywhere. The
union-find in `merge_short`, since joins are only ever between neighbours, so a boolean per gap
and one sweep does it. Plus a one-line helper used once, one of two source-class constants, the
receipt totals that were the sum of their own halves, and the per-folder manifest key table.

Fixed rather than deleted: `verify_meta` and `subsplit` each called a counting function and then
un-counted it, which is how you get a receipt nobody can trust; both now count into a scratch
dict. `ADVISORY` was nine string prefixes answering two different questions; a flag's kind is now
the word before its colon, and the two flags that report a malformed answer say so in their kind.
`addrs.index()` scanned the address list once per piece; an index map is built once.

Kept after testing showed they earn their place: the multi-line join in `resolve` and two label
rules in merging. Cutting the join broke six checks.

## 1.2, the regression the run caught

Justin, from a real run: "still getting misses on the text matching." Deleting `find_text` in 1.1
was wrong. I had tested it against a probe that happened to start at a line boundary. The break
pointer that failed was a sentence that **begins mid line and wraps**:

```
day, so we made our way back to Baker Street.  It was not till after
dinner that Holmes reverted to the subject.
```

No line-by-line check can see that, and the piece stayed unsplit at 3,717 words. Fixed in the
resolver rather than by restoring the duplicate: a copy of five words or more that **begins
inside** a line and wraps onward names that line, and when the index is too far wrong for the
window (his was off by 3,357 lines) the text is searched once, whitespace-flexibly, and a copy
appearing exactly once places the boundary. My first attempt omitted the begins-inside condition
and matched sentences starting two lines later; a test caught it. Checked against regressions:
400 exact line copies from each of three real files all resolve at their own line.

## 1.3, faster, and one kind per unit

**Speed.** Sub-splits of a document now go out together (`FANOUT` 8) and documents run
`DOCUMENTS` at a time. A big book's twenty to thirty sub-split calls had been serial.

One hazard found and fixed before it could bite: a thread pool queues all its work immediately,
so when the spend stop tripped, every remaining document would still have been read and written
as a flagged record, filling the run log with thousands. The stop is now a flag every queued task
checks.

**One kind per unit**, Justin's ruling: "the merge should never merge two units of different
types." It was happening in grouping, not merging, and the prompt invited it by asking for "a
play with the notes that follow it". Unit 1 of Euripides volume I held a body piece and a notes
piece. That clause is gone and code now cuts any group where the kind changes and flags it, the
same way merging already refused a cross-kind join.

**The misses diagnosed** against the files rather than guessed. Of twelve unresolved pointers,
five are short copies naming an ambiguous line (`MR.` matches eleven lines exactly, `BOOK XIX.`
is a running page header) and seven are text the model rewrote rather than copied: it repairs OCR
as it copies (`Ma- cedon` to `Macedon`) and drops inline footnote markers
(`[_Enter a Messenger_.[29]]` to `[_Enter a Messenger_.]`). Searched flexibly across line breaks,
those seven appear zero times in the file. No matcher finds a string the file does not contain;
that is the quote gate working, and both classes stay counted.

## 1.4, the cost defects

Justin ran out of credits mid-run: "fix it, this is getting expensive." Three defects, all in the
run rather than the design.

1. **It did not stop when the credits ran out.** A 429 saying the account was out of credits was
   handled as a rate limit: three attempts, 45 seconds of sleeps, an error, then on to the next
   document to do it again. It was walking the whole remaining corpus that way. Out of credits,
   401 and 403 now raise `SpendStop`; only a genuine busy signal is retried.
2. **Per-document cost was wrong**, my regression from parallelism. It was measured as session
   spend before and after the document, which counts every other thread. Diodorus reporting $1.55
   is not real, and documents that spent nothing reported $0.12. Calls now carry the document they
   belong to, including those the sub-split threads make.
3. **The loader bump re-billed the whole corpus.** Every book appears twice in that run's log,
   once at the old loader and once at the new, because the resume redid every record an older
   loader wrote. Right in principle, ruinous at roughly twenty dollars a pass. Now the `REDO_ALL`
   switch, **off by default**: a settled record from an older loader is kept, and block 8 prints
   how many.

154 checks pass across the five batteries.

## The finished run, analysed

Justin ran the whole corpus and downloaded `splits.jsonl` and the run log from the session.
Kaggle attaches `/kaggle/working` to a version only for Save & Run All, so a Quick Save kept
the code and the cell outputs but no files; the records came out of the session by hand. Kept
here: [run-read-documents.jsonl](run-read-documents.jsonl), the final record for each of the
231 text and PDF documents, and [run-chat-summary.json](run-chat-summary.json), because the
19,206 chat records are uniform and eighty-five megabytes.

**Every document completed.** 19,437 files, no run errors, and the pieces tile every one of
them with zero gaps. 24,170 units, 4,964 read and 19,206 chat. Of 4,014 flagged documents,
3,944 are the advisory note that a benchmark session carries several dates, leaving 70 real
flags: 40 merging, 21 pointers, 11 metadata, 9 shape, 8 merging answer, 6 over cap, 5
grouping, 3 count.

**It was four passes, not one.** The append order shows 88 documents at 1.0, 134 at 1.3, then
19,344 at 1.4, then a full pass of all 19,437 that wrote the final records. That last pass was
the older notebook: **1.1 and 1.2 both shipped under the `1.0` loader label**, because the
label was only bumped at 1.3. Running the older build after the newer one meant every 1.4
record looked like another loader's work, so the whole corpus was asked again, serially,
because parallelism only arrived in 1.3. That is the answer to why it went slowly, and most
of what it cost.

| pass | read documents | cost | billing |
|---|---|---|---|
| 1.0, early | 88 | $5.84 | serial, honest |
| 1.3 | 134 | $29.64 reported | parallel with the broken per-document billing; the real figure is far lower |
| 1.4 | 138 + all chats | $2.45 | per document, correct: about $0.018 a document |
| final, 1.2 under the 1.0 label | 231 + all chats | $7.64 | serial, honest; median $0.013, most expensive Diodorus at $0.393 |

**Quality of the final pass.** Body share median 77%, none at zero. 270 pointer mismatches of
which 197 recovered, 73 unresolved, 8 duplicates, 12 metadata pointers nulled. Six units over
the cap and 309 under a hundred words. The 43 documents under half body share are the Loeb
scans and the papers, where reference lists and notes are a real share of the file.

**Two defects the run exposed, both fixed in 1.5.**

- **Every chat had a cross-kind unit.** The header piece (front matter) shared the first turn's
  unit, which the one-kind ruling forbids; the rule had been applied to grouping for text and
  PDF but never to chats. The header is now a unit of its own. Verified over 3,000 real
  sessions: no unit mixes a region kind with anything else, and tiling stays exact. It costs
  19,206 more units, one per session, each about eighteen words, which the ingestor skips.
  Speaker roles still share a unit, which is the design.
- **The loader label did not track the code**, as above. Bumped to 1.5 with a note saying why
  it matters.

One record, `papers/hipporag-2024.pdf`, carries a cost of minus $4.90. That cannot come from
the 1.4 code, which sums a document's own calls; it comes from cells re-run out of order, so
the session held a mix of old and new definitions. Worth knowing, not a defect I can reproduce.

**The kind rule works where it ran.** The 138 read documents processed at 1.4 have zero
cross-kind units. The 231 in the final pass have 181, because that pass was 1.2.

## The clean pass, 1.5, Save & Run All

The whole corpus in one pass, one loader, no redo, saved as a version so the working files came
down with it. Kept here: [run15-receipt.json](run15-receipt.json) and
[run15-read-documents.jsonl](run15-read-documents.jsonl), the record for each of the 231 text
and PDF documents. The export itself is 340 MB and stays on Kaggle.

**It is clean.** 19,437 files, no run errors, every record written by `factledger-extractor 1.5`.
19,436 documents exported: the two byte-identical papers collapse to one, which the receipt
names. **$7.72**, median $0.013 a document, most expensive Diodorus at $0.421, and no negative
costs, so the per-document billing holds.

Checked against the schema and the text rather than taken on trust:

| check | result |
|---|---|
| `unit` and `piece` fields, in order | exact |
| unit ids unique, positions 0-based with no gaps | yes |
| every piece points at a real unit | yes |
| pieces tile every document; units tile every document | 0 defects |
| every unit's slice of its document is non-empty, last unit ends at EOF | 19,436 of 19,436 |
| units mixing a region kind with anything else | **0** |

44,262 units and 227,100 pieces. Piece kinds: 100,522 assistant, 99,119 user, 19,567 front
matter, 5,900 body, 1,062 appendix, 642 notes, 209 references, 79 license. Body is 82% of the
48.6 M characters read from text and PDF.

**The kind rule fires on real documents**, not only in tests: two papers report a group cut
where the kind changed, and Apollodorus volume 2 refused 89 cross-region joins on its own.

**The two zero-body regressions are gone.** Metamorphoses I-VII went from 0% body to **91%**,
and the Loeb Apollodorus volume 1 from 0% to **90%**. No document is at zero now, and the
median is 79%. The 39 below half are the Loeb scans and the papers, where notes, references
and appendices are genuinely most of the file.

**Flags**, 4,016 documents, of which 3,944 are the advisory reused-session date note. The
remaining 72: 38 merging, 19 pointers, 9 shape, 8 metadata, 8 merging answer, 7 count, 7
grouping, 6 over cap, 4 author-is-a-publication. Pointers: 370 mismatches, 291 recovered, 79
unresolved, 4 duplicates, 8 metadata pointers nulled.

**The unresolved pointers are the classes already diagnosed**, unchanged and expected: short
copies naming an ambiguous line (`CHORUS.`, `BOOK XXXIV.`, `CHAP. II.`, `XVIII.`) and OCR or
Greek text the model repaired as it copied. Nothing in the matcher reaches either.

**Metadata came off the page even where the file has no Author line.** The Archive.org scans
resolved to Apollodorus, Ovid and Diodorus Siculus with their titles; a GraphRAG text with no
byline resolved to its publisher, flagged as a publication. `unknown_author` is 0. 52 read
documents carry no date, which is the no-inferred-dates rule doing its job on Gutenberg files
whose preamble gives only a release date.

## Published, with its documentation

The clean pass is a public Kaggle dataset:
[FactLedger Step 0: Documents, Units, Pieces](https://www.kaggle.com/datasets/jhffmn/it494-factledger-step0),
MIT, 312 MB, ten files. It is what the ingestor reads and what a reader of the paper can check.

**The reference papers are the one thing held back.** Their publishers' licenses mostly forbid
redistribution, so their 141 document rows go out with a null `text` and the flag
`text withheld: license`, while their 2,328 units and 4,581 pieces go out in full. A tenth file,
`papers.jsonl`, carries each one's source URL, PDF sha256 and byte count, so the text can be
rebuilt with block 1 of the same notebook and the offsets then resolve. Nothing else is
withheld: the literature is public domain and the two benchmark corpora are MIT.

**The documentation is five files, written against the receipt rather than from memory.**
[README](../../dataset/step0/README.md) says what it is and how to slice a unit;
[SCHEMA](../../dataset/step0/SCHEMA.md) gives every field and the guarantees that were actually
checked; [METHOD](../../dataset/step0/METHOD.md) explains the address list, the four calls and
the gates; [PROVENANCE](../../dataset/step0/PROVENANCE.md) gives corpus, source and license;
[LIMITS](../../dataset/step0/LIMITS.md) gives the 72 real flags, the 79 unresolved pointers and
their diagnosis, and four things the dataset does not claim.

**The packer is a repo script, not a one-off.**
[pack_step0_public.py](../../scripts/pack_step0_public.py) takes an export directory and a
staging directory, withholds the paper text, builds `papers.jsonl` from the papers manifest, and
copies the documentation in from `dataset/step0/`, so what is on Kaggle and what is in git are
the same bytes. Re-running it against the same export reproduces all eleven files byte for byte,
which is how the committed script was checked.

Before uploading, the staged files were gated once more on their own: field lists exact, unit
ids unique, positions dense, pieces and units tiling every document, every piece pointing at a
real unit, zero units mixing a region kind, and no paper text present. One number in the earlier
analysis was wrong and is corrected here and in the dataset: 39 read documents are below half
body, not 40.

## Open

- **Turn `REDO_ALL` back to False.** It was on for the clean pass; leaving it on re-bills the
  corpus on the next code change.
- **The old units dataset is now stale.** `it494-narrative-corpora-units` is public, holds the
  hand-rolled splitter's output from 09-01, and shares file names with the new dataset while
  meaning something else. It should be retitled as superseded or unpublished.
- **Re-asking is not reliably better.** In the second pass, Metamorphoses I-VII went from 91% body
  to 0% with everything labelled notes, and Apollodorus volume 2 from 49% to 0%. The region
  answer is the model's, not the code's.
- **The OCR scans** (Diodorus, Apollodorus, Heroides) are where the pointer misses concentrate,
  for the reason above. Nothing in the matcher will fix them.
- `flags` on the document record: declare it in SCHEMA.md or move it out of the export.
- From 09-05: the docs patch to correct and apply; the two identical papers.

## Next

The full run's receipt, once saved, against the old design's numbers. Then the document
ingestor: [ingestor-brief.md](ingestor-brief.md) opens on revisiting the Oz chapter-1 ingestion,
then rebuilds against the schema and tests over books, papers and chats, with the ingested set
as the deliverable rather than the notebook.

## Still not done (carried)

- The branch is not merged, so master has no extractor, no unpack scripts, and no log for the
  4th, 5th or 6th.
- The ingestion notebook's loader still reads unit text; it must read ranges.
- Fang endorsement email; the names to Fang (Palimpsest, FactLedger); repository visibility.
