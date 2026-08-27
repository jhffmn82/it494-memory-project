# EvoTaxo: Building and Evolving Taxonomy from Social Media Streams
Yiyang Li et al., arXiv:2603.19711, 2026-03

## Abstract (verbatim)

Constructing taxonomies from social media corpora is challenging because posts are short, noisy,
semantically entangled, and temporally dynamic. Existing taxonomy induction methods are largely
designed for static corpora and often struggle to balance robustness, scalability, and
sensitivity to evolving discourse. We propose EvoTaxo, a LLM-based framework for building and
evolving taxonomies from temporally ordered social media streams. Rather than clustering raw
posts directly, EvoTaxo converts each post into a structured draft action over the current
taxonomy, accumulates structural evidence over time windows, and consolidates candidate edits
through dual-view clustering that combines semantic similarity with temporal locality. A
refinement-and-arbitration procedure then selects reliable edits before execution, while each
node maintains a concept memory bank to preserve semantic boundaries over time. Experiments on
two Reddit corpora show that EvoTaxo produces more balanced taxonomies than baselines, with
clearer post-to-leaf assignment, better corpus coverage at comparable taxonomy size, and
stronger structural quality. A case study on the Reddit community /r/ICE_Raids further shows
that EvoTaxo captures meaningful temporal shifts in discourse. Our codebase is available here.

## Bearing on this project

Builds and EVOLVES taxonomies from temporally ordered streams, accumulating structural evidence
over time windows with per-node concept memory to preserve semantic boundaries. That is the
living-tree-that-ingests-over-time idea, applied to taxonomy, with results on two Reddit
corpora.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
