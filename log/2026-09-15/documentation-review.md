# Documentation review, 2026-09-15

At Justin's ask. Every master document read against the code that runs
(`notebooks/threadatlas-global-layer.py` version 24, ingestor 1.8, extractor 1.8) and against
the rulings through today. Per file: what is wrong, what is missing, the fix. A line marked
**contradiction** is a place two documents disagree with each other. Nothing here was applied;
the fixes are proposed in the order to make them.

## Verdict

The Step 0 and Step 1 documentation is sound and current. Everything above them (the global
layer, the store, the sidecar, the wiki, retrieval) is described in three different states
across seven files: the September 8 design (attach on name and co-occurrence, an alias set
hand-labeled), the September 13 first cut (case-folded name and kind), and the September 14
build (bottom-up clustering with a judge, a Wikipedia key, collections, a wiki that exists).
Only `docs/global-layer.md`, `docs/rulings.md` and the logs say the third. A reader opening
README, RESEARCH or the proposal is told the first. Today's lean-store ruling changes the
schema again and none of the seven says it yet.

## README.md

- "the global layer: silent parents over document-local entities, attached on name and
  co-occurrence" and "attachment accuracy against the Oz alias set, name-only versus name plus
  co-occurrence": stale. The global layer clusters document-local entities bottom up through a
  judge; the key is Wikipedia's Oz roster; the arms are what the judge sees (L+V+I against
  L+V+I+C). **Contradiction** with `docs/global-layer.md`.
- The calendar's Sep 20 row ("the global layer (first cut) ... exist over the test packages")
  is met and should say so, with the date (09-14) and the kernel, as the Sep 14 row does.
- The bill: "The global layer: the design note, then the first cut 8-12", "The store 6-10",
  "The embedding sidecar 3-5" are done; "wiki pages over document clusters (an afternoon)" is
  built. The remaining rows are the query path, the harnesses, the Kaggle changes, scale, the
  paper.
- The repo map lists the extractor and ingestor notebooks only; add the global-layer notebook,
  `docs/global-layer.md`, `docs/wiki/` (the mock-up) and `dataset/step1/`.
- "Also in the fall, after the numbers: wiki pages over document clusters ... (an afternoon)":
  the pages exist before the numbers now; say what exists (four page types, rendered from the
  store, mock-up in `docs/wiki/`).

## RESEARCH.md

