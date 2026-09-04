# IT 494: a memory backend for a desktop assistant

The end state is a backend that bolts onto a desktop AI client. It ingests what
a person accumulates, chat logs above all, builds a knowledge graph of entities,
dated facts, and per-entity narratives, and feeds that structure to the client
as RAG context. The first intended user is the author's own desktop assistant.

Fall 2026 builds and tests the
methodology: the schema, entity reconciliation, and per-entity narrative
distillation, measured well enough to publish. Spring 2027 wraps the proven
methodology in the desktop product and points it at real chat logs.

## Why literature comes first

You cannot publish measurements taken on a private life. So the fall runs on
four public-domain literature corpora, on one hypothesis: works of fiction fed
in narrative order behave like a life recorded in chat. Characters accumulate
aliases, facts get superseded, threads interleave, and what is true depends on
when you ask. Tip becoming Ozma at the end of the second Oz book is the same
event, structurally, as a course pivoting or an internship ending. Literature
supplies these dynamics with ground truth attached and no privacy cost.

The corpora live in `data/raw/` with their own documentation: Oz for the
supersession fixture, Holmes for contradiction and a contamination probe, Greek
myth for cross-source disagreement and free entity-resolution labels, the
Chinese classics for measuring OCR and translation error.

## The visible artifact

From the ingested corpora we assemble a wiki. Pages are composed mechanically
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
| SQLite and FTS5 | corpus loaders and the split gates | 9 published GraphRAG-Bench baselines, gpt-4o-mini |
| an embedding model for candidate lookup | resolution by name, co-occurrence, and profile | full-context and flat-retrieval arms |
| GraphRAG-Bench, LongMemEval, NarrativeQA | fact extraction behind the quote gate | Zep's LongMemEval numbers, parity arm first |
| Gutenberg texts | narrative cells and summary folding | MemTree's published refold costs |
| hierarchical summaries (GraphRAG, RAPTOR), dated facts (Zep), per-character summaries (EntSUM) | the assembled wiki renderer | NarrativeQA reference answers on 12 owned works |

The schema is in `SCHEMA.md`, the pipeline rules in `BUILD.md`, and the claim,
prior art, and measurement plan in `RESEARCH.md`.

## How to read this repository

`SCHEMA.md` and `BUILD.md` are the consolidated design and are edited only when a decision is
settled. Dated folders under `log/` are working notes from design sessions and experiment runs;
they are provisional, may propose alternatives that contradict the consolidated documents, and
mark such proposals as PROPOSED until ruled on. Executable prototypes live in linked Kaggle
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
| Sep 14 | All four corpora split and gated; dataset published. Oz, Holmes, and Greek landed Sep 1 (kaggle.com/datasets/jhffmn/it494-narrative-corpora-units); Chinese remains |
| Sep 21 | Store and pipeline working over Oz book 1 |
| Sep 27 | Three-tier pilot done; open block ends |
| Oct 19-26 | GraphRAG-Bench arms and the ablation; NarrativeQA arm; LongMemEval parity and update band |
| Nov 10 | Dataset DOI minted |
| Nov 15 | Paper frozen; wiki demo standing; arXiv submission the next day |

Hours are the scarce resource, and the author writes the code; AI drafts and
argues but ships nothing unexamined.

## The bill, priced now

The two open blocks hold roughly 64 hours at eight a week, and the
8-hours-a-week assumption is itself unverified against a real week. The
slate, priced:

| Work | Hours |
|---|---|
| Splitting, gates, dataset publish | 8-12 |
| Store, ingest, organize, maintain | 20-40 |
| Hand-labeled alias set | 1 |
| GraphRAG-Bench: three arms, scorer wiring, plain-RAG parity check | 8-12 |
| Resolution ablation, replayed from logged scores | 2-3 |
| Cost curves: read, refold, coverage | 3-5 |
| OCR control | 2-3 |
| Translation control, including the machine translation run | 3-6 |
| NarrativeQA evaluator and arms | 3-5 |
| Wiki: the Tip and Ozma page, the Holmes page, the ship checks | 4-8 |
| Cells ablation | 2 |
| LongMemEval loader, parity arm, update band | 8-15 |
| Paper writing | 10-15 |

That sums to 74 to 127 against 64, so the cut order is decided now, not in
November, and a lost week deletes from the bottom:

1. Protected: splitting, the store, the alias set, the GraphRAG-Bench arms
   with their parity check, the resolution ablation, the instruments, the
   cost curves, the OCR control, the two wiki pages, and the paper.
2. First cut: the LongMemEval stretch item.
3. Then: the cells ablation.
4. Then: the wiki beyond its two showpiece pages.
5. Then: NarrativeQA.
6. Last cut before touching the protected core: the translation control. The
   OCR control stays, because it is cheaper and carries the same argument.

## Repo map

    README.md                this plan
    SCHEMA.md                the record types and their rules
    BUILD.md                 how the pipeline code behaves
    RESEARCH.md              framing, prior art, measurements, open items
    docs/proposal.md         the three-page project explanation
    docs/evaluation-corpus.md  every dataset and what the build owes it
    docs/entity-resolution.md  the resolution design and its guards
    docs/references.md       sources behind the schema decisions
    docs/digest.md           one verified paragraph per reference work
    docs/related-work/       drafted related-work prose, by theme
    docs/*.json              survey bibliography, with citation corrections
    advisor-meeting-2026-08-19.md  the meeting record that set the direction
    build/                   the delivered research package and proposal
    data/raw/                the four corpora and their manifests
    data/benchmarks/         GraphRAG-Bench, LongMemEval, NarrativeQA subset
    papers/                  the reference library, indexed by MANIFEST.md
    summaries/               one-pagers for the reference library
    reading-list.md          what to read and in what order
    scripts/                 corpus, paper, and benchmark fetchers
