# kg-rag-cc: CC-licensed papers on knowledge graphs and RAG

100 full-text papers, every one Creative Commons (all `cc-by` in this build), gathered from
OpenAlex by `scripts/fetch_kg_rag_cc.py`. The PDFs are tracked in git (100 files under `pdf/`,
194 MB) and ship in version 4 of the Kaggle raw dataset, jhffmn/it494-narrative-corpora-raw;
they are also reproducible from the script. `manifest.json` records each paper's title, authors,
year, venue, DOI, OpenAlex id, exact license, source URL, filename, sha256, and byte count.

Re-fetch: `python scripts/fetch_kg_rag_cc.py --target 100 --out data/raw/kg-rag-cc`

Attribution: CC-BY requires it. Render authors, title, and license from the manifest wherever a
paper is shown (e.g. the wiki's document page).
