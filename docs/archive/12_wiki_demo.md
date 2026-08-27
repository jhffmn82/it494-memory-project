> **SUPERSEDED 2026-08-28** by `03_design.md`. Its corpus ladder is also obsolete: the corpora are now Oz, Greek, Holmes and Chinese.
> Kept for the record; do not build from it. Index: `docs/README.md`.

# The wiki demo

An AI-generated Harry Potter wiki, built by the harness from the raw text, with generated portraits.

## What it is

The wiki is the store made visible, not a new subsystem. Entity pages render the entity layer: each attribute's current value, linked through the merge ledger to its fact rows and their quotes. Group pages are fact queries rendered as lists: Gryffindor's members, the Order's allegiance, each membership traceable to its source line. Timeline pages sort fact rows by narrative position, so a page can show what was true of a character in chapter three and what replaced it in chapter nineteen. The Scabbers page is the showpiece: a reader watches a rat become Peter Pettigrew, both states preserved, the supersession explicit, every claim quoting its page.

Portraits are the attribute layer performing: the generator reads an entity's appearance attributes (each a merged product of fact rows with quotes behind it), composes a description, and calls an image API. The picture is fun; the receipt trail under it is the point, because a wrong portrait is traceable to a wrong extraction.

## Why it earns its place

Three audiences, one artifact. For inspection, it makes induced structure browsable without reading JSONL: a projection of exactly the tree, entity, and fact layers the paper measures. For evaluation, it is the like-for-like face of the structure-versus-wiki comparison: the harness's pages beside the fan community's, with entity coverage and relation recall computable between them. For everyone else, it is the demo that needs no explanation, and a running one: the generator renders whatever exists, so the wiki grows as the pipeline matures and doubles as the project's progress report.

## The corpus ladder

The pipeline is corpus-blind: build it on Harry Potter, then run it on anything. Each rung does a different job.

Harry Potter develops and demos. The complete works of Lovecraft add two things: they are public domain, so that wiki can be published openly as a portfolio artifact, and the mythos recurs across dozens of separate stories, exercising cross-document entity resolution (Cthulhu, Arkham, the Necronomicon across many works) that no single novel can test. Sherlock Holmes, also public domain with a large fan wiki, brings a third property: adversarial contamination, since models know a century of adaptations that contradict the canon (the famous phrase that appears nowhere in the stories, the hat that comes from the illustrations). A Holmes question set filtered to canon facts that bare models get wrong from adaptation lore is a certified set with a story attached: the harness with receipts reports what the text says, the bare model what the culture believes. The cold-corpus serial then carries the uncontaminated measurement. Same pipeline, four rungs: the generality claim performing itself.

## The corpus split

Harry Potter is the development and demonstration corpus deliberately: the models know it and everyone knows it, so extraction quality is judgeable by eye and demo audiences need no setup. That same familiarity disqualifies it from measurement under the contamination rule. The measured corpus is the cold-corpus serial with its community wiki, certified per question rather than per work, where the identical generator produces the pages used in the formal comparison. Same code, two corpora: one persuades, one proves. The paper reports only the second; the demo leads with the first. A fan-built wiki of copyrighted fiction, generated for a class demonstration and not distributed, sits where fan wikis have always sat; the repository stays private regardless.

## Build note

Covered in the build plan: `jinja2` templates over the store, static HTML, no server, portraits optional and last. The generator is deliberately the smallest component in the project; its entire job is to show what the pipeline already made.
