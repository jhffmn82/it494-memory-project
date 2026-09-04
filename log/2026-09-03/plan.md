# Plan: from the two notebooks to a testable pipeline

2026-09-03. Goal, in Justin's words: handle any document, work on SQLite, use a cached embedding
model, merge documents to a global level and cluster the entities, pipe it into RAG, and every
quote links back to a stored file. Soon enough to run the tests. Rules of record stay BUILD.md
and SCHEMA.md; anything here that changes them is marked PROPOSED.

## 1. What exists, and what is wrong with it

### The splitter (it494-narrative-corpora-splitting-and-gates)

Right: sha256-verified inputs; content-hash doc_id and unit_id; byte spans into the raw file;
three gates with the proportion clause; documents.jsonl and units.jsonl in the SCHEMA shape.

Deficient for the general case:

- Boundaries come from a hand-written strategy table per work (OZ_STRATEGY, HOLMES_STRATEGY,
  GREEK_STRATEGY: 60 or so entries naming a regex or a table-of-contents mode each). A new file
  needs a new entry. This is what "handle any document" forbids.
- Eleven works are "single", one unit for a whole play or anthology. The proportion gate cannot
  fire on one unit, so these are unsplit, not verified.
- Unit text keeps the heading line and Gutenberg noise inside the unit; nothing records what was
  stripped as boilerplate beyond the header and footer.
- No chat, email, markdown, or metadata loader exists. Only Gutenberg text.
- The raw files are not stored with the units. Spans point into files that live in a separate
  Kaggle dataset, so the chain from quote to bytes depends on both datasets staying aligned.

### The ingestion (it494-chapter-ingestion-oz-book-1, v6)

Right: three calls per unit with a shared prefix; quote gate on every fact and surface form;
nothing shared between units; bottom-up reconciliation with a written verdict ledger; predicate
consolidation with fork flags; document and unit nodes; per-entity and document abstracts; a
spending stop; cost by stage.

Deficient against SCHEMA.md and BUILD.md:

- Store is an in-memory dict dumped to store.json. No SQLite, no port, no FTS, no vectors.
- Units are keyed by label ("chapter 1") and the document by source_uri, not by the content-hash
  ids the splitter already minted. Facts therefore cannot resolve to a unit_id.
- The quote gate returns a boolean. No offsets are kept, so no drill-down and no stored audit.
  It does not normalize curly quotes or case, so some rejections are punctuation, not fabrication.
- No Mention record, no spans on surface forms. Resolution measurements cannot be computed later.
- Candidate generation is all-pairs over cheap signals (4,286 pairs for one book). At the global
  level this is quadratic in documents, and the judge was two thirds of the cost.
- Reconciliation is whole-document batch; nothing incremental, nothing persists across documents.
  The `different` set dies with the run.
- No embeddings anywhere.
- Salience is per unit; 70 of 141 majors were single-unit events. No document-level salience.
- Cells are generated only for named entities, so unnamed majors ("the house") get no thread.
- No valid_from, valid_to, rank, or tier on facts. No supersession, no collision detection.
- Predicates are consolidated per document; no global controlled list and no type table
  (SCHEMA rule 6 unenforced).
- No profile record for the matcher.
- Model calls are raw HTTP with JSON mode; no schema validation, no retry-with-error, no
  rejection log, no run log rows; embed() does not exist.
- Abstract fold has a 300-word cap and no name check against child content (BUILD's cheap
  fabrication check). No previous-unit summary as coreference context.
- No consistency check between unit summary and cells.
- No retrieval, no injection, no consult log.

### Missing entirely

The global merge; the store; search and rank; the engine, MCP server, and hooks; the package.

## 2. The plan, step by step

Each step names tools, the acceptance test, and a rough size. Sizes assume small modules Justin
reads, drafted with the assistant, not a dump.

### Step 0. Raw text layer and the general splitter

Build: the store's source side and a loader framework.

- Tables: raw_file (sha256, bytes or path, media type), document, unit, containment edges,
  external-content FTS5 over units. PROPOSED: raw bytes stored as a blob table keyed by sha256 so
  the store is self-contained; a corpus is megabytes. Spans on units index into those bytes, so a
  quote resolves to (file, byte range) with nothing outside the database.
