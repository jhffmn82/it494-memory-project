# Remember When It Matters: Proactive Memory Agent for Long-Horizon Agents
Yifan Wu et al., arXiv:2607.08716, 2026-07

## Abstract (verbatim)

In long-horizon tasks, decision-relevant state is often scattered across an expanding
trajectory, while the action agent must surface it and act. As trajectories grow, task
requirements, environment facts, prior attempts, diagnoses, and open subgoals can be buried in
the context window or pushed beyond it, failing to influence decisions when needed. We call this
failure mode "behavioral state decay". We study memory as an active intervention mechanism
rather than passive retrieval. A separate memory agent runs alongside an unmodified action
agent, updating a structured memory bank from the recent trajectory and deciding whether to
inject a memory-grounded reminder or remain silent. The module is plug-and-play with frontier
action agents and existing agent harnesses. Across Terminal-Bench 2.0 and $τ^2$-Bench, it
improves pass@1 for both weaker and stronger action agents, with gains of +8.3 pp on Terminal-
Bench and +6.8 pp on $τ^2$-Bench. Ablations show that selective intervention outperforms passive
bank exposure, always-on injection, advisor-only guidance, and general retrieval. As an early
step toward open-weight memory policies, we train Qwen3.5-27B on SETA using SFT and GRPO,
improving validation reward and achieving partial transfer to Terminal-Bench.

## Bearing on this project

Already known from the 08-19 dossier, where it was recorded as naming the adjacent failure
(behavioral state decay) but only intra-task. Its horizon is within a task; this project's is
cross-session over years.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
