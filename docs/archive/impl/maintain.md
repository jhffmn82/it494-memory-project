> **SUPERSEDED 2026-08-28** by `03_design.md` and `05_fall_plan.md`. These module specs were written against the superseded data model and build plan. Their end-of-file gap lists were never absorbed until 08-28; the surviving items (the `Mention` record, `Rejection.target`, `Rejection.unit_id`, `Run.answer_text`, `merged_into`) are now in `03_design.md`.
> Kept for the record; do not build from it. Index: `docs/README.md`.

# Implementation: MAINTAIN (staleness, refold, supersession, entity merge)

Maintain is a pass over the store, never per query, in two halves: fold (content-hash staleness detection, refold of stale rollups only) and truth (subject-predicate supersession with later-assertion-wins reads, and `same_as` entity merge with fact re-attachment). The fold call is the only model call; the rest is deterministic. Two mock lessons hold: markers are stripped from hashes so stamping never cascades, and only rewritten nodes are stamped.

## Modules

**`harness/maintain/staleness.py`**: computes and compares content hashes; owns no prose.

    children_hash(node_id, store) -> str        # hash over (relpath, content-hash) pairs of children, markers stripped
    scan(store) -> list[StaleNode]              # nodes whose stored hash disagrees with recomputed; no marker means stale
    stamp(node_id, new_hash, store) -> None     # writes hash into the rollup; called only by refold on acceptance

**`harness/maintain/refold.py`**: rewrites stale rollups from child summaries only, never raw text.

    gather(node_id, store) -> list[str]                 # child leaf and rollup summaries, in tree order
    refold_node(node, store, tier) -> Rollup|Rejection  # generate() against the fold contract; stamps only on acceptance
    run_folds(store, tier) -> FoldReport                # leaf-upward order; counts folded, skipped, rejected

**`harness/maintain/supersede.py`**: deterministic collision detection on the fact file; no model calls.

    collisions(facts, functional, resolve=identity) -> list[tuple[Fact, Fact]]  # same resolved subject, functional predicate, ordered by asserted_at
    mark(earlier, later, store) -> None                       # appends a sidecar row; both fact rows remain untouched
    read_current(subject, predicate, store, as_of=None) -> Fact|None  # later-assertion-wins over a functional predicate

`functional` is the repo-checked list of functional predicates (`is_a` and kin); non-functional predicates (`member_of`) never collide. `resolve` defaults to identity so the module builds before merge.py; `reattach` passes the real resolver.

**`harness/maintain/merge.py`**: handles `same_as` rows.

    pending_merges(facts, store) -> list[Fact]             # same_as rows whose loser page still has merged_into null
    merge(loser_id, winner_id, store) -> MergeRecord       # sets merged_into, writes alias rows, unions the two entity page indexes (pages point, never copy)
    resolve(entity_id, store) -> entity_id                 # follows redirect chains with cycle guard; used by every fact read
    reattach(loser_id, winner_id, store) -> ReattachReport # rerun collisions() under the merged identity; supersede conflicts, retain the rest

**`harness/maintain/run_maintain.py`**: the driver, `main(store, tier)`: merges, then supersession, then staleness and folds (a merge changes which facts collide; the tree half is independent, rollups reading child summaries only), one MaintainReport with counts.

## Data touched

Reads: Leaf, Node rollup (`children_hash`, `folded_by_tier`), Fact rows (`subject`, `predicate`, `asserted_at`, `qualifiers`), Alias records, Entity pages, merge ledger (read-only here). Writes: rollup prose and hash, alias rows, entity pages, supersession sidecar rows, MergeRecord entries, Rejection records through `generate`.

Four gaps in `10_data_model.md`. Supersession has nowhere to live: keep the fact JSONL append-only, mark supersessions in a sidecar `supersessions.jsonl` `{earlier, later, reason}`; superseded status is a read-time join, never a `superseded_by` field in a fact row. The entity page lacks `merged_into`: add it, null for live entities, the substrate for `resolve()` and `pending_merges()`. The rollup lacks `last_folded`: add it for the report. The Rejection record has no target: add `target` (the node_id), or the twice-rejected report is unqueryable.

## Contracts

Only `refold_node` calls the model. Fold contract: input, the topic path plus ordered child summaries; output `{"summary": str, "key_entities": [str]}`, `summary` length-bounded (ceiling: half the combined child word count, capped at 400 words; floor: min(50 words, input length)), `key_entities` drawn only from names in the children. Reject: schema-invalid; `key_entities` naming anything absent from the input by case-insensitive substring (the cheap fabrication check); summary under the floor or over the ceiling. Retry once with the error appended, then a Rejection record. A rejected node is never stamped, stays stale, and retries next pass; a twice-rejected node lands in the report by name via `target`, not a silent loop.

## Build sequence

1. `children_hash` and `scan` over a fixture tree (three nodes, six leaves). Test: edit one leaf, exactly one node reads stale; edit nothing, zero stale.
2. `stamp` and the idempotence property. Test: scan after stamp reports zero stale; and the out-of-band case, a leaf edited directly on disk reads its node stale (what a dirty flag would miss).
3. `collisions`, `mark`, `read_current` with the sidecar file and identity resolver. Test: two planted `is_a` rows on one entity at ch03 and ch19; `read_current` returns the earlier object at ch03, the later at ch19; a `member_of` pair does not collide; both rows stay byte-identical. (The Scabbers rows span two subject ids and cannot collide until step 4.)
4. `merge`, `resolve`, `reattach` on the literal Scabbers rows. Test: after the `same_as` row, the alias ledger maps Scabbers to `pettigrew_e01`, `is_a rat` is superseded, `owned_by ron` retained, and `read_current(pettigrew_e01, is_a, as_of=ch03)` through `resolve()` returns rat.
5. `refold_node` through `generate` with the canned fake tier. Test: valid fake output stamps the node; garbage twice records a Rejection and the node stays stale.
6. `run_maintain` end to end, leaf-upward. Test: pass one folds N greater than zero, pass two folds zero; then a live smoke on one corpus slice, rejection rate per tier.

## Risks

Re-attachment fights the append-only rule: rewriting subject ids in place would destroy what was believed at chapter 3, so re-attachment is read-time resolution through redirects, and every fact read must call `resolve()` or silently miss merged entities; chains (A into B into C) and cycles need the guard from day one.

Conflict detection is not bare collision: `is_a` is functional, `member_of` is not, and superseding every collision would falsify legitimately plural predicates; `collisions` therefore takes the declared functional-predicate list, whose contents are judgment, not code.

Fold order can break idempotence: a refold changes the node's content and so its parent's `children_hash`; fold leaf-upward in one pass, re-evaluating staleness at each visit, or pass two will always find work.

## Done means

Pytest green on the idempotence property (second pass folds zero), the out-of-band edit test, and the Scabbers fixture (read rule plus retention of superseded rows). On disk: the five modules, the fixture corpus under `harness/tests/fixtures/`, `supersessions.jsonl` populated on the fixture, one MaintainReport with fold counts N then zero, a logged per-tier rejection rate for the fold contract. The corrected-facts band and stale-serve instrument also need the spine and inject; their first fixture run is a later end-to-end receipt, not an exit gate here.
