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

## Rulings (Justin, 2026-09-04, in conversation)

The governing rule, stated by Justin: **the extractor sees raw files and nothing else.** No
metadata beside a file, no manifest as input, no question sets. It reads the bytes, decides
what the file is, and writes document and unit JSON. Everything below follows from that.

1. **chinese/ is out.** NarrativeQA becomes 11 works and 319 questions (Dream of the Red
   Chamber carried 26). The OCR control and the translation control lose their source and
   leave the fall slate; they return only if the folder does.
2. **The Thebaid file is removed from the dataset.** greek/ is 31 files; SOURCES.md keeps the
   provenance and the reason. No exclusion flag exists anywhere.
3. **LongMemEval: `_s` is the source; a session is a document.** A one-time unpack script
   writes one JSON file per distinct non-empty session (session id, date, turns as role and
   content; the `has_answer` flag is question data and is dropped). About 18,800 files. The
   oracle and `_cleaned` files are not used. Questions are deferred to the evaluation step.
   This is how the product is meant to be used, so the session loader is the one to get
   exactly right.
4. **Units are turn groups cut by size at turn boundaries**, never a turn alone and never a
   cut inside a turn, with a short tail merged into the unit before it. The same rule covers
   every source: a unit is a size-bounded run of the document's natural pieces (chapters,
   turns, sections). The speaker is read off the role prefix in the text. The cap and the tail
   floor are the two numbers the extractor chat proposes. This also settles sub-splitting.
5. **GraphRAG-Bench: the 20 contexts are unpacked to 20 text files**, written as-is (one line
   each). `novel.json`, `novel_questions.json`, the gold, and the scorers stay in the
   repository for the evaluation step; the LICENSE is copied into the folder for attribution.
6. **Papers go in raw, as the 142 PDFs, in a private Kaggle dataset** (most arXiv PDFs and
   all paywalled ones cannot be redistributed publicly). The extractor reads a PDF like any
   other file: one dependency for the text layer, document is the whole paper, units are
   sections, the abstract is the first unit, author, title, and date are read from the first
   page and quote-backed. The PDF loader moves from spring to fall. The abstract demo stays
   spring. No arXiv metadata is fetched for the extractor.
7. **Public dataset license is MIT**, with attribution in the manifests, the description, and
   the two copied LICENSE files. The extractor never sees any of it.
8. **The manifest is packaging, not a decision.** Built by the fetch and unpack scripts as
   provenance plus the answer key for scoring the extractor's metadata (title, author, year,
   translator, quality flags, ordinal, real source URL, license, sha256). Never an input.
9. **Source class follows the sniffed format**: book to canonical, chat session to record,
   paper to published. Author comes from the file or is flagged unknown.
10. **Export goes to `data/clean/` and the next version of the units dataset.** Packaging.
11. **The extractor lives on Kaggle for now**, visible to Fang and ready for the preprint;
    eventually it is a GitHub tool that runs on the desktop.
12. **The old unit counts are a reference, not a requirement.** The extractor runs, Justin
    reviews the count differences, and his rulings become the new fixture.
13. **LongMemEval is fall** (dataset and extractor); the parity arm is scored at the
    evaluation step. The consolidated docs are corrected to say so.
