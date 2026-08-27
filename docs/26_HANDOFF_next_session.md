# Handoff: mission for the next session

**Written 2026-08-27 at the end of a very long session.** Read this first. It is the only
document that reflects where things actually landed, and several documents in this repo are
wrong in ways recorded below.

---

## Mission

1. Read this document and `25_paper_argument.md`, then audit the rest of `docs/` for accuracy.
2. **Lock in a plan of attack** — the current plan documents predate the findings below.
3. **Find and patch holes** in the understanding recorded here.
4. **Rework the docs** to reflect the actual plan rather than the plan as of yesterday morning.
5. **Archive vestigial material** — `docs/` has grown to 26 files, many superseded, and `papers/`
   holds 92 PDFs of varying relevance.
6. Leave the repo clean and accurate.

---

## Where we ended up

### The claim that survived

Seven candidate contributions were searched adversarially and **all seven were occupied**
(`docs/14`, and the session index). What is left standing is narrower and more specific:

> **Pre-determined, unit-level entity salience driving extraction, versus per-chunk extraction.**

Both published baselines extract chunk-first:

| System | Extraction order | Verified how |
|---|---|---|
| GraphRAG | chunks first; entities pulled from each text unit **separately** | its indexing documentation |
| Zep | per-episode, plus a four-message lookback, then resolve against the graph | its paper |
| **This project** | scan the unit, establish the cast, condition everything downstream on it | the thing under test |

That claim has a mechanism, a measured consequence (duplicate minting rate, entity F1), and gold
data to score against (LitBank). It is the most solid thing produced by the session.

**Secondary and unverified: covering versus partition.** Every hierarchical memory system found
partitions — HERCULES uses recursive k-means, TraceMem clusters traces into threads, GraphRAG
uses Leiden, Zep uses label propagation. This design places one unit in N threads at full weight.
Not searched properly. Treat as a hypothesis.

### The framing, and it is load-bearing

*"Here is our backend and we measured it"* is a system paper and dies on prior art.
*"Here are measured tradeoffs in this design space, demonstrated on a working backend"* is an
empirical study and survives.

The difference shows up in the first paragraph. Decide before writing one.

### Evaluation shape

- **On their turf:** LongMemEval. Public, conversational, has knowledge-update bands
  (= supersession), and Zep published numbers on it — 63.8% with gpt-4o-mini and 71.2% with
  gpt-4o, against full-context baselines of 55.4% and 60.2%. **DMR is near-useless** as a
  discriminator and Zep's own paper says so (94.8% vs 94.4% full-context). GraphRAG's evaluation
  is LLM-judged on self-generated questions and is hard to reproduce fairly.
- **On gold data:** LitBank. Confirmed — 100 public-domain Gutenberg works, 210,532 tokens,
  entities / coreference / events / quotation attribution. **~2,000 words sampled per work, not
  whole books.**
- **On the literary corpora:** the four in `data/raw/`, as testbed with built-in controls.
- **This session's own transcript:** a worked example for the covering claim — ten interleaved,
  non-contiguous threads with cross-thread supersession. **A figure, not a result.**

---

## Errors made this session. Do not repeat them.

**1. Claimed Zep/Graphiti has no community summarisation. FALSE.** Read the repository README,
saw no mention, called it "verified." Zep's paper defines a community subgraph with high-level
summarisations and incremental label-propagation maintenance. **A README is not the paper.**
Corrected in `docs/19`, `docs/25` and the index, but the correction reshaped the whole gap
argument.

**2. Invented a number.** `docs/25` says "the best single system covers five or six of nine."
**That was never computed.** The coverage matrix was drawn with empty cells and a score asserted.
**This still needs fixing** — either fill the matrix honestly or delete the claim.

**3. Overstated a measurement.** Called the assembled-versus-RAG gap "the assistant's fabrication
rate." It is the fabrication rate of **one rendering path on one corpus**. Narrow it.

