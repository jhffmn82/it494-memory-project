"""Build the Phase 1 research package PDF.

Pipeline: markdown -> styled HTML -> Edge headless print-to-PDF (one PDF per
section, so real page numbers are known) -> table of contents rendered with
those numbers -> merged with pypdf, bookmarks added, page labels continuous.

Usage: python scripts/build_package.py            (full build to build/IT494_Phase1_Research_Package.pdf)
"""
import os, re, subprocess, sys, tempfile
from pathlib import Path

import markdown
from pypdf import PdfReader, PdfWriter

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
OP = ROOT / "summaries" / "one-pagers"

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
EDGE = next((p for p in EDGE_CANDIDATES if Path(p).exists()), None)

# Package order: user's spec of 2026-08-25. Proposal placement per his call.
# (front, title, source-path) — one-pager appendix is appended programmatically.
SECTIONS = [
    ("The proposal, before the research", ROOT / "docs" / "02_proposal_draft.md"),
    ("Reading list", ROOT / "reading-list.md"),
    ("The field, by problem", ROOT / "docs" / "01_topic_narrative.md"),
    ("Ways the research could elevate the project", ROOT / "docs" / "04_elevation_options.md"),
    ("Three shapes the project could take", ROOT / "docs" / "05_project_shapes.md"),
    ("End product, test data, and records", ROOT / "docs" / "06_end_product_and_testing.md"),
    ("Anatomy of the mock", ROOT / "docs" / "07_pipeline_anatomy.md"),
    ("The plan, in phases", ROOT / "docs" / "08_plan_of_record.md"),
    ("How it pipes together", ROOT / "docs" / "09_architecture.md"),
    ("How information is modeled", ROOT / "docs" / "10_data_model.md"),
    ("Tentative build plan", ROOT / "docs" / "11_build_plan.md"),
    ("The wiki demo", ROOT / "docs" / "12_wiki_demo.md"),
]
DIGEST = ("The literature, work by work", ROOT / "docs" / "03_digest.md")
IMPL_ORDER = ["ingest", "organize", "retrieve-inject", "maintain", "spine", "wiki"]

CSS = """
@page { size: letter; margin: 25mm 22mm 22mm 22mm; }
html { font-size: 10.5pt; }
body { font-family: Georgia, 'Times New Roman', serif; line-height: 1.5;
       color: #1a1a1a; max-width: 100%; margin: 0; }
h1 { font-size: 17pt; line-height: 1.25; margin: 0 0 4pt 0; font-weight: 700; }
h2 { font-size: 13pt; margin: 18pt 0 6pt 0; font-weight: 700; }
h3 { font-size: 11pt; margin: 14pt 0 4pt 0; font-weight: 700; }
p  { margin: 0 0 8pt 0; text-align: justify; }
li { margin: 0 0 4pt 0; }
table { border-collapse: collapse; font-size: 9.5pt; margin: 8pt 0; }
th, td { border: 0.5pt solid #999; padding: 3pt 6pt; text-align: left; }
code { font-family: Consolas, monospace; font-size: 9pt; }
pre { white-space: pre-wrap; word-wrap: break-word; overflow-wrap: anywhere; }
pre code { font-size: 8.5pt; }
table { table-layout: fixed; width: 100%; word-wrap: break-word; overflow-wrap: anywhere; }
blockquote { margin: 8pt 0 8pt 14pt; color: #444; }
.section-eyebrow { font-family: Arial, sans-serif; font-size: 8pt;
  letter-spacing: 2px; text-transform: uppercase; color: #666; margin-bottom: 18pt; }
.onepager { page-break-before: always; }
.onepager-first { margin-top: 14pt; }
a { color: inherit; text-decoration: none; }
"""

COVER = """
<div style="margin-top:75mm; text-align:left;">
<div style="font-family:Arial,sans-serif; font-size:8pt; letter-spacing:3px; text-transform:uppercase; color:#666;">IT 494 &middot; Research and Proposal &middot; Phase 1</div>
<h1 style="font-size:26pt; margin-top:10pt; line-height:1.2;">Persistent Memory for Stateless Models</h1>
<div style="font-size:12pt; margin-top:6pt; color:#333;">Proposal, literature review, and project plan</div>
<div style="margin-top:32mm; font-size:10.5pt;">Justin Hoffman<br>Illinois State University, MS Computer Science<br>Supervisor: Dr. Xing Fang<br>{date}</div>
<div style="margin-top:8mm; font-size:8.5pt; color:#777;">Literature summaries assembled with AI assistance; all citations verified against source publications.</div>
</div>
"""


def md_to_html(md_text: str, eyebrow: str) -> str:
    body = markdown.markdown(md_text, extensions=["tables", "smarty"])
    return (f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>"
            f"<div class='section-eyebrow'>{eyebrow}</div>{body}")


def print_pdf(html_path: Path, pdf_path: Path):
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                   check=True, capture_output=True, timeout=120)


