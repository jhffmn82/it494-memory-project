> **SUPERSEDED 2026-08-28** by `03_design.md`, section 3.
> Kept for the record; do not build from it. Index: `docs/README.md`.

# Ingestion pipeline

**2026-08-27.** The design worked out in session on 08-26/27. Records the *what* and *why*;
implementation is the student's, per the authorship rule. Schema references point at
`docs/17_schema_current.md`.

---

## The two axes

The design records on two axes over the same source text, and neither substitutes for the other.

**Plot axis** — summaries per unit, on work nodes. Complete by construction: every unit gets one,
no threshold, no entity judgment involved.

**Entity axis** — per-node narrative cells. Sparse by design: only above-threshold nodes, and
only for units they appear in.

Each covers the other's blind spot. The plot axis loses the individual thread — a character in
twelve chapters is scattered across twelve summaries, none of which is about them. The entity
axis loses the causal frame — Ozma's thread says she was Tip and became ruler; it does not say
*why*, because the why is Mombi's enchantment and Jinjur's revolt, which are facts about other
things.

Formally the atom is the **cell**, `(unit × node)`. Plot summaries are the row marginals; entity
narratives are the column marginals. Two complementary views over one matrix.

### Threads are a covering, not a partition

GraphRAG partitions by graph topology, RAPTOR by embedding cluster, a folder tree by topic path.
All assign each unit to exactly one place.

Threads do not. A chapter belongs to Tip's thread *and* Jack Pumpkinhead's *and* Mombi's,
simultaneously, at full weight in each. The same text is covered N times from N vantage points.

This matters beyond literature. Measured on the live archive: leaves mentioning IT 494 sit in
**six different era folders**, including `health/justin-trt`. The routing is not wrong — that
leaf genuinely belongs in health — but the thread is orthogonal to the hierarchy, so no
assignment of documents to folders can represent it. That is a structural limit, not a curation
failure.

Consequence: **a thread index is a second index over the same leaves, not a reorganisation.**
The tree stays. Nothing is re-filed.

---

## Pipeline stages

### 0. Preprocessing (separate; see `docs/19` and the notebook)

Raw text to normalised `Unit` records. Per-corpus handlers, one output contract. Deliberately
outside this pipeline so its heterogeneity is absorbed once.

### 1. High-level pass — identify topics and major entities

One call per unit. Returns the cast: entities and topics present, with a salience signal.

**Entity-first, not chunk-first.** Verified against the GraphRAG documentation: its pipeline
composes text units first (Phase 1, ~1200 tokens) and extracts entities from each text unit
*separately* (Phase 3). There is no document-level entity pass.

That ordering is where duplicate minting comes from. Chunk 3 sees "Tip," chunk 9 sees "the boy,"
chunk 15 sees "Tippetarius" — three independent extractions with no shared context, reconciled
afterward if at all. The live prototype measured the consequence: a registry that grew to ~1,169
names against a 400-name prompt cap, with active duplicate minting.

A chapter-level cast list passed into each downstream call fixes it before it happens. The same
pass does three jobs at once: de-duplication, cross-chunk coreference resolution, and
**determining which cells exist** — which is what makes the sparse matrix tractable rather than
requiring every entity against every unit.

### 2. Dedup against the existing registry

Resolve the cast against known nodes and aliases. **This is on the critical path and it is the
step the prototype already failed.**

Once the registry exceeds what fits in a prompt, this stops being a prompt and becomes
retrieval-then-prompt: embed the mention, pull top-k candidates from the node store, resolve
against those few.

**Topic dedup is harder than person dedup.** A person has a name; a topic has whatever
description the speaker reached for — "IT 494 project," "the directed project," "the grad
project." Person aliases converge; topic aliases proliferate, because each mention invents its
own label.

**Topic granularity has no natural boundary**, and the live archive already proves it: the
hand-curated boundary rules in `eras/directory.md` exist because automatic topic boundaries
drifted and had to be adjudicated. Expect the same here — a curated layer over the induced one.

### 3. Fact extraction

Dated S-P-O rows with verbatim quotes and unit pointers, validated against the fact contract and
the δ table. Rejections logged.

Order matters: **dedup precedes facts**, or facts bind to duplicate nodes.

### 4. Narrative cells

One cell per above-threshold node per unit. **The dominant cost, and the batching decision lives
here** — emit all N cells for a unit in one call rather than N calls, or the unit text is re-sent
N times. See `docs/21`.

### 5. Maintenance — abstracts refold

An abstract is a fold over its node's cells, so `children_hash` says exactly when it is stale.
Refold only nodes whose cells changed: **O(nodes touched)**, not O(all nodes). That is the
difference between an affordable nightly pass and an unaffordable one.

