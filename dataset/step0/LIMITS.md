# Known limits

Everything here is measured, not estimated, and comes from `receipt.json` and the released rows.

## Dates known to be wrong

- **"Plays of Sophocles" (Oedipus the King, Oedipus at Colonus, Antigone) is dated `1912`, from
  its page.** That is the translation's year, not when the plays were written. The model pointed
  at a line that states 1912, and the page gate checks only that the year is on the line.
- **Scientific American Supplement No. 360 (November 25, 1882)** has three articles dated by a
  web search that matched the wrong publication: "The Maidenhair Tree" `1938-02-12`, "The Building
  Stone Supply" `1887-01-22/1887-01-29`, and "The Chinese Sign Manual" `1881`. The document takes
  its earliest unit, so it reads `1881`.

A looked-up date is only as good as the search that found it. Every document's flags name the
page or the URL behind each of its dates, so a doubtful date can be checked at its source.

## Dates not found

12 works got no date, and their 15 units carry none: four pieces of the Homerica ("The Great
Works", "The Great Eoiae", "The Epigrams of Homer", "The Battle of Frogs and Mice"), two Pindar
fragments, three pieces in a newspaper reminiscence and three Scientific American articles. Each
null is explained in its document's flags. No document is undated.

## Flags

Every book and paper carries its `date:` notes. Setting those aside, **103 of the 189 read
documents carry a flag**:

| flag | occurrences | what it means |
|---|---|---|
| merging | 79 | a short piece could not be joined: the join crossed a region boundary or a change of date, or would have gone over the cap |
| pointers | 19 | a break the model named matched no line, so that break was dropped |
| shape | 9 | one piece holds most of the body, so the document is probably under-split |
| merging answer | 9 | the model answered the merge question with a word other than the three offered |
| count | 7 | the number of headed pieces disagrees with the document's own table of contents |
| author is a publication | 5 | no person is named anywhere, so the publication stands as the voice |
| over cap | 3 | a unit is over 4,000 words because the model could not break it further |
| grouping | 2 | a group was dissolved or cut |

63 chats carry one flag, `empty turns`, naming the turns with no content that were skipped.

## Pointers

The model named 135 line numbers that did not match the line it copied. 85 were recovered from
the copied text; 50 were not, and those breaks were dropped. The causes, as diagnosed in earlier
runs: a copy too short to name one line (a running header matches dozens), text the model repaired
as it copied, and a line's own `[n]` label copied with it.

## Units that are the wrong size

- **3 read units** are over the 4,000-word cap; the model found no break inside. **6 chat units**
  are too, each a single turn, and a turn is never cut.
- **449 read units** are under 100 words. **130,986 chat units** are, which is expected: a chat
  unit is one turn, and most turns are short.

## Chats

- **1,230 empty sessions** are not exported; they are counted in the receipt.
- **70 empty turns** are skipped, so a session's turn numbers can have gaps.
- A session used by several histories is several documents with different dates. Load one history
  folder to see one user's timeline; loading all of them repeats those sessions.

## Coverage of the body

Body text is 81.6% of the 42.2 M characters read from books and papers, and the median read
document is 74% body. 30 documents are below half: 27 papers, where references and appendices are
genuinely much of the file, and three Greek volumes whose region labels went wrong rather than
their tiling (Pausanias' Description of Greece, Volume II at 1%; The Extant Odes of Pindar at 12%;
The Library at 28%).

## Things this dataset does not claim

- **It is not ground truth.** There is no gold segmentation and no gold date table to score
  against. What is verified is internal: the tiling, the ids, the kind and date purity of units,
  that every chat turn's date equals its history's, and that every pointer behind a boundary
  matched real text.
- **The labels are the model's words, not a controlled vocabulary.**
- **A rerun will differ.** The model and the web search are not deterministic.
- **The paper metadata on a document row is what the model read off page one.** For the
  publisher's own record of a paper's title and authors, use `attribution.jsonl`.
