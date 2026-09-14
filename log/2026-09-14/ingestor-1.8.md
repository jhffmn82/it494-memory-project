# Ingestor 1.8, 2026-09-14: the chat reading rerun, verified

From the ingestor thread's report of the run, checked here against the packages and the 1.8 Step 0
export before anything was committed. Step 1 had been frozen on 09-12; Justin unfroze it for one
chat run on the morning of 09-14 (`note-to-ingestor-thread.md`), unhappy with what the 09-13 run's
chat packages held: every chat entity kind `thing`, every subject a major, one alias each. All 81
test documents were rerun, not only the chats, so the 09-13 packages are replaced whole and are not
to be mixed with these.

## The run

`threadatlas-ingestor 1.8`, Kaggle, 16:21 to 16:43 UTC for block 15's window. 81 documents, all
complete; $5.47; 1,784 calls; 1 schema retry, recovered; 0 error lines. Packages at
`%TEMP%/f18b/packages`, the layout as before (`packages/<history>/<session>/<session>.jsonl` for
chats; `oz`, `greek`, `graphrag-bench`, `pdf` for the rest). Verified here: 81 packages, 81
completion records labelled 1.8; every one of the 6,605 non-null quotes slices from the 1.8
export's text at its offsets, 0 off.

## What changed in the code (1.7 to 1.8, 142 changed lines)

- **A salience call for chats.** After the session reading, one Luna call sees the session's
  summary and every entity with its facts and returns each entity's kind (one lowercase word,
  never `thing`; a `thing` is refused and left null) and its salience (major or minor). The user
  stays a major person. An entity the reply leaves out is minor. 68 calls over the 71 sessions
  (the three sessions with no facts had none), $0.034 in all.
- **A minor's facts are kept on the session's document node**, direction `mentioned`, the
  entity's name in `provenance.subject_name`, quote and offsets real. 1,113 of them. This narrows
  the 09-11 rule (a fact whose subject is minor everywhere is not stored) for chats.
- **Every document node carries the document's own facts, written from the export without a
  call**: `has_title`, `has_author` (when known), `has_date`, `has_source_class`, and
  `belongs_to_history` on chats. 324 in all (81, 10, 81, 81, 71). They have no quote: `quote`,
  `quote_start`, `quote_end` and `unit_id` are null, `provenance.from` is `document record`, and
  the date fact's `provenance.flags` carries the extractor's date flags (the page or the URL).
- `kind` may be null in principle (a refused `thing`); in this run none was.

## What the chats look like now (71 sessions; the 09-13 run in brackets)

- Entity nodes: 643, the user's 60 included [1,061]; median 5 a session, the most 64 (a Europe
  trip session listing cities and events).
- Kinds: 0 `thing` [1,001]; 53 distinct across the chats, 99 across all 81 packages. Most common:
  product 130, person 91, work 86, organisation 70, event 42, place 40, store 37, restaurant 29,
  project 22.
- Facts: 5,696 forward, 1,113 mentioned, 120 inverse across the 81 packages; on the chats 2,258
  forward on majors plus the 1,113 mentioned [3,212 forward].

## The answer check

All 22 answer sessions of the 14 questions still hold their answer fact (the ingestor thread's
check; not rerun here). Two notes from it:

- The shift-sheet answer (question 7161e7e2) is weaker than on 09-12: the facts read "shift
  rotation sheet has_agent Admon", quoting the table's Sunday row without its header, so the
  8 am to 4 pm shift is recoverable from the turn's text, not from the fact alone.
- Only a fact's subject becomes an entity. A store named only as an object ("placed an online
  order with Thrive Market") has no node and stays a string, so a lexical or vector signal over
  entity names will not see it. The global layer's nomination over facts and summaries does.

## What follows

- `scripts/pack_step1_public.py` stops on the quote-less document facts
  (`texts[doc][None:None] != None`); it must skip facts whose quote is null before the Step 1
  dataset is repacked.
- Nothing goes to `jhffmn/it494-threadatlas-step1` until Justin approves this receipt. Then the
  `dataset/step1/` docs take the 1.8 label, the `mentioned` direction, the salience call and the
  kind rule, the quote-less document facts, and the counts above.
- The global layer's store is built from these packages, not the 09-13 ones.
