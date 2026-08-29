"""Check the entity-resolution claims in docs/10_entity_resolution.md against the PDFs.

Every claim in that document's "What is actually unmeasured" table asserts how some
published system resolves entities. This script does not evaluate those claims. It
finds the passages and prints them so you can read them and judge for yourself.

Two sections:

  PER-SYSTEM   For each system, the pattern that should find its resolution method.
               Read the hits. If they do not say what the doc says, the doc is wrong.

  ABSENCE      The doc claims no system in this corpus uses entity co-occurrence as a
               resolution signal. An absence claim is only as good as its search, so
               this prints every co-occurrence hit across every PDF, with context,
               and leaves the judgement to you. A control pattern runs first: if the
               control finds nothing, the search itself is broken and the absence
               result means nothing.

Usage: python scripts/verify_claims.py [system_name]
Needs pdftotext on PATH (poppler). Check with: pdftotext -v
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "papers"

# (label, pdf, what the doc claims, regex to find the passage)
CLAIMS = [
    ("GraphRAG", "edge2024-graphrag.pdf",
     "exact string matching, stated outright",
     r"string match|exact match|resolv\w* entit|duplicate entit"),
    ("iText2KG", "itext2kg-2024.pdf",
     "name-embedding cosine, threshold 0.7",
     r"cosine similarity|threshold|0\.7"),
    ("RAKG", "rakg-2025.pdf",
     "name plus type embedding, then an LLM adjudicates",
     r"VectJudge|SameJudge|disambiguat"),
    ("CORE-KG", "corekg-2025.pdf",
     "type-wise LLM coreference pass before extraction",
     r"coreference resolution|type-aware|entity-type-aware"),
    ("LINK-KG", "linkkg-2025.pdf",
     "prompt cache of aliases, explicit details only",
     r"[Pp]rompt [Cc]ache|non-speculative|auxiliary description"),
    ("Zep / Graphiti", "rasmussen2025-zep.pdf",
     "name and summary embedding, then an LLM resolution prompt",
     r"entity resolution|cosine similarity|BM25|summar\w+ .{0,40}entit"),
    ("AutoSchemaKG", "bai2025-autoschemakg.pdf",
     "no resolution stage at all",
     r"entity resolution|deduplicat|canonicaliz|coreference"),
    ("HippoRAG", "hipporag-2024.pdf",
     "never merges; adds synonym edges above cosine 0.8",
     r"synonym|standardiz"),
    ("HippoRAG 2", "hipporag2-2025.pdf",
     "same approach as HippoRAG 1",
     r"synonym|standardiz"),
]

# The absence claim, and the control that proves the search works at all.
ABSENCE = r"co-?occurr\w*"
CONTROL = r"entit\w+"


def text_of(pdf: Path) -> str:
    if not pdf.exists():
        return ""
    try:
        r = subprocess.run(["pdftotext", str(pdf), "-"],
                           capture_output=True, text=True, errors="replace", timeout=180)
        return r.stdout
    except Exception as e:
        print(f"    ! extraction failed: {e}")
        return ""


def show(text: str, pattern: str, limit: int, width: int = 240) -> int:
    """Print matching passages. Returns the number of matches found."""
    hits = list(re.finditer(pattern, text, re.I))
    for m in hits[:limit]:
        a, b = max(0, m.start() - width // 2), min(len(text), m.end() + width // 2)
        frag = " ".join(text[a:b].split())
        print(f"      ...{frag}...")
    if len(hits) > limit:
        print(f"      ({len(hits) - limit} more matches not shown)")
    return len(hits)


def main():
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext not on PATH. Install poppler, or run: winget install poppler")

    only = sys.argv[1].lower() if len(sys.argv) > 1 else None

    print("=" * 78)
    print("PER-SYSTEM: what the doc claims, and the passages behind it")
    print("=" * 78)
    print("Read the excerpts. If they do not support the claim, the doc is wrong.\n")

    for label, fname, claim, pattern in CLAIMS:
        if only and only not in label.lower():
            continue
        print(f"  {label}   [{fname}]")
        print(f"    doc says: {claim}")
        pdf = PAPERS / fname
        if not pdf.exists():
            print("    ! PDF NOT ON DISK, claim unverifiable here\n")
            continue
        n = show(text_of(pdf), pattern, limit=4)
        if n == 0:
            print("      NO MATCHES. Either the pattern is wrong or the claim is.")
        print()

    if only:
        return

    print("=" * 78)
    print("ABSENCE: 'no system here uses co-occurrence as a resolution signal'")
    print("=" * 78)
    print("Control first. If the control finds nothing, the search is broken and the")
    print("absence result below proves nothing.\n")

    pdfs = sorted(PAPERS.glob("*.pdf"))
    control_total = 0
    findings = []
    for pdf in pdfs:
        t = text_of(pdf)
        if not t:
            continue
        control_total += len(re.findall(CONTROL, t, re.I))
        hits = list(re.finditer(ABSENCE, t, re.I))
        if hits:
            findings.append((pdf.name, t, len(hits)))

    print(f"  CONTROL '{CONTROL}': {control_total:,} matches across {len(pdfs)} PDFs")
    print("  -> search is working\n" if control_total else "  -> SEARCH BROKEN, stop here\n")

    if not findings:
        print(f"  '{ABSENCE}' appears in NO paper on disk.")
        return

    print(f"  '{ABSENCE}' appears in {len(findings)} of {len(pdfs)} papers.")
    print("  Each is printed below. The claim is not that the word is absent, it is that")
    print("  nobody uses it AS A RESOLUTION SIGNAL. Read them and decide.\n")
    for name, t, n in sorted(findings, key=lambda x: -x[2]):
        print(f"  --- {name}  ({n} hit{'s' if n > 1 else ''})")
        show(t, ABSENCE, limit=3)
        print()


if __name__ == "__main__":
    main()
