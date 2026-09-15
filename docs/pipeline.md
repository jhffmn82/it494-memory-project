# ThreadAtlas, start to finish

The three pipelines as they ran (extractor 1.8, ingestor 1.8, global layer, 2026-09-15). Each
is one Kaggle notebook; each reads the one before it through a published dataset and nothing
else. The significant steps, the decisions behind them, the gates that can fail, the calls each
document costs, and what each stage writes. Detail is in `docs/extractor.md`,
`docs/ingestor.md`, `docs/global-layer.md`; field schemas in `dataset/step0/SCHEMA.md`,
`dataset/step1/SCHEMA.md`, SCHEMA.md (the serving store); the rulings and their dates in
`docs/rulings.md`.

```
raw files --extractor--> documents / units / pieces --ingestor--> one package per document
          (Step 0)       text + split plan + dates    (Step 1)     nodes, facts, cells, abstracts

one package per document + Step 0 text --global layer--> threadatlas.sqlite + threadatlas.npy
                                                          parents, collections, wiki; build.sqlite

threadatlas.sqlite + threadatlas.npy --retrieval (its own pipeline, docs/retrieval.md)--> context
```

Rules that hold in every stage:

- One model interface, `generate(prompt, schema)`: every call logged with model, tier, tokens,
  seconds and cost; a reply that does not fit its schema gets one retry with the error appended,
  then a logged rejection. Models: `gpt-5.6-luna` reads, checks and writes prose;
  `gpt-5.6-terra` judges, folds and adjudicates. Flex tier, priced by the tier that served.
- The model never returns an offset; code locates what it copies. Nothing the model asserts
  reaches an output without a code check: a boundary must copy real text, a quote must slice
  from the document, a parent's name must be one an instance carries.
- Nothing is overwritten and nothing is edited after it is written; a correction is a new record.
- Every document, unit and fact is dated; no supersession this fall, every dated fact is served.
- A spending stop per run; a dead key is fatal, never a corpus of empty records.

## 1. Extractor (Step 0): raw bytes to a dated split plan

**In:** the raw dataset, one folder per corpus with a manifest (sha256 per file), 24,071 files.
**Out:** `documents.jsonl` (text, title, author, `source_class`, `occurred_at`, flags),
`units.jsonl` (character ranges, dated), `pieces.jsonl` (kind per range), `receipt.json`.
All offsets are character indices into `documents.text`, one coordinate system for every later
quote. `doc_id` is the sha256 of the bytes; re-ingesting the same file is a no-op.

**The one rule:** the extractor sees a raw file and nothing else. The format is sniffed from the
bytes; no filename convention, no per-corpus branch, no hand-written rule for a publisher's
boilerplate.

```
sniff       PDF (text layer, PyMuPDF) | chat JSON (one block per turn: SESSION <id> TURN <n> <time>,
            then role: content) | UTF-8 text
chat        no call: each turn that says something is one piece and one unit, kind user|assistant,
            its own timestamp; the document takes the earliest; title = session id, author null,
            source_class record; empty sessions and empty turns skipped and counted
document    the numbered non-blank lines (by sentence when a PDF puts one word a line) in one Luna
            call, asking for
              metadata    source_class, title, author, source        (a pointer + the value)
              works       every separate work and the line stating when it was written
              toc_count   how many pieces the contents promise
              regions     front_matter | body | notes | references | appendix | license
              pieces      chapters, sections, scenes                  (pointer = line number + copied text)
            flags -> one retry on Luna; still flagged -> one try on Terra if under 80,000 tokens;
            keep the answer with a body region and the fewest flags
gates       pointer: the copy must name the line (the line itself, its first 8 words, a run of 5+
              words, or a 2-line heading copied whole; 5 words so CHAPTER I cannot answer for
              CHAPTER II); wrong number but text nearby -> recovered and counted; text nowhere ->
              dropped and counted
            metadata: a substring of the line; a date's year must be on its line; failure -> null + flag
            tiling: pieces cover the text, no gaps, no overlaps; every unit slice non-empty
            shape (a flag, never a drop): no body region; piece count != toc_count; one piece
              holds most of the body (added after Metamorphoses left 97 percent in its last unit)
date        a piece takes its work's date (written, else first published; never a translation,
            edition or ebook release); a document its earliest unit's. From the page when the
            model pointed at a line with the year on it; else one Luna web-search call by title
            and author, the URL kept in the flags. Forms: YYYY | YYYY-MM | YYYY-MM-DD | a turn's
            timestamp | a signed year with a year zero (-0404 = 405 BC) | ~ approximate | a/b range
units       sub-split: a piece over CAP_WORDS 4,000 goes back as numbered lines, cut where the
              model points, up to 3 rounds; one it cannot break stays whole and is flagged
            merge short: a piece under SHORT_WORDS 100 is offered with its text: it joins the
              piece before, the piece after, or stands alone
            group: the outline (every piece with kind, word count, heading) goes back; the model
              groups consecutive pieces into units, a section with its subsections, never two
              peers because they fit; code checks order and coverage, dissolves a group over the
              cap, cuts a group at any change of kind or of date
```

