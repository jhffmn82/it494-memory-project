# The ingestor: algorithm and data contract

`factledger-ingestor 0.9`. One document at a time, from the extractor's export to a **document
package**: the entities the document is about, facts with a verbatim quote at document offsets,
a cell per entity per unit, the document's abstract, and an abstract per major. It never looks at
a second document. Store fields are in [`SCHEMA.md`](../SCHEMA.md).

## Input

The extractor's three files ([`docs/extractor.md`](extractor.md)): `documents.jsonl` (text once,
`null` for a withheld paper), `units.jsonl` (character ranges), `pieces.jsonl` (the split plan,
with a chat turn's author). `papers.jsonl` rebuilds a withheld paper's text from its PDF.

## Algorithm

A document of many units:

```
triage     one call: which unit kinds are not the work (front matter, references); leave them out
per unit:  entities   kept only if a surface form is found in the unit text
           facts      each with a verbatim quote; kept only if the quote is located;
                      a quote crossing a change of speaker is cut into one fact per voice
           cells      a unit summary and one narrative cell per major
reconcile  same proper name and kind unite with no call; other pairs (shared form, shared name
           word, one said to be the other) are scored and judged round by round, strongest first,
           same / different / unsure, ten pairs a call; every verdict and scored pair is logged
fold       the abstract summarises the unit summaries; every major gets its own abstract
adjudicate a major with >= 4 facts: one call consolidates them into facts, attributes and
           contradictions, each citing the raw facts behind it; a major with fewer keeps its raw
           facts, and all such facts are checked against their passages in one call
verify     every flagged fact is looked at again: stand, reword to what its passage states, or
           drop; what is kept is checked once more
write      the package, then the roll-up
```

A document of one unit (a chat session): triage by rule, the unit's entities then facts and cells
together, nothing to reconcile, the unit summary is the abstract, one support call, verify, write.
About four calls instead of twenty-five.

## Rules

- **Quote gate.** A stored quote is a verbatim slice of the document. Located as `exact`,
  `normalised`, `unwrapped`, or `words`; rejected as `paraphrase`, `not_found`, or `empty`.
- **Salience.** A unit that calls an entity major makes it a document-major; nothing else promotes
  or demotes, except a major with nothing to summarise (no facts, no cells) falls to minor.
- **Minors have no node.** A minor's fact rides to the major it concerns: the subject major
  (forward) or the major it points at (inverse); a minor's fact tied to no major is dropped.
- **Mentions are not written.** A node id is a moniker and its first mention; a fact's span comes
  through them; nothing else needs the record.
- Predicates stay as the model wrote them; a controlled list is Step 2's.

## Output

One package per document at `packages/<corpus>/<file>/<file>.jsonl`, one record a line under a
`record` field: `document`, `unit`, `piece`, `node`, `alias`, `edge` (`appears_in`, `has_unit`),
`profile`, `cell`, `abstract`, `adjudicated_fact`, `attribute`, `contradiction`, `fact`,
`rejection`, `ledger`, `candidate`, and a `completion` with the counts. A `roll-up.txt` is written
beside it. Run logs at the output root: `calls.jsonl` (every call with its cost), `retries.jsonl`,
`rejections.jsonl`, `ingest.log`, `receipt.json`.

Ids are readable: `<doc_id[:8]>:doc` for the document node, `:n<index>` for an entity, `:u<unit>:f<n>`
for a fact. All offsets are document offsets. A finished package is skipped on a rerun.
