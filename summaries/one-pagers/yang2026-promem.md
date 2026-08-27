# Beyond Static Summarization: Proactive Memory Extraction for LLM Agents
Chengyuan Yang et al., arXiv:2601.04463, 2026-01

## Abstract (verbatim)

Memory management is vital for LLM agents to handle long-term interaction and personalization.
Most research focuses on how to organize and use memory summary, but often overlooks the initial
memory extraction stage. In this paper, we argue that existing summary-based methods have two
major limitations based on the recurrent processing theory. First, summarization is "ahead-of-
time", acting as a blind "feed-forward" process that misses important details because it doesn't
know future tasks. Second, extraction is usually "one-off", lacking a feedback loop to verify
facts, which leads to the accumulation of information loss. To address these issues, we propose
proactive memory extraction (namely ProMem). Unlike static summarization, ProMem treats
extraction as an iterative cognitive process. We introduce a recurrent feedback loop where the
agent uses self-questioning to actively probe the dialogue history. This mechanism allows the
agent to recover missing information and correct errors. Our ProMem significantly improves the
completeness of the extracted memory and QA accuracy. It also achieves a superior trade-off
between extraction quality and token cost.

## Bearing on this project

Proactive memory EXTRACTION rather than recall - an iterative self-questioning loop that probes
dialogue history to recover missed detail. Different axis from proactive retrieval; relevant to
the distiller stage.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
