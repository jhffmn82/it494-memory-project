# OCR Hinders RAG: Evaluating the Cascading Impact of OCR on Retrieval-Augmented Generation
Junyuan Zhang et al., arXiv:2412.02592, 2024-12

## Abstract (verbatim)

Retrieval-augmented Generation (RAG) enhances Large Language Models (LLMs) by integrating
external knowledge to reduce hallucinations and incorporate up-to-date information without
retraining. As an essential part of RAG, external knowledge bases are commonly built by
extracting structured data from unstructured PDF documents using Optical Character Recognition
(OCR). However, given the imperfect prediction of OCR and the inherent non-uniform
representation of structured data, knowledge bases inevitably contain various OCR noises. In
this paper, we introduce OHRBench, the first benchmark for understanding the cascading impact of
OCR on RAG systems. OHRBench includes 8,561 carefully selected unstructured document images from
seven real-world RAG application domains, along with 8,498 Q&amp;A pairs derived from multimodal
elements in documents, challenging existing OCR solutions used for RAG. To better understand
OCR's impact on RAG systems, we identify two primary types of OCR noise: Semantic Noise and
Formatting Noise and apply perturbation to generate a set of structured data with varying
degrees of each OCR noise. Using OHRBench, we first conduct a comprehensive evaluation of
current OCR solutions and reveal that none is competent for constructing high-quality knowledge
bases for RAG systems. We then systematically evaluate the impact of these two noise types and
demonstrate the trend relationship between the degree of OCR noise and RAG performance. Our
OHRBench, including PDF documents, Q&amp;As, and the ground truth structured data are released
at: https://github.com/opendatalab/OHR-Bench

## Bearing on this project

Kills the input-degradation angle. This is exactly the question of how OCR quality cascades into
a retrieval-augmented pipeline, with a benchmark. The OCR tax control in this project's Chinese
corpus is therefore an established method applied to a new setting, not a new instrument -
weaker as a claim, stronger as science, and now citable. That control left the fall slate with
chinese/ on 2026-09-04 and returns only if the folder does.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
