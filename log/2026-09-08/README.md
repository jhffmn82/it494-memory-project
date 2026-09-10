# 2026-09-08: the review, and the ingestor made readable

Two threads on this day. [review.md](review.md) is the assistant review of the whole repository
after the tree decision (every finding PROPOSED until ruled). The rest of this folder is the
ingestor rewrite: same pipeline, same prompts, same packages, in code a person can read.

## The rewrite: ingestor 0.8 to 0.9

The 0.8 notebook as it last ran on Kaggle is kept here as
`factledger-ingestor-0.8-as-run.py`. The 0.9 notebook is `notebooks/factledger-ingestor.py`
(the `.ipynb` is generated from it by `scripts/py_to_ipynb.py`).

What changed, and why each thing went:

- **Content-hash ids are gone.** The ingestor minted a sha256 for every mention, fact, node
  and cell, and an `input_hash` over the unit ids to decide whether a package was finished.
  Every id it mints is now readable: `<first 8 chars of doc_id>:doc` for the document node,
  `...:n<index>` for an entity, `...:u<unit position>:f<n>` for a fact. `completed()` compares
  the package's unit ids and ingestor version to the document's instead of hashing them. The
  extractor's own ids (`doc_id`, `unit_id`) are untouched. With them went `first_mention`,
  `stamp_first_mention`, `entity_key`, `node_id_of`, `h()`, and the node-collision check that
  only existed because two clusters could hash alike.
- **One verification path instead of two.** The one-reading path and the "fewer than four
  facts" path each had their own copy of the support pass; `adjudicate` now sorts majors into
  "consolidate" and "stand", and every standing fact is checked in the one pass.
- **Counters nobody read are gone** from the unit record and the completion counts:
  `shared_spans`, `ambiguous_voice`, `facts_split_by_voice`, `cells_unlisted`,
  `adjudication_dropped`, `adjudications_skipped`, `adjudication_stranded`, and the `rank`
  dict on an entity that only ever held `no_abstract`. What a fact needs (`voice_ambiguous`,
  `matched_by`) is still on the fact.
- **Mentions are not built as records** any more; they were not written (ruling of 09-08)
  and nothing read them once `first_mention` went. The count survives.
- **Duplicated helpers folded:** `read_jsonl` and `read_own_jsonl`, `document_spend` and
  `unit_spend`, `whole_word` and `whole_word_hit`, `call_thunk`, `boilerplate_of` inside
  `triage`, `show_reconcile`/`show_fold`/`show_adjudication` into `show_document`, three
  `choose_*` functions into `first_existing`. A unit's kind is computed once at load instead
  of on every use.
- **Every block has a markdown cell** saying what it does, and the top cell carries the input
  schema and the algorithm in pseudocode for both paths.

Size: 2,732 lines and 127 functions to 2,523 lines and 107 functions; 2,161 code lines to
1,837. The prompts, the quote gate and the reconciliation are most of what is left, and they
are the pipeline.

## How it was checked

`scripted_model.py` is a model that answers every prompt from the unit text, plus the bad
answers the gates must catch. `diff_ingestor.py` runs 0.8 and 0.9 on the same documents with
that model and compares the packages by content, ids mapped back to what they name: a
synthetic two-speaker chat session (the one-reading path and the speaker cuts), Oz book 1,
the Dong 2005 paper (triage), and a Greek play. All four come out the same, record for record,
with the same sequence of model calls. `test_ingestor.py` is the standalone battery for 0.9:
72 checks over the gate, the helpers, both paths, the package, the receipt and the model
interface. Both need `data/export`, rebuilt by `scripts/rebuild_export.py data/raw papers`.

One thing kept on purpose: the third check after the correction pass rechecks every flagged
fact the second look kept, upheld or reworded, not only the reworded ones. The 0.8 comment said
"reworded" but the code checked both, and that is what the Zep run of this morning did.

## PROPOSED, for a ruling

- `SCHEMA.md` says twice that ids are content hashes (the header, and rule 1 under "What the
  code enforces"). The ingestor's ids are now readable and document-local; the extractor's are
  still hashes. The sentence should say which.
- `SCHEMA.md` rule 5 and `BUILD.md` ("summaries rebuild only when the hash of their inputs
  changes") describe a `children_hash` nothing writes, as review.md already notes.
