# Provenance

Six corpora, four licenses. Nothing here was scraped: every file came from a named source, was
checked against a hash, and is recorded in the raw dataset's manifests.

## Public domain by expiry of term

**Oz, 29 volumes.** Project Gutenberg. L. Frank Baum's fourteen, five companion volumes, and
Ruth Plumly Thompson's 1922 to 1930 run. Chosen because the project needs a long series by
several hands, which is where a memory backend's entity problems actually appear.

**Sherlock Holmes, 9 volumes.** Project Gutenberg. The canon that is public domain in the
United States.

**Greek and Roman literature, 31 volumes.** Project Gutenberg, plus six institutional scans from
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

## Withheld

**Reference papers, 141 documents.** The papers read for the project, fetched from arXiv, the
ACL Anthology and publisher sites. Licenses are per paper and mostly do not permit
redistribution, so the text is not in this dataset. What is here: the document row with a null
text, its units and pieces, and a row in `papers.jsonl` with the source URL and the PDF's
sha256.

Rebuilding one is three steps. Fetch the source URL, confirm the bytes hash to the recorded
sha256, and run the text extraction in block 1 of the notebook, which is page text from
`pdfplumber` joined with form feeds. The offsets in `units.jsonl` and `pieces.jsonl` then
resolve against the result.

One paper appears twice in the fetch under two names and is exported once, as the receipt's
`duplicate_files` records.

## This dataset

Packaging, schema, the split plan and every derived field are MIT, copyright 2026 Justin
Hoffman. The underlying text keeps the license of its corpus. Do not treat the whole dataset as
MIT: the benchmark texts are MIT, the literature is public domain, and the papers are absent for
a reason.

## Raw inputs

[IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw), where
every file is byte-identical to what its source served, with a manifest giving bytes and sha256
per file, a sources file recording where each came from, and a usage file recording what it is
for.
