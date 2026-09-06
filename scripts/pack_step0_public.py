"""Pack a Step 0 export as the public Kaggle dataset.

    python scripts/pack_step0_public.py <export-dir> <staging-dir>

<export-dir> is the extractor's `export/` from a finished run: documents.jsonl, units.jsonl,
pieces.jsonl, receipt.json. <staging-dir> is what gets uploaded.

The literature and the two benchmarks are public domain or MIT and go out whole. The reference
papers carry their publishers' licenses and mostly may not be redistributed, so their text is
withheld: the document row, its units and its pieces stay, the text is null, and papers.jsonl
gives the source URL and the PDF's sha256 so anyone can fetch the paper and rebuild the text
with the same public notebook.

The documentation in dataset/step0/ is copied in as well, so what is published and what is in
git are the same files.
"""
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "dataset" / "step0"
PAPERS = "it494-reference-papers/"
WITHHELD = "text withheld: license"


def pack(src: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)

    kept = 0
    paper_files = {}
    with (out / "documents.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for line in (src / "documents.jsonl").open(encoding="utf-8"):
            d = json.loads(line)
            if d["source_uri"].startswith(PAPERS):
                paper_files[d["source_uri"][len(PAPERS):]] = (d["doc_id"], d.get("title"), d.get("author"))
                d["text"] = None
                d["flags"] = list(d["flags"]) + [WITHHELD]
            else:
                kept += 1
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"documents: {kept} with text, {len(paper_files)} withheld")

    for name in ("units.jsonl", "pieces.jsonl", "receipt.json"):
        shutil.copy2(src / name, out / name)
        print(f"copied {name} ({(out / name).stat().st_size / 1e6:.1f} MB)")

    manifest = json.loads((REPO / "papers" / "manifest.json").read_text(encoding="utf-8"))
    rows = 0
    with (out / "papers.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for entry in manifest["files"]:
            got = paper_files.get(entry["file"])
            if not got:
                continue
            doc_id, title, author = got
            f.write(json.dumps({"doc_id": doc_id, "file": entry["file"], "pdf_sha256": entry["sha256"],
                                "bytes": entry["bytes"], "source_url": entry["source_url"],
                                "title": title, "author": author}, ensure_ascii=False) + "\n")
            rows += 1
    print(f"papers.jsonl: {rows} of {len(paper_files)} withheld documents have a source URL")
    missing = sorted(set(paper_files) - {e["file"] for e in manifest["files"]})
    if missing:
        print("  NOT in the manifest, so not rebuildable:", missing)

    for doc in sorted(DOCS.iterdir()):
        if doc.is_file():
            shutil.copy2(doc, out / doc.name)
    print(f"documentation: {len(list(DOCS.iterdir()))} files from {DOCS.relative_to(REPO)}")
    print(f"\nupload with:  cd {out}  &&  kaggle datasets version -p . -m '<message>' -t -r skip")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pack(Path(sys.argv[1]), Path(sys.argv[2]))
