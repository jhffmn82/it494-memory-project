# Hostile review of it494-memory-project at 0edcd23 (branch claude/kg-rag-cc-corpus), 2026-09-13

Read-only. Every line number is from the tracked file at HEAD. "Code" means `notebooks/threadatlas-extractor.py` (LOADER 1.8) and `notebooks/threadatlas-ingestor.py` (INGESTOR 1.7). Ordered most serious first. Categories with nothing to report are stated at the end.

## 1. The rulings ledger cites files the same day's cleanup deleted

- **docs/rulings.md:59** and **docs/rulings.md:78**: the "recorded" column reads `chat; log/2026-09-13/extractor/make_18.py` and `chat; log/2026-09-13/extractor/block0_unpack.py`.
- Evidence: `git ls-files` has no `log/2026-09-13/extractor/`; commit 005f19c ("The repository reduced to what a person reads") deleted `log/2026-09-13/extractor/{block0_unpack,check_18,make_18,numbers_18,verify_18,verify_unpack}.py` and `log/2026-09-13/check_flex_run.py`. The ledger was written the same day. Its one job is "where it is recorded"; two of its 09-13 rulings point at nothing a reader can open.
- Fix: cite `code (extractor 1.8: block 0; date_works)` the way line 60-61 already do.

## 2. BUILD.md states the opposite of the reconciliation guards the code enforces, and the ruling behind the code is not in the ledger

- **BUILD.md:57-60**: "The guards in `docs/entity-resolution.md` are binding: a different verdict never vetoes a later one reached on more evidence, every decision records its evidence and stays revocable, cluster size is capped, and the pairing rate is watched".
- Evidence: `threadatlas-ingestor.py:1342-1348` `ineligible()`: "Two clusters are never paired when they hold a local from one unit ... or a pair the judge ruled different (decisions 44 and 51)"; `:1470-1474` a later "same" against a ruled-apart pair is refused. A "different" verdict is a permanent veto. No cluster cap and no pairing-rate watch exist anywhere in the file (grep for cap/size/rate: nothing); `log/2026-09-06/audit.md:52` recorded both as "Not done" and `log/2026-09-08/review.md:47` flagged the same BUILD sentence. Decision 44 (`log/2026-09-07/decisions-ingestor-0.7.md:32-41`) is the standing rule and has no line in `docs/rulings.md`.
- Fix: rewrite BUILD.md:54-61 to the two pruning rules and the round-by-round queue; add decision 44 to the ledger under "Entities, identity"; strike "capped" and "watched" or mark them unbuilt.

## 3. SCHEMA.md still claims a controlled predicate list and a type table the code never had, against a ruling the ledger says not to raise again

- **SCHEMA.md:169-172**: "Predicates come from a small controlled list with a table of which subject and object kinds each may join, which catches ... a fabricated relationship carrying a perfectly real quote." **SCHEMA.md:224-225** (under "What the code enforces"): "6. A relationship that violates the predicate type table is rejected before it is stored." **docs/references.md:12** lists the type table as a schema decision with no "not in use" note (line 16 gives one for `rank`).
- Evidence: `docs/rulings.md:86`: "Predicates are the model's own strings; there is no controlled list at Step 1 and predicates are never merged or renamed | stands; ruled repeatedly". `docs/ingestor.md:81-82`: "Predicates stay as the model wrote them, in snake_case." Code: `threadatlas-ingestor.py:521-530` `snake_case`, `:1092` `predicate = snake_case(f["predicate"]) or "related_to"`; no table, no kind check on predicates. SCHEMA.md:150-152 and BUILD.md:66-67 also say "the functional list is maintained by hand"; `log/2026-09-13/project-state.md:118` says the list does not exist.
- Fix: replace SCHEMA.md:169-172 and rule 6 with the ruling; annotate references.md:12 "not built; predicates are free strings (09-06)"; state the functional list as unbuilt spring work.

## 4. Ledger says front matter is triage's decision; the code excludes it by rule; docs/ingestor.md documents the code

