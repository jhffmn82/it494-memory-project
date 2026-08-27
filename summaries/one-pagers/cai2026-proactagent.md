# Ask Only When Needed: Proactive Retrieval from Memory and Skills for Experience-Driven Lifelong Agents
Yuxuan Cai et al., arXiv:2604.20572, 2026-04

## Abstract (verbatim)

Online lifelong learning agents must decide not only how to act but also when to consult prior
experience to continually improve on long-horizon tasks. Existing methods typically retrieve
memories passively, such as at task initialization or after each step, and therefore miss
knowledge gaps that arise during interaction. We propose ProactAgent, an experience-driven
lifelong learning framework for proactive retrieval over a structured Experience Base.
ProactAgent continually improves through ExpOnEvo, which jointly updates policies and refines
memory, organizing past interactions into factual, episodic, and skill repositories. It further
introduces ProactRL, which treats retrieval as an explicit policy action and learns when and
what to retrieve. By comparing paired continuations from identical interaction prefixes with and
without retrieval, ProactRL provides step-level process rewards that encourage retrieval only
when it improves task outcomes or efficiency. Experiments on SciWorld, AlfWorld, and StuLife
show that ProactAgent consistently outperforms all baselines, achieving up to 32% relative
improvement in success rate and over 33% reduction in interaction rounds. Our code will be
publicly available at GitHub.

## Bearing on this project

**Takes the measurement.** Observes that existing methods retrieve passively and therefore miss
knowledge gaps arising during interaction, and learns when to retrieve by comparing paired
continuations from identical prefixes with and without retrieval. That paired counterfactual is
the core of the counterfactual miss rate, expressed as a learned policy rather than a reported
rate.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
