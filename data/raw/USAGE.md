# How these corpora are used

Companion to `SOURCES.md`, which records where every file came from, and `WANTLIST.md`, which
records what is absent and why. This file records what the corpora are *for*: which property
each one exercises, and which controls were designed into them so the two known error sources,
OCR and machine translation, could be measured rather than assumed. Both controls live in
chinese/, which left the dataset on 2026-09-04; they return only if the folder does.

Nothing here should be read as a result. These are design notes written before the pipeline
runs, and the whole point of the controls below is that they turn assumptions into numbers.

## The ladder

The four corpora are ordered so each adds exactly one hard problem to the one before it. That
ordering is the reason there are four rather than one large pile. Three are in the dataset;
Chinese, the fourth, left it on 2026-09-04 and returns only if the folder does.

| Corpus | Adds | Use it to |
|---|---|---|
| **Oz** | Nothing adversarial. One world, one continuous canon | Build the pipeline. Establish that ingest, organize and maintain work at all |
| **Holmes** | Contradiction inside one author, plus a contamination probe | Test supersession where no reconciling reading exists. Detect the store being bypassed |
| **Greek** | Contradiction between independent authors, and two clocks | Test corroboration and source weighting. Force the bitemporal model |
| **Chinese** (out since 2026-09-04) | Mixed source quality, and a non-English option | Measure OCR and translation error. Test the model-agnostic claim. Both wait on the folder's return |

Work in that order. A pipeline that cannot handle Oz will not produce interpretable results on
Greek, and a failure on Greek would be impossible to attribute.

## What each corpus is for, specifically

### Oz: the control, and the supersession fixture

Twenty-nine files: Baum's fourteen novels, five companions, the Woggle-Bug Book, and Thompson's nine-novel run to 1930.

**The primary fixture is Tip becoming Ozma** at the end of book 2. A boy raised by a witch is
revealed to be the transformed princess of Oz. Everything asserted about Tip in book 2 stays
true *of that period* and is superseded after it. One case exercises aliasing, entity merge,
supersession and time-scoped truth at once, and it arrives at book 2 rather than book 14, so
incremental update behaviour can be demonstrated with two documents.

**Two secondary properties, both accidental and both useful.**

*Entities that change universe.* Trot and Cap'n Bill are established in The Sea Fairies and Sky
Island, which are not Oz books, and then migrate into the Oz canon in book 9. An entity that
crosses fictional worlds is a harder resolution problem than one that merely recurs, and it is
here without being constructed.

*A change of author mid-canon.* Books 1 to 14 are Baum. The Royal Book onward is Thompson. A
fact Thompson asserts about Baum's characters is a different class of evidence from one Baum
asserted. No other corpus here has that property, and it is what makes the source-coloured wiki
render worth building: the authorial handover becomes visible on the entity page itself rather
than stated in a footnote.

### Holmes: the contamination probe

Nine volumes, the complete canon of sixty.

**The probe.** What the Holmes text says and what the surrounding culture believes have
measurably diverged. The deerstalker is Sidney Paget's illustration, not Doyle's text. The
curved calabash pipe is William Gillette's stage prop; Doyle writes a black clay, a cherrywood
and a briar. "Elementary, my dear Watson" is not in the canon.

So if the pipeline induces a character description from this corpus and a deerstalker appears in
it, **that description did not come from the corpus.** It came from the model's weights. This is
a direct test of whether an answer is store-grounded or parametric, and unlike every published
memory benchmark it does not require a question set engineered to be unanswerable without the
store. The failure is visible.

The same test carries downstream: an image rendered from an induced description is a leak
detector a reader can judge by looking. Note carefully that **the research artifact is the
induced description, not the image.** The image displays the result; it does not produce it.

**The supersession case.** Watson's war wound is in his shoulder in *A Study in Scarlet* and in
his leg in *The Sign of the Four*. Doyle never reconciled it and no reading reconciles it. That
is a contradiction inside a single-author corpus, which is a cleaner test than two ancient
sources disagreeing, because authorship is held constant.

### Greek: disagreement, and the second clock

Thirty-one files spanning roughly a thousand years of authorship and nine translators.

