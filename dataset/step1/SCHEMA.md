# Schema

Sixteen JSON Lines files regrouped from the run's packages, one file per record type, plus the
run's call log, the papers' attribution and the receipt. One JSON object per line, UTF-8.

Every row carries `doc_id`, the sha256 of the document's bytes, added at packing from the package
the row came from. It is the join key to every other file here and to Step 0, whose
`documents.jsonl` holds the text. Character offsets are indices into that text for the same
`doc_id`, as Python string indices over the decoded UTF-8; read it without normalising and
`text[quote_start:quote_end]` is the quote exactly.

## Ids

- `doc_id` and `unit_id`: content hashes, the same values as Step 0.
- `node_id`: `<tag>:doc` for the document's own node, `<tag>:n<i>` for an entity, where `<tag>`
  is the first eight characters of `doc_id`. Readable, minted per document; `<tag>` is for
  reading, and `doc_id` is the key.
- `fact_id`: `<tag>:u<unit position>:f<n>`; a document-record fact is `<tag>:doc:f<n>`.

Node and fact ids are unique within a document and, in this release, across it; a bigger
corpus keys on `doc_id` plus the id.

## documents.jsonl

The document as the run saw it. The same fields as Step 0's document row, with `text_length`
in place of `text`.

| field | type | meaning |
|---|---|---|
| `doc_id`, `sha256` | string | the document's hash, twice, as Step 0 names them |
| `source_uri` | string | where Step 0 read the file: the raw dataset path for a book or paper, `chats/longmemeval/<history>/<session>.json` for a chat |
| `title`, `author`, `source_class` | string or null | as Step 0 |
| `occurred_at` | string or null | the earliest unit's date, in Step 0's date forms |
| `ingested_at`, `loader`, `flags` | | Step 0's run stamp, version and notes |
| `text_length` | integer | length of the text in characters |

## units.jsonl and pieces.jsonl

Step 0's split plan for these 81 documents, copied into the package so it stands alone. The
fields are Step 0's; a unit also carries `kind`, the kind of its pieces (`body`, `front_matter`,
`references`, `user`, `assistant` and the rest).

## nodes.jsonl

One row per major entity the document is about, plus one row per document (`kind` `document`).
Minor entities have no node: in a book or paper, a fact from a major to a minor is a property of
the major with the minor's name as its value; in a chat, a minor's facts are carried by the
session's node as `mentioned` facts.

| field | type | meaning |
|---|---|---|
| `node_id` | string | see Ids |
| `name` | string | the entity's name as the reading settled it |
| `kind` | string or null | an open vocabulary, the model's own word: `person`, `place`, `object`, `event`, `product`, `work`, `organisation`, `store`, and 90 more; 99 distinct in this release. On a chat the kind comes from the salience call, which may not answer `thing`; a `thing` would be stored null, and none was. |
| `created_from_unit` | string | the unit the entity was first found in |
| `provenance` | object | `ingestor`, the version; `names`, every name the unit-local entities that became this node carried |

## aliases.jsonl

| field | type | meaning |
|---|---|---|
| `alias` | string | a surface form found in the text |
| `node_id` | string | the entity it names |
| `first_seen_unit` | string | the unit it was first found in |

## edges.jsonl

| field | type | meaning |
|---|---|---|
| `predicate` | string | `appears_in`: an entity appears in the document; `has_unit`: the document holds a unit |
| `subject`, `object` | string | for `appears_in`, the entity's node and the document's node; for `has_unit`, the document's node and the `unit_id` |
| `units` | array of string | `appears_in` only: every unit the entity appears in |
| `position` | integer | `has_unit` only: the unit's position |

## facts.jsonl

One row per stored fact. Every fact with a quote slices from the document at its offsets; this
was checked at packing against Step 0's text. Three shapes share the file, told apart by
`direction` and `quote`:

- a fact read from the text about a major entity (`direction` `forward` or `inverse`, quote and
  offsets set);
- a chat minor's fact carried by its session (`direction` `mentioned`, subject the session's
  document node, quote and offsets set, the entity's name in `provenance.subject_name`);
- a document-record fact (`quote`, `quote_start`, `quote_end` and `unit_id` null,
  `provenance.from` `document record`): `has_title`, `has_date`, `has_source_class`,
  `has_author` when Step 0 names one, and `belongs_to_history` on a chat, built from Step 0's
  document row with no model call. 324 in this release. Nothing searched the text for them; the
  date fact's `provenance.flags` carries the extractor's `date:` notes saying where the date came
  from.

