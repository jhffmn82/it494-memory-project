> **SUPERSEDED 2026-08-27** by docs/22 and docs/23.
> Kept for the record; do not build from it. Index: `docs/README_SESSION_2026-08-27.md`.

# Build plan: execution, tools, validation

This document is sequence and method, not schedule: the build runs to hundreds of hours across the year and is paced by that total, so per-stage hour figures are omitted. Every stage follows the same discipline: implemented by hand, the contract frozen before the code, tests written with the code, and no stage grading its own output.

## Standing toolchain

Python 3.12, stdlib first. Chosen once, used everywhere: `dataclasses` for objects; `jsonschema` for contract validation (pydantic deferred: one validation library with no model magic keeps every line explainable, and pydantic can be adopted later without redesign); `pytest` for every stage's suite; `numpy` for vectors; `sentence-transformers` for local embeddings; plain `requests` against Ollama's HTTP API and the hosted APIs (LangChain and LiteLLM rejected: a framework puts someone else's pipeline decisions in the critical path, and the two interfaces are under a page each). Storage is files, per the data model. Every build session ends in a commit.

## Stage by stage

**Interfaces first.** `embed(texts) -> ndarray` and `generate(prompt, schema, tier) -> validated dict | Rejection`. Three tier configs: local (Ollama, a 7B instruct model), mini (a small hosted model), frontier. `generate` validates output against the given JSON schema, retries once with the validation error appended, then records a Rejection. Validation: unit tests with a canned fake tier, then a live smoke test per tier, ten calls each, rejection rates logged. This stage comes first because everything else routes through it.

**Ingest: adapters.** One reader per corpus kind emitting the Document stream: chat transcripts (markdown conversations) and plain text (a novel split by chapters). Tools: stdlib only; `regex` for turn boundaries. Validation: round-trip property tests (every emitted span maps back to identical source text), plus counts against known files.

**Ingest: segmenter.** Two arms from day one. The deterministic arm imports TextTiling rather than hand-implementing it: the authorship rule protects the load-bearing core, not plumbing, and a hundred lines of 1997 lexical cohesion is plumbing. The model arm calls `generate` against the segment contract, returning boundary positions with one-line topic labels. Validation: Pk and WindowDiff against a hand-labeled boundary set (twenty documents, labeled per the agreement reference); disagreements between arms sampled and read, per the EES rule that every methodological choice is tested against an alternative with a named failure mode.

**Organize: distiller and filing.** Three schema-validated calls per segment (summary, mentions, facts), three small modules sharing one driver. Coreference and alias resolution ride the mentions call: the prompt carries the current alias ledger for candidate entities, and the model returns mention-to-entity bindings with quotes. Filing is a further model call choosing a topic path from the existing tree plus a new-topic escape. Validation: rejection rate per tier per contract; a hand-checked sample of fifty bindings, fifty fact rows, and fifty filed topic paths scored against source, precision with a confidence interval (the Eywa-style measured-rejection posture); the merge ledger spot-audited by walking five attributes back to their source tokens.

**Retrieve and inject.** Retrieval is functions over the store, no model calls. The injection accountant assembles context under a hard budget for the three strategies, ordering per the injection reading. Validation: budget never exceeded (property test), composition logged and replayable from run rows, and a manual read of ten compositions per strategy before any scoring run.

**Maintain: fold and supersession.** Fold is deterministic gather plus one summarize call per stale node; staleness is the content hash from the data model. Supersession is deterministic collision detection on subject plus predicate, with `same_as` handling: entity merge and fact re-attachment. Validation: idempotence (a second maintain pass folds zero nodes); the hash property that out-of-band edits are detected where a dirty flag would miss them; a fixture corpus with planted supersessions (the Scabbers case as literal test data) asserting both the read rule and the retention of superseded rows; the corrected-facts question band later re-validates this end to end.

**Evaluation spine.** The runner executes question sets against arms; the judge is `generate` on a tier never used for writing in that run, with position and verbosity bias mitigations from the judge reading. Validation: judge calibrated against one hundred hand-labeled answers, agreement reported with kappa; certification stored per question per tier. The spine runs from the first week it exists, thin, so numbers accumulate while stages mature.

**Wiki generator (the demo, spring).** Sequenced after the committed core: it renders whatever exists whenever it runs, so deferring it costs nothing but the pages themselves. A projection, not a subsystem: `jinja2` templates over the store (one small, standard dependency, replaceable by string templates) rendering entity pages, group pages as fact queries, and timeline pages in `asserted_at` order, as static HTML. Portrait generation reads appearance attributes from the entity page and calls an image API; optional, cheap, last. Validation: human eyes for the demo corpus; the structure-versus-wiki comparison in the testing outline for the measured corpus.

## Order and gates

Interfaces, adapters, segmenter, distiller with filing, retrieve, inject, fold and supersession, spine, wiki: the framework's own order (ingest, organize, retrieve, inject, maintain) with the spine alongside. Each stage opens only when the previous stage's validation is logged. Two standing exceptions: the spine starts as soon as the distiller exists, and the wiki can render at any time, which makes it the running progress demo as well as the final one.

## What "validated" means here

For every stage: the contract rejects malformed output and the rejection is counted; the deterministic parts carry property tests; the model parts carry a hand-labeled sample with an agreement or precision number; and the whole pipeline answers to the question bands, the miss rate, and the stale-serve rate, which no stage can satisfy by grading itself.
