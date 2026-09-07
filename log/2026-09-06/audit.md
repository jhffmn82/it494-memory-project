# Audit: the ingestor against the project, and the project against itself

2026-09-06. Two audits in one file. The first reads `notebooks/factledger-ingestor.py` against
SCHEMA.md, BUILD.md, the brief (`log/2026-09-05/ingestor-brief.md`) and
`docs/entity-resolution.md`, record by record and rule by rule. The second reads the project's
living documents against each other and against the code that now exists. Everything marked
PROPOSED is Justin's to rule; everything marked DECISION is a call I made to keep building and
is his to reverse.

Status of the evidence: the offline battery (`test_ingestor.py`, 70 checks) ran against the
extractor's real export with a scripted model, and a six-lens adversarial review of the code
(32 findings confirmed and applied as version 0.2, see README.md) preceded the paid run.
**No model call has been made.** Every claim below that needs the model (rejection rates,
cost, the tier spread, the roster's effect on the judge) is marked as untested.

## Part 1: the ingestor against the project

### 1.1 Record by record against SCHEMA.md

| record | SCHEMA fields | what the package writes | note |
|---|---|---|---|
| document | doc_id, source_uri, sha256, title, author, source_class, text, ingested_at, occurred_at, loader | all but `text`; adds `flags`, `text_length` | The package does not copy the text: the merge reads it from the export by `doc_id`, so the text exists once (DECISION 1). `flags` is the extractor's field, still not in SCHEMA (09-05 audit finding 4, PROPOSED there, unchanged). |
| unit | unit_id, doc_id, position, label, start, end, occurred_at, occurred_until | verbatim from the export | |
| piece | doc_id, unit_id, position, kind, start, end, author, occurred_at | verbatim from the export | Carried so the merge can look voice up without a join to the export. |
| node | node_id, name, kind, created_from_unit, provenance | exact; `provenance` holds the salience rank and the member names | One node per document-major, plus one for the document itself (kind `document`). Minors get no node. |
| alias | alias, node_id, first_seen_unit, evidence_quote | exact; the verbatim form with the unit it first appeared in; `evidence_quote` is null | The surface's spans are in the mention rows; a quote would duplicate them. |
| mention | mention_id, node_id?, unit_id, start, end, surface, resolved_by | exact; `node_id` null for a minor; `resolved_by` is always `surface` here | Code located every span by surface form; a span is one mention, the first entity listed keeping it (`shared_spans` counted); the merge's matcher will write other values. |
| profile | node_id, attribute, value, confidence, from_unit | exact; `confidence` is a constant 0.5 | The model is not asked for a confidence; SCHEMA calls these low-confidence by definition. Only majors' profiles are written, since a minor has no node. |
| fact | fact_id, subject, predicate, object, qualifiers, rank, unit_id, quote, quote_start, quote_end, valid_from, valid_to, tier, provenance | exact; adds `author` and `object_is_node`; `rank` is `active`; `provenance.voice_ambiguous` says when `author` is null because the same words occur in two voices | PROPOSED A: `author` on the fact, filled by the piece lookup at write time (the word is `author`, never `speaker`). PROPOSED B: `object_is_node`, because SCHEMA does not say how a reader tells a node reference from a literal in `object`. PROPOSED C: name the default `rank` (`active`) beside `deprecated`. |
| cell | cell_id, node_id, unit_id, scope_id, text, tier, provenance | exact; `scope_id` is the `doc_id`; one cell per node per unit, two locals' cells joined | DECISION 2: at this stage the document is the scope; the merge re-scopes to the declared grouping. |
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
| Re-runs mint nothing | Done and tested: a package whose `input_hash` (doc_id, unit ids, ingestor version) matches is skipped; two derivations with the same answers agree line for line. On Kaggle a new session starts empty, so the previous version's output attached as an input is copied in first; a document stopped mid-way resumes from a sidecar of its finished units. A version bump of the ingestor invalidates every package by design. |
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
3. ~~The cell rule: an entity gets a cell when at least one accepted fact names it.~~ **Reversed by Justin (evening):** the model's per-unit salience call ("major" only if it would appear in a two-sentence summary of the unit) decides the cells and which candidate pairs the judge sees, as in the demo; the fact rule is printed beside it as a diagnostic only. With it, the demo's judge-everything reconciliation, the re-judging of unsure pairs, and the folds on Terra were restored; all four had been dropped without a ruling.
4. **The package layout:** one JSONL file per document under `packages/<group>/<name>.jsonl`, mirroring the raw layout (`oz/01_55.jsonl`, `papers/hipporag-2024.jsonl`, `longmemeval/<session>.jsonl`), every line a record with a `record` field, the completion record last; `manifest.jsonl`, `receipt.json`, `calls.jsonl`, `rejections.jsonl` and `ingest.log` beside them.
5. **Predicates** (ruled in chat): the model's string, normalised to `lowercase_snake_case` only; a `predicate_census` per document; no consolidation call; the controlled list is the merge's.
6. **The roster** (agreed in chat): entities that earned a place (a fact or a second mention) and every predicate used, shown to the next unit as suggestions; a declared continuation is a ledger row.
7. A one-unit document's abstract is its unit summary and its entity abstracts are its cells; no fold call.
8. Salience: an entity is major when any of its surface forms (over two characters) appears in the abstract, case-insensitively; the ranked list (in abstract, unit count, fact count) is kept in the node's provenance.
9. A fact whose subject is a minor is not stored, whatever its object; counted as `facts_minor_subject`. A fact from a major to a minor keeps the minor's name as its value.
10. Reconciliation numbers, unruled: exact name or declared continuation unites without a judge; combined score 0.6 name + 0.25 co-occurrence + 0.15 profile; unite at 0.85 and above, keep apart below 0.35, judge between. Name similarity is `difflib` on the names, not an embedding; the embedding is on the dossier.
11. Embedding model `text-embedding-3-small`, $0.02 per million tokens, inline in the dossier record.
12. An entity with at most two children (facts plus cells) gets those children as its abstract without a call.
13. Every unit is derived, whatever the kinds of its pieces. A paper's references unit, a Gutenberg license unit and a chat's header unit (the final extractor makes every session two units, the header alone and then its turns) get the same calls as a chapter; a unit the model finds nothing in costs one call and is recorded empty. Nothing branches on `kind`, which is the rule; the cost and the noise it produces are for the run to show and Justin to rule on.
14. A span is one mention. When two entities list the same surface form, the first listed keeps every occurrence; an entity left with no span is dropped and counted (`span_claimed`).
15. A quote that recurs verbatim in pieces with different authors gets `author` null and `voice_ambiguous` true, rather than the first speaker's voice.
16. When the document abstract was rejected twice, salience falls back to the tie-breakers (two units, or two facts) and the node's provenance carries `in_abstract: null`, so a rejected fold does not drop every fact in the document.
17. A declared continuation unites without a judge only when its target is a named entity; a continuation of an unnamed role, and two units both using an unnamed name, are scored and, in the ambiguous band, judged.
18. A document with exactly one summarised unit takes that summary as its abstract with no fold call; this is what makes a two-unit chat (empty header, turns) cost no fold.
19. The roster shows its 60 most recently seen entities, so the previous unit's new entities are always visible to the next.
20. ~~Partitions by kind.~~ **Replaced the same evening by Justin's triage judge:** no hardcoded kinds anywhere. One call per document tells the model what we are doing, gives it the document's title, author, class and date, and every kind of unit with the first line of each of its units, and asks which kinds to leave out; those units are never derived and the completion record lists them with the reason. The only code check is a cap: an answer leaving out more than half the units is ignored and flagged.
21. **Demotion** (Justin's): a document-major seen in fewer than two units with fewer than three facts is demoted to minor (`DEMOTE_UNITS`, `DEMOTE_FACTS`), so the merge is never asked to nominate it; the node's provenance says `demoted`.
22. **Minors swallowed** (Justin's): a minor's fact about a major lands on the major with the minor's name as its value, marked `direction: inverse` (PROPOSED H on the fact record); a major's fact about a minor is a property as before; a fact between two minors is dropped and counted.
23. **Adjudication** (Justin's): after reconcile, the abstract and salience, one Terra call per document-major over its raw facts (forward and inverse) and its cells returns consolidated facts, attributes and contradictions, each pointing at the raw facts it was drawn from by number; an item pointing at nothing is dropped and counted. Written as `adjudicated_fact`, `attribute` and `contradiction` records beside the raw facts, which stay append-only under them (PROPOSED I: the three record types). An adjudicated item never carries a quote of its own.

24. ~~**A minor's facts about itself are discarded**~~ **Reversed within the hour by 27.** (Justin's ruling, evening of 09-06, after the Oz run showed 373 of 869 kept facts had a minor subject and no major object). Only a minor's fact about a major rolls into the major. Nothing changes in code.
25. **Predicates are free during derive and judged after adjudication** (Justin's direction, same evening): the running predicate list in the fact prompt pushed Luna into misfits (`eliminate` for every killing, `lives_with` for a palace, `has_release_date` for the Monkeys' release). The list comes out; after the majors are ruled and their minor facts rolled in, one judge call over the majors' consolidated facts, grouped by predicate, merges a group only when one predicate fits every fact under it, with a reason per merge. PROPOSED J: each fact keeps the model's original predicate string beside the merged one. Built the same evening (stage C of 0.5): the list is out of the fact prompt; `judge_predicates` runs one Terra call after adjudication over the majors' consolidated facts, eighty predicates a call with counts and examples; `adjudicated_fact.predicate_raw` beside `predicate`; a `predicate_merge` record per merge with its reason; a merge naming nothing the document uses is dropped and counted.
26. **Withheld text.** The public Step 0 dataset ships the 141 reference papers with `text: null` and a `papers.jsonl` row (file, sha256, source URL). The loader rebuilds the text from the PDF under the private papers dataset, checks the sha256 and the units' end, and reads it with PyMuPDF exactly as the extractor did (pages joined with a newline; the dataset's PROVENANCE.md wrongly says pdfplumber and form feeds). All 141 rebuild byte-identical locally. A first reply that misses its schema is now logged in `retries.jsonl` (Oz: 38 adjudications took 70 calls and nothing said why), and an adjudicated attribute may carry a null value, the one shape that was rejected twice.

27. **A minor's own facts ride into the major it is tied to** (Justin's ruling, replacing 24): under the first fact tying a minor to a major, the minor's facts about itself follow as lines marked `about`, in Terra's adjudication listing and in the package, so the adjudicated fact can read "Dorothy lodges with Boq, the richest Munchkin" and point at the quotes behind both. A riding fact is stored under each major it rides into, under an id of its own (`h(fact_id, "rides into", name, first_unit)`) with `provenance.rides_on` naming the fact it rides on; `direction: about` joins forward and inverse (PROPOSED H widened). A minor tied to no major still keeps nothing (`facts_minor_subject` counts those; `facts_riding` counts what rode). One function, `landings`, decides where every fact lands and both the package writer and the adjudication read it.

28. **Rolling reconciliation, and the both-named rule** (Justin's design, 09-06 evening; replaces 17 and 19 and the end-of-document judge of the first Oz run). As each unit lands, its locals are set against the document so far, in this order: the unit's majors against the rolling majors, the unit's majors still new against the rolling minors, the unit's minors against the rolling majors; minors are never set against minors. Within a corpus an instant match needs both entities named: a declared continuation unites without a judge only when both sides are named, and a named local bearing an established named entity's name and kind unites on sight (`same_name`); a declared continuation with an unnamed side is a candidate. Every other nominated pair is judged as the unit lands, so the next unit's roster shows the merged entity; unsure is deferred to one last look at the end, and a final sweep judges what the rolling lists never met. The roster the model sees is every rolling major plus the sixty most recent minors that earned a place (`ROSTER_MINORS`), under each cluster's most used name; the first Oz run's window of sixty by recency alone had hidden Oz, the Emerald City, Kansas and Aunt Em by chapter XV. A unit's ledger and candidate rows are checkpointed with it and replayed on resume without a judge. The dossier gains a `with:` line (what the entity appears alongside), since that is what tells one unnamed "the girl" from another. BUILD.md's reconciliation paragraph to follow (PROPOSED K).

29. **Nothing to fold, no call** (Justin's ruling, 09-07, for the 19,206 chats where Terra stages would have dominated the spend): a major with fewer than `ADJUDICATE_MIN_FACTS` (4) landed facts, all from one unit, is not adjudicated and its raw facts stand (`adjudications_skipped` counted, the result says why); a document with fewer than `PREDICATES_MIN` (8) distinct predicates across its consolidated facts skips the predicate judge (`predicate_judge_skipped`). In the same spirit as the one-summary abstract and the two-record entity abstract that already cost nothing. Ingesting documents in parallel was offered and declined: in practice one does not ingest many novels at once.

30. **The 0.5 review** (six lenses, one refuter per finding; `review-findings-4.json`): 30 confirmed, all fixed the same night; items 24 to 31 of `decisions-ingestor-0.5.md` say what changed. Refuted and left alone: forward-only landing between two majors, inverse lines not restated in the adjudication prompt, the census counting raw predicates.

## Part 2: the project against itself

1. **SCHEMA.md opens "Nine record types plus logs" and lists ten.** `piece` was added on 09-04. One word.
2. **The 09-05 docs patch is still unapplied**, so SCHEMA.md's unit paragraph and rule 4, and BUILD.md's loader paragraph, describe the extractor before the rebuild: "a compressed view of the text", "proposes verbatim marker lines", "body start, body end". The 1.0 extractor numbers every line, the model points by number, regions are piece kinds, and units are the model's groups. The patch in `log/2026-09-05/docs-rulings-2026-09-05.patch` says all of that and its chat sentence ("a run of at least two turns under the cap") now matches the code. Recommend applying it.
3. **`flags` on the document record** is read by the ingestor now (a flagged split lands in the package's document record), so the 09-05 recommendation to declare it in SCHEMA.md has a second reason.
4. **The extractor's export is on Kaggle as the kernel's output** (loader `factledger-extractor 1.5`), after a first run whose Quick Save kept no files; the ingestor was first tested on a reconstruction of that first run (`scripts/rebuild_export.py`, from the run's log and the raw files, verified snippet by snippet to the run's exact counts) and then on the real export, which differs from it: every chat session is two units (header, turns), 44,262 units in all, and the read documents were re-split. The reconstruction script stays as the record of how a lost export can be recovered from the log.
5. **The 09-05 open question about Luna's context window is answered by the run**: no `too long` flag in the receipt; the largest document (Snodgrass 1999, 666k listing tokens) came out as 80 pieces in 80 units, flagged on pointers and cap, not on length.
6. **Units equal pieces on 78 read documents** in the final run, most of them Oz and Holmes. That is ruling 5 of 09-05 working as written, not a fallthrough: grouping joins a piece with the pieces under it and chapters have nothing under them. Consequence for the ingestor: Oz book 1 has 26 units (front matter, introduction, 24 chapters, license), not the 12 my cost model assumed; the read corpus is 5,850 units, the chats 38,412, and the sample 1,177.
7. **The abstract is not reliably the first unit of a paper.** Measured over the 142 papers from the final run's log: 31 have an abstract piece as `front_matter` in unit 0 and 7 as `body` in unit 0; 52 as `body` in unit 1 and 32 as `front_matter` in unit 1; 20 have no piece labelled abstract (folded into a long front matter or, for 3, into a short one). The ingestor does not care, because it derives every unit and branches on nothing; anything that evaluates "the abstract path" by unit position does. PROPOSED F: either the extractor's paper prompt asks for the abstract as its own piece, or the evaluation finds the abstract by label rather than position.
8. **The demo's fact-drop rate was never classified.** v3 dropped 53 of 1,022 facts (5.2 percent); v4 dropped 157 of 1,016 (15.5 percent), and the run printed counts only. The new gate names the match path for every kept quote and the category for every rejected one, and keeps the quote and its nearest text in the rejection row, so the next run's number comes classified.
9. **`docs/entity-resolution.md`'s open question, at what scope a node exists,** is answered for this stage by construction: nodes are document-scoped, carry dossiers, and the merge decides the rest. The cross-scope shape is the merge's to rule, before the second corpus.
10. **The 09-04 open item, cells for entities promoted after being unit-minor,** disappears under the cell rule: a cell exists wherever an entity has a fact, whatever its document-level salience turns out to be. What remains is a major present in a unit only by mention, which the unit summary covers.
11. **plan.md Step 1 names pydantic and fastembed.** Neither is used: a 20-line validator in stdlib and the embedding endpoint, per the brief's stdlib-first rule. plan.md's tool line for Step 1 should say so.
12. **The extractor's `flags_by_kind` shows 40 `merging` and 8 `merging answer` flags on papers**, nearly all "join across a region boundary left alone". That is the merge refusing to move a region boundary, which is correct, and it is also why 90 paper units hold more than one piece kind (a body piece with its footnote). Harmless to the ingestor.
