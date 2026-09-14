# The global-layer discussion, 2026-09-13 (night)

The global thread read the handoff's documents and the 1.8 run's 81 packages, then brought the design
to Justin one question at a time. What the packages showed, then what he ruled, in the order ruled.
The design that came out is `docs/global-layer.md` (PROPOSED). Nothing was built.

## What the packages hold

- Every non-user chat entity is kind `thing` (1,001 of 1,001); chat nodes have one alias, no cells,
  no entity abstract. Across the 53 sessions of gpt4_2ba83207: 691 case-folded names, 20 in two
  sessions, only `user` in more.
- The three Oz books share 12 exact names; Scarecrow is `person` in books 1 and 3, `character` in
  book 2. Book 2 states Tip is Princess Ozma as facts with quotes and an adjudicated `identity`
  attribute; Princess Ozma (book 2) and Ozma (book 3) share a word, not a name.
- The ingestor's cast overlap (Jaccard over names sharing a unit) carried across books scores every
  pair between 0.04 and 0.12 (Toto against Billina 0.109, Tip against Ozma 0.079): the shared cast
  is always the same core. Co-occurrence does not unite on Oz.
- Papers: 285 names, 11 shared across the five, all generic, kinds disagreeing.
- No 8-character doc-tag collision among the 81 packages.

## Ruled by Justin

1. No rerun of the chat reading; the global layer takes over kind and salience.
2. Co-occurrence is for grouping document clusters and for keeping same-name entities from different
   works apart; it is not the uniter.
3. The global layer redefines the entity, its kind and other fields from what comes in.
4. Documents are entities; document entities are also global entities; they connect as instances;
   facts belong to the instance and the role it played; the entity holds a summary of the parts it
   played and links to its children. (Confirmed as the settled tree with the abstract sharpened to
   a summary of roles.)
5. The design works over the full corpus; the whole graph is loaded and a test filters at retrieval
   time.
6. The parent's name, kind and summary are written by a model call, never code alone.
7. Storage is SQLite; search is a linear scan of embeddings. Better indexes (HNSW, IVF, a k-means
   tree that Justin proposed and then withdrew) were discussed and set aside: "linear is fine".
   The vectors live in a `.npy` beside the database, held in memory for the scan.
8. Retrieval: linear scans over facts and narratives, then the join. The thread contested a
   filter-style intersection and proposed expansion (a hit pulls its neighbours through node,
   document and parent, then rerank); Justin asked how graph navigation is done, got the four steps
   (entry, expansion, rerank, pack) and a worked Tip example on the real records, and proposed
   prefixing each narrative sentence with its entity; adopted.
9. The cast is the ingestor's own definition (names sharing a unit); the 09-08 rarity formula is
   for document clusters.
10. The judge picks the parent's name (which name is most salient); the parent is a record separate
    from every instance.
11. Nomination is not exact-string: a similarity search over summaries and facts plus co-occurrence
    offers candidates loosely and the judge decides (Big Apple against New York).
12. On every attach the parent's abstract, aliases, name and instance list are updated.
13. For chats, a call decides whether an entity needs a parent at all; the rest stay leaves of the
    session. The chat reading judged salience poorly. Chats are living documents updated by nightly
    pulls, so the global layer owns salience for updates.
14. The Oz key: a public wiki, not hand labels. Wikipedia's list of Baum's Oz characters (CC BY-SA
    4.0) is the source; the Oz Fandom wiki refused the fetch. Character key and coverage of majors
    now; fact and narrative coverage later.
15. A Step 1 dataset is made from the ingestor run, documented like the Step 0 dataset.

## Superseded by these rulings

The plan's first-cut rule (case-folded name and kind; kind conflict stays apart; name by frequency;
count-sentence abstract). The ledger lines enter `docs/rulings.md` when the design note is accepted.
