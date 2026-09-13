# Provenance

Six corpora, three licenses. Nothing here was scraped: every file came from a named source, was
checked against a hash, and is recorded in the raw dataset's manifests.

## Public domain by expiry of term

**Oz, 29 volumes.** Project Gutenberg. L. Frank Baum's fourteen, five companion volumes, and
Ruth Plumly Thompson's 1922 to 1930 run.

**Sherlock Holmes, 9 volumes.** Project Gutenberg. The canon that is public domain in the
United States.

**Greek and Roman literature, 31 volumes.** Project Gutenberg, plus five institutional scans from
Archive.org, kept deliberately for their OCR damage, running headers and editorial apparatus.

Public domain in the United States. Project Gutenberg's own license text is part of these files
and is tagged as a license region in the piece table rather than stripped.

## MIT, redistributed with their notices

**GraphRAG-Bench novels, 20 documents.** The novel contexts of GraphRAG-Bench, unpacked one per
file. MIT, copyright the GraphRAG-Bench authors. https://github.com/GraphRAG-Bench/GraphRAG-Benchmark

**LongMemEval-S, 23,882 chat documents in 500 histories.** Unpacked by the extractor's block 0
from `longmemeval_s.json`, which the raw dataset carries byte-identical to the benchmark's release
and checks against its sha256. Each of the 500 questions' histories is one folder; each session in
it is one document, its turns dated as that history dates the session. The questions, answers and
evidence marks are not written. MIT, copyright 2024 Di Wu. https://github.com/xiaowu0162/LongMemEval

Both keep their upstream license files in the raw dataset.

## Creative Commons Attribution

**Papers on knowledge graphs and RAG, 100 documents.** Full-text research papers gathered from
OpenAlex, filtered to works whose best open-access location reports a Creative Commons license
and offers a PDF. Every one of the 100 is `cc-by`, read per paper from OpenAlex and recorded.
Their text is in this dataset in full; `attribution.jsonl` carries the authors, title, year,
venue, DOI, OpenAlex id, exact license and source URL that the license requires be rendered.

## Dates looked up

Where a book or paper's page does not state when a work was written, its date was found by a web
search, and the URL it came from is recorded in the document's flags. Those pages are cited, not
redistributed.

## This dataset

Packaging, schema, the split plan and every derived field are MIT, copyright 2026 Justin
Hoffman. The underlying text keeps the license of its corpus.

## Raw inputs

[IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw), version 4,
where every file is byte-identical to what its source served, with a manifest giving bytes and
sha256 per file.