| field | type | meaning |
|---|---|---|
| `fact_id` | string | see Ids |
| `subject` | string | the node the fact is about: a major, or the document's node |
| `predicate` | string | the model's own words in snake_case, never merged or renamed; 2,235 distinct in this release. `stated`, on a chat, is one user sentence that states a detail |
| `object` | string | the value, or a `node_id` when `object_is_node` is true |
| `object_is_node` | boolean | whether `object` names another node of the same document |
| `direction` | string | `forward`: the subject is the fact's subject; `inverse`: the fact was read with a minor as its subject and stored under the major it points at; `mentioned`: a chat minor's fact carried by the session's node |
| `qualifiers` | string or null | role, timing, manner, as the text gives them |
| `rank` | string | `active` throughout |
| `unit_id` | string or null | the unit the quote lies in; null on a document-record fact |
| `quote` | string or null | a verbatim slice of the document, no ellipsis; null on a document-record fact |
| `quote_start`, `quote_end` | integer or null | the slice's offsets into Step 0's `text` |
| `valid_from` | string or null | when the fact began to be true, only when the quote states it |
| `occurred_at` | string or null | the unit's date, copied down: when it was said; the document's date on a record fact |
| `tier` | string or null | the model that read it; null on a record fact |
| `author` | string or null | the voice: the turn's speaker on a chat, else the document's author |
| `provenance` | object | `ingestor`; `matched_by`, how the quote was located (`exact`, `normalised`, `unwrapped`, `words`); `subject_name`, the subject as the reading wrote it (the minor's name on a `mentioned` fact); `corrected_from`, the fact's earlier wording when the passage check reworded it, else null; `from` `document record` and `flags` on a record fact |

## cells.jsonl

Narrative, not claims: what happened to an entity in a unit, in the reading's words, with no
quote. Books and papers only.

| field | type | meaning |
|---|---|---|
| `node_id` | string | the entity, or the document's node for a unit summary |
| `unit_id` | string | the unit |
| `text` | string | the cell |
| `tier` | string | the model |
| `provenance` | object | `kind` `unit_summary` on a document's node; else `entity_names`, the names the cell was written for |

## abstracts.jsonl

| field | type | meaning |
|---|---|---|
| `node_id` | string | the document's node, or a major entity's |
| `text` | string | for a document, a fold over its unit summaries (a chat's is the reading's own summary of the session); for an entity, a fold over its cells and facts |
| `tier`, `updated_at` | | the model and when |

## adjudicated_facts.jsonl and attributes.jsonl

For a major with four or more facts, one call consolidated them. Each row cites the raw facts
behind it in `from_facts`; the raw facts stay in `facts.jsonl`. A consolidated row asserts
nothing its raw facts do not.

| field | type | meaning |
|---|---|---|
| `node_id` | string | the major |
| `predicate`, `object`, `qualifiers` (adjudicated_facts) | | the consolidated claim |
| `attribute`, `value` (attributes) | | a property, such as `is_a` or `occupation` |
| `from_facts` | array of string | the `fact_id`s behind it |
| `tier` | string | the model |

## contradictions.jsonl

Facts of one entity within one document that disagree, resolved by the state of the entity at
the document's end. Both facts stay stored and active.

| field | type | meaning |
|---|---|---|
| `node_id` | string | the entity |
| `note` | string | what disagrees |
| `from_facts` | array of string | the facts involved |
| `holds` | string or null | which fact is true at the document's end; null when the reading could not say (3 of 48) |
| `because` | string or null | why |

## rejections.jsonl

Everything turned away, so the gate's rate can be read.

| field | type | meaning |
|---|---|---|
| `stage` | string | `entities`, `facts` or `verify` |
| `unit_id` | string | the unit |
| `category` | string | `facts`: `not_found`, `paraphrase`, `duplicate`, `self_reference`, `unlisted_subject`; `entities`: `no_surface_form`, `span_claimed`; `verify`: `unsupported` |
| `subject`, `predicate`, `object`, `quote` | | the fact as the model wrote it (`facts`, `verify`) |
| `name`, `forms` | | the entity and its surface forms (`entities`) |
| `why` | string | the check's own words, where it gave them |

## ledger.jsonl and candidates.jsonl

The reconciliation of unit-local entities into document entities, for books and papers. A
ledger row is a verdict; a candidate row is a scored pair the reconciliation weighed. `a_unit`
and `b_unit` are unit positions.

| field | type | meaning |
|---|---|---|
| `a`, `a_unit`, `b`, `b_unit` | | the two unit-local entities by name and unit position |
| `verdict` (ledger) | string | `same`, `different`, `unsure` |
| `how` (ledger) | string | `same_name`: united on sight; `same_name_conflicting_is_a`: same name but their `is_a` disagreed, sent to the judge; `judged`, `judged again`: a judge call |
| `evidence` (ledger) | string | the reason, the judge's own words when it ruled |
| `reason` (candidate) | string | why the pair was offered: `shared_surface`, `shared_word`, `is_a_link` |
| `name_score`, `cooc_score`, `combined` (candidate) | number | the name similarity, the overlap of the two entities' unit casts, and 0.7 name plus 0.3 co-occurrence |
| `round`, `tier` (candidate) | | the judging round and the nomination's weight |

A chat's ledger holds only `same_name` rows: the same name in two turns is one entity, no judge.

## completions.jsonl

One row per document: `counts` (units, entities, majors, minors, mentions, facts kept, stored,
without a major, rejected, cells, flagged, upheld, corrected, dumped, `document_facts`,
`facts_mentioned`, and the rest), `stats` (calls, cost, candidate pairs, judge calls and rounds,
how quotes were matched, rejections by category), `excluded` (units triage left out) and
`demoted` (majors with nothing to summarise).

## calls.jsonl

Every model call: `stage` (`session`, `salience`, `support`, `correct`, `verify`, `triage`,
`entities`, `facts`, `cells`, `judge`, `fold`, `entity_abstract`, `adjudicate`, `ping`), `model`,
`tier`, `in` and `out` tokens, `seconds`, `cost` in dollars, `doc`. The receipt's cost is the sum.

## attribution.jsonl

The five CC-BY papers, the same shape as Step 0's: `doc_id`, `source_uri`, `title`, `authors`,
`year`, `venue`, `doi`, `openalex_id`, `license`, `source_url`, `pdf_sha256`, `bytes`.
**Rendering the authors, the title and the license is a condition of the license** wherever a
paper's quote is shown.

## receipt.json

The run's totals: documents by group, the counts above summed, quotes by how they matched,
rejections by category, calls by stage, cost, start and finish. Its `minutes` covers the last
block of the run only; the kernel ran about 2.8 hours in all.
