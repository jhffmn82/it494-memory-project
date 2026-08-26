# Implementation: Ingest (adapters and the two-arm segmenter)

All code lives in `harness/ingest/`, written by hand; model traffic goes only through `generate(prompt, schema, tier)`.

## Modules

**documents.py** (source layer storage)

```python
def make_doc(corpus_id, kind, title, ordinal, text, meta) -> Document   # content-hash doc_id
def write_doc(store_dir, doc) -> Path        # verbatim text plus JSONL row; append-only
def read_doc(store_dir, doc_id) -> Document  # byte-identical round trip or raise
def span_text(doc, span) -> str              # the only sanctioned span dereference
def write_segments(store_dir, doc, boundaries, method, tier) -> list[Segment]  # Segment rows; tier null for texttiling
```

**adapt_chat.py** (markdown conversations from the mock)

```python
def parse_turns(text) -> list[Turn]          # regex turn boundaries; Turn = (speaker, char_span, ordinal)
def chat_documents(path, corpus_id) -> Iterator[Document]  # one conversation file, one Document; turns into meta
def turn_offsets(doc) -> list[int]           # legal boundary positions; segmenters cut only here
```

**adapt_book.py** (plain-text novel)

```python
def split_chapters(text) -> list[tuple[str, span]]   # chapter-title heuristic; whole-file fallback
def book_documents(path, corpus_id) -> Iterator[Document]  # one chapter, one Document, ordinal = chapter number
def sentence_offsets(doc) -> list[int]       # rule-based sentence ends; the book's legal boundaries
```

**tile.py** (deterministic arm; TextTiling implemented from Hearst 1997, not imported)

```python
def tokenize(doc) -> list[tuple[str, int]]            # (token, char_offset); offsets survive to snapping
def pseudo_sentences(tokens, w) -> list[Block]        # fixed-size token windows per the paper
def gap_scores(blocks, k) -> list[float]              # block cosine similarity at each gap
def depth_scores(scores) -> list[float]               # valley depth per the paper
def tile(doc, legal_offsets, w=20, k=10) -> list[Boundary]  # depth cutoff, snapped to nearest legal offset
```

**seg_model.py** (model arm)

```python
def build_prompt(doc, units) -> str          # numbered units, never raw char offsets
def segment_model(doc, tier) -> list[Boundary] | Rejection  # generate() against SEGMENT_SCHEMA, then validate_indexes
def validate_indexes(result, n_units) -> list[str]   # empty list means clean; messages feed the retry
```

**seg_eval.py** (agreement instruments)

```python
def pk(ref, hyp, n_units, k=None) -> float   # Beeferman et al.; k defaults to half mean segment length
def windowdiff(ref, hyp, n_units, k) -> float        # Pevzner and Hearst
def load_labels(path, legal) -> dict[doc_id, list[int]]  # the 20-doc hand set; illegal positions reject
def compare_arms(store_dir, labels) -> Report        # per-arm Pk/WindowDiff plus the disagreement sample
```

## Data touched

Reads nothing upstream. Writes Document rows `{doc_id, corpus_id, kind, title, ordinal, meta}` with verbatim text (append-only) and Segment rows `{seg_id, doc_id, span, ordinal, boundary_method, tier}`.

Three gaps against `10_data_model.md`: Segment cannot store the model arm's one-line topic label per boundary (add an optional `label` field the filing call consumes); Document has no home for turns (park speaker, span, ordinal under `meta.turns`); `tier` is meaningless for the deterministic arm (write null).

## Contracts

A `Boundary` is always a character offset into the stored text; the model reports unit indexes, since models miscount characters, and `segment_model` converts validated indexes through the adapter's unit table.

`SEGMENT_SCHEMA` sketch:

```json
{"type": "object",
 "properties": {"boundaries": {"type": "array", "items": {
   "type": "object",
   "properties": {"after_unit": {"type": "integer", "minimum": 0},
                  "label": {"type": "string", "minLength": 1, "maxLength": 80}},
   "required": ["after_unit", "label"]}}},
 "required": ["boundaries"]}
```

`validate_indexes` rejects beyond the schema: indexes not strictly increasing; any index outside `[0, n_units - 2]`; zero boundaries on a document over 30 units; more than one boundary per 3 units. One retry with the validation messages appended, then a Rejection record (stage `segment`, contract version, tier, error). A rejected document falls back to the deterministic arm, recorded as `boundary_method: texttiling`.

## Build sequence

Steps 1-6 need no model access; 7 and 8 open once `generate` passes its smoke test and SEGMENT_SCHEMA freezes (Phase 1.5).

1. `documents.py`: dataclasses, hash ids, write/read. Test: byte-identical round trip; re-ingest yields identical ids.
2. `adapt_book.py` on the novel. Test: chapter count matches a hand count; property test: emitted spans dereference to identical source text.
3. `adapt_chat.py` on three mock conversations. Test: turn counts against hand counts; same span property test.
4. `tile.py` from the paper, about a hundred lines. Test: a fixture with three planted topic shifts recovers all three within one legal offset; runs are deterministic; `write_segments` output round-trips.
5. `seg_eval.py`. Test: Pk and WindowDiff reproduce hand-computed worked examples from the defining papers.
6. Hand-label the 20-document boundary set, rule written first per the agreement reference; budget three to five hours. The set may open at ten documents (five chat, five book) and grow to twenty before step 8. Test: every position is a legal offset; `load_labels` accepts all.
7. `seg_model.py` against the frozen contract. Test: canned malformed outputs (out of range, non-monotonic, over-segmented) all reject; then a live smoke, ten documents per tier, rejection rate logged.
8. `compare_arms` over the labeled set, both arms, all tiers. Test: the comparison note, disagreements sampled and read.

## Risks

TextTiling targets expository prose in fixed token windows; short, vocabulary-sparse chat turns can degenerate the cosine blocks. Parameter work is expected, and a poor chat-side Pk is a finding, not a failure. Offset bookkeeping breaks silently: any normalization (encoding, BOM, newline collapse) between parse and store voids the span invariant; spans are computed against exactly the stored bytes (property tests, steps 2 and 3). Hand-labeling runs long; without the written rule the Pk numbers anchor to nothing.

## Done means

Both adapters pass the span round-trip and count checks. `tile.py` is deterministic and paper-faithful. The 20-document labeled set exists with its labeling rule. Logged per arm and tier: Pk and WindowDiff over the labeled set, and the model-arm rejection rate (ten calls per tier minimum). Phase 2 exits with segments on disk for three known transcripts and one book chapter, plus the disagreement note on where the arms differ; then the distiller opens.
