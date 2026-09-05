# Schema

Nine record types plus logs. Anything not listed here gets added when the data
demands it. Storage is SQLite and JSONL in a single folder, no server. Raw
files are never edited, ids are content hashes, and re-ingesting the same
input is a no-op rather than a duplicate.

**Nothing in the schema knows what a novel is.** Books, chat logs, and PDFs
all arrive the same way: a document holding an ordered run of units. A series
is several documents in order; so is a year of chat sessions. The grouping
the user or a loader declares carries that order.

## The source side

    document  doc_id, source_uri, sha256, title, author, source_class, text,
              ingested_at, occurred_at?, loader
    unit      unit_id, doc_id, position, label?, start, end,
              occurred_at?, occurred_until?
    piece     doc_id, unit_id, position, kind, start, end, author?, occurred_at?

The document holds the text, once: the source decoded to a string at load,
never normalized, with the sha256 of the original bytes beside it as proof of
which bytes it came from. A unit is a range in that string, `start` to `end`
in character offsets, and its text is that slice; nothing stores a second
copy. Every offset anywhere in the store, on units, mentions, and fact quotes,
is a document offset in this one coordinate system, so a quote resolves to
text with a single slice and no join. A unit is the atom every other record
points at. `position` is one integer, 0-based, no gaps. `label` is a free
string with no meaning to the system: keep "chapter 4" or "turns
12-30" in it if it helps a human, but nothing branches on it.

`author` and `source_class` are set by the loader, never by the model reading
the text: the Gutenberg Author line, the first page of a PDF, the role prefix on a
chat turn; a session itself has no author unless the file names one. An author string is resolved to an entity through the merge
before the document's facts commit, because the collision rule has nothing to
compare without it; an unknown author is flagged and can contest but never
supersede. Source classes: canonical, published, record, authored,
tool-output. The voice of a chat turn is its piece's `author`, not a
document class; user and assistant are piece kinds.

A document is an entity in its own right: a node whose cells are its unit
summaries, whose abstract folds from them, with `has_unit` edges in order,
`produced_by` to its author, and `appears_in` edges from the entities found in
it. Two documents never merge; the same bytes are the same document by hash,
and a revision of a work is linked as the same work, not unioned.

`occurred_at` has exactly one meaning: when the source was produced. A chat
session fills it from the session date, a published work from publication, a
novel with neither leaves it null. When the story is set is not this field;
in-story time lives on facts, because it changes within a document.

A unit carries a range, `occurred_at` to `occurred_until`, the time of its
first piece and of its last, filled by the loader only when the file carries
times (a turn timestamp, a dated session); otherwise both are null and the
document's `occurred_at` stands in at read time. When the file carries times,
a unit never spans a day change: the day cut comes before the size rule, and
the short-tail merge applies only inside a day. Two sessions that overlap in
time are ordered fact by fact through their units, not whole against whole.

The split plan is the piece table: one row per natural piece the loader cut
(a chapter, a turn, a section), with its range, its unit, its `kind`, its
`author` when the file names a speaker (the role prefix on a chat turn), and
its time when the file carries one. Written by code at load, never by the
model. Unit ranges and the day cut derive from it. It is also where voice
lives: a fact's voice at read time is the `author` of the piece holding its
quote, else the document's `author`, else unknown, the same shape as the
ordering rule for time.

## The entity side

    node      node_id, name, kind, created_from_unit, provenance
    alias     alias, node_id, first_seen_unit, evidence_quote
    mention   mention_id, node_id?, unit_id, start, end, surface, resolved_by
    profile   node_id, attribute, value, confidence, from_unit

Mentions are what resolution measurements read: duplicate counting needs the
node link, cluster purity needs the full set per node, and coreference scoring
against gold needs the character span. Without spans, that whole class of test
requires a re-ingest, which is why the field exists from day one. `node_id`
is null when the mention names a minor entity: the mention keeps its surface
and span inside its document and never enters the merge. A minor is minor
because the text gave too little to disambiguate it, so tracking it across
documents would mean merging hundreds of names per work on no evidence.

