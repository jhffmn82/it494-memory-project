# Working log: 2026-09-06

The document ingestor (Step 1), opened from `log/2026-09-05/ingestor-brief.md` in its own chat
on a worktree branch. Read the brief, SCHEMA.md, BUILD.md, the 09-05 and 09-04 logs, plan.md's
Step 1 and `docs/entity-resolution.md`; revisited the Oz chapter-1 demo; settled the three
questions the brief left open; then, on Justin's "build the full pipeline, audit it against the
project, audit the project, test it", built it end to end against a reconstruction of the
extractor's export and ran a 59-check offline battery. Decisions are Justin's where marked;
mine are listed in [audit.md](audit.md) section 1.5 for him to reverse.

## The extractor run landed

Kaggle version 347794765 of `factledger-extractor`, the 1.0 code on the branch, finished over
the whole corpus in an interactive session:

| | |
|---|---|
| documents | 19,436 (89 text, 141 PDF, 19,206 chat) |
| units | 24,156 |
| pieces | 226,418 |
| pointers | mismatch 270, recovered 197, unresolved 73, duplicate 8, metadata nulled 12 |
| body share | 78.9% of 48.6M characters read from text and PDF |
| flagged | 70 of 231 read documents; 3,944 chats on reused dates (advisory) |
| cost | $40.67 |

The Quick Save kept the printed log and zero output files, so the export
(`documents.jsonl`, `units.jsonl`, `pieces.jsonl`, `receipt.json`) is still inside the session.
The rendered log is saved here as `extractor-run-347794765.txt` and the notebook as it ran as
`factledger-extractor-as-run-347794765.py`; it differs from the committed 1.0 only in comments,
a helper rename and the merge's rewrite of its own bookkeeping.

**`scripts/rebuild_export.py`** rebuilds the export locally from that log and the raw files:
every text and PDF piece's start offset, unit and kind are in the log, pieces tile, and chats
need no model. Every rebuilt piece is checked against the log's 60-character snippet of its
text, so a PyMuPDF or line-ending difference would drop the document rather than export it
wrong. Result: the run's exact counts, zero snippet mismatches, the duplicate paper skipped as
the run skipped it. Labels are cut at 40 characters, which is the one loss. The ingestor ran
on this; the real export drops into `data/export/` when Justin downloads it.

## Rulings and agreements from the morning

- **Predicates.** Everything is derived at document level, fresh, without seeing the global;
  the merge folds. The ingestor keeps the model's predicate string (normalised to
  `lowercase_snake_case` only), writes a per-document census, and makes no consolidation
  call. The controlled list and the type table are the merge's, minted from every census.
  Reading of SCHEMA.md's "small controlled list": derived once, controlled thereafter; only
  `is_a` is declared. The honest weakness stated: a derived type table catches the outlier,
  not a first-time fabrication; a second pass over stored facts is the cheap fix.
- **A running roster.** Units are not independent: entities that earned a place and the
  predicates used so far go forward as suggestions, each reuse declared by the model and
  logged as a resolution decision with evidence. BUILD.md's previous-unit-summary rule, done
  properly. PROPOSED sentence in the audit.
- **Cost.** The demo's $1.26 was 82 percent judge. The chat corpus (51M tokens) is three
  quarters of the derive bill and has no judge at all, being one unit per session. The cuts
  taken: dossiers sent once per judge call, scored pairs before any judge, one-unit documents
  fold nothing, only document-majors get abstracts, profile in the entity call, no predicate
  call. Two to measure: two calls per unit instead of three; the judge on Luna.
- The cell rule and the package layout were put to Justin, not ruled, and taken as decisions
  3 and 4 in the audit.

## What was built

`notebooks/factledger-ingestor.py` (script form, `# %%` cells) and `.ipynb` generated from it
by `scripts/py_to_ipynb.py` (the 09-05 generator generalised to take a path); the two
round-trip to identical text. Eleven blocks:

1. inputs: the export indexed by `source_uri` with a byte offset per document, one seek per
   load, every unit asserted to be a real slice;
2. `generate(prompt, schema)` and `embed(texts)` over raw HTTP (`urllib`), `reasoning_effort`,
   JSON mode, a stdlib schema validator, one retry with the error, three retries on
   transient failures, every call logged with cost, the spend stop;