- Loader interface: load(path) yields documents and units and nothing else. Loaders: Gutenberg
  text, plain text and markdown, Claude transcript JSONL, LongMemEval JSON, arXiv metadata.
- Boundary finding: AI proposes verbatim marker lines from a compressed view (short lines, first
  and last few hundred lines, table of contents), code locates them with the whitespace-forgiving
  matcher and cuts, the three gates verify, and the split plan is stored per document. On gate
  failure: retry on the strong tier once, then a heuristic fallback (headings by regex family, else
  fixed windows), and the document is flagged. Long units are sub-split the same way from
  paragraph openings.
- Tools: Python 3.11, sqlite3, FTS5 probe, hashlib, the existing gate code and the 69-document
  corpus as fixtures with known unit counts.
- Accept: every existing work reproduces its unit count without a per-work strategy entry, or is
  flagged with a reason; LongMemEval sessions and one local transcript pass the gates; the eleven
  "single" works either split or are explicitly recorded as one-unit by decision.
- Size: 10 to 12 hours.

### Step 1. Model interfaces and the per-document derive

Move the notebook into a module behind BUILD's two interfaces.

- embed(texts) and generate(prompt, schema) with model id, tokens, latency, and tier on every
  call; schema validation with one retry carrying the error; rejections logged with a reason
  category (not found, paraphrase, normalization, unlisted subject).
- Quote gate returns offsets; normalize NFKC, curly quotes, and case for matching; store offsets
  into the original unit text.
- Mentions with spans for every kept surface form. Cells for every above-threshold entity, named
  or not. Previous unit's summary passed as coreference context. Unit summary versus cells set
  check recorded.
- Package output: content-hash ids, unit ids, dossiers per major entity, mentions, per-document
  salience (named in the document abstract, then unit and fact counts), provenance fields, verdict
  ledger, rejection counts. Written as JSONL, the write-ahead log for the merge.
- Tools: openai client or httpx as today, pydantic for schemas, fastembed for the dossier
  embeddings the merge will need.
- Accept: Oz 1 re-derived from the new units with rejections classified by hand; every fact
  slices to its quote at its offsets; cost within 20 percent of v6.
- Size: 8 hours.

### Step 2. SQLite store and the global merge

- The seventeen-operation port over one SQLite file per corpus: document, unit, node, alias,
  mention, profile, fact with offsets and valid_from and valid_to and rank and tier, cell,
  abstract, and the logs (rejection, run, consult). sqlite-vec table with a header row (model,
  dim, built_at); mismatch rebuilds.
- Merge, per package, in manifest order: write documents and units first; embed dossiers;
  candidates by the rule in the 2026-09-03 log (major to major by nearest-k plus exact surface
  hits; exact hits inside the set nominate a judge; minor to minor never); judge in batches on
  the strong tier; disambiguators on both nodes when a primary name collides and the verdict is
  different; alias table with three row kinds; kept-apart pairs persisted; minor entities stay in
  the package; facts commit unit by unit with the collision check on functional predicates;
  predicate names mapped to the controlled list with the type table enforced; cells appended;
  abstracts refolded where children_hash changed, bounded per BUILD, names checked against
  children.
- Tools: sqlite3, sqlite-vec, fastembed, numpy; networkx only for the graph drawing.
- Accept: Oz 1 then Oz 2 merged from packages into an empty store; Tip and Ozma both states
  render; re-running the merge over the same packages mints nothing; the resolve() chain is
  followed on every read; the alias set (hand-labelled, one novel, built first) scores merge
  precision and recall.
- Size: 14 to 16 hours. This is the largest step and the one the resolution ablation replays.

### Step 3. Search and rank into RAG

- Query embedding once; seeds from dossiers and alias FTS; four channels (FTS5 over derived text,
  sqlite-vec nearest-k, one hop over facts, FTS5 over raw units); reciprocal rank fusion;
  budgeted packer with MMR emitting quote, unit id, offsets, and the raw-file reference; consult
  log row per query; scope from seeds and session, boosting not excluding.
