# Schema

Five record types. Anything not listed here gets added when the data demands
it. Storage is SQLite in a single file, with JSONL export for publishing.
Raw files are never edited, and every id is a content hash, so re-ingesting the
same input is a no-op rather than a duplicate.

## source

One row per ingested file.

    source_id   hash of the raw bytes
    corpus_id   which collection it belongs to (oz, holmes, greek, chinese, chat, ...)
    ordinal     position within the corpus, where one exists
    title
    lang        en, zh, ...
    kind        book | chat_export | note
    meta        JSON carrying origin url, quality flags, and whatever else the
                corpus manifest knows about the file

## unit

The atom every other record points at: a chapter, a play, a chat session.

    unit_id     hash of (source_id, text)
    source_id
    ordinal     1-based position within the source
    unit_type   chapter | book | play | ode | hui | session | whole
    title
    text        verbatim after boilerplate stripping, never normalized

## entity

People, places, things, and topics. One row per real thing, however many names
it wears.

    entity_id
    name        canonical
    kind        person | place | thing | topic
    aliases     surface forms, each with the unit where it was first seen
    summary     one paragraph, rebuilt when the entity's cells change

## fact

Dated, attributed assertions. Append-only. When a predicate is functional, a
later fact on the same subject and predicate supersedes an earlier one at read
time, in unit order; ruler_of collides that way, member_of never does. Nothing
is deleted or overwritten.

    fact_id
    subject     entity_id
    predicate   drawn from a small controlled list
    object      entity_id or literal
    unit_id     where it was asserted
    quote       verbatim string that must appear in the unit's text

## cell

One entity's narrative for one unit. Only entities above a salience threshold
get cells; every entity gets facts and a summary regardless, so no lookup ever
comes back empty.

    cell_id
    entity_id
    unit_id
    text

## Rules

1. Unit text is verbatim. The quote gate is a plain string find against it, so
   any normalization silently breaks every quote.
2. A fact whose quote does not appear in its unit is dropped and logged, never
   stored.
3. Unit ids hash content, not position. Fixing a bad split changes one id
   instead of every id after it.
4. Ordering is corpus ordinal, then unit ordinal. Chat corpora order by session
   time, which is what their unit ordinal encodes.
5. A split must reproduce its source: the units of a file, concatenated in
   order, equal the stripped file byte for byte.
6. Everything above unit is rebuilt from unit. Model calls, rejections, and
   costs are logs, not schema.
