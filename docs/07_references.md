# Schema prior art, and what to take from it

Originally read against the superseded schema draft, now `archive/15_schema_and_architecture.md`. The changes below are all incorporated in `03_design.md`. Sources are papers already in `papers/`,
read directly rather than recalled. Each section states what the source specifies, then what our
schema should do about it.

---

## Angles 2018, the property graph model

**What it specifies.** A property graph is a tuple `G = (N, E, ρ, λ, σ)`: nodes, edges, an
incidence function mapping each edge to a node pair, a labelling function over nodes and edges,
and a property function mapping node-or-edge plus property name to values.

Separately, and more usefully for us, a **schema** is `S = (TN, TE, β, δ)`:

- `TN`, node types
- `TE`, edge types, disjoint from `TN`
- `β`, which properties each node/edge type carries, and their datatypes
- **`δ`, which edge types are allowed between which pairs of node types**

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

Wikidata also carries **ranks**, preferred, normal, deprecated, which let contradictory
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
fact is simply wrong, an extraction error has no later assertion to supersede it, and deleting
it violates append-only.

This is not hypothetical: the Ash-Catchum-aliased-to-Ursa error in the live archive was resolved
by appending an is-distinct-from assertion rather than editing. That is the same pattern, done ad
hoc. A `rank` field makes it explicit and queryable: `deprecated` means present, preserved,
and excluded from reads by default.

Recommend adding `rank: preferred | normal | deprecated` to the fact row, defaulting to `normal`.

---

## Rezazadeh et al. 2025, Collaborative Memory

**What it specifies.** Two-tier memory: private fragments visible only to the originating user,
and shared fragments. Each fragment carries **immutable provenance attributes**, contributing
agents, accessed resources, timestamps, to support *retrospective* permission checks. Read
policies project stored fragments into filtered views at query time; write policies decide
retention and sharing. Access is modelled as a **time-varying bipartite graph** over users,
agents and resources.

**What we should take: this is the answer to quality-pass item 1.** Our schema has no
multi-tenancy at all, and the product's stated end state is one user scaling to an organisation.

The important design property is that **permission is enforced at read time against current
policy, not stamped at write time**. That means revoking access retroactively hides everything
that depended on it, without rewriting stored fragments, which is the same read-time-resolution
discipline we already use for supersession and merges. It fits our model rather than fighting it.

Concretely: add immutable provenance to every derived record (who contributed it, which
resources it drew on, when), and make the storage port's read operations take a policy context
rather than returning everything. Single-tenant is then the degenerate case where the policy
admits all.

---

## Summary of schema changes these sources drove

| Change | Source | Why |
|---|---|---|
| Add `δ`, allowed `(subject_kind, predicate, object_kind)` triples | Angles 2018 | Catches fabricated relations that carry genuine quotes, which the quote gate cannot see |
| State the interval convention as `[from, to)`, upper exclusive | Rost 2021 | Free correctness at every boundary |
| Record that fact-level validity subsumes property-level | Rost 2021 | Stops the question being re-opened |
| Document qualifiers as carrying n-ary relations, not just timing | Wikidata 2014 | Prevents predicate sprawl from encoding roles as new predicates |
| Add `rank: preferred/normal/deprecated` to facts | Wikidata 2014 | Supersession handles "the world changed"; rank handles "we were wrong" |
| Add immutable provenance + read-time policy context to the port | Collaborative Memory 2025 | Multi-tenancy, with single-tenant as the degenerate case |

## Deliberately not adopted

**RDF reification schemes** (Hernandez et al. 2015, four schemes benchmarked over 57M Wikidata
quads). The question they answer, how to attach metadata to a triple, is native in a property
graph, where edges carry properties directly. Their finding that singleton properties broke four
of five engines is a warning about RDF stores, not about us.

**CoALA's four-way memory taxonomy** (working / episodic / semantic / procedural). A useful frame
for describing the system in prose, but it does not map onto storage: our units are episodic, our
facts and abstracts are semantic, and we have no procedural memory at all. Adopting it as schema
would add a field that never varies usefully.

---

## References

Bibliographic details extracted from the PDFs in `papers/`, not recalled.

**All four items previously marked `[verify]` were resolved on 2026-08-28.** Two were correct and
needed only completion; two were materially wrong. Nothing in this file is now uncitable. The
resolution method is recorded with each entry.

**Angles, Renzo. "The Property Graph Database Model."**
In *Proceedings of the 12th Alberto Mendelzon International Workshop on Foundations of Data
Management (AMW 2018)*, Cali, Colombia, May 21-25, 2018, eds. Dan Olteanu and Barbara Poblete.
CEUR Workshop Proceedings, Vol. 2100, paper 26. http://ceur-ws.org/Vol-2100/paper26.pdf

Single author, not "et al." The paper is unpaginated and has no DOI; those fields are legitimately
absent rather than unconfirmed. **Venue confirmed 2026-08-28** three ways: the local PDF is
byte-identical to the CEUR-WS copy (both 680,900 bytes, matching SHA1), the CEUR-WS Vol-2100 index
lists it, and Rost's own reference list cites it the same way.
Local: `papers/angles2018-property-graph-model.pdf`.

Do not confuse this with `papers/angles2017-graph-query-foundations.pdf`, a different six-author
ACM Computing Surveys paper that is not cited here.

- *Property graph data structure*, **Definition 1**: `G = (N, E, ρ, λ, σ)`
- *Schema, including δ*, **Definition 2**: `S = (TN, TE, β, δ)`, where δ is "a partial function
  that defines the edge types allowed between a given pair of node types"

