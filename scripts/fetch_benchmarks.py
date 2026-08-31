"""Fetch the evaluation benchmarks into data/benchmarks/.

Re-runnable: existing non-empty files are skipped. Writes a manifest with sizes and
sha256 so a later run can prove it got the same bytes.

Two benchmarks:

  GraphRAG-Bench (ICLR 2026, MIT) -- 20 public-domain novels, 2,010 questions with
    gold answers, gold evidence, and question-type labels. Nine systems already
    published numbers on it using GPT-4o-mini, so our rows drop into their table.
    Small enough to commit; it lives in git.

  LongMemEval (ICLR 2025, MIT) -- 500 questions over synthetic multi-session chat,
    including 78 knowledge-update questions that test supersession directly. Zep
    published numbers on the _s split. The _s file is 278 MB and the _m file is
    2.7 GB, so neither is committed; this script fetches them on demand and
    .gitignore keeps them out. The oracle split (15 MB) carries the same 500
    questions with only the answer sessions, and IS committed, because it is
    enough to develop the loader against.

NarrativeQA (google-deepmind, Apache 2.0) -- the 345 questions covering 12 works
    already in data/raw/ are committed as data/benchmarks/narrativeqa/*_ours.csv;
    --all pulls the full documents.csv and qaps.csv they were filtered from.

  LongMemEval-cleaned -- the maintainers' revision of the _s split. Zep's published
    numbers used the ORIGINAL _s; run that for any comparison against them and the
    cleaned file for our own standalone numbers. --all fetches both.

Usage: python scripts/fetch_benchmarks.py [--all]
       --all also pulls longmemeval_s and longmemeval_s_cleaned (278 MB each)
       and the full NarrativeQA csvs.
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "benchmarks"

UA = {"User-Agent": "Mozilla/5.0 (IT494 research fetch; jhffmn.myalt1@gmail.com)"}

GRB = "https://raw.githubusercontent.com/GraphRAG-Bench/GraphRAG-Benchmark/main"
LME = "https://huggingface.co/datasets/xiaowu0162/longmemeval/resolve/main"
LMEC = "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main"
NQA = "https://raw.githubusercontent.com/google-deepmind/narrativeqa/master"

# (subdir, filename, url, committed?)
ITEMS = [
    ("graphrag-bench", "novel.json",            f"{GRB}/Datasets/Corpus/novel.json",              True),
    ("graphrag-bench", "novel_questions.json",  f"{GRB}/Datasets/Questions/novel_questions.json", True),
    ("graphrag-bench", "LICENSE",               f"{GRB}/LICENSE",                                 True),
    ("longmemeval",    "longmemeval_oracle.json", f"{LME}/longmemeval_oracle",                    True),
]

BIG = [
    ("longmemeval", "longmemeval_s.json", f"{LME}/longmemeval_s", 278_025_796),
    ("longmemeval", "longmemeval_s_cleaned.json", f"{LMEC}/longmemeval_s_cleaned.json", 277_383_467),
    ("narrativeqa", "documents.csv", f"{NQA}/documents.csv", 341_683),
    ("narrativeqa", "qas.csv", f"{NQA}/qaps.csv", 11_475_505),
]


def fetch(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  cached  {dest.name}")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=600) as r:
            dest.write_bytes(r.read())
        print(f"  ok      {dest.name}  ({dest.stat().st_size:,} bytes)")
        return True
    except Exception as e:
        print(f"  FAILED  {dest.name}: {e}")
        return False


def main():
    want_big = "--all" in sys.argv
    for sub, name, url, _ in ITEMS:
        fetch(url, DEST / sub / name)
    if want_big:
        for sub, name, url, _ in BIG:
            fetch(url, DEST / sub / name)
    else:
        print("\n  skipping longmemeval_s (278 MB); pass --all when you need it")

    manifest = {}
    for p in sorted(DEST.rglob("*")):
        if p.is_file() and p.name != "manifest.json":
            manifest[p.relative_to(DEST).as_posix()] = {
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\nmanifest written: {len(manifest)} files")


if __name__ == "__main__":
    main()
