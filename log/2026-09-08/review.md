# Review: the repository against itself, after the tree decision

2026-09-08, laptop. An assistant review, so by README rule every finding below is PROPOSED
until Justin rules, and each carries the design principle it rests on in one sentence. Nothing
here was applied. The laptop clone was 137 commits behind origin at the start of the session
and was fast-forwarded to `081d47f` before anything was read; the ingestor branch
`claude/infallible-einstein-e34c97` was read at `25ab88a` (this morning, 07:41).

Read: README, SCHEMA, BUILD, RESEARCH, docs/proposal, docs/entity-resolution,
docs/evaluation-corpus, dataset/step0/SCHEMA and README, every `log/` README from 09-02 to
09-07 on both master and the branch, the 0.7 and 0.8 rulings, the 0.8 worklist, audit.md Part
2, claim-search.md, plan.md, the two notebooks' block structure, and the archive leaves for
08-19, 08-26, 08-28 and 09-03.

The short version. Between 09-03 and 09-07 three decisions changed what the system is: the
global merge was deleted, identity became a tree whose parents assert nothing, and minors
became mentions that are now not even written. The code followed. The four consolidated
documents and the proposal followed only partly, and the measurement slate did not follow at
all: it still describes a three-signal merge scorer with a four-arm ablation, which is the
paper's stated central measurement and no longer corresponds to anything that runs.

## 1. Three things that are not drift, first

1. **149 reference PDFs, 338 MB, are committed to a public repository** whose own manifest says
   "not redistributed". Verified this morning: `github.com/jhffmn82/it494-memory-project`
   answers HTTP 200 unauthenticated and `gh` reports `visibility: PUBLIC`. Raised in the 09-07
   log, not acted on. Removing the folder from HEAD does not remove it from history, and the
   repository has been public since September 1, so a history rewrite is not a guaranteed fix
   either. Justin's decision; the private Kaggle dataset `it494-reference-papers` already
   holds the same files.
