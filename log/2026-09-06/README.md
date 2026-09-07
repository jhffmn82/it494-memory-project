# Working log: 2026-09-06

The document ingestor (Step 1), opened from `log/2026-09-05/ingestor-brief.md` in its own chat
on a worktree branch (`claude/infallible-einstein-e34c97`, with `claude/step0-raw-dataset`
merged in). Read the brief, SCHEMA.md, BUILD.md, the 09-05 and 09-04 logs, plan.md's Step 1 and
`docs/entity-resolution.md`; revisited the Oz chapter-1 demo; settled the three questions the
brief left open; then, on Justin's "build the full pipeline, audit it against the project,
audit the project, test it", built it end to end, ran a 59-check offline battery, put it
through a six-lens adversarial review before any paid run, applied the 32 confirmed findings,
and regenerated the Kaggle notebook. Decisions are Justin's where marked; mine are listed in
[audit.md](audit.md) section 1.5 for him to reverse.

## The extractor's final export

Two runs happened today. The first (Kaggle version 347794765, loader 1.0, $40.67 by its own
receipt) finished in an interactive session whose Quick Save kept the printed log and no
files; its log is saved here as `extractor-run-347794765.txt`, and `scripts/rebuild_export.py`
rebuilt its export locally from that log and the raw files, every piece checked against the
log's snippet, to exactly the run's counts. The ingestor was built and first tested on that
reconstruction.

The **final run** (loader `factledger-extractor 1.5`, Justin's, with a further change to the
chat units) then landed as the kernel's output on Kaggle and replaces the reconstruction. Its
receipt and per-document log are here as `extractor-final-receipt.json` and
`extractor-final-splits.log`:

| | |
|---|---|
| documents | 19,436 (89 text, 141 PDF, 19,206 chat) |
| units | 44,262: 5,850 read, 38,412 chat |
| pieces | 227,100 |
| chat shape | every session is two units, the header alone and then all its turns |
| read units | 2,344 paper (median 516 words), 3,522 text (median 1,670 words) |
| pointers | mismatch 370, recovered 291, unresolved 79, duplicate 4, metadata nulled 8 |
| body share | 81.6% of the characters read from text and PDF |
| flagged | 72 of 231 read documents; 3,944 chats on reused dates (advisory) |
| cost in its splits file | $7.72 |

Measured from its log, for the ingestor: the abstract of a paper is unit 0 in 38 of 142
papers, unit 1 in 84, and has no labelled piece in 20; the ingestor derives every unit and
branches on nothing, so it does not care, but anything that evaluates "the abstract path" by
position would. Oz book 1 is 26 units (front matter, introduction, 24 chapters, license).
Holmes 03 is 44, the Hesiod anthology (greek 03) is 90.

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
  quarters of the derive bill and has no judge at all. The cuts taken: dossiers sent once per
  judge call, scored pairs before any judge, a document with one summarised unit folds
  nothing, only document-majors get abstracts, profile in the entity call, no predicate call.
  Two to measure: two calls per unit instead of three; the judge on Luna.
- The cell rule and the package layout were put to Justin, not ruled, and taken as decisions
  3 and 4 in the audit.

## What was built

`notebooks/factledger-ingestor.py` (script form, `# %%` cells, version 0.2) and `.ipynb`
generated from it by `scripts/py_to_ipynb.py` (the 09-05 generator generalised to take a
path); the two round-trip to identical text. Twelve blocks:

1. inputs: the export indexed by `source_uri` with a byte offset per document, one seek per
   load, every unit asserted to be a real slice; a previous Kaggle version's output attached
   as an input seeds the packages folder so a resumed run pays only for what is unfinished;
2. `generate(prompt, schema)` and `embed(texts)` over raw HTTP (`urllib`), `reasoning_effort`,
   JSON mode, a stdlib schema validator, one retry with the error, three retries on
   transient failures, a 429 for exhausted quota ending the run, embeddings in batches,
   every call appended to `calls.jsonl` the moment it returns, the spend stop;
3. content-hash ids and the name finder for the fabrication check;
4. **the quote gate**: exact, then whitespace-flexible, then on an NFKC/quote/dash/case
   normalised copy that also closes a hyphenated line break, whose every character maps back
   to an original offset; a miss classified `paraphrase` (most words there in order) or
   `not_found`; surface forms located the same way, whole words only;
5. the prompts: entities with surface forms, profile and `continues`; facts with quote,
   `valid_from` and `valid_to`; summary and cells in one call with the previous summary;
   the judge with numbered dossiers; the fold; the roster shown most-recent first;
