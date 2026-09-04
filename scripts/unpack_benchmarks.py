"""Unpack the benchmark JSON files into raw per-document files under data/raw/.

GraphRAG-Bench: data/benchmarks/graphrag-bench/novel.json holds 20 records of
{corpus_name, context}, each context one string with no newlines. Each becomes
data/raw/graphrag-bench/<corpus_name>.txt, the string encoded as UTF-8 and
nothing else: no newline added, no text touched. The LICENSE is copied beside
them because the MIT notice must accompany copies.

LongMemEval: data/benchmarks/longmemeval/longmemeval_s.json is 500 questions,
each with a haystack of about 50 sessions. The dedupe key is the session id
over non-empty slots: 25,112 slots, 1,230 empty, 19,829 distinct ids of which 623
only ever appear empty, so 19,206 sessions. By role-and-content hash they would
be 18,474; the 641 content groups spread over several ids stay separate files
because the id is the benchmark's join key from questions to sessions. Each
becomes data/raw/longmemeval/<session_id>.json holding
session_id, dates, and turns as role and content. `dates` lists every date the
benchmark assigned the session, in first-seen order, because 3,944 sessions
carry different dates in different questions. The per-turn `has_answer` flag is
question data and is dropped. The folder is gitignored (about 250 MB); the
Kaggle dataset carries it.

The manifest written beside the files is packaging: checksums and where the
bytes came from. The extractor never reads it.

Usage: python scripts/unpack_benchmarks.py [graphrag-bench] [longmemeval]
"""
import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "data" / "benchmarks"
RAW = ROOT / "data" / "raw"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def write_manifest(out, corpus_id, license_name, source_url, unpacked_from, files):
    manifest = {
        "corpus_id": corpus_id,
        "license": license_name,
        "source_url": source_url,
        "unpacked_from": {
            "file": unpacked_from.name,
            "bytes": unpacked_from.stat().st_size,
            "sha256": sha256(unpacked_from.read_bytes()),
        },
        "built": date.today().isoformat(),
        "files": files,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def unpack_graphrag():
    src = BENCH / "graphrag-bench" / "novel.json"
    out = RAW / "graphrag-bench"
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for record in json.loads(src.read_bytes()):
        data = record["context"].encode("utf-8")
        dest = out / (record["corpus_name"] + ".txt")
        dest.write_bytes(data)
        files.append({"file": dest.name, "bytes": len(data), "sha256": sha256(data)})
        print(f"  {dest.name:<20} {len(data):>9,} bytes")
    shutil.copyfile(BENCH / "graphrag-bench" / "LICENSE", out / "LICENSE")
    write_manifest(out, "graphrag-bench", "MIT",
                   "https://github.com/GraphRAG-Bench/GraphRAG-Benchmark", src, files)
    print(f"{len(files)} files + LICENSE + manifest.json -> {out.relative_to(ROOT)}")


def unpack_longmemeval():
    src = BENCH / "longmemeval" / "longmemeval_s.json"
    out = RAW / "longmemeval"
    out.mkdir(parents=True, exist_ok=True)
    sessions = {}
    for question in json.loads(src.read_bytes()):
        haystack = zip(question["haystack_session_ids"], question["haystack_dates"],
                       question["haystack_sessions"])
        for sid, when, turns in haystack:
            if not turns:
                continue
            kept = [{"role": t["role"], "content": t["content"]} for t in turns]
            record = sessions.setdefault(sid, {"session_id": sid, "dates": [], "turns": kept})
            if record["turns"] != kept:
                raise ValueError(f"session {sid} differs between questions")
            if when not in record["dates"]:
                record["dates"].append(when)
    files = []
    for sid, record in sessions.items():
        data = (json.dumps(record, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        dest = out / (sid + ".json")
        dest.write_bytes(data)
        files.append({"file": dest.name, "bytes": len(data), "sha256": sha256(data)})
    shutil.copyfile(BENCH / "longmemeval" / "LICENSE", out / "LICENSE")
    write_manifest(out, "longmemeval", "MIT",
                   "https://github.com/xiaowu0162/LongMemEval", src, files)
    multi = sum(1 for r in sessions.values() if len(r["dates"]) > 1)
    print(f"{len(files)} sessions ({multi} with more than one date) + LICENSE + manifest.json"
          f" -> {out.relative_to(ROOT)}")


UNPACKERS = {"graphrag-bench": unpack_graphrag, "longmemeval": unpack_longmemeval}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(UNPACKERS):
        UNPACKERS[name]()
