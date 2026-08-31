# Research notes

What the paper claims, what it measures, and what stands in its way. Per-work
detail is in `docs/digest.md`, drafted related-work prose in
`docs/related-work/`, the full dataset contract in `docs/evaluation-corpus.md`,
the resolution design in `docs/entity-resolution.md`, schema sources in
`docs/references.md`, and bibliographic corrections in the two survey JSONs.

## There is no new idea, and that is survivable

Twelve candidate contributions were searched adversarially and all twelve are
already published. Do not resurrect one, and do not add a thirteenth without
searching it first; all twelve died by assuming nobody had done it.

| The idea | Already published by |
|---|---|
| Memory that speaks up unasked | CogniFold 2605.13438, ProactAgent 2604.20572, ENPMR-Bench 2605.27240 |
| Schema induction from raw text | AutoSchemaKG 2505.23628, SCOPE/SCION 2607.21610, EvoTaxo 2603.19711 |
| Narrative threads from chat | TraceMem 2602.09712 |
| Per-character summaries | EntSUM (ACL 2022), EntSUMv2 |
| Thread disentanglement | an active ACL, SIGIR, LREC task |
| Nobody measures memory costs | Anatomy of Agentic Memory 2602.19320 says it first |
| One person's archive as a case study | MyLifeBits (CACM 2006) |
| One chunk in several threads at once | RAPTOR, and CAM (NeurIPS 2025) |
| Novels as a memory testbed | NarrativeXL, MemoryAgentBench, StoryBench |
| Requirements for assistant memory | Jones et al. (CHI 2025), 2606.24775 across 12 systems |
| Entities before facts | iText2KG, RAKG, LINK-KG, CORE-KG, and GraphRAG and Zep themselves, per their own prompts |
| Publishing cleaned novels as a test set | GraphRAG-Bench, AffilKG, STAGE, CoSER |

The sharpest death is entities-first: GraphRAG's prompt "first identifies all
entities" before relationships, and Zep's fact extraction takes an ENTITIES
block. iText2KG ran the nearest experiment and explicitly declines to call
global or local entity context better, because the precision cost buys
unmeasured richness; cite it as an open trade-off. Six memory benchmarks
appeared in eighteen months, so every check here is stale by November; re-run
the adversarial queries immediately before posting.

The venues make the reframe legitimate. PVLDB: novelty "often lies in the
design ... or interesting and effective combination of existing techniques."
NeurIPS 2026: "originality does not necessarily require introducing an
entirely new method." SIGSOFT lists "not the first known solution" as an
invalid reviewer criticism. The price is stated in the same guidelines: less
novelty demands more rigorous evaluation. So the paper is a systems paper for
a demonstration or in-use track: **here is the system, and here is which parts
of it actually help.** Concede in the introduction that every mechanism is
borrowed, with citations, before a reviewer says it for you: hierarchical
summaries from GraphRAG and RAPTOR, dated facts and invalidation from Zep and
Snodgrass beneath it, per-character summaries from EntSUM, incremental updates
from MemTree, graph structure from Angles, fact ranking from Wikidata.

Two papers sit close enough to require full reads before a word is written:
Narrative World Model (2607.05577), same niche and baselines, and Story
Ribbons (IEEE VIS 2025), which builds per-character per-scene summaries with a
quote check over 30 Gutenberg works. Story Ribbons has no search layer; that
difference goes in our introduction, not in a reviewer's complaint.

## The one open measurement worth owning

Resolution is where this design departs from everything it is measured
against. Every surveyed system resolves entities on strings or embeddings plus
an LLM verdict; none uses co-occurrence as a signal. Collective entity
resolution settled in 2007 that the relational signal works. What is
unmeasured is **whether it still pays when the candidate scorer is an
embedding and an LLM**, and iText2KG's own future work asks for the profile
signal. Answering an open question posed by a system in the comparison table
is a better position than any novelty claim. The design, the guards against
merge black holes, and the citations are in `docs/entity-resolution.md`; the
Walmart report (2607.26298) that argues against our soft-veto choice gets
cited against ourselves.

## What the field says is unsolved

Each row cites published work saying so. The two-year prototype deployment
corroborates every row and authorizes none of them.

