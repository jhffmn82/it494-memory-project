# 2026-09-07: the dataset published and corrected, the ingestor audited, the rework called off

Step 0's day. The extractor did not change. What changed is what the world can see of it, what
the audit found in Step 1, and one design question that was asked and then correctly withdrawn.

The ingestor's own record for today is on its branch, `log/2026-09-07/decisions-ingestor-0.7.md`
and `audit-answers.md`. This file is the other side of the same day.

## The dataset is public

[ThreadAtlas Step 0: Documents, Units, Pieces](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step0),
MIT, ten files, from the clean 1.5 pass. Five documentation files travel with it and are kept in
[dataset/step0/](../../dataset/step0/README.md), so what is on Kaggle and what is in git are the
same bytes. [pack_step0_public.py](../../scripts/pack_step0_public.py) builds the upload from an
export and was checked by reproducing all eleven published files byte for byte.

The 141 reference papers are withheld: null text, the flag `text withheld: license`, units and
pieces complete, and `papers.jsonl` carrying each source URL and PDF sha256 so the text rebuilds.

**What the Kaggle API will and will not do**, measured rather than assumed:

| pending action | result |
|---|---|
| provenance | settable, as a single `userSpecifiedSources` string. Usability 5.00 to 7.50 |
| cover image | settable, as `dataset-cover-image.png` beside the metadata file |
| per-file descriptions | **not settable**, three ways tried |
| licence | applied at the API but the page still renders Unknown |

Two things worth carrying forward. The client sends `userSpecifiedSources` as an empty string when
the key is absent, so every earlier update had been silently blanking it; `title`, `subtitle` and
`description` behave the same way, so the metadata file must never be hand-trimmed. And the cover
crops are hardcoded absolute pixels, not a proportional fit: the cover is the top-left 560x280 and
the thumbnail is 280x280 starting at x=140, so the art has to be authored at exactly that size
with anything essential between x 140 and 420.

Per-file descriptions failed three ways, all measured: the `resources` key makes the endpoint
return a body that is not JSON; the same payload under `data` returns 200 and is ignored; and a
full version upload with `resources` present left all ten empty after re-uploading 326 MB. That
upload is why the dataset is at version 2 with byte-identical files, and it appears to be what
knocked the licence display loose.

## Seventeen corrections to the published documentation

An audit swept every factual claim in the five files against the extractor and the released rows.
Every count was right. The prose describing how the data was made was not.

The worst was the framing. The README said a language model finds the boundaries. It does, for
230 books and papers. The other 19,206 documents are chat sessions split on their own turns by
code, with **no model call at all**, which is 98.8 percent of the corpus attributed to a decision
never made about it.

Next worst, SCHEMA.md and LIMITS.md promised per-turn chat timestamps. Measured against the
released pieces: 4,001 sessions sampled, 51,950 pieces, **zero** carrying more than one date. The
benchmark dates a session, not a turn, so the promise could never have been kept.

Also corrected: a second model went unmentioned, and 2 of 230 documents escalated to
`gpt-5.6-terra`; the README said a rerun reproduces the dataset while METHOD and LIMITS said the
opposite; `REDO_ALL` works the reverse of how METHOD described it; the reproduction steps stop
before reading a file without the private papers dataset; metadata pointers are matched loosely,
not by the five-word rule; `over_cap_read` counts units, not documents, and the 8 over-cap chat
units were omitted; the flag table counts occurrences; the 39 documents below half body are 38
papers and one scan; and the Archive.org scans are five, not six.

And one the ingestor found first: PROVENANCE.md told a reader to rebuild a withheld paper with
`pdfplumber` and form feeds. The extractor is `pymupdf.open(stream=data, filetype="pdf")` with
`page.get_text()` joined by a single newline, in block 2. Following the old instruction would
have produced a string the offsets do not resolve against.

Not yet republished. The corrections and the cover image go up as one version.

## The ingestor audited

