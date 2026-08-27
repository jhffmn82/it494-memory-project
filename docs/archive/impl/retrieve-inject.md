> **SUPERSEDED 2026-08-28** by `03_design.md` and `05_fall_plan.md`. These module specs were written against the superseded data model and build plan. Their end-of-file gap lists were never absorbed until 08-28; the surviving items (the `Mention` record, `Rejection.target`, `Rejection.unit_id`, `Run.answer_text`, `merged_into`) are now in `03_design.md`.
> Kept for the record; do not build from it. Index: `docs/README.md`.

# Implementation: Retrieve and Inject

Pipeline steps three and four: lookups over the store, then the budget accountant composing context three ways. All hand-implemented; model-free except `embed()` for the naive-RAG control arm.

## Modules

**`harness/retrieve/tree_route.py`** Tree routing: index, rollup, descend only if needed.
`load_index(store) -> TreeIndex` (topic paths and rollup front matter parsed into memory; pure read, no caching).
`route(index, question) -> list[topic_path]` (lexical scoring of question terms against path names and rollup text, ranked; zero-match questions return the top-level paths, flagged).
`descend(store, path, question) -> RouteResult` (the rollup, plus child leaf ids only when its body misses the question terms; decision logged).

**`harness/retrieve/entity_lookup.py`** Entity and fact lookup for point questions and everything-about-X.
`resolve_alias(store, name) -> entity_id | None` (exact then case-folded match against the alias ledger; never fuzzy).
`entity_bundle(store, entity_id, as_of=None) -> Bundle` (entity page plus fact rows under later-assertion-wins; `as_of` caps `asserted_at` for chapter-3 truth).
`facts_for(store, subject, predicate=None, as_of=None, include_superseded=False) -> list[FactRow]` (filtered rows; superseded excluded by default).

**`harness/retrieve/lexical.py`** The floor.
`build_lex(store) -> LexIndex` (lowercased term index over leaf bodies and segment text).
`search(index, query, k) -> list[Hit]` (term-count scoring in the mock's `_score` style; hits carry seg_id or leaf_id plus score).

**`harness/retrieve/vectors.py`** Sidecar for the control arm only.
`build_vectors(store, embed) -> VecIndex` (embed every segment once; persist keyed by seg_id with the embed model id).
`nearest(index, embed, query, k) -> list[Hit]` (cosine over the sidecar; same query, same ids).

**`harness/inject/strategies.py`** One function per arm, each returning a ranked `Candidate` list (id, text, score, kind).
`top_k_chunks(question, store, vecindex, embed, k)` (the control: naive RAG over segments; `embed` vectorizes the question).
`tree_summaries(question, store, index)` (route, rollups, then leaves per `descend`).
`hybrid(question, store, index)` (tree_summaries plus fact rows for every entity `resolve_alias` finds among question n-grams matched against the alias ledger).

**`harness/inject/accountant.py`** The budget.
`count_tokens(text) -> int` (one counter everywhere; see risks).
`render(id, store) -> str` (the one deterministic id-to-text form for segments, leaves, rollups, fact rows; shared by `compose` and replay).
`compose(candidates, budget) -> Composition` (greedy admission in rank order, whole items only, never truncating; top-ranked material at the window edges, weakest in the middle, per the injection reading).
`to_run_fields(comp) -> dict` (the ordered `injected` id list and token totals for the run row).

## Data touched

Reads Segment, Leaf, Node rollup, Entity page, Alias record, Fact row; writes nothing. The only output is the `injected` list and token counts for the run row, written by the evaluation spine.

Two gaps. Embeddings have no storage: add a sidecar npz keyed by seg_id plus the embed model id, rebuildable at will. The Fact row has no `superseded_by` field: MAINTAIN stamps a sidecar supersession map, and `facts_for` also computes later-wins on the fly so retrieval works before MAINTAIN exists; that covers same-subject collisions only, `same_as` re-attachment arriving with MAINTAIN, so earlier tests supply post-merge fixtures.

## Contracts

None; nothing here calls `generate()`. The one model-adjacent surface is `embed()`, whose contract is dimensional (fixed dimension, finite values); a mismatch fails loud, no retry.

## Build sequence

1. `lexical.py` over the ingested tenant-zero slice. Test: a known term returns its known leaf.
2. `count_tokens` and `compose` on synthetic candidates. Test: property test over a few hundred random candidate sets; budget never exceeded, order stable.
3. `tree_route.py`. Test: three hand-picked questions route to their expected topic paths.
4. `entity_lookup.py` with the read rule. Test: a hand-authored post-merge Scabbers fixture (literal rows, aliases, sidecar map, pre-merge rows sitting under two subject ids); `as_of` chapter 3 yields rat, chapter 19 yields wizard, alias Wormtail resolves.
5. `vectors.py` and `top_k_chunks`. Test: replay determinism, identical query, identical ids.
6. `tree_summaries` and `hybrid`. Test: all three arms on ten hand-written questions (the certified set arrives in Phase 3); read the thirty compositions, commit the review note.
7. Run-row wiring through the Phase 0 run-row dataclass; verdicts stay empty until the spine. Test: rebuild one composition from its `injected` list via `render` and byte-compare.

## Risks

Token counting is three tokenizers pretending to be one: tiers count differently, so one `count_tokens` can overrun the budget at a tier while passing the property test; the default is the local tier's tokenizer plus a 15 percent margin. Lexical routing will misroute vocabulary-mismatched questions, and the miss-rate instrument must know whether the evidence segment was ever a candidate or was dropped by the accountant; hence routing decisions logged in the RouteResult. The never-truncate rule can under-fill small budgets, and the admission rule changes arm comparisons, so it is pinned: strict greedy, no skip-ahead, rank order preserved across arms.

## Done means

The pytest suite green, including the budget property test (zero overruns) and the replay test (byte-identical reconstruction from a run row); run rows from all three strategies over the tenant-zero slice, each with its ordered `injected` list, verdicts empty until the spine scores; the committed manual-read note, ten compositions per strategy; and the authorship gate logged. No scoring run starts before those four artifacts exist.
