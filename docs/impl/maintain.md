# Implementation: MAINTAIN (staleness, refold, supersession, entity merge)

Prepared by the assistant.

Maintain runs as a pass over the store, never per query. Two halves: the fold half (content-hash staleness detection, refold of stale rollups only) and the truth half (subject-predicate supersession with later-assertion-wins reads, and `same_as` entity merge with fact re-attachment). One model call type exists in the whole component: the fold summarize call. Everything else is deterministic, which is where the mock's lessons live (markers stripped from hashes so stamping never cascades; stamp only what was actually rewritten).

## Modules

**`harness/maintain/staleness.py`**: computes and compares content hashes; owns no prose.

    children_hash(node_id, store) -> str        # hash over (relpath, content-hash) pairs of children, markers stripped
    scan(store) -> list[StaleNode]              # every node whose stored hash disagrees with recomputed; no marker means stale
    stamp(node_id, new_hash, store) -> None     # writes hash into the rollup, called only by refold on acceptance

**`harness/maintain/refold.py`**: rewrites stale rollups from child summaries only, never raw text.

    gather(node_id, store) -> list[str]                 # child leaf and child rollup summaries, in tree order
    refold_node(node, store, tier) -> Rollup|Rejection  # generate() against the fold contract; stamps only on acceptance
    run_folds(store, tier) -> FoldReport                # leaf-upward order; counts folded, skipped, rejected

**`harness/maintain/supersede.py`**: deterministic collision detection on the fact file; no model calls.

    collisions(facts, functional, resolve=identity) -> list[tuple[Fact, Fact]]  # same resolved subject, functional predicate, ordered by asserted_at
    mark(earlier, later, store) -> None                       # appends a sidecar row; both fact rows remain untouched
    read_current(subject, predicate, store, as_of=None) -> Fact|None  # later-assertion-wins over a functional predicate; None when no row

`functional` is the repo-checked list of functional predicates (`is_a` and kin); non-functional predicates (`member_of`) never collide. `resolve` defaults to identity so this module builds before merge.py; `reattach` passes the real resolver.

**`harness/maintain/merge.py`**: handles `same_as` rows.

    pending_merges(facts, store) -> list[Fact]             # same_as rows whose loser page still has merged_into null
    merge(loser_id, winner_id, store) -> MergeRecord       # sets merged_into, writes alias rows, unions the two entity page indexes deterministically (pages point, never copy; no model call)
    resolve(entity_id, store) -> entity_id                 # follows redirect chains with cycle guard; used by every fact read
    reattach(loser_id, winner_id, store) -> ReattachReport # rerun collisions() under the merged identity; supersede conflicts, retain the rest

**`harness/maintain/run_maintain.py`**: the driver. `main(store, tier)` runs merges, then supersession, then staleness and folds (that order because a merge changes which facts collide; the tree half is independent, since rollups fold child summaries only and never read entity pages), and writes one MaintainReport with counts.

Five modules.

## Data touched

Reads: Leaf, Node rollup (`children_hash`, `folded_by_tier`), Fact rows (`subject`, `predicate`, `asserted_at`, `qualifiers`), Alias records, Entity pages, Merge ledger. Writes: rollup prose and hash, alias rows, entity pages, supersession sidecar rows, MergeRecord entries, and Rejection records through `generate`. The data model's merge ledger records attribute-level token merges; it is read-only here.

Four gaps in the schema in 10_data_model.md. First, supersession has nowhere to live: keep the fact JSONL append-only and record marks in a sidecar `supersessions.jsonl` with `{earlier, later, reason}` rows; superseded status is a read-time join, and no `superseded_by` field is ever written into a fact row. Second, the entity page has no `merged_into` field; add it, null for live entities, so `resolve()` and `pending_merges()` have a substrate. Third, the rollup has no `last_folded` timestamp; add it for the report, it costs nothing. Fourth, the Rejection record carries no target: add a `target` field (here the node_id), or the twice-rejected report below is unqueryable.

## Contracts

