# Review of the rebuilt extractor notebook, 2026-09-05

Sixty-three agents over `notebooks/factledger-extractor.py` as it stood after the morning's
rulings and before the fix batch: seven finding lenses (Kaggle runtime, block 6 logic under
adversarial replies, block 7 logic, export and resume, rule-by-rule fit, how a model reads the
three prompts, cost and size of the real run), then two independent refuters per finding, one
reading the code, one reproducing the claim with a stubbed model. Read-only on the repository,
no network. 77 findings, 28 unique verified, 26 confirmed, 2 contested, 0 refuted; 48 dropped
by the cap unverified, mostly duplicates and nits, the five real risks among them folded in
below. Line numbers refer to the pre-batch script.

## Confirmed, consolidated

1. **Title, author, source and date pointers were never verified** (five findings; blocker).
   `resolve()` ran on regions, pieces and breaks only. Reproduced: an author pointer at a line
   reading "at www.gutenberg.org…" exported `author: Nobody Realperson`, `occurred_at: 1850`,
   mismatch 0, no flag, and the date landed on every unit. Fix: `verify_meta()` in block 6.
2. **Coverage gate skipped a single body piece** (`len(body) > 1`): regions with no headings
   passed with the whole body as one piece. Fix: the guard is body-over-cap, not piece count.
3. **`longmemeval/manifest.json` matched the chat glob**, went to the model three times as a
   3 MB document and was exported. Fix: excluded.
4. **`SPEND_STOP` did not stop**: the RuntimeError was caught per document and every later
   document was written as a flagged "whole". Fix: `SpendStop`, the loop ends, the document in
   flight is not written.
5. **A bare-string `date` crashed the paid split into "whole"**; likewise malformed grouping
   and break replies. Fix: type guards, `iso_of()`.
6. **Chat runs**: a first turn over the cap made a header-only unit; a short turn before an
   over-cap turn became a lone-turn unit. Fix: a run closes only with two or more turns.
7. **`resolve()`**: an empty copy verified at any index; the prefix match let "CHAPTER I"
   verify against "CHAPTER II"; recovery returned the lowest index in the window, not the
   nearest; a trailing ellipsis never matched. Fix: exact, eight-word cut, or a prefix of five
   words or more; nearest first; ellipsis and "[i] " stripped; numeric-string indexes.
8. **Sub-split gave up silently** (TooLong, no cut, depth exhausted) with `flags: []`, and its
   unresolved breaks bypassed the pointer gate. Fix: over-cap leftovers and new unresolved
   breaks flagged in block 8; one more ask when no break resolved.
9. **A region with an unknown kind was dropped silently; a model that omitted the line-0
   region got the Gutenberg header labelled body.** Fix: both flagged.
10. **Receipt**: `flags_by_kind` fragmented on flag texts whose number preceded the colon;
    `source_class` exported unvalidated; cost summed only the surviving record; identical-text
    units in one document shared a `unit_id`. Fix: "kind: detail" flag texts; validated
    against the five schema values; cost over every record; occurrence count in the hash.
11. **Contested, taken**: best-of-two by flag count let "no body region" (one flag) beat a real
    outline with two; records stored absolute Kaggle paths, which move between sessions. Fix:
    body-present ranks first; records carry a dataset-relative `file`.
12. **Runtime**: blocks 8 and 9 each read 19,206 chat files serially over the network
    filesystem (locally 4.6 s; on Kaggle tens of minutes each, per block 1's comment), and
    block 8 read a file before checking whether it was done. Fix: done-check by name first;
    block 9 reads 32 at a time.

## Cost and size, measured

From the script's own `addresses()` and `listing()` over the local mirror, 231 text and PDF
documents, 13.5M listing tokens:

| | |
|---|---|
| Luna, one pass over everything that fits 200k | $2.12 ($1.71 at 128k) |
| Group calls | about $0.08 |
| Sub-splits at realistic piece sizes | about $0.71 |
| Terra on every flagged document, at the old run's flag rate | $10 to $18 |
| Over 200k listing tokens | 13 documents: 11 Greek, Snodgrass 1999 (666k), Weikum 2021 |
| 128k to 200k | 12 documents: 4 Holmes, 7 Greek, Hogan 2021 |

Ruling that followed: Luna retries everywhere; Terra only under 80,000 listing tokens.

Also noted by the cost lens and not yet acted on: `SPEND_STOP` resets per kernel session, so
spend across reruns is unbounded by design; a flagged document is re-asked on every rerun;
`toc_count` counts the whole contents list, so the gate now compares it with headed pieces in
every region rather than body pieces only.

## Covered and found sound

Execution order across the nine cells; the record shape and `read_splits`; Python
%-formatting against documents containing "%"; the word JSON in every prompt; the chat path
over all 19,206 sessions (19,211 units, 5 multi-unit sessions, 8 over-cap single turns, 3,944
ambiguous dates); export sizes within Kaggle limits (about 38 MB of records, 240 MB of
documents).
