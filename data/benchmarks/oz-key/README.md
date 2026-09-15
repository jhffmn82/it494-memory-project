# The Oz key

The one external key for ThreadAtlas's global layer: which document-local entities of the three
Oz books held in the test store are one identity. It is Wikipedia's "List of Oz characters
(created by Baum)", revision 1374825486, under CC BY-SA 4.0, one entry per character with the
names the page gives it (its heading, its main-article title, the terms the page sets in bold),
plus the aliases added by hand in `aliases-added.json`, each counted (53 across 30 characters).

Files:

- `wikipedia.json`: the page as the MediaWiki API returned it (wikitext and revision id), unedited.
- `aliases-added.json`: the hand-added aliases, character name to list.
- `oz-key.json`: the key, built by `scripts/build_oz_key.py` from the two above: source, license,
  revision, the three books, and 100 characters (83 with their own section, 17 from the minor
  list), each with `name`, `aliases`, `hand_aliases`, `about`.

How it scores a store (block 15b of `notebooks/threadatlas-global-layer.py`): a child of one of
the three books matches a character when its name or an alias folds to one of the character's
names (a name two characters share is dropped from matching). Over the cross-document pairs of
matched children: united (one parent) against split, recall = united / (united + split); wrong
joins are pairs of children of two characters under one parent; per character, the number of
parents its children span. Children the key does not name (places, objects, events, the minor
cast, Baum himself) are outside the score and listed when they are persons or animals.

The key is fixed before any run is scored; the vector floor of the global layer (0.75) was set
on 2026-09-14 without it.
