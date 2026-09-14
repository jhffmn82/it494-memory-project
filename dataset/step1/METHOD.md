# Method

The ingestor is one Kaggle notebook:
[ThreadAtlas Document Ingestor](https://www.kaggle.com/code/jhffmn/threadatlas-document-ingestor),
`threadatlas-ingestor 1.8`, run on 2026-09-14 over the Step 0 1.8 export. Two models:
`gpt-5.6-luna` reads units and chat sessions, sorts a chat's entities, and runs every check and
correction; `gpt-5.6-terra` judges entity pairs, folds abstracts and consolidates a major's facts.
Every call runs on OpenAI's Flex tier. There is no embedder; no vector is stored.

The rule behind it: **a document is read on its own, and every claim read from it must point at
its text.** Nothing here sees a second document, and a fact the text cannot be shown to state is
not kept.

## The document record

Before any reading, every document's node gets the facts Step 0 already established, built
from the export with no model call: `has_title`, `has_author` when a person or publication is
named, `has_date` (with the extractor's notes on where the date came from in the fact's
provenance), `has_source_class`, and `belongs_to_history` for a chat. They carry no quote and no
unit, and their provenance says `document record`. Nothing searches the text for them; a later
extractor that exports the offsets of the lines it verified will let them carry quotes.

## A book or a paper

Unit by unit, four at a time, each unit read with nothing from any other unit:

1. **Triage**, one call over the unit list: which kinds of unit are not the work itself. Front
   matter and license go by rule; the model may leave out references or an appendix, but never
   more than half the document.
2. **Entities**, per unit: every entity with its surface forms, and which are major, meaning the
   entity would appear in a two-sentence summary of the unit. An entity is kept only if one of
   its forms is found in the unit's text.
3. **Facts**, per unit: subject, predicate, object, and a verbatim quote. The quote is located
   in the unit (exactly, or after normalising whitespace and quotes, or across a wrapped line,
   or by edge rewording of a word or two) and the offsets are stored; a quote that cannot be
   located is rejected and logged. A fact whose object restates its subject, whose subject the
   unit did not list, or which repeats a stored fact is rejected too.
4. **Cells**, per unit: a summary of the unit, and one narrative cell per major entity in it.
5. **Reconciliation**, at the end of the document: unit-local entities become document entities.
   The same proper name and kind unite with no call, unless their `is_a` conflict. Other pairs
   (a shared surface form, a shared name word, or a fact saying one is the other) are scored 0.7
   name similarity plus 0.3 co-occurrence (the overlap of the entities each appears beside),
   dropped under 0.35, and judged round by round on Terra, ten pairs a call, same, different or
   unsure. Every verdict is a ledger row and every scored pair a candidate row. Two entities of
   one unit are never paired, and a pair ruled different is not offered again.
6. **Fold**: the document's abstract from its unit summaries; an abstract per major entity from
   its cells and facts. A major with no facts and no cells is demoted.
7. **Adjudicate**: a major with four or more facts gets one Terra call that consolidates them
   into facts, attributes and contradictions, each citing the raw facts behind it; a contradiction
   names which fact holds at the document's end. A major with fewer keeps its raw facts and gets
   a support check instead, sixty facts a call.
8. **Verify**: every flagged fact is looked at again on Luna: stand, reword to what its passage
   states, or drop. A rewording is checked once more. A flagged fact no verdict reaches is
   dropped.

A document of one unit takes the short path: no triage, entities then facts and cells, nothing
to reconcile, the unit summary as the abstract.

## A chat session

One Luna call reads the whole session, its turns numbered (a session over 40,000 characters is
read in stretches of whole turns). The call returns the session's summary, which becomes its
abstract, and its facts, each naming the turn it comes from. From a user turn: what the user
says of their own life, plus one `stated` fact per user sentence that states a detail, the whole
sentence as its object and its quote. From an assistant turn: the specific names, numbers,
amounts, steps and options it gives the user. A fact is kept only if its quote is located in its
turn and its subject is the user, appears in the turn, or shares a word with it. The same name
in two turns is one entity, no judge.

Then **one more Luna call sorts the session's entities** (new in 1.8). It sees the session's
summary and every entity with its facts and quotes, and gives each entity a kind, which may not
be `thing`, and a salience: major when a person who owns this chat history would want it found
again in a later session (a named person, place, organisation, store, product, work, event,
project, a specific thing the user owns, plans, attends or returns to); minor when it is the
scaffolding of the one conversation (a category, a section of the assistant's answer, an option
among options, a step in a list, an abstract topic); when in doubt, minor. The user stays a
major, kind `person`. A major becomes a node with its facts. A minor gets no node, and its facts
are stored on the session's own node with `direction` `mentioned`, the entity's name kept in
`provenance.subject_name`, quote and offsets untouched.

Then one support call over every fact, verify, write. No cells, no fold, no entity abstracts.

## Salience

In a book or paper, a unit's call decides what is major; nothing else promotes. In a chat, the
sorting call decides. A minor entity has no node. In a book or paper a fact lands on the major
that is its subject, or under the major it points at with the minor's name as its value, and a
fact between two minors is not stored, with the completion record counting it; in a chat a
minor's facts are `mentioned` facts of the session.

## Dates and voice

A fact carries `occurred_at` copied from its unit: when it was said. `valid_from` is filled only
when the quote itself states when the fact began. A fact's `author` is its turn's speaker on a
chat, else the document's author.

## Cost

$5.47 for the 81 documents, 1,784 calls, about 2.8 hours of kernel time with four units read at a
time and sixteen chats at once. A chat session costs about $0.005, of which the sorting call is
$0.0005; a novel about $1.10; a paper $0.23. Flex prices, per million tokens: Luna $0.10 in and
$0.60 out; Terra $1.00 in and $6.00 out.

## Reproducing it

Fork the notebook, attach
[ThreadAtlas Step 0](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step0), add an
OpenAI key, and run blocks 12 to 15, which select this release's documents by path. A model is
not deterministic, so a rerun differs in what it names and how it words a fact; the receipt and
the rejection log are how two runs are compared. The packing script that regrouped the packages
into these files, `scripts/pack_step1_public.py`, is in the project repository and re-checks
every quoted fact against Step 0's text.
