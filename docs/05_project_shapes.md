# Three shapes the project could take

Prepared by the assistant from the research package, the design brief, and the constraints on record: roughly 70 to 100 project hours this fall concentrated between September 1 and November 15, PhD applications due December 1 to 15, IT 494 continuing through Spring 2027, and the standing requirement that Justin works through all code himself. One correction governs this document: the goal is a rigorous and defensible general system, not an improvement to the existing prototype. The prototype's role in every shape below is evidence and instrument: two years of operation that reveal the real problems, a corpus, and a first tenant. It is never the deliverable. These are judgments, not options for the sake of options, and a recommendation follows.

## Shape 1. Design first, prove the core

The semester's product is a defensible design and a working core. The sequence: read the field until each design question can be argued from the literature rather than from habit; write the architecture of a general knowledge backend, with every load-bearing choice justified by a citation, a measurement, or a named open question; then implement the core of it, small but real, with evaluation built in from the first commit rather than bolted on. The prototype supplies the requirements the literature cannot: the documented failure cases, the corpus, and a live user. Where the new design disagrees with what the prototype does, that disagreement is stated and defended, which is what makes the design an argument rather than a description.

What it pays: this is the shape that matches the stated goal directly. It produces the artifacts a committee and an application both respect: a design that can be defended choice by choice, a core that runs, and numbers behind both. It fits the hour budget because the expensive half, construction at scale, is explicitly deferred to spring.

What it risks: a design semester can slide into a reading semester. The mitigation is the core: code that runs is the proof the design is real, and the December paper is scoped to design plus first measurements, not to a finished system.

## Shape 2. Build the general system outright

The semester's product is the backend itself: capture, structure, currency, and retrieval as a general service, installable, multi-tenant in principle, with the prototype's data migrated in as the first tenant and the annual-training multi-chat pattern as the demonstration.

What it pays: the strongest possible demo, and a foundation the organizational use case could stand on immediately. A portfolio artifact for the federal hiring channel as well as the academic one.

What it risks: rigor is the first casualty of a build semester. Under a review-every-line constraint inside 70 to 100 hours, engineering will crowd out both the reading and the evaluation, and December would hold a partially built system with neither a defended design nor results. Honestly scoped, this is the spring semester, executed against a design that fall produced.

## Shape 3. One question, answered generally

The semester's product is a single defensible result about memory systems in general, studied on the prototype's corpus because that is the corpus available. The two candidates the package supports: the counterfactual miss rate, how often a store held the answer and the session never consulted it, which no published benchmark can even express because benchmarks pose the query; and content-derived staleness against write-time flags, which is a general correctness property of any human-editable store. Either is framed as a claim about the class of systems, measured on one instance.

What it pays: the cleanest research identity per hour, and the fourth-band and miss-rate instruments would be contributions other systems could adopt.

What it risks: a narrow result leaves the general-system goal unadvanced except by reputation. If the aim is a defensible system rather than a defensible sentence, this shape is an ingredient, not a semester.

## Recommendation

Shape 1, with Shape 3's instruments as its evaluation layer, and Shape 2 as spring. Concretely: September is the reading, closed out by a short written synthesis that turns the reading list into positions. October is the design document, general by construction, defended line by line, with the prototype cited as evidence rather than authority. October into November is the core implementation with the evaluation harness alongside it, the corrected-facts band and the miss rate among its instruments, run first against the prototype's corpus as tenant zero. The December paper reports the design and the first measurements. Spring, in the student's framing, builds the distributable harness others can run and tests it: installation by someone who is not the author, a cold corpus the workflow did not grow up on (the certified-unknown literature test in the testing outline), migration of the student's own two years of raw data out of the prototype and into the harness as the proof that tenant zero moves, and the fall harness riding along as the regression suite. The migration doubles as the strongest single validation available: the mock retires, the product carries its history, and any answer the old system could give and the new one cannot is a regression with a name.

Two commitments make it concrete. First, every fall artifact is written about the general problem, with the prototype as the running example, so nothing has to be reframed later. Second, the paper is scoped to what exists by November 15, aligned with the calendar's dead stretches, so coursework collisions are planned rather than suffered.
