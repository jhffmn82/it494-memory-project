# Provenance

Every row here derives from one document of
[ThreadAtlas Step 0](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step0), version
1.8, joined on `doc_id`. Step 0's `PROVENANCE.md` traces each document to its source and its
hash; this file says what license the derived rows carry and what the quotes keep.

## The derived rows

Entities, aliases, edges, facts with their predicates and offsets, cells, abstracts,
consolidations, contradictions, rejections, the reconciliation ledger and candidates, the
completions, the call log and the receipt are the output of a model reading under the project's
rules, plus the document-record facts copied from Step 0's document rows. They are MIT,
copyright 2026 Justin Hoffman.

## The quotes

Every fact's `quote` and every rejection's `quote` is verbatim text of its document and keeps
that document's license.

**Oz, three volumes** (The Wonderful Wizard of Oz, 1900; The Marvelous Land of Oz, 1904; Ozma of
Oz, 1907) and **The Bacchae** (Euripides): Project Gutenberg texts, public domain in the United
States by expiry of term.

**LongMemEval-S, 71 chat sessions**: the 53 sessions of one question's history and 18 answer
sessions of 13 other questions, unpacked by Step 0 from `longmemeval_s.json`. MIT, copyright 2024
Di Wu. https://github.com/xiaowu0162/LongMemEval . Nothing from the test itself is here: no
question, answer or evidence mark. The session ids are the benchmark's own, and a chat's
`belongs_to_history` fact names the benchmark question whose history holds the session.

**GraphRAG-Bench, one novel**: MIT, copyright the GraphRAG-Bench authors.
https://github.com/GraphRAG-Bench/GraphRAG-Benchmark

**Five papers on knowledge graphs and RAG**: Creative Commons Attribution, read per paper from
OpenAlex. Their quotes are here; `attribution.jsonl` carries the authors, title, year, venue,
DOI, OpenAlex id, license and source URL that the license requires be rendered wherever a
paper's text is shown.

## The models

`gpt-5.6-luna` and `gpt-5.6-terra`, OpenAI, on the Flex tier, called through the chat
completions API by the public notebook. Every call is in `calls.jsonl` with its tokens and cost.

## Raw inputs

Step 0's inputs are byte-identical to what each source served and are published at
[IT494 Raw Corpora](https://www.kaggle.com/datasets/jhffmn/it494-narrative-corpora-raw),
version 4, with a manifest giving bytes and sha256 per file.
