> **COUNTS CORRECTED 2026-08-28.** This file was written when the corpora were roughly half their
> current size and its section headers were never updated: it documented 37 of the 81 files now on
> disk. Headers below now match `manifest.json` in each corpus directory, which is the authority.
>
> **Two absence claims in this file were false and are corrected in place.** Apollodorus and Water
> Margin were both recorded here as unavailable; both were acquired on 2026-08-26 and are on disk.
> The corrections landed in `fetch_corpus.py` and `WANTLIST.md` at the time but never reached this
> file. That is the same failure the project's method rules exist to prevent, preserved here as a
> worked example rather than quietly deleted.

# Raw corpora: where each text came from, and why it is here

Everything in this directory is a verbatim download from Project Gutenberg or, where no
Gutenberg edition exists, from an institutional scan on Archive.org. Nothing has been
cleaned, split, or normalised. That is deliberate: the raw layer is the write-ahead log for
everything downstream, so it stays byte-identical to what the source served and every later
artifact can be rebuilt from it. Preprocessing into homogeneous datasets is a separate step
and does not belong in this folder.

Each corpus directory carries a `manifest.json` recording, per work, the source URL, byte
count, sha256, and whether the title in the Gutenberg header matched what we expected. The
manifest is what makes a work removable later: excluding it is a filter, not a rebuild.

## Why these corpora

The project needs a test corpus where the right answers are knowable and the material is
outside any model's training data in the parts that matter. Literature supplies both kinds of
information the system stores: the story as it happened, and the facts about people and places
that the story changes over time. Each corpus below was chosen to stress one specific part of
the design, and they are ordered so that each adds exactly one new hard problem.

**Oz is the control.** One author, one continuous canon, one narrator, no conflicting sources.
Entity resolution across works is real but never adversarial, because Baum is not arguing with
anyone. This is where the pipeline gets built.

**Holmes adds contradiction inside one author.** Sixty works, one writer, recurring entities
across all of them, and documented inconsistencies that Doyle never reconciled. It also
supplies something no other corpus here does: a measurable gap between what the text says and
what the surrounding culture believes, which turns it into a contamination probe.

**Greek adds disagreement between authors.** The same figures appear across independent sources
written centuries apart, in two languages, that contradict each other on matters of fact. It
also breaks the single time axis: source position and story time come apart, which forces the
bitemporal distinction rather than allowing it to be optional.

**Chinese adds mixed source quality and one real hole.** Three Kingdoms is complete, but three
of its five files are OCR from page scans rather than proofread transcription, and Water Margin
has no public domain English translation in existence. It is last because it is the corpus whose
inputs are least trustworthy, and because it carries a deliberate duplicate that turns OCR error
into something measurable rather than assumed.

## Oz (29 works, roughly 1,279,000 words)

L. Frank Baum's fourteen canonical Oz novels, 1900 to 1920, all public domain in the United
States by expiry of term. Files are numbered by publication order, which is also narrative
order, so the file ordinal is directly usable as the `asserted_at` position.

| # | Work | Gutenberg |
|---|---|---|
| 1 | The Wonderful Wizard of Oz | 55 |
| 2 | The Marvelous Land of Oz | 54 |
| 3 | Ozma of Oz | 486 |
| 4 | Dorothy and the Wizard in Oz | 420 |
| 5 | The Road to Oz | 485 |
| 6 | The Emerald City of Oz | 517 |
| 7 | The Patchwork Girl of Oz | 955 |
| 8 | Tik-Tok of Oz | 956 |
| 9 | The Scarecrow of Oz | 957 |
| 10 | Rinkitink in Oz | 958 |
| 11 | The Lost Princess of Oz | 959 |
| 12 | The Tin Woodman of Oz | 960 |
| 13 | The Magic of Oz | 419 |
| 14 | Glinda of Oz | 961 |

**The reason this corpus leads.** At the end of book 2, a boy named Tip is revealed to be
Princess Ozma, transformed and hidden since infancy. Every fact asserted about Tip in book 2
remains true of that period and is superseded thereafter, which exercises aliasing, entity
merge, supersession and time-scoped truth in a single case. It arrives at book 2 rather than
book 14, so the incremental update behaviour can be demonstrated with two documents instead of
the whole series.

Baum's world also has invented geography with stable internal structure (the Munchkin, Winkie,
Quadling and Gillikin countries), a cast that persists and changes across all fourteen volumes,
and an active community wiki to score induced structure against. Contamination falls sharply
after book 1, which makes closed-book question certification easier in the later volumes rather
than harder.

