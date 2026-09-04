> **BODY SECTIONS ARE STALE, the closing summary table is correct.** Corrected 2026-08-28.
> The per-corpus sections below still describe the mid-acquisition state (Oz 28 of 28, Greek 13
> of ~24, Chinese 3 of 4). Actual counts are Oz 29, Greek 31, Holmes 9, totalling 69
> files and roughly 5.15M words (recounted 2026-09-04: chinese/ out, the Thebaid removed). Several items still listed as HUNT are on disk: the Woggle-Bug
> Book, Apollodorus, Pausanias, Quintus, Heroides, Pindar and the extra Euripides. Trust the
> summary table and `manifest.json`, not these section headers.

# Want list: what each corpus needs to be complete

A corpus assembled opportunistically has no completeness measure. This file defines the target
set for each corpus first, so that "we have 19 of 19" or "we have 13 of 24" is a statement with
meaning behind it, and so that a gap is a recorded decision rather than an oversight.

Status codes used throughout:

- **HAVE**, downloaded, title-verified, in `data/raw/`
- **HUNT**, public domain and believed to exist, not yet located or not on Project Gutenberg
- **BLOCKED**, no public domain English source exists, with the reason recorded
- **DECIDE**, availability is not the question; whether it belongs in the set is

---

## Oz: 29 of 29. Baum's canon, his companions, the Woggle-Bug Book, and Thompson's run to 1930

**Target definition.** Every work by Baum sharing characters or continuity with the Oz novels.
Baum linked his own books deliberately, so the boundary is drawn at shared characters rather
than at the word "Oz" in the title.

### The fourteen canonical novels

All **HAVE**. Books 1 through 14, 1900 to 1920, in publication order, which is also narrative
order.

### Companions inside the continuity

| Work | Year | Status | Why it belongs |
|---|---|---|---|
| The Sea Fairies | 1911 | HAVE | Introduces Trot and Cap'n Bill, who **migrate into the Oz canon** in book 9 |
| Sky Island | 1912 | HAVE | Trot, Cap'n Bill and Button-Bright, before Oz absorbs them |
| Little Wizard Stories of Oz | 1913 | HAVE | Six canonical short stories |
| The Life and Adventures of Santa Claus | 1902 | HAVE | Santa attends Ozma's birthday party in book 5 |
| The Royal Book of Oz | 1921 | HAVE | Thompson, published under Baum's name. The canon boundary itself |

The Sea Fairies and Sky Island are the most valuable additions in this set and the least
obvious. Trot and Cap'n Bill are established as entities in a *different fictional world*, then
cross into Oz. An entity that changes universe mid-corpus is a harder resolution problem than
one that merely recurs, and it exists here without being constructed.

### Still to track down

| Work | Year | Status | Note |
|---|---|---|---|
| The Woggle-Bug Book | 1905 | HAVE | Oz character spinoff, `oz/29_21914.txt` |
| Queer Visitors from the Marvelous Land of Oz | 1904-05 | HUNT | Newspaper serial. May never have been digitised |

### Scope decisions outstanding

