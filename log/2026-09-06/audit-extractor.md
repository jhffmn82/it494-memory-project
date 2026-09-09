# Audit of the extractor, 2026-09-06

The artefact audited is the notebook as **saved on Kaggle** (`jhffmn/threadatlas-extractor`,
loader `threadatlas-extractor 0.9`), pulled with the Kaggle CLI and committed here as
`notebooks/threadatlas-extractor.{py,ipynb}`. It was ahead of the branch, whose last commit
(`91df457`) is 0.7. Every finding below was produced by running code against the real corpus
mirrored in `data/raw`, not by reading alone; the harnesses are named per finding.

## What is right

Worth saying first, because most of it is.

- **The design is the right one.** Code numbers the lines, the model points by number and
  copies the line, code checks the copy against the line and recovers from the neighbours.
  That replaced fifteen commits of quote-matching fallbacks with one verifiable contract.
- **Pieces tile.** Over 3,000 real LongMemEval sessions: zero gaps, zero bad ends, kinds
  `front_matter`, `user`, `assistant` throughout. `split()` asserts the same for text and PDF
  on every document.
- **The merge and group repairs from the 09-05 reviews hold.** Reproduced directly: two
  adjacent short pieces pointing at each other merge once and tile; a join across a region
  boundary is refused and flagged; a grouping with a gap or an overlap is caught and degraded
  to one unit per piece with a flag.
- **Records match the schema** field for field, with one exception noted below. `unit` and
  `piece` are exact.
- **The date discipline is real.** `date_ok` requires the year on the line, accepts Roman
  numerals on a title page, and drops an ungrounded month or day. A chat takes the earliest
  of its several dates, consistently in blocks 7 and 9.

## Findings

### 1. BLOCKER: chat units are one per turn, reversing the ruling and the schema

`chat_runs()` in 0.9 returns one unit per turn (the header joined to the first). SCHEMA.md
says a unit is "size-bounded runs of pieces, cut only at piece boundaries, **never a lone
turn**, never across a day change"; BUILD.md says the same. The 0.7 version implemented that
and was replaced in 0.8.

It also contradicts the extractor thread's **own** unapplied docs patch in this folder, which
says "A chat unit is a run of at least two turns under the cap". So the code diverged from
both the standing schema and the change the thread was proposing.

Measured over 3,000 real sessions and scaled to the 19,206 (`audit/check_chat.py`):

| | units | single-piece units | median unit | units under 100 words | derive calls at 3 per unit |
|---|---|---|---|---|---|
| 0.9, one per turn | 198,961 | 90% | 76 words | 106,913 | 596,884 |
| 0.7 and the schema | 19,206 | few | ~1,700 words | few | 57,618 |

The text path spends three model calls per document (sub-split, merge, group) to avoid pieces
under 100 words. The chat path then emits 106,913 units below that same threshold.

The author problem this was presumably meant to solve is already solved by the piece table:
each turn is a piece carrying its own `author`, and a fact's voice is the author of the piece
holding its quote. Grouping turns costs nothing in voice fidelity and keeps the exchange
together, which a single turn ("yes, the second one") loses.

**Fix:** restore the 0.7 `chat_runs(pieces, text)`: runs of at least two turns, under the cap,
never across a day change, short tail merged back. It is thirteen lines and is in
`git show 91df457:notebooks/threadatlas-extractor.py`.

### 2. MAJOR: two of the three offline test batteries no longer run

`test_review.py` and `test_verify.py` both crash on `chat_runs() takes 1 positional argument
but 2 were given`. `test_run1.py` passes 24 of 26. The check that crashes in `test_review.py`
is, by its own heading, "chat_runs: header never alone, **never a lone turn**": the guard for
finding 1 was orphaned by the change it should have caught.

The 09-05 log's "91 in three batteries, all passing" is stale. The current state is:

| battery | checks | result |
|---|---|---|
| test_review.py | 40 | crashes |
| test_verify.py | 25 | crashes |
| test_run1.py | 26 | 24 pass |
| test_run2.py | 40 | 40 pass |
| test_diag.py | 22 | 22 pass |

**Fix:** with finding 1 reverted, the two call sites work again. The two stale expectations in
`test_run1.py` are superseded behaviour, not defects: the mid-line copy now resolves through
`find_text` by design, and the over-cap merge message was reworded. Re-baseline both.

### 3. MAJOR: the final run cannot finish under the spending stop

`SPEND_STOP` is $8.00. There are 231 text and PDF documents; chats cost nothing. The first run
of the new design reached 87 documents for $7.71, which is $0.089 a document, so the whole read
corpus is about **$20.50**. The 0.6 and 0.9 patches cut per-document cost (coverage fires only
with a contents list, metadata flags buy no retry), so the true figure is lower, but not by a
factor of two and a half.

For reference, one main call per document over the whole text corpus is 12.1M input tokens,
$2.42 at Luna's input price; the rest is retries, sub-splits, merges and groups.

**Fix:** raise `SPEND_STOP` for the final run to $25 and let it finish in one session, or leave
it at $8 and accept three sessions with the resume doing its job. My recommendation is $25 with
the run watched, because the resume path is the least-tested code in the notebook.

### 4. MINOR: `flags` on the document record is not in the schema

`documents.jsonl` carries a `flags` array. SCHEMA.md does not define it and BUILD.md says a
loader "may not add fields". The field is genuinely useful: the ingestor should know a
document's split was flagged before it derives from it.

**Fix, one of:** declare `flags` on the document record in SCHEMA.md (my recommendation), or
carry it only in the receipt and the piece table.

### 5. MINOR: a piece with no unit silently joins unit 0

Block 9 writes `ids[p.get("unit", 0)]`. `units_from_runs` sets `unit` on every piece it groups,
and `group()` verifies coverage, so this should never fire; if it ever does, the piece attaches
to the first unit of the document rather than failing.

**Fix:** `ids[p["unit"]]`, so a defect upstream raises instead of mislabelling.

## Verdict

The extractor is sound and close to final. One blocker, and it is a thirteen-line revert of a
change that was never ruled. With findings 1 to 3 applied, it is ready for the full run.