2. **Calendar.** Today is the "one-semester proposal form filed" row. The endorsement email
   (the "Sep 1" row, and RESEARCH.md's only item that depends on another person) was still
   unsent in the 09-05 log. The names (Palimpsest, FactLedger) were still unsaid to Fang.
3. **The ingestor branch is 20 commits ahead of master, including this morning's.** It carries
   R2, R4, R6 and the mentions ruling into SCHEMA.md; master's SCHEMA.md is therefore behind
   the code by four rulings. `git merge-tree` reports two conflicts, both log files
   (`log/2026-09-07/README.md`, add/add against the step0 branch's file of the same name, and
   `log/README.md`). Nothing in code or schema conflicts.

## 2. Concept drift: the slate describes a system that no longer exists

Principle for the whole section: **the paper may measure only what the code does.**

| Claim as written | Where | What is built (0.8) | PROPOSED |
|---|---|---|---|
| Resolution is a weighted sum of name, co-occurrence and profile; the ablation switches signals off and replays from logged per-signal scores; "the measurement I most want to land" | README.md:43, RESEARCH.md:61-67 and :92, docs/proposal.md:77-90, docs/entity-resolution.md top half, BUILD.md:56-60, docs/evaluation-corpus.md:28 | Within a document: an LLM judge over dossiers, candidates by shared surface, `is_a` link or shared word, `SIMILAR_ENOUGH = 0.35`, round-by-round pairing (decision 53). Across documents: nothing merges; an up-edge attaches a child to a parent, and "what draws the up-edge" is listed as undecided (entity-resolution.md, still-to-decide 1) | (a) Restate the ablation at the up-edge: name-only versus name plus co-occurrence (shared cast among the parent's existing children) versus name plus profile, same four arms, scored as attachment accuracy. Co-occurrence survives as a signal and the citations stand; the tree makes the replay honest, because re-pointing an edge is not a merge. (b) Drop the ablation and lead with attachment accuracy alone. Recommend (a). |
| "Entity merges are read-time redirection ... marked merged-into ... resolve() follows merged-into chains ... cluster size is capped, merge rate per chunk watched" | BUILD.md:47-60 | No merge exists. `merged_into`, `resolve()`: zero occurrences in the 0.8 ingestor | Replace the two paragraphs with the tree's rules: a child belongs to one document, a parent holds derived fields only, the up-edge carries its score and evidence and can be re-pointed. |
| Tip becomes Ozma: "aliasing, merge, supersession, time-scoped truth, at document 2" | RESEARCH.md:150, docs/evaluation-corpus.md fixtures, README | Tip appears only in book 2 and becomes Ozma inside it, so under R4 this is a **within-document** contradiction with `holds = Ozma`. Across books it is an attachment: book 2's Ozma-child and book 3's Ozma-child under one parent | Restate the fixture in those terms. It is a better fixture than before: it exercises R4 and the up-edge in one case, and "merge" appears nowhere. |
| A later same-voice fact on a functional predicate supersedes at read time | SCHEMA.md read rule; the claim-search's two surviving measurements; LongMemEval's 78 knowledge-update questions | Facts belong to one document and subjects are document-local children. "A parent counts and never adjudicates." The 09-07 log says the cross-session join "moves from ingest to retrieval and the paper should claim that", but no read rule says how | **Needs a ruling.** Proposed: supersession is a read-time view computed over a parent's children (collect the children's facts on one functional predicate, apply voice then time, serve all with the ordering), never stored. That is "N of M children say X" plus an ordering, so it does not violate the parent's silence. Without this ruling the knowledge-update band, the collision-rule measurements, and "you in August revise you in February" have no mechanism. |
| "The functional list is maintained by hand"; the paper must report supersession "beside its denominator: which predicates the functional list holds" | SCHEMA.md, BUILD.md, RESEARCH.md rules | No list exists. Predicates "stay as the model wrote them" (ingestor header); consolidation is per document; the 09-02 demo had 324 canonical forms for one book | Rule where the list comes from: written by hand for the benchmark predicates, or Step 2 maps raw predicates onto a controlled list. Until then supersession fires on nothing and the denominator is zero. |
| Mentions are "what resolution measurements read ... which is why the field exists from day one"; the long-tail instrument reads "the mention table"; BookCoref needs `Mention.span`, "cost if deferred: full re-ingest" | SCHEMA.md:76-79, RESEARCH.md:97, docs/evaluation-corpus.md:13 and :25 | Mentions are derived and not written (`6d28a7b`, ruled today; they were 53 percent of a package and Step 1 read none of them). The tree section's own replacement metric, attachment accuracy against gold coreference, reads spans | Either the three documents drop those instruments, or mentions go to a sidecar file beside the package (`mentions.jsonl`, omitted from the package proper). Principle: a measurement the documents promise needs the record it reads. Recommend the sidecar; it is the same 53 percent written elsewhere and costs no call. |
| Attachment accuracy "scored against LitBank's gold coreference" | docs/entity-resolution.md, settled section | LitBank is under Rejected in docs/evaluation-corpus.md and in the 08-28 leaf (96 of 100 documents are two chunks; no relation annotation); BookCoref was the replacement | One word: BookCoref. |
| Sep 21: "Store and pipeline working over Oz book 1"; "Storage is SQLite and JSONL" | README calendar, SCHEMA.md:4 | Packages are JSONL on Kaggle. The 09-03 PROPOSED set (SQLite as the whole store, raw bytes as a blob table, a headered vector table, the set node) is still unruled in the 09-05 open list | Rule the 09-03 set, or move the row. Under the tree the store's job has changed anyway: it holds per-document graphs plus one forest of up-edges. |
| plan.md Step 2 "SQLite store and the global merge, 14-16 hours"; Step 3 "one hop from seeds over facts" | log/2026-09-03/plan.md | Written for the merge | Banner Step 2 as superseded and describe the attachment step in its place; Step 3's hop goes up through a parent and down into another document. plan.md is provisional by rule, but it is the only build plan. |

## 3. Schema drift, record by record

| Record | master SCHEMA.md | branch SCHEMA.md | ingestor 0.8 | Note |
|---|---|---|---|---|
| header | "Nine record types" | "Nine record types" | | Ten on master (piece), eleven on the branch (contradiction). Audit Part 2 item 1, still open. |
| document | no `flags` | no `flags` | extractor writes, ingestor reads, published dataset schema declares | Audit Part 2 item 3. The public dataset's schema and the repository's disagree on the document record. |
| fact | no `occurred_at`/`occurred_until` | added (R2) | written | Master is one ruling behind. |
| cell, abstract | `scope_id`, `children_hash` | both dropped | `children_hash`: zero occurrences | `scope_id` going is right under the tree. `children_hash` going leaves rule 5 ("staleness is that hash comparison", branch line 190) and BUILD.md ("summaries rebuild only when the hash of their inputs changes") describing a field that does not exist. Field back, or the two sentences change. |
| contradiction | absent | `node_id, note, from_facts, holds, because` (R4) | written | Master lacks it. The two PROPOSED read-rule sentences in the 0.8 worklist section 3 are still awaiting wording. |
| mention | written from day one | "Mentions are not written (2026-09-08)" | derived, not written | Section 2. |
| profile | read "only by the matcher" | same | written (11 references) | The matcher that reads it is the three-signal scorer. If the judge's dossier does not include it, it is in the same class as the mentions: written and read by nothing. Check the dossier before cutting; not a ruling to take from this review. |
| node `kind` | rule 6: a type table over subject and object kinds | same | open vocabulary, 58 distinct words over 631 majors, one kind per merged entity (09-07) | A type table keyed on an open vocabulary is enforced on the six canonical words and silent on `software`, `technology`, `organization`. Say which. |
| predicate | "a small controlled list" | same | as the model wrote them, consolidated per document | Section 2, functional list. |
| salience | abstract-only route (09-04) | union of promotions, nothing demoted for salience (R6), with the merge-budget provenance recorded | R6 | Master is behind. |
| alias | `evidence_quote` | same | filled (decision 62) | Fine. |

BUILD.md, in addition to :47-60 above: "Supersession applies only to a small list of functional
predicates, and that list is maintained by hand" (no list); "Embeddings live in a rebuildable
sidecar keyed by record id and model id" (decision 54 ships no vector; decision 64 keeps the
interface; the sidecar sentence can stand but nothing writes one).

