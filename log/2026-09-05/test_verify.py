"""Offline tests for the verification pass's fixes; runs after test_review.py. From the project root."""
import json
import re
import shutil
import sys
from pathlib import Path

SCR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("C:/Users/jhffm/AppData/Local/Temp/claude/C--Users-jhffm-claude-archive/cd11ff96-d4f9-4abd-878f-030ba8ba58dd/scratchpad/test_run2")
shutil.rmtree(SCR, ignore_errors=True)
SCR.mkdir(parents=True)

src = Path("notebooks/threadatlas-extractor.py").read_text(encoding="utf-8")
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
    calls.append(model)
    if script.get("spendstop_at") is not None and len(calls) >= script["spendstop_at"]:
        raise SpendStop("spending stop: $8.00")
    lines = {int(m.group(1)): m.group(2) for m in re.finditer(r"^\[(\d+)\] (.*)$", prompt, re.M)}
    if prompt.startswith("Below is one document"):
        return script["main"](lines)
    if prompt.startswith("Below is one piece"):
        idx = sorted(lines); step = max(1, len(idx) // 4)
        return {"breaks": [{"index": idx[k], "text": lines[idx[k]][:50]} for k in range(step, len(idx), step)]}
    if prompt.startswith("Below is the outline"):
        return {"units": [{"first": i, "last": i} for i in range(len(lines))]}
    if prompt.startswith("Below are the pieces"):
        return {"merges": []}
    raise AssertionError(prompt[:40])


ns.update(MODEL="luna", RETRY="terra", RETRY_MAX_TOKENS=80_000, TooLong=TooLong, SpendStop=SpendStop, generate=generate, spend=lambda: 0.0)

# 2026-09-06: block 3 also carries the per-document billing helpers; the stub supplies them.
ns.update(BILL={}, bill_to=lambda name: None, spent_on=lambda name: 0.0)
exec(block[4][:block[4].index("for path in [")], ns); exec(block[5], ns); exec(block[6], ns); exec(block[7], ns)
b8_defs = block[8][:block[8].index("paths = sorted(")]
b8_defs = b8_defs.replace('Path("/kaggle/working/splits.jsonl")', f'Path(r"{SCR / "splits.jsonl"}")').replace('Path("/kaggle/working/splits.log")', f'Path(r"{SCR / "splits.log"}")')
exec(b8_defs, ns)
R = lambda k: ns[k]
ok = []


def check(name, cond, detail=""):
    ok.append(bool(cond))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}{('  ' + str(detail)) if detail else ''}")


print("== exact copies of real lines that begin with [n] or end in ... ==")
text = Path("data/raw/greek/07_15081.txt").read_text(encoding="utf-8", errors="replace")
addrs = R("addresses")(text)
fn = next(i for i, (a, b) in enumerate(addrs) if text[a:b].startswith("[1] "))
st = R("fresh_stats")(addrs, "luna")
check("exact copy of a real '[1] ...' footnote line resolves", R("resolve")({"index": fn, "text": text[slice(*addrs[fn])]}, text, addrs, st) == addrs[fn], text[slice(*addrs[fn])][:50])
t2 = "Wasted...\nnext line\n"; a2 = R("addresses")(t2); st = R("fresh_stats")(a2, "luna")
check("exact copy of a short line ending in ... resolves", R("resolve")({"index": 0, "text": "Wasted..."}, t2, a2, st) == a2[0])
st = R("fresh_stats")(a2, "luna")
check("index '1.0' accepted", R("resolve")({"index": "1.0", "text": "next line"}, t2, a2, st) == a2[1])
bad = 0
for name in ["greek/07_15081.txt", "holmes/01_244.txt"]:
    t = Path("data/raw", name).read_text(encoding="utf-8", errors="replace"); ad = R("addresses")(t)
    for i, sp in enumerate(ad):
        stt = R("fresh_stats")(ad, "luna")
        if R("resolve")({"index": i, "text": t[slice(*sp)]}, t, ad, stt) != sp:
            bad += 1
check("every exact copy in two real files resolves", bad == 0, bad)

print("\n== dates ==")
# 2026-09-06: the Roman-numeral parser was deleted. The year must be on the line as digits,
# so a title page giving only MCMXXI yields no date and the document is counted unknown-date.
check("a year only in Roman numerals is not accepted", R("date_ok")("LONDON: WILLIAM HEINEMANN MCMXXI", "1921") is None)
check("the same year in digits is", R("date_ok")("LONDON: WILLIAM HEINEMANN 1921", "1921") == "1921")
check("month kept when on the line", R("date_ok")("Chicago, April, 1900.", "1900-04") == "1900-04")
check("month dropped when not on the line", R("date_ok")("Original publication: 1886", "1886-05") == "1886")
check("bad iso rejected", R("date_ok")("1886", "18860") is None and R("date_ok")("no year here", "1886") is None)

