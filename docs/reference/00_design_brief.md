> **REFERENCE, not superseded.** This is the calendar, the hour budget, the planning rules and the eleven-risk register. Still the source of record for all of those; the fall plan quotes it rather than replacing it.
> It is background rather than part of the working set. Index: `docs/README.md`.

# Design brief: context from Justin's own records that should shape the IT 494 project

Internal document. Deliverable 0 of the Phase 1 workflow (`C:\Users\jhffm\it494-memory-project\WORKFLOW.md`). Everything here is sourced to his own files. Where the records conflict, the newer one is preferred and the conflict is named. Where nothing was found, that is stated rather than filled in.

One governing note before the calendar. The newest statement of intent on file is not in the archive at all; it is in `C:\Users\jhffm\it494-memory-project\WORKFLOW.md`, dated 2026-08-25, in his words: "providing a user level knowledge back end that can be scaled to an organization." That is more recent than `IT494_PLAN.md` (2026-08-22, verified mtime) and more recent than every leaf in the era tree. It also carries a second live instruction: "I don't even know that knowledge graphs are the way I want to go." The professor asked him to explore the knowledge-graph domain, so the survey happens, but nothing in the package may frame this as a knowledge-graph project. Every design decision below is judged against the scalable-backend statement, not against `IT494_PLAN.md`'s cold-start framing, which is three days older.

---

## 1. The calendar, concretely

### What is already spent

The ISU semester began 2026-08-17 (`C:\Users\jhffm\claude-archive\eras\school-classes\fall-2026\it483-os\2026-08-17_os-course-start-and-memgpt-anchor-paper_0867e348.md`). As of today, 2026-08-25, week one and most of week two are gone, and the record of what they produced is thin: the IT 427 week-one check-in leaf states plainly that the session produced no study, having offered three directions and had none chosen (`eras\school-classes\fall-2026\it427-algorithms\2026-08-19_algorithms-week1-checkin_e12767ce.md`). The fall has about fourteen usable weeks left, not sixteen.

### The two structurally dead days

Both ISU courses meet in person, Monday and Wednesday, at ISU Normal. IT 483 runs 2:00 to 3:15 PM in Stevenson Hall 104; IT 427 runs 6:30 to 7:45 PM in STV 105 (`C:\Users\jhffm\it483-os\reference\syllabus_facts.md`; `C:\Users\jhffm\it427-algorithms\README.md`, both verified). The commute from Dahinda is recorded twice and the figures conflict: "one hour away" in the October 2025 planning leaf and "1:20 each way" in the April 2026 one (`eras\school-classes\degree-logistics\2025-10-13_mscs-spring2026-planning-vre_68ed28db.md` versus `2026-04-01_mscs-degree-planning-isu-uiuc_69cd559c.md`). The later and more specific figure governs. He built the schedule deliberately around holding campus days to two per week.

That puts roughly 8.5 hours door to door on each of Monday and Wednesday, about 17 hours a week, of which the only working time is the 3h15m gap between the two classes. That gap is the largest reliably free block in his week and it is already paid for, but it is a laptop-and-reading block on a campus, not a lab block. Reading, writing and analysis fit it. Building does not.

A practical consequence for tomorrow and every future meeting: never schedule an advisor meeting, a demo or a deadline on a Monday or Wednesday afternoon or evening.

### The fixed graded calendar

Consolidated from `C:\Users\jhffm\uiuc-cs425\reference\deadlines.md` (verified in full) and `C:\Users\jhffm\it427-algorithms\README.md`. All CS 425 times are 11:59 PM US Central, and the deadlines page corrects an earlier record: homework is due at midnight, not 2:00 PM, because the 2:00 PM rule is the on-campus deadline and he is section DS4.

| Date | Item |
|---|---|
| Sep 6, 13, 20, 27 | CS 425 Part 1 quizzes 1 through 4 |
| **Sep 17** | **CS 425 HW1** |
| **Sep 30** | **IT 427 Test 1** (in person, evening) |
| **Oct 4** | **CS 425 HW2** |
| **Oct 9 9AM to Oct 11 11:59PM** | **CS 425 midterm window** |
| **Oct 16** | **CS 425 Part 1 programming assignment** |
| Oct 18 | Part 1 Quiz 5 and Part 1 Final Quiz |
| **Nov 1** | **CS 425 HW3** plus Part 2 Quiz 1 |
| Nov 8, 15 | Part 2 quizzes |
| **Nov 18** | **IT 427 Test 2** (in person, evening) |
| Nov 22, 29 | Part 2 quizzes |
| **Dec 3 (Thu)** | **CS 425 HW4** |
| **Dec 6** | **CS 425 Part 2 Final Quiz** |
| **Dec 7** | **CS 425 Part 2 programming assignment** |
| **Dec 11 to 13** | **CS 425 final exam window** |
| **Dec 1 to 15** | **PhD application deadlines** (`C:\Users\jhffm\.claude\projects\C--Users-jhffm-dnd-campaign\memory\phd-application-track.md`) |

Layered on top: IT 427 also runs seven to eight Python programming assignments with a written approach and performance analysis each, plus homework due at the beginning of class with five points off per day late, walking in late included. IT 483 adds four or more C programming projects, weekly quizzes, pop quizzes with no makeup, and a Portfolio/Case Study worth 20 percent of the grade that the syllabus never defines.

### Which weeks are already lost

Working from the table, the fall splits cleanly.

