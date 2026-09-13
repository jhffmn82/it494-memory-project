"""Offline check of extractor 1.8's new parts, no model calls: blocks 0 to 7 run with Kaggle's
paths pointed at the local raw folder; then the chat path over every unpacked file, the date
forms, and the work dating with the web lookup stubbed."""
import json
import re
import sys
import types
from pathlib import Path

S = Path(__file__).resolve().parent
REPO = Path(r"C:\Users\jhffm\it494-memory-project")
RAW = REPO / "data" / "raw"
CHATS = S / "chats18"

requests = types.ModuleType("requests")
requests.Timeout = requests.ConnectionError = requests.RequestException = type("NetError", (Exception,), {})
requests.post = None
secrets = types.ModuleType("kaggle_secrets")
secrets.UserSecretsClient = type("Client", (), {"get_secret": lambda self, name: "sk-offline"})
sys.modules["requests"], sys.modules["kaggle_secrets"] = requests, secrets

src = (S / "extractor-1.8.py").read_text(encoding="utf-8")
for old, new in (('LME_CANDIDATES = (Path("/kaggle/input/it494-narrative-corpora-raw/longmemeval"),', f'LME_CANDIDATES = (Path(r"{RAW / "longmemeval"}"),'),
                 ('CHATS = Path("/kaggle/temp/chats")', f'CHATS = Path(r"{CHATS}")'),
                 ('RAW = mount("it494-narrative-corpora-raw")', f'RAW = Path(r"{RAW}")')):
    assert old in src, old
    src = src.replace(old, new)
parts = re.split(r"^# %%( \[markdown\])?\n", src, flags=re.M)
cells = [body for marker, body in zip(parts[1::2], parts[2::2]) if not marker]
ns = {"__name__": "__main__"}
for i, body in enumerate(cells[:8]):
    exec(compile(body, f"<block {i}>", "exec"), ns)

print("\n== the chat path over every unpacked file")
counts = {"files": 0, "empty sessions": 0, "chats": 0, "turns skipped": 0, "undated pieces": 0,
          "piece time differs from the file": 0, "unit per turn broken": 0, "tiling broken": 0,
          "label lacks the time": 0, "earliest unit differs": 0}
for path in sorted(CHATS.glob("longmemeval/*/*.json")):
    counts["files"] += 1
    d = ns["to_text"](path)
    pieces, flags = ns["chat_pieces"](d)
    if not pieces:
        counts["empty sessions"] += 1
        continue
    counts["chats"] += 1
    counts["turns skipped"] += d["skipped_turns"]
    units = ns["units_from_runs"](pieces, ns["chat_runs"](pieces, d["text"]), d["text"])
    stamp = json.loads(path.read_text(encoding="utf-8"))["turns"][0]["timestamp"]
    want = ns["parse_time"](stamp)
    counts["undated pieces"] += sum(p["occurred_at"] is None for p in pieces)
    counts["piece time differs from the file"] += sum(p["occurred_at"] != want for p in pieces)
    counts["unit per turn broken"] += len(units) != len(pieces) or any(u["occurred_at"] != p["occurred_at"] for u, p in zip(units, pieces))
    counts["tiling broken"] += not (pieces[0]["start"] == 0 and pieces[-1]["end"] == len(d["text"])
                                    and all(a["end"] == b["start"] for a, b in zip(pieces, pieces[1:])))
    counts["label lacks the time"] += any(not u["label"].endswith(stamp) for u in units)
    earliest = min((u["occurred_at"] for u in units), key=ns["date_key"])
    counts["earliest unit differs"] += earliest != want
for k, v in counts.items():
    print(f"   {k}: {v:,}")
assert counts["chats"] == 23882 and counts["empty sessions"] == 1230 and counts["undated pieces"] == 0
assert not any(counts[k] for k in ("piece time differs from the file", "unit per turn broken", "tiling broken", "label lacks the time", "earliest unit differs"))

print("\n== answer sessions that 1.7 left undated")
questions = json.loads((RAW / "longmemeval" / "longmemeval_s.json").read_text(encoding="utf-8"))
dates_of = {}
for q in questions:
    for sid, stamp in zip(q["haystack_session_ids"], q["haystack_dates"]):
        dates_of.setdefault(sid, set()).add(stamp)
answer_multi = {(q["question_id"], sid) for q in questions for sid in q["answer_session_ids"] if len(dates_of.get(sid, ())) > 1}
dated = 0
for qid, sid in sorted(answer_multi):
    path = CHATS / "longmemeval" / qid / f"{sid}.json"
    d = ns["to_text"](path)
    pieces, flags = ns["chat_pieces"](d)
    dated += bool(pieces) and all(p["occurred_at"] for p in pieces)
print(f"   {len(answer_multi)} answer placements on a session with several dates; dated now: {dated}")

print("\n== date forms")
date_ok, date_key, DATE_FORM = ns["date_ok"], ns["date_key"], ns["DATE_FORM"]
cases = [("THE BACCHAE, first produced about 405 B.C.", "-0404~", "-0404~"),
         ("Published 1900 by George M. Hill", "1900", "1900"),
         ("London, June 1891", "1891-06", "1891-06"),
         ("London, 1891", "1891-06", "1891"),
         ("no year on this line", "1900", None),
         ("sung between 800 and 701 BC", "-0799~/-0700~", "-0799~/-0700~"),
         ("anything", "circa 405", None)]
for line, value, want in cases:
    got = date_ok(line, value)
    print(f"   {'ok ' if got == want else 'BAD'} date_ok({value!r}) on {line!r} -> {got!r}")
    assert got == want
order = sorted(["1900", "-0404~", "2023-05-20T02:38:00", "-0799~/-0700~", "0100", "1891-06"], key=date_key)
print("   sorted:", order)
assert order == ["-0799~/-0700~", "-0404~", "0100", "1891-06", "1900", "2023-05-20T02:38:00"]

print("\n== work dating, the web lookup stubbed")
asked = []


def fake_lookup(title, author):
    asked.append((title, author))
    return "-0799~/-0700~", "https://example.org/source"


ns["lookup_date"] = fake_lookup
piece = ns["piece"]
pieces = [piece(0, 100, "front matter", "front_matter"), piece(100, 500, "THE BACCHAE", "body"),
          piece(500, 900, "THE ILIAD", "body"), piece(900, 1300, "BOOK II", "body")]
stats = {"works": [{"start": 100, "title": "The Bacchae", "author": None, "date": "-0404~"},
                   {"start": 500, "title": "The Iliad", "author": "Homer", "date": None}]}
flags = []
ns["date_works"]({}, pieces, {"author": {"name": "Various"}}, stats, flags)
print("   piece dates:", [p["occurred_at"] for p in pieces])
print("   flags:", flags)
print("   looked up:", asked)
assert [p["occurred_at"] for p in pieces] == ["-0404~", "-0404~", "-0799~/-0700~", "-0799~/-0700~"]
assert asked == [("The Iliad", "Homer")]
runs = ns["split_by_kind"](pieces, [1, 2, 3])
print("   one run over two works is cut at the date change:", runs)
assert runs == [[1], [2, 3]]
print("\n1.8 OFFLINE CHECKS PASS")
