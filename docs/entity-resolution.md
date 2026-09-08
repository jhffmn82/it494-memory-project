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

Resolution misses divide the way retrieval misses do in BUILD.md: never a candidate (the gold
match was outside the nearest-k and shared no exact surface, so no judge ran) against judged
apart (nominated, then ruled different). The alias set is scored for gold-pair candidate recall
first, the share of must-merge pairs that appear together in some nominated set, and merge
precision and recall are reported against that denominator. A pair never nominated leaves no
candidate row, so the number comes from joining the gold pairs against the nomination log.

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

## Settled, 2026-09-07: a node exists at document scope, and nothing is ever merged

The question was at what scope a node exists, with two shapes offered: corpus-global with
per-scope aliases, or scope-local with explicit cross-scope links. Justin's answer takes the
second and pushes it further than "links". **Nothing is ever merged. It is a tree.**

Three rules, and everything else is a consequence of them.

1. **A fact, a relationship edge and a child node each belong to exactly one document.**
2. **A parent node holds no asserted content.** It carries three derived fields and nothing else:
   a name, a profile of what it is, and an abstract. Every one of them is recomputed from its
   children and none of them is ever the source of a fact or citable as evidence.
3. **A parent owns no edges.** Documents point up at it. The up-edge belongs to the child's
   document, like every other edge.

A fourth rule governs what those derived fields may say. **A child says something about the
world; a parent says something about the corpus.** "GPT-4 scored 71.2 percent" is a claim about
the world, needs a quote, and lives on a child. "This entity appears in sixteen documents, as the
system under test in twelve" is a claim about documents that are in hand and countable, and needs
no quote because it asserts nothing about GPT.

Stated as a test a reviewer can apply: **every sentence on a parent must be reducible to "N of M
children say X".** A clause that cannot be written as a count does not belong there. That is
stricter than the fabrication check, which only asks whether the names below are real; this asks
whether the claim itself is a count.

### Why the three fields are those three

An entity mentioned in a paper's abstract yields exactly three things: its name, that it is an LLM
model, and that it was used for benchmarking in that paper. Nothing else is knowable from a
mention, and nothing else belongs on the parent. They map one to one: the name feeds the parent's
name, the kind feeds its profile, the role feeds one line of its abstract.

That also says which fields should agree and which should vary. Name and kind should agree across
every child, so **disagreement between children is the attachment alarm** rather than a tie to
break: a parent whose children call it `model` and `company` has a wrong up-edge, and the signal
is free because the field was being computed anyway. Role is the field that legitimately differs,
which is why the abstract is a collection of roles rather than a summary of a thing.

The shape scales by itself. GPT's parent is thin, because its children are mentions. Dorothy's is
rich, because her children are protagonists carrying dozens of facts each: "a recurring character
in Baum's Oz series, frequently depicted as brave, who ventures to Oz numerous times" is three
counts over her children and asserts nothing they do not. Same rule, no special case for a
mention-only entity against a lead character. A parent is as informative as its children can
support and never more.

So the store is a forest of identity trees over a set of per-document graphs. Relationships are
still graphs; they are confined to a document. The only thing that spans documents is the tree,
and a cross-document traversal goes up through a parent and back down into another document.

### Say it as class and instance

Justin's own framing, and the one to use with a CS audience: **Dorothy is the class, each Dorothy
in a book is a living instance.** The up-edge is `instance_of`, which is also Wikidata's P31, so
the name comes with precedent. Precision worth keeping, because a reviewer will test it: this is
a class **induced from its instances**, bottom up, and it constrains nothing. A child may
contradict its siblings and both stand. Plain OOP declares the class first and makes instances
conform; a class that cannot reject a non-conforming instance is not doing a class's job, so say
"a class induced from its instances, with no authority over them" and the analogy holds.

Two things follow directly. The kind alarm gets its reason: two things cannot be instances of one
class if their `is_a` disagrees, so a child whose kind differs from its siblings is a wrong
attachment rather than a tie to break. And the parent's three derived fields get a definition:
they are static members computed over the instances, with the counting rule above as the only
thing keeping them from becoming assertions.

The comparison worth borrowing and not overclaiming is the B+ tree. Its defining property is that
**all data lives in the leaves and internal nodes are routing keys**, which is this design
restated in another vocabulary and is the justification for treating the parent as an index. What
does not carry over is the rest of the B+ tree: identity has no total order, there is no separator
key, and at two levels deep there is nothing to descend. What this actually resembles is an
inverted index with cluster representatives, except that the representative keeps every member's
vector instead of a centroid, **because a centroid is a merge**: averaging the children's vectors
destroys exactly what the design refuses to destroy, and it fails hardest on the case that
matters, where one instance of Dorothy is a farm girl in Kansas and another is a ruler in Ozma.
So in writing take the property and leave the name.

### What this buys

**Merging stops being destructive, because it stops existing.** Attaching a child to a parent is
adding an edge. Nothing is rewritten and nothing is combined, so there is no un-merge problem:
re-deciding identity is re-pointing an edge.

**Insertion is append-only, and the incremental-insertion problem is not solved but unposed.**
RAPTOR, GraphRAG and Talebirad all leave insertion open because inserting means re-merging: a new
document can change what an existing node *is*. Here a new document mints its own children and
attaches edges, and no existing node changes.

