# TraceMem: Weaving Narrative Memory Schemata from User Conversational Traces
Yiming Shu et al., arXiv:2602.09712, 2026-02

## Abstract (verbatim)

Sustaining long-term interactions remains a bottleneck for Large Language Models (LLMs), as
their limited context windows struggle to manage dialogue histories that extend over time.
Existing memory systems often treat interactions as disjointed snippets, failing to capture the
underlying narrative coherence of the dialogue stream. We propose TraceMem, a cognitively-
inspired framework that weaves structured, narrative memory schemata from user conversational
traces through a three-stage pipeline: (1) Short-term Memory Processing, which employs a
deductive topic segmentation approach to demarcate episode boundaries and extract semantic
representation; (2) Synaptic Memory Consolidation, a process that summarizes episodes into
episodic memories before distilling them alongside semantics into user-specific traces; and (3)
Systems Memory Consolidation, which utilizes two-stage hierarchical clustering to organize these
traces into coherent, time-evolving narrative threads under unifying themes. These threads are
encapsulated into structured user memory cards, forming narrative memory schemata. For memory
utilization, we provide an agentic search mechanism to enhance reasoning process. Evaluation on
the LoCoMo benchmark shows that TraceMem achieves state-of-the-art performance with a brain-
inspired architecture. Analysis shows that by constructing coherent narratives, it surpasses
baselines in multi-hop and temporal reasoning, underscoring its essential role in deep narrative
comprehension. Additionally, we provide an open discussion on memory systems, offering our
perspectives and future outlook on the field. Our code implementation is available at:
https://github.com/YimingShu-teay/TraceMem

## Bearing on this project

**This is the closest published work to the whole design.** Segmentation into episodes, episodic
summaries, distillation into traces, hierarchical clustering into time-evolving narrative
threads, memory cards, agentic search. It occupies the thread idea end to end and is SOTA on
LoCoMo. The one visible difference is that TraceMem CLUSTERS traces into threads, which is a
partition (a trace belongs to one thread), where this project places one unit in N threads at
full weight. That distinction is thin, unverified, and the only thing standing between this
design and being a reimplementation.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
