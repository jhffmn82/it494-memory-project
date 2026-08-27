> **SUPERSEDED 2026-08-28** by `03_design.md` and `05_fall_plan.md`. These module specs were written against the superseded data model and build plan. Their end-of-file gap lists were never absorbed until 08-28; the surviving items (the `Mention` record, `Rejection.target`, `Rejection.unit_id`, `Run.answer_text`, `merged_into`) are now in `03_design.md`.
> Kept for the record; do not build from it. Index: `docs/README.md`.

# Implementation: Organize (distiller, filing, merge ledger)

Three schema-validated model passes per segment (summary, mentions, facts), a filing call placing each leaf in the tree, and a merge ledger keeping attribute understanding out of the black box. Supersession and `same_as` entity merging belong to MAINTAIN; this stage emits the rows they run on.

## Modules

All under `harness/organize/`.

**driver.py**, per-segment orchestration and resumability.

```
run_segment(seg, store, tiers) -> SegmentResult   # four calls in order; partial failure stays resumable
run_corpus(corpus_id, store, tiers) -> RunStats   # segments in ordinal order; skip completed passes, aggregate rejections
pass_state(seg_id, store) -> dict                 # completed passes, read from disk, never memory
```

**summarize.py**, the summary pass.

```
build_summary_prompt(seg, contract) -> str        # segment text plus the frozen summary contract
summarize(seg, tier) -> LeafDraft | Rejection     # one generate() call, schema-validated
write_leaf(draft, topic_path, store) -> leaf_id   # markdown body, YAML front matter per Leaf schema
```

**filing.py**, tree placement.

```
tree_index(store) -> list[TopicPath]                          # current two-level paths, each with a one-line gist
file_leaf(draft, index, tier) -> TopicPath | NewTopic | Rejection  # pick an existing path or the new-topic escape
create_topic(new_topic, store) -> TopicPath                   # mint the path; ancestors go stale via children_hash
```

**mentions.py**, coreference and alias binding.

```
candidate_aliases(seg, store, k) -> AliasSlice        # lexical match plus recently active entities, hard-capped
extract_mentions(seg, candidates, tier) -> list[MentionBinding] | Rejection
verify_quotes(bindings, seg) -> (accepted, rejected)  # deterministic: every quote must appear in segment text after whitespace normalization
apply_bindings(accepted, store) -> None               # mint NEW entities, append alias records and entity-page pointer lines
```

**facts.py**, dated assertion rows.

```
extract_facts(seg, bound_entities, tier) -> list[FactDraft] | Rejection
resolve_ids(drafts, store) -> (rows, rejected)    # subject must resolve to an entity id, object only when a ref; code sets asserted_at from document ordinal
append_rows(rows, store) -> list[fact_id]
```

**merge_ledger.py**, the anti-black-box record.

```
fold_attribute(entity_id, attribute, store, tier) -> (AttrValue, [fact_id])  # code gathers rows in asserted_at order; the model merges under the merge contract
record_merge(entity_id, attribute, fact_ids, tier, store) -> attr_id  # fact_ids code-supplied, never model-claimed
audit_walk(attr_id, store) -> Chain               # attr to fact rows to segments to source spans; the spot-audit tool
```

## Data touched

Reads: Segment (with source text through its span), Leaf topic paths, Alias records, Entity pages, Fact rows. Writes: Leaf, Alias record, Entity page, Fact row, Merge ledger entry, Rejection record. Rollups are never written here; staleness is MAINTAIN's to notice.

Six gaps against `10_data_model.md`: no Mention object, though quote verification and the fifty-binding hand-check need bindings as data (add `mentions.jsonl` `{mention_id, seg_id, surface, entity_id, alias_used, quote, extracted_by_tier}`); Alias records lack `extracted_by_tier`; Merge ledger entries lack `asserted_through` (last ordinal folded, for idempotent re-folding); the filing tier goes unrecorded, `written_by_tier` covering only the summary (add `filed_by_tier`); Rejection records lack the `seg_id` resumability needs; the `tree_index` gist has no home (add `topics.jsonl` `{topic_path, gist}`).

## Contracts

Five contracts freeze at v1 before code (Phase 1.5): summary `{title, body: 50-200 words, salient_entities: [surface]}`; mentions `{mentions: [{surface, quote, binding: alias-string | "NEW", kind_if_new}]}`; facts `{facts: [{subject_ref, predicate, object_ref_or_literal, qualifiers, quote}]}`; filing `{path} | {new_topic: {parent, name, gist}}`; merge `{value}` over code-gathered rows.

Rejection has two layers. `generate()` handles schema failure: one retry with the validation error appended, then a Rejection record. Semantic failure (quote not verbatim, binding outside the candidate slice, unresolvable subject or object) is a deterministic post-check rejecting the item, not the batch: drop it, write a Rejection naming the criterion, no second call. An empty yield with no rejections writes an empty completion record; only a Rejection leaves a pass incomplete, retried once by `run_corpus`, then marked failed.

## Build sequence

1. `summarize.py` and `write_leaf`: ten archive segments, fixed topic path, no filing. Test: front matter validates; rejection count logged, ten calls per tier.
2. `filing.py` against a hand-seeded two-level tree, driver wiring both. Test: file thirty step-1 leaves, hand-score the paths, write the disagreement note.
3. `mentions.py` with an empty ledger (everything NEW) plus `verify_quotes`. Test: every accepted quote is a verbatim substring (property test); one chapter's entity pages match a hand list of named characters.
4. Alias binding: `candidate_aliases` feeds the prompt; pronoun-context aliases recorded. Test: re-running the same chapter mints zero new entities.
5. `facts.py` end to end. Test: a planted Scabbers-shaped fixture (alias, later reveal) yields the `same_as` row with correct segment pointers.
6. `merge_ledger.py` folding the ten most-mentioned entities. Test: `audit_walk` on five attributes reaches source quotes with no broken links.
7. Full slice: one corpus through all passes. Test: the 50/50/50 hand-check and the rejection table below.

## Risks

Alias binding under a capped candidate slice will mint duplicates (the mock: 1,169 names against a 400-name cap); candidate retrieval is load-bearing from step 4. Cross-segment coreference resolves here: the mentions prompt carries the prior segment's summary as trailing context; still-unresolved pronouns are counted honestly. The hand-checks are the long pole: 150 scored items plus the ledger walk is several evenings of reading against source, inside the October 19 to November 15 block.

## Done means

Per `11_build_plan`: a rejection-rate table per tier per contract (three tiers, five contracts), queryable from Rejection records; fifty bindings, fifty fact rows, and fifty filed paths hand-scored against source, precision and confidence interval logged (fallback: thirty each); five attributes walked through the merge ledger to source tokens, zero gaps; leaves, pages, and rows for one corpus slice, a second run minting zero entities and rewriting zero accepted artifacts; and the authorship gate logged, every module written by hand.