**RESOLVED, included.** Thompson's nine Oz novels from 1922 to 1930 are all HAVE: Kabumpo
(#53765), The Cowardly Lion (#58765), Grampa (#61681), The Lost King (#65849), The Hungry Tiger
(#70152), The Gnome King (#71273), The Giant Horse (#73170), Jack Pumpkinhead (#75720), The
Yellow Knight (#78637). They are on Project Gutenberg after all; the earlier search that missed
them used a bad query rather than proving absence.

The reason they are in: **a change of author mid-canon.** A fact Thompson asserts about Baum's
characters is a different class of evidence from one Baum asserted, and no other corpus in this
project has that property. It also pays off directly in the wiki render, where colouring each
assertion by its source work makes the authorial handover visible on the entity pages
themselves.

**Still outstanding.** Thompson wrote ten more Oz books between 1931 and 1939, and Project
Gutenberg carries several of them (Pirates, The Purple Prince, Ojo, Speedy, The Wishing Horse,
Captain Salt, Handy Mandy, The Silver Princess, Ozoplaning). Those postdate the 1930 line, so
their public domain status rests on copyright non-renewal rather than expiry of term. That is
the same basis this project rejected for Conan, with one real difference: Project Gutenberg is
a conservative United States host that has affirmatively cleared and published these, whereas
nothing of Conan's appears on the United States site. Taking Gutenberg's hosting as the
clearance signal is defensible and consistent with the heuristic used elsewhere here, but it is
a weaker footing than the 1922 to 1930 books and should be recorded as such if they are added.

**Baum's non-Oz fantasy.** The Master Key, The Enchanted Island of Yew, American Fairy Tales,
Dot and Tot of Merryland, The Magical Monarch of Mo, Policeman Bluejay. Separate worlds with no
established crossover. Recommend excluding, since the point of the companions above is the
crossover and these do not have one.

---

## Holmes: complete, nothing outstanding

**Target definition.** The canon of sixty: four novels and fifty-six stories.

All **HAVE**, in nine volumes. This corpus is finished and needs no further work.

**DECIDE, marginal.** Doyle wrote two short Holmes pieces outside the canon, *The Field Bazaar*
(1896) and *How Watson Learned the Trick* (1924). Including them is defensible and adds perhaps
two thousand words. Not worth effort unless they turn up free.

---

## Greek: the hunt closed at 32 files, 31 in the dataset

**Target definition.** Every surviving classical source that asserts facts about the Greek
pantheon and heroes, available in public domain English. The point of this corpus is
disagreement between independent sources, so coverage matters more here than anywhere else:
each missing source is a missing witness.

### Have

Iliad, Odyssey, Hesiod with the Homeric Hymns, Sophocles twice over (the Theban plays and the
complete seven), Aeschylus twice (the Oresteia and the four other plays), Euripides volume I,
Ovid's Metamorphoses in two volumes, Apollonius's Argonautica, Virgil's Aeneid, and Bulfinch.

**On Bulfinch, which is not a primary source and is here on purpose.** *The Age of Fable* is a
19th century synthesis that compiles and reconciles the primary sources into unified narrative
articles. That is precisely what this project's pipeline produces. It therefore functions as a
**human-written reference implementation of the output**, and induced structure can be scored
against it as well as against a modern wiki. It partly replaces Apollodorus, which is not on
Gutenberg.

### Formerly hunted, now in hand

Every item on the original hunt list except Hyginus was acquired: Apollodorus's
Bibliotheca in two volumes, nine further Euripides plays beyond volume I,
Pausanias in two volumes, Quintus Smyrnaeus's Fall of Troy, Ovid's Heroides,
Pindar's Odes, and Diodorus in two volumes. The Statius Thebaid was downloaded
and then removed from the dataset on OCR quality; SOURCES.md keeps the provenance and the reason.
Hyginus remains BLOCKED, no public domain English translation.

### Decide

Herodotus, Thucydides, Plutarch's *Lives* and Aristophanes all touch the mythological corpus
without being sources for it. Including them widens the corpus into history and comedy. My view
is to exclude them for now and revisit if the Greek set proves too small, which seems unlikely.

---

## Chinese: out of the dataset since 2026-09-04; 3 of 4 novels acquired, only 1 of them complete

**Target definition.** The Four Great Classical Novels, complete, in English.

| Novel | Status | Detail |
|---|---|---|
| Three Kingdoms | **HAVE, complete** | Brewitt-Taylor 1929, both volumes. Also the complete Chinese original |
| Journey to the West | **HAVE, abridged** | Richard 1913, roughly one sixth. Complete PD English is **BLOCKED** |
| Dream of the Red Chamber | **HAVE, partial** | Joly 1892, roughly chapters 1 to 56 of 120. The remainder is **BLOCKED**: Joly never finished it and no other pre-1931 English translation exists |
| Water Margin | **BLOCKED** | No public domain English translation exists. First complete one is Pearl Buck, 1933 |

### The one real lead left

**The Chinese-language originals.** Project Gutenberg has only Three Kingdoms in Chinese, but
the originals of all four are ancient and unambiguously public domain, and they are certainly
available from Chinese text repositories. The Chinese Text Project and Chinese Wikisource are
the obvious places.

This would close the Chinese corpus completely, at the cost of making it a non-English corpus.
That cost may be a benefit: it is a direct test of the model-agnostic claim, and it makes every
whitespace-based rule in the pipeline show itself, since Chinese does not delimit words with
spaces. The Three Kingdoms file already demonstrates the problem, reporting 20,000 "words" for
1.86 MB of text.

**RESOLVED 2026-09-04, out.** chinese/ is out of the dataset; whether it is an English corpus that happens to be incomplete or a Chinese corpus that is complete is asked again only if the folder returns.

### Also worth considering

*Investiture of the Gods* (Fengshen Yanyi) genuinely shares deities with Journey to the West:
Nezha, Li Jing, Erlang Shen. It would create real cross-work entity overlap rather than the
merely shared cosmology the Four Novels have. An English public domain translation is unlikely
to exist and has not been checked.

---

## Summary: nothing acquirable is still missing

69 files, roughly 5.15M words (chinese/ out and the Thebaid removed, 2026-09-04). Everything not present is blocked, quality-degraded, or a scope decision. Nothing is merely unfetched.

| Corpus | Files | Words | State |
|---|---|---|---|
| Oz | 29 | ~1.28M | Baum's 14, five companions, the Woggle-Bug Book, Thompson 1921-1930 |
| Holmes | 9 | ~0.69M | The complete canon of sixty |
| Greek | 31 | ~3.19M | Every major narrative source in public domain English |
| Chinese | 0 | — | Out of the dataset since 2026-09-04; 11 files acquired, complete in Chinese, permanently partial in English |

### Blocked: no public domain English source exists

| Item | Why |
|---|---|
| Hyginus, *Fabulae* | Archive.org has it only in Latin. The standard English is Mary Grant, 1960 |
| Nonnus, *Dionysiaca* | Only Greek and German editions predate 1931. Rouse's English Loeb is 1940 |
| Water Margin, English | Earliest complete translation is Pearl Buck, 1933 |
| Journey to the West, complete English | Richard 1913 is roughly one sixth. Complete is Yu, 1977 |
| Dream of the Red Chamber, chapters 57-120 | Joly died before finishing. No other pre-1931 translation |

### Blocked on quality rather than rights

**Statius, *Thebaid*.** The 1767 English verse translation is public domain and downloaded, but
the scan is unusable: 18th century printing uses the long s, which OCR renders as "f"
throughout. A real line reads "It muft oertoly be an infinite Fleafure to perafe". Entity
extraction on this would produce garbage. The 1928 Loeb (`volumeiithebaidb0002publ`) is cleaner
but covers only books 5 to 12 and is bilingual. Removed from the dataset 2026-09-04 on that basis; SOURCES.md keeps the provenance and the reason.

### Degraded but usable, recorded so it is not discovered later

Bilingual Loeb editions interleave Greek or Latin with English in their OCR: both Apollodorus
volumes and Ovid's Heroides. Three of the Chinese files and the Richard Journey to the West are
OCR from page scans. The Three Kingdoms proofread duplicate was there to put a number on what that costs; it went out with chinese/ on 2026-09-04 and returns only if the folder does.

### Open scope decisions, not acquisition problems

1. **Thompson's Oz books 1931 to 1939**, ten more volumes. Gutenberg carries several. Their
   status rests on non-renewal rather than expiry, the basis this project rejected for Conan.
2. **Herodotus, Plutarch, Aristophanes.** They touch the mythological corpus without being
   sources for it. Recommend excluding.
3. **Holmes apocrypha**, two short pieces, perhaps 2,000 words.
4. **Machine-translating the Chinese originals.** RESOLVED 2026-09-04, out: the translation control left with chinese/ and returns only if the folder does. Three Kingdoms was the calibration source, existing as Chinese original, human English translation, OCR and proofread text.

### On what "comprehensive" means for Greek

Greek has no natural boundary: there is a long tail of late antique mythographers, hymns and
scholia. The stopping rule applied here is **sources that assert facts about the pantheon and
heroes at narrative length, in public domain English.** By that rule the set is complete except
for the two blocked items above. Visible tail not pursued: the Orphic Hymns (Taylor 1792) and
Apuleius's Cupid and Psyche. Both could be added cheaply if coverage ever looks thin.
