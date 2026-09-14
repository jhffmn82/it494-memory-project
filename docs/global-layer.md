# The global layer

PROPOSED 2026-09-13, from the discussion with Justin that evening (`log/2026-09-13/global-layer.md`);
it stands on his ruling. It replaces the first-cut rule in `docs/execution-plan.md` section 2b
(case-folded name and kind; a parent named by its most frequent child name; a count-sentence
abstract), which is superseded. The settled shape in `docs/entity-resolution.md` stands: nothing
is merged, a child belongs to one document, a parent asserts nothing about the world.

## What it is

One graph over everything loaded. The store holds every package that is given to it, chats, books
and papers together, and the parents are built over all of it; a test is a filter at retrieval
time on a set of documents (one LongMemEval history, the three Oz books), never a different build.
Deployed, the same path takes each night's new sessions: nothing already stored is changed except
the parents that gain a child.

## The parent

A parent is its own record, owned by no document. It holds a name, a kind, the union of its
children's aliases, a role summary, and its instance list (the children, each an entity node in
one document). The role summary is one line per document saying what part that instance played
there, and every line carries the id of the child it came from; a line with no child behind it is
rejected. The judge picks the name and the kind from what the children carry (a name no child ever
used is rejected, and the log records which child supplied it), so "Ozma" over "Tip" is a choice
among the evidence. Kind is redefined here from what comes in; a child's kind never blocks an
attachment.

The parent is rewritten on every attach: one model call reads the parent as it stands and the one
new child (its name, aliases, kind, summary, or for a chat child its facts) and writes the new
name, kind and summary; code takes the union of the aliases and appends the child to the instance
list; the parent's vector in the sidecar is refreshed. A child that matches nothing founds a new
parent as a copy of itself, with no call.

## Salience for chats

A chat session's reading made every subject a major. Before nomination, one call per session sees
the session's abstract and every entity with its facts and answers which are things a person would
want found again across sessions (a store, a show, a person, a place, a product, a project) and
which are the scaffolding of that one conversation. Only the first group is nominated; the rest
stay as leaves under the session document, with no parent and no further call, still reachable
through their facts. Books and papers keep their majors, judged per unit already. Step 1 is not
rerun. The user is never nominated (ruled 2026-09-12).

## The up-edge

