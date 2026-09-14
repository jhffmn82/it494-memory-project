# The ingestor: algorithm and data contract

`threadatlas-ingestor 1.8`. Step 1 was frozen at 1.7 on 2026-09-12 and unfrozen for one chat
run on 2026-09-14, after the 1.8-export run's chat packages showed every entity as kind `thing`
and every subject a major; 1.8 adds a salience call for chats and the document's own facts, and
ran over all 81 test documents on 2026-09-14 (`log/2026-09-14/ingestor-1.8.md`). One document at a
time, from the extractor's export to a **document package**: the entities the document is about,
every fact with a verbatim quote located at document offsets, a narrative cell per entity per
unit, the document's abstract, and an abstract per major entity. Nothing here looks at a second
document. The input's field schema: [`dataset/step0/SCHEMA.md`](../dataset/step0/SCHEMA.md).

## Input

The extractor's three files ([`docs/extractor.md`](extractor.md)): `documents.jsonl` (every
document with its whole text), `units.jsonl` (character ranges, each dated; a chat's unit is one
turn), `pieces.jsonl` (the split plan, with a chat turn's author). A chat is any document whose
units are of kind `user` or `assistant`.

## Algorithm

A document of many units (a book or a paper):

```
triage      one call: which kinds of unit are not the work; front matter and license go by
            rule; an answer that would leave out more than half the document is ignored
per unit,   entities   each with its surface forms; kept only if a form is found in the unit
WORKERS=4   facts      each with a verbatim quote; kept only if the quote is located
at a time   cells      a unit summary and one narrative cell per major
reconcile   same proper name and kind unite with no call, unless their is_a conflict; other
            pairs (a shared surface form, one said to be the other, a shared name word) are
            scored 0.7 name + 0.3 co-occurrence, dropped under SIMILAR_ENOUGH (0.35), judged
            round by round on Terra, ten pairs a call: same / different / unsure; every
            verdict is a ledger row, every scored pair a candidate row
fold        the abstract summarises the unit summaries on Terra; every major gets its own
            abstract; a major with no facts and no cells is demoted (decision 52)
adjudicate  a major with ADJUDICATE_MIN_FACTS (4) or more: one Terra call consolidates them
            into facts, attributes and contradictions, each citing the raw facts behind it;
            a major with fewer keeps its raw facts, checked against their passages in one
            support call, VERIFY_BATCH (60) facts a call
verify      every flagged fact is looked at again on Luna: stand, reword to what its passage
            states, or drop; a rewording is checked once more; a flagged fact no verdict
            reaches is dropped
write       the package, then the roll-up
```

A document of one unit: no triage call, the unit's entities then facts and cells together,
nothing to reconcile, the unit summary is the abstract and a major's own cells its abstract, every
fact checked in one support call, verify, write. About four calls instead of twenty-five.

A chat session: one Luna call over all its turns (`read_session`, medium reasoning effort), a
session over `SESSION_WINDOW` (40,000 characters) read in stretches of whole turns. Each fact names
its turn and is kept only if its quote is located in that turn and its subject is the user,
appears in the turn, or shares a word with it. Every subject the reading used is an entity; the
same name in two turns is one entity, no judge. Then one more Luna call, `salience`, sees the
session's summary and every entity with its facts and gives each entity a kind (one lowercase
word, never `thing`; a `thing` is refused and left null) and a salience: major, or minor. The user
stays a major person; an entity the reply leaves out is minor. A major becomes a node with its
facts; a minor gets no node, and its facts are kept on the session's document node with direction
`mentioned` and the entity's name in `provenance.subject_name`. The reading's summary is the
abstract. No judge, no cells, no fold, no entity abstracts. Then one support call over every fact,
verify, write.

Models: `gpt-5.6-luna` derives units, reads a chat, and runs the support checks and corrections;
`gpt-5.6-terra` judges, folds and adjudicates books and papers. `SERVICE_TIER` is `flex`, priced by
the tier that served the call (Luna 0.10/0.60, Terra 1.00/6.00 per million tokens in and out on
Flex; 0.20/1.20 and 2.00/12.00 standard). No embedder; no vectors are stored.

