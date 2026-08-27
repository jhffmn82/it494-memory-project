> **SUPERSEDED 2026-08-27** by docs/18 (ingestion) and docs/19 (retrieval and delivery).
> Kept for the record; do not build from it. Index: `docs/README_SESSION_2026-08-27.md`.

# Architecture

One dataflow, organized by the five steps. Everything is Python; the model is the only black box, reached through two interfaces: `embed(texts)` and `generate(prompt, schema, tier)`. Every model call records its tier.

## The flow

```
                          CORPUS
            chat transcripts        documents / books
                  |                        |
                  v                        v
             +--------------------------------+
   INGEST    |  adapters -> document stream   |
             |  segmenter -> segments         |
             +--------------------------------+
                  |
                  v            (each segment, one pass)
             +--------------------------------+
   ORGANIZE  |  distiller (model calls):      |
             |    summary  -> LEAF            |
             |    mentions -> ENTITY layer    |
             |    tokens   -> FACT rows       |
             +--------------------------------+
                  |
                  v
             +--------------------------------+
    STORE    |  tree/   leaves + rollups      |
             |  entities/  pages + aliases    |
             |  facts/  dated rows + ledger   |
             +--------------------------------+
               ^      |                |
               |      v                v
             +----------+      +---------------+
   MAINTAIN  | fold,    |      |  RETRIEVE     |
             | stale-   |      |  route tree,  |
             | ness,    |      |  entity/fact  |
             | supersede|      |  lookup, lex  |
             +----------+      +---------------+
                                       |
                                       v
             +--------------------------------+
    INJECT   |  budget accountant: compose    |
             |  context (3 strategies)        |
             +--------------------------------+
                       |
                       v
             answering model  ->  answer + receipts
                       |
                       v
             +--------------------------------+
   EVALUATE  |  runner + judge (different     |
             |  tier than any writer)         |
             |  -> run rows, bands, tables    |
             +--------------------------------+
```

## The five steps as components

**Ingest.** Adapters normalize each corpus type into one document stream: a chat transcript becomes ordered turns with speakers and timestamps; a book becomes ordered passages with chapter positions. The segmenter cuts the stream into topic-coherent segments via a model call against the segment contract, with TextTiling as the deterministic comparison arm. The segment is the atom everything downstream shares.

**Organize.** The distiller makes three schema-validated model calls per segment. The summary pass writes the leaf and files it in the two-level tree. The mention pass extracts entity references, resolves pronouns and aliases against the alias ledger, and updates entity pages (indexes of quotes and pointers, never copies). The fact pass emits dated subject-predicate-object rows with source pointers; the merge ledger records which raw tokens merged into which attribute.

**Retrieve.** Three lookups, composed per question shape: tree routing (read the index, read the rollup, descend only if needed), entity and fact lookup for "everything about X" and point questions, and lexical search as the floor. Deliberately thin.

**Inject.** The budget accountant assembles the context window under a hard token budget, in one of three strategies: top-k chunks (the naive-RAG control), tree-routed summaries, or summaries plus fact rows. Ordering follows the injection literature; every composition is logged as a run row.

**Maintain.** A pass over the store, not per query: content-hash staleness marks nodes whose children changed, refold rewrites only those rollups, and supersession marks fact rows whose subject and functional predicate collide with a later row; `same_as` rows execute as entity merges, resolved as read-time redirects rather than rewritten rows. Nothing is deleted; the superseding is itself stored.

**The evaluation spine** sits beside the pipeline, not after it: a question runner, an LLM judge on a different model tier than any writer, and the instruments (question bands, counterfactual miss rate, stale-serve rate) reading the same run rows everything else writes.

## Two properties the flow enforces

Provenance is continuous: answer to injected context, context to leaves and fact rows, rows to segments, segments to source documents. No stage grades itself: every acceptance check (summary faithfulness, fact support, answer scoring) runs on a different model tier than the writer it checks.
