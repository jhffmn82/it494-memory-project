# Attack on the 09-13 academic audit and the execution plan

Hostile reviewer and hostile project manager, 2026-09-13. Read-only. Every finding names a
file and line; every number was recomputed from the repository (the benchmark file, the
notebooks, the git log, the Step 0 docs) rather than taken from the documents under attack.
Ordered most damaging first. Categories: A factual, B arithmetic and feasibility, C evaluation
validity, D verdict, E missing risks and rulings, F authorship, G flattery, hedging, unsourced.

Abbreviations: audit = `log/2026-09-13/academic-audit.md`; plan = `docs/execution-plan.md`;
state = `log/2026-09-13/project-state.md`; ingestor = `notebooks/threadatlas-ingestor.py`;
extractor = `notebooks/threadatlas-extractor.py`; LME = `data/benchmarks/longmemeval/longmemeval_s.json`.

---

## 1. [B, E] The full Step 1 run will hit the Kaggle output-file failure the extractor already hit, and neither document prices it

- Where: plan:86-88 ("all 500 in four or five 12-hour sessions with the previous output
  attached"); audit:184-188 ("Kaggle time. The constraint nobody priced"); plan:152.
- Claim: the only Kaggle constraint is the 12-hour cap and the resume.
- Why wrong: the ingestor writes one folder per document with a `.jsonl` and a `roll-up.txt`
  (`docs/ingestor.md:94-97`). 23,882 chat documents is about 48,000 output files under
  `/kaggle/working`. The extractor comment at extractor:164 records that 25,112 files there
  "make the notebook's output too big to list or download", which is why 1.8 moved the unpack to
  `/kaggle/temp` (`log/2026-09-13/README.md:34-36`). The resume mechanism makes it worse: each
  launch mounts the previous output as a dataset (`docs/ingestor.md:102-103`), so launch four
  mounts about 36,000 files. Nothing in 2e says how packages leave Kaggle, and the PC-side
  download is the Kaggle CLI that already needed a short path and `PYTHONUTF8` for a 71-session
  run (`log/2026-09-12/README.md:66-67`).
- Say instead: 2e needs a packaging step before the first launch: one archive or one JSONL per
  history written under `/kaggle/temp` and tarred into `/kaggle/working` at the end of each
  block, and the store loader reads that. Price it (2 to 3 hours plus one test launch) and put
  it in the 2a gate, since the store is what reads it.

## 2. [B] Block 12's budget stops a 12-hour session at about 7 hours, so it is eight launches, not four or five

- Where: audit:185-187 ("four or five sessions"); plan:86-88; state:42.
- Claim: 48 kernel-hours divide into four or five 12-hour sessions.
- Why wrong: `CHAT_AT_ONCE, BUDGET = 16, 15.00` at ingestor:2587 and `start_block(BUDGET)` at
  ingestor:2593 end the block past $15 of its own spending (`docs/ingestor.md:90-91`). At $0.0045
  a session a 12-hour launch spends 8.2 x 720 x 0.0045 = $26.6, so the block stops at about
  3,300 sessions, 6.8 hours in. 23,882 / 3,300 = 7.2, so eight launches, each needing a human to
  attach the previous output and press run, inside an exam block described as "unattended"
  (plan:111). Also `SPEND_STOP` defaults to 25 (ingestor:288). Trivial to change; not changed,
  not priced, and the "four or five" is wrong as the code stands.
- Say instead: "eight launches at the frozen budget, or four to five if BUDGET is raised to $30
  and SPEND_STOP to $120 for the exam-block runs; each launch is a manual step and lands on a
  named date in the calendar."

## 3. [B] The calendar assigns 22 to 32 priced hours to the 16 hours of weeks 1 and 2, and the Sep 16 gate needs 10 to 16 hours in three days

- Where: plan:109-110 (weeks 1 and 2) against plan:33-83 (the prices); audit:176 ("fits, barely").
- Claim: the spine (24 to 34 hours) fits the remaining build hours and the weekly gates hold.
- Why wrong: week 1 carries 2a (4 to 6) + 2b (6 to 10) + part of 2c, in 8 hours, with the Sep
  16 gate (store plus first-cut parents, 10 to 16 hours) due Wednesday, three working days after
  Sunday Sep 13. Week 2 carries the rest of 2c + 2d (6 to 8) + labels + the gpt-4o-mini check in
  8 hours. The build weeks in the calendar total 32 hours (weeks 1 to 4) plus 0 to 8 in the exam
  block; the audit's "33 to 46 build hours" (audit:169) counts weeks 5 and 6, which the calendar
  gives entirely to writing. So the real comparison is 24 to 34 spine against 32 to 40 build
  hours, and the stretch's 8 to 12 plus ingest fits only if every low estimate holds.
- Say instead: re-lay the calendar by dependency: weeks 1 to 3 for 2a to 2d (24 to 34 hours),
  the Sep 27 gate moved to Oct 25 for "14 questions scored on three arms", and the stretch
  declared dead now unless the measured week is above 8.

## 4. [B] Every 09-13 price is the 09-08 price cut by about half with no new information

- Where: audit:172-176; plan:33-83; against README.md:91-103 (the 09-08 bill).
- Claim: the spine costs 24 to 34 hours.
- Why wrong: the same items on 09-08 were "Store, ingest, organize, maintain 20-40" (README:94)
  and "LongMemEval loader, parity arm, update band 8-15" (README:102). On 09-13 the store plus
  global layer is 10 to 16 and the LongMemEval harness is 6 to 8 with more scope (three arms, a
  judge, calibration, per-question cost accounting). Nothing was built in between that would
  make them cheaper; the packages got a new shape (1.8) that the loader has never seen. The
  prices shrank as the deadline approached. Debugging, Kaggle friction, the judge's prompt per
  question type, the abstention rule, the truncation rule, the download of 48k files, and the
  result tables are priced nowhere.
- Say instead: keep the 09-08 prices, add 30 percent for the unbuilt loader and the harness's
  six question types, and state that the number is a floor.

## 5. [C] The parity design is incoherent: the ThreadAtlas arm answers on Luna, the parity arm on gpt-4o-mini, and the judge is not the benchmark's

- Where: plan:63 ("`answer(question, context)` on Luna"); plan:74-80 (parity arm on gpt-4o-mini,
  judge on Terra); audit:104-108.
- Claim: if gpt-4o-mini is callable, the full-context arm reproduces Zep's 55.4 and "our numbers
  join Zep's table".
- Why wrong: three things. (a) If the reader differs between arms, no arm-versus-arm comparison
  is valid, and the ThreadAtlas number is not a gpt-4o-mini number, so it cannot sit beside
  Zep's 63.8 either way. (b) Zep's and LongMemEval's published numbers are scored by the
  benchmark's released evaluator, an LLM judge (GPT-4o) with a prompt per question type; a
  Terra judge calibrated on thirty of Justin's labels is a different instrument, so matching
  55.4 would be a coincidence, not parity. (c) 429 of the 500 histories are over about 120k
  tokens at four characters a token (recomputed from LME), against a 128k window; the original
  harness's truncation rule is part of what "parity" means and the plan has none.
- Say instead: rule the reader for all three arms (one model, ideally the parity model); use the
  benchmark's own judge prompt and model for the scored number and Terra only as a second
  opinion; write the truncation rule before the first full-context call.

## 6. [C] The knowledge-update band, as designed, tests nothing about the system

- Where: plan:64-66 ("until it exists every fact is served and the model chooses"); plan:12;
  audit:114-117 ("The second is buildable").
- Claim: the 78 knowledge-update questions are where the temporal claim is testable.
- Why wrong: every one of the 78 has exactly two answer sessions (recomputed from LME), the
  update in the later one. Serving both dated facts and letting the reader choose gives the
  reader exactly what the full-context arm already has (sessions carry dates). No mechanism in
  the system decides anything: `valid_to` is dropped (`docs/rulings.md:158`), the functional
  list does not exist, the read-time view is unbuilt (state:117-120). So the band measures the
  reader's temporal reasoning over two retrieved facts, which is a retrieval test with a date
  in the prompt. Six of the 78 are abstention questions, which the plan does not mention.
- Say instead: either build the read rule of SCHEMA.md:150-164 for chats (a functional list of
  the ten predicates the 78 questions actually touch is an afternoon, not a semester) and report
  the band with its denominator, or report the band as "retrieval with dates" and drop the word
  supersession from the fall paper.

## 7. [C] On the spine, the tree is a string grouping over one user's 48 sessions; the paper measures its cost and none of its claimed benefits

- Where: plan:15 ("with its query-time cost measured on the LongMemEval arm"); plan:44-55
  (first cut: case-folded name and kind); audit:77-80; `docs/entity-resolution.md:297-301`.
- Claim: the merge-free tree is a committed result.
- Why wrong: on chats every subject is a major and "the same name in two turns is one entity, no
  judge" (`docs/ingestor.md:51-52`), so 2b's attach is the within-document rule applied across
  sessions: exact string match. About 18 nodes a session (`log/2026-09-12/README.md:57`) times
  48 sessions is under a thousand rows per history; a one-hop join over them in SQLite is
  microseconds, and reporting it is not a result. The benefits the design claims (append-only
  insertion, clean deletion, re-pointing, disagreement kept visible) are exercised by no
  benchmark in the slate; static QA cannot exercise them. "Kind" is an open vocabulary
  (`docs/rulings.md:91`), so "kind agrees" is undefined until a normalisation is ruled. The 2b
  gate (plan:54-55) cannot fail: the grocery stores each appear in one session, so "one parent
  each" is one child under one parent.
- Say instead: measure one benefit or drop the word "measured": an insertion cost (ingest
  history N, then add session N+1, count what is rewritten: zero by construction, and say so
  against MemTree's refold numbers already in RESEARCH.md:96), and a deletion check (remove one
  session, verify no orphan). Both are hours, not weeks, and both are what the position claims.

## 8. [C] "One history per graph" is fair to the benchmark and unfair to the paper

- Where: plan:39-40; `docs/rulings.md:182`; audit does not raise it.
- Claim: implicit, that one history per graph is the right scope.
- Why wrong in part: LongMemEval is one user per history by construction, and the end state is a
  single user's backend, so cross-user interference is not a claim the paper makes and the
  scope is defensible on the benchmark's terms. What it dodges is the paper's own highest-upside
  item on 09-08: the combined-store interference delta (`log/2026-09-08/forward-plan.md:49-51`),
  the only test where the tree would be doing something a flat index does not. Within one
  history the ThreadAtlas arm minus 2b is the same FTS5 index over abstracts and quotes as the
  flat arm plus a join. The strongest objection the plan does not answer: "what does the tree
  buy on this benchmark that flat retrieval over your own session abstracts does not?"
- Say instead: keep one history per graph for the scored number; add a fourth arm, ThreadAtlas
  without 2b (FTS5 over the store, no parent expansion), so the tree's contribution is a
  measured delta rather than an assumed one. It is a flag in 2c, not a new build.

## 9. [C] The spine measures a corpus on which the paper's one kept differentiation does not exist

- Where: audit:77-80 ("Two things weaken it"); `docs/rulings.md:24` (cell primacy narrowed:
  chats get no cells); `log/2026-09-12/README.md:34-40`.
- Claim: the differentiation "source-local narrative states of an entity through ordered units"
  is weakened for chats.
- Why wrong: not weakened, absent. Chats get no cells, no fold, no entity abstracts. The paper's
  method section will describe cells as the primary representation (09-08 decision record,
  `log/2026-09-08/threadatlas-decision.md:13`) and its results will come from a corpus where the
  representation is facts and one session summary. This is the 09-08 review's "your headline
  measurement describes a system you deleted" (`log/2026-09-08/publishability-review.md:16`)
  one level up, and the audit filed it under "weakens".
- Say instead: state in the slate that on the spine the accumulating object is the dated fact
  and the session abstract, that cells are a books-and-papers feature not measured this fall,
  and rewrite the differentiation paragraph accordingly before the addendum goes to the advisor.

## 10. [A] The reproducibility claim was written sixteen minutes after the verification scripts left the repository

- Where: audit:134-137 ("Strong where it matters"); state:52-55, 109 (cites
  `log/2026-09-13/check_flex_run.py` and `log/2026-09-13/extractor/`); `log/2026-09-13/README.md:45-46`
  ("Committed as f0d38ad with the build and verification scripts"); `log/2026-09-12/README.md:22-23`.
- Claim: the checks that verified every number are in the public record.
- Why wrong: commit 005f19c (14:19, "reduced to what a person reads") untracked
  `log/2026-09-13/check_flex_run.py`, `log/2026-09-13/extractor/{block0_unpack,check_18,make_18,numbers_18,verify_18,verify_unpack}.py`,
  both `test_ingestor.py` batteries, both `mutate_ingestor.py`, `scripted_model.py` and
  `build/IT494_Proposal.docx`. `git ls-files log/2026-09-13` returns four markdown files. The
  audit (14:35) and the state document (14:09, still cited at HEAD) point at files a reader of
  the public repository cannot open. "94 of 94", "verify_18.py passed", "0 quotes off" are now
  claims nobody outside the PC can rerun, which is exactly what section 4.5 says is strong.
- Say instead: either track the verification scripts (they are small, 72 to 672 lines) or say
  in 4.5 that the checks are on the author's machine and the public record holds only their
  outputs in receipts; the second is what a reviewer will discover.

## 11. [B] "8 a week, unverified" is contradicted by three weeks of the repository's own timestamps

- Where: audit:166; state:143; README.md:88; RESEARCH.md:289-290; plan:149.
- Claim: the hour assumption cannot be checked until a real week is measured.
- Why wrong: `git log` from Aug 23 to Sep 13 shows commits on 17 of 22 days, 55 commits on Sep
  6, 46 on Sep 4, a Sep 8 running 06:36 to 23:12, and Kaggle launches at 23:24 and 01:18 local
  on the night of Sep 12 to 13 (`log/2026-09-12/README.md:56, 61`; `log/2026-09-13/README.md:7`).
  Justin runs every notebook and rules on every question (`docs/rulings.md:175`), so this is his
  attendance, not only the agent's. The measured pace is several times 8 hours a week. The audit
  had this evidence and planned on a number it calls unverified. Either the hours exist (then the
  slate was cut too early) or September's pace is unsustainable through exams (then say that and
  price the discount).
