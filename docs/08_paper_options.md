# Is there a paper, and what is it?

**2026-08-28.** Written after nine novelty claims were searched and all nine came back occupied.
This document answers the question that follows: with no novelty claim, is there an honest paper
here at all?

**Short answer: one, and it is a spring project.** Five candidate paper shapes were searched
adversarially. Four are occupied or do not fit the hours. The fifth has genuine daylight, in a
place nobody was looking.

Every verdict below carries its evidence. Nothing here is asserted without a search, because the
absence claims that were asserted without one are what cost this project nine claims and, on
08-28, a tenth (the corpora were described in this repo as "occupied by nobody"; they are not).

---

## The five shapes, and what happened to each

### 1. Stage-wise model-tier sensitivity. OCCUPIED.

Which pipeline stages need a frontier model is a named subfield with accepted papers: LLMSelector
(ICML 2025), SCOPE (KDD 2026), Schnabel et al. (WWW 2025). *Asymmetric Capacity Allocation*
(arXiv:2608.21345) already claims the "first stage-wise model size study" flag and reaches the
operationally identical conclusion, that capacity should not be allocated uniformly.

The format-versus-comprehension split is occupied three times over, including by
`papers/tam2024-format-restrictions.pdf`, already on disk. And the 146-fold cost spread is a
liability rather than a hook: FrugalGPT opened with a two-orders-of-magnitude price spread in 2023,
and this project's own rates are perishable and two months stale.

**What survives:** tier-resolved duplicate-node-minting curves on long-form narrative. CORE-KG
measured that metric against component presence; nobody measured it against model tier. That is a
table in an engineering report, not a paper.

### 2. The corpus as a resource paper. PARTIALLY OCCUPIED, and thin.

- **GraphRAG-Bench** (arXiv:2506.05690) curated Project Gutenberg novels "prioritizing lesser-known
  works to minimize overlap with pretraining data," released for evaluating graph construction end
  to end. Gutenberg curation, contamination control and KG scope, already shipped.
- **AffilKG** (LREC 2026, arXiv:2505.10798) pairs complete book scans and their OCR text with
  labelled knowledge graphs, with a companion paper on OCR error propagating into graph analyses.
  That is the OCR-tax idea, published, at the venue class this paper would target.
- **STAGE** (arXiv:2601.08510): 151 bilingual screenplays on a provenance-linked narrative
  backbone, with gold annotation this project does not have.
- **CoSER** (ICML 2025): 771 books, alias-to-canonical character mappings.
- **SPGC** (*Entropy* 22(1):126, 2020) and **StonyBook**: cleaned Gutenberg as a resource
  contribution, at roughly 600 times this scale.

What remains is a *composition* of individually occupied parts. "Novel combination of occupied
components" is the argument that killed claims one through nine.

**What survives, and it is worth doing anyway:** a DOI'd artifact release. Roughly 15 hours, no
novelty claim to shoot down, citable in December. And the cheapest real measurement available is
the OCR tax on Three Kingdoms, where proofread and OCR versions of identical content are already on
disk: one pipeline, two runs, one delta.

### 3. Book-scale replication of the cast-conditioning ablation. DO NOT PURSUE.

Four independent killers:

- **The instrument cannot measure the variable.** BOOKCOREF annotates only character coreference:
  no relations, no non-character entities. iText2KG's ablation metric is human-judged triplet
  precision. Swapping the outcome measure is not a replication.
- **The measurable half is predictable.** CORE-KG already shows removing coreference costs +28.25%
  node duplication; LINK-KG shows 27.0 to 10.6 and 36.0 to 17.8. Extrapolating a twice-published
  monotone trend to longer input is not a finding.
- **The corpus is maximally contaminated.** BOOKCOREF's three gold books are *Pride and Prejudice*,
  *Animal Farm* and *Siddhartha*. The model knows the cast before it sees chunk one, so a null is
  uninterpretable and a positive is confounded.
- **It does not fit.** 72 to 113 hours for the cheap half alone, against a 70-hour budget, on an
  unbuilt pipeline. The alignment layer between emitted entity strings and annotated mention spans
  is itself an entity-resolution system, so you must solve the problem to measure it.

Also: **SLIDE** (arXiv:2503.17952) already varies extraction context on a 160,000-token novel, and
**HAKG** (ICSP 2026) already reports global-prior-beats-local at full-book scale. HAKG is
abstract-only and is the single most likely scoop; read it in full before revisiting this.

Every negative-results venue for 2026 has closed. Insights at EMNLP 2026 shut in June.

### 4. Deployed-system measurement by fault injection. THE FRAMING IS OCCUPIED.

- **AgentChaos** (ASE 2026, arXiv:2608.06790), **AgentChaosBench** (arXiv:2608.14680), and TU
  Delft's observability work all do fault injection on LLM agent systems.
- **SuperLocalMemory** (arXiv:2608.08253) ran eleven fault-injection scenarios against a memory
  system's own invariants, 200 repetitions each, one month ago.
- **When Errors Become Narratives** (arXiv:2606.14589) is a single personal-assistant runtime over
  eight weeks reporting that roughly **70% of silent failures were caught by human observation, not
  by tests or health checks.** That is this project's finding, in print.
- The hedge-stripping mechanism is published as **Manufactured Confidence** (arXiv:2606.29279):
  consolidation rewrites hedged remarks into flat dated assertions.

**And the n is too small.** 5 of 10 injected faults invisible carries a 95% interval of roughly
19% to 81%. Comparable papers used 250 executions, 65 configurations, or 200 repetitions per
scenario.

