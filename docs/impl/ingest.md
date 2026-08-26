# Implementation: Ingest (adapters and the two-arm segmenter)

Prepared by the assistant.

Everything below lives in `harness/ingest/`. All model traffic goes through `generate(prompt, schema, tier)`; nothing here calls an API directly. You write every line; the AI may draft, you rewrite and log it.

## Modules

**documents.py** (source layer objects and storage)

```python
def make_doc(corpus_id, kind, title, ordinal, text, meta) -> Document   # content-hash doc_id; same input, same id
def write_doc(store_dir, doc) -> Path        # verbatim text plus JSONL row; append-only, never edits
def read_doc(store_dir, doc_id) -> Document  # byte-identical round trip or raise
def span_text(doc, span) -> str              # the only sanctioned way to dereference a segment span
def write_segments(store_dir, doc, boundaries, method, tier) -> list[Segment]  # boundaries to Segment rows; tier is null for texttiling
```

**adapt_chat.py** (the mock's markdown conversations)

```python
def parse_turns(text) -> list[Turn]          # regex turn boundaries; Turn = (speaker, char_span, ordinal)
def chat_documents(path, corpus_id) -> Iterator[Document]  # one conversation file, one Document; turns into meta
def turn_offsets(doc) -> list[int]           # legal boundary positions; the segmenters may cut only here
```

**adapt_book.py** (plain-text novel)

```python
def split_chapters(text) -> list[tuple[str, span]]   # chapter title heuristic; falls back to whole-file
def book_documents(path, corpus_id) -> Iterator[Document]  # one chapter, one Document, ordinal = chapter number
def sentence_offsets(doc) -> list[int]       # rule-based sentence ends; legal boundaries for the book case
```

**tile.py** (deterministic arm, TextTiling implemented from Hearst 1997, not imported)

```python
def tokenize(doc) -> list[tuple[str, int]]            # (token, char_offset); offsets must survive to the snap step
def pseudo_sentences(tokens, w) -> list[Block]        # fixed-size token windows per the paper
def gap_scores(blocks, k) -> list[float]              # block cosine similarity at each gap
def depth_scores(scores) -> list[float]               # valley depth per the paper's formulation
def tile(doc, legal_offsets, w=20, k=10) -> list[Boundary]  # depth cutoff, snapped to nearest legal offset
```

**seg_model.py** (model arm)

```python
def build_prompt(doc, units) -> str          # numbered turns or sentences with indexes; never raw char offsets
def segment_model(doc, tier) -> list[Boundary] | Rejection  # generate() against SEGMENT_SCHEMA, then validate_indexes
def validate_indexes(result, n_units) -> list[str]   # empty list means clean; messages feed the retry
```

**seg_eval.py** (agreement instruments)

```python
def pk(ref, hyp, n_units, k=None) -> float   # Beeferman et al.; boundary index lists need the unit count; k defaults to half mean segment length
def windowdiff(ref, hyp, n_units, k) -> float        # Pevzner and Hearst
def load_labels(path, legal) -> dict[doc_id, list[int]]  # the 20-doc hand set; legal maps doc_id to legal offsets, positions outside it reject
def compare_arms(store_dir, labels) -> Report        # per-arm Pk/WindowDiff plus the disagreement sample
```

## Data touched

Reads nothing upstream; this is the pipeline's mouth. Writes **Document** rows `{doc_id, corpus_id, kind, title, ordinal, meta}` with verbatim text (the write-ahead layer; never edited after write) and **Segment** rows `{seg_id, doc_id, span, ordinal, boundary_method, tier}`.

Three gaps in the schema as written in `10_data_model.md`. First, the model arm returns a one-line topic label per boundary and Segment has no field for it; the filing call later would gladly consume it. Proposal: add optional `label` to Segment rather than discarding paid-for output. Second, Document has no structured home for turns (speaker, span, ordinal); park them under `meta.turns` now and note it for a schema revision. Third, `tier` on Segment has no meaning for the deterministic arm; write null there. Flag all three in the data-model doc when this component lands.

## Contracts

Design decision stated once: the model reports **unit indexes, not character offsets**, because models miscount characters. Adapters own the deterministic index-to-span conversion. A `Boundary`, everywhere in this component, is a character offset into the stored document text; `segment_model` converts validated unit indexes to offsets through the adapter's unit table, so the model never sees or emits an offset.

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

Rejection criteria beyond the schema, enforced by `validate_indexes`: indexes not strictly increasing; any index outside `[0, n_units - 2]` (a boundary after the final unit cuts nothing); zero boundaries on a document over 30 units; more than one boundary per 3 units (over-segmentation). Retry rule is the standing one from the build plan: one retry with the validation messages appended to the prompt, then a Rejection record with stage `segment`, contract version, tier, and error. A rejected document still segments: the deterministic arm is the fallback, recorded honestly as `boundary_method: texttiling`.

## Build sequence

Steps 1 through 6 need no model access. Steps 7 and 8 open only when the `generate` interfaces have passed their own smoke test and SEGMENT_SCHEMA is frozen (Phase 1.5); do not let API setup block the deterministic work.

1. `documents.py`: dataclasses, hash ids, write/read. Test: byte-identical round trip; re-ingest yields identical ids.
2. `adapt_book.py` on one real novel file. Test: chapter count matches a hand count; property test that every emitted span dereferences to identical source text.
3. `adapt_chat.py` on three mock conversation files. Test: turn counts against hand counts on those files; same span property test.
4. `tile.py` from the paper, about a hundred lines. Test: a fixture document with three planted topic shifts recovers all three within one legal offset; determinism (two runs, identical boundaries); `write_segments` on the fixture output round-trips through the store.
5. `seg_eval.py` metrics. Test: Pk and WindowDiff reproduce worked examples computed by hand from the defining papers.
6. Hand-label the 20-document boundary set, with the labeling rule written down first (the agreement reference governs how). Budget three to five hours of clock time; the set may open at ten documents (five chat, five book) and grow to twenty before step 8 runs. Test: `load_labels` accepts every labeled document and every position is a legal offset.
7. `seg_model.py` against the frozen contract. Test: canned malformed outputs (out of range, non-monotonic, over-segmented) all reject; then a live smoke run, ten documents per tier across transcripts and book chapters, rejection rate logged.
8. `compare_arms` over the labeled set, both arms, all tiers. Test: the comparison note itself, disagreements sampled and read.

## Sanity risks

TextTiling was built for expository prose in fixed token windows; short, vocabulary-sparse chat turns can make the cosine blocks degenerate, so expect parameter work and possibly a poor chat-side Pk. That is a finding for the note, not a failure of the build. Second, offset bookkeeping breaks silently: any normalization (encoding, BOM, newline collapse) between parse and store voids the span invariant, so compute spans against exactly the stored bytes and let the property test in steps 2 and 3 stand guard. Third, hand-labeling 20 documents runs longer than it reads; boundary ambiguity is real, and without the written labeling rule the Pk numbers anchor to nothing.

## Done means

Both adapters pass the span round-trip property test and the count checks on known files. `tile.py` is deterministic and paper-faithful. The 20-document labeled set exists with its labeling rule. Per arm and per tier: Pk and WindowDiff over the labeled set, logged; model-arm rejection rate per tier from the smoke run (ten calls per tier minimum), logged. The Phase 2 exit artifact: segments on disk for three known transcripts and one book chapter, plus the disagreement note explaining where the arms differ and why. When those numbers are in the log, the distiller may open.

## Sanity check

Challenged every signature, the schema reads, the rejection criteria, and the sequence against `10_data_model.md` and the build plan. Held: the index-not-offset contract, the retry-then-fallback rule, the two flagged schema gaps, the fixture and property tests. Fixed six defects. Nothing wrote Segment rows despite the exit artifact claiming segments on disk; added `write_segments` and a round-trip test in step 4. `pk`, `windowdiff`, and `load_labels` could not compute or enforce as typed; they now take `n_units` and the legal-offset map. `tile` lost character offsets at tokenization; `tokenize` now carries them. The index range allowed a cut after the final unit; now `n_units - 2`. The smoke run (four calls) undershot the ten-call done bar; now ten documents per tier. Hand-labeling got an hour budget and an opening valve, and steps 7 and 8 got their interface entry condition.
