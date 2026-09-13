# BoostTaxo: Zero-Shot Taxonomy Induction via Boosting-Style Agentic Reasoning and Constraint-Aware Calibration
Yancheng Ling et al., arXiv:2605.12520, 2026-04

## Abstract (verbatim)

Taxonomy induction is crucial for organizing concepts into explicit and interpretable semantic
hierarchies. While existing methods have achieved promising results, their generalization,
structural reliability, and efficiency remain limited, hindering their performance in zero-shot
and large-scale scenarios. To overcome these limitations, we introduce BoostTaxo, a boosting-
style LLM framework for zero-shot taxonomy induction. It takes a set of domain terms as inputs
and performs parent identification in a coarse-to-fine manner, employing retrieval-augmented
definition refinement, hybrid parent candidate selection, candidate rating, and structure-aware
score calibration to improve taxonomy construction. Specifically, a lightweight LLM is used to
efficiently filter candidate parents, while a large-scale LLM is employed to rank and score
candidate parents for fine-grained parent selection. Structural features are further
incorporated to calibrate candidate edge weights and enhance the reliability of the induced
taxonomy. The unified BoostTaxo is evaluated on three public benchmark datasets, namely WordNet,
DBLP, and SemEval-Sci, and achieves superior or comparable performance to state-of-the-art
methods in zero-shot taxonomy induction. The ablation study validates the contribution of the
hybrid parent candidate selection and the structure-aware score calibration to the overall
performance. Further analysis investigates the impact of candidate selection size on taxonomy
quality and presents representative case and failure studies, providing deeper insights into the
effectiveness and limitations of the proposed framework.

## Bearing on this project

Zero-shot taxonomy induction via boosting-style agentic reasoning. Further evidence the
induction space is populated.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