print("\n== verify_meta counts a non-dict pointer ==")
doc = ns["to_text"](Path("data/raw/oz/01_55.txt")); text = doc["text"]; addrs = R("addresses")(text)
st = R("fresh_stats")(addrs, "luna"); r = {"author": "Doyle", "title": {"index": 0, "text": text[slice(*addrs[0])], "title": "x"}}
R("verify_meta")(text, r, addrs, st)
check("string author nulled and counted as metadata, not as a retryable pointer", r["author"] is None and st["unresolved"] == 0 and st["meta_unresolved"] == 1, st)

print("\n== unknown kind keeps its boundary; int containers ==")
def oz(lines, kinds=("front_matter", "body", "license"), regions_override=None):
    first = lambda pred, after=0: next(i for i, t in lines.items() if i >= after and pred(t))
    intro = first(lambda t: t == "Introduction", 20); end = first(lambda t: t.startswith("*** END OF THE PROJECT GUTENBERG"))
    chapters = [i for i, t in lines.items() if re.fullmatch(r"Chapter [IVXL]+", t) and i > intro]
    return {"source_class": "canonical", "toc_count": 24, "title": None, "author": None, "source": None, "date": None,
            "regions": regions_override if regions_override is not None else [
                {"index": 0, "text": lines[0], "kind": kinds[0]}, {"index": intro, "text": "Introduction", "kind": kinds[1]},
                {"index": end, "text": lines[end][:40], "kind": kinds[2]}],
            "pieces": [{"index": i, "text": lines[i]} for i in chapters]}
script["main"] = lambda lines: oz(lines, kinds=("front_matter", "body", "Back Matter"))
pieces, reply, flags, stats = R("split")(doc)
check("unknown kind kept as the region's kind, flagged", pieces[-1]["kind"] == "back_matter" and any("unknown kind" in f for f in flags), (pieces[-1]["kind"], [f for f in flags if "regions" in f]))
script["main"] = lambda lines: {**oz(lines), "regions": 5, "pieces": 7}
pieces, reply, flags, stats = R("split")(doc)
check("integer regions/pieces do not crash; flagged", "no body region" in flags and pieces[0]["kind"] == "whole", flags)

print("\n== coverage gate only on a body over the cap ==")
short = "Title\n\nOne.\nTwo.\nThree.\n"; a = R("addresses")(short)
st = R("fresh_stats")(a, "luna")
pcs = R("pieces_from_reply")(short, {"regions": [{"index": 0, "text": "Title", "kind": "body"}], "pieces": [{"index": 1, "text": "One."}, {"index": 4, "text": "Three."}]}, a, st)
check("a short two-piece body is not coverage-flagged", not any(f.startswith("coverage") for f in R("gates")(pcs, {}, st, short)))

print("\n== chat tail ==")
def chat(turn_words):
    head = "session_id: x\ndate: 2023/05/20 (Sat) 02:21\n\n"; text = head; turns = []
    for k, w in enumerate(turn_words):
        seg = ("user" if k % 2 == 0 else "assistant") + ": " + ("word " * w) + "\n\n"
        turns.append((len(text), len(text) + len(seg))); text += seg
    return {"text": text, "turns": turns, "dates": ["2023/05/20 (Sat) 02:21"], "kind": "chat", "sha256": "x"}
for tw in ([3000, 3000, 2000], [2500, 2500, 3900, 3900, 2000], [5000], [100, 100]):
    d = chat(tw); cp, _ = R("chat_pieces")(d); runs = R("chat_runs")(cp, d["text"])
    # 2026-09-06: the header is its own unit; the turn units carry at least two turns unless
    # the session has fewer, or a single turn is over the cap on its own.
    check(f"turns {tw}: the header stands alone and turn units are pure",
          runs[0] == [0] and all(all(j > 0 for j in run) for run in runs[1:])
          and all(len(run) >= min(2, len(tw)) or len(run) == 1 for run in runs[1:]), runs)

