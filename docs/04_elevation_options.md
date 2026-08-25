# Ways the research could elevate the project

Prepared by the assistant. An itemized list of options, not recommendations. The project's goal is a rigorous general system, with the existing prototype serving as evidence and first tenant; read each item accordingly, as a candidate mechanism for the general design, stated here against the prototype because the prototype is where the evidence and the baseline live. Each item traces to the work that suggested it, and each states what the prototype already does, since no item may propose what already exists. Where overlap exists, the item is scoped to the delta, usually the automated, measured, or scaled version of a manual practice. Citations outside the packaged reading list, from the adversarial literature pass, carry arXiv identifiers inline. Effort figures are orders of magnitude (days, a week, weeks), not commitments. Items plainly exceeding the fall budget of 70 to 100 hours are marked spring-scale. Nothing here is ranked or sequenced; selection and ordering belong to another document and the advisor conversation.

### Capture

**A revived runtime citation log**

A PostToolUse hook that appends every tree read to a session log, so a leaf's citations become transcription rather than recollection. The system built exactly this (`cite_log.py`), shelved it on 2026-07-31, and deleted it on 2026-08-21 without it ever running; OPERATIONS.md keeps the argument alive in prose ("reconstructing at session close is a recollection"). CoALA (Sumers et al. 2024) names memory writes as deliberate internal actions worth first-class treatment, and Noy et al. 2019 report provenance-first assertion as the pattern all five industrial graphs converged on. The delta is a rebuild, wired and verified, feeding the cued-versus-read-versus-load-bearing distinction OPERATIONS names but never mechanized. Effort is days, rebuilding from git history. The counterfactual miss instrument below consumes its output.

**Outcome-signal mining from correction turns**

A pass that scans transcripts for implicit negative feedback, the rephrasings and "no, I meant" turns, and converts recurring ones into failure-log candidates. Liu, Zhang and Choi 2025 show later user turns are dense with correction signal, reliable as a lens on unmet intent even though noisy as training data; ReasoningBank (Ouyang et al. 2026) shows failure records carry real value when the schema stores lessons rather than replays. The overlap is the failure loop: `fail` exists but fires only when someone notices a miss, and nothing mines the archive for the ones nobody logged. This is the wrongness signal his own dossier lists as open space, since `_failure_log.jsonl` records misroutes, not wrong answers. Effort is a week, including a hand-checked precision sample.

**A segmentation quality lane in the stale-leaf slice**

An audit of whether multi-topic sessions were cut into leaves at the right boundaries, with permission to re-cut. Event segmentation theory (Zacks et al. 2007) treats the cut as an encoding decision, and Reflective Memory Management (2503.08026, ACL 2025) shows rigid granularity fragments conversational structure. The overlap is real but partial: the one-chat-many-leaves rule governs capture, and the stale-leaf slice re-summarizes in place every pass, yet nothing ever re-segments; a badly cut leaf stays badly cut forever, a gap his own literature dossier already names. The delta is a sampled bad-cut rate plus a re-segmentation lane in the existing burn-down, converting a permanent defect class into a measured, shrinking one. Effort is days for the audit sample, a week for the lane.

### Structure and representation

**A one-era property-graph trial**

A small representation experiment, honoring the standing position that knowledge graphs are one candidate representation, not the destination. Render one era's ledger rows as a typed property graph using the Angles 2018 formalization, whose delta function (an edge-type whitelist per node-type pair) is a vocabulary contract for an extraction pipeline, then answer the same golden questions by graph walk versus sheet read, scoring accuracy and hop count. The overlap is that the ledger is already subject-predicate-object rows with qualifiers, so most of a graph exists; the delta is typed edges and multi-hop query. Rossi et al. 2021 show sparse personal graphs are the worst regime for embedding methods, so the trial stays symbolic, per Hogan et al. 2021 on lightweight schema. Effort is days, and it produces evidence for or against the professor's graph steer, drawn from the student's own corpus.

**Recorded currency judgments as dated rank rows**

When a read-time judgment decides which of two conflicting rows is current, record that judgment as its own dated, sourced row, in the spirit of Wikidata's preferred and deprecated marks (Vrandecic and Krotzsch 2014) and Fowler's 2021 point that record history stays append-only even under correction. Nothing is overwritten or invalidated at write time, so the founding facts-cannot-be-wrong rule holds; what changes is that an expensive judgment is made once and cached as data instead of remade at every read. The overlap is that the ledger already stores corrections as new rows and imprecision as date_precision qualifiers; the currency call currently lives only in the reading agent's head. Effort is days. The stale-serve measurement below can consume these rows.

**Entity resolution measured on his own registry**

