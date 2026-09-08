# Working log: 2026-09-06

Two threads ran this day and both are kept, because they record different work and neither is a
summary of the other.

- [extractor.md](extractor.md): the extractor's whole-corpus run. The saved 0.9 notebook audited
  against the schema and the rulings, then 1.0 to 1.5: the audit applied, the debugging
  accretions cut, a real regression caught by a run and fixed in the resolver, the run
  parallelised, one kind per unit enforced, and three cost defects closed, including a
  no-credits 429 that walked the whole corpus and a per-document cost that counted every other
  thread. Then the clean single pass: 19,436 documents, 44,262 units, 227,100 pieces, $7.72,
  verified against the schema and the text rather than assumed.
- [ingestor.md](ingestor.md): the document ingestor built against the schema in twelve blocks,
  the quote gate returning offsets with classified rejections, a document roster,
  within-document reconciliation with a scored ledger, the package as one file per document, a
  Kaggle-ready notebook; a six-lens adversarial review before the paid run with 32 findings
  confirmed and applied; a 70-check offline battery; the rulings on predicates and the roster.

## Audits

- [audit.md](audit.md): the ingestor against SCHEMA.md, BUILD.md and the brief, record by
  record, the decisions taken and the PROPOSED items, and the project's documents against each
  other.
- [audit-extractor.md](audit-extractor.md): the extractor audited the same way.

## Records

The extractor's run: [run15-receipt.json](run15-receipt.json) and
[run15-read-documents.jsonl](run15-read-documents.jsonl), the record for each of the 231 text and
PDF documents; the 340 MB export stays on Kaggle. The run as it happened is
`extractor-final-receipt.json`, `extractor-final-splits.log`, `extractor-run-347794765.txt` and
`factledger-extractor-as-run-347794765.py`.

The ingestor's: [decisions-ingestor-0.5.md](decisions-ingestor-0.5.md), every decision of the
0.4-to-0.5 session with who took it; [devlog-ingestor-0.5.md](devlog-ingestor-0.5.md), the
building chat's own account; `review-findings*.json`, four rounds of adversarial review;
[test_ingestor.py](test_ingestor.py), the offline battery.

Also here: [final-run-changes.md](final-run-changes.md) and
[ingestor-brief.md](ingestor-brief.md), the opening message for the ingestor chat.
