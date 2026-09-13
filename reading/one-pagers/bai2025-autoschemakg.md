# AutoSchemaKG: Autonomous Knowledge Graph Construction through Dynamic Schema Induction from Web-Scale Corpora
Jiaxin Bai et al., arXiv:2505.23628, 2025-05

## Abstract (verbatim)

We present AutoSchemaKG, a framework for fully autonomous knowledge graph construction that
eliminates the need for predefined schemas. Our system leverages large language models to
simultaneously extract knowledge triples and induce comprehensive schemas directly from text,
modeling both entities and events while employing conceptualization to organize instances into
semantic categories. Processing over 50 million documents, we construct ATLAS (Automated Triple
Linking And Schema induction), a family of knowledge graphs with 900+ million nodes and 5.9
billion edges. This approach outperforms state-of-the-art baselines on multi-hop QA tasks and
enhances LLM factuality. Notably, our schema induction achieves 92\% semantic alignment with
human-crafted schemas with zero manual intervention, demonstrating that billion-scale knowledge
graphs with dynamically induced schemas can effectively complement parametric knowledge in large
language models.

## Bearing on this project

**The schema-induction scoop.** Fully autonomous knowledge graph construction with no predefined
schema, inducing schemas directly from text while extracting triples. 50M documents, 900M nodes,
and 92 percent semantic alignment with human-crafted schemas at zero manual intervention. That
is cold-start structure induction, at web scale, with a number.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
