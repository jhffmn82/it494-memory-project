# Known limits

Everything here is measured, not estimated, and comes from `receipt.json`. A model made the
decisions in this dataset, so the useful question is not whether it is perfect but where it is
known to be wrong and how you would tell.

## Flags

4,016 of 19,436 documents carry at least one flag. **3,944 of those are one advisory note**, on
chat sessions whose turns carry more than one date, saying which date was kept for the document.
Nothing is wrong with those sessions; the turns keep their own dates.

That leaves **72 documents with a real flag**:

| flag | documents | what it means |
|---|---|---|
| merging | 38 | a short piece could not be joined: the outline was too long to ask, the join crossed a region boundary, or it would have gone over the cap |
| pointers | 19 | a break the model named matched no line, so that break was dropped |
| shape | 9 | one piece holds most of the body, so the document is probably under-split |
| metadata | 8 | a title, author or date pointer matched no line, so the field is null |
| merging answer | 8 | the model answered the merge question with a word other than the three offered |
| count | 7 | the number of headed pieces disagrees with the document's own table of contents |
| grouping | 7 | a group was dissolved or cut, including where the kind changed |
| over cap | 6 | a unit is over 4,000 words because the model could not break it further |
| author is a publication | 4 | no person is named anywhere, so the publication stands as the voice |

## Pointers

Across the corpus the model named 370 line numbers that did not match the line it copied. 291 of
those were **recovered** from the copied text. **79 were not**, and those breaks were dropped: a
boundary the model wanted does not appear in the split.

The 79 are two classes, both diagnosed against the files:

- **A copy short enough to name several lines.** `CHORUS.`, `BOOK XXXIV.`, `CHAP. II.`, `XVIII.`
  A running header on a scanned page matches dozens of lines exactly. The gate requires five
  words for a run inside a line precisely so a short heading cannot land on the wrong one, and
  the cost is that a genuinely short heading sometimes cannot be placed at all.
- **Text the model repaired as it copied.** An OCR break healed, a footnote marker dropped.
  Searched with whitespace ignored, these strings appear zero times in the file. No matcher can
  find them, and the right answer is to drop the break rather than guess at one.

8 metadata pointers failed the same way and those fields are null.

## Units that are the wrong size

- **6 read documents** have a unit over the 4,000-word cap. The model could not find a break
  inside and code does not invent one.
- **627 read units** are under 100 words. Most are the short front matter of a scanned volume.
- **19,443 chat units** are under 100 words, which is expected: a short exchange is a short unit,
  and a unit is never a lone turn.

## Coverage of the body

Body text is 82% of the 48.6 M characters read from books and papers. The median document is 79%
body. **No document is at 0%.** The 39 below half are the institutional scans and the reference
papers, where notes, references and appendices genuinely are most of the file.

## Dates

`unknown_author` is 0. **52 read documents carry no date**, which is the no-inferred-dates rule
working: a Project Gutenberg preamble often gives only an ebook release date, and the prompt
forbids keeping that as the work's date. Do not read a null date as an unknown work.

## Things this dataset does not claim

- **It is not ground truth.** There is no gold segmentation for these books to score against.
  What is verified is internal: the tiling, the ids, the kind purity, and that every pointer
  behind a boundary matched real text.
- **The labels are the model's words, not a controlled vocabulary.** A unit's `label` is the
  heading it named. Two units of the same book may label the same structure differently.
- **A rerun will differ.** The model is not deterministic. Compare two runs by their receipts.
- **The paper rows have no text.** Their offsets resolve only after you rebuild the text from
  the source PDF. See `PROVENANCE.md`.
