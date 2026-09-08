# Build 0.8: the worklist

Everything the 09-07 audit raised, everything I raised, and every ruling taken today, in one
place. Nothing here is optional and nothing here is a proposal except where it says PROPOSED.
The build is done when every row is ticked and the battery covers each one.

Sources: the audit thread's Part B (open from the first audit), Part C (new in 0.7), Part D
(rulings) and Part E (the settled architecture); `decisions-ingestor-0.7.md`; the rulings taken
in conversation today.

## 1. The rulings, as settled law

**R1 — a quote must STATE its fact, not support it.** One sentence, written once, used in the
fact prompt and the support prompt alike: *the passage must carry the claim itself, in whatever
words the document uses; a table row, a heading or a caption carries what it lists.* The two
prompts had asked for different things — line 912 said "supports", line 955 said "states" — so
the gate admitted on one standard and the check condemned on another. The worked example in the
support prompt is rewritten: `"deletion 0.02 to 0.42"` carries neither "optimized" nor
"accuracy", so as written it licensed exactly the loose citation the rule forbids.

**R2 — a fact carries `occurred_at` and `occurred_until`,** copied from its unit, alongside
`valid_from`/`valid_to`. Not a change: SCHEMA.md:104 already ordered facts by "its unit's
`occurred_at`" while SCHEMA.md:95 never listed the fields on the record, and the code followed
the record line. `valid_from`/`valid_to` keep their meaning (validity the text states);
`occurred_at` keeps its one meaning (when the source was produced). The document fallback stays
a read-time rule.

**R3 — an unsupported fact is corrected if possible, dumped otherwise, never kept with a flag.**
`rank: "unsupported"` is retired. The passage is fixed and the claim moves to fit it: one
batched call restates subject/predicate/object so the passage states it, or returns null. The
quote and its offsets never change, so nothing re-enters `locate`. A corrected fact re-runs the
checks that need no gate (self-reference, the object rules) and is dumped if it fails them. A
fact that cannot be corrected is not written; it becomes a `rejection` with category
`unsupported`, alongside `not_found`, `paraphrase` and `span_too_wide`.

**R4 — within a document the judge resolves; across documents nothing does.** A document is a
snapshot with an end state and is entitled to say what that state is; refusing to let it throws
away a judgement made with the whole document in view. A parent counts and never adjudicates.
The resolution is recorded **on the contradiction record**, naming which of its `from_facts`
holds at the document's end — not on the fact, because global can only disambiguate what
reaches it, and ranking the loser out of reads hides from the global layer that the document
ever said it. Both facts stay `active`. The adjudication prompt's `do not resolve them` is
replaced. The short path is unaffected: no judge, no contradiction records, and the
cross-session case belongs to Step 2.

**R5 — minors stay mentions only.** No nodes, no dossiers, no promotion of the population. The
minor population is not under-salient people; it is scenery. One Oz book: 644 distinct minor
surfaces against 45 major nodes — throne room, flowers, straw, the raft, the wall, wind, his
axe, the basket, silk, the ladder — and pronouns, `them`, `man`, `woman`, which would each be
minted a node. A global layer handed those is not getting a weak signal, it is getting a
category error. The cost is real and accepted: a named minor character never accumulates across
documents. If that ever breaks an eval answer the fix is a salience change, not a storage
change.

**R6 — salience is a union of promotions and nothing is demoted for salience.** An entity is a
document-major if *anything* made it one: a unit called it major (the per-unit flag at the
entity prompt, "major only if it would appear in a two-sentence summary of this text"), the
document abstract names it, or it carries a proper name. Bare unit and fact counts do NOT
promote: I had written them in as a fourth route, carried over from the old no-abstract fallback
and not part of what was ruled, and they re-minted exactly the scenery R5 excluded. They are out.

The `in_abstract` test stops being the *only* route to major. Its provenance:
`log/2026-09-04/README.md:19` ruled it, and the sentence that follows gives its reason — *"Only
document-majors carry dossiers into the merge."* It was a budget on the global merge. The merge
was deleted this week, so the rule has been enforcing a constraint for a design that no longer
exists. With a 400-word abstract as the only gate, the abstract's word limit was silently the
document's entity budget: Oz survives on 46 majors in 354 words, a Greek play with thirty
speaking characters cannot, and every character the fold had no room to name was reduced to a
mention with a null node_id.

The tie-break demotion goes with it — it fires on exactly the entities the new rule promotes.
Decision 52 survives untouched: an entity with no facts and no cells was never a unit-major, so
the two rules cannot fight over the same entity. Cost, measured after the fact: adjudication is bounded by
FACTS, not by majors — one call per major over that major's own facts, at $0.028 a major — so the
3.7x growth in majors is not 3.7x the cost. My "62% and scales with majors" was a misreading of
the 09-07 table and is withdrawn. R6 takes the 230 full-path documents from ~10,571 majors to
~43,565; Justin kept the rule against that number, accepting that the growth lands in Step 2's
merge. The short path makes no per-major call at all, so the 19,206 chat sessions are unaffected,
and riding shrinks as a side effect.

## 2. The changes

