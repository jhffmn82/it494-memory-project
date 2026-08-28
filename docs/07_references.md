# Where the schema decisions came from

**2026-08-28.** Six design choices in `03_design.md` came from published work rather than from
taste. Each citation below was read out of the PDF, not recalled.

---

## The six

| Decision | Source | Why |
|---|---|---|
| A table of which relationship types may join which entity types | Angles 2018, Definition 2 | Catches a made-up relationship that carries a real quote, which the quote check cannot see |
| Date ranges are `[from, to)`, upper bound excluded | Rost et al. 2021, pp. 6-7 | Free correctness wherever two ranges meet |
| Validity lives on the fact, not on the property | Rost et al. 2021 | Already covered here, since our facts *are* the properties. Recorded so it is not re-opened |
| Qualifiers carry roles and timing, not just dates | Vrandečić and Krötzsch 2014, p. 82 | Stops "as Chancellor" becoming a new invented predicate |
| Facts carry preferred / normal / deprecated | Wikidata *Help:Ranking* | Supersession handles "the world changed". This handles "we were wrong", where no later event exists and deleting would break append-only |
| Provenance on every record, permissions applied at read time | Rezazadeh et al. 2025 | Makes multi-user a later config change rather than a rewrite |

---

## Citations

**Angles, Renzo. "The Property Graph Database Model."** *Proceedings of the 12th Alberto Mendelzon
International Workshop on Foundations of Data Management (AMW 2018)*, Cali, Colombia, May 21-25
2018, eds. Olteanu and Poblete. CEUR Workshop Proceedings Vol. 2100, paper 26.
`http://ceur-ws.org/Vol-2100/paper26.pdf`

Single author, unpaginated, no DOI. Venue confirmed three ways: the local PDF is byte-identical to
the CEUR copy, the Vol-2100 index lists it, and Rost's reference list cites it the same way. Not to
be confused with `angles2017-graph-query-foundations.pdf`, a different six-author survey.

**Rost, Christopher; Fritzsche, Philip; Schons, Lucas; Zimmer, Maximilian; Gawlick, Dieter; Rahm,
Erhard. "Bitemporal Property Graphs to Organize Evolving Systems."** arXiv:2111.13499 [cs.DB], 26
November 2021. DOI 10.48550/arXiv.2111.13499

**There is no venue.** The LNCS-style layout is misleading: arXiv lists no journal reference, DBLP
carries it only under CoRR, and the authors' own page calls it a Leipzig technical report. **Cite it
as a preprint.**

**Vrandečić, Denny; Krötzsch, Markus. "Wikidata: A Free Collaborative Knowledgebase."**
*Communications of the ACM* 57(10), October 2014, pp. 78-85. DOI 10.1145/2629489

Qualifiers are on p. 82. Statement marking is on p. 83.

**Note:** the ranking vocabulary is **not in this paper**. Two independent extractors over all nine
pages find no occurrence of "rank" and no "normal" value; only "preferred" and "deprecated" appear.
For the three-value scheme cite the help page below.

**Wikidata contributors. "Help:Ranking."** Revision of 11 August 2026 (oldid 2530015510).
`https://www.wikidata.org/w/index.php?title=Help:Ranking&oldid=2530015510`

Defines all three: *preferred* ("the most current statement or statements that best represent
consensus"), *normal* ("assigned to all statements by default"), *deprecated* ("statements that are
known to include errors"). Use the permalink so the citation cannot drift.

**Rezazadeh, Alireza; Li, Zichao; Lou, Ange; Zhao, Yuying; Wei, Wei; Bao, Yujia. "Collaborative
Memory: Multi-User Memory Sharing in LLM Agents with Dynamic Access Control."** arXiv:2505.18279v1
[cs.MA], 23 May 2025.

Each fragment carries immutable provenance (contributing agents, resources, timestamps) to support
retrospective permission checks.

**Sumers, Theodore R.; Yao, Shunyu; Narasimhan, Karthik; Griffiths, Thomas L. "Cognitive
Architectures for Language Agents."** *Transactions on Machine Learning Research*, February 2024.
arXiv:2309.02427v3.

---

## Considered and not adopted

**RDF reification** (Hernández, Hogan, Krötzsch, *"Reifying RDF: What Works Well With Wikidata?"*,
SSWS 2015, CEUR Vol. 1457 pp. 32-47). The question it answers, how to attach metadata to a triple,
is native in a property graph where edges carry properties directly. Its finding that singleton
properties broke four of five engines is a warning about RDF stores, not about this one. Trap: the
PDF's own metadata says 2014; the venue is 2015.

**CoALA's four-way memory taxonomy** (working, episodic, semantic, procedural). A useful frame for
prose, but it does not map onto storage here: units are episodic, facts and abstracts are semantic,
and there is no procedural memory at all. Adopting it would add a field that never varies.

---

`papers/MANIFEST.md` predates roughly half the current corpus and needs rebuilding before it is used
as an inventory.
