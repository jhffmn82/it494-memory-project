# Deciding when two names mean one thing

**2026-08-28.** Requirement 2 in `../RESEARCH.md`. This is the one stage where the
design departs from every system it is measured against, so it gets its own page.

## The problem

"The boy" and "Tip" are the same person. So are "Mrs. Hudson" and "the landlady". Neither pair
shares a string. Get this wrong in the merging direction and two people become one; get it wrong in
the splitting direction and one person becomes twenty nodes and no narrative holds together.

## Three signals, cheapest first

1. **Name.** Embedding cosine over the alias table. What everyone already does.
2. **Co-occurrence.** Score a candidate higher when the current chunk also contains entities already
   linked to it. "The boy" appears alongside Mombi and Jack Pumpkinhead, both already linked to Tip.
3. **Profile.** At extraction the model emits low-confidence attributes inferred from context rather
   than stated in the text: gender, age band, animacy, species, role. From "Tip pulled off his hat"
   it infers male, child, human.

Score is a weighted sum. **Profile mismatch lowers a score. It never blocks a merge.** Reason in the
guards section.

### The profile is not a fact

```
Profile {node_id, attribute, value, confidence, from_unit}
```

Separate table, read only by the matcher. It never renders, never exports, never reaches a reader.
Profile attributes have no supporting quote, because the text never says "Tip is male," so putting
them in the fact table would break invariant 3 and make the quote gate a lie. Keeping them apart
keeps the fact layer single-ruled: everything in it has a quote, no exceptions.

## Where this comes from

None of it is new, and the write-up should say so in one sentence rather than get caught.

| Piece | Cite |
|---|---|
| Resolving co-occurring references jointly instead of one at a time | Bhattacharya and Getoor, TKDD 1(1) art. 5, 2007. Their score is (1 minus alpha) times attribute similarity plus alpha times relational similarity |
| Associations between references, evidence propagated between decisions, references enriched by merging attributes | Dong, Halevy and Madhavan, SIGMOD 2005, pp. 85-96. Motivating domain was personal desktop email and files |
| Type compatibility as a soft probabilistic term, not a filter | Ling, Singh and Weld, TACL 3:315-328, 2015, section 4.3. Fine-grained types beat coarse ones |
| Merged entity keeps all attribute variants when they contradict | Lee et al., Computational Linguistics 39(4), 2013, section 3.2.3 |
| Why the profile is worth the plumbing | DeepType (AAAI 2018): with oracle types, linking accuracy reaches 99.0 on CoNLL and 98.6 on TAC KBP 2010 |

**Use these words:** collective entity resolution, relational similarity, neighborhood similarity,
reference enrichment, entity type compatibility, transitive closure.

**Do not use these:** "coreference propagation", "merge propagation", "error propagation in
collective ER", "cascading merge errors", "merge avalanche". None of them appear in the surveys.
They read as invented, because they are.

## What is actually unmeasured

Every system this is benchmarked against resolves on strings or embeddings plus an LLM verdict.

| System | How it resolves |
|---|---|
| GraphRAG | exact string matching, stated outright |
| iText2KG | name-embedding cosine, threshold 0.7 |
| RAKG | name plus type embedding, then an LLM adjudicates |
| CORE-KG | type-wise LLM coreference pass before extraction |
| LINK-KG | prompt cache of aliases, explicit details only |
| Zep / Graphiti | name and summary embedding, then an LLM resolution prompt |
| AutoSchemaKG | no resolution stage at all |
| HippoRAG 1 and 2 | never merges; adds synonym edges above cosine 0.8 |

A search across the resolution-relevant papers on disk, 46 at the time, found no LLM knowledge-graph or agent-memory system using
co-occurrence as a resolution signal. So the question is not whether collective entity resolution
works, which was settled in 2007. It is **whether the classical relational signal still pays when
the candidate scorer is an embedding and an LLM rather than a string metric.** That is measurable,
and measuring it is the contribution.

Usefully, iText2KG's own future work asks for signal 3: "integrating the entity type as a parameter
of the matching process." Answering an open question posed by a system in the comparison table is a
better position than any novelty claim.

## The risk, with numbers

Collective resolution buys accuracy by letting merges feed each other, which is the same mechanism
by which one bad merge poisons the next.

