# Novelty reassessment, 2026-08-26

Both contributions named in `IT494_PLAN.md` are occupied by published work. This document
records what was searched, what was found, what each paper takes, and what has not been checked.
It does not propose a replacement claim.

## What was searched, and how it differed from the August 19 survey

Adversarial full-text queries against the arXiv API, written to **find the paper that scoops the
project** rather than to map the field. Roughly ten minutes of querying.

The August 19 survey ran seven agents and verified 33 citations. It missed every paper below
except one, and most of them predate it. The difference is the question being asked. A survey
asking "what is this field" and a search asking "what kills this claim" return different sets,
and only the second one protects a contribution.

That is a methods finding independent of the result, and it matters because the same survey
method was going to be relied on again before submission.

## Contribution 1: proactive recall. Taken.

The claim in the plan reads: *"Every published memory benchmark presupposes that a question is
asked... A memory that is complete, indexed and never consulted fails no existing benchmark."*

That sentence is false as of May 2026.

**CogniFold** (arXiv:2605.13438, May 2026) is the closest and the most damaging. It presents a
brain-inspired "always-on" agent memory for proactive assistants that continuously **folds**
fragmented event streams into self-emerging structures; grounds itself by **extending
Complementary Learning Systems theory**, which is the same theoretical spine identified for this
project on August 19; merges structures when semantically similar and decays them when stale;
and surfaces intents when concept-cluster density crosses a threshold. It ships code, evaluates
on LoCoMo and LongMemEval, and introduces its own CogEval-Bench for structural formation.

The only visible difference from the abstract is the trigger. CogniFold fires on concept-cluster
density; this project fires on a session-boundary hook. That is the same class of narrow
distinction this project's own adversarial pass already downgraded when it was made about
hash-versus-flag staleness.

**ProactAgent** (arXiv:2604.20572, April 2026) takes the measurement. It observes that existing
methods retrieve passively and therefore "miss knowledge gaps that arise during interaction",
and learns when to retrieve by **comparing paired continuations from identical interaction
prefixes with and without retrieval**. That is a counterfactual measurement of whether retrieval
would have helped, which is the core of the counterfactual miss rate, expressed as a learned
policy rather than a reported rate.

**ENPMR-Bench** (arXiv:2605.27240, May 2026) is a benchmark for proactive memory retrieval. Its
domain is narrower, being emotional support rather than general recall, but its existence alone
falsifies the "no benchmark can express this" framing.

**Also in the cluster**, each occupying nearby ground: ProMem (2601.04463) on proactive memory
extraction, PASK (2604.08000) on intent-aware proactive agents with long-term memory, VitaBench
2.0 (2605.27141) on evaluating proactive agents in long-term user interaction, and Proactive
Memory Agent (2607.08716), which was already known from the August 19 dossier and had been
recorded there as intra-task only.

## Contribution 2: cold-start structure induction. Taken.

**AutoSchemaKG** (arXiv:2505.23628, May 2025) is fully autonomous knowledge graph construction
that eliminates the need for predefined schemas, inducing schemas directly from text while
extracting triples. Fifty million documents, 900 million nodes, 5.9 billion edges. It reports
**92 percent semantic alignment with human-crafted schemas at zero manual intervention.** That
is the contribution, done at web scale, with a number attached.

**SCOPE and SCION** (arXiv:2607.21610) is a benchmark for corpus-to-schema induction plus an
auditable reference pipeline. Schema induction is therefore not merely solved but measured, with
released baselines to beat.

**EvoTaxo** (arXiv:2603.19711, March 2026) builds and evolves taxonomies from **temporally
ordered streams**, accumulating structural evidence over time windows, consolidating candidate
edits, and keeping a concept memory per node to preserve semantic boundaries as discourse
shifts. That is the living-tree-that-ingests-over-time idea, applied to taxonomy, with results
on two Reddit corpora.

**From Strings to Things** (arXiv:2607.00003) constructs personal knowledge graphs from
unstructured conversational data, framed around privacy, with an evaluation of extraction
fidelity and downstream utility. That is this project's corpus type and its privacy angle.

**BoostTaxo** (2605.12520) does zero-shot taxonomy induction. **Bian et al.** (2510.20345) is a
survey of LLM-empowered knowledge graph construction, which is itself evidence that the space
is mapped.

## What this does not establish

Read from abstracts only. None of these papers has been read in full. Differences that abstracts
hide are the place any daylight would be, and three are worth checking specifically: CogniFold
evaluates structural formation rather than recall miss rate; ProactAgent's domain is embodied
task agents rather than conversational archives; AutoSchemaKG operates on web-scale document
corpora rather than a single user's longitudinal record.

Not searched at all: the three instruments added to the corpus on August 26, being the OCR tax
control, the translation tax control, and the contamination probe. These were flagged as weak or
unverified when proposed and remain so. They are methodological rather than architectural, and
whether they are novel in this setting is unknown.

## The standing implication for method

The field is publishing at a rate that makes any novelty check perishable. Six memory benchmarks
have appeared in eighteen months. CogniFold is three months old and was invisible to both a
seven-agent survey and to an assistant whose training cutoff precedes it.

Any claim cleared today is stale by November. A re-check immediately before posting is
mandatory, and it should use adversarial queries rather than a field survey.
