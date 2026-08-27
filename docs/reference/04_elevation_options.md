> **REFERENCE, not superseded.** This is the menu of candidate mechanisms, each traced to a source. Roughly seven of its citations appear nowhere else in the repo.
> It is background rather than part of the working set. Index: `docs/README.md`.

# Ways the research could elevate the project

Each item is a candidate mechanism for the general design, scoped to its delta beyond the prototype (the evidence base and first tenant), usually the automated, measured, or scaled version of a manual practice. Citations outside the packaged reading list carry arXiv identifiers inline. Effort figures are orders of magnitude; items exceeding the fall budget of 70 to 100 hours are marked spring-scale. Nothing is ranked.

### Capture

**A revived runtime citation log**

A PostToolUse hook appends every tree read to a session log, making a leaf's citations transcription rather than recollection. The prototype built this (`cite_log.py`) but shelved it unrun; OPERATIONS.md argues the case in prose. CoALA (Sumers et al. 2024) treats memory writes as deliberate internal actions; Noy et al. 2019 report provenance-first assertion as the pattern all five industrial graphs converged on. The rebuild feeds the cued-versus-read-versus-load-bearing distinction OPERATIONS names but never mechanized; the counterfactual miss instrument below consumes its output. Effort: days, from git history.

**Outcome-signal mining from correction turns**

A pass that scans transcripts for implicit negative feedback, the rephrasings and "no, I meant" turns, and converts recurring ones into failure-log candidates. Liu, Zhang and Choi 2025 show later user turns are dense with correction signal; ReasoningBank (Ouyang et al. 2026) shows failure records carry value when the schema stores lessons rather than replays. `_failure_log.jsonl` records only misroutes somebody noticed, not wrong answers; nothing mines the archive for unlogged misses. Effort: a week, including a hand-checked precision sample.

**A segmentation quality lane in the stale-leaf slice**

An audit of whether multi-topic sessions were cut into leaves at the right boundaries, with permission to re-cut. Event segmentation theory (Zacks et al. 2007) treats the cut as an encoding decision; Reflective Memory Management (2503.08026, ACL 2025) shows rigid granularity fragments conversational structure. The stale-leaf slice re-summarizes in place but never re-segments. The delta is a sampled bad-cut rate plus a re-segmentation lane in the existing burn-down. Effort: days for the sample, a week for the lane.

### Structure and representation

**A one-era property-graph trial**

A representation experiment; knowledge graphs are one candidate, not the destination. Render one era's ledger rows as a typed property graph under the Angles 2018 formalization, whose delta function (an edge-type whitelist per node-type pair) doubles as a vocabulary contract for an extraction pipeline; answer the same golden questions by graph walk versus sheet read, scoring accuracy and hop count. The ledger is already subject-predicate-object rows with qualifiers, so most of a graph exists; the delta is typed edges and multi-hop query. Rossi et al. 2021 show sparse personal graphs are the worst regime for embedding methods, so the trial stays symbolic with lightweight schema (Hogan et al. 2021). Effort: days.

**Recorded currency judgments as dated rank rows**

When a read-time judgment decides which of two conflicting rows is current, record that judgment as its own dated, sourced row, following Wikidata's preferred and deprecated marks (Vrandecic and Krotzsch 2014) and Fowler's 2021 observation that record history stays append-only even under correction. Nothing is overwritten, so the facts-cannot-be-wrong rule holds; an expensive judgment is made once and cached as data rather than remade at every read. The ledger already stores corrections as new rows and imprecision as date_precision qualifiers; the currency call lives only in the reading agent's head. Effort: days; the stale-serve measurement below can consume these rows.

**Entity resolution measured on the existing registry**

