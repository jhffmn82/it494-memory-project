# Which benchmark, and why

**2026-08-28.**

## Short version

**Infinity-Bench En.MC.** 229 multiple-choice questions over long books, answers public, scored by
exact match, no judge and no API cost. The text ships with it.

**The reason it wins:** its books have had the character names swapped out. "Mrs. Natalie Ernesto"
replaces "Mrs. Rachel Lynde". A model cannot answer from what it memorised in training when the
names have changed, so the score reflects the system rather than the model's reading history.

That matters because contamination is otherwise fatal here: **GPT-4 scores 60.94% on NovelQA
multiple-choice with no book in front of it at all.**

---

## How it gets run

Three arms through one scorer, plus one ablation:

1. **Full system.**
2. **No context.** Random is 25%. This goes in the headline table, not a footnote.
3. **Flat chunk retrieval.** The baseline the design has to beat.
4. **Entity cells switched off.** The one ablation worth running, because it tests the actual design
   decision.

---

## The problem with 229 questions

At around 60% accuracy, one arm has a standard error of about **3 points**. The difference between
two arms needs to be roughly **5 to 9 points** before it is real rather than noise.

Switching off a component usually moves accuracy **2 to 5 points**.

So the ablation may come back showing nothing, not because the component does not matter but because
the test cannot see it. **Check this in October against real arm agreement, before committing to the
run.**

**If more sensitivity is needed:** LiteraryQA has 3,785 questions across 138 Gutenberg books, about
sixteen times as many items. Its metric is free-form text overlap, which is noisier and correlates
poorly with human judgment, so it buys sensitivity at the cost of metric quality. Use Infinity-Bench
for the headline number and LiteraryQA for the ablation difference. Report effect sizes with
confidence intervals either way, rather than claiming significance.

LiteraryQA needs `datasets==3.6.0` pinned. Its licence is stated three different ways across the
paper, the repo and the dataset card; research use is fine, redistribution is unverified.

---

## What no benchmark here can measure

Both are **static**: one book, questions about it, all at once. Neither can touch updating a fact,
adding new material, or recomputing only what changed. Those get measured on cost instead, and need
no answers at all. See `05_fall_plan.md`.

---

## Rejected, and why

**NovelQA.** Looked ideal: 89 novels, multiple choice, a published no-book baseline. But **the
answers are not released.** Scoring goes through a leaderboard submission, so every ablation would
be a round trip through someone else's server. Also 24 of its 89 books are in copyright and will
never be released.

**LitBank.** Withdrawn. 96 of its 100 documents are two chunks long at standard chunk sizes, so the
cross-chunk effects this design is about cannot appear in it. It also has no relation annotations.

**BOOKCOREF.** Book-length and gold, but it annotates only who-refers-to-whom. No questions at all.

**QuALITY.** Documents are about 5,000 words, roughly ten times too short.

---

## One data trap

The HuggingFace copy of NarrativeQA serves 28,668 rows against the 46,765 its own card claims; the
training split is missing more than half. Use the original CSVs if you touch it.