- **docs/rulings.md:89**: "Triage may not leave out more than half a document; front matter is triage's decision, not a rule | ... | stands".
- Evidence: `threadatlas-ingestor.py:145` `BOILERPLATE = ("front_matter", "license")   # never the work, whatever the document`; `:2140` `excluded = {u["kind"]: ... for u in doc["units"] if u["kind"] in BOILERPLATE}` before triage is asked. `docs/ingestor.md:22-23`: "front matter and license go by rule". The ruling the ledger cites, `log/2026-09-07/ingestor.md:160-163`, says "A hard exclusion I had written was reverted." The code re-reverted it and no log records a ruling.
- Fix: find the ruling or mark the line "reversed by code (BOILERPLATE) with no ruling logged"; either way the ledger and docs/ingestor.md must agree.

## 5. SCHEMA.md contradicts itself on ids, and the contradiction was flagged five days ago

- **SCHEMA.md:205**: "1. Raw text is never edited. Ids are content hashes, so a corrected split changes one id instead of every id after it." vs **SCHEMA.md:5-6**: "document and unit ids are content hashes, entity and fact ids are readable and minted per document (2026-09-08)".
- Evidence: `docs/rulings.md:94`; `threadatlas-ingestor.py:1952-1953` `node_id` = `f"{doc_tag(doc)}:n{entity['index']}"`, `:1213` fact ids `:u<pos>:f<n>`. `log/2026-09-08/README.md:62-64` proposed fixing exactly this sentence. `log/2026-09-13/questions.md:25` says of the accepted SCHEMA commit "every sentence traces to the code that ran".
- Fix: rule 1 becomes "document and unit ids are content hashes; entity and fact ids are readable and document-local".

## 6. Hash-based abstract staleness is claimed in two master documents; nothing hashes

- **SCHEMA.md:221-223** rule 5: "rebuilt whenever the hash of its children changes, and staleness is that hash comparison, never a guess." **BUILD.md:63-64**: "Summaries rebuild only when the hash of their inputs changes, and staleness markers are stripped before hashing".
- Evidence: `docs/rulings.md:164` lists `children_hash` under "Records dropped" (09-07, dcd11c0). `grep children_hash|stale` on the ingestor: nothing. `log/2026-09-08/README.md:65-66` and `review.md:63,167` asked for a ruling ("field back, or the two sentences change"); none was given and the sentences survived the 09-13 cleanup.
- Fix: delete both, or say "an abstract is written once per package; no rebuild mechanism exists".

## 7. No license file at the repository root

- **git ls-files**: no `LICENSE`, `COPYING` or `NOTICE` at the root. The tree carries 100 CC-BY PDFs, 89 public-domain texts, two MIT benchmark folders, notebooks, scripts and docs.
- Evidence: `dataset/step0/PROVENANCE.md:49-50` and `dataset/step0/README.md:113` say "Packaging, schema, the split plan and every derived field are MIT, copyright 2026 Justin Hoffman", but that is a statement about the Kaggle dataset; nothing in the repository says what license `notebooks/`, `scripts/`, `docs/` or `reading/` carry. A public reader (or arXiv/JOSS, which RESEARCH.md:196-197 names) has no grant to reuse the code.
- Fix: add a root `LICENSE` (MIT for code and docs) and a one-paragraph `data/raw/` and `data/benchmarks/` license pointer.

## 8. NarrativeQA: the docs say 11 works and 319 questions; the tracked data and script say 12 and 345

