# 2026-09-09: the rename, the CC-BY corpus, and two rulings

Written 2026-09-13 from the day's commits, the weekly report and the Step 0 export, because no
log was kept on the day. Every number is the one the commit or the export records.

## The system is ThreadAtlas (819c678)

The decision record of the 9 September project review, filed as
[threadatlas-decision.md](../2026-09-08/threadatlas-decision.md), named the complete system
ThreadAtlas and left FactLedger as the name of the fact, quote, validity and provenance layer
underneath. Every artifact took the new name: both notebooks and their `.py` sources, the four
as-run copies in the logs, the two Kaggle notebook slugs, the Step 0 dataset id, 396 occurrences
across 51 files. Dated logs that record the name being FactLedger on their day were left alone.
The loader constant became `threadatlas-extractor 1.6`; the version is not consulted when deciding
what to re-ask, so the rename triggered no re-extraction.

## The profile record is dropped (0b6cc81, ruled)

Measured over every package on disk, 486 profile rows across 132 nodes: animacy 438 times and
gender 48, age band and role never once though the prompt asked for both, every animacy value
"animate" and every gender value "female", and only on person and character nodes. It was not
making category errors on other kinds; it was asserting 438 times that a person is animate. It was
also the last record in the package that said something about the world with no quote behind it.

The pair score was renormalised with it: 0.6 name + 0.25 co-occurrence + 0.15 profile became
0.7 name + 0.3 co-occurrence, so `SIMILAR_ENOUGH = 0.35` means what it meant. Dropping the term
alone would have lowered the maximum to 0.85 and made person pairs relatively harder to unite. The
battery pins the score; both mutations (putting the record back, dropping the term without
renormalising) go red.

## The papers corpus is 100 CC-BY works inside the raw dataset (0d949b0, 76da655, 9f412c9)

The private `it494-reference-papers` mount is gone from the extractor. The 100 CC-BY papers on
knowledge graphs and RAG (`kg-rag-cc`, gathered 09-08 from OpenAlex, most cited first) ride in the
public raw dataset, so the extractor has one input again and no document's text is withheld. The
packer writes `attribution.jsonl` (authors, title, license, DOI, source URL per paper, joined on
`doc_id`, which equals the PDF's sha256) instead of `papers.jsonl`. The raw dataset's v3 metadata
lists `kg-rag-cc` and moves the dataset-level license label from MIT to "other", since the folders
are under three licenses. A record naming a file outside the raw dataset now raises instead of
being silently truncated to a path that exists nowhere.

## The ingestor: four fixes folded onto master, the PDF path gone, three Oz books (b5c8b90)

Branch fold-09 carried the 0.9 test material and four fixes from the 09-08 and 09-09 review onto
master: `one_phrase` (a corrected qualifier is one string; a list had killed a 28-minute chat
block in the roll-up), a roll-up that reports its own failure instead of taking the run with it,
the profile drop, and the score renormalisation. `pdf_text`, `withheld_text`, `PAPERS`,
`papers.jsonl` and the sha256 check went with the PDF path: Step 1 now runs end to end on public
data. **Ruled:** block 13 runs the first three Oz books, not one, because one book cannot show a
character carrying across works, and contradictions between books are where a document's end
state and the layer above it differ. 2,526 to 2,502 lines, 81 checks.

## Step 0 documentation, twice (c3bee9d, 6dda4cd)

The five `dataset/step0/` documents and the metadata were rewritten from the export of the CC-BY
run: 19,395 documents, 42,979 units, 224,718 pieces, $6.60, 6 of 189 read documents escalated.
The 1.6 re-run then asked the model again rather than only re-exporting, so the split moved:
42,822 units, 224,522 pieces, $6.64, four escalations, 224 pointer mismatches with 178 recovered.
Every count was re-derived. LIMITS gained the three Apollodorus and Ovid scans whose region
labelling collapsed to almost no body. That run was published as
`jhffmn/it494-threadatlas-step0` at 03:23 UTC on the 10th, before the two rulings below reached
the code; chat titles were null and units still carried `occurred_until` in that version.

The README and SCHEMA of that version said a book's pieces carry the document's author. In every
run book pieces have null author and null time; the docs were corrected in the repo on 09-10.

## Two rulings (fa48997)

1. **`occurred_until` is gone** from the unit record and the fact record. Across the released
   export the two ends were equal on 41,374 units and both null on 1,448, and differed on none.
   Removed from the extractor, the ingestor, SCHEMA, BUILD, docs/extractor, the published
   dataset/step0/SCHEMA, `rebuild_export` and `render_package`. The day cut in `chat_runs` was
   left in place that day (it went with 1.7 on 09-10). Accepted cost, Justin's with the case in
   view: when the Claude and ChatGPT archives arrive with a timestamp per message, a unit spanning
   an hour will have no way to say so.
2. **A chat document's title is the session id its own file states.** Title had been null on all
   19,206 chats because no metadata call is made for a chat. SCHEMA states the general rule: a
   title is the source's own name, an identifier counts as a name when it is the only one, and a
   title is never parsed out of a filename. Author stays null on chats; the voice lives on the
   piece.

Held, not ruled: `valid_to`. It was dropped on 09-10 (decisions-ingestor-1.7, ruling 3).

## The weekly report (c8d6de8)

[reports/2026-09-09-weekly.md](../../reports/2026-09-09-weekly.md) went to Dr. Fang: the name,
the change of direction to narrative cells as the primary representation, answers to his three
questions (the papers run end to end and are now redistributable; SQLite, one file; bge-small
through fastembed, sentence-level vectors), and the ASKS overlap question. `scripts/render_package.py`
produced the attached Zep rendering. ASKS (`papers/ran2026-asks.pdf`, one-pager
`summaries/one-pagers/ran2026-asks.md`) was added the same day.

## Open at the end of the day

- The published Step 0 version predates both rulings; republish after the chats are settled.
- The chat design: every chat was two units (a header and the whole conversation), and every
  turn carried the session's earliest date. Ruled wrong on 09-10.
- Root SCHEMA.md, BUILD.md and docs/extractor.md still describe a day cut and runs of turns.
