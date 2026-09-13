"""Every number the 1.8 Step 0 docs will state, read off the export and the run's records."""
import collections
import json
import statistics
from pathlib import Path

S = Path(__file__).resolve().parent
E = S / "kout18" / "export"


def rows(name):
    with (E / name).open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


docs = {d["doc_id"]: d for d in rows("documents.jsonl")}
units, pieces = collections.defaultdict(list), collections.defaultdict(list)
for u in rows("units.jsonl"):
    units[u["doc_id"]].append(u)
for p in rows("pieces.jsonl"):
    pieces[p["doc_id"]].append(p)
receipt = json.loads((E / "receipt.json").read_text(encoding="utf-8"))


def corpus(d):
    return d["source_uri"].split("/")[1]


print("== per corpus: documents, units, pieces, characters")
for c in ("longmemeval", "greek", "oz", "kg-rag-cc", "graphrag-bench", "holmes"):
    ds = [d for d in docs.values() if corpus(d) == c]
    print(f"  {c:<15} {len(ds):>6,} {sum(len(units[d['doc_id']]) for d in ds):>8,} {sum(len(pieces[d['doc_id']]) for d in ds):>8,} {sum(len(d['text']) for d in ds):>13,}")
print(f"  total           {len(docs):>6,} {sum(map(len, units.values())):>8,} {sum(map(len, pieces.values())):>8,} {sum(len(d['text']) for d in docs.values()):>13,}")

kinds, kchars = collections.Counter(), collections.Counter()
for ps in pieces.values():
    for p in ps:
        kinds[p["kind"]] += 1
        kchars[p["kind"]] += p["end"] - p["start"]
read = [d for d in docs.values() if corpus(d) != "longmemeval"]
read_chars = sum(len(d["text"]) for d in read)
print("\n== piece kinds:", dict(kinds.most_common()), f"| body share {kchars['body'] / read_chars:.1%} of {read_chars:,} read chars")

print("\n== flags on read documents, the date-source notes set aside")
real = collections.Counter()
flagged_real = 0
for d in read:
    other = [f for f in d["flags"] if not f.startswith("date:")]
    flagged_real += bool(other)
    for f in other:
        real[f.split(":")[0]] += 1
print(f"  {flagged_real} read documents with a flag other than a date note: {dict(real.most_common())}")
chat_flags = collections.Counter(f.split(":")[0] for d in docs.values() if corpus(d) == "longmemeval" for f in d["flags"])
print(f"  chat flags: {dict(chat_flags)} on {sum(1 for d in docs.values() if corpus(d) == 'longmemeval' and d['flags'])} chats")

print("\n== dates")
sources = collections.Counter()
for d in read:
    for f in d["flags"]:
        if f.startswith("date: ") and f.endswith("from the page"):
            sources["page"] += 1
        elif f.startswith("date: ") and " from " in f:
            sources["web"] += 1
        elif f.startswith("date: ") and ": none, " in f:
            sources["none"] += 1
print(f"  works dated: {dict(sources)} | works in all {sum(sources.values())}")
print(f"  undated units {sum(1 for us in units.values() for u in us if not u['occurred_at'])} | undated documents {sum(1 for d in docs.values() if not d['occurred_at'])}")
print(f"  read documents with more than one date: {sum(1 for d in read if len({u['occurred_at'] for u in units[d['doc_id']]}) > 1)}")
bc = sum(1 for d in read if (d["occurred_at"] or "").startswith("-"))
print(f"  read documents dated BC: {bc} | approximate: {sum(1 for d in read if '~' in (d['occurred_at'] or ''))} | ranges: {sum(1 for d in read if '/' in (d['occurred_at'] or ''))}")
chats = [d for d in docs.values() if corpus(d) == "longmemeval"]
print(f"  chats {len(chats):,} in {len({d['source_uri'].split('/')[2] for d in chats})} histories; chat dates from {min(d['occurred_at'] for d in chats)} to {max(d['occurred_at'] for d in chats)}")

print("\n== units over and under the cap")
for side, sel in (("read", read), ("chat", chats)):
    over = under = 0
    for d in sel:
        for u in units[d["doc_id"]]:
            w = len(d["text"][u["start"]:u["end"]].split())
            over += w > 4000
            under += w < 100
    print(f"  {side}: {over} over 4,000 words, {under:,} under 100")

print("\n== body share by document")
shares = sorted((sum(p["end"] - p["start"] for p in pieces[d["doc_id"]] if p["kind"] == "body") / max(1, len(d["text"])), d) for d in read)
low = [(s, d) for s, d in shares if s < 0.5]
print(f"  median {statistics.median(s for s, _ in shares):.0%}; below half {len(low)}: {dict(collections.Counter(corpus(d) for _, d in low))}")
for s, d in low:
    if corpus(d) != "kg-rag-cc":
        print(f"     {s:.0%} {d['title']}")

print("\n== receipt")
print({k: receipt[k] for k in ("documents", "units", "pieces", "unknown_author", "unknown_date", "empty_sessions", "empty_turns",
                               "mismatch", "recovered", "unresolved", "duplicate", "meta_unresolved", "cost")})
print("  duplicate files:", len(receipt["duplicate_files"]))

recs = {}
for line in (S / "kout18" / "splits.jsonl").open(encoding="utf-8"):
    if line.strip():
        r = json.loads(line)
        recs[r["file"]] = r
readrecs = [r for r in recs.values() if r.get("kind") != "chat"]
costs = sorted(r.get("cost", 0) for r in readrecs)
top = max(readrecs, key=lambda r: r.get("cost", 0))
print(f"\n== cost: read documents ${sum(costs):.2f}, median ${statistics.median(costs):.4f}, max ${top['cost']:.3f} ({top['file']})")
print("  escalated to terra:", sum(1 for r in readrecs if (r.get("stats") or {}).get("model") == "gpt-5.6-terra"))
print("  ingested_at:", next(iter(docs.values()))["ingested_at"])
