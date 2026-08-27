# HERCULES: Hierarchical Embedding-based Recursive Clustering Using LLMs for Efficient Summarization
Gabor Petnehazi et al., arXiv:2506.19992, 2025-06

## Abstract (verbatim)

The explosive growth of complex datasets across various modalities necessitates advanced
analytical tools that not only group data effectively but also provide human-understandable
insights into the discovered structures. We introduce HERCULES (Hierarchical Embedding-based
Recursive Clustering Using LLMs for Efficient Summarization), a novel algorithm and Python
package designed for hierarchical k-means clustering of diverse data types, including text,
images, and numeric data (processed one modality per run). HERCULES constructs a cluster
hierarchy by recursively applying k-means clustering, starting from individual data points at
level 0. A key innovation is its deep integration of Large Language Models (LLMs) to generate
semantically rich titles and descriptions for clusters at each level of the hierarchy,
significantly enhancing interpretability. The algorithm supports two main representation modes:
`direct' mode, which clusters based on original data embeddings or scaled numeric features, and
`description' mode, which clusters based on embeddings derived from LLM-generated summaries.
Users can provide a `topic\_seed' to guide LLM-generated summaries towards specific themes. An
interactive visualization tool facilitates thorough analysis and understanding of the clustering
results. We demonstrate HERCULES's capabilities and discuss its potential for extracting
meaningful, hierarchical knowledge from complex datasets.

## Bearing on this project

Hierarchical embedding-based recursive clustering with LLM summarization. Uses recursive
k-means, i.e. HARD assignment - one item, one cluster. Part of the evidence that the
hierarchical-summary line partitions by default, which is what makes the covering question worth
asking.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
