# ThreadAtlas, start to finish

The three pipelines as they ran (extractor 1.8, ingestor 1.8, global layer, 2026-09-15). Each
is one Kaggle notebook; each reads the one before it through a published dataset and nothing
else. The significant steps, the gates that can fail, and what each writes. Detail is in
`docs/extractor.md`, `docs/ingestor.md`, `docs/global-layer.md`; field schemas in
`dataset/step0/SCHEMA.md`, `dataset/step1/SCHEMA.md`, SCHEMA.md (the serving store).

```
raw files --extractor--> documents / units / pieces --ingestor--> one package per document
          (Step 0)       text + split plan + dates    (Step 1)     nodes, facts, cells, abstracts

one package per document + Step 0 text --global layer--> threadatlas.sqlite + threadatlas.npy
                                                          parents, collections, wiki; build.sqlite

threadatlas.sqlite + threadatlas.npy --retrieval (its own pipeline, docs/retrieval.md)--> context
```

Every model call in every stage goes through one function, `generate(prompt, schema)`, and is
logged with its model, tier, tokens and cost. Models: `gpt-5.6-luna` for reading and checking,
`gpt-5.6-terra` for judging and folding; Flex tier. Nothing the model asserts reaches an output
without a code check: a boundary must copy real text, a quote must slice from the document, a
parent's name must be one an instance carries.

## 1. Extractor (Step 0): raw bytes to a dated split plan

**In:** the raw dataset, one folder per corpus with a manifest (sha256 per file). 24,071 files.
**Out:** `documents.jsonl` (text, title, author, `source_class`, `occurred_at`, flags),
`units.jsonl` (character ranges, dated), `pieces.jsonl` (kind per range), `receipt.json`.
All offsets are character indices into `documents.text`; one coordinate system for every later
quote.

```
sniff       PDF (text layer, PyMuPDF) | chat JSON (one block per turn, SESSION/TURN/time line) | UTF-8 text
chat        no call: each turn that says something is one piece and one unit, kind user|assistant,
            its own timestamp; the document takes the earliest; title = session id, source_class record
document    one Luna call over the numbered non-blank lines, asking for
              metadata    source_class, title, author, source   (pointer + value)
              works       every separate work and the line stating when it was written
              toc_count   how many pieces the contents promise
              regions     front_matter | body | notes | references | appendix | license
              pieces      chapters, sections, scenes             (pointer = line number + copied text)
            flags -> one retry on Luna; still flagged -> one try on Terra if under 80,000 tokens;
            keep the answer with a body region and the fewest flags
gates       pointer: the copy must name the line (the line, its first 8 words, a run of 5+ words,
              or a 2-line heading); off-by-a-few recovered from the copy; text nowhere -> dropped
            metadata: substring of the line; a date's year must be on its line; failure -> null + flag
            tiling: pieces cover the text, no gaps, no overlaps; every unit slice non-empty
            shape (flag, never drop): no body region; piece count != toc_count; one piece holds most of the body
date        a piece takes its work's date; a document its earliest unit's. From the page when the
            model pointed at a line with the year on it; else one Luna web-search call by title and
            author (URL kept). Forms: YYYY | YYYY-MM | YYYY-MM-DD | turn timestamp | signed year with
            a year zero (-0404 = 405 BC) | ~ approximate | a/b range
units       sub-split: a piece over CAP_WORDS 4,000 goes back as lines, cut where pointed, 3 rounds max
            merge short: a piece under SHORT_WORDS 100 joins before, after, or stands
            group: the outline goes back; the model groups consecutive pieces into units; code checks
              order and coverage, dissolves a group over the cap, cuts at any change of kind or date
```

Guarantees verified at export on every document: units and pieces each tile the text; a unit is
one kind and one date; `unit_id` unique; every piece points at a unit of its own document.
Measured (1.8): 24,071 documents (23,882 chats in 500 histories, 189 read documents), 251,446
units, $8.24, 6 escalations to Terra, 103 of 189 read documents flagged, 15 undated units.

## 2. Ingestor (Step 1): one document to one package

**In:** `documents.jsonl`, `units.jsonl`, `pieces.jsonl`. Nothing looks at a second document.
**Out:** one package per document: `node`, `alias`, `edge` (`appears_in`, `has_unit`), `fact`,
`cell`, `abstract`, `adjudicated_fact`, `attribute`, `contradiction`, `rejection`, `ledger`,
`candidate`, `completion`. Ids are readable: `<doc_id[:8]>:doc`, `:n<i>`, `:u<unit>:f<n>`.

A book or paper (many units):

```
triage      one call: which unit kinds are not the work (front matter and license by rule);
            an answer that would drop more than half the document is ignored
per unit    entities   name, kind, surface forms; kept only if a form is found in the unit
(4 at a     facts      subject, predicate, object, qualifiers, verbatim quote; kept only if the
time)                  quote locates: exact | normalised | unwrapped | words; else rejected as
                       paraphrase | not_found | empty | duplicate | self_reference | unlisted_subject
            cells      a unit summary and one narrative cell per major
reconcile   within the document only: same proper name and kind unite with no call unless their
            is_a conflicts; other pairs (shared surface form, one said to be the other, shared
            name word) scored 0.7 name + 0.3 co-occurrence, dropped under 0.35, judged on Terra
            ten pairs a call: same | different | unsure; every verdict a ledger row
fold        the abstract from the unit summaries (Terra); an abstract per major; a major with
            no facts and no cells is demoted
adjudicate  a major with 4+ facts: one Terra call consolidates them into adjudicated facts,
            attributes and contradictions, each citing the raw facts behind it; fewer: raw
            facts checked against their passages, 60 a call
verify      every flagged fact once more on Luna: stand | reword to what the passage states | drop;
            a rewording checked again; no verdict -> dropped
write       the package; the document node gets the record facts (has_title, has_author,
            has_date, has_source_class, belongs_to_history) with no quote, from the export
```