| # | what | where | verified by |
|---|---|---|---|
| ✅ B6 | the battery committed, and grown 146 -> 176 | `log/2026-09-06/test_ingestor.py` | committed at `fbfc5a0` |
| ✅ C7 | a quote is cut where the speaker changes, not at every piece boundary | `voice_spans` | a two-piece one-author unit keeps a crossing quote whole |
| ✅ C1 | reconciliation converges on unnamed entities: `seen_pairs` passed into `pair_up` and skipped while scoring, so the slot goes to the next-best candidate | `reconcile`, `pair_up` | four locals named "the girl" judge all six pairs, not two |
| ✅ C2 | a refused verification is reported, not swallowed: `unsupported_of` returns the refusal and `rejected` is set from it at all three call sites | `unsupported_of`, `adjudicate` | a stubbed refusal marks the document rejected, not clean |
| ✅ C3 | `support_calls` counts calls | `write_package` counts | a short-path package reports 1, not 3 |
| ✅ C4 | the verification listing is batched | `unsupported_of` | a document with more facts than the batch makes more than one call |
| ✅ C5 | a riding fact's verdict reaches the record that exists: raw ids translated through `landings` | `adjudicate`, `write_package` | a minor's flagged fact ranks its riding copy |
| ✅ C6 | on the short path a fact is listed once, under the id the package will carry | `adjudicate` light branch | no duplicate numbers in the listing |
| ✅ C8 | the judge keeps a verdict only when its number is in range, and counts the failures | `judge` | an out-of-range pair number is dropped and counted |
| ✅ C9 | an abstract does not degrade to concatenated predicates: children only when two or fewer, else no abstract at all (nothing demotes under R6, so the major simply carries none) | `abstract_of` | no abstract is a run of three or more predicate strings |
| ✅ B1 | qualifiers typed in the fact prompt as they are in the adjudication prompt | fact prompt | the prompt names the type |
| ✅ B2 | `different` verdicts applied before `same` ones within a batch | `decide` | (A,B) same, (B,C) same, (A,C) different leaves A and C apart |
| ✅ B3 | the sidecar label is derived from the derive path, not typed by hand | `input_hash` | a changed derive path rejects an old sidecar |
| ✅ B4 | every reply a document buys is checkpointed, not four intermediate object graphs: `generate` reads its document's sidecar first | `generate`, `remember_reply`, `load_replies` | a remembered reply is read back from the sidecar after being forgotten in memory |
| ✅ R1 | one standard, both prompts, example fixed | fact + support prompts | both prompts carry the same sentence |
| ✅ R2 | `occurred_at`/`occurred_until` on the fact record | `write_package` | a fact carries its unit's times |
| ✅ R3 | correction pass; `rank: "unsupported"` retired; `unsupported` becomes a rejection category | `adjudicate`, `write_package` | an uncorrectable fact is a rejection, not a ranked fact |
| ✅ R4 | the contradiction carries the document's resolution | adjudication prompt, `write_package` | a contradiction record names which fact holds |
| ✅ R6 | salience as a union, nothing demoted | `fold_document` | a unit-major absent from the abstract stays major |

Also, not a defect: `fold_document` records `by_abstract_only`, the number of entities the old
abstract-only rule would have made major, so every run reports the size of R6's change beside the
new count.

## 2a. What changed from this list while building it

- **R6 narrowed** as above: no promotion on bare unit or fact counts.
- **B2 was refactored to be testable.** The batch ordering came out of `decide()` as
  `constraints_first`, because inside a closure it could only be tested through a scripted judge
  and a fixture that happened to produce three pairs sharing a cluster in one batch.
- **`corrected_fact` was wrong on first writing** and the battery caught it: it compared the
  corrected object to the predicate without flattening the snake_case, so "reduces latency" did
  not read as a restatement of "reduces_latency".
- **Three checks I wrote first were tautologies** (`... if False else True`, `VERIFY_BATCH > 0`,
  a `pair_up` call on an empty list) and were replaced with behavioural tests. A check that
  cannot fail is worse than no check.
- **The E3 battery check was retired as written.** "An object is a node only when the text wrote
  it as a name" was never a rule in the code; it held because an unnamed entity could never be
  major. It now tests what is guaranteed: an object points at a node only when that node is in
  the package.
- **BUILD.md needed no change** — it does not mention Step 1.

## 3. Not in this build

- **PROPOSED, awaiting Justin's word on the wording only** — two sentences for SCHEMA.md's read
  rules, the behaviour already ruled under R4: *A read that returns the facts for an entity and
  predicate must return all of them or say it truncated, and must join the contradiction records
  for those facts or say it did not. A document's own resolution of a contradiction is recorded
  on the contradiction, not on the fact; a fact served without its contradictions may be one the
  document itself superseded.* Neither exists today; `truncat` appears nowhere in SCHEMA.md.
- **Terra's output price** is inferred, not read. It was 71% of the $11.47 run's reported cost,
  so every terra-heavy figure is an upper bound until it is verified. Mine to do, not a ruling.
- **`QUOTE_SPAN_MAX` against table quotes**, conditional on R1. Requiring the quote to carry the
  column header may push a header-to-cell span past 400 characters, and the gate would refuse a
  true fact as `span_too_wide`. Measured on the papers during the build; a ruling only if it
  happens. The cap is not widened without one.

## 4. Documents to update when the build lands

`SCHEMA.md` (R2's two fields on the fact record; R4's resolution field and the read rules; R6's
salience paragraph, replacing the abstract rule and noting the merge-budget provenance so nobody
re-derives it), `BUILD.md`, and a `decisions-ingestor-0.8.md` recording R1–R6 with what each
changed.
