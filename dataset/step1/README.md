# ThreadAtlas Step 1: Document Packages

What one language-model pass reads out of a document, one package per document: the entities
the document is about, every fact with a verbatim quote located at character offsets into the
document's text, a narrative cell per major entity per unit, the document's abstract, and an
abstract per major entity. **81 documents, 6,929 facts, every quoted fact proven to slice from
its document at its offsets**, produced by a public notebook for $5.47.

This release is the test set, not the corpus: the 81 documents the memory backend is being built
and tuned on before the full Step 0 corpus (24,071 documents) is read. They were chosen to cover
every input shape once: one user's whole chat history, the answer sessions of thirteen other
questions, three novels in a series, five research papers, one play, one benchmark novel. The
full corpus follows in batches once the layers above this one are tested.

## What is read, and what is never written

Step 0 split every document into dated units. Step 1 reads each unit and answers, per unit,
**who or what this unit is about, what it states about them, and what happened to each of them
here**. Nothing here looks at a second document. Three rules the release keeps, and verifies
rather than asserts:

- **Every fact read from the text carries a verbatim quote and the offsets where it lies.** A
  claim the model made that could not be found in its unit was rejected and logged, never
  stored. The 6,605 quoted facts all slice to their text; the 1,105 rejections are in the
  dataset with their category. The other 324 facts are the document record itself (title,
  author, date, source class, a chat's history), built from Step 0 with no model call and no
  quote, and say so in their provenance.
- **A fact is one its passage states.** After extraction, every fact was checked against its
  passage; a fact the passage does not state was reworded to what it does state or dropped. 486
  were dropped that way and are logged.
- **Nothing is merged across documents.** Every entity, fact and edge belongs to one document.
  A recurring character in three novels is three entities here; connecting them is the next step.

## Version 2: ingestor 1.8

The first version (1.7, 2026-09-13) read a chat session in one call and made every subject a
major of kind `thing`. This version adds one call per session after the reading that gives each
entity a kind (never `thing`) and marks it major or minor, keeps a minor's facts on the session's
own node as `mentioned` facts, and adds the document-record facts above to every document. The
chats went from 1,061 entity nodes to 643, with 53 distinct kinds. All 81 documents were rerun.

## Files

One file per record type, joined on `doc_id`, the sha256 of the document's bytes, the same key
as Step 0. Document rows carry no text; slice quotes from Step 0's `documents.jsonl`.

| file | rows | what it is |
|---|---|---|
| `documents.jsonl` | 81 | the document as the run saw it: identity, title, author, date, flags |
| `units.jsonl` | 879 | the units read, copied from Step 0 with each unit's kind |
| `pieces.jsonl` | 957 | the piece table, copied from Step 0 |
| `nodes.jsonl` | 1,534 | one row per entity, plus one per document; name and kind |
| `aliases.jsonl` | 4,746 | every surface form an entity was found under, with its first unit |
| `edges.jsonl` | 2,332 | which entities appear in which units, and the document's unit order |
| `facts.jsonl` | 6,929 | subject, predicate, object, and the verbatim quote with its offsets |
| `cells.jsonl` | 1,826 | a narrative per major entity per unit, and a summary per unit |
| `abstracts.jsonl` | 891 | one abstract per document and per major entity |
| `adjudicated_facts.jsonl` | 1,253 | a major entity's facts consolidated, each citing its raw facts |
| `attributes.jsonl` | 873 | the same consolidation's attributes, citing raw facts |
| `contradictions.jsonl` | 48 | facts of one entity that disagree, and which holds at the document's end |
| `rejections.jsonl` | 1,105 | every fact or entity turned away, with why |
| `ledger.jsonl` | 3,168 | every same-or-different verdict on a pair of unit-local entities |
| `candidates.jsonl` | 2,061 | every scored pair the reconciliation weighed, with both scores |
| `completions.jsonl` | 81 | each document's own counts and run statistics |
| `calls.jsonl` | 1,784 | every model call: stage, model, tier, tokens, seconds, cost |
| `attribution.jsonl` | 5 | the CC-BY papers whose text the facts quote |
| `receipt.json` | | the run's totals |

`SCHEMA.md` gives every field. `METHOD.md` explains how the reading works. `PROVENANCE.md` says
where the documents came from and under what license. `LIMITS.md` says what is known to be
wrong or thin.

## Quick start

```python
import json

def rows(name):
    for line in open(f"/kaggle/input/it494-threadatlas-step1/{name}.jsonl", encoding="utf-8"):
        yield json.loads(line)

nodes = {n["node_id"]: n for n in rows("nodes")}
facts = list(rows("facts"))

# every fact about Tip in The Marvelous Land of Oz, with its quote
for f in facts:
    if nodes[f["subject"]]["name"] == "Tip":
        print(f["predicate"], f["object"], "|", f["quote"][:80])

# prove a quote: slice it from Step 0's text at its offsets
texts = {}
for line in open("/kaggle/input/it494-threadatlas-step0/documents.jsonl", encoding="utf-8"):
    d = json.loads(line)
    texts[d["doc_id"]] = d["text"]
quoted = [f for f in facts if f["quote"] is not None]
f = quoted[0]
assert texts[f["doc_id"]][f["quote_start"]:f["quote_end"]] == f["quote"]
```

## What is in the release

| documents | count | facts | cells | entities | cost |
|---|---|---|---|---|---|
| LongMemEval sessions: one user's history (53) and 18 answer sessions of 13 other questions | 71 | 3,371 | 0 | 643 | $0.36 |
| Oz: The Wonderful Wizard of Oz, The Marvelous Land of Oz, Ozma of Oz | 3 | 2,253 | 1,034 | 374 | $3.29 |
| CC-BY papers on knowledge graphs and RAG | 5 | 909 | 551 | 309 | $1.16 |
| GraphRAG-Bench novel | 1 | 240 | 155 | 76 | $0.43 |
| Greek drama: The Bacchae | 1 | 156 | 86 | 51 | $0.24 |

Fact counts include each document's record facts. The chats' 3,371 are 2,258 on major entities
and 1,113 `mentioned` facts of minor entities carried by their session.

A chat session is read whole in one call, then one more call sorts its entities by kind and
salience; it gets facts and a session abstract but no cells and no entity abstracts. A book or
a paper is read unit by unit with cells, a reconciliation of its entities, an abstract per major
entity and a consolidation of each major's facts. `METHOD.md` says why. A chat costs about
$0.005; a novel $1.10 on average.

Across the release: 3,557 entities were named, 1,453 of them majors that carry facts and 2,104
minors that leave no node of their own; 24,903 mentions; 2,235 distinct predicates, the model's
own words in snake_case, never merged. Of the 7,422 facts that passed the quote gate, 6,605 are
stored with their quote, 331 fell with no major to stand under in a book or paper, and 486 were
dropped by the passage check.

## Provenance and license

The packaging, the schema and every derived row (entities, facts, cells, abstracts, logs) are
MIT. The quotes are verbatim text of the documents and keep their licenses: the Oz books and the
Bacchae are public domain in the United States, the chat sessions and the novel are MIT with
their notices, and the five papers are CC-BY, which requires attribution; `attribution.jsonl`
carries it. `PROVENANCE.md` gives this per corpus.

## How this was made

[ThreadAtlas Document Ingestor](https://www.kaggle.com/code/jhffmn/threadatlas-document-ingestor),
`threadatlas-ingestor 1.8`, one pass on 2026-09-14 over the Step 0 1.8 export, `gpt-5.6-luna`
for reading, sorting and checking and `gpt-5.6-terra` for judging, folding and consolidating,
every call on OpenAI's Flex tier. $5.47, 1,784 calls, about 2.8 hours of kernel time. Input:
[ThreadAtlas Step 0](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step0).

Part of the IT 494 directed project at Illinois State University, fall 2026.
