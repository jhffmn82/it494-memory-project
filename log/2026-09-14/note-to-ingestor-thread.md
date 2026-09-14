# Note to the ingestor thread: unfreeze 1.7 for one chat run, 2026-09-14

From the global-layer thread, at Justin's ruling of 09-14 (early). Step 1 was frozen on 09-12;
Justin unfreezes it for one more run over the chats to fix what the 1.8-export run's packages
show about the session reading. Books and papers are not rerun. The packages are on Justin's
machine at `%TEMP%\fr18\packages` and, regrouped, in the public dataset
`jhffmn/it494-threadatlas-step1`; the global layer's store is built from them and rebuilds in
minutes, so nothing downstream blocks on you.

## What the packages show (measured over the 71 chat sessions)

- Every chat entity but the user has kind `thing`: 1,001 of 1,061 entity nodes. The reading is
  never asked for a kind, so kind carries nothing on a chat.
- Every subject the reading uses is a major. A session about a birthday party yields nodes named
  `menu`, `story`, `presentation`, `party favors`, `Classic & Elegant` beside the one or two
  things worth finding again. Across the 53 sessions of history gpt4_2ba83207: 691 distinct
  names, 20 in a second session, only `user` in more.
- A chat entity has exactly one alias, its name. Book entities carry ten to twenty.
- Chat entities have no description of their own; the session abstract and the facts are all.

## The change Justin ruled (the same one call per session, more asked of it)

1. **Kind per entity.** Ask for a kind and say what one looks like (person, place, organisation,
   store, product, work, event, project); `thing` is refused.
2. **Salience per entity.** Mark each entity worth finding again in a later session (a named
   person, place, organisation, store, product, work, event, project, a specific thing the user
   owns, plans, attends or returns to) as major; the scaffolding of the one conversation (a
   category, a section of the assistant's answer, an option among options, a step in a list, an
   abstract topic) as minor. When in doubt, minor.
3. **Roll the minors' facts onto the session.** A fact whose subject is minor is not dropped: its
   subject becomes the session's own document node (`<tag>:doc`); predicate, object, quote,
   offsets and date stay exactly as read; `provenance.subject_name` keeps the entity's name (the
   field is already written); `direction` takes the new value `mentioned`. So "menu
   has_dietary_option vegetarian" stays one searchable fact with its quote, carried by the
   session. Justin's words: "increase a session entity, and roll non salient facts into a tuple
   of session mentioned fact into it"; the global thread's shaping, which he saw, is that each
   stays a fact rather than a stringified tuple, so the quote gate and the offsets hold. Minors
   still get no node.

Suggested in the same call, not yet ruled, take them to Justin one at a time if you want them:

4. **Alternate names** the session uses for a salient entity (the short name, a nickname, an
   abbreviation), written as aliases. The up-edge's lexical signal sees only exact names on chats
   today.
5. **A one-line description** per salient entity, as the session describes it, written as the
   entity's abstract (chats have none). The global layer nominates parents by a vector over the
   child's text, and a sentence beats a fact list; it also becomes the founding parent's summary
   line.
6. **Relative dates resolved against the turn time**: "I ordered from Publix last week" on a turn
   dated 2023-05-30 gives `valid_from` 2023-05-23 with the approximate mark. Today `valid_from`
   is filled only for an absolute date in the quote; this is a ruling change and needs his yes.
   It is what LongMemEval's temporal-reasoning band asks.
7. **The output shape** from `docs/execution-plan.md` 2e (one JSONL per history rather than two
   files per document), since block 12 is open and the full run needs it before it launches.

## What the global thread needs back

- The version label (`threadatlas-ingestor 1.8`), the receipt, and the packages for the 71
  sessions in the same folder layout as before (`packages/<history>/<session>/<session>.jsonl`),
  or the 2e shape if you build it, in which case tell me the shape and I change the packer.
- Every stored quote still slicing at its offsets; the packer re-checks all of them against the
  Step 0 export and refuses otherwise.
- Nothing else changes for books and papers, so the Oz and paper packages of the 09-13 run stay
  as they are.

## Push the output to the Step 1 dataset (Justin, 09-14)

The run's packages go to the public dataset `jhffmn/it494-threadatlas-step1` as its next
version, in the published shape: one file per record type, every row keyed by `doc_id`. The
packer does it and re-checks every quote against the Step 0 export:

```powershell
$env:PYTHONUTF8=1; python scripts\pack_step1_public.py <packages-dir> C:\Users\jhffm\kstep1 <step0-export-dir>
```

where `<packages-dir>` holds the new chat packages beside the unchanged Oz, paper, play and
novel packages of the 09-13 run (copy those in, or point the packer at a folder that has both),
and `<step0-export-dir>` is the 1.8 Step 0 export (`documents.jsonl` with text; on Justin's
machine at the a3b08f2d scratchpad, `dates/kout18/export`). Then:

```powershell
$env:PYTHONUTF8=1; kaggle datasets version -p C:\Users\jhffm\kstep1 -m "ingestor 1.8: chat kinds, salience, mentioned facts" -r skip
```

Before the push, update `dataset/step1/` (README, SCHEMA, METHOD, LIMITS, `dataset-metadata.json`):
the version label, the new `direction` value, the salience rule, the kind rule, and the counts
from the new receipt; the packer copies those files into the staging folder. Subtitles are
capped at 80 characters; `kaggle datasets version` applies the files and the subtitle, and the
description needs `kaggle datasets metadata --update -p C:\Users\jhffm\kstep1 jhffmn/it494-threadatlas-step1`
afterwards. Nothing is pushed without Justin's yes on the run's receipt.

Then the global thread rebuilds the store and the sidecar from the new version and drops its
own salience call for chats, since the reading now carries it.

## Rulings touched

- 09-12 "Step 1 is frozen on this version": superseded by this run (Justin, 09-14).
- 09-13 (night) "no rerun of the chat reading; the global layer takes over kind and salience":
  reversed by Justin 09-14; kind and salience come from the reading.
- 09-11 "a fact whose subject is minor in every unit is not stored; the completion record keeps
  the count": narrowed for chats: it is stored on the session node as `mentioned`.
- Everything else in `docs/rulings.md` stands, in particular: predicates are the model's own
  strings and are never merged; every fact carries a located verbatim quote; a chat session is
  read in one Luna call; the user is a standing major and gets no global entity.
