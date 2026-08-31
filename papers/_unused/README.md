# Retired sources

Nothing here is deleted; move a file back if a document starts citing it.

## Retired 2026-08-28, first pass: unreferenced by any probe

- `tics2016-vol20no7-contents.pdf`: a journal table-of-contents page, not a paper. Never had a
  one-pager.
- `fu2026-vikingmem.pdf`: VikingMem, a memory base management system (arXiv:2605.29640).
- `lin2026-stagewise-benchmarking.pdf`: stage-wise benchmarking of LLMs for fact-checking
  (arXiv:2601.02669).

## Retired 2026-08-28, second pass: the timeline-summarisation cluster

`01_argument.md` borrows "per-entity chronology from timeline summarisation" in a single clause and
names no specific paper. That claim needs one citable source, not five. **Ghalandari et al. 2020,
the survey, was kept and is now cited explicitly**; these four application papers were adding
nothing to the claim:

- `qorib2024-constrained-tls.pdf` (arXiv:2412.17408)
- `tran2017-tls-entity-ranking.pdf` (arXiv:1701.03947)
- `zhang2024-dtels.pdf` (arXiv:2411.09297)
- `zhang2026-timelinereasoner.pdf` (arXiv:2605.12518)

Their one-pagers moved to `summaries/one-pagers/_unused/`.

## Nearly retired by mistake, and worth recording

`zhang2024-ocr-hinders-rag.pdf` **is OHRBench**, the paper `02_requirements_and_testing.md` had been
pointing at by name for the OCR-tax control. An edit earlier the same day replaced that vague
"prior art in OHRBench" mention with a citation to a different, later paper, which orphaned the
original and made it look unreferenced. Both are now cited. **A paper looking unused can mean a
citation was broken rather than that the paper is unneeded.**

## On the method

The first automated pass over this directory reported 23 unreferenced papers. It matched on filename
slug only, and produced a false positive for every paper cited by project name or arXiv identifier:
AutoSchemaKG, ProactAgent, HERCULES, TraceMem, CogniFold and eleven others. The current check probes
slug, arXiv id, author surname, and distinctive title tokens, and every match resting on the weakest
probe was audited by hand. **130 of 130 remaining PDFs are referenced.**