## Rules

- **Quote gate.** A stored quote is a verbatim slice of the document, no ellipsis. Located as
  `exact`, `normalised`, `unwrapped` or `words`; rejected as `paraphrase`, `not_found`, `empty`,
  `duplicate`, `self_reference` or `unlisted_subject`.
- **Salience.** A unit's call makes an entity major for the document; abstract naming and proper
  names do not promote. A major with nothing to summarise (no facts, no cells) is demoted.
- **Minors have no node.** A fact lands on the major that is its subject (forward), or under the
  major it points at (inverse), with the lesser thing's name as its value. A fact between two
  lesser things is not stored, except in a chat, where a minor's facts are kept on the session's
  document node as `mentioned` (1.8).
- **Every document node carries the document's own facts**, written from the export without a
  call: `has_title`, `has_author` (when known), `has_date`, `has_source_class`, and
  `belongs_to_history` on a chat. They have no quote (`quote`, `quote_start`, `quote_end` and
  `unit_id` are null); `provenance.from` is `document record`, and the date fact's
  `provenance.flags` carries the extractor's date flags.
- **Stated facts.** From a user turn: what the user says of their own life, plus one `stated` fact
  per user sentence that states a detail, the whole sentence as its object and its quote. From an
  assistant turn: the specific names, numbers, amounts, steps and options it gives the user.
  `drop_repeated_stated` drops a stated fact whose span another kept fact already holds. Books
  and papers keep the general fact instruction.
- **Dates.** `valid_from` only when the quote itself states it; no `valid_to`. A fact carries
  `occurred_at` copied from its unit. `rank` is `active`.
- **Contradictions are resolved within a document only.** A contradiction record names which of
  its source facts holds at the document's end; both facts stay active. Across documents nothing
  is resolved.
- No profile record; no mention records (mentions are counted, not written). Predicates stay as
  the model wrote them, in snake_case.

## Run configuration

Blocks 12 to 15 are the run. Block 12: one LongMemEval history, `gpt4_2ba83207` (53 sessions),
plus the answer sessions of 13 other questions covering the six question types; sessions are
chosen by path since 1.8, never by title; 16 at a time, budget $15. Block 13: the first three Oz
books, $12. Block 14: five of the 100 kg-rag-cc papers, drawn with seed 494, $8. Block 15: the
Bacchae and Dandy Dick, $6. A block's budget ends it past that many dollars of its own spending.

## Output

One package per document at `packages/<corpus>/<file>/<file>.jsonl`, one record a line under a
`record` field: `document`, `unit`, `piece`, `node`, `alias`, `edge` (`appears_in`, `has_unit`),
`cell`, `abstract`, `adjudicated_fact`, `attribute`, `contradiction`, `fact`, `rejection`,
`ledger`, `candidate`, and a final `completion` with the counts. A `roll-up.txt` is written beside
it. Run logs at the output root: `calls.jsonl` (every call with its cost), `retries.jsonl` and
`rejections.jsonl` (replies that did not fit their shape), `ingest.log`, `receipt.json`.

Ids are readable: `<doc_id[:8]>:doc` for the document node, `:n<index>` for an entity node,
`:u<unit position>:f<n>` for a fact. All offsets are document offsets. A finished package is
skipped on a rerun; to continue a stopped run, make a dataset from the output and attach it.

## Measured cost

A chat costs about half a cent a session on the one-call design, the salience call adding
$0.0005 ($0.034 over 71 sessions), about $110 for the 23,882 chats. The 1.8 run of 09-14 over the
81 test documents: $5.47, 1,784 calls, 1 schema retry recovered, every one of the 6,605 quotes
slicing from the export at its offsets. The books and papers are $5 of that; the 71 sessions are
under $0.50.