- Say instead: "the measured rate for Aug 23 to Sep 13 is N hours a week by commit and run
  timestamps; the plan assumes 8 because the exam block and the semester's other courses cut it
  by X; re-price on Sep 20 against the logged hours."

## 12. [D] Cutting GraphRAG-Bench inverts the cheapest path to a number and is argued from sunk cost

- Where: plan:16 (stretch), plan:99-103; audit:176-178; state:162-168 ("the last four days went
  entirely into chats... it should be the plan" that changes).
- Claim: GraphRAG-Bench costs "8 to 12 plus its own ingest" on top of the spine and fits only if
  weeks hold more than 8 hours.
- Why wrong: GraphRAG-Bench questions map one to one onto 20 novels, 71 to 137 each (recomputed
  from `novel_questions.json`), so under the plan's own scope rule a graph is one document and
  2b (6 to 10 hours) is not on its path at all: it needs 2a + 2c + a harness, and its scorer is
  released under MIT. It has 2,010 questions (power stated at `docs/evaluation-corpus.md:77-79`),
  nine baselines, no judge to build, and the co-occurrence ablation the proposal calls "the
  measurement I most want to land" (`docs/proposal.md:81-88`) replays from logged candidate
  scores (`docs/entity-resolution.md:356-372`). LongMemEval needs 2b, a judge, a truncation
  rule, an abstention rule, a deprecated parity model, and its supersession band is empty
  (finding 6). The only argument for the inversion is "chats are the end state", a product
  argument, and "four days went into chats", which is sunk cost. The audit does not weigh the
  two on evidence; it ratifies where the build went.
- What the advisor loses: the first committed measurement and the only "open question" in the
  proposal he approved; the three-tier pilot (goal 4, audit:28-29, the model-sensitivity result,
  which appears in no slate row and is silently gone); the Oz alias set and the Sep 27
  milestone; the wiki; the next-week plan he was told on 09-09 (Oz plus ten papers plus a
  hand-labelled key plus retrieval plus a first wiki page, `reports/2026-09-09-weekly.md:104-111`);
  and the bge-small sentence embedder he was told was settled (weekly:59-72), replaced by FTS5
  with no vectors (`docs/ingestor.md:59`). The addendum (audit:62-65) reaches him after week 1
  has spent its hours on the new slate.
- Say instead: run GraphRAG-Bench first on the plan's own dependency order (2a, 2c, harness; no
  2b), because it is the shortest path to a number with published baselines, then LongMemEval
  with 2b as the second arm; or, if chats stay the spine, say plainly that the reason is the end
  state and that the advisor is being asked to accept a weaker evidence base for it.

