# Changes made before the final run

**APPLIED 2026-09-06 as `factledger-extractor 1.0`**, from [audit.md](audit.md), and the
notebook regenerated with `py_to_ipynb.py` (round trip exact). All five offline batteries pass
together for the first time since 0.7: 154 checks (`test_review` 40, `test_verify` 25,
`test_run1` 26, `test_run2` 41, `test_diag` 22). What follows is what changed and why; only
the SCHEMA.md edit in 4 is still PROPOSED and unapplied.

Measured after the change, over 3,000 real sessions scaled to the corpus: **19,206 chat units**
(was 198,961), zero tiling defects, six lone-turn units (sessions with one turn in total), one
over-cap unit (a single turn over the cap, which stands alone by design), median unit 1,704
words.

Re-baselining the batteries surfaced something worth recording: **six checks had been failing
unnoticed** because two batteries were crashing on the `chat_runs` signature, so 0.8 and 0.9
changed behaviour that nothing was watching. All six were stale expectations, not defects: the
count gate became one-sided, the resume redoes any record an older loader wrote, a copy of five
words or more now names its line wherever it begins, and the over-cap merge flag was reworded.
Each is now asserted in its new form with the reason in a comment.

## 1. Restore grouped chat units (blocker)

In block 7, put back `day()` and the 0.7 `chat_runs`, and restore `TAIL_FLOOR` beside
`CAP_WORDS` in block 6.

```python
TAIL_FLOOR = CAP_WORDS // 3        # block 6, beside CAP_WORDS


def day(t):                        # block 7
    return (t or "")[:10]


def chat_runs(pieces, text):
    """Runs of piece indices: at least two turns each unless a day changes, under the cap where
    two turns allow it, the short tail merged into the unit before it. Index 0 is the header."""
    runs, run, size = [], [], 0
    for i, q in enumerate(pieces):
        w = words(text, q)
        turns = sum(1 for j in run if j > 0)
        new_day = bool(run) and day(q["occurred_at"]) != day(pieces[run[-1]]["occurred_at"])
        if run and (new_day or (size + w > CAP_WORDS and turns >= 2)):
            runs.append(run)
            run, size = [], 0
        run.append(i)
        size += w
    if run:
        same_day = runs and day(pieces[run[0]]["occurred_at"]) == day(pieces[runs[-1][-1]]["occurred_at"])
        lone = sum(1 for j in run if j > 0) < 2
        if runs and same_day and (size < TAIL_FLOOR or lone):   # a short tail, or a lone turn, joins the unit before it
            runs[-1].extend(run)
        else:
            runs.append(run)
    return runs
```

and in block 8 the call site returns to `runs = chat_runs(pieces, doc["text"])`.

Effect: 19,206 chat units instead of 198,961, none a lone turn, none under the hundred-word
floor the text path enforces. Voice is unaffected: it lives on the piece, and every turn is
still its own piece with its own `author`.

## 2. Re-run the batteries, re-baseline the stale checks

With 1 applied, `test_review.py` and `test_verify.py` run again. In `test_run1.py` two
expectations are superseded and should be updated rather than fixed:

- "a copy that begins mid-line does not resolve": 0.9 resolves it through `find_text`, on
  purpose, and counts it as `by_text`. Expect resolution.
- "a join that would pass the cap is left alone and flagged": the message is now
  `merging: over cap, left alone: ...`. Match the new wording.

All five batteries now pass together: 154 checks.

## 3. Raise the spending stop for the final run

Block 3: `SPEND_STOP = 25.00`. At the first run's observed $0.089 a document, the 231 text and
PDF documents come to about $20.50; the 0.6 and 0.9 patches make it less. The alternative is
three sessions at $8, which exercises the resume path more than it exercises the extractor.

## 4. Declare `flags` on the document record

`documents.jsonl` carries `flags` and SCHEMA.md does not define it, while BUILD.md says a
loader may not add fields. Proposed, for Justin's ruling, in SCHEMA.md's source side:

```
    document  doc_id, source_uri, sha256, title, author, source_class, text,
              ingested_at, occurred_at?, loader, flags
```

with one sentence after the `occurred_at` paragraph: "`flags` records what the loader could not
settle: an unresolved pointer, a failed gate, a date it would not guess. A flagged document is
stored and used, never dropped; the ingestor reads the flags before it derives."

## 5. Fail loudly on a piece with no unit

Block 9: `ids[p.get("unit", 0)]` becomes `ids[p["unit"]]`. A piece that never got a unit is an
upstream defect and should stop the export rather than attach itself to the document's first
unit.

## After applying

`python log/2026-09-05/py_to_ipynb.py` from the repository root regenerates the notebook and
proves the round trip, then the notebook goes to Kaggle and the full run goes with
`SPEND_STOP` at 25. What the receipt should show, to compare against the old design's run:

| | old design, 230 documents | expected |
|---|---|---|
| cost | $5.67 | about $20, all 231 |
| pieces dropped after end matter | 2,514 | 0, pieces tile |
| heading collisions | 1,113 in 204 documents | 0, duplicates counted |
| chat units | not run | 19,206 |
| body share | not comparable | 89% to 97% on Oz and Holmes |
