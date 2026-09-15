"""The Oz key: Wikipedia's list of the characters L. Frank Baum created (CC BY-SA 4.0), one entry per
character with the names the page gives it, plus the aliases added by hand in aliases-added.json
(each counted as a hand match). Reads data/benchmarks/oz-key/wikipedia.json (the API's parse
result, wikitext and revision id) and writes data/benchmarks/oz-key/oz-key.json.

    python scripts/build_oz_key.py
"""
import json
import re
from pathlib import Path

FOLDER = Path("data/benchmarks/oz-key")
SKIP = {"Other characters created by Baum", "See also", "References", "Sources"}
SPLIT = {"Aunt Em and Uncle Henry": ["Aunt Em", "Uncle Henry"], "Smith and Tinker": ["Smith", "Tinker"]}


def plain(text):
    """Wikitext to plain text: links to their labels, templates and references dropped, quotes stripped."""
    text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
    return text.replace("'''", "").replace("''", "").strip()


def entry(name, section, added):
    """One character: its names from the heading, the main link and the bold terms, plus the hand aliases."""
    names = [name]
    main = re.search(r"\{\{main\|([^}|]+)", section)
    if main:
        title = re.sub(r"\s*\([^)]*\)$", "", main.group(1)).strip()
        names.append(title)
    names += [b.strip() for b in re.findall(r"'''([^']+)'''", section)]
    names += added.get(name, [])
    seen, aliases = set(), []
    for n in names:
        if n and n.casefold() not in seen:
            seen.add(n.casefold())
            aliases.append(n)
    first = plain(section).split("\n")
    first = next((line for line in first if line.strip()), "")
    return {"name": name, "aliases": aliases, "hand_aliases": added.get(name, []), "about": first[:300]}


def main():
    page = json.load((FOLDER / "wikipedia.json").open(encoding="utf-8"))["parse"]
    added = json.load((FOLDER / "aliases-added.json").open(encoding="utf-8"))
    parts = re.split(r"^==+ *([^=]+?) *==+\s*$", page["wikitext"], flags=re.M)
    characters = []
    for heading, section in zip(parts[1::2], parts[2::2]):
        if heading in SKIP:
            continue
        for name in SPLIT.get(heading, [heading]):
            characters.append(entry(name, section if heading not in SPLIT else "", added))
    minor_section = parts[2 + 2 * parts[1::2].index("Other characters created by Baum")]
    for line in minor_section.split("\n"):
        m = re.match(r"\* *'''\[?\[?([^'\]]+)\]?\]?'''\s*-\s*(.*)", line)
        if m:
            name = m.group(1).strip()
            characters.append({"name": name, "aliases": [name] + added.get(name, []), "hand_aliases": added.get(name, []),
                               "about": plain(m.group(2))[:300], "minor": True})
    key = {"source": "https://en.wikipedia.org/wiki/List_of_Oz_characters_(created_by_Baum)",
           "license": "CC BY-SA 4.0", "revision": page["revid"], "title": page["title"],
           "books": ["The Wonderful Wizard of Oz", "The Marvelous Land of Oz", "Ozma of Oz"],
           "characters": characters}
    (FOLDER / "oz-key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    hand = sum(len(c["hand_aliases"]) for c in characters)
    print(f"{len(characters)} characters ({sum(1 for c in characters if c.get('minor'))} minor), {hand} hand aliases, revision {page['revid']}")


if __name__ == "__main__":
    main()