**Dead:** Sep 28 to Oct 4 (Test 1 and HW2 back to back). Oct 5 to Oct 11 (midterm window). Oct 12 to Oct 18 (MP1 due 10/16, then two quizzes on 10/18). Nov 16 to Nov 22 (Test 2 plus Thanksgiving week). Nov 30 to Dec 13 (HW4, final quiz, MP2, finals, and the entire PhD application window on the same fourteen days).

**Open:** Aug 25 through Sep 27, with HW1 taking a bite around 9/17. Oct 19 through Nov 15, with HW3 taking a bite on 11/1 and quizzes on 11/8 and 11/15.

That is roughly nine usable weeks, in two blocks, and they are the only two.

### The weekly hour budget

No record anywhere states his actual study hours. What follows is arithmetic over sourced fixed commitments and should be handed to him for correction rather than treated as a finding.

Seventeen hours a week to campus and class. Outside-class work for three graded courses, two of which forbid AI assistance on assigned work and therefore cannot be compressed with the tooling he uses everywhere else (`C:\Users\jhffm\it427-algorithms\CLAUDE.md`; `C:\Users\jhffm\it483-os\reference\syllabus_facts.md`). Non-campus working days are Tuesday, Thursday, Friday and weekends, minus roughly one drill weekend a month.

A realistic IT 494 allowance is six to ten hours in a normal week, near zero in the five named dead stretches, and zero from Nov 18 through year end. Total fall project budget: **70 to 100 hours, concentrated Sep 1 to Nov 15.** Design to that number, and put it in front of him to correct.

### Unknowns that will change this calendar

Three holes, all of them real and none of them fillable from the records.