**Cross-language aliasing with free ground truth.** Ovid names in Latin what Homer names in
Greek. Odysseus and Ulysses, Zeus and Jupiter, Heracles and Hercules. Hundreds of pairs,
unambiguously the same entity, spanning works, requiring no hand annotation. This is a labeled
entity-resolution test set obtained for nothing.

**Irreconcilable contradiction.** Euripides has Helen never reach Troy. Iphigenia is sacrificed
in some accounts and rescued in others. Diodorus preserves variants the poets do not. A system
that folds summaries together without tracking which source said what will produce a
confidently wrong answer here, and the error is detectable rather than theoretical.

**Two clocks that visibly disagree.** Hesiod describes the origin of the gods, Homer describes a
war, Ovid retells events across the whole span, the tragedians revisit Homeric characters after
Homer, and Apollodorus and Diodorus systematise all of it centuries later. There is no single
ordinal that orders both *when a thing happened* and *when a source asserted it*. This corpus
therefore makes the valid-time and transaction-time distinction mandatory rather than optional.
It cannot be faked with one number, which is exactly why it is here.

**Bulfinch is not a primary source and is present on purpose.** *The Age of Fable* is a 19th
century synthesis that compiles and reconciles the primary sources into unified narrative
articles. That is precisely what this project's pipeline produces, so it functions as a
human-written reference implementation of the output. Induced structure can be scored against
it as well as against a modern wiki. It partly replaces Apollodorus's role and complements it.

**Translator variance is a live variable here.** Translations were not held constant, and in one
case not even within an author. Entity naming will vary by translator as well as by source. That
is part of the difficulty rather than a defect, but any result on this corpus must record it.

### Chinese: the measurement corpus

Eleven files, out of the dataset since 2026-09-04 and back only if the folder returns. Complete
in Chinese, permanently partial in English.

This corpus is where the two error sources that affect everything else become measurable,
because it is the only place the same content exists in multiple forms. Its literary content is
almost secondary to that function.

*Investiture of the Gods* shares deities with Journey to the West, Nezha and Li Jing and Erlang
Shen among them, which is the genuine cross-work entity overlap the Four Great Classical Novels
alone never provided, since those four share a cosmology but not their mortal casts.

---

## The controls

Two deliberate redundancies were built into `data/raw/` through chinese/; both left the fall
slate with that folder on 2026-09-04 and return only if it does. Neither is an accident, and
neither should be deduplicated away by a tidying pass.

### Control 1: the OCR tax

**Files.** `chinese/01_sankuoorromanceo0001chbr.txt` is Brewitt-Taylor's Three Kingdoms volume 1
as OCR from a page scan. `chinese/05_77416.txt` is the *same volume 1*, the same translation, as
a Project Gutenberg human-proofread transcription.

**What it measures.** Run the extraction pipeline identically over both. Every difference in the
resulting entity set, alias ledger and fact rows is attributable to OCR error, because the
content is otherwise identical. That number is the OCR tax, obtained with no hand annotation.

**Why it matters here.** Several files in this collection are OCR from scans rather than
proofread transcription: both Apollodorus volumes and the Diodorus volumes. The three Chinese
scans left with chinese/, and the Statius scan was removed from the dataset on quality grounds. Without this control, any result on those files carries an unquantified error term.

### Control 2: the translation tax

This is the one that makes machine-translating the Chinese originals defensible rather than
reckless.

**The problem.** The Chinese originals are complete and unambiguously public domain, while every
complete English translation is still in copyright. Machine translation solves the rights
problem completely, since a translation produced here is original work. But it introduces a
confound: if a fact is missing from the pipeline's output, translation error and extraction
error are indistinguishable, and for a project whose entire purpose is measuring what the
pipeline does, that is fatal.

**Why Three Kingdoms resolves it.** It is the only novel fetched for this project that exists in
all of these forms at once; every file in the table is in chinese/ and left with it:

| Artifact | File |
|---|---|
| Chinese original, complete | `chinese/04_23950.txt` |
| Human English translation, proofread, volume 1 | `chinese/05_77416.txt` |
| Human English translation, OCR, volumes 1 and 2 | `chinese/01_*`, `chinese/02_*` |
| Machine English translation | to be produced |

**The calibration protocol.**

