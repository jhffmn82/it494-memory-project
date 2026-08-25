# End product, test data, and what gets recorded

Prepared by the assistant. This outline assumes the recommendation in the project-shapes document: fall produces a measured evaluation of the memory system with a short paper; spring produces the distributable backend. If a different shape is chosen, the testing section still applies, since every shape eventually answers to the same measurements.

## The end product, concretely

Fall delivers three things. First, an evaluation harness in the project repository: a stratified question set over the archive, scoring code, and a runner that evaluates each delivery arm under identical conditions. Second, a results report: the arm-by-arm, band-by-band numbers with their definitions, honest about what the corpus is and how the questions were built. Third, the paper distilled from the report, targeted at a workshop or arXiv by early December.

Spring delivers the backend: the engine separated from the personal archive, installable, documented, with the fall harness repurposed as its regression suite and the annual-training multi-chat pattern as the demonstration.

## Test data, the fork that must be chosen deliberately

Three options exist and they answer different questions.

The personal archive is the primary instrument. Two years, roughly a thousand distilled summaries over twenty million tokens of transcript, with a single ground-truth authority available: the person the corpus is about. No published benchmark has this property, and the corrected-facts band is only constructible here, because only this corpus carries documented instances of facts that changed and were superseded. Its weaknesses are equally real: it is private, so no one can reproduce the numbers; and the model that wrote the summaries has seen patterns of the writer's life, so contamination must be named in the report rather than waved off. The mitigation is procedural: questions authored from transcripts by a process that is documented, answers fixed before any arm runs, and the question set published even though the corpus cannot be.

A public benchmark supplies comparability. One suite from the package, run in its published configuration, anchors the harness to numbers other people can check. This is a secondary result and should be scoped as a week, not a month.

A fresh synthetic corpus is the clean option and the expensive one: conversations generated or collected after the fact, never seen by any maintenance pass. It answers the contamination objection completely and costs more hours than the fall has. It belongs in spring, or in the paper's future-work section, stated plainly.

The deliberate choice this outline assumes: primary results on the personal archive with the contamination caveat in the open, one public suite for anchoring, synthetic deferred.

## What gets recorded

Every run records the same row: date, arm, configuration hash, question identifier and band, verdict against the fixed answer, tokens in and out, dollars, and latency. Alongside the runs, the standing counters the system already computes stay in the record: coverage, drift and staleness counts, and audit results per maintenance pass, since the paper's claims about currency rest on them. Incidents get their own log: every observed case of the store holding an answer that a session failed to consult, and every case of a superseded fact served as current, each with enough context to be re-derived. These two logs are the raw material of the miss rate and the stale-serve rate, and they start accumulating the day the harness exists, not the day the paper is written.

## What gets printed

For the advisor, three artifacts on a cadence. A one-page metric definition sheet, early, so the measurements are agreed before results exist. The arm-by-band results table with confidence noted, once per milestone. And the review trail: which code was walked through line by line, when, and what changed as a result, kept as a running log rather than reconstructed later.

## The QA constraint, structurally

Nothing lands unreviewed. Work arrives in units small enough to read in one sitting, each with a stated purpose and a diff against the last reviewed state; the harness runner, the scorer, and every metric definition are review gates, meaning the project does not proceed past them until they have been walked through and signed off in the log. The weekly rhythm follows the campus calendar: build lands Tuesday through Friday, review happens in the Monday and Wednesday campus gaps, which are reading time by construction. The five dead stretches in the design brief are scheduled as review-and-writing weeks, not build weeks, because reading survives a deadline week and building does not.
