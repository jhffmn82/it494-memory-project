"""Offline tests for the review batch: one check per fix, no network. Run from the project root."""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(".")
SCR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Users/jhffm/AppData/Local/Temp/claude/C--Users-jhffm-claude-archive/cd11ff96-d4f9-4abd-878f-030ba8ba58dd/scratchpad/test_run")
shutil.rmtree(SCR, ignore_errors=True)
SCR.mkdir(parents=True)

src = Path("notebooks/factledger-extractor.py").read_text(encoding="utf-8")
cells = src.split("\n# %%\n")
block = {int(m.group(1)): c for c in cells for m in [re.search(r"^# Block (\d+):", c, re.M)] if m}

ns = {}
exec("import hashlib, json, re\nfrom pathlib import Path\nfrom datetime import datetime\nfrom concurrent.futures import ThreadPoolExecutor\n"
     "RAW = Path('data/raw'); PAPERS = Path('papers')", ns)
exec(block[2].split("# One of each, to see the shape.")[0], ns)

# ---- Block 3 stand-in: constants, exceptions, a scripted generate() ----
calls, script = [], {}


class TooLong(Exception):
    pass


class SpendStop(Exception):
    pass


def generate(prompt, model="luna", effort="low"):
    calls.append((model, prompt[:30]))
    if script.get("spendstop_at") is not None and len(calls) >= script["spendstop_at"]:
        raise SpendStop("spending stop: $8.00")
    lines = {int(m.group(1)): m.group(2) for m in re.finditer(r"^\[(\d+)\] (.*)$", prompt, re.M)}
    if prompt.startswith("Below is one document"):
        return script["main"](lines)
    if prompt.startswith("Below is one piece"):
        n = script["split_calls"] = script.get("split_calls", 0) + 1
        if script.get("split_first_empty") and n == 1:
            return {"breaks": []}
        idx = sorted(lines)
        step = max(1, len(idx) // 4)
        return {"breaks": [{"index": idx[k], "text": lines[idx[k]][:50]} for k in range(step, len(idx), step)]}
    if prompt.startswith("Below is the outline"):
        return script["group"](lines)
    if prompt.startswith("Below are the pieces"):
        return script.get("merge", lambda lines: {"merges": []})(lines)
    raise AssertionError(prompt[:40])


ns.update(MODEL="luna", RETRY="terra", RETRY_MAX_TOKENS=80_000, TooLong=TooLong, SpendStop=SpendStop,
          generate=generate, spend=lambda: 0.0)
b4 = block[4][:block[4].index("for path in [")]
exec(b4, ns); exec(block[5], ns); exec(block[6], ns); exec(block[7], ns)
b8_defs = block[8][:block[8].index("paths = sorted(")]
b8_defs = b8_defs.replace('Path("/kaggle/working/splits.jsonl")', f'Path(r"{SCR / "splits.jsonl"}")').replace('Path("/kaggle/working/splits.log")', f'Path(r"{SCR / "splits.log"}")')
exec(b8_defs, ns)                                            # rel_of, path_of, iso_of, read_splits, rendered, show
R = lambda k: ns[k]
ok = []


def check(name, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  ' + str(detail)) if detail else ''}")


# ---------------- 7. resolve(): prefix, nearest, ellipsis, empty, string index, [i] prefix ----------------
print("\n== resolve ==")
text = "CHAPTER I\nCHAPTER II\nCHAPTER III\nThe quick brown fox jumps over the lazy dog and keeps going far\nCHAPTER II\n"
addrs = R("addresses")(text)
st = R("fresh_stats")(addrs, "luna")
check("CHAPTER I does not verify against CHAPTER II", R("resolve")({"index": 1, "text": "CHAPTER I"}, text, addrs, st) is None or R("resolve")({"index": 1, "text": "CHAPTER I"}, text, addrs, st) == addrs[0])
st = R("fresh_stats")(addrs, "luna")
check("nearest first: index 3 with text CHAPTER II recovers to 4 (d=1), not 1 (d=2)", R("resolve")({"index": 3, "text": "CHAPTER II"}, text, addrs, st) == addrs[4], st)
st = R("fresh_stats")(addrs, "luna")
check("eight-word cut with ellipsis matches", R("resolve")({"index": 3, "text": "The quick brown fox jumps over the lazy..."}, text, addrs, st) == addrs[3])
st = R("fresh_stats")(addrs, "luna")
check("empty text is unresolved and counted", R("resolve")({"index": 0, "text": ""}, text, addrs, st) is None and st["unresolved"] == 1)
st = R("fresh_stats")(addrs, "luna")
check("string index '2' is accepted", R("resolve")({"index": "2", "text": "CHAPTER III"}, text, addrs, st) == addrs[2])
st = R("fresh_stats")(addrs, "luna")
check("a copied '[2] ' prefix is stripped", R("resolve")({"index": 2, "text": "[2] CHAPTER III"}, text, addrs, st) == addrs[2])
st = R("fresh_stats")(addrs, "luna")
check("nine-word prefix of a long line matches", R("resolve")({"index": 3, "text": "The quick brown fox jumps over the lazy dog"}, text, addrs, st) == addrs[3])

# ---------------- 1. meta pointers verified; 5. string date; 9. unknown kind / first region; 2. coverage ----------------
print("\n== Oz with a fake author, fake date, unknown kind, and a string title ==")
doc = ns["to_text"](Path("data/raw/oz/01_55.txt")); text = doc["text"]


def oz_reply(lines, bad_meta=True, no_pieces=False, kinds=("front_matter", "body", "license"), first_at=0):
    first = lambda pred, after=0: next(i for i, t in lines.items() if i >= after and pred(t))
    intro = first(lambda t: t == "Introduction", 20)
    end = first(lambda t: t.startswith("*** END OF THE PROJECT GUTENBERG"))
    chapters = [i for i, t in lines.items() if re.fullmatch(r"Chapter [IVXL]+", t) and i > intro]
    author_i = first(lambda t: t.startswith("Author:"))
    r = {"source_class": "canonical", "toc_count": 24,
         "title": {"index": 0, "text": lines[0], "title": "The Wonderful Wizard of Oz"},
         "author": ({"index": 5, "text": "this text is on no line", "name": "Nobody Realperson"} if bad_meta
                    else {"index": author_i, "text": lines[author_i], "name": "L. Frank Baum"}),
         "date": ({"index": 3, "text": "nope", "iso": "1850"} if bad_meta else None),
         "source": None,
         "regions": [{"index": first_at, "text": lines[first_at], "kind": kinds[0]},
                     {"index": intro, "text": "Introduction", "kind": kinds[1]},
                     {"index": end, "text": lines[end][:40], "kind": kinds[2]}],
         "pieces": [] if no_pieces else [{"index": i, "text": lines[i]} for i in chapters]}
    return r


script["main"] = lambda lines: oz_reply(lines)
script["group"] = lambda lines: {"units": [{"first": i, "last": i} for i in range(len(lines))]}
calls.clear()
pieces, reply, flags, stats = R("split")(doc)
check("fake author nulled", reply["author"] is None, reply.get("author"))
check("fake date nulled", reply["date"] is None)
check("real title kept", reply["title"] is not None and reply["title"]["title"] == "The Wonderful Wizard of Oz")
check("failed document pointers counted and flagged as metadata", any(f.startswith("metadata:") for f in flags) and stats.get("meta_unresolved") == 2, flags)
check("tiles", pieces[0]["start"] == 0 and pieces[-1]["end"] == len(text) and all(a["end"] == b["start"] for a, b in zip(pieces, pieces[1:])))
check("headed 24 = toc 24, no count flag", stats["headed"] == 24 and not any(f.startswith("count") for f in flags), stats["headed"])
check("a metadata flag alone buys no retry: one call", [c[0] for c in calls] == ["luna"], [c[0] for c in calls])
script["main"] = lambda lines: {**oz_reply(lines, bad_meta=False), "toc_count": 25}    # fewer headed than the contents count is retryable
# 2026-09-06: 0.9 made the count gate one-sided, so a toc BELOW the headed count no longer
# flags (Bulfinch, 32 headed against a contents list of 24, is correct). 25 > 24 still does.
calls.clear(); R("split")(doc)
check("a count flag retries on the same model, then terra under 80k tokens", [c[0] for c in calls] == ["luna", "luna", "terra"], [c[0] for c in calls])

script["main"] = lambda lines: oz_reply(lines, bad_meta=False, no_pieces=True)
pieces, reply, flags, stats = R("split")(doc)
check("single body piece over the cap -> coverage flag", any(f.startswith("coverage") for f in flags), flags)

script["main"] = lambda lines: oz_reply(lines, bad_meta=False, kinds=("front_matter", "body", "bibliography"), first_at=4)
pieces, reply, flags, stats = R("split")(doc)
check("unknown region kind flagged", any("unknown kind" in f for f in flags), [f for f in flags if "regions" in f])
check("first region not at 0 flagged", any("first begins at line 4" in f for f in flags))
check("still tiles from byte 0", pieces[0]["start"] == 0)

script["main"] = lambda lines: {**oz_reply(lines, bad_meta=False), "date": "1900", "title": "just a string", "toc_count": "24"}
pieces, reply, flags, stats = R("split")(doc)
check("string date and string title nulled, no crash", reply["date"] is None and reply["title"] is None)
check("toc_count '24' as a string still gates (24 == 24, no count flag)", not any(f.startswith("count") for f in flags), flags)
check("best-of keeps an answer with a body over 'no body region'", not any(f == "no body region" for f in flags))
check("iso_of on a string date is None", ns["iso_of"]({"date": "1900"}) is None and ns["iso_of"]({"date": {"iso": "1900"}}) == "1900")

# ---------------- 8. subsplit retry once, flags for leftovers; 5. malformed group ----------------
print("\n== Novel-30752: subsplit with an empty first answer, malformed group ==")
doc2 = ns["to_text"](Path("data/raw/graphrag-bench/Novel-30752.txt")); t2 = doc2["text"]
script["main"] = lambda lines: {"source_class": "canonical", "regions": [{"index": 0, "text": " ".join(lines[0].split()[:8]), "kind": "body"}], "pieces": []}
script["split_first_empty"] = True; script["split_calls"] = 0
script["group"] = lambda lines: [1, 2, 3]                    # a list, not a dict
calls.clear()
pieces, reply, flags, stats = R("split")(doc2)
stats_before = stats["unresolved"]
pieces = [q for p in pieces for q in R("subsplit")(t2, p, stats)]
check("subsplit asked twice when the first answer had no break, then cut", script["split_calls"] >= 2 and len(pieces) > 1, (script["split_calls"], len(pieces)))
over = [q for q in pieces if R("words")(t2, q) > 4000]
check("no piece over the cap after recursion", not over, len(over))
runs = R("group")(t2, pieces, stats, flags)
check("list reply to group -> one unit per piece and a grouping flag", len(runs) == len(pieces) and any(f.startswith("grouping answer:") for f in flags), flags)
script["group"] = lambda lines: {"units": [{"first": "0", "last": "1"}] + [{"first": i, "last": i} for i in range(2, len(lines))]}
flags = []
runs = R("group")(t2, pieces, stats, flags)
check("string first/last coerced; coverage ok", runs[0] == [0, 1] and sum(len(r) for r in runs) == len(pieces), flags)

# ---------------- 6. chat_runs: header never alone, never a lone turn ----------------
print("\n== chat runs ==")
big = "user: " + ("word " * 5000) + "\n\n"
small = "assistant: short reply here\n\n"
chat_text = "session_id: x\ndate: 2023/05/20 (Sat) 02:21\n\n" + big + small + "user: another short one\n\n" + big
turns, pos = [], len("session_id: x\ndate: 2023/05/20 (Sat) 02:21\n\n")
for seg in (big, small, "user: another short one\n\n", big):
    turns.append((pos, pos + len(seg))); pos += len(seg)
cdoc = {"text": chat_text, "turns": turns, "dates": ["2023/05/20 (Sat) 02:21"], "kind": "chat", "sha256": "x"}
cp, cf = R("chat_pieces")(cdoc)
runs = R("chat_runs")(cp, chat_text)
units = R("units_from_runs")(cp, runs, chat_text)
check("no unit holds only the header", all(any(j > 0 for j in run) for run in runs), runs)
check("no unit is a lone turn (except a day change)", all(sum(1 for j in run if j > 0) >= 2 for run in runs[:-1]) , runs)
check("chat tiles", cp[0]["start"] == 0 and cp[-1]["end"] == len(chat_text) and all(a["end"] == b["start"] for a, b in zip(cp, cp[1:])))

# ---------------- 3. glob; 4. SpendStop; 10-12. Block 8/9 end to end on two docs ----------------
print("\n== Blocks 8 and 9 end to end, spend stop on the second document ==")
b8 = block[8].replace('Path("/kaggle/working/splits.jsonl")', f'Path(r"{SCR / "splits.jsonl"}")').replace('Path("/kaggle/working/splits.log")', f'Path(r"{SCR / "splits.log"}")')
b8 = b8.replace('paths = sorted(RAW.glob("oz/*.txt")) + sorted(RAW.glob("holmes/*.txt")) + sorted(RAW.glob("greek/*.txt")) \\\n      + sorted(RAW.glob("graphrag-bench/*.txt")) + sorted(PAPERS.glob("*.pdf")) \\\n      + sorted(p for p in RAW.glob("longmemeval/*.json") if p.name != "manifest.json")',
                'paths = [RAW / "oz" / "01_55.txt", RAW / "oz" / "02_54.txt", RAW / "longmemeval" / "sharegpt_yywfIrx_0.json"]')
assert 'paths = [RAW / "oz" / "01_55.txt"' in b8, "path substitution failed"
full_paths = eval(re.search(r"paths = (sorted\(RAW.*?manifest\.json\"\))", block[8], re.S).group(1), ns)
check("glob excludes longmemeval/manifest.json and has 19,206 chats", not any(p.name == "manifest.json" for p in full_paths) and sum(1 for p in full_paths if p.parent.name == "longmemeval") == 19206, sum(1 for p in full_paths if p.parent.name == "longmemeval"))
script["main"] = lambda lines: oz_reply(lines, bad_meta=False) if "Wonderful Wizard" in " ".join(list(lines.values())[:12]) else {"source_class": "canonical", "regions": [{"index": 0, "text": " ".join(lines[0].split()[:8]), "kind": "body"}], "pieces": []}
script["group"] = lambda lines: {"units": [{"first": i, "last": i} for i in range(len(lines))]}
script["split_first_empty"] = False
calls.clear(); script["spendstop_at"] = 4                      # doc 1: main + group = 2 calls; doc 2's first call is #3, stop at #4
exec(b8, ns)
recs = [json.loads(l) for l in (SCR / "splits.jsonl").read_text(encoding="utf-8").split("\n") if l]
# 2026-09-06: documents run in parallel, so order is completion order and the documents
# already in flight when the stop trips are each written flagged.
check("the clean document is written clean and the stopped one flagged",
      {r["file"] for r in recs} >= {"raw/oz/01_55.txt", "raw/oz/02_54.txt"}
      and any(r["flags"][:1] and r["flags"][0].startswith("spend stop") for r in recs)
      and any(not r["flags"] for r in recs), [(r["file"], r["flags"][:1]) for r in recs])
check("record carries a dataset-relative file name", all(r["file"].startswith(("raw/", "papers/")) for r in recs))
check("text/PDF units carry the document date (None here: Oz has no date line)",
      all(u["occurred_at"] is None for r in recs if r["kind"] != "chat" for u in r["units"]))
script["spendstop_at"] = None
exec(b8, ns)                                                    # resume: doc 1 skipped by name, doc 2 redone, the chat run
recs = [json.loads(l) for l in (SCR / "splits.jsonl").read_text(encoding="utf-8").split("\n") if l]
check("resume skipped the clean document by name and redid the flagged one",
      "raw/oz/01_55.txt" in [r["file"] for r in recs]
      and [r["file"] for r in recs].count("raw/oz/02_54.txt") == 2
      and not recs[-1]["flags"][:1] == ["spend stop"], [r["file"] for r in recs])
b9 = block[9].replace('Path("/kaggle/working/export")', f'Path(r"{SCR / "export"}")')
exec(b9, ns)
docs = [json.loads(l) for l in (SCR / "export" / "documents.jsonl").read_text(encoding="utf-8").split("\n") if l]
units = [json.loads(l) for l in (SCR / "export" / "units.jsonl").read_text(encoding="utf-8").split("\n") if l]
receipt = json.loads((SCR / "export" / "receipt.json").read_text(encoding="utf-8"))
check("export wrote 3 documents", len(docs) == 3, len(docs))
check("unit ids unique", len({u["unit_id"] for u in units}) == len(units))
check("source_class validated", all(d["source_class"] in {"canonical", "published", "record", "authored", "tool-output", None} for d in docs))
check("flags_by_kind keys are stable kinds", all(not re.match(r"^\d", k) for k in receipt["flags_by_kind"]), receipt["flags_by_kind"])
check("receipt cost sums every record in the file", receipt["cost"] == round(sum(r["cost"] for r in recs), 3))
print(f"\n{sum(ok)} of {len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
