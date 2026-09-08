# Forward plan: execution timeline to the fall paper

2026-09-08. The build sequence and the paper, on one calendar, back-planned from arXiv Nov 16.
Two tracks run in parallel from mid-October: **build** (produces the numbers) and **write** (the
results-independent 60% does not wait for them). The hard rule: **build stops Oct 31**, because the
two weeks after it are the advisor-review cycle and cannot be compressed.

Fixed anchors: open block 1 now–Sep 27; exam block Sep 28–Oct 18 (little build); open block 2
Oct 19–Nov 15; Zenodo DOI Nov 10; freeze Nov 15; arXiv Nov 16 (avoid Nov 23–27).

## Decisions to lock this week (they unblock the build)

- **Up-edge signal** (ruling 1): restate the resolution ablation at the tree's up-edge as
  attachment accuracy. Settled empirically when Step 2 runs; name it now so the build logs
  per-signal scores.
- **Cross-document supersession read-rule** (ruling 2): a read-time view over a parent's children
  (collect facts on a functional predicate, apply voice then time, serve all). Needed to score the
  Oz temporal claim.
- **Functional-predicate list**: hand-write it for the benchmark predicates, or LongMemEval
  measures nothing.

## Build track

| Phase | Window | Deliverable | Acceptance / gate |
|---|---|---|---|
| **Step 1 — ingestor 0.9** | now | the current run finishes | packages written; battery green on Kaggle |
| **Step 2 — global** | Sep 8–27 | tree-attach over the two-clouds-plus-noise sample (Oz ×N + ~10 papers + Greek/novel/chat noise) | attachment precision **and** recall scored against a hand-labeled gold set (both failure directions); Tip/Ozma renders; the homonym noise does not black-hole. Settles rulings 1 and 2. |
| **Step 3 — SQL** | late Sep – mid Oct | SQLite store; private extractor export that keeps paper txt (freezes offsets); ingestor reads the frozen txt; drop fact `quote` strings (offsets remain); public/private text split; add the bge-small embedder (rebuildable sidecar) | store built from packages; every quote resolves from offsets; public dump validates (paper text null, rebuildable); embedder builds |
| **Step 4 — benchmark harness** | Oct 19–31 | the arms (= the retrieval path: FTS5 + sqlite-vec + fusion + packer), per-dataset evaluators wiring each benchmark's own scorer, the parity check, judge calibration | each arm returns; parity reproduces the published plain-RAG baseline (or numbers become ratios) |
| **Floor benchmarks** | Oct 19–31 | in priority order: parity check → clean-Oz attachment (BookCoref, the spine) → clean GraphRAG-Bench QA → NarrativeQA → LongMemEval parity + update band → free instruments + MemTree cost curves | one stated run each, with a variance band over k reruns |
| **HARD BUILD-STOP** | **Oct 31** | — | whatever is not measured by now is not in the fall paper |

The floor uses **clean per-benchmark stores** (the only runs comparable to published baselines).
The combined-store run is wishlist.

## Write track (parallel)

| Phase | Window | Deliverable |
|---|---|---|
| Endorsement + proposal | this week | arXiv cs.CL endorsement email to Fang (longest human lead, not build-gated); one-semester proposal form filed |
| Results-independent skeleton | exam block, done ~Oct 18 | intro, related work (prose exists in `docs/related-work/`), method/architecture (the tree, provenance, merge-free), dataset (Step 0), contamination framing — none of it needs results |
| Full draft to Fang | **~Nov 3** | results and tables slotted into the skeleton |
| Fang review | ~Nov 3–9 | advisor comments back (≈1 week; do not assume faster) |
| Revise + DOI | Nov 9–14 | incorporate; Zenodo DOI by Nov 10; final polish |
| Freeze → arXiv | Nov 15 → 16 | resource-and-experience paper, cs.CL |

## Wishlist (only if the floor lands clean; never blocks the paper)

- **Combined-store interference** — replay every package into one store, rerun the same arms, report
  the delta against your own clean number (the LongMemEval oracle-vs-`_s` shape). Cheap once the
  floor exists (a replay; only the cross-corpus judge is new). Highest paper-upside item; also the
  one that could return a bad number, which is why it stays wishlist.
- **Assembled wiki** — the three fixture pages (Oz/Tip-Ozma, Holmes/deerstalker, Greek/Helen), each
  as the assembled-vs-generated pair, behind the three ship checks, hosted as an HF static Space.

## The argument the paper makes

Not "we beat them." On its own benchmark: **competitive accuracy within X points at 1/N the token
cost, every answer quote-backed, no graph DB, no server** — the 377-fold GraphRAG-Bench token spread
is what makes "almost as well" read as "much better product." Then, if the wishlist lands: accuracy
moves only δ in a store that also holds y and z. Clean-vs-published and combined-vs-your-own-clean
are different columns with different denominators; never cross them.

## The honest risk, and the three release valves

Steps 2–4 plus the floor are the unbuilt critical path, and the slate is priced at 69–118 hours
against ~64. The plan closes only with discipline:

1. **Write the skeleton during exams** so November is results-only.
2. **Floor-only.** Cut the wishlist (interference, wiki) without hesitation the moment time is tight.
3. **LongMemEval is the first benchmark to cut** — it needs the predicate list and measures the
   least of the five.

The one dependency that is *not* build-gated and has the longest lead is the endorsement email.
Send it now. The Oct 31 build-stop is what protects the Fang review window; if the build slips past
Nov 1, the review cycle is what dies.

## Fall / spring boundary

Fall ships the methodology (the notebooks), the numbers, the dataset, and — wishlist — the wiki.
Spring develops the notebooks into the desktop product (engine, MCP/HTTP/extension, workspaces,
auth, ingest-by-watching), re-points the same store schema at real data, and is out of scope for
the fall paper.
