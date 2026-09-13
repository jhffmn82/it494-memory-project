# IT 494: a memory backend for a desktop assistant

The end state, ThreadAtlas, is a backend that bolts onto a desktop AI client. It ingests what
a person accumulates, chat logs above all, builds a knowledge graph of entities,
dated facts, and per-entity narratives, and feeds that structure to the client
as RAG context. The first intended user is the author's own desktop assistant.

Fall 2026 builds and tests the
methodology: the schema, entity reconciliation, and per-entity narrative
distillation, measured well enough to publish. Spring 2027 wraps the proven
methodology in the desktop product and points it at real chat logs.

## Why literature comes first

You cannot publish measurements taken on a private life. So the fall runs on
public text (three public-domain literature corpora, the 20 GraphRAG-Bench
novels, 100 CC-BY papers, and the LongMemEval chat sessions), on one hypothesis: works of fiction fed
in narrative order behave like a life recorded in chat. Characters accumulate
aliases, facts get superseded, threads interleave, and what is true depends on
when you ask. Tip becoming Ozma at the end of the second Oz book is the same
event, structurally, as a course pivoting or an internship ending. Literature
supplies these dynamics with ground truth attached and no privacy cost.

The corpora live in `data/raw/` with their own documentation: Oz for the
supersession fixture, Holmes for contradiction and a contamination probe, Greek
myth for cross-source disagreement and free entity-resolution labels.

## The visible artifact

From the ingested corpora we will assemble a wiki: this fall, pages over document clusters rendered from the store; the full assembled-versus-generated pair in spring. Pages are composed mechanically
from the store: the infobox from fact rows, the lead from the entity summary,
the biography from narrative cells, every claim traceable to a verbatim quote.
A second version is then written by a strong model doing RAG over the same
store. The assembled pages cannot contain anything the text never said; the
generated pages can, and the difference between the two renders is our
fabrication instrument. Doyle never gave Holmes a deerstalker, so if one shows
up, we caught the model's weights leaking into the record.

## Borrow, build, measure

| Borrowed | Built here | Measured against |
|---|---|---|
| SQLite and FTS5 | the extractor and its gates; the ingestor and its quote gate | 9 published GraphRAG-Bench baselines, one reader model for every arm |
| a small local embedding model (bge-small through fastembed) | the global layer: silent parents over document-local entities, attached on name and co-occurrence | attachment accuracy against the Oz alias set, name-only versus name plus co-occurrence; the parent join off, on LongMemEval |
| GraphRAG-Bench, LongMemEval, each with its own published evaluator | the store, the embedding sidecar, the query path, the harness | full-context and flat-retrieval arms; Zep's LongMemEval numbers, parity arm first |
| hierarchical summaries (GraphRAG, RAPTOR), dated facts (Zep), per-character summaries (EntSUM) | narrative cells and summary folding, for books and papers | the instruments: quote-gate and rejection rates, cost per stage and tier, duplicate parents |

Also in the fall, after the numbers: wiki pages over document clusters drawn from the
document-entity graph, rendered from the store (an afternoon). Deferred to spring:
NarrativeQA, the cells ablation, the three-tier model-sensitivity pilot, maintenance
(re-ingest, refold, delete), deployment and a living stream of data.

The schema is in `SCHEMA.md`, the pipeline rules in `BUILD.md`, and the claim,
prior art, and measurement plan in `RESEARCH.md`.

## How to read this repository

`SCHEMA.md` and `BUILD.md` are the consolidated design and are edited only when a decision is
settled. Dated folders under `log/` are working notes from design sessions and experiment runs;
they are provisional, may propose alternatives that contradict the consolidated documents, and
mark such proposals as PROPOSED until ruled on. The same applies to any defect, fix, or rule that
originates from an assistant or an outside review rather than from the author: it is PROPOSED,
with the design principle it rests on stated in one sentence, until the author rules. Executable prototypes live in linked Kaggle
notebooks whose code and saved outputs are copied into the matching `log/` folder; accepted
findings are folded back into `SCHEMA.md` and `BUILD.md` periodically. `log/README.md` is the
index of sessions and notebooks.

## Fall calendar

Dr. Fang approved the topic change in person on August 28. Two open blocks
carry everything: now to September 27, and October 19 to November 15. The
stretch between them is three weeks of exams and nothing gets scheduled there.

