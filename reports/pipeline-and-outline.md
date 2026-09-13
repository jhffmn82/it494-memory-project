# The pipeline, and the tentative paper outline

Justin Hoffman. IT 494. 2026-09-08.

Updated 2026-09-13 to the pipeline as it runs.

## The extractor (Step 0): a raw file becomes a split plan

Input: any raw file, a Gutenberg text, a chat log, a PDF. The format is sniffed from the bytes;
there are no per-file rules. A book or paper is shown to a model as its own numbered lines; the model
points at each boundary by line number and copies the line, and code verifies the number against
the copy before cutting. Three gates check the result: the pieces cover the whole document with no
gaps, no unit mixes kinds (body vs references vs appendix), and every boundary's text is real.
A chat needs no model call: each turn that says something is one piece and one unit, carrying its
speaker and its time. LongMemEval is unpacked from the benchmark file into one folder per question
history, each session copied under that history's date. Every unit is dated where a source allows,
by when the work was written; a document takes its earliest unit's date.
Output, one row per line of JSONL: documents (the text, once), units (character ranges), pieces
(the split plan, with a chat turn's speaker). Whole corpus in one pass (extractor 1.8, 2026-09-13):
24,071 documents (23,882 chats in 500 histories, 89 texts, 100 PDFs), 251,446 units, for $8.24.
Published as the Step 0 dataset, kaggle.com/datasets/jhffmn/it494-threadatlas-step0.

## The ingestor (Step 1): a document becomes a knowledge package

Input: one document's text, units, and pieces. A book or paper takes the full path. For each unit:
the entities in it (kept only if a name is found in the text), the facts about them (kept only if a
verbatim quote is located), and a short summary plus a narrative cell per major entity. The
document's unit-local entities are then reconciled into document entities, with a judge deciding
which are the same, and each major entity's facts are consolidated, with contradictions recorded
rather than erased. A chat is read in one model call per session (a long session in stretches of
whole turns): each fact is tied to its turn, the reading's summary is the document's abstract, and
there are no cells and no judge; one support call and a verification pass follow. Output: one
package per document (entities, quote-backed facts at character offsets, cells for books and papers,
an abstract per entity), plus a full cost log. A chat session costs $0.0042 to $0.0045 (ingestor
1.7, frozen 2026-09-12); a book costs more.

## The store (Steps 2 and 3): a merge-free identity tree, in SQLite

Across documents, entities are not merged. Each document keeps its own version of an entity, and an
edge attaches it to a parent that holds only a derived name and summary, nothing asserted.
Re-deciding identity re-points an edge; nothing is rewritten. This makes three normally-hard things
easy: adding a document is append-only, deleting one is a clean delete, and every claim keeps its
source. The store will be a SQLite file with a local embedding sidecar for search; it is not built yet.

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
