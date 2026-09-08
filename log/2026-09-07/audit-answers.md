# The outside audit's items, answered

The audit thread reviewed `claude/infallible-einstein-e34c97` at `f3d8e4e` and the 0.6 Oz pass
and sent 17 defect claims, 3 questions for Justin, 5 answers to the hand-off's own questions,
5 refutations of its own, and 12 unverified observations. Every claim was reproduced against
the code before it was answered; nothing below is taken on the audit's word. Line numbers are
those of the head at the time of answering (`10d7567`), which differs from `f3d8e4e` in two
places: the adjudication prompt types its fields and the roll-up no longer prints profile rows.

| Item | Verdict | What was done |
|---|---|---|
| A1 roll-up crashes on `predicate_raw` | confirmed | The dead clause is gone; the roll-up runs again. A battery check now reads a package back through `rollup`. |
| A2 a consolidated fact built only from unsupported sources is unmarked | confirmed | Settled by decision 45: the sources set aside come out of the list; an item left with none is dropped and counted. |
| A3 every adjudication paid for twice | already resolved | The prompt at HEAD types `object` and `qualifiers`. 61 of the 65 retries in the pass were a `qualifiers` object. If the next receipt still shows them, the fallback is to accept an object and join it. |
| A4 the abstract failed, and the fallback made 92 majors | confirmed | Decision 42 lets the fold use the document's own names; decision 52 makes an entity that cannot be summarised a minor; the receipt now names each package whose abstract was rejected. |
| A5 the whole-word test defeats itself on a hyphenated line break | confirmed | `whole_word_hit` is now the first span `surface_spans` finds, which has always tested the boundary on the normalised copy. |
| A6 the pieces path attributes a fact to the wrong speaker | confirmed | Decision 46: the span is cut at the piece boundary and stored once per voice. |
| A7 a "different" verdict undone transitively inside one batch | confirmed | A union that would join a pair ruled different is refused; the ledger keeps the judge's verdict with `how` "refused". |
| A8 two clusters kept apart can share a node id | confirmed | Decision 48 rebuilds the id from the moniker and its first mention, and `write_package` refuses to write two nodes with one id. |
| A9 the four-fact skip skips the only support check | confirmed | Decision 43: a Luna support call instead of nothing. |
| A10 the support judgement is made on a truncation | confirmed | The whole quote is sent. About a cent on an Oz run. |
| A11 the nomination queue is uncapped and quadratic | confirmed | Decision 44: no cap, two pruning rules at nomination instead. |
| A12 the version label has not moved | confirmed | 0.6 to 0.7; `input_hash` carries it, so old packages and sidecars are re-derived. |
| A13 a cell is dropped when the model spells the name differently | confirmed | Cells resolve through the same loose map as a fact's subject; a cell that resolves to nothing is counted. |
| A14 a torn sidecar destroys what the resume then pays for | confirmed | `checkpointed` trims to the last complete line before reading. The battery reproduces the tear. |
| A15 23 facts vanish between kept and stored | refuted | Nothing vanishes: 948 kept, 31 with a minor subject riding nowhere, 34 distinct facts riding as 42 copies, 925 stored. The missing term was the distinct riding facts, now counted. |
| A16 a battery check re-derives the value the code derives | confirmed | The chat checks now assert from the fixture's piece table that no fact's quote spans two voices. |
| A17 `from_facts` checked only as a subset | confirmed | The new check asserts a consolidated `is_a` is drawn from raw `is_a` facts, and fails under the audit's permutation. |
| B1 the words matcher's shape | measured | Decision 47. The table is in the decisions log. |
| B2 the both-named union and the two Ajaxes | measured | Decision 49. |
| B3 whether the stored quote should be capped | moot | Decision 46 bounds a chat quote at the speaker; a novel's ellipsis quote is unchanged. |
| C1 to C5 | answered | C1 is B1, C2 is B2, C3 is A9, C4 is A8. C5, the papers rebuild, was confirmed correct end to end by both sides. |
| D1 to D5 | not pursued | Nothing to do; D4 is right that no stage after the last unit is checkpointed, by decision 32. |
| E1 a rider stays active under an unsupported tie | confirmed, then dissolved | Decision 50 checks every entity's facts before anything rides, so the rider's rank is its own. |
| E2 the empty-triage guard is never exercised | refuted as a defect | The guard exists and fires and the package records it. What is true is a text mismatch: `audit.md` says "more than half the units", the code guards "every unit". For Justin. |
| E3 the capitalised-object rule is untested | confirmed as a gap | A check now asserts no lowercase object is stored as pointing at a node. |
| E4 no check scripts a reply that fails twice | confirmed as a gap | A check now asserts the refusal and its record. |
| E5 salience compared case-sensitively | confirmed | Read case-insensitively, as `kind` already was. |
| E6 a thin dossier is asked for a five-word abstract | confirmed | Superseded by decision 52: such an entity is not a major. |
| E7 a resumed document under-reports its cost | refuted | Unit costs are stored in the sidecar and summed on resume. |
| E8 the roll-up skips the completion check | confirmed | It now reads a package the way every other reader does. |
| E9 three whole-word matchers | partly confirmed | The A5 fix removes one. The abstract's `whole_word` stays: it works on casefolded text with no offset map. |
| E10 to E12 | mixed | E10 and E11 went to the simplification list. E12 refuted: every timed-out attempt is logged and counted, three at most. |

## What the audit could not see

Three of its claims rested on files that are uploaded after a run: `receipt.json`,
`retries.jsonl`, `rejections.jsonl`. A rejected abstract was recorded only in the completion
record and the run log, neither of which is uploaded, which is why A4 read as "invisible in
every artifact". The receipt now carries it. The retries file also appends across runs in one
Kaggle session, so its 100 lines held an earlier run's 35; the receipt counts the session only.
