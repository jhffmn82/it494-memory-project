# Phase 1 workflow: research and proposal package

**Goal:** a research package Justin can hand his professor on the morning of 2026-08-26, giving him aggregated breadth now so his own time goes to depth reading afterward.

**The end state, in Justin's words (2026-08-25):** "providing a user level knowledge back end that can be scaled to an organization." Every forward-looking document below (proposal, elevation options, project shapes, end product) is judged against that, not against any particular technique.

**Knowledge graphs are a candidate, not a commitment.** Justin: "I don't even know that knowledge graphs are the way I want to go." The professor asked him to explore the KG domain, so the survey happens, but the narrative and the options documents treat KGs as one representation among several (hierarchical summaries, flat fact stores, temporal graphs, vectors, hybrids), and nothing frames the project as a KG project.

**Standing rules for everything below**
- Provenance is labeled everywhere. Three buckets, never mixed: Justin's own words and work; what his records show; LLM survey output. Survey output never wears his voice. The one document in his voice (the proposal, item 5) is drafted from his own material only and delivered as a draft for his correction.
- Every citation verified against a source page before it enters any document.
- Each deliverable is committed and pushed as it finishes, so partial progress is readable from anywhere.
- Repo is private; paper PDFs are personal reference copies. Paywalled works get a stub with DOI and library link, never a pirated copy.

**Scope of record, revised 2026-08-25 evening (supersedes the softer framing above where they differ).** The prototype is a MOCK of the end state, not the subject. The build target is a bottom-to-top HARNESS: corpus in, memory tree + entity knowledge base + dated facts out, with efficient budgeted injection for RAG at query time. Fall: read, then build the harness at the toned-down spec (fixed shape, induced content; two corpora; simple supersession; three injection arms compared). Spring: distributable version others install, tested on a certified-unknown literature corpus, plus migration of Justin's raw data into the harness as tenant-zero proof.

**Design constraints of record (Justin, 2026-08-25):**
- Depth band: the model is the only accepted black box. No reimplementing inference, tokenizers, or index internals; every pipeline decision (segment boundaries, summary contracts, fact schema, staleness, injection budgeting, scoring) is his code, reviewable line by line.
- MODEL-AGNOSTIC BY CONSTRUCTION: every LLM-touching stage goes through two thin interfaces, embed(texts) and generate(prompt, schema), so embedders and generation models slot in and out, including low-powered cheap ones (local via Ollama, mini/haiku-class APIs). Every run row records the model id per stage. This is both the dev-loop economics (build and iterate on cheap models, final numbers on strong ones) and a first-class experiment: stage-wise model sensitivity, i.e. which pipeline stages actually need a frontier model and which run fine on a 7B, measured per question band. Schema-validated outputs make cheap-model failure detectable rather than silent.
- Anatomy first: docs/07_pipeline_anatomy.md (in progress) inventories every by-hand stage of the mock with code receipts; its by-hand table is the harness component backlog.

## Deliverables, in build order

| # | Ask | Output | Depends on |
|---|-----|--------|------------|
| 0 | Context mining: his records searched for goals, time, constraints he did not restate | `docs/00_design_brief.md` (internal, shapes everything below) | running |
| 1a | KG augmentation of the reading list, ~8-10 items curated from a verified survey | `reading-list.md` updated | running |
| 1b | PDF of every paper in the repo | `papers/` + `papers/MANIFEST.md` | 1a for the new items; existing list fetchable now |
| 2 | One-page summary per paper, marked full-text or abstract-only | `summaries/one-pagers/` | 1b |
| 3 | Reference digest: one paragraph per work, organized by work | `docs/06_digest.md` | 2 |
| 4 | Topic narrative: major topics, approaches traced by work and date | `docs/01_topic_narrative.md` | 2; topic set shown to Justin before final |
| 5 | His proposal as it stood before the research, in his voice, from his record only | `docs/02_proposal_draft.md` (DRAFT until he corrects it) | 0, sealed from 1-4 |
| 6 | Elevation options: itemized approaches from the research, each traced to source and checked against what the system already does | `docs/03_elevation_options.md` | 2, 0 |
| 7 | Three project shapes, with real calls made, against the actual calendar | `docs/04_project_shapes.md` | 0, 6 |
| 8 | End product outline: what to build, test data options, what to record, QA checkpoints for his line-by-line review | `docs/05_end_product.md` | 7 |
| 9 | Master PDF, beautifully formatted, with index | `IT494_Research_Package.pdf` | all |

## Master PDF order (per Justin, 2026-08-25)

1. Cover and index
2. Topic narrative (4)
3. His proposal (5)
4. Elevation options (6)
5. Three project shapes (7)
6. End product and testing outline (8)
7. Reference digest (3), second to last
8. One-page paper summaries (2), last

## Gated on Justin (to resolve when he is back)

- Topic set for the narrative (I derive it from the corpus and show it; he confirms or renames).
- The proposal draft needs his correction pass before it is anything but a draft.
- KG curation: my 8-10 picks are shown with the ~10 next-best listed as "cut, available on request."
- Anything the context mine flags as contradicting what he told me directly.
- Paywalled papers he wants badly enough to pull through the ISU library himself.

## Style standard (all deliverables, per Justin 2026-08-25)

Publishable and human. Concretely: no em dashes; no AI-tell vocabulary or formula phrasing; headers that say something rather than label a category; paragraphs carrying the argument, with lists reserved for genuinely enumerable things; varied sentence rhythm; no emoji, no "in conclusion", no bold-term-colon pattern marching down a page; zero generation stamps or tool attributions in any deliverable. Provenance is disclosed once, plainly, in the package front matter (the professor already knows an LLM assisted), and nowhere else. Every document gets a final read for tells before it ships.

## Tooling notes

- PDF fetching: arXiv and ACL Anthology are deterministic; author-hosted copies used where legitimate; everything logged in `papers/MANIFEST.md` with source URL and fetch status.
- Master PDF: typeset via LaTeX if a distribution is installed, else HTML with print CSS rendered to PDF. Decided at build time, recorded here.
- One-pagers: generated from the actual PDF text wherever the PDF exists; abstract-only summaries are marked as such in their header.
