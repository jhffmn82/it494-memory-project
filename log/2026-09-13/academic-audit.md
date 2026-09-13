# Academic audit, 2026-09-13: the proposal reviewed, the project measured against Justin's goals

Verdict first, no silver linings. Companion to `project-state.md` (what exists and what is
verified) and `docs/execution-plan.md` (what to do about it). Every claim below names its
source; where the source is a chat, it says so. Revised the same night after an adversarial
review (`attack-assessment.md`, `attack-repo.md`); the revisions are marked.

## 1. Verdict

The project is a publishable dataset-and-method resource paper today, at the size it really
has, and an unproven research paper. The resource claim rests on the 189 read documents'
verified contract and the dataset's shape, not on its row count: 23,882 of the 24,071 documents
are a deterministic, no-model unpack of an MIT benchmark, and the read documents carry 103
flags, 50 dropped breaks and four known-wrong dates (revised after review). The work that
exists is rigorous in a way most student projects are not: every boundary, quote and date is
code-verified, every run has a receipt, every ruling has a date. But the goal stated in
August was a harness that ingests, organizes, retrieves, injects and maintains, measured against
a published number, and after four weeks the harness ingests. It does not organize, retrieve,
inject or maintain, and no number exists. The proposal filed with the advisor commits five
measurements; the hours left in the semester hold one, perhaps two. The committed slate is not
achievable as written, and nobody has said so to the advisor. That is the finding.

## 2. Your goals, as you stated them

From the August sessions and the advisor record, in your words where they were recorded:

1. "Build a rigorous and defensible system, not just improve my system." (08-25)
2. "A bottom to top harness that builds a memory tree / entity knowledge base from a corpus and
   efficiently injects that for RAG." Five steps: ingest, organize, retrieve, inject, maintain.
   (08-25)
3. "I can't just vibe code this." The model is the only black box; every pipeline decision is
   yours; Python, stdlib first, raw HTTP, no orchestration framework. (08-25)
4. Model-agnostic by requirement: two thin interfaces, `generate` and `embed`, so tiers swap and
   stage-wise model sensitivity becomes a result. (08-25)
5. "This is going to take 100s of hours not 35." Hour boxes are sequence, not schedule; the
   five-step build is a full-year deliverable; fall realistically reaches ingest and organize plus
   one comparison; the December paper is not hostage to the build. (08-25)
6. Validation is the work: "taking this from something that works for me to something validated
   and tested." No feel-good framing; verdict first. (08-19, 08-26)
7. The end state: a backend that bolts onto a desktop AI client, chat logs above all, your own
   assistant as the first user; the wiki as the store made visible. (README, 09-08 record)
8. Public artifacts only on public-domain or licensed text; the private archive stays private.

## 3. The proposal, reviewed

Two versions exist: the August 31 draft (the docx, filed with the advisor, now untracked) and
`docs/proposal.md` (brought to the project today). What the filed version says that is no longer
true:

| the filed proposal says | true on 09-13 | weight |
|---|---|---|
| four corpora, 81 files, 6.9M words, including the Chinese classics | three literature corpora (69 files) plus GraphRAG-Bench, 100 CC-BY papers and LongMemEval; Chinese removed 09-04 | corpus list |
| fifth measurement: the OCR tax and the translation tax | gone with the Chinese corpus; LongMemEval took the slot | a committed measurement dropped |
| resolution scores name, co-occurrence and a low-confidence profile; the ablation switches both off | the profile was dropped 09-09; co-occurrence survives as the global layer's second signal, and the ablation is restated at the up-edge (09-08 review) | the open question moved, not narrowed (corrected on 09-13 after Justin pointed at the 09-08 records) |
| NarrativeQA: 345 questions over twelve books | 319 over eleven | number |
| LongMemEval is a stretch item; the full comparison is spring | the last four days of build went into chats; LongMemEval is the de facto spine | the plan inverted |
| "two narrow interfaces" | one; `embed` is not built | design claim |
| "the pipeline is my code end to end" | the notebooks are drafted by an AI under your rulings, run and tested by you | authorship claim (section 5) |
| by September 27, the store and pipeline over Oz book 1 at three tiers, the alias set scored | no store, no alias set, one tier measured | milestone at risk in 14 days |
| "a few dollars to a few hundred at batch rates" | measured: $8.24 for Step 0, about $107 for the chats at Step 1 | fine |

What the proposal never says and the design now depends on: that nothing is merged across
documents (the tree, settled 09-07); that narrative cells are the primary representation (09-08);
that chats are read whole in one call and get no cells (09-12). `docs/proposal.md` now carries
the first; the other two belong in the paper's method section, not the proposal.