**Rost, Christopher; Fritzsche, Philip; Schons, Lucas; Zimmer, Maximilian; Gawlick, Dieter;
Rahm, Erhard. "Bitemporal Property Graphs to Organize Evolving Systems."**
Subtitle: "Towards the development of a graph model, database, and query language to represent,
store, and query bitemporal graphs." University of Leipzig / ScaDS.AI Dresden-Leipzig / Oracle.
21 pages. **arXiv preprint arXiv:2111.13499 [cs.DB], 26 November 2021.**
DOI: 10.48550/arXiv.2111.13499. https://arxiv.org/abs/2111.13499

**Resolved 2026-08-28: there is no venue.** The document's LNCS-style layout is misleading. arXiv
lists no journal reference, DBLP carries it only under CoRR as an informal publication, and the
authors' own group page labels it a University of Leipzig technical report. Cite it as a preprint
and technical report; do not assign it a workshop or conference.
Local: `papers/rost2021-bitemporal-property-graphs.pdf`.

- *Period identifiers and interval convention*, **~p. 6–7**: `VAL_TIME` / `TX_TIME` domains,
  bounds `VAL_FROM`/`VAL_TO` and `TX_FROM`/`TX_TO`, textual form `[{from},{to})`, lower bound
  inclusive and upper exclusive, "like in SQL, not a data type but a type definition"
- *Property-level temporal attributes*, same section: `var1.prop1.TX_FROM` as a valid access path

**Vrandečić, Denny; Krötzsch, Markus. "Wikidata: A Free Collaborative Knowledgebase."**
*Communications of the ACM* **57**(10), October 2014, pp. 78–85. **DOI: 10.1145/2629489**.
Fully verified from the document. Local: `papers/vrandecic2014-wikidata.pdf`.

- *Qualifiers*, **p. 82**: the subordinate property-value pair model, including the Meryl Streep,
  Margaret Thatcher and *The Iron Lady* ternary-relation example
- *Statement marking*, **p. 83**: contributors may optionally mark statements as "preferred" or
  "deprecated"

**Correction, 2026-08-28: the rank vocabulary is not in this paper.** Two independent extractors
over all nine pages find zero occurrences of "rank" and no "normal" value; only "preferred" (once)
and "deprecated" (twice) appear, both on p. 83. Controls returned results on the same pass
("qualifier" 9 hits, "Meryl Streep" 2), so the absence is real. For the three-value vocabulary,
cite the Wikidata help page below instead.

**Rezazadeh, Alireza; Li, Zichao; Lou, Ange; Zhao, Yuying; Wei, Wei; Bao, Yujia.
"Collaborative Memory: Multi-User Memory Sharing in LLM Agents with Dynamic Access Control."**
Center for Advanced AI, Accenture. **arXiv:2505.18279v1** [cs.MA], 23 May 2025.
Local: `papers/rezazadeh2025-collaborative-memory.pdf`.

- *Two-tier memory, immutable provenance, read-time policy projection*, abstract and
  related-work section, **~p. 3**: "Each fragment carries immutable provenance attributes
  (contributing agents, accessed resources, and timestamps) to support retrospective permission
  checks"
- *Dynamic access graph*, same section: "time-varying bipartite graphs between users, agents,
  and resources"

### Cited in "deliberately not adopted"

**Hernández, Daniel; Hogan, Aidan; Krötzsch, Markus. "Reifying RDF: What Works Well With
Wikidata?"** In *Proceedings of the 11th International Workshop on Scalable Semantic Web Knowledge
Base Systems (SSWS 2015)*, co-located with ISWC 2015, Bethlehem, PA, USA, October 11, 2015, eds.
Thorsten Liebig and Achille Fokoue. CEUR Workshop Proceedings, Vol. 1457, pp. 32-47.
http://ceur-ws.org/Vol-1457/SSWS2015_paper3.pdf

**Completed 2026-08-28.** Trap to avoid: the PDF's own `/Subject` metadata field reads "Scalable
Semantic Web Systems 2014", a stale LaTeX template value. The venue is SSWS **2015**. Its
substantive claims check out: 57,088,184 Wikidata quads (Table 2), and the Conclusions state that
four of five engines "struggled with the high number of unique predicates generated by singleton
properties" (Virtuoso was the exception).
Local: `papers/hernandez2015-reifying-rdf-wikidata.pdf`.

**Sumers, Theodore R.; Yao, Shunyu; Narasimhan, Karthik; Griffiths, Thomas L. "Cognitive
Architectures for Language Agents."** *Transactions on Machine Learning Research*, February 2024.
arXiv:2309.02427v3, 15 March 2024. OpenReview `forum?id=1i6ZCvflQJ`.
Local: `papers/sumers2024-coala.pdf`.

### Added 2026-08-28

**Wikidata contributors. "Help:Ranking."** Wikidata, Wikimedia Foundation. Revision of 11 August
2026 (oldid 2530015510).
`https://www.wikidata.org/w/index.php?title=Help:Ranking&oldid=2530015510` (accessed 27 August
2026).

Defines all three values: *preferred* ("the most current statement or statements that best
represent consensus"), *normal* ("assigned to all statements by default"), and *deprecated*
("statements that are known to include errors"). Use the `oldid` permalink so the citation does not
drift. This is the source for `rank` in `03_design.md`, not the CACM paper.

### Standing rule for this file

Every claim attributed to a source above was read out of the PDF or the publisher's page, not
recalled. Anything added later must meet the same bar.

**`papers/MANIFEST.md` does not cover these four sources.** It holds 72 rows and has no entry for
`angles2018`, `rost2021`, `hernandez2015` or `vrandecic2014`, all of which were fetched after the
manifest's own stated fetch time. Its header also claims "34/43 on disk" against 92 PDFs actually
present. Repair it before the manifest is used as an inventory.