- **Kardes et al. (TextGraphs-8, 2013)** name it "black hole entities" and measure it: a pairwise
  classifier gets precision 97 and recall 63; unrestrained transitive closure gets precision **64**
  and recall 98. Their soft clustering recovers to 95 and 76.
- **Bhattacharya and Getoor** admit it about their own algorithm: merges cannot be undone, so
  "precision is crucial for the bootstrap process," and that cost is one "not necessary for
  approaches that are not collective." Irrevocability is the price of going collective.
- **Their Table I** shows both edges. Attribute-only to collective: CiteSeer 0.980 to 0.995, arXiv
  0.974 to 0.985, BioBase 0.568 to **0.819**. Collective buys almost nothing on clean data and 25
  points on ambiguous data. Meanwhile plain transitive closure *hurts* BioBase, 0.568 to 0.559.
- **Walmart's ER-in-practice report (arXiv:2607.26298)** contradicts the soft-veto choice directly
  and should be cited against ourselves rather than left for a reviewer to find: transitivity moved
  Pair-F1 on MusicBrainz-200K from 0.540 to **0.000** by forming mega-clusters. Their rule of thumb
  is that above 0.9 baseline precision transitivity is safe and below 0.5 it makes mega-clusters,
  and their Lesson 2 is that precision needs hard vetoes.

This is also the failure already measured in the personal deployment: a false merge inherits both
fact sets, and the inherited facts then look like independent corroboration.

## Guards

1. **Profile compatibility is evidence, never a veto.** Tip is the fixture that proves it. The system
   infers male and boy in chapter 1, and by the end of book 2 Tip is Ozma and always was. A profile
   veto would make the most important case in the corpus fail by design.
2. **Inherited facts never count as independent corroboration.** A merged node's evidence carries the
   merge that produced it.
3. **Every merge records its evidence** and stays revocable. The literature has no name for this and
   no source was found for it as a known mitigation, so it is a design choice, not a citation.
4. **Cap cluster size.** Kardes's fix: if a component exceeds a threshold, raise the match threshold
   and re-partition it.
5. **Watch the merge rate per chunk.** A spike is a black hole forming.
6. **Report a pair metric and a cluster metric.** Menestrina, Whang and Garcia-Molina (PVLDB 3(1),
   2010) show these measures disagree and can rank the same system differently. Their generalized
   merge distance takes separate merge and split costs, which is how to say "a wrong merge costs more
   than a wrong split" formally.

## How it gets tested

Four arms, same corpus, same model, everything else held constant:

| Arm | Signals |
|---|---|
| N | name only, the field default |
| N+C | name plus co-occurrence |
| N+P | name plus profile |
| N+C+P | all three |

Reported per arm: duplicate nodes minted per chunk, merge precision on a hand-checked sample,
cluster purity, and downstream accuracy on GraphRAG-Bench. Duplicate rate uses the CORE-KG and
LINK-KG protocol: fuzzy match at 75 percent within type, connected components, manual review, then
count the sum over components of size minus one, normalized by node count.

## This is a build instrument before it is a paper instrument

Resolution is not one test among five. It is the **gate on the other four**. Cells are per-entity
narratives, facts attach to nodes, and the wiki is a page per entity, so if resolution is wrong then
the cells ablation, the supersession fixtures and the demo are all measuring noise. Nothing
downstream can be trusted until this is known to work.

So the instrumentation below belongs in the build phase, not the evaluation phase, and it would be
written even if no paper came out of it.

**That exposes a gap.** Every comparison in this document needs a working end-to-end system first,
which means there is no signal at all during the weeks when it would be most useful. Fix it cheaply:
**hand-label the aliases for one novel** before the first ingest. Around twenty characters, their
aliases and epithets, the pairs that must merge, and a few near-misses that must not. Half an hour of
work, runnable from day one, and it catches the two failures that actually kill the build (a black
hole forming, or nothing merging at all) months before any benchmark would.

The Tip fixture belongs here too. It is a regression test first and a demonstration second.

## Open: at what scope does a node exist

Undecided, cheap now, expensive after any corpus is loaded. `scope_id` exists on cells and abstracts
and is **not** on resolution.

Within one novel "the boy" has a few dozen candidates. Across many works the same name collides
constantly: every Elizabeth, every Mary, every doctor. Resolve globally and those merge. Resolve per
work and cross-work linking disappears, which is the interesting case, since Napoleon in Tolstoy and
Napoleon in Hugo are the same person.