A labeled set of alias pairs drawn from the corpus (Defy Medical, Defy, the clinic; GAO across four eras) and a measured resolution accuracy over it. Balog and Kenter 2019 frame long-tail personal entity linking as the defining open problem of personal knowledge graphs; Noy et al. 2019 call disambiguation the top challenge across all five industrial graphs; Zhong et al. 2024 supply the task decomposition. The overlap is that the ledger resolves identity through `registry_entities.txt`, and OPERATIONS.md itself flags that the two entity systems produced 70 versus 388 entities with only 17 names in common, so the corpus already demonstrates the problem. Nothing measures it. The delta is a number for a known weakness and a defensible answer when a reviewer asks how identity is managed. Effort is days to a week.

### Currency

**A stale-serve rate**

A measurement of how often a recall surface serves a superseded fact. MemStrata (2606.26511) supplies the metric shape and reports plain RAG serving outdated facts 15 to 40 percent of the time; MemoryAgentBench (Hu, Wang and McAuley 2025) finds no tested system above 28 percent on multi-hop fact updates, so the number is expected to be nonzero. The overlap is drift-debt, which measures whether a leaf is current against its source, a storage property; nothing measures the delivery property, whether answers actually reaching a session were stale. The method: a probe set built from his own documented supersessions (the internship ending, the session renumbering, the topic pivot) run against tree and ledger reads. Effort is days once the probe set exists; the typed gold set item can supply it.

**An implicit-conflict probe**

A test of whether the system detects conflicts carrying no explicit negation, where a later observation quietly falsifies an earlier row. STALE (2605.06527) defines the task and reports a best-model score of 55.2 percent; Pollertlam and Kornsuwannawit 2026 name update non-propagation, a "twice a week" fact surviving its revision to three, as a leading failure of flat fact extraction. The overlap: the tail-scan rule already catches corrections inside one conversation at capture time, but the validator only re-checks that quotes still appear, never that a claim went false; cross-conversation supersession has no detector at all. This measures the cost of the deliberate design choice against Zep-style invalidation-on-write without proposing to reverse it. Effort is a week; measurement only, no write-path change.

### Retrieval and delivery

**A counterfactual miss instrument**

A measurement of how often the store held the answer and the session never consulted it. The adversarial literature pass rated this the project's strongest publishable claim; today it is only a limitation note (access is not recall): every published benchmark poses the query, so this failure cannot occur in their setups, and Remember When It Matters (2607.08716) covers only the intra-task horizon. The overlap is substantial and the item scopes around it: the failure mode is named, `recall_cue.py` is the intended fix, and the failure loop logs misses somebody noticed. What is missing is the denominator, the misses nobody noticed. The method seeds sessions with tasks whose answers provably sit in the tree, instruments reads through the citation log, and counts non-consultations. Effort is a week to build, with data accruing on normal use afterward. Depends on the runtime citation log item.

**A retrieval-depth router**

A cheap per-query decision among no lookup, a one-hop rollup read, and multi-hop descent, made before retrieval starts. Adaptive-RAG (Jeong et al. 2024) matches its always-iterate baseline at a third of the steps and shows usage logs can self-label the router by recording which depth sufficed; Wang et al. 2024 find the decide-whether-to-retrieve gate the single cheapest accuracy and latency win in their module search. The overlap is that current policy is static: the primer's standing instruction plus the cue hook's boundary triggers, no per-query decision anywhere. The delta buys cheaper recall and, as a side effect, a free labeled dataset of query difficulty over his own corpus, which feeds the evaluation work. Effort is a week.

**The endorsed escape-hatch index, built and measured**

A brute-force exact-cosine embedding index over leaf text, no vector database, consulted only when tree descent lands on the wrong branch. His own records already endorse this role, with the flattened-CBC example as the worked case, and fix the design point: at roughly 1,200 files exact search is correct and index machinery is overhead, consistent with the Faiss sizing guidance (Douze et al. 2024) placing the brute-force crossover far above this scale. NoLiMa (2025) supplies the motivation, showing retrieval must bridge vocabulary before the model sees anything because lexical mismatch is the normal case. The overlap is a decision and a cost model with nothing built. The delta is an afternoon of code plus a probe set of vocabulary-mismatch questions measuring wrong-branch recovery. Effort is days.

**Self-selection routing across eras (spring-scale)**

The blackboard pattern applied to the tree: partition agents that have each pre-digested one era volunteer answers when a query touches their subtree, instead of a central index deciding who knows what. Salemi et al. 2026 report 13 to 57 percent end-to-end gains over master-slave routing, with the advantage growing as the corpus grows. The overlap is direct: `directory.md` plus the curated boundary lines is exactly the central index whose staleness the blackboard result targets, and the era summaries are already the pre-digestion. It buys an architecture argument for the organizational scale-out his newest statement of intent names. Effort is weeks, and the payoff scales with corpus size he does not yet have: spring-scale on both counts.