Supersession and merges also resolve here, at read time rather than by rewriting rows.

---

## The threshold

**All nodes enter the fact layer. Only above-threshold nodes get narrative cells.**

That places the threshold between a cheap layer and an expensive one rather than between having
something and having nothing.

### Three tiers, matching wiki practice

Confirmed against the Naruto and Harry Potter wikis via their MediaWiki APIs:

| Tier | On a wiki page | Scope | Cost |
|---|---|---|---|
| Facts | infobox (`born`, `died`, `blood`, `alias`) | every node | cheap |
| Abstract | lead paragraph; `Background`, `Personality`, `Appearance` | every node | O(nodes) |
| Cells | `Biography` → per-year → named events; `Part I` / `Part II` → arcs | above threshold | O(nodes × units) |

Scabbers pre-reveal gets facts and a paragraph — Ron's pet rat, unusually long-lived — and no
biography, because he isn't doing anything. Post-reveal, Pettigrew has a full segmented one.

**A search therefore never returns null.** The abstract is the floor. Below-threshold nodes
degrade gracefully instead of disappearing.

**And nothing is lost when a node falls below threshold**, because the plot axis records that
unit regardless. What is missing is the entity-indexed *access path*, not the content — which
makes it measurable rather than silent: ask the same question against each axis and the
difference is what the entity layer buys.

### What the threshold must not be

Salience-by-action would demote exactly the entities that carry an argument. Running step 1 over
this session's own transcript, Tip/Ozma and Scabbers/Pettigrew are the most-referenced concrete
examples in it and they never act — they are cited, not participants. They belong in the fact
layer and inside the design thread's narrative, not in threads of their own.

**Major/minor is scoped per corpus, not a property of the node.** Tip is major in Oz and minor in
a chat archive. Same node, different salience. This falls out of the keying for free, since cells
are keyed by (node, unit) and units belong to corpora.

### Promotion

Candidates, and they are not equivalent: cross-unit recurrence; within-unit salience; retroactive
promotion via a `same_as` merge; on-demand when a query targets the node.

**Record "considered, below threshold" as distinct from "never considered."** The two are
indistinguishable later otherwise. The live archive already makes this distinction —
`leafed` versus `registered_no_leaf` versus `covered_by_nothing`.

**Retroactive promotion is re-narration, not backfill.** A wiki's Pettigrew biography covers
1981–1993 as "hiding as a rat," a framing unavailable to anyone reading those chapters at the
time. So cells generated retroactively are written from an epistemic position the source did not
have — a second-order supersession where both accounts are valid from different vantage points.

---

## Free consistency gate

The plot-axis summary and the entity cells are **independent summaries over identical text**. If
the plot summary carries an event that no cell mentions, either it was invented or step 1 missed
a thread. Set comparison, no ground truth, no judge model, catches both directions.

---

## Model tier per stage

The intuition that higher abstraction deserves higher tier is **half right**, and the wrong half
is expensive.

| Stage | Volume | Difficulty | Errors | Tier |
|---|---|---|---|---|
| Entity spotting | 1/unit | easy — NER is solved | local | cheap |
| **Coreference / alias resolution** | per ambiguous mention | **hard** | **propagate** | **high** |
| Fact extraction | 1/unit | medium | local, quote-gated | mid |
| Cell generation | **N/unit, dominates cost** | medium | recoverable | cheap–mid |
| Abstract refold | 1/node when stale | high | recoverable | high |
| Judge | low | high | n/a | high, and never the writer's tier |

Coreference sits at the bottom of the stack and is the one sub-task small models genuinely fail.

**The rule is not "spend more at higher abstraction." It is: spend where errors propagate,
economise where they are recoverable.** A mediocre abstract costs one call to regenerate. A
corrupted entity registry costs a re-ingest.

The live example: the archive currently cannot distinguish Dr. Xing Fang from Bloodfang the clan.
No amount of frontier-model summarisation fixes that — a top-tier abstract over a merged node
just writes a confident paragraph about a hybrid that does not exist.

Both expensive categories are low-volume, so this is affordable. The cost driver is cell
generation, which is also the layer where a bad output is one cheap regeneration away.

---

## Known risks, carried forward

- **Step 2 is the critical path** and the prototype already failed it at scale.
- **Predicate sprawl** breaks supersession silently: `is_a` vs `species` vs `form` never collide.
  Count distinct predicates per unit; linear growth means the contract needs a controlled
  vocabulary.
- **Duplicate minting** — count nodes minted per unit. A rising line is the failure.
- **Contract rejection on cheap tiers** is a format failure, not a comprehension failure, and has
  a different remedy (grammar-constrained decoding). Measure them separately.
