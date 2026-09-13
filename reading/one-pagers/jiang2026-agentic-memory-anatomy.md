# Anatomy of Agentic Memory: Taxonomy and Empirical Analysis of Evaluation and System Limitations
Dongming Jiang et al., arXiv:2602.19320, 2026-02

## Abstract (verbatim)

Agentic memory systems enable large language model (LLM) agents to maintain state across long
interactions, supporting long-horizon reasoning and personalization beyond fixed context
windows. Despite rapid architectural development, the empirical foundations of these systems
remain fragile: existing benchmarks are often underscaled, evaluation metrics are misaligned
with semantic utility, performance varies significantly across backbone models, and system-level
costs are frequently overlooked. This survey presents a structured analysis of agentic memory
from both architectural and system perspectives. We first introduce a concise taxonomy of MAG
systems based on four memory structures. Then, we analyze key pain points limiting current
systems, including benchmark saturation effects, metric validity and judge sensitivity,
backbone-dependent accuracy, and the latency and throughput overhead introduced by memory
maintenance. By connecting the memory structure to empirical limitations, this survey clarifies
why current agentic memory systems often underperform their theoretical promise and outlines
directions for more reliable evaluation and scalable system design.

## Bearing on this project

A survey that names, as known limitations, two things this project was going to contribute:
backbone-dependent accuracy (the stage-wise tier sensitivity) and overlooked system-level cost.
Naming is not measuring, so per-stage measurement may still be open, but the gap can no longer
be presented as unnoticed. Also useful in the other direction: it says the field's empirical
foundations are fragile - underscaled benchmarks, metrics misaligned with semantic utility -
which is the argument for careful measurement being worth more than another architecture.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
