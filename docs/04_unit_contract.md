# The unit contract

**Re-frozen 2026-08-28.** This is the one thing that must be settled before preprocessing starts.
Everything else in `03_design.md` gets settled by contact with real data.

## Short version

Splitting produces one record shape and nothing else. **Text is text.** A novel, a chat log and a
PDF all come out the same way.

---

## The record

```
{unit_id, doc_id, position, text, span, label?}
```

| Field | What it is |
|---|---|
| `unit_id` | content hash of `text`. Re-splitting identical text gives the same id |
| `doc_id` | content hash of the source file |
| `position` | integer, 0-based, ordering units inside their document. No gaps |
| `text` | the chunk, verbatim, never edited |
| `span` | `[start, end]` byte offsets into the source. A cache; the text is the truth |
| `label` | **optional free string with no meaning to the system.** "chapter 4", "session 2026-08-12". Nothing branches on it |

The document record carries `source_uri` and `sha256` separately, so provenance is a lookup rather
than a field copied onto every unit.

**What changed, and why.** This contract previously required `unit_type` from a fixed list
(`chapter|book|play|ode|hui|session`) and carried two ordinals, `work_ordinal` and `unit_ordinal`,
so a character's thread could span volumes of a series. Both were chapter-parsing concerns that had
leaked into the data model. A series is now just several documents in order, which is the same thing
a year of chat sessions is, and the corpus manifest carries that order. The system no longer knows
what a novel is.

---

## The three gates

Splitting is not done until all three pass, per document.

1. **Count.** Where the source has a table of contents, unit count equals its entry count. Where it
   does not, unit markers must increase monotonically with no gaps. A document with no internal
   structure is one unit.
2. **Coverage.** The units account for the whole source. Concatenated unit text plus stripped
   boilerplate equals the original, and **no single unit holds a wildly disproportionate share.**
3. **Round-trip.** Every `span` resolves, and the text at that span equals the unit text.

**Gate 2's second half was added 2026-08-28** after a real failure: Metamorphoses volume 1 split
into 7 units taken from its *summary* section, leaving 97% of the book inside the last unit, and it
passed the monotonic check while doing so. Counting and ordering cannot tell a good split from a
catastrophic one. Proportion can.

---

## Boilerplate

Project Gutenberg's `*** START OF ***` and `*** END OF ***` markers bound the text, but they are not
sufficient: producer notes and transcriber comments appear **inside** the start marker on some
files. Strip to the first real content, and record what was stripped so the coverage gate can
account for it.

---

## What the corpora actually throw at a splitter

Implementation notes, not part of the contract. A dispatcher picks by inspection.

| Form | Example |
|---|---|
| Number and title on one line, caps | Holmes *A Study in Scarlet*, Brewitt-Taylor *Three Kingdoms* |
| `Chapter I` with the title on the next line | Oz book 1 |
| `Chapter One` with the title on the next line | Oz books 7, 14 |
| Indented under a `Contents` block | Holmes *Adventures* |
| `BOOK I.` | Iliad, Odyssey |
| `第一回` | Chinese originals, 105 in *Journey to the West* |
| No marker at all, body titles matched against a chapter list | Oz books 2, 3, 13, 17 |
| The work is one unit | Euripides plays, Pindar's odes |

Eight forms, one output shape. If a ninth turns up, it is a new function in preprocessing and
nothing downstream changes.

---

## Known quality problems in the sources

- One Greek work (`29_thebaidstatius00conggoog`) fails title verification and is unusable as-is.
- The Internet Archive scans are OCR and carry scan artifacts. That is deliberate: the same content
  exists clean and OCR'd, which is a controlled variable rather than a defect.
- Corpus files are stored with their original line endings and must not be normalised. `.gitattributes`
  enforces this; without it, checkouts break the hashes the manifests attest.
