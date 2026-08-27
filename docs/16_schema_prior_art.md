# Schema prior art, and what to take from it

Read against `docs/15_schema_and_architecture.md`. Sources are papers already in `papers/`,
read directly rather than recalled. Each section states what the source specifies, then what our
schema should do about it.

---

## Angles 2018, the property graph model

**What it specifies.** A property graph is a tuple `G = (N, E, ρ, λ, σ)`: nodes, edges, an
incidence function mapping each edge to a node pair, a labelling function over nodes and edges,
and a property function mapping node-or-edge plus property name to values.

Separately, and more usefully for us, a **schema** is `S = (TN, TE, β, δ)`:

- `TN` — node types
- `TE` — edge types, disjoint from `TN`
- `β` — which properties each node/edge type carries, and their datatypes
- **`δ` — which edge types are allowed between which pairs of node types**

**What we should take: δ.** Our schema has `kind` on nodes and a free predicate vocabulary, with
a note that "some predicates only apply to some kinds." Angles gives that the formal shape and
makes it enforceable. `parent_of` between two `person` nodes is valid; `parent_of` between a
`place` and a `thing` is not, and today nothing would catch it.

This is cheap to add and it catches a class of extraction error that no quote gate can see,
because a fabricated relation can still carry a genuine quote. Recommend adding a `δ` table to
the predicate registry: allowed `(subject_kind, predicate, object_kind)` triples, with violations
logged as rejections rather than silently stored.

---

## Rost et al. 2021, bitemporal property graphs

**What it specifies.** Two period domains, `VAL_TIME` and `TX_TIME`, each with `FROM` and `TO`
bounds. **Lower bound inclusive, upper bound exclusive**, written `[from, to)`, following SQL.
Periods are a type definition rather than a data type.

Critically, temporal attributes attach not only to vertices and edges but **to individual
properties**: `var1.prop1.TX_FROM` is a valid access path.

**What we should take, in two parts.**

*The interval convention.* `[from, to)` with the upper bound exclusive. This is free correctness
and it prevents the off-by-one that appears at every boundary when two intervals abut. Our
current schema says "validity intervals" without stating the convention, which is exactly how a
project ends up with two conventions.

*The property-level question, answered.* Rost puts validity on individual properties because
his vertices carry properties directly. Ours do not: our facts **are** the properties, so
fact-level validity already gives us property-level granularity. Worth recording that we
considered it and why we do not need it, rather than leaving it to be re-litigated.

---

## Vrandečić and Krötzsch 2014, Wikidata

**What it specifies.** Property-value pairs on items can carry subordinate property-value pairs
called **qualifiers**. Qualifiers do two jobs: they state contextual information such as validity
time, and they **encode ternary relations that the property-value model cannot express**. Their
example: "Meryl Streep played Margaret Thatcher in The Iron Lady" becomes `cast_member = Meryl
Streep` on the film, plus the qualifier `role = Margaret Thatcher`.

Wikidata also carries **ranks** — preferred, normal, deprecated — which let contradictory
statements coexist while marking which is current.

**What we should take.**

*Qualifiers are load-bearing, not decoration.* Our schema has a `qualifiers` field documented
only as "any timing the source states." That undersells it. N-ary relations are common in every
corpus here: Ozma rules Oz *as restored by Glinda*; Holmes is retained *by a client* *for a fee*;
Zhuge Liang serves Liu Bei *in the capacity of Chancellor*. Without qualifiers those become
either lost detail or invented predicates, and invented predicates are the sprawl that breaks
supersession.

*Ranks fill a real gap.* Our design says nothing is overwritten and supersession is computed at
read time from a later assertion. That works when the world changed. It does **not** work when a
fact is simply wrong — an extraction error has no later assertion to supersede it, and deleting
it violates append-only.

This is not hypothetical: the Ash-Catchum-aliased-to-Ursa error in the live archive was resolved
by appending an is-distinct-from assertion rather than editing. That is the same pattern, done ad
hoc. A `rank` field makes it explicit and queryable: `deprecated` means present, preserved,
and excluded from reads by default.

Recommend adding `rank: preferred | normal | deprecated` to the fact row, defaulting to `normal`.

---

## Rezazadeh et al. 2025, Collaborative Memory

**What it specifies.** Two-tier memory: private fragments visible only to the originating user,
and shared fragments. Each fragment carries **immutable provenance attributes** — contributing
agents, accessed resources, timestamps — to support *retrospective* permission checks. Read
policies project stored fragments into filtered views at query time; write policies decide
retention and sharing. Access is modelled as a **time-varying bipartite graph** over users,
agents and resources.

**What we should take: this is the answer to quality-pass item 1.** Our schema has no
multi-tenancy at all, and the product's stated end state is one user scaling to an organisation.

The important design property is that **permission is enforced at read time against current
policy, not stamped at write time**. That means revoking access retroactively hides everything
that depended on it, without rewriting stored fragments — which is the same read-time-resolution
discipline we already use for supersession and merges. It fits our model rather than fighting it.

Concretely: add immutable provenance to every derived record (who contributed it, which
resources it drew on, when), and make the storage port's read operations take a policy context
rather than returning everything. Single-tenant is then the degenerate case where the policy
admits all.

---

## Summary of changes to `docs/15`

| Change | Source | Why |
|---|---|---|
| Add `δ` — allowed `(subject_kind, predicate, object_kind)` triples | Angles 2018 | Catches fabricated relations that carry genuine quotes, which the quote gate cannot see |
| State the interval convention as `[from, to)`, upper exclusive | Rost 2021 | Free correctness at every boundary |
| Record that fact-level validity subsumes property-level | Rost 2021 | Stops the question being re-opened |
| Document qualifiers as carrying n-ary relations, not just timing | Wikidata 2014 | Prevents predicate sprawl from encoding roles as new predicates |
| Add `rank: preferred/normal/deprecated` to facts | Wikidata 2014 | Supersession handles "the world changed"; rank handles "we were wrong" |
| Add immutable provenance + read-time policy context to the port | Collaborative Memory 2025 | Multi-tenancy, with single-tenant as the degenerate case |

## Deliberately not adopted

**RDF reification schemes** (Hernandez et al. 2015, four schemes benchmarked over 57M Wikidata
quads). The question they answer — how to attach metadata to a triple — is native in a property
graph, where edges carry properties directly. Their finding that singleton properties broke four
of five engines is a warning about RDF stores, not about us.

**CoALA's four-way memory taxonomy** (working / episodic / semantic / procedural). A useful frame
for describing the system in prose, but it does not map onto storage: our units are episodic, our
facts and abstracts are semantic, and we have no procedural memory at all. Adopting it as schema
would add a field that never varies usefully.