Two shapes: a node is corpus-global with per-scope aliases, or scope-local with explicit cross-scope
links. Decide before the second corpus is ingested, not after.

## What to instrument at build time

Most of these tests are free once the pipeline records the right things, and expensive to retrofit
after. Build these in from the start.

**Log every candidate the matcher evaluates, with each signal scored separately.** Not just accepted
merges, and not just the combined score.

```
MergeCandidate {mention_id, candidate_node, name_score, cooc_score,
                profile_score, combined, threshold, decision, unit_id}
```

This turns most of the ablation into an offline re-scoring: replay the log with different weights and
read off what the decision would have been, instead of paying for another full ingest.

**The limit, stated so it does not become a false claim later.** Every signal here is collective. A
merge changes the alias table, the co-occurrence sets and the node's accumulated profile, so a
different arm generates *different candidates* from that point on. Replay is exact only up to the
first divergence and drifts after it. Use it as a **screen, not a substitute**: run full ingests on
the two extreme arms, replay-estimate the middle ones, and spend a real ingest on a middle arm only
when the extremes are far enough apart to make it worth knowing.

Also required, and painful to add later:

- **Rejected candidates**, not only accepted merges. Merge precision needs the ones turned down.
- **Node lineage:** every node's constituent mentions with their source unit. Duplicate counting and
  cluster purity both read this.
- **The merge ledger with its evidence**, which guard 3 requires anyway.
- **Per-stage call and token counts by tier**, which is requirement 6 for free.

What this does not make cheaper: running someone else's system. That is a second implementation with
its own dependencies and its own full indexing pass, and no amount of instrumentation here reduces
it.

## Their numbers are not a target, and here is why

Checked 2026-08-28. **CORE-KG's 30.38 to 20.27 and LINK-KG's 27.0 to 10.6 cannot be beaten**, for
three independent reasons:

1. **The corpus was never released.** Both repos publish code and prompts and no data.
   `CoreKG-HumanSmuggling` has 33 files, one stray 11 KB blob named `...`, and no case documents.
   `LinkKG-HS` leaked a vim swap file (`.02USVsYusuf.txt.swp`) but not the text.
2. **Zero overlap with our corpus**, confirmed by Gutenberg ID. GraphRAG-Bench picked obscure works
   to limit contamination; gold-annotated book sets pick canonical works because that is where
   character lists exist. The disjointness is structural.
3. **Duplication rate is normalized by node count**, so it is bound to a domain and a graph size.

A rate on novels printed next to their rate on court filings is two unrelated numbers.

## What produces a comparable number instead

**Run their method on our corpus.** Both pipelines are released in full. Their seven coreference
prompts are typed for human smuggling (person, location, organization, means of transportation,
smuggled item, route, means of communication); retype them for narrative and run their method and
ours over the same novels, same model, same chunking, same duplication protocol. That controls every
confound a cross-corpus comparison leaves open, and it asks a question nobody has answered: **does
type-partitioned coreference transfer outside the domain it was written for?**

Cost note: they ran LLaMA 3.3 70B on an A100 80GB. Hold the model constant across both arms and use
whatever runs here; the comparison is what matters, not their hardware.

**Second gold number, different metric: BookCoref** (ACL 2025, HuggingFace
`sapienzanlp/bookcoref`). 53 Gutenberg books, gold coreference clusters, CoNLL-F1, published
baselines: best off-the-shelf 46.6, their pipeline 80.5, Dual cache 36.3 on Animal Farm. It measures
mention clustering rather than graph node dedup, and its gold split is three books, so it is a
second opinion and not the headline.

**Weak ground truth on our own corpus:** every one of the 2,010 GraphRAG-Bench questions carries an
`evidence_triple`, roughly 128 entity mentions per novel. It says which entities exist, not which are
the same, so it supports a recall check (did resolution lose an entity) and not a duplication rate.
Parsing needs care: some entries pack several triples into one field.

**Rejected: CoSER.** Alias-to-canonical mappings for 17,966 characters across 771 books would be
exactly right, but it releases "only the processed data, not the raw content from the novels" for
copyright reasons. Gold labels with no text.

**The expected result is worth predicting in advance.** By Bhattacharya and Getoor's finding, the
collective signal should buy little on low-ambiguity text and a lot on high-ambiguity text. Novels
full of pronouns, epithets and renamings are the high-ambiguity case. If N+C does not beat N here,
that is a real finding and it gets reported.