- Injection arms for the benchmark: full system, no-context control, flat retrieval over units,
  and one ablation with cells off. Evaluators read the store directly and use the dataset's own
  scorer.
- Tools: sqlite-vec, numpy, the serving tier's tokenizer or tiktoken for budgets, GraphRAG-Bench
  scorers as shipped.
- Accept: each channel alone returns the known unit for a chosen fact; fusion ranks a
  three-channel item above a one-channel item; the packer never exceeds budget; GraphRAG-Bench
  runs end to end on one novel.
- Size: 10 hours.

### Step 4. Entity clustering

Deferred until a theme question or the wiki needs an abstract over a group nobody declared.
Leiden or Louvain over the entity graph (fact edges weighted by count plus co-mention), levels
kept, each community a set node with member edges and a folded abstract, ids kept stable by
member overlap between runs, reclustered on condition. Tools: networkx, or igraph with leidenalg.
Accept: the literature corpora recover their known groupings; on the local archive, agreement
with the hand-built era tree is reported. Size: 6 hours when it is needed.

### Step 5. Engine, MCP, hooks

One long-lived process on localhost owning the database, the embedder, search, and merge; MCP
shim with search, ingest, entity, and source tools; hook CLI for prompt-submit retrieval and
session-end ingestion; autostart. Tools: FastAPI and uvicorn or stdlib http.server, httpx, the
mcp package. Accept: two concurrent ingests do not lock or corrupt; the hook returns in under 200
milliseconds; the source tool returns the paragraph around any fact. Size: 8 to 10 hours. Not
needed for the benchmark.

### Step 6. Package

pyproject with a console script, init that probes FTS5, loads sqlite-vec, downloads the default
embedding model once, writes a config with tiers and no keys; pytest suite with the injected-
defect tests; README; build and pipx install; the outside install test. Size: 10 hours. Spring.

## 3. How a user feeds it documents

Every entry point ends in the same three calls, load then derive then merge, so the entry points
are thin and the user never names a format.

- **A path.** `memory ingest <file or folder>` from the command line, and the same as an MCP
  tool so the assistant can be told "ingest this". Folders recurse; files already in the store by
  sha256 are skipped and reported, so re-pointing at a folder is safe.
- **A watch folder.** The engine watches one directory the user drops things into. This is the
  desktop case: save a PDF or paste a transcript there and it is in the store by the next prompt.
- **Session transcripts.** The session-end hook hands the transcript path to ingest. The user
  does nothing.
- **A URL.** Fetch, store the bytes, and ingest. Later; the arXiv metadata loader is the first
  use.

What the loader does with any of those: sniff the format from the bytes and structure, never
from a flag (Gutenberg markers, JSONL with role fields, markdown headings, email headers, PDF
magic, else plain text); store the raw bytes under their sha256 at that moment, so the quote
chain holds from the first second; split with the marker-and-gates method; return a receipt the
user can read: documents found, units per document, gates passed or flagged with the reason,
boilerplate share, cost of the split call. A flagged document is stored as one unit and listed,
never dropped, so the user sees what needs a decision.

Formats by when they land: text, markdown, Gutenberg, transcript JSONL, LongMemEval JSON, arXiv
metadata in the fall. PDF (pdfplumber or pymupdf for extraction, with the extracted text stored
as a derived file beside the original bytes), docx (python-docx), HTML (trafilatura), and mbox
email in spring. Each is one loader; the receipt, the gates, and everything downstream are shared.

## 4. Order and the calendar

Steps 0, 1, 2, and 3 are the fall and they are sequential: the splitter feeds derive, derive
feeds the merge, the merge feeds search, and search feeds the benchmark. That is 42 to 46 hours
against the two open blocks in README.md. It fits only if nothing in steps 4 to 6 is started
before the GraphRAG-Bench number exists, and only if each step ships its acceptance test before
the next begins.

The two irreversible items come first: the package format (step 1), because re-deriving costs the
judge again, and the raw-file blob and offsets (step 0), because a quote that cannot reach bytes
today cannot be made to later without a re-ingest.
