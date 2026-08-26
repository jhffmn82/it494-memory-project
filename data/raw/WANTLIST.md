# Want list: what each corpus needs to be complete

A corpus assembled opportunistically has no completeness measure. This file defines the target
set for each corpus first, so that "we have 19 of 19" or "we have 13 of 24" is a statement with
meaning behind it, and so that a gap is a recorded decision rather than an oversight.

Status codes used throughout:

- **HAVE** — downloaded, title-verified, in `data/raw/`
- **HUNT** — public domain and believed to exist, not yet located or not on Project Gutenberg
- **BLOCKED** — no public domain English source exists, with the reason recorded
- **DECIDE** — availability is not the question; whether it belongs in the set is

---

## Oz: 28 of 28. Baum's canon, his companions, and Thompson's run to 1930

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
| The Woggle-Bug Book | 1905 | HUNT | Oz character spinoff. Not yet searched |
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

## Greek: 13 of roughly 24, and the gaps are the interesting ones

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

### Hunt

| Work | Why it matters | Where to look |
|---|---|---|
| **Apollodorus, *Bibliotheca*** | An ancient systematic mythography. The closest thing antiquity produced to this project's own output. Frazer's 1921 Loeb is public domain | Archive.org, HathiTrust |
| **Euripides, volumes II and III** | We have volume I only. Euripides is the source that most often contradicts Homer, so a third of him is a third of the disagreement | Gutenberg individual plays, or Way's Loeb on Archive.org |
| **Pausanias, *Description of Greece*** | Geographic mythography: which city claimed which hero, where the tombs were. Local variants that contradict the panhellenic versions | Frazer 1898 or Jones 1918, Archive.org |
| **Quintus Smyrnaeus, *The Fall of Troy*** | Fills the gap between the Iliad's end and the Odyssey's start. Way's 1913 translation | Gutenberg, not yet searched |
| **Ovid, *Heroides*** | Letters from mythological women. The same events from the perspective the epics do not give | Gutenberg, not yet searched |
| **Hyginus, *Fabulae*** | A second ancient mythography. Not on Gutenberg. May have no pre-1931 English translation, in which case it is BLOCKED rather than HUNT | Needs checking |
| **Statius, *Thebaid*** | The Theban war at epic length | Not yet searched |
| **Pindar, *Odes*** | Mythological narrative embedded in victory poems, often the earliest surviving version of a story | Not yet searched |

### Decide

Herodotus, Thucydides, Plutarch's *Lives* and Aristophanes all touch the mythological corpus
without being sources for it. Including them widens the corpus into history and comedy. My view
is to exclude them for now and revisit if the Greek set proves too small, which seems unlikely.

---

## Chinese: 3 of 4 novels present, only 1 of them complete

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

**DECIDE.** Whether the Chinese corpus is an English corpus that happens to be incomplete, or a
Chinese corpus that is complete. It cannot be both.

### Also worth considering

*Investiture of the Gods* (Fengshen Yanyi) genuinely shares deities with Journey to the West:
Nezha, Li Jing, Erlang Shen. It would create real cross-work entity overlap rather than the
merely shared cosmology the Four Novels have. An English public domain translation is unlikely
to exist and has not been checked.

---

## Summary of what is actually needed

| Corpus | Have | Target | Blocked | Decisions open |
|---|---|---|---|---|
| Oz | 19 | 19, or 28 with Thompson | 0 | Thompson yes or no |
| Holmes | 9 vols / 60 works | 60 | 0 | none |
| Greek | 13 | ~21 | 0 to 1 | history and comedy in or out |
| Chinese | 7 files / 3 novels | 4 novels | 1 whole novel, 2 partials | English incomplete, or Chinese complete |

The Greek hunt list is where the effort should go. Every item on it is public domain, exists,
and is findable with the same Archive.org method that rescued Three Kingdoms. Nothing there is
blocked, only unfetched.
