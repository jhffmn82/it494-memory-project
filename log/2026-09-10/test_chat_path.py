"""Offline check of the patched chat path: run the extractor's own chat functions, lifted out
of the script by name, over sample sessions and then the whole LongMemEval folder.

    python test_chat_path.py path/to/extractor.py path/to/data/raw/longmemeval
"""
import ast
import glob
import io
import json
import re
import sys
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
SRC, RAW = sys.argv[1], sys.argv[2]
tree = ast.parse(open(SRC, encoding="utf-8").read())
WANT = {"chat_turns", "chat_text", "piece", "words", "words_of", "parse_time",
        "chat_pieces", "chat_runs", "units_from_runs"}
ns = {"json": json, "re": re, "datetime": datetime, "CAP_WORDS": 4000}
got = set()
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in WANT:
        exec(compile(ast.Module([node], []), SRC, "exec"), ns)
        got.add(node.name)
print("lifted:", ", ".join(sorted(got)), "| missing:", sorted(WANT - got) or "none")


def run(obj):
    turns = ns["chat_turns"](obj)
    text, spans = ns["chat_text"](obj, turns)
    doc = {"text": text, "turns": spans, "dates": list(obj.get("dates", [])),
           "session_id": obj.get("session_id")}
    pieces, flags = ns["chat_pieces"](doc)
    units = ns["units_from_runs"](pieces, ns["chat_runs"](pieces, text), text)
    return turns, text, pieces, units, flags


def tiles(xs, n):
    return xs[0]["start"] == 0 and xs[-1]["end"] == n and all(a["end"] == b["start"] for a, b in zip(xs, xs[1:]))


ok = True
for f in ["1dbf3319.json", "1bab001f.json", "37141183.json",
          "answer_sharegpt_2kpncbX_13.json", "sharegpt_00qHEQ6_0.json"]:
    obj = json.load(open(f"{RAW}/{f}", encoding="utf-8"))
    turns, text, pieces, units, flags = run(obj)
    nd = len(obj["dates"])
    checks = {
        "tiles": tiles(pieces, len(text)) and tiles(units, len(text)),
        "units=turns": len(units) == len(turns) == len(pieces),
        "roles": [p["author"] for p in pieces] == [t["role"] for t in turns],
        "content": all(t["content"] in text[p["start"]:p["end"]] for t, p in zip(turns, pieces)),
        "labels": all(u["label"].startswith(f"SESSION {obj['session_id']} TURN {i + 1}") for i, u in enumerate(units)),
        "time rule": all((u["occurred_at"] is not None) == (nd == 1) for u in units),
        "non-empty": all(text[u["start"]:u["end"]].strip() for u in units),
    }
    ok &= all(checks.values())
    bad = [k for k, v in checks.items() if not v]
    print(f"{f:<34} dates {nd}  turns {len(turns):>2}  units {len(units):>2}  "
          f"{'all checks pass' if not bad else 'FAILED: ' + ', '.join(bad)}  flags {flags}")
    print(f"    unit 1: {units[0]['label']!r}  occurred_at {units[0]['occurred_at']}  first role {pieces[0]['author']}")

total, flagged, dated, bad = 0, 0, 0, []
for path in glob.glob(f"{RAW}/*.json"):
    if path.endswith("manifest.json"):
        continue
    obj = json.load(open(path, encoding="utf-8"))
    turns, text, pieces, units, flags = run(obj)
    total += len(units)
    flagged += bool(flags)
    dated += units[0]["occurred_at"] is not None
    if not (tiles(units, len(text)) and len(units) == len(turns)
            and all(text[u["start"]:u["end"]].strip() for u in units)):
        bad.append(path)
print(f"\nwhole folder: {total:,} units (expect 199,641)  {dated:,} sessions dated (expect 15,262)  "
      f"{flagged:,} flagged (expect 3,944)  {len(bad)} failing tiling/count/non-empty")
ok &= total == 199641 and flagged == 3944 and dated == 15262 and not bad
print("ALL CHECKS PASS" if ok else "SOME CHECK FAILED")
