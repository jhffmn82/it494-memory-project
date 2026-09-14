"""The store: one SQLite file built from a Step 1 dataset folder and the Step 0 text.

    python -m threadatlas.store <step1-dir> <step0-documents.jsonl> <out.sqlite>

<step1-dir> is the Step 1 dataset as published (one file per record type, every row keyed by
doc_id; `scripts/pack_step1_public.py` makes it). <step0-documents.jsonl> holds the text. The
document's text is stored once; every quote is re-sliced from it at load and the load stops on
the first mismatch. FTS5 is built over abstracts, cells and fact quotes when the SQLite build has
it, and skipped with a note when it does not (BUILD.md).

Everything the global layer adds (parents, up-edges, offers) and the sidecar's row map have their
tables declared here and are filled by later steps, so the schema is in one place.
"""
import json
import sqlite3
import sys
from pathlib import Path

SCHEMA = """
create table document (
    doc_id text primary key, source_uri text, sha256 text, title text, author text,
    source_class text, occurred_at text, ingested_at text, loader text, flags text, text text);
create table unit (
    unit_id text primary key, doc_id text, position integer, label text, kind text,
    start integer, end integer, occurred_at text);
create table piece (
    doc_id text, unit_id text, position integer, kind text, start integer, end integer,
    author text, occurred_at text);
create table node (
    doc_id text, node_id text, name text, kind text, created_from_unit text, provenance text,
    primary key (doc_id, node_id));
create table alias (doc_id text, alias text, node_id text, first_seen_unit text);
create table edge (
    doc_id text, predicate text, subject text, object text, units text, position integer);
create table fact (
    doc_id text, fact_id text, subject text, predicate text, object text, object_is_node integer,
    direction text, qualifiers text, rank text, unit_id text, quote text, quote_start integer,
    quote_end integer, valid_from text, occurred_at text, tier text, author text, provenance text,
    primary key (doc_id, fact_id));
create table cell (doc_id text, node_id text, unit_id text, text text, tier text, provenance text);
create table abstract (doc_id text, node_id text, text text, tier text, updated_at text);
create table adjudicated_fact (
    doc_id text, node_id text, predicate text, object text, qualifiers text, from_facts text,
    tier text);
create table attribute (
    doc_id text, node_id text, attribute text, value text, from_facts text, tier text);
create table contradiction (
    doc_id text, node_id text, note text, from_facts text, holds text, because text);
create table rejection (doc_id text, stage text, unit_id text, category text, row text);
create table ledger (
    doc_id text, a text, a_unit integer, b text, b_unit integer, verdict text, how text,
    evidence text);
create table candidate (
    doc_id text, a text, a_unit integer, b text, b_unit integer, round integer, tier real,
    reason text, name_score real, cooc_score real, combined real);
create table completion (doc_id text primary key, row text);

-- the global layer (filled by threadatlas.attach)
create table parent (
    parent_id integer primary key, name text, kind text, aliases text, summary text,
    version integer, founded_by text);
create table instance_of (
    doc_id text, node_id text, parent_id integer, pass integer, reason text, scores text,
    primary key (doc_id, node_id));
create table offer (
    doc_id text, node_id text, parent_id integer, parent_version integer, pass integer,
    lexical real, vector real, cast real, cast_rare real, identity integer, offered integer,
    verdict text, reason text);
create table leaf (doc_id text, node_id text, why text, primary key (doc_id, node_id));

-- the embedding sidecar's map (filled by threadatlas.embed)
create table vec_header (model text, dimension integer, built_at text);
create table vec_row (
    row integer primary key, record text, doc_id text, record_id text, ordinal integer, text text);
"""

FTS = """
create virtual table abstract_fts using fts5(text, content='abstract', content_rowid='rowid');
create virtual table cell_fts using fts5(text, content='cell', content_rowid='rowid');
create virtual table fact_fts using fts5(quote, content='fact', content_rowid='rowid');
insert into abstract_fts(abstract_fts) values ('rebuild');
insert into cell_fts(cell_fts) values ('rebuild');
insert into fact_fts(fact_fts) values ('rebuild');
"""