Children are processed in document order. For each child, nomination is a similarity search: the
child's text (name, aliases, summary or facts) is embedded and scanned against every existing
parent's text, and the nearest few parents are offered to the judge. Each offered pair is logged
with three scores, kept separate so the attachment replays under any one of them: the lexical
match (case-folded name or alias overlap), the vector similarity, and the cast overlap (the
ingestor's own co-occurrence score, Jaccard over the names that share a unit with each side,
carried across documents; a rarity-weighted variant, with the 09-08 term log(N over one plus the
documents holding the name), is logged as a second column). A document's own identity fact (book 2
states that Tip is Princess Ozma, with a quote) is a fourth nomination, ranked first. The judge
rules attach or found, with a reason; the edge (`instance_of`, owned by the child's document)
carries the reason and the scores. Co-occurrence is what keeps a Dorothy of Oz apart from a Dorothy
in a chat inside the one graph, and what clusters documents; on the three Oz books it does not
unite anything on its own (measured 09-13: every cross-book pair scores 0.04 to 0.12 because the
shared cast is the same core), and the identity fact and the judge do that work.

## The key

The attachment is scored against a public key drawn from the Wikipedia list of Baum's Oz characters
(CC BY-SA 4.0) and the per-character articles: one line per character with the names the first three
books call it, and pairs that must stay apart. From it: wrong-unite and wrong-split counts, attachment
accuracy, and the replay by signal. From the same roster, the coverage of majors (which of the
roster's characters the three packages hold as nodes). Fact and narrative coverage against the
articles' plot sections is a later instrument, since it needs a model reading and its own hand check.
A second check: 30 parents drawn at random from the history, hand checked.

## What the store holds and how it is read

SQLite, one file: every package record keyed by the full document hash (the 8-character tag is
display only), the parent table, the up-edges with their reasons and scores, the candidate log, the
row map and header of the sidecar. FTS5 over abstracts, cells and fact quotes; every quote
re-resolved from its offsets at load.

The sidecar is one float16 `.npy` beside the database, memory-mapped, rows in row-map order, holding
one vector per fact rendered as a line (subject, predicate, object, date, document), one per sentence
of every cell, entity summary, session abstract and parent summary, each sentence prefixed with its
entity and document. No index: a linear scan of the corpus's vectors is a fraction of a second, far
under the reader's call, and memory is the only limit (about 1.1 GB at the full chat corpus).

Retrieval: two flat scans, facts and narratives, give the entry hits; one hop of expansion along
node (sibling facts and cells), document (the same session's turns) and parent (the other children
and their cells and top facts) pulls what they connect to; everything is rescored against the
question with a fixed discount per hop, kept once at its best score, rendered whole with its date
and document, and packed by rank within the budget. The log records every candidate, how it arrived
and whether it was packed or cut. Flat is the scans alone; full adds the three hops; parent-off
removes the parent hop. The insertion measurement: ingest the history, add one session, count what
was rewritten.

## Amendments of 2026-09-14

From two adversarial reviews of the pipeline pseudocode and Justin's rulings on them
(`log/2026-09-14/global-layer.md`). Each is part of the design above.

- **The offer floor.** A parent is offered to the judge only when its lexical score is nonzero
  (its name or an alias matches the child's name or an alias, or appears in the child's summary
  or facts), or its vector similarity clears a threshold set on the test packages, or a fact of
  the child's document names one of its children as a node (`object_is_node`). Candidates below
  the floor are logged so the floor can be tuned. A child with no parent over the floor founds
  one with no call. Chat children are judged on Luna, book and paper children on Terra.
- **Two children of one document are never offered to each other.** Each is offered parents;
  both may land under the same parent, in the first pass or the second. So Tip founds a parent,
  Princess Ozma is offered it, and the judge rules.
- **The second pass.** After every package is loaded, every child that founded its own parent is
  offered the full parent set under the same rule, once; an attach moves its edge and deletes the
  one-child parent, which loses nothing. This is also what makes arrival order matter for
  reproducibility only: a document arriving out of order attaches the same way, later.
- **Order.** Packages are ingested by the document's `occurred_at` (first year as a signed
  integer), ties by `source_uri`, undated last. Nothing in the rules depends on the order for
  correctness. Within a package, children are processed by first unit.
- **The judge sees texts, never scores.** Scores decide what is offered; the judge rules on the
  child's text, the parents' summaries and both casts as names. Every verdict is logged with the
  parent's version at the time, so a replay can reuse it for a pair already ruled and count where
  the summary has since changed.
- **The filter applies at every hop.** Retrieval's document filter masks the entry scans, every
  expansion hop, and the parent's summary lines (only lines whose child id is inside the filter
  render). Without this a LongMemEval number leaks another user's sessions.
- **Expansion is capped.** Each hop takes the top m items by score and logs the rest as cut.
- **The sentence prefix** is the entity name, plus the document's title where Step 0's title is a
  title and not an identifier (a session id is noise). Date and document render at pack time.
- **FTS5 stays.** Retrieval has a keyword scan beside the two vector scans, fused by rank as the
  plan says; every packed item renders with its date.
- **The ablation.** The arms (which signals nominate) are a switch in the pipeline. They are run
  as full rebuilds over the scored subset only, the three Oz books against the key and the
  held-out histories the harness scores, never the whole corpus; the replay from the log is the
  screen. Which histories is the test-set ruling, still open.
- **The key's matching** step is reported: Wikipedia names matched to children by case-folded
  alias first, the rest by hand, with the hand count beside the accuracy.
- **Deletion has its twin measurement**: remove one session and count what was rewritten.
- **Re-ingesting a changed package** (detach its children, rewrite the touched parents) is
  spring; this fall a finished package is skipped on a rerun.
- **The sidecar row map** is written in the same transaction as the parent's record and verified
  on load; a mismatch rebuilds the sidecar.
- **Open, parked by Justin 09-14:** the gold for the document-cluster test. The recommendation on
  the table is LongMemEval's multi-session questions, whose answer sessions form labelled
  clusters inside a history; not ruled.

## Gate, Sep 20

Parents over the test packages with the key scored; the store built from them; the sidecar rebuilt
byte for byte twice.
