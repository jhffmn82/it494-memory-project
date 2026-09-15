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