def rows(path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def dump(value):
    return None if value is None else json.dumps(value, ensure_ascii=False)


def load_texts(step0_documents, wanted):
    texts = {}
    for d in rows(step0_documents):
        if d["doc_id"] in wanted:
            texts[d["doc_id"]] = d["text"]
    return texts


def build(step1, step0_documents, out):
    if out.exists():
        out.unlink()
    db = sqlite3.connect(out)
    db.executescript(SCHEMA)

    docs = list(rows(step1 / "documents.jsonl"))
    texts = load_texts(step0_documents, {d["doc_id"] for d in docs})
    missing = [d["doc_id"] for d in docs if d["doc_id"] not in texts]
    if missing:
        sys.exit(f"{len(missing)} documents have no text in the Step 0 file, first {missing[0]}")
    for d in docs:
        db.execute("insert into document values (?,?,?,?,?,?,?,?,?,?,?)",
                   (d["doc_id"], d["source_uri"], d["sha256"], d["title"], d["author"],
                    d["source_class"], d["occurred_at"], d["ingested_at"], d["loader"],
                    dump(d["flags"]), texts[d["doc_id"]]))

    for u in rows(step1 / "units.jsonl"):
        db.execute("insert into unit values (?,?,?,?,?,?,?,?)",
                   (u["unit_id"], u["doc_id"], u["position"], u["label"], u.get("kind"),
                    u["start"], u["end"], u["occurred_at"]))
    for p in rows(step1 / "pieces.jsonl"):
        db.execute("insert into piece values (?,?,?,?,?,?,?,?)",
                   (p["doc_id"], p["unit_id"], p["position"], p["kind"], p["start"], p["end"],
                    p["author"], p["occurred_at"]))
    for n in rows(step1 / "nodes.jsonl"):
        db.execute("insert into node values (?,?,?,?,?,?)",
                   (n["doc_id"], n["node_id"], n["name"], n["kind"], n["created_from_unit"],
                    dump(n["provenance"])))
    for a in rows(step1 / "aliases.jsonl"):
        db.execute("insert into alias values (?,?,?,?)",
                   (a["doc_id"], a["alias"], a["node_id"], a["first_seen_unit"]))
    for e in rows(step1 / "edges.jsonl"):
        db.execute("insert into edge values (?,?,?,?,?,?)",
                   (e["doc_id"], e["predicate"], e["subject"], e["object"], dump(e.get("units")),
                    e.get("position")))

    checked, unquoted = 0, 0
    for f in rows(step1 / "facts.jsonl"):
        if f["quote"] is None:                 # a document fact from the export (1.8): no quote by rule
            unquoted += 1
        else:
            text = texts[f["doc_id"]]
            if text[f["quote_start"]:f["quote_end"]] != f["quote"]:
                sys.exit(f"quote of {f['fact_id']} in {f['doc_id'][:8]} does not slice to its text; load refused")
            checked += 1
        db.execute("insert into fact values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (f["doc_id"], f["fact_id"], f["subject"], f["predicate"], f["object"],
                    int(f["object_is_node"]), f["direction"], f["qualifiers"], f["rank"],
                    f["unit_id"], f["quote"], f["quote_start"], f["quote_end"], f["valid_from"],
                    f["occurred_at"], f["tier"], f["author"], dump(f["provenance"])))

    for c in rows(step1 / "cells.jsonl"):
        db.execute("insert into cell values (?,?,?,?,?,?)",
                   (c["doc_id"], c["node_id"], c["unit_id"], c["text"], c["tier"], dump(c["provenance"])))
    for a in rows(step1 / "abstracts.jsonl"):
        db.execute("insert into abstract values (?,?,?,?,?)",
                   (a["doc_id"], a["node_id"], a["text"], a["tier"], a["updated_at"]))
    for a in rows(step1 / "adjudicated_facts.jsonl"):
        db.execute("insert into adjudicated_fact values (?,?,?,?,?,?,?)",
                   (a["doc_id"], a["node_id"], a["predicate"], a["object"], a["qualifiers"],
                    dump(a["from_facts"]), a["tier"]))
    for a in rows(step1 / "attributes.jsonl"):
        db.execute("insert into attribute values (?,?,?,?,?,?)",
                   (a["doc_id"], a["node_id"], a["attribute"], a["value"], dump(a["from_facts"]), a["tier"]))
    for c in rows(step1 / "contradictions.jsonl"):
        db.execute("insert into contradiction values (?,?,?,?,?,?)",
                   (c["doc_id"], c["node_id"], c["note"], dump(c["from_facts"]), c["holds"], c["because"]))
    for r in rows(step1 / "rejections.jsonl"):
        db.execute("insert into rejection values (?,?,?,?,?)",
                   (r["doc_id"], r["stage"], r.get("unit_id"), r["category"], dump(r)))
    for l in rows(step1 / "ledger.jsonl"):
        db.execute("insert into ledger values (?,?,?,?,?,?,?,?)",
                   (l["doc_id"], l["a"], l["a_unit"], l["b"], l["b_unit"], l["verdict"], l["how"], l["evidence"]))
    for c in rows(step1 / "candidates.jsonl"):
        db.execute("insert into candidate values (?,?,?,?,?,?,?,?,?,?,?)",
                   (c["doc_id"], c["a"], c["a_unit"], c["b"], c["b_unit"], c["round"], c["tier"],
                    c["reason"], c["name_score"], c["cooc_score"], c["combined"]))
    for c in rows(step1 / "completions.jsonl"):
        db.execute("insert into completion values (?,?)", (c["doc_id"], dump(c)))
    db.commit()

    try:
        db.executescript(FTS)
        fts = "built"
    except sqlite3.OperationalError as e:
        fts = f"not built ({e}); the plain scorer serves keyword search"
    db.commit()

    print(f"documents {len(docs)}, quotes checked {checked}, all slice to their text; {unquoted} document facts without a quote; FTS5 {fts}")
    off = []
    for doc_id, row in db.execute("select doc_id, row from completion"):
        counts = json.loads(row)["counts"]
        have = db.execute("select count(*) from fact where doc_id = ? and quote is not null", (doc_id,)).fetchone()[0]
        if have != counts["facts_stored"]:
            off.append((doc_id[:8], have, counts["facts_stored"]))
        have = db.execute("select count(*) from cell where doc_id = ?", (doc_id,)).fetchone()[0]
        if have != counts["cells"]:
            off.append((doc_id[:8], have, counts["cells"]))
    if off:
        print(f"counts differ from the completion records in {len(off)} places: {off[:5]}")
    else:
        print("facts and cells per document equal the completion records")
    for table in ("document", "unit", "node", "alias", "edge", "fact", "cell", "abstract"):
        print(f"  {table:12} {db.execute(f'select count(*) from {table}').fetchone()[0]:7}")
    db.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
