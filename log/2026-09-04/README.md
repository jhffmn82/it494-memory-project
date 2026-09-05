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

## Rulings on the Step 0 inventory (evening)

Justin ruled all twelve, one at a time; the rulings are recorded in full at the end of
[inventory.md](inventory.md). The governing rule: the extractor sees raw files and nothing
else. In short: chinese/ out (NarrativeQA 11 works, 319 questions; OCR and translation
controls leave the slate); the Thebaid file removed; LongMemEval `_s` unpacked to one file per
session and a session is a document; units everywhere are size-bounded runs of natural pieces
cut at piece boundaries; GraphRAG-Bench unpacked to 20 text files; papers as raw PDFs in a
private dataset with the PDF loader moved to fall; public dataset MIT; manifests are packaging;
source class follows the sniffed format; Kaggle now, desktop tool later; old unit counts are a
reference and Justin's review becomes the fixture; LongMemEval is fall. Question sets are not
part of Step 0.

Two rulings from the extractor chat's first findings, later in the evening: (a) a reused
LongMemEval session keeps every date it was assigned, as a `dates` list in first-seen order;
one date fills the document's `occurred_at`, several leave it null and flag the document
ambiguous. (b) Units carry a time range, `occurred_at` to `occurred_until`, filled only when
the file carries times; a unit never spans a day change; a fact's time is the date its text
states, else its unit's, else its document's, else null. Facts were always meant to have
dates; novels hid that, chats bring it back. SCHEMA.md and BUILD.md updated.

A design review Justin brought in late in the evening raised six points; five held against the
files and one partly. Rulings: (A) voice lives on the piece. The split plan is the piece table
(kind, range, unit, `author` when the file names a speaker, time when it carries one); a fact's
voice at read time is its piece's author, else the document's; one word, `author`, at every
level, no `speaker`. Turn-as-unit was considered and declined: 246,930 units and 740,000 derive
calls against 19,000 and 57,000, and the exchange context lost. (B) Minor entities stay mentions
inside their document, `node_id` null, never merged: a minor is minor because the text gave too
little to disambiguate it, and hundreds per work make a global merge on no evidence not worth
its cost. (C) Two instruments added: the long-tail count of surfaces recurring across N
documents with no node, and gold-pair candidate recall before merge precision and recall.
(D) plan.md corrected: the resolution ablation is the benchmark's fourth arm, and the combined
store estimate is superseded by the 09-04 counts.

The living docs were then corrected to the rulings in one commit (README.md, SCHEMA.md,
BUILD.md, RESEARCH.md, docs/proposal.md, docs/evaluation-corpus.md, data/raw/SOURCES.md,
USAGE.md, WANTLIST.md): 87 verified edits from a sweep of every living markdown file, each
checked against the rulings by a second reader. Dated logs and the paper one-pagers were
left as historical record, except one note on the OCR control's status.

## Open

- The unit cap and the tail floor (words), proposed by the extractor chat, ruled by Justin.
- The compressed view for a document that is one line, or nearly all short lines: built from
  substrings rather than lines; the exact rule is the extractor chat's to propose.
- Cells for entities promoted to document-major after being unit-minor: accept the missing
  cells, or one extra cells call per promoted entity over the units it lacked.
- From 09-03, still to rule: the set node, the vector table inside SQLite instead of a
  sidecar, raw bytes as a blob table.

## Still not done

- Fang endorsement email (draft in the 09-02 session; add the repository link).
- Say the names to Fang: Palimpsest (paper, architecture), FactLedger (tool).
- Repository visibility: still private unless changed in the GitHub UI.
