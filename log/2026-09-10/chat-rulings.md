# 2026-09-10: chat preprocessing, ruled one question at a time

Why this came up: the extractor log showed every LongMemEval chat as one conversation unit with
one date, and 3,944 sessions flagged for carrying several dates. The chat design had been fitted to
LongMemEval, the only chat the pipeline has read, instead of to the end state.

## What the data showed

LongMemEval is 500 simulated users, each a history of about 48 sessions in date order: 23,882
placements over 19,206 distinct texts. A session's date comes from its place in a history, and
3,944 sessions sit in 2 to 6 histories on different dates. The text is identical in every
placement (0 content variants in `longmemeval_s.json`), so the unpacker's dedup by id lost no text.
It lost the histories, their order, and which date belongs to which. 16 evidence placements sit on
a multi-date session: 8 temporal-reasoning, 8 knowledge-update.

For the script: 1,230 placements are empty and are skipped. 1,426 sessions open with an assistant
turn and 52 have no user turn at all, so a unit starts at each user turn and anything before the
first user turn is a unit of its own; 13 sessions with two turns in a row by one speaker fall under
the same rule. At one unit per exchange the 19,206 sessions hold 99,119 units, about five times the
19,206 conversation units today. 1,475 placements in 76 of the 500 questions are dated after the
question itself; the script keeps dates as given, and whether a question may see its own future
is the evaluation's ruling.

Real chats are a different shape. Every source but Gemini puts a time on every message.

| | User turn (median words) | Assistant turn (median words) | Conversation (median / p90 words) | Over 4,000 words | Sittings (median / p90) |
|---|---|---|---|---|---|
| LongMemEval | 32 | 272 | 1,694 / 2,679 | 8 of 19,207 | 1 |
| ChatGPT (548) | 16 | 74 | 3,039 / 31,940 | 45% | not measured |
| Claude.ai (203) | 16 | 198 | 3,600 / 36,945 | 47% | 1 / 6 |
| Claude Code (106) | 19 | 55, text only | 2,012 / 37,058 | 45% | 2 / 10 |
| Gemini (219) | 13 | 457 | 1,427 / 5,375 | 17% | 1 |

About a quarter of Claude.ai and Claude Code conversations span more than one day. ChatGPT
conversations are trees (edits and regenerations branch). Gemini has no threads at all.

## Rulings

1. The ingestor rerun is held, all of it, until chat preprocessing is redesigned and Step 0 reruns.
2. A chat document is a conversation. Every turn keeps its speaker, position, and own time. A
   history is an ordering over conversations: LongMemEval has 500, the archive has one. A session
   reused in several histories is several dated placements over one stored text.
3. A unit is a snapshot in time and carries one time. `occurred_until` stays dropped, reaffirming
   ruling 1 of 2026-09-09.
4. A chat unit is an exchange: a user turn and the assistant's reply. Its time is the user turn's.
   A single oversized turn is flagged over the cap.
5. Chats are preprocessed now by a script specific to LongMemEval's data, not by the general
   extractor. A general chat preprocessor comes later.
6. The output schema must carry Gemini, Grok, Claude, and OpenAI chats. A conversation carries a
   title, a time, and an author; each unit is one exchange and carries its own time.
   PROPOSED, not yet ruled: the placement record (ruling 2 made concrete) and a `tool` piece
   kind. Draft in `step0-chat-schema-draft.md`.

7. LongMemEval, settled: a session is a document, titled by its session id, and a turn is a
   unit, named by the line that opens it: `SESSION <id> TURN <n> <date>`. A turn's time is the
   session's date when the session has exactly one (15,262); a session placed on several dates
   (3,944) names and keeps none. The evaluation filters by the question's haystack session ids
   only, never by date, because 75 evidence placements in 44 questions are dated after their own
   question, and it labels each returned session with that question's date. This supersedes the
   exchange unit in 4 and the placement in 2 and 6. 19,206 documents, 199,641 units.

## Done

- Extractor 1.7 drafted as `extractor-1.7.patch` (11 edits, +46 -62, line endings kept): one unit
  per turn, the SESSION/TURN/date line, the one-date rule, chats from an older loader re-split at
  no cost while model-read documents stay cached, and the dead `day()` and `TAIL_FLOOR` removed.
  Verified offline on all 19,206 sessions: 199,641 units, 15,262 dated, 3,944 flagged, 0 failures.
  The cell-order check's two forward references and the notebook round-trip warning fail the same
  way on the unpatched original.

## Open

- Apply the patch and rerun Step 0.
- After the rerun, update the docs that still describe runs of turns, a session header, and the
  start-date rule: `docs/extractor.md`, `dataset/step0/SCHEMA.md`, `METHOD.md`, `README.md`,
  `SCHEMA.md`, `BUILD.md`. The receipt's short-unit count will jump, since most single turns are
  under 100 words.
- The ingestor's chat path assumed one unit per chat. With a unit per turn, chats take the
  multi-unit path; check it and price it on a sample before the full ingest.
