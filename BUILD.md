# Build rules

The records themselves are defined in SCHEMA.md.

## Dataset code lives only at the seams

Every dataset enters through a loader that emits documents and units and
nothing else, and is scored by an evaluator that reads the finished store and
computes one metric. A loader must fill `author` and `source_class`, may fill
`occurred_at` and `label`, may not add fields, and the system may not branch
on which loader ran. The format is sniffed from the bytes, never taken from a
flag. Structured inputs (a transcript with turns, a metadata record per
abstract) become units directly with no model call. Unstructured text is
split by one model call per document that proposes verbatim marker lines
(body start, body end, headings) from a compressed view of the text; code
locates the markers and cuts, the three gates verify, and the split plan is
stored per document so a re-run is a replay. There are no per-work or
per-corpus rules in the splitter; a document the gates reject is stored as
one unit and flagged, never dropped. Gold files and
question sets keep whatever shape they shipped in, because each evaluator is
dataset-specific by definition. Adding a dataset is one loader plus one
evaluator; anything that cannot be expressed that way means the schema is
missing a field.

Ingest runs in corpus order. A book loaded all at once is static and tests
nothing temporal; read in sequence, the store's state after chunk 10
differs from chunk 20, which is what supersession is for. Every mention gets
recorded with its span at ingest, because resolution measurements read
mentions and spans cannot be reconstructed after merging.

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
zero accepted records. Entity merges are read-time redirection: the losing
entity is marked merged-into and never rewritten. Every fact read passes
through one resolve() that follows merged-into chains with a cycle guard,
because chains and cycles both occur and a read that skips resolve() misses
merged entities silently. After a merge, collision detection re-runs under the
merged identity: conflicts supersede, the rest stay.

Resolution scores name similarity, co-occurrence, and profile compatibility
together, and the guards in `docs/entity-resolution.md` are binding: profile
mismatch lowers a score and never blocks a merge, inherited facts never count
as independent corroboration, every merge records its evidence and stays
revocable, cluster size is capped, and the merge rate per chunk is watched,
because a spike is a black hole forming.

Summaries rebuild only when the hash of their inputs changes, and staleness
markers are stripped before hashing so stamping a summary cannot cascade. A
rebuild reads the ordered child texts, never raw source, and is bounded: at
most half the combined child word count, capped at 400 words, and every name
it emits must appear in the child content by case-insensitive substring, which
is the cheap fabrication check. A rejected rebuild is never stamped; the node
stays stale and retries next pass. Supersession applies only to a small list
of functional predicates, and that list is maintained by hand.

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
