# The plan, in phases

The prototype is a mock. The build target is a bottom-to-top harness: corpus in, memory tree plus entity knowledge base plus dated facts out, with budgeted injection for RAG, model-agnostic by construction, in Python. Calendar constraints: two usable work blocks (September 1 to 27 and October 19 to November 15), five dead stretches owned by coursework, applications December 1 to 15, and roughly 70 to 100 project hours in total. Each phase states an entry condition, ordered steps, an exit deliverable, and a scope valve (the first cut if hours run short), and closes with an authorship gate: implementation by hand, AI assisting in drafting and discussion but never as unexamined author, completion logged.

## Phase 0. Decisions and scaffold (now through August 31, about 4 hours)

Entry: the advisor meeting.

1. Deliver the corrected proposal to Dr. Fang.
2. Take three outcomes from the meeting: agreement on the harness scope, a reaction to the December paper target, and a decision on the GAO EES preprint (one paper or two this fall).
3. Pick the model tiers for the sensitivity axis: one local 7B via Ollama, one mini-class API model, one frontier model. Install Ollama and confirm the local model runs.
4. Nominate three candidate works for the cold-corpus test. Criteria: long (a serial of several hundred thousand words beats a doorstopper standalone), fiction with entity structure and reveals, and an active community wiki to score induced structure against. Certification is per-question (bare tiers must fail each kept question closed-book), not per-work, so popular works qualify; certification happens in Phase 3.
5. Scaffold the build repo inside the project repo: `harness/` with the two interfaces stubbed (`embed(texts)`, `generate(prompt, schema, tier)`), the run-row schema from the testing outline as a dataclass, and pytest wired. Gate: the interfaces, about two pages, walked through.
6. Turn on consult-logging in the mock immediately: each session records what memory was cued, what was read, and what the answer used, so the miss-rate clock starts accruing from September. This is mock-side instrumentation, exempt from the authorship rule; no later phase builds it otherwise.

Exit: decisions logged in the repo; an empty harness that imports and passes a trivial test.
Valve: none; this phase is small on purpose.

## Phase 1. Read with the build in mind (September 1 to 21, about 18 hours)

Entry: Phase 0 decisions logged.

1. Week one: consolidation and hierarchy, read against the question "what does the fold stage need to do." Output: one page of positions, each a sentence plus the work that grounds it.
2. Week two: knowledge graph representation, temporal and bitemporal modeling, and open information extraction, read against the fact-row schema. Output: fact-row schema v1 with each field justified by a citation, and the supersession rule stated.
3. Week three: retrieval, injection, and evaluation (RAG best practices, Lost-in-the-Middle-class work, LLM-as-judge validity, narrative QA benchmarks), read against the three injection arms and the scorer. Output: metric definition sheet v1, to be agreed with Dr. Fang before any results exist.
4. Throughout: the gap-list sources on schema-constrained generation and model cascades, read against the contracts design. Output: summary and extraction contracts v0, with named rejection criteria.

Exit: a synthesis memo (the three outputs merged, five to eight pages) and the metric sheet sent to Dr. Fang for agreement. Gate: the memo; it is the reading made checkable.
Valve: week three compresses to the judge-validity and narrative-QA reads; injection-ordering literature moves to the October dead stretch.

## Phase 1.5. Design and dry scaffold (September 22 to 27, about 8 hours)

1. Write the pipeline design as one document: every stage from the anatomy's 25-row by-hand table mapped to a component, each with contract, inputs and outputs, and executed-by target (deterministic code, or a model call through the interfaces). The 26 of the mock's 49 stages that are already deterministic port unchanged.
1a. Write the segmentation specification as its own artifact. Segmentation has no specification anywhere in the mock, so this is new design work, not porting. The spec defines a testable boundary function with ground-truth metrics (the Pk and WindowDiff framing from the segmentation reading), TextTiling as the deterministic baseline arm, and the dialogue-segmentation work governing the chat case.
2. Implement the corpus adapters dry: transcript-file reader and plain-text book reader emitting a common document stream. No model calls yet.
3. Freeze contracts v1 (segment, summarize, extract-entities, extract-facts) as JSON schemas with validators and rejection logging.
4. Gate: design document, adapters, and contracts, one sitting each.

Exit: the design document, adapters passing tests on real files, contracts that validate.
Valve: none; Phase 2 cannot start without this.

## Dead window (September 28 to October 18)

Coursework owns these weeks (Test 1, HW2, the midterm window, MP1). Project work is reading-only: leftover gap-list sources and the paper's related-work section, at most two hours a week.

## Phase 2. Build the pipeline (October 19 to November 15, about 35 hours)

Entry: design document gated; contracts frozen; metric sheet with Dr. Fang.