### Evaluation and measurement

**E2, a typed gold set built on published task definitions**

An extension of EXPERIMENTS.md: 100 to 150 gold questions typed by the published categories (single-hop, multi-hop, temporal, knowledge-update, abstention) from LoCoMo (Maharana et al. 2024) and LongMemEval, per the standing rule that benchmarks supply task definitions and comparability, never a contest to win. The overlap: `_golden.jsonl` exists as a frozen deterministic set, the adversarial-sampling rule is written, and E1 established the file format, so the delta is size, typed coverage, and category-level reporting a reviewer can read. Agent fleets make the labeling tractable inside the budget; completion accounting is mandatory: five of twelve automated audit checks have previously stopped running without raising an error. Effort is a week of fleet runs plus review. Presented as an option for the advisor to shape, not a finished design.

**A calibration set for the faithfulness gate**

A measurement of the gate itself. FABLES (Kim et al. 2024) shows automatic faithfulness checking reaches 58.2 F1 at best on the indirect multi-hop claims that rollups are made of, and the cold audit proved the point locally: eight defects, all in the rollup layer, all invisible to entailment checking because a hardened sentence is still entailed by its hedged source. The overlap is that the faithfulness metric already runs every pass, and the 39 hand-verified claims from 2026-08-21 are a free labeled seed. The delta scores the gate against those labels, reports its precision and recall, and extends the target taxonomy to the omission and salience errors BooookScore (Chang et al. 2024) shows dominate hierarchical summarization. Effort is days; it converts a known blind spot into a calibrated one.

**A layer-localized error study of the write path**

The 39-claim audit scaled with agent fleets and reported by layer: transcript to leaf, leaf to node, node to era. BooookScore scores only final summaries and cannot localize which level introduced an error; Wu et al. 2021 documented compounding errors at composition points; Talebirad et al. 2026 prove the atom layer sets the information ceiling, which makes the fold step the place losses concentrate. The overlap is that the rotating source audit is the standing mechanism and the cold audit ran this design once by hand, finding 31 confirmed, 4 wrong, 4 unsupported, with every defect in the synthesized layer; audit coverage sits at 2.3 percent. The delta is coverage, statistics, and the by-layer cut. This is the paper's motivating study run on machinery that already exists. Effort is a week of fleet time.

**The hash-versus-dirty-flag demonstration**

The controlled experiment behind the one mechanism claim that survived his adversarial novelty review. Hand-edit N leaves out of band, then show that a write-time dirty flag, the scheme MemForest (2605.23986) and every build system use, misses all N while content-hash recomputation catches all N, because a flag is only correct if every writer remembers to set it and a recomputed hash is self-checking. The overlap is nearly total and that is the point: `fold_sig` is implemented, tested, and running, so nothing new gets built except the comparison arm and the write-up. It buys the strongest defensible contribution named in his own literature review for the cost of a fixture script. Effort is days. It pairs naturally with the layer study as a short paper's experimental section.

### Scale-out

**A permission-graph formalization of the existing boundaries (spring-scale)**

A recasting of the guard patterns, the holds ledger, and the gitignored eras as the provenance-stamped fragments and retrospective permission checks of Collaborative Memory (Rezazadeh et al. 2025), where revoking an edge in the access graph retroactively hides every fragment derived through it. The overlap is that the single-user version already runs: CUI boundaries, held-local UUIDs, and the guard-your-own-writing rule are hand-enforced policy over the primitives that paper formalizes. It buys the concrete bridge from a personal backend to the organization-scale framing in his newest statement of intent, since multi-tenant access is the one thing the current design cannot claim. Effort is weeks and spring-scale, though a two-page design note mapping current mechanisms onto the formalism would fit a fall afternoon.

**A measured cache-tier policy for the primer**

Treat the SessionStart primer as the preloaded tier of a two-tier design and set its boundary from data. CAG (Chan et al. 2025) shows that below some corpus size, precomputed context beats retrieval outright, and its own large-corpus result shows where that stops; Pollertlam and Kornsuwannawit 2026 supply break-even arithmetic between resending history and extract-then-retrieve, with memory winning after roughly ten turns at 100K tokens. The overlap is that the tiering already exists by instinct: the primer preloads the era map, the dossiers load on demand, and everything else sits behind search, with no measurement saying what belongs where. The delta varies primer contents and measures recall against token cost per session. Effort is days; the numbers strengthen the cost section of any write-up.
