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

## Open

- **`REDO_ALL` for one run.** With the switch off, clean documents from earlier passes keep any
  mixed-kind units they still contain. Turning it on for a single run applies the kind rule
  everywhere, at the cost of a full re-ask. Justin's call.
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