Calls per document: chat 0; read document 1 read (+ up to 2 on a flag) + 1 web search per
work not dated from the page + 1 per sub-split round per over-cap piece + 1 merge-short when
any piece is short + 1 group. Six documents in parallel, sub-splits eight at a time.

Guarantees verified at export on every document, not asserted: units and pieces each tile the
text; a unit is one kind and one date; `unit_id` unique; every piece points at a unit of its own
document. Not claimed: a gold segmentation or a gold date table. Measured (1.8): 24,071 documents
(23,882 chats in 500 histories, 189 read documents), 251,446 units, $8.24 (a median of $0.0081
per read document), 156 of 405 works dated from the page and 237 by search, 6 escalations to
Terra, 103 of 189 read documents flagged, 135 mismatched pointers of which 50 dropped, 15
undated units.

## 2. Ingestor (Step 1): one document to one package

**In:** `documents.jsonl`, `units.jsonl`, `pieces.jsonl`. **Nothing looks at a second document.**
**Out:** one package per document, one record a line: `node`, `alias`, `edge` (`appears_in`
with the units, `has_unit`), `fact`, `cell`, `abstract`, `adjudicated_fact`, `attribute`,
`contradiction`, `rejection`, `ledger`, `candidate`, `completion` (the counts). Ids are readable:
`<doc_id[:8]>:doc` for the document node, `:n<i>` an entity, `:u<unit>:f<n>` a fact.

### A book or paper (many units)

```
triage      one Luna call: which unit kinds are not the work; front matter and license go by
            rule; an answer that would leave out more than half the document is ignored
per unit    entities   one call: name, kind, salience (major | minor), surface forms; kept only
(4 units               if a form is found in the unit's text; a fact's subject must be listed
at a time)  facts      one call: subject, predicate, object, qualifiers, verbatim quote; kept only
                       if the quote locates in the unit: exact | normalised | unwrapped | words;
                       else rejected and logged as paraphrase | not_found | empty | duplicate |
                       self_reference | unlisted_subject
            cells      one call: a unit summary and one narrative cell per major
reconcile   unit-local entities become document entities, bottom up (below)
fold        one Terra call: the abstract (up to 400 words) from the unit summaries; one Terra
            call per major: its abstract from its cells; a major with no facts and no cells is
            demoted
adjudicate  one Terra call per major with ADJUDICATE_MIN_FACTS 4 or more facts: consolidated
            facts, attributes and contradictions, each citing the raw facts behind it; the
            other majors' raw facts checked against their passages, VERIFY_BATCH 60 a call
verify      every flagged fact once more on Luna: stand | reword to what the passage states |
            drop; a rewording checked once more; a flagged fact no verdict reaches is dropped
write       the package; the document node gets the record facts (has_title, has_author,
            has_date, has_source_class, belongs_to_history) from the export, no call, no quote
```

**Salience.** A unit's entity call says major or minor for that unit; a major in any unit is a
major of the document (ruling 09-07); abstract naming and proper names do not promote; a major
with nothing to summarise is demoted. **Minors have no node.** A fact lands on the major that is
its subject (forward) or under the major it points at (inverse), with the minor's name as its
value; a fact between two minors is not stored (except in a chat, below).

**Reconcile, within one document.** Two named locals with the same proper name and kind are one
entity with no call, unless their `is_a` conflict (then a ledger row `unsure`). Every other pair
is nominated by one of three reasons, tiered:

```
shared_surface   a surface form in common                       tier 1.00
is_a_link        one's is_a names a surface form of the other   tier 0.85
shared_word      a word of the name in common                   tier 0.50
name   = 1.0 for shared_surface, else difflib ratio of the normalised names
cooc   = |cast(a) & cast(b)| / |cast(a) | cast(b)|      cast = the other entities' names in
                                                         the local's own unit
score  = 0.7 * name + 0.3 * cooc                         dropped under SIMILAR_ENOUGH 0.35
```

