# Ingestor decisions, 2026-09-07 (0.6 to 0.7)

Continues `log/2026-09-06/decisions-ingestor-0.5.md`, which ends at item 41. The day's work
began with an outside audit thread's critique of the head at `f3d8e4e` and the 0.6 Oz pass.
Every item in that critique was reproduced against the code before it was answered; the
verifications are summarised in `audit-answers.md`. What follows are the rulings Justin gave
in reply, one at a time, and the code that carries them.

Justin's words are quoted where they settle a point. Where a ruling reverses something the
chat had built or recommended, that is said plainly.

## The rulings

42. **The document fold may use the document's own names** (Justin, ruling 1, option d). The
    fold's fabrication check counted any capitalised run that no unit summary contained as an
    invented name. On Oz the fold was rejected twice, so the document had no abstract, salience
    fell to the tie-break rule (two units or two facts), and 92 of 282 entities became majors,
    each buying a dossier, an entity abstract and a Terra adjudication. The document's own
    entity names and surface forms are now allowed names, as they already were for an entity
    abstract. The fallback threshold itself stays as decision 16 wrote it.

43. **A small entity's facts are read on the cheap model rather than not at all** (Justin:
    "why not use a luna call for a small judgement", then "fewer than 4 facts, use luna").
    Decision 15 skipped the adjudication for a major with fewer than four facts from one unit,
    which was right when that call only consolidated. Decision 37 later made the same call the
    only check that a fact's passage states it, and the threshold was never revisited: 22 of 92
    majors in the 0.6 pass had their facts stored `active`, unchecked. Now a major with fewer
    than four landed facts, from however many units, gets a support-only call on Luna: the
    facts, numbered, each with its passage, and one question, which of them their passage does
    not state. The one-unit condition is gone.

