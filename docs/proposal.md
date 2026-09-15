# Persistent memory for a desktop assistant

Justin Hoffman. IT 494, Fall 2026. Supervisor: Dr. Xing Fang. Revision of
September 13, replacing the draft of August 31 that was filed with the
advisor; the changes are listed at the end.

## The problem

Conversational AI retains nothing between sessions. The standard remedy,
retrieval-augmented generation, indexes past text and returns passages that
look similar to the question. That answers "what did I say about X" but not
"what is true of X now." Similarity ranks a superseded statement as
confidently as the statement that replaced it, offers no account of where an
answer came from, and cannot say that two phrasings are one fact. "Jenny is
employed by GAO" and "Jennifer works at the Government Accountability Office"
are the same fact, and a system that stores them as two passages does not know
that.

I have run a personal memory system over my own AI conversations for two
years, roughly a thousand distilled summaries over twenty million tokens of
transcript. It works well enough to use every day and it taught me where the
real problems are: deciding that two names refer to one thing, keeping facts
current without destroying the record of what was believed before, and
compressing a long history into something a model can actually be handed. That
system was built to prove the idea. This project builds the real one and
measures it.

## What gets built

The end product is a backend for a desktop AI client. It ingests documents
and chat logs, and from them builds three layers: entities with their aliases,
dated facts with verbatim supporting quotes, and a running narrative of each
entity across the source material. A client reads those layers as context.
Facts are never overwritten. A new fact supersedes an old one at read time,
and the superseding is itself part of what the system knows. Across sources
nothing is merged: each document keeps its own version of an entity, and an
edge attaches it to a parent that holds only a derived name, kind and
summary and asserts nothing of its own, so re-deciding an identity re-points
an edge instead of rewriting records.

The pipeline has five stages, and the first two are built and measured:

1. **The extractor** reads a raw file and nothing else, sniffs its format from
   the bytes, and has a model point at every boundary by line number while
   code verifies the copy. Every unit is dated: a chat turn by its timestamp,
   a book or paper by when the work was written. It ran over the whole corpus
   on September 13 for $8.24 and is published with its data.
2. **The ingestor** turns one document into a package: entities, facts behind
   a quote gate (a fact whose quote is not found verbatim in its unit is never
   stored), a narrative cell per entity per unit for books and papers, and an
   abstract. A chat session is read in one call, each fact tied to its turn.
   Frozen on September 12; a chat session costs under half a cent.
3. **The global layer** clusters each document's entities bottom up into
   parents, a judge ruling each pair from the texts and the parents written
   once after the clustering. Built first (09-14), because the database schema
   and the embedding followed from it.
