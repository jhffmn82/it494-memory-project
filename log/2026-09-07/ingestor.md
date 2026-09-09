# Working log: 2026-09-07 (ingestor thread)

The document ingestor from 0.6 to 0.7 and then to the one-reading path, in the same chat and
worktree (`claude/infallible-einstein-e34c97`). The day ran in three parts: an outside audit
answered item by item and twenty-four rulings taken one at a time (`decisions-ingestor-0.7.md`,
`audit-answers.md`); a full paid run over 48 documents that exposed four defects; and a rebuild
of the chat path after the corpus turned out to cost far more than the design assumed. The
battery went from 106 checks to 146. Every ruling is Justin's; the corrections to my own claims
are collected at the end, because several of the numbers I gave during the day were wrong.

The notebook as it ended the day is here as `threadatlas-ingestor-as-run.py` and
`threadatlas-ingestor-as-run.ipynb` (18 cells, round trip identical under
`scripts/py_to_ipynb.py`). The offline battery it must pass is not duplicated here; it stays at
[test_ingestor.py](../2026-09-06/test_ingestor.py), where it is maintained, and runs 146 of 146.

## The abstract gate, and its removal

0.7 opened with the fold wrapped in a fabrication check: an abstract naming anything absent from
its records was rejected, retried once, then left unstamped, and decision 52 then demoted an
entity that had no abstract out of nodehood. On the first Oz run of the day the check read
possessives as names and compared them literally, so "Dorothy's" failed against the records and
"Oz*" failed against the document. Twelve entity abstracts and the document abstract were
rejected; Dorothy, the Scarecrow and the Emerald City ceased to be major entities; salience fell
back to tie-breaks and produced 92 majors; riding exploded to 1,906 copies from 198 source facts.
The run cost $2.97 and was worthless.

Justin's ruling (decision 65): the fold is a summary of the records and the summary stands. One
call, no check, no retry; the only failure left is the model not answering. What survives from 52
is narrower — an entity with nothing at all to summarise is not a major. The rerun produced a
354-word abstract, 46 majors all named in it, Dorothy restored at 123 raw facts consolidated to
46, riding down to 171 copies from 112 sources, and $2.21.

## The 48-document run

Oz book 1, five papers, forty chat sessions, a Greek play and a novel from the GraphRAG
benchmark: 48 documents, 191 units written (137 of them read — the run's own line counts what it
read, triage having set the rest aside), 2,656 calls, **$11.47**, no errors, no schema retries, no
sidecars left in flight.

| | |
|---|---|
| entities | 3,185 (631 major) |
| mentions | 23,963 |
| facts | 5,094 kept, 164 rejected, 4,723 stored |
| consolidated | 1,515 facts, 739 attributes, 10 contradictions |
| unsupported | 1,182 of 4,723 (25%) |

Where the money went, measured from the call log rather than assumed:

| stage | cost | share | scales with |
|---|---:|---:|---|
| adjudicate | $7.12 | 62.1% | majors |
| judge | $1.99 | 17.3% | unit-locals |
| entity_abstract | $0.91 | 7.9% | majors |
| entities + facts + cells | $1.18 | 10.3% | units |
| support | $0.20 | 1.7% | fact-bearing minors |

**Output is 81% of the spend** ($9.26 against $2.21 of input), so nothing on the input side —
prompt caching included — is worth optimising. Two-thirds of the cost follows the number of
majors in a document. That single fact decided the rest of the day.

## Four defects the run exposed

**The pieces match path had no bound.** A quote may skip words with an ellipsis, so its halves
can be found far apart, and nothing stopped the span. Every other path settles under 300
characters — exact tops out at 285, normalised 248, words 177, unwrapped 258 — while pieces ran
to **17,131 characters**, most of an Oz chapter, cited for one fact about the Wicked Witch
melting. The measured distribution has an empty band between 300 and 400, so the cap sits there:
`QUOTE_SPAN_MAX = 400`, refused as `span_too_wide`, touching no other path.

