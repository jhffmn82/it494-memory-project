"""Unpack the benchmark JSON files into raw per-document files under data/raw/.

GraphRAG-Bench: data/benchmarks/graphrag-bench/novel.json holds 20 records of
{corpus_name, context}, each context one string with no newlines. Each becomes
data/raw/graphrag-bench/<corpus_name>.txt, the string encoded as UTF-8 and
nothing else: no newline added, no text touched. The LICENSE is copied beside
them because the MIT notice must accompany copies.

The manifest written beside the files is packaging: checksums and where the
bytes came from. The extractor never reads it.

Usage: python scripts/unpack_benchmarks.py graphrag-bench
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


UNPACKERS = {"graphrag-bench": unpack_graphrag}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(UNPACKERS):
        UNPACKERS[name]()