6. `derive_unit`: three calls, every gate in code, offsets stored as document offsets, a
   span is one mention (the first entity listed keeps it), voice by piece lookup with the
   same words in two voices claiming none, the date kept only when its year is in the quote,
   the agreement check, one record per unit holding everything kept and everything rejected;
7. `reconcile`: union-find over unit-locals; a declared continuation of a named entity and
   the same proper name in two units unite without a judge, an unnamed role never on its
   name alone; every other candidate scored on name, co-occurrence and profile separately,
   a possession never against its own anchor; the ambiguous band judged ten pairs a call
   with each dossier sent once; a ledger row with evidence for every decision;
8. `fold_document`: the abstract under BUILD's bound exactly, with the name check and one
   retry; salience by whole-word match against the abstract, the tie-breakers alone when
   the abstract was rejected, and the node says which; dossiers with embeddings; per-entity
   abstracts with `children_hash`;
9. `write_package`: one JSONL per document mirroring the raw layout, records in merge order,
   minors without nodes, one cell per node per unit, alias rows with the verbatim form and
   its first unit, a completion record with counts, stats and `input_hash`;
10. `run` over a list of documents, resumable by `input_hash` and, mid-document, by a sidecar
    of finished units; `ingest.log`, `manifest.jsonl`, `receipt.json` summed from disk;
11. the test variety: three hundred sessions, twenty papers, two GraphRAG-Bench texts, three
    Oz, two Holmes, two Greek, cheapest first (329 documents, 1,177 units);
12. the run cell for Kaggle, `RUN` and `SPEND_STOP` ($25) in the open, the receipt written
    even when the run is interrupted.

**Tests:** `test_ingestor.py`, 70 checks, no network, against the real export. A scripted
model reads each unit and answers with real substrings plus the bad answers the gate must
catch (doubled spaces, curly quotes and swapped case, a paraphrase, a fabrication, an
unlisted subject, a duplicate, a surface form that is not there, a second entity claiming
the first one's spans). Over Oz book 1: every fact slices to its quote inside its unit; all
three match paths and all four rejection categories exercised; every mention slices to its
surface and mention and cell ids are unique; minors have null `node_id` and no node; cells
only where a fact is; the abstract's names in its children; majors exactly the entities
named in the abstract; a dossier with an embedding per major; ledger rows with evidence;
candidate rows with three scores; every call on disk as made; re-running skips by
`input_hash` and two derivations agree line for line. On a real LongMemEval session: the
header unit yields nothing, every fact carries the author of the piece holding its quote
or null when the same words occur in both voices, user and assistant both present, the
turns unit's summary is the abstract with no fold call. On a real paper: quotes located
through PDF ligatures, the published voice. A fold that keeps a fabricated name after its
retry is not stamped, and with no abstract the tie-breakers decide and the node says so. A
spend stop three units into a document leaves a sidecar and no package; the resumed run
derives only the remaining units and finishes. The hyphenated line break bridges. 70 of 70.

## The review before the paid run

A six-lens review (Kaggle runtime, the API contract, schema fidelity, the quote gate,
reconcile and fold, cost and prompts), each finding handed to an adversarial verifier told
to refute it by reproduction: 34 findings, 33 after dedup, **32 confirmed, 1 refuted**
([review-findings.json](review-findings.json)). The ones that would have hurt a paid run:
resume never worked across Kaggle versions because `/kaggle/working` starts empty; the call
log lived only in memory; two entities sharing a surface form collided on `mention_id` and
two locals uniting in one unit on `cell_id`; a rejected abstract silently dropped every fact
in the document; salience matched bare substrings; a hyphenated PDF line break defeated the
gate; a quote recurring in two turns took the first speaker's voice; the sample spent the
budget on the books before the chats and papers; an exhausted-quota 429 was retried for
minutes per document. All 32 applied as version 0.2 (`a57911b`, 378 lines in, 153 out), the
battery grown to 70. A second pass, four lenses over the patch with one refuter per finding,
was launched after the commit; its outcome is recorded below when it lands.

## Evening: Justin's design put back, and his new rulings built (0.3, 0.4)

Justin's reading of the first Kaggle output (Oz book 1, five units) and of the code brought a
correction that stands as the rule for this project: the chat had replaced four parts of his
design with its own without a ruling. The model's per-unit salience call had been dropped for a
fact rule, so narrative cells went to everything with a fact (37 cells for the front matter, 30
for Chapter III where the summary named 10); with it went the at-least-one-major filter on judge
pairs, the re-judging of unsure pairs, and Terra for the folds. All four were restored (commit
`11b6e6a`), the fact rule and the scores kept only as printed diagnostics. Then, on his rulings:

- **0.3**: the code made readable. No lambdas, no regular expressions; the quote gate has two
  paths, exact and normalised, the normalised copy collapsing whitespace as well as case, quotes,
  dashes and hyphenated line breaks; the export path named outright; documents found by title; a
  connection-test block before anything spends; the Kaggle secret imported explicitly.
- **0.4** (`05ab318`): an AI judge decides which kinds of unit to read, given what we are doing,
  the document's title, author, class and date, and every kind with the first line of each of its
  units; the hardcoded partition is gone. A document-major seen in fewer than two units with fewer
  than three facts is demoted to minor. A minor's fact about a major lands on the major, marked
  inverse. An adjudication call per major, on Terra, consolidates its facts and attributes and
  flags contradictions, every item pointing at the raw facts it was drawn from. Battery 79 of 79.

A review of 0.4 against Justin's goals as stated (four lenses: goals, style, correctness, Kaggle;
one refuter per finding) confirmed a dozen things, all applied before the hand-over: the cap
that overrode the judge's triage on documents with more apparatus than body is gone; the version
string; abstracts stamped with the tier that wrote them; an unsure pair judged once more at the
end and never mid-run; no demotion in a one-unit document, which every chat is; a sidecar cut
short by a kill cannot poison a document; cost carried through a resume; both Kaggle mount paths;
no per-corpus rule in the package path; `reconcile` split into named pieces. Battery 82 of 82.

