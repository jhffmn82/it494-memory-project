# Known limits

Everything here is measured from the released rows and `receipt.json`, not estimated.

## This is the test set

81 documents, chosen to cover every input shape, out of the 24,071 in Step 0. One user's chat
history is complete (53 sessions); the other 18 sessions are single answer sessions of 13
questions, not their histories. Nothing statistical about the corpus should be read from these
counts.

## The chat reading

- **Only a fact's subject becomes an entity.** A store named only as the object of a fact (the
  user placed an online order with a store) has no node and stays a string in the object; a
  search over entity names will not see it.
- **A table read row by row loses its header.** One answer session's facts quote a shift-sheet
  row without the column names, so the shift it states is recoverable from the turn's text, not
  from the fact alone.
- **Salience is one model's judgement per session.** 643 entity nodes across 71 sessions, a
  median of 5 a session and at most 64 (a trip-planning session listing cities and events); the
  1,113 `mentioned` facts carried by sessions are what the sorting call judged minor. No gold
  says it was right.
- **No cells and no entity abstracts on a chat.** The session's abstract and its facts are all
  there is.

## What the gates turned away

Of the facts the model wrote, 1,044 failed the quote gate: 268 repeated a stored fact, 103 quoted
text not in the unit, 73 paraphrased it, 62 restated their subject as their object, 52 named a
subject the unit had not listed. The passage check then flagged 1,163 stored facts and dropped
486 of them as unsupported, reworded 426 and upheld 251. In books and papers, 331 facts fell
because their subject was minor in every unit and they pointed at no major. 61 entities were
turned away: 54 with no surface form in their unit, 7 claiming a span another entity held. All
of it is in `rejections.jsonl` and the completion counts.

## Quotes

All 6,605 facts read from the text slice from their document at their offsets, checked at
packing. 3,938 were located exactly, 2,928 after normalising whitespace and quote marks, 229
across a wrapped line, and 327 by rewording a word or two at an edge (`provenance.matched_by`);
the stored quote is always the document's text, never the model's. The 324 document-record facts
carry no quote by design: they restate Step 0's document row (title, author, date, source class,
history), and a reader who wants the evidence goes to that row and to the extractor's date notes
in the fact's provenance.

## Kind and predicate are the model's words

99 distinct kinds in the release, 53 of them on chats; the same character is `person` in two Oz
books and `character` in the third, and `organisation` and `organization` both occur. 2,235
distinct predicates; `is_a` most often. Nothing is normalised, by rule. A reader who wants a
controlled vocabulary maps these.

## Consolidation

A major with four or more facts had them consolidated on Terra; a major with fewer kept its raw
facts and got a support check. So the raw facts of a consolidated major were not support-checked
individually; their consolidation cites them. 3 of 48 contradictions have no `holds`: the
reading could not say which state held at the document's end.

## Within one document only

Nothing is merged across documents. Dorothy in three Oz books is three nodes; the papers' shared
terms are one node per paper. The reconciliation ledger and candidates are within-document only.

## Things this dataset does not claim

- **It is not ground truth.** No gold entity list, fact list or coreference was scored against.
  What is verified is internal: every quoted fact slices to its text, every fact's subject is a
  node of its document, every consolidation cites stored facts.
- **A rerun will differ.** The models are not deterministic; version 1 (ingestor 1.7, 2026-09-13)
  and this version differ on every document that was reread, not only the chats.
- **The 8-character tag in ids is display.** Key on `doc_id`; at the full corpus size two
  documents can share a tag.