**Recommendation.** Do not re-file. Send Dr. Fang a one-page addendum with the next weekly:
the corpus as it is, the measurement slate as the execution plan sets it, the milestone slip,
and the authorship sentence in section 5. He approved the topic on August 28; he has not been
told the slate changed.

## 4. Academic soundness

### 4.1 The claim

RESEARCH.md states it correctly: no new idea; a systems paper for a demonstration or in-use
track; "here is the system, and here is which parts of it actually help." The 09-08 review
sharpened it: on a benchmark's own terms, competitive accuracy at a fraction of the token cost,
every answer quote-backed, no graph database, no server. That claim is legitimate for the venues
named (PVLDB, resource tracks, cs.CL preprint). It is also unsupported: no arm has run.

The differentiation kept is "the object that accumulates: source-local narrative states of an
entity through ordered units", against ASKS, GraphRAG, LLM-Wiki, KGGen, PAGER. Two things
weaken it today. Chats, the end state's main input, get no narrative cells since 09-12, so for
the corpus the paper will measure on, the accumulating object is facts and a session summary.
And the object-by-object comparison with ASKS, required by the 09-08 record before the global
layer is built, is unwritten; the tree formulation is unsearched (review decision 6). Neither is
hours; each is one or two hours of reading. Both must precede the paper.

### 4.2 Evidence

What can be reported today with a straight face: the dataset (24,071 documents, verified
contract, five docs, $8.24); the extractor's measured limits; the ingestor's cost, rejection
categories and quote-gate rate per corpus (from receipts); the 14-question presence check on
LongMemEval; the tree as a design position with its costs named. What cannot: any accuracy, any
ablation, any comparison, any supersession result, any resolution result. The "one open
measurement worth owning" (co-occurrence as a resolution signal) has moved: the system no longer
merges across documents, so the signal only nominates pairs inside a document, and the 09-08
review's fix (restate it as attachment accuracy at the up-edge) requires the up-edge, which does
not exist. As the proposal stands, the ablation would measure a signal at a place the paper's
story does not turn on. The plan cuts it and says why; what replaces it is an arm with the
parent join switched off, which measures what the tree buys instead of asserting it. One more
question the review raised and this audit had not: what a positive result would be worth.
"Retrieval over model-written facts approaches full context at a fraction of the tokens" is
what every retrieval baseline in the LongMemEval and Zep papers already shows; the design's
distinctive benefits (insertion, deletion, provenance, re-pointing) are exercised by no
benchmark in the slate. The paper must measure at least one of them or claim it as a position.

### 4.3 Evaluation validity

- **Contamination.** The four-part answer (pre-1900 novels, arm-versus-arm over identical text,
  the NovelQA depth finding, the deerstalker probe) is sound and travels with every result. The
  deerstalker probe needs the wiki's assembled page to exist; without the wiki, only three parts
  survive.
- **Parity.** The plan reproduces each benchmark's published plain baseline before claiming
  comparability. Zep's LongMemEval numbers are on gpt-4o-mini and gpt-4o over the original `_s`
  file. Your pipeline runs gpt-5.6-luna and gpt-5.6-terra. A parity arm therefore needs
  gpt-4o-mini to still be callable; if it is not, no number here joins Zep's table and every
  comparison is a ratio between your own arms. Check this in the first hour of the harness.
- **The judge.** "Never shares a tier with a writer, calibrated on a hand-labeled sample" is
  stated in three documents and built nowhere. Thirty labels is an hour.
- **Variance.** One stated run with a band over k reruns: stated, not planned in hours. On
  LongMemEval a band needs the same histories ingested k times; at $0.22 a history that is cheap
  in money and expensive in Kaggle time.
- **Supersession.** The knowledge-update band (78 questions) is the one place the paper's
  temporal claim is testable, and it depends on a functional-predicate list that does not exist,
  or on an answering harness that reads dated facts and lets the model choose. The second is
  buildable; the first is a ruling.
- **The presence check is not evaluation.** "All 14 answers are stored" says the facts exist
  somewhere in the packages. A reviewer will ask whether retrieval finds them and the model
  answers with them. Do not present presence as accuracy.
- **The reader model** (added after review). Every arm of a benchmark must answer with one
  model, and parity with a published number needs that number's model; the pipeline's Luna and
  Terra are neither gpt-4o-mini nor gpt-4o. The benchmark's own evaluator, as published, is the
  scorer; a custom judge with thirty labels would be a second experiment, not a control.
