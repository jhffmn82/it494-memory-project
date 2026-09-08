# The pipeline, and the tentative paper outline

Justin Hoffman. IT 494. 2026-09-08.

## The extractor (Step 0): a raw file becomes a split plan

Input: any raw file, a Gutenberg text, a chat log, a PDF. The format is sniffed from the bytes;
there are no per-file rules. The file is shown to a model as its own numbered lines; the model
points at each boundary by line number and copies the line, and code verifies the number against
the copy before cutting. Three gates check the result: the pieces cover the whole document with no
gaps, no unit mixes kinds (body vs references vs appendix), and every boundary's text is real.
Output, one row per line of JSONL: documents (the text, once), units (character ranges), pieces
(the split plan, with a chat turn's speaker). Whole corpus in one pass: 19,436 documents for $7.72.
Published as the Step 0 dataset.

## The ingestor (Step 1): a document becomes a knowledge package

Input: one document's text, units, and pieces. For each unit: the entities in it (kept only if a
name is found in the text), the facts about them (kept only if a verbatim quote is located), and a
short summary plus a narrative cell per major entity. The document's unit-local entities are then
reconciled into document entities, with a judge deciding which are the same, and each major entity's
facts are consolidated, with contradictions recorded rather than erased. Output: one package per
document (entities, quote-backed facts at character offsets, cells, an abstract per entity), plus a
full cost log. About four model calls for a short chat session, more for a book.

## The store (Steps 2 and 3): a merge-free identity tree, in SQLite

Across documents, entities are not merged. Each document keeps its own version of an entity, and an
edge attaches it to a parent that holds only a derived name and summary, nothing asserted.
Re-deciding identity re-points an edge; nothing is rewritten. This makes three normally-hard things
easy: adding a document is append-only, deleting one is a clean delete, and every claim keeps its
source. The store is a SQLite file with a local embedding sidecar for search.

## Evaluation (Step 4): four arms, five benchmarks, on Kaggle

Each benchmark runs the system four ways (full store, no context, flat retrieval, and one with a
resolution signal switched off), scored by that benchmark's own published scorer. Benchmarks:
GraphRAG-Bench and NarrativeQA (question answering), LongMemEval (knowledge updates), BookCoref
(how correctly entities are linked), and MemTree (the cost of keeping summaries current). The plain
baseline is reproduced first, so the numbers are comparable to published ones.

## Tentative paper outline

A systems-and-experience paper (a working backend, measured), for a resource or in-use track.

1. Introduction. Retrieval returns similar passages, not current truth, with no provenance and no
   sense of what a fact superseded. A working backend that fixes this with borrowed parts, measured
   for what each part is worth.
2. Related work. The borrowed mechanisms and where they came from (hierarchical summaries, dated
   facts, per-entity summaries, entity resolution), cited up front.
3. The system. The store, the quote gate, the merge-free identity tree, salience, and how "what is
   true now" is computed at read time.
4. The dataset. Step 0: public, reproducible, with a verified structural contract.
5. Evaluation setup. The four arms, the five benchmarks, the parity check, judged-scoring
   discipline, and cost accounting.
6. Results. Attachment accuracy; question-answering accuracy per token against the published
   baselines; knowledge-update accuracy; the cost curves; the free instruments.
7. Discussion. What a merge-free store buys (insertion, deletion, provenance); the controls against
   the model already knowing famous books; honest limitations.
8. Conclusion. The dataset (with a DOI) and the assembled wiki as the artifacts.

The claim is not "we win on accuracy." It is competitive accuracy at a fraction of the token cost,
every answer traceable to a quote, no graph database and no server; and, if time allows, that the
accuracy holds in a large mixed store, not just on a clean single corpus.