1. Machine-translate the Chinese original over the chapter range covered by Brewitt-Taylor
   volume 1, which is roughly chapters 1 to 60. Do this through the same `generate()` interface
   the pipeline uses, recording the model tier per call, so the cost lands in the same run rows
   as everything else.
2. Carry a **forward glossary** across chapters. Without it, 宋江 returns as "Song Jiang",
   "Sung Chiang" and "Sòng Jiāng" in different chapters and name consistency collapses. This
   glossary is the project's own alias ledger used one stage earlier than designed, which makes
   the translation step a demonstration of the architecture rather than a detour around it.
3. Run the extraction pipeline **identically** over the machine translation and over the
   proofread Brewitt-Taylor volume 1.
4. Report entity recall, fact recall, alias-consistency rate, and the delta between the two runs.

**That delta is the translation tax**, measured against a competent human translator on
identical source content. It licenses a stated confidence bound when the same method is applied
to Water Margin, Journey to the West and Dream of the Red Chamber, where no human English
translation exists to check against.

**The two error sources separate cleanly**, because the OCR control shares a work with this one:

| Run | Isolates |
|---|---|
| Proofread human translation | Baseline |
| OCR human translation | Baseline plus OCR error |
| Machine translation from Chinese | Baseline plus translation error |

**Caveats that must be stated with any result.** Brewitt-Taylor is himself an imperfect and
century-old translator, so what is measured is *agreement with a competent human translation*,
not agreement with truth. The Chinese Gutenberg text and the 1925 or 1929 printings Brewitt-
Taylor worked from are not guaranteed to be the same edition, so some divergence is textual
rather than translational. And Three Kingdoms is historical narrative; Water Margin's 108
semantic nicknames, where 及時雨 is "Timely Rain" and 黑旋風 is "Black Whirlwind", are a harder
translation-consistency problem than anything in Three Kingdoms, so the measured tax is a floor
rather than an estimate.

---

## Quality variables to record per file

Every result must carry these, because they vary across the collection and none of them is
visible from the text alone.

- **Transcription method.** Proofread transcription (Gutenberg) or OCR from page scan
  (Archive.org). Recorded per work in each corpus manifest via `source_url`.
- **Bilingual interleaving.** Loeb editions print facing-page originals, so their OCR mixes
  Greek or Latin into the English. Affects both Apollodorus volumes and Ovid's Heroides.
- **Abridgement.** Both known cases are in chinese/ and out with it: the Richard Journey to the
  West is roughly one sixth of the novel, and Joly's Dream of the Red Chamber stops at chapter 56
  of 120.
- **Translator identity.** Not held constant within the Greek corpus, and entity naming follows
  the translator.
- **Language.** Whitespace word counts are meaningless for the Chinese-language files, which
  left with chinese/; the Three Kingdoms original reports about 20,000 "words" for 1.86 MB. If
  the folder returns, any length-based rule, including the unit size cap, needs a per-language
  definition before it is applied.

## Things not to do

- **Do not deduplicate `chinese/05_77416.txt` if chinese/ returns.** It looks like a redundant
  copy of volume 1 and it is the OCR control.
- **Do not restore `greek/29_thebaidstatius00conggoog.txt`.** Removed from the dataset on
  2026-09-04: the 1767 printing's long-s renders as "f" throughout the OCR (a real line reads "It
  muft oertoly be an infinite Fleafure to perafe"). `SOURCES.md` keeps the provenance and the reason.
- **Do not quote word counts for the Chinese-language files if chinese/ returns.** See above.
- **Do not treat Archive.org hosting as evidence of public domain status.** Check the
  `collection` field: institutional programmes such as `cornell`, `americana` and
  `graduatetheologicalunion` carry rights review, while `opensource` and `community` are user
  uploads that carry none.
- **Do not trust Archive.org catalogue metadata.** Two records among the files fetched for this project are wrong, both in chinese/. The
  San Kuo identifier suffixes are reversed relative to volume order, and *A Mission to Heaven*
  is credited to Li Zhichang, who wrote a different work with the same English title. Both were
  caught by reading content. See `SOURCES.md`.
- **Do not read "no records found" as absence.** Two works were reported here as unavailable and
  were on Project Gutenberg the whole time, both because a multi-term query returned nothing.
  Search failure and absence look identical and are not the same thing.
