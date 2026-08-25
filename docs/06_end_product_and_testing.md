# End product, test data, and what gets recorded

Prepared by the assistant. This outline assumes the recommendation in the project-shapes document: the goal is a rigorous, defensible general system; fall produces the defended design, a working core with its evaluation harness, and a short paper; spring builds the system out. The existing prototype is evidence, corpus, and first tenant throughout, never the deliverable. If a different shape is chosen, the testing section still applies, since every shape answers to the same measurements.

## The end product, concretely

Fall delivers four things. First, a written synthesis that closes the reading phase: the positions taken, with the works that ground them. Second, the design document for the general backend: capture, structure, currency, retrieval, and evaluation as first-class components, each choice defended from the literature or marked as an open question the implementation will test, and each departure from the prototype's way of doing it stated and argued. Third, the core implementation with its evaluation harness built alongside: enough of the design running to measure, populated with the prototype's archive as tenant zero. Fourth, the paper distilled from the design and the first measurements, targeted at a workshop or arXiv by early December.

Spring delivers the system the design describes: installable, documented, separable from any one tenant's data, with the annual-training multi-chat pattern as the demonstration and the fall harness as its regression suite.

## Test data, the fork that must be chosen deliberately

Three options, answering different questions, and the general-system goal changes their weights.

The prototype's archive is tenant zero: two years, roughly a thousand distilled summaries over twenty million tokens of transcript, with ground truth available from the one person the corpus is about. It is the only corpus on which the corrected-facts band can be built today, because it carries documented instances of facts that changed. Its limits are real: private, so results are not reproducible by others, and the summaries were written by models that have seen the writer's patterns, so contamination is named in the report. For a general-system claim it has one more limit worth stating plainly: it is one tenant, and nothing measured on it alone demonstrates generality.

A public benchmark is the generality check, not just an anchor. One suite from the package, run in its published configuration, shows the design is not shaped to one man's archive. Scoped as a week.

A second, disjoint corpus is the honest test of the design's portability, and the cheapest version need not be synthetic: any project corpus the system did not grow up on, ingested cold through the same pipeline. This is a spring gate for the distributable claim, stated in the paper as future work if fall runs out of hours.

The deliberate choice this outline assumes: design measured on tenant zero with the contamination caveat open, one public suite for generality, a cold second corpus gating the spring release.

## What gets recorded

Every run records the same row: date, arm, configuration hash, question identifier and band, verdict against the fixed answer, tokens in and out, dollars, and latency. The harness instruments are general by construction: the four question bands, the counterfactual miss rate, and the stale-serve rate are defined against any conforming store, with tenant zero merely their first subject. Alongside the runs, the standing counters the prototype already computes stay in the record, since the design document will cite them as the evidence base. Incidents get their own log: every case of a store holding an answer a session failed to consult, and every superseded fact served as current, each with enough context to re-derive. These logs start accumulating the day the harness exists, not the day the paper is written.

## What gets printed

For the advisor, three artifacts on a cadence. The metric definition sheet, early, so the measurements are agreed before results exist. The design document at its first complete draft, because that is the artifact this project stands on and the one that most needs adversarial reading. And the review trail: which code was walked through line by line, when, and what changed as a result, kept as a running log rather than reconstructed later.

## The QA constraint, structurally

Nothing lands unreviewed. Work arrives in units small enough to read in one sitting, each with a stated purpose and a diff against the last reviewed state. The design document, the harness runner, the scorer, and every metric definition are review gates: the project does not proceed past them until they are walked through and signed off in the log. The weekly rhythm follows the campus calendar: build lands Tuesday through Friday, review happens in the Monday and Wednesday campus gaps, which are reading time by construction. The five dead stretches in the design brief are scheduled as review-and-writing weeks, not build weeks, because reading survives a deadline week and building does not.