Never paired: two locals of one unit (the unit already listed them as two things); a pair the
judge ruled different, transitively over clusters (decisions 44 and 51); a pair with no unit-major
in it; an unnamed thing against the entity its parenthetical anchors it to ("car (Sam's car)"
against Sam). Round by round: every entity still in consideration is scored against every other,
the pairs sorted by (tier, score) descending, each taken with both sides leaving the round; the
round's pairs go to Terra ten a call, each cluster's dossier sent once; `same` unites (union-find),
`different` stays apart and is remembered, `unsure` waits for one last look, where unsure means
apart. Every verdict is a ledger row with its evidence; every scored pair a candidate row.

Calls per book or paper: 1 triage + 3 per kept unit + ceil(pairs / 10) per reconcile round + 1
fold + 1 per major (abstract) + 1 per major with 4+ facts (adjudicate) + ceil(facts / 60)
(support) + the correction calls; about twenty-five for a short book. A document of one unit:
no triage, entities then facts and cells together, nothing to reconcile, the unit summary is the
abstract, a major's own cell its abstract, every fact in one support call; about four calls.

### A chat session

```
read        one Luna call (medium effort) over all turns, a session over SESSION_WINDOW 40,000
            characters read in stretches of whole turns; asks for what the user says of their
            own life (plus one stated fact per user sentence that states a detail, the sentence
            as its object), the specifics the assistant gives (names, numbers, amounts, steps,
            options), and a summary; each fact names its turn; kept only if its quote locates in
            that turn and its subject is the user, appears in the turn, or shares a word with it
entities    one per name the reading used; the same name in two turns is one entity, no judge
salience    one Luna call over the summary and every entity with its facts: a kind (one
            lowercase word, never thing; a thing is refused and left null) and major | minor;
            the user stays a major person; an entity the reply leaves out is minor
nodes       a major becomes a node with its facts; a minor gets no node, its facts stay on the
            session's document node with direction mentioned and the name in
            provenance.subject_name
abstract    the reading's summary, no call; no cells, no fold, no entity abstracts
support     ceil(facts / 60) calls; verify; write
```

Calls per session: 1 read per 40,000-character window + 1 salience + the support and
correction calls; about half a cent a session, $110 for all 23,882.

Measured (1.8 over the 81 test documents, 09-14): $5.47, 1,784 calls, 1 schema retry, 6,929
facts of which 6,605 quoted and every quote slices at its offsets, 324 record facts, 1,113
mentioned facts, 1,534 nodes (643 chat nodes in 53 kinds).

## 3. Global layer: every package to one store, a tree of parents, a tree of collections

**In:** the Step 1 dataset (one JSONL per record type) and Step 0's `documents.jsonl` (the text,
read at load and not kept). **Out:** `threadatlas.sqlite` (the serving store), `threadatlas.npy`
(float16, 384 dimensions, one row per sentence), `build.sqlite` (`pair`, `merge`),
`receipt.json`, the wiki pages.

**What a parent is.** A record owned by no document: a name and a kind chosen from its
instances, the union of their aliases, one summary line per instance tagged with the instance's
id. It asserts nothing about the world, is never the source of a fact, and is written once, after
the clusters exist. Its vector plays no part in identity: nomination and judgement run over the
children, which are immutable, so no model-written prose feeds back into resolution.