A document of one unit: no triage, entities then facts and cells together, nothing to
reconcile, the unit summary is the abstract; about four calls instead of twenty-five.

A chat session:

```
read        one Luna call over all turns (40,000-character stretches of whole turns); each fact
            names its turn; kept only if its quote locates in that turn and the subject is the
            user, appears in the turn, or shares a word with it; every subject is an entity,
            the same name in two turns one entity, no judge
salience    one Luna call: the summary and every entity with its facts -> a kind (one lowercase
            word, never thing) and major | minor; the user stays a major person
nodes       a major becomes a node with its facts; a minor gets no node, its facts stay on the
            session's document node with direction mentioned and provenance.subject_name
support     one call over every fact; verify; write. No cells, no fold, no entity abstracts
```

Rules that hold everywhere: a stored quote is a verbatim slice, no ellipsis; minors have no
node; `valid_from` only when the quote states it, `occurred_at` copied from the unit;
contradictions resolve within a document only; predicates stay as written, snake_case.
Measured (1.8 over the 81 test documents): $5.47, 1,784 calls, 6,929 facts of which 6,605
quoted and every quote slices at its offsets, 324 record facts, 1,113 mentioned facts, 1,534
nodes; a chat session about half a cent.

## 3. Global layer: every package to one store, one tree of parents, one tree of collections

**In:** the Step 1 dataset (one JSONL per record type) and Step 0's `documents.jsonl` (text,
read at load and not kept). **Out:** `threadatlas.sqlite` (the serving store: `document`,
`unit`, `node`, `alias`, `fact`, `adjudicated_fact`, `cell`, `abstract`, `parent`,
`instance_of`, `collection`, `document_in`, `vec_header`, `vec_row`, `search` FTS5),
`threadatlas.npy` (float16, 384-d, one row per sentence), `build.sqlite` (`pair`, `merge`),
`receipt.json`, the wiki pages.

```
load        the Step 1 rows into the store; every quote re-sliced from the Step 0 text at its
            offsets, the load refused on the first mismatch; one search row per record (a fact's
            clause and quote, a cell's text, an abstract's text); counts checked against the
            completion records
embed       bge-small-en-v1.5 (fastembed, CPU): one vector per fact rendered as a line, per
            narrative sentence prefixed "entity, title: ", and one per child
child       an entity node that is not the document's own node and not the user of a chat; a
            titled document's node is a child too (flagged document), kept out of the clustering
            until the mentions pass
nominate    candidate pairs of children, each once:
              NEAREST 8 other-document children by cosine (block matrix products)
              every two children sharing a name or a naming alias (an index over proper forms)
              every is_a link between two children of one document
            scored: lexical (name or alias match), vector (cosine), cast (Jaccard of the names each
            appears beside, plain and rarity-weighted log((N+1)/(df+1))), identity (is_a)
            OFFERED when lexical or identity fires or the vector clears VECTOR_FLOOR 0.75
cluster     log n bottom up over a union-find:
              every child its own cluster; offered pairs ranked by the tuple (identity, lexical, vector)
              round: each cluster takes its best eligible partner, the pairs disjoint; the round is
                judged in parallel (WORKERS 16); pairs ruled same unite; repeat until a round
                finds no pair
              skipped: a pair whose children already share a cluster
              blocked: a pair between clusters that hold any pair ruled different
judge       one call about the pair's two instances (name, kind, aliases, abstract, up to 12
            facts; the cast as names when the arm includes it); each side also lists what is
            already united with it, as context only; Luna for a chat pair, Terra otherwise;
            same | different with a reason; texts, never scores
mentions    a final pass: each finished cluster is offered at most one document, by a member's
            name or naming alias equal to the title, else by the member text nearest the document's
            abstract at DOCUMENT_FLOOR 0.85; the judge rules with the document as the other side;
            a cluster ruled a mention becomes the document's children, the document's node its
            anchor, the parent named by the title, kind document
write       one parent per cluster: a cluster of one copied from its child, no call; two or more
            get one Luna call that picks the name and kind from what the instances carry (a name
            no instance carries is refused) and writes one line per instance; instance_of per
            child; pair and merge rows to build.sqlite; the parents' summary sentences join the
            sidecar
invariants  every up-edge points at a written parent; every child has an up-edge; else the run stops
collect     every parent held by 2+ documents seeds a group of those documents; groups merge when
            the smaller shares half its documents with the other; one Luna call names each
            collection and writes its abstract from the documents' abstracts and the shared
            parents; a document may belong to several collections
wiki        rendered from the store and nothing else: entity page (parent lines; per instance its
            abstract and cells under unit labels; consolidated facts opening to raw facts and
            quotes), document page, portal (every entity the collection holds, by documents
            holding it then facts), the collection figure (collections as hubs, documents as leaves)
```

The arm for the ablation is what the judge sees: L+V+I (texts alone) against L+V+I+C (texts
plus casts); nomination and the floor never change. Measured (the test store, keyed run):
about 2,700 pairs judged in about 30 rounds, $2.4, 20 to 45 minutes; about 1,313 parents, 80
unions; Tip and Ozma united, Toto and Billina apart, no chained cluster; 15,758 vectors; 4
collections named by the call.

## What is not built

The retrieval pipeline (drafted, `docs/retrieval.md`), the Wikipedia Oz key and its scorer, the
harnesses, the nightly path, a second look for partners by a merged cluster, supersession.
