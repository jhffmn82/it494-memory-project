# The evaluation corpus, settled

**2026-08-28.** Which benchmark supplies the gold questions, and why. Searched and verified rather
than assumed; every count below was measured from the distributed files or extracted from the paper,
not taken from a summary.

**The decision: ∞Bench En.MC as primary, LiteraryQA as the Gutenberg-native scale-up. NovelQA is
out.**

---

## Why NovelQA is out

It looked ideal: 89 novels, 2,305 questions, multiple choice scoreable by exact match, and a
published closed-book baseline. It fails on one thing.

**The gold answers are not distributed.** The released JSON carries QID, aspect, complexity,
question and options, and no answer key. Scoring runs through a Codabench leaderboard submission
(competition 2727, verified live). Every ablation run would be a round-trip through someone else's
server, which is unusable for iterative development. Full access requires a request form and the
authors embed a tracking identifier in the data to trace leaks.

Two further traps, recorded so nobody re-opens this: 24 of its 89 books are **copyright-protected
and will never be released** ("we affirm that we will not release these novels"), and some of its
"public domain" books come from Gutenberg Australia or Canada, which are **not public domain in the
US**. Its HuggingFace card also contradicts its own paper on the copyrighted count (28 versus 24).

**The one number worth keeping from it**, verified exactly against Table 6: **GPT-4 scores 60.94%
multichoice closed-book**, with no novel in context, against 71.80% with the book. That is the
contamination problem in one figure, and it is the reason for the primary choice below.

**NovelQA has no verified Oz content.** Apparent matches were substring artifacts from words like
"dozen."

---

## Primary: ∞Bench En.MC

arXiv:2402.13718, ACL 2024.

| Property | Value |
|---|---|
| Questions | **229, gold answers public** |
| Metric | four-way accuracy, exact match, **no judge, no API cost** |
| Context length | ~184k tokens per book |
| Text | **ships with the benchmark** (`longbook_choice_eng.jsonl`), nothing to fetch |
| Random baseline | 25% |

**The decisive property: the books are entity-substituted.** "Mrs. Natalie Ernesto" replaces "Mrs.
Rachel Lynde." A model cannot answer from memorised pretraining when the names have been changed, so
whatever the system scores is attributable to the system rather than to recall of the training set.
This defeats the confound that the 60.94% figure above makes fatal for ordinary public-domain
classics.

License flagged as inconsistent between sources (MIT in one place, an unparsed Apache-2.0 fragment
in the card). Research use is not in question; confirm before redistributing anything derived.

## Scale-up: LiteraryQA

Bonomo, Gioffré and Navigli (Sapienza NLP), **EMNLP 2025**, anthology `2025.emnlp-main.1729`, pages
34086 to 34107, verified HTTP 200. arXiv:2510.13494.

A cleaned, Gutenberg-only subset of NarrativeQA: movies, plays and non-narrative documents removed,
Gutenberg headers and footers stripped, QA pairs corrected by LLM plus human pass.

| Property | Value |
|---|---|
| Test set | **138 documents, 3,785 QA pairs**, down from 355 / 10,557 |
| Gold answers | **fully public**, multiple references per question |
| Length | 74K ± 59K tokens |
| Text | **100% Project Gutenberg**, ships `download_and_clean_books.py` |
| Metrics | EM, F1, ROUGE-L, METEOR, BERTScore, plus Prometheus 2; `evaluate_predictions.py` included |
| Closed-book setting | yes, title only |

**License is contested three ways** and must not be stated as settled: Apache-2.0 in the paper's
Appendix D, CC BY-NC 4.0 on the GitHub badge, CC BY-SA 4.0 in the HuggingFace card YAML. All three
permit research use. **Redistribution is UNVERIFIED**; ask the authors if it matters.

**Gotcha:** it uses a dataset loading script, so `datasets==3.6.0` must be pinned. Newer versions
fail with "Dataset scripts are no longer supported."

---

## Overlap with this project's existing corpora

Measured from NarrativeQA's `documents.csv` and `qaps.csv`. **Neither file is in this repository**,
so this table cannot be regenerated here; it is reported on the authority of the session that
computed it. Recompute and commit the script before relying on it. (Caveat added 2026-08-29.)

| Title | Split | Words | Questions | Gutenberg |
|---|---|---|---|---|
| The Adventures of Sherlock Holmes | valid | 123,921 | 28 | 1661 |
| The Emerald City of Oz | train | 66,486 | **50** | 41667 |
| The Patchwork Girl of Oz | train | 72,412 | 29 | 32094 |
| Dorothy and the Wizard in Oz | train | 69,119 | 30 | 40300 |
| Tik-Tok of Oz | train | 59,869 | 30 | 52176 |
| The Lost Princess of Oz | train | 58,109 | 30 | 24459 |
| The Scarecrow of Oz | train | 57,563 | 30 | 51263 |
| The Tin Woodman of Oz | train | 55,125 | 30 | 30852 |
| The Road to Oz | train | 50,530 | 29 | 26624 |
| The Magic of Oz | train | 49,263 | 30 | 419 |

