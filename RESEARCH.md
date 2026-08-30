# Research notes

What the paper claims, what it measures, and what stands in its way. Per-work
detail is in `docs/digest.md`; drafted related-work prose is in
`docs/related-work/`; bibliographic corrections for the survey tails are in
`docs/gap_survey_entries.json` and `docs/kg_survey_entries.json`.

## The claim

Published pipelines extract entities chunk by chunk. GraphRAG composes text
units of about 1,200 tokens and extracts entities from each one separately;
Zep extracts per episode with a four-message lookback, then resolves against
its graph. This design reads the whole unit first, establishes its cast, and
conditions every downstream call on that cast. The bet is that the cast pass
measurably reduces duplicate entities, because "Tip", "the boy", and
"Tippetarius" stop being three independent discoveries reconciled after the
fact.

Reconciliation across works uses two signals: attributes the text itself
supports, and co-occurrence. A Harry who appears with Ron is not a Harry who
appears with Watson. The Greek corpus supplies hundreds of labeled test pairs
for free, since Ovid names in Latin what Homer names in Greek.

A second hypothesis rides along unverified: every hierarchical memory system
we found partitions its material, one unit to one cluster, while this design
places a unit in every thread it belongs to at full weight. Search before
claiming it.

## What is already taken

Seven earlier candidate claims were searched adversarially and all seven are
occupied. Do not resurrect one without rereading its occupier.

| Claim | Occupied by |
|---|---|
| Proactive recall | CogniFold 2605.13438, ProactAgent 2604.20572, ENPMR-Bench 2605.27240 |
| Cold-start schema induction | AutoSchemaKG 2505.23628, SCOPE/SCION 2607.21610, EvoTaxo 2603.19711 |
| Narrative threads from conversation | TraceMem 2602.09712 |
| Entity-centric summarization | EntSUM (ACL 2022), EntSUMv2 (EMNLP 2023) |
| Quote-gated writes | Governed Persistent Memory 2608.12476, Eywa 2605.30771 |
| Hash-triggered refolding | MemForest 2605.23986, and every build system |
| n=1 longitudinal corpus | MyLifeBits (CACM 2006) |

All seven occupiers were characterized from abstracts, none read in full.
Where daylight might exist: CogniFold evaluates structural formation rather
than recall, ProactAgent lives in embodied task agents rather than
conversational archives, AutoSchemaKG operates at web scale rather than one
person's record, and EntSUM summarizes single documents on request without
accumulating anything. Personal-KG work closest to our corpus type: From
Strings to Things 2607.00003.

Two threats never searched: a published requirements analysis for assistant
memory, and an existing literary memory benchmark. Search both before the
first paragraph of the paper is written. And six memory benchmarks appeared in
eighteen months, so any novelty check is stale by November; re-run the
adversarial queries immediately before posting, not just before writing.

Three method rules, each paid for once. Adversarial kill-searches find what
field surveys miss; the August survey of 33 verified citations missed six of
the seven occupiers that ten minutes of hostile queries found. A README is not
the paper; a capability was once denied from a README and the paper defined
it. Run a control query before trusting an empty result; two works were
declared unavailable that were on Gutenberg the whole time.

## What the field says is unsolved

Each row cites published work saying so. The two-year prototype deployment
corroborates every row and authorizes none of them.

| Requirement | The field saying so |
|---|---|
| Fact supersession | MemoryAgentBench: no tested system above 28% on fact updates |
| Entity resolution | Noy et al. 2019: disambiguation the top challenge across five production graphs |
| Faithfulness | FABLES: best model 90.9% faithful; best automatic checker 58.2 F1 |
| Coverage | FABLES: 33 to 65% of summaries omit key events |
| Incremental update | RAPTOR, GraphRAG, and Talebirad all name insertion unsolved |
| Cost accounting | Anatomy of Agentic Memory 2602.19320: system costs overlooked |
| Consultation | every benchmark poses the query; a store never consulted fails none |

## Measurements

Committed for October 15, in order of certainty.

| Measurement | Against | Cost |
|---|---|---|
| Entity and coreference F1, entity-first vs chunk-first | LitBank gold (dbamman/litbank; about 2,000 words sampled per work) | free scoring |
| Duplicate-minting curve, nodes minted per unit | our own ingest, per tier | free |
| Quote-gate pass rate, rejection rate per stage per tier, predicate sprawl, token cost | run logs | free |
| Plot-vs-cell consistency | the two axes over identical text | free |
| LongMemEval-S, whole set with the 78-question knowledge-update band broken out | Zep's published overall scores: 63.8 (gpt-4o-mini) and 71.2 (gpt-4o) vs full-context 55.4 and 60.2 | one paid run |
| NarrativeQA on the 12 overlapping works, 345 questions | reference answers; three injection arms: raw top-k, entity store, both | one paid run |
| OCR tax and translation tax | Three Kingdoms as proofread text, raw OCR, and machine translation of the same content | cheap runs |

The LongMemEval file Zep measured on is the original release, now deprecated
in favor of a cleaned one. Run the original for the comparison and the cleaned
for our own numbers; quoting one against the other is invalid. Both are in
`data/eval/` via `scripts/fetch_eval.py`.

The anti-goal: do not try to beat Zep on its benchmark. Benchmarks here supply
task definitions and comparability, never a contest. Full-context is the
honest upper baseline on small corpora and long-context models beat extraction
stores on raw recall by 33 to 35 points on LoCoMo and LongMemEval; the store's
case is cost, provenance, and supersession, not recall supremacy.

