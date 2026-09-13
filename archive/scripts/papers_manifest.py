"""Write papers/manifest.json for the private Kaggle dataset of reference PDFs.

The dataset is the 142 PDFs in papers/ and this manifest, nothing else: _unused/
and the working JSON files stay out. Per file: name, bytes, sha256, and the source
URL looked up from papers/MANIFEST.md, the fetch log written by fetch_papers.py.
Licenses are per paper and unrecorded, which is why the dataset is private.

Packaging only. The extractor never reads it.

Usage: python scripts/papers_manifest.py
"""
import hashlib
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"
OUT = PAPERS / "manifest.json"

ARXIV = re.compile(r"\b(\d{4}\.\d{4,5})(?:v\d+)?\b")


def fetch_log():
    """MANIFEST.md holds several tables in different shapes. Any row whose first cell
    is a PDF name counts; the source is a URL cell if there is one, else an arXiv id
    turned into its PDF URL, else nothing. The rest of the row is kept as the note."""
    rows = {}
    for line in (PAPERS / "MANIFEST.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if not cells[0].endswith(".pdf"):
            continue
        rest = cells[1:]
        url = next((c for c in rest if c.startswith("http")), None)
        if url is None:
            ids = [ARXIV.search(c) for c in rest]
            hit = next((m for m in ids if m), None)
            url = f"https://arxiv.org/pdf/{hit.group(1)}" if hit else None
        rows.setdefault(cells[0], {"source_url": url, "note": " | ".join(rest)})
    return rows


def main():
    log = fetch_log()
    files, unlogged = [], []
    for pdf in sorted(PAPERS.glob("*.pdf")):
        data = pdf.read_bytes()
        row = log.get(pdf.name)
        if row is None:
            unlogged.append(pdf.name)
        files.append({
            "file": pdf.name,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "source_url": row["source_url"] if row else None,
            "note": row["note"] if row else None,
        })
    manifest = {
        "corpus_id": "papers",
        "license": "per paper, unrecorded; private dataset, not redistributed",
        "built": date.today().isoformat(),
        "files": files,
    }
    OUT.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    with_url = sum(1 for f in files if f["source_url"])
    print(f"{len(files)} PDFs, {with_url} with a source URL, {len(unlogged)} not in MANIFEST.md"
          f" -> {OUT.relative_to(ROOT)}")
    for name in unlogged:
        print("  no fetch-log row:", name)


if __name__ == "__main__":
    main()