**Known wrinkle.** The fourteen were digitised by different volunteers over about twenty years
and do not share a chapter heading convention. At least three variants are present: `Chapter I`
with the title on the following line, `Chapter One` with the title on the following line, and
book 2, which uses no chapter marker at all and identifies chapters only by a bare title line
under a `LIST OF CHAPTERS` table. Every book does carry a table of contents, so the chapter
count from the table of contents is available as an automatic check on any splitter. Note that
table of contents titles do not always match body titles exactly, so that check should compare
counts and order rather than strings.

## The Sherlock Holmes canon (9 volumes, 60 works, roughly 685,000 words; unchanged and accurate)

The complete canon: four novels and five story collections, 1887 to 1927. All of it is public
domain in the United States, including *The Case-Book*, whose stories were the last to clear
and did so on expiry of term rather than on any contested basis.

| # | Volume | Gutenberg |
|---|---|---|
| 1 | A Study in Scarlet | 244 |
| 2 | The Sign of the Four | 2097 |
| 3 | The Adventures of Sherlock Holmes | 1661 |
| 4 | The Memoirs of Sherlock Holmes | 834 |
| 5 | The Hound of the Baskervilles | 2852 |
| 6 | The Return of Sherlock Holmes | 108 |
| 7 | The Valley of Fear | 3289 |
| 8 | His Last Bow | 2350 |
| 9 | The Case-Book of Sherlock Holmes | 69700 |

**Position on the ladder.** Oz is one author with one continuous canon and no contradiction.
Greek is many authors contradicting each other. Holmes sits between them: one author, sixty
works, and contradictions he introduced himself and never fixed. Watson's war wound is in his
shoulder in *A Study in Scarlet* and in his leg in *The Sign of the Four*. That is a
supersession case with no reconciling reading available, inside a single-author corpus, which
is a different and cleaner test than two ancient sources disagreeing.

**The contamination probe, which is the real reason this corpus is here.** What the Holmes text
says and what the culture believes have measurably diverged, and the divergences are specific
and checkable:

- The deerstalker cap does not appear in the text. It comes from Sidney Paget's magazine
  illustrations.
- The curved calabash pipe does not appear in the text. It comes from William Gillette's stage
  performance. Doyle writes a black clay pipe, a cherrywood, and a briar.
- "Elementary, my dear Watson" is not in the canon.
- Watson in the text is an army surgeon invalided home from Afghanistan, not the elderly
  bumbler of mid-century film.

Holmes himself, by contrast, *is* described in the text: over six feet, excessively lean, sharp
piercing eyes, a thin hawk-like nose, a square prominent chin.

This gives a genuinely measurable instrument. If the system induces a character description from
the corpus and that description contains a deerstalker, the description did not come from the
corpus. It came from the model's parametric memory. The same test works on any downstream render:
an image generated from an induced description is a **visible leak detector**, and a reader can
judge it by looking rather than by reading a table of numbers.

That property is worth stating plainly because it is rare. Most memory benchmarks can only
detect this failure statistically, through question sets built to be answerable only from the
store. Here the failure has a picture of it. Note that the description induction is the part
this project's pipeline does, as a call against an entity page; rendering an image from that
description is a downstream step through the same model interface, and the honest framing is
that the render displays the result rather than producing it.

## Greek and Roman sources (32 works, roughly 3,363,000 words)

A shared pantheon across independent authors, translators and centuries. File ordinal here is
**source position and not story time**, and the gap between those two is the reason this corpus
is in the set.

| # | Work | Author | Gutenberg |
|---|---|---|---|
| 1 | The Iliad | Homer | 2199 |
| 2 | The Odyssey | Homer | 1727 |
| 3 | Hesiod, the Homeric Hymns, and Homerica | Hesiod, trans. Evelyn-White | 348 |
| 4 | Oedipus the King, Oedipus at Colonus, Antigone | Sophocles | 31 |
| 5 | The Seven Plays in English Verse | Sophocles | 14484 |
| 6 | The House of Atreus (the Oresteia) | Aeschylus | 8604 |
| 7 | The Tragedies of Euripides, Volume I | Euripides | 15081 |
| 8 | Metamorphoses, Books I to VII | Ovid | 21765 |
| 9 | Metamorphoses, Books VIII to XV | Ovid | 26073 |

**What this corpus supplies that Oz cannot.**

Cross-language aliasing with free ground truth. Ovid names the same gods in Latin that Homer
names in Greek. Odysseus and Ulysses, Zeus and Jupiter, Heracles and Hercules: hundreds of
pairs that are unambiguously the same entity, spanning works, requiring no hand annotation.

Genuine contradiction between sources. Euripides has Helen never reach Troy. Iphigenia is
sacrificed in some accounts and rescued in others. A system that folds summaries together
without asking which source said what will produce a confidently wrong answer here, and that
failure is detectable rather than theoretical.

