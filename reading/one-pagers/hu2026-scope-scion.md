# SCOPE and SCION: A Benchmark and an Auditable Reference Pipeline for Schema Induction and Fusion from Text
Miaobo Hu et al., arXiv:2607.21610, 2026-05

## Abstract (verbatim)

Schema graphs are an upstream bottleneck of schema-grounded information extraction and knowledge
graph construction, yet most extraction systems assume the schema is already available. We
introduce SCOPE (Schema Construction and Ontology-induction Pipeline Evaluation), a train-text-
only benchmark for corpus-to-schema induction and optional schema fusion from raw text, built
from 24 public information extraction sources (15 RE and 9 EE) normalized into evaluation-only
gold schema graphs; its core event-extraction target covers event types and within-event
argument roles, with inter-event links reported separately. We present SCION (Schema
Construction and Induction with Ontology Normalization), an auditable reference pipeline rather
than a new extraction architecture; it constructs candidate spaces from train text and restricts
naming, merging, filtering, validation, and conservative fusion to candidate-linked evidence
under strict JSON contracts. On the SCOPE core suite, SCION-lite attains the highest F1 among
released source-schema references, Text2Onto-style, LLM-only, and matched extract-then-aggregate
baselines under Literal, Fuzzy, Continuous, and Graph schema-graph metrics, while the compact
open-model SCION-RL variant reduces reliance on proprietary LLM schema engineers. These results
are reported against normalized typed-edge targets rather than as claims that induced schemas
surpass human ontology design; the release includes evidence-linked outputs, parse/fallback
logs, candidate retention/merging logs, run manifests, code, and benchmark packages at
https://github.com/wandugu/paper_scion.

## Bearing on this project

A benchmark AND an auditable reference pipeline for corpus-to-schema induction. So schema
induction is not only solved but measured, with released baselines to beat.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
