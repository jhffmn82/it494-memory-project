"""Rebuild the extractor's export locally from a run's rendered log and the raw files.

The extractor run of 2026-09-06 (Kaggle script version 347794765) finished in an interactive
session, and a Quick Save keeps the printed log but not /kaggle/working. The log prints, for
every text and PDF document, each piece's start offset, word count, unit number, kind, label
(cut at 40 characters) and the first 60 characters of its text, plus the document's title,
author, source, class and date. Pieces tile a document, so every piece's end is the next
piece's start; units are the runs of pieces sharing a unit number. Chats need no model call,
so their pieces and units are rebuilt by the extractor's own code.

Every rebuilt piece is checked against the log's snippet, character for character, so a text
that decodes differently here than on Kaggle (a PyMuPDF version, a line ending) is caught and
the document is left out and listed, never exported wrong.

    python scripts/rebuild_export.py [RAW] [PAPERS] [LOG] [OUT]

Defaults: the main clone's data/raw and papers, today's saved log, and data/export/ here.
The receipt says it is a rebuild and from which run.
"""
import ast
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Users/jhffm/it494-memory-project/data/raw")
PAPERS = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("C:/Users/jhffm/it494-memory-project/papers")
LOG = Path(sys.argv[3]) if len(sys.argv) > 3 else HERE / "log/2026-09-06/extractor-run-347794765.txt"
OUT = Path(sys.argv[4]) if len(sys.argv) > 4 else HERE / "data/export"
AS_RUN = HERE / "log/2026-09-06/threadatlas-extractor-as-run-347794765.py"
RUN = "347794765"
RAW_NAME, PAPERS_NAME = "it494-narrative-corpora-raw", "it494-reference-papers"   # the Kaggle mount names the real export uses

# The extractor's own code for the parts that need no model: block 2 (bytes to text), the chat
# functions of block 7, and unit_id from block 9. Exec'd from the script as it ran on Kaggle.
src = AS_RUN.read_text(encoding="utf-8")
cells = src.split("\n# %%\n")
block = {int(m.group(1)): c for c in cells for m in [re.search(r"^# Block (\d+):", c, re.M)] if m}
ns = {}
exec("import hashlib, json, re\nfrom pathlib import Path\nfrom datetime import datetime", ns)
exec(block[2].split("# One of each, to see the shape.")[0], ns)
b7 = block[7]
for name in ("parse_time", "chat_pieces", "day", "chat_runs", "units_from_runs"):
    start = b7.index(f"\ndef {name}(")
    end = b7.find("\n\n\ndef ", start + 1)
    exec(b7[start:end if end > 0 else None], ns)
for name in ("CAP_WORDS", "TAIL_FLOOR"):
    exec(re.search(rf"^{name} = .*$", src, re.M).group(0), ns)
exec(re.search(r"^def piece\(.*?\n\n\n", src, re.M | re.S).group(0), ns)
exec(re.search(r"^def words\(.*?\n\n\n", src, re.M | re.S).group(0), ns)
exec(re.search(r"^def unit_id\(.*?\n\n\n", src, re.M | re.S).group(0), ns)
to_text, chat_pieces, chat_runs, units_from_runs, unit_id, parse_time = (
    ns["to_text"], ns["chat_pieces"], ns["chat_runs"], ns["units_from_runs"], ns["unit_id"], ns["parse_time"])
LOADER = re.search(r'^LOADER = "(.*?)"', src, re.M).group(1)

HEADER = re.compile(r"^(\S+)\s+(ok|FLAGGED)\s+pieces (\d+)\s+units (\d+)")
ROW = re.compile(r"^ {4} {0,7}(\d+) +(\d+) w  u(\d+) +(\S+) ")     # start is right-aligned in 8 columns
META = re.compile(r"class (\S+) \| title (.*?) \| author (.*?) \| source (.*?) \| date (\S+) \| toc")