**The support check asked the wrong question of half its facts.** Its prompt opened "things one
document says about {name}", but a fact stated from the side of a lesser thing is filed under the
entity it points *at*, so for those the named entity is the object and the statement is about
something else. Inverse facts were called unsupported at 47% against forward's 24%, and the flags
read wrongly: `the raft is_built_for the travelers` against "The Tin Woodman must build us a
raft, so we can float to the other side" is plainly stated. The check now judges statements one
at a time and names no entity.

**Per-document cost and calls were global deltas.** `len(CALLS)` at the end less `len(CALLS)` at
the start is exact only while documents run one at a time; running sixteen together, each
document's window swept up its neighbours' calls, and every document reported about sixteen times
what it spent. `document_spend(doc, since)` filters the call log by document and by when that
ingest began — the second half mattered, because a document derived twice in one session would
otherwise count the first derivation again, which the "two derivations agree line for line" check
caught immediately.

**`in_parallel` ignored the width it was given**, building its pool at `WORKERS` whatever it was
asked for, so a batch of eight documents ran four at a time and the eight was a fiction.

## The chat corpus, and the one-reading path

A chat session ingests as its own document of one unit, so reconciliation reports `0 pairs
queued` every time and nothing ever merges — yet each session still paid the full per-document
machinery for a single reading. Measured on forty sessions: **$0.052 and 74 seconds each**, so
**$1,003 and 394 hours** for all 19,206. Thirty-three Kaggle sessions. Not feasible.

What the corpus actually holds, once the filenames are parsed properly:

```
ultrachat_*   5,173  |
sharegpt_*    4,525  |  10,638 shared filler and answer sessions
answer_*        940  |
hex ids       8,568     evidence sessions across 6,768 question ids
```

Evidence sessions per question: 5,355 questions have exactly one, 1,112 have two, and only three
have as many as six. So there is no "one user over time" anywhere in the export, and grouping by
question id would give 6,768 documents averaging 1.27 units — no help. **Every one of the 19,206
is exactly two units**, which is what made the branch safe to take.

Justin's ruling: chats stay one session per document, and the efficiency is the ingestor's
problem. The **one-reading path** follows from the architecture rather than from cost — a
document whose boilerplate leaves a single unit to read has nothing to merge, so consolidating
facts stated once is compression rather than judgement, and an entity abstract paraphrases the
single narrative cell that already exists. Such a document skips triage (the boilerplate is set
aside by rule, since with one unit there is no choice to make), writes no entity abstracts, runs
no adjudication, and verifies its whole fact list against the passages in one pass. On the short
path `facts` and `cells` are asked together, since both take the entity list and nothing else.

**Four calls a document instead of twenty-five, all on the cheap model.** The branch is a
property of the document, `one unit left to read after boilerplate`, so Oz, the papers and the
Greek keep every unit and the full path untouched. Documents also now run sixteen at a time, with
the per-unit trace stilled while more than one runs and a spend stop letting the rest of its
batch finish and report before the run halts.

## The 200-session run

```
done 200  spent $1.91 this session
calls_by_stage: {ping 1, entities 200, cells 200, facts 200, support 200}
adjudicated_facts 0, attributes 0, contradictions 0
```

Two hundred documents, **$1.906**, **954 seconds**, exactly four calls each.

| | |
|---|---|
| entities | 6,509 (1,875 major) |
| mentions | 44,011 |
| facts | 7,362 kept, 149 rejected, 5,915 stored |
| unsupported | 1,207 of 5,915 (**20.4%**, from 37.8%) |
| new rejection categories | `span_too_wide` 35, `self_reference` 2 |

The unsupported rate falling from 37.8% to 20.4% — now the same rate the papers run at — is the
support-framing fix, and it is the day's largest single correctness gain. Projected over the
whole chat corpus: **~$182 and ~25 hours** at sixteen at a time, against $1,003 and 394 hours
before.

## The rulings

Twenty-four rulings are recorded in `decisions-ingestor-0.7.md`. The nine taken in the afternoon,
one at a time as Justin requires:

