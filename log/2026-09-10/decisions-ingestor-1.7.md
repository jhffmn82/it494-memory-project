# Ingestor decisions, 2026-09-10 (Step 1 thread)

Rulings by Justin, in the order made. The ingestor follows Step 0 `threadatlas-extractor 1.7`.

1. The ingestor work lands on `claude/kg-rag-cc-corpus` (the renamed `threadatlas-ingestor.py`,
   where fa48997 already is), carrying fold-09's b5c8b90 onto it.
2. Of "Step 0: what changed since factledger-extractor 1.5", all four ingestor items: the chat
   path for one turn per unit, block 14 off Zep, the 55 empty chat turns skipped, the header's
   kinds table.
3. `valid_to` is dropped now; it had been held since 09-09.
4. A chat now has many units, so it takes the end-of-document roll-up and everything else, not
   the one-reading shortcut. A document left with one unit to read still takes the short path
   (ruling of 09-07): 59 sessions in the 1.7 export.
5. Block 12 runs one user's entire chat history, a whole LongMemEval haystack, in place of the
   200 random sessions, as the input for testing the global step.

Chosen in carrying out 5, not ruled: the haystack of question gpt4_2ba83207 (multi-session, 53
sessions, 502 turns). It is one of the 46 haystacks whose every session is in the export, the one
with the fewest undated sessions (7), and its four answer sessions are dated.

Found along the way:
- A user's history is the haystack, not the filename stem: a haystack mixes the user's own
  sessions with filler from ShareGPT and UltraChat.
- 623 haystack session ids have no file. None is an answer session; they are empty sessions the
  unpacker skips.
- No haystack is fully dated: each has 7 to 33 sessions the export leaves undated (ruling 7), so
  the global step takes those dates from the question.
