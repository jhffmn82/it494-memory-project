# Working log: 2026-09-04

PC session. Picked up the laptop's 09-03 notes (`log/2026-09-03/`), walked through the
merge after document ingestion, and planned the general extractor. Decisions below are
Justin's; open items are marked.

## Decisions

- **Community grouping is out.** Not deferred, removed. It pays only for thematic questions
  over a group nobody declared, which nothing this project asks. Declared groupings (a
  series, a thread) exist only for supersession ordering and disambiguation scope, and
  nothing is clustered. SCHEMA.md now says so.
- **Document-level salience is reassessed at the end of ingestion**, once the document
  abstract exists: named in the abstract means major; unit count, then fact count, break
  ties. Only document-majors carry dossiers into the merge. Unit-level salience still
  decides who gets a cell. SCHEMA.md updated.
- **Abstracts refold whenever their children change** (confirmed; the hash rule in BUILD).
- **Documents are entities** (confirmed): a node with unit summaries as cells, an abstract,
  `has_unit`, `produced_by`, and `appears_in` edges. Documents never merge with each other.
  SCHEMA.md updated.
- **The document holds its text, once; units are ranges.** The source is decoded to a string
  at load and stored on the document record with the sha256 of the original bytes. A unit is
  `(doc_id, position, label, start, end)`. Every offset in the store, on units, mentions, and
  fact quotes, is a document offset in that one coordinate system. In SQLite this is a text
  column on the document table and a range table for units; FTS5 reads through the offsets;
  `get_source` is one slice; the stored quote audit is one SQL statement. SCHEMA.md updated.
- **Next build step: the general extractor** (plan.md Step 0), simplest code, no per-corpus
  regex. Contract `load(path) -> documents, units`. Two paths chosen by sniffing the bytes:
  structured inputs (LongMemEval JSON, arXiv abstracts, transcript JSONL) become units with no
  model call; unstructured text gets one Luna call per document that proposes verbatim marker
  lines from a compressed view (short lines numbered, plus the first and last two hundred
  lines), code cuts, the three gates verify, retry once on Terra, then fixed windows and a
  flag. Outputs: `documents.jsonl` (with text), `units.jsonl` (ranges), `split_plans.jsonl`,
  a receipt. Author and source class are captured at load. BUILD.md updated.
- **All raw text for the project goes into one Kaggle dataset** (`oz/`, `holmes/`, `greek/`,
  `chinese/`, `graphrag-bench/`, `longmemeval/`, `arxiv/`, each with a manifest regenerated to
  one schema), and the extractor runs over all of it; the output is the next units dataset.
  Test set for the ingestor afterward, a sampling of every source type: three Oz books, two
  Greek works, two Holmes collections, a few GraphRAG-Bench contexts, a handful of LongMemEval
  sessions, and twenty or so abstracts (the abstract sample moves into the fall test set so
  the abstract ingestor is locked down early; the abstract demo itself stays spring).
- **NarrativeQA stays the 12-work, 345-question subset.** NarrativeQA holds 1,572 works of its
  own (Gutenberg books and film scripts); we do not pull them. The gold joins to our raw
  files by Gutenberg id; NarrativeQA's own copies were different fetches of the same ids
  (sizes differ), so edition alignment is checked when the arm is scored.
- **Order of work from here:** (1) the raw extractor solid against every source in the
  dataset; (2) the document ingestor against a sampling of each source type, with the
  abstract path as a first-class case; (3) the global merge. Each gets its own chat with a
  brief from this log.

## The merge, as walked through (no change to the 09-03 rules)

Raw layer first (document and units by content hash, idempotent); resolve the author to a
node before any fact; nominate candidates for document-majors only (nearest-k by dossier
embedding plus exact surface hits, exact hits nominate a judge and never auto-union); judge
on the strong tier with dossiers recorded per verdict, disambiguators on a judged-different
name collision, kept-apart pairs persisted, `different` never vetoes a later verdict on a
larger dossier; commit facts unit by unit in position order with the voice-lineage collision
rule on functional predicates; cells appended; abstracts refolded where the children hash
changed; vectors and alias FTS refreshed; package marked applied.

## Inventory of what Step 0 must cover

The first draft of the Step 0 brief was checked against the repository, the disk, and Kaggle
by five sweeps; the findings are in [inventory.md](inventory.md). It had eleven statements
wrong (among them: NarrativeQA's twelfth work is in `chinese/`; seventeen works were left
single, not eleven; nine Archive.org scans have no Gutenberg markers or Author line; the
GraphRAG-Bench contexts are one line each with markers stripped and nine lack a chapter
token; the manifests have no license field and `cached` for a URL; LongMemEval is three
files with no per-turn timestamps; the abstracts were ruled spring on 09-03) and left out
twenty things, from the `chinese/` folder and the Thebaid exclusion mechanism to the
ingestion notebook's dependence on unit text. The brief was rewritten against it; the twelve
decisions it raises are Justin's and are listed at the end of the inventory.

## Open

- Chat unit granularity in the extractor: a LongMemEval session as one unit, or turn groups cut
  by length as the desktop case will need.
- Sub-splitting: cap unit length and sub-split at paragraph openings, or leave long units whole.
- Where the extractor code lives: Kaggle notebook first with the repo holding the copy, or a
  `scripts/extract.py` module the notebook imports.
- Cells for entities promoted to document-major after being unit-minor: accept the missing
  cells, or one extra cells call per promoted entity over the units it lacked.
- From 09-03, still to rule: the set node, the vector table inside SQLite instead of a
  sidecar, raw bytes as a blob table.

## Still not done

- Fang endorsement email (draft in the 09-02 session; add the repository link).
- Say the names to Fang: Palimpsest (paper, architecture), FactLedger (tool).
- Repository visibility: still private unless changed in the GitHub UI.
