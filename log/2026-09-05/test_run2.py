"""Offline tests for 0.8: chat units are single turns with the session's first date; a break that
names a sentence starting mid line cuts there; a wrong index resolves when the copy names one
line; outcome flags are advisory. Run from the repository root."""
import json
import re
import sys
from pathlib import Path

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
R = lambda k: ns[k]
ok = []


def check(name, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  ' + str(detail)) if detail else ''}")


print("== chat units are single turns; the session's first date on document, unit and turn ==")
multi = json.loads((Path("data/raw/longmemeval") / "001cefa7_2.json").read_text(encoding="utf-8"))
doc = ns["to_text"](Path("data/raw/longmemeval/001cefa7_2.json"))
pieces, flags = R("chat_pieces")(doc)
runs = R("chat_runs")(pieces)
units = R("units_from_runs")(pieces, runs, doc["text"])
turns = len(doc["turns"])
check("one unit per turn", len(units) == turns, (len(units), turns))
check("the header opens the first unit and no unit is turn-less",
      runs[0] == [0, 1] and all(any(j > 0 for j in run) for run in runs))
check("every unit holds exactly one turn", all(sum(1 for j in run if j > 0) == 1 for run in runs))
earliest = min(t for t in (R("parse_time")(d) for d in doc["dates"]) if t)
check("the session's earliest date is kept, not the first listed",
      earliest == "2023-05-20T02:38:00" and doc["dates"][0] == "2023/05/22 (Mon) 15:34", (earliest, doc["dates"]))
check("every turn carries that one date", all(q["occurred_at"] == earliest for q in pieces))
check("every unit carries it on both ends", all(u["occurred_at"] == u["occurred_until"] == earliest for u in units))
check("a reused session is flagged, and the flag is advisory",
      flags and flags[0].startswith("dates: 3 session dates") and R("advisory")(flags[0]), flags)
check("the pieces tile the session", pieces[0]["start"] == 0 and pieces[-1]["end"] == len(doc["text"])
      and all(a["end"] == b["start"] for a, b in zip(pieces, pieces[1:])))
one = ns["to_text"](Path("data/raw/longmemeval/sharegpt_yywfIrx_0.json"))
p1, f1 = R("chat_pieces")(one)
check("a single-date session carries no flag", not f1 and p1[1]["occurred_at"] == "2023-05-20T02:21:00", (f1, p1[1]["occurred_at"]))
check("kind and author are the role, one per unit", {q["kind"] for q in pieces[1:]} == {"user", "assistant"}
      and all(q["author"] == q["kind"] for q in pieces[1:]))

print("\n== the four real failures of run 347601080, whose copies drop the front of the line ==")
for f, probe, why in [
        ("data/raw/holmes/02_2097.txt", "In Worcestershire the life of a man seems a great", "opening quotation mark dropped"),
        ("data/raw/holmes/03_1661.txt", "And it did, though they hardly found upon the mud-bank what", "opening quotation mark dropped"),
        ("data/raw/holmes/06_108.txt", "And yet the next day brought us no nearer to the solution.", "indented, and rounded off with a period"),
        ("data/raw/greek/03_348.txt", "Then the goddess grey-eyed Athene came near them and", "line-number marker dropped")]:
    t = Path(f).read_text(encoding="utf-8", errors="replace")
    ad = R("addresses")(t)
    st = R("fresh_stats")(ad, "luna")
    span = R("resolve")({"index": 0, "text": probe}, t, ad, st)      # index 0 is deliberately wrong
    line_start = span is not None and t[span[0] - 1] == "\n"
    check(f"{Path(f).name}: {why}", span is not None and line_start and st["unresolved"] == 0,
          None if span is None else t[slice(*span)][:46])

print("\n== the boundary is the line, and find_text is the last resort ==")
text = Path("data/raw/holmes/02_2097.txt").read_text(encoding="utf-8", errors="replace")
probe = "In Worcestershire the life of a man seems a great"
pos = text.find(probe)
addrs = R("addresses")(text)
check("the probe is real and does not start its line", pos > 0 and text[pos - 1] != "\n")
big = ns["piece"](0, len(text), "whole", "body")
script["split"] = lambda l: {"breaks": [{"index": 3, "text": probe}]}
st = R("fresh_stats")(addrs, "luna")
parts = R("subsplit")(text, big, st, depth=2)          # depth 2 so it cuts once and stops
check("the piece is cut at the line, so the opening quotation mark stays with it",
      len(parts) == 2 and parts[1]["start"] == pos - 1 and text[parts[1]["start"]] == "“", [q["start"] for q in parts])
check("the cut is counted as recovered, not unresolved", st["recovered"] == 1 and st["unresolved"] == 0, st)
check("the part is labelled with the line's own words", parts[1]["label"].startswith("“In Worcestershire"), parts[1]["label"][:40])
check("find_text still locates a copy at its exact offset", R("find_text")(text, 0, len(text), probe) == pos)
check("four words is too few for find_text to place a break", R("find_text")(text, 0, len(text), "the life of a") is None)
check("a phrase that is not there returns nothing", R("find_text")(text, 0, len(text), "the quick brown llama jumps over") is None)

print("\n== a wrong index whose copy names exactly one line ==")
t2 = "alpha\nbravo\ncharlie\nThe unique sentence that appears once here\ndelta\n"
a2 = R("addresses")(t2)
st = R("fresh_stats")(a2, "luna")
check("an index off by more than the window still resolves",
      R("resolve")({"index": 0, "text": "The unique sentence that appears once here"}, t2, a2, st) == a2[3] and st["recovered"] == 1, st)
t3 = "repeat me here\nfiller\nrepeat me here\n"
a3 = R("addresses")(t3)
st = R("fresh_stats")(a3, "luna")
check("a copy that names two lines does not resolve",
      R("resolve")({"index": 9, "text": "repeat me here"}, t3, a3, st) is None and st["unresolved"] == 1, st)

print("\n== advisory flags ==")
for f, want in [("metadata: 1 pointer(s) matched no line", True), ("shape: one piece holds 100% of the body", True),
                ("dates: 3 session dates, 2023-05-20 kept", True), ("too long: about 666,328 tokens for one call", True),
                ("merging: join across a region boundary left alone, 2", True),
                ("merging: over cap, left alone: Chapter I", True),
                ("merging: outline too long; short pieces left alone", True),
                ("grouping: dissolved a group over the cap: A .. B", True),
                ("grouping: outline too long, one unit per piece", True),
                ("merging: 1 answer(s) not understood: sideways", False),
                ("grouping: covered 2 of 5 pieces; one unit per piece", False),
                ("count: 3 headed pieces, contents says 24", False),
                ("coverage: one piece holds 90% of the body", False),
                ("pointers: 2 matched no line", False), ("no body region", False),
                ("run error: ValueError: x", False)]:
    check(f"advisory({f[:44]!r}) is {want}", R("advisory")(f) is want)

print("\n== the unrecognised merge word is named ==")
t4, pcs4 = "A\n" + ("w " * 300) + "\nh\n" + ("w " * 300) + "\n", None
pcs4 = [ns["piece"](0, 10, "A", "body"), ns["piece"](10, 14, "h", "body"), ns["piece"](14, len(t4), "B", "body")]
script["merge"] = lambda l: {"merges": [{"index": 1, "into": "sideways"}]}
fl = []
R("merge_short")(t4, pcs4, {}, fl)
check("the flag names the word", fl and "sideways" in fl[0], fl)

print(f"\n{sum(ok)} of {len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
