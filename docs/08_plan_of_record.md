# The plan, in phases

Prepared by the assistant. This is the operative sequence for the harness project and supersedes the recommendation section of the project-shapes document where they differ. Scope of record: the prototype is a mock; the build target is a bottom-to-top harness, corpus in, memory tree plus entity knowledge base plus dated facts out, with budgeted injection for RAG, model-agnostic by construction, in Python, at the rigor bar of the EES work. The calendar constraints come from the design brief: two usable work blocks (September 1 to 27 and October 19 to November 15), five dead stretches owned by coursework, applications December 1 to 15, and roughly 70 to 100 project hours in total. Each phase below states its entry condition, its steps in order, its exit deliverable, and its scope valve, the thing that gets cut first if hours run short. Review gates marked QA are the line-by-line walkthroughs; they land in campus gaps and dead stretches by design.

## Phase 0. Decisions and scaffold (now through August 31, about 4 hours)

Entry: the advisor meeting.

1. Resolve the five [CHECK] flags in the proposal and hand the corrected proposal to Dr. Fang.
2. Take three outcomes from the meeting: agreement on the harness scope, a reaction to the December paper target, and a ruling on the GAO EES preprint question (one paper or two this fall).
3. Pick the model tiers for the sensitivity axis: one local 7B via Ollama, one mini-class API model, one frontier model. Install Ollama and confirm the local model runs.
4. Nominate three candidate works for the cold-corpus test. Criteria, revised: long (a serial of several hundred thousand words is fine and better than a doorstopper standalone), fiction with entity structure and reveals, and carrying an ACTIVE COMMUNITY WIKI to score induced structure against. Popularity is acceptable because certification is per-question (bare tiers must fail each kept question closed-book), not per-work. No commitment yet; certification happens in Phase 3.
5. Scaffold the build repo inside the project repo: `harness/` with the two interfaces stubbed (`embed(texts)`, `generate(prompt, schema)`), the run-row schema from the testing outline as a dataclass, and pytest wired. QA gate: the interfaces, about two pages, walked through.

Exit: decisions logged in the repo, empty harness that imports and passes a trivial test.
Valve: none; this phase is small on purpose.

## Phase 1. Read with the build in mind (September 1 to 21, about 18 hours)

Entry: Phase 0 decisions logged.

