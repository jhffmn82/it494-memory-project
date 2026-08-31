# Schema

Nine record types plus logs. Anything not listed here gets added when the data
demands it. Storage is SQLite and JSONL in a single folder, no server. Raw
files are never edited, ids are content hashes, and re-ingesting the same
input is a no-op rather than a duplicate.

**Nothing in the schema knows what a novel is.** Books, chat logs, and PDFs
all arrive the same way: a document holding an ordered run of units. A series
is several documents in order; so is a year of chat sessions. The corpus
manifest carries that order.

## The source side

    document  doc_id, source_uri, sha256, ingested_at, occurred_at?, provenance
    unit      unit_id, doc_id, position, text, span, label?

A unit is the atom every other record points at. `position` is one integer,
0-based, no gaps. `text` is verbatim after boilerplate stripping, never
normalized, because the quote gate is a plain string find against it. `span`
is byte offsets into the source, a cache; the text is the truth. `label` is a
free string with no meaning to the system: keep "chapter 4" or "session
2026-08-12" in it if it helps a human, but nothing branches on it.

`occurred_at` has exactly one meaning: when the source was produced. A chat
session fills it from the session date, a published work from publication, a
novel with neither leaves it null. When the story is set is not this field;
in-story time lives on facts, because it changes within a document.

## The entity side

    node      node_id, name, kind, created_from_unit, provenance
    alias     alias, node_id, first_seen_unit, evidence_quote
    mention   mention_id, node_id, unit_id, span, surface, resolved_by
    profile   node_id, attribute, value, confidence, from_unit

Mentions are what resolution measurements read: duplicate counting needs the
node link, cluster purity needs the full set per node, and coreference scoring
against gold needs the character span. Without spans, that whole class of test
requires a re-ingest, which is why the field exists from day one.

The profile is not a fact. It holds low-confidence attributes the model
inferred from context (gender, age band, animacy, role), read only by the
matcher, never rendered and never exported. The text never says "Tip is male,"
so these rows have no quote, and putting them in the fact table would make the
quote gate a lie.

## The record side

    fact      fact_id, subject, predicate, object, qualifiers,
              rank, unit_id, quote, valid_from, valid_to, tier, provenance
    cell      cell_id, node_id, unit_id, scope_id, text, tier, provenance
    abstract  node_id, scope_id, text, children_hash, tier, updated_at

Facts are append-only. When a predicate is functional, a later fact on the
same subject and predicate supersedes an earlier one at read time; ruler_of
collides that way, member_of never does, and the functional list is maintained
by hand. What "later" means: `occurred_at` when both facts have one, otherwise
the pair of document order in the corpus manifest and unit position. Dates win
where both sides have them; position carries everything else. Order by date
alone and a novel corpus supersedes nothing, because almost no fact in a novel
carries a date. Order by position alone and backfilling an old chat session
silently reverses the truth.

`rank` covers the case supersession cannot: we were wrong, there is no later
event, and deleting would break append-only. `deprecated` means present,
preserved, excluded from reads. `qualifiers` carry role and timing so nobody
invents a new predicate for "as Chancellor". Predicates come from a small
controlled list with a table of which subject and object kinds each may join,
which catches the error a quote cannot: a fabricated relationship carrying a
perfectly real quote.

Cells and abstracts are scoped by `scope_id`, so importance is a property of
the collection, not the entity: a character can be major in one corpus and a
footnote in another. Every entity gets facts and an abstract; only entities
above the salience threshold get cells, so no lookup comes back empty, and
nothing is lost below the line, because the per-unit summary, a cell on the
document's own node, still recorded it.

## What the code enforces

1. Raw text is never edited. Ids are content hashes, so a corrected split
   changes one id instead of every id after it.
2. Nothing is overwritten. Supersession and merges resolve at read time.
3. Every fact carries a verbatim quote that must appear in its unit. A fact
   whose quote does not is dropped and logged, never stored.
4. Splitting passes three gates per document. Count: units match the table of
   contents where one exists, else markers are monotonic with no gaps, else
   the document is one unit. Coverage: concatenated unit text plus stripped
   boilerplate equals the original, and no single unit holds a wildly
   disproportionate share. Round-trip: every span resolves to exactly its
   unit's text.
5. An abstract is a fold over its cells; staleness is a hash comparison,
   never a guess.
6. A relationship that violates the predicate type table is rejected before
   it is stored.
7. Model calls, rejections, consults, and costs go to the run log.

Gate 4's proportion clause was added after a real failure: Metamorphoses
volume 1 split into 7 units taken from its summary section, left 97% of the
book in the last unit, and passed the monotonic check while doing so.
