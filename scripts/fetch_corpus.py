"""Fetch a corpus from Project Gutenberg into data/raw/<corpus>/.

Downloads only. No cleaning, no chapter splitting: those are separate steps so the
raw download stays a verifiable artifact. Every file is recorded in a manifest with
its source URL, byte count and sha256, which is what makes a work strikeable later
(a filter over the manifest, not a rebuild).

Usage: python scripts/fetch_corpus.py oz
"""
import hashlib, json, sys, time, urllib.request
from pathlib import Path

# Windows consoles default to cp1252, which cannot print CJK. The corpus includes
# Chinese-language source, so make stdout UTF-8 rather than avoid the characters.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
UA = "IT494-research-corpus/0.1 (ISU graduate project; contact via repo)"

# Baum's fourteen canonical Oz books, in publication order. `expect` is a distinctive
# fragment of the real title, checked against the Gutenberg header so a wrong ebook
# number fails loudly instead of silently poisoning the corpus.
CORPORA = {
    "oz": {
        "title": "The Oz books (L. Frank Baum, 1900-1920)",
        "works": [
            (1,  55,    "Wonderful Wizard of Oz"),
            (2,  54,    "Marvelous Land of Oz"),
            (3,  486,   "Ozma of Oz"),
            (4,  420,   "Dorothy and the Wizard in Oz"),
            (5,  485,   "Road to Oz"),
            (6,  517,   "Emerald City of Oz"),
            (7,  955,   "Patchwork Girl of Oz"),
            (8,  956,   "Tik-Tok of Oz"),
            (9,  957,   "Scarecrow of Oz"),
            (10, 958,   "Rinkitink in Oz"),
            (11, 959,   "Lost Princess of Oz"),
            (12, 960,   "Tin Woodman of Oz"),
            (13, 419,   "Magic of Oz"),
            (14, 961,   "Glinda of Oz"),
        ],
    },

    # Greek: a shared pantheon across independent sources that disagree with each other.
    # Ordinal here is source position, NOT story time; the two differ in this corpus and
    # that difference is the point.
    "greek": {
        "title": "Greek and Roman mythological sources",
        "works": [
            (1,  2199,  "Iliad"),
            (2,  1727,  "Odyssey"),
            (3,  348,   "Homeric Hymns"),           # Hesiod + Homerica, Evelyn-White
            (4,  31,    "Sophocles"),               # Oedipus the King / Colonus / Antigone
            (5,  14484, "Seven Plays"),             # Sophocles, complete surviving plays
            (6,  8604,  "House of Atreus"),         # Aeschylus, the Oresteia
            (7,  15081, "Euripides"),               # Tragedies, volume I
            (8,  21765, "Metamorphoses"),           # Ovid, books I-VII
            (9,  26073, "Metamorphoses"),           # Ovid, books VIII-XV
        ],
    },

    # Chinese: INCOMPLETE by necessity, not by choice. See data/raw/SOURCES.md.
    "chinese": {
        "title": "Chinese classical novels (partial: see SOURCES.md)",
        "works": [
            (1,  77416, "three kingdoms"),          # Brewitt-Taylor 1925, volume 1 of 2
            (2,  23950, "三國"),            # Chinese-language original, complete
        ],
    },
}


def gutenberg_urls(ebook_id):
    """Gutenberg has moved text files around over the years; try the known layouts."""
    return [
        f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt",
        f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}-0.txt",
        f"https://www.gutenberg.org/files/{ebook_id}/{ebook_id}.txt",
    ]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main(corpus_key):
    spec = CORPORA[corpus_key]
    out = ROOT / "data" / "raw" / corpus_key
    out.mkdir(parents=True, exist_ok=True)
    manifest, failures = [], []

    for ordinal, ebook_id, expect in spec["works"]:
        dest = out / f"{ordinal:02d}_{ebook_id}.txt"
        raw, used = None, None

        if dest.exists():                      # idempotent: never refetch
            raw, used = dest.read_bytes(), "cached"
        else:
            for url in gutenberg_urls(ebook_id):
                try:
                    raw, used = fetch(url), url
                    break
                except Exception as e:
                    last = f"{type(e).__name__}: {e}"
            if raw is None:
                failures.append((ordinal, ebook_id, expect, last))
                print(f"  [{ordinal:02d}] FAIL  #{ebook_id}  {expect}  ({last})")
                continue
            dest.write_bytes(raw)
            time.sleep(1)                      # be a decent citizen

        text = raw.decode("utf-8", errors="replace")
        head = text[:1500]
        ok = expect.lower() in head.lower()
        if not ok:
            first = next((l for l in head.splitlines() if l.strip()), "")
            failures.append((ordinal, ebook_id, expect, f"title mismatch; header says {first!r}"))

        manifest.append({
            "ordinal": ordinal, "ebook_id": ebook_id, "expected_title": expect,
            "title_verified": ok, "source_url": used, "file": dest.name,
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "words_est": len(text.split()),
        })
        flag = "ok " if ok else "MISMATCH"
        print(f"  [{ordinal:02d}] {flag} #{ebook_id:<6} {expect:<32} "
              f"{len(raw):>8,} b  ~{len(text.split()):>7,} words")

    (out / "manifest.json").write_text(json.dumps(
        {"corpus_id": corpus_key, "title": spec["title"],
         "source": "Project Gutenberg (US, public domain)",
         "works": manifest}, indent=2), encoding="utf-8")

    total = sum(m["words_est"] for m in manifest)
    print(f"\n{len(manifest)}/{len(spec['works'])} works | ~{total:,} words total")
    print(f"manifest -> {(out / 'manifest.json').relative_to(ROOT)}")
    if failures:
        print("\nNEEDS ATTENTION:")
        for o, e, x, why in failures:
            print(f"  [{o:02d}] #{e} {x}: {why}")
    return failures


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "oz")
