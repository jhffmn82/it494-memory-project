# Audit: the ingestor against the project, and the project against itself

2026-09-06. Two audits in one file. The first reads `notebooks/factledger-ingestor.py` against
SCHEMA.md, BUILD.md, the brief (`log/2026-09-05/ingestor-brief.md`) and
`docs/entity-resolution.md`, record by record and rule by rule. The second reads the project's
living documents against each other and against the code that now exists. Everything marked
PROPOSED is Justin's to rule; everything marked DECISION is a call I made to keep building and
is his to reverse.

Status of the evidence: the offline battery (`test_ingestor.py`, 59 checks) ran against the
rebuilt export with a scripted model. **No model call has been made.** Every claim below that
needs the model (rejection rates, cost, the tier spread, the roster's effect on the judge) is
marked as untested.

## Part 1: the ingestor against the project

### 1.1 Record by record against SCHEMA.md

| record | SCHEMA fields | what the package writes | note |
|---|---|---|---|
| document | doc_id, source_uri, sha256, title, author, source_class, text, ingested_at, occurred_at, loader | all but `text`; adds `flags`, `text_length` | The package does not copy the text: the merge reads it from the export by `doc_id`, so the text exists once (DECISION 1). `flags` is the extractor's field, still not in SCHEMA (09-05 audit finding 4, PROPOSED there, unchanged). |
| unit | unit_id, doc_id, position, label, start, end, occurred_at, occurred_until | verbatim from the export | |
| piece | doc_id, unit_id, position, kind, start, end, author, occurred_at | verbatim from the export | Carried so the merge can look voice up without a join to the export. |
| node | node_id, name, kind, created_from_unit, provenance | exact; `provenance` holds the salience rank and the member names | One node per document-major, plus one for the document itself (kind `document`). Minors get no node. |
| alias | alias, node_id, first_seen_unit, evidence_quote | exact; `evidence_quote` is null | The surface's spans are in the mention rows; a quote would duplicate them. |
| mention | mention_id, node_id?, unit_id, start, end, surface, resolved_by | exact; `node_id` null for a minor; `resolved_by` is always `surface` here | Code located every span by surface form; the merge's matcher will write other values. |
| profile | node_id, attribute, value, confidence, from_unit | exact; `confidence` is a constant 0.5 | The model is not asked for a confidence; SCHEMA calls these low-confidence by definition. Only majors' profiles are written, since a minor has no node. |
| fact | fact_id, subject, predicate, object, qualifiers, rank, unit_id, quote, quote_start, quote_end, valid_from, valid_to, tier, provenance | exact; adds `author` and `object_is_node`; `rank` is `active` | PROPOSED A: `author` on the fact, filled by the piece lookup at write time (the word is `author`, never `speaker`). PROPOSED B: `object_is_node`, because SCHEMA does not say how a reader tells a node reference from a literal in `object`. PROPOSED C: name the default `rank` (`active`) beside `deprecated`. |
| cell | cell_id, node_id, unit_id, scope_id, text, tier, provenance | exact; `scope_id` is the `doc_id` | DECISION 2: at this stage the document is the scope; the merge re-scopes to the declared grouping. |
| abstract | node_id, scope_id, text, children_hash, tier, updated_at | exact | Document abstract on the document node; one per major. |

Records the package writes that SCHEMA does not name, all under "plus logs": `package` (header),
`edge` (`has_unit`, `appears_in`), `dossier`, `ledger`, `candidate`, `predicate_census`,
`rejection`, `completion`. The `produced_by` edge to the author is not written, because the
author string becomes an entity only at the merge (SCHEMA: "resolved to an entity through the
merge before the document's facts commit"). PROPOSED D: SCHEMA names `dossier` as the record
a package carries for each document-major, since the brief requires it and the merge reads it.

### 1.2 Rule by rule against BUILD.md

| rule | status |
|---|---|
| Two interfaces, `embed(texts)` and `generate(prompt, schema)`, every call with model id, tokens, latency | Done. `CALLS` rows carry stage, model, in, out, seconds, cost, document, unit. Tier is the model id. |
| Schema-invalid output: one retry with the error appended, then a logged rejection | Done. `check_schema` names the failing path; the retry prompt carries it; `REJECTIONS` gets the row. |
| Semantic failure (a quote not in its unit) rejected with no retry, measured separately | Done. Four categories on the quote (`whitespace`, `normalised` are matches; `paraphrase`, `not_found` are rejections) plus `unlisted_subject`, `duplicate`, `empty`; counted per document in `matched_by` and `rejected_by`, summed in the receipt. |
| Fields the model could lie about are never model-supplied | Offsets, ids, unit ordinals, voice and time are code's. `valid_from` is the model's claim, kept only when its year appears in the quote. |
| Grammar-constrained decoding on local tiers | No local tier in this build. |
| Previous unit's summary as coreference context | Done, plus the document roster. PROPOSED E: BUILD's sentence becomes "the previous unit's summary and the document's roster of established entities and predicates". |
| Empty completion record | Done: `completion.empty` is true when a document stored no fact and no cell; `empty` per unit in the unit record. |
| Re-runs mint nothing | Done and tested: a package whose `input_hash` (doc_id, unit ids, ingestor version) matches is skipped; two derivations with the same answers agree line for line. |
| Resolution scores name, co-occurrence and profile together; guards binding | Scores computed and logged separately per candidate (`candidate` rows, the `MergeCandidate` shape). Profile weight 0.15, never a veto (guard 1). Every union has a ledger row with evidence (guard 3). **Not done:** cluster size cap (guard 4) and the merge rate per unit (guard 5); both computable from the ledger, neither computed. |
| Summaries rebuild on a children hash; bound of half the child words, at most 400; name check; a rejected rebuild never stamped | Done. `fold()` retries once with the missing names, then leaves the abstract absent and the reason in the completion record. |
| Batch each unit's cell calls into one | Done. |
| Spend stop before the run | Done, `SPEND_STOP` default $10. |
| Iterate on the cheapest tier; report the spread | Derive on Luna, judge on Terra. The spread is untested. |

### 1.3 The brief's acceptance list

| acceptance | offline | needs the model |
|---|---|---|
| Every fact's offsets slice to exactly its quote; every quote inside its unit | verified, 59-check battery | the rate at which real quotes need each match path |
| Every mention has a span; every minor mention has a null node_id and no node | verified | |
| Re-running mints and rewrites nothing | verified | |
| Cells for every above-threshold entity; abstract names in children; staleness is a `children_hash` mismatch | verified | |
| A chat unit's facts carry the voice of their turn, user and assistant differing | verified on a real LongMemEval session's pieces with scripted facts | the same on real facts |
| Rejection counts by category, cost per document, summary-versus-cells agreement in a receipt | verified (shape) | the numbers |
| Oz book 1 re-derived, rejections classified by hand, within 20 percent of the demo's cost | | all of it |

### 1.4 What is not built

- **The real run.** No key in this environment. `python notebooks/factledger-ingestor.py --sample`
  runs the test variety once `OPENAI_API_KEY` is set, or the notebook runs on Kaggle with the
  export attached as a dataset.
- Guards 4 and 5 of `docs/entity-resolution.md` (cluster cap, merge rate per unit).
- A hand-classification of Oz book 1's rejections, which needs the run.
- The tier spread (Luna against Terra on the judge, and on derive), which needs the run.

### 1.5 Decisions taken to keep building

1. The package omits the document text; the merge reads it from the export by `doc_id`.
2. `scope_id` is the `doc_id` at this stage.
3. **The cell rule:** an entity gets a cell in a unit when at least one accepted fact in that unit has it as subject or object. Code-decided. The model's per-unit salience is not asked for.
4. **The package layout:** one JSONL file per document under `packages/<group>/<name>.jsonl`, mirroring the raw layout (`oz/01_55.jsonl`, `papers/hipporag-2024.jsonl`, `longmemeval/<session>.jsonl`), every line a record with a `record` field, the completion record last; `manifest.jsonl`, `receipt.json`, `calls.jsonl`, `rejections.jsonl` and `ingest.log` beside them.
5. **Predicates** (ruled in chat): the model's string, normalised to `lowercase_snake_case` only; a `predicate_census` per document; no consolidation call; the controlled list is the merge's.
6. **The roster** (agreed in chat): entities that earned a place (a fact or a second mention) and every predicate used, shown to the next unit as suggestions; a declared continuation is a ledger row.
7. A one-unit document's abstract is its unit summary and its entity abstracts are its cells; no fold call.
8. Salience: an entity is major when any of its surface forms (over two characters) appears in the abstract, case-insensitively; the ranked list (in abstract, unit count, fact count) is kept in the node's provenance.
9. A fact whose subject is a minor is not stored, whatever its object; counted as `facts_minor_subject`. A fact from a major to a minor keeps the minor's name as its value.
10. Reconciliation numbers, unruled: exact name or declared continuation unites without a judge; combined score 0.6 name + 0.25 co-occurrence + 0.15 profile; unite at 0.85 and above, keep apart below 0.35, judge between. Name similarity is `difflib` on the names, not an embedding; the embedding is on the dossier.
11. Embedding model `text-embedding-3-small`, $0.02 per million tokens, inline in the dossier record.
12. An entity with at most two children (facts plus cells) gets those children as its abstract without a call.
13. Every unit is derived, whatever the kinds of its pieces. A paper's references unit and a Gutenberg license unit get the same three calls as a chapter. Nothing branches on `kind`, which is the rule; the cost and the noise it produces are for the run to show and Justin to rule on.

## Part 2: the project against itself

1. **SCHEMA.md opens "Nine record types plus logs" and lists ten.** `piece` was added on 09-04. One word.
2. **The 09-05 docs patch is still unapplied**, so SCHEMA.md's unit paragraph and rule 4, and BUILD.md's loader paragraph, describe the extractor before the rebuild: "a compressed view of the text", "proposes verbatim marker lines", "body start, body end". The 1.0 extractor numbers every line, the model points by number, regions are piece kinds, and units are the model's groups. The patch in `log/2026-09-05/docs-rulings-2026-09-05.patch` says all of that and its chat sentence ("a run of at least two turns under the cap") now matches the code. Recommend applying it.
3. **`flags` on the document record** is read by the ingestor now (a flagged split lands in the package's document record), so the 09-05 recommendation to declare it in SCHEMA.md has a second reason.
4. **The extractor's export is not on Kaggle.** Version 347794765 is a Quick Save with zero output files. The ingestor ran on a reconstruction (`scripts/rebuild_export.py`) built from the run's own log and the raw files, verified snippet by snippet: 19,436 documents, 24,156 units, 226,418 pieces, the run's exact counts. The real export must leave the session and become a dataset before the ingestor can run on Kaggle; locally the reconstruction is byte-equivalent for every piece boundary and differs only in `label` (cut at 40 characters by the log) and `ingested_at`.
5. **The 09-05 open question about Luna's context window is answered by the run**: no `too long` flag in the receipt; the largest document (Snodgrass 1999, 666k listing tokens) came out as 80 pieces in 80 units, flagged on pointers and cap, not on length.
6. **Units equal pieces on 64 read documents**, most of them Oz and Holmes (Oz 2 through 28 at 22 to 33 units each). That is ruling 5 of 09-05 working as written, not a fallthrough: grouping joins a piece with the pieces under it and chapters have nothing under them. Consequence for the ingestor: Oz book 1 has 26 units (front matter, introduction, 24 chapters, license), not the 12 my cost model assumed, so the derive call count on the read corpus is about 8,500 rather than 5,000. Chats are unaffected.
7. **The abstract is not reliably the first unit of a paper.** Measured over the 142 papers from the run's log: 49 have an abstract piece as `front_matter` in unit 0, 8 as `body` in unit 0, 43 as `body` in unit 1, 22 as `front_matter` in unit 1, 19 have no piece labelled abstract (folded into a long front matter or, for 3, into a short one), and 1 is mislabelled `appendix`. The ingestor does not care, because it derives every unit and branches on nothing; anything that evaluates "the abstract path" by unit position does. PROPOSED F: either the extractor's paper prompt asks for the abstract as its own piece, or the evaluation finds the abstract by label rather than position.
8. **The demo's fact-drop rate was never classified.** v3 dropped 53 of 1,022 facts (5.2 percent); v4 dropped 157 of 1,016 (15.5 percent), and the run printed counts only. The new gate names the match path for every kept quote and the category for every rejected one, and keeps the quote and its nearest text in the rejection row, so the next run's number comes classified.
9. **`docs/entity-resolution.md`'s open question, at what scope a node exists,** is answered for this stage by construction: nodes are document-scoped, carry dossiers, and the merge decides the rest. The cross-scope shape is the merge's to rule, before the second corpus.
10. **The 09-04 open item, cells for entities promoted after being unit-minor,** disappears under the cell rule: a cell exists wherever an entity has a fact, whatever its document-level salience turns out to be. What remains is a major present in a unit only by mention, which the unit summary covers.
11. **plan.md Step 1 names pydantic and fastembed.** Neither is used: a 20-line validator in stdlib and the embedding endpoint, per the brief's stdlib-first rule. plan.md's tool line for Step 1 should say so.
12. **The extractor's `flags_by_kind` shows 40 `merging` and 8 `merging answer` flags on papers**, nearly all "join across a region boundary left alone". That is the merge refusing to move a region boundary, which is correct, and it is also why 90 paper units hold more than one piece kind (a body piece with its footnote). Harmless to the ingestor.