Two clocks that visibly disagree. Hesiod describes the origin of the gods, Homer describes a
war, Ovid retells events from across the whole span, and the tragedies revisit Homeric
characters after Homer. There is no single ordinal that orders both when a thing happened and
when a source asserted it.

**CORRECTED 2026-08-28: Apollodorus is present.** The paragraph below is wrong and is kept to show how the error read. The *Bibliotheca* is on disk as `27_library00apolgoog.txt` and `28_apollodoruslibra02apol.txt`, acquired from Archive.org rather than Project Gutenberg. The original note checked one source, found nothing, and recorded absence as a decision.

~~**Deliberately absent.** Apollodorus's *Bibliotheca* is not on Project Gutenberg. It was wanted
because it is an ancient systematic mythography, effectively a pre-modern attempt at the same
wiki this project induces, and would have allowed induced structure to be scored against both a
modern wiki and an ancient one. Worth revisiting through another public domain source.

**Translator note.** Translations were not held constant across this corpus and in one case not
within an author. Entity naming will therefore vary by translator as well as by source, which is
part of the difficulty rather than a defect, but it needs recording before any result is
reported.

## Chinese classical novels (11 files, roughly 1,577,000 words)

| # | Work | Source | Detail |
|---|---|---|---|
| 1 | San Kuo, volume 1 | Archive.org `sankuoorromanceo0001chbr` | Brewitt-Taylor, 1929 printing. Library scan, OCR. |
| 2 | San Kuo, volume 2 | Archive.org `sankuoorromanceo0000chbr` | Brewitt-Taylor, 1929 printing. Library scan, OCR. |
| 3 | A Mission to Heaven | Archive.org `cu31924074502034` | Timothy Richard, 1913. **Abridged**, roughly a sixth of the novel. |
| 4 | 三國志演義 | Gutenberg 23950 | Chinese-language original, complete and unabridged. |
| 5 | San Kuo, volume 1 again | Gutenberg 77416 | Proofread transcription of the 1925 printing. Deliberate duplicate of work 1. |

**Three Kingdoms is now complete in English.** Project Gutenberg carries only volume 1. Both
volumes of the 1929 Brewitt-Taylor printing are held by Archive.org as a Graduate Theological
Union scan, openly accessible and public domain on expiry of term. Together they are the whole
novel, roughly 560,000 words.

**Two verification notes, both of which would have quietly poisoned the corpus.**

The Archive.org identifier suffixes are misleading. `sankuoorromanceo0001chbr` carries a
`volume: 1` field and is volume 1; `sankuoorromanceo0000chbr` carries no volume field and is
volume 2. This was settled by reading chapter content, not by trusting the labels: the first
covers Li Ts'ui and Kuo Ssu in the early chapters, the second covers Liu Bei claiming the
succession and attacking Wu, which is chapter eighty onward.

Archive.org credits *A Mission to Heaven* to Li Zhichang, who wrote a **different** work whose
English title is also rendered "Journey to the West", a Taoist travel account of Qiu Chuji's
journey to Genghis Khan. That record is wrong. The text is signed "Timothy Richard, Shanghai,
October 1913", uses the word Monkey 391 times and never mentions Genghis Khan, so it is the Wu
Cheng'en novel. Do not trust that catalogue record if the corpus is ever rebuilt.

**Work 5 is a deliberate duplicate and should not be deduplicated away.** Volume 1 exists here
twice: once as Archive.org OCR of a page scan, once as a Gutenberg human-proofread
transcription. That makes OCR error cost measurable rather than assumed. Run entity extraction
over both and the difference between the two entity sets is the OCR tax, on identical content,
with no annotation required. Given that three of the five files here are OCR, that number is
worth having before any Chinese result is reported.

**CORRECTED 2026-08-28: Water Margin is present**, in Chinese, as `08_23863.txt` (水滸). It was a search failure after all: the original queries were too specific and missed the Gutenberg record. The paragraph below is kept as written so the error is visible.

~~**Water Margin is genuinely unavailable and this is not a search failure.** The first complete
English translation is Pearl Buck's *All Men Are Brothers*, 1933, which is past the public
domain line. Jackson's is 1937, Shapiro's is 1980. A search of Archive.org restricted to
pre-1931 returned one Japanese adaptation from 1868 and one unvetted community upload. Pearl
Buck's translation is on Archive.org, but in the `opensource` and `community` collections,
meaning a user uploaded it rather than a library digitising a public domain work. It is not
usable here.

That collection field is the general heuristic worth keeping: `cornell`, `americana`,
`graduatetheologicalunion` and similar are institutional digitisation programmes with rights
review behind them, while `opensource` and `community` are user uploads with none. Archive.org
hosting a file is not evidence that the file is public domain.