## 13. [C] The fourteen questions are a development set and the 2d gate compares arms over different inputs

- Where: plan:81 ("the 14 known questions scored by the judge on all three arms");
  `log/2026-09-12/README.md:38-40, 61-62` (rulings 3 to 6 gated on all 14 answers found);
  `docs/rulings.md:182` (only one history is a graph); audit:118-120.
- Claim: scoring the 14 on three arms is the harness gate.
- Why wrong: the chat prompts were tuned until those 14 answers were captured, so they are
  training data for the reported number and must be excluded or disclosed. Worse, 13 of the 14
  have only their answer sessions ingested, not their 39 to 66-session haystacks, so the
  ThreadAtlas arm on them retrieves from a store with no distractors while the full-context
  arm reads the whole history: the gate compares three arms over different inputs and will
  pass for the wrong reason.
- Say instead: ingest the 13 other histories (13 x $0.22, about 80 kernel-minutes) before 2d,
  score the 14 as a smoke test only, and report the 500 with the 14 marked as used in
  development.

## 14. [C] Thirty labels cannot be "the first thing in 2d", and kappa on thirty items is noise

- Where: plan:76, 81-82, 153; audit:109-111 ("Thirty labels is an hour").
- Claim: calibrate the judge on thirty hand labels before scoring, gate at 0.7 kappa.
- Why wrong: a label is a verdict on a (system answer, gold answer) pair; there are no system
  answers until an arm has run, so the labels cannot precede 2d. The standard error of kappa on
  30 binary items is roughly 0.15 to 0.2, so 0.7 versus 0.5 is indistinguishable. The labeller
  is the system's builder, scoring the system's own answers. The benchmark has six question
  types with different judging rules (abstention, preference, temporal) and one prompt does not
  cover them.
