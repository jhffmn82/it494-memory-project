# 2026-09-11: the first full Step 1 run read, the audit answered, and the Flex tier

Written 2026-09-13 from the run receipts, the Step 1 thread's diffs and its record of the day's
rulings, because no log was kept on the day. Nothing was committed on the day; the notebooks that
ran were recovered into git on 09-13 (59180a1, 1c4132d).

## The full run on Step 0 1.7 (started 00:03 UTC, the evening of the 10th)

The notebook that ran was 1e381d8 plus the chat edits of 09-10 (`TURNS`, the user a standing major
on a user turn, `user stated` facts, chat abstracts from cells, no consolidation in chats, triage
skipping turns, `RUN_TIMES`), labelled `threadatlas-ingestor 0.9` as it ran. Output in the Kaggle
kernel `jhffmn/threadatlas-document-ingestor`.

- 63 documents: the 53 sessions of haystack gpt4_2ba83207, 3 Oz books, 5 kg-rag-cc papers, the
  Bacchae, Dandy Dick.
- 3,690 calls, $15.68. Every package complete; 0 quotes off their offsets against the 1.7 export;
  2 schema retries, both recovered.
- The receipt's 15.3 minutes is block 15 alone: `RUN_TIMES` is reset each block, so the receipt's
  "minutes" covers only the last `run()` call. The whole notebook takes hours.
- Chats cost $0.095 a session, and the judge is 61 percent of it; all 19,206 sessions would be
  about $1,830.
- Oz resolved 42 of 43 contradictions, the first time R4 fired on real data.
- 0 of 8,360 facts crossed a speaker; the "refused" merge guard fired once, so it is reachable;
  0 one-reading documents; 53 chat graphs drawn.

Baseline for question gpt4_2ba83207 (Thrive Market $150, Walmart $120, Trader Joe's $80, Publix
$60): three of the four stores and amounts were linked user facts; Publix's $60 was lost as a fact
about a minor entity; adjudication dropped the Walmart link.

## The audit, answered

- **B2, 1,395 unstored facts.** They come from a9bff5b (09-07), which dropped riding (ruling 27,
  decision 11) without a ruling, on the false premise that nothing is demoted any more; decision
  52 still demotes. Of the 743 losses the fact ids can place, 710 came from assistant turns (17.6
  percent of the assistant's kept facts) and 33 from user turns (2.4 percent).
- **The fact prompt still permits an ellipsis that `locate()` refuses** (ruling of 09-08). It cost
  192 facts in the run: 178 paraphrase, 14 not_found.
- **PRICE** matches OpenAI's published standard short-context rates (Luna $0.20/$1.20, Terra
  $2.00/$12.00 per million). Flex and Batch are half price for both.

## Rulings (Justin, in the order made)

1. **A fact whose subject is minor in every unit is not stored.** The completion record keeps the
   count; riding stays gone; no `no_major` rejection category. Revisit only if the B3 test finds
   an answer in one.
2. **Block 12 gets six answer sessions of other questions**, making 59: answer_ultrachat_448704,
   113156 and 13075 (single-session-assistant questions 4c36ccef, 0e5e2d1a, e8a79c70);
   answer_a25d4a91_1 and _2 (knowledge-update 6a1eabeb); answer_a17423e7_1 (temporal
   gpt4_b5700ca9).
3. **Try a Flex run.** The judge and the document abstract go on Luna, for chats only.
4. No reply cache (C3). C5 no. C6 no.
5. Item 8: fix the ellipsis prompt first; no quote widening yet.
6. A2 yes: the audit thread commits and pushes. (It did so on 09-13.)
7. Version label: `threadatlas-ingestor 1.7`.
8. **Complexity audit: all four groups approved**, each as its own diff: A (cuts), C
   (restructure), B7 (drop decision 46's speaker-cut code), B8 (no chat graphs). Order: B1, B4,
   A3 first (the audit's no-ruling defects), then B8, B7, A, C. Prepare in scratch against the
   Flex notebook; commit only after A2 lands.
9. **All six chat edits of 09-10 are rulings**: user always major on a user turn; the speaker
   note and `user stated` facts; chat majors take their cells as abstracts; no consolidation in
   chats; triage never offers turns; `RUN_TIMES`.
10. **A flagged fact the correction step skips is dropped.** The recommendation was "stands"; the
    ruling is drop. It never triggered in the full run: all 1,350 flagged facts got an answer, and
    the 36 counted as unanswered were failed rewordings, which B1 now drops.
11. `reconcile` stays as it is (99 lines); it is not split.
12. Run the Flex test notebook first, as sent; the pruned notebook runs after it.

Also that day: the global merge is due by Wednesday 2026-09-16. The plan given: check the Flex
run, then one run of the tidied notebook; those packages are what the global merge reads. After
that Step 1 is frozen unless something blocks the merge.

## Built

- **The Flex notebook** (`for-kaggle/threadatlas-ingestor.ipynb`, 41 changed lines): `SERVICE_TIER
  = "flex"`, PRICE by the tier that served each call, timeout 900 seconds, the judge and the fold
  chosen by whether the document is a chat, the ellipsis prompt fix (one continuous passage), the
  1.7 label. Battery 84 of 84. It must run without the prior output attached, or finished
  packages are skipped.
- **The prune steps**, as patch scripts applied in order on the Flex notebook: p_b1, p_b4, p_a3,
  p_b8, p_b7, p_a, p_c, p_c4 (diffs 10 to 17), then p_r2 (18) for ruling 10. Battery 91 of 91,
  round trip identical, 0 lambdas. 2,571 lines to 2,551; longest function `reconcile`, 99 lines.

## The Flex run (started 23:08 UTC)

69 documents (the 59 sessions plus the ten books and papers), 3,884 calls, $6.36, every call
served on Flex, all packages complete, quotes verbatim, 2 schema retries. The receipt's 21.1
minutes is block 15; the notebook took about 3 hours. Read on 09-12.

## Open at the end of the day

- Facts under majors with 4 or more facts get no support call, so some ride on quotes that do not
  state them.
- Decision 52 still demotes a major that has no facts or cells (3 in the run).
- Triage now runs on chats and could drop the `assistant` kind when it is exactly half the units.
- The battery `log/2026-09-06/test_ingestor.py` has been dead since 6da9186 (`whole_word`
  removed); the live one is `log/2026-09-08/test_ingestor.py`.
