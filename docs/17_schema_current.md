# Schema, current state

**2026-08-27.** Supersedes the schema sections of `docs/15_schema_and_architecture.md`, which
predates the prior-art pass. Incorporates the six changes from `docs/16_schema_prior_art.md`.
Citations refer to the References section of `docs/16`; items marked there as `[verify]` are used
here as design input but are **not citable** until confirmed.

Seven record types plus instrumentation. Field names are indicative.

---

## Source layer

### Document
```
{doc_id, corpus_id, work_id, kind: text|chat, title,
 source_url, sha256, ingested_at,
 provenance: {contributed_by, resources, ts}}
```
Raw text sits beside it on disk and is never edited. Ids are content hashes, so re-ingesting the
same material is a no-op rather than a duplicate.

`provenance` is immutable and exists on every derived record below as well. It carries who
contributed the record, what resources it drew on, and when. This is the substrate for read-time
access control (Collaborative Memory, arXiv:2505.18279).

### Unit
```
{unit_id, doc_id, unit_type: chapter|book|play|ode|hui|session,
 work_ordinal, unit_ordinal, title, span: [start, end], text}
```
The atom. Every derived record points here.

`unit_type` carries heterogeneity forward as data rather than erasing it. A Euripides play has no
siblings to fold with; an Oz chapter does. Normalising to one record shape is correct;
flattening the distinction is not.

---

## Node layer

### Node
```
{node_id, canonical_name, kind: person|org|place|thing|topic|event,
 created_from_unit, provenance}
```
**Entities and topics are the same type.** Dr. Fang is a node, the IT 494 project is a node, the
Chūnin Exams is a node. `kind` exists because extraction prompts differ per kind and because it
participates in the δ constraint below — not because storage differs.

**Works are nodes.** "Oz book 2" is a `topic` node. This removes the need for a separate
chapter-summary record type: the plot axis is cells on work nodes, and the book blurb is that
node's abstract.

**Type versus instance is not a kind distinction.** The Chūnin Exams is one node whose sequence
holds every exam event; an instance is promoted to its own node only when it accumulates enough
to warrant one. Same promotion mechanism as minor-entity → major-entity. This matches wiki
practice, where instances appear as sections until they earn a page.

### Alias
```
{alias, node_id, alias_kind: name|nickname|epithet,
 first_seen_unit, evidence_quote}
```
The keyword list mapping surface forms to one node. Resolution reads it; nothing writes over it.

---

## Fact layer

### Fact
```
{fact_id, subject, predicate, object, object_is_node,
 qualifiers, rank: preferred|normal|deprecated,
 unit_id, quote,
 valid_from, valid_to,            # [from, to), upper exclusive
 asserted_at_unit, asserted_at_wallclock,
 tier, contract_version, provenance}
```

**Append-only.** Nothing is overwritten, and there is no stored `superseded_by`: supersession is
computed at read time over a functional-predicate list.

**`rank` is new, and it fills a gap supersession cannot.** Computed supersession handles *the
world changed* — a later assertion collides with an earlier one on a functional predicate.
It does not handle *we were wrong*: an extraction error has no later assertion to supersede it,
and deleting violates append-only. `deprecated` means present, preserved, and excluded from reads
by default. Source: Wikidata ranks (Vrandečić & Krötzsch 2014, CACM 57(10), DOI 10.1145/2629489).

This is not hypothetical. The Ash-Catchum-aliased-to-Ursa error in the live archive was resolved
by appending an is-distinct-from assertion rather than editing — the same pattern, done ad hoc.

**`qualifiers` carry n-ary relations, not just timing.** Ozma rules Oz *as restored by Glinda*;
Zhuge Liang serves Liu Bei *in the capacity of Chancellor*. Without qualifiers, role information
becomes either lost detail or invented predicates, and invented predicates are the sprawl that
silently breaks supersession. Source: Wikidata qualifiers, same paper.

**Interval convention is `[from, to)`** — lower bound inclusive, upper exclusive, following SQL.
Stating it prevents the off-by-one that appears wherever two intervals abut. Source: Rost et al.,
*Bitemporal Property Graphs*, pp. 6–7 `[verify venue]`.