The standing objection to the whole corpus choice: these are famous books, the
model already holds them from training, so a raw score proves nothing about
the memory. Three answers travel with every result. Every committed comparison
is between arms over identical text, so both arms are equally contaminated.
The NovelQA finding is that models know famous plots but fail on depth, minor
characters, and chapter-level chronology, which is exactly where the store
competes. And the deerstalker probe catches weight leakage directly.

Probes worth running if hours remain: a stale-serve rate over documented
supersessions (MemStrata 2606.26511 puts plain RAG at 15 to 40% stale), and an
implicit-conflict probe (STALE 2605.06527: best model 55.2%). Both numbers
come from abstracts; neither paper is in the library yet.

Rules that keep the numbers honest. The judge model never shares a tier with
any writer and is calibrated on a hand-labeled sample before its scores count.
Segmentation gets a deterministic baseline (TextTiling) beside the model call.
Retrieval misses are classified coverage versus vocabulary before prescribing
a fix, because the two have different remedies. Agent-fleet evaluations carry
completion accounting, since a partial fleet result looks confident.

## Evidence checked by eye

Never presented as results.

| Fixture | Shows |
|---|---|
| Tip becomes Ozma, Oz book 2 | aliasing, merge, supersession, time-scoped truth, at document 2 |
| Watson's wound, shoulder then leg | contradiction inside one author, no reconciling reading |
| The deerstalker probe | Doyle never wrote one; assembled pages cannot contain it, generated pages can |
| Helen at Troy, Homer vs Euripides | source disagreement rendered inline |

## What a run costs

Oz is about 600 units, 1.7M tokens, 2,800 tokens per unit, five major entities
per unit. Unbatched, a unit costs roughly 19,000 tokens in and 2,150 out
across the entity, fact, and cell passes; batching the cell calls is the
dominant saving. The full four-corpus run spans $2.30 on the cheapest tier to
$335 on the priciest at August 2026 batch rates, two orders of magnitude,
which is why tier sensitivity gets its own experiment. Batch discounts run 50%
on the three majors. Set the spending stop before every run; the prototype ran
out of credit mid-pass twice.

## What the prototype already showed

The two-year personal deployment (about 1,000 distilled summaries over 20M
transcript tokens, a 25:1 ratio) supplies motivation, not evidence. Its
sharpest finding: tracing 39 rolled-up claims to raw transcripts found all 8
defects in the synthesis layer while all 31 leaf-level checks were clean, and
an entailment gate is structurally blind to this because a hardened sentence
is still entailed by its hedged source. A mutation study found 5 of 10 induced
breakages produced no signal at all. Twice, dated, the store held an answer
and a session argued for twenty turns without consulting it.

It also demonstrates the duplicate-minting problem the claim targets: its
registry grew to 1,169 entity names, and its two entity systems produced 70
and 388 entities with only 17 names in common. The corpus proves the problem;
nothing there measures it. And read-time supersession is a paid-for decision,
not taste: the prototype's automatic supersession engine produced four
distinct classes of confidently wrong answers and was deleted on purpose. The
fix was subtraction, and the append-only ledger judged at read time is what
replaced it.

The prototype's summaries were written by models that had seen the writer's
patterns, a contamination any mention of the archive must carry.

## How the paper must be framed

The framing rule, decided before the first paragraph: "here is our backend and
we measured it" is a system paper and dies on prior art. "Here are measured
tradeoffs in this design space, demonstrated on a working backend" is an
empirical study. Borrow openly and say so: hierarchical summaries from
GraphRAG and RAPTOR, temporal facts and invalidation from Zep and Snodgrass
beneath it, per-entity summarization from EntSUM. Cite Asymmetric Capacity
Allocation 2608.21345 beside any tier-allocation result. Four citations are
not usable until verified: the Angles venue, the Rost venue, the Wikidata
ranks page, and the full Hernández record; details in
`docs/kg_survey_entries.json`.

Deliberately not adopted, with reasons. RDF reification answers a question
that is native in a property graph whose edges carry properties; Hernández
2015's finding that singleton properties broke four of five engines is a
warning about RDF stores, not about this design. CoALA's four-way memory
taxonomy is a useful prose frame that does not map onto storage. And the
prepared answer to the Cyc objection: symbolic AI failed on the authoring
bottleneck, LLMs removed exactly that bottleneck, and the accepted caveat is
that what becomes inspectable is the memory, not the weights.

## Spring: one store, two access paths

The product serves MCP over stdio for desktop clients and a local HTTP server
with a browser extension for everything else. Workspaces partition by
filesystem, one folder per workspace; the vocabulary is workspace and device
pairing, never user and access grant. Isolation is one process per workspace,
never one process routing by token, because a token-validation bug would cross
the partition. Credentials live outside the synced folder or encrypted at
rest; the prototype has already pushed unrevoked tokens to history. A pairing
code checked once at provisioning is not authentication on a publicly
reachable tunnel. Updates snapshot per layer and roll back rather than merge.

Chat exports are worse than they look. They include no attachments, so
onboarding scrapes those once through the authenticated browser. Gemini
exports carry no stable conversation id, so a re-export mints duplicates
wholesale and content-hash idempotence alone will not save you. Only the
newest takeout per vendor gets parsed today, so older archives with unique
conversations are silently skipped; state the denominator on every corpus
statistic. The prototype also retired one entity layer for being rebuilt
nightly and consumed by nothing; an entity index earns trust only after it is
built from the ledger and wired into a recall surface.

IRB review comes before recruiting a single tester; a department email is
human-subjects research, and if testers might set it up for family, scope the
study to adults explicitly, since minors require parental permission and child
assent. Per-user API keys are the default, keeping the host out of the
accountability path. The symposium provides one 36 by 48 foamboard; lay it out
problem, evidence, artifact.