**4. Read "no records found" as absence, twice.** Reported the Chinese-language originals and
Thompson's Oz books as unavailable; both were on Project Gutenberg the whole time, behind bad
multi-term queries. Nearly did it a third time when arXiv returned 503 mid-session and four
searches came back empty — caught only by running a control query that had to return results.

### Method rules that came out of those

- **Run a control query before trusting an empty result set.**
- **A README, a repo, or a product page is not the paper.**
- **Mark abstract-only reads as abstract-only.** All 26 one-pagers added this session say so.
- **Absence claims are the weakest thing that can be asserted.** Both project contributions were
  absence claims and both were false.

---

## Unverified things the plan currently rests on

| Assumption | Consequence if false |
|---|---|
| Graphiti ingests **document** corpora, not just conversation episodes | The Zep-as-baseline comparison needs a different corpus |
| Graphiti accepts **pre-extracted** entities | The spring product must build its own graph layer |
| Covering-versus-partition is unoccupied | Secondary claim dies; primary claim survives |
| No literary memory benchmark exists | The corpus-as-resource angle weakens |
| No published requirements analysis for assistant memory | Move 1 of the argument weakens |
| Design-space / empirical studies place in this field | The framing needs a different venue |
| Angles venue and year; Rost venue and year; Wikidata ranks page; full Hernández citation | Four citations are not usable |

**The first two are one evening's work** — feed Graphiti three Oz chapters and see what happens.
Do them before committing to the baseline framing.

---

## Document inventory

**Current and load-bearing:** `14` (novelty), `16` (schema prior art + references), `17` (schema),
`18` (ingestion), `19` (retrieval/delivery, carries a correction banner), `20` (evaluation),
`21` (cost — perishable, rates fetched 2026-08-27), `22` (Project 1 fall), `23` (Project 2
spring), `24` (unit contract, **FROZEN**), `25` (paper argument, carries a correction banner and
**one known false number**), `README_SESSION_2026-08-27`.

**Superseded, banners in place:** `06`, `08`, `09`, `10`, `11`, `12`, `15`.

**Predates everything and needs triage:** `00` through `07`, `13`, plus `impl/` (six
implementation plans written before the design work) and `narrative_sections/`. `13`
(feasibility review) is the exception — its conclusions held up all session and it should stay.

**Also outstanding:** the master PDF (`scripts/build_package.py`) has not been rebuilt and would
currently ship both versions of the data model.

---

## Late correction: the requirements source was flipped

An earlier draft derived requirements from the personal deployment. That is a wish list with a
case study attached, and it fails on two counts: no citable source, and it drags personal detail
into a paper.

**`docs/27_requirements_and_testing.md` flips it.** Seven requirements, each sourced to a
published paper stating the problem is unsolved. No personal detail anywhere. The deployment
corroborates in one sentence and does not authorise. Consequence: that section is **motivation,
not contribution** - which is what it always was.

`docs/27` also carries the testing plan, the asymmetric baseline strategy, and the scope cut, and
supersedes `docs/20`.

## The artifact that does not exist yet

**Superseded by the flip above.** The requirements now exist, in `docs/27`, sourced to
literature. What remains outstanding is smaller: confirming each citation resolves to the claim
attributed to it, since several were quoted from one-pagers rather than from full papers.

---

## State of the corpora

Four corpora, 81 files, ~6.8M words, all public domain, in `data/raw/` with `SOURCES.md`,
`WANTLIST.md` and `USAGE.md`. Preprocessing has **not** started; `24_unit_contract.md` is frozen
and specifies eight convention handlers and three acceptance gates. The first milestone is Oz
books 1 and 2 — book 2 contains the Tip→Ozma fixture and has the worst chapter structure, so it
is both the demonstration and the hard case.

`papers/` holds 92 PDFs and `summaries/one-pagers/` holds 93 one-pagers. The 26 added this
session are abstract-only reads and say so.
