# The global layer, 2026-09-15: the wiki's shape

Continues `log/2026-09-14/global-layer.md`. Rulings and builds after midnight, in order.

- Cells on a wiki page sit under their unit's label (a chapter, or a chat turn's time); the
  facts panel shows the ingestor's consolidated facts, each opening to the raw facts and quotes
  behind it, and the raw facts one line per distinct claim where nothing was consolidated
  (Justin: "the fact lists look pretty bad"; Dorothy's 100 raw lines in book 1 became 24).
- The pages restyled: a header band, an accent colour, the facts in a card (Justin: "so bland
  and grey / monotone").
- Two drawings of the collections built for Justin to choose: an interactive map page (plain
  SVG and JavaScript, labels always shown after his check, the view fitted after the layout
  settles) and a static radial figure. Ruled: the static graph leads; the map stays as a page.
- A document page: the record, the abstract, the unit summaries under their labels, the
  entities in the document linking to their parents; the portal, the map and the entity pages
  link to it (Justin: "shouldn't the doc titles lead to the document page? we have document
  entities correct?").
- The portal lists every entity its documents hold, ranked by the documents holding it and
  the facts about it, a page written for each (Justin: "ALL the entities across all the
  documents in order of relevance"); the recurring set still seeds and names the collection.
- Kernel version 16 carries all of it; the mock-up in `docs/wiki/` is from the keyed run of
  version 15: the Oz portal, the three Oz document pages, the Ozma and Dorothy pages, the
  radial figure and the map.

Correction, minutes later: the push became kernel version 17, not 16; a version 16 was saved from the editor in between.

- Justin, on the version 17 keyed run: duplicate collection nodes in the figure. The store held three "Retrieval-Augmented Generation" collections (the five papers and two pairs inside them) and three meal-planning ones over the same sessions, because seed groups merged only at Jaccard 0.5 and a pair inside a set of five scores 0.4. The merge rule is now the overlap of the smaller group (a group inside a larger one always joins it): four collections on that store, the papers, the shopping sessions, the grocery sessions, the Oz books, and no document in two. Kernel version 18.
  Correction: the push became kernel version 19; a version 18 was saved from the editor in between.

## The reviewer's second pass, and the hardening

Justin brought two reviews from an adversarial judge. The first read the incremental attach and
is moot: no second pass, no parent rewritten on attach, no parent vector in nomination exist in
the batch build. The second read the batch build, kept the architecture ("I would not go back
to the previous second-pass attachment system") and asked for four fixes, all made:

- priority as hard tiers, a tuple (identity, lexical, vector), not a sum;
- merge provenance: a `merge` table with every union in order, and the up-edge's reason taken
  from the pair whose union first joined the child's cluster to another, not an arbitrary
  "same" pair;
- the rarity term nonnegative, log of (documents plus one) over (holders plus one);
- wiki file names carrying the parent's id, so two parents named alike never collide.

Also from the review and Justin ("fix the issues and simplify the code, there has been a lot
of complexity creep"): the interactive map page and the unused document-graph code are gone
(the static figure was ruled); the ablation is stated exactly in the notebook and the design
note (nomination fixed; the arm is what the judge sees: L+V+I against L+V+I+C; a replay of
logged verdicts is a sensitivity check, not an arm); the vector floor's provenance is written
down and the floor frozen before the key is scored; two invariants stop the run if broken.
`docs/global-layer.md` is rewritten to the batch build; SCHEMA.md gains the global side
(PROPOSED). Blocks now run 13 to 204 lines each, the wiki page the largest. Kernel version 20.

## Documents as parents of their mentions (Justin, 09-15)

"Mentions of books that become entities within the units aren't being merged with the
document entities and they should. This would go especially so for research papers that
mention each other." And: "obviously, the document entity is the parent, and the mention is
the child"; "that probably needs a final pass after the clustering ... since it wouldn't make
sense to pair documents and entities and then create parents." Built as the final pass in
block 13: titled documents stay out of the clustering; each finished cluster is offered at
most one document, by a member's name or naming alias equal to the title, else by the member
text nearest the document's abstract at 0.85; the judge rules with the document as the other
side; a cluster ruled a mention becomes the document's children with the document's own node
as its anchor, and the parent takes the document's title and the kind `document`. Dry run: The
Wonderful Wizard of Oz's parent holds book 1's node, book 1's entity for itself and book 2's
mention; each paper's node takes the paper's mention of itself; 6 of 1,344 clusters. Kernel
version 21.

- Justin: the document titles should lead to a document page (built), every entity should be listed on the portal by relevance (built), a breadcrumb up to the collection under the title (built), and on the colours: "the dark cream background is not great and border colors aren't making it better". The palette is a named choice of four (harbour, parchment, emerald, slate), rendered side by side for him; slate is the default: white paper, hair-line rules, the accent kept only for the small labels. Kernel version 22 carries the mentions pass, the breadcrumb and the palette.

- The slate scheme settled with Justin ("looks good"): white paper, a pale blue-grey header band, a light blue-grey tint on the header rule, the section rules and the facts card, the amber kept for the small labels. Kernel version 24; the mock-up in `docs/wiki/` is rendered in it.

- The lean serving store built (blocks 4 and 5 rewritten, 6, 7, 8, 13 to 16, 18 and 19 adjusted):
  fourteen tables and one `search` FTS5 table with a row per record (a fact's line and quote, a
  cell, an abstract); `fact` carries `subject_name` in place of `provenance`; the document's text
  is read from Step 0 at load to prove every quote and not kept; the casts are read from the
  Step 1 edges at build time; `parent` and `collection` keep derived fields only (instance and
  document counts are counted from `instance_of` and `document_in`); `pair` and `merge` go to
  `build.sqlite` beside the store. Dry run with the judge stubbed: 6,929 facts, 6,605 quotes
  checked, 9,646 search rows, 15,758 vectors, 1,344 parents, 4 collections, the figure, the
  portal, an entity page and a document page all render. Kernel pushed.

- Block 20 (retrieval) and block 21 (one question over the largest collection) written to the
  manual with its seven corrections; the master is `docs/retrieval.md`. Dry run over the Oz
  collection on the stubbed-judge store: a question answers in about a tenth of a second; both
  arms find entries (a parent summary tops the vector arm for "Who is Tip" and routes to its
  children; the keyword arm's top hits are the Emerald City cells and facts); the parent hop off
  removes the `parent` edge and the parent rows; each arm alone runs; 6,000 tokens pack 57 to
  74 whole records. A fact's packed line is its clause and its quote; the date and the title
  are the record's prefix, not repeated. `questions.jsonl` holds one line per question. The
  BGE query prefix is empty until the 14 tuning questions choose it. Kernel pushed.

- Justin: retrieval is not part of this notebook; a new pipeline imports the SQLite store and
  nothing else of the build. Blocks 20 and 21 moved out into `notebooks/threadatlas-retrieval.py`
  as a draft (not blocked, not run as a kernel); the global layer ends at the store, the build
  log and the wiki. Open: the vectors are in `threadatlas.npy` beside the store by the 09-13
  ruling, so the new pipeline reads two files from the dataset or the vectors move inside the
  database. The merge is the focus now.

- Justin: the dataset carries the SQLite and the array together; the retrieval pipeline reads both.

- `docs/pipeline.md` written at Justin's ask: the three pipelines start to finish, the significant
  steps, low prose. GPT's review of `docs/retrieval.md` (brought by Justin): the architecture stands;
  four edge-case rulings folded into the master and the draft (entry against record; the discount
  as a bias, not a guarantee; total orders with keys as tie-breaks; no document edge from an
  abstract, the parent edge only from a parent entry); the master is approved with them.

- GPT's second review of retrieval (brought by Justin, after reading `docs/pipeline.md`): the
  store holds an entity at three resolutions and the generic expansion flattened them. Ruled
  ("yes"): the same typed traversal from every entry (route, traverse, substantiate), no
  per-question routing, facts kept as entries, the bundle as a cell with its facts and quotes.
  Sections 4 to 7 of `docs/retrieval.md` rewritten; the draft `notebooks/threadatlas-retrieval.py`
  is behind the master (it still expands along node, document and parent) and follows when the
  pipeline is built.

- The Oz key built (Justin: "start on 1"): Wikipedia's "List of Oz characters (created by Baum)",
  revision 1374825486, fetched through the API and kept unedited; `scripts/build_oz_key.py` makes
  one entry per character (83 with a section, 17 from the minor list) with the heading, the main
  link, the bold terms and the hand aliases of `aliases-added.json` (53 across 30 characters, each
  counted; the book title was removed from Ozma's aliases so the document node cannot match).
  Block 15b matches the three books' children by folded name or alias (a name two characters share
  is dropped) and scores cross-document pairs: united, split, recall, wrong joins, parents per
  character; `oz-score.json` beside the store. On the dry store (the judge stubbed to same names):
  59 children matched, 12 characters in two or more books, 15 united, 15 split, recall 0.5, 0 wrong
  joins; the splits are the alias cases (Tip and Ozma, Saw-Horse, Glinda the Good, the Wonderful
  Wizard, the Guardian of the Gate). Dataset `jhffmn/it494-threadatlas-oz-key` published, attached
  to the kernel; kernel version 29. The first keyed run on the lean store is Justin's.
