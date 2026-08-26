# Implementation: Organize (distiller, filing, merge ledger)

Prepared by the assistant.

The stage that turns segments into meaning: three schema-validated model passes per segment (summary, mentions, facts), a filing call that places each leaf in the tree, and the merge ledger that keeps attribute understanding out of the black box. Supersession and `same_as` entity merging belong to MAINTAIN; this stage only emits the rows they run on.

## Modules

All under `harness/organize/`.

**driver.py**, per-segment orchestration and resumability.

```
run_segment(seg, store, tiers) -> SegmentResult   # four calls in order; partial failure leaves the segment resumable
run_corpus(corpus_id, store, tiers) -> RunStats   # iterate segments by ordinal, skip completed passes, aggregate rejections
pass_state(seg_id, store) -> dict                 # which passes have completion records, read from disk, never from memory
```

**summarize.py**, the summary pass.

```
build_summary_prompt(seg, contract) -> str        # segment text plus the frozen summary contract
summarize(seg, tier) -> LeafDraft | Rejection     # one generate() call, schema-validated
write_leaf(draft, topic_path, store) -> leaf_id   # markdown body plus YAML front matter per the Leaf schema
```

**filing.py**, tree placement.

```
tree_index(store) -> list[TopicPath]                          # current two-level paths, each with a one-line gist
file_leaf(draft, index, tier) -> TopicPath | NewTopic | Rejection  # model picks an existing path or takes the new-topic escape
create_topic(new_topic, store) -> TopicPath                   # mint the path; ancestor rollups go stale via children_hash on the next maintain scan
```

**mentions.py**, coreference and alias binding.

```
candidate_aliases(seg, store, k) -> AliasSlice        # lexical match plus recently active entities, hard-capped; the cap is the mock's 400-name lesson
extract_mentions(seg, candidates, tier) -> list[MentionBinding] | Rejection
verify_quotes(bindings, seg) -> (accepted, rejected)  # deterministic: every evidence quote must appear in segment text after whitespace normalization of both sides
apply_bindings(accepted, store) -> None               # mint NEW entities, append alias records, append pointer lines to entity pages
```

**facts.py**, dated assertion rows.

```
extract_facts(seg, bound_entities, tier) -> list[FactDraft] | Rejection
resolve_ids(drafts, store) -> (rows, rejected)    # subject must resolve to an entity id, object only when a ref (literals pass through); asserted_at set by code from the document ordinal, never trusted from the model
append_rows(rows, store) -> list[fact_id]
```

**merge_ledger.py**, the anti-black-box record.

```
fold_attribute(entity_id, attribute, store, tier) -> (AttrValue, [fact_id])  # code gathers rows in asserted_at order; the model merges under the merge contract
record_merge(entity_id, attribute, fact_ids, tier, store) -> attr_id  # fact_ids code-supplied from fold_attribute, never model-claimed
audit_walk(attr_id, store) -> Chain               # attr to fact rows to segments to source spans; the spot-audit tool
```

## Data touched

Reads: Segment (and source text through its span), Leaf topic paths, Alias records, Entity pages, Fact rows (for folding). Writes: Leaf, Alias record, Entity page, Fact row, Merge ledger entry, Rejection record. Rollups are never written here; `children_hash` staleness is MAINTAIN's to notice.

Schema gaps to flag against 10_data_model.md: (1) there is no standalone Mention object; bindings exist only as lines inside entity pages, but quote verification and the fifty-binding hand-check need them as data. Add `mentions.jsonl`: `{mention_id, seg_id, surface, entity_id, alias_used, quote, extracted_by_tier}`. (2) The Alias record carries no `extracted_by_tier`; every other model artifact does. Add it. (3) The Merge ledger entry has no `asserted_through` (last source ordinal folded), which re-folding on new facts needs for idempotence. Add it. (4) The filing decision's tier is recorded nowhere; the Leaf's `written_by_tier` covers the summary only. Add `filed_by_tier` to leaf front matter. (5) Rejection records lack the `seg_id` resumability needs; add it. (6) No object stores the per-path gist `tree_index` needs; add `topics.jsonl`: `{topic_path, gist}`.

