"""Fetch reference PDFs for the IT 494 reading list into papers/.

Every fetch is logged to papers/MANIFEST.md with status. Paywalled works get a
stub entry pointing at the DOI. Re-runnable: existing non-empty PDFs are skipped.
"""
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPERS = ROOT / "papers"
PAPERS.mkdir(exist_ok=True)

UA = {"User-Agent": "Mozilla/5.0 (personal research reference fetch; contact jhffmn.myalt1@gmail.com)"}

def arxiv(aid):
    return f"https://arxiv.org/pdf/{aid}"

# slug -> (url or None, citation note)
ITEMS = {
    # start-here
    "kumaran2016-cls-updated": (None, "Trends Cog Sci 20(7). DOI:10.1016/j.tics.2016.05.004 (Elsevier)"),
    "park2023-generative-agents": (arxiv("2304.03442"), "UIST 2023"),
    "sarthi2024-raptor": (arxiv("2401.18059"), "ICLR 2024"),
    "rasmussen2025-zep": (arxiv("2501.13956"), "arXiv"),
    "edge2024-graphrag": (arxiv("2404.16130"), "Microsoft Research"),
    # consolidation
    "mcclelland1995-cls": (None, "Psych Review 102(3). DOI:10.1037/0033-295X.102.3.419 (APA)"),
    "teyler2007-hippocampal-index": (None, "Hippocampus 17(12). DOI:10.1002/hipo.20350 (Wiley)"),
    "tononi2014-shy": (None, "Neuron 81(1). DOI:10.1016/j.neuron.2013.12.025 (Elsevier)"),
    "zacks2007-event-perception": (None, "Psych Bulletin 133(2). DOI:10.1037/0033-2909.133.2.273 (APA)"),
    "sumers2024-coala": (arxiv("2309.02427"), "TMLR"),
    "rezazadeh2025-memtree": (arxiv("2410.14052"), "ICLR 2025"),
    "talebirad2026-hierarchical-theory": (arxiv("2603.21564"), "arXiv"),
    "wu2021-recursive-books": (arxiv("2109.10862"), "OpenAI"),
    # retrieval / caching
    "wang2024-rag-best-practices": (arxiv("2407.01219"), "EMNLP 2024"),
    "douze2024-faiss": (arxiv("2401.08281"), "arXiv"),
    "kuffo2025-pdx": (arxiv("2503.04422"), "SIGMOD 2025"),
    "malkov2016-hnsw": (arxiv("1603.09320"), "arXiv/TPAMI"),
    "chan2025-cag": (arxiv("2412.15605"), "WWW 2025"),
    "nolima2025-long-context": (arxiv("2502.05167"), "arXiv"),
    "jeong2024-adaptive-rag": (arxiv("2403.14403"), "NAACL 2024"),
    # benchmarks
    "maharana2024-locomo": (arxiv("2402.17753"), "ACL 2024"),
    "wu2025-memoryagentbench": (arxiv("2507.05257"), "arXiv"),
    # faithfulness
    "chang2024-booookscore": (arxiv("2310.00785"), "ICLR 2024"),
    "kim2024-fables": (arxiv("2404.01261"), "COLM 2024"),
    # knowledge graphs (existing entries)
    "chen1976-er-model": (None, "ACM TODS 1(1). DOI:10.1145/320434.320440 (ACM)"),
    "angles2017-graph-query-foundations": (arxiv("1610.06264"), "ACM CSUR 50(5), preprint"),
    "hogan2021-knowledge-graphs": (arxiv("2003.02320"), "ACM CSUR 54(4), preprint"),
    "snodgrass1999-time-oriented-db": ("https://www2.cs.arizona.edu/~rts/tdbbook.pdf", "author-released book PDF"),
    "weikum2021-machine-knowledge": (arxiv("2009.11564"), "FnT Databases, preprint"),
    "pan2024-unifying-llm-kg": (arxiv("2306.08302"), "IEEE TKDE, preprint"),
    "rossi2021-kg-embedding": (arxiv("2002.00819"), "ACM TKDD, preprint"),
    # conversation mining
    "kecht2021-event-log-nli": (
        "https://icpmconference.org/2021/wp-content/uploads/sites/5/2021/09/Event-Log-Construction-from-Customer-Service-Conversations-Using-Natural-Language-Inference.pdf",
        "ICPM 2021, conference-hosted PDF"),
    "gung2023-dstc11-intent": (arxiv("2304.12982"), "SIGDIAL 2023"),
    "deraedt2023-idas": ("https://aclanthology.org/2023.nlp4convai-1.7.pdf", "ACL Anthology"),
    "wegmann2022-style-content": (arxiv("2204.04907"), "RepL4NLP 2022"),
    # outcomes
    "brynjolfsson2025-genai-at-work": (None, "QJE 140(2). DOI:10.1093/qje/qjae044 (OUP)"),
    "ouyang2026-reasoningbank": (arxiv("2509.25140"), "ICLR 2026"),
    "liu2025-user-feedback": (arxiv("2507.23158"), "EMNLP 2025"),
    "rezazadeh2025-collaborative-memory": (arxiv("2505.18279"), "arXiv"),
    # shared state
    "erman1980-hearsay-ii": (None, "ACM Comp Surveys 12(2). DOI:10.1145/356810.356816 (ACM)"),
    "hayesroth1985-blackboard-control": (None, "Artificial Intelligence 26(3). DOI:10.1016/0004-3702(85)90063-3 (Elsevier)"),
    "salemi2026-blackboard-llm": (arxiv("2510.01285"), "arXiv"),
    "pollertlam2026-beyond-context-window": (arxiv("2603.04814"), "arXiv"),
    # note: LongMemEval intentionally absent: no verified id on file yet; added after verification.
}

def fetch(url, dest):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if not data.startswith(b"%PDF"):
        return f"NOT-PDF ({len(data)} bytes)"
    dest.write_bytes(data)
    return f"OK ({len(data)//1024} KB)"

rows = []
for slug, (url, note) in ITEMS.items():
    dest = PAPERS / f"{slug}.pdf"
    if dest.exists() and dest.stat().st_size > 10_000:
        rows.append((slug, "cached", url or "-", note))
        continue
    if url is None:
        rows.append((slug, "PAYWALLED - use DOI via library", "-", note))
        continue
    try:
        status = fetch(url, dest)
    except Exception as e:  # noqa: BLE001 - log and continue
        status = f"FAILED: {type(e).__name__}: {e}"
    rows.append((slug, status, url, note))
    time.sleep(3)  # be polite to arXiv

ok = sum(1 for _, s, _, _ in rows if s.startswith(("OK", "cached")))
lines = [
    "# Paper manifest",
    "",
    f"Fetched {time.strftime('%Y-%m-%d %H:%M')}. {ok}/{len(rows)} on disk.",
    "Paywalled items: pull via ISU library using the DOI in the note.",
    "",
    "| File | Status | Source | Note |",
    "|---|---|---|---|",
]
for slug, status, url, note in rows:
    lines.append(f"| {slug}.pdf | {status} | {url} | {note} |")
(PAPERS / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"{ok}/{len(rows)} papers on disk; manifest written")
for slug, status, _, _ in rows:
    if not status.startswith(("OK", "cached", "PAYWALLED")):
        print(" PROBLEM:", slug, status)
