> **SUPERSEDED 2026-08-27 (later)** by `docs/27_requirements_and_testing.md`, which flips the
> requirements source from personal deployment to published literature, adds the asymmetric
> baseline strategy (Zep on its metric, GraphRAG on ours), and scopes to 70-100 hours.
> Kept for the record; do not build from it.

# Evaluation plan

**2026-08-27.** What can be measured, with what, and in what order. Selection is driven by
result-per-hour, because the feasibility review prices question authoring at 15–30 hours and
judge calibration at another 5–8 against a 70–100 hour budget.

---

## The positioning this has to serve

As of the 08-26 novelty reassessment (`docs/14`), both contributions named in `IT494_PLAN.md` are
occupied by published work. Proactive recall is taken by CogniFold (arXiv:2605.13438),
ProactAgent (arXiv:2604.20572) and ENPMR-Bench (arXiv:2605.27240); cold-start schema induction by
AutoSchemaKG (arXiv:2505.23628), SCOPE/SCION (arXiv:2607.21610) and EvoTaxo (arXiv:2603.19711).

So the evaluation is not decoration on a novelty claim. **It is the deliverable.** A competent,
reproducible study with real measurement and stated limitations is what the fall can actually
produce.

**The strategic point about datasets: a published benchmark gives comparison.** "We scored 0.71"
is weak; "0.71 where the published baseline is 0.64" is a result. A homegrown question set over
Oz can never do that.

---

## Core — do these

### 1. LitBank. The single highest result-per-hour item.

Hand-annotated entity, coreference, event and quotation labels over ~100 Project Gutenberg works.

- **Evaluates:** the entity-first pass, head-to-head against GraphRAG's chunk-first, on identical
  text
- **Method:** run both pipelines over the same LitBank documents; score extracted entities
  against gold (precision, recall, F1) and coreference against gold clusters
- **Why it wins:** no question authoring, no judge model, no kappa study, no hand labelling.
  Deterministic scoring against a published annotation, on Gutenberg text — the same family as
  the project corpus
- **Status: CONFIRMED 2026-08-27.** 100 works of English fiction, 1719-1922, all US public
  domain, all drawn from Project Gutenberg. 210,532 tokens. Four annotation layers: entities
  (six ACE categories), coreference (OntoNotes-style, singletons included), events (asserted
  realis), and **quotation attribution with speaker**. Repo: `dbamman/litbank`
- **Caveat that changes the design:** roughly **2,000 words are sampled per work, not whole
  books**. So this scores extraction on excerpts, not a full pipeline run over a novel. The
  head-to-head against chunk-first is still valid; the unit is smaller than a chapter

That one experiment produces a real number against a real baseline for roughly a day of work.
Nothing else on the list is close.

### 2. The free instruments — no dataset required

These fall out of running the pipeline at all:

| Instrument | Source | What it shows |
|---|---|---|
| Contract rejection rate, per stage per tier | rejection log | which tiers can hold which stages |
| Duplicate minting curve, nodes minted per unit | ingest | whether entity-first fixes the measured failure |
| Predicate sprawl, distinct predicates per unit | fact rows | whether supersession is silently missing |
| Quote gate pass rate | deterministic string check | fabrication rate, no judge needed |
| Token cost and latency per arm | run rows | the cost side of every comparison |
| Plot-vs-cell consistency | set comparison | invented events or missed threads, both directions |

The stage-wise sensitivity table comes entirely from these, and **nobody publishes it per-stage.**

### 3. NarrativeQA — only if the October block survives intact

QA over full Gutenberg books, questions already written. Runs the three injection arms — raw
top-k control, tree-routed, tree plus facts — against published baselines.

---

## Demonstration, not comparison

The project's own corpora produce no comparable numbers but produce evidence a reader can check
by eye. **Label these as demonstrations. They are not results.**

| Fixture | Corpus | Shows |
|---|---|---|
| **Tip → Ozma**, end of book 2 | Oz | Aliasing, entity merge, supersession and time-scoped truth in one case, at document 2 rather than document 14 |
| **Watson's wound** — shoulder in *A Study in Scarlet*, leg in *The Sign of the Four* | Holmes | Contradiction with no reconciling reading, inside a single author |
| **The deerstalker probe** | Holmes | See below |
| **Source disagreement rendered inline** | Greek | Helen reached Troy per Homer, never per Euripides |
| **OCR tax** | Chinese | Same volume, same translation, proofread vs OCR |
| **Translation tax** | Chinese | Machine translation vs Brewitt-Taylor, identical source |

### The contamination probe, as a two-arm experiment

The deerstalker is Sidney Paget's illustration, not Doyle's text. The calabash pipe is William
Gillette's stage prop. "Elementary, my dear Watson" is not in the canon.

- **Arm 1:** ask a model to describe Holmes with the chapter text in context — free generation,
  leakage possible
- **Arm 2:** compose the description from quoted `appearance.*` fact rows — **structurally cannot
  leak**, because no deerstalker fact row exists

Measure incidence in each. Binary, eyeball-checkable, isolates parametric leakage, costs almost
nothing.

### The two controls, and why Three Kingdoms carries both

Three Kingdoms is the only work present as Chinese original, human English translation
(proofread), human English translation (OCR), and — once produced — machine translation.

| Run | Isolates |
|---|---|
| Proofread human translation | baseline |
| OCR human translation | baseline + **OCR error** |
| Machine translation from Chinese | baseline + **translation error** |

That licenses a stated bound when the same method is applied to Water Margin, Journey to the West
and Dream of the Red Chamber, where no human English translation exists to check against.

Caveats to state with any result: Brewitt-Taylor is himself an imperfect century-old translator,
so what is measured is agreement with a competent human translation, not with truth; the Chinese
Gutenberg text may not be the edition he worked from; and Water Margin's 108 semantic nicknames
are a harder consistency problem than anything in Three Kingdoms, so the measured tax is a floor.

---

## Cut, with reasons

QuALITY, NovelQA, LoCoMo, LongMemEval, MemoryAgentBench, SCOPE. Each is defensible; seven
benchmarks in eighty hours is not.

**BooookScore (arXiv:2310.00785) and FABLES (arXiv:2404.01261) are cited rather than run** — they
already supply the context numbers: best-model faithfulness at 90.9%, and the strongest automated
fabrication-checker reaching only 58.2 F1 with the whole book in hand. That second number is the
reason the faithfulness metric is the least trustworthy one in this system, and it is worth
saying so rather than discovering it.

---

## The unresolved instrument

`Consult.used_ids` is the whole proactive-recall measurement, and **there is no sound way to
populate it.** Model self-report is unreliable. The defensible version is a paired counterfactual
— run the same question with and without the memory injected and diff the answers — which is what
ProactAgent does, and it doubles the cost of every measured query.

Decide which, and price it, before collection starts. The rate is meaningless without weeks of
data, so consult-logging has to be running long before the measurement is wanted.

---

## Order

1. **Verify LitBank.** Determines whether the cheapest experiment exists.
2. **ACL Anthology search** on interleaved-thread summarisation. Every novelty search so far has
   been arXiv-only, which is the wrong index for computational literary studies. This gates
   whether the design direction survives at all.
3. **Freeze the unit contract**, preprocess Oz books 1–2.
4. **Pilot across tiers on Oz book 1** — 24 units, roughly $3 total. Produces the sensitivity
   numbers and surfaces schema gaps by contact rather than by reasoning.
5. Freeze the rest of the schema against what the pilot found.

The realistic November 15 outcome is **one instrument, measured on one corpus.** That is a
workshop paper or an arXiv preprint supporting an application. It is not an ICLR submission, and
planning for one produces neither.
