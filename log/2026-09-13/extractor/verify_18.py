"""The 1.8 run's export against the dates brief's end state, before anything is published."""
import collections
import hashlib
import json
from pathlib import Path

S = Path(__file__).resolve().parent
E = S / "kout18" / "export"
LME = Path(r"C:\Users\jhffm\it494-memory-project\data\raw\longmemeval\longmemeval_s.json")


def rows(name):
    with (E / name).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def date_key(value):
    first = value.split("/")[0].rstrip("~")
    if first.startswith("-"):
        return int(first[:5]), first[5:]
    return int(first[:4]), first[4:]


docs = {d["doc_id"]: d for d in rows("documents.jsonl")}
units, pieces = collections.defaultdict(list), collections.defaultdict(list)
for u in rows("units.jsonl"):
    units[u["doc_id"]].append(u)
for p in rows("pieces.jsonl"):
    pieces[p["doc_id"]].append(p)
chats = [d for d in docs.values() if d["source_uri"].startswith("chats/")]
read = [d for d in docs.values() if not d["source_uri"].startswith("chats/")]
receipt = json.loads((E / "receipt.json").read_text(encoding="utf-8"))
print(f"documents {len(docs):,}: {len(chats):,} chats, {len(read)} read | units {sum(map(len, units.values())):,} | pieces {sum(map(len, pieces.values())):,}")
print(f"loader {dict(collections.Counter(d['loader'] for d in docs.values()))} | cost ${receipt['cost']:.2f} | empty sessions {receipt.get('empty_sessions')} | empty turns {receipt.get('empty_turns')}")

problems = collections.Counter()
print("\n== tiling, ids, kinds")
seen_ids = set()
for d in docs.values():
    text = d["text"]
    for label, rs in (("units", sorted(units[d["doc_id"]], key=lambda r: r["position"])),
                      ("pieces", sorted(pieces[d["doc_id"]], key=lambda r: r["position"]))):
        if not rs or rs[0]["start"] != 0 or rs[-1]["end"] != len(text) or any(a["end"] != b["start"] for a, b in zip(rs, rs[1:])):
            problems[f"{label} do not tile"] += 1
    seen = {}
    for u in sorted(units[d["doc_id"]], key=lambda r: r["position"]):
        body = text[u["start"]:u["end"]]
        n = seen.get(body, 0)
        seen[body] = n + 1
        problems["unit id does not recompute"] += hashlib.sha256(f"{d['doc_id']}\n{n}\n{body}".encode("utf-8")).hexdigest() != u["unit_id"]
        seen_ids.add(u["unit_id"])
    by_unit = collections.defaultdict(set)
    for p in pieces[d["doc_id"]]:
        by_unit[p["unit_id"]].add((p["kind"], p["occurred_at"]))
    for k in by_unit.values():
        kinds = {kind for kind, _ in k}
        problems["unit mixes region kinds"] += len(kinds) > 1 and not kinds <= {"user", "assistant"}
        problems["unit spans two dates"] += len({when for _, when in k}) > 1
problems["unit ids not unique"] += len(seen_ids) != sum(map(len, units.values()))

print("\n== every unit dated, every null explained, every document its earliest unit")
for d in docs.values():
    us = units[d["doc_id"]]
    nulls = [u for u in us if not u["occurred_at"]]
    if nulls and not any(f.startswith("date:") for f in d["flags"]):
        problems["undated unit with no reason in the flags"] += 1
    problems["undated units"] += len(nulls)
    times = [u["occurred_at"] for u in us if u["occurred_at"]]
    earliest = min(times, key=date_key) if times else None
    problems["document date is not its earliest unit"] += d["occurred_at"] != earliest