def parse_row(line):
    """A piece line of the extractor's show(): fixed-width columns, so a label or a snippet that
    itself holds ' | ' (a table drawn in text) cannot move the separator. The line is
    f"    {start:>8} {words:>6} w  u{unit:<3} {kind[:12]:<12} {label[:40]:<40} | {snippet}"."""
    m = ROW.match(line)
    if not m:
        return None
    kind_at = 28                                  # 4 + 8 + 1 + 6 + 3 + 1 + 4 + 1
    kind = line[kind_at:kind_at + 12].strip()
    label = line[kind_at + 13:kind_at + 53].strip()
    sep = line[kind_at + 53:kind_at + 56]
    if kind != m.group(4) or sep != " | ":
        return None
    return {"start": int(m.group(1)), "words": int(m.group(2)), "unit": int(m.group(3)),
            "kind": kind, "label": label, "snip": line[kind_at + 56:]}


def read_log(path):
    """{file name: {flag, meta, pieces:[{start, words, unit, kind, label, snip}], flags}} for the
    text and PDF documents the log printed in full."""
    docs, cur = {}, None
    for line in path.read_text(encoding="utf-8").split("\n"):
        m = HEADER.match(line)
        if m:
            cur = m.group(1)
            docs[cur] = {"flag": m.group(2), "pieces": [], "flags": [], "meta": None}
            continue
        if cur is None:
            continue
        if line.startswith("    class "):
            docs[cur]["meta"] = line.strip()
        elif line.startswith("    FLAG "):
            docs[cur]["flags"].append(line.strip()[5:])
        else:
            row = parse_row(line)
            if row:
                docs[cur]["pieces"].append(row)
    return docs


def literal(s):
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return None


def meta_of(line):
    m = META.search(line or "")
    if not m:
        return {"source_class": None, "title": None, "author": None, "source": None, "date": None}
    date = m.group(5)
    return {"source_class": m.group(1) if m.group(1) != "None" else None, "title": literal(m.group(2)),
            "author": literal(m.group(3)), "source": literal(m.group(4)), "date": None if date == "None" else date}


def snippet(text, start):
    return " ".join(text[start:start + 90].split())[:60]


