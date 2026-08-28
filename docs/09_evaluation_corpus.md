# Which benchmark, and why

**2026-08-28.** Both are downloaded, verified and in the repo.

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

**The argument comes from their own numbers.** Best accuracy costs 1,008 tokens; the most expensive
system costs 331,375, a 377x spread. Landing near the top of the accuracy column at the bottom of
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
- **BOOKCOREF.** Coreference only, no questions.

## Reproducing

```bash
python scripts/fetch_benchmarks.py         # GraphRAG-Bench + LongMemEval oracle
python scripts/fetch_benchmarks.py --all   # adds longmemeval_s, 278 MB
```

Hashes in `data/benchmarks/manifest.json`.