The profile is not a fact. It holds low-confidence attributes the model
inferred from context (gender, age band, animacy, role), read only by the
matcher, never rendered and never exported. The text never says "Tip is male,"
so these rows have no quote, and putting them in the fact table would make the
quote gate a lie.

## The record side

    fact      fact_id, subject, predicate, object, qualifiers, rank, unit_id,
              quote, quote_start, quote_end, valid_from, valid_to, tier, provenance
    cell      cell_id, node_id, unit_id, scope_id, text, tier, provenance
    abstract  node_id, scope_id, text, children_hash, tier, updated_at

Facts are append-only. When a predicate is functional, a later fact on the
same subject and predicate supersedes an earlier one at read time; ruler_of
collides that way, member_of never does, and the functional list is maintained
by hand. Supersession needs the same voice: the `author` of the piece holding
each quote, else the document's `author`. Different voices are contested, and
both facts are served with their source. What "later" means: a fact's ordering time is its `valid_from` when the text
states one, else its unit's `occurred_at`, else its document's `occurred_at`,
else null. Dated facts order by
that time. Undated facts order among themselves by document order in the
declared grouping and unit position, and an undated fact never supersedes a
dated one; that collision is flagged for review instead of resolved. Order by
date alone and a novel corpus supersedes nothing, because almost no fact in a
novel carries a date. Order by position alone and an undated upload ingested
today would silently outrank a dated chat fact from two years ago, which is
exactly the mixed corpus the spring product ingests.

`rank` covers the case supersession cannot: we were wrong, there is no later
event, and deleting would break append-only. `deprecated` means present,
preserved, excluded from reads. `qualifiers` carry role and timing so nobody
invents a new predicate for "as Chancellor". Predicates come from a small
controlled list with a table of which subject and object kinds each may join,
which catches the error a quote cannot: a fabricated relationship carrying a
perfectly real quote.

Cells and abstracts are scoped by `scope_id`, so importance is a property of
the collection, not the entity: a character can be major in one corpus and a
footnote in another. Salience is decided twice. Per unit, it decides who gets
a cell. Per document, it is reassessed once the document's abstract exists:
an entity named in the abstract is major, with unit count and fact count as
tie-breakers, and only document-majors carry a dossier into the merge and
become global nodes. Minor entities never become nodes: a fact from a major
to a minor is a property of the major with the minor's name as its value, a
fact between two minors is not stored, and nothing is lost below the line,
because the per-unit summary, a cell on the document's own node, still
recorded it and every mention keeps its surface and span. There is no community layer: groupings the user or a loader
declares (a series, a thread) exist for ordering and disambiguation scope, and
nothing is clustered.

## What the code enforces

1. Raw text is never edited. Ids are content hashes, so a corrected split
   changes one id instead of every id after it.
2. Nothing is overwritten. Supersession and merges resolve at read time.
3. Every fact carries a verbatim quote that must appear in its unit, and the
   offsets where it was found. A fact whose quote does not is dropped and
   logged, never stored. The gate proves the quote exists, not that it
   supports the fact.
4. Splitting passes three gates per document. Count: pieces (chapters, turns, sections) match the table of
   contents where one exists, else markers are monotonic with no gaps, else
   the document is one piece. Units are size-bounded runs of pieces, cut
   only at piece boundaries, never a lone turn, never across a day change
   when the file carries times, a short tail merged into the unit before it. Coverage: the unit ranges tile the body, between
   its start and end markers where the file has them, with no gaps and no overlaps, and no single unit
   holds a wildly disproportionate share. Round-trip: every unit's slice of
   the document text is identical to what the splitter cut.
5. An abstract is a fold over its cells and facts; it is rebuilt whenever
   the hash of its children changes, and staleness is that hash comparison,
   never a guess.
6. A relationship that violates the predicate type table is rejected before
   it is stored.
7. Model calls, rejections, consults, and costs go to the run log.

Gate 4's proportion clause was added after a real failure: Metamorphoses
volume 1 split into 7 units taken from its summary section, left 97% of the
book in the last unit, and passed the monotonic check while doing so.