**Deletion is correct for free.** In a merged graph, "forget this conversation" is close to
impossible, because the merged node carries contributions from it that cannot be subtracted
without re-deriving everything downstream. Here, deleting a document removes its children and its
edges, including its claim on the parent; the parent survives with fewer children or is dropped.
Nothing else is touched. For a backend meant to hold one person's archive, retention and
forgetting become a delete rather than a research problem.

**Provenance is total, and the synthesized layer disappears.** Every edge in the store answers
"which document says so", including the identity claim. This matters because of a measured
finding, not a hoped-for one: in the archive's own layer-seam audit, 39 node claims traced to raw
gave 31 confirmed, 4 wrong and 4 unsupported, and *every* defect sat in the synthesized layer
while all 31 leaf checks were clean. A store with no synthesized layer has nowhere for that class
of defect to live.

**The quote gate becomes structural rather than procedural.** A fact needs a quote, a quote needs a
document, so every fact hangs off a child. A parent cannot carry a fact, so it is impossible *by
shape* for an unsourced claim to exist. That is a stronger guarantee than the gate, which is code
and could be wrong.

**Disagreement survives and becomes visible.** Two children of one parent may say contradictory
things and both stand. A merged node cannot represent "these sources disagree about whether this
is one person"; a spine can, and that is the state a memory over two years of an archive is
actually in.

**One parent per child, with no ambiguity to bury.** A child belongs to one document and its
document makes one claim. Two documents disagreeing appears as two children under different
parents, which is visible and resolvable, rather than as an ambiguity folded inside a node.

### What it costs, and what it changes about the paper

There is no stored answer to "what is true of Dorothy". There are eleven document-Dorothies and a
parent; any consolidated view is computed on demand and never written. That is a one-hop
traversal, deterministic and cheap, but it is a traversal.

**Duplicate-minting rate stops being a metric this system can compete on**, because it is not
minting duplicates, it is declining to decide. The honest replacement is *attachment accuracy*:
how often the up-edge puts a child under the right parent, scored against LitBank's gold
coreference. That is a cleaner question than "did the merge lose something" and it is measurable
without a judge model.

The comparison to GraphRAG therefore changes shape. It is no longer "our merge is better than
yours"; it is "we do not merge, here is what that costs at query time and here is what it buys in
insertion, deletion and provenance". A reviewer will ask how a multi-hop cross-document question
gets answered. The answer is the traversal, and its cost and accuracy have to be measured rather
than asserted.

### Still to decide, none of it destructive

0. **Granularity, and it may answer itself.** GPT, GPT-3.5, GPT-4 and GPT-4o: one parent or four?
   If the evidence is name, kind and role, they stay four, because nothing in the corpus says they
   are the same and a design whose point is to not assert what it does not know cannot quietly
   assert it. They collapse only when a document says so, in which case that is a fact on a child
   with a quote behind it. The rule falls out rather than being imposed.
1. **What draws the up-edge.** Given a new document's children, which existing parents they attach
   to. This is the only global operation left. It is a matching problem over monikers and
   dossiers, not a merge, and being an edge it can be redone.
2. **The parent's name.** It needs one to be findable. Derived from its children and recomputable,
   a cache rather than an assertion, consistent with the rule that indexes are derived and
   disposable.
3. **Whether the up-edge carries its score and its evidence.** It should, or the reason for the
   link is thrown away and it cannot be re-decided later.

### Consequences already ruled, 2026-09-07

These were taken as ingestor decisions before the shape above was stated, and they are its
consequences rather than separate rules. Numbering is from
`log/2026-09-07/decisions-ingestor-0.7.md`.

- **48.** A node id cannot be a hash of a single document at the global level, though it can at the
  document level. The document-level id is the moniker plus its first mention. The global id is
  Step 2's business, which under this shape means it is a parent token and nothing more.
- **49.** The same name and kind unite on sight only when nothing in their `is_a` conflicts. The
  Iliad's two men named Ajax and Oz's two Wicked Witches are why.
- **54.** The package ships the dossier text and no vector, so the embedder can change. Under this
  shape the parent's index is derived anyway, which is the same argument.
- **It may reopen the minors ruling.** Minor entities are mentions inside documents because
  disambiguating them costs too much and, being minor, there is not enough information to do it
  with. A parent asks for nothing more than name, kind and role, which is what a minor already
  has, and a wrong up-edge is an edge to re-point rather than a merge to unpick. The cost argument
  survives, since it is thousands more attachment decisions. The information argument may not.
  Decide deliberately rather than inheriting it.

- **61.** A node records whether its document ever named it, so the both-named rule can be applied
  across documents rather than guessed from aliases. That rule is now what draws the up-edge.

### Not yet claimed as novel

This resembles published things: Wikidata items whose statements carry references rather than
being merged, cluster representatives in entity resolution, singleton and canopy models. Whether
this exact formulation, a parent that holds nothing and edges that are all document-owned, is
published is unsearched. It is written here as a design position that dissolves three open
problems named in the reading list, which is worth recording whether or not it turns out to be
new. Search before it goes near the paper.

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