| Date | Done means |
|---|---|
| Sep 1 | Repo public; endorsement email to Dr. Fang sent |
| Sep 2 | One chapter of Oz book 1 ingested end to end for Dr. Fang: split, cast, entities, facts, summary, rendered graph |
| Sep 8 | One-semester proposal form filed |
| Sep 14 | All four corpora split and gated; dataset published. Oz, Holmes, and Greek landed Sep 1 (kaggle.com/datasets/jhffmn/it494-narrative-corpora-units, since superseded); Chinese remains. Superseded Sep 4: one general extractor over one raw dataset holding every source (Oz, Holmes, Greek, GraphRAG-Bench, LongMemEval sessions, paper PDFs), documents carrying their text and units as ranges; see `log/2026-09-04/`. Done Sep 13: extractor 1.8 over the whole raw dataset, 24,071 documents (23,882 chats in 500 LongMemEval histories, 89 texts, 100 PDFs) for $8.24, published at kaggle.com/datasets/jhffmn/it494-threadatlas-step0 |
| Sep 20 | The global layer (first cut), the store to the schema it decides, and the embedding sidecar exist over the test packages (71 chat sessions, three Oz books, five papers, two plays); the schema written down |
| Sep 27 | The design lock: the harness runs a question end to end through store, parents, vectors and query on a novel and a chat history; testing begins; open block ends |
| Sep 28 to Oct 18 | Exams. The pipeline tuned on the test packages until ready; only then the full corpus through the ingestor in Kaggle batches, unattended, while the paper is written. Oct 11: results-independent sections drafted. **Oct 15: first draft of the paper**, with whatever numbers exist. Oct 18: GraphRAG-Bench scored on all 20 novels |
| Oct 25 | Build stop: both benchmark numbers exist, each with its denominator; the wiki pages over document clusters |
| Oct 30 | The paper complete in ECIR format; the dataset DOI minted |
| Nov 2 | Submitted to the ECIR 2027 resource track; arXiv preprint the next day; Dr. Fang gets the submitted paper |
| Dec 7 | ECIR decision; if rejected, an EACL 2027 workshop by Dec 15, PVLDB by Jan 1 |

The plan behind this calendar, with the build order, the gates, the rulings it needs and the
feasibility tracker, is `docs/execution-plan.md` (ruled 2026-09-13).

Hours are the scarce resource. The author directs, reviews and answers for the
code, which is drafted with AI assistance under his rulings and checked by a
test battery; nothing ships unexamined.

## The bill, priced 2026-09-13

Done and measured: the extractor ($8.24 over the whole corpus) and the ingestor
(a chat session under half a cent on the frozen version, less on the current
one; the ten test books and papers about $5). Remaining, priced in
`docs/execution-plan.md`:

| Work | Hours |
|---|---|
| The global layer: the design note, then the first cut | 8-12 |
| The store, to the schema the global layer decides | 6-10 |
| The embedding sidecar | 3-5 |
| The query path | 8-10 |
| The two harnesses (each benchmark's own evaluator) | 12-18 |
| Kaggle changes before the full run (output shape, block budget) | 2-4 |
| Scale, bands, instruments, tables | 6-8 |
| Debugging and Kaggle friction | 6-8 |
| The paper: first draft mid-October, second draft Nov 3 | 10-15 |

The design lock (the first four rows) must land by September 27. The plan
prices at eight hours a week and re-prices after the first week's real hours;
the repository's own record says the real pace is well above eight. The cut
order, if a week is lost: the LongMemEval bands, then the parent-off arm, then
the second benchmark's scale; the design lock, one benchmark number, the
instruments and the paper are never cut. Money is not a constraint: the whole
fall is under $300.

## Repo map

The tree holds what a person reads: the plan by stage, the rulings, the logs, the datasets, the
notebooks. Working tooling (test batteries, build scripts, the reference PDFs) stays on the
author's machine, untracked.

    README.md                this plan
    SCHEMA.md                the record types and their rules
    BUILD.md                 how the pipeline code behaves
    RESEARCH.md              framing, prior art, measurements, open items
    docs/rulings.md          every design ruling, its date, its log, and what superseded it
    docs/execution-plan.md   the slate, the build order, the calendar to the paper, the feasibility tracker
    docs/proposal.md         the three-page project explanation
    docs/extractor.md        Step 0 algorithm and data contract
    docs/ingestor.md         Step 1 algorithm and package contract
    docs/evaluation-corpus.md  every dataset and what the build owes it
    docs/entity-resolution.md  the resolution design, its guards, and the tree
    docs/references.md       sources behind the schema decisions
    notebooks/               the extractor and ingestor, as script and notebook, as they run on Kaggle
    dataset/step0/           the published Step 0 dataset's docs, as published, with the 09-13 corrections pending republish
    data/raw/                the raw corpora (three literature corpora, GraphRAG-Bench novels, kg-rag-cc papers, LongMemEval) and their manifests
    data/benchmarks/         GraphRAG-Bench, LongMemEval, NarrativeQA gold files
    scripts/                 the fetchers and unpackers that built the raw dataset, the Step 0 packer, the package renderer
    reading/                 the reading list, one-pagers, the digest, related-work drafts, the advisor meeting record
    reports/                 the weekly reports to the advisor
    log/                     dated working log: one folder per day, notebooks as run, receipts