print("\n== Blocks 8 and 9: old records, tries cap, chats final, duplicate bytes, unreadable file, spend stop ==")
oz_reply = lambda lines: oz(lines)
script["main"] = lambda lines: oz_reply(lines) if "Wonderful Wizard" in " ".join(list(lines.values())[:12]) else {"source_class": "published", "regions": [{"index": 0, "text": " ".join(lines[0].split()[:8]), "kind": "body"}], "pieces": []}
b8 = block[8].replace('Path("/kaggle/working/splits.jsonl")', f'Path(r"{SCR / "splits.jsonl"}")').replace('Path("/kaggle/working/splits.log")', f'Path(r"{SCR / "splits.log"}")')
b8 = re.sub(r"paths = sorted\(RAW.*?manifest\.json\"\)", 'paths = [RAW / "oz" / "01_55.txt", RAW / "oz" / "02_54.txt", RAW / "longmemeval" / "001cefa7_2.json", PAPERS / "novelqa-2024.pdf", PAPERS / "wang2024-novelqa.pdf", RAW / "oz" / "missing.txt"]', b8, flags=re.S)
assert 'paths = [RAW / "oz" / "01_55.txt"' in b8
# seed: an old-style clean record for 01_55 (no "file"), a flagged record for 02_54 with two tries already
oz1 = ns["to_text"](Path("data/raw/oz/01_55.txt")); oz2 = ns["to_text"](Path("data/raw/oz/02_54.txt"))
old = {"path": str(Path("data/raw/oz/01_55.txt")), "sha256": oz1["sha256"], "kind": "text", "reply": {}, "pieces": [{"start": 0, "end": len(oz1["text"]), "label": "whole document", "kind": "whole", "author": None, "occurred_at": None, "unit": 0}], "units": [{"position": 0, "start": 0, "end": len(oz1["text"]), "label": "whole document", "occurred_at": None, "occurred_until": None, "pieces": 1, "words": 1}], "flags": [], "stats": {}, "cost": 0.0}
fl = {**old, "path": str(Path("data/raw/oz/02_54.txt")), "sha256": oz2["sha256"], "flags": ["no body region"], "pieces": [{**old["pieces"][0], "end": len(oz2["text"])}], "units": [{**old["units"][0], "end": len(oz2["text"])}]}
(SCR / "splits.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in (old, fl, fl)) + "\n", encoding="utf-8")
calls.clear(); script["spendstop_at"] = None
exec(b8, ns)
recs = [json.loads(l) for l in (SCR / "splits.jsonl").read_text(encoding="utf-8").split("\n") if l]
new = [r["file"] for r in recs[3:]]
# 2026-09-06: 0.9 redoes every record an older loader wrote, which is what these seeded
# records are (they carry no "loader"), so both are re-asked rather than skipped. The
# older-loader rule itself is checked in test_diag.py.
# 2026-09-06: with REDO_ALL off, the clean record from an older loader is kept, and the
# flagged one is kept too because it has already been asked in two sessions.
check("the clean older-loader record and the twice-asked one are both kept",
      "raw/oz/01_55.txt" not in new and "raw/oz/02_54.txt" not in new, new)
# 2026-09-06: records land in completion order now, so the set is the check, not the list.
check("every path not already settled got a record", sorted(new) == sorted(["raw/longmemeval/001cefa7_2.json", "papers/novelqa-2024.pdf", "papers/wang2024-novelqa.pdf", "raw/oz/missing.txt"]), new)
err = next(r for r in recs if r.get("file") == "raw/oz/missing.txt")
check("unreadable file is a run-error record, kind error, loop continued", err["kind"] == "error" and err["flags"][0].startswith("run error"), err["flags"])
calls.clear()
exec(b8, ns)
recs2 = [json.loads(l) for l in (SCR / "splits.jsonl").read_text(encoding="utf-8").split("\n") if l]
redone = [r["file"] for r in recs2[len(recs):]]
check("second run: the flagged chat is final, the clean PDFs stay, only the missing file gets its second try", redone == ["raw/oz/missing.txt"], redone)
calls.clear()
exec(b8, ns)
recs2b = [json.loads(l) for l in (SCR / "splits.jsonl").read_text(encoding="utf-8").split("\n") if l]
check("third run: everything flagged has had two tries; nothing is redone", len(recs2b) == len(recs2), (len(recs2), len(recs2b)))
# spend stop mid-document writes a flagged record
(SCR / "splits.jsonl").write_text("", encoding="utf-8")
b8s = re.sub(r"paths = \[.*?\]", 'paths = [RAW / "oz" / "01_55.txt", RAW / "oz" / "02_54.txt"]', b8, flags=re.S)
calls.clear(); script["spendstop_at"] = 2
exec(b8s, ns)
recs3 = [json.loads(l) for l in (SCR / "splits.jsonl").read_text(encoding="utf-8").split("\n") if l]
# 2026-09-06: with documents in parallel, every document in flight when the stop trips is
# written flagged; the rest are untouched and wait for the next session.
check("the documents in flight when the stop trips are written flagged",
      recs3 and all(r["flags"][0].startswith("spend stop") for r in recs3), [r["flags"] for r in recs3])
script["spendstop_at"] = None
# export with a duplicate and an error record
(SCR / "splits.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in recs2) + "\n", encoding="utf-8")
b9 = block[9].replace('Path("/kaggle/working/export")', f'Path(r"{SCR / "export"}")')
exec(b9, ns)
docs = [json.loads(l) for l in (SCR / "export" / "documents.jsonl").read_text(encoding="utf-8").split("\n") if l]
units = [json.loads(l) for l in (SCR / "export" / "units.jsonl").read_text(encoding="utf-8").split("\n") if l]
receipt = json.loads((SCR / "export" / "receipt.json").read_text(encoding="utf-8"))
check("identical PDFs exported once, recorded in the receipt", len(receipt["duplicate_files"]) == 1 and len({d["doc_id"] for d in docs}) == len(docs), receipt["duplicate_files"])
check("error document exported with no units", any(d["source_uri"].endswith("missing.txt") for d in docs) and not any(u["doc_id"] == err["sha256"] for u in units))
check("receipt carries meta_unresolved", "meta_unresolved" in receipt)
print(f"\n{sum(ok)} of {len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