4. **The store and the query path**: SQLite with full-text search, a local
   embedding sidecar (a small model run on the user's own machine), and
   hybrid retrieval, keyword and vector fused by rank, that returns whole
   records with their dates and sources.
5. **The harness** that runs a benchmark's questions through the query path
   and scores them with the benchmark's own evaluator.

The fall builds and tests this on public text rather than on private data, for
one reason: you cannot publish measurements taken on a personal life. The
working hypothesis is that fiction fed in narrative order behaves like a life
recorded in chat, and that a benchmark of simulated chat histories behaves
like the real thing. The corpus, all of it public and licensed for
redistribution: three public-domain literature corpora (the Oz canon, the
complete Sherlock Holmes, the major Greek and Roman sources; 69 files), the
20 GraphRAG-Bench novels, 100 CC-BY research papers on knowledge graphs and
retrieval, and the 500 chat histories of LongMemEval, 24,071 documents in all.
Oz supplies the supersession fixture (a boy named Tip is revealed to be the
princess Ozma, and everything asserted about Tip stays true of its period);
Holmes a contradiction Doyle never reconciled; the Greek corpus disagreement
between sources and free entity-resolution pairs; the chat histories the
shape of the end product's real input.

## What gets measured

I checked twelve candidate ideas against published work and every one of them
is already taken. That settles what kind of paper this is: here is a working
system, and here is what each part of it is worth, measured. Novelty is
conceded in the introduction; rigor is the price.

Four measurements are committed for the fall.

First, question answering on GraphRAG-Bench: 2,010 questions with gold
answers over twenty pre-1900 novels, where nine systems have published
numbers under one reader model. Arms: no context, flat retrieval over the raw
text, and the full system; the benchmark's own plain-retrieval baseline is
reproduced on my harness before any comparison is claimed. Their results give
the target: the best system spends about a thousand tokens per question and
the most expensive over three hundred thousand, so accuracy per token is
where a serverless design can show up.

Second, question answering on LongMemEval, the chat-memory benchmark where
the nearest commercial system published its numbers. One history is one
graph. Arms: full context, flat retrieval over raw turns, the full system, and
the full system with the parent join switched off, which measures what the
global layer buys instead of asserting it. The questions used to tune the
ingestor are excluded from every reported number. The knowledge-update
questions are reported as accuracy; no read-time supersession mechanism is
claimed this fall.

Third, the instruments that fall out of running the pipeline at all: the rate
at which extracted quotes fail to appear verbatim in their source, rejections
per stage and model tier, token cost per stage, duplicate parents per history,
and agreement between unit summaries and entity narratives, which describe
the same text independently and catch each other's omissions.

Every model call goes through one narrow interface, `generate(prompt,
schema)`, and every run records which model and tier ran each call and what
it cost; an embedding interface joins it with the store. The pipeline is code
I direct, review and answer for end to end, drafted with AI assistance under
my rulings and checked by an offline test battery; the model is the only black
box. Each benchmark is scored with its own published evaluator, on one reader
model for every arm.

Also this fall, after the numbers: wiki pages over document clusters, rendered from the store, an afternoon's work that makes the store visible. Fourth, the one question in the design that is genuinely open: whether the relational signal
still pays when the candidate scorer is an embedding and a language model. Every system I
compare against attaches or merges entities on name similarity or a model's verdict; mine can also
show the judge the surrounding cast, the names each entity appears beside, at the point where
two documents' entities are ruled the same. The two arms are full builds, the judge shown texts
alone against texts plus casts, scored as attachment accuracy against Wikipedia's list of
Baum's Oz characters. The parents that documents share are what cluster the documents into
collections for the wiki pages.

Deferred to spring, with reasons recorded: NarrativeQA; the assembled-versus-generated
fabrication probe; the narrative-cell ablation; the three-tier model-sensitivity pilot; and
maintenance, deployment and a living stream of data.

## The calendar

Dr. Fang approved the topic change in person on August 28. The semester has
two open blocks, now through September 27 and October 19 through November 15,
with three exam weeks between them.

By September 13 the extractor had run over the whole corpus and the dataset
was published; the ingestor was frozen and measured. By September 20 the
global layer, the store and the embedding exist over a test set of packages
(71 chat sessions, three Oz books, five papers, two plays). By September 27
the harness runs a question end to end through them on both corpora, and
testing begins. In the exam block the pipeline is tuned on that test set until
it is ready, and only then does the full corpus go through it, in batches,
while I write. A first draft of the paper is due in mid-October with whatever numbers exist by then; the build stops October 25; the paper is complete by October 30 with the dataset's DOI; it is submitted to the ECIR 2027 resource track on November 2 and posted to arXiv the next day. The ECIR decision comes December 7; if it is rejected, an EACL 2027 workshop takes it on December 15.

The spring semester wraps the proven methodology in the desktop product,
points it at real chat exports, and ships something a person can install.

Hours are the binding constraint. Compute is measured, not estimated: $8.24
for the extractor over everything, about $100 for the ingestor over every
chat on the frozen version and less on the current one, tens of dollars for
the novels, under $20 to answer 500 questions three ways. The plan in the
repository (`docs/execution-plan.md`) prices every remaining step, sets the
gates, and carries the cut order; when something slips, I cut from the bottom
and keep the committed measurements.

## Changes since the filed draft of August 31

- The corpus: the Chinese classics are out (licensing), and the OCR and
  translation controls with them; GraphRAG-Bench, the CC-BY papers and
  LongMemEval are in. The private reference papers are not part of the corpus.
- The measurements: GraphRAG-Bench and LongMemEval are the two committed benchmarks, with
  the instruments and the resolution ablation restated at the up-edge; NarrativeQA and the
  cells ablation are deferred; the profile signal was dropped on September 9; the wiki's fall
  form is pages over document clusters.
- The design: nothing is merged across documents (the tree, September 7);
  chats are read in one call and carry no narrative cells (September 12).
- The interfaces: one today, `generate`; the embedding interface arrives with
  the store.
- The milestone of September 27 (store and pipeline over Oz book 1 at three tiers, alias
  set scored) is replaced by the design lock above; the key is Wikipedia's roster of Baum's Oz
  characters rather than hand labels, and the three-tier pilot is spring.
- Authorship is stated as it is.
