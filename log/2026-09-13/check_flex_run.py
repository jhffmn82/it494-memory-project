"""The Flex run, checked in one pass: what it cost and on which tier, what failed, whether every
package is whole with its quotes verbatim, and whether the answers the benchmark asks for are
stored. Run with the run's packages folder and the 1.7 export folder."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

pk, export = Path(sys.argv[1]), Path(sys.argv[2])
ANSWERS = {                                   # session title: words the stored facts should carry
    "answer_6a3b5c13_3": ["Thrive", "150"], "answer_6a3b5c13_1": ["Walmart", "120"],
    "answer_6a3b5c13_2": ["Trader Joe", "80"], "answer_6a3b5c13_4": ["Publix", "60"],
    "answer_ultrachat_448704": ["Roscioli"], "answer_ultrachat_113156": ["38"],
    "answer_ultrachat_13075": ["2-3 eggs"], "answer_a25d4a91_1": ["5K"], "answer_a25d4a91_2": ["25:50"],
    "answer_a17423e7_1": ["Maundy Thursday"],
    "answer_280352e9": ["Business Administration"], "answer_40a90d51": ["45 minutes"],
    "answer_edb03329": ["Premiere Pro"], "answer_555dfb94": ["Sony"],
    "answer_afa9873b_1": ["Zara"], "answer_afa9873b_2": ["blazer"], "answer_afa9873b_3": ["Zara"],
    "answer_d00ba6d0_1": ["Museum of Modern Art"], "answer_d00ba6d0_2": ["Ancient Civilizations"],
    "answer_3f9693b7_1": ["three different"], "answer_3f9693b7_2": ["four different"],
    "answer_sharegpt_5Lzox6N_0": ["Admon"],
}

calls = [json.loads(l) for l in open(pk / "calls.jsonl", encoding="utf-8") if l.strip()]
chat = [c for c in calls if "/longmemeval/" in (c.get("doc") or "")]
sessions = {c["doc"] for c in chat}
print(f"calls {len(calls)}, ${sum(c['cost'] for c in calls):.2f}; served on {dict(Counter(c.get('tier') for c in calls))}")
if sessions:
    per = sum(c["cost"] for c in chat) / len(sessions)
    print(f"chats: {len(sessions)} sessions, ${per:.4f} a session, about ${per * 19206:,.0f} for all 19,206")
    stage = defaultdict(float)
    for c in chat:
        stage[(c["stage"], c["model"])] += c["cost"]
    print("  chat cost by stage:", {f"{s} on {m}": round(v, 3) for (s, m), v in sorted(stage.items(), key=lambda kv: -kv[1])})
for name in ("retries.jsonl", "rejections.jsonl"):
    path = pk / name
    print(f"{name}: {sum(1 for l in open(path, encoding='utf-8') if l.strip()) if path.exists() else 0}")
log = pk / "ingest.log"
print("ERROR lines in ingest.log:", sum(1 for l in open(log, encoding="utf-8") if " ERROR " in l) if log.exists() else "no log")

texts = {}
wanted = set()
packs = []
for p in sorted(pk.rglob("*.jsonl")):
    if p.parent != pk:
        rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        packs.append((p, rows))
        wanted.add(rows[0]["doc_id"])
for line in open(export / "documents.jsonl", encoding="utf-8"):
    i = line.find('"doc_id": "')
    if line[i + 11:i + 75] in wanted:
        d = json.loads(line)
        texts[d["doc_id"]] = d["text"]
complete = bad = 0
by_title = {}
for p, rows in packs:
    complete += rows[-1].get("record") == "completion"
    text = texts.get(rows[0]["doc_id"], "")
    facts = [r for r in rows if r["record"] == "fact"]
    bad += sum(1 for f in facts if text[f["quote_start"]:f["quote_end"]] != f["quote"])
    by_title[rows[0].get("title")] = facts
print(f"packages {len(packs)}, complete {complete}; quotes not verbatim at their offsets: {bad}")

print("answers:")
for title, needles in ANSWERS.items():
    facts = by_title.get(title)
    if facts is None:
        print(f"  {title}: NO PACKAGE")
        continue
    hits = [f for f in facts if all(n.lower() in (f["quote"] + " " + str(f["object"])).lower() for n in needles)]
    shown = f"{hits[0]['predicate']} | {hits[0]['object']} | {hits[0]['author']} | {hits[0]['occurred_at']}" if hits else "-"
    print(f"  {title} {needles}: {len(hits)} fact(s)  {shown}")
