# The global layer

PROPOSED 2026-09-13, rewritten 2026-09-15 to the build that runs (`notebooks/threadatlas-global-layer.py`).
The rulings behind it are in `docs/rulings.md` under "Entities, identity and the global layer" and
"Store and retrieval"; the discussion is in `log/2026-09-13/global-layer.md`, `log/2026-09-14/global-layer.md`
and `log/2026-09-15/global-layer.md`. The settled shape in `docs/entity-resolution.md` stands: nothing is
merged, a child belongs to one document, a parent asserts nothing about the world.

## What it is

One graph over everything loaded: chats, books and papers together; a test is a filter at retrieval
time on a set of documents, never a different build. The store is one SQLite file built from the Step 1
dataset and the Step 0 text, every quote re-sliced at load; the sidecar is one float16 array of
sentence vectors beside it; the parents are a tree over the documents' entities; the collections are a
tree over the documents. Search is a linear scan of the array.

## The parent

A parent is its own record, owned by no document: a name and a kind chosen from its instances, the
union of their aliases, a role summary of one line per instance tagged with the instance's id, and
the instance list. It is written once, after the clusters exist, by one call per cluster of two or
more instances; a name no instance carries is refused, and a cluster of one is a copy of its child
with no call. Its vector plays no part in identity: nomination and judgement run over the children,
which are immutable, so no model-written prose feeds back into resolution.

## The build, bottom up (ruled 2026-09-14)

```
load        every Step 1 record; a quote that does not slice from its text stops the load; FTS5
embed       one vector per fact line and per narrative sentence; one per child (an entity node
            that is not the document itself and not the user of a chat)
nominate    candidate pairs of children, each once: the NEAREST other-document children by
            vector (block matrix products), every two children sharing a name or a naming alias
            (an alias names when a word after any article is capitalised), and every is_a link
            between two children of one document; each pair scored on four signals: lexical,
            vector, cast (overlap of the names each appears beside, plain and rarity-weighted),
            identity; a pair is OFFERED when lexical or identity fires or the vector clears 0.75
cluster     log n bottom up: every child its own cluster; the offered pairs ranked by hard tiers
            (is_a, then a name match, then the cosine); each round every cluster takes its best
            eligible partner, the pairs disjoint; the round is judged in parallel; the pairs
            ruled same unite; a pair whose children share a cluster is skipped; a pair between
            clusters holding any pair ruled different is blocked; until a round finds no pair
judge       one call about the pair's two instances, each shown with what is already united
            with it as context only; texts and casts as names, never scores; same or different
            with a reason; every pair and verdict logged
write       the parents; every union logged in `merge`
mentions    a final pass: titled documents stay out of the clustering; each finished cluster is
            offered at most one document, by a member's name or naming alias equal to the title,
            else by the member text nearest the document's abstract at 0.85; the judge rules with
            the document as the other side; a cluster ruled a mention becomes the document's
            children, the document's own node its anchor, the parent named by the title
collect     a collection per body of work: every parent held by two or more documents seeds a
            group; groups merge when the smaller shares half its documents with the other; one
            call names the collection and writes its abstract from the documents' abstracts and
            the shared parents; a document may belong to several
```

Order does not decide correctness: every child starts on equal footing and the rounds are drawn
from the merged pool. Grouping is transitive, so one wrong "same" chains two entities; only judged
pairs join, a "different" is a constraint the clusters keep, and every cluster's size is an
instrument. After the build two invariants hold or the run stops: every up-edge points at a written
parent, and every child has an up-edge.

## The ablation, exactly

The signals `lexical`, `vector` and `identity` nominate; `cast` never does. The arm is what the
judge sees: L+V+I shows the two entities' texts alone; L+V+I+C shows also the names each appears
beside. The question is whether relational evidence buys anything on top of an embedding nomination
and a language-model judge. Each arm is a full build over the scored subset (the three Oz books
against the Wikipedia key; the held-out histories the harness scores); a replay of logged verdicts
under another arm is a fixed-verdict sensitivity check, not the arm, because a verdict was given
with the clusters as they stood. The vector floor was set on 2026-09-14 from the cosine distribution
over the test store and a handful of pairs read by eye, and is frozen before the key is scored.

## The store and the wiki

The serving store is lean (ruled 2026-09-15; SCHEMA.md, the serving store): what a question or
a page reads and nothing else. `document` without its text, `unit`, `node`, `alias`, `fact`,
`adjudicated_fact`, `cell`, `abstract`; `parent`, `instance_of`; `collection`, `document_in`;
`vec_header`, `vec_row`; and `search`, one FTS5 row per record. Every quote is sliced against
the Step 0 text at load and the load stops on a mismatch. The build's evidence, `pair` and
`merge`, goes to `build.sqlite` beside it; the casts are read from the Step 1 edges at build
time. The query path over the store is `docs/retrieval.md` (block 20): keyword and vector entry
scans inside the filter fused by rank, one hop along the entity, the unit and the parent, a
rerank by each record's own score, whole records packed to a budget, one log line per question.
The wiki is four page types rendered from the store and nothing else: the
entity page (the parent's lines; a section per instance with its abstract and its cells under their
unit labels; the consolidated facts opening to their raw facts and quotes), the document page, the
portal (the collection's name and abstract; its documents; every entity they hold by relevance), and
the collection figure (collections as hubs, documents as leaves). File names carry the record's id,
so two parents named alike never collide.

## Not built this fall

The nightly path (a new document attached against the parents that exist), an approximate index
for nomination at the full corpus (exact search is kept for the measurement), and any second look
for partners by a merged cluster.

## Gate, Sep 20

Parents, store and vectors over the test packages with the schema written down: met on Kaggle on
2026-09-14. The key and its scorer are the next instrument.