---

## 5. The one that survives: provenance integrity

**The contribution is not fault injection. It is two measured provenance failures and the link
between them.**

> **Corroboration inflation launders a silent over-merge into apparent authority.**

**A. Corroboration inflation, measured on a live corpus.** 194 claims carried more than one
recorded source; **77 of them, 40%, were inflated** because a roll-up summary echoing its own child
counted as an independent witness. Consequence: the best-supported-*looking* claims were the
most-summarised, not the most-observed.

The *fix* is published: **Isnad-Rijal** (arXiv:2607.24117, July 2026) implements independent-chain
corroboration for exactly this. **The field measurement is not.** Nobody has reported the rate on a
real deployment, tied causally to a specific downstream defect.

**B. Silent over-merging.** Every check in the system asked whether a claim *resolves*; none asked
whether two entities that collapsed into one *should have*. A search of the LLM entity-resolution
literature returns four papers, all about performing resolution better; none treats over-merging as
a failure mode with a structurally silent validation surface.

Do not oversell B alone. Classical record linkage has known over-merging for decades as precision
loss, and a reviewer will say so. The defensible claim is narrower and is the **A-to-B linkage**:
in LLM-built registries the validation surface only tests resolvability, so over-merges are silent,
and the echo mechanism then manufactures their authority.

**Supporting measurements, all already collected:** 33.4% of stored facts trace to summaries of
summaries rather than to leaves or primary documents; of induced entities, 84% typed `unknown`, 56%
appearing in one fact or none, and 37% carrying names that read as a claim rather than a thing.

### What it would cost, and what must be fixed first

**115 to 140 hours.** That is a spring project. It does not fit the fall's 70.

| Work | Hours |
|---|---|
| Read the threat papers properly, rewrite positioning | 20-25 |
| Enlarge fault injection to 40-60 defects with per-class rates and intervals | 15-20 |
| Grow the 39-claim layer-seam audit to 150-200 with a protocol and a second rater | 25-30 |
| Formalise independent-chain counting against Isnad-Rijal | 10 |
| Turn the false-merge case into a systematic sweep with a detection method | 15 |
| Writing, threats to validity, synthetic replica and artifact package | 30-40 |

**Two threats that must be answered, not avoided:**

- **RAPTOR (ICLR 2024) explicitly reports that hallucinations did not propagate to higher layers**,
  sampled over 150 nodes across 40 stories. The 39-claim result here contradicts a published ICLR
  finding on a smaller sample. This is why the audit has to reach 150-200 claims with a second
  rater, and it is the least negotiable line in the table above.
- **The entailment argument is wrong as currently worded.** "X may be true" does not entail "X is
  true." The real claim is empirical: NLI and LLM-judge checkers are insensitive to epistemic
  modality. State it that way or it dies in one sentence.

**Kill criteria. Two hours of reading that could save 140.** Read **arXiv:2607.24117**
(Isnad-Rijal) and **arXiv:2606.14589** (When Errors Become Narratives) in full before spending
anything else. If Isnad-Rijal already measures inflation on a real corpus, the best asset is gone
and the answer is no. If 2606.14589 covers the memory plane's synthesis layer rather than only the
runtime, the case weakens further. Both are currently snippet or abstract-level reads.

**Privacy is not a blocker.** The ACM SIGSOFT Empirical Standards permit deviation from data
sharing when data is too sensitive. Ship the injection harness, the check code, a redacted schema,
per-fault detection logs, the annotation protocol, and a **synthetic replica corpus**. Do not skip
the replica; it is what reviewers actually want.

**Venue:** CAIN or ICSE-SEIP, an experience or industry track, not a research track. The model is
*Seven Failure Points When Engineering a RAG System* (CAIN 2024).

---

## The fall plan that actually fits

No research paper this fall. The following produces citable output inside 70 hours.

1. **This week: ask Dr. Fang for an arXiv endorsement in cs.CL.** First-time submitters require it,
   and an institutional email alone does not grant it. One endorser suffices and arXiv explicitly
   recommends the thesis advisor. This is the longest human-dependency in the plan and it blocks
   everything downstream.
2. **September 1: make the repository public.** Free, and it starts the six-month public-history
   clock that JOSS requires, making that route viable from roughly March 2027.
3. **Build the backend.** It is the degree project, and it needs no novelty claim.
4. **November 10: publish the DOI'd artifact.** Zenodo mints on publish with no review gate;
   Hugging Face has a one-click DOI. Mint it only when final, because the repo then locks.
5. **November 16: submit to arXiv**, primary category cs.CL, framed as a resource and experience
   paper. **Not** as a survey or position paper: arXiv CS has required prior peer-reviewed
   acceptance for those since 2025-10-31. Announcement runs one to four days with a long tail, and
   arXiv defers around Thanksgiving, so avoid November 23 to 27.

**ARR's October 12 cycle was considered and rejected.** October 12 falls inside the dead window of
September 28 to October 18, so hitting it means finishing a paper by September 27, in direct
competition with preprocessing. Take the February cycle in spring, with the provenance paper, which
is when it would actually exist.

**On how much a preprint helps, stated honestly:** a solo, non-refereed preprint from an applicant
with no publication record is weak evidence on its own. Its value is instrumental. It gives the
research letter writer something specific to describe, and it demonstrates the ability to finish
and ship a paper-shaped object. List it under **Preprints**, never under Publications, and list the
dataset under Research Artifacts. Miscategorising a preprint as a publication is the most common CV
error and committees notice it.
