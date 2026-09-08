# Decisions: ingestor 0.8

Six rulings taken 2026-09-07, one at a time, and what each changed in the build. The defects
fixed alongside them are in [build-0.8-worklist.md](build-0.8-worklist.md); this file is only the
rulings. Every one is Justin's. Where my recommendation was wrong, or my reason for it was, that
is recorded too, because a ruling taken on a bad reason is worth re-examining later and a ruling
taken on a good one is not.

---

## R1 — a quote must STATE its fact, not support it

The fact prompt asked for a quote that *supports* the fact; the support check asked which facts
their passage does not *state*, defined as carrying the claim in its own words. The gate admitted
on one standard and the check condemned on another, so part of the 20.4% unsupported rate was
just the distance between two sentences.

One sentence now, written once as `QUOTE_RULE` and used in both prompts: *a passage states a fact
when it carries the claim itself, in whatever words the document uses: it need not repeat the
fact's wording, the subject may be a pronoun or a shorter form, and a table row, a heading or a
caption states what it lists.*

The worked example was rewritten. The old one — `"deletion 0.02 to 0.42"` states an optimized
accuracy of 0.42 — carried neither "optimized" nor "accuracy"; those words are in the column
header, which was not in the quote. It licensed exactly the loose citation the rule forbids. The
fact prompt now also says to quote the heading a table value sits under.

**Cost accepted:** papers lose table facts whose quote is a bare cell, and a header-to-cell span
may exceed `QUOTE_SPAN_MAX = 400` and be refused as `span_too_wide`. That is measured on the
papers during the next run; if it happens it is a further ruling, and the cap is not widened
without one.

## R2 — a fact carries `occurred_at` and `occurred_until`

Copied from its unit, alongside `valid_from`/`valid_to`. Justin: *"It was always supposed to be
occurred at and occurred until."*

A correction, not a change. SCHEMA.md:104 already ordered facts by "its unit's `occurred_at`",
but the fact record line at :95 never listed the fields and the code followed the record line, so
ordering by time required a join to the unit. `valid_from`/`valid_to` keep their meaning, the
validity the text states; `occurred_at` keeps its one meaning, when the source was produced. The
document fallback stays a read-time rule.

## R3 — an unsupported fact is corrected if possible, dumped otherwise

`rank: "unsupported"` is retired. It was a flag on a fact we shipped anyway, which is the thing
the ruling forbids: a flag on a stored fact is a claim the reader has to know to distrust.

The passage is held fixed and the claim moves to fit it. One batched call restates subject,
predicate and object so the passage does state them; the quote and its offsets never change, so
nothing re-enters `locate` and the evidence stays exactly what the gate verified. A fact that
cannot be corrected is not written at all — it becomes a `rejection` with category `unsupported`,
beside `not_found`, `paraphrase` and `span_too_wide`.

A correction is not taken on trust. The model that just failed to support a claim is the one
rewriting it, and the cheap way out is a bland restatement the passage trivially states, so
`corrected_fact` re-runs the checks a fact must pass that do not need the gate: it must say
something, its object must restate neither its subject nor its predicate (with the snake_case
flattened, so "reduces latency" does not slip past "reduces_latency"), and it must not be a bare
boolean.

**Cost accepted:** a fifth call on the short path whenever a document has any flagged fact, which
at the current rate is most of them. Roughly **$182 → $225** for the chat corpus, and about the
same on wall clock. The next run answers the question neither of us can: of the flagged facts,
how many are a bad claim over a good passage that correction rescues, and how many are nothing
at all.

## R4 — within a document the judge resolves; across documents nothing does

The audit proposed "never resolve, anywhere". Justin narrowed it, and the narrower line is the
better one: a document is a snapshot with an end state and is entitled to say what that state is;
refusing to let it throws away a judgement made with the whole document in view. A parent counts
and never adjudicates, so the layer above inherits nothing settled.

The resolution goes **on the contradiction, not on the fact**. The contradiction record gains
`holds`, naming which of its `from_facts` is true at the end of the document, and `because`. Both
facts stay `active`. Justin's reason decided it over mine: I argued from append-only, he argued
that *"global has to disambiguate something"* — ranking the loser out of reads hides from the
global layer that the document ever said it, and that layer can only work with what reaches it.

