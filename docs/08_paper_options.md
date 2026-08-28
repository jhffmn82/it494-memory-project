# Is there a paper, and what kind

**2026-08-28.**

## Short version

Yes, but it is a **systems paper**, not a research paper with a new idea. The contribution is the
measurement: which parts of this design earn their cost. Venue is a **system demonstration track**.

---

## What kind of paper

Not "here is a new method." That door is closed; see `01_argument.md`.

Instead: **here is a working system, and here is what each piece of it is worth.** You build it,
then switch off one piece at a time and measure what breaks. That is the whole paper.

This works because the venues say novelty is optional and rigour is the price. It also means the
class project and the paper are the same work.

---

## What it has to contain

The venue analysis is specific about the bill:

1. **Compare against real systems.** Mem0, Zep, MemGPT/Letta, A-MEM, plain RAG, full-context.
2. **Turn parts off, one at a time.** No salience threshold. No per-character summaries. No fact
   layer. No incremental refolding. Report what each costs.
3. **Measure something other than accuracy.** The best candidate is **recompute cost when the corpus
   changes**, because incremental refolding is the piece this design actually invests in. Position
   it against MemTree's published numbers (3,750 LLM calls per insertion for RAPTOR, 3,850 for
   GraphRAG, 3.27 for MemTree), not as a first.
4. **Ship a DOI'd artifact**, and report at least one honest negative result.
5. **Concede in the introduction that every mechanism is borrowed**, with citations, before a
   reviewer says it for you.

---

## Where it goes

**ACL, EMNLP or NAACL System Demonstrations.** Six pages, prototypes explicitly in scope, entry is a
live link plus a short screencast. The model is **FlexRAG (ACL 2025 Demo)**, an open-source
framework with no algorithmic claims at all.

**ESWC In-Use** is the one archival venue that waives method novelty *and* accepts "a principled
evaluation" in place of a deployed user base. Roughly early December, 15 pages. Deadline unverified.

**Closed:** KDD ADS and CIKM Applied desk-reject systems with no live users. VLDB Industrial needs a
non-academic author. ICSE-SEIP is built around an organisation. Every 2026 negative-results workshop
has passed.

---

## For the December applications

A preprint helps at the margin. Its real value is giving Fang something concrete to describe in the
research letter, and showing you can finish a paper-shaped thing.

- **Now:** ask Fang for an arXiv cs.CL endorsement. First-time submitters cannot post without one
  and an ISU address does not grant it. Only step that depends on another person.
- **Sept 1:** make the repo public. Free, and it starts the six-month clock JOSS requires.
- **Nov 10:** publish the dataset with a DOI. Zenodo mints on publish, no review.
- **Nov 16:** submit to arXiv, cs.CL, as a resource-and-experience paper. Not a survey or position
  paper, which arXiv CS rejects without prior acceptance. Avoid Nov 23 to 27.

**On the CV:** "Preprints", never "Publications". Dataset under "Research Artifacts".
Miscategorising a preprint is the most common mistake and committees notice.

**ARR's October cycle was rejected:** its deadline falls inside the dead weeks.

---

## Ideas considered and dropped

Each was searched, each is occupied. One line apiece so nobody re-opens them. Detail in
`01_argument.md`.

- **Stage-wise model tier study.** Occupied at ICML 2025, KDD 2026, WWW 2025.
- **The corpus as a resource paper.** GraphRAG-Bench and AffilKG got there; SPGC did it at 600x the
  scale.
- **Book-scale replication of the cast-conditioning experiment.** The only book-scale gold set
  (BOOKCOREF) cannot score the metric, the answer is predictable, its three books are among the most
  memorised in English, and the build alone exceeds the semester.
- **Fault injection on the personal archive.** Occupied by AgentChaos (ASE 2026) and
  SuperLocalMemory, and ruled out anyway by the scope decision that the personal archive is not
  evidence.
- **Local-first at personal scale.** *As We May Search* (ICTIR 2026) is the same thesis, the same
  two arms and the same crossover number, seven weeks earlier.
