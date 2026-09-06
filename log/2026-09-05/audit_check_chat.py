"""Independent check of the 0.9 chat path over real LongMemEval sessions: tiling, unit counts,
piece kinds, dates, and what block 9 would export."""
import hashlib, json, re, sys, glob, random
from pathlib import Path
from datetime import datetime

SRC = Path(r"C:\Users\jhffm\AppData\Local\Temp\claude\C--Users-jhffm-claude-archive\f37b45c2-24a7-4251-baf3-7d3787ce8928\scratchpad\audit\extractor_0_9.py")
text = SRC.read_text(encoding="utf-8")
cells = {}
for chunk in text.split("# %%"):
    m = re.search(r"Block (\d)", chunk)
    if m:
        body = chunk.split("\n", 1)[1] if chunk.lstrip().startswith("(cell") else chunk
        cells[int(m.group(1))] = body

g = {"__name__": "chk", "hashlib": hashlib, "json": json, "re": re, "Path": Path, "datetime": datetime}
# block 4 without its demo loop
exec(cells[4].split("\nfor path in [")[0], g)
# block 6 up to (not including) split(), which needs the model
b6 = cells[6].split("def split(doc):")[0]
exec(b6, g)
# block 7 without the model-calling functions' bodies being invoked
exec(cells[7], g)


def to_text(path):
    data = path.read_bytes()
    obj = json.loads(data)
    turns = obj["turns"]
    header = [f"session_id: {obj['session_id']}"] + [f"date: {d}" for d in obj.get("dates", [])]
    t = "\n".join(header) + "\n\n"
    spans = []
    for turn in turns:
        s = len(t)
        t += f"{turn['role']}: {turn['content']}\n\n"
        spans.append((s, len(t)))
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "kind": "chat",
            "text": t, "turns": spans, "dates": list(obj.get("dates", []))}


files = [f for f in glob.glob(r"C:\Users\jhffm\it494-memory-project\data\raw\longmemeval\*.json")
         if not f.endswith("manifest.json")]
random.seed(11)
sample = random.sample(files, 3000)

tile_bad = gap = overlap = 0
units_total = turns_total = 0
lone_turn_units = 0
multi_date = 0
undated = 0
words_hist = []
kinds = {}
for f in sample:
    doc = to_text(Path(f))
    pieces, flags = g["chat_pieces"](doc)
    runs = g["chat_runs"](pieces)
    units = g["units_from_runs"](pieces, runs, doc["text"])
    # tiling of pieces
    if pieces[0]["start"] != 0:
        tile_bad += 1
    for a, b in zip(pieces, pieces[1:]):
        if a["end"] != b["start"]:
            gap += 1
    if pieces[-1]["end"] != len(doc["text"]):
        tile_bad += 1
    for p in pieces:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    units_total += len(units)
    turns_total += len(doc["turns"])
    lone_turn_units += sum(1 for u in units if u["pieces"] == 1)
    multi_date += len(doc["dates"]) > 1
    undated += not any(p["occurred_at"] for p in pieces)
    words_hist += [u["words"] for u in units]

n = len(sample)
scale = 19206 / n
print(f"sample {n} sessions")
print(f"  piece tiling: bad ends {tile_bad}  gaps {gap}")
print(f"  piece kinds: {kinds}")
print(f"  turns {turns_total:,}  units {units_total:,}  units/session {units_total/n:.1f}")
print(f"  units that are ONE piece: {lone_turn_units:,} of {units_total:,} ({lone_turn_units/units_total:.0%})")
print(f"  sessions with >1 date {multi_date}  sessions with no date {undated}")
words_hist.sort()
import statistics
print(f"  unit words: median {statistics.median(words_hist):.0f}  mean {statistics.mean(words_hist):.0f}"
      f"  p90 {words_hist[int(len(words_hist)*0.9)]}  max {max(words_hist)}")
print(f"  under SHORT_WORDS(100): {sum(1 for w in words_hist if w < 100):,} ({sum(1 for w in words_hist if w<100)/len(words_hist):.0%})")
print(f"CORPUS ESTIMATE: units {units_total*scale:,.0f}   derive calls at 3/unit {units_total*scale*3:,.0f}")
print(f"  short units exported: {sum(1 for w in words_hist if w<100)*scale:,.0f}")
