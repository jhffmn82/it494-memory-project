"""Offline tests for 0.9, the eleven defects the diagnosis of run 347601080 confirmed.
Run from the repository root."""
import json
import re
import shutil
import sys
from pathlib import Path

SCR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Users/jhffm/AppData/Local/Temp/claude/C--Users-jhffm-claude-archive/cd11ff96-d4f9-4abd-878f-030ba8ba58dd/scratchpad/test_diag")
shutil.rmtree(SCR, ignore_errors=True)
SCR.mkdir(parents=True)

src = Path("notebooks/factledger-extractor.py").read_text(encoding="utf-8")
cells = src.split("\n# %%\n")
block = {int(m.group(1)): c for c in cells for m in [re.search(r"^# Block (\d+):", c, re.M)] if m}
ns = {}
exec("import hashlib, json, re\nfrom pathlib import Path\nfrom datetime import datetime\nfrom concurrent.futures import ThreadPoolExecutor\n"
     "RAW = Path('data/raw'); PAPERS = Path('papers')", ns)
exec(block[2].split("# One of each, to see the shape.")[0], ns)
calls, script = [], {}


class TooLong(Exception):
    pass


class SpendStop(Exception):
    pass


def generate(prompt, model="luna", effort="low"):
    calls.append((model, prompt[:22]))
    lines = {int(m.group(1)): m.group(2) for m in re.finditer(r"^\[(\d+)\] (.*)$", prompt, re.M)}
    if prompt.startswith("Below is one document"):
        return script["main"](lines)
    if prompt.startswith("Below is one piece"):
        return script.get("split", lambda l: {"breaks": []})(lines)
    if prompt.startswith("Below is the outline"):
        return {"units": [{"first": i, "last": i} for i in range(len(lines))]}
    if prompt.startswith("Below are the pieces"):
        return script.get("merge", lambda l: {"merges": []})(lines)
    raise AssertionError(prompt[:40])


ns.update(MODEL="luna", RETRY="terra", RETRY_MAX_TOKENS=80_000, TooLong=TooLong, SpendStop=SpendStop,
          generate=generate, spend=lambda: 0.0)
exec(block[4][:block[4].index("for path in [")], ns)
exec(block[5], ns)
exec(block[6], ns)
exec(block[7], ns)
b8defs = block[8][:block[8].index("paths = ")]
b8defs = b8defs.replace('Path("/kaggle/working/splits.jsonl")', f'Path(r"{SCR / "splits.jsonl"}")').replace('Path("/kaggle/working/splits.log")', f'Path(r"{SCR / "splits.log"}")')
exec(b8defs, ns)
R = lambda k: ns[k]
ok = []