## 4. Documents that say different things

- **Corpus size.** README body: three corpora. README calendar row for Sep 14: "All four
  corpora" with the superseded note inline. docs/evaluation-corpus.md: "Our 81-work corpus"
  (after chinese/ and the Thebaid left: 68 literature works plus 20 GraphRAG-Bench novels).
  data/raw/SOURCES.md: 81 files in its header. docs/proposal.md is correct (three).
- **NarrativeQA.** README and RESEARCH say 11 works and 319 questions; the
  docs/evaluation-corpus.md table still says 12 works and 345.
- **RESEARCH.md Open list.** Item 3 (regenerate `data/clean/`) was superseded by the Step 0
  dataset; item 5 (rebuild `papers/MANIFEST.md`) now has `scripts/papers_manifest.py`, and the
  manifest header reads 142 of 157 while 149 PDFs are on disk; item 1 (endorsement) is
  still the live one.
- **README repo map** lists `data/clean/` (untracked on master) and omits `notebooks/` and
  `dataset/step0/`, which are the two folders a reader now needs first.
- **Naming.** Palimpsest and FactLedger were decided 09-03. The Kaggle dataset and both
  notebooks say FactLedger; README, RESEARCH and the proposal say neither. Say them to Fang,
  then propagate or not; half-adopted is the worst state.
- **docs/proposal.md:77-90** is the document Fang reads and it carries the three-signal claim
  and the ablation as the semester's central measurement. Whatever section 2 row 1 becomes,
  this file is the first to change.
- **log/2026-09-07/README.md on master** says "Nothing is merged. `master` has stopped at
  09-04." True when written; false since 22:31 that night. It is a dated log and should stand,
  but the branch's file of the same name is the add/add conflict in section 1.

## 5. Defensibility: the questions a reviewer asks first

1. "Your ablation isolates a signal your system does not use." Section 2, row 1.
2. "If parents never adjudicate, where is 'what is true now' computed?" Section 2, supersession.
3. "Which predicates are functional, and what fraction of the scored questions touch one?"
   There is no list, so the answer today is none and zero.
4. "Which run are these numbers from?" The 09-07 log records the same document coming back
   as 57 entities and 6 majors, then 72 and 6, then 61 and 9. Standing rule, already written:
   one stated run, or a mean with the variance reported. Every table in the paper should
   carry the run id.