A labeled set of alias pairs drawn from the corpus (Defy Medical, Defy, the clinic; GAO across four eras) and a measured resolution accuracy over it. Balog and Kenter 2019 call long-tail personal entity linking the defining open problem of personal knowledge graphs; Noy et al. 2019 call disambiguation the top challenge across all five industrial graphs; Zhong et al. 2024 supply the task decomposition. The two entity systems (`registry_entities.txt` and the ledger's) produced 70 versus 388 entities with only 17 names in common; the corpus demonstrates the problem, nothing measures it. Effort: days to a week.

### Currency

**A stale-serve rate**

How often a recall surface serves a superseded fact. MemStrata (2606.26511) supplies the metric shape and reports plain RAG serving outdated facts 15 to 40 percent of the time; MemoryAgentBench (Hu, Wang and McAuley 2025) finds no tested system above 28 percent on multi-hop fact updates. Drift-debt measures whether a leaf is current against its source; nothing measures whether answers reaching a session were stale. Method: a probe set built from documented supersessions in the corpus (an internship ending, a session renumbering, a topic pivot) run against tree and ledger reads. Effort: days once the probe set exists; the typed gold set item can supply it.

**An implicit-conflict probe**

Whether the system detects conflicts carrying no explicit negation, where a later observation quietly falsifies an earlier row. STALE (2605.06527) defines the task and reports a best-model score of 55.2 percent; Pollertlam and Kornsuwannawit 2026 name update non-propagation, a "twice a week" fact surviving its revision to three, as a leading failure of flat fact extraction. The tail-scan rule catches corrections inside one conversation, but the validator re-checks only that quotes still appear, never that a claim went false; cross-conversation supersession has no detector. This prices the design choice against Zep-style invalidation-on-write without reversing it. Effort: a week; measurement only, no write-path change.

### Retrieval and delivery

**A counterfactual miss instrument**

How often the store held the answer and the session never consulted it. The project's strongest publishable claim, so far only a limitation note (access is not recall): every published benchmark poses the query, so this failure cannot occur in their setups, and Remember When It Matters (2607.08716) covers only the intra-task horizon. The failure loop logs misses somebody noticed; missing is the denominator, the misses nobody noticed. Method: seed sessions with tasks whose answers provably sit in the tree, instrument reads through the citation log, count non-consultations. Effort: a week to build, data accruing on normal use; depends on the citation log item.

**A retrieval-depth router**

A cheap per-query decision among no lookup, one-hop rollup read, and multi-hop descent. Adaptive-RAG (Jeong et al. 2024) matches its always-iterate baseline at a third of the steps and shows usage logs can self-label the router by recording which depth sufficed; Wang et al. 2024 find the decide-whether-to-retrieve gate the single cheapest accuracy and latency win in their module search. Current policy is static: the primer's standing instruction plus the cue hook's boundary triggers. The delta buys cheaper recall plus a free labeled dataset of query difficulty over the corpus. Effort: a week.

**The endorsed escape-hatch index, built and measured**

A brute-force exact-cosine embedding index over leaf text, no vector database, consulted only when tree descent lands on the wrong branch. The design already endorses this role, with the flattened-CBC example as the worked case: at roughly 1,200 files exact search is correct and index machinery is overhead, consistent with Faiss sizing guidance (Douze et al. 2024) placing the brute-force crossover far above this scale. NoLiMa (2025) supplies the motivation: lexical mismatch is the normal case, so retrieval must bridge vocabulary before the model sees anything. The delta is an afternoon of code plus a probe set of vocabulary-mismatch questions measuring wrong-branch recovery. Effort: days.

**Self-selection routing across eras (spring-scale)**

The blackboard pattern applied to the tree: partition agents that have each pre-digested one era volunteer answers when a query touches their subtree. Salemi et al. 2026 report 13 to 57 percent end-to-end gains over master-slave routing, growing with corpus size. `directory.md` plus the curated boundary lines is exactly the central index whose staleness the blackboard result targets, and the era summaries are already the pre-digestion. It buys an architecture argument for organizational scale-out. Effort: weeks, with payoff scaling on corpus size the project does not yet have; spring-scale on both counts.

### Evaluation and measurement

**E2, a typed gold set built on published task definitions**

An extension of EXPERIMENTS.md: 100 to 150 gold questions typed by the published categories (single-hop, multi-hop, temporal, knowledge-update, abstention) from LoCoMo (Maharana et al. 2024) and LongMemEval; benchmarks supply task definitions and comparability, never a contest to win. `_golden.jsonl` exists as a frozen deterministic set, the adversarial-sampling rule is written, and E1 established the file format; the delta is size, typed coverage, and category-level reporting. Agent fleets make the labeling tractable inside the budget; completion accounting is mandatory, since five of twelve automated audit checks have previously stopped running without raising an error. Effort: a week of fleet runs plus review.

**A calibration set for the faithfulness gate**

A measurement of the gate itself. FABLES (Kim et al. 2024) shows automatic faithfulness checking reaches 58.2 F1 at best on the indirect multi-hop claims rollups are made of; the cold audit agrees locally: eight defects, all in the rollup layer, all invisible to entailment checking because a hardened sentence is still entailed by its hedged source. The faithfulness metric already runs every pass, and the 39 hand-verified claims from the cold audit are a free labeled seed. The delta scores the gate against those labels, reports precision and recall, and extends the taxonomy to the omission and salience errors BooookScore (Chang et al. 2024) shows dominate hierarchical summarization. Effort: days.

**A layer-localized error study of the write path**

The 39-claim audit scaled with agent fleets and reported by layer: transcript to leaf, leaf to node, node to era. BooookScore scores only final summaries and cannot localize which level introduced an error; Wu et al. 2021 documented compounding errors at composition points; Talebirad et al. 2026 prove the atom layer sets the information ceiling, making the fold step the place losses concentrate. The rotating source audit is the standing mechanism, and the cold audit ran this design once by hand: 31 confirmed, 4 wrong, 4 unsupported, every defect in the synthesized layer; coverage sits at 2.3 percent. The delta is coverage, statistics, and the by-layer cut: the paper's motivating study on existing machinery. Effort: a week of fleet time.

**The hash-versus-dirty-flag demonstration**

The controlled experiment behind the project's strongest surviving mechanism claim. Hand-edit N leaves out of band, then show that a write-time dirty flag, the scheme MemForest (2605.23986) and every build system use, misses all N while content-hash recomputation catches all N: a flag is only correct if every writer remembers to set it, and a recomputed hash is self-checking. `fold_sig` is implemented, tested, and running; only the comparison arm and write-up are new. Effort: days. It pairs with the layer study as a short paper's experimental section.

### Scale-out

**A permission-graph formalization of the existing boundaries (spring-scale)**

A recasting of the guard patterns, the holds ledger, and the gitignored eras as the provenance-stamped fragments and retrospective permission checks of Collaborative Memory (Rezazadeh et al. 2025), where revoking an edge in the access graph retroactively hides every fragment derived through it. The single-user version already runs: CUI boundaries, held-local UUIDs, and the guard-your-own-writing rule are hand-enforced policy over the primitives that paper formalizes. Multi-tenant access is the one thing the current design cannot claim. Effort: weeks, spring-scale, though a two-page note mapping current mechanisms onto the formalism would fit a fall afternoon.

**A measured cache-tier policy for the primer**

Treat the SessionStart primer as the preloaded tier of a two-tier design and set its boundary from data. CAG (Chan et al. 2025) shows that below some corpus size precomputed context beats retrieval outright, and its own large-corpus result shows where that stops; Pollertlam and Kornsuwannawit 2026 supply break-even arithmetic between resending history and extract-then-retrieve, with memory winning after roughly ten turns at 100K tokens. The tiering already exists: the primer preloads the era map, the dossiers load on demand, everything else sits behind search, with no measurement saying what belongs where. The delta varies primer contents and measures recall against token cost per session. Effort: days.