**Two caveats that matter.** None of these are in LiteraryQA's manually validated **test** set; they
sit in the auto-processed portion. And *The Adventures of Sherlock Holmes* is a **twelve-story
collection, not a novel**, so it exhibits far less cross-chunk structure than 124k words suggests.

Large clean test-split candidates if more length is wanted: Of Human Bondage (301,578 words, PG
351), Villette (234,484, PG 9182), Barchester Towers (228,855, PG 2432), Uncle Silas (204,194, PG
14851), Mary Barton (191,688, 39 questions, PG 2153).

---

## The evaluation

Ingest the 229 En.MC book contexts, then run **three arms through one identical scorer**:

1. **Full system.**
2. **No-context control.** Random is 25%. This is the memory-versus-recall floor and it goes in the
   headline table, not a footnote.
3. **Flat chunk retrieval.** The baseline the components have to beat.

Ablations slot in as additional arms on the same scorer: no salience threshold, no entity cells, no
fact layer. Report **relative deltas between arms** rather than chasing comparability with published
absolutes, because n-gram metrics rank systems poorly (LiteraryQA's own meta-evaluation found most
system-level Kendall's tau below 0.07, with only METEOR reaching moderate correlation, against
0.6881 for a Prometheus 2 7B judge that is out of budget but is open-weight and local if a GPU ever
frees up).

**What this cannot measure**, and it must be said in the write-up: ∞Bench and LiteraryQA are
**static**. One book, questions about it, all at once. Neither can touch supersession, incremental
update, or hash-gated refolding. Those need the read-cost and refold-cost measurements, which
require no gold data at all. Quality comes from the benchmark; the temporal half is measured on
cost.

---

## The Zep comparison: LongMemEval, kept deliberately

Zep is the closest published system to this design, so its numbers are the only ones this work can
be measured against directly. The strategy is asymmetric on purpose: **compete with Zep on its own
metric rather than on ours**, because it never ran on literary corpora and a comparison invented
here would be against a reimplementation rather than against their published result.

**Zep's published LongMemEval numbers:** 63.8% with gpt-4o-mini against a 55.4% full-context
baseline, and 71.2% with gpt-4o against 60.2%.

Two qualifiers that must travel with those figures, both verified against the paper:

- They are **LongMemEval_s**, the small variant, averaging about 115,000 tokens per conversation,
  not the full benchmark.
- **The accuracy is the weaker half of their result.** Zep served those numbers from roughly 1,600
  tokens of context against the baseline's 115,000, with about a tenfold latency reduction.
  Competing on LongMemEval means competing on that frontier. A system that matches Zep's accuracy
  while reading far more context has lost, and the paper should report context size alongside
  accuracy or it is reporting half the comparison.

**A dependency this creates.** LongMemEval is conversational, so the `session` value of `unit_type`
in `04_unit_contract.md` has to actually work. That is real preprocessing effort and it is easy to
overlook because the enum already lists it.

**Do not spend a run on DMR.** Zep's own paper calls the benchmark inadequate: 94.8% against a 94.4%
full-conversation baseline with gpt-4-turbo, and 98.2% against 98.0% on the gpt-4o-mini row, where
each conversation is only 60 messages and "easily fits within current LLM context windows." Cite the
caveat, and cite Table 1 rather than the abstract, since the abstract's headline compares Zep to
MemGPT rather than to full context.

**Note the tension, and state it in the write-up rather than hoping nobody notices.** LongMemEval is
assembled rather than organic (roughly 25% ShareGPT, 25% UltraChat, 50% model self-chat), and this
project's stated reason for preferring novels is that synthetic dialogue has planted structure. Both
things are true. The resolution is that LongMemEval is not being used as a substrate for measuring
the design; it is being used as the one place a head-to-head against the nearest published system is
possible on that system's own terms.

---

## Alternatives considered

| Benchmark | Gold public | Long books | Cheap metric | Verdict |
|---|---|---|---|---|
| **∞Bench En.MC** | yes, 229 | ~184k tok | yes, accuracy | **primary** |
| **LiteraryQA** | yes, 3,785 | 74k avg | F1 / METEOR | **scale-up** |
| MemoryAgentBench EventQA | yes, 500 | ~420k words | yes, accuracy | good, but only 5 books and it reuses ∞Bench texts |
| NovelQA | **no, held out** | 200k+ | would be | **out, see above** |
| QuALITY | train/dev only | **~4.8k words** | yes | roughly 10x too short |
| NoCha | **no, held out** | yes | yes | author-run leaderboard only |
| BOOKCOREF | yes | 200k+ | CoNLL-F1 | **not QA, zero questions** |
| TLDM | **no gold exists** | 40 PG novels | **no, needs GPT-4.1** | authors spent $600 on judging |

---

## Data traps

- **The HuggingFace `deepmind/narrativeqa` mirror serves 28,668 rows against the 46,765 its own card
  declares.** Test and validation match the official CSVs exactly; **train is short by more than
  half** (14,650 versus 32,747). Use the DeepMind CSVs as truth.
- Gutenberg Australia and Canada sourced books are not public domain in the US.
- Verify licenses before redistributing anything derived. Three of the datasets here carry
  conflicting license statements across paper, repo and card.
