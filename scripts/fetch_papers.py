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
    # --- added 2026-08-28: evaluation corpora ---
    "infinitebench-2024": (arxiv("2402.13718"), "ACL 2024. En.MC split is the primary evaluation set"),
    "literaryqa-2025": (arxiv("2510.13494"), "EMNLP 2025, anthology 2025.emnlp-main.1729. Cleaned Gutenberg NarrativeQA"),
    "novelqa-2024": (arxiv("2403.12766"), "Gold answers held out, Codabench only. Kept for the closed-book baseline"),
    "bookcoref-2025": (arxiv("2507.12075"), "ACL 2025. Book-scale coreference, no relations"),
    "storybench-2025": (arxiv("2506.13356"), "Long-term memory over interactive fiction"),
    "stonybook-2023": (arxiv("2311.03614"), "~50k novels, standard XML annotation"),
    # --- added 2026-08-28: extraction ordering, the ninth dead claim ---
    "itext2kg-2024": (arxiv("2409.03284"), "Ran the global-vs-local cast ablation; global scored ~10 pts LOWER"),
    "rakg-2025": (arxiv("2504.09823"), "Document-wide disambiguation then per-entity relation construction"),
    "linkkg-2025": (arxiv("2510.26486"), "Global alias cache, node duplication 27.0->10.6 short, 36.0->17.8 long"),
    "corekg-2025": (arxiv("2506.21607"), "ICDM 2025. Removing coreference costs +28.25% node duplication"),
    "slide-2025": (arxiv("2503.17952"), "Extraction context varied on a 160k-token novel"),
    "elite-2025": (arxiv("2505.11908"), "Discards embeddings AND graph construction"),
    # --- added 2026-08-28: the composition, per-element occupants ---
    "story-ribbons-2025": (arxiv("2508.06772"), "IEEE VIS 2025. NEAREST PEER-REVIEWED THREAT: cell matrix, both marginals, quote gate, 30 Gutenberg works"),
    "reveriemem-2026": (arxiv("2606.25632"), "Per-character per-scene retrospective summaries, 8 novels incl. Holmes"),
    "cam-2025": (arxiv("2510.05520"), "NeurIPS 2025. Incremental overlapping clustering; killed covering-vs-partition"),
    "nkw-2026": (arxiv("2606.05724"), "Degree-gated per-entity extraction; closest whole-stack analogue"),
    "statefuse-2026": (arxiv("2607.05844"), "Append-only, resolution at projection time, conflict objects"),
    "moss-2026": (arxiv("2607.04391"), "A year in production on one scholar's corpus, no LLM in the retrieval loop"),
    "xmemory-2026": (arxiv("2604.27906"), "Explicit unknowns as a first-class operation"),
    "streaming-knowledge-compilation-2026": (arxiv("2606.09877"), "Per-(entity, document) materiality gate under a token budget"),
    "memtier-2026": (arxiv("2605.03675"), "Checked and NOT entity-salience tiering; kept to prevent re-checking"),
    "engram-2026": (arxiv("2606.09900"), "arXiv comments field names no venue; do not cite a venue for it"),
    # --- added 2026-08-28: the LLM Wiki line, absent from this repo until now ---
    "llm-wiki-ming-2026": (arxiv("2605.25480"), "One page per entity, 5,825 pages, YAML frontmatter, wikilinks"),
    "llm-wiki-cochran-2026": (arxiv("2607.04576"), "A real 709-page LLM-maintained wiki"),
    "wiki-vs-rag-cochran-2026": (arxiv("2605.18490"), "PREREGISTERED head-to-head: vector RAG vs an LLM-compiled wiki"),
    "wicer-2026": (arxiv("2605.07068"), "Wiki construction with entity resolution"),
    "llmpedia-2026": (arxiv("2603.24080"), "Infobox plus lead, ~1.3M articles"),
    # --- added 2026-08-28: local-first, the eleventh dead claim ---
    "as-we-may-search-2026": (arxiv("2606.29652"), "ICTIR 2026. OCCUPIES the local-first thesis; 1K-1M sweep, exact vs HNSW vs IVF"),
    "memx-2026": (arxiv("2603.16171"), "Local-first libSQL plus FTS5, evaluated on LongMemEval"),
    "vstash-2026": (arxiv("2604.15484"), "Single SQLite file, sqlite-vec plus FTS5"),
    "superlocalmemory-2026": (arxiv("2608.08253"), "Eleven fault-injection scenarios x200 reps against its own invariants"),
    "graphrag-bench-2025": (arxiv("2506.05690"), "When graphs help: reasoning 53.4 vs 42.9, summarization 64.4 vs 51.3"),
    # --- added 2026-08-28: the provenance findings, ruled out but searched ---
    "isnad-rijal-2026": (arxiv("2607.24117"), "Independent-chain corroboration; publishes the FIX for echo inflation"),
    "errors-become-narratives-2026": (arxiv("2606.14589"), "Single personal-assistant runtime; ~70% of silent failures caught by humans"),
    "manufactured-confidence-2026": (arxiv("2606.29279"), "Consolidation rewrites hedged remarks into flat dated assertions"),
    "agentchaos-2026": (arxiv("2608.06790"), "ASE 2026. Fault injection for agent systems"),
    "agentchaosbench-2026": (arxiv("2608.14680"), "Ten operational fault types, 275 traces"),
    # --- added 2026-08-28: benchmark generality and requirements ---
    "ama-bench-2026": (arxiv("2602.22769"), "Cross-substrate ranking flip"),
    "cross-scenario-generality-2026": (arxiv("2606.04315"), "Winning on one scenario does not imply winning on others"),
    "agent-native-memory-2026": (arxiv("2606.24775"), "12 systems, 11 datasets; occupies requirements-plus-coverage"),
    "meme-2026": (arxiv("2605.12477"), "100 episodes, 694 questions, entity KG, CC BY 4.0"),
    # --- added 2026-08-28: narrative memory and corpora ---
    "narrative-world-model-2026": (arxiv("2607.05577"), "MOST IMPORTANT UNREAD PAPER: same niche, baselines and corpus type"),
    "stage-2026": (arxiv("2601.08510"), "151 bilingual screenplays, provenance-linked narrative backbone"),
    "coser-2025": (arxiv("2502.09082"), "ICML 2025. 771 books, alias-to-canonical character mappings"),
    "affilkg-2026": (arxiv("2505.10798"), "LREC 2026. Book scans plus OCR text paired with labelled KGs"),
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