The audit added a requirement I had filed as a cost, correctly: **A carries an obligation.** A
read that returns facts for an entity and predicate must join the contradiction records or say it
did not, or it will serve a superseded fact as current. That sentence and the retrieval-
completeness sentence beside it are written into SCHEMA.md as **PROPOSED** — the behaviour is
ruled, the wording is not. Neither existed before; `truncat` appeared nowhere in SCHEMA.md.

The short path is unaffected: no judge, no contradiction records, and the cross-session case is
Step 2's.

## R5 — minors stay mentions only

No nodes, no dossiers, no promotion of the population. My recommendation was named-minors-only
and the audit's was a node for every entity; both were wrong, and Justin's reason is why: *"Minor
entities include literally anything mentioned within the text. To include, dishes in Dorothy's
farmhouse."*

Measured against one Oz book, mentions with a null node_id: **644 distinct minor surfaces against
45 major nodes** — throne room 21, flowers 16, straw 10, the raft 9, the wall 8, wind 7, his axe
7, the basket 6, silk 6, the ladder 5 — and `them` 17, `man` 15, `woman` 7, which would each have
been minted a node. A global layer handed those is not getting a weak signal, it is getting a
category error.

I had priced the minor population as *under-salient people* — the colleague named once a session,
the LongMemEval shape — and it is nothing like that. The audit's argument that unnamed minors are
weak-but-harmless rested on the same mistake.

**Cost accepted:** Gayelette, Quelala and the Guardian of the Gates are named characters and stay
document-local, so they never accumulate across the Oz books. Small against 644 surfaces of
furniture, and if it ever breaks an eval answer the fix is a salience change, not a storage
change — which is the direction that does not require re-ingesting a corpus. R6 is that fix,
arrived at within the hour.

## R6 — salience is a union of promotions and nothing is ever demoted

An entity is a document-major if **anything** made it one: a unit called it major, the document
abstract names it, or it carries a proper name. Nothing demotes.

Being named in the abstract had been the *only* route, which made a 400-word abstract the
document's entity budget. Oz survives on 46 majors in 354 words; a Greek play with thirty
speaking characters cannot, and every character the fold had no room to name was reduced to a
mention with a null node_id. Justin: *"if we reduce them down to minor, we lose a lot of the named
characters in say a greek work."*

Its provenance matters and is recorded in SCHEMA.md so the rule is not re-derived from its old
reason. `log/2026-09-04/README.md:19` ruled it, and the next sentence gives the reason: *"Only
document-majors carry dossiers into the merge."* It was a budget on the global merge. The merge
was deleted this week.

The tie-break demotion at `DEMOTE_UNITS`/`DEMOTE_FACTS` went with it — it fired on exactly the
entities the new rule promotes. Decision 52 survives untouched: an entity with no facts and no
cells was never a unit-major, so the two rules cannot fight over the same entity.

**Two things I changed inside the ruling, and should be checked.** First, I had written bare unit
and fact counts into the union as a fourth route; they were not part of what Justin ruled, I
imported them from the old no-abstract fallback, and they re-minted exactly the scenery R5
excluded. They are out: an unnamed thing that merely recurs is not promoted. Second, the battery's
E3 check — *"an object is a node only when the text wrote it as a name"* — was never a rule in the
code. It held because an unnamed entity could never be major and so never became a node, and the
09-07 audit answer added a check asserting that accident. R6 removes the cause on purpose, so the
check now tests what is actually guaranteed: an object points at a node only when that node is in
the package.

**The residual, stated plainly:** an unnamed entity a *unit* judged central — the raft, in the
chapter where the raft is built — is now a document node. That is R5's line narrowed, not
overturned, and it is exactly what *"a major entity at roll up was a major entity in one chapter"*
asks for. The Oz run reports the major count under both rules so the size of it is visible.

**Cost accepted:** adjudication scales with majors and is 62% of a full-path run, but only the 230
full-path documents are affected. The short path makes no per-major call at all, so the 19,206
chat sessions are unchanged, and less riding makes their one verification call shorter.