**Fall drill dates are not in the archive.** Cross-checked two ways, by keyword search across `eras\` and by a Python walk over every markdown file matching drill, IDT or battle assembly with a fall month and 2026 in scope. Fourteen hits, none of them a Fall 2026 date. The record shows he possesses a drill schedule (he submitted it to GAO HR in April, `eras\internship\gao-admin\2026-04-27_gao-onboarding-docs-transcripts-drill-schedule-hr-mentor-emails_41fb40d6.md`), but no leaf, node or ledger row carries September through December. History says roughly one weekend a month at Peoria, occasionally four days Thursday through Sunday (`eras\army-reserve\personnel-admin\2026-03-23_guard-at-and-drill-scheduling-c_69c16898.md`). Expect four-plus multi-day holes at unknown positions. Ask him.

**IT 483's midterm and final dates do not exist anywhere.** The syllabus page titled "Tentative schedule" contains no schedule table, and the final exam date comes from the University through My Illinois State (`C:\Users\jhffm\it483-os\reference\syllabus_facts.md`). That is 48 percent of one course's grade sitting on two unknown dates that will land inside the table above, most likely making December worse.

**His medical calendar is unreadable.** On 2026-08-16 the Google Calendar connector was refusing every call including simply listing calendars, and the household's hand-entered appointments live only on the Family calendar (`eras\household\family-logistics\2026-08-16_upcoming-appointments-and-the-calendar-blind-spot_3d4c26cc.md`). Two appointments he believed existed could not be located. A clean search result is not an empty calendar.

### Spring 2027, briefly, because it is not a relief valve

IT 494 is the ISU MSCS Project option and runs across both semesters, supervisor Dr. Xing Fang, graduating Spring 2027 (`eras\school-classes\degree-logistics\2026-04-01_advising-graduation-plan-it494_69cd30d7.md`, reconfirmed `2026-07-22_mscs-plan-final-vre-docs_071ce2b0.md`). Spring is IT 426, IT 428 and the second half of IT 494, plus whatever UIUC course comes next. It is not lighter than fall. Anything deferred out of fall lands in an equally full spring, on which both the graduation date and the May 2027 GAO conversion eligibility depend.

---

## 2. What the project must produce to serve his career, with dates

### The gap it is closing

His PhD profile has exactly two holes: no peer-reviewed publications and no research-faculty letter. Academics are not among them (GRE 333 with a 170 quantitative, 4.0 in both master's programs, 3.83 undergraduate). The decided fix is IT 494 with Fang as a "measurement-first semester (eval harness, vector-RAG baseline, ablations) aiming at a workshop paper or arXiv preprint by December" (`C:\Users\jhffm\.claude\projects\C--Users-jhffm-dnd-campaign\memory\phd-application-track.md`).

Half of that is already closed and the package should stop spending effort on it. **Letters are committed:** Fang for research, Jaren Haber for research practice, Andrew Kurtzman for impact. The only remaining logistics is a one-page brag sheet to each when portals open in November; he declined to formally request them until he has applied to something (`phd-application-track.md`; `eras\career-job-search\strategy-and-playbook\2026-07-29_phd-track-doubts-and-relocation-clock_451253f8.md`). So the project should not be designed around getting a letter. It should be designed around giving Fang something specific to say, and around feeding that November brag sheet.

### The dated ladder

**Wednesday 2026-08-26, the meeting.** Written agreement from Fang on the topic change. This is the single highest-value outcome of the meeting and it is administrative, not intellectual. The approved April 2026 proposal on file is a practical survey of LLM/NLP tools on government documents; the topic pivoted on 2026-07-29 and nothing in any source shows Fang agreeing (`IT494_PLAN.md`, Risks section, verified: "This is the first action and everything else waits behind it"; `eras\school-classes\degree-logistics\2026-07-29_grad-project-memory-framework-and-eval-corpora_451253f8.md`; a 2026-08-15 audit row in `ledger\sheets\it-494.md` states the file position as undecided). Also to be decided in the room: one paper or two (see below).

**Early September, the paperwork.** The ISU IT 494 proposal form allows only one semester at a time, which is why the project was split into two one-semester proposals in the first place. Fang signs the CHAIR line, then Justin forwards the signed form to Kelly Hasselbring and Dr. Tang for the course permit (`eras\school-classes\degree-logistics\2026-04-06_itk494-directed-project-proposal-llm-nlp-tools_49eb34c5.md` and `2026-04-08_it494-project-supervision-emails_69d640bc.md`). A changed fall topic means a new one-semester proposal written and signed on that routing.

**By roughly Sep 15, the outreach artifact.** Professor outreach emails are planned for September and October with the memory-tree artifact attached, aimed at a named, metro-constrained shortlist: Iyyer at UMD, Khashabi at JHU, Yao at GMU, Yang at Georgetown, Zhou at UMD, plus Bau at Northeastern, Andreas at MIT, Du at Harvard (`eras\career-job-search\strategy-and-playbook\2026-07-28_phd-program-exploration-and-fit_6b14c112.md`; `phd-application-track.md`). This is a deliverable that predates any result: a short, self-contained system note, two pages, that a busy professor can read in four minutes. It is due about four weeks from now, well before the measurement work produces anything.

There is also an unconfirmed action sitting on him from the same session: email online-mcs@siebelschool.illinois.edu to ask whether an online MCS student can register for CS 597 individual study. The degree rules permit it and it is notably not barred to online students the way CS 491 and CS 591 are. Nothing on record shows the email sent.

**By Nov 15, the paper.** Not December. His own stated target is a preprint by December, and December holds HW4 on 12/3, the Part 2 Final Quiz on 12/6, MP2 on 12/7, the CS 425 final window 12/11 to 12/13, and PhD deadlines 12/1 to 12/15. That is not schedulable. If the preprint is meant to strengthen the applications, it has to exist before they are written, which pulls the real deadline forward three to four weeks and lands the writing in the week of IT 427 Test 2. The fall deliverable must therefore be complete and posted by roughly **November 15**, and the plan should treat that as the hard date.

**November, the brag sheets.** One page each to Fang, Haber and Kurtzman when portals open.

**Dec 1 to 15, the applications.** Eight to ten advisor-named applications. December belongs to this and to finals. No project work.

**Spring 2027, the symposium.** His stated end state is a poster board with a QR code that a visitor scans and it sets the whole system up for them, with the distribution model already decided: not a hosted service and not an install script, but a downloadable self-describing folder the user points their client at (`memory\grad-project-memory-tree.md`). He has run the ISU symposium circuit before (`eras\school-classes\ERA_SUMMARY.md`, spring-2026 symposium node, six leaves). That is a working-software bar, not a paper bar, and it is a spring item. It constrains fall engineering only in one way: the system has to be extractable from his own hardcoded setup.

### The two-paper question, which the meeting should settle

There are two candidate papers on record, not one, and the most recent record leaves the choice open and in the advisor's hands.

The **GAO EES method** is a finished result with verified numbers: 7,218 comments to 25,785 sentences to 14,700 blobs to 70 topics, roughly a 70 percent sentence collapse, pinned in `C:\Users\jhffm\internship-landing\NUMBERS.md` with a `GAO_CLOSEOUT_FACT_SHEET.md` alongside. No new experiments needed. An arXiv preprint of it was recorded on 2026-07-31 as "the concrete artifact the PhD track needed" (`ledger\facts.txt` rows 199 and 1990; `eras\internship\ERA_SUMMARY.md`). Then on 2026-08-17, drafting the outreach email to Fang, he deliberately "softened the preprint line from a statement of intent to an offer," meaning he would convert the work if the advisor thinks it worthwhile (`eras\school-classes\degree-logistics\2026-08-17_advisor-outreach-email-and-claim-verification_fd97111d.md`). That is the newer record and it governs: undecided, offered, not promised.

The **memory-system evaluation** needs a harness built from scratch inside the nine-week budget.

The EES route is the low-risk November paper. The memory route is the one that matches the topic and the letter. Trying both inside 70 to 100 hours is not credible. Put the choice in front of Fang as a decision, not as a plan.

---

## 3. The unfair advantages, and what the project must not require

### Build on these

**The corpus.** Re-counted from disk today: `eras\` holds 1,229 markdown files, `ledger\facts.txt` holds 2,113 dated assertions, and `ledger\sheets\` holds 1,120 rendered per-entity sheets. Two years, ten life eras, three assistants. He articulated its structural property himself: a private archive is uncontaminated by construction, which turns n=1 from a weakness into the evaluation's one structural advantage (`IT494_PLAN.md`). This is unpurchasable and no other student has it. The project must be built around this corpus, not around a public benchmark.

**A running system that measures itself while he is elsewhere.** Roughly 5,800 to 6,600 lines of stdlib-only Python across `claude-archive\scripts\` and `mcp_server\`, with `rollup_tools.py` alone at 2,906 lines and 32 selftest checks, plus a further ~3,280 lines in `C:\Users\jhffm\agent-memory-kit\prototype\` with 35 tests and 19 written lessons. Nightly, weekly and monthly passes already run on OS schedulers with a metrics layer, a failure log and a staleness signal (`eras\_maintenance_log.md`; `OPERATIONS.md`, 87 KB, v3.3). This is the most important fit in the whole brief: **a measurement-first project whose data accrues on a scheduler is compatible with his real calendar. A project requiring continuous hands-on hours is not.**

**Agent fleets.** He routinely runs multi-agent Claude Code workflows at a scale most solo students cannot absorb: 128 agents on one deep-research task, six parallel agents plus two rollup builders for the ~205-leaf coverage wave at roughly 2M agent tokens, four auditors on combat simulations, twelve lenses on the August system audit (`EXPERIMENTS.md`, E1, verified; `eras\claude-archive-meta\ERA_SUMMARY.md`). Labeling 100 to 150 gold answers and running three evaluation arms is tractable for him. One caveat from his own record: five of twelve audit lenses died on API errors and returned a confident-looking partial result, so any agent-run evaluation needs completion accounting.

**Measured failure modes he already owns.** Thirty-nine node claims traced to raw transcripts gave 31 confirmed, 4 wrong, 4 unsupported, and every one of the eight defects lived in the synthesized rollup layer while all 31 leaf-level checks were clean (`eras\claude-archive-meta\maintenance-and-review\2026-08-21_cold-audit-from-disk_faba7b9a.md`). The faithfulness gate structurally cannot see this, because a hardened sentence is still entailed by its hedged source. Separately, a mutation study broke ten real things and ran every gate: three produced a failing exit code, two a warning at exit 0, and five produced nothing at all (`2026-08-21_backend-repair-and-neutral-assessment_1a84e5f9.md`). These are localized, dated, reproducible defects that no published evaluation grades. They are a paper.

**Evaluation experience he is not crediting himself with.** He benchmarked six Wordle solvers against Bertsimas and Paskov's 3.421 published optimum and raised the vocabulary-sensitivity objection about the expanded guess list (`eras\school-classes\spring-2026\machine-learning-it448\NODE_SUMMARY.md`). He hit 0.9135 private leaderboard on IEEE-CIS fraud with time-aware GroupKFold and explicit no-leakage restructuring. He ran E1 on his own system and correctly diagnosed that one improvement was a query failure rather than a coverage failure, adopting agentic multi-query as protocol. Gold-standard construction, held-out discipline and construct-validity critique are already in his hands. Surfacing this back to him is legitimate. Handing him a finished evaluation design is not (see section 4).

**Production ML delivery under hostile review.** He rebuilt GAO's EES pipeline into a four-phase production architecture and shipped it, and separately owned FACET end to end: BERTopic over 93,755 reassembled findings producing 24 topics with zero outliers, shipped as a GitLab merge request (`dossiers\ees-pipeline.md`; `dossiers\facet.md`). The IT 494 write-up can cite production work rather than a class project.

**Domain knowledge as the actual edge.** The decisive technical move at GAO was recognizing that GAO is legislative branch, so the OPM FEVS mandate does not apply, which is what let the instrument's own nine indexes become the frozen anchor taxonomy. The record calls this "the load-bearing move that made the taxonomy defensible" (`dossiers\semantic-classification.md`). His edge is knowing which structure already exists in the world to be borrowed rather than induced, not raw modeling sophistication. Frame accordingly.

**A CH-47 pilot's operational demonstration.** At Northern Strike 26.2 he ran concurrent chats for flight schedule, storyboard, weather board and situation report against one shared knowledge base, pulling images and video out of email and matching them against the mission tracker, AMRS and the flight schedule by metadata (`eras\army-reserve\at-ns26-2\NODE_SUMMARY.md`). This is the concrete demonstration that engaged Fang.

### Do not require these

**A GPU, model training, or fine-tuning.** No personal GPU is on record. The only GPU material is a 2025-11-22 chat where the dedicated GPU was not detected and the issue was left unresolved (`eras\household\tech-support\NODE_SUMMARY.md`). HPC access (ISU aspen, SDSC Expanse) appears only in the Spring 2026 IT 388 course context with no record of it continuing. Stay on API calls and local CPU sentence-transformer embedding, which is exactly what the GAO stack did.

**Anything from GAO.** All of it ended 2026-07-28: AWS Bedrock and Nova Pro in GovCloud, Posit Workbench and Connect, the self-hosted GitLab, and the EES and FACET data. The archive's own open-questions register is full of `[VERIFY]` items that can now never be checked (`dossiers\open-questions.md`). The GAO work is citable as experience and method; no result from it can be re-run or extended.

**The held-out corpus.** `eras\army-reserve\` is gitignored and quarantined local, nine of eleven AT transcripts are held out by UUID, and the health-era rule was reversed on his direction in August but military CUI still holds (`eras\army-reserve\ERA_SUMMARY.md`; `OPERATIONS.md` v3.3 changelog). Any published question set draws from the shareable subset only, and the methodology must say so up front rather than discover it late.

**Sustained personal grind.** Hypertrophic cardiomyopathy with a prior NSTEMI, training under a prescribed heart-rate cap, and a documented instance of two consecutive low-productivity days after back-to-back hard sessions (`eras\health\cardiac\NODE_SUMMARY.md`; `2026-06-17_gpt_fatigue-after-heavy-cardio-hcm_6a32c887.md`). Overnight agent waves are fine because the agents work. A schedule that requires him personally to grind is not.

**Uncapped API spend.** He has already hit `credit_balance_exhausted` on the image-generation pipeline (`ledger\facts.txt`, 2026-08-17 row).

**A network he does not use.** Job-search scope is federal only, stated 2026-07-26. He does not use LinkedIn and does not want LinkedIn-centric advice (`memory\justin-role-gao-reserve.md`; `memory\internship-landing.md`).

---

## 4. What is settled and must not be relitigated

**The topic.** IT 494 is the memory system. The LLM/NLP tools survey was abandoned 2026-07-29 with his own line: the memory structure "would be the engine behind it all that keeps the world consistent." Do not re-propose the tools framing.

**Architecture novelty is conceded, on his own investigation.** Three adversarial reviews in August converged: the engineering is sound and there is no research contribution as currently framed. Zep and Graphiti (arXiv:2501.13956) already built bitemporal invalidation; GraphRAG (arXiv:2404.16130) already published hierarchical community summaries, which is the fold step (`IT494_PLAN.md`, verified). He found this prior art himself and recorded it rather than working around it. Re-presenting the tree as novel relitigates a settled loss.

**Five candidate contributions are dead or downgraded with citations attached** (`dossiers\agent-memory-literature.md` §13): evidence-quote validation (Governed Persistent Memory, Eywa do the stronger fail-closed form); n=1 over two years (MyLifeBits, autobiographical design at DIS 2012); fixpoint refolding (MemForest, and incremental view maintenance generally); the metric gate componentwise (ChronoMem, ConsistencyGate, EvolveMem), which must not be headlined.

**Two claims survived** and both are cheap to demonstrate this semester: the rotating source audit, whose weakness is that he does not have the number yet, and the non-growth ratchet on the agent's own maintenance code, whose weakness is that it is a policy rather than a mechanism and is unmeasured. Named as strongest defensible: hash-recomputed staleness as a self-checking correctness property in a human-editable store, demonstrable by hand-editing N leaves and showing that dirty-flag schemes miss them.

**Do not try to beat Zep on LongMemEval.** Recorded verbatim as an anti-goal: "a loss and not his edge" (`eras\claude-archive-meta\memory-architecture\2026-08-14_learned-db-and-the-airframe-argument_750c1146.md`). Benchmarks are for task definitions and comparability, not for winning.

**Facts cannot be wrong.** The founding rule of the fact layer is his: nothing is ever overwritten, every row carries the date the source asserted it, and deciding what is current is a judgment made at read time rather than a destructive update at write time. His reason: "the whole point of this over semantic search is that relationships change" (`eras\claude-archive-meta\memory-architecture\2026-08-20_fact-ledger-design-and-handoff-kit_7900c75a.md`). Any proposal involving invalidation-on-write contradicts it. Note the live tension worth naming honestly rather than hiding: Zep's bitemporal invalidation is the published answer to fact expiry and he has deliberately chosen the other side.

**Automatic temporal inference was built and then deleted**, not repaired, "because it was the thing Justin had explicitly said not to build. Four defect classes went with it. That is the strongest result in the session: the fix was subtraction." Do not re-propose it.

**A vector store is deferred, not rejected, and the reason is specific.** Summaries encode editorial curation and supersession judgment that cosine similarity cannot supply. Separately measured: at roughly 950 documents a vector store is not warranted, brute-force exact cosine is correct, and the crossover is around 100K vectors. The one endorsed embedding role is a semantic index over leaf text as an escape hatch from wrong-branch descent, with a worked example (a NODE_SUMMARY flattened an open CBC out of existence, recoverable only by descending, where an embedding index would have hit "hematocrit" in zero hops) and a cost model in which the atomic unit is the hop.

**Entities are a secondary index over the same rows, not a branch of the tree**, and structure should be multi-parent DAG membership rather than an exclusive taxonomy. Relations are expensive to maintain and are "the entire reason the system is worth building."

**Three subsystems are dead by decision as of 2026-08-21** (`OPERATIONS.md` v3.2 changelog): the old entity layer under `eras\entities\` ("a concordance of quotes is not knowledge"), `abstracts\`, and the hosted remote MCP server with its Docker and fly.toml scaffolding. Do not resurrect them.

**Distribution is not a hosted service.** Downloadable self-describing folder, user points their own client at it. Also settled: official exports do not include user files and images, so attachments must be scraped through the authenticated browser once at onboarding. Do not re-suggest exports.

**Delete authority has not been granted.** The tree only accretes and nothing decides a leaf has stopped earning its place. The write-ahead-log argument that would make pruning safe is written; the permission is not given (`2026-08-14_learned-db-and-the-airframe-argument_750c1146.md`).

**Campaign 2, the AI-run D&D table, is out of scope**, explored and rejected 2026-07-29 and listed under scope creep in `IT494_PLAN.md`: "It borrows the architecture; it is not a deliverable." One unreconciled remnant to flag rather than propose: the same 07-29 session floated "semester 2 = an AI DM demo," and the auto-memory records it as a tension, not a plan.

**Personal information in the private archive is settled and marked never-raise-again.** He accepts the risk because isolating it makes the tool useless; only military CUI still warrants a hold, and the blanket health-era off-cloud rule was reversed on his explicit direction 2026-08-23 with `OPERATIONS.md` instructing that it not be restored as a regression fix (`memory\sensitive-info-risk-accepted.md`). The existing guard architecture is an asset for the cold-start privacy story, not a problem to re-solve. This does not extend to credentials (see Risk 2).

**Two framings he has corrected and told Claude to stop using.** The GAO result is not a cautionary tale about classification: "this isn't fair. My GAO work determined that we can pick out central ideas from human text even if rigid classification fails." What failed was narrowly deriving a parent taxonomy from embedding geometry, because the embeddings carried shared register rather than subject. And Hayek is about dispersed knowledge, the center being unable to reconstruct what the periphery holds, not a generic caution that summarization loses detail: "you don't even understand the hayek reference and you keep bringing hayek back up" (`eras\school-classes\degree-logistics\2026-08-19_it494-advisor-meeting-and-voice-correction_686f584b.md`).

**The GAO back-door plays are closed.** The VR&E route into GAO (NPWE, SEI, an IEAP amendment, an exit-review billet ask, a McGree email left unsent in drafts) was built 2026-07-22 and explicitly set down 2026-07-26, whose standing rule names NPWE arrangements as exactly the kind of maybe he will not trade time for. The archive still contains an elaborate live-looking plan. Treating it as open misreads the record.

**Do not hand him a finished evaluation design.** His words at the close of the 08-19 session: "validating and improving the tree to something real and tested would be a good use of time," immediately qualified with "but we currently don't know how to do that." The leaf carries a standing instruction: do not propose an evaluation design for him unprompted, because that is the open question, not a gap to fill. Present options with tradeoffs.

**The three-bucket voice rule.** At the exploration stage, documents in his voice carry only what he knows. His experience, what was said in the room, and Claude's survey output are three separate buckets and bucket three never wears bucket one's voice. It took four correction rounds to establish and is saved to auto-memory as `stage-appropriate-knowledge`. His framing: "there will come a time when I use you to ingest all these ideas and further my understanding of the knowledge space, but we are not there yet." This is a formatting requirement on every deliverable, not a stylistic preference.

---

## 5. The context he did not restate, and why it changes the design

This is the section that earns the brief. Fourteen items, ordered by how much they should move the plan.

**1. The December target is not schedulable, and he has not noticed the collision.** His stated goal is "a workshop paper or arXiv preprint by December" (`phd-application-track.md`). December holds HW4 on 12/3, the Part 2 Final Quiz on 12/6, MP2 on 12/7, the CS 425 final 12/11 to 12/13, and 8 to 10 PhD applications due 12/1 to 12/15. The preprint is supposed to strengthen those applications, which means it has to exist before they are written. **The real date is Nov 15, and nothing in the records has yet moved it there.**

**2. His own memory tree understates his semester by a whole course.** `eras\school-classes\fall-2026\` contains only `it427-algorithms` and `it483-os` nodes, and the 08-17 leaves state "Fall 2026 load now fully on record: IT 427, IT 483, IT 494." CS 425 was confirmed 2026-08-24 and exists only in the auto-memory card and the `C:\Users\jhffm\uiuc-cs425\` workspace. Any plan assembled from the era tree alone is wrong by 4 credit hours and two individual C++ programming assignments worth 45 of 181.75 points. This is also, incidentally, a live demonstration of the tree's own lag that the paper could use.

**3. Everything in CS 425 was released on day one.** All ten weekly quizzes, both final quizzes, and both programming assignments (`C:\Users\jhffm\uiuc-cs425\reference\deadlines.md`, verified). The deadline table is a list of latest acceptable dates, not a schedule, and weekly quizzes are unlimited-attempt with the best score kept. **This is the single most actionable schedule move available:** 31.75 points, 17.5 percent of the course, can be banked in the next three quiet weeks and removed from every pileup, and MP1 can be built well before 10/16. Nothing in the records shows him having done this.

**4. IT 483 has an undefined 20 percent deliverable and he has already built the bridge to it.** The syllabus lists a Portfolio/Case Study at 20 percent that the body text never describes (`it483-os\reference\syllabus_facts.md`). Meanwhile `C:\Users\jhffm\it483-os\project\os_to_memory_tree_bridge.md` already maps his archive onto file-system theory: the weekly pass as fsck, pass open and close as TxB and TxE, and LFS naming the fold cascade as the recursive update problem, with the honest note that the analogy breaks because LFS cleaning is lossless and folding summaries is lossy. Sixteen OSTEP chapter notes are written, and MemGPT (arXiv:2310.08560) is the settled anchor paper. **The IT 483 portfolio and the IT 494 fall deliverable could be the same work, which is the cheapest hour available all semester.** Two caveats already in his record: MemGPT lands on virtualization rather than persistence, which is a live risk to the framing, and IT 483's AI policy bans AI on assigned work and requires prompt screenshots whenever used, so this needs a written question to Dr. Chaudhari before he commits.

**5. Two live GitHub personal access tokens are still committed and unrevoked.** A classic `GITHUB_TOKEN=` in a 2026-04-12 transcript and a fine-grained `github_pat_` in a 2025-08-30 one, both in the private archive's pushed history, so they must be revoked on GitHub rather than deleted (`eras\claude-archive-meta\maintenance-and-review\2026-08-22_cold-audit-two-gates-and-two-tokens_fd8d065d.md`). Verified still open in the open_threads of the newest leaf on disk, `eras\claude-archive-meta\recall-plumbing\2026-08-24_pc-handoff-completion-overnight_live-session.md`: "Pre-existing and still open: 2 credential-shape transcripts to revoke." The settled decision about his own PII does not extend to credentials. **If any part of the archive becomes a research artifact, a poster, a public repo or an installable kit, this is a hard blocker, and it is the most time-sensitive item in the whole record.**

**6. His August retrieval numbers are contaminated by a broken transport.** The 08-11/08-15 twelve-lens audit reported cold recall at 11/15 in both tree-walk and MCP mode with 13/15 correct-leaf top-3 hits, and concluded "every single miss traced to stale or missing content rather than to search." That conclusion was later contradicted: both MCP servers had crashed on startup from 2026-08-11 to 2026-08-21 because an unrelated project's pip install downgraded anyio in the one shared site-packages (`2026-08-21_backend-repair-and-neutral-assessment_1a84e5f9.md`). **Any baseline for the fall benchmark must be re-measured on a verified-live transport, and the health check must launch the real process rather than import its data module.**

**7. The plan of record's own numbers are stale and low.** `IT494_PLAN.md` (2026-08-22) states "~1,000 leaves" and "1,498 dated assertions over 134 source documents." Counted from disk today: 1,229 markdown files under `eras\`, 2,113 rows in `ledger\facts.txt`, 1,120 rendered sheets. It also claims 24 automated gates while the 2026-08-24 leaf reports invariants at 21/24. The archive's own rule is to re-run counts rather than restate them. **Re-count before any number goes in front of Fang.**

**8. There is a measured, localized, unpublished failure mode sitting in his own logs.** Thirty-nine node claims traced to raw transcripts: 31 confirmed, 4 wrong, 4 unsupported, and all eight defects in the synthesized rollup layer while all 31 leaf checks were clean. "Distillation from transcript to leaf is working. The roll-up from leaf to node is manufacturing false confidence, in exactly the layer a fresh session reads first." The faithfulness gate structurally cannot detect it because a hardened sentence is still entailed by its hedged source. This is corroborated by the 08-17 incident where eight false claims were caught in a draft email to this same supervisor and three of them originated in the archive's own summaries rather than the draft, with the leaf noting that "the same sentences were headed for a PhD application." **This converts an embarrassment into the paper's motivating example, and it is a study that fits the nine-week budget.**

**9. His own evidence chain has been dormant for a month.** `EXPERIMENTS.md` was created 2026-07-26/27, contains exactly one entry, E1, and the file's mtime is still 2026-07-26 (verified). E1 is genuinely good: coverage 67.3 to 99.9 percent, retrieval 3.5/5 to 8/8, the coverage-versus-vocabulary failure taxonomy, the adopted agentic-multi-query countermeasure. **Reviving E1's format is cheaper than inventing an evidence framework, and the fall benchmark should be E2 in the same file rather than a new apparatus.**

**10. Coverage figures have an honest denominator problem.** 219 Gemini conversations carry no parseable conversation id and are invisible to coverage, drift detection and the entity build, so a reported 99.6 percent coverage excludes roughly 21 percent of the corpus. The id scheme is still queued for him. This is a small data-engineering fix that would materially strengthen the fall measurement work, and it is an obvious reviewer attack surface if left unstated.

**11. Fang's actual assignment was reading and problem-framing, not building.** He asked for two things: write down everything they discussed, and use an LLM to read some articles (`2026-08-19_it494-advisor-meeting-and-voice-correction_686f584b.md`). And what engaged him was not the architecture but that the system had been useful, specifically for large multi-chat projects sustained over time. Justin deliberately withheld his own system until the end so the topics would stand on their own. Fang also steered him in April away from an academic build toward a practical survey (`2026-04-06_itk494-directed-project-proposal-llm-nlp-tools_49eb34c5.md`). **A package that arrives with a designed experiment answers a question Fang did not ask and skips the stage he set. Lead with the working system and its real use.** The tension worth naming: the PhD letter wants something paper-shaped and Fang has twice steered practical.

**12. Descoping IT 494 mid-semester is not free.** VR&E Chapter 31 funds the degrees and pays only for degree-applicable credit; dropping below full time can trigger overpayment and stipend changes, and the project-option switch itself required VRC approval through counselor Michael McGree (`eras\school-classes\ERA_SUMMARY.md`; `2026-02-25_isu-ml-course-drop-grievance-vre-transfer_699f17d2.md`). IT 494 is 3 of the 9 ISU hours that constitute full-time. **This is the strongest argument in the whole brief for designing a deliberately small, finishable fall deliverable rather than an ambitious one he can shrink later.**

**13. Money is not the binding constraint, and the design should spend that freedom.** 100 percent permanent and total VA disability at roughly $54k a year tax-free, VR&E funding the degrees, Jessica working full time as an RN. The recorded worry is narrower than income: living on student loans against expected disability forgiveness, and GI Bill and VR&E stacking against assistantships still needing verification with a school certifying official. He can afford to optimize the fall for the strongest application rather than the nearest paycheck. He also has no employer claim on his weeks this fall, since the GAO internship ended 2026-07-28 with "you are eligible to convert" and "we are not hiring," and the Pathways conversion authority does not vest until the degree completes in Spring 2027.

**14. The federal job search is currently posture rather than work, and it will restart.** No job-search activity is recorded anywhere since March 2026; the `federal-apps` node spans 2025-12 to 2026-03 and its only August entries are document imports of a January resume and older essays. Cross-checked by directory listing and by grep for usajobs. It is not competing for time this month, but historically each federal application consumed a multi-hour tailored build, and the fall plan should not assume the whole semester belongs to IT 494.

**Two smaller items worth carrying.** His standing rules from the internship closeout are "never again trade time for a maybe" and "nothing boring," summarized as "permanent and interesting or do not apply" (`eras\internship\ERA_SUMMARY.md`). A fall scoped as pure benchmark construction with nothing intellectually live until spring fails his own filter. And the Cyc objection to the learned-database framing was flagged in his own notes as needing a one-sentence answer ready before IT 494 review; the prepared answer exists (symbolic AI failed on the authoring bottleneck, and LLMs removed exactly that bottleneck) but the thread is still marked open.

One item found and worth stating plainly so nobody mines it again: `dossiers\open-questions.md` is not about this project. It is the GAO internship's verify-in-environment register (FACET v2 thresholds, EES deploy blockers, Posit Connect permissions), synthesized 2026-07-13 and largely superseded by the internship's end. The project's open threads live in the `claude-archive-meta` leaf frontmatter and in `IT494_PLAN.md`'s risks section.

---

## 6. Five rules the project plan must satisfy

**Rule 1: nine weeks, eight hours, two blocks.** No milestone may be placed outside Aug 25 to Sep 27 or Oct 19 to Nov 15. The plan assumes a ceiling of eight hours in a normal week and zero in a dead one, for a fall total of 70 to 100 hours, and it presents that figure to Justin for correction rather than asserting it, because no record states his actual study hours. Any plan whose arithmetic exceeds this is rejected on sight.

**Rule 2: complete by November 15, or it does not count.** The fall deliverable must be finished, committed and citable by Nov 15 so that it can appear in applications due Dec 1 to 15 and in the November brag sheets. December is not available. A plan that targets December targets nothing.

**Rule 3: the machines do the hours, not the man.** Every measurement in the plan must run on the existing scheduled automation (`rollup_tools.py`, the nightly and weekly passes, the metrics and failure logs) or on agent fleets, extending `EXPERIMENTS.md` as E2 rather than building a new apparatus. No GPU, no training, no fine-tuning, no new subsystems, no re-architecture. Where an agent fleet runs an evaluation, the plan must include completion accounting, because five of twelve lenses have died silently before.

**Rule 4: every milestone ends in a committed artifact that survives a two-week interruption.** His own record shows an "evening of work" item deferred for weeks by calendar pressure and a scheduled maintenance pass dying mid-run while the staleness signal read green for five days. Milestones must be resumable and must never end in a state only he holds in his head.

**Rule 5: provenance on every claim, primary sources for every number.** Documents in his voice carry only what he knows, with survey output labeled and separated. Every figure is re-counted from disk or traced to a primary artifact (`internship-landing\NUMBERS.md`, `eras\_metrics.json`), never to a tree summary, and every corpus statistic states its denominator. Nothing drawn from the archive is published until the two GitHub tokens are revoked and the shareable subset is defined in writing.

---

## 7. Risks, ranked, with the trigger for each

**1. The topic change is never approved.** Trigger: leaving the 8/26 meeting without Fang's written agreement and without starting a new one-semester proposal. Consequence: a Project-option degree he must finish by May 2027 has paperwork describing a project he is not doing. His own plan calls this the first action with everything else waiting behind it. The routing is Fang signs the CHAIR line, then forward to Kelly Hasselbring and Dr. Tang for the permit.

**2. The two unrevoked GitHub tokens meet a public artifact.** Trigger: posting a preprint that links the repo, publishing the installable kit, making any archive content public, or the symposium QR code pointing anywhere real. They are in pushed git history, so deletion does not fix them. Still open as of the newest leaf on disk. This is the fastest-moving risk and the cheapest to close.

**3. The December collision eats both the paper and the applications.** Trigger: keeping "preprint by December" as the stated date. Fourteen days in December hold four graded CS 425 events, an exam window, and 8 to 10 applications.

**4. Two candidate papers, one budget, no decision.** Trigger: leaving the meeting without choosing between the GAO EES method preprint (finished data, verified numbers, no new experiments) and the memory-system evaluation (harness from scratch), or attempting both. The most recent record leaves this deliberately in the advisor's hands, softened from intent to offer on 2026-08-17.

**5. Baselines measured on a broken transport.** Trigger: quoting the August 11 to 15 retrieval figures, or any number produced while both MCP servers were crashing on startup from an anyio downgrade. Every fall baseline needs re-measurement with the live process verified, not the data module imported.

**6. Stale or undenominated figures get attacked.** Trigger: quoting `IT494_PLAN.md`'s "~1,000 leaves" and "1,498 assertions," or a 99.6 percent coverage number without noting that 219 Gemini conversations have no parseable id and are excluded. Both are avoidable with a re-count and a sentence.

**7. Unknown calendar holes swallow a milestone.** Trigger: committing to dates before pinning Fall 2026 drill weekends (absent from the archive, cross-checked two ways), IT 483's midterm and final dates (absent from the syllabus, 48 percent of that grade), and the two queued medical items. Compounded by the Google Calendar connector, which was refusing every call on 2026-08-16, so a clean search proves nothing.

**8. Self-direction without an external pusher.** Trigger: the pattern already visible twice, where a Fall 2026 course session starts in the wrong workspace so the course CLAUDE.md and its AI policy do not auto-load, and dissolves without output. This is the first item in three consecutive four-course terms with nobody pushing it; both prior terms carried 4.0 with every course externally deadlined.

**9. A finished evaluation design gets handed to him.** Trigger: the package's design section written as his conclusion rather than as options for Fang to shape. He spent four correction rounds on this exact problem six days ago and saved the rule to auto-memory.

**10. The fall is boring and does not get executed.** Trigger: a semester whose content is entirely labeling gold answers, with nothing intellectually live until spring. Two of his standing rules apply, and he declined a federal job on temperament with "sounds boring AF" and "I'm not the steady and persistent in the face of drudgery type." Pair every measurement block with something he wants to build.

**11. An out-of-band interrupt lands mid-semester.** Trigger: the Illinois National Guard line-of-duty and medical-separation determination arriving. The portal read "findings approved, awaiting final approval" on 2026-05-16, with the leaf's own key point that "approved" is routing language rather than an outcome, and no later leaf updates it. Unpriced, not scheduled.

**12. The VR&E plan of record contradicts the trajectory.** Trigger: employment services (the IEAP phase) getting invoked as training winds down in Spring 2027. The self-authored 2025 career plan and justification letter on file set the goal as a GS-2210 federal cybersecurity role at CISA, DoD or NSA, and the whole funding argument rests on it. Imported to the archive 2026-08-23 but written in 2024 and 2025. Not a tomorrow item; a dated obligation attached to his tuition funding that should be reconciled before spring.