- **README.md:47** "NarrativeQA reference answers on 11 owned works"; **RESEARCH.md:94** "the 319 questions over 11 works we own"; **docs/proposal.md:108** "319 human-written questions over eleven books"; **docs/evaluation-corpus.md:16** "11 works ... 319 questions".
- Evidence: `data/benchmarks/narrativeqa/documents_ours.csv` has 12 rows, one of them `chinese 9603 Dream of the Red Chamber`; `qas_ours.csv` has 345 rows, 26 of them for that work; `scripts/fetch_benchmarks.py:21-22` "the 345 questions covering 12 works already in data/raw/". `log/2026-09-04/inventory.md:60-61` ruled chinese/ out and "NarrativeQA becomes 11 works and 319 questions"; the csvs and the script were never cut. `log/2026-09-08/review.md:83-84` reported the same split. The manifest hashes (`data/benchmarks/manifest.json`) pin the 12-work files.
- Fix: drop the chinese row and its 26 questions from both csvs, re-hash them in `manifest.json`, and fix fetch_benchmarks.py:21; or say 12/345 with one work excluded at evaluation.

## 9. README says the Step 0 docs are byte-identical to Kaggle; the same day's questions file says they are not

- **README.md:139**: "dataset/step0/ the published Step 0 dataset's docs, kept byte-identical to Kaggle".
- Evidence: `log/2026-09-13/questions.md:55-62` (question 4): the five docs now say "every unit dated where a source gives a date (15 are not)", the quick start lost its lambda and the em dash is gone, "The published 1.8 version still carries the old text"; questions.md:6-7 leaves question 4 for Justin's CLI. `dataset/step0/README.md:5` and `dataset-metadata.json` carry the new text.
- Fix: "prepared for the next docs-only version; the published copy lags until republished", or republish.

## 10. "The user is a standing major on every user turn" is not what the 09-12 reader does, and the ledger dates it three ways

- **SCHEMA.md:184-185**: "In a chat the user is a standing major on every user turn (2026-09-10)". **docs/rulings.md:135** dates the ruling 09-12 and records it at "log/2026-09-11/README.md ruling 9; log/2026-09-10 (chat)"; **docs/rulings.md:97** dates the same edit 09-10.
- Evidence: `threadatlas-ingestor.py:1226-1229`: a turn's entities are `dict.fromkeys(f["subject"] for f in rec["facts"])`, so `user` exists only in a turn where a kept fact names it; a user turn with no kept fact yields no user entity. No "standing" code exists (grep). The per-turn user-major code of 09-10 went with the one-call reading (rulings.md:97 "cells-as-abstracts and the rest superseded 09-12").
- Fix: SCHEMA: "the user is a major wherever a kept fact names it"; ledger: one date per ruling.

## 11. SCHEMA.md's record lines do not match the package

- **SCHEMA.md:121** `cell  cell_id, node_id, unit_id, text, tier, provenance`: the code writes no `cell_id` (`threadatlas-ingestor.py:1981-1982`, `:1989-1990`).
- **SCHEMA.md:118-120** fact record lacks `direction`, `author`, `object_is_node`, all written at `:2048-2056` (proposed for SCHEMA on 09-06, `log/2026-09-06/audit.md:29`, never taken).
- **SCHEMA.md:116-123** lists no `adjudicated_fact` or `attribute` record; the package writes both (`:2004-2005`, `:2009-2010`) with `from_facts` and no quote, while **SCHEMA.md:113-114** says "nothing unsourced can exist in the store". `docs/ingestor.md:95-97` lists them correctly.
- Fix: bring the four record lines to the writer, and say that adjudicated facts and attributes are Terra's consolidation citing raw fact ids.

## 12. SCHEMA.md promises a `produced_by` edge that is never written

- **SCHEMA.md:50-51**: "with `has_unit` edges in order, `produced_by` to its author, and `appears_in` edges".
- Evidence: `threadatlas-ingestor.py:1970-1971` writes `appears_in` and `has_unit` only; `log/2026-09-06/audit.md:35-37` said so on 09-06.
- Fix: drop `produced_by` or mark it as the global layer's.

## 13. SCHEMA.md gate 4 and BUILD.md describe a rejection path the extractor does not have