print("\n== chats against the benchmark")
questions = json.loads(LME.read_text(encoding="utf-8"))
want = {}
for q in questions:
    listed = {}
    for sid, stamp, turns in zip(q["haystack_session_ids"], q["haystack_dates"], q["haystack_sessions"]):
        listed[sid] = listed.get(sid, 0) + 1
        name = sid if listed[sid] == 1 else f"{sid}.{listed[sid]}"
        day, weekday, clock = stamp.split(" ")
        if turns:
            want[f"chats/longmemeval/{q['question_id']}/{name}.json"] = day.replace("/", "-") + "T" + clock + ":00"
histories = {d["source_uri"].split("/")[2] for d in chats}
print(f"   histories {len(histories)} (want 500) | chat documents {len(chats):,} (want 23,882; placements with turns {len(want):,})")
for d in chats:
    w = want.get(d["source_uri"])
    if w is None:
        problems["chat not in the benchmark"] += 1
        continue
    problems["chat turn date differs from its history"] += sum(p["occurred_at"] != w for p in pieces[d["doc_id"]])
    problems["chat title is not its session id"] += d["title"] != d["source_uri"].rsplit("/", 1)[1].split(".")[0]
missing = set(want) - {d["source_uri"] for d in chats}
problems["benchmark placement with no chat document"] += len(missing)
dates_of = collections.defaultdict(set)
for q in questions:
    for sid, stamp in zip(q["haystack_session_ids"], q["haystack_dates"]):
        dates_of[sid].add(stamp)
answer = [f"chats/longmemeval/{q['question_id']}/{sid}.json" for q in questions for sid in q["answer_session_ids"] if len(dates_of[sid]) > 1]
by_uri = {d["source_uri"]: d for d in chats}
print(f"   answer placements on a session with several dates: {len(answer)}, dated now: {sum(1 for a in answer if a in by_uri and by_uri[a]['occurred_at'])}")

print("\n== books and papers: dates and where they came from")
sources = collections.Counter()
for d in read:
    for f in d["flags"]:
        if f.startswith("date: ") and " from " in f:
            sources["the page" if f.endswith("from the page") else "a web search"] += 1
        elif f.startswith("date: ") and ": none, " in f:
            sources["none: " + f.split(": none, ", 1)[1][:50]] += 1
print("   works dated by:", dict(sources))
by_corpus = collections.defaultdict(list)
for d in read:
    by_corpus[d["source_uri"].split("/")[1]].append(d)
for corpus, ds in sorted(by_corpus.items()):
    undated = sum(1 for d in ds if not d["occurred_at"])
    print(f"   {corpus:<16} {len(ds):>3} documents, {undated} undated, dates {sorted({d['occurred_at'] for d in ds if d['occurred_at']}, key=date_key)[:8]}")
greek = sorted((d for d in by_corpus.get("greek", []) if d["occurred_at"]), key=lambda d: date_key(d["occurred_at"]))
print("   greek in date order:")
for d in greek:
    print(f"      {d['occurred_at']:<16} {str(d['title'])[:60]}")
multi = [(d, sorted({u["occurred_at"] for u in units[d["doc_id"]] if u["occurred_at"]}, key=date_key)) for d in read]
multi = [(d, ds) for d, ds in multi if len(ds) > 1]
print(f"   documents whose units carry more than one date (collections): {len(multi)}")
for d, ds in multi[:12]:
    print(f"      {str(d['title'])[:44]:<46} {len(ds)} dates, {ds[0]} .. {ds[-1]}")
bacchae = [d for d in read if "bacchae" in str(d["title"]).lower() or any("bacchae" in str(u["label"]).lower() for u in units[d["doc_id"]])]
iliad = [d for d in read if "iliad" in str(d["title"]).lower()]
print("   Bacchae:", [(str(d["title"])[:40], d["occurred_at"]) for d in bacchae][:3], "| Iliad:", [(str(d["title"])[:40], d["occurred_at"]) for d in iliad][:3])

print("\n== problems")
for k, v in problems.items():
    print(f"   {k}: {v}")
print("\nEND STATE MET" if not any(problems.values()) else "\nPROBLEMS ABOVE")
