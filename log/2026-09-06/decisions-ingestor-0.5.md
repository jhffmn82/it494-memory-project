# Decisions: ingestor 0.4 to 0.5 (the evening of 2026-09-06 into the night)

Every decision taken in the session that read the first real Oz run and produced ingestor
0.5, who took it, why, what it changed, and where it stands. "Ruled" means Justin decided;
"drafted" means the chat proposed and built it under his direction; PROPOSED means it waits
for his ruling before SCHEMA.md or BUILD.md change. Numbers refer to `audit.md` where the
same decision is filed there.

## Reading the 0.4 run

The run: Oz book 1, 25 units read (the license unit left out by triage), 604 unit-locals to
358 document entities, 38 majors, 869 facts kept, 74 rejected, $2.23, 305 calls (75 Luna for
derive; 100 judge, 54 entity abstracts, 70 adjudications, 2 folds on Terra). Receipt and the
one rejection row are `receipt.json` and `rejections.jsonl` in this folder.

1. **The rejections were mostly string mismatches, not model errors** (drafted). 33 of 74
   were `unlisted_subject`, every one a case or article difference ("The Scarecrow",
   "Dainty China Country"); chapter XVI lost 24 of its 38 facts this way. Of 41 paraphrase
   rejections, 28 were rerun through the gate against the real text: 10 failed only because
   the model wrapped the quote in its own quotation marks; 18 were true paraphrases. Both
   fixes went into stage A: `loose_name` matches subjects and objects case-folded without a
   leading article; `locate` retries a quote with its wrapping quotation marks off and marks
   the match `unwrapped`.
2. **The roster window hid the cast** (drafted, then subsumed by 8). Sixty entries by
   recency alone; by chapter XV chapters XII to XIV filled it, so Oz, the Emerald City,
   Kansas and Aunt Em were listed as new and judged. Replaced by the rolling roster: every
   rolling major plus the sixty most recent minors that earned a place.
3. **The model skipped established entities** (drafted). Chapter IX listed no Tin Woodman;
   Dorothy appeared in 20 of 25 units. The entity prompt now says an established entity the
   unit involves is listed again with `continues` set.
4. **Per-unit salience is loose; the document pass corrected it** (observed, no change).
   281 unit-majors, 121 not named in the model's own two-sentence summary, mostly events; the
   document pass cut it to 38 majors that read as the book's cast.
5. **One pronoun leaked into salience** (observed; PROPOSED). Chapter XXII's farmhouse listed
   "it" as a surface form and the abstract check matched it. A bare-pronoun guard on the
   abstract check waits for a ruling.
6. **Possessives inflate the judge** (observed; PROPOSED). `name_words` counted "dorothys" as
   a word, so every "Dorothy's X" paired with every other. A rule that a possessive word does
   not nominate waits for a ruling.