Only `refold_node` calls the model. Fold contract sketch: input is the topic path plus the ordered child summaries; output schema `{"summary": str, "key_entities": [str]}` with `summary` length-bounded relative to input (ceiling: half the combined child word count, capped at 400 words; floor: min(50 words, input length), so short children force no padding) and `key_entities` drawn only from names appearing in the children. Rejection criteria: schema-invalid; `key_entities` names anything absent from the input by case-insensitive substring (the cheap fabrication check); summary under the floor (a lazy fold) or over the ceiling (no compression happened). Retry rule: the standard `generate` behavior, one retry with the validation error appended, then a Rejection record; on rejection the node is never stamped, so it stays stale and the next pass retries it. A node that rejects twice in a row lands in the report as a named item via the Rejection record's `target` field, not a silent loop.

## Build sequence

1. `children_hash` and `scan` over a hand-built fixture tree (three nodes, six leaves). Test: edit one leaf, exactly one node reads stale; edit nothing, zero read stale.
2. `stamp`, then the idempotence property. Test: pytest property test, scan after stamp reports zero stale; also the out-of-band case, edit a leaf file directly on disk and assert the node reads stale (the check a dirty flag would miss).
3. `collisions`, `mark`, `read_current` with the sidecar file and the identity resolver. Test: a planted same-subject fixture, two `is_a` rows on one entity id at ch03 and ch19; `read_current` returns the earlier object at ch03, the later at ch19; a `member_of` pair does not collide; both rows remain byte-identical in the fact file. (The data model's Scabbers rows span two subject ids and cannot collide until step 4.)
4. `merge`, `resolve`, `reattach`, with the literal Scabbers rows as fixture data. Test: after the `same_as` row executes, the alias ledger maps Scabbers to `pettigrew_e01`, `is_a rat` is superseded, `owned_by ron` is retained, and `read_current(pettigrew_e01, is_a, as_of=ch03)` through `resolve()` returns rat.
5. `refold_node` through `generate` with the canned fake tier from the interfaces stage. Test: fake tier returns valid output, node stamps; fake tier returns garbage twice, Rejection recorded and node stays stale.
6. `run_maintain` end to end, leaf-upward fold order. Test: on the fixture, pass one folds N greater than zero and pass two folds zero; then a live smoke on one corpus slice with rejection rate logged per tier.

## Sanity risks

Re-attachment fights the append-only rule. Rewriting subject ids in place would destroy "what was believed at chapter 3", so re-attachment must be read-time resolution through redirects, and then every fact read everywhere must call `resolve()` or silently miss merged entities. Chains (A into B into C) and accidental cycles need the guard from day one.

Conflict detection is not bare collision, before or after a merge. `is_a` is functional (one value at a time) but `member_of` is not; superseding every collision would falsify legitimately plural predicates, so `collisions` takes the declared functional-predicate list from day one. Deciding that list's contents is judgment, not code.

Fold order can break idempotence. A refold changes the node's own content, which changes its parent's `children_hash`; fold leaf-upward in one pass, re-evaluating staleness at each visit rather than from a pre-pass snapshot, or pass two will always find work.

## Done means

The validation line from 11_build_plan.md, made concrete: pytest green on the idempotence property (second pass folds zero nodes), the out-of-band edit test, and the Scabbers fixture asserting both the read rule and retention of superseded rows. Artifacts on disk: the five modules, the fixture corpus committed under `harness/tests/fixtures/`, `supersessions.jsonl` populated on the fixture, one MaintainReport showing fold counts N then zero, and a logged rejection rate per tier for the fold contract from the live smoke. Downstream closure, deferred: the corrected-facts question band and the stale-serve instrument read this component's output but also require the spine and inject, so their first successful run on the fixture corpus is a later end-to-end receipt, not an exit gate for this component.

## Sanity check

Challenged every signature, schema claim, and build step against 10_data_model.md and the build order. What held: the module split, the sidecar over in-place edits, the hash and idempotence tests, the leaf-upward risk analysis. What changed: `collisions` gained the functional-predicate list and an identity-default resolver, because step 3 built it before `resolve()` existed and would have superseded plural predicates; the step 3 Scabbers test could not pass pre-merge (two subject ids) and moved to step 4; `read_current` now returns `Fact|None`; `pending_merges` needed the store; entity page merge was reworded as deterministic index union, preserving the one-model-call claim; the Rejection record needed a `target` field or twice-rejected nodes were unreportable; fixed fold length bounds became input-relative; the false entity-pages-feed-rollups rationale was cut; downstream instruments were demoted from exit gate to later receipt.