| Requirement | The field saying so |
|---|---|
| Fact supersession | MemoryAgentBench: no tested system above 28% on multi-hop fact updates |
| Entity resolution | Noy et al. 2019: disambiguation the top challenge across five production graphs |
| Faithfulness | FABLES: best model 90.9% faithful; best automatic checker 58.2 F1 |
| Coverage | FABLES: 33 to 65% of summaries omit key events |
| Incremental update | RAPTOR, GraphRAG, and Talebirad all name insertion unsolved |
| Cost accounting | Anatomy of Agentic Memory 2602.19320: system costs overlooked |
| Consultation | every benchmark poses the query; a store never consulted fails none |

## The measurement slate

The dataset contract, row by row, is `docs/evaluation-corpus.md`. The slate:

| Measurement | Against | Cost |
|---|---|---|
| GraphRAG-Bench novels: full system, no-context control, flat retrieval, then the cells ablation | 9 published gpt-4o-mini baselines, gold answers and evidence, 2,010 questions | the main paid run |
| Hand-labeled alias set, one novel | merge precision and recall from the first ingest | half an hour of labeling |
| NarrativeQA, the 345 questions over 12 works we own | reference answers; same three arms | cheap secondary run |
| LongMemEval, stretch: full-context parity arm, then the 78-question knowledge-update band | Zep's 63.8 over a 55.4 full-context baseline (gpt-4o-mini, original `_s` file) | ~$9 parity, one paid run |
| Read cost, refold cost, coverage difference | MemTree's published 3,750 / 3,850 / 3.27 calls per insertion; no gold answers needed | free |
| The free instruments: rejection rate per stage per tier, duplicate mints per chunk, predicate sprawl, quote-gate pass rate, chunk-versus-cell summary agreement, token cost per arm | our own run logs | free |
| The OCR tax and the translation tax | Three Kingdoms as proofread text, raw OCR, and machine translation of identical content | cheap runs |

GraphRAG-Bench carries the argument in its own baseline table: the cheapest
system spends 879 tokens per question, the strongest graph system 1,008, and the most
expensive 331,375, a 377-fold spread. Landing near the top of the accuracy column at the
bottom of the cost column, with no graph database and no server, is the
finding. Graph methods beat plain RAG on complex reasoning and summarization,
not fact retrieval, so the cells ablation has a built-in target. At n=2,010 a
2.4-point difference is detectable and ablations typically move 2 to 5.

Two LongMemEval files exist because the original was revised: Zep's numbers
are on the original `_s`, so comparisons run there; our own standalone numbers
use the cleaned file. Quoting one against the other is invalid. Run the
full-context arm first: if it reproduces 55.4, the harness is comparable; if
not, say so instead of claiming parity.

The anti-goal: do not try to beat Zep on its benchmark. Benchmarks supply task
definitions and comparability. Long-context models beat
extraction stores on raw recall by 33 to 35 points; the store's case is cost,
provenance, and supersession.

The standing objection to famous books: the model already holds them, so a raw
score proves nothing. Four answers travel with every result. GraphRAG-Bench
chose pre-1900 novels specifically to minimize contamination. Every committed
comparison is between arms over identical text, so both arms are equally
contaminated. The NovelQA finding is that models know famous plots but fail on
depth, minor characters, and chapter-level chronology, which is where the
store competes. And the deerstalker probe catches weight leakage directly.

Rules that keep the numbers honest. The judge model never shares a tier with
any writer and is calibrated on a hand-labeled sample before its scores count.
Segmentation gets a deterministic baseline (TextTiling) beside the model call.
Retrieval misses are classified coverage versus vocabulary before prescribing
a fix. Agent-fleet evaluations carry completion accounting, since a partial
fleet result looks confident. Report a pair metric and a cluster metric for
resolution, because they can rank the same system differently.

## Evidence checked by eye

Never presented as results.

| Fixture | Shows |
|---|---|
| Tip becomes Ozma, Oz book 2 | aliasing, merge, supersession, time-scoped truth, at document 2 |
| Watson's wound, shoulder then leg | contradiction inside one author, no reconciling reading |
| The deerstalker probe | Doyle never wrote one; assembled pages cannot contain it, generated pages can |
| Helen at Troy, Homer vs Euripides | source disagreement rendered inline |