- **SCHEMA.md:213-216**: "Count: pieces ... match the table of contents where one exists, else markers are monotonic with no gaps, else the document is one piece." **BUILD.md:15-16**: "a document the gates reject is stored as one unit and flagged, never dropped."
- Evidence: `threadatlas-extractor.py:850-871` `gates()` returns flags only; `:856-857` a contents mismatch is the flag `count:`; `:894-899` the best flagged answer is kept with its pieces; only `TooLong` (`:900-902`) or an exception (`:1374-1381`) yields one piece. No "markers monotonic" step exists (the model points by line number, `docs/extractor.md:54-58`). `docs/extractor.md:89-91` has it right: "a flag, never a drop".
- Fix: restate gate 4 and BUILD.md:15-16 from extractor.md.

## 14. Present-tense storage and read-time claims for things that do not exist

- **SCHEMA.md:3-4** "Storage is SQLite and JSONL in a single folder, no server"; **SCHEMA.md:207** "2. Nothing is overwritten. Supersession and merges resolve at read time"; **BUILD.md:71-84** alias lookup, greedy context assembly, byte-for-byte replay, the embedding sidecar "verified against ids on load".
- Evidence: `log/2026-09-13/project-state.md:124-127`: "No SQLite schema, no loader from packages, no FTS5, no embedder"; `docs/rulings.md:156` "no reader is built"; the ingestor writes JSONL only (`:2106`).
- Fix: one sentence at the top of each section: "the store and the reader are unbuilt; this is their contract".

## 15. README.md and docs/execution-plan.md give opposite cut orders and different hour budgets

- **README.md:87** "roughly 64 hours"; **README.md:105-115** cut order: "First cut: the LongMemEval parity arm and update band ... 5. Then: NarrativeQA"; **README.md:76-77** "Sep 21 Store and pipeline working over Oz book 1; Sep 27 Three-tier pilot done".
- Evidence: `docs/execution-plan.md:12-22`: LongMemEval "the spine, committed", NarrativeQA "cut", GraphRAG-Bench "stretch", "33 to 46 build hours remain"; `:109-110` Sep 16 store on one history, Sep 27 fourteen questions on three arms. `log/2026-09-13/project-state.md:162-168`: "the plan on file says the opposite ... One of the two has to change". execution-plan.md is PROPOSED, so today two master documents disagree.
- Fix: on the slate ruling, replace README.md:85-118 with a pointer to execution-plan.md; until then mark README's slate "superseded pending ruling".

## 16. docs/entity-resolution.md names a rejected gold set and a reversed decision as current

- **docs/entity-resolution.md:294**: attachment accuracy "scored against LitBank's gold coreference"; `docs/evaluation-corpus.md:113` rejects LitBank; `project-state.md:121` "LitBank is dead"; `questions.md:106-107` lists it as unruled since the 09-08 review (review.md:171 asked for the one-word fix).
- **docs/entity-resolution.md:339-340**: "61. A node records whether its document ever named it ... That rule is now what draws the up-edge." `docs/rulings.md:147`: decision 61 "reversed hours later (dcd11c0 cut `named`)"; the node record at `threadatlas-ingestor.py:1966-1968` has no `named`.
- Fix: BookCoref; strike the decision-61 paragraph or mark it reversed.

## 17. A PROPOSED section from 09-08 still sits unruled inside RESEARCH.md

- **RESEARCH.md:221-256**: "PROPOSED 2026-09-08: the model tiers are the user's own, behind the seam ... PROPOSED until Justin rules"; **:223** "the two model interfaces (`generate`, `embed`)".
- Evidence: `BUILD.md:30` "embed(texts) belongs to the serving side and is not built"; `docs/rulings.md:92` the ingestor has no `embed()`. No ledger line rules or rejects the section; `README.md:54-59` says proposals belong in `log/` until ruled.
- Fix: rule it, or move it to `log/2026-09-08/` and leave one sentence.

## 18. The ledger's line citations into three logs are off, and one cites the wrong file