def build():
    if not EDGE:
        sys.exit("Edge not found; install Edge or adjust EDGE_CANDIDATES.")
    BUILD.mkdir(exist_ok=True)
    work = BUILD / "sections"
    work.mkdir(exist_ok=True)

    from datetime import date
    parts = []  # (title, pdf_path, page_count)

    # Cover
    cover_html = work / "00_cover.html"
    cover_html.write_text(f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>"
                          + COVER.replace("{date}", date.today().strftime("%B %d, %Y")),
                          encoding="utf-8")
    cover_pdf = work / "00_cover.pdf"
    print_pdf(cover_html, cover_pdf)

    # Main sections
    for i, (title, src) in enumerate(SECTIONS, start=1):
        if not src.exists():
            print(f"  SKIP (missing): {src.name}")
            continue
        html = work / f"{i:02d}.html"
        html.write_text(md_to_html(src.read_text(encoding="utf-8"), f"Part {i}"),
                        encoding="utf-8")
        pdf = work / f"{i:02d}.pdf"
        print_pdf(html, pdf)
        parts.append((title, pdf, len(PdfReader(str(pdf)).pages)))
        print(f"  ok: {title} ({parts[-1][2]} pp)")

    # Implementation plans, one part, each plan on a fresh page
    impl_dir = ROOT / "docs" / "impl"
    impl_files = [impl_dir / f"{s}.md" for s in IMPL_ORDER if (impl_dir / f"{s}.md").exists()]
    if impl_files:
        chunks = []
        for j, f in enumerate(impl_files):
            body = markdown.markdown(f.read_text(encoding="utf-8"), extensions=["tables", "smarty"])
            cls = "onepager" if j else "onepager-first"
            chunks.append(f"<div class='{cls}'>{body}</div>")
        html = work / "80_impl.html"
        html.write_text(f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>"
                        f"<div class='section-eyebrow'>Part {len(SECTIONS) + 1}</div>"
                        f"<h1>Implementation plans, step by step</h1>"
                        f"<p>One plan per component, in build order.</p>" + "".join(chunks),
                        encoding="utf-8")
        pdf = work / "80_impl.pdf"
        print_pdf(html, pdf)
        parts.append(("Implementation plans", pdf, len(PdfReader(str(pdf)).pages)))
        print(f"  ok: implementation plans ({parts[-1][2]} pp)")

    # Digest, second to last, before the one-pager appendix
    title, src = DIGEST
    html = work / "85_digest.html"
    html.write_text(md_to_html(src.read_text(encoding="utf-8"), f"Part {len(SECTIONS) + 2}"), encoding="utf-8")
    pdf = work / "85_digest.pdf"
    print_pdf(html, pdf)
    parts.append((title, pdf, len(PdfReader(str(pdf)).pages)))
    print(f"  ok: {title} ({parts[-1][2]} pp)")

    # One-pager appendix, alphabetical by slug, each on a fresh page
    op_files = sorted(OP.glob("*.md"))
    if op_files:
        chunks = []
        for j, f in enumerate(op_files):
            body = markdown.markdown(f.read_text(encoding="utf-8"), extensions=["tables", "smarty"])
            cls = "onepager" if j else "onepager-first"
            chunks.append(f"<div class='{cls}'>{body}</div>")
        html = work / "90_onepagers.html"
        html.write_text(f"<!doctype html><meta charset='utf-8'><style>{CSS}</style>"
                        f"<div class='section-eyebrow'>Appendix</div>"
                        f"<h1>One-page summaries of the sources</h1>"
                        f"<p>{len(op_files)} summaries, alphabetical by first author. Each states at its foot "
                        f"how much of the source it was written from.</p>" + "".join(chunks),
                        encoding="utf-8")
        pdf = work / "90_onepagers.pdf"
        print_pdf(html, pdf)
        parts.append(("Appendix: one-page summaries", pdf, len(PdfReader(str(pdf)).pages)))
        print(f"  ok: appendix ({parts[-1][2]} pp)")

    # Index with real page numbers (cover=1, index itself = 1 page, content follows)
    index_page_count = 1
    start = 1 + index_page_count + 1  # cover + index, first content page
    rows, cursor = [], start
    for title, _, n in parts:
        rows.append(f"<tr><td>{title}</td><td style='text-align:right'>{cursor}</td></tr>")
        cursor += n
    idx_html = work / "01_index.html"
    idx_html.write_text(
        f"<!doctype html><meta charset='utf-8'><style>{CSS}"
        "table.toc{width:100%;border:none} table.toc td{border:none;padding:5pt 0;"
        "border-bottom:0.5pt dotted #bbb;font-size:11pt}</style>"
        f"<div class='section-eyebrow'>Contents</div><h1>Index</h1>"
        f"<table class='toc'>{''.join(rows)}</table>", encoding="utf-8")
    idx_pdf = work / "01_index.pdf"
    print_pdf(idx_html, idx_pdf)
    if len(PdfReader(str(idx_pdf)).pages) != index_page_count:
        print("  note: index exceeded one page; page numbers off by the difference")

    # Merge with bookmarks
    writer = PdfWriter()
    def add(path):
        r = PdfReader(str(path))
        for pg in r.pages:
            writer.add_page(pg)
        return len(r.pages)

    n = add(cover_pdf)
    writer.add_outline_item("Cover", 0)
    at = n
    at += add(idx_pdf)
    writer.add_outline_item("Index", n)
    for title, pdf, count in parts:
        writer.add_outline_item(title, at)
        at += add(pdf)

    # Stamp page numbers (skip the cover) directly onto the writer's pages,
    # so the outline built above survives.
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    total = len(writer.pages)
    overlay_path = BUILD / "_numbers.pdf"
    c = canvas.Canvas(str(overlay_path), pagesize=letter)
    for p in range(total):
        if p > 0:
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(0.4, 0.4, 0.4)
            c.drawCentredString(letter[0] / 2, 24, str(p + 1))
        c.showPage()
    c.save()
    nums = PdfReader(str(overlay_path))
    for p in range(1, total):
        writer.pages[p].merge_page(nums.pages[p])

    out = BUILD / "IT494_Phase1_Research_Package.pdf"
    with open(out, "wb") as fh:
        writer.write(fh)
    overlay_path.unlink()
    print(f"\nWrote {out} ({total} pages)")


if __name__ == "__main__":
    build()
