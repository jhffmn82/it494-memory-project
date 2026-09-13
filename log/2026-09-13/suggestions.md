# Suggestions after the walkthrough, 2026-09-13

Written at Justin's ask after the audit walkthrough and the venue ruling (ECIR 2027 resource
track, Nov 2). Numbered so each can be taken or declined; none is filed as a plan item until he
says so. Items 32 and 35 were discussed the same night.

## The ECIR submission

1. Ask Dr. Fang to be second author, not only the letter writer: a supervised student paper with
   the advisor on it is normal, it gets his read before submission, and a letter from a co-author
   carries more.
2. ECIR requires one author in Southampton in March. Check ISU graduate travel funding this
   month; if travel is impossible, the venue choice changes now, not in December.
3. Resource-track reviewers score the artifact: mint the dataset DOI on Zenodo before Oct 30 so
   the paper cites it, add a root LICENSE (question 10), keep the dataset card, and write an
   availability paragraph (dataset, notebooks, receipts, the test battery), which is why a
   tracked `tests/` (question 12) matters for this venue.
4. Write the paper in the LNCS template from the first draft in mid-October.
5. Put the contamination answer, the authorship disclosure and "no supersession mechanism this
   fall" in the limitations section, in Justin's words, before a reviewer writes them.
6. The two hours of reading (ASKS object by object, the tree formulation search, Story Ribbons,
   Narrative World Model) come before the mid-October draft; an unsearched related-work claim is
   what a resource track rejects.
7. Report a variance band on GraphRAG-Bench from three reruns of the questions over one fixed
   store; a single number with no band reads as one lucky run.

## The admissions case

8. Draft the statement of purpose in November around this project: a working system, a public
   dataset, measured costs, one open question owned. Have Fang and one person outside the field
   read it.
9. Line up three letters now: Fang, the GAO supervisor (recent, real work), one more ISU faculty
   member who has seen the work. Ask in October, with the preprint in hand in November.
10. Identify eight to twelve programs whose faculty publish on agent memory, KG construction or
    RAG evaluation; email two or three of those faculty in November with the arXiv link and one
    paragraph. That is what the preprint is for in an admissions cycle.
11. CV lines, exactly: "Under review, ECIR 2027 (resource track)" from Nov 2; "Preprint, arXiv"
    from Nov 3; "Dataset, DOI" from Oct 30; the Kaggle notebooks as public artifacts. Never a
    preprint listed as a publication.
12. A one-page project site a faculty reader absorbs in two minutes: the problem, the pipeline
    diagram, the two numbers, the dataset link. The README nearly is one.
13. The department symposium board tells the same story; the wiki pages over document clusters
    are what goes on it.

## The paper's content

14. The spine is the tree plus its measurement: attachment accuracy on the Oz alias set (name
    against name plus co-occurrence) and the parent-off arm on LongMemEval. Say what a positive
    and a null result each mean before either exists.
15. A cost table reproducible from receipts: dollars and minutes per stage, corpus and tier. The
    cheapest table in the paper and the one resource reviewers quote.
16. The four contamination answers apply to the novels; for LongMemEval say only that
    arm-versus-arm holds and that the comparison to Zep's run carries the training-window caveat.
17. The 14-question presence check goes in an appendix as development evidence, never as
    accuracy.

## The build, in the next two weeks

18. The global layer's design note comes before its code and is one page: what a parent is, what
    draws the up-edge (name, kind, co-occurrence), what the store must hold. Written first;
    everything follows from it.
19. In the first hour of the harness, check whether gpt-4o-mini is callable; it decides whether
    any number is comparable to a published one.
20. Each benchmark's own published evaluator; no judge built. Thirty hand-checked verdicts after
    the first scored run, as a sanity check only.
21. The Oz alias set in week 2, one hour: the only gold there will be, and the ablation needs it.
22. The two Kaggle fixes before any scaled run: one JSONL per history in the output, and the
    block budget.
23. The 8-character `doc_tag` collision fixed before packages are loaded into one store.
24. The page-date gate (translation years) and the three Scientific American dates fixed after
    the merge, and the Step 0 docs republished (question 4) with those and the "15 undated"
    correction in one push.
25. The ingestor stays frozen; every improvement goes to a spring list; the fall's numbers come
    from one version.

## Process

26. The addendum to Fang this week, one page, from the proposal's change list, with the venue,
    the arXiv endorsement ask (the January 2026 policy) and the co-authorship ask in it.
27. Ask what IT 494 itself grades before the addendum; a required report or talk changes
    November.
28. Real hours into the tracker every Sunday; the plan re-prices on Sep 20 and nowhere else.
29. The daily log written on the day. The three missing days this fortnight are the days whose
    rulings had to be reconstructed.
30. One thread does git; every other thread hands its work to it (ruled 09-12). Tonight's forty
    commits came from a week of breaking that rule.
31. The twelve questions in `questions.md` and the ten in the plan's section 5, one a day rather
    than in a batch, starting with the reader model and the tracked `tests/`.

## Risks named now

32. The full-context arm on LongMemEval: a history averages about 115,000 tokens and 429 of 500
    exceed 120,000 at four characters a token, so a 128,000-token reader (gpt-4o-mini, Zep's
    baseline model) cannot take the longest whole. Whatever is dropped and how (oldest first, a
    hard cut) changes the baseline. If the reader's window holds the longest history, the rule is
    "nothing dropped" and is stated in one sentence; if the reader is gpt-4o-mini for parity, the
    benchmark's own truncation rule is used and cited. Decided with the reader model (plan
    ruling 2), written into the harness and the paper.
33. If the pace really is eight hours a week, ECIR is still reachable with GraphRAG-Bench alone
    and LongMemEval becomes the appendix. Decided Sep 20, not Oct 24.
34. The reference PDFs remain in public git history (ruled left); the paper's availability
    statement points at the current tree, not a commit range.
35. The personal archive never enters the paper, the dataset or the demo; the proposal says so;
    the admissions statement keeps it to one sentence.

## Spring, written down once

36. Maintenance (re-ingest, refold, delete), deployment, the living stream, the
    assembled-versus-generated probe, NarrativeQA, the cells ablation, the three-tier pilot, and
    a journal version (PVLDB or a data journal) built on the ECIR reviews.