Ten reviewers over build 0.6, each finding handed to a second agent told to refute it. 18 survived,
4 were refuted on the logs. The hand-off went back as a numbered list with the standing instruction
to agree, disagree or show it resolved, and to bring rulings to Justin one at a time.

The two that came from the run's own artifacts rather than from reading:

- **Every adjudication call was paid for twice.** All 100 lines of `retries.jsonl` are one cause,
  `qualifiers: expected string/null, got dict`. The schema demands a string; the prompt calls
  qualifiers "a short phrase for role, manner, or condition", three named facets, and the model
  answers with an object. 92 majors minus 22 skipped is 70 adjudications; the stage made 134 calls.
- **The abstract failed on Oz and the fallback made 92 majors.** `"abstract": 0` in the receipt is
  a boolean. With no abstract, salience falls to "two units or two facts", which caught 92 of 282
  entities against 38 of 358 in the run that had one, and demotion cannot fire on the units branch.
  The knowledge graph shows the result: "Oz's departure by balloon" sits at Dorothy's level.

`rollup()` reading `predicate_raw` after decision 39 removed it was found independently by three
reviewers: every run died with a KeyError after the package was written and paid for.

## The LongMemEval rework, asked and withdrawn

Step 1 asked for a re-export with one document per question, a haystack per document, plus four
schema fields. The structure is real and was never lost: `longmemeval_s.json` carries
`haystack_session_ids`, `haystack_dates` and `haystack_sessions` per question, and
`unpack_benchmarks.py` flattened it deliberately.

Measured from the source: 500 questions, 25,112 slots, 1,230 empty, 23,882 non-empty over 19,206
distinct sessions with content and 623 ids that are only ever empty. 38 to 62 sessions a haystack,
median 48; median 47 distinct dates across those 48. `answer_*` is an exact marker for the
evidence in both directions: all 940 such sessions are named in some question's
`answer_session_ids` and every one of the 948 references is `answer_`-prefixed.

Of the four schema fields, one already existed (`unit.occurred_at`, populated on every chat unit),
one was genuinely new (`unit.source_uri`), one was withdrawn on argument (`unit.author`, because
the piece table settles voice and the unit level would only ever be null or a copy), and one
belongs to Step 1's fact record.

Then Step 1 stood the whole thing down, and was right to. Grouping does not save money: the
reading was always about 15 percent of a session and reconciliation on chats is currently zero, so
grouping would have turned the judge back on rather than off. The saving is in what gets
consolidated, and Step 1 took it internally with a short path for a document whose boilerplate
leaves one unit: four calls instead of about 25, roughly $0.0096 a session, Luna only, the quote
gate untouched.

**Verified before agreeing**: counting units whose kinds are not all front matter or licence,
exactly 19,206 documents have one, and every one is a chat. No Oz volume, no Holmes, no Greek
text, no novel, no paper falls into the short path.

Two things said back rather than fixed. On the short path no entity is ever the same entity twice
across 19,206 sessions, while 344 of LongMemEval's 500 questions are inherently cross-session, so
the join moves from ingest to retrieval and the paper should claim that rather than be caught by
it. And money is solved while time is not: 4 calls at 2.9 seconds is about 64 hours sequential,
six Kaggle sessions, and documents in parallel is the only lever left.

## Open

- **Nothing is merged.** `master` has stopped at 09-04. This branch holds 09-05 and 09-06, the
  ingestor's holds 09-05, 09-06 and 09-07, and the two collide: both wrote
  `log/2026-09-06/README.md` and `log/2026-09-06/audit.md` with different content, and four files
  this branch moved from 09-05 to 09-06 still sit under 09-05 on theirs.
- The cover image, and the republish that carries the seventeen corrections with it.
- The licence rendering as Unknown on the dataset page, and per-file descriptions, both of which
  need the browser.
- **142 reference PDFs are committed to a public GitHub repository**, 338 MB, while their own
  manifest says "not redistributed" and the Kaggle copy is private for that reason. Raised, not
  acted on.
- The old `it494-narrative-corpora-units` dataset is public, stale, and shares file names with the
  new one for a different schema.