def check(name, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  ' + str(detail)) if detail else ''}")


print("== 8. a text layer of one word per line is addressed by sentence ==")
pdf = Path("papers/snodgrass1999-time-oriented-db.pdf")
if pdf.exists():
    d = ns["to_text"](pdf)
    a = R("addresses")(d["text"])
    per = sum(len(d["text"][slice(*s)].split()) for s in a) / max(1, len(a))
    check("snodgrass is addressed by sentence, not by its one-word lines", len(a) < 30_000 and per > 3, f"{len(a):,} addresses, {per:.1f} words each")
    check("its listing now fits a call", len(R("listing")(d["text"], a)) // 4 < 400_000, f"{len(R('listing')(d['text'], a)) // 4:,} tokens")
else:
    check("snodgrass present", False, "papers/snodgrass1999-time-oriented-db.pdf missing")
oz = ns["to_text"](Path("data/raw/oz/01_55.txt"))
check("an ordinary book is still addressed by line", len(R("addresses")(oz["text"])) == 3812, len(R("addresses")(oz["text"])))

print("\n== 4. a title, author, source or date verifies inside its line at any length ==")
t = "net IMPRESSIONS OF THEOPHRASTUS SUCH GEORGE ELIOT Second Edition William Blackwood and Sons Edinburgh MDCCCLXXIX and more words follow here\nsecond line\n"
a = R("addresses")(t)
r = {"title": {"index": 0, "text": "IMPRESSIONS OF THEOPHRASTUS SUCH", "title": "Impressions of Theophrastus Such"},
     "author": {"index": 0, "text": "GEORGE ELIOT", "name": "George Eliot"},
     "source": {"index": 0, "text": "William Blackwood and Sons", "name": "William Blackwood and Sons"},
     "date": {"index": 0, "text": "MDCCCLXXIX", "iso": "1879"}}
st = R("fresh_stats")(a, "luna")
R("verify_meta")(t, r, a, st)
check("four values inside one long address all verify", all(r[k] is not None for k in ("title", "author", "source", "date")), {k: (r[k] is not None) for k in r})
check("nothing counted as nulled", st.get("meta_unresolved", 0) == 0, st)
st = R("fresh_stats")(a, "luna")
r2 = {"author": {"index": 0, "text": "CHARLES DICKENS", "name": "Charles Dickens"}}
R("verify_meta")(t, r2, a, st)
check("an author who is not on the line is still nulled", r2["author"] is None and st["meta_nulled"] == ["author"], st.get("meta_nulled"))
st = R("fresh_stats")(a, "luna")
check("a two-word heading pointer is still strict", R("resolve")({"index": 1, "text": "second"}, t, a, st) is None or R("resolve")({"index": 1, "text": "second line"}, t, a, R("fresh_stats")(a, "luna")) == a[1])

print("\n== 6. the count gate fires only when the model found fewer pieces than the contents lists ==")
st = {"headed": 24, "unresolved": 0}
check("24 headed against a contents list of 24: no flag", not any(f.startswith("count") for f in R("gates")([], {"toc_count": 24}, st, "")))
check("24 headed against 89: flagged", any(f.startswith("count") for f in R("gates")([], {"toc_count": 89}, st, "")))
check("24 headed against 10: no flag", not any(f.startswith("count") for f in R("gates")([], {"toc_count": 10}, st, "")))

print("\n== 5. a merge is refused for the cap only when the cap is not already broken ==")
def pcs_from(spec):
    text, pieces, pos = "", [], 0
    for label, n, kind in spec:
        seg = label + "\n" + ("w " * max(0, n - len(label.split()))) + "\n"
        pieces.append(ns["piece"](pos, pos + len(seg), label, kind)); text += seg; pos += len(seg)
    return text, pieces
t, pcs = pcs_from([("II.", 1, "body"), ("A Scandal in Bohemia", 4005, "body")])
script["merge"] = lambda l: {"merges": [{"index": 0, "into": "next"}]}
fl = []
m = R("merge_short")(t, pcs, {}, fl)
check("a bare heading joins a chapter already over the cap, no orphan unit", len(m) == 1 and not fl, (len(m), fl))
t, pcs = pcs_from([("Big", 3990, "body"), ("tail", 30, "body")])
script["merge"] = lambda l: {"merges": [{"index": 1, "into": "previous"}]}
fl = []
m = R("merge_short")(t, pcs, {}, fl)
check("a merge that would itself carry a piece past the cap is still refused", len(m) == 2 and any(f.startswith("merging: over cap") for f in fl), fl)

print("\n== 1. a record carries its loader, and a rerun redoes what an older loader left ==")
check("the loader is defined in block 8, before the record is written", "LOADER" in ns and ns["LOADER"].endswith("0.9"), ns.get("LOADER"))
old = {"file": "raw/oz/01_55.txt", "path": "x", "sha256": "s1", "kind": "chat", "flags": [], "units": [], "pieces": [], "stats": {}, "cost": 0}
cur = {**old, "file": "raw/oz/02_54.txt", "sha256": "s2", "loader": ns["LOADER"]}
(SCR / "splits.jsonl").write_text("\n".join(json.dumps(x) for x in (old, cur)) + "\n", encoding="utf-8")
latest = R("read_splits")()
done = {k for k, rec in latest.items() if rec.get("loader") == ns["LOADER"]
        and (all(R("advisory")(f) for f in rec["flags"]) or rec.get("kind") == "chat" or rec["tries"] >= 2)}
check("a clean chat from an older loader is NOT done", "raw/oz/01_55.txt" not in done, done)
check("a clean chat from this loader is done", "raw/oz/02_54.txt" in done, done)

print("\n== 2, 3, 7, 9. block 9 ==")
b9 = block[9]
check("a chat document takes the earliest date, sorted", 'dates = sorted(t for t in (parse_time(d) for d in doc["dates"]) if t)' in b9
      and 'occurred = dates[0] if dates else None' in b9)
check("the reused-date counter reads the flag key, not a prefix",
      'f.split(":")[0] in ("dates", "ambiguous date")' in b9)
check("short and over-cap units are both split by kind, neither excluding chats",
      'receipt[f"over_cap_{side}"]' in b9 and 'receipt[f"short_{side}"]' in b9
      and 'receipt["short_units"] += u["words"] < SHORT_WORDS\n' in b9)
check("a publication becomes the author only when no person was named",
      '"author" not in st_of(record).get("meta_nulled", [])' in b9)

print("\n== the chat date rule end to end ==")
doc = ns["to_text"](Path("data/raw/longmemeval/001cefa7_2.json"))
pieces, flags = R("chat_pieces")(doc)
units = R("units_from_runs")(pieces, R("chat_runs")(pieces), doc["text"])
dates = sorted(t for t in (R("parse_time")(d) for d in doc["dates"]) if t)
check("the file lists its dates out of order", doc["dates"][0] > doc["dates"][-1], doc["dates"])
check("block 7 gives every unit the earliest", all(u["occurred_at"] == dates[0] for u in units), dates[0])
check("block 9 would give the document the same", (sorted(t for t in (R("parse_time")(d) for d in doc["dates"]) if t) or [None])[0] == dates[0])

print(f"\n{sum(ok)} of {len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
