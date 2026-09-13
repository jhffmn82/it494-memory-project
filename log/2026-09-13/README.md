# 2026-09-13: the frozen run, extractor 1.8, git caught up, the cleanup

Times UTC unless marked local (CDT, UTC minus 5).

## The frozen Step 1 run on the 1.7 export (06:18 to 06:27, block 15's window)

The full notebook frozen on 09-12 (all blocks on, `threadatlas-ingestor 1.7`): 81 documents (71
sessions, 3 Oz books, 5 kg-rag-cc papers, the Bacchae, Dandy Dick), 1,696 calls, $5.57, 3 schema
retries all recovered, 0 quotes off. Chats $0.0042 a session. The answer check first reported 12
of 14 questions hit; on a second look all 14 are answerable: the Korean "three" was stored as a
stated fact ("I've tried three different ones recently", the needle had wrongly required "Korean"
in the same fact), and the Ancient Civilizations visit is in the session abstract, whose document
carries the date. So a merge-side retrieval that indexes session abstracts and fact quotes and
joins each to its document's date can answer all 14; that is a merge requirement, not a Step 1
change. The 96 `self_reference` rejections (80 in one session) are assistant list items written
as "X is_theme X", refused rightly. Notebook recovered into git as 06de67d.

## Every unit dated (Justin, morning, local)

Justin: his intent was always that every unit and every fact is dated. The 09-10 wording that
left a session placed on several dates undated was not an informed ruling and is not to be
cited. Measured: 3,944 of 19,206 sessions were undated because each appears in 2 or more
histories with a different date in each (8,620 copies in all); every one of the 500 histories has
7 to 33 of them (mean 17.2), and 8 answer sessions are among them. Turns in LongMemEval have no
times; dates are per session, per history. Books are dated by when the work was written, BC and
approximate included (the Bacchae c. 405 BC, the Iliad c. 8th century BC), never the translation.
Dates are per unit; the document takes its earliest.

## Raw dataset v4 (15:09) and extractor 1.8 (16:48 last run, published 17:46)

- v4 adds `longmemeval/longmemeval_s.json` and its manifest entry. The CLI needs the `data\raw`
  backslash path; with a forward slash the version silently fails to be created.
- 1.8 was built in scratch as a patch over the uncommitted 1.7 (`make_18.py`): block 0 unpacks
  the 500 histories into 25,112 files under `/kaggle/temp/chats` (the first run wrote them to
  `/kaggle/working`, and 25k output files made the notebook impossible to list or download); chat
  turns carry their own timestamps; empty sessions and turns skipped and counted; a `works` list
  in the prompt, each work dated from its page or by one Responses API web search on Luna, the
  source recorded in the flags; a group is cut where the date changes; every call on Flex. The
  offline check `check_18.py` passed with the lookup stubbed.
- The run: 24,071 documents, 251,446 units, 252,830 pieces, $8.24. `verify_18.py` passed except
  for the known wrong dates (Sophocles 1912 from the page; three Scientific American articles
  from bad lookups). 15 units undated, each explained in the flags; no document undated. One
  8-character `doc_tag` collision between two histories.
- Published as the new version of `jhffmn/it494-threadatlas-step0` with the five docs rewritten
  from the export. Committed as f0d38ad with the build and verification scripts under
  `log/2026-09-13/extractor/`.

## Block 12 by path (e15623d)

Since 1.8 a session reused by several histories has a copy in each under the same title, so the
ingestor selects sessions by path: the history folder `chats/longmemeval/gpt4_2ba83207/` plus the
(question, session) answer paths of the 13 other questions, 71 sessions. Prune step p_history
(24-history-folders.diff), battery 94 of 94. Not yet run on the day's export when committed.

## Git caught up (13:06 to 13:11 local)

Nothing since fa48997 (09-09) had been committed. In order: extractor 1.7 as it ran with the Step
0 docs as published and the 09-10 logs (f00dcdb); the ingestor as it ran 09-10, 09-11 and 09-13
(59180a1, 1c4132d, 06de67d); the ingestor prepared for 1.8 (e15623d); the answer check
(f8a8ab2); the merge of ingestor-1.7 (84d344c); extractor 1.8 (f0d38ad); the merge of master's
09-09 weekly (4bf0177). Branch `claude/kg-rag-cc-corpus`, pushed.

## The first Step 1 run on the 1.8 export (started about 18:07)

The notebook of e15623d, on Kaggle, in progress through the evening. Its packages are the global
merge's input. Result to be recorded by the thread that reads it.

## The cleanup (afternoon and evening, local)

Rulings (Justin):

1. The daily logs are snapshots in time, not persistent truths. A log whose summary is wrong as
   of today is not edited or annotated. The master documents represent current truth.
2. Like the global merge: every fact is stored as it was true, and recency on contradictions
   forms the global truth. The narrative of how a ruling changed is tracked, so that past
   mistakes are not revisited. `docs/rulings.md` is that record.
3. Questions are brought one at a time; while he is away, the work proceeds and the questions
   are logged for the end (`questions.md`).

Done, each as its own commit on `claude/kg-rag-cc-corpus`:

- Four readers inventoried every markdown file in the repository against the code and the
  export (reports in the session scratchpad, not committed): what each claims, whether it is
  still true, and where each ruling is recorded. Findings: no log for 09-09, 09-11 or 09-12;
  three rulings recorded nowhere but code or chat; one logged ruling reversed by code with no
  log; the 150 reference PDFs in public history; two public mentions of copyrighted fiction.
- Logs written for 09-09, 09-11 and 09-12 from commits and receipts; the index lists every day.
- `docs/rulings.md`, the ledger.
- SCHEMA.md and BUILD.md as PROPOSED commits; docs/extractor.md and docs/ingestor.md rewritten
  for 1.8 and the frozen 1.7; docs/entity-resolution.md, README.md, RESEARCH.md, docs/proposal,
  evaluation-corpus, references, reports/pipeline-and-outline, the data/raw docs and the Step 0
  docs brought to the code. No em dash in any master document.
- `archive/`: the private-papers scripts moved; the 150 reference PDFs untracked and ignored.
- `project-state.md`: the audit. `questions.md`: nine rulings left open.
