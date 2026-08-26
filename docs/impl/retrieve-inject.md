# Implementation: Retrieve and Inject

Prepared by the assistant.

Steps three and four of the pipeline: lookups over the store, then the budget accountant that composes context three ways. Per the build plan this stage is deliberately thin and model-free; the one exception is `embed()` for the naive-RAG control arm. You implement every line; the design decisions below are the ones to hold or consciously revise.

## Modules

**`harness/retrieve/tree_route.py`** Tree routing: index, rollup, descend only if needed.
`load_index(store) -> TreeIndex` (parse topic paths and rollup front matter into memory; pure read, no caching across runs).
`route(index, question) -> list[topic_path]` (lexical scoring of question terms against path names and rollup text; ranked, never empty if the tree is nonempty; zero-match questions return the top-level paths flagged zero-match).
`descend(store, path, question) -> RouteResult` (return the rollup; include child leaf ids only when the rollup body fails to cover the question terms; the decision is logged in the result).

**`harness/retrieve/entity_lookup.py`** Entity and fact lookup for "everything about X" and point questions.
`resolve_alias(store, name) -> entity_id | None` (exact then case-folded match against the alias ledger; never fuzzy, a miss is a miss).
`entity_bundle(store, entity_id, as_of=None) -> Bundle` (entity page plus fact rows under later-assertion-wins; `as_of` caps `asserted_at` so chapter-3 truth is answerable).
`facts_for(store, subject, predicate=None, as_of=None, include_superseded=False) -> list[FactRow]` (filtered rows; superseded rows excluded by default).

**`harness/retrieve/lexical.py`** The floor.
`build_lex(store) -> LexIndex` (lowercased term index over leaf bodies and segment text).
`search(index, query, k) -> list[Hit]` (term-count scoring in the mock's `_score` style, reimplemented cleanly; hits carry seg_id or leaf_id plus score).

**`harness/retrieve/vectors.py`** Sidecar for the control arm only.
`build_vectors(store, embed) -> VecIndex` (embed every segment once; persist keyed by seg_id with the embed model id).
`nearest(index, embed, query, k) -> list[Hit]` (cosine over the sidecar; deterministic replay, same query same ids).

**`harness/inject/strategies.py`** One function per arm, all returning ranked `Candidate` lists (id, text, score, kind).
`top_k_chunks(question, store, vecindex, embed, k)` (the control, naive RAG over segments; `embed` vectorizes the question at query time).
`tree_summaries(question, store, index)` (route, rollups, then leaves per `descend`).
`hybrid(question, store, index)` (tree_summaries plus fact rows for every entity `resolve_alias` finds; candidate names come from matching question n-grams against the alias ledger).

**`harness/inject/accountant.py`** The budget.
`count_tokens(text) -> int` (one counter everywhere; see risks).
`render(id, store) -> str` (one deterministic id-to-text form for segments, leaves, rollups, and fact rows; `compose` and replay both use it, or byte-compare cannot hold).
`compose(candidates, budget) -> Composition` (greedy admission in rank order, whole items only, never truncate mid-item; ordering per the injection reading, top-ranked material at the edges of the window, weakest in the middle).
`to_run_fields(comp) -> dict` (the ordered `injected` id list and token totals for the run row).

## Data touched

Reads: Segment, Leaf, Node rollup, Entity page, Alias record, Fact row, all as defined in the data model. Writes nothing into the store; its only output is the `injected` list and token counts handed to the run row, which the evaluation spine writes. Two gaps in the schema. First, no embedding storage exists anywhere; add a sidecar file (one npz keyed by seg_id plus the embed model id), and per the mock's own rule it is an index, never the memory, rebuildable at will. Second, the Fact row lists no superseded marker field; supersession is described as a later-row property but no `superseded_by: fact_id` field is in the row. Decide now: MAINTAIN stamps a sidecar supersession map, and `facts_for` also computes later-wins on the fly so retrieval works before MAINTAIN exists (build order puts it after this stage). On-the-fly later-wins covers same-subject collisions only; `same_as` re-attachment exists only after MAINTAIN, so earlier tests supply post-merge state as fixtures.

## Contracts

None. This component makes no `generate()` calls, so no JSON schema, rejection criteria, or retry rule apply. The one model-adjacent surface is `embed()`: its contract is dimensional (fixed dimension, finite values), a mismatch fails loud with no retry because the call is deterministic.

## Build sequence

1. `lexical.py` over the already-ingested tenant-zero slice. Test: a known term returns its known leaf.
2. `count_tokens` and `compose` against synthetic candidates. Test: property test over a few hundred random candidate sets, budget never exceeded, order stable.
3. `tree_route.py`. Test: three hand-picked questions route to their expected topic paths.
4. `entity_lookup.py` with the read rule. Test: a hand-authored post-merge Scabbers fixture (literal rows, aliases, sidecar map; MAINTAIN is unbuilt and pre-merge rows sit under two subject ids); `as_of` chapter 3 yields rat, chapter 19 yields wizard, alias Wormtail resolves.
5. `vectors.py` and `top_k_chunks`. Test: replay determinism, identical query, identical ids.
6. `tree_summaries` and `hybrid`. Test: run all three arms on ten hand-written questions (the certified set does not exist until Phase 3); manually read the thirty compositions and commit the sanity note.
7. Run-row wiring through the Phase 0 run-row dataclass (verdicts stay empty; the full spine is its own stage). Test: rebuild one composition from its `injected` list via `render` and byte-compare.

## Sanity risks

Token counting is three tokenizers pretending to be one: the three tiers count differently, so a single `count_tokens` can overrun the budget at one tier while passing the property test. Default: the local tier's tokenizer plus a 15 percent margin; revise only with a logged reason. Lexical tree routing will misroute vocabulary-mismatched questions, and the miss-rate instrument needs to know whether the evidence segment was ever a candidate versus dropped by the accountant; log routing decisions in the RouteResult or the instrument cannot separate the two failures. And the never-truncate rule under small budgets can under-fill the window; the admission rule changes arm comparisons, so it is pinned: strict greedy, no skip-ahead, since it preserves rank order across arms; revise only with a logged reason.

## Done means

The validation from the build plan, concretely: the pytest suite green, including the budget property test (zero overruns across the random sets) and the replay test (byte-identical reconstruction from a run row); run rows on disk from all three strategies over the tenant-zero slice, each carrying its ordered `injected` list (composition-only; verdicts empty until the spine scores); the committed manual-read note covering ten compositions per strategy; and the QA authorship gate logged in the review trail. No scoring run starts before those four artifacts exist.

## Sanity check

Challenged: every signature against the data model, the build order against what earlier stages actually produce, and the two tests claiming byte-level or time-scoped truth. What held: the module split, the sidecar decisions, the never-truncate rule, the seven-step sequence, and the model-free scope. What changed: `top_k_chunks` gained the `embed` parameter it could not run without; the Scabbers test became a hand-authored post-merge fixture, since on-the-fly later-wins cannot cross the pre-merge subject split and MAINTAIN builds later; a `render` function was added so replay byte-compare is enforceable; run-row wiring now names its minimal writer and empty verdicts; step 6 uses hand-written questions; zero-match routing got a defined return; and the two deferred decisions (counter plus margin, strict greedy) are pinned in writing.