Build order follows the five steps of the framework: ingest, organize, retrieve, inject, maintain, with the evaluation spine built alongside. One step per block, each ending in an authorship gate and a pytest suite. The hour boxes below record sequence and build order, not schedule: they are task-decomposition floors, the full build by one person learning each stage runs to hundreds of hours, and against a realistic 24 to 32 hour block they price at two to three times what fits. The five-step build is therefore a full-year deliverable. Fall's realistic reach is ingest and organize for one corpus plus the control-versus-one-arm comparison; the build proceeds in order as far as the block allows, and everything past the committed core is stretch. That core: the instruments running on the mock, one two-arm comparison on the archive's corrected-facts band, the synthesis memo, the design document with the segmentation spec, and the paper frozen by November 15. The December paper does not depend on the build: its anchor instrument, the counterfactual miss rate, runs on the live mock with consult-logging and needs no harness, so the paper reports the instruments plus whatever pipeline slice exists by November 15.

1. INGEST (5h): the corpus adapters (chat transcripts, plain-text documents) feeding one document stream, then segmentation as a model call against the segment contract, with TextTiling as the deterministic comparison arm. Test: boundaries on three known transcripts and one book chapter, disagreements with the baseline explained in a note.
2. ORGANIZE (13h), three sub-blocks: summaries (4h), segment to leaf against the summary contract, filed into the fixed two-level tree, rejection rate logged per model tier; entities (4h), extraction against the entity contract with the alias ledger, pronoun resolution as a bought model call, pages as quote-validated indexes; facts (5h), dated assertion rows per the Phase 1 schema with source pointers, the token-to-attribute merge recorded in a ledger rather than silent, rejection rate logged. This is the stage the OpenIE, canonicalization, and coreference reading governs.
3. RETRIEVE (2h): tree routing (index, rollup, descend), entity and fact lookup, lexical fallback. Deliberately thin; retrieval is not the hard part.
4. INJECT (5h): the token-budget accountant composing context three ways (top-k chunks as control; tree-routed summaries; tree plus facts hybrid), ordering per the injection reading, every run emitting the standard run row.
5. MAINTAIN (3h): content-hash staleness with refold of stale nodes only (test: idempotence, a second run folds nothing), and supersession by subject-predicate collision with later-assertion-wins reads.
6. The evaluation spine (5h), built alongside rather than after: question runner, LLM-judge scorer with the bias mitigations from the judge reading, calibrated against a small hand-labeled set (the agreement reference). The judge model is never the writer model (the mock's self-grading is the unverifiable-self-report failure this project exists to close): every acceptance check runs on a different tier than the artifact's writer, and the sensitivity table reports judge effects alongside writer effects.
7. Integration (2h): corpus in, answers out, one command.

Exit: the harness runs end to end on a slice of the archive as tenant zero.
Valves, in cut order: the entity layer reduces to extraction-only (no pages), saving about 2h; injection arms drop from three to two (control plus hybrid), saving about 2h; the sensitivity axis defers the frontier tier and reports cheap-versus-mini only.

## Phase 3. Measure and write (November 16 to December 7, about 12 hours, deliberately low-intensity)

Entry: harness end-to-end. All fall measurement runs inside November 1 to 15 and the paper posts by November 15; this window, which contains Test 2, Thanksgiving, HW4, and the application deadlines, carries only runs, prose, submission logistics, brag sheets, and the applications themselves.

1. Certify the question set per question: every bare tier runs the candidate set closed-book, and only questions all tiers fail survive; then ingest and run all arms (runs are cheap once built; evenings suffice). Score induced entities and timelines against the community wiki, adjudicating disagreements by the text.
2. Run the archive slice with the corrected-facts band and the miss-rate instrument.
3. Stage-wise sensitivity table: swap tiers per stage on the fixed question set.
4. Write the paper from the design document, the synthesis memo, and the run tables; the related-work section already exists from the dead window. Target: arXiv by December 5, cited in the applications.
5. Brag sheets to the three letter writers when portals open, the paper named.

Exit: preprint posted, applications out.
Valve: if runs expose a broken stage, the paper narrows to the corpus actually working (the novel alone is a complete story) and says so.

## Phase 4. Spring: the distributable harness

Scoped now, planned in January against the spring syllabus: packaging and installation by someone who is not the author; the cold-corpus protocol run in full on the primary work and as a lighter replication on at least one more (smaller certified set, entity-coverage scoring), so portability is shown across works; migration of the full two-year raw archive through the harness as tenant-zero proof, with any answer the mock could give and the harness cannot logged as a named regression; multi-tenant separation; and the second paper if the fall decision was two. The fall harness rides along as the regression suite. Entry condition: the fall paper exists; this phase never starts at the cost of Phase 3.

## Standing across all phases

Weekly rhythm: build lands Tuesday through Friday; review happens in the Monday and Wednesday campus gaps; dead stretches are review-and-writing only. Writer and judge are separate models everywhere. The build backlog of record is the anatomy's by-hand inventory; a stage in neither that table nor this plan is not built until added here in writing. Every model call goes through the two interfaces and lands in a run row with its model id. Every stage has a contract, a rejection count, and a test. Anything cut by a valve is cut in writing, in the log, the day it is cut.
