# Academic audit, 2026-09-13: the proposal reviewed, the project measured against Justin's goals

Verdict first, no silver linings. Companion to `project-state.md` (what exists and what is
verified) and `docs/execution-plan.md` (what to do about it). Every claim below names its
source; where the source is a chat, it says so.

## 1. Verdict

The project is a sound resource-and-experience paper today and an unproven research paper. The
work that exists is rigorous in a way most student projects are not: every boundary, quote and
date is code-verified, every run has a receipt, every ruling has a date. But the goal stated in
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
| resolution scores name, co-occurrence and a low-confidence profile; the ablation switches both off | the profile was dropped 09-09; only co-occurrence remains, and only inside a document | the open question narrowed |
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
story does not turn on. Either restate it (the plan does) or drop it.

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
- **Gold.** LitBank is dead (96 of 100 documents are two chunks); BookCoref was proposed on 09-08
  and never ruled; the Oz alias set was due in week one and is unwritten. Without one of them,
  resolution and attachment have no gold and the paper reports instruments only.

### 4.4 Baselines

Zep on LongMemEval (published numbers, no reimplementation); GraphRAG-Bench's nine systems
(published, gpt-4o-mini); full-context and flat retrieval (yours). Adequate for the track. The
anti-goal is right: do not try to beat Zep; the case is cost, provenance and supersession.

### 4.5 Reproducibility

Strong where it matters: public raw dataset with hashes, public split dataset with its contract,
public notebooks, receipts with every call's cost, the offline battery. Two gaps: the model is
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
`docs/proposal.md` now says it.

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

**Hours.** The plan assumes 8 a week, unverified against a real week. From September 14: two
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
sessions with the attach-previous-output resume. The exam block is the place to run them, since
they need no build hours. A 50-history subset (about 2,400 sessions, $11, 5 hours) is the
fallback and is enough for a number with a variance band.

**The deadline in three days.** The global merge is due Wednesday September 16. What is
deliverable by then is the first cut: packages of one history loaded into SQLite, parents drawn
by exact name and kind, one question answered through the store. The specification (the up-edge
signal beyond exact name, the parent's name rule, the read-time view) is not written and cannot
be finished by Wednesday; the first cut should be built as the way to find out what the
specification must say, which is what the 09-08 record's strategy called for.

## 6. What must change, in order

1. Decide the slate now, not in November: LongMemEval as the spine, GraphRAG-Bench as the
   stretch, the rest cut. Tell the advisor.
2. Build the first-cut global layer this week on one history and answer one question end to end.
   Everything the paper claims runs through that path.
3. Write the thirty judge labels, the Oz alias set (if Oz is measured at all), and the
   functional-predicate list or the dated-fact answering rule. Each is an hour.
4. Read Story Ribbons, Narrative World Model and ASKS; search the tree formulation. Two hours.
   Before any prose.
5. Send the endorsement email if it is unsent, and ask what the course itself grades.
6. State the authorship model plainly everywhere the proposal's sentence appears.