5. "A quarter of your stored facts were not stated by their own quote." That was 25 percent
   on the 48-document run and 20.4 percent after the support-framing fix; R3 now corrects or
   dumps them, and this morning's pass upheld 19 of 30, corrected 8, dumped 3. Reported per
   corpus per tier, that is an instrument, not a flaw. Unreported, it is the first thing a
   reader who checks a quote finds.
6. "What does terra output cost?" Inferred, not read (09-07 open); 71 percent of the
   $11.47 run. Every terra-heavy figure is an upper bound until the price page is read.
7. "Is a parent that holds nothing and edges that are all document-owned new?" The settled
   section says it is unsearched. House rule: search before it goes near the paper. Terms
   to try first: singleton and canopy entity resolution, cluster representatives without a
   centroid, Wikidata items with referenced statements, provenance-preserving entity
   resolution, document-scoped mention clustering with cross-document linking. The 08-28
   lesson applies: the one claim nobody searched is the one that survived.
8. LitBank versus BookCoref, section 2.
9. The contamination answer (pre-1900 corpus, arm-versus-arm over identical text, NovelQA's
   depth finding, the deerstalker) still stands and travels with every result.

## 6. Repository hygiene

- The papers folder, section 1.
- Merge the ingestor branch; the two log conflicts are mechanical (keep both 09-07 READMEs
  under distinct names, or fold the branch's into master's, and rebuild the index line).
- `claude/amazing-shaw-3182ee` (08-27, laptop worktree, 42 behind at the time, now further):
  `src/it494/preprocess/` and `scripts/verify_corpus.py`, superseded by the extractor, whose
  `check()` does the sha256 verification. The `.gitattributes` fix it carried landed on
  master separately. Delete the branch and the worktree.
- The archive's laptop clone is 50 behind origin, 1 ahead, 3 files modified, and both laptop
  scheduled tasks have been Disabled since 08-29 (the PC became authoritative on 08-26, so
  that is the cutover, not a failure). Four IT 494 leaves sit in the laptop's
  `eras/_staging/` (gitignored): 08-25 phase-1 package, 08-28 doc consolidation, 09-03 build
  design, 09-03 Graphiti assessment. They will never file on their own. The tree's record of
  this project stops at 08-26; the repo log is the record after that, by the 09-03 ruling,
  but the tree should at least point at it.
- Kaggle: the old `it494-narrative-corpora-units` dataset is public, stale, and shares file
  names with the new one under a different schema; the seventeen Step 0 corrections and the
  cover image are not yet republished (09-07 open).

## 7. What is right

Numbered rulings with attribution and the reason each was taken; a 176-check battery with
refuters and a mutation script; costs measured from call logs and the assistant's own wrong
numbers recorded beside the right ones; three withdrawals in a week (cannot-link, decision 64,
the LongMemEval regroup) each with the argument that withdrew it. An extractor and an ingestor
exist, ran end to end on 248 documents for under $25, and every fact in every package
resolves to offsets in a text the reader can slice. The drift above is in the documents, not
the discipline.

## 8. Rulings requested, in order

1. The ablation: restate at the up-edge (a), or drop it (b).
2. Cross-document supersession as a read-time view over a parent's children, never stored.
3. Mentions: sidecar file, or the three documents drop the instruments that read them.
4. The functional predicate list: hand-written for the benchmark predicates, or a Step 2
   mapping onto a controlled list.
5. The 09-03 PROPOSED store set (SQLite whole store, blob table, vector table, set node), or
   the Sep 21 calendar row moves.
6. `children_hash`: back on the abstract, or rule 5 and BUILD.md change.
7. `papers/`: history rewrite, or untrack and accept the history.
8. Delete `claude/amazing-shaw-3182ee`.
9. Merge the ingestor branch (the conflict resolution can be prepared for review).
10. LitBank to BookCoref in docs/entity-resolution.md.

On any of those the mechanical edits follow in one commit each: SCHEMA.md brought level with
the branch and the header count fixed; BUILD.md's merge paragraphs replaced; RESEARCH.md's
slate, fixture row and Open list; docs/proposal.md:77-90 and :130; docs/evaluation-corpus.md's
corpus count, NarrativeQA row and mention requirement; README's repo map and calendar rows
already done (Sep 1 and Sep 2, and Sep 14 as superseded).
