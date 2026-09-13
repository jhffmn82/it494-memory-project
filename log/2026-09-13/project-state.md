# Project state, 2026-09-13

Written at the end of the repository cleanup, before the global thread starts. Every number is
from a receipt, an export or a commit; every "verified" below names what checked it. The end state
this is measured against is the one README.md and the 09-08 decision record state: a memory
backend for a desktop assistant that ingests what a person accumulates (chat logs above all),
holds document-local entities with dated, quote-backed facts and per-entity narrative cells,
attaches them to silent global parents, and serves the result as retrieval context and as a wiki.
The fall's job is the methodology, measured well enough to publish.

## The verdict first

Two of the pipeline's stages exist, run on public data for tens of dollars, and are documented
to the row. Nothing after them exists: no store, no global layer, no retrieval, no evaluation, no
wiki. The resource paper (the dataset, the extractor's method, its measured limits) is in hand.
The experience paper (what each stage costs and rejects, per corpus and tier) is mostly in hand
from receipts. The research claim (a merge-free identity tree whose cost at query time and gain
in insertion, deletion and provenance are measured; competitive accuracy on a benchmark at a
fraction of the token cost) has no number behind it yet, and the path to one runs through the
four largest unbuilt pieces. The 09-08 review said this; four days of building have made Step 1
cheaper and correct on chats without moving that line.

## What exists and runs

**Step 0, the extractor, `threadatlas-extractor 1.8`** (Kaggle `jhffmn/threadatlas-extractor`,
ran 2026-09-13). One pass over raw dataset v4: 24,071 documents (23,882 LongMemEval sessions in
500 histories, 89 Gutenberg and benchmark texts, 100 CC-BY PDFs), 251,446 units, 252,830 pieces,
$8.24, every call on the Flex tier. Chats cost nothing (no model call); a read document costs a
median of $0.0081 with its date lookups. Published as `jhffmn/it494-threadatlas-step0` with five
documentation files. Books and papers are dated by when the work was written, from the page or a
web search; every unit but 15 is dated, and no document is undated.

**Step 1, the ingestor, `threadatlas-ingestor 1.7`, frozen 2026-09-12** (Kaggle
`jhffmn/threadatlas-document-ingestor`). Books and papers go through triage, per-unit entities,
facts and cells, reconciliation with a Terra judge, folds, adjudication and verification. A chat
session is read in one Luna call, each fact tied to its turn, then one support call and
verification. Measured on the frozen design:

| what | measured | source |
|---|---|---|
| a chat session | $0.0042 to $0.0045, 8.2 sessions a minute at 16 at a time | receipts of the 09-13 runs (71 sessions, 8.7 minutes) |
| all 23,882 chat documents | about $100 to $107 and about 48 hours of Kaggle time | the line above, multiplied |
| the ten books and papers of the test set | about $5.26 for 3 Oz books, 5 papers, the Bacchae and Dandy Dick | 09-13 frozen run, $5.57 less the chats |
| all 189 books and papers | roughly $100, unmeasured; the Oz books are large and the papers small | extrapolated, not run |
| quote gate | 0 quotes off their offsets in the 09-11, 09-12 and 09-13 runs | `check_flex_run.py` |
| answer facts | all 14 LongMemEval test questions (six types) have their answer stored in a fact or a session abstract | `check_flex_run.py` on the second chats-only run |
| offline battery | 94 of 94 checks on the frozen version | `log/2026-09-08/test_ingestor.py` lineage, scratch copy |

The first Step 1 run on the 1.8 export is in progress as this is written. Every package the
global thread reads must come from it: the 1.7-export packages carry the old chat documents (one
copy per session, not per history) and the old book dates.

**Around them:** `scripts/render_package.py` renders a package as a readable document;
`log/2026-09-13/check_flex_run.py` checks a run's cost, integrity and the 14 answers;
`log/2026-09-13/extractor/` holds the 1.8 build and verification scripts; the offline battery and
the mutation tool live under `log/2026-09-08/`.

## What is verified, and what is only claimed

Verified means a script checked it on every row and its output is on disk.

- Verified in Step 0 (`verify_18.py`, the export's own checks): pieces and units tile every
  document; `unit_id` is unique and recomputes from the text; no unit mixes kinds or dates; every
  chat turn's date equals its history's; every pointer behind a boundary matched real text; the
  counts in the published docs equal the export's.
- Verified in Step 1: every stored quote is a verbatim slice at its offsets; every package is
  complete; the 14 answers are stored; the receipt's costs are the sum of `calls.jsonl`.
- Claimed and not measured: the correctness of any boundary the model chose (no gold
  segmentation); the correctness of any looked-up date beyond the two known wrong (no gold date
  table); reconciliation quality (no hand-labeled alias set exists, and the Tip/Ozma fixture has
  never been checked in a package); cell quality (read by eye on one paper); contradiction
  resolution (42 of 43 "resolved" in Oz means the judge answered, not that it answered right);
  salience; whether the stored chat facts suffice to answer a question through retrieval (only
  presence was checked, never an answer).
- Claimed and never run: everything from Step 2 on.

## Open defects

1. **The page-date gate passes a translation year.** "Plays of Sophocles" is dated 1912 from a
   line the model pointed at; the gate checks only that the year is on the line. Fix after the
   merge: reject a page date later than the author's death, or later than the source's own
   transcription notice, and fall through to the lookup.
2. **Three Scientific American articles carry wrong looked-up dates** (a 1938 article, an 1887
   range, 1881 for an 1882 supplement); the document reads 1881. A looked-up date is only as good
   as the search that found it; every date names its URL in the flags.
3. **15 units of 12 works have no date** (Homerica fragments, Pindar fragments, a newspaper
   reminiscence, three Scientific American articles).
4. **The reference PDFs were in the public repository** from its first commits: 150 files, 142 of
   them the reading list, most under licenses that forbid redistribution, plus the ASKS paper.
   Untracked at HEAD as of today; still in history (question 2 in `questions.md`).
5. **Stale Kaggle artifacts**: the 09-01 units dataset and the two 09-02 notebooks are public and
   superseded; the private reference-papers dataset is unused (question 3).
6. **Block 12 mixes histories.** The test input is one history plus the answer sessions of 13
   other questions, so a global merge over its packages spans 14 users unless it filters by
   history folder (question 5).
7. **One 8-character `doc_tag` collision** exists between two chat documents in different
   histories; ids inside a package are readable prefixes of `doc_id`, so two packages share a
   prefix. Harmless until packages are loaded into one store, where it is a key collision.
8. **Facts under a major with 4 or more facts get no support call**; adjudication consolidates
   them, so a raw fact can ride on a quote that does not state it.
9. Small: `check_flex_run.py` still names the 1.7 export and prices 19,206 sessions;
   `verify_unpack.py` replaces the old `/kaggle/working/chats` path; the extractor's chat log
   line counts the header in `turns`; the 09-06 battery is dead.

## What the global thread needs that does not exist

In the order it will hit them.

1. **The packages from the 1.8 run**, downloaded and checked with `check_flex_run.py` (whose
   needles must be re-pointed at the 1.8 paths).
2. **The scope rule**: which packages form one graph. Nothing says "one history"; the brief says
   it and no log or code does (question 5).
3. **The parent.** Its record (`name`, `kind`, `abstract`, the `instance_of` up-edges) is
   described in `docs/entity-resolution.md` and `SCHEMA.md` in prose; no schema line, no code, no
   id scheme, no rule for how its name is chosen when children disagree, no statement of what
   draws the up-edge beyond "the both-named rule" (decision 61, later cut from the node record).
4. **The read-time view** for "what is true now": a view over a parent's children applying voice
   then time on functional predicates. The functional-predicate list does not exist; without it
   LongMemEval's knowledge-update questions measure nothing (09-08 forward plan, ruling 2 and
   the list, never locked).
5. **A gold set for attachment accuracy.** LitBank is dead (96 of 100 documents are two chunks);
   BookCoref was proposed on 09-08 and not ruled; the hand-labeled Oz alias set (about twenty
   characters, half an hour) was called for on 08-28 and never written.
6. **The store.** No SQLite schema, no loader from packages, no FTS5, no embedder (bge-small
   through fastembed is a plan; the ingestor stores no vector). The `data/export` and
   `data/packages` folders are gitignored placeholders.
7. **Retrieval.** No entity lookup, no cell retrieval, no context assembly, no arm. The query
   fixture (decision record section 4) is a list of question shapes with no gold answers.
8. **An evaluation harness for LongMemEval**: question file in, retrieval over the packages of
   that question's history, an answer, a judge against the benchmark's answer. `check_flex_run.py`
   checks presence, not answering. The benchmark's `question_date`, `has_answer` and
   `answer_session_ids` are deliberately absent from the export and must be read from
   `longmemeval_s.json`.
9. **The wiki.** `render_package.py` renders one document; there is no entity page, no
   assembled-versus-generated pair, no ship check.
10. **The ASKS comparison**, object by object, which the 09-08 record required before the
    global layer is implemented. Not written.

## Where the paper stands

**The track and the dates.** A resource-and-experience paper on arXiv cs.CL, freeze Nov 15,
submission Nov 16, build stop Oct 31, Fang's review Nov 3 to 9. The slate was priced on 09-08 at
69 to 118 hours against about 64, and the 8-hour week is unverified. Today is Sep 13; open block
1 ends Sep 27; the global merge is due Wednesday Sep 16.

**What is publishable today.** The dataset (DOI not yet minted; the plan says Zenodo by Nov 10),
the extractor's method and its measured limits, the ingestor's measured cost and rejection rates
per corpus and tier, and the merge-free architecture as a stated design position. That is the
floor the 09-08 review named, and it is real: it needs writing, not building.

**What is not.** The central table. No arm has returned a number, and the four pieces between
here and one number (store, tree, retrieval, arm) are the largest unbuilt pieces. The review's
recommendation, decide the floor explicitly now, was not taken up in any log.

**Novelty.** Conceded by design (reviewer question 1): the contribution is a working merge-free
backend and a measurement of what each mechanism buys. The one differentiation kept is the object
that accumulates, source-local narrative states of an entity through ordered units, against ASKS,
GraphRAG, LLM-Wiki, KGGen and PAGER. It has not been searched or compared object by object, and
the tree formulation has not been searched either (review decision 6). Neither can go in the paper
unsearched.

**The plan and the build have diverged.** The 09-08 plan makes LongMemEval the first benchmark to
cut. The last four days went entirely into chats: the chat unit shape, per-history dating, the
one-call reading, the 14 answer questions, the freeze. The reason is sound (chat memory is the end
state, and LongMemEval is the only conversational benchmark on the list), but the plan on file
says the opposite, and LongMemEval's own gate, the functional-predicate list or an answering
harness, is still unbuilt. One of the two has to change, and it should be the plan: state that
LongMemEval is the spine, GraphRAG-Bench the second arm, and NarrativeQA cut.

**Baselines.** Zep is the baseline on LongMemEval (63.8 percent with gpt-4o-mini, 71.2 with
gpt-4o, against full-context 55.4 and 60.2). Nothing here answers a question yet, so no
comparison exists. The judge discipline (the scorer never shares a tier with a writer) is stated
and unbuilt.

**Advisor and mechanics.** The 09-09 weekly reported the memory project to Dr. Fang, and README
says he approved the topic change on Aug 28, so the survey-versus-memory scope question of
August is closed in practice; no document records him saying so. The arXiv endorsement email
was "still unsent" on 09-08 and no later log mentions it. Its status is unknown.

**The academic risk, plainly.** The work that exists is careful, measured and reproducible, and
it is the kind of work a resource track publishes. The work the ambitious paper needs has not
started, and the calendar has three weeks of exams in the middle of it. A complete modest paper
beats a thin ambitious one; the choice is still open and should be made before the global thread
spends its first hour.

## The repository after the cleanup

- Logs exist for every day from 09-02 to 09-13; 09-09, 09-11 and 09-12 were written today from
  commits and receipts; the index lists them all. Logs are snapshots and were not edited.
- `docs/rulings.md` is the ledger: every design ruling, its date, its log, and what superseded
  it. Three rulings that had lived only in code or chat are now written down (every unit dated,
  the date forms, one Luna call per session), and one logged ruling is marked reversed by the
  code (the 09-10 "not the one-reading shortcut").
- Master documents brought to the code: SCHEMA.md and BUILD.md (PROPOSED), docs/extractor.md and
  docs/ingestor.md (rewritten), docs/entity-resolution.md, README.md, RESEARCH.md, docs/proposal,
  evaluation-corpus, references, reports/pipeline-and-outline, the data/raw docs, the Step 0 docs.
  No em dash remains in any of them; no copyrighted modern fiction is named in any public file.
- `archive/` holds the private-papers scripts; the 150 reference PDFs are untracked.
- `questions.md` beside this file lists the nine rulings left open.
