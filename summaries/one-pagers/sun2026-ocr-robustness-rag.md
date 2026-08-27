# When Good OCR Is Not Enough: Benchmarking OCR Robustness for Retrieval-Augmented Generation
Lin Sun et al., arXiv:2605.00911, 2026-04

## Abstract (verbatim)

Industrial Retrieval-Augmented Generation (RAG) systems depend on optical character recognition
(OCR) to transform visual documents into text. Existing OCR benchmarks rely on character-level
metrics, which inadequately measure downstream RAG effectiveness under real-world conditions. We
introduce an OCR benchmark for industrial RAG systems covering 11 challenging document types,
including extreme layouts, high-resolution pages, complex or watermarked backgrounds, historical
documents with non-standard reading orders, visually decorated text, and documents containing
tables and mathematical formulas. Evaluating recent SOTA OCR models under a controlled OCR-first
RAG pipeline shows clear performance degradation on realistic industrial documents despite
strong conventional benchmark scores. We find that high OCR accuracy does not necessarily
translate into strong downstream RAG performance: structural and semantic errors can cause
substantial retrieval failures even when WER/CER remains low. Further analysis shows that this
mismatch is category-dependent, arises through both retrieval-side and downstream generation-
side failures, and remains stable across representative OCR-first pipeline choices. The
benchmark is publicly available at https://github.com/Qihoo360/InduOCRBench.

## Bearing on this project

Second paper on OCR robustness for RAG, 2026. Confirms the line is populated rather than a one-
off.

Read from: **abstract only**. Added 2026-08-27 during the novelty reassessment. Full-text read
outstanding; do not cite specifics beyond the abstract until that is done.