## What a run costs

Rates fetched 2026-08-27 and perishable. Per chunk the pipeline makes one
entity pass, one fact pass, and N cell calls, each re-sending the chunk text;
batching the cell calls is 2.3x on total input and 5x on the dominant part,
so it is built in from the start. Full four-corpus run, batched: $2.30 on the
cheapest model, $34 to $168 across the three mainline tiers, $335 at the top,
a 146-fold spread, which is why tier sensitivity gets measured rather than
assumed. The pilot is about $2.
Set the spending stop before every run; the prototype ran out of credit
mid-pass twice. Money is not the constraint; hours are.

## What the prototype already showed

The two-year personal deployment (about 1,000 distilled summaries over 20M
transcript tokens, a 25:1 ratio) is design rationale, never evidence, and no
personal detail from it enters the paper. Its sharpest finding: tracing 39
rolled-up claims to raw transcripts found all 8 defects in the synthesis layer
while all 31 leaf-level checks were clean, and an entailment gate is
structurally blind to this because a hardened sentence is still entailed by
its hedged source. A mutation study found 5 of 10 induced breakages produced
no signal at all. Twice, dated, the store held an answer and a session argued
for twenty turns without consulting it.

It also demonstrates the problems the fall measures. Its registry grew to
1,169 entity names, and its two entity systems produced 70 and 388 entities
with only 17 names in common; a false merge there inherited both fact sets,
and the inherited facts then looked like independent corroboration. Read-time
supersession is a paid-for decision, not taste: the prototype's automatic
supersession engine produced four distinct classes of confidently wrong
answers and was deleted on purpose. The fix was subtraction, and the
append-only ledger judged at read time is what replaced it.

The prototype's summaries were written by models that had seen the writer's
patterns, a contamination any mention of the archive must carry.

## The December mechanics

Ask Dr. Fang for an arXiv cs.CL endorsement now; first-time submitters cannot
post without one and an ISU address does not grant it. Repo public September 1,
which starts the six-month JOSS clock. Dataset DOI via Zenodo by November 10.
arXiv submission November 16, cs.CL, as a resource-and-experience paper,
avoiding November 23 to 27. On the CV it goes under preprints, with the dataset under research artifacts;
miscategorizing a preprint as a publication is the mistake committees notice. Deliberately not adopted, with
reasons recorded in `docs/references.md`: RDF reification (native in a
property graph whose edges carry properties; Hernández 2015's engine failures
are a warning about RDF stores, not this design) and CoALA's memory taxonomy
(a prose frame that does not map onto storage). The prepared answer to the Cyc
objection: symbolic AI failed on the authoring bottleneck, LLMs removed
exactly that bottleneck, and what becomes inspectable is the memory, not the
weights.

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
statistic. The LongMemEval loader must decide what counts as a document, one
session or the whole haystack, before it is written. The prototype also
retired one entity layer for being rebuilt nightly and consumed by nothing; an
entity index earns trust only after it is built from the ledger and wired into
a recall surface. Re-ingesting the personal archive is the eventual goal and
is settled: everything on the PC goes into the private PC database, local, no
gating.

IRB review comes before recruiting a single tester; a department email is
human-subjects research, and if testers might set it up for family, scope the
study to adults explicitly, since minors require parental permission and child
assent. Per-user API keys are the default, keeping the host out of the
accountability path. The symposium provides one 36 by 48 foamboard; lay it out
problem, evidence, artifact.

## Open

1. Endorsement email to Dr. Fang. The only item depending on another person.
2. Read Story Ribbons and Narrative World Model in full before writing.
3. Regenerate `data/clean/` from committed code; the old spike never met the
   contract and was deleted.
4. Verify the 8-hours-a-week assumption against one real week before trusting
   the calendar.
5. Rebuild `papers/MANIFEST.md`; it predates half the corpus.
6. The cells ablation is committed. Whether a second one fits is open; of
   the four remaining candidates (resolution, threshold, fact layer, refold),
   `docs/entity-resolution.md` argues resolution should take the slot because
   it has published reference numbers and cells do not.
