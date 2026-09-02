# Working log: 2026-09-02

First book ingested end to end. What exists, where it is, and what the run showed.

## Links

- Dataset, split units: https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-units
- Dataset, raw texts with sha256 manifests: https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw
- Preprocessing notebook (raw texts to verified units): https://www.kaggle.com/code/jhffmn/it494-narrative-corpora-splitting-and-gates
- Ingestion notebook (Oz book 1, all 24 chapters): https://www.kaggle.com/code/jhffmn/it494-chapter-ingestion-oz-book-1

## Files in this folder

- `it494-narrative-corpora-splitting-and-gates.ipynb`: the preprocessing notebook as published.
- `it494-narrative-corpora-splitting-and-gates.output.txt` and `.output.html`: its saved run
  (oz 29/29 documents, 613 units; holmes 9/9, 111; greek 31/31 with 1 excluded, 577; master
  69 documents, 1,301 units).
- `it494-chapter-ingestion-oz-book-1.ipynb`: the ingestion notebook as run (version 3).
- `it494-chapter-ingestion-oz-book-1.output.txt`: every line the run printed, extracted from the saved output.
- `it494-chapter-ingestion-oz-book-1.output.html`: the saved output as Kaggle rendered it.

## What was done

**Corpus.** Harry Potter is copyrighted, so the corpus is public domain: the Oz series, the
complete Sherlock Holmes, and Greek and Roman classics, with the Chinese classics held back
because the public-domain translations are incomplete. Each work was split into chapter- or
section-level units, every unit carrying its byte span and its document's sha256, so any
quote can be traced back to the raw file. Published: 69 documents, 1,301 units (Oz 613,
Holmes 111, Greek 577).

**Ingestion, per unit.** Each chapter is processed on its own, with no identity resolved:

1. Entity pass: name, kind, salience (major or minor), and the verbatim surface forms.
   A surface form that does not occur in the text is dropped.
2. Fact pass: atomic facts `{subject, predicate, object, qualifiers, quote}`. A fact whose
   quote is not in the text is dropped and counted.
3. Summary and cells: a unit summary and a narrative cell for each named entity.

**Reconciliation, bottom up.** Every entity from every unit starts as its own cluster.
Candidate pairs are nominated by a shared name or surface form, a fact stating one is the
other, or a shared name word. The strongest pairs are judged first, in batches of ten, by a
stronger model that sees both clusters' accumulated names, forms, facts, and relationships;
a same verdict merges them, so later pairs are judged with more evidence. Every verdict and
its reason are in the ledger. Entities from the same unit are never paired, and two minor
entities are never paired with each other.

**Store.** Major entities are nodes; the document and each unit are nodes too. A fact from a
major entity to another major entity is an edge; a fact to a minor entity or a literal is a
property. Minor entities are dropped from the store and kept in the unit records.
Predicates are consolidated under canonical names, with names used for two different
relations flagged as fork candidates. Each major entity's cells fold into an abstract; the
unit summaries fold into a document summary.

The prompts do not know they are reading a novel. The only corpus-specific cell is the
loader.

## Results, Oz book 1

| stage | result | cost |
|---|---|---|
| derive, 24 units | 632 local entities, 969 quote-backed facts | $0.16 |
| reconcile | 307 major locals to 114 major entities; 976 verdicts (326 same, 650 different) from 4,286 candidate pairs | $1.03 |
| store | 113 nodes, 866 facts (465 edges, 401 properties); 103 minor-only facts left in the unit records | |
| predicates | 374 surface forms to 334 canonical; 6 fork candidates | $0.07 |
| total | 171 calls | $1.26 |

Models: gpt-5.6-luna for extraction, gpt-5.6-terra for reconciliation, vocabulary, and
abstracts.

What the judge got right: the Wizard's disguises (the Head, the Ball of Fire) merged into
Oz; Dorothy's house absorbed "old farmhouse" and "home"; the Emerald City absorbed "City of
Emeralds"; Dorothy's basket stayed apart from the balloon's basket. The document summary
runs correctly from the cyclone to Aunt Em's welcome.

What needs work, in order: about half the 114 major entities are single-chapter events
("first ditch crossing", "raft building") that meet the two-sentence-summary test but make
poor nodes; some facts echo the predicate in the object (`is_gray -> gray`); `has` (92
uses) and `is` (67) dominate the vocabulary, which the fork flags correctly call out;
Dorothy's abstract stopped at chapter 2 while every other abstract ran to the end. Three
one-sentence prompt changes for the first three are in the next version of the notebook.
Two pairs the judge kept apart are debatable: `Kansas prairies` vs `Kansas`, and
`Scarecrow's brains` vs `brains`.

## Next

- Run the revised notebook and compare rosters.
- Merge a document's entities into the corpus with the same bottom-up strategy.
- Measurement: a hand-labeled alias set for the reconciliation, then the evaluation slate in
  `docs/evaluation-corpus.md`.