- **The spending stop is a per-block budget**, counted from the block's start. It had compared
  against total session spend, so the papers block spending $7.19 made the $3.00 chat cap and the
  $6.00 Greek cap unreachable and both halted having spent nothing.
- **The roll-up is written beside its package** as `roll-up.txt` rather than printed. The per-unit
  trace already carries every fact and its quote; printing the roll-up too doubled a 26,000-line
  log.
- **Front matter is triage's decision**, not a rule. Triage is told to keep a kind whenever one of
  its units is part of the work, and it follows that correctly: Pask's two front-matter units are
  its title block *and its abstract*, so keeping the kind is right. A hard exclusion I had written
  was reverted.
- **Triage of references and appendices stands as it is**, inconsistency across documents
  accepted, against my recommendation to exclude bibliographies by rule.
- **Unsupported facts are dumped or corrected, not kept with a flag** — but nothing is dumped
  until the rate is measured on a checker worth trusting, so the ruling is deferred one run.
- **The support prompt was edited** to say that a passage carries a claim in its own words, tables
  and headings included.
- **A fact whose object restates its subject is rejected at the gate** as `self_reference`.
- **Kind is an open vocabulary** — "examples of kind include but are not limited to person, group,
  place, object, topic, event" — and a merged entity settles on **one** kind, chosen by its own
  abstract call. Counted back out of the packages: 58 distinct words over 631 majors, the six
  canonical ones covering 76% and 28 words used exactly once — `topic` 144, `object` 112,
  `person` 60, `group` 60, `place` 57, `event` 48, then a long tail through `software`,
  `technology`, `organization`.
- **Decision 64's embedding removal was applied**; it had never reached the notebook, and the
  connection test was still calling the embeddings endpoint once a run.

## Corrections to my own claims

Several numbers I gave during the day were wrong, and the pattern was the same each time: I
answered the question in front of me and checked the invalidating fact only when the next
question forced me to look.

- **Self-referential facts: 223, of which 120 active.** Wrong. 213 of those are `inverse` facts,
  where the `object` field holds the other entity's name and `provenance.subject_name` names the
  same entity — equal by construction, and correct. The genuine count is **10**, of which 8 were
  active. The guard is still worth having; the defect was a twentieth of what I reported.
- **Thirty-eight sessions per LongMemEval question.** I got that by dividing 19,206 by 500 without
  looking. The real figure is **1.27**, and the grouping design built on it was unnecessary.
- **$3,073 as a floor for the chat corpus.** Measured, it is **$182** on the one-reading path and
  was $1,003 on the full one.
- **Prompt caching would cut cost by a third.** Measured, caching every `facts` and `cells`
  prompt in full would save **1%** of a run; output is 81% of the spend.
- **Twenty-five hours became fourteen at sixteen documents at a time.** It is **25**: I costed the
  pool as though it stayed saturated, and each batch waits for its slowest member.
- **The front-matter fix.** I proposed it as a Step 1 change and discovered while writing the
  patch that half of it belonged to the extractor, then found the ingestor half overrode a
  judgement triage was already making correctly.

## Open, and known

- An entity with no narrative cell prints its own fact text where its abstract belongs — about 4%
  of majors on the 200-session run. Cosmetic in the package, visible in every roll-up.
- The terra output price in `PRICE` is inferred, not read from the model page, and terra output
  was 71% of the 48-document run's reported cost. Luna's pair is confirmed. Until terra's is,
  every cost figure for a terra-heavy run is an upper bound.
- Package contents vary between runs of the same document — one session came back as 57
  entities/6 majors, then 72/6, then 61/9. The gate keeps every fact honest, but any number
  quoted in the paper must come from one stated run, or be averaged with the variance reported.
- Riding multiplies on the papers: MEME turned 130 source facts into 391 copies.
- Three near-duplicate majors survived reconciliation across 48 documents, only one of them a
  true duplicate (`the forest` twice in Oz).
- Cross-session resume does not exist: `completed()` looks only under `/kaggle/working/packages`,
  which Kaggle wipes between sessions, so a multi-session run would re-ingest everything at full
  price.
