# %% [markdown]
# # ThreadAtlas global layer
#
# The store, the embedding sidecar and the parents over a Step 1 dataset (`docs/global-layer.md`).
# Attach `it494-threadatlas-step1` and `it494-threadatlas-step0`, add an `OPENAI_API_KEY`
# secret, turn Internet on (fastembed fetches its model once), and run all. Outputs in
# `/kaggle/working`: `threadatlas.sqlite`, `threadatlas.npy`, `attach-calls.jsonl`.
#
# Generated from `threadatlas/*.py` by `scripts/build_global_layer_notebook.py`; edit the
# modules, not this file.

# %%
import subprocess, sys
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "fastembed"], check=True)
import os
if not os.environ.get("OPENAI_API_KEY"):
    try:
        from kaggle_secrets import UserSecretsClient
        os.environ["OPENAI_API_KEY"] = UserSecretsClient().get_secret("OPENAI_API_KEY")
    except Exception:
        print("no OPENAI_API_KEY secret attached: the store and the sidecar will build, the attach step will not")

# %% [markdown]
# ## threadatlas/model.py

# %%
"""The one model interface: generate(prompt, schema, stage) -> dict, priced and logged.

The ingestor's block 2, trimmed: raw HTTP to chat completions, JSON replies, one retry when a
reply does not fit its shape, three retries on a timeout, a 429 or a 5xx. Every call is appended
to a calls log beside the store with its model, tier, tokens, seconds and cost. The key comes
from the OPENAI_API_KEY environment variable and nowhere else.
"""
import http.client
import json
import os
import time
import urllib.error
import urllib.request

LUNA = "gpt-5.6-luna"
TERRA = "gpt-5.6-terra"
SERVICE_TIER = "flex"
PRICE = {"flex": {LUNA: (0.10, 0.60), TERRA: (1.00, 6.00)},
         "default": {LUNA: (0.20, 1.20), TERRA: (2.00, 12.00)}}
KEY = os.environ.get("OPENAI_API_KEY")
LOG_PATH = None
SPENT = 0.0
SPEND_STOP = float(os.environ.get("SPEND_STOP", "10"))


class SchemaError(Exception):
    pass


class SpendStop(Exception):
    pass


def check_schema(reply, schema):
    """`schema` maps a required key to a type (or a tuple of types); extra keys are allowed."""
    if not isinstance(reply, dict):
        raise SchemaError("reply is not an object")
    for key, kind in schema.items():
        if key not in reply:
            raise SchemaError(f"missing {key}")
        if kind is not None and not isinstance(reply[key], kind):
            raise SchemaError(f"{key} is not {kind}")


def log_call(row):
    global SPENT
    SPENT += row.get("cost", 0.0)
    if LOG_PATH:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        return resp.status, resp.read().decode("utf-8")


