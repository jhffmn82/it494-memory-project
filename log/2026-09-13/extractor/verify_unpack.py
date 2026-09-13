"""Run block 0 locally against the benchmark file and check what the plan says it must produce:
500 folders, 25,112 files, 23,882 with content; every file's turns identical to the benchmark's;
every turn's timestamp equal to its history's date for that session; nothing from the test."""
import json
import shutil
from pathlib import Path

S = Path(__file__).resolve().parent
REPO = Path(r"C:\Users\jhffm\it494-memory-project")
LOCAL = S / "lme"                                  # the raw dataset's longmemeval folder, as Kaggle will mount it
LOCAL.mkdir(exist_ok=True)
shutil.copyfile(REPO / "data" / "raw" / "longmemeval" / "manifest.json", LOCAL / "manifest.json")
if not (LOCAL / "longmemeval_s.json").exists():
    shutil.copyfile(REPO / "data" / "benchmarks" / "longmemeval" / "longmemeval_s.json", LOCAL / "longmemeval_s.json")
OUT = S / "chats"
if OUT.exists():
    shutil.rmtree(OUT)

src = (S / "block0_unpack.py").read_text(encoding="utf-8")
for old, new in (('LME_CANDIDATES = (Path("/kaggle/input/it494-narrative-corpora-raw/longmemeval"),', f'LME_CANDIDATES = (Path(r"{LOCAL}"),'),
                 ('CHATS = Path("/kaggle/working/chats")', f'CHATS = Path(r"{OUT}")')):
    assert old in src, old
    src = src.replace(old, new)
exec(compile(src, "block0", "exec"), {"__name__": "__main__"})


def iso(stamp):
    day, weekday, clock = stamp.split(" ")
    return day.replace("/", "-") + "T" + clock


questions = json.loads((LOCAL / "longmemeval_s.json").read_text(encoding="utf-8"))
folders = [p for p in (OUT / "longmemeval").iterdir() if p.is_dir()]
files = list((OUT / "longmemeval").glob("*/*.json"))
bad = {"missing": 0, "turns differ": 0, "timestamp wrong": 0, "extra keys": 0, "session id wrong": 0}
content = 0
for q in questions:
    listed = {}
    for sid, stamp, turns in zip(q["haystack_session_ids"], q["haystack_dates"], q["haystack_sessions"]):
        listed[sid] = listed.get(sid, 0) + 1
        path = OUT / "longmemeval" / q["question_id"] / (f"{sid}.json" if listed[sid] == 1 else f"{sid}.{listed[sid]}.json")
        if not path.exists():
            bad["missing"] += 1
            continue
        chat = json.loads(path.read_text(encoding="utf-8"))
        content += bool(chat["turns"])
        bad["session id wrong"] += chat["session_id"] != sid
        bad["extra keys"] += set(chat) != {"session_id", "turns"} or any(set(t) != {"role", "content", "timestamp"} for t in chat["turns"])
        bad["turns differ"] += [(t["role"], t["content"]) for t in chat["turns"]] != [(t["role"], t["content"]) for t in turns]
        bad["timestamp wrong"] += any(t["timestamp"] != iso(stamp) for t in chat["turns"])
placements = sum(len(q["haystack_session_ids"]) for q in questions)
print(f"\nfolders {len(folders)} (want 500), files {len(files):,} (want 25,112; placements {placements:,}), with content {content:,} (want 23,882)")
print("problems:", bad)
assert len(folders) == 500 and len(files) == 25112 == placements and content == 23882 and not any(bad.values())
print("UNPACK VERIFIED")
