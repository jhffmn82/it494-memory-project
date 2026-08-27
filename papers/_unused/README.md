# Unreferenced sources

Moved here 2026-08-28. Nothing in the live document set, the reference material, or the reading
list cites any of these, checked by filename slug, author surname, arXiv identifier and title
token.

- `tics2016-vol20no7-contents.pdf`: a journal table-of-contents page, not a paper. It has no
  one-pager and never had one.
- `fu2026-vikingmem.pdf`: VikingMem, a memory base management system for stateful LLM
  applications (arXiv:2605.29640). Relevant to the field, cited by nothing here.
- `lin2026-stagewise-benchmarking.pdf`: stage-wise benchmarking of LLMs for fact-checking
  (arXiv:2601.02669). Adjacent, cited by nothing here.

Their one-pagers moved to `summaries/one-pagers/_unused/`. Nothing was deleted. If a document
starts citing one, move it back.

**The other 89 PDFs are all referenced.** An earlier note describing `papers/` as holding "92 PDFs
of varying relevance" implied a large unused tail; there is not one. A first pass suggested 23
unused, but that matched on filename slug only and produced false positives for every paper cited
by project name or arXiv identifier (AutoSchemaKG, ProactAgent, HERCULES, TraceMem, CogniFold and
eleven others).
