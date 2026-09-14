"""Pack an ingestor run's packages as the public Step 1 dataset.

    python scripts/pack_step1_public.py <packages-dir> <staging-dir> [<step0-export-dir>]

<packages-dir> is the ingestor's output root: packages/<group>/<file>/<file>.jsonl, with
calls.jsonl, retries.jsonl and receipt.json beside them. <staging-dir> is what gets uploaded.
<step0-export-dir>, when given, is the Step 0 export the run read (documents.jsonl with text);
every fact's quote is then sliced from its document at its offsets and the pack stops on the
first mismatch, so the released offsets are proven against the released text.

A package is one JSON record per line under a `record` field. The dataset is the same records
regrouped one file per record type, the way Step 0 ships one file per table, with `doc_id` set
on every row from the package it came from (node, fact, cell and the rest carry only the
8-character document tag inside their ids, which is display, not a key). Nothing else is added
and nothing is rewritten. Document rows carry no text; join them to Step 0 on doc_id.

`attribution.jsonl` carries what CC-BY asks for the papers whose facts quote them, joined on
doc_id, which is the sha256 of the PDF and so equals the manifest's own hash. The documentation
in dataset/step1/ is copied in, so what is published and what is in git are the same files.
"""
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "dataset" / "step1"
MANIFEST = REPO / "data" / "raw" / "kg-rag-cc" / "manifest.json"

# One output file per record type, in the order a reader meets them.
TABLES = {"document": "documents", "unit": "units", "piece": "pieces", "node": "nodes",
          "alias": "aliases", "edge": "edges", "fact": "facts", "cell": "cells",
          "abstract": "abstracts", "adjudicated_fact": "adjudicated_facts",
          "attribute": "attributes", "contradiction": "contradictions",
          "rejection": "rejections", "ledger": "ledger", "candidate": "candidates",
          "completion": "completions"}


def read_package(path):
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_texts(export):
    texts = {}
    for line in (export / "documents.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        texts[d["doc_id"]] = d["text"]
    return texts


def pack(src, out, export):
    out.mkdir(parents=True, exist_ok=True)
    texts = load_texts(export) if export else None
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_sha = {row["sha256"]: row for row in manifest["papers"]}

    files = {kind: (out / f"{name}.jsonl").open("w", encoding="utf-8", newline="\n") for kind, name in TABLES.items()}
    counts = {name: 0 for name in TABLES}
    papers, packages, quotes_checked = {}, 0, 0
    for path in sorted(src.glob("*/*/*.jsonl")):
        rows = read_package(path)
        if not rows or rows[0]["record"] != "document" or rows[-1]["record"] != "completion":
            sys.exit(f"{path}: not a finished package (first {rows[0]['record'] if rows else 'nothing'}, last {rows[-1]['record'] if rows else 'nothing'})")
        doc_id = rows[0]["doc_id"]
        if doc_id in by_sha:
            papers[doc_id] = rows[0]
        packages += 1
        for r in rows:
            kind = r["record"]
            if kind not in files:
                sys.exit(f"{path}: unknown record kind {kind}")
            if r.get("doc_id", doc_id) != doc_id:
                sys.exit(f"{path}: a {kind} row names another document, {r['doc_id']}")
            # a document fact (title, author, date, source class, history) is built from the
            # export with no quote (1.8); every other fact's quote is proven here
            if kind == "fact" and texts is not None and r["quote"] is not None:
                sliced = texts[doc_id][r["quote_start"]:r["quote_end"]]
                if sliced != r["quote"]:
                    sys.exit(f"{path}: quote of {r['fact_id']} does not slice to its text")
                quotes_checked += 1
            row = {"doc_id": doc_id}
            row.update(r)
            del row["record"]
            files[kind].write(json.dumps(row, ensure_ascii=False) + "\n")
            counts[kind] += 1
    for f in files.values():
        f.close()
    print(f"packages: {packages}")
    for kind, name in TABLES.items():
        print(f"  {name + '.jsonl':24} {counts[kind]:7} rows")
    if texts is not None:
        print(f"quotes checked against the Step 0 text: {quotes_checked}, all slice to their quote; "
              f"{counts['fact'] - quotes_checked} document facts carry no quote")
    else:
        print("quotes not checked (no Step 0 export given)")

    for name in ("calls.jsonl", "retries.jsonl", "receipt.json"):
        shutil.copy2(src / name, out / name)
        print(f"copied {name} ({(out / name).stat().st_size / 1e6:.2f} MB)")

    with (out / "attribution.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for doc_id, d in papers.items():
            row = by_sha[doc_id]
            f.write(json.dumps({"doc_id": doc_id, "source_uri": d["source_uri"], "title": row["title"],
                                "authors": row["authors"], "year": row["year"], "venue": row["venue"],
                                "doi": row["doi"], "openalex_id": row["openalex_id"], "license": row["license"],
                                "source_url": row["pdf_url"], "pdf_sha256": row["sha256"],
                                "bytes": row["bytes"]}, ensure_ascii=False) + "\n")
    print(f"attribution.jsonl: {len(papers)} papers")

    for doc in sorted(DOCS.iterdir()):
        if doc.is_file():
            shutil.copy2(doc, out / doc.name)
    print(f"documentation: {len(list(DOCS.iterdir()))} files from {DOCS.relative_to(REPO)}")
    print(f"\nupload with:  cd {out}  &&  kaggle datasets create -p . -r skip   (first time)")
    print(f"          or:  cd {out}  &&  kaggle datasets version -p . -m '<message>' -r skip")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    pack(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]) if len(sys.argv) == 4 else None)
