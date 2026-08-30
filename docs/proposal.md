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

Four public-domain corpora are already assembled, 81 files and about 6.8
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

The claim under test is about extraction order. The published baselines
extract entities chunk by chunk and reconcile afterward; GraphRAG extracts
from each text unit separately, and Zep extracts per conversational episode.
My pipeline reads the whole chapter first, establishes the cast, and
conditions every downstream step on it. Whether that ordering measurably
reduces duplicate and fragmented entities is an empirical question with gold
data available to answer it.

Five measurements are committed for this semester.

First, entity and coreference accuracy against LitBank, a hand-annotated
corpus of a hundred Project Gutenberg works, scoring my entity-first pass
head to head against chunk-first extraction on identical text.

Second, question answering on NarrativeQA, which supplies 345 human-written
questions over twelve books that are already in my corpora, compared across
three retrieval arms: plain passage retrieval, my structured store, and both
together.

Third, the knowledge-update section of LongMemEval, the public benchmark for
long-horizon chat memory, where Zep has published numbers against a
full-context baseline. The point is comparability on the update problem, not
a contest; long-context models win raw recall, and the store's case is cost,
provenance, and supersession.

Fourth, the instruments that fall out of running the pipeline at all:
duplicate entities minted per chapter, the rate at which extracted quotes
fail to appear verbatim in their source, predicate sprawl, token cost per
stage, and agreement between the chapter-level and entity-level summaries,
which are independent summaries of the same text and catch each other's
omissions.

Fifth, the corpus controls: the OCR tax and the translation tax, each
isolated by comparing pipeline output over the same content in two forms.

Every model call in the pipeline goes through two narrow interfaces, so
models swap freely and every run records which tier ran each stage. The
pipeline is my code end to end; the model is the only black box. Judged
scoring, where unavoidable, runs on a model tier that never writes anything
in the pipeline, calibrated against a hand-labeled sample first.

## The fall calendar

By September 2 a single chapter runs end to end: split, cast identified,
entities and facts extracted behind the quote gate, chapter and entity
summaries written, and a small graph rendered. By September 14 all four
corpora are preprocessed into clean, split, verified units and published as a
public dataset, which is the reproducibility piece: everything is public
domain, so anyone can rerun the study. By September 21 the full pipeline has
run over the first Oz book at three model tiers. By September 28 the LitBank
comparison is done, by October 5 LongMemEval, by October 12 NarrativeQA and
the compiled instruments. October 15 is the freeze: every table and figure
the paper needs, measured and archived. The remainder of the semester writes
the paper and stands up the wiki demonstration.

The spring semester wraps the proven methodology in the desktop product,
points it at real chat exports, and ships something a person can install.
That work is out of scope for the fall.

Hours, not compute, are the binding constraint. The full four-corpus run
costs from a few dollars on the cheapest model tier to a few hundred on the
priciest at batch rates. When something slips, the plan cuts corpus scope,
never measurement.
