# Known limits

Everything here is measured, not estimated, and comes from `receipt.json` and the released rows.
A model made the decisions in this dataset, so the useful question is not whether it is perfect
but where it is known to be wrong and how you would tell.

## Flags

4,012 of 19,395 documents carry at least one flag. **3,944 of those are one advisory note**, on
chat sessions whose turns carry more than one date, saying which date was kept for the document.
Nothing is wrong with those sessions. The benchmark reuses a session across questions and so
gives it several dates; the earliest is kept for the document, its units and every one of its
turns, and the others are dropped. The source dates a session, not a turn, so there is no
per-turn time to keep.

That leaves **68 documents with a real flag**:

| flag | occurrences | what it means |
|---|---|---|
| merging | 41 | a short piece could not be joined: the outline was too long to ask, the join crossed a region boundary, or it would have gone over the cap |
| pointers | 17 | a break the model named matched no line, so that break was dropped |
| metadata | 10 | a title, author or date pointer matched no line, so the field is null |
| shape | 9 | one piece holds most of the body, so the document is probably under-split |
| over cap | 5 | a unit is over 4,000 words because the model could not break it further |
| merging answer | 5 | the model answered the merge question with a word other than the three offered |
| count | 3 | the number of headed pieces disagrees with the document's own table of contents |
| author is a publication | 2 | no person is named anywhere, so the publication stands as the voice |
| grouping | 1 | a group was dissolved or cut, including where the kind changed |

The flagged documents are overwhelmingly the scanned volumes. Diodorus Siculus, Apollodorus and
the Ovid Loeb account for most of the `shape` and `merging` flags between them.

## Pointers

Across the corpus the model named 170 line numbers that did not match the line it copied. 125 of
those were **recovered** from the copied text. **45 were not**, and those breaks were dropped: a
boundary the model wanted does not appear in the split.

The 45 are two classes, both diagnosed against the files:

- **A copy short enough to name several lines.** `CHORUS.`, `BOOK XXXIV.`, `CHAP. II.`, `XVIII.`
  A running header on a scanned page matches dozens of lines exactly. The gate requires five
  words for a run inside a line precisely so a short heading cannot land on the wrong one, and
  the cost is that a genuinely short heading sometimes cannot be placed at all.
- **Text the model repaired as it copied.** An OCR break healed, a footnote marker dropped.
  Searched with whitespace ignored, these strings appear zero times in the file. No matcher can
  find them, and the right answer is to drop the break rather than guess at one.

10 metadata pointers failed the same way and those fields are null.

## Units that are the wrong size

- **5 read units** are over the 4,000-word cap. The model could not find a break inside and code
  does not invent one. **8 chat units** are also over it; those carry no flag, because a chat's
  cap is enforced by code rather than reported by a model.
- **547 read units** are under 100 words. Most are the short front matter of a scanned volume.
- **19,443 chat units** are under 100 words, which is expected: a short exchange is a short unit,
  and a unit is never a lone turn.

## Coverage of the body

Body text is 76.9% of the 42.2 M characters read from books and papers. The median read document
is 74% body. **No document is at 0%.** 30 are below half, and 27 of those are papers, where the
references and appendices genuinely are much of the file. The lowest is Diodorus Siculus volume
1 at 1%, a scan whose contents, index and apparatus dwarf the text.

A low body share on a paper is not a defect. It says the extractor found the references and the
appendix and labelled them, which is the point of the region kinds.

## Dates

`unknown_author` is 0 for every read document. **43 read documents carry no date**, which is the
no-inferred-dates rule working: a Project Gutenberg preamble often gives only an ebook release
date, and the prompt forbids keeping that as the work's date. Do not read a null date as an
unknown work. Four of the 100 papers carry no date for the same reason.

Every chat carries a date and no title, because a LongMemEval session has one and not the other.

## Things this dataset does not claim

- **It is not ground truth.** There is no gold segmentation for these books to score against.
  What is verified is internal: the tiling, the ids, the kind purity, and that every pointer
  behind a boundary matched real text.
- **The labels are the model's words, not a controlled vocabulary.** A unit's `label` is the
  heading it named. Two units of the same book may label the same structure differently.
- **A rerun will differ.** The model is not deterministic. Compare two runs by their receipts.
- **The paper metadata on a document row is what the model read off page one.** For the
  publisher's own record of a paper's title and authors, use `attribution.jsonl`.