- **docs/rulings.md:18-23,35** cite `inventory.md:73-75, 76-81, 82-83, 84-87, 92-93, 96-97, 88-89`; the rulings are at `log/2026-09-04/inventory.md:76-78, 79-84, 85-86, 87-89, 93-94, 97-98, 90-91` (three lines off each).
- **docs/rulings.md:36,41,53,55,70** cite `log/2026-09-05/README.md:43-48, 70-71, 60-62, 63-64, 65`; the rulings are at `:44-49, :71-72, :59-61, :62-63, :64`.
- **docs/rulings.md:118** cites `log/2026-09-07/ingestor.md:167-168`; the `self_reference` ruling is at `:170`.
- **docs/rulings.md:86** cites `decisions-ingestor-0.5.md 12, 32, 39, 41`; item 32 of that file (`log/2026-09-06/decisions-ingestor-0.5.md:187-195`) is the rolling-reconciliation reversal; the predicate ruling numbered 32 is in `log/2026-09-06/audit.md:119`.
- The other spot-checks resolve: :16 (09-02/README.md:24), :49-52 (09-04/README.md:24-31, 117-121), :57,72-77 (chat-rulings.md), :95-96,158 (decisions-ingestor-1.7.md), :97-107,121,134 (09-11 and 09-12 rulings), :117,119,132,148 (0.8 R1-R6), :141,155 (09-03/README.md:26-54, 149-163), :175 (devlog:157-161), :176 (threadatlas-decision.md:28-37).
- Fix: re-point the cited ranges.

## 19. Rulings in the 09-06 to 09-10 logs that a builder needs and the ledger lacks

- Decision 44, `log/2026-09-07/decisions-ingestor-0.7.md:32-41`: never pair clusters sharing a unit; never re-pair a ruled-different pair. In code (`ineligible`), contradicted by BUILD.md (item 2).
- Decision 57, `decisions-ingestor-0.7.md:139-142`: the scored candidate rows stay in the package as the audit log. In code (`:1515-1517`); the ablation replay (RESEARCH.md:92) depends on it.
- `log/2026-09-07/ingestor.md:164-165`: triage of references and appendices stands as it is, no rule. In code (BOILERPLATE excludes only front_matter and license).
- `log/2026-09-10/chat-rulings.md:49-50` ruling 6: the output schema must carry Gemini, Grok, Claude and OpenAI chats. Not in the ledger, not marked superseded.
- `log/2026-09-08/review.md:158-171` rulings 4 (the functional-predicate list) and 6 (`children_hash`): requested, never ruled, not listed as open anywhere but execution-plan.md:127.
- Fix: one line each.

## 20. log/README.md, edited in the cleanup commit, links to two files that commit deleted

- **log/README.md:30** `[threadatlas_blocks_3_to_9.py](2026-09-04/threadatlas_blocks_3_to_9.py)`; **log/README.md:38** `[docs-rulings-2026-09-05.patch](2026-09-05/docs-rulings-2026-09-05.patch)`.
- Evidence: both deleted in 005f19c, which also changed log/README.md (+5). `log/README.md:40-41` and `:105-106` name `test_review.py`, `test_verify.py`, `test_run1.py`, `py_to_ipynb.py`, `check_flex_run.py` and `extractor/`, all gone; the note at `:5-7` covers names, not links.
- Fix: unlink the two; the index is maintained, not a snapshot.

## 21. Broken relative links in tracked markdown (all in log/; listed, not to be corrected)

Caused by 005f19c today: `log/2026-09-06/README.md:29` (run15-read-documents.jsonl), `:37` (test_ingestor.py); `log/2026-09-06/extractor.md:202` (run15-read-documents.jsonl); `log/2026-09-06/ingestor.md:134` (review-findings.json); `log/2026-09-07/ingestor.md:14` (../2026-09-06/test_ingestor.py); `log/2026-09-04/README.md:10` and `:173` (threadatlas_blocks_3_to_9.py). Pre-existing: `log/2026-09-05/README.md:304` (ingestor-brief.md, which lives in 09-06); `log/2026-09-06/extractor.md:150-151` (run-read-documents.jsonl, run-chat-summary.json, never tracked). No broken markdown link outside log/.
- Fix: none for the snapshots; a line in log/README.md:5-7 saying links, not only names, may be dead.