Under the scripted model, Oz book 1 now runs: front matter and license left out, 24 chapters
derived, 144 unit-locals, every candidate pair to the judge, majors demoted, each major
adjudicated. The real numbers are the run's.

## Kaggle

The notebook is `notebooks/factledger-ingestor.ipynb` (13 cells, nbformat 4.5 with ids).
Import it, then: Add Input > Your Work > `factledger-extractor` (its output holds
`export/units.jsonl`, which block 1 finds); Add-ons > Secrets > attach `OPENAI_API_KEY`;
Settings > Internet on; check `RUN` and `SPEND_STOP` in block 12; Save & Run All. The
packages land under `/kaggle/working/packages` with `ingest.log`, `manifest.jsonl`,
`calls.jsonl`, `rejections.jsonl` and `receipt.json`. To continue a run that stopped, attach
that version's output as an input before the next Save & Run All.

## Open

- **The real run**, on Kaggle as above. Then: Oz book 1's rejections classified by hand, the
  cost against the demo's $1.26, the tier spread, the roster's effect on the judge, and the
  paper and chat paths on real facts.
- The PROPOSED items in the audit: `author` and `object_is_node` on the fact, the default
  `rank`, `dossier` as a named record, the roster sentence in BUILD.md, the abstract as a
  labelled piece, plus the 09-05 docs patch and `flags`.
- Guards 4 and 5 of the resolution doc (cluster cap, merge rate per unit).
- Whether reference, license and chat-header units should be derived at all (audit decision
  13); the header unit costs one call that returns nothing.
- The reconciliation numbers (0.6/0.25/0.15, 0.85/0.35) and `ROSTER_SHOWN` 60, to rule after
  the run.

## 0.5, the night of 09-06 into 09-07

The first real run (0.4, Oz book 1: 358 entities, 38 majors, 869 facts, 74 rejected, $2.23, receipt and rejections in this folder's `receipt.json` and `rejections.jsonl` as Justin uploaded them) was read against the design, and the five papers failed to load because the public export withholds their text. Rulings 24 to 29 in `audit.md` followed within the evening. Commits, each with the battery green:

- `7b0b2c6` a withheld text is rebuilt from its PDF (private papers dataset), sha256 and units' end checked.
- `53971fd` a first schema miss is logged in `retries.jsonl`; an attribute may have a null value.
- `7f6aba0` a minor's own facts ride into the major it is tied to (`about`); `landings` decides where every fact lands.
- `12c3ebe` stage A: loose subject match, unwrapped quotes, rejected abstracts printed, adjudication progress; version 0.5.
- `e60f0a1` stage B: rolling reconciliation, the both-named rule, the roster of all majors plus sixty recent minors, verdicts replayed on resume.
- `76438c1` stage C: predicates free during derive, judged after adjudication; `predicate_raw`, `predicate_merge`.
- `d9cb559` stage D: entity abstracts and adjudications four at a time.
- `890a849` the entity prompt re-lists an established entity the unit involves.
- `2d7a307` nothing to fold, no call: adjudication skipped under four facts in one unit; the predicate judge under eight predicates.
- `8525579` the final roll-up per document and one knowledge graph per document, the 09-02 demo's way; block 14 (five papers) in the repo.

The offline battery is at 102 checks. An adversarial review of the 0.5 code (six lenses, one refuter per finding) ran after stage D; its confirmed findings and fixes are recorded below when it returns.
