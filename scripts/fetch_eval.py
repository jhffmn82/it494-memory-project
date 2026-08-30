"""Fetch the benchmark datasets into data/eval/, which is gitignored.

Run from the repo root: python scripts/fetch_eval.py

LitBank        entity/coreference/event/quotation gold over 100 Gutenberg works
LongMemEval    500 questions over long chat histories, in three variants:
               the original S file (what Zep's published numbers were measured
               on), the cleaned S file (the current instrument), and the oracle
               file (evidence sessions only, for development)
NarrativeQA    question/answer pairs over full books; we keep only the two CSVs
               because the 12 overlapping story texts are already in data/raw
"""

import subprocess
import sys
import urllib.request
from pathlib import Path

EVAL = Path(__file__).resolve().parent.parent / "data" / "eval"

LME = "https://huggingface.co/datasets/xiaowu0162/longmemeval/resolve/main"
LMEC = "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main"
NQA = "https://raw.githubusercontent.com/google-deepmind/narrativeqa/master"

FILES = [
    (f"{LME}/longmemeval_s", "longmemeval/longmemeval_s.json"),
    (f"{LMEC}/longmemeval_s_cleaned.json", "longmemeval/longmemeval_s_cleaned.json"),
    (f"{LME}/longmemeval_oracle", "longmemeval/longmemeval_oracle.json"),
    (f"{NQA}/documents.csv", "narrativeqa/documents.csv"),
    (f"{NQA}/qaps.csv", "narrativeqa/qas.csv"),
]


def main() -> None:
    litbank = EVAL / "litbank"
    if not litbank.exists():
        subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/dbamman/litbank", str(litbank)],
            check=True,
        )
    for url, rel in FILES:
        dest = EVAL / rel
        if dest.exists() and dest.stat().st_size > 0:
            print(f"have {rel}")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"fetching {rel} ...")
        urllib.request.urlretrieve(url, dest)
    print("done")


if __name__ == "__main__":
    sys.exit(main())
