"""Offline tests for the post-run patch (0.6). From the project root."""
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
        idx = sorted(lines); step = max(1, len(idx) // 4)
        return {"breaks": [{"index": idx[k], "text": lines[idx[k]][:50]} for k in range(step, len(idx), step)]}
    if prompt.startswith("Below is the outline"):
        script["last_outline"] = prompt
        return script.get("group", lambda l: {"units": [{"first": i, "last": i} for i in range(len(l))]})(lines)
    if prompt.startswith("Below are the pieces"):
        script["last_merge_prompt"] = prompt
        return script.get("merge", lambda l: {"merges": []})(lines)
    raise AssertionError(prompt[:40])


ns.update(MODEL="luna", RETRY="terra", RETRY_MAX_TOKENS=80_000, TooLong=TooLong, SpendStop=SpendStop, generate=generate, spend=lambda: 0.0)
exec(block[4][:block[4].index("for path in [")], ns); exec(block[5], ns); exec(block[6], ns); exec(block[7], ns)
R = lambda k: ns[k]
ok = []


def check(name, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  ' + str(detail)) if detail else ''}")


print("== wrapped copies ==")
t = ("It was a cold morning of the early spring, and we sat after\n"
     "breakfast on either side of a cheery fire in the old room at\n"
     "Baker Street. A thick fog rolled down between the rows of\n"
     "houses.\n")
a = R("addresses")(t)
st = R("fresh_stats")(a, "luna")
check("a sentence that runs past its first line resolves at that line",
      R("resolve")({"index": 0, "text": "It was a cold morning of the early spring, and we sat after breakfast on either side of a cheery fire"}, t, a, st) == a[0])
st = R("fresh_stats")(a, "luna")
# 2026-09-06: 0.9 matches a run of five words or more anywhere inside the line, not only as
# its prefix, so a copy that begins mid-line now names its line instead of failing. A copy
# under five words is still strict, which the next check holds.
check("a copy of five words or more names its line wherever it begins",
      R("resolve")({"index": 1, "text": "on either side of a cheery fire in the old room"}, t, a, st) is not None
      and not st["unresolved"], st.get("unresolved_samples"))
st = R("fresh_stats")(a, "luna")
check("a four-word copy still needs an exact line", R("resolve")({"index": 3, "text": "houses."}, t, a, st) == a[3] and R("resolve")({"index": 2, "text": "Baker Street. A thick"}, t, a, R("fresh_stats")(a, "luna")) is None)

print("\n== gates: coverage only against a contents list; metadata flags do not retry ==")
doc = ns["to_text"](Path("data/raw/oz/01_55.txt")); text = doc["text"]


def oz(lines, toc=24, pieces=True, bad_author=False, body_at_title=False):
    first = lambda pred, after=0: next(i for i, t in lines.items() if i >= after and pred(t))
    intro = first(lambda t: t == "Introduction", 20); end = first(lambda t: t.startswith("*** END OF THE PROJECT GUTENBERG"))
    chapters = [i for i, t in lines.items() if re.fullmatch(r"Chapter [IVXL]+", t) and i > intro]
    if body_at_title:                                   # the body starts at the title line just before Chapter I, as the real run did
        intro = chapters[0] - 1
    return {"source_class": "canonical", "toc_count": toc, "title": None, "source": None, "date": None,
            "author": {"index": 5, "text": "not on this line", "name": "Nobody"} if bad_author else None,
            "regions": [{"index": 0, "text": lines[0], "kind": "front_matter"}, {"index": intro, "text": lines[intro], "kind": "body"},
                        {"index": end, "text": lines[end][:40], "kind": "license"}],
            "pieces": [{"index": i, "text": lines[i]} for i in chapters] if pieces else []}


script["main"] = lambda lines: oz(lines, toc=None, pieces=False)
calls.clear(); pieces, reply, flags, stats = R("split")(doc)
check("one body piece, no contents list: no coverage flag, one attempt", not any(f.startswith("coverage") for f in flags) and len(calls) == 1, (flags, len(calls)))
script["main"] = lambda lines: oz(lines, toc=24, pieces=False)
calls.clear(); pieces, reply, flags, stats = R("split")(doc)
check("one body piece, contents says 24: coverage flag", any(f.startswith("coverage") for f in flags), flags)
script["main"] = lambda lines: oz(lines, bad_author=True)
calls.clear(); pieces, reply, flags, stats = R("split")(doc)
check("a failed author pointer: nulled, flagged metadata, no retry", reply["author"] is None and any(f.startswith("metadata:") for f in flags) and len(calls) == 1, (flags, len(calls)))

print("\n== merge_short, parts, labels ==")
script["main"] = lambda lines: oz(lines, body_at_title=True)
pieces, reply, flags, stats = R("split")(doc)
opening = next(q for q in pieces if q["label"] == "opening")
check("the Oz opening sliver is under 100 words", R("words")(text, opening) < 100, R("words")(text, opening))
script["merge"] = lambda lines: {"merges": [{"index": i, "into": "next"} for i, l in lines.items() if "opening" in l]}
merged = R("merge_short")(text, pieces, stats, flags)
ch1 = next(q for q in merged if q["label"] == "Chapter I")
check("opening merged into Chapter I, label kept as the heading's words", len(merged) == len(pieces) - 1 and ch1["start"] == opening["start"] and stats["merged"] == 1, (len(pieces), len(merged)))
check("the merge prompt showed the short piece's text", "text: " in script["last_merge_prompt"])
# a heading merging into the next keeps its words in the label
pcs = [ns["piece"](0, 10, "PART I.", "body"), ns["piece"](10, 500, "Chapter I", "body"), ns["piece"](500, 900, "Chapter II", "body")]
tt = "PART I.\n" + ("w " * 245) + "\n" + ("w " * 200)
script["merge"] = lambda lines: {"merges": [{"index": 0, "into": "next"}]}
m2 = R("merge_short")(tt, pcs, {}, [])
check("a heading joins the next piece with both labels", m2[0]["label"] == "PART I. / Chapter I" and m2[0]["start"] == 0, m2[0]["label"])
script["merge"] = lambda lines: {"merges": [{"index": 2, "into": "previous"}]}
pcs = [ns["piece"](0, 400, "A", "body"), ns["piece"](400, 800, "B", "body"), ns["piece"](800, 812, "sliver", "body")]
tt2 = ("w " * 200) + ("w " * 200) + "the end.\n"
m3 = R("merge_short")(tt2, pcs, {}, [])
check("a sliver joins the previous piece", len(m3) == 2 and m3[-1]["end"] == 812 and m3[-1]["label"] == "B")
# sub-split parts are marked in the outline
doc2 = ns["to_text"](Path("data/raw/graphrag-bench/Novel-30752.txt")); t2 = doc2["text"]
script["main"] = lambda lines: {"source_class": "canonical", "regions": [{"index": 0, "text": " ".join(lines[0].split()[:8]), "kind": "body"}], "pieces": []}
pieces, reply, flags, stats = R("split")(doc2)
pieces = [q for p in pieces for q in R("subsplit")(t2, p, stats)]
check("sub-split parts carry their origin", all(q.get("part") for q in pieces) and len(pieces) > 1, len(pieces))
R("group")(t2, pieces, stats, flags)
check("the outline marks parts", "(part of" in script["last_outline"])
# a rule line takes the next line's words as label
tr = "Title\n\nprose one\n\n----------\nThe next scene begins here\nmore prose\n"
ar = R("addresses")(tr); st = R("fresh_stats")(ar, "luna")
pcs = R("pieces_from_reply")(tr, {"regions": [{"index": 0, "text": "Title", "kind": "body"}], "pieces": [{"index": 2, "text": "----------"}]}, ar, st)
check("a rule of dashes is labelled by the next line", any(q["label"] == "The next scene begins here" for q in pcs), [q["label"] for q in pcs])
print("\n== third pass: merges as edges, kinds, cap, synonyms; ranking; advisory flags; labels ==")


def pcs_from(spec):
    """[(label, words, kind)] -> a text and the pieces tiling it."""
    text, pieces, pos = "", [], 0
    for label, n, kind in spec:
        seg = label + "\n" + ("w " * max(0, n - len(label.split()))) + "\n"
        pieces.append(ns["piece"](pos, pos + len(seg), label, kind))
        text += seg
        pos += len(seg)
    return text, pieces


t, pcs = pcs_from([("A", 200, "body"), ("CHAPTER I", 2, "body"), ("The Cyclone", 2, "body"), ("B", 200, "body"), ("C", 200, "body")])
script["merge"] = lambda l: {"merges": [{"index": 1, "into": "next"}, {"index": 2, "into": "previous"}]}
m = R("merge_short")(t, pcs, {}, [])
check("next then previous joins the pair only; B untouched",
      [q["label"] for q in m] == ["A", "CHAPTER I / The Cyclone", "B", "C"] and m[1]["end"] == pcs[2]["end"], [q["label"] for q in m])
t, pcs = pcs_from([("A", 200, "body"), ("B", 3, "body"), ("C", 3, "body"), ("D", 200, "body")])
script["merge"] = lambda l: {"merges": [{"index": 1, "into": "next"}, {"index": 2, "into": "previous"}]}
m = R("merge_short")(t, pcs, {}, [])
check("a mutual pair stands alone; D untouched", len(m) == 3 and m[1]["end"] == pcs[2]["end"] and m[2]["label"] == "D", [q["label"] for q in m])
t, pcs = pcs_from([("front", 5, "front_matter"), ("Chapter I", 300, "body")])
script["merge"] = lambda l: {"merges": [{"index": 0, "into": "next"}]}
fl = []
m = R("merge_short")(t, pcs, {}, fl)
check("a join across a region boundary is left alone and flagged", len(m) == 2 and any("region boundary" in f for f in fl), fl)
t, pcs = pcs_from([("Big", 3990, "body"), ("tail", 30, "body")])
script["merge"] = lambda l: {"merges": [{"index": 1, "into": "before"}]}
fl = []
m = R("merge_short")(t, pcs, {}, fl)
# 2026-09-06: the synonym table was deleted; the prompt asks for "previous", "next" or
# "alone", and anything else is counted and named. "before" is now a counted miss, so the
# join never happens and the cap check has nothing to refuse.
check("a synonym is not applied; it is counted and named", len(m) == 2 and any("merging answer" in f and "before" in f for f in fl), fl)
t, pcs = pcs_from([("A", 200, "body"), ("h", 2, "body"), ("B", 200, "body")])
script["merge"] = lambda l: {"merges": [{"index": 1, "into": "After"}, {"index": 0, "into": "next"}, {"index": 1, "into": "sideways"}]}
fl, stt = [], {}
m = R("merge_short")(t, pcs, stt, fl)
check("only the three words are applied; the rest are counted and named",
      stt["merged"] == 0 and any("3 not understood" in f and "After" in f and "sideways" in f for f in fl), (stt, fl))
script["merge"] = lambda l: {"merges": []}
fl, stt = [], {}
m = R("merge_short")(t, pcs, stt, fl)
check("an empty answer means every short piece stands alone: no flag", m == pcs and not fl and stt["merged"] == 0, fl)

t2 = "CHAPTER I.\nMR. SHERLOCK HOLMES.\nIn the year 1878 I took my degree of Doctor of Medicine\n"
a2 = R("addresses")(t2)
st = R("fresh_stats")(a2, "luna")
check("a short two-line heading copied whole resolves at its first line",
      R("resolve")({"index": 0, "text": "CHAPTER I. MR. SHERLOCK HOLMES."}, t2, a2, st) == a2[0])
tg = "ΚΕΦΑΛΑΙΟΝ Α\nprose\n* * *\nThe next scene\n"
ag = R("addresses")(tg)
check("a Greek heading keeps its own words; a rule takes the next line",
      R("label_at")(tg, ag, 0) == "ΚΕΦΑΛΑΙΟΝ Α" and R("label_at")(tg, ag, 2) == "The next scene")

seq = iter([lambda l: {**oz(l, toc=99), "author": {"index": 5, "text": "nope", "name": "X"}}, lambda l: oz(l, toc=99), lambda l: oz(l, toc=99)])
script["main"] = lambda l: next(seq)(l)
calls.clear()
pieces, reply, flags, stats = R("split")(doc)
check("a tie on retryable flags keeps the attempt without the metadata flag",
      not any(f.startswith("metadata") for f in flags) and len(calls) == 3, (flags, len(calls)))
script["main"] = lambda l: oz(l, toc=None, pieces=False)
calls.clear()
pieces, reply, flags, stats = R("split")(doc)
check("no contents list, one body piece: a shape flag, no retry", any(f.startswith("shape:") for f in flags) and len(calls) == 1, (flags, len(calls)))
check("advisory() names metadata and shape", R("advisory")("shape: x") and R("advisory")("metadata: x") and not R("advisory")("count: x"))
addrs = R("addresses")(text)
st = R("fresh_stats")(addrs, "luna")
R("verify_meta")(text, {"author": {"index": 5, "text": "not on this line", "name": "N"}}, addrs, st)
check("a metadata failure leaves no unresolved sample", not st.get("unresolved_samples") and st["meta_unresolved"] == 1, st.get("unresolved_samples"))

print(f"\n{sum(ok)} of {len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
