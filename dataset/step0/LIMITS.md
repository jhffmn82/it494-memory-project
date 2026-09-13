# Known limits

Everything here is measured, not estimated, and comes from `receipt.json` and the released rows.
A model made the decisions in this dataset, so the useful question is not whether it is perfect
but where it is known to be wrong and how you would tell.

## Flags

4,013 of 19,395 documents carry at least one flag. **3,944 of those are one advisory note**, on
chat sessions the benchmark places on more than one date, saying no date was kept. Nothing is
wrong with those sessions. The benchmark reuses a session in the histories of several questions
and dates each placement for its question, so the session has no single date of its own; its
document, units and turns carry none.

That leaves **69 documents with a real flag**:

| flag | occurrences | what it means |
|---|---|---|
| merging | 38 | a short piece could not be joined: the outline was too long to ask, the join crossed a region boundary, or it would have gone over the cap |
| pointers | 18 | a break the model named matched no line, so that break was dropped |
| metadata | 11 | a title, author or date pointer matched no line, so the field is null |
| shape | 9 | one piece holds most of the body, so the document is probably under-split |
| merging answer | 8 | the model answered the merge question with a word other than the three offered |
| count | 7 | the number of headed pieces disagrees with the document's own table of contents |
| grouping | 6 | a group was dissolved or cut, including where the kind changed |
| over cap | 3 | a unit is over 4,000 words because the model could not break it further |
| author is a publication | 2 | no person is named anywhere, so the publication stands as the voice |
| grouping answer | 1 | the model's groups did not cover the outline, so each piece became its own unit |

`receipt.json` lists every flagged document under `flagged`.

## Pointers

Across the corpus the model named 189 line numbers that did not match the line it copied. 127 of
those were **recovered** from the copied text. **62 were not**, and those breaks were dropped: a
boundary the model wanted does not appear in the split.

The causes, as diagnosed against the files in earlier runs, are properties of the gate rather
than of one run:

- **A copy short enough to name several lines.** `BOOK XXXIV.`, `CHAP. II.`, `XVIII.` A running
  header on a scanned page matches dozens of lines exactly. The gate requires five words for a
  run inside a line precisely so a short heading cannot land on the wrong one, and the cost is
  that a genuinely short heading sometimes cannot be placed at all.
- **Text the model repaired as it copied.** An OCR break healed, a footnote marker dropped, Greek
  accents normalised. Searched with whitespace ignored, such strings appear nowhere in the file,
  and the right answer is to drop the break rather than guess at one.
- **The line's own label copied with it.** The model sometimes copies `[1235] CHAPTER VI.` for
  line 1235. The gate does not strip the label, so a break at the right line is dropped.

11 metadata pointers failed the same way and those fields are null.

## Units that are the wrong size

- **3 read units** are over the 4,000-word cap. The model could not find a break inside and code
  does not invent one. **5 chat units** are also over it; each is a single turn, and a turn is
  never cut.
- **443 read units** are under 100 words.
- **105,485 chat units** are under 100 words, which is expected: a chat unit is one turn, and
  most turns are short.
- **55 chat units hold no words of the conversation.** The turn's content is empty (10) or only a
  zero-width space (45), so the unit holds its opening line and the role and nothing else. They
  are kept so the turn numbers stay aligned with the benchmark's.

## Coverage of the body

Body text is 80.1% of the 42.2 M characters read from books and papers. The median read document
is 75% body. 31 documents are below half, and 28 of those are papers, where the references and
appendices genuinely are much of the file. The other three are volumes where the region labels
went wrong rather than the tiling: both volumes of Ovid's Metamorphoses round to 0% and 1% body,
and the scanned Apollodorus volume 2 rounds to 0%. Their text is all present and all addressable,
but almost none of it is labelled `body`, so a reader filtering on that kind would see nearly
nothing.

A low body share on a paper is not a defect. It says the extractor found the references and the
appendix and labelled them, which is the point of the region kinds.

## Dates and titles

`unknown_author` is 0 for every read document. **46 read documents carry no date**, which is the
no-inferred-dates rule working: a Project Gutenberg preamble often gives only an ebook release
date, and the prompt forbids keeping that as the work's date. Do not read a null date as an
unknown work. Four of the 100 papers carry no date for the same reason. Two read documents carry
no title, because no title pointer on the page could be verified.

Every chat carries its session id as its title, because that is the only name a LongMemEval
session file gives itself. 15,262 chats carry their session's date; the other 3,944 carry none,
as the Flags section explains.

## Things this dataset does not claim

- **It is not ground truth.** There is no gold segmentation for these books to score against.
  What is verified is internal: the tiling, the ids, the kind purity, and that every pointer
  behind a boundary matched real text.
- **The labels are the model's words, not a controlled vocabulary.** A unit's `label` is the
  heading it named. Two units of the same book may label the same structure differently.
- **A rerun will differ.** The model is not deterministic. Compare two runs by their receipts.
- **The paper metadata on a document row is what the model read off page one.** For the
  publisher's own record of a paper's title and authors, use `attribution.jsonl`.