**Why the gap exists at all.** English translation of Chinese vernacular fiction began too late
to clear the copyright window. United States public domain currently reaches published works
through 1930. Brewitt-Taylor's Three Kingdoms is 1925 and lands inside it. Everything else
lands outside: Water Margin's first complete English translation is 1933, and Journey to the
West had to wait until Waley's abridgement in 1942 and Anthony Yu's complete translation in
1977. Compare Greek and Latin, translated continuously into English since the 1600s, which is
why that corpus pulled nine works without difficulty. The novels themselves are 14th to 16th
century and entirely public domain; this is purely a translation rights problem.

**A design point that was not obvious at the outset.** The Four Great Classical Novels do not
share a narrative universe. They share a cosmology and pantheon, the Jade Emperor and the
celestial bureaucracy, but not their mortal casts. Cross-work entities would therefore be a
specific identifiable subset rather than the general case, which is arguably a cleaner test
than was originally assumed, but it is not the same test.

**Measurement warning already visible.** The word count recorded for the Chinese-language text
is meaningless. It reports roughly 20,000 "words" for a 1.86 MB file because the count is
whitespace-delimited and Chinese does not delimit words with whitespace. Any length-based
metric, and any chunking rule expressed in words, needs a per-language definition before this
corpus is used.

## Copyright basis

All works here are public domain in the United States by expiry of term. Project Gutenberg is
United States based and conservative about status, so its hosting a text is itself a reasonable
signal. This matters because the downstream artifacts are public: a preprint, a Kaggle notebook,
a distributable harness, and a symposium demonstration.

Two things were considered and excluded. Harry Potter is under copyright and cannot appear in
any published artifact, though it remains the strongest candidate for a private working corpus
because its community wiki is the best scoring target available. Robert E. Howard's Conan
stories were excluded because their public domain status rests on copyright non-renewal rather
than expiry of term, which is a per-story question requiring records research, the character
name is separately trademarked and actively enforced, and much of the circulating text is a
later edited version carrying its own copyright.

---

## The collection as it stands, 2026-08-30

Per-file provenance for every file, including the ones added after the sections
above were written, lives in each corpus's `manifest.json`: ordinal, Gutenberg or
Archive.org identifier, verified title, byte count, and sha256. The counts:

**oz** — 29 files: 1 Wonderful Wizard of Oz, 2 Marvelous Land of Oz, 3 Ozma of Oz, 4 Dorothy and the Wizard in Oz, 5 Road to Oz, 6 Emerald City of Oz, 7 Patchwork Girl of Oz, 8 Tik-Tok of Oz, 9 Scarecrow of Oz, 10 Rinkitink in Oz, 11 Lost Princess of Oz, 12 Tin Woodman of Oz, 13 Magic of Oz, 14 Glinda of Oz, 15 Sea Fairies, 16 Sky Island, 17 Little Wizard Stories, 18 Santa Claus, 19 Royal Book of Oz, 20 Kabumpo in Oz, 21 Cowardly Lion of Oz, 22 Grampa in Oz, 23 Lost King of Oz, 24 Hungry Tiger of Oz, 25 Gnome King of Oz, 26 Giant Horse of Oz, 27 Jack Pumpkinhead of Oz, 28 Yellow Knight of Oz, 29 Woggle-Bug.

**holmes** — 9 files: 1 Study in Scarlet, 2 Sign of the Four, 3 Adventures of Sherlock Holmes, 4 Memoirs of Sherlock Holmes, 5 Hound of the Baskervilles, 6 Return of Sherlock Holmes, 7 Valley of Fear, 8 His Last Bow, 9 Case-Book of Sherlock Holmes.

**greek** — 32 files: 1 Iliad, 2 Odyssey, 3 Homeric Hymns, 4 Sophocles, 5 Seven Plays, 6 House of Atreus, 7 Euripides, 8 Metamorphoses, 9 Metamorphoses, 10 Aeschylus, 11 Argonautica, 12 Aeneid, 13 Age of Fable, 14 Fall of Troy, 15 Pausanias, 16 Pausanias, 17 Pindar, 18 Alcestis, 19 Electra, 20 Hecuba, 21 Medea, 22 Bacchae, 23 Trojan Women, 24 Iphigenia, 25 Rhesus, 26 Hippolytus, 27 library, 28 library, 29 Thebaid, 30 Heroides, 31 Diodorus, 32 Diodorus.

**chinese** — 11 files: 1 San Kuo, 2 San Kuo, 3 mission to heaven, 4 三國, 5 three kingdoms, 6 Hung Lou Meng, 7 Hung Lou Meng, 8 水滸, 9 西遊, 10 紅樓夢, 11 封神.

81 files in all.
