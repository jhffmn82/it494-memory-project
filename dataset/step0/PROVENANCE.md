# Provenance

Six corpora, three licenses. Nothing here was scraped: every file came from a named source, was
checked against a hash, and is recorded in the raw dataset's manifests.

## Public domain by expiry of term

**Oz, 29 volumes.** Project Gutenberg. L. Frank Baum's fourteen, five companion volumes, and
Ruth Plumly Thompson's 1922 to 1930 run. Chosen because the project needs a long series by
several hands, which is where a memory backend's entity problems actually appear.

**Sherlock Holmes, 9 volumes.** Project Gutenberg. The canon that is public domain in the
United States.

**Greek and Roman literature, 31 volumes.** Project Gutenberg, plus five institutional scans from
Archive.org. The scans are deliberate: they carry OCR damage, running headers, footnote markers
and heavy editorial apparatus, and a splitter that only works on clean e-texts is not a
splitter. Diodorus Siculus, Apollodorus and Ovid are the hard cases.

Public domain in the United States. Project Gutenberg's own license text is part of these files
and is tagged as a license region in the piece table rather than stripped, so the tiling stays
honest.

## MIT, redistributed with their notices

**GraphRAG-Bench novels, 20 documents.** The novel contexts of GraphRAG-Bench, unpacked one per
file. MIT, copyright the GraphRAG-Bench authors.
https://github.com/GraphRAG-Bench/GraphRAG-Benchmark

**LongMemEval-S sessions, 19,206 documents.** Every distinct non-empty session of LongMemEval-S,
one JSON file each with a session id, dates, and turns as role and content. MIT, copyright 2024
Di Wu. https://github.com/xiaowu0162/LongMemEval

Both keep their upstream license files in the raw dataset. The question sets are not used here.
Step 0 reads sessions as documents.

## Creative Commons Attribution

**Papers on knowledge graphs and RAG, 100 documents.** Full-text research papers gathered from
OpenAlex by `scripts/fetch_kg_rag_cc.py` in the project repository, filtered to works whose best
open-access location reports a Creative Commons license and offers a PDF. Every one of the 100
is `cc-by`. The license was read per paper from OpenAlex and recorded, never assumed.

**Their text is in this dataset in full**, because CC-BY permits redistribution. What it requires
in exchange is attribution, and `attribution.jsonl` carries it: one row per paper with the
authors, the title, the year, the venue, the DOI, the OpenAlex id, the exact license and the URL
the PDF came from. If you show, quote or redistribute any of this text, render the authors, the
title and the license from that row.

These replaced an earlier set of 141 papers whose publishers' licenses did not permit
redistribution. That set was withheld from the 1.5 release, its text null and rebuildable only
from the source PDFs. It is gone from the corpus entirely, and with it the whole withheld-text
mechanism: no document in this release has a null text.

## This dataset

Packaging, schema, the split plan and every derived field are MIT, copyright 2026 Justin
Hoffman. The underlying text keeps the license of its corpus. Do not treat the whole dataset as
MIT: the benchmark texts are MIT, the literature is public domain, and the papers are CC-BY and
carry an attribution condition.

## Raw inputs

[IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw), where
every file is byte-identical to what its source served, with a manifest giving bytes and sha256
per file, a sources file recording where each came from, and a usage file recording what it is
for. The papers' manifest there is the same record `attribution.jsonl` is built from, joined on
the sha256 of the PDF, which is also the document's `doc_id`.
