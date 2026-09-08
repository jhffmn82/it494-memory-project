"""Render a document package into a human-readable document (HTML always, PDF when a
renderer is present).

    python scripts/render_package.py path/to/<file>.jsonl            # writes <file>.html beside it
    python scripts/render_package.py path/to/<file>.jsonl --pdf      # also writes <file>.pdf
    python scripts/render_package.py --demo out/                     # a synthetic package, to prove it runs

A package is the ingestor's output: one JSON record per line, ending in a `completion`. This
reads it back and lays out the knowledge it holds, not the run's diagnostics: how many units were
read, the document summary, a summary per unit, every entity, the facts of each entity with the
verbatim quote behind each one, then the most-covered entities in full.

HTML is the canonical output: it is unicode-safe (the corpus includes Greek), it is the same
format the wiki uses, and any browser prints it to PDF. `--pdf` writes a PDF directly when
WeasyPrint is importable; otherwise the HTML is written and a one-line note says how to get a PDF.
No non-stdlib import is required unless `--pdf` is asked for.
"""
import argparse
import html
import json
from pathlib import Path


def read_jsonl(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except ValueError:
                break                       # a killed run can leave a half-written last line
    return rows


def grouped(rows, key):
    out = {}
    for row in rows:
        out.setdefault(row.get(key), []).append(row)
    return out


def read_package(path):
    rows = read_jsonl(path)
    if not rows or rows[-1].get("record") != "completion":
        raise SystemExit(f"{path}: no completion record; the package is unfinished or not a package")
    return grouped(rows, "record")


def ranked_majors(by):
    """Entity nodes, most units first then most facts: [(units, facts, node)]."""
    units_of = {e["subject"]: len(e.get("units", [])) for e in by.get("edge", []) if e["predicate"] == "appears_in"}
    facts_of = grouped(by.get("fact", []), "subject")
    ranked = [(units_of.get(n["node_id"], 0), len(facts_of.get(n["node_id"], [])), n)
              for n in by.get("node", []) if n["kind"] != "document"]
    return sorted(ranked, key=lambda item: (-item[0], -item[1]))


def esc(text):
    return html.escape(str(text if text is not None else ""))


def one_line(text):
    return " ".join(str(text).split())


def readable(predicate):
    """A stored predicate as words: is_powered_by -> "is powered by"."""
    return str(predicate or "").replace("_", " ").strip()


CSS = """
:root { --ink:#1a1a1a; --muted:#70757a; --line:#e4e6e9; --accent:#2f6f9f; --quote:#1a7a4c; --bg:#fff; }
* { box-sizing:border-box; }
body { font:15px/1.6 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:var(--ink);
       background:var(--bg); max-width:820px; margin:2.2rem auto; padding:0 1.6rem; }
h1 { font-size:1.55rem; margin:0 0 .15rem; line-height:1.25; }
h2 { font-size:1.1rem; margin:2rem 0 .6rem; color:var(--accent); border-bottom:2px solid var(--line); padding-bottom:.25rem; }
h3 { font-size:1rem; margin:1.3rem 0 .35rem; }
.meta { color:var(--muted); font-size:.86rem; margin-bottom:.4rem; }
.summary { background:#f6f9fc; border-left:3px solid var(--accent); padding:.75rem 1rem; border-radius:3px; margin:.4rem 0; }
.unit { margin:.35rem 0; }
.unit .u { color:var(--muted); font-weight:600; }
table.roster { border-collapse:collapse; width:100%; font-size:.9rem; }
table.roster td { padding:.22rem .5rem; border-bottom:1px solid var(--line); vertical-align:top; }
table.roster td.k { color:var(--muted); white-space:nowrap; width:1%; }
.entity { margin:1.1rem 0; padding-top:.4rem; border-top:1px solid var(--line); }
.entity h3 { margin-bottom:.15rem; }
.kind { color:var(--muted); font-weight:400; font-size:.9rem; }
.forms { color:var(--muted); font-size:.82rem; margin:.15rem 0 .4rem; }
.fact { margin:.5rem 0; }
.stmt { font-weight:600; }
.q { display:block; color:#33383d; border-left:2px solid var(--quote); margin:.15rem 0 0 1rem;
     padding-left:.7rem; font-size:.88rem; }
.q .src { color:var(--muted); font-size:.82rem; }
.attrs { margin:.3rem 0 0 1rem; }
.attrs li { margin:.1rem 0; }
.deep .summary { background:#f6f9fc; }
@media print { body { margin:0; max-width:none; font-size:11pt; } h2 { page-break-after:avoid; } .entity { page-break-inside:avoid; } }
"""


def statement(f, name_of, this_name):
    """A fact as a readable line: the entity is the subject on a forward fact, the object on an
    inverse one (where the object slot holds the other entity's name)."""
    pred, qual = readable(f["predicate"]), (f" ({esc(f['qualifiers'])})" if f.get("qualifiers") else "")
    if f.get("direction") == "inverse":
        other = esc(f.get("provenance", {}).get("subject_name", f["object"]))
        return f"{other} {esc(pred)} {esc(this_name)}{qual}"
    obj = name_of.get(f["object"], f["object"]) if f.get("object_is_node") else f["object"]
    return f"{esc(this_name)} {esc(pred)} {esc(obj)}{qual}"


def render_html(by, top=5, note=None):
    doc = by["document"][0]
    counts = by["completion"][0].get("counts", {})
    units = sorted(by.get("unit", []), key=lambda u: u["position"])
    read_units = counts.get("units", len(units))
    label_of = {u["unit_id"]: (f"[{u['position']}] {u.get('label') or ''}").strip() for u in units}
    position = {u["unit_id"]: u["position"] for u in units}
    doc_node = next(n["node_id"] for n in by["node"] if n["kind"] == "document")
    abstracts = {a["node_id"]: a["text"] for a in by.get("abstract", [])}
    cells_of = grouped(by.get("cell", []), "node_id")
    facts_of = grouped(by.get("fact", []), "subject")
    attributes_of = grouped(by.get("attribute", []), "node_id")
    aliases_of = grouped(by.get("alias", []), "node_id")
    name_of = {n["node_id"]: n["name"] for n in by.get("node", [])}

    o = []
    title = doc.get("title") or doc["source_uri"]
    o.append(f"<h1>{esc(title)}</h1>")
    line = f"{read_units} of {len(units)} units read" if read_units != len(units) else f"{len(units)} units"
    extra = " &middot; ".join(esc(doc[k]) for k in ("author", "source_class", "occurred_at") if doc.get(k))
    o.append(f'<div class="meta">{esc(doc["source_uri"])} &middot; {line}{" &middot; " + extra if extra else ""}</div>')

    o.append("<h2>Document summary</h2>")
    o.append(f'<div class="summary">{esc(abstracts.get(doc_node, "(no summary)"))}</div>')

    summary_of = {c["unit_id"]: c["text"] for c in cells_of.get(doc_node, [])}
    if summary_of:
        o.append("<h2>Unit summaries</h2>")
        for u in units:
            if u["unit_id"] in summary_of:
                o.append(f'<div class="unit"><span class="u">{esc(label_of[u["unit_id"]])}</span> &mdash; {esc(summary_of[u["unit_id"]])}</div>')

    ranked = ranked_majors(by)
    o.append(f"<h2>Entities ({len(ranked)})</h2>")
    o.append("<table class='roster'>")
    for n_units, n_facts, n in ranked:
        o.append(f"<tr><td>{esc(n['name'])}</td><td class='k'>{esc(n['kind'])}</td></tr>")
    o.append("</table>")

    o.append("<h2>Facts by entity</h2>")
    for n_units, n_facts, n in ranked:
        facts = facts_of.get(n["node_id"], [])
        if not facts:
            continue
        o.append('<div class="entity">')
        o.append(f'<h3>{esc(n["name"])} <span class="kind">({esc(n["kind"])})</span></h3>')
        for f in facts:
            src = esc(label_of.get(f["unit_id"], ""))
            o.append(f'<div class="fact"><span class="stmt">{statement(f, name_of, n["name"])}</span>'
                     f'<span class="q"><span class="src">{src}</span> &ldquo;{esc(one_line(f["quote"]))}&rdquo;</span></div>')
        o.append("</div>")

    deep = ranked[:top]
    if deep:
        o.append(f"<h2>In depth: the {len(deep)} most-covered entities</h2>")
    for n_units, n_facts, n in deep:
        nid = n["node_id"]
        o.append('<div class="entity deep">')
        o.append(f'<h3>{esc(n["name"])} <span class="kind">({esc(n["kind"])})</span></h3>')
        forms = [a["alias"] for a in aliases_of.get(nid, [])][:20]
        if forms:
            o.append(f'<div class="forms">also written: {esc(" | ".join(forms))}</div>')
        if nid in abstracts:
            o.append(f'<div class="summary">{esc(abstracts[nid])}</div>')
        cells = sorted(cells_of.get(nid, []), key=lambda c: position.get(c["unit_id"], 0))
        if cells:
            o.append("<p><b>Across the document</b></p>")
            for c in cells:
                o.append(f'<div class="unit"><span class="u">{esc(label_of.get(c["unit_id"], ""))}</span> &mdash; {esc(c["text"])}</div>')
        attrs = attributes_of.get(nid, [])
        if attrs:
            o.append("<p><b>Attributes</b></p><ul class='attrs'>")
            for a in attrs:
                v = f": {esc(a['value'])}" if a.get("value") else ""
                o.append(f"<li>{esc(readable(a['attribute']))}{v}</li>")
            o.append("</ul>")
        o.append("</div>")

    if note:
        o.append(f'<div class="meta" style="margin-top:2rem;border-top:1px solid var(--line);padding-top:.5rem">{esc(note)}</div>')
    body = "\n".join(o)
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{esc(title)}</title><style>{CSS}</style></head><body>{body}</body></html>"


def write_pdf(html_text, pdf_path):
    try:
        import weasyprint
    except ImportError:
        return False
    weasyprint.HTML(string=html_text).write_pdf(str(pdf_path))
    return True


def demo_package(out_dir):
    """A tiny synthetic package (no real quotes) so the renderer can be proven anywhere."""
    dn, e = "demo:doc", "demo:n1"
    rows = [
        {"record": "document", "doc_id": "demo", "source_uri": "demo/widget.txt", "sha256": "0" * 64,
         "title": "The Widget Report", "author": "A. Author", "source_class": "canonical",
         "ingested_at": "2026-09-08T00:00:00+00:00", "occurred_at": "2026", "loader": "demo", "flags": [], "text_length": 100},
        {"record": "unit", "unit_id": "demo:u0", "doc_id": "demo", "position": 0, "label": "Chapter 1", "start": 0, "end": 100,
         "occurred_at": None, "occurred_until": None, "kind": "body"},
        {"record": "node", "node_id": dn, "name": "The Widget Report", "kind": "document", "created_from_unit": "demo:u0", "provenance": {}},
        {"record": "node", "node_id": e, "name": "Widget", "kind": "object", "created_from_unit": "demo:u0",
         "provenance": {"names": ["Widget", "the widget"]}},
        {"record": "alias", "alias": "the widget", "node_id": e, "first_seen_unit": "demo:u0"},
        {"record": "edge", "predicate": "appears_in", "subject": e, "object": dn, "units": ["demo:u0"]},
        {"record": "cell", "node_id": dn, "unit_id": "demo:u0", "text": "A widget is introduced and described.", "tier": "demo"},
        {"record": "cell", "node_id": e, "unit_id": "demo:u0", "text": "The widget is blue and round.", "tier": "demo"},
        {"record": "abstract", "node_id": dn, "text": "A short report about a widget.", "tier": "demo", "updated_at": "2026-09-08"},
        {"record": "abstract", "node_id": e, "text": "A blue, round widget that spins.", "tier": "demo", "updated_at": "2026-09-08"},
        {"record": "attribute", "node_id": e, "attribute": "shape", "value": "round", "from_facts": ["demo:u0:f0"], "tier": "demo"},
        {"record": "fact", "fact_id": "demo:u0:f0", "subject": e, "predicate": "is_colored", "object": "blue",
         "object_is_node": False, "direction": "forward", "qualifiers": None, "rank": "active", "unit_id": "demo:u0",
         "quote": "the widget is blue", "quote_start": 0, "quote_end": 18, "valid_from": None, "valid_to": None,
         "occurred_at": "2026", "occurred_until": None, "tier": "demo", "author": "A. Author",
         "provenance": {"subject_name": "Widget", "matched_by": "exact"}},
        {"record": "completion", "doc_id": "demo", "ingestor": "demo", "counts": {"units": 1}, "empty": False},
    ]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "widget.jsonl"
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    return path


def main():
    ap = argparse.ArgumentParser(description="Render a document package to a human-readable HTML (and optionally PDF).")
    ap.add_argument("package", nargs="?", help="path to a package .jsonl")
    ap.add_argument("--out", help="output directory (default: beside the package)")
    ap.add_argument("--top", type=int, default=5, help="entities shown in full at the end (default 5)")
    ap.add_argument("--pdf", action="store_true", help="also write a PDF (needs WeasyPrint)")
    ap.add_argument("--note", help="a footer note on the page")
    ap.add_argument("--demo", metavar="DIR", help="write a synthetic package to DIR and render it")
    args = ap.parse_args()

    if args.demo:
        args.package = str(demo_package(args.demo))
        print(f"wrote demo package {args.package}")
    if not args.package:
        ap.error("give a package .jsonl, or --demo DIR")

    pkg = Path(args.package)
    by = read_package(pkg)
    out_dir = Path(args.out) if args.out else pkg.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    html_text = render_html(by, top=args.top, note=args.note)
    html_path = out_dir / (pkg.stem + ".html")
    html_path.write_text(html_text, encoding="utf-8")
    print(f"wrote {html_path}")
    if args.pdf:
        pdf_path = out_dir / (pkg.stem + ".pdf")
        if write_pdf(html_text, pdf_path):
            print(f"wrote {pdf_path}")
        else:
            print("PDF skipped: WeasyPrint is not installed. `pip install weasyprint`, or open the HTML and Print to PDF.")


if __name__ == "__main__":
    main()