7. **Front matter leaked through triage by unit boundary** (observed; the extractor's).
   The extractor's unit 0 holds the Gutenberg header and the Introduction together, so the
   judge rightly kept it. Filed for Step 0.
8. **The nine rejected entity abstracts had no diagnostic** (drafted). `show_fold` now prints
   each with the names that sank it.
9. **32 adjudication retries and 16 abstract retries were invisible** (drafted). The one call
   rejected twice returned an attribute with a null value. A first schema miss is now logged
   in `retries.jsonl` and counted in the receipt; an attribute may carry a null value.
10. **373 of 869 facts were derived and discarded** because their subject was a minor with no
    major object. Ruled twice: first discarded (24), then within the hour reversed (27):
    a minor's own facts ride into the major it is tied to.

## Rulings on the design (Justin)

11. **A minor's own facts ride into the major it is tied to** (27). Under the first fact
    tying a minor to a major, the minor's facts about itself follow as lines marked `about`
    in Terra's adjudication listing, so the consolidated fact can read "Dorothy lodges with
    Boq, the richest Munchkin". In the package the riding fact is stored under the major with
    `direction: about`, an id of its own (`h(fact_id, "rides into", name, first_unit)`) and
    `provenance.rides_on` naming the fact it rides on. A minor tied to no major keeps nothing.
    One function, `landings`, decides where every fact lands; the package writer and the
    adjudication both read it. PROPOSED H widened to the third direction.
12. **Predicates are free during derive and judged after adjudication** (25). His first
    framing: audit predicates at the end and rename misfits, or drop the list and let a
    judge merge the semantically similar ones by looking at the facts beneath them. He chose
    the second, with the point that predicates only matter once the majors are ruled and
    their minor facts have rolled in. The running predicate list is out of the fact prompt.
    After adjudication, one Terra call sees every predicate the majors' consolidated facts
    use, with counts and examples, and merges a group only when one predicate fits every
    fact under it. Each adjudicated fact keeps `predicate_raw` beside `predicate`; each merge
    is a `predicate_merge` record with its reason; a merge naming nothing the document uses
    is dropped and counted. PROPOSED J: `predicate_raw` on the adjudicated fact.
13. **Rolling reconciliation** (28). His design, refined across three messages: every new
    minor is checked against the rolling majors, every new major against the rolling majors
    first and then against the minors, the lists collapsing as they go, a rolling tally of
    majors; minors are never matched against minors. The chat's shaping of it, accepted: one
    judge call per unit rather than one per step; the roster the model sees is the rolling
    majors in full plus the recent minors; the end of the document is a sweep over pairs the
    lists never met, then one last look at the deferred pairs.
14. **An instant match needs both entities named** (28). Raised by him against the chat's
    "same normalised name and kind unites on sight": an unnamed entity called "lion" or
    "girl" cannot. The rule as coded: a declared continuation unites without a judge only
    when both sides are named; a named local bearing an established named entity's name and
    kind unites on sight; everything with an unnamed side is judged with the unit's context,
    and the dossier gained a `with:` line (what the entity appears alongside) because that is
    what tells one "the girl" from another. Across documents nothing is instant.
15. **Nothing to fold, no call** (29). Offered as one of four efficiency levers after the
    chats' Terra load was estimated at hundreds of dollars; he took it and declined running
    documents in parallel ("in practice, you shouldn't be ingesting tons of novels at a
    time"). Thresholds chosen by the chat and named in the audit: a major with fewer than
    four landed facts, all from one unit, is not adjudicated and its raw facts stand; a
    document with fewer than eight distinct predicates skips the predicate judge.
16. **Effort medium to low on the judge and adjudication** (offered, not taken up). Needs an
    Oz rerun and a ledger diff before adoption.
17. **The final roll-up and the graph** (ruled, built). After each run, per document: the
    abstract, the unit summaries in order, the major entities, then everything known about
    the top five; and, in a separate block below the runs, one knowledge graph per document
    drawn the 09-02 demo's way ("just look at the last version of the ingestor and do that").

## Decisions the chat took inside those rulings

18. **Withheld text is rebuilt from the PDF** (26). The five-paper block failed because the
    public Step 0 dataset ships the reference papers with `text: null` and a `papers.jsonl`
    row. The loader now finds the PDF under the private papers dataset (or `papers/`),
    checks its sha256 against the export's record, reads it with PyMuPDF exactly as the
    extractor did (pages joined with a newline; the dataset's PROVENANCE.md wrongly says
    pdfplumber and form feeds), and checks the units end at its length. All 141 papers
    rebuild byte-identical locally. Without the PDFs the document is a clear error.
19. **Version 0.5**, bumped at stage A, since output shapes changed; `input_hash` carries it,
    so 0.4 sidecars are ignored on resume.
20. **The judge stays sequential** under stage D, because each verdict changes the next
    batch; entity abstracts and adjudications run four at a time (`WORKERS`), results kept
    in order, one lock on the run logs, a spend stop inside a worker raised to the caller.
21. **The battery follows the design, not the reverse.** Three checks had to change for
    stage B: the scripted entities were all named persons, so under the both-named rule the
    judge was never exercised; now every third unit's entities are unnamed. The stop-at test
    counted unit positions from zero while triage drops the front matter; now it stops at
    the fourth kept unit. The scripted adjudication returns a predicate spread that grows
    with the fact count and is capped under one judge slice, so books judge predicates and
    chats skip.
22. **The graph's edges** come from a major's consolidated facts where it has them, else its
    raw facts; a consolidated object is matched to a major by name or alias.
23. **Block layout**: 12 naming plus `rollup` and `draw_graph`; 13 Oz book 1; 14 the five
    papers, Zep first (in the repo now); 15 the graphs.

## Still PROPOSED for Justin

- H: `direction` on the fact record now takes `about` besides `forward` and `inverse`.
- J: `predicate_raw` on the adjudicated fact; `predicate_merge` as a record type.
- K: BUILD.md's reconciliation paragraph rewritten for the rolling design.
- The possessive nomination rule and the bare-pronoun salience guard (5, 6 above).
- Effort levels (16), and the dataset's PROVENANCE.md correction (18).

## The review

An adversarial review ran after stage D: six lenses over the diff since the ride-in (the
rolling logic, threads, landings, predicates, the gate, the design as ruled), one refuter per
finding told to reproduce it or refute it. 33 findings, 30 confirmed, 3 refuted; the full
record is `review-findings-4.json`. Every confirmed finding was fixed the same night, with
the battery at 111 checks:

24. **A declared continuation is resolved through the roster entry the model copied**, the one
    of the local's kind when several bore the name, never a same-unit sibling; when the name
    stood for several entries and none is of the kind, it is the judge's call. It never
    overrides an earlier "different" verdict (the ledger says so). The Wizard and the Land of
    Oz are both "Oz"; the old code welded a declaration to whichever bore the name last.
25. **A fresh local counts as major when its cluster does**, so the sweep no longer skips a
    major-cluster pair because the later local was a unit minor.
26. **Settled pairs are indexed once per burst**, not rescanned per candidate: the rolling
    phase and the sweep were growing cubically (a 100-unit document spent minutes in Python).
27. **Replay keeps the judge counters**, so a resumed document's completion agrees with its
    ledger; `continues` is matched loosely like a fact's subject; the ledger row for a
    declared continuation between two minors says they are not set against each other.
28. **The predicate judge follows chains to their end** (governs to rules to leads ends at
    leads for every member), refuses a blank target instead of turning it into `related_to`
    through `snake_case`'s fallback, counts repeated groups apart from groups naming nothing
    the document uses, folds a tail slice of one into the slice before it, and names the
    predicates left unjudged when a slice's reply was rejected. The after-count is computed
    from the standing set.
29. **The gate's unwrapped retry** takes one matched pair of marks (or a stray double mark)
    off and leaves a lone apostrophe, which is the text's own; the bare quote must land on
    whole words, so "Oz" cannot match inside "Ozma". A loose name that two listed entities
    share resolves neither (the fact is rejected `ambiguous_subject`); an object resolves to
    an entity only when written with a capital, so "a wizard" stays a literal.
30. **Node ids carry the kinds** beside name and first unit, since two clusters the judge
    kept apart can share both; the riding fact's id and the abstract and dossier records use
    the same key. `provenance.rides_on` now names the fact the riding fact rides under, and
    `copy_of` the minor's own raw fact it copies.
31. **The sidecar checkpoints the document-level stages** as they land (the sweep's result,
    the fold with the entities it ranked, each adjudication as it returns, the predicate
    judge), the triage row carries its cost and calls, the triage flags come back on resume,
    and a unit whose rolling judge stopped the run keeps its derive and is judged on resume.
    A resumed document repeats no unit, no judge, no fold and no finished adjudication, and
    its completion counts what was paid before the stop. Every parallel call names its major,
    so retries and rejections can be attributed.

Refuted, and left alone: a fact between two majors landing forward only (the object major's
listing does see it, as inverse); the adjudication prompt not restating inverse lines; the
census counting raw unit predicates beside merged ones (documented as such).

Residuals, said plainly: a stop during the entity abstracts still loses the abstracts that
finished, since the fold is checkpointed whole; the general gate has no whole-word rule (a
short quote written without marks can still land inside a longer word, as before 0.5); the
ambiguous-subject rejection is verified by the review's reproduction, not by the battery.

## 0.6: the reversal (09-07, after the 0.5 run)

32. **The rolling reconciliation was wrong in practice** (ruled). On Kaggle the per-unit judge
    spent $0.53 by chapter XIV against $0.14 at the same point in the 0.4 run, with sixty-odd
    "different" verdicts a chapter, because every chapter's locals were set against every
    earlier cluster that shared a word; the run stalled and ended. Justin's ruling: treat each
    unit individually with no look back, then do all the merging at the end: an agglomerative
    bottom-up priority queue of major-to-major and major-to-minor pairs, then merge the
    entities, merge the facts, and merge predicates pairwise on similarity with the judge
    naming the merged predicate. Rolling reconciliation and the document-level checkpointing
    that served it are withdrawn.
33. **No look back means no roster and no previous summary** (chat's reading of the ruling).
    The entity prompt no longer carries the established entities or asks for `continues`; the
    cells prompt no longer sees the previous unit's summary. The both-named instant match
    stays: two named locals with the same name and kind are one entity without a judge, so
    Dorothy's twenty chapters do not cost 190 judged pairs.
34. **Ellipsis quotes are kept** (ruled, from "we are dropping too many facts": the quote
    "Quelala ... the best and wisest man" was rejected as a paraphrase though both pieces were
    verbatim). A quote with an ellipsis is located piece by piece, in order, and the stored
    quote is the passage from the first piece to the last, marked `pieces`. The fact prompt
    says so. A "words" matcher that located near-verbatim citations by their words was built
    alongside and taken out before the commit, as a relaxation of the gate no one ruled.
35. **The code cut** (ruled: "cut by like 40% at min"). 3,000 lines to 2,284 (24 percent),
    with the rolling machinery, the stage checkpointing, the per-unit agreement diagnostics
    and the sliced predicate judge gone and the pairwise one in their place. What is still in
    and could go, each with Justin's say: the scored candidate rows, the profile records and
    their score, the dossier embeddings, the seeding from a prior Kaggle output, the unit
    sidecar and resume, the diagnostic flags, the top-five audit in the roll-up.
36. **A citation reworded at its edges is kept** (ruled, from "why are we dropping facts like
    this?": the model cited "she started along the road of yellow brick" for a sentence that
    reads "She bade her friends good-bye, and again started along the road of yellow brick";
    seven of its eight words stood in order). The `words` path is back, as a longest-common-
    subsequence match: the shortest passage holding at least 85 percent of the quote's words in
    order, no longer than the quote plus three words, may start at any matching word; the
    stored quote is the text's own passage, so provenance stays verbatim, and the receipt counts
    it apart so the kept facts can be read by hand.
37. **A loosely cited fact is judged where the facts are already read** (Justin: flag them and
    adjudicate them in batches at the roll-up; then "or does that even need to be done?"). Not
    as a stage of its own: the adjudication already reads every landed fact with its passage,
    so its prompt now asks for the numbers of listed facts whose own passage does not state
    them, and draws on none of those. The raw fact stays in the package with its quote, ranked
    `unsupported` instead of `active`, and the completion counts them. No extra call.
38. **Quotes are stored as text**, not only as offsets (Justin's check). Every fact record
    carries `quote` beside `quote_start` and `quote_end`; the battery slices the document at the
    offsets and requires the stored quote back, for every fact and every mention.
39. **Predicates are not merged** (Justin's ruling, 09-07, and the same ruling he gave on
    09-06: keep the model's predicate string, a census, no consolidation call). Facts are
    searched semantically; redundant facts are collapsed by the adjudication and redundant
    edges by the entity reconciliation; a merged predicate name fits neither original exactly
    and is one more place to be wrong. The chat had argued for a "consolidated vocabulary" from
    the 09-02 demo's section 9 and brought it back twice, as the sliced judge (25) and the
    pairwise judge (32); Justin: "you keep overruling me even when I am right." The pairwise
    judge, its prompt, schema, map and `predicate_merge` records are out; `adjudicated_fact`
    carries the predicate the model wrote; the census stays as a count. 2,269 lines.
40. **The adjudication names the consolidated predicates properly** (Justin, 09-07: "some of
    these predicates are pretty dumb, so a second pass needs made when the entity facts are
    rolled up at the end"). The adjudication is that pass: its prompt no longer tells Terra to
    keep the predicates the way the raw facts named them, but to name each consolidated
    relation clearly (has_aunt, is_carried_to are the examples given), per entity, with the raw
    facts keeping their own names underneath and `from_facts` tying them. No vocabulary is
    shared across entities and no call is added; this is not the merging ruled out in 39.
