# What this project claims

**2026-08-28.**

## Short version

Nothing in this design is new. Twelve ideas were checked against published work and all twelve were
already taken. That is survivable, because the paper does not need a new idea. It needs a
measurement.

**The paper is: here is the system, and here is which parts of it actually help.**

---

## The twelve ideas, and who got there first

| The idea | Already published by |
|---|---|
| Memory that speaks up without being asked | CogniFold, ProactAgent, ENPMR-Bench |
| Building a schema from scratch out of text | AutoSchemaKG, SCOPE/SCION, EvoTaxo |
| Turning chat history into story threads | TraceMem |
| Summaries written per character | EntSUM (ACL 2022), EntSUMv2 |
| Untangling interleaved conversations | an active task at ACL, SIGIR, LREC |
| Nobody measures memory system costs | Anatomy of Agentic Memory says it first |
| One person's archive as a case study | MyLifeBits, twenty years ago |
| Putting one chapter in several threads at once | RAPTOR does this, and so does CAM |
| Using novels to test memory | NarrativeXL, MemoryAgentBench, StoryBench |
| Listing what assistant memory needs | Jones et al. (CHI 2025), and 2606.24775 across 12 systems |
| Finding entities before extracting facts | iText2KG, RAKG, LINK-KG, CORE-KG |
| Publishing cleaned novels as a test set | GraphRAG-Bench, AffilKG, STAGE, CoSER |

The last row is the sharpest lesson. The plan said GraphRAG and Zep pull facts out chunk by chunk,
so scanning the whole chapter for characters first was the contribution. **Both of them already do
characters first**, by their own papers. And iText2KG already ran that exact experiment: doing it
"our" way scored about ten points *worse*.

**Rule from here: do not add a thirteenth idea without searching it first.** All twelve died the
same way, by assuming nobody had done it. Three were disproved by papers already sitting in this
repo's `papers/` folder.

---

## Why having no new idea is survivable

The conferences this would go to say so in their own guidelines:

- **PVLDB:** novelty "often lies in the design, innovative system architecture, new abstractions, or
  interesting and effective combination of existing techniques."
- **NeurIPS 2026:** "originality does not necessarily require introducing an entirely new method."
- **ACM SIGSOFT** lists "This is not the first known solution" as an **invalid** reviewer criticism.

The catch, from the same source: **"less innovative artifacts require more rigorous evaluations."**
You trade novelty for measurement. The novelty is gone, so the measurement has to be good.

**The upside:** measuring which parts help means building the system. So the class project and the
paper are the same work, not two things competing for the same hours.

---

## Say this, not that

**Say:** every part is borrowed, and here is who from. Hierarchical summaries from GraphRAG and
RAPTOR. Dated facts from Zep. Per-character summaries from EntSUM. Character timelines from timeline
summarisation. Incremental updates from MemTree. Graph structure from Angles. Fact ranking from
Wikidata.

**Say:** every claim the system makes traces back to a quote in the source, because a claim without
a matching quote never gets written.

**Do not say:** the system never makes things up. Tracing is not the same as being right. A false
relationship can still carry a real quote, which is why there is a type check on relationships.

**Do not say:** this measures how often an AI assistant makes things up. It measures one output
format on one set of books.

---

## What could still sink it

- **The measurement may not be sensitive enough to show anything.** The main test set has 229
  questions. Switching off one part of the system usually moves accuracy 2 to 5 points, and with 229
  questions you need roughly 5 to 9 points before a difference is real rather than noise. Biggest
  risk, and it is fixable. See `09_evaluation_corpus.md`.
- **Two papers sit very close.** *Narrative World Model* (arXiv:2607.05577) does memory for long
  fiction and tests against Zep and GraphRAG. *Story Ribbons* (IEEE VIS 2025) already builds
  per-character summaries per scene across 30 Gutenberg books, with the same quote check. Read both
  before writing. Story Ribbons has no search layer, which is the honest difference, and that
  belongs in your introduction rather than in a reviewer's complaint.
- **This goes stale fast.** Re-run the checks right before submitting. Three months is enough for
  something new to land.
