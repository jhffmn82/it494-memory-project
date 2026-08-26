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
            # Companion works in the same continuity. Ordinal here is file order, not
            # publication order; see the `year` field for the real sequence.
            (15, 48778, "Sea Fairies", 1911),      # Trot and Cap'n Bill introduced
            (16, 4356,  "Sky Island", 1912),   # 21159 has no plain-text format       # Trot, Cap'n Bill, Button-Bright
            (17, 25519, "Little Wizard Stories", 1913),
            (18, 520,   "Santa Claus", 1902),      # Santa attends Ozma's party in book 5
            (19, 30537, "Royal Book of Oz", 1921), # Thompson, credited to Baum

            # Thompson's Oz run, 1922-1930. Public domain by expiry of term, same basis
            # as Baum. The reason they are here is the change of author mid-canon: a fact
            # Thompson asserts about Baum's characters is a different class of evidence
            # from one Baum asserted, and no other corpus in this project has that.
            (20, 53765, "Kabumpo in Oz", 1922),
            (21, 58765, "Cowardly Lion of Oz", 1923),
            (22, 61681, "Grampa in Oz", 1924),
            (23, 65849, "Lost King of Oz", 1925),
            (24, 70152, "Hungry Tiger of Oz", 1926),
            (25, 71273, "Gnome King of Oz", 1927),
            (26, 73170, "Giant Horse of Oz", 1928),
            (27, 75720, "Jack Pumpkinhead of Oz", 1929),
            (28, 78637, "Yellow Knight of Oz", 1930),
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
            (10, 8714,  "Aeschylus"),               # the plays outside the Oresteia
            (11, 830,   "Argonautica"),             # Apollonius: Jason, Medea, Heracles
            (12, 228,   "Aeneid"),                  # Virgil: Troy from the other side
            (13, 3327,  "Age of Fable"),            # Bulfinch, a 19th c. mythography
        ],
    },

    # Holmes: the contamination probe. What the text says and what the culture
    # believes have measurably diverged, so induced descriptions can be checked
    # against the corpus rather than against received impression.
    "holmes": {
        "title": "The Sherlock Holmes canon (Doyle, 1887-1927)",
        "works": [
            (1, 244,   "Study in Scarlet"),
            (2, 2097,  "Sign of the Four"),
            (3, 1661,  "Adventures of Sherlock Holmes"),
            (4, 834,   "Memoirs of Sherlock Holmes"),
            (5, 2852,  "Hound of the Baskervilles"),
            (6, 108,   "Return of Sherlock Holmes"),
            (7, 3289,  "Valley of Fear"),
            (8, 2350,  "His Last Bow"),
            (9, 69700, "Case-Book of Sherlock Holmes"),
        ],
    },

    # Chinese: INCOMPLETE by necessity, not by choice. See data/raw/SOURCES.md.
    "chinese": {
        "title": "Chinese classical novels (partial: see SOURCES.md)",
        "works": [
            # Three Kingdoms, COMPLETE. Brewitt-Taylor 1929 printing, both volumes, from a
            # Graduate Theological Union scan. Gutenberg has only volume 1 (#77416).
            # Volume identity was confirmed from chapter content, not from the item labels:
            # the identifier suffixes are misleading (0001 is vol 1, 0000 is vol 2).
            (1, "sankuoorromanceo0001chbr", "San Kuo"),
            (2, "sankuoorromanceo0000chbr", "San Kuo"),

            # Journey to the West, ABRIDGED. Timothy Richard 1913, Cornell scan. Roughly a
            # sixth of the novel. Archive.org credits this to Li Zhichang, who wrote a
            # different work of the same English title; the text is signed by Richard and
            # is the Wu Cheng'en novel. Do not trust that catalogue record.
            (3, "cu31924074502034", "mission to heaven"),

            # Chinese-language Three Kingdoms, complete and unabridged.
            (4, 23950, "三國"),

            # Volume 1 AGAIN, as a Gutenberg proofread transcription of the 1925 printing.
            # Deliberate duplicate: the same content exists here as human-proofread text
            # and as OCR (work 1), which makes OCR error cost measurable rather than
            # assumed. Extract entities from both and the difference is the OCR tax.
            (5, 77416, "three kingdoms"),

            # Dream of the Red Chamber, PARTIAL. Joly 1892 rendered roughly the first
            # 56 of 120 chapters. The fourth Great Classical Novel; ~400 named characters
            # in a dense kinship graph.
            (6, 9603, "Hung Lou Meng", 1892),
            (7, 9604, "Hung Lou Meng", 1892),
        ],
    },
}


def source_urls(work_id):
    """An int is a Project Gutenberg ebook number; a string is an Archive.org identifier.

    Gutenberg is preferred wherever it has the text: it serves proofread transcriptions.
    Archive.org items here are library scans with OCR text, used only where no Gutenberg
    edition exists. OCR quality is a real variable and is recorded in SOURCES.md.
    """
    if isinstance(work_id, int):
        return [
            f"https://www.gutenberg.org/cache/epub/{work_id}/pg{work_id}.txt",
            f"https://www.gutenberg.org/files/{work_id}/{work_id}-0.txt",
            f"https://www.gutenberg.org/files/{work_id}/{work_id}.txt",
        ]
    return [f"https://archive.org/download/{work_id}/{work_id}_djvu.txt"]


def fetch(url):
    """requests, because the system CA bundle is stale and Archive.org redirects to a
    CDN host that fails verification against it. requests uses certifi."""
    try:
        import requests
        r = requests.get(url, headers={"User-Agent": UA}, timeout=180)
        r.raise_for_status()
        return r.content
    except ImportError:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as r:
            return r.read()


def main(corpus_key):
    spec = CORPORA[corpus_key]
    out = ROOT / "data" / "raw" / corpus_key
    out.mkdir(parents=True, exist_ok=True)
    manifest, failures = [], []

    for work in spec["works"]:
        ordinal, ebook_id, expect = work[0], work[1], work[2]
        year = work[3] if len(work) > 3 else None
        dest = out / f"{ordinal:02d}_{ebook_id}.txt"
        raw, used = None, None

        if dest.exists():                      # idempotent: never refetch
            raw, used = dest.read_bytes(), "cached"
        else:
            for url in source_urls(ebook_id):
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
            "year": year,
            "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "words_est": len(text.split()),
        })
        flag = "ok " if ok else "MISMATCH"
        print(f"  [{ordinal:02d}] {flag} {str(ebook_id):<26} {expect:<30} "
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