**Fact-level validity subsumes property-level.** Rost puts validity on individual properties
because his vertices carry properties directly. Ours do not — our facts *are* the properties — so
this is already covered. Recorded so it is not re-opened.

### Predicate registry
```
core:    ~15-20 universal predicates, including every functional one
corpus:  per-corpus vocabulary, namespaced
delta:   allowed (subject_kind, predicate, object_kind) triples
```

**Namespaced predicates** — `appearance.height`, `appearance.build` — give attribute grouping for
free. That is how a "Physical description" section assembles itself, and it stays human-readable.

**δ is new.** A table of allowed `(subject_kind, predicate, object_kind)` triples, with violations
logged as rejections rather than stored. Source: Angles, *The Property Graph Database Model*,
Definition 2 `[verify venue]`, where δ "defines the edge types allowed between a given pair of
node types."

This catches a class of error **the quote gate structurally cannot see**: a fabricated relation
can carry a perfectly genuine quote. `parent_of` between a place and a thing passes every other
check in the system.

### Merge ledger
```
{attr_id, node_id, attribute, merged_from: [fact_ids in order],
 absorbed_node, evidence, tier}
```
Which rows, in what order, folded into an attribute. The anti-black-box requirement, stored as
data rather than asserted.

---

## Summary layer

### Cell
```
{cell_id, node_id, unit_id, corpus_id,
 work_ordinal, unit_ordinal, text, tier, provenance}
```
One node's narrative for one unit. The expensive layer and the thresholded one.

**Ordered by `(work_ordinal, unit_ordinal)`, never a single integer**, because a node's cells
span multiple works.

Keyed by (node, unit), which flattens two separate scenes involving the same character in one
chapter into one cell. Accepted deliberately; recorded so it is a decision rather than an
omission.

### Abstract
```
{node_id, corpus_id, text, children_hash, tier, updated_at, provenance}
```
One paragraph per node **per corpus**. Salience is corpus-scoped: Tip is a major entity in Oz and
a passing citation in a conversation archive. The node is global; its narrative is local.

`children_hash` is computed over the node's cells, so the abstract is stale exactly when its
cells change. Refold is incremental, never a full pass.

**Composition, not storage.** A visual description is not a stored artifact — it is a query over
`appearance.*` fact rows, rendered. Free to regenerate, automatically current, and every clause
traces to a quote. This is also why the Holmes contamination probe passes by construction: there
is no deerstalker fact row, because Doyle never wrote one, so nothing composes.

---

## Instrumentation

```
Rejection  {rej_id, ts, stage, contract_version, tier, error}
Run        {run_id, ts, arm, question_id, injected_ids, verdict,
            judge_tier, tokens_in, tokens_out, latency_ms}
Consult    {consult_id, ts, cued_node_ids, retrieved_ids, used_ids}
```

`Consult` is the proactive-recall instrument. It needs to exist from day one because the rate is
meaningless without weeks of collection. See `docs/20_evaluation.md` for the unresolved question
of how `used_ids` gets populated.

---

## Invariants

1. Raw is immutable. Ids are content hashes.
2. Nothing is overwritten. Supersession, merges and permissions all resolve at read time.
3. Every assertion carries a verbatim quote that must appear in its unit. Unverifiable claims are
   flagged or dropped, never asserted.
4. Every model call goes through the two interfaces and records its tier.
5. Every contract rejection is logged, so rejection rate per stage per tier is a query.
6. The abstract is a fold over cells; staleness is a hash comparison, never a wall-clock guess.
7. Every δ violation is a rejection, not a stored row.

---

## Still open

- **Mixed-corpus ordering.** Books order by narrative position, chats by wall-clock. A store
  containing both has no defined sequence, and `(work_ordinal, unit_ordinal)` silently
  interleaves incomparable things.
- **Nothing demotes or retires.** Promotion is one-way. The live archive already carries 82
  orphaned sheets from exactly this.
- **`kind` does two jobs** — routing extraction prompts, and constraining δ. Those will want to
  diverge; `event` and `topic` need the same predicates and very different prompts.
- **Conformance testing.** Two adapters, twelve operations, no shared test suite. The realistic
  failure is that the files adapter is developed against and the Neo4j adapter rots.