```
load        every Step 1 row the store keeps; each quote re-sliced from the Step 0 text at its
            offsets, the load refused on the first mismatch; one search row per record (a fact's
            clause and quote, a cell's text, an abstract's text); counts checked against the
            completion records
embed       bge-small-en-v1.5 (fastembed, CPU, one call over every text): one vector per fact
            rendered as a line (clause, date, title), one per narrative sentence prefixed
            "entity, title: ", and one per child's text
child       an entity node that is not the document's own node and not the user of a chat;
            child text = name, kind, aliases, document title, abstract (else up to 12 facts)
cast        from the Step 1 appears_in edges: the folded names of the other children a child
            shares any unit with; rarity(name) = log((N + 1) / (df + 1)), N documents loaded,
            df documents holding the name
nominate    candidate pairs of children, each once, by three routes:
              vector    each child's NEAREST 8 other-document children by cosine (block matrix
                        products, 2,048 rows at a time; two children of one document never
                        pair by vector)
              lexical   every two children of different documents sharing a name or a naming
                        alias (an alias names when a word after any leading article is
                        capitalised), through one index
              identity  every is_a link between two children of one document
            scored:
              lexical    1 if the names or naming aliases intersect, else 0
              vector     cosine of the two child texts
              cast       |cast(a) & cast(b)| / |cast(a) | cast(b)|
              cast_rare  the same with each name weighted by rarity
              identity   1 for an is_a link
            OFFERED when lexical fires, or identity fires, or vector >= VECTOR_FLOOR 0.75
            (the floor set 09-14 from the cosine distribution and pairs read by eye; frozen)
cluster     log n bottom up over a union-find; the offered pairs sorted by the tuple
            (identity, lexical, vector) descending:
              every child its own cluster
              round: walking the pairs strongest first, a pair is taken when neither of its
                clusters is taken this round (pairs disjoint, at most one per cluster); the
                whole round is judged in parallel (16 in flight); pairs ruled same unite; the
                next round is drawn from the merged pool; until a round finds no pair
              skipped: a pair whose children already share a cluster
              blocked: a pair between two clusters where any member of one was ruled different
                from any member of the other
judge       one call per pair, Luna when either side is a chat, else Terra, medium effort:
              each side = the nominated instance's text, then up to 5 instances already united
              with it (most facts first) as context only; "appears beside" = the cast as names,
              shown only in the arm that includes it; texts and names, never a score
              same | different with a one-sentence reason about the two instances themselves;
              a disagreement in kind or role is not a reason for different, a contradiction in
              identity is; a part, possession, place or event of the other is different
mentions    a final pass: titled documents' own nodes stay out of the clustering; each finished
            cluster is offered at most one document, by a member's name or naming alias equal
            to the title, else by the member text nearest the document's abstract at
            DOCUMENT_FLOOR 0.85; the judge rules with the document as the other side; a cluster
            ruled same becomes the document's children, the document's node its anchor, the
            parent named by the title with kind document
write       one parent per cluster: a cluster of one copied from its child, no call; two or more
            get one Luna call shown up to 20 instances (most facts first) that picks the name and
            kind from what the instances carry (a name no instance carries is refused) and writes
            one line per instance; instance_of per child; every pair with its signals and verdict
            and every union in order to build.sqlite; the parents' summary sentences join the
            sidecar
invariants  every up-edge points at a written parent; every child has an up-edge; else the run stops
collect     every parent held by 2+ documents seeds a group of those documents; groups merge
            when the smaller shares half its documents with the other; one Luna call per group
            names the collection and writes its abstract from the documents' abstracts and the
            shared parents; a document may belong to several collections
wiki        rendered from the store and nothing else: the entity page (the parent's lines; per
            instance its abstract and its cells under their unit labels; the consolidated facts
            opening to raw facts and quotes), the document page, the portal (every entity the
            collection holds, by documents holding it then facts), the collection figure
            (collections as hubs, documents as leaves); file names carry the record's id
```

Why bottom up in rounds: the count of candidate pairs is bounded by nomination (8 nearest plus
name matches plus links per child), not n squared; every child starts on equal footing and order
does not decide correctness; one wrong `same` chains two entities, so only judged pairs join, a
`different` is a constraint the clusters keep, and every cluster's size is an instrument. Showing
the judge whole clusters chained 21 of 54 clusters in the first run; the pair-focused prompt
brought that to 0.

Calls per build: one judge call per pair reaching a round (about 2,700 on the test store, over
about 30 rounds) + one per cluster offered a document + one per parent of two or more + one per
collection. Measured (keyed run over the test store): $2.4, 20 to 45 minutes; about 1,313
parents, 80 unions; Tip and Ozma united, Toto and Billina apart, no chained cluster; 15,758
vectors; 4 collections named by the call ("Oz series").

**The ablation.** Nomination and the floor never change; the arm is what the judge sees: L+V+I
(the two texts alone) against L+V+I+C (the texts plus the casts). Each arm is a full build over
the scored subset; a replay of logged verdicts under the other arm is a fixed-verdict sensitivity
check, not the arm. Scored as attachment accuracy against Wikipedia's list of Baum's Oz
characters (CC BY-SA 4.0), matched to children by alias, the hand-matched remainder counted; the
parent-off retrieval arm on LongMemEval says what the tree buys.

## What is not built

The retrieval pipeline (drafted; the rule is `docs/retrieval.md`), the Wikipedia Oz key and its
scorer, the harnesses, the nightly path for a new document, a second look for partners by a
merged cluster, supersession, the refold of a parent when its children change.