- Say instead: use the benchmark's evaluator as the scored instrument; label 100 items
  stratified by type after the first arm runs, report agreement with a confidence interval,
  and state that the labeller is the author.

## 15. [B, C] The 50-history subset yields a pilot, not "a number with a variance band"

- Where: audit:187-188; plan:86-91, 152.
- Claim: 50 histories are enough for a number with a band.
- Why wrong: 50 histories are 50 questions; the standard error on a proportion at n = 50 is
  about 7 points; the Zep-versus-full-context gap the paper positions against is 8.4 points. A
  random 50 holds about 8 knowledge-update questions and 3 abstention questions. "Three reruns
  of one 50-history subset" does not say what is rerun (the ingest, the answer, the judge), and
  the three sources of variance are different in kind.
- Say instead: the 50 is a pilot; the band comes from k answer-and-judge reruns over the full
  set on a fixed ingest, and one ingest rerun on the pilot to bound ingest variance; if only the
  subset completes, choose it stratified by question type with the seed stated.

## 16. [A] The master documents contradict the plan, and the ruling of 09-13 says the master documents are current truth

- Where: README.md:76-78 (Oz book 1 by Sep 21, three-tier pilot Sep 27, GraphRAG-Bench Oct
  19-26); README.md:105-118 (LongMemEval is the first cut, GraphRAG-Bench protected);
  README.md:44 ("an embedding model for candidate lookup"); RESEARCH.md:90-97 (slate with
  GraphRAG-Bench first), RESEARCH.md:223 ("the two model interfaces"), RESEARCH.md:291-294 ("The
  resolution ablation is committed"); `docs/evaluation-corpus.md:33-35` ("The GraphRAG-Bench
  numbers come next"); against plan:10-20 and `docs/rulings.md:178`.
- Claim: audit:52 says the "two narrow interfaces" claim is corrected ("one; `embed` is not
  built"); plan:3 says it "replaces the 09-08 forward plan".
- Why wrong: two master documents still say two interfaces, the README still carries the 09-08
  bill and cut order, and RESEARCH.md still commits the ablation the plan cuts. A reader who
  follows the 09-13 ruling reads the README and gets the opposite slate.
- Say instead: the plan is PROPOSED, fine; but the audit's table row must read "one in the
  proposal; two in README and RESEARCH", and the plan's ruling 1 must name the README and
  RESEARCH edits it triggers.

## 17. [A, G] The audit says the plan restates the ablation; the plan cuts it

- Where: audit:95-96 ("Either restate it (the plan does) or drop it"); plan:17 ("**cut**,
  restated as attachment accuracy on Oz if the alias set is written and Oz is ingested"); plan
  ruling 4 (plan:130-132) recommends not ingesting Oz.
- Claim: the plan restates the resolution ablation.
- Why wrong: the plan cuts it and makes the restatement conditional on a ruling it recommends
  against. Net: dropped. The two documents written the same evening disagree on the one
  measurement the proposal calls its open question.
- Say instead: "the plan drops it for the fall; the proposal's open question is spring work."

## 18. [C] The contamination answer does not cover the spine

- Where: audit:100-103 (the four-part answer); RESEARCH.md:123-129.
- Claim: the contamination answer "travels with every result".
- Why wrong: the four parts are about pre-1900 novels and a Holmes fixture. LongMemEval has been
  public on GitHub and HuggingFace since 2024, inside the training window of a 2026 model, and
  its answers are in the same file as its histories. Arm-versus-arm over identical text stays
  valid (equal contamination); the comparison against Zep's 2025 gpt-4o-mini run does not,
  because the models are not equally contaminated. No probe exists for chats.
- Say instead: state that the LongMemEval numbers are arm-versus-arm only, and add a cheap
  probe: answer 50 questions with no history at all (the "no-context control" the proposal
  already names at `docs/proposal.md:95`) and report the floor.

## 19. [B] The draft-by-Nov-3 date is unreachable from the hours as laid out

- Where: plan:114 ("full draft to Dr. Fang by Nov 3", week 5, Nov 1 to 8, 8 hours); audit:168-169
  (paper 10 to 15 hours).
- Claim: the paper's hours fit weeks 5 and 6.
- Why wrong: Nov 3 is a Tuesday; at most 2 or 3 of week 5's hours precede it. The draft must
  come from the exam block (0 to 8 hours, also assigned the skeleton, the ASKS comparison and
  the tree search) and week 4 (assigned GraphRAG-Bench or the results analysis). Writing the
  tables, the LIMITS statements and the results section is priced nowhere; the 10 to 15 is the
  09-08 number for prose only.
- Say instead: draft to Fang Nov 8, review Nov 8 to 13, freeze Nov 15 with no revision slack;
  or move the skeleton into week 2 and accept that 2d slips.

## 20. [B] The cost extrapolation sample is 10 percent shorter than the corpus, and "money is not the constraint" is asserted from an under-count

- Where: `docs/ingestor.md:107-108`; state:41-42; audit:180-182 ("The whole fall is under $300").
- Claim: $100 to $107 for the chats; the fall under $300.
- Why wrong: the block-12 history's sessions average 9,280 characters against 10,253 across all
  23,882 (recomputed from LME), so the per-session cost measured on 71 sessions of that history
  is about 10 percent low: $110 to $118. Flex is "sometimes refused" (ingestor:285) and the
  extractor falls back to standard at twice the price (`docs/extractor.md:100`); no fallback
  rate is measured. The $300 sum is chats ~$115, books and papers ~$100 (unmeasured,
  state:44), twenty novels $20 to 30, three ingest reruns $33, arms and judge under $20, the
  GraphRAG-Bench scorer's own model calls unpriced: it is at $300 before one failed run.
- Say instead: "$300 to $450 with one failed run and a 20 percent standard-tier fallback;
  the constraint is still hours, but the spending stop must be raised per block and a credit
  balance checked before each unattended launch (RESEARCH.md:166-167 records two mid-pass
  credit deaths)."

## 21. [E] Risks and steps the plan omits

For plan section 2:
- 2a: the loader must consume 500 per-history archives, not 48k files (finding 1); the
  `doc_tag` collision (state:96-98) is harmless per graph, say so in the gate.
- 2c: chats have no cells, so "FTS5 over abstracts, cells and fact quotes" indexes an empty
  table on the spine; the flat arm needs its own index over raw turns, a separate build.
- 2d: the truncation rule for full-context; `question_date` in the answer prompt (the benchmark's
  harness supplies it); the abstention rule for 30 questions; the judge prompt per type.
- 2e: which of ingest, answer and judge is rerun for the band; the sampling rule for the subset.
- Sequencing: the 500-history ingest launches in the exam block before 2c and 2d have read
  more than one history's packages. Step 1 is frozen (`docs/rulings.md:107`), so any Step 1
  defect found in weeks 1 and 2 is either accepted for the paper or re-ingested at 48 more
  kernel-hours. Say which.

For plan section 3:
- The ASKS object-by-object comparison was required "before implementing the global layer"
  (`log/2026-09-08/threadatlas-decision.md:150-152, 210`); the plan schedules it in the exam
  block after 2b is built (plan:111), and the audit softens the requirement to "before the
  paper" (audit:81-83) without saying it is changing the 09-08 order.
- The one-semester form, "the remaining paperwork" (`docs/proposal.md:134-135`), appears in
  neither section 3 nor section 5.

For plan section 6:
- gpt-5.6-luna and terra deprecation mid-semester (the plan worries only about gpt-4o-mini).
- API credit exhaustion during an unattended launch.
- Flex refusal rate and the standard-tier fallback.
- The advisor does not accept the slate change: no fallback path exists, and week 1 spends its
  hours before he answers.
- The 1.8 Step 1 run in progress produces packages the loader has never seen: this is listed
  (plan:151) but priced at zero.

Rulings section 4 does not ask for, and needs:
1. The reader model for all three arms (finding 5).
2. Whether the 14 development questions are excluded from the reported number (finding 13).
3. Whether the 13 other histories are ingested before 2d (finding 13).
4. Per-history packaging on Kaggle and the raised block budget (findings 1 and 2).
5. The subset sampling rule (finding 15).
6. The judge: the benchmark's evaluator or a custom one (findings 5 and 14).
7. The abstention rule.
8. What "kind agrees" means over an open vocabulary (finding 7).
9. Whether week 1 waits for the advisor's answer to the addendum.
10. Whether `CHAT_AT_ONCE` is raised: 48 kernel-hours is a constant at ingestor:2587, not a
    constraint, and Flex rate limits are the only thing that decides it.

## 22. [D] The verdict: right in direction, too kind on "sound", and silent on what a positive result would be worth

- Where: audit:9-16; state:13-20.
- "Sound resource paper": the resource is 23,882 chat documents produced by a deterministic
  unpack of an MIT benchmark with no model call (`docs/extractor.md:118`), plus 189 read
  documents of which 103 carry a flag, 50 breaks were dropped, four dates are known wrong, and
  no gold exists (`dataset/step0/LIMITS.md`). A resource-track reviewer asks what it enables
  that `longmemeval_s.json` and Gutenberg do not; the honest answer is "an LLM-chosen tiling
  of 189 books, internally verified", and the verification scripts are no longer public
  (finding 10). "Sound" is too kind; "publishable as a dataset note with its limits" is the
  size of it.
- "Unproven research paper": right. But the audit never asks what a proven one shows. Retrieval
  over LLM-written facts approaching full context at 1/50 the tokens is the result every
  retrieval baseline in the LongMemEval and Zep papers already shows; the tree's benefits are
  unexercised (finding 7); the differentiation is absent on the spine (finding 9). Even a
  green run yields "FTS5 over our abstracts is within X of full context, cheaper", which is a
  competent engineering report. The audit should say that, because it decides whether the
  fall paper should chase the number at all or write the dataset note and the design position
  and spend the hours on the insertion and deletion measurements that only this design can
  report.
- Too harsh anywhere? Only in tone toward the advisor: "nobody has said so to the advisor"
  (audit:16) is true of the slate but the 09-09 weekly did report the direction change and the
  ASKS question; the audit should credit that and name what was not reported (the milestone
  slip, the embedder, the cut order).

## 23. [F] The authorship sentence understates, and the README contradicts it

- Where: audit:138-147; `docs/proposal.md:125-128`; README.md:82 ("the author writes the code;
  AI drafts and argues but ships nothing unexamined").
- The proposed sentence ("drafted with AI assistance; every design decision, citation and
  number reviewed and answered for by the author"):
  - Understates the extent. Per the repository, the agent drafted the notebooks, the test
    batteries that check them (now untracked), the documentation, the daily logs for 09-09,
    09-11 and 09-12 written two days later from receipts (`log/2026-09-11/README.md:3-5`),
    the related-work prose (`reading/related-work/`), the proposal, the audit and the plan
    under attack here. "Drafted with AI assistance" reads as light editing; the accurate word
    is "produced by an LLM coding agent at the author's direction".
  - "Every number reviewed" is not evidenced: the 09-11 numbers were reconstructed by the agent
    from receipts with "no log kept on the day"; the check scripts are untracked.
  - "Checked by an offline test battery" (proposal:127) is a battery drafted by the same
    agent; it is not an independent check and should not be offered as one.
  - README.md:82 says the author writes the code. That sentence and the proposal's cannot both
    stand in a public repository a committee may read.
  - The docx footer the audit quotes (audit:144-145) is in a file removed from the repository at
    005f19c; the audit cites it as if checkable.
- For arXiv cs.CL: adequate on the letter (no AI author; a human answers for the content). For
  the ACL-family venues the audit names, the policy asks for the extent of assistance to be
  stated, which the sentence does not do. For a university directed project: adequacy cannot be
  judged because the course's academic-integrity rule is unknown (audit:158-162 admits this);
  the only correct action is to ask the instructor before the addendum, since a directed
  project's grade may rest on the student's own implementation in a way an arXiv preprint does
  not.
- Say instead: "Design decisions and rulings are the author's and are dated in
  `docs/rulings.md`. The code, tests, documentation and first drafts of this manuscript were
  produced by an LLM coding agent under the author's direction; the author ran every
  experiment, ruled every design question, and checked the reported numbers against the run
  receipts, which are published." Then delete README.md:82's clause.

## 24. [G] Flattery, hedges and claims without a source

- audit:10-11 "rigorous in a way most student projects are not": no comparison set; flattery.
- audit:20 "in your words where they were recorded": the 08-25 and 08-26 sessions have no file
  in the repository (the log index starts 09-02; the advisor record is 08-19); the six quotes in
  section 2 fail the audit's own rule at audit:4-5 ("every claim below names its source").
- audit:62 "Do not re-file": a recommendation about the department's process made without
  knowing what the course requires (audit:158-162).
- audit:111 "Thirty labels is an hour"; audit:83 "each is one or two hours of reading"; plan:84
  "few build hours"; plan:93 "2 hours": no basis given for any.
- audit:128 "Adequate for the track"; audit:134 "Strong where it matters"; audit:150 "Sound:";
  state:13-14 "documented to the row": verdict words used as evidence.
- audit:166-168 "call it 0 to 8 hours": a hedge spanning the whole feasibility question.
- audit:176 "fits, barely, and only if nothing else is built": a hedge that the calendar then
  violates (finding 3).
- audit:180-182 "Money. Not the constraint. ... under $300": a sum with no lines (finding 20).
- plan:22-24 "The August calibration named exactly this reach": self-confirmation by an
  unsourced quote.
- plan:117-120 "decided at the gates, never later": the gates are unreachable on the plan's own
  prices, so the valves will fire and the sentence is a promise the calendar breaks.
- audit:95-96 "the plan does": false (finding 17).
- state:180-184 "A complete modest paper beats a thin ambitious one; the choice is still open":
  the plan then chooses the ambitious spine with the modest paper as a valve, which is not
  making the choice.

## 25. [A] Smaller factual points

- audit:47 "four corpora, 81 files, 6.9M words" and audit:50 "345 questions over twelve books"
  describe the filed docx, which is now untracked (005f19c) and unverifiable from the
  repository; mark them as from the author's copy.
- audit:121 "LitBank is dead" while `docs/entity-resolution.md:293` still names LitBank as the
  attachment gold; `log/2026-09-13/questions.md:106-107` records this as unruled. The audit
  should list it as a master-document defect, not only as "BookCoref never ruled".
- state:52-55 and state:109 cite `check_flex_run.py` at a path that does not exist at HEAD
  (finding 10); `docs/extractor.md:119-120` says each turn carries "its own timestamp" while
  `log/2026-09-13/README.md:24` says turns have no times and dates are per session; both are
  true of the data (every turn carries the session's stamp) and the wording should say so.
- audit:113 "$0.22 a history" holds only at 48 sessions and the under-count of finding 20; the
  corpus mean is 50.2 sessions a history (recomputed): $0.24 to $0.25.
- plan:31 "four answer sessions dated" for gpt4_2ba83207 is confirmed by
  `log/2026-09-10/decisions-ingestor-1.7.md:17-19`; plan:101 "480 units" for the novels is
  confirmed by `dataset/step0/README.md:93`; audit:186 "16 at a time" matches ingestor:2587.
  These check out.

---

## The top twenty, in order

1. The full Step 1 run writes about 48k files to `/kaggle/working`; the extractor already failed
   at 25k (extractor:164). Plan 2e and the audit's "Kaggle time" section do not mention it.
2. Block 12's $15 budget (ingestor:2587) stops a 12-hour launch at about 3,300 sessions: eight
   manual launches, not "four or five" (audit:186, plan:87).
3. Weeks 1 and 2 (16 hours) carry 22 to 32 priced hours; the Sep 16 gate needs 10 to 16 hours in
   three days; the audit's "33 to 46 build hours" counts weeks the calendar gives to writing.
4. Every 09-13 price is roughly half the 09-08 price for the same item (README:94, 102) with no
   new information; debugging, the download, the judge prompts and the tables are priced nowhere.
5. The ThreadAtlas arm answers on Luna, the parity arm on gpt-4o-mini, and the judge is not the
   benchmark's: no number produced this way joins Zep's table or compares arm to arm.
6. The knowledge-update band with "every dated fact served" gives the reader what full context
   already has; no supersession mechanism exists, so the band measures retrieval, not the claim.
7. On chats the tree is exact-string grouping over about 900 nodes; its query cost is
   microseconds and none of its claimed benefits (insertion, deletion, re-pointing) is exercised.
8. One history per graph is fair to the benchmark but leaves the tree's contribution unmeasured;
   the missing arm is ThreadAtlas without 2b.
9. Chats get no cells, so the paper's one kept differentiation is absent from the corpus it
   measures on; the audit files this under "weakens".
10. Audit 4.5 calls reproducibility "strong" sixteen minutes after 005f19c untracked every
    verification script and test battery; the state document cites paths that do not exist.
11. "8 a week, unverified" ignores three weeks of commit and run timestamps showing several
    times that pace; the plan is priced on a number the repository contradicts.
12. GraphRAG-Bench does not need 2b (one novel per graph), has 2,010 questions, an MIT scorer
    and the proposal's open question; cutting it to a stretch is argued from sunk cost and the
    advisor loses the first committed measurement, the three-tier pilot and what he was told on
    09-09.
13. The 14 questions are the development set the prompts were tuned on, and 13 of them have no
    haystack ingested, so the 2d gate compares arms over different inputs.
14. Thirty labels cannot precede the first arm, and kappa on thirty items cannot hold a 0.7 gate.
15. Fifty histories give a 7-point standard error against an 8.4-point positioning gap and
    about 8 knowledge-update questions: a pilot, not a number with a band.
16. README, RESEARCH and evaluation-corpus still carry the 09-08 slate, two interfaces and the
    committed ablation; the 09-13 ruling makes those the current truth.
17. The audit says the plan restates the ablation; the plan cuts it and recommends against the
    condition for restating it.
18. The contamination answer is for novels; LongMemEval is a 2024 public benchmark inside the
    model's training window and no chat probe exists.
19. A full draft by Tuesday Nov 3 cannot come from week 5's hours; the paper's 10 to 15 hours
    have no week.
20. The authorship sentence understates the extent, offers an agent-written battery as an
    independent check, cites a footer in a file removed from the repository, and contradicts
    README.md:82; for the course it cannot be judged adequate until the instructor is asked.
