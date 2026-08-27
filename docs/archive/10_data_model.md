> **SUPERSEDED 2026-08-28** by `03_design.md`.
> Kept for the record; do not build from it. Index: `docs/README.md`.

# Data model

The schema for every object the harness stores, with Harry Potter as the worked example throughout. Storage is plain files, JSONL for rows and markdown for prose, in a directory layout git can diff. SQLite was deferred: at this scale one dependency buys nothing that sorted JSONL does not, and files keep every artifact human-readable. Identifiers are short content hashes, so re-ingesting the same material yields the same ids.

## Source layer

**Document.** `{doc_id, corpus_id, kind: chat|text, title, ordinal, meta}` plus the raw text, stored verbatim and never edited. A book chapter and a chat session are both documents. The layer is append-only and serves as the write-ahead log; everything above it can be rebuilt from it.

**Segment.** `{seg_id, doc_id, span: [start, end], ordinal, boundary_method: model|texttiling, tier}`. The atom: a segment records which characters of which document it covers, so every downstream claim can point back to text.

## Tree layer

**Leaf.** Markdown with YAML front matter: `{leaf_id, seg_id, topic_path, title, written_by_tier, contract_version}` and a summary body written against the summary contract. One segment, one leaf.

**Node rollup.** `{node_id, topic_path, children_hash, folded_by_tier}` plus prose built only from child summaries. `children_hash` is the content hash over the node's children; the maintain pass refolds a node only when stored and recomputed hashes disagree. Example: `hogwarts/gryffindor` carries a rollup over its leaves; a new leaf under it changes the hash and marks it stale.

## Entity layer

**Entity page.** `{entity_id, canonical_name, kind: person|org|place|thing, created_from}` plus an index body: for each attribute, the current value, the fact rows behind it, and quoted mention lines with segment pointers. A page never copies content; it points. The page for Peter Pettigrew indexes every mention, including those that predate anyone knowing Scabbers was him.

**Alias record.** `{alias, entity_id, kind: name|nickname|epithet|pronoun-context, first_seen_seg, evidence_quote}`. The keyword list mapping to one individual: `Scabbers -> pettigrew_e01`, `Wormtail -> pettigrew_e01`, `Peter -> pettigrew_e01`. Pronoun resolution happens at distill time, a bought model capability; the alias ledger records the durable names.

## Fact layer

**Fact row.** One JSONL line: `{fact_id, asserted_at: source_position, subject: entity_id, predicate, object, qualifiers, seg_id, quote, extracted_by_tier, contract_version}`. `asserted_at` is position in the corpus (chapter or session ordinal), not wall-clock, because narrative time is what supersession runs on.

**Supersession.** Neither a deletion nor an edit: a later row with the same subject and a functional predicate (a repo-checked list, `is_a` and kin; plural predicates like `member_of` never collide) marks the earlier row superseded, and the read rule is later-assertion-wins. Both rows remain, so "what was believed at chapter 3" stays answerable. The worked example:

```
{f_0412, ch03, scabbers_e07, is_a, rat, {}, seg_031, "Scabbers the rat dozed..."}
{f_2210, ch19, scabbers_e07, same_as, pettigrew_e01, {}, seg_198, "...you're Peter Pettigrew"}
{f_2211, ch19, pettigrew_e01, is_a, wizard(animagus), {}, seg_198, "..."}
```

The `same_as` row triggers an entity merge: `scabbers_e07` folds into `pettigrew_e01`, the alias ledger gains the mapping, and every prior Scabbers fact re-attaches to Pettigrew, superseded where it conflicts (a rat, now an animagus form) and retained where it does not (owned by Ron, still true of the disguise period). This one case exercises aliasing, merging, supersession, and time-scoped truth, which is why it leads the demo.

**Merge ledger entry.** `{attr_id, entity_id, attribute, merged_from: [fact_ids in sequence], written_by_tier}`. The record of which tokens, in what order, merged into an attribute: a hundred employment-shaped fact rows collapsing into one "works at" attribute leave their trail here. This is the anti-black-box requirement, stored as data.

## Evaluation layer

**Question record.** `{q_id, corpus_id, band: rollup|leaf|synthesis|corrected, text, fixed_answer, evidence_segs, certified: {tier: pass|fail}}`. The corrected band requires a superseded fact in its evidence. Certification is stored per tier, so "every bare tier failed this closed-book" is a queryable property, not a claim.

**Run row.** `{run_id, timestamp, arm, config_hash, tiers: {stage: model}, q_id, injected: [ids in order], verdict, judge_tier, tokens_in, tokens_out, dollars, latency_ms}`. Every scored run lands here. `injected` records what the accountant composed, in order, so a composition is replayable and the stale-serve and miss-rate instruments are queries (was a superseded fact served; was the evidence segment ever injected) rather than new logging. The sensitivity table, the arm comparison, and the cost accounting are all queries over this one file.

**Rejection record.** `{rej_id, timestamp, stage, contract_version, tier, error}`. One line per contract rejection out of `generate`, so the rejection rate per tier per contract is a query, not a recount. Accepted calls need no separate record; every artifact already carries its tier.

## Grouping

Grouping by house, school, or allegiance is not the tree. The topic tree holds narrative flow (books, chapters, arcs), because that is what folds and range-scans. House, school, and allegiance are membership facts, rows like `{harry_e01, member_of, gryffindor_e12}`, and a grouping is a query over fact rows, not a place in a hierarchy. An entity belongs to every group its facts support; the wiki renders whichever grouping a page wants by querying.
