# Inventory: everything the raw dataset and the extractor must handle

2026-09-04. Four sweeps (design documents, disk, Kaggle, file formats) and a cross-check of
`step0-brief.md` against them. Every figure below was recomputed from the repository or the
Kaggle CLI; the sweep outputs are in the session record. Items needing Justin's ruling are
under "Decisions" at the end.

## What exists

| source | on disk | documents | words | license | format |
|---|---|---|---|---|---|
| oz/ | `data/raw/oz/`, 29 files, 7.4 MB, all sha256 verified | 29 | 1.28M | US public domain | Gutenberg text, CRLF, header/footer markers in all 29 |
| holmes/ | `data/raw/holmes/`, 9 files, 4.0 MB | 9 | 0.68M | US public domain | Gutenberg text; PART/CHAPTER nesting in 01 and 07; five story collections |
| greek/ | `data/raw/greek/`, 32 files, 21.0 MB | 32 (31 used; Thebaid excluded) | 3.36M | US public domain; 6 Archive.org scans | 26 Gutenberg texts (25 with a `Translator:` line) + 6 Archive.org OCR scans with NO header, footer, markers, or preamble; 3 bilingual Loeb OCR |
| chinese/ | `data/raw/chinese/`, 11 files, 18.1 MB; on Kaggle raw already; never split | 11 | n/a (5 files are Chinese-language) | US public domain | 8 Gutenberg + 3 Archive.org OCR (no markers); 01 OCR vs 05 proofread of the same volume is the OCR control; 04 is the translation-control source; 06 is NarrativeQA's Dream of the Red Chamber |
| graphrag-bench/ | `data/benchmarks/graphrag-bench/novel.json`, 4.8 MB, sha256 attested | 20 | 839,608 | MIT (notice must accompany copies) | ONE JSON file, 20 records `{corpus_name, context}`; each context is a single string with zero newlines; Gutenberg START/END markers stripped; producer credit at the head, "End of ... Project Gutenberg" tail in 17/20; 9 of 20 have no CHAPTER token; several are not novels (a periodical issue, Pepys's diary, a play, Ovid's Amores, travel books, essays, a primer, story collections) |
| longmemeval/ | `longmemeval_oracle.json` 15 MB committed; `longmemeval_s.json` 278 MB and `longmemeval_s_cleaned.json` 277 MB on disk, gitignored, not in the manifest | oracle: 500 questions, 948 session slots (940 distinct), 10,960 turns; _s: 500 questions, ~50 sessions each, 246,930 turns, 1,230 empty sessions | | MIT | one JSON ARRAY (not JSONL); turns are `{role, content, has_answer}` with NO timestamps; session dates in a parallel `haystack_dates` list ("2023/04/10 (Mon) 17:50"), unsorted in 34 oracle records; sessions reused across questions (8 in oracle, ~5,300 in _s) |
| arxiv/ | nothing on disk; 142 PDFs in `papers/`, 7 more in `_unused/`, 9 paywalled stubs; 125 have a recoverable arXiv id, 17 do not | 90 to 125 depending on the set chosen | | per-paper arXiv licenses, unrecorded | record shape undefined anywhere in the repo |
| narrativeqa | `documents_ours.csv` (12 rows), `qas_ours.csv` (345 rows); full CSVs only with `--all` | 0 new text; 12 works = greek 5, oz 3, holmes 3, **chinese 1** | | Apache 2.0 | gold only; joins to raw files through the project-added `_gutenberg`/`_corpus` columns; NarrativeQA's copies were different Gutenberg fetches of the same ebook ids (sizes differ) |
| local transcripts | outside the repo, `C:\Users\jhffm\.claude\projects\`, 46 top-level JSONL files | smoke test only, never uploaded | | private | one JSON object per line; line `type` in {user, assistant, attachment, queue-operation, atis-latch, last-prompt}; only user/assistant lines carry a message; ISO timestamps; content is a list of typed blocks |

Also on Kaggle: `jhffmn/it494-narrative-corpora-raw` (public, CC0, v1, 88 files incl. chinese/, empty description) and `jhffmn/it494-narrative-corpora-units` (public, CC0, v1, 69 documents / 1,301 units, byte-span units with text). Two notebooks, both public.

## What the brief got wrong

1. "NarrativeQA needs no new text: its 12 works are in oz/, holmes/, greek/": one of the 12 is `chinese/06_9603.txt`. Without chinese/ the NarrativeQA arm, the protected OCR control, and the translation control all lose their source.
2. "Eleven works the old splitter left as one unit": it was seventeen (oz 15, oz 29, greek 3, the nine Euripides plays greek 18-26, and the scans greek 27, 28, 30, 31, 32).
3. "Gutenberg text with header and footer": true of 72 of 81 raw files. The 9 Archive.org scans have no header, footer, markers, or Author line, and the 20 GraphRAG-Bench contexts have their markers stripped.
4. The line-based compressed view is undefined for graphrag-bench/: each context is one line. Markers must be found as substrings, and the "raw file" for sha256 is `novel.json`, not 20 files.
5. "The 20 novels split into chapters or are flagged": 9 have no chapter token and several are not novels; a large share will take the flagged path by design, and the cost line did not anticipate it.
6. "Reuse the existing manifests": they carry no license field, record the literal string `cached` instead of a URL for 65 of 81 works, call the Archive.org files Gutenberg, and holmes/ lacks the `year` key. They must be regenerated.
7. "longmemeval/ (the JSON)": three files, not one, and Zep parity must run on the original `_s`, which is gitignored and unmanifested.
8. "abstracts for the papers in papers/": at most 125 of 142 PDFs have an arXiv id; the docs say "roughly 90" and "roughly 100"; 09-03 ruled the abstracts SPRING and the brief silently made them fall.
9. "69 existing works reproduce their unit count without a per-work entry": greek/ has 32 files; 69 assumes the Thebaid exclusion, which today exists only as a per-work entry in the old splitter and a ban in USAGE.md.
10. "Kaggle notebook first": the log lists notebook-vs-`scripts/extract.py` as open, not decided.
11. Chat inputs "JSONL with roles and timestamps": LongMemEval is a JSON array with no per-turn timestamps; the document boundary (session vs whole haystack) is recorded as undecided in RESEARCH.md.

## What the brief left out

- chinese/ entirely (11 files, three fixtures depend on it), and the per-language rule the compressed view needs: 98% of lines in the Chinese-language files are under 40 characters, so "every short line" is the whole file.
- The Thebaid exclusion mechanism under a no-per-work-entries rule.
- Per-work quality and provenance fields USAGE.md requires: transcription method (proofread vs OCR), bilingual, abridged, translator, ordinal (corpus order, which SCHEMA.md uses to order undated facts), publication year for `occurred_at` (greek years are all null; holmes has none).
- `Translator:` (28 files), `Illustrator:` (14), `Credits:` (68) preamble lines as quote-backed document facts; the docs say entity naming follows the translator.
- Author is unrecoverable in-file for 9 Archive.org files, 3 GraphRAG-Bench contexts, and every LongMemEval session: the unknown-author path fires by design, and the receipt should count it.
- The fixtures' unit counts embed per-work rulings (Pausanias tail cut at INDEX, Aeneid/Bulfinch monotonic fallback, Sea Fairies single for a headless edition, Euripides vol. I split into 9 by titles, Holmes 01/07 per-PART numbering): "reproduce the known count" needs a policy for which of these are matches and which are acceptable flags.
- No fixture exists for plain text, markdown, email, or meeting notes; the only markdown on hand is the repository's own docs.
- The machine-translation artifact (translation control) is a fall document type produced by us, not loaded.
- The ingestion notebook reads `units.jsonl` and `u["text"]`; the new range-based export breaks it until its loader is updated.
- The hand-labeled alias set must be labeled against the unit ids this extractor mints; it cannot be built before this run.
- GraphRAG-Bench gold, LICENSE, and the three scorer scripts (never fetched) need a home; NarrativeQA gold and its join columns need to sit beside the dataset for the Kaggle arm.
- The raw dataset's root docs (SOURCES.md, USAGE.md, WANTLIST.md) and the empty Kaggle description.
- The consolidated docs still schedule LongMemEval as spring or first cut (README.md:104, :113; evaluation-corpus.md:35-36); the 09-04 decision that puts it in the fall dataset was not carried into them.

## Decisions (Justin)

1. **chinese/**: in the raw dataset (all 11, with the per-language line rule deferred) or out (and then NarrativeQA is 11 works, the OCR control and translation control have no source on Kaggle)?
2. **Thebaid**: excluded by a manifest flag (`exclude: true, reason`), by removing the file from the folder, or processed and flagged by the gates?
3. **longmemeval/**: oracle only (15 MB), or oracle plus `_s` (278 MB) so the parity arm has a Kaggle input? And the document boundary: one session per document (948 in oracle), or the whole haystack per question?
4. **graphrag-bench/**: keep `novel.json` as the one raw file with 20 documents extracted from it, or write 20 text files? Where do `novel_questions.json`, LICENSE, and the scorers live?
5. **arxiv/**: fall or spring; which set (the 125 with ids, or a chosen subset); the JSONL record shape; redistribution terms recorded per paper.
6. **Licensing of the combined dataset**: CC0 no longer fits a dataset that carries MIT (GraphRAG-Bench, LongMemEval) and Apache (NarrativeQA gold) material; per-folder license in each manifest with the dataset declared as mixed.
7. **Manifest schema** for every folder: file, sha256, bytes, source_url (real, not `cached`), source (gutenberg, archive.org, graphrag-bench, longmemeval, arxiv), license, ordinal, title, author (when known at load), year, quality flags (ocr, bilingual, abridged), translator, exclude + reason. `fetch_corpus.py` is rewritten to emit it, or the manifests are regenerated by hand.
8. **Author and source_class per folder**: Gutenberg from the `Author:` line; Archive.org from the manifest; GraphRAG-Bench from the trailing "by <Author>" in 17/20 else unknown; LongMemEval per turn (user, assistant) with the session as `record`; arXiv from the authors field. Source classes: canonical for Gutenberg and Archive.org works, record for benchmarks, published for arXiv.
9. **Export location and dataset identity**: `data/clean/` in the repo for the JSONL (already covered by .gitattributes), and whether the new raw and units datasets are new versions of the existing two or new datasets.
10. **Extractor location**: Kaggle notebook with a repo copy, or `scripts/extract.py` imported by the notebook.
11. **Fixture policy**: which of the embedded per-work rulings the general extractor must reproduce exactly, and which count as acceptable flags.
12. **Fall/spring status of LongMemEval** in README.md and evaluation-corpus.md, to match the 09-04 decision.
