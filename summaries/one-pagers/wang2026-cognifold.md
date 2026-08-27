# CogniFold: Always-On Proactive Memory via Cognitive Folding
Suli Wang et al., arXiv:2605.13438, 2026-05

## Abstract (verbatim)

Existing agent memory remains predominantly reactive and retrieval-based, lacking the capacity
to autonomously organize experience into persistent cognitive structure. Toward genuinely
autonomous agents, we introduce CogniFold, a brain-inspired "always-on" agent memory designed
for the next generation of proactive assistants. CogniFold continuously folds fragmented event
streams into self-emerging cognitive structures, bootstrapping progressively higher-level
cognition from incoming events and accumulated knowledge. We ground this by extending
Complementary Learning Systems (CLS) theory from two layers (hippocampus, neocortex) to three,
adding a prefrontal intent layer. Emulating the prefrontal cortex as the locus of intentional
control and decision-making, CogniFold achieves this through graph-topology self-organization:
cognitive structures proactively assemble under the stream, merge when semantically similar,
decay when stale, relink through associative recall, and surface intents when concept-cluster
density crosses a threshold. We evaluate structural formation using CogEval-Bench, demonstrating
that CogniFold uniquely produces memory structures that match cognitive expectations and concept
emergence. Furthermore, across eight downstream benchmarks -- two probing long-term
conversational memory (LoCoMo, LongMemEval) and six spanning other cognitive domains -- we
validate that CogniFold simultaneously performs robustly on conventional memory tasks. Our code
is available at https://github.com/OpenNorve/CogniFold.

## Bearing on this project

**The architecture scoop.** An always-on proactive agent memory that continuously FOLDS event
streams into self-emerging structures, grounded by extending Complementary Learning Systems
theory - the same theoretical spine this project identified on 08-19 - with similarity merging,
staleness decay, and intent surfacing when concept-cluster density crosses a threshold. Ships
code, evaluates on LoCoMo and LongMemEval. The only visible difference from this design is the
trigger: concept-cluster density versus a session-boundary hook.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