1. Week one: consolidation and hierarchy (the reading list's sections in that order), read against the question "what does the fold stage need to do." Output: one page of positions, each position a sentence plus the work that grounds it.
2. Week two: knowledge graph representation, temporal and bitemporal modeling, and open information extraction, read against the fact-row schema. Output: the fact-row schema v1 with each field justified by a citation, and the supersession rule stated.
3. Week three: retrieval, injection, and evaluation (RAG best practices, Lost-in-the-Middle-class work, LLM-as-judge validity, narrative QA benchmarks), read against the three injection arms and the scorer. Output: the metric definition sheet v1, the artifact the testing outline says gets agreed with Fang before results exist.
4. Throughout: the gap-list sources on schema-constrained generation and model cascades, read against the contracts design. Output: the summary and extraction contracts v0, with named rejection criteria.

Exit: a synthesis memo (the three outputs above merged, five to eight pages) sent to Fang, and the metric sheet on his desk for agreement. QA gate: the memo is the gate; it is the reading made checkable.
Valve: week three compresses to the judge-validity and narrative-QA reads only; injection-ordering literature can be read during the October dead stretch.

## Phase 1.5. Design and dry scaffold (September 22 to 27, about 8 hours)

1. Write the pipeline design as one document: every stage from the anatomy's 25-row by-hand table mapped to a component, each with its contract, its inputs and outputs, and its executed-by target (deterministic code, or a model call through the interfaces). The anatomy found 26 of the mock's 49 stages already deterministic; those port, they are not redesigned.
1a. Write the segmentation specification as its own artifact. The anatomy's sharpest finding: segmentation has no specification anywhere in the mock, so this is new design work, not porting. The spec defines a testable boundary function with ground-truth metrics (the Pk and WindowDiff framing from the segmentation reading), with TextTiling as the deterministic baseline arm and the dialogue-segmentation work governing the chat case.
2. Implement the corpus adapters dry: transcript-file reader and plain-text book reader emitting a common document stream. No model calls yet.
3. Freeze contracts v1 (segment, summarize, extract-entities, extract-facts) as JSON schemas with validators and rejection logging.
4. QA gate: design document plus adapters plus contracts, one sitting each.

Exit: the design document, adapters passing tests on real files, contracts that validate.
Valve: none; Phase 2 cannot start without this.

## Dead window (September 28 to October 18)

Coursework owns these weeks (Test 1, HW2, the midterm window, MP1). Project work is reading-only: leftover gap-list sources, the paper's related-work section drafted from the digest and narrative, at most two hours a week. Nothing lands unreviewed later because nothing lands.

## Phase 2. Build the pipeline (October 19 to November 15, about 32 hours)

Entry: design document QA'd; contracts frozen; Fang has the metric sheet.

Build order is corpus order, one stage per step, each step ending in a QA gate and a pytest suite. Hour boxes are budgets, not estimates of luck.

1. Segmentation (4h): boundary detection over the document stream, model-called against the segment contract, with the cheap-tier model as default. Test: boundaries on three known transcripts and one book chapter, compared against one alternative segmenter, differences explained in a note.
2. Summarization and filing (5h): segment to leaf against the summary contract; filing into the fixed two-level shape by model call with the routing rule in the prompt; rejection rate logged per model tier.
3. Fold (3h): rollup generation from children only, staleness by content hash ported conceptually from the mock's fold_sig, refold only stale nodes. Test: idempotence, a second run folds nothing.
4. Entities (4h): extraction against the entity contract, alias resolution by explicit map plus model proposal, pages built as indexes with quote validation, the mock's rule kept.
5. Facts (4h): dated assertion rows per the Phase 1 schema, subject-predicate collision detection, later-assertion-wins read rule, rejection rate logged. This is the stage the OpenIE and Eywa-style reading directly governs.
6. Injection arms (5h): the three strategies (top-k chunks as control; tree-routed summaries; tree plus facts hybrid) under one token-budget accountant, ordering per the injection reading, every run emitting the standard run row.
7. Harness and scorer (5h): question runner, LLM-judge scorer with the bias mitigations from the judge reading, calibration against a small hand-labeled set (the agreement reference from the gap list), per-band reporting. One rule the anatomy makes non-negotiable: the judge model is never the writer model. The mock's refold prose and audit scores are self-graded by the model that produced them, which is exactly the unverifiable-self-report failure the harness exists to close; in the harness, every acceptance check (summary faithfulness, fact support, answer scoring) runs on a different model tier than the one that generated the artifact, and the sensitivity table reports judge-model effects alongside writer-model effects.
8. Integration pass (2h): corpus in, answers out, one command.

Exit: the harness runs end to end on a slice of the archive as tenant zero.
Valves, in cut order: the entity layer reduces to extraction-only (no pages) saving ~2h; injection arms drop from three to two (control plus hybrid) saving ~2h; the sensitivity axis defers the frontier tier and reports cheap-versus-mini only.

## Phase 3. Measure and write (November 16 to December 7, about 12 hours, deliberately low-intensity)

Entry: harness end-to-end. This window contains Test 2, Thanksgiving, HW4, and the application deadlines; everything here is runs and prose, no construction.

1. Certify the question set per question: every bare tier runs the candidate set closed-book, and only questions all tiers fail survive; then ingest and run all arms (runs are cheap once built; evenings suffice). Score induced entities and timelines against the community wiki, adjudicating disagreements by the text.
2. Run the archive slice with the corrected-facts band and the miss-rate instrument.
3. Stage-wise sensitivity table: swap tiers per stage on the fixed question set.
4. Write the paper from the design document, the synthesis memo, and the run tables; the related-work section already exists from the dead window. Target: arXiv by December 5, cited in the applications.
5. Brag sheets to the three letter writers when portals open, the paper named.

Exit: preprint posted, applications out.
Valve: if runs expose a broken stage, the paper narrows to the corpus actually working (the novel alone is a complete story) and says so.

## Phase 4. Spring: the distributable harness

Scoped now, planned in January against the spring syllabus: packaging and installation by someone who is not the author; the cold-corpus protocol repeated on a second unknown work; migration of the full two-year raw archive through the harness as tenant-zero proof, with any answer the mock could give and the harness cannot logged as a named regression; multi-tenant separation; and the second paper if fall's ruling was two. The fall harness rides along as the regression suite. Entry condition: the fall paper exists; this phase never starts early at the cost of Phase 3.

## Standing across all phases

Weekly rhythm: build lands Tuesday through Friday; review happens in the Monday and Wednesday campus gaps; dead stretches are review-and-writing only. Writer and judge are separate models everywhere, per the anatomy's finding that the mock self-grades. The build backlog of record is the anatomy's by-hand inventory; a stage not in that table and not in this plan does not get built without being added here first, in writing. Every model call goes through the two interfaces and lands in a run row with its model id. Every stage has a contract, a rejection count, and a test. Anything cut by a valve is cut in writing, in the log, the day it is cut.
