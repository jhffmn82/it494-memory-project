# The wiki demo

Prepared by the assistant, from the student's idea: an AI-driven Harry Potter wikipedia, built by the harness from the raw text, with generated portraits. This document scopes it.

## What it is

The wiki is not a new subsystem; it is the store made visible. Entity pages render the entity layer: each attribute's current value, linked through the merge ledger to its fact rows and their quotes. Group pages are fact queries rendered as lists: Gryffindor's members, the Order's allegiance, each membership traceable to its source line. Timeline pages sort fact rows by narrative position, so a character's page can show what was true of them in chapter three and what replaced it in chapter nineteen. The Scabbers page is the showpiece: a reader watches a rat become Peter Pettigrew, with both states preserved, the supersession explicit, and every claim quoting its page.

Portraits are the attribute layer performing: the generator reads an entity's appearance attributes (each one a merged product of fact rows with quotes behind it), composes a description, and calls an image API. The picture is fun; the receipt trail under it is the point, because a wrong portrait is traceable to a wrong extraction.

## Why it earns its place

Three audiences, one artifact. For the professor, it makes induced structure inspectable without reading JSONL: a browsable projection of exactly the tree, entity, and fact layers the paper measures. For the evaluation, it is the like-for-like face of the structure-versus-wiki comparison: the harness's pages and the fan community's pages, side by side, entity coverage and relation recall computable between them. For everyone else, it is the demo that needs no explanation, and a running one: the generator renders whatever exists, so week-by-week the wiki visibly grows as the pipeline matures, which also makes it the project's progress report.

## The corpus ladder

The pipeline is corpus-blind, so one build serves many corpora, and the student named the ladder himself: build it on Harry Potter, then run it on anything, Lovecraft, Sherlock Holmes, whatever the corpus is. Each rung does a different job.

Harry Potter develops and demos. The complete works of Lovecraft add two things: they are public domain, so that wiki can be published openly as a live portfolio artifact rather than a private demo, and the mythos recurs across dozens of separate stories, which exercises cross-document entity resolution (Cthulhu, Arkham, the Necronomicon appearing in many works) that no single novel can test. Sherlock Holmes, also public domain with a large fan wiki, brings a third property: the contamination is polluted, since models know a century of adaptations that contradict the canon (the famous phrase that appears nowhere in the stories, the hat that comes from the illustrations), so a Holmes question set filtered to canon facts that bare models get wrong from adaptation lore is a certified set with a story attached: the harness with receipts reports what the text says, the bare model reports what the culture believes. The cold-corpus serial then carries the uncontaminated measurement. Same pipeline, four rungs, which is the generality claim performing itself.

## The corpus split, stated once

Harry Potter is the development and demonstration corpus, deliberately: the models know it, everyone knows it, so extraction quality is instantly judgeable by eye and demo audiences need no setup. That same familiarity disqualifies it from the measurements, per the student's own contamination rule. The measured corpus remains the cold-corpus serial with its community wiki, certified per question rather than per work, where the identical generator produces the pages used in the formal comparison. Same code, two corpora, two jobs: one persuades, one proves. The paper reports only the second; the demo leads with the first. One practical note: a fan-built wiki of copyrighted fiction, generated for a class demonstration and not distributed commercially, sits where fan wikis have always sat; the repository stays private regardless.

## Build note

Covered in the build plan: `jinja2` templates over the store, static HTML, no server, portraits optional and last. The generator is deliberately the smallest component in the project, because its entire job is to show what the pipeline already made.
