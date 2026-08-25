# Three shapes the project could take

Prepared by the assistant from the research package, the design brief, and the constraints on record: roughly 70 to 100 project hours this fall concentrated between September 1 and November 15, PhD applications due December 1 to 15, IT 494 continuing through Spring 2027, and the standing requirement that Justin works through all code himself. These are judgments, not options for the sake of options. A recommendation follows the three shapes.

## Shape 1. Measure the tree

The semester's product is an evaluation, not a feature. Build the harness that the system has never had: a stratified question set over the archive with four bands (answerable from rollups alone; requiring a specific leaf; requiring synthesis across areas; requiring a fact that was later corrected), scored across delivery arms (summaries preloaded, retrieval as it stands, and both). Add the two measurements the package's corpus does not supply: a counterfactual miss rate, which has no published counterpart at all, and a stale-serve rate, measured elsewhere for plain RAG but never on a live personal store. Write the result as a short paper by early December.

What it pays: this is the only shape that produces a December artifact for the applications, and it converts the system's weakest point, no real metrics, into the contribution itself. The fourth band and the miss rate have no published counterpart in the package's corpus. It fits the hour budget because the corpus, the golden-question scaffolding, and the maintenance instrumentation already exist; the work is design, measurement, and writing rather than construction.

What it risks: no new capability ships. The demo at the end is a report and a harness, which is the right artifact for a committee and a thin one for anyone else. The result may also be unflattering to the system; academically that is still a result, and it is worth saying in advance.

## Shape 2. Ship the backend

The semester's product is a distributable system. Extract the engine from the personal archive: the capture, filing, rollup, and maintenance machinery, separated from one man's life categories, installable by someone else, with the multi-chat shared-state pattern from annual training as the flagship demonstration. The organizational use case becomes a design target rather than a hypothetical: one backend, several concurrent consumers.

What it pays: a portfolio artifact that a non-academic audience can run, which serves the federal hiring channel better than a paper, and a foundation the help-desk use case could later stand on.

What it risks: it does not produce a December paper, and the engineering will not fit 70 fall hours under a review-every-line constraint. Packaging, isolation of personal data, and installation paths are exactly the kind of work that consumes weeks silently. Honestly scoped, this is a spring product, and choosing it for fall means entering the application window with nothing new.

## Shape 3. One innovation, studied

Pick the single narrowest mechanism the research pass left unclaimed and study it properly: implement, measure against the obvious alternative, write. The two candidates the package supports are content-derived staleness, the hash-versus-dirty-flag demonstration (staleness recomputed from the material itself, which stays correct under hand edits where flag-based schemes silently fail), and outcome-signal mining from correction turns (recovering, from the rephrasings and corrections in past transcripts, the misses nobody logged, which the system currently cannot surface). Either is a contained experiment on the live archive.

What it pays: the strongest research identity per hour. A narrow, true, measured claim is a better writing sample than a broad description of a system.

What it risks: single-shot exposure. If the experiment lands null, December holds a null result on a personal corpus, which is publishable in a workshop sense but is a harder sell, and the wider system story goes untold.

## Recommendation

Treat the year as two semesters, because IT 494 is two semesters. Fall is Shape 1 carrying Shape 3 inside it: the evaluation harness is the semester, and the corrected-facts band plus the miss rate are the innovation, embedded where they cannot miss the December window. Spring is Shape 2 built on what fall measured: ship the backend whose properties are now documented rather than asserted, with the spring half of the course absorbing the packaging work that would sink the fall.

Two commitments make the recommendation concrete. First, the paper is scoped to what the harness shows by November 15, with the writing weeks aligned to the calendar's dead stretches so coursework collisions are planned rather than suffered. Second, every artifact of the fall, questions, scoring code, and results, is built for reuse as the spring backend's regression suite, so nothing measured is thrown away.
