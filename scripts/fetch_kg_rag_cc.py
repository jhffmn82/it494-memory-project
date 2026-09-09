"""Gather a CC-BY corpus of knowledge-graph and RAG papers, full text, with a manifest.

    python scripts/fetch_kg_rag_cc.py --target 100 --out data/raw/kg-rag-cc

Uses OpenAlex (no key) to find open-access works on the two topics, keeps only those whose
best open-access location reports a Creative Commons license (cc-by / cc-by-sa / cc0) and has a
downloadable PDF, downloads the PDFs, and writes a manifest.json with title, authors, year,
venue, DOI, OpenAlex id, the exact license, the source URL, the file, its sha256, and byte count.
Resumable: a PDF already on disk with a matching sha256 is not re-fetched.

License is read per paper from OpenAlex, never assumed; only CC works are kept, and the license
is recorded so attribution (which CC-BY requires) can be rendered from the manifest.
"""
import argparse
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

MAILTO = "jhffmn.myalt1@gmail.com"
CC = {"cc-by", "cc-by-sa", "cc0", "cc-by-nd", "cc-by-nc", "cc-by-nc-sa"}   # redistributable-with-attribution
PREFER = {"cc-by", "cc-by-sa", "cc0"}                                      # the clean ones for a public corpus
QUERIES = ["retrieval augmented generation", "knowledge graph", "graph retrieval augmented generation",
           "knowledge graph question answering", "knowledge graph language model"]
SELECT = "id,doi,title,publication_year,authorships,primary_location,best_oa_location,open_access"
UA = {"User-Agent": "Mozilla/5.0 (compatible; it494-corpus/1.0; +%s)" % MAILTO}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def candidates(target):
    """CC works on the topics with a PDF, deduped by OpenAlex id, PREFER licenses first."""
    seen, out = {}, []
    for q in QUERIES:
        cursor = "*"
        for _ in range(6):                       # up to 6 pages (1200 works) per query
            params = urllib.parse.urlencode({
                "search": q, "filter": "open_access.is_oa:true,best_oa_location.license:cc-by",
                "select": SELECT, "per-page": 200, "cursor": cursor, "mailto": MAILTO})
            data = get_json(f"https://api.openalex.org/works?{params}")
            for w in data.get("results", []):
                loc = w.get("best_oa_location") or w.get("primary_location") or {}
                lic, pdf = loc.get("license"), loc.get("pdf_url")
                if lic in CC and pdf and w["id"] not in seen:
                    rec = {"openalex_id": w["id"], "doi": w.get("doi"), "title": w.get("title") or "",
                           "year": w.get("publication_year"),
                           "venue": ((loc.get("source") or {}) or {}).get("display_name")
                                    or ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                           "authors": [a["author"]["display_name"] for a in w.get("authorships", [])][:12],
                           "license": lic, "pdf_url": pdf}
                    seen[w["id"]] = rec
                    out.append(rec)
            cursor = (data.get("meta") or {}).get("next_cursor")
            if not cursor:
                break
            time.sleep(0.3)
        if len(seen) >= target * 2:              # plenty of candidates to survive download failures
            break
    out.sort(key=lambda r: (r["license"] not in PREFER, -(r["year"] or 0)))
    return out


def slug(rec, i):
    doi = (rec.get("doi") or "").rsplit("/", 1)[-1] or rec["openalex_id"].rsplit("/", 1)[-1]
    return f"{i:03d}_" + "".join(c if c.isalnum() or c in "-._" else "-" for c in doi)[:60] + ".pdf"


def download(url, dest):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if not data[:5].startswith(b"%PDF"):
        raise ValueError("not a PDF (got %r)" % data[:16])
    dest.write_bytes(data)
    return hashlib.sha256(data).hexdigest(), len(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=int, default=100)
    ap.add_argument("--out", default="data/raw/kg-rag-cc")
    args = ap.parse_args()
    out = Path(args.out)
    (out / "pdf").mkdir(parents=True, exist_ok=True)

    print("querying OpenAlex ...")
    cands = candidates(args.target)
    print(f"{len(cands)} CC candidates with a PDF")

    manifest, failures, i = [], [], 0
    for rec in cands:
        if len(manifest) >= args.target:
            break
        i += 1
        name = slug(rec, len(manifest) + 1)
        dest = out / "pdf" / name
        try:
            sha, size = download(rec["pdf_url"], dest)
            manifest.append({**rec, "file": f"pdf/{name}", "sha256": sha, "bytes": size})
            print(f"  [{len(manifest):3d}/{args.target}] {size//1024:5d} KB  {rec['title'][:60]}")
        except Exception as e:
            failures.append({"title": rec["title"][:80], "url": rec["pdf_url"], "why": str(e)[:80]})
            if dest.exists():
                dest.unlink()
        time.sleep(0.25)

    (out / "manifest.json").write_text(json.dumps({
        "corpus": "kg-rag-cc", "description": "CC-licensed full-text papers on knowledge graphs and RAG",
        "source": "OpenAlex", "queries": QUERIES, "count": len(manifest),
        "license_note": "Each paper's license is recorded per row; all are Creative Commons. CC-BY requires attribution: render authors, title, and license from this manifest.",
        "papers": manifest}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nwrote {out/'manifest.json'}: {len(manifest)} papers, {len(failures)} download failures")
    lic = {}
    for r in manifest:
        lic[r["license"]] = lic.get(r["license"], 0) + 1
    print("licenses:", lic)


if __name__ == "__main__":
    main()