3. content-hash ids and the name finder for the fabrication check;
4. **the quote gate**: exact, then whitespace-flexible, then on an NFKC/quote/dash/case
   normalised copy whose every character maps back to an original offset; a miss classified
   `paraphrase` (most words there in order) or `not_found`; surface forms located the same way,
   whole words only;
5. the prompts: entities with surface forms, profile and `continues`; facts with quote,
   `valid_from` and `valid_to`; summary and cells in one call with the previous summary;
   the judge with numbered dossiers; the fold;
6. `derive_unit`: three calls, every gate in code, offsets stored as document offsets, voice
   by piece lookup, the date kept only when its year is in the quote, the agreement check,
   one record per unit holding everything kept and everything rejected;
7. `reconcile`: union-find over unit-locals; declared continuations and exact names unite
   without a judge; every other candidate scored on name, co-occurrence and profile
   separately; the ambiguous band judged ten pairs a call with each dossier sent once; a
   ledger row with evidence for every decision;
8. `fold_document`: the abstract under the bound with the name check and one retry; salience
   against the abstract; dossiers with embeddings; per-entity abstracts with `children_hash`;
9. `write_package`: one JSONL per document mirroring the raw layout, records in merge order,
   minors without nodes, a completion record with counts, stats and `input_hash`;
10. `run` over a list of documents, resumable by `input_hash`, `ingest.log`, `manifest.jsonl`,
    `receipt.json`, `calls.jsonl`, `rejections.jsonl`;
11. the test variety as a list: three Oz, two Holmes, two Greek, two GraphRAG-Bench, twenty
    papers, three hundred sessions (`--sample`).

**Tests:** `test_ingestor.py`, 59 checks, no network. A scripted model reads each unit and
answers with real substrings plus the bad answers the gate must catch (doubled spaces, curly
quotes and swapped case, a paraphrase, a fabrication, an unlisted subject, a duplicate, a
surface form that is not there). Over Oz book 1's real units: every fact slices to its quote
inside its unit; all three match paths and all four rejection categories exercised; every
mention slices to its surface; minors have null `node_id` and no node; cells only where a
fact is; the abstract's names in its children; majors exactly the entities named in the
abstract; a dossier with an embedding per major; ledger rows with evidence; candidate rows
with three scores; re-running skips by `input_hash` and two derivations agree line for line.
On a real LongMemEval session: every fact carries the author of the piece holding its quote,
user and assistant both present, the abstract is the unit summary with no fold call. On a real
paper: quotes located through PDF ligatures, the published voice, the first unit derived like
any other. A fold that keeps a fabricated name after its retry is not stamped, and with no
abstract no node is minted. 59 of 59.

## What was measured from the run's log, for the ingestor

- **Paper abstracts** are not reliably unit 0: 57 of 142 papers have the abstract piece in
  unit 0, 65 in unit 1, 19 with no labelled abstract piece, 1 mislabelled. The ingestor does
  not branch on it; the evaluation of "the abstract path" must not assume position.
- **Oz book 1 is 26 units**, one per chapter plus front matter, introduction and license,
  because grouping joins a piece only with the pieces under it and chapters have none. The
  read corpus is 4,964 units (2,139 paper, 2,825 text), median 609 and 2,164 words.
- The chat corpus is 19,206 one-unit documents at a median of about 1,700 words.

## Open

- **The real run.** No `OPENAI_API_KEY` in this environment. Either set it and run
  `python notebooks/factledger-ingestor.py --sample` (about $8 by the cost model, stop at
  $10), or publish the export as a dataset and run the notebook on Kaggle. Then: Oz book 1's
  rejections classified by hand, the cost against the demo's $1.26, the tier spread, the
  roster's effect on the judge, and the paper and chat paths on real facts.
- The real export out of the Kaggle session, into `data/export/` and onto Kaggle.
- The PROPOSED items in the audit: `author` and `object_is_node` on the fact, the default
  `rank`, `dossier` as a named record, the roster sentence in BUILD.md, the abstract as a
  labelled piece, plus the 09-05 docs patch and `flags`.
- Guards 4 and 5 of the resolution doc (cluster cap, merge rate per unit).
- Whether reference and license units should be derived at all (audit decision 13).
