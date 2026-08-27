# Towards Comprehensive Stage-wise Benchmarking of Large Language Models in Fact-Checking
Hongzhan Lin et al., arXiv:2601.02669, 2026-01

## Abstract (verbatim)

Large Language Models (LLMs) are increasingly deployed in real-world fact-checking systems, yet
existing evaluations focus predominantly on claim verification and overlook the broader fact-
checking workflow, including claim extraction and evidence retrieval. This narrow focus prevents
current benchmarks from revealing systematic reasoning failures, factual blind spots, and
robustness limitations of modern LLMs. To bridge this gap, we present FactArena, a fully
automated arena-style evaluation framework that conducts comprehensive, stage-wise benchmarking
of LLMs across the complete fact-checking pipeline. FactArena integrates three key components:
(i) an LLM-driven fact-checking process that standardizes claim decomposition, evidence
retrieval via tool-augmented interactions, and justification-based verdict prediction; (ii) an
arena-styled judgment mechanism guided by consolidated reference guidelines to ensure unbiased
and consistent pairwise comparisons across heterogeneous judge agents; and (iii) an arena-driven
claim-evolution module that adaptively generates more challenging and semantically controlled
claims to probe LLMs' factual robustness beyond fixed seed data. Across 16 state-of-the-art LLMs
spanning seven model families, FactArena produces stable and interpretable rankings. Our
analyses further reveal significant discrepancies between static claim-verification accuracy and
end-to-end fact-checking competence, highlighting the necessity of holistic evaluation. The
proposed framework offers a scalable and trustworthy paradigm for diagnosing LLMs' factual
reasoning, guiding future model development, and advancing the reliable deployment of LLMs in
safety-critical fact-checking applications.

## Bearing on this project

Stage-wise benchmarking of LLMs, adjacent to the per-stage sensitivity idea. Worth a full read
before claiming anything about which pipeline stage needs which tier.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
