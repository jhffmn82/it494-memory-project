# Development log: ingestor 0.5, written by the chat

What I did, in order, with the reasoning and the mistakes. Justin's decisions are in
`decisions-ingestor-0.5.md`; this is the work between them. Times are Central.

## Reading the first real run (about 18:00 to 19:00)

The Oz output arrived chapter by chapter and I read it against the design before the judge
finished. Three checks I ran before saying anything: how a fact's subject was matched to the
entity list (an exact string compare, which explained 33 rejections at once), how the roster
was shown (sixty by recency, which explained why chapter XV had no continuations), and the
quote gate against the real text, which I could do offline because the export is local. I
wrote a scratch script that exec'd blocks 4 and 5 of the notebook and ran the 28 rejected
quotes that printed in full: ten failed only for the model's own quotation marks. That gave
me a fix list with evidence rather than guesses, which is what he had asked for after the
09-06 afternoon.

While the judge ran I explained the silence (the judge, then the adjudication: 38 sequential
Terra calls, no progress print) and estimated the wait. The receipt confirmed the shape: 224
Terra calls after 75 Luna ones, and 48 of the Terra calls were retries nobody had logged.

## The paper crash (about 19:00 to 19:40)

All five papers failed instantly with `len(None)`. The export records looked fine locally, so
I reproduced offline with the model stubbed: the paper ran clean. The difference had to be
the data on Kaggle. The dataset listing showed `documents.jsonl` 13.6 MB smaller than the
local export and a `papers.jsonl` I did not have locally, which matched my notes on the
publication split: the public dataset withholds the papers' text by license. PROVENANCE.md
on the dataset said the text was pdfplumber pages joined with form feeds; the extractor's
as-run source said PyMuPDF joined with newlines. I installed PyMuPDF locally, rebuilt all 141
papers from `papers/` with the extractor's function, and compared: byte-identical. Then the
loader learned to rebuild a withheld text, with sha256 and units'-end checks, and the battery
gained three checks, one of which runs the real rebuild. A two-document miniature export with
the Zep row nulled ran end to end.

## The receipt, the retries and the ride-in (about 19:40 to 20:20)

Justin uploaded the receipt and the rejections file. One row: an attribute with a null value
rejected twice. The other 31 adjudication retries had recovered and left no trace, so I added
`retries.jsonl` and let attributes carry null. He then ruled twice on the 373 discarded
minor-subject facts: discard, then ride them into the tied major. I built `landings`, one
function that decides where every fact lands, and made both the package writer and the
adjudication read it, so the two could never disagree about which facts a major owns. The
riding facts needed ids of their own because one minor can ride into two majors; I hashed the
original id with the major's name and first unit and kept `rides_on` in the provenance.

## The four stages (about 20:20 to 21:00)

He asked for an updated notebook after a design conversation that had settled predicates,
the rolling reconciliation and the both-named rule. Rather than one large rewrite I built it
in four commits, each with the battery green, so every diff stays readable in the history:

- Stage A were the small fixes from the run's reading. Straightforward.
- Stage B replaced block 8. I read the old reconcile, the sidecar functions and the ingest
  loop in full before writing, then wrote the block whole: a `Rolling` state, `unite_on_sight`
  for the both-named unions, `nominate` in his order, `judge_pairs` shared by the per-unit
  step and the end sweep, `replay_rows` so a resumed run applies checkpointed verdicts without
  a judge, and `roster_of` building the model's roster from the clusters. Three battery checks
  failed and all three were the battery's fault, not the code's: its scripted entities were
  all named persons, so nothing reached the judge under the new rule; its stop-at test counted
  unit positions from zero while triage drops the front matter. I changed the script, not the
  design.
- Stage C took the predicate list out of the fact prompt and added the post-adjudication
  judge, with `predicate_raw` kept so nothing is lost. The battery's scripted adjudication
  had to return a spread of predicates that grows with the fact count, capped under one
  judge slice, for the merge check to be meaningful.
- Stage D put the entity abstracts and adjudications on a thread pool. I left the judge
  sequential on purpose.

One slip: my block 8 replacement left two blank lines before a cell marker and the notebook
generator's round trip reported a difference; the committed `.ipynb` was correct, the `.py`
was normalised in the next commit. Another: I had listed "the entity prompt re-lists an
established entity" among the queued diffs and forgot it in stage A; it went in as its own
commit before the review.

## Review, efficiency, roll-up (about 21:00 onward)

I launched a six-lens adversarial review of the diff (rolling logic, threads, landings,
predicates, the gate, the design as ruled), one refuter per finding, and worked while it ran:
the efficiency levers (he took "nothing to fold, no call", declined documents in parallel),
then the roll-up and the graph. For the graph I read the 09-02 demo's closing cells and
reused its drawing code line for line, since he said to do what the last version did. I
verified the roll-up and the PNG offline on a scripted Oz book 2 package and looked at the
image before committing.

## What I would watch in the next run

The `rolling:` line per chapter, whether Dorothy now appears in every unit she acts in, how
many judge calls the book takes against the last run's 100, `retries.jsonl` for what the
first misses actually are, and the predicate merges, which are the first thing in this
pipeline that rewrites what the model said.

## The review's findings (about 21:30 to 22:15)

The review returned 30 confirmed findings out of 33, each with a reproduction. Four were
high: the declared continuation resolved by name recency (the Wizard welded to the Land of
Oz), `rides_on` naming the wrong fact, predicate merge chains leaving facts on an absorbed
name, and a blank merge target becoming `related_to`. I grouped the thirty into five fixes
(the rolling block, the gate, the predicate judge, ids and the tying fact, the sidecar) and
wrote them as two patch scripts, then read every anchor line in the current file before
running them, because the stages had moved the code since the review started. The battery
gained nine checks: a predicate chain ending at its last link, a blank target set aside, a
riding fact naming a stored fact of its node, three direct gate checks (whole-word hit, a
matched pair off with the apostrophe kept, a lone apostrophe kept), and a stop inside the
adjudication followed by a resume that repeats no unit, judge, fold or finished adjudication
and counts what was paid. One failing check was the test's own: the sidecar's call count now
includes the triage call. 111 of 111.

What I did not fix, and said so in the decisions log: a stop during the entity abstracts
still loses them (the fold is checkpointed whole), the general gate has no whole-word rule,
and the ambiguous-subject path is verified by the review's reproduction rather than the
battery. The refuted three I left alone.

## Closing

The notebook posted to Justin is the last commit of 2026-09-06 on the branch; the decisions log
is `decisions-ingestor-0.5.md`, the review's record `review-findings-4.json`, both in this
folder, and the branch is pushed to the project's GitHub.
