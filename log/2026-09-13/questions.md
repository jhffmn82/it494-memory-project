# Questions left open by the cleanup of 2026-09-13

**Answered the same evening: yes to all nine** (Justin). Done on the spot: the SCHEMA and BUILD
commits stand; history is not rewritten; the five merged local branches and their two remote
copies are deleted (two locals stay because worktrees hold them); the one-history rule is in
`docs/rulings.md`; the root files moved with the reading apparatus. Left for Justin's own CLI:
questions 3 and 4 (Kaggle). Then a further ruling: the repository is reduced to what a person
reads, with the working tooling untracked on disk (see `docs/rulings.md`).

For Justin, one at a time, each with a recommendation. Nothing below was acted on. The
cleanup itself (the missing logs, the index, the rulings ledger, the master documents, the
archive) is committed on `claude/kg-rag-cc-corpus`; SCHEMA.md and BUILD.md carry PROPOSED
commits (89c45e8, 414fff3, e7488f5) that stand only on a ruling.

## 1. SCHEMA.md and BUILD.md: accept the PROPOSED commits?

What changed in SCHEMA.md: every unit dated with the date forms and their source in `flags`; the
day cut and "never a lone turn" gone; a chat is one document with one unit per turn; `flags`
declared on the document record; `mention` removed from the record list (not written since
09-08); `valid_to` dated as held 09-09 and dropped 09-10; decision 52's demotion, the
minor-subject rule and the standing `user` major stated; ids described as content hashes for
documents and units, readable for entities and facts. In BUILD.md: loaders date every unit and
piece; one model interface (`generate`) in the ingestor, `embed` named as serving-side and not
built; no cross-unit context (decisions 31 and 33); no dossier text. Recommendation: accept; every
sentence traces to the code that ran. If any sentence is wrong, name it and I revert that one.

## 2. The reference PDFs in public history

150 PDFs (the 142 reference papers, 7 retired, the ASKS paper) were pushed to the public
repository from its first commits and are still in every commit before 2026-09-13. They are
untracked at HEAD now. Two options: (a) leave history as it is and rely on the untracking; (b)
rewrite history (`git filter-repo --path-glob 'papers/*.pdf' --invert-paths`) and force-push,
which changes every commit hash, breaks every branch and worktree that is not rebased, and needs
every collaborator (there are none) to re-clone. Recommendation: (a) for now, since nothing links
to those files and the risk is a takedown request rather than an exposure; (b) only if the repo
is to be cited in the paper as the artifact. This is the only item where I would not act alone.

## 3. Stale Kaggle artifacts

Public and superseded: dataset `jhffmn/it494-narrative-corpora-units` (09-01) and notebooks
`it494-narrative-corpora-splitting-and-gates` and `it494-chapter-ingestion-oz-book-1` (09-02).
Private and unused: dataset `jhffmn/it494-reference-papers`. Recommendation: add a "superseded
by it494-threadatlas-step0" line to the units dataset's subtitle and description and leave the
notebooks (they are the 09-02 record); delete the private papers dataset, since nothing mounts it
and its contents are the redistribution question above. The CLI blocked my metadata download;
to do the first:

```powershell
kaggle datasets metadata -p C:\Users\jhffm\kmeta-units jhffmn/it494-narrative-corpora-units
```

then edit `subtitle` and `description` in the downloaded `dataset-metadata.json` and run
`kaggle datasets metadata --update -p C:\Users\jhffm\kmeta-units jhffmn/it494-narrative-corpora-units`.

## 4. Republish the Step 0 docs?

`dataset/step0/README.md` and `dataset-metadata.json` now say "every unit dated where a source
gives a date (15 are not)" instead of "every unit dated", the quick start has no lambda, and the
one em dash is gone. The published 1.8 version still carries the old text. Recommendation: push
the five docs as a new version with no data change (`kaggle datasets version -p <staging>
-m "docs only"` after copying the five files beside the unchanged JSONL). Low priority; the data
is right.

## 5. Only one history in the graph?

The brief for the global thread says only one LongMemEval history is ever loaded into the graph.
Block 12 loads history gpt4_2ba83207 (53 sessions) plus the answer sessions of 13 other
questions (18 sessions) so that all 14 question types can be checked, and every one of those
sessions is a separate document with its own date. If the global merge reads every package in
the output, it builds one graph over 14 users' timelines. Options: (a) the global merge takes a
history folder as its input and reads only packages whose `source_uri` starts with it; (b) block
12 stops loading the other questions' sessions. Recommendation: (a), and record it as the rule
in `docs/rulings.md`; the answer sessions stay as the Step 1 check.

## 6. Branches

Merged into HEAD and deletable: `claude/focused-robinson-ec8930`, `claude/sleepy-benz-ef2ef7`,
`claude/step0-raw-dataset` (also on origin), `claude/upbeat-engelbart-aba388`, `ingestor-1.7`
(also on origin). Not merged: `fold-09` (on origin), `review-09`, `claude/infallible-einstein-e34c97`
(on origin; the Step 1 thread's worktree, still checked out under `.claude/worktrees/`).
Recommendation: delete the five merged local branches and their two remote copies; keep the
three unmerged until their threads close. Local deletion is `git branch -d <name>`; remote is
`git push origin --delete <name>`.

## 7. Two root files

`advisor-meeting-2026-08-19.md` and `reading-list.md` sit at the repository root. Both are
reference, not current design. Recommendation: leave them; `reading-list.md` says it supersedes
the meeting record and both are linked from README.

## 8. Em dashes inside dated logs

Eleven log files carry em dashes (09-07 decisions and worklist, 09-08 forward plan, review and
decision record, and the two run-log Python copies). The logs are snapshots and were not
touched. Recommendation: leave them; the rule applies to master documents and published
artifacts.

## 9. Open items no ruling closed (from the logs, for the global thread)

- The R4 read rule's two PROPOSED sentences (09-07 worklist) never entered SCHEMA.md.
- Terra's output price is still inferred, not confirmed against a bill.
- `log/2026-09-06/test_ingestor.py` is dead since 6da9186; the live battery is
  `log/2026-09-08/test_ingestor.py` (a scratch copy at 94 checks ran the frozen version).
- The page-date gate passes a translation year (Sophocles 1912); fix after the merge.
- Facts under majors with 4 or more facts get no support call.
- `docs/entity-resolution.md` still names LitBank as the attachment-accuracy gold; the 09-08
  review proposed BookCoref. Not ruled.
- The chat log line prints `turns {len(pieces)}`; the tail merge ignores the cap (both extractor,
  both cosmetic since 1.7).
