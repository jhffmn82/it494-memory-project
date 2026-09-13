# Archive

Things the project no longer uses, kept so the history reads whole. Nothing here is current.
Moved on 2026-09-13 during the repository cleanup; `docs/rulings.md` says what replaced each.

## scripts/

- `fetch_papers.py`: fetched the 142 reference PDFs into `papers/` and wrote `papers/MANIFEST.md`.
  The reference papers left the corpus on 2026-09-09 (replaced by the 100 CC-BY papers in
  `data/raw/kg-rag-cc/`), and the PDFs are untracked since 2026-09-13. Still runnable for a
  local reading copy.
- `papers_manifest.py`: wrote the manifest of the private Kaggle dataset
  `jhffmn/it494-reference-papers`, which the extractor mounted until 1.6. Nothing mounts it now.
- `rebuild_export.py`: rebuilt the 2026-09-06 extractor export locally from a run's printed log,
  with the withheld-paper path. Every export since 1.7 is downloaded whole from Kaggle and every
  document carries its text, so there is nothing to rebuild.

## Not moved, but superseded

- On Kaggle: the dataset `jhffmn/it494-narrative-corpora-units` (69 documents, 1,301 units,
  2026-09-01) and the notebooks `it494-narrative-corpora-splitting-and-gates` and
  `it494-chapter-ingestion-oz-book-1` are the 09-02 demo. The current dataset is
  `jhffmn/it494-threadatlas-step0` (1.8) and the current notebooks are `threadatlas-extractor`
  and `threadatlas-document-ingestor`. Marking or retiring them on Kaggle is Justin's action.
- `summaries/one-pagers/_unused/` and `papers/_unused/README.md`: retired reading, already set
  aside on 2026-08-28.
- `log/`: every dated folder is a snapshot of its day and is never edited.
