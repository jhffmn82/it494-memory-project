# LLMs Interpret, Embeddings Organize, Graphs Emerge: Agent-Driven Compilation of Scientific Knowledge
Ran, Zhang, Wu, Yang, Li 2026, arXiv:2608.29612 (cs.AI), submitted 30 August 2026

ASKS, the Agent-Driven Scientific Knowledge System, does what the decision record feared: it turns a
corpus into a graph-organized wiki with a hierarchical portal, and it published first. The pipeline
is close enough to ThreadAtlas that the overlap has to be stated plainly. Each source is preserved
and versioned, then an LLM compiles it into two sibling surfaces from the same evidence root: a
readable Wiki view for people and models, and machine-facing semantic slots for computation.
Deterministic checks turn the slots into a document-local GraphDelta, a validated statement of what
this one source proposes to change. Embedding geometry plus explicit graph rules (lexical gates,
thresholds with hysteresis, routing checks, Hub capacity, lineage constraints) convert that proposal
into admissible writes against persistent state. Fusion is transactional: the whole document update
lands or the previous graph is restored. The claimed contribution is the state transition itself,
inspectable, replayable, and source-linked, which the authors name scientific knowledge compilation.

The evaluation is a chronological compilation of 56 papers from one research program, the
corresponding author's own tensor-network group, producing a source-traceable author research
portrait. Reported: all born branches persist, membership churn 0.00467, canonical-node growth
purely additive, Hub organization stable and low-churn across the trajectory. Notice what those
metrics are. They are structural properties of the graph the system built, measured against itself.
There is no question-answering benchmark, no retrieval accuracy, no comparison arm against flat
retrieval or a published baseline, and no second corpus. The paper is careful about this and says
scientific novelty remains a separate review judgment, but it means ASKS has demonstrated that its
construction is stable, not that anything downstream reads better because of it.

That gap is the opening. Four object-level differences survive a close read. First, the readable
surface: an ASKS Wiki page is compiled per source, with concepts, propositions and Hubs as the
reusable nodes, whereas a ThreadAtlas page is compiled per entity from cells, and the cell sequence
is the page body. Second, order: ASKS is chronological at the corpus level, paper index t, and
nothing in it is ordered within a document; ThreadAtlas's unit ordinal makes narrative progression
inside one source the thing that accumulates. Third, identity: ASKS canonicalizes into canonical
nodes under gated, consequential merge decisions, and reports additive growth as a good result;
ThreadAtlas refuses to merge at all, keeps a document-local entity per source, and makes global
attachment a reversible edge the child owns, so a source's own account of an entity is never
overwritten by the consensus. Fourth, what the system is for: ASKS organizes a literature so a
researcher can navigate it; ThreadAtlas is a memory backend whose portal is one of two readers, the
other being an assistant's context constructor exercising the same retrieval path.

Three practical consequences. The hierarchical-portal claim is dead and the guardrail against
claiming it was correct, so the fall paper should position on ordered entity cells and reversible
identity and evaluate exactly that. The un-run measurement in ASKS is the one already on the
ThreadAtlas slate, which makes the GraphRAG-Bench and NarrativeQA arms more valuable rather than
less: they answer the question this paper leaves open. And the licensing matters for the corpus
plan: the ASKS software is PolyForm Noncommercial 1.0.0 and the frozen artifact, 56 sanitized paper
Wiki pages plus 18 Hub pages in the Ran-ASKS v0.2.0 release, is CC BY-NC 4.0, so none of it can
enter the public CC-BY dataset. It belongs in the reference library and in related work, not in
`data/raw/kg-rag-cc/`.

Read from: full text, 21 pages, plus the code and data availability statement.