## Contracts

Three JSON schemas plus filing, frozen at v1 before code (Phase 1.5). Sketches: summary `{title, body: 50-200 words, salient_entities: [surface]}`; mentions `{mentions: [{surface, quote, binding: alias-string | "NEW", kind_if_new}]}`; facts `{facts: [{subject_ref, predicate, object_ref_or_literal, qualifiers, quote}]}`; filing `{path} | {new_topic: {parent, name, gist}}`; merge `{value}`, rows code-gathered, frozen before step 6.

Rejection has two layers. Schema failure is handled inside `generate()`: one retry with the validation error appended, then a Rejection record. Semantic failure is deterministic post-checks: quote not verbatim in segment, binding not in the supplied candidate slice, subject or object unresolvable. Semantic failures reject the item, not the batch: drop the row or binding, write a Rejection with the named criterion, no second model call. An empty yield with no rejections is complete: write an empty completion record. Only a Rejection leaves a pass incomplete; `run_corpus` retries once, then marks it failed.

## Build sequence

1. `summarize.py` plus `write_leaf` on ten archive segments, fixed topic path, no filing. Test: all front matter validates; rejection count logged from ten calls per configured tier.
2. `filing.py` against a hand-seeded two-level tree; driver wires both. Test: file thirty step-1 leaves, hand-score the paths, write the disagreement note.
3. `mentions.py` with an empty ledger (everything NEW) plus `verify_quotes`. Test: property test that every accepted quote is a verbatim substring; one chapter's entity pages match a hand list of named characters.
4. Alias binding: `candidate_aliases` feeds the prompt; pronoun-context aliases recorded. Test: re-running the same chapter mints zero new entities.
5. `facts.py` end to end. Test: a planted Scabbers-shaped fixture (alias, later reveal) yields the `same_as` row with correct segment pointers.
6. `merge_ledger.py` folding the ten most-mentioned entities. Test: `audit_walk` on five attributes reaches source quotes with no broken links.
7. Full slice: one corpus through all passes. Test: the 50/50/50 hand-check and the rejection table below.

## Sanity risks

Alias binding under a capped candidate slice will mint duplicates; the mock's 1,169 names against a 400-name cap is the receipt, and candidate retrieval is load-bearing from step 4, not a later optimization. Cross-segment coreference, resolved here: the mentions prompt carries the prior segment's summary as trailing context; still-unresolved pronouns are counted honestly. And the hand-checks are the long pole: 150 scored items plus the ledger walk is several evenings of careful reading against source, which must sit inside the October 19 to November 15 block, not after it.

## Done means

Per 11_build_plan, made concrete: a rejection-rate table per tier per contract (three tiers, five contracts), queryable from rejection records over the full slice; fifty bindings, fifty fact rows, and fifty filed paths hand-scored against source with precision and a confidence interval logged (valve: thirty each, in writing); five attributes walked through the merge ledger to source tokens with zero gaps; leaves, pages, and rows existing for one whole corpus slice, with a second organize run over it minting zero entities and rewriting zero accepted artifacts; and the QA authorship gate logged, the student having written or rewritten every module above.

## Sanity check

Challenged: signatures, rejection criteria, and build-step inputs against 10_data_model.md and the calendar. Held: module boundaries, pass order, deterministic post-checks, hand-check warning. Changed: empty-yield semantics (a factless segment retried forever, invisible on disk; now an empty completion record, retries capped); `resolve_ids` no longer contradicts literal objects; `fold_attribute` returns the fact ids `record_merge` needs, and the merge call gained a contract; `asserted_at` aligned to document ordinal; quote checks got normalization; Rejection `seg_id` and a topic-gist home added to the gaps; cross-segment coreference decided; a 30/30/30 valve for the hour budget.
