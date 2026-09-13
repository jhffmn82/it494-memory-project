# VitaBench 2.0: Evaluating Personalized and Proactive Agents in Long-Term User Interactions
Yuxin Chen et al., arXiv:2605.27141, 2026-05

## Abstract (verbatim)

Large language models (LLMs) have evolved into interactive agents that collaborate with users in
real-world tasks. Effective collaboration in such settings increasingly depends on understanding
the user beyond what is explicitly stated, as user intent is often reflected in fragmented daily
interactions and requires both personalized modeling and proactive interaction. However,
existing agent benchmarks primarily evaluate reasoning and tool use, largely overlooking the
challenges of inferring and leveraging user preferences in realistic scenarios. To address this
gap, we introduce VitaBench 2.0, a benchmark for evaluating personalized and proactive agent
behavior in long-term user interactions. In VitaBench 2.0, tasks are organized as temporally
ordered sequences for individual users, where preferences are embedded in fragmented and
heterogeneous interactions. Successful completion of tasks requires the agent to continuously
extract, utilize, and update user preferences from these interactions. We further evaluate
proactiveness through tasks that require agents to recognize missing information and actively
acquire it from users or environments before making decisions. To support systematic analysis,
we provide an extensible memory interface that enables controlled comparison across different
memory architectures. We benchmark a diverse set of frontier proprietary and open-source LLMs.
Results show that real-world personalization remains highly challenging even for state-of-the-
art models, revealing a substantial gap between current capabilities and practical requirements.
Extensive analysis further reveals the failure modes and capability bottlenecks of current
agents in real-world personalized decision-making, providing insights for future model
improvements.

## Bearing on this project

Evaluating personalized and proactive agents in long-term user interaction. Benchmark, part of
the same cluster.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