def call(payload, model, stage, ctx, prompt_chars):
    if not KEY:
        raise RuntimeError("no OPENAI_API_KEY in the environment")
    if SPENT >= SPEND_STOP:
        raise SpendStop(f"spending stop: ${SPENT:.2f} of ${SPEND_STOP:.2f}")
    price_in, price_out = PRICE[SERVICE_TIER][model]
    started = time.time()
    for attempt in range(3):
        try:
            status, text = post("https://api.openai.com/v1/chat/completions", payload)
        except urllib.error.HTTPError as error:
            status, text = error.code, error.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            log_call({"stage": stage, "model": model, "in": prompt_chars // 4, "out": 0,
                      "seconds": round(time.time() - started, 1),
                      "cost": prompt_chars // 4 * price_in / 1e6, "timeout": True, **ctx})
            if attempt == 2:
                raise
            time.sleep(15 * (attempt + 1))
            continue
        if status == 429 and "insufficient_quota" in text:
            raise SpendStop(f"OpenAI quota exhausted: {text[:200]}")
        if status == 429 or status >= 500:
            if attempt == 2:
                raise RuntimeError(f"OpenAI {status}: {text}")
            time.sleep(15 * (attempt + 1))
            continue
        if status != 200:
            raise RuntimeError(f"OpenAI {status}: {text}")
        break
    body = json.loads(text)
    tier = body.get("service_tier") or SERVICE_TIER
    price_in, price_out = PRICE.get(tier, PRICE["default"])[model]
    usage = body.get("usage", {})
    tokens_in, tokens_out = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    log_call({"stage": stage, "model": body.get("model", model), "tier": tier, "in": tokens_in,
              "out": tokens_out, "seconds": round(time.time() - started, 1),
              "cost": (tokens_in * price_in + tokens_out * price_out) / 1e6, **ctx})
    return body


def generate(prompt, schema, stage, model=LUNA, effort="low", ctx=None):
    """The reply as a dict that fits `schema`, or None after one retry with the error appended."""
    ctx = ctx or {}
    for attempt in range(2):
        body = call({"model": model, "reasoning_effort": effort, "service_tier": SERVICE_TIER,
                     "response_format": {"type": "json_object"},
                     "messages": [{"role": "user", "content": prompt}]},
                    model, stage, ctx, len(prompt))
        try:
            message = body["choices"][0]["message"]
            if not message.get("content"):
                raise SchemaError("empty reply")
            reply = json.loads(message["content"])
            check_schema(reply, schema)
            return reply
        except (SchemaError, ValueError, TypeError, KeyError, IndexError) as e:
            log_call({"stage": stage, "model": model, "schema_miss": f"{type(e).__name__}: {e}"[:200], "cost": 0.0, **ctx})
            prompt += f"\n\nYour previous reply did not fit the required shape ({type(e).__name__}: {e}). Reply again, in exactly the shape asked for."
    return None

# %% [markdown]
# ## threadatlas/embed.py

# %%
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


def build_sidecar(store):
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

# %% [markdown]
# ## threadatlas/store.py

# %%
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

# %% [markdown]
# ## threadatlas/attach.py

# %%
import sys
llm = sys.modules[__name__]
"""The global layer: parents and up-edges over the store (docs/global-layer.md).

    python -m threadatlas.attach <store.sqlite> [signals]

`signals` is the arm: a comma-joined subset of lexical,vector,cast,identity (default all four).
Only the named signals may put a parent over the offer floor; every score is logged regardless,
so the log replays under any arm.

Documents are taken by date then source_uri, undated last; within a document, children by
first unit (a chat's salience is decided at Step 1 since ingestor 1.8). Each child is
offered the parents over the floor (at most K, by vector similarity) and the judge rules
attach or not on texts alone; a child with nothing offered founds a parent as a copy of itself.
An attach rewrites the parent (name, kind, one summary line for this document) in one call and
refreshes its vector. Two children of one document are never offered to each other; both may
land under one parent. After every document, a second pass re-offers every founder once. The
parent, instance_of, offer and leaf tables are rewritten from scratch each run; run
threadatlas.embed afterwards so the parents' summaries join the sidecar.
"""
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

import numpy


K = 5                    # parents offered to the judge at most
VECTOR_FLOOR = 0.80      # cosine over bge-small; tuned on the test packages, log carries the rest
BELOW_FLOOR_LOGGED = 3   # candidates under the floor logged per child, so the floor can be tuned
FACTS_SHOWN = 12         # facts of a child shown to the judge and the rewrite
WORD = re.compile(r"[a-z0-9]+")


def first_year(date):
    if not date:
        return 10 ** 9
    head = date.split("/")[0].rstrip("~")
    m = re.match(r"-?\d{4}", head)
    return int(m.group(0)) if m else 10 ** 9


def fold(s):
    return " ".join(WORD.findall((s or "").casefold()))


# ---------------------------------------------------------------- the store, read once

class Corpus:
    def __init__(self, db):
        self.db = db
        self.docs = {}
        for row in db.execute("select doc_id, title, source_uri, occurred_at from document"):
            self.docs[row[0]] = {"title": row[1], "source_uri": row[2], "occurred_at": row[3]}
        self.unit_kind = {}
        for unit_id, doc_id, kind, position in db.execute("select unit_id, doc_id, kind, position from unit"):
            self.unit_kind[unit_id] = (kind, position)
        self.nodes = {}
        for doc_id, node_id, name, kind, created in db.execute("select doc_id, node_id, name, kind, created_from_unit from node"):
            self.nodes[(doc_id, node_id)] = {"name": name, "kind": kind, "first_unit": self.unit_kind.get(created, ("", 0))[1],
                                             "aliases": [], "facts": [], "abstract": None, "cast": set(), "identity": set()}
        for doc_id, alias, node_id in db.execute("select doc_id, alias, node_id from alias"):
            if (doc_id, node_id) in self.nodes:
                self.nodes[(doc_id, node_id)]["aliases"].append(alias)
        for doc_id, node_id, text in db.execute("select doc_id, node_id, text from abstract"):
            if (doc_id, node_id) in self.nodes:
                self.nodes[(doc_id, node_id)]["abstract"] = text
        for doc_id, subject, predicate, obj, is_node, qualifiers, date in db.execute(
                "select doc_id, subject, predicate, object, object_is_node, qualifiers, occurred_at from fact order by doc_id, fact_id"):
            node = self.nodes.get((doc_id, subject))
            if node is None:
                continue
            value = self.nodes[(doc_id, obj)]["name"] if is_node and (doc_id, obj) in self.nodes else obj
            node["facts"].append(f"{predicate.replace('_', ' ')} {value}" + (f" ({qualifiers})" if qualifiers else ""))
            # the ingestor's own link: an is_a fact whose object is another node of the document
            if is_node and predicate == "is_a" and (doc_id, obj) in self.nodes:
                node["identity"].add(obj)
                self.nodes[(doc_id, obj)]["identity"].add(subject)
        # the cast: names sharing a unit, from the appears_in edges
        by_unit = {}
        for doc_id, subject, units in self.db.execute("select doc_id, subject, units from edge where predicate = 'appears_in'"):
            if (doc_id, subject) not in self.nodes:
                continue
            for u in json.loads(units or "[]"):
                by_unit.setdefault((doc_id, u), []).append(subject)
        for (doc_id, u), members in by_unit.items():
            for a in members:
                for b in members:
                    if a != b:
                        self.nodes[(doc_id, a)]["cast"].add(fold(self.nodes[(doc_id, b)]["name"]))
        # rarity of a cast name over the loaded documents
        docs_with = {}
        for (doc_id, node_id), node in self.nodes.items():
            docs_with.setdefault(fold(node["name"]), set()).add(doc_id)
        n = len(self.docs)
        self.rarity = {name: math.log(n / (1 + len(ds))) for name, ds in docs_with.items()}

    def is_chat(self, doc_id):
        row = self.db.execute("select kind from unit where doc_id = ? limit 1", (doc_id,)).fetchone()
        return row is not None and row[0] in ("user", "assistant")

    def ordered_docs(self):
        def key(doc_id):
            return (first_year(self.docs[doc_id]["occurred_at"]), self.docs[doc_id]["source_uri"])
        return sorted(self.docs, key=key)

    def children(self, doc_id):
        out = [(node_id, node) for (d, node_id), node in self.nodes.items() if d == doc_id]
        out = [(nid, n) for nid, n in out if not nid.endswith(":doc") and fold(n["name"]) != "user"]
        out.sort(key=lambda_free_key)
        return out


def lambda_free_key(item):
    return (item[1]["first_unit"], item[0])


def child_text(node, doc):
    lines = [f"name: {node['name']}", f"kind: {node['kind']}"]
    aliases = [a for a in node["aliases"] if a != node["name"]]
    if aliases:
        lines.append("also called: " + "; ".join(aliases[:15]))
    if not is_identifier(doc["title"], doc["source_uri"]):
        lines.append(f"document: {doc['title']}")
    if node["abstract"]:
        lines.append("summary: " + node["abstract"])
    elif node["facts"]:
        lines.append("facts: " + "; ".join(node["facts"][:FACTS_SHOWN]))
    return "\n".join(lines)


# ---------------------------------------------------------------- parents in memory

class Parents:
    def __init__(self):
        self.rows = []                                     # dicts: name, kind, aliases, summary(list of (child key, line)), version, children, cast
        self.vecs = numpy.zeros((0, DIMENSION), dtype=numpy.float32)
        self.alive = []

    def add(self, name, kind, aliases, summary, vec, child):
        self.rows.append({"name": name, "kind": kind, "aliases": set(aliases), "summary": summary,
                          "version": 1, "children": [child], "cast": set()})
        self.vecs = numpy.vstack([self.vecs, vec[None, :]])
        self.alive.append(True)
        return len(self.rows) - 1

    def text(self, i):
        p = self.rows[i]
        return f"name: {p['name']}\nkind: {p['kind']}\nalso called: {'; '.join(sorted(p['aliases'])[:20])}\n" + \
               "\n".join(line for (_, line) in p["summary"])


def cosine(vec, mat):
    return mat @ vec


def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def rare_jaccard(a, b, rarity):
    keys = a | b
    if not keys:
        return 0.0
    both = sum(rarity.get(k, 0.0) for k in a & b)
    either = sum(rarity.get(k, 0.0) for k in keys)
    return both / either if either else 0.0


# ---------------------------------------------------------------- the prompts (rules only)

JUDGE ="""You are deciding whether an entity found in one document is an instance of a global entity that other
documents have already established, or something else with a similar name. Both are described only by
what their documents say. Attach when the two descriptions are of the same person, place, thing or
concept, even under different names, spellings or roles, and even when one document knows it under a
name the other never uses. Keep apart when they are different things that share a name or a word, or
when nothing in the descriptions connects them. A disagreement in kind or role is not by itself a reason
to keep apart; a contradiction in identity is.

The entity from its document:
{child}
Appears beside: {child_cast}

The candidates, numbered:
{parents}

Reply with a JSON object: {{"attach": <candidate number or null>, "reason": "<one sentence>"}}."""

REWRITE = """A global entity is described by the instances of it that documents hold. It has just gained a new
instance. Rewrite its name and kind from all its instances, and write one line saying what part the new
instance played in its document. The name must be one the instances actually use (a name or an alias
listed below), the one a reader would look for first. The kind is one or two words. The line must say
only what the new instance's description says, in the third person, naming the document.

The global entity as it stands:
{parent}

The new instance:
{child}

Reply with a JSON object: {{"name": "<name>", "kind": "<kind>", "line": "<one sentence>"}}."""


# ---------------------------------------------------------------- the build

def run(store, signals):
    db = sqlite3.connect(store)
    llm.LOG_PATH = store.with_name("attach-calls.jsonl")
    from fastembed import TextEmbedding
    embedder = TextEmbedding(MODEL)
    corpus = Corpus(db)
    parents = Parents()
    edges = {}                          # (doc_id, node_id) -> parent index
    leaves = []
    offers = []
    order = corpus.ordered_docs()
    print(f"{len(order)} documents, {len(corpus.nodes)} nodes; signals {sorted(signals)}")

    def embed_one(text):
        return numpy.asarray(list(embedder.embed([text]))[0], dtype=numpy.float32)

    def offer(doc_id, node_id, node, vec, pass_no, exclude):
        """Score every live parent; return the offered indexes and log the rows."""
        if not parents.rows:
            return []
        sims = cosine(vec, parents.vecs)
        rows = []
        child_names = {fold(node["name"])} | {fold(a) for a in node["aliases"]}
        text_folded = fold(child_text(node, corpus.docs[doc_id]))
        for i, p in enumerate(parents.rows):
            if not parents.alive[i] or i in exclude:
                continue
            pnames = {fold(p["name"])} | {fold(a) for a in p["aliases"]}
            lexical = 1.0 if child_names & pnames else (0.5 if any(n and n in text_folded for n in pnames) else 0.0)
            vector = float(sims[i])
            cast = jaccard(node["cast"], p["cast"])
            cast_rare = rare_jaccard(node["cast"], p["cast"], corpus.rarity)
            identity = int(any(c[0] == doc_id and c[1] in node["identity"] for c in p["children"]))
            over = (("lexical" in signals and lexical > 0) or ("vector" in signals and vector >= VECTOR_FLOOR)
                    or ("identity" in signals and identity))
            rows.append((over, vector, i, lexical, cast, cast_rare, identity))
        rows.sort(key=offer_sort)
        offered = [r for r in rows if r[0]][:K]
        below = [r for r in rows if not r[0]][:BELOW_FLOOR_LOGGED]
        for over, vector, i, lexical, cast, cast_rare, identity in offered + below:
            offers.append({"doc_id": doc_id, "node_id": node_id, "parent": i, "parent_version": parents.rows[i]["version"],
                           "pass": pass_no, "lexical": lexical, "vector": vector, "cast": cast, "cast_rare": cast_rare,
                           "identity": identity, "offered": int(over), "verdict": None, "reason": None})
        return [r[2] for r in offered]

    def judge(doc_id, node_id, node, offered, pass_no):
        doc = corpus.docs[doc_id]
        # the cast arm: co-occurrence reaches the judge as names, or not at all
        def cast_line(names):
            return ", ".join(sorted(names)[:25]) if "cast" in signals else "(not shown)"
        listing = "\n".join(f"[{n + 1}]\n{parents.text(i)}\nAppears beside: {cast_line(parents.rows[i]['cast'])}\n"
                            for n, i in enumerate(offered))
        prompt = JUDGE.format(child=child_text(node, doc), child_cast=cast_line(node["cast"]), parents=listing)
        tier = llm.LUNA if corpus.is_chat(doc_id) else llm.TERRA
        reply = llm.generate(prompt, {"attach": None, "reason": str}, "judge", model=tier, effort="medium",
                             ctx={"doc": doc_id[:8], "node": node_id, "pass": pass_no})
        choice = reply.get("attach") if reply else None
        if isinstance(choice, str) and choice.strip().isdigit():
            choice = int(choice)
        picked = offered[choice - 1] if isinstance(choice, int) and 1 <= choice <= len(offered) else None
        for o in offers:
            if o["doc_id"] == doc_id and o["node_id"] == node_id and o["pass"] == pass_no and o["offered"]:
                o["verdict"] = "attach" if o["parent"] == picked else "apart"
                o["reason"] = reply.get("reason") if reply else "no reply"
        return picked

    def found(doc_id, node_id, node, vec):
        doc = corpus.docs[doc_id]
        summary = [((doc_id, node_id), f"In {doc['title']}: " + (node["abstract"] or "; ".join(node["facts"][:FACTS_SHOWN]) or node["name"]))]
        i = parents.add(node["name"], node["kind"], [node["name"]] + node["aliases"], summary, vec, (doc_id, node_id))
        parents.rows[i]["cast"] = set(node["cast"])
        edges[(doc_id, node_id)] = i
        return i

    def attach(doc_id, node_id, node, i):
        p = parents.rows[i]
        doc = corpus.docs[doc_id]
        prompt = REWRITE.format(parent=parents.text(i), child=child_text(node, doc) + f"\ndocument: {doc['title']}")
        reply = llm.generate(prompt, {"name": str, "kind": str, "line": str}, "rewrite", model=llm.LUNA, effort="low",
                             ctx={"doc": doc_id[:8], "node": node_id, "parent": i})
        p["children"].append((doc_id, node_id))
        p["aliases"] |= {node["name"], *node["aliases"]}
        p["cast"] |= node["cast"]
        allowed = {fold(a) for a in p["aliases"]}
        if reply and fold(reply["name"]) in allowed:
            p["name"] = reply["name"]
        if reply and reply.get("kind"):
            p["kind"] = reply["kind"]
        line = reply["line"] if reply and reply.get("line") else f"In {doc['title']}: {node['name']}."
        p["summary"].append(((doc_id, node_id), line))
        p["version"] += 1
        parents.vecs[i] = embed_one(parents.text(i))
        edges[(doc_id, node_id)] = i

    def place(doc_id, node_id, node, vec, pass_no, exclude):
        offered = offer(doc_id, node_id, node, vec, pass_no, exclude)
        picked = judge(doc_id, node_id, node, offered, pass_no) if offered else None
        if picked is None:
            return None
        attach(doc_id, node_id, node, picked)
        return picked

    # pass 1
    for n, doc_id in enumerate(order):
        doc = corpus.docs[doc_id]
        children = corpus.children(doc_id)
        # a chat's salience is decided at Step 1 since ingestor 1.8: its minors have no node here
        # children with identity links go after the others (they may point at a sibling not yet placed)
        children.sort(key=identity_last)
        placed_here = set()
        for node_id, node in children:
            vec = embed_one(child_text(node, doc))
            picked = place(doc_id, node_id, node, vec, 1, exclude=set())
            if picked is None:
                picked = found(doc_id, node_id, node, vec)
            placed_here.add(picked)
        print(f"  [{n + 1}/{len(order)}] {doc['title'][:40]:40} children {len(children):3}  parents {sum(parents.alive):5}  spent ${llm.SPENT:.2f}")

    # pass 2: every founder still alone is offered the full set once
    founders = [(key, i) for key, i in edges.items() if len(parents.rows[i]["children"]) == 1]
    print(f"pass 2 over {len(founders)} founders")
    moved = 0
    for (doc_id, node_id), i in founders:
        node = corpus.nodes[(doc_id, node_id)]
        vec = embed_one(child_text(node, corpus.docs[doc_id]))
        picked = place(doc_id, node_id, node, vec, 2, exclude={i})
        if picked is not None:
            parents.alive[i] = False
            moved += 1
    print(f"pass 2 moved {moved}; parents {sum(parents.alive)}; spent ${llm.SPENT:.2f}")

    # write
    db.execute("delete from parent"); db.execute("delete from instance_of"); db.execute("delete from offer"); db.execute("delete from leaf")
    for i, p in enumerate(parents.rows):
        if not parents.alive[i]:
            continue
        summary = "\n".join(f"[{d[:8]}:{nid}] {line}" for ((d, nid), line) in p["summary"])
        db.execute("insert into parent values (?,?,?,?,?,?,?)",
                   (i, p["name"], p["kind"], json.dumps(sorted(p["aliases"]), ensure_ascii=False), summary, p["version"],
                    f"{p['children'][0][0][:8]}:{p['children'][0][1]}"))
    for (doc_id, node_id), i in edges.items():
        last = [o for o in offers if o["doc_id"] == doc_id and o["node_id"] == node_id and o["parent"] == i and o["verdict"] == "attach"]
        reason = last[-1]["reason"] if last else "founded"
        scores = {k: last[-1][k] for k in ("lexical", "vector", "cast", "cast_rare", "identity")} if last else None
        db.execute("insert into instance_of values (?,?,?,?,?,?)",
                   (doc_id, node_id, i, last[-1]["pass"] if last else 1, reason, json.dumps(scores)))
    for o in offers:
        db.execute("insert into offer values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (o["doc_id"], o["node_id"], o["parent"], o["parent_version"], o["pass"], o["lexical"], o["vector"],
                    o["cast"], o["cast_rare"], o["identity"], o["offered"], o["verdict"], o["reason"]))
    db.executemany("insert into leaf values (?,?,?)", leaves)
    db.commit()
    multi = sum(1 for i, p in enumerate(parents.rows) if parents.alive[i] and len(p["children"]) > 1)
    print(f"written: {sum(parents.alive)} parents ({multi} with two or more children), {len(edges)} up-edges, "
          f"{len(offers)} offer rows, {len(leaves)} leaves; ${llm.SPENT:.2f}")
    db.close()


def offer_sort(row):
    return (not row[0], -row[1])


def identity_last(item):
    return (1 if item[1]["identity"] else 0, item[1]["first_unit"], item[0])

# %%
# Run: the store, the sidecar, the parents, the sidecar again with the parents' summaries.
from pathlib import Path
STEP1 = Path("/kaggle/input/it494-threadatlas-step1")
STEP0 = Path("/kaggle/input/it494-threadatlas-step0/documents.jsonl")
STORE = Path("/kaggle/working/threadatlas.sqlite")
SIGNALS = {"lexical", "vector", "cast", "identity"}     # the arm; drop names to run an ablation arm

build(STEP1, STEP0, STORE)
build_sidecar(STORE)
if os.environ.get("OPENAI_API_KEY"):
    KEY = os.environ["OPENAI_API_KEY"]
    run(STORE, SIGNALS)
    build_sidecar(STORE)
