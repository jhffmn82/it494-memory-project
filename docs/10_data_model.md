# How information is modeled

Prepared by the assistant. The schema for every object the harness stores, with Harry Potter as the worked example throughout, because the questions get crisp on a concrete corpus. Storage is plain files, JSONL for rows and markdown for prose, in a directory layout that git can diff; SQLite was considered and deferred (one dependency bought nothing at this scale that sorted JSONL does not give, and files keep every artifact human-readable, which the QA rule wants). Identifiers are short content hashes, so re-ingesting the same material yields the same ids.

## Source layer

**Document.** `{doc_id, corpus_id, kind: chat|text, title, ordinal, meta}` plus the raw text, stored verbatim and never edited. A book chapter and a chat session are both documents. The mock's append-only rule carries over: this layer is the write-ahead log, and everything above it can be rebuilt from it.

**Segment.** `{seg_id, doc_id, span: [start, end], ordinal, boundary_method: model|texttiling, tier}`. The atom. A segment knows exactly which characters of which document it covers, so every downstream claim can point back to text.

## Tree layer

**Leaf.** Markdown file with YAML front matter: `{leaf_id, seg_id, topic_path, title, written_by_tier, contract_version}` and a summary body written against the summary contract. One segment, one leaf.

**Node rollup.** `{node_id, topic_path, children_hash, folded_by_tier}` plus prose built only from child summaries. `children_hash` is the content hash over the node's children; the maintain pass refolds a node only when the stored hash and the recomputed hash disagree. Example: `hogwarts/gryffindor` carries a rollup over its leaves; a new leaf under it changes the hash and marks it stale.

## Entity layer

**Entity page.** `{entity_id, canonical_name, kind: person|org|place|thing, created_from}` plus an index body: for each attribute, the current value, the fact rows behind it, and quoted mention lines with segment pointers. A page never copies content; it points. Example: the page for Peter Pettigrew indexes every mention, including the ones that predate anyone knowing Scabbers was him.

**Alias record.** `{alias, entity_id, kind: name|nickname|epithet|pronoun-context, first_seen_seg, evidence_quote}`. The keyword list that maps to one individual, exactly as specified in the proposal. Example rows: `Scabbers -> pettigrew_e01`, `Wormtail -> pettigrew_e01`, `Peter -> pettigrew_e01`. Pronoun resolution happens at distill time (a bought model capability); the alias ledger records the durable names.

## Fact layer

**Fact row.** One JSONL line: `{fact_id, asserted_at: source_position, subject: entity_id, predicate, object, qualifiers, seg_id, quote, extracted_by_tier, contract_version}`. `asserted_at` is position in the corpus (chapter or session ordinal), not wall-clock, because narrative time is what supersession runs on.

**Supersession.** Not a deletion and not an edit: a later row with the same subject and predicate marks the earlier row superseded, and the read rule is later-assertion-wins. Both rows remain, so "what was believed at chapter 3" is answerable. The worked example, which is also the demo's best moment:

```
{f_0412, ch03, scabbers_e07, is_a, rat, {}, seg_031, "Scabbers the rat dozed..."}
{f_2210, ch19, scabbers_e07, same_as, pettigrew_e01, {}, seg_198, "...you're Peter Pettigrew"}
{f_2211, ch19, pettigrew_e01, is_a, wizard(animagus), {}, seg_198, "..."}
```

The `same_as` row triggers an entity merge: `scabbers_e07` folds into `pettigrew_e01`, the alias ledger gains the mapping, and every prior Scabbers fact re-attaches to Pettigrew, superseded where it conflicts (a rat, now an animagus form) and retained where it does not (owned by Ron, still true of the disguise period). This one case exercises aliasing, merging, supersession, and time-scoped truth, which is why it leads the demo.

**Merge ledger entry.** `{attr_id, entity_id, attribute, merged_from: [fact_ids in sequence], written_by_tier}`. The record of which tokens, in what order, merged into an attribute understanding: a hundred employment-shaped fact rows collapsing into one "works at" attribute leave their trail here. This is the anti-black-box requirement from the proposal, stored as data.

## Evaluation layer

**Question record.** `{q_id, corpus_id, band: rollup|leaf|synthesis|corrected, text, fixed_answer, evidence_segs, certified: {tier: pass|fail}}`. The corrected band requires a superseded fact in its evidence. Certification results are stored per tier, so "every bare tier failed this closed-book" is a queryable property, not a claim.

**Run row.** `{run_id, timestamp, arm, config_hash, tiers: {stage: model}, q_id, injected: [ids in order], verdict, judge_tier, tokens_in, tokens_out, dollars, latency_ms}`. Every scored run lands here. `injected` records what the accountant composed, in order, which is what makes a composition replayable and makes the stale-serve and miss-rate instruments queries (was a superseded fact served; was the evidence segment ever injected) rather than new logging; the sensitivity table, the arm comparison, and the cost accounting are all queries over this one file.

**Rejection record.** `{rej_id, timestamp, stage, contract_version, tier, error}`. One line per contract rejection out of `generate`, so the rejection rate per tier per contract that the build plan validates against is a query, not a recount. Accepted calls need no separate record: every artifact already carries its tier.

## Grouping, answered

The proposal asks how characters are grouped: by house, by school, by allegiance. The model's answer: grouping is not the tree. The topic tree holds narrative flow (books, chapters, arcs), because that is what folds and range-scans. House, school, and allegiance are membership facts, rows like `{harry_e01, member_of, gryffindor_e12}`, and a grouping is a query over fact rows, not a place in a hierarchy. An entity belongs to every group its facts support, which dissolves the which-axis-wins question: all of them, none exclusively, and the wiki demo renders whichever grouping a page wants by querying.