- **The development set** (added after review). The 14 questions that tuned Step 1 on 09-12
  are excluded from every reported number, and a history is scored only when ingested whole;
  13 of the 14 had only their answer sessions in the package set, which is no test of retrieval.
- **Contamination on the spine** (added after review). LongMemEval has been public since 2024,
  inside the training window of every model here; arm-versus-arm survives, the comparison to
  Zep's 2025 run does not, and no chat-side probe like the deerstalker exists.
- **Gold.** LitBank is dead (96 of 100 documents are two chunks); BookCoref was proposed on 09-08
  and never ruled; the Oz alias set was due in week one and is unwritten. Without one of them,
  resolution and attachment have no gold and the paper reports instruments only.

### 4.4 Baselines

Zep on LongMemEval (published numbers, no reimplementation); GraphRAG-Bench's nine systems
(published, gpt-4o-mini); full-context and flat retrieval (yours). Adequate for the track. The
anti-goal is right: do not try to beat Zep; the case is cost, provenance and supersession.

### 4.5 Reproducibility

Strong on the artifacts: public raw dataset with hashes, public split dataset with its contract,
public notebooks, receipts with every call's cost. Weakened tonight (revised after review): the
offline battery, the export verifier and the answer check left the tracked tree under the
ruling that working tooling stays on the author's machine, so "94 of 94" and "0 quotes off" are
not checkable by a reader; ruling 8 of the plan asks for a tracked `tests/` holding those three
and nothing else. Two more gaps: the model is
not deterministic and no seed or version pin exists beyond the model name, so "a rerun will
differ" must be stated beside every number (it is, in LIMITS.md); and the DOI is not minted.

### 4.6 Authorship and disclosure

Goal 3 says the code is yours and the model is the only black box. What is true: the design is
yours (every ruling is dated and yours), the runs are yours, the tests are run by you, and the
notebooks are drafted by an AI at your direction. The filed proposal's "the pipeline is my code
end to end" is a sentence a reviewer or a committee could hold against you if the drafting is
later evident, and the docx's own footer already says "drafted with AI assistance; every design
decision, citation and number reviewed and answered for by the author." Say that, exactly, in
the paper and the proposal; the venues' disclosure policies expect it, and it is true.
`docs/proposal.md` and README now say it. Whether it satisfies the course is the instructor's
call, and it is asked before the addendum goes (plan, section 6). The same disclosure covers
the batteries that check the code, the documentation, the retroactive logs, the related-work
prose, this audit and the plan: all drafted with AI assistance under the author's rulings.

### 4.7 Licensing and ethics

Sound: public domain, MIT with notices, CC-BY with `attribution.jsonl`; the private archive never
public; IRB noted before any tester. One defect: the reference PDFs sat in the public repository
for two weeks under licenses that forbid it (untracked today, still in history; your ruling was
to leave history).

### 4.8 The scope with the advisor

August's open question (the April survey proposal versus the memory project) is closed in
practice: the 09-09 weekly reports the memory project and README records the approval of August
28. Not recorded anywhere: what IT 494 itself requires as graded deliverables (a report, a
presentation, the symposium board, a demonstration). The paper is your deliverable; the course's
may differ. Find out this week; it changes the November calendar if a report or a talk is due.

## 5. Feasibility

**Hours** (revised after review). The plan assumes 8 a week. The repository's own record says
otherwise: commits on 17 of 22 days from August 23 to September 13, 55 commits on September 6,
Kaggle launches after midnight, and every notebook run by hand. The real pace is several times
8 a week; the plan prices at 8 and re-prices after week 1's real hours. At 8 a week: From September 14: two
open weeks to September 27 (16 hours), the exam block September 28 to October 18 (call it 0 to 8
hours, writing only), four open weeks October 19 to November 15 (32 hours). About 48 to 56 hours
in all, of which the paper itself takes 10 to 15. So 33 to 46 hours of build remain against a
slate priced on 09-08 at 69 to 118. Your own August calibration ("100s of hours not 35") was
right, and the fall's realistic reach was named then: ingest and organize plus one comparison.

**What one comparison costs in hours**, from the pieces: a store from packages (4 to 6), the
global attach inside one history (6 to 10), retrieval and context assembly (6 to 8), the
LongMemEval harness with parity and judge (6 to 8), instruments (2). About 24 to 34 hours. That
fits, barely, and only if nothing else is built. GraphRAG-Bench adds 8 to 12 and its own ingest
of 20 novels; it fits only if the week holds more than 8 hours. NarrativeQA, the wiki, the cells
ablation and the resolution ablation do not fit.