## 22. reports/pipeline-and-outline.md was deleted with no ruling covering it

- **git ls-files reports/**: only `2026-09-09-weekly.md`. `log/2026-09-13/README.md:91` and `project-state.md:196` list "reports/pipeline-and-outline" among the master documents brought to the code that day; 005f19c deleted it hours later. `README.md:144` says reports/ holds "the weekly reports to the advisor"; the 09-08 weekly was removed in c3bee9d.
- Evidence: `docs/rulings.md:184` covers "test batteries, build tooling, the reference PDFs and the archive of superseded scripts"; a report is none of those.
- Fix: restore it, or add a ledger line saying why a master document left.

## 23. .gitignore is duplicated and points readers at untracked scripts

- **.gitignore:43-52** and **:53-62**: the "2026-09-13: the public tree holds only what a person reads" block is pasted twice, verbatim.
- **.gitignore:32** "rebuilt locally by scripts/rebuild_export.py"; **:41** "Fetch with scripts/fetch_papers.py": both untracked (moved to archive/ in 52b6732, then archive/ untracked in 005f19c).
- Fix: dedupe; say "on the author's machine".

## 24. Master documents refer to files a reader cannot open

- **RESEARCH.md:7** "bibliographic corrections in the two survey JSONs" (reading/*.json, gitignored). **reading/reading-list.md:3** "`papers/MANIFEST.md`" and "reference copy in `papers/`" (untracked). **docs/references.md:28-30** "the local PDF is byte-identical to the CEUR copy ... `angles2017-graph-query-foundations.pdf`" (untracked). **log/2026-09-13/project-state.md:60-67** defines "Verified" as "a script checked it on every row and its output is on disk" and cites `verify_18.py`, `check_flex_run.py` and the battery; none is public, so a reader cannot re-run any verification the master documents rest on.
- Fix: say "on the author's machine, untracked" at each; consider tracking the two verification scripts (they are what makes "verified" checkable).

## 25. docs/extractor.md's input table misdescribes the raw dataset

- **docs/extractor.md:23-28**: "one folder per corpus, each with a `manifest.json` recording every file's source URL, byte count and sha256" then `longmemeval | 25,112 | chat sessions in 500 histories ... (written by block 0)`.
- Evidence: `data/raw/dataset-metadata.json` and `data/raw/SOURCES.md:296`: v4's `longmemeval/` holds 19,206 session files plus `longmemeval_s.json`; the 25,112 files are block 0's output under `/kaggle/temp/chats` (`log/2026-09-13/README.md:33-35`), with no manifest.
- Fix: two rows: what the mount holds, what block 0 writes.

## 26. Smaller disagreements

- **docs/execution-plan.md:35** "packages/longmemeval/<history>/<session>/": `threadatlas-ingestor.py:1944-1949` builds `OUT/<parts[-2]>/<stem>/<stem>.jsonl`, so a chat lands at `packages/<history>/<session>/`, no `longmemeval` level.
- **docs/evaluation-corpus.md:3** "2026-08-28, amended 2026-08-30 and 2026-09-04" heads a file whose lines 89 and 117-124 describe 09-13.
- **docs/ingestor.md:3-4** "Its first run on the 1.8 export is in progress on 2026-09-13": a transient state in a master document.
- **data/raw/SOURCES.md:2-3** "37 of the 81 files now on disk"; **:231** "Water Margin is present, in Chinese, as `08_23863.txt`": chinese/ left on 09-04 (`docs/rulings.md:17`); the file is not in the dataset. `data/raw/USAGE.md:132-163` names six chinese/ files (qualified as "left with chinese/").
- **reports/2026-09-09-weekly.md:39** "141 reference papers" vs **docs/rulings.md:19** and **questions.md:29** "142".
- **docs/rulings.md:24** dates the ThreadAtlas naming 09-08; `log/2026-09-08/threadatlas-decision.md:3` says the review was 9 September and `log/2026-09-09/README.md:6` says the rename landed 09-09.
- **README.md:75** Sep 14 row: "Chinese remains. Superseded Sep 4" in one cell; chinese/ was removed Sep 4.
- **dataset/step0/README.md:100** and **METHOD.md:53** print the BC years with U+2212 (`−0749`); the data and SCHEMA.md use ASCII `-`.

## 27. Tracked files a person would not read, and files a reader needs that are missing

- Not read by a person, still tracked: `log/2026-09-05/old-design-run.splits.log` (the matching `.jsonl` was untracked); `log/2026-09-06/extractor-final-splits.log`, `extractor-run-347794765.txt`, `extractor-final-receipt.json`, `run15-receipt.json` (README.md:145 calls receipts part of the log, so these are defensible; the two `.log` files are raw run output, 09-06's is named as "the run as it happened").
- Missing that README names: nothing. Every path in README.md:126-145 resolves. `scripts/` holds the six scripts README:142 describes.
- Missing that a reader needs: a root LICENSE (item 7); the verification scripts (item 24).

## 28. Integrity and licensing, as a public reader sees it

- No root license (item 7).
- 150 reference PDFs "most under licenses that forbid redistribution" remain in every commit before 2026-09-13 (`log/2026-09-13/questions.md:27-36`, `project-state.md:88-90`); ruled (a) "leave history" on 09-13 (`docs/rulings.md:181`). A public reader can still clone them. Noted, not re-argued.
- `data/raw/kg-rag-cc/manifest.json`: all 100 papers `cc-by`, each with DOI and source URL; `data/raw/kg-rag-cc/README.md` states the attribution duty. Clean.
- `data/raw/graphrag-bench/manifest.json` and `data/benchmarks/graphrag-bench/LICENSE`: MIT, sha256 per file. Clean.
- The NarrativeQA csvs carry 26 questions over a work whose text is not in the corpus (item 8): an evaluator run as shipped scores against text the repo does not hold.

## Categories with nothing to report

- **Em dashes (U+2014)** outside log/ and data/benchmarks: none in any markdown, JSON or script prose. The only occurrences are `notebooks/threadatlas-ingestor.py:493` and `notebooks/threadatlas-ingestor.ipynb:545`, inside the `REPLACEMENTS` table that maps `—` to `-` for quote normalisation (data the gate needs, not prose). If the rule is literal, build it from `chr(8212)`.
- **Harry Potter / Rowling / Hogwarts** outside data/ and log/: none. The hit inside `data/benchmarks/graphrag-bench/novel.json` is the word "prowling" (false positive); no GraphRAG-Bench novel is a modern work (all 20 are the benchmark's pre-1900 contexts, MIT-packaged). No other copyrighted modern fiction is named in any non-log, non-data file.
- **Numbers that agree everywhere**: 24,071 / 23,882 / 189 / 89 / 100 / 251,446 / 252,830 / $8.24 / median $0.0081 / 6 escalations / 156+237+12 = 405 works / 1,230 empty sessions / 70 empty turns / 15 undated units in 12 works / 103 of 189 flagged / 135 pointers, 50 dropped; the dataset README's per-corpus table sums exactly; block 12 = 53 + 18 answer sessions of 13 questions = 71 (code ANSWERS has 18 entries, 13 distinct questions); 81 documents / $5.57 / 1,696 calls; $0.0042-$0.0045 x 23,882 = $100-$107; prices Luna 0.10/0.60, Terra 1.00/6.00 Flex; CAP_WORDS 4000, SHORT_WORDS 100, RETRY_MAX_TOKENS 80,000, SPEND_STOP 25, DOCUMENTS 6, FANOUT 8, WORKERS 4, SESSION_WINDOW 40,000, SIMILAR_ENOUGH 0.35, ADJUDICATE_MIN_FACTS 4, VERIFY_BATCH 60, blocks 12-15 budgets 15/12/8/6, seed 494. Terra judges, folds, writes entity abstracts and adjudicates; Luna reads sessions, supports and corrects (docs/ingestor.md:56-57 is right).
