# Persistent memory for a desktop assistant

Justin Hoffman. IT 494, Fall 2026. Supervisor: Dr. Xing Fang. Draft.

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
system was built to prove the idea. This project builds the real one, with my
own code, and measures it.

## What gets built

The end product is a backend for a desktop AI client. It ingests documents
and chat logs, and from them builds three layers: entities with their aliases,
dated facts with verbatim supporting quotes, and a running narrative of each
entity across the source material. A client reads those layers as context.
Facts are never overwritten. A new fact supersedes an old one at read time,
and the superseding is itself part of what the system knows.

The fall semester builds and tests the methodology on literature rather than
on private data, for one reason: you cannot publish measurements taken on a
personal life. The working hypothesis is that fiction fed in narrative order
behaves like a life recorded in chat. Characters accumulate names, facts
change while old ones stay true of their time, and many threads run through
one document. In the second Oz book a boy named Tip is revealed to be the
transformed princess Ozma. Everything asserted about Tip stays true of the
period it was asserted in, and everything after must attach to the same
entity under a new name. That is the same event, structurally, as a course
pivoting or a colleague changing jobs, and it arrives with ground truth
attached.

Four public-domain corpora are already assembled, 81 files and about 6.9
million words: the Oz canon, the complete Sherlock Holmes, the major Greek
mythological sources, and the Chinese classical novels. Oz supplies the
supersession fixture and a mid-canon change of author. Holmes contributes a
contradiction Doyle never reconciled and a contamination probe:
the deerstalker cap belongs to the illustrations, not the text, so if an
induced description of Holmes contains one, the description came from the
model's training and not from my store. The Greek corpus supplies
irreconcilable disagreement between sources and hundreds of free
entity-resolution test pairs, since Ovid names in Latin what Homer names in
Greek. The Chinese corpus holds the same novel as proofread text, raw OCR,
and machine translation, which lets me measure what OCR error and translation
error each cost the pipeline.

The visible artifact is a wiki assembled mechanically from the store: infobox
from fact rows, lead paragraph from the entity summary, biography from the
narrative layer, every claim traceable to a verbatim quote. A second version
of each page is then written freely by a strong model reading the same store.
The assembled page cannot contain anything the text never said; the generated
page can; the difference between them is a fabrication measurement a reader
can check by eye.

## What gets measured

I checked twelve candidate ideas against published work and every one of them
is already taken, including the ones I thought were mine. That settles what
kind of paper this is. The venues that fit this work say novelty is optional
and rigorous measurement is the price, so the paper is: here is a working
system, and here is what each part of it is worth. I build it, switch parts
off one at a time, and report what each costs. The class project and the
paper are the same work.

One question in the design is genuinely open. Every system I would compare
against resolves entities using name similarity, embeddings, or a model's
verdict. Mine also scores co-occurrence, whether the surrounding cast matches,
and a low-confidence profile inferred from context. Collective entity
resolution established the idea in 2007; whether the relational signal still
pays when the base matcher is an embedding and a language model is unmeasured,
and one of the systems in my comparison table asks for exactly this in its
future work. That is the measurement I most want to land.

Five measurements are committed for the semester.

First, question answering on GraphRAG-Bench, a benchmark of 2,010 questions
with gold answers and gold evidence over twenty pre-1900 novels, where nine
systems have published numbers under the same reader model. I run the full
system, a no-context control, and flat retrieval, then once more with the
co-occurrence and profile resolution signals switched off, which isolates
what my one open question is worth. The per-entity narrative ablation runs
after it if hours allow. Their own results give the target: the
best system spends about a thousand tokens per question and the most
expensive spends over three hundred thousand, so accuracy per token is where
a serverless design can show up.

Second, resolution accuracy against a hand-labeled alias set over one novel,
built in the first week and scored from the very first ingest.

Third, question answering on NarrativeQA, which happens to include 345
human-written questions over twelve books already in my corpora, run through
the same three arms.

Fourth, the instruments that fall out of running the pipeline at all:
duplicate entities minted per chapter, the rate at which extracted quotes
fail to appear verbatim in their source, predicate sprawl, token cost per
stage and per model tier, agreement between the chapter-level and
entity-level summaries, which describe the same text independently and catch
each other's omissions, and the cost of keeping summaries current as the
corpus grows, set against published figures for full-rebuild systems.

Fifth, the corpus controls: the OCR tax and the translation tax, each
isolated by comparing pipeline output over the same content in two forms.

If the schedule holds, one stretch item: LongMemEval, the chat-memory
benchmark where the nearest commercial system published its numbers. I run
the full-context arm first to prove my harness reproduces their baseline,
then the 78 questions that test knowledge updates, which is supersession
under its benchmark name. The full comparison belongs to spring.

Every model call in the pipeline goes through two narrow interfaces, so
models swap freely and every run records which tier ran each stage. The
pipeline is my code end to end; the model is the only black box. Judged
scoring, where unavoidable, runs on a model tier that never writes anything
in the pipeline, calibrated against a hand-labeled sample first.

## The fall calendar

Dr. Fang approved the topic change in person on August 28; the one-semester
form is the remaining paperwork. The semester has two open blocks, now
through September 27 and October 19 through November 15, with three exam
weeks between them where nothing gets scheduled.

By September 2 a single chapter runs end to end: split, cast identified,
entities and facts extracted behind the quote gate, chapter and entity
summaries written, and a small graph rendered. By September 14 all four
corpora are split into clean, verified units and published as a public
dataset, which is the reproducibility piece: everything is public domain, so
anyone can rerun the study. By September 27 the store and pipeline have run
over the first Oz book at three model tiers and the alias set is scored. The
benchmark arms and the ablation run October 19 to 26, right after the exam
block. The dataset gets its DOI by November 10, the paper freezes November
15, and the preprint goes to arXiv the next day. The wiki demonstration
stands up alongside the writing.

The spring semester wraps the proven methodology in the desktop product,
points it at real chat exports, and ships something a person can install.
That work is out of scope for the fall.

Hours are the binding constraint; the compute is a few dollars to a few
hundred at batch rates for the full four-corpus run. The plan in the
repository prices every slate item against the open weeks and carries a cut
order decided now rather than in November. When something slips, I cut from
the bottom of that order and keep the committed measurements.
