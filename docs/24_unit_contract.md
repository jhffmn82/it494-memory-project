# The unit contract

**2026-08-27. FROZEN.** This is the only schema element that must be settled before preprocessing
begins. Everything else in `docs/17` is provisional and gets settled by contact with real data.

Preprocessing emits records matching this contract and nothing else. Per-corpus handlers absorb
the heterogeneity; downstream sees one shape.

---

## The record

```jsonc
{
  "corpus_id":     "oz",              // oz | greek | holmes | chinese
  "work_id":       "55",              // Gutenberg number or Archive.org identifier
  "work_ordinal":  1,                 // position of the work within the corpus
  "work_title":    "The Wonderful Wizard of Oz",
  "unit_type":     "chapter",         // chapter | book | play | ode | hui | session
  "unit_ordinal":  3,                 // position within the work, 1-based
  "title":         "How Dorothy Saved the Scarecrow",
  "text":          "...",             // verbatim, boilerplate stripped, nothing else altered
  "chars":         11482,
  "source_sha256": "…",               // sha256 of the RAW file, from the corpus manifest
  "unit_id":       "u_a91f0c33"       // content hash: cid(corpus_id, work_id, unit_ordinal, text)
}
```

---

## Field notes

**`unit_type` carries the heterogeneity forward rather than erasing it.** A Euripides play has no
siblings to fold with; an Oz chapter does. Normalising to one record shape is correct;
flattening that distinction is not, and downstream needs to know which it is holding.

**Ordering is `(work_ordinal, unit_ordinal)`, never a single integer.** A node's cells span
multiple works, and a flat ordinal silently interleaves them.

**`unit_id` is a content hash**, so re-running preprocessing on unchanged input produces
identical ids and a second run is visible as an empty diff.

**`text` is verbatim after boilerplate stripping.** No normalisation, no whitespace collapsing, no
smart-quote conversion. The quote gate compares extracted quotes against this text, so anything
done here has to be done identically at extraction time or every quote fails.

**No `span` field.** Offsets into the raw file are deliberately omitted: any change to a splitter
invalidates every offset, and the quote is the durable pointer. Spans are recomputed downstream
as a cache, never stored here. See `docs/19`, quote-primary / span-as-cache.

---

## Acceptance gates

A work passes preprocessing only if one of these holds. **A failure is a failure**, not a
warning — a corpus that is quietly wrong in the middle is worse than one that is visibly short.

| Gate | Applies to |
|---|---|
| Split count equals the table-of-contents entry count | any work carrying a TOC |
| Markers are monotonic with no gaps | regular-marker works with no TOC (e.g. `第N回`) |
| Count equals 1 | single-unit works — plays, odes, standalone stories |

**Table-of-contents titles do not always match body titles.** *The Marvelous Land of Oz* lists
"Tip Manufactures Pumpkinhead" and the body reads "Tip Manufactures **a** Pumpkinhead." Match on
count and order, never on string equality.

---

## Convention handlers

Five known variants, one visible function each, plus a dispatcher that picks by inspection.
Ugly on purpose: every line is defensible and a failure points at exactly one handler.

| Handler | Form | Seen in |
|---|---|---|
| `caps_inline` | `CHAPTER I. TITLE` — number and title on one line, all caps | Holmes *A Study in Scarlet*, Brewitt-Taylor *Three Kingdoms* |
| `roman_own_line` | `Chapter I` with the title on the following line | Oz book 1 |
| `word_own_line` | `Chapter One` with the title on the following line | Oz books 7, 14 |
| `contents_indent` | `I.  A Scandal in Bohemia` indented under `Contents` | Holmes *Adventures* |
| `book_marker` | `BOOK I.` | Iliad, Odyssey |
| `hui_marker` | `第一回 靈根育孕源流出` | Chinese originals — 105 in *Journey to the West* |
| `bare_title` | no marker at all; body titles matched against a `LIST OF CHAPTERS` block | Oz books 2, 3, 13, 17 |
| `single_unit` | the work is the unit | Euripides plays, Pindar's odes |

---

## Boilerplate stripping

Gutenberg's `*** START OF ***` and `*** END OF ***` markers bound the text, **but they are not
sufficient.** Several files carry producer credits *inside* the START marker — "Produced by
Dennis Amundson", proofreading team notes, HTML-version pointers.

The rule is explicit and inspectable: after the START marker, drop leading blocks matching known
producer patterns until the title line. A heuristic that trims N characters is not defensible and
will eat a real first chapter somewhere.

Archive.org scans have no markers at all and open with digitisation boilerplate — the Statius
title does not appear until character 39,300. Those need a per-file front-matter rule or manual
inspection.

---

## Known quality flags to carry forward

These are properties of specific files, recorded so downstream results can be qualified:

- **OCR, not proofread transcription** — three Chinese files, the Richard *Journey to the West*,
  both Apollodorus volumes, both Diodorus volumes
- **Bilingual interleaving** — the Loeb editions mix Greek or Latin into the English: Apollodorus
  ×2, Ovid's *Heroides*
- **Unusable** — the 1767 Statius: 18th-century long-s renders as "f" throughout
- **Abridged** — Richard's *Journey to the West* is roughly one sixth; Joly's *Dream of the Red
  Chamber* stops at chapter 56 of 120
- **No whitespace tokenisation** — the Chinese-language originals. Every length-based rule,
  including chunk size, needs a per-language definition

---

## What is deliberately not in this contract

**Segments below the unit.** If a unit needs subdividing for a context window, that is a
downstream decision recorded on the segment, not baked into preprocessing. Preprocessing finds
the units the work itself declares; it does not invent boundaries.

**Anything derived.** No summaries, no entities, no embeddings. This layer is the write-ahead log
and everything above it is rebuildable from it.