def find_file(name):
    if name.endswith(".pdf"):
        p = PAPERS / name
        return p, f"{PAPERS_NAME}/{name}"
    for folder in ("oz", "holmes", "greek", "graphrag-bench"):
        p = RAW / folder / name
        if p.exists():
            return p, f"{RAW_NAME}/{folder}/{name}"
    return None, None


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    files = {n: (OUT / f"{n}.jsonl").open("w", encoding="utf-8", newline="\n") for n in ("documents", "units", "pieces")}   # LF, as on Kaggle
    receipt = {"rebuilt_from_run": RUN, "rebuilt_at": now, "loader": LOADER, "documents": 0, "units": 0, "pieces": 0,
               "by_kind": {}, "skipped": [], "snippet_mismatches": 0, "label_cut_at": 40, "flagged": []}
    exported = {}

    def write_document(doc_id, src, text, meta, occurred, flags, kind, units, pieces):
        author = meta["author"]
        if author is None and meta["source"]:
            author = meta["source"]
            flags = flags + ["author is a publication"]
        files["documents"].write(json.dumps({
            "doc_id": doc_id, "source_uri": src, "sha256": doc_id, "title": meta["title"], "author": author,
            "source_class": meta["source_class"], "text": text, "ingested_at": now, "occurred_at": occurred,
            "loader": LOADER, "flags": flags}, ensure_ascii=False) + "\n")
        ids, seen = [], {}
        for u in units:
            uid = unit_id(doc_id, text, u["start"], u["end"], seen)
            ids.append(uid)
            assert text[u["start"]:u["end"]].strip(), (src, u)
            files["units"].write(json.dumps({"unit_id": uid, "doc_id": doc_id, "position": u["position"], "label": u["label"],
                                             "start": u["start"], "end": u["end"], "occurred_at": u["occurred_at"],
                                             "occurred_until": u["occurred_until"]}, ensure_ascii=False) + "\n")
        for position, p in enumerate(pieces):
            files["pieces"].write(json.dumps({"doc_id": doc_id, "unit_id": ids[p["unit"]], "position": position,
                                              "kind": p["kind"], "start": p["start"], "end": p["end"],
                                              "author": p["author"], "occurred_at": p["occurred_at"]}, ensure_ascii=False) + "\n")
        receipt["documents"] += 1
        receipt["units"] += len(units)
        receipt["pieces"] += len(pieces)
        receipt["by_kind"][kind] = receipt["by_kind"].get(kind, 0) + 1
        if flags:
            receipt["flagged"].append({"source_uri": src, "flags": flags})

    # Text and PDF documents: pieces and units from the log, verified against the file.
    logged = read_log(LOG)
    for name, rec in logged.items():
        path, src = find_file(name)
        if path is None:
            receipt["skipped"].append({"file": name, "why": "not on disk"})
            continue
        doc = to_text(path)
        text, doc_id = doc["text"], doc["sha256"]
        if doc_id in exported:
            receipt["skipped"].append({"file": name, "why": f"same bytes as {exported[doc_id]}"})
            continue
        rows = rec["pieces"]
        bad = [p["start"] for p in rows if snippet(text, p["start"]) != p["snip"]]
        if bad or not rows:
            receipt["snippet_mismatches"] += len(bad)
            receipt["skipped"].append({"file": name, "why": f"{len(bad)} of {len(rows)} snippets differ" if rows else "no pieces logged"})
            continue
        meta = meta_of(rec["meta"])
        occurred = meta["date"]
        pieces = []
        for p, nxt in zip(rows, rows[1:] + [None]):
            end = nxt["start"] if nxt else len(text)
            pieces.append({"start": p["start"], "end": end, "label": p["label"], "kind": p["kind"],
                           "author": None, "occurred_at": None, "unit": p["unit"]})
        # the log's word count is a second check on the range
        off = [p for p, r in zip(pieces, rows) if len(text[p["start"]:p["end"]].split()) != r["words"]]
        if off:
            receipt["skipped"].append({"file": name, "why": f"{len(off)} piece word counts differ"})
            continue
        units = []
        for p in pieces:
            if units and units[-1]["position"] == p["unit"]:
                units[-1]["end"] = p["end"]
                units[-1]["label"] = f"{units[-1]['first']} .. {p['label']}"
            else:
                assert p["unit"] == len(units), (name, p)
                units.append({"position": p["unit"], "start": p["start"], "end": p["end"], "label": p["label"],
                              "first": p["label"], "occurred_at": occurred, "occurred_until": occurred})
        for u in units:
            del u["first"]
        exported[doc_id] = name
        write_document(doc_id, src, text, meta, occurred, rec["flags"], doc["kind"], units, pieces)

    # Chats: the extractor's own code, no model, no log needed.
    for path in sorted(p for p in (RAW / "longmemeval").glob("*.json") if p.name != "manifest.json"):
        doc = to_text(path)
        if doc["kind"] != "chat":
            receipt["skipped"].append({"file": path.name, "why": "not a chat"})
            continue
        pieces, flags = chat_pieces(doc)
        runs = chat_runs(pieces, doc["text"])
        units = units_from_runs(pieces, runs, doc["text"])
        dates = sorted(t for t in (parse_time(d) for d in doc["dates"]) if t)
        meta = {"source_class": "record", "title": None, "author": None, "source": None, "date": None}
        if doc["sha256"] in exported:
            receipt["skipped"].append({"file": path.name, "why": f"same bytes as {exported[doc['sha256']]}"})
            continue
        exported[doc["sha256"]] = path.name
        write_document(doc["sha256"], f"{RAW_NAME}/longmemeval/{path.name}", doc["text"], meta,
                       dates[0] if dates else None, flags, "chat", units, pieces)
        if receipt["by_kind"]["chat"] % 2000 == 0:
            print(f"  chats {receipt['by_kind']['chat']}")

    for f in files.values():
        f.close()
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"documents {receipt['documents']}  units {receipt['units']}  pieces {receipt['pieces']}  by kind {receipt['by_kind']}")
    print(f"skipped {len(receipt['skipped'])}  snippet mismatches {receipt['snippet_mismatches']}")
    for s in receipt["skipped"][:40]:
        print(f"    {s['file']}: {s['why']}")


if __name__ == "__main__":
    main()
