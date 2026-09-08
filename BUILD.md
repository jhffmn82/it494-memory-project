# Build rules

The records themselves are defined in SCHEMA.md.

## Dataset code lives only at the seams

Every dataset enters through a loader that emits documents and units and
nothing else, and is scored by an evaluator that reads the finished store and
computes one metric. A loader must fill `author` (quote-backed from the file bytes, or flagged unknown) and `source_class` (from the sniffed format), may fill
`occurred_at` on the document, `occurred_at` and `occurred_until` on units when
the file carries times, and `label`, may not add fields, and the system may not branch
on which loader ran. The loader sees the file bytes and nothing else: the format is sniffed from them, never taken from a flag, and no manifest, metadata record, or question set is an input. Structured inputs (a chat session with turns) become pieces with no model call, the role the author. Unstructured text is split by one model call per document that numbers the document's lines; the model points at each boundary by line number and copies the line, code verifies the number against the copy and cuts (`docs/extractor.md`). The three gates verify, and the split plan is stored as the piece table (one row per piece: kind, range, unit, author when the file names a speaker, time when it carries one) so a re-run is a replay and a fact's voice is a lookup. A unit is a size-bounded run of the document's natural pieces (chapters, turns, sections), cut only at a piece boundary, never a turn alone, never across a day change when the file carries times, with a short tail merged into the unit before it. There are no per-work or
per-corpus rules in the splitter; a document the gates reject is stored as
one unit and flagged, never dropped. Gold files and
question sets keep whatever shape they shipped in, because each evaluator is
dataset-specific by definition. Adding a dataset is one fetch or unpack script that lays raw files and their manifest on disk, one evaluator, and a loader only when the sniffed format is new; anything that cannot be expressed that way means the schema is
missing a field.

Ingest runs in corpus order. A book loaded all at once is static and tests
nothing temporal; read in sequence, the store's state after chunk 10
differs from chunk 20, which is what supersession is for.

## Two interfaces, every failure measured

Every model touch goes through two interfaces, embed(texts) and
generate(prompt, schema), and every call records its model id, tokens, and
latency. Schema-invalid output gets one retry with the validation error
appended, then a logged rejection. Semantic failure is different: a quote that
is not in its unit or an alias pointing at an unknown entity is rejected with
no retry, because that is bad data, not bad formatting, and the two get
measured separately. Fields the model could lie about are never model-supplied:
the unit ordinal behind every fact date and the id lists behind every merge are
set by code. On local tiers, use grammar-constrained decoding so malformed
output is impossible rather than counted.

Cross-unit coreference gets the previous unit's summary as context. A pronoun
that still does not resolve stays recorded as unresolved.
A stage that completes with zero yield and zero rejections writes an explicit
empty completion record, so a resumed run can tell done-but-empty from failed.

## Re-runs mint nothing

Re-running any stage over unchanged input mints zero new entities and rewrites
zero accepted records. Identity is a tree, not a merge: a child entity belongs
to one document and an up-edge attaches it to a parent that holds only derived
fields. Re-deciding identity re-points an edge; nothing is rewritten or unioned,
so there is no merged-into chain to resolve and no un-merge problem.

Within a document, entity pairs are nominated by a shared surface form, a shared
name word, or a fact saying one is the other, and a judge rules
same/different/unsure on their dossiers; every verdict and every scored pair is
logged. The guards in `docs/entity-resolution.md` are binding: a different
verdict never vetoes a later one reached on more evidence, every decision records
its evidence and stays revocable, cluster size is capped, and the pairing rate is
watched, because a spike is a black hole forming. Which resolution signals the
paper ablates is the open item there.

Summaries rebuild only when the hash of their inputs changes, and staleness
markers are stripped before hashing so stamping a summary cannot cascade. A
rebuild reads the ordered child texts, never raw source, and is bounded to 400
words; the fold is a summary of the children and stands as written. Supersession
applies only to a small list of functional predicates, maintained by hand.

## Exact match, whole items, byte-for-byte replay

Alias lookup is exact match, then case-folded match; fuzzy matching stays
out of the query path. Context is
assembled greedily in rank order, whole items only, nothing truncated, with the
strongest material at the edges of the window. Budgets use the serving tier's
own tokenizer plus a fifteen percent margin, because tiers tokenize
differently. Every record type has one deterministic render function shared by
serving and replay, so the context of any past run rebuilds byte for byte from
its log line. Routing and admission decisions are logged, so a retrieval miss
divides into "never a candidate" and "cut by the budget", which have different
fixes.

Embeddings live in a rebuildable sidecar keyed by record id and model id. The
store never depends on them, and the sidecar's row map is verified against ids
on load, because a partial write there fails silently.

The embedder is small, local, cached once, and model-agnostic behind `embed()`,
because the serving side must run offline on the user's own machine and
Anthropic has no embedding endpoint. Default: `bge-small-en-v1.5` through
fastembed, 384 dimensions, ONNX with no torch, the model fetched once (~130 MB)
and then offline on CPU. `model2vec` (static, ~256 dimensions, no encoder to
load) is the lighter option for a hot path; sentence-transformers/mpnet is an
optional heavier one; reuse Ollama if the user already runs it. 384 dimensions
is deliberate: brute-force exact cosine at personal scale is one matrix multiply
and a wider vector buys nothing, which is why retrieval is benchmarked on brute
force rather than an ANN index (the ANN option sits behind the same port call,
so the recall confound stays out of the measurement). The sidecar carries a
header (model, dimension, built_at); a mismatch on load rebuilds rather than
serves stale vectors. The ingestor stores no vector; only the dossier text it
would embed.

## The stop comes before the run

Set a hard per-run spending stop and check it against the run log before
continuing. Iterate on the cheapest tier that holds each stage and
report at three tiers; the spread between tiers is a finding, and running
everything on the best model erases it. Batch each chunk's cell calls into one
from the start; re-sending the chunk text per entity is 2.3x on total input
and 5x on the part that dominates.

## Three checks before the wiki ships

Static pages, generated by one command, as a read-only projection of the store.
It ships only when three checks pass: every rendered quote string-matches its
source text, a link checker finds zero dead links, and the Tip and Ozma page
renders both states of the supersession. Check for FTS5 at startup and fall
back to a plain scorer, because not every SQLite build has it.