44. **No cap on the reconciliation queue; two pruning rules instead** (Justin, ruling 3:
    "C, a couple of things to make it easier. Never try to merge any entity that contains merged
    entities that existed within the same unit. once a rejection was made, never try to merge
    entities that contain pieces that have already been ruled not the same"). Two clusters that
    each hold a local from one unit are never paired, since that unit already listed them as two
    things; two clusters holding a pair the judge ruled different are never paired again. Both
    are enforced at nomination, so the saving is in local work rather than judge calls. The
    three verdicts the second rule needs already exist: same, different, unsure.
    Cost, stated once and then built: if a unit names one thing twice, say "the Wizard" and "Oz"
    before the reveal, the first rule keeps them apart for the whole document.

45. **A consolidated fact is redundant facts merged, so one supported source carries it**
    (Justin: "if a consolidated fact is consolidated from other facts, it has sources", then
    "no, consolidated means REDUNDANT so one quote should work"). The chat's first reading, that
    the consolidated fact keeps every source and takes the rank of the worst, was wrong and is
    withdrawn. The numbers the same reply set aside come out of the fact's source list; if a
    supported source remains the fact stands with that list; if none remains it is dropped and
    counted, exactly as an item pointing at nothing already was.

46. **A quote may not span a change of speaker** (Justin: "quotes can't span cross speakers.
    Break it into two", then "or, multiple authors stated the same fact"). The pieces path could
    return a span running from a user turn into an assistant turn, and the fact was filed under
    whoever held its first character; widened, one quote covered a whole session. The located
    span is now cut at every piece boundary inside it and stored as one fact per voice, each
    with that voice's words and author. Two speakers who state the same thing are two
    attributions of it, so the duplicate key carries the author: a fact repeated by one speaker
    is still one fact.

47. **The words path takes only edge rewording** (Justin, ruling 6, option a). Decision 36
    accepted a citation holding 85 percent of its words in order. Measured on 200 sentences of
    8 to 25 words from each of Oz, Holmes and the Greek corpus, a word invented at the midpoint
    was accepted 87 to 91 percent of the time, and the stored passage was the text's own words
    without it, so a negation could vanish from the evidence. The unmatched words must now fall
    at the front or the back of the quote, never inside the matched run. Measured cost: about
    one in eight genuine edge-reworded citations, nearly all of them sentences with a
    contraction or a hyphen, which the tokeniser fix in the same commit addresses.

48. **A node id is the moniker and its first mention** (Justin, ruling 7: "node_id can't be a
    hash of a single document at the global level. However, a node_id at the document level can.
    When the entities are merged, and a moniker is selected from all the surface values, the
    node_id should be the first mention of that surface value in the document"). Decision 30's
    key was name, first unit and kinds, all three of which two clusters the judge kept apart can
    share; reproduced, and the package then wrote two nodes with one id. Said once: two clusters
    that pick the same moniker also share its first mention, so an unnamed pair can still
    collide, and `write_package` therefore refuses to write two nodes with one id instead of
    merging them quietly. The global id is Step 2's business.

49. **The same name and kind unite on sight only when nothing in their `is_a` conflicts**
    (Justin, ruling 8: "i think we have to do b"). The Iliad has two men named Ajax: 34 of its
    63 units mention one, 9 name both patronymics, 12 carry the bare name with nothing to tell
    them apart. Oz has the Wicked Witch of the East and of the West with 9 bare "Wicked Witch".
    A conflict now sends the pair to the queue and the judge. The chat recommended leaving the
    rule alone and was overruled; its cost estimate for doing so was also wrong, see the
    correction below.

50. **Every entity's facts are read before anything rides** (Justin: "but his facts should be
    adjudicated prior to being delegated as a minor"). A unit-major demoted at the document
    level keeps its facts only by riding into a major, so under the old order a rider's support
    was never checked. Now a document major goes through the Terra adjudication as before and
    every other entity with facts of its own gets the Luna support call from 43. A rider arrives
    carrying a rank earned on its own quote, and the tie keeps its own rank, so the question the
    chat had put as ruling 9, whether a rider inherits its tie's rank, does not arise.

51. **A re-nomination sweep, and what makes a pair eligible** (Justin, ruling 11: "a, but, pairs
    that contain children that have been ruled appart should not be considered", then "the
    eligibility of pairs should be determined by both the similarity of the parents and the
    prior rulings against children"). A merged cluster carries the union of its members' surface
    forms, so a pair with no reason at the start can acquire one. When the queue is exhausted
    the pairs are nominated again; only new and eligible pairs are judged; the rounds stop when
    one brings nothing new. Eligibility is the parents' similarity together with 44's rules.

52. **An entity the document cannot summarise is not a major** (Justin: "at the document level
    anything that can't get a short abstract shouldn't be a major entity"). This replaces the
    chat's proposal of a word-count floor on the fold, which is withdrawn. An entity whose
    abstract is rejected or which has nothing to summarise falls to minor, and its facts ride
    into the majors as any minor's do. It is also the salience test the 92-major fallback
    lacked.

53. **The clustering pairs entities off round by round** (Justin, in his own words: "all
    existing entities entered into clustering, for each entity in clustering its similarity is
    compared to all other entities in clustering, then those above threshold are filtered by
    eligibility, then top pair both removed from clustering and entered into pairing queue. When
    no entities remain in clustering consideration, check each in queue and repeat until nothing
    is queued"). This replaces the single all-pairs queue and the sweep of 51, which are gone.
    No entity is in two pairs of one round, so a round's merges cannot conflict and the
    transitive union that A7's refusal was written for cannot arise inside a round; the refusal
    stays as a guard the rules should make unreachable. Every round re-scores against the merged
    clusters, so the strongest evidence merges first and the later rounds see fewer, larger
    clusters. The threshold is now explicit, `SIMILAR_ENOUGH = 0.35`, the demo's old keep-apart
    line; on the battery's scripted Oz the rounds converge 19, 9, 3, 1, judging 32 pairs in 6
    calls where 144 unit-locals become 47 entities.

54. **The package ships the dossier text and no vector** (Justin: "my understanding of the end
    state is we will be using a model agnostic light weight embedder, so caching the embeddings
    of raw text into global serves no purpose and might not be used. But maybe at a future time,
    assuming a constant model on the backend, it might make sense"). The embedding call and the
    stored vector go; the dossier text stays, so a vector can be built whenever the backend
    model is settled. It was also most of a package's size: 1,536 numbers for every major.

55. **One switch for the diagnostics** (ruling 14, option a). Eleven flags and the dict threaded
    through `ingest`, `run`, `show_unit` and `show_reconcile` become `WATCH`. Only two
    combinations were ever used, and both printed everything.

56. **RUN always names documents** (ruling 15, option a). `sample()` and the `"sample"` and
    `"all"` specs go; `"all"` on the present export would have tried 19,206 chat sessions. The
    three test runs are their own blocks.

57. **The scored candidate rows stay** (Justin: "yes, keep it so we can audit this. it's
    essentially just a log that doesn't affect anything"). They never leave the package;
    `docs/entity-resolution.md` asks for exactly this log, with each signal scored separately and
    the rejected pairs kept, because merge precision and candidate recall are computed from it.

58. **`manifest.jsonl` goes** (ruling 17, option b). The receipt sums every package on disk and
    each package's completion record carries its own counts, so the manifest was a third copy.

59. **The package header record goes** (ruling 18, option a). Three of its six fields repeated
    the `document` record on the next line and the rest are in the completion, which is what
    `completed`, the receipt and the roll-up all read.

60. **The `predicates_distinct` count goes** (ruling 19, option a). It counted consolidated
    predicates while the census in the same package counts raw ones: two numbers with one name.

61. **A node says whether the document ever named it** (ruling 20, option a). The field existed
    on the merged entity and was read by nothing and written nowhere; now it is written, so Step
    2 can apply the both-named rule across documents rather than guessing from the aliases.

62. **An alias carries the sentence it was first read in** (ruling 21, option a). `evidence_quote`
    was a constant null; it now holds the sentence around the form's first mention. The profile's
    `confidence` was a constant 0.5 and is gone, with SCHEMA.md amended, since the paragraph
    above it already says these rows are low-confidence by definition.

63. **Triage may not leave out more than half a document** (ruling 22, option a). `audit.md` said
    that and the code guarded only the everything case; the code now matches the text, ignores
    such an answer, reads every kind, and records the flag.

64. **Withdrawn within the hour: the embedding interface stays** (the chat proposed cutting
    `embed(texts)`, the model id and its price row, since decision 54 left the connection ping
    as their only caller; Justin: "wait scratch that, keep the embedding ID", and on the
    follow-up, "just interface"). The removal was made and reverted at `2f093a4`, and BUILD.md's
    "two interfaces" paragraph stands as written. What decision 54 settled is unchanged: the
    package ships the dossier text and no vector, and the dossier record carries no
    `embedding_model` either.

## Two corrections to the chat's own claims

- **The judge does not cost 190 pairs for a twenty-chapter character** (Justin: "it shouldn't
  cost us 190 pairings because they are all done at the end and bottom up, so it should instead
  be log n"). He is right. The queue resolves each pair through the cluster roots before
  judging, so once two Dorothy locals unite every later pair against either maps to the same
  root pair and is judged once: about nineteen judgments in the worst case, and the simulation
  in the audit's own item 11 shows roughly fifty judged pairs for a 25-unit novel. The estimate
  that argued against decision 49 was wrong by an order of magnitude.
- **Bands are not needed, because the queue is already banded** (Justin raised threshold bands,
  then "maybe it should instead just be a queue"). `nominate` sorts by reason first, shared
  surface, then `is_a` link, then shared word, and only then by score, and roots collapse as the
  judge goes. The one thing bands would have added, pairs that gain a reason after a merge, is
  what decision 51's sweep does in five lines.

## What the audit found that was not a ruling

Confirmed and fixed without a ruling, each with a reproduction and a battery check: the
roll-up's dead `predicate_raw` read, which crashed every run after the money was spent (A1);
the whole-word test that read its boundary characters from the raw text after finding hits on
the normalised copy, so half a hyphenated word could be stored as a verbatim quotation (A5);
the union inside one judge batch that could undo an earlier "different" verdict (A7); the
adjudication judging support on a quote truncated at 120 characters (A10); a cell dropped in
silence when the model spelled the entity differently (A13); a sidecar torn by a kill hiding
every unit a resume then paid for (A14); the version label that had not moved across four
commits that changed what is written (A12); salience compared case-sensitively (E5); the
roll-up reading a package without the completion check every other reader applies (E8).

Refuted, with evidence: the claim that 23 facts vanish between kept and stored (they are the
distinct riding facts, now counted, and the arithmetic closes at 948 kept, 31 riding nowhere,
34 riding, 925 stored, A15); that a document could be silently emptied by triage (the guard
exists and fires, E2); that a resumed document under-reports its cost (unit costs are stored in
the sidecar and summed, E7); that a timing-out call can bill unlogged (every attempt is logged,
E12).

Documentation mismatch for Justin to settle in `audit.md`, not a code defect: the text says
triage is capped at "more than half the units" while the code guards only "every unit".
