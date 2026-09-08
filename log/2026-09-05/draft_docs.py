"""Draft the SCHEMA.md and BUILD.md sentences that 2026-09-05's rulings changed, as a patch for
Justin to correct. Writes edited copies beside itself and regenerates
log/2026-09-05/docs-rulings-2026-09-05.patch. The repo's SCHEMA.md and BUILD.md are NOT touched.
Run from the repository root: python log/2026-09-05/draft_docs.py
"""
import difflib
from pathlib import Path

OUT = Path(__file__).parent
PATCH = OUT / "docs-rulings-2026-09-05.patch"

edits = {
"SCHEMA.md": [
# ---- unit time ----
('''A unit carries a range, `occurred_at` to `occurred_until`, the time of its
first piece and of its last, filled by the loader only when the file carries
times (a turn timestamp, a dated session); otherwise both are null and the
document's `occurred_at` stands in at read time. When the file carries times,
a unit never spans a day change: the day cut comes before the size rule, and
the short-tail merge applies only inside a day. Two sessions that overlap in
time are ordered fact by fact through their units, not whole against whole.
''',
'''A unit carries a range, `occurred_at` to `occurred_until`. A chat unit is one
turn and carries that session's time on both ends. A session a benchmark
reused carries several dates; the document, its units and its turns all take
the one it started on, and the document is flagged so the reuse stays visible.
A text or PDF unit carries the document's date on both ends, and a piece never
carries a date of its own. Where nothing carries a time, both are null and the
document's `occurred_at` stands in at read time. Two sessions that overlap in
time are ordered fact by fact through their units, not whole against whole.
'''),
# ---- piece table ----
('''The split plan is the piece table: one row per natural piece the loader cut
(a chapter, a turn, a section), with its range, its unit, its `kind`, its
`author` when the file names a speaker (the role prefix on a chat turn), and
its time when the file carries one. Written by code at load, never by the
model. Unit ranges and the day cut derive from it. It is also where voice
lives: a fact's voice at read time is the `author` of the piece holding its
quote, else the document's `author`, else unknown, the same shape as the
ordering rule for time.
''',
'''The split plan is the piece table: one row per piece, with its range, its
unit, its `kind`, its `author` when the file names a speaker (the role prefix
on a chat turn), and its time when the file carries one. The pieces tile the
document from its first byte to its last; nothing is cut away. For text and
PDF the model decides every boundary and code verifies each one against the
numbered line it points at; a piece's `kind` is the region it lies in:
`front_matter`, `body`, `notes`, `references`, `appendix`, `license`. For a
chat the pieces are the header and the turns, the role as `kind` and `author`,
with no model call; each turn is its own unit, so a unit never mixes two
voices. Unit ranges derive from the piece table. It is also where voice lives:
a fact's voice at read time is the `author` of the piece holding its quote,
else the document's `author`, else unknown, the same shape as the ordering
rule for time.
'''),
# ---- gate 4 ----
('''4. Splitting passes three gates per document. Count: pieces (chapters, turns, sections) match the table of
   contents where one exists, else markers are monotonic with no gaps, else
   the document is one piece. Units are size-bounded runs of pieces, cut
   only at piece boundaries, never a lone turn, never across a day change
   when the file carries times, a short tail merged into the unit before it. Coverage: the unit ranges tile the body, between
   its start and end markers where the file has them, with no gaps and no overlaps, and no single unit
   holds a wildly disproportionate share. Round-trip: every unit's slice of
   the document text is identical to what the splitter cut.
''',
'''4. Splitting passes three gates per document, and a failed gate is a flag,
   never a drop. Count: the model found no fewer pieces than the table of
   contents lists, where one exists; more is not an error, because a contents
   list names top-level divisions and the pieces include what sits under
   them. Coverage: the pieces tile the whole document with no gaps and no
   overlaps, a body region is present, and no single body piece holds most of
   a body over the word cap. Pointers: every line the model pointed at is the
   line it copied, or a neighbour within five that is, or the one line in the
   document that carries those words; the title, author, source and date are
   checked the same way and one that fails is nulled and flagged, so nothing
   the model invented is stored. A document flagged on count, coverage or
   pointers is asked once more on the same model, and once on the stronger
   model when it is small enough to be cheap there; a flag that only describes
   the document buys no call. A text or PDF unit is one piece with the pieces
   under it (a section with its subsections, a chapter with its scenes, a play
   with its notes), grouped by the model, never two peers, never over the word
   cap. A piece over the cap is split by the model inside itself until its
   parts fit, and one that will not split is flagged; a piece under a hundred
   words is offered to the model, which joins it to the piece before, the
   piece after, or leaves it alone, and a join that would cross a region
   boundary or itself carry a piece past the cap is refused and flagged. A
   chat unit is one turn, the header opening the first turn's unit, so a unit
   has one author and one time.
'''),
('''Gate 4's proportion clause was added after a real failure: Metamorphoses
volume 1 split into 7 units taken from its summary section, left 97% of the
book in the last unit, and passed the monotonic check while doing so.
''',
'''Gate 4's proportion clause was added after a real failure: Metamorphoses
volume 1 split into 7 units taken from its summary section, left 97% of the
book in the last unit, and passed the monotonic check while doing so. The
region rule replaced a body-end marker after a second: the first footnote
block after Book VIII was taken as the end of Metamorphoses volume 2 and the
seven books after it were dropped, 95% of the file, and passed every gate.
The count gate became one-sided after a third: it fired on eleven documents
whose contents list and piece list were counting different things, and each
one bought two calls that changed nothing.
'''),
],
"BUILD.md": [
('''A loader must fill `author` (quote-backed from the file bytes, or flagged unknown) and''',
 '''A loader must fill `author` (quote-backed from the file bytes, else the publication the text names, flagged, else flagged unknown) and'''),
('''Structured inputs (a chat session with turns) become units with no model call. A paper is the text layer of its PDF, read through one dependency: the whole paper is the document, its sections the units, the abstract first. Unstructured text is
split by one model call per document that proposes verbatim marker lines
(body start, body end, headings) from a compressed view of the text; code
locates the markers and cuts, the three gates verify, and the split plan is stored per document as the piece table (one row per piece: kind, range, unit, author when the file names a speaker, time when it carries one) so a re-run is a replay and a fact's voice is a lookup. On either path a unit is a size-bounded run of the document's natural pieces (chapters, turns, sections), cut only at a piece boundary, never a turn alone, never across a day change when the file carries times, with a short tail merged into the unit before it. There are no per-work or
per-corpus rules in the splitter; a document the gates reject is stored as
one unit and flagged, never dropped.''',
 '''Structured inputs (a chat session with turns) become pieces and units with no model call, one unit per turn. A paper is the text layer of its PDF, read through one dependency, and is split like any other text. Text and PDF are split by the model over the whole document as numbered lines: one call returns the regions (front matter, body, notes, references, appendix, license) and the headings by line number, code verifies each number against the line the model copied, and every byte lands in a piece; nothing is cut away, and a wrong boundary is a mislabel, not a loss. Code never decides where a break may be, from line shape, font, or pattern; it decides only how to address the text, by line, or by sentence when the file has no lines or its lines are one word each. Units are the model's too: a piece over the word cap is split by the model inside itself, and the outline goes back to the model to group each piece with the pieces under it, never two peers. The three gates verify, and the split plan is stored per document as the piece table (one row per piece: kind, range, unit, author when the file names a speaker, time when it carries one) so a re-run is a replay and a fact's voice is a lookup. Each record carries the loader that wrote it, so a resume redoes what an older loader left rather than keeping it. There are no per-work or
per-corpus rules in the splitter; a document the gates reject is stored as
it was split and flagged, never dropped; a document too long for one call is
one piece and flagged.'''),
],
}

patch = []
for name, pairs in edits.items():
    old = Path(name).read_text(encoding="utf-8")
    new = old
    for a, b in pairs:
        assert new.count(a) == 1, (name, a[:60])
        new = new.replace(a, b)
    (OUT / name).write_text(new, encoding="utf-8", newline="\n")
    patch += difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                  fromfile=f"a/{name}", tofile=f"b/{name}")
PATCH.write_text("".join(patch), encoding="utf-8", newline="\n")
added = sum(1 for l in patch if l.startswith("+") and not l.startswith("+++"))
removed = sum(1 for l in patch if l.startswith("-") and not l.startswith("---"))
print(f"patch: {added} lines added, {removed} removed -> {PATCH}")
