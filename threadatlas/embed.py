"""The embedding sidecar: one float16 .npy beside the store, its row map inside the store.

    python -m threadatlas.embed <store.sqlite>

Rows, in this order: one per fact, rendered as a line (subject, predicate, object, qualifiers,
date, document); one per sentence of every cell and abstract, prefixed with the entity's name
and, when the document's title is a title and not an identifier, the title; one per sentence of
every parent summary (none until the attach step runs; re-run this after it). The model is
bge-small-en-v1.5 through fastembed (384 dimensions, ONNX, CPU, fetched once). The row map
(`vec_row`) and the header (`vec_header`) are written in one transaction after the array is
written, so a crash leaves either both or neither; `load(store)` verifies the header and the row
count against the array and refuses a mismatch, which is the signal to rebuild.
"""
import datetime
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy

MODEL = "BAAI/bge-small-en-v1.5"
DIMENSION = 384
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


def sentences(text):
    parts = SENTENCE.split(text.strip())
    return [p for p in parts if p.strip()]


def is_identifier(title, source_uri):
    return title is None or title == Path(source_uri).stem


def render_fact(f, names, doc):
    subject = names.get(f["subject"], f["subject"])
    if f["direction"] == "mentioned" and f["subject_name"]:
        subject = f["subject_name"]                    # a chat minor's fact, carried by the session
    obj = names.get(f["object"], f["object"]) if f["object_is_node"] else f["object"]
    line = f"{subject} {f['predicate'].replace('_', ' ')} {obj}"
    if f["qualifiers"]:
        line += f" ({f['qualifiers']})"
    if f["occurred_at"]:
        line += f", {f['occurred_at']}"
    if not is_identifier(doc["title"], doc["source_uri"]):
        line += f", {doc['title']}"
    return line


def prefix(entity_name, doc):
    if is_identifier(doc["title"], doc["source_uri"]):
        return f"{entity_name}: "
    return f"{entity_name}, {doc['title']}: "


def texts(db):
    """Yield (record, doc_id, record_id, ordinal, text) in row order."""
    docs = {}
    for row in db.execute("select doc_id, title, source_uri from document"):
        docs[row[0]] = {"title": row[1], "source_uri": row[2]}
    names = {}
    for doc_id, node_id, name in db.execute("select doc_id, node_id, name from node"):
        names[(doc_id, node_id)] = name

    cols = ["doc_id", "fact_id", "subject", "predicate", "object", "object_is_node", "qualifiers", "occurred_at", "direction", "provenance"]
    for row in db.execute("select " + ", ".join(cols) + " from fact order by doc_id, fact_id"):
        f = dict(zip(cols, row))
        f["subject_name"] = json.loads(f["provenance"] or "{}").get("subject_name")
        local = {f["subject"]: names.get((f["doc_id"], f["subject"]), f["subject"]),
                 f["object"]: names.get((f["doc_id"], f["object"]), f["object"])}
        yield ("fact", f["doc_id"], f["fact_id"], 0, render_fact(f, local, docs[f["doc_id"]]))

    for doc_id, node_id, unit_id, text in db.execute("select doc_id, node_id, unit_id, text from cell order by rowid"):
        name = names.get((doc_id, node_id), node_id)
        for i, s in enumerate(sentences(text)):
            yield ("cell", doc_id, f"{node_id}@{unit_id}", i, prefix(name, docs[doc_id]) + s)

    for doc_id, node_id, text in db.execute("select doc_id, node_id, text from abstract order by rowid"):
        name = names.get((doc_id, node_id), node_id)
        for i, s in enumerate(sentences(text)):
            yield ("abstract", doc_id, node_id, i, prefix(name, docs[doc_id]) + s)

    for parent_id, name, summary in db.execute("select parent_id, name, summary from parent order by parent_id"):
        for i, s in enumerate(sentences(summary or "")):
            yield ("parent", None, str(parent_id), i, f"{name}: " + s)


def build(store):
    from fastembed import TextEmbedding
    db = sqlite3.connect(store)
    rows = list(texts(db))
    print(f"{len(rows)} texts to embed")
    model = TextEmbedding(MODEL)
    vectors = numpy.zeros((len(rows), DIMENSION), dtype=numpy.float16)
    batch = 256
    for start in range(0, len(rows), batch):
        chunk = [r[4] for r in rows[start:start + batch]]
        for i, v in enumerate(model.embed(chunk, batch_size=batch)):
            vectors[start + i] = v.astype(numpy.float16)
        if (start // batch) % 20 == 0:
            print(f"  {start + len(chunk)} / {len(rows)}")
    array = store.with_suffix(".npy")
    numpy.save(array, vectors)

    db.execute("begin")
    db.execute("delete from vec_row")
    db.execute("delete from vec_header")
    db.executemany("insert into vec_row values (?,?,?,?,?,?)",
                   [(i, r[0], r[1], r[2], r[3], r[4]) for i, r in enumerate(rows)])
    db.execute("insert into vec_header values (?,?,?)",
               (MODEL, DIMENSION, datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")))
    db.commit()
    kinds = {}
    for r in rows:
        kinds[r[0]] = kinds.get(r[0], 0) + 1
    print(f"wrote {array.name}: {vectors.shape}, float16; rows by record: {kinds}")
    db.close()


def load(store):
    """The array and its map, verified; the caller rebuilds on a mismatch."""
    db = sqlite3.connect(store)
    header = db.execute("select model, dimension, built_at from vec_header").fetchone()
    if header is None:
        sys.exit("no sidecar header in the store; run threadatlas.embed")
    array = numpy.load(store.with_suffix(".npy"), mmap_mode="r")
    n = db.execute("select count(*) from vec_row").fetchone()[0]
    if header[0] != MODEL or header[1] != DIMENSION or array.shape != (n, DIMENSION):
        sys.exit(f"sidecar mismatch: header {header}, array {array.shape}, rows {n}; rebuild with threadatlas.embed")
    return db, array


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(Path(sys.argv[1]))