**Money.** Not the constraint. All 23,882 chats at Step 1 are about $107; answering 500 questions
three ways on the Flex tier is under $20; a GraphRAG-Bench run is tens of dollars. The whole fall
is under $300.

**Kaggle time.** The constraint nobody priced. Step 1 over every chat is about 48 hours of kernel
time at 16 sessions at a time; a Kaggle CPU session caps at 12 hours, so that is four or five
sessions with the attach-previous-output resume, each a manual launch. Two things the code does
today make it worse (added after review): block 12 stops at its $15 budget, about 3,300 sessions,
and the packages are two files per document, 48,000 files for all chats, when 25,000 output
files already made one notebook impossible to download. Both are fixed before any scaled run
(plan 2e). The exam block is the place to run them, since
they need no build hours. A 50-history subset (about 2,400 sessions, $11, 5 hours) is the
fallback and is enough for a number with a variance band.

**The deadline in three days.** The global merge is due Wednesday September 16. What is
deliverable by then is the first cut: packages of one history loaded into SQLite, parents drawn
by exact name and kind, one question answered through the store. The specification (the up-edge
signal beyond exact name, the parent's name rule, the read-time view) is not written and cannot
be finished by Wednesday; the first cut should be built as the way to find out what the
specification must say, which is what the 09-08 record's strategy called for.

## 6. What must change, in order

1. Decide the slate now, not in November. Ruled the same night: both benchmarks, the rest
   spring; the global layer first regardless, then the store and embedding it decides, the
   query path, the harness, and only then the full data; a first draft of the paper in
   mid-October. Tell the advisor.
2. Build the first-cut global layer this week on one history and answer one question end to end.
   Everything the paper claims runs through that path.
3. Write the thirty judge labels, the Oz alias set (if Oz is measured at all), and the
   functional-predicate list or the dated-fact answering rule. Each is an hour.
4. Read Story Ribbons, Narrative World Model and ASKS; search the tree formulation. Two hours.
   Before any prose.
5. Send the endorsement email if it is unsent, and ask what the course itself grades.
6. State the authorship model plainly everywhere the proposal's sentence appears.

## 7. After the rulings of the evening

Justin ruled, after this audit and the attack on it: the global layer is built first regardless
of which benchmark needs it, because the store schema and the embedding follow from it; then the
query path; then a harness that tests it; every step tuned on the test packages already on disk;
the full data through the ingestor only when the whole pipeline is ready for testing, in Kaggle
batches, with the run's kernel time used for writing; both benchmarks stay; a first draft of the
paper in mid-October, the second to Dr. Fang by November 3.

Justin's reading of the verdict, on walking through it: "unproven" describes the evidence on hand tonight, not the odds. Every stage so far has shipped and each one improved the plan, so the plan assumes the design lock lands and the mid-October draft is written as the research paper, with the resource content as its floor rather than its frame; the gates re-price, they do not pre-cut.

What that does to the findings above. The verdict stands as a statement of evidence. The feasibility changes shape: the
design lock (global layer, store, embedding, query path, 25 to 37 hours by the plan's prices)
must land in the two weeks to September 27, which is impossible at eight hours a week and
plausible at the pace the repository records; the week of September 20 says which. The
mid-October draft means the results-independent sections are written before most numbers
exist, which is the right order for a resource paper and the only order that meets the date.
The academic risks that remain are the ones in section 4: one reader model and the benchmark's
own evaluator (rulings 2 and 3 of the plan), the tuning questions excluded, no supersession
claim without a mechanism, the ASKS comparison and the tree search before any prose, the
authorship sentence everywhere, and the course's own deliverables, still unasked.

On point 2, Justin ruled the fall scope: ingest, the global layer, storage, retrieval, the test harness, test and assessment, and wiki pages over document clusters (an afternoon after the numbers); then publish. Maintenance, deployment and a living stream of data are spring, and the proposal now says so.

On point 3, Justin corrected the audit: co-occurrence is not a within-document leftover. The 09-08 review restates the resolution ablation at the up-edge (name-only against name plus co-occurrence as inputs to attachment, scored as attachment accuracy) and the 09-08 decision record and wiki note cluster documents from shared entities and meaningful co-occurrence. Section 4.2's claim that the signal acts inside a document only is withdrawn; the ablation is a fall measurement, the Oz alias set is written in week 2, and the plan, proposal, RESEARCH, entity-resolution and README now say so.
