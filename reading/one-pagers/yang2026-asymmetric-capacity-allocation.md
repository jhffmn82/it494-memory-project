# Asymmetric Capacity Allocation in Self-Refinement Pipelines
Zhuoyi Yang et al., arXiv:2608.21345, 2026-08

## Abstract (verbatim)

Self-refinement, typically structured as generation, critique, and revision, is a widely adopted
paradigm for improving LLM generation and serves as a core mechanism in many LLM agents. While
the three stages involve different cognitive demands, most existing approaches conveniently
treat the model size as an implementation detail rather than a subject of study, which may lead
to a waste of resources. Little work has systematically examined how model size affects each
stage or whether effective self-refinement requires equally capable models for generation,
critique, and revision. We present the first stage-wise model size study of the self-refinement
pipeline on 5 benchmarks from different domains using 6 model sizes of Qwen3 and 4 model sizes
of Gemma 3. We conclude that larger generators and refiners generally improve the pipeline,
whereas an undersized refiner can even harm performance. Second, performance is highly
insensitive to the size of the critic, although including even a small critic consistently
outperforms omitting critique altogether. Our findings demonstrate that model capacity should
not be allocated uniformly across self-refinement pipelines. Instead, different stages exhibit
distinct size scaling characteristics, providing practical guidance for designing more
computationally efficient multi-stage language model systems.

## Bearing on this project

Kills the per-stage tier angle. Allocating model capacity asymmetrically across pipeline stages
is the question this project's sensitivity table was going to answer. Published this month.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
