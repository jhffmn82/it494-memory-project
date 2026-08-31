# The datasets, and what each demands of the build

**2026-08-28, amended 2026-08-30.** Three are downloaded and verified. This is the list every build step gets checked
against: if a stage cannot serve a row here, it is not done.

## The handle

| Dataset | Status | What it tests | What the build must support |
|---|---|---|---|
| **GraphRAG-Bench** novels | in repo, verified | QA accuracy against 9 published baselines, token cost, the cells ablation, resolution arms downstream | plain-text loader, splitting per the unit contract, the retrieval and answer path |
| **Hand-labelled aliases**, one novel | **does not exist. Build first** | merge precision and recall from the very first ingest | nothing special; it is the day-one smoke test |
| **Our 81-work corpus** | in repo | the fixtures: Tip becoming Ozma, Watson's wound, the deerstalker, Helen and Troy, clean text against OCR | supersession, `rank: deprecated`, the quote gate |
| **BookCoref** | **not fetched** | coreference F1 against published numbers on full books | `Mention.span`, a character offset into the source, plus a CoNLL scorer |
| **CORE-KG's pipeline** on our corpus | not attempted | duplication rate head to head, same corpus and model | their code, GraphRAG 0.3.2, their seven prompts retyped for narrative |
| **LongMemEval** | oracle in repo, `_s` on demand | Zep parity, 78 knowledge-update questions, 133 temporal-reasoning | chat loader, `Document.occurred_at` populated, speaker recoverable from unit text |
| **NarrativeQA subset** | in repo, verified | QA over 12 works we already hold, 345 questions with reference answers | nothing beyond the GraphRAG-Bench paths; same three arms |
| **The personal archive** | in another repo | nothing. Design rationale only, never evidence | not an input |

## What that implies for the code

Read this column-first. Each row is a build requirement that more than one dataset depends on, which
is why none of them can be deferred to an evaluation phase.

| Requirement | Needed by | Cost if deferred |
|---|---|---|
| `Mention` with a character span | BookCoref, duplicate counting, cluster purity | full re-ingest |
| `Document.occurred_at` | LongMemEval temporal and knowledge-update | a batch ingest flattens a year of chat into one timestamp |
| Per-signal candidate scores, rejects included | every resolution arm, merge precision | one full ingest per arm instead of a replay |
| Node lineage, mentions to node | duplicate rate, cluster purity | cannot be reconstructed after merging |
| Per-stage call and token counts by tier | the cost result, requirement 6 | re-run everything |
| Loader and evaluator as the only dataset-aware code | all six | dataset logic leaks into the pipeline and every new set touches the middle |

**The order this forces.** The alias set and the fixtures run against the first working ingest. The
GraphRAG-Bench numbers come next because everything else is scoped by whether the QA path works at
all. BookCoref and the CORE-KG run are additive and can slip. LongMemEval is spring, and it is the
only one needing a loader shape we have not built.

---

## Primary: GraphRAG-Bench, novel split

ICLR 2026, **MIT licensed**, `github.com/GraphRAG-Bench/GraphRAG-Benchmark`. In
`data/benchmarks/graphrag-bench/`.

| | |
|---|---|
| Corpus | **20 public-domain novels, 839,608 words**, pre-1900, picked to minimise pretraining contamination |
| Questions | **2,010**, every one with a gold answer and gold evidence |
| Question types | Fact Retrieval 971, Complex Reasoning 610, Contextual Summarize 362, Creative Generation 67 |
| Fields | `id, source, question, answer, question_type, evidence, evidence_triple` |
| Metrics | ACC, ROUGE-L, Evidence Recall, Context Relevance, average tokens |
| Scorers | Provided: `generation_eval.py`, `retrieval_eval.py`, `indexing_eval.py` |

**Why this one.** Nine systems already published on it **using GPT-4o-mini**, so our numbers go
straight into their table. We cite; we re-run nothing of theirs.

| System | Fact retrieval | Complex reasoning | Contextual summarize | Avg tokens |
|---|---|---|---|---|
| RAG (no rerank) | 58.76 | 41.35 | 50.08 | **879** |
| RAG (rerank) | 60.92 | 42.93 | 51.30 | |
| **HippoRAG2** | 60.14 | **53.38** | 64.10 | **1,008** |
| RAPTOR | 49.25 | 38.59 | 47.10 | 3,441 |
| Fast-GraphRAG | 56.95 | 48.55 | 56.41 | 4,204 |
| HippoRAG | 52.93 | 38.52 | 48.70 | 7,208 |
| MS-GraphRAG (local) | 49.29 | 50.93 | **64.40** | 38,707 |
| LightRAG | 58.62 | 49.07 | 48.85 | 100,832 |
| MS-GraphRAG (global) | | | | **331,375** |

**The argument comes from their own numbers.** The cheapest system spends 879
tokens per question, the strongest graph system 1,008, and the most expensive
331,375, a 377-fold spread. Landing near the top of the accuracy column at the bottom of
the cost column, with no graph database and no server, is the finding.

**Where the cells should pay:** graph methods beat plain RAG on Complex Reasoning and Contextual
Summarize, not on Fact Retrieval. The benchmark separates those, so the ablation has a built-in
target rather than an invented one.

**Statistical power:** at n=2,010 a difference of about 2.4 points is detectable. Ablations move 2
to 5. At ∞Bench's 229 questions we would have needed 7 points and measured nothing, which is why
that benchmark was dropped.

## Second: LongMemEval

ICLR 2025, **MIT**, `github.com/xiaowu0162/LongMemEval`, HuggingFace `xiaowu0162/longmemeval`.

| | |
|---|---|
| Questions | **500**, gold answers, gold answer-session ids |
| Types | temporal-reasoning 133, multi-session 133, **knowledge-update 78**, single-session-user 70, single-session-assistant 56, single-session-preference 30 |
| Splits | `oracle` 15 MB (committed), `_s` 278 MB (fetch on demand), `_m` 2.7 GB (not used) |

**Why.** Zep published on `_s`: 63.8% with gpt-4o-mini against a 55.4% full-context baseline. It is
the parity check against the system this reimplements. And its **78 knowledge-update questions test
supersession directly**, which GraphRAG-Bench cannot: that one is static QA over novels.

**Run the full-context arm first.** If it reproduces their 55.4%, our harness matches theirs and our
number is comparable to their 63.8%. If it does not, we cannot claim parity, and that is worth
knowing before claiming it. Cost is about $9 on gpt-4o-mini.

## Fixtures, from our own corpora

Pass/fail, no benchmark needed, testing what neither benchmark reaches.

- **Tip becomes Ozma**, end of Oz book 2. Both supersession mechanisms in one case.
- **Watson's wound**, shoulder in one book and leg in another. A contradiction that must survive.
- **The deerstalker.** Doyle never wrote it, so no fact row exists, so the composed path
  structurally cannot say it. The generated path might. A leakage detector.
- **Helen and Troy**, Homer against Euripides.

## Rejected

- **NovelQA.** Gold answers held out behind a Codabench leaderboard.
- **∞Bench En.MC.** 229 questions is underpowered, and no comparable system published on it.
- **LitBank.** 96 of 100 documents are two chunks long.

## Reproducing

```bash
python scripts/fetch_benchmarks.py         # GraphRAG-Bench + LongMemEval oracle
python scripts/fetch_benchmarks.py --all   # adds longmemeval_s and _s_cleaned (278 MB each) and the full NarrativeQA csvs
```

Hashes in `data/benchmarks/manifest.json`.
