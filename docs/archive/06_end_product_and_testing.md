> **SUPERSEDED 2026-08-28** by `03_design.md` (delivery) and `02_requirements_and_testing.md` (evaluation).
> Kept for the record; do not build from it. Index: `docs/README.md`.

# End product, test data, and what gets recorded

The prototype is a mock of the intended end state: a general workflow built into a product and tested on data the workflow did not grow up on. Fall produces the defended design, a working core with its evaluation harness, and a short paper; spring builds the product out. Every candidate shape answers to the same measurements.

## The end product

Fall delivers four things: a written synthesis closing the reading phase, the positions taken with the works that ground them; the design document for the general backend, treating the five stages (ingest, organize, retrieve, inject, maintain) and the evaluation spine as first-class components, each choice defended from the literature or marked as an open question for the implementation to test, each departure from the prototype argued; the core implementation with its harness built alongside, enough of the design running to measure, populated with the prototype's archive as tenant zero (fall's realistic reach: ingest and organize plus one comparison); and the paper distilled from the design and first measurements, targeted at a workshop or arXiv by early December.

Spring delivers the system the design describes: installable, documented, separable from any one tenant's data, with the annual-training multi-chat pattern as the demonstration and the fall harness as its regression suite.

## Test data, a fork to choose deliberately

Three options answer different questions.

The prototype's archive is tenant zero: two years, roughly a thousand distilled summaries over twenty million tokens of transcript, with ground truth available from the one person the corpus is about. It is the only corpus on which the corrected-facts band can be built today, because it carries documented instances of facts that changed. Its limits: private, so not reproducible; summaries written by models that have seen the writer's patterns, a contamination named in the report; and one tenant, so nothing measured on it alone demonstrates generality.

A public benchmark is the generality check: one suite from the package, run in its published configuration, shows the design is not shaped to one archive. Scoped as a week.

A second, disjoint corpus is the honest test of portability, ingested cold through the same pipeline. The chosen class: long serial fiction with a dedicated community wiki. The novel half instantiates the corrected-facts band: a book is a life in miniature, events arriving in order, entities accumulating relationships, facts superseded by later reveals, ground truth obtainable by reading. The wiki half upgrades the evaluation from answers to structure: the harness induces a tree, entity pages, and dated facts from raw text, and the community hand-built the same artifacts over years, so induced structure can be scored against theirs for entity coverage, relation recall, and timeline agreement. Two rules govern it. First, a wiki implies popularity and popularity implies training exposure, so certification moves from the work to the question: the question set is run closed-book against every bare model tier and only questions all tiers fail are kept; long serials make this workable because models know famous plots but fail on depth, minor characters, and chapter-level chronology (the NovelQA finding). Second, the wiki is a reference, never an authority: disagreements are adjudicated by the text, and cases where the harness is right and the wiki wrong are reported, not discarded. Three candidates are nominated in Phase 0. One becomes the primary corpus with the full protocol (deep question set, all four bands, structure scored against its wiki); at least one more runs as a lighter replication (a smaller certified set, entity-coverage scoring only), so the claim is about books, not one book. The replication protocol exists the moment the primary protocol does, making the second work cheap. This corpus gates the spring distributable claim; if fall runs out of hours, it is stated in the paper as future work.

The assumed choice: design measured on tenant zero with the contamination caveat open, one public suite for generality, and a cold literature corpus, certified per question, gating the spring release.

## What gets recorded

Every run records the same row: date, arm, configuration hash, question identifier and band, verdict against the fixed answer, tokens in and out, dollars, and latency. The instruments are general by construction: the four question bands, the counterfactual miss rate, and the stale-serve rate are defined against any conforming store; tenant zero is their first subject. The standing counters the prototype already computes stay in the record as the design document's evidence base. Incidents get their own log: every case of a store holding an answer a session failed to consult, and every superseded fact served as current, each with enough context to re-derive. These logs start accumulating the day the harness exists, not the day the paper is written.

## What gets printed

Three artifacts go to the advisor on a cadence: the metric definition sheet, early, so the measurements are agreed before results exist; the design document at its first complete draft, the artifact that most needs adversarial reading; and the review trail, which code was walked through line by line, when, and what changed, kept as a running log rather than reconstructed later.

## The authorship constraint

The constraint is authorship, not review. The mock was built by directed AI execution that went unexamined, the right way to prove the idea and the wrong way to build the product. Here the student implements, with AI assistance in drafting and discussion but never as the unexamined author. The design document, the harness runner, the scorer, and every metric definition are build gates: the project does not proceed past them until the student has written or rewritten them and logged it. Build lands Tuesday through Friday; review happens in the Monday and Wednesday campus gaps, reading time by construction. The five dead stretches in the design brief are scheduled as review-and-writing weeks, because reading survives a deadline week and building does not.
