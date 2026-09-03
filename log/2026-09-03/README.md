# Working log: 2026-09-03

Design session on the laptop, no code written. Started from "can Graphiti's namespaces module
be reconfigured for SQLite" and ended with the merge rules, the retrieval design, the raw text
layer, the process architecture, and the dataset list for the preprocessor rebuild. Everything
below is a decision reached in dialogue with Justin unless marked PROPOSED, which means it
changes SCHEMA.md or BUILD.md and needs his ruling before it is edited in. The archive leaf for
the session is local to the laptop (eras/_staging is gitignored); this file is the copy that syncs.

## Pick up here

1. `git pull` first. This clone was 11 behind this morning; the PC rewrote the repo on 09-02.
2. Read this file, then SCHEMA.md and BUILD.md, and note the PROPOSED items below against them.
3. Before the corpus run: change the ingestion notebook's package output (section "Package format").
4. Then the order in "Build order".

## Graphiti, closed

graphiti_core/namespaces/ is a facade (typed CRUD wrappers, zero Cypher). The database coupling
is in driver/, driver/operations/, driver/search_interface/, and search/search_utils.py
(about 1,200 lines, 30+ provider branches). No SQLite backend exists upstream; Kuzu is the only
embedded backend and its repo was archived 2025-10-10; FalkorDB Lite (PR #1240) is Linux/macOS
only. Confirms the 08-28 decision not to build on Graphiti. Nothing to port; borrow the
bitemporal edge idea, which the fact table already has as valid_from and valid_to.

## The merge (document package into the global store)

- A document package is the write-ahead log for the global level. A bad global merge is undone by
  replaying packages, never by editing the store.
- Nodes are corpus-global with per-scope aliases and per-scope salience. Minor entities never
  become global nodes; they stay in unit records. Minor-to-minor facts do not commit; they replay
  if either end is later promoted. Do NOT use rank=deprecated for below-threshold; that field
  means "we were wrong".
- Salience for the merge is document-level: an entity named in the document abstract is major;
  unit count and fact count break ties. Chunk-level salience stays the bar for cells.
- Candidate rule for the judge:
  - major to major: nearest-k global majors by dossier embedding, plus any exact surface hit;
  - any pair on an exact surface hit inside the same set: a candidate, never an automatic union;
  - minor to minor with no exact hit: never paired.
  Bare surface forms ("Mary", "the doctor") nominate only when the entity stage flagged them
  named; canonical (fullest) names nominate always.
- A collision on the primary name that the judge rules different gives BOTH nodes a
  parenthetical disambiguator, supplied by the judge in the same verdict call, drawn from each
  dossier's most distinctive fact, for example "Dr. Smith (dentist)". Display only; node_id stays
  a hash. Once a primary name has collided it becomes a pure alias pointing at every node
  carrying it.
- The alias table has three row kinds: name to one node; name to several nodes (demands a
  judge); pair recorded as kept apart (the notebook's `different` set, made durable).
- The judge runs twice on different evidence: within-document (two chapter dossiers) and at
  merge (document dossier against a global abstract). The second gets the strong tier.
- Commit unit by unit in position order so the collision check runs per unit, even when the
  document arrives whole.
- Supersession policy is read-time (invariant 2). The store records collisions; the reader
  applies: latest wins when both facts carry a date, both served with sources when not. A
  proposed "sequential vs witnesses" manifest flag was withdrawn as a literature accommodation.

## PROPOSED schema additions (Justin to rule; SCHEMA.md unchanged)

- Document node: node_id = doc_id, kind document, name = title from the loader; cells = unit
  summaries; abstract folded from them; structural edges has_unit (ordered), member_of set
  (optional position), appears_in from entities carrying salience and unit_count; provenance
  fields (source_uri, sha256, occurred_at?, ingested_at, loader) cite the loader, not a quote.
  Author is a produced_by edge to a resolved entity; the loader hands over the string.
- Set node: any user-declared or detected grouping (series, thread, project, era). Nestable,
  multi-parent; order lives on the membership edge. Replaces "corpus/series". Uses that
  survived scrutiny: disambiguation scope, theme questions (fold abstracts over a group),
  policy boundaries (local-only vs synced), raw text containment. Retrieval scoping for speed
  was dropped as unnecessary.
- Fact gains quote offsets (start, end within the unit). The notebook's regex gate already finds
  the match; keep the position.
- Storage: SQLite as the whole store (FTS5 plus sqlite-vec), with document packages as JSONL.
  SCHEMA.md currently says "SQLite and JSONL in a single folder" and BUILD.md keeps embeddings in
  a sidecar; a vector table with a header (model, dim, built_at) and rebuild-on-mismatch is the
  same rule in one file. One SQLite file per corpus.

## Layer 0: raw text (build first)

documents; units (verbatim, spans); containment edges; external-content FTS5 over units; back-links
with quote offsets on facts, unit_id on cells and mentions, children_hash on abstracts; a stored
quote audit (one SQL statement over facts); get_source in the port and an MCP source tool;
a rebuild-from-units command. The merge's first act on a package is writing documents and units,
before any fact.

## Retrieval (step 2)

Embed the query once. Seeds = nearest dossiers (unfiltered) plus alias FTS. Four channels: FTS5
bm25 over derived text; sqlite-vec nearest-k; one hop from seeds over facts; FTS5 over raw unit
text. Reciprocal rank fusion, 1/(60+rank). Budgeted packer with MMR returning quote, unit id,
offsets. Every read logged (the consult log is the counterfactual miss-rate instrument).

What is embedded: dossiers, facts as one string (rendered triple plus quote), cells, abstracts.
Raw units are not embedded; quotes are the sentence-level sample of raw text. Brute-force scan
is the choice (one matrix multiply, fine to about 1M rows); ANN (usearch or hnswlib) only as a
deployment option behind the same port call; benchmark on brute force to avoid the recall confound.

Scope for a query comes from the seeds' sets, a per-session running scope, a declared scope
(prior, never a filter), and set abstracts as a router when nothing else resolves; scope boosts,
never excludes, with an unfiltered rerun when the filtered result is thin.

## Process architecture (step 3)

One long-lived engine process owns the SQLite file, the loaded embedder, search, and merge, on
localhost. The MCP server (FastMCP) and the hooks are thin clients with autostart. Reasons: SQLite
single writer; one choke point for consult logging; warm index; hooks stay fast. Justin: semantic
search is a necessity, so the embedder cannot live in a per-prompt hook process.

Embedder: default fastembed with bge-small-en-v1.5 (no torch); sentence-transformers mpnet as an
optional extra; model2vec if a hook ever needs semantic; reuse Ollama if present. The Anthropic
API has no embedding endpoint, so "whatever model the user has" cannot be assumed.

## Communities

Detected communities (Leiden or Louvain over the entity graph, or embed, cluster, LLM-name over
units) are deferred until a theme question needs them. The LLM names, adjudicates boundaries,
and folds abstracts; it never clusters from scratch. Recluster on condition, keep ids stable by
member overlap, never let a community be the only path to a document.

## Preprocessor rebuild and datasets

The existing splitting-and-gates notebook is corpus-specific regex per set. It is a source of
gate code and of fixtures with known answers, not the base for the general splitter, which is a
rewrite. Rebuild to take RAW text. AI proposes verbatim marker lines (body start, body end, headings,
topic changes), code cuts, the three gates verify, the split plan is stored per document.
Preamble metadata becomes quote-backed document facts. Deliverable is the next version of the
Kaggle units dataset. Loaders for the fall: Gutenberg text, plain text, LongMemEval JSON, arXiv
metadata (abstracts). DMR left out (Zep treats it as saturated). Personal archive stays
non-evidence, local smoke tests only. The roughly 100 paper abstracts (Dr. Fang's suggestion) and
the QA-with-source-handles demo over them are SPRING; check redistribution terms before publishing.

## Grounding in the paper

Property, not claim. 08-19 already killed quote validation as novelty (Governed Persistent Memory,
Eywa). Report: rejection rate per stage and tier (classify the Oz rejections by hand first:
fabrication vs paraphrase vs curly-quote normalization vs unlisted subject), audit pass rate,
drill-down capability, tier sensitivity. Normalize quotes and case before matching, store offsets
into the original. The gate proves the quote exists, not that it supports the fact; say so.

## Package format (change before the corpus run)

The package must carry: content-hash ids for document and units (not "chapter 1" labels); unit
text or ids resolvable in the units dataset; a dossier per major entity in the form the global
judge reads; mention spans on kept surface forms; per-document salience and unit count; the five
provenance fields; the verdict ledger and rejection counts. Re-deriving is real money (the judge
is two thirds of a book's cost), so fix the format on Oz 1 and 2, build the merge on those, then
batch the rest.

## Build order

Layer 0, then merge, then retrieval items 1 to 6, then benchmark. Then packer, consult log,
engine, MCP, hooks, package. Full ranking, MCP, and the installable package do not block the
benchmark (evaluators read the store directly).
