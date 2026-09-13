# 2026-09-12: the Flex run read, chats cut to one call a session, Step 1 frozen

Written 2026-09-13 from the run receipts, the prune diffs (19 to 23) and the Step 1 thread's
record of the day's rulings, because no log was kept on the day. Nothing was committed on the day.

## The Flex run, read

The run of the evening before (69 documents, $6.36): every call served on Flex, all packages
complete, quotes verbatim.

- Chats cost $0.020 a session, about $387 for all 19,206 (was $0.095 on the standard tier with
  the judge on Terra).
- The Luna judge was within about 2 percent of the Terra run on the 53 haystack sessions.
- The quote-prompt fix (one continuous passage, no ellipsis) joined store and amount in one fact
  (Thrive $150, Trader Joe's $80), so quote widening (C4) is not needed.
- Chat volume: 85 stored facts a session, 70 percent of them from the assistant; 27 majors, 59
  cells, 28 abstracts; the package is 16 times the size of the chat.
- Against the benchmark's `has_answer` turns: grocery (4 stores), Roscioli, 2 to 3 eggs and Maundy
  Thursday captured; the 5K time 25:50 is a value and the old 27:12 only inside a quote; "38
  subjects" (an assistant specific) was never extracted.

`check_flex_run.py` (committed 09-13 as `log/2026-09-13/check_flex_run.py`) reports cost per
session and tier, failures, quotes, and whether each answer fact is stored.

## Rulings (Justin, in the order made)

1. **B3 yes: the assistant's specifics are facts** (p_b3, diff 19).
2. The main thread does the git work: both run versions, extractor 1.7, docs, logs, push. The
   Step 1 thread adds the tidied version on top after its run.
3. **We capture too much from chats.** The chat fact prompt is narrowed (p_narrow, diff 20): a
   user turn yields only the user's own details plus the stated-detail facts; an assistant turn
   only the specifics it gives the user; books and papers keep the general instruction. The gate:
   all six answer questions must still find their answers.
4. **A chat session is read in one Luna call** (p_session, diff 21, +217 -75). This replaces the
   per-turn prompts of ruling 3, which moved into `session_prompt`. `read_session` ties each fact
   to its turn: the quote must be found in that turn, and the subject must be the user, appear in
   the turn, or share a word with it. No judge, no cells, no fold for chats; the reading's summary
   is the abstract, and chat majors get no abstract. A session over `SESSION_WINDOW` (40,000
   characters) is read in stretches of whole turns. Battery 94 of 94. The gate is the six answer
   questions (10 answer sessions), on a chats-only copy of the notebook (block 12 only).
5. **Tighten the stated rule**: every user sentence stating a detail becomes one stated fact
   quoting the whole sentence (p_stated, diff 22).
6. **Eight more answer questions** go into block 12 (p_more_answers, diff 23): 2
   single-session-user, 2 single-session-preference, 1 each of the other four types; in each type
   the first non-abstention questions in file order. 12 sessions, 71 in all. The needles were
   added to `check_flex_run.py`.
7. **Step 1 is frozen** on the prune working copy through p_more_answers. The full notebook, all
   blocks on, was sent from `for-kaggle/full/`; its packages feed the global merge.

This reverses ruling 4 of 09-10 (decisions-ingestor-1.7: "not the one-reading shortcut"): a chat
is again read as one document, in one call, but by a session prompt built for chats, not by the
old one-unit path.

## The two chats-only test runs (times UTC; the evening of the 12th, local)

**First, rulings 1 to 4 (started 04:24 UTC on the 13th):** 59 sessions complete, 0 bad quotes,
213 calls, $0.25, $0.0043 a session (about $82 for the corpus), 6.7 minutes. Per session: 43 facts
(was 85), 18 nodes, 1 abstract, 0 cells. "38 subjects" captured for the first time. Thrive and $150
split into two facts; stated facts fell to 4 a session from 5.9. Rulings 5 and 6 followed.

**Second, rulings 5 and 6 (started 04:38 UTC):** 71 of 71 complete, 0 bad quotes, 245 calls,
$0.32, $0.0045 a session, 8.7 minutes. All 14 questions have their answers stored. Thrive and $150
are in one stated fact. Stated facts are 1.6 a session because 232 whole-sentence stated facts
were dropped as duplicates by `drop_repeated_stated`. Ruling 7 followed.

Kaggle CLI notes: the scratchpad path is too long for the CLI, so outputs go to a short path
(`%TEMP%\sr2`); the CLI needs `PYTHONUTF8=1`.

## Open at the end of the day

- The frozen full run has not run yet (it ran at 06:18 UTC on the 13th).
- Nothing since fa48997 is in git: extractor 1.7 as run, the three ingestor versions that ran,
  the Step 0 docs as published, the 09-10 logs, the prune diffs.
- The "one history only" question: block 12 now loads one history plus the answer sessions of 13
  other questions. Whether a global merge over those packages mixes 14 users' timelines was not
  raised.
