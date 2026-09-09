"""Pack a Step 0 export as the public Kaggle dataset.

    python scripts/pack_step0_public.py <export-dir> <staging-dir>

<export-dir> is the extractor's `export/` from a finished run: documents.jsonl, units.jsonl,
pieces.jsonl, receipt.json. <staging-dir> is what gets uploaded.

Everything goes out whole. The literature is public domain, the two benchmarks are MIT, and the
papers are Creative Commons Attribution, so for the first time no document's text is withheld and
no row needs rebuilding from a source file. `attribution.jsonl` carries what CC-BY asks of anyone
redistributing the papers: per paper, its authors, title, license, DOI and source URL, joined to
the export on doc_id, which is the sha256 of the PDF's bytes and so equals the manifest's own hash.

The documentation in dataset/step0/ is copied in as well, so what is published and what is in
git are the same files.
"""
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "dataset" / "step0"
MANIFEST = REPO / "data" / "raw" / "kg-rag-cc" / "manifest.json"


def pack(src: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)

    # doc_id is the sha256 of a file's bytes and the manifest records each PDF's sha256, so the
    # two join with no path parsing and no guess about which rows are papers.
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    by_sha = {row["sha256"]: row for row in manifest["papers"]}

    documents, papers, withheld = 0, {}, 0
    with (out / "documents.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for line in (src / "documents.jsonl").open(encoding="utf-8"):
            d = json.loads(line)
            if d["doc_id"] in by_sha:
                papers[d["doc_id"]] = d
            withheld += d.get("text") is None
            documents += 1
            f.write(line if line.endswith("\n") else line + "\n")
    print(f"documents: {documents}, of which {len(papers)} are CC-BY papers; {withheld} have no text")
    if withheld:
        print("  WARNING: a document with no text cannot be read downstream; expected zero")

    for name in ("units.jsonl", "pieces.jsonl", "receipt.json"):
        shutil.copy2(src / name, out / name)
        print(f"copied {name} ({(out / name).stat().st_size / 1e6:.1f} MB)")

    with (out / "attribution.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for doc_id, d in papers.items():
            row = by_sha[doc_id]
            f.write(json.dumps({"doc_id": doc_id, "source_uri": d["source_uri"], "title": row["title"],
                                "authors": row["authors"], "year": row["year"], "venue": row["venue"],
                                "doi": row["doi"], "openalex_id": row["openalex_id"], "license": row["license"],
                                "source_url": row["pdf_url"], "pdf_sha256": row["sha256"],
                                "bytes": row["bytes"]}, ensure_ascii=False) + "\n")
    print(f"attribution.jsonl: {len(papers)} papers")
    unmatched = sorted(set(by_sha) - set(papers))
    if unmatched:
        print(f"  {len(unmatched)} manifest papers are not in this export: {unmatched[:3]}")

    for doc in sorted(DOCS.iterdir()):
        if doc.is_file():
            shutil.copy2(doc, out / doc.name)
    print(f"documentation: {len(list(DOCS.iterdir()))} files from {DOCS.relative_to(REPO)}")
    print(f"\nupload with:  cd {out}  &&  kaggle datasets version -p . -m '<message>' -t -r skip")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pack(Path(sys.argv[1]), Path(sys.argv[2]))