- Section on the resolution ablation (lines about "replayed from the logged scores" and "the
  hand-labeled Oz alias set (one hour of labels)"): stale on both counts. The replay is a
  fixed-verdict sensitivity check; the arms are full builds; the key is Wikipedia's list of
  Baum's Oz characters (CC BY-SA 4.0), matched to children by alias, the hand-matched remainder
  counted. **Contradiction** with `docs/global-layer.md` "The ablation, exactly".
- The measurements table's row for the ablation: same fix. Add the collection layer as an
  instrument (collection sizes, documents in more than one) and the mentions pass.
- The open-question framing ("whether the relational signal still pays when the candidate
  scorer is an embedding and a language model") is right and now matches the experiment
  exactly; say the experiment's name there.

## docs/proposal.md

- "The global layer attaches each document's entities to silent parents. It is built first":
  built; say how (clustering, judge, parents written once) in one sentence.
- "mine also scores co-occurrence ... at the point where a document's entity attaches to its
  cross-document parent ... replayed name-only and name plus co-occurrence ... against a
  hand-labeled alias set over the Oz books": stale as in RESEARCH.md; same fix.
- "the alias set is written in the week after it": the key comes from Wikipedia; not hand
  labels.
- The store and query path bullet (4) is right as a statement of intent; add "hybrid: keyword
  and vector fused by rank" now that it is ruled.

## docs/execution-plan.md

- 2a: "one SQLite file per graph ... A graph is one document for GraphRAG-Bench and one
  history folder for LongMemEval": superseded 09-13 night (one graph over everything loaded; a
  test is a retrieval filter). **Contradiction** with the ruling and the design note.
- 2b: the first-cut paragraph is kept "so the attack reports still read"; it now reads as a
  second design. Replace with one line pointing at `docs/global-layer.md` and the ruling dates.
- 2b2: "one vector per sentence of every cell and abstract and one per fact quote": it is one
  per fact rendered as a line, plus parent summary sentences; the sidecar is appended, not
  rebuilt, after the parents.
- 2c: matches the retrieval manual except "expanded through their parent" only; the manual has
  three hops (node, document, parent). Point at `log/2026-09-15/retrieval.md` until a master
  `docs/retrieval.md` exists.
- Section 5, ruling 6 ("the first-cut attach rule, case-folded name and kind, and its
  hand-checked gate"): superseded; mark it and point at the ledger.
- Section 1: "the hand-labeled Oz alias set (one hour of labels, written in week 2)": Wikipedia
  key.
- Section 8, the feasibility tracker: the Sep 20 row has no real hours; Justin's to fill.

## SCHEMA.md

- "Storage is JSONL packages today ... will be SQLite in one folder, no server (Step 2, not
  built)": the store is built (block 4 and 5). Say so and name the file.
- The read-time supersession paragraph ("When a predicate is functional, a later fact ...
  supersedes an earlier one at read time; ruler_of collides that way ... the functional list is
  maintained by hand") describes a mechanism the 09-13 ruling says is not built this fall
  (every dated fact served, no supersession claim). It should say it is the intended rule and
  that the fall's query path serves every dated fact. **Contradiction** with the ruling and the
  retrieval manual as written.
- "Rebuilding it when its children change is the store's rule (Step 2, not built)": not built
  and not planned this fall; say spring.
- "The global side (PROPOSED 2026-09-15)": written this morning; the lean-store ruling of today
  moves `pair`, `merge` and the build-only Step 1 records out of the serving store into a build
  log, and drops `text`, `provenance`, `tier`, `piece`, `edge`, `ledger`, `candidate`,
  `rejection`, `completion`, `attribute`, `contradiction` from it. Rewrite to the twelve-table
  serving store and the build log once the blocks are rewritten.
- Mentions: the document node as the parent of its mentions (ruled today) belongs in the global
  side.

## BUILD.md

- "embed(texts) belongs to the serving side and is not built": built (block 7), bge-small
  through fastembed, one call.
- "In the store (Step 2, not built), summaries rebuild only when ...": the store is built; the
  refold rule is spring.
- "This section and the two after it describe the serving side, which is not built": the store
  and the sidecar are built; retrieval is PROPOSED (the manual). Rewrite the sentence.
- "Three checks before the wiki ships": the wiki exists; the quote string-match check and the
  dead-link check apply now and are not yet run; the Tip and Ozma page renders both states
  (Tip's line and Ozma's under one parent). Add the checks to the build as the next wiki item.
- Nothing in BUILD.md says the judge sees texts and never scores, that the parent is written
  once after clustering, or that the query path is hybrid. Those are the three rules of the
  serving side worth one sentence each.

## docs/entity-resolution.md

- "Still to decide, none of it destructive", items 1 to 3 (what draws the up-edge; the parent's
  name; whether the up-edge carries its score and evidence): all decided 09-13 and 09-14
  (nomination by vector, name and is_a link with a judge; the judge or the writer picks the
  name from what the instances carry; `instance_of` carries the reason and scores, `pair` and
  `merge` the audit). Mark each with its date and ruling.
- "scored as attachment accuracy against the hand-labeled Oz alias set" and the LitBank and
  BookCoref paragraphs: the gold is the Wikipedia roster; say so and keep BookCoref as the
  second opinion if it is still wanted.
- The four-arm table (N, N+C, N+P, N+C+P) and "of the four arms below N and N+C survive": the
  live arms are L+V+I and L+V+I+C at the judge; N alone is not an arm any more. Rewrite the
  table.
- "What to instrument at build time": the `MergeCandidate` shape is now the `pair` row; say so.
- The 09-14 softenings (insertion, deletion, the synthesized layer) are right and current.

## docs/global-layer.md

- Rewritten this morning to the batch build; missing since: the final pass that makes a
  document the parent of its mentions, the collection merge rule (the overlap of the smaller
  group), the wiki's breadcrumb and palette, and the lean store. Add the first two to the
  algorithm block, the last as the store section once rewritten.

## docs/rulings.md

- Missing lines for today: the lean serving store and the build log; hybrid retrieval (keyword
  and vector fused by rank, no term extraction from the question) with the manual PROPOSED; the
  static figure leads the wiki; the slate scheme; the breadcrumb; every entity on a portal by
  relevance; a document is the parent of its mentions through a final pass; collections merge
  on the overlap of the smaller group. Each is a chat ruling of 09-15 and belongs in the
  ledger the day it was made.

## docs/ingestor.md, docs/extractor.md, dataset/step0, dataset/step1

- Current. `docs/ingestor.md` describes 1.8; the Step 1 dataset docs describe version 2. One
  line to add to `dataset/step1/README.md`: the global layer reads this dataset and the Step 0
  text, with a link to the notebook.

## docs/evaluation-corpus.md

- "one history is one graph" and the alias set and LitBank or BookCoref lines: same fixes as
  above. "two plays": the run holds one play (the Bacchae) and one play from GraphRAG-Bench
  (Dandy Dick); say which.

## log/README.md

- No entries for 2026-09-14 and 2026-09-15. Each day has a global-layer log; 09-15 also has
  the retrieval manual and this review.

## Missing documents

- A master `docs/retrieval.md` once the manual is ruled; the log copy is a snapshot.
- A master for the wiki (the four page types, what each reads, the file-name rule, the three
  checks before it ships), or a section of `docs/global-layer.md`; today the wiki is described
  only in the 09-15 log.
- The build log's own schema (`pair`, `merge`, the Step 1 diagnostics), once the lean store is
  built.

## Order of fixes

1. SCHEMA.md and BUILD.md to the lean store and the built sidecar (after the blocks are
   rewritten, so the documents describe code that runs).
2. `docs/rulings.md`: today's eight lines.
3. README, RESEARCH, the proposal and the plan: the same three stale statements in each
   (attach on name and co-occurrence; the hand-labeled alias set; one graph per history).
4. `docs/entity-resolution.md`: the decided items marked, the arms table rewritten.
5. `docs/global-layer.md`: the mentions pass, the merge rule, the store section.
6. `log/README.md`: the two days.
