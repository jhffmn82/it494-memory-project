# %% [markdown]
# # ThreadAtlas global layer
#
# From the Step 1 packages to one store: every document's entities, facts, cells and abstracts
# in SQLite, a flat array of sentence vectors beside it, and a **tree of parents** over the
# entities, so that the same person, place or thing in different documents connects while
# every claim stays with the one document that made it. Nothing is merged. A parent asserts
# nothing about the world: it holds a name, a kind, its children's aliases, a role summary of
# one line per instance, and the list of its instances. The design is `docs/global-layer.md`.
#
# ## What comes in
#
# Two public datasets. [ThreadAtlas Step 1](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step1):
# one JSON Lines file per record type (`documents`, `units`, `pieces`, `nodes`, `aliases`,
# `edges`, `facts`, `cells`, `abstracts`, `adjudicated_facts`, `attributes`, `contradictions`,
# `rejections`, `ledger`, `candidates`, `completions`), every row keyed by `doc_id`.
# [ThreadAtlas Step 0](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step0) for the
# documents' text, which Step 1 does not carry; every quote is re-sliced from it at load.
#
# ## What goes out
#
# `threadatlas.sqlite`, `threadatlas.npy`, `calls.jsonl`, `receipt.json` in the output folder.
#
# ## The store
#
# The Step 1 records, one table each with the same fields, plus:
#
# | table | fields | meaning |
# |---|---|---|
# | `parent` | `parent_id`, `name`, `kind`, `aliases`, `summary`, `version`, `founded_by` | a global entity: a name and kind the judge chose from its instances, the union of their aliases, one summary line per instance tagged with the instance's id, how many times it was rewritten, the instance that founded it |
# | `instance_of` | `doc_id`, `node_id`, `parent_id`, `pass`, `reason`, `scores` | the up-edge from a document's entity to its parent, owned by the document: which pass drew it, the judge's reason (or `founded`), and the scores of the offer that won |
# | `offer` | `doc_id`, `node_id`, `parent_id`, `parent_version`, `pass`, `lexical`, `vector`, `cast`, `cast_rare`, `identity`, `offered`, `verdict`, `reason` | every candidate parent scored for a child: the four signals, whether it cleared the floor, and the judge's verdict on it; the attachment replays from this table under any subset of the signals |
# | `vec_header`, `vec_row` | `model`, `dimension`, `built_at`; `row`, `record`, `doc_id`, `record_id`, `ordinal`, `text` | the sidecar's map: what each row of the array is |
#
# FTS5 tables sit over abstracts, cells and fact quotes when the SQLite build has FTS5.
#
# ## The sidecar
#
# One float16 vector per row of `vec_row`: every fact rendered as a line (subject, predicate,
# object, qualifiers, date, document); every sentence of every cell, abstract and parent
# summary, prefixed with its entity and, for a book or paper, its title. `bge-small-en-v1.5`
# through fastembed, 384 dimensions, fetched once. Search is a linear scan of the array.
#
# ## The algorithm
#
# ```
# load        every Step 1 record into the store; a fact's quote must slice from its
#             document's text at its offsets, or the load stops; FTS5 over the text fields
# embed       one vector per fact line and per narrative sentence
# for each document, by date then source_uri (a document arriving out of order attaches the
#   same way, later):
#   for each entity of the document, by first unit, those with an is_a link to a sibling last:
#     score   every live parent: lexical (name or alias match), vector (cosine of the child's
#             text against the parent's), cast (overlap of the names each appears beside),
#             identity (the document says in an is_a fact that this child is one of the
#             parent's children); a parent is OFFERED when a named signal clears its floor;
#             the top K offered and a few below the floor are logged
#     judge   one call over texts only (no scores): attach to one offered parent, or none
#     attach  the parent gains the child, its aliases and its cast; one call rewrites the
#             parent's name and kind (a name no child carries is refused) and writes the line
#             for this document; the parent's vector is refreshed
#     found   a child nothing was offered to, or the judge kept apart, founds a parent as a
#             copy of itself, with no call
# second pass every parent still alone is offered the full set once under the same rule; an
#             attach moves the edge and retires the one-child parent
# embed       the parents' summaries join the sidecar
# ```
#
# Two children of one document are never offered to each other; both may land under the
# same parent. The user of a chat is never a child. Every call is logged with its cost, and
# the run stops at a spending limit.
#
# ## Running it
#
# On Kaggle: attach the two datasets, add an `OPENAI_API_KEY` secret, turn Internet on, run
# all. Without a key the store and the sidecar build and the parents do not. Locally: set
# `STEP1`, `EXPORT` and `OUT` in the environment and run the script; the blocks are the same.

# %% [markdown]
# ## Block 1: files and settings
#
# Where the inputs are (Kaggle's mount, or the environment), where the outputs go, and the
# constants the pipeline turns on. The signals named in `SIGNALS` are the arm: the ones that
# may put a parent in front of the judge. Every signal is logged whatever the arm.

# %%
import json
import math
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = "threadatlas-global-layer 0.1"
KAGGLE_STEP1 = (Path("/kaggle/input/datasets/jhffmn/it494-threadatlas-step1"), Path("/kaggle/input/it494-threadatlas-step1"))
KAGGLE_EXPORT = (Path("/kaggle/input/datasets/jhffmn/it494-threadatlas-step0"), Path("/kaggle/input/it494-threadatlas-step0"))
KAGGLE_OUT, LOCAL_OUT = Path("/kaggle/working"), Path("data/global")

K = 5                      # parents offered to the judge at most, strongest first
VECTOR_FLOOR = 0.85        # cosine over bge-small at which a parent is offered on the vector alone
BELOW_FLOOR_LOGGED = 3     # candidates under the floor logged per child, so the floor can be tuned
FACTS_SHOWN = 12           # facts of a child shown to the judge and the rewrite
SIGNALS = set(os.environ.get("SIGNALS", "lexical,vector,cast,identity").split(","))
SPEND_STOP = float(os.environ.get("SPEND_STOP", "10"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:                                        # the embedder is not on Kaggle's image; fetched once, with Internet on
    import fastembed
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "fastembed"], check=True)


def first_existing(variable, *candidates):
    """The folder the environment names, else the first candidate that exists, else None."""
    if os.environ.get(variable):
        return Path(os.environ[variable])
    return next((p for p in candidates if p.exists()), None)


STEP1 = first_existing("STEP1", *KAGGLE_STEP1)
EXPORT = first_existing("EXPORT", *KAGGLE_EXPORT)
OUT = first_existing("OUT") or (KAGGLE_OUT if KAGGLE_OUT.exists() else LOCAL_OUT)
OUT.mkdir(parents=True, exist_ok=True)
STORE = OUT / "threadatlas.sqlite"
print(f"{VERSION}\nStep 1: {STEP1}\nStep 0: {EXPORT}\noutput: {OUT}\nsignals: {sorted(SIGNALS)}")


def read_jsonl(path):
    """One dict per non-empty line."""
    with Path(path).open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def fold(text):
    """Case-folded words joined by single spaces: the lexical form of a name."""
    return " ".join(re.findall(r"[a-z0-9]+", (text or "").casefold()))


def first_year(date):
    """A Step 0 date's sort key: its first year as a signed integer; undated sorts last."""
    if not date:
        return 10 ** 9
    match = re.match(r"-?\d{4}", date.split("/")[0])
    return int(match.group(0)) if match else 10 ** 9


def is_identifier(title, source_uri):
    """A chat's title is its session id, which is not a title."""
    return title is None or title == Path(source_uri).stem


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

# %% [markdown]
# ## Block 2: the model
#
# `generate(prompt, schema, stage)` is the one way this notebook talks to a model: raw HTTP,
# the key from the `OPENAI_API_KEY` environment variable or the Kaggle secret of that name,
# JSON replies, one retry when a reply does not fit its shape, three on a timeout or a busy
# server. Every call goes to `calls.jsonl` with its model, tier, tokens, seconds and cost, and
# the run stops at `SPEND_STOP` dollars. The same interface as the ingestor's.

# %%
import http.client
import urllib.error
import urllib.request

LUNA = "gpt-5.6-luna"                   # the rewrite, and the judge for chat children
TERRA = "gpt-5.6-terra"                 # the judge for book and paper children
SERVICE_TIER = "flex"
PRICE = {"flex": {LUNA: (0.10, 0.60), TERRA: (1.00, 6.00)},          # $ per million tokens in, out
         "default": {LUNA: (0.20, 1.20), TERRA: (2.00, 12.00)}}
CALLS = OUT / "calls.jsonl"
SPENT = 0.0

KEY = os.environ.get("OPENAI_API_KEY")
if not KEY:
    try:
        from kaggle_secrets import UserSecretsClient
        KEY = UserSecretsClient().get_secret("OPENAI_API_KEY")
    except Exception:
        KEY = None


class SpendStop(Exception):
    pass


def log_call(row):
    global SPENT
    SPENT += row.get("cost", 0.0)
    with CALLS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def post(payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=data, method="POST",
                                     headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=900) as response:
        return response.status, response.read().decode("utf-8")


def call(payload, model, stage, ctx):
    """One exchange under the retry policy; the parsed body. The cost is logged here."""
    if not KEY:
        raise RuntimeError("no OPENAI_API_KEY in the environment or as a Kaggle secret")
    if SPENT >= SPEND_STOP:
        raise SpendStop(f"spending stop: ${SPENT:.2f} of ${SPEND_STOP:.2f}")
    started = time.time()
    for attempt in range(3):
        try:
            status, text = post(payload)
        except urllib.error.HTTPError as error:
            status, text = error.code, error.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
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
    log_call({"stage": stage, "model": body.get("model", model), "tier": tier, "in": tokens_in, "out": tokens_out,
              "seconds": round(time.time() - started, 1), "cost": (tokens_in * price_in + tokens_out * price_out) / 1e6, **ctx})
    return body


def fits(reply, schema):
    """`schema` maps each required key to its type, or None for any."""
    if not isinstance(reply, dict):
        return "reply is not an object"
    for key, kind in schema.items():
        if key not in reply:
            return f"missing {key}"
        if kind is not None and not isinstance(reply[key], kind):
            return f"{key} is not {kind.__name__}"
    return None


def generate(prompt, schema, stage, model=LUNA, effort="low", ctx=None):
    """The reply as a dict that fits `schema`, or None after one retry with the error appended."""
    ctx = ctx or {}
    for attempt in range(2):
        body = call({"model": model, "reasoning_effort": effort, "service_tier": SERVICE_TIER,
                     "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]},
                    model, stage, ctx)
        try:
            reply = json.loads(body["choices"][0]["message"]["content"] or "")
            error = fits(reply, schema)
        except (ValueError, KeyError, IndexError, TypeError) as e:
            error = f"{type(e).__name__}: {e}"
        if error is None:
            return reply
        log_call({"stage": stage, "model": model, "schema_miss": error[:200], "cost": 0.0, **ctx})
        prompt += f"\n\nYour previous reply did not fit the required shape ({error}). Reply again, in exactly the shape asked for."
    return None


print(f"models {LUNA} (rewrite, chat judge), {TERRA} (book and paper judge); {SERVICE_TIER} tier; key {'present' if KEY else 'MISSING'}")

# %% [markdown]
# ## Block 3: connection test
#
# One tiny call, so a missing key or a closed network shows up before anything spends.

# %%
if __name__ == "__main__":
    if not KEY:
        print("no key: the store and the sidecar will build; the parents need OPENAI_API_KEY")
    else:
        reply = generate('Reply with the JSON object {"ok": true}.', {"ok": None}, "ping", ctx={"doc": "connection test"})
        print("connection", "ok" if reply else "FAILED", f"(${SPENT:.4f})")

# %% [markdown]
# ## Block 4: the store
#
# Every Step 1 record into SQLite, one table per record type with the same fields (`flags`,
# `provenance`, `units` and the other nested values as JSON text), the documents' text from
# Step 0 stored once, every quoted fact re-sliced from it at load and the load stopped on the
# first mismatch. The parent, up-edge, offer and sidecar tables are declared here and filled
# by the later blocks, so the whole schema is in one place.

# %%
SCHEMA = """
create table document (doc_id text primary key, source_uri text, sha256 text, title text, author text,
    source_class text, occurred_at text, ingested_at text, loader text, flags text, text text);
create table unit (unit_id text primary key, doc_id text, position integer, label text, kind text,
    start integer, end integer, occurred_at text);
create table piece (doc_id text, unit_id text, position integer, kind text, start integer, end integer,
    author text, occurred_at text);
create table node (doc_id text, node_id text, name text, kind text, created_from_unit text, provenance text,
    primary key (doc_id, node_id));
create table alias (doc_id text, alias text, node_id text, first_seen_unit text);
create table edge (doc_id text, predicate text, subject text, object text, units text, position integer);
create table fact (doc_id text, fact_id text, subject text, predicate text, object text, object_is_node integer,
    direction text, qualifiers text, rank text, unit_id text, quote text, quote_start integer, quote_end integer,
    valid_from text, occurred_at text, tier text, author text, provenance text, primary key (doc_id, fact_id));
create table cell (doc_id text, node_id text, unit_id text, text text, tier text, provenance text);
create table abstract (doc_id text, node_id text, text text, tier text, updated_at text);
create table adjudicated_fact (doc_id text, node_id text, predicate text, object text, qualifiers text,
    from_facts text, tier text);
create table attribute (doc_id text, node_id text, attribute text, value text, from_facts text, tier text);
create table contradiction (doc_id text, node_id text, note text, from_facts text, holds text, because text);
create table rejection (doc_id text, stage text, unit_id text, category text, row text);
create table ledger (doc_id text, a text, a_unit integer, b text, b_unit integer, verdict text, how text, evidence text);
create table candidate (doc_id text, a text, a_unit integer, b text, b_unit integer, round integer, tier real,
    reason text, name_score real, cooc_score real, combined real);
create table completion (doc_id text primary key, row text);

create table parent (parent_id integer primary key, name text, kind text, aliases text, summary text,
    version integer, founded_by text);
create table instance_of (doc_id text, node_id text, parent_id integer, pass integer, reason text, scores text,
    primary key (doc_id, node_id));
create table offer (doc_id text, node_id text, parent_id integer, parent_version integer, pass integer,
    lexical real, vector real, cast real, cast_rare real, identity integer, offered integer, verdict text, reason text);

create table vec_header (model text, dimension integer, built_at text);
create table vec_row (row integer primary key, record text, doc_id text, record_id text, ordinal integer, text text);
"""

FTS = """
create virtual table abstract_fts using fts5(text, content='abstract', content_rowid='rowid');
create virtual table cell_fts using fts5(text, content='cell', content_rowid='rowid');
create virtual table fact_fts using fts5(quote, content='fact', content_rowid='rowid');
insert into abstract_fts(abstract_fts) values ('rebuild');
insert into cell_fts(cell_fts) values ('rebuild');
insert into fact_fts(fact_fts) values ('rebuild');
"""

# the Step 1 file behind each table, and the fields in the table's column order
TABLES = {
    "document": ("documents", ["doc_id", "source_uri", "sha256", "title", "author", "source_class", "occurred_at",
                               "ingested_at", "loader", "flags"]),
    "unit": ("units", ["unit_id", "doc_id", "position", "label", "kind", "start", "end", "occurred_at"]),
    "piece": ("pieces", ["doc_id", "unit_id", "position", "kind", "start", "end", "author", "occurred_at"]),
    "node": ("nodes", ["doc_id", "node_id", "name", "kind", "created_from_unit", "provenance"]),
    "alias": ("aliases", ["doc_id", "alias", "node_id", "first_seen_unit"]),
    "edge": ("edges", ["doc_id", "predicate", "subject", "object", "units", "position"]),
    "fact": ("facts", ["doc_id", "fact_id", "subject", "predicate", "object", "object_is_node", "direction",
                       "qualifiers", "rank", "unit_id", "quote", "quote_start", "quote_end", "valid_from",
                       "occurred_at", "tier", "author", "provenance"]),
    "cell": ("cells", ["doc_id", "node_id", "unit_id", "text", "tier", "provenance"]),
    "abstract": ("abstracts", ["doc_id", "node_id", "text", "tier", "updated_at"]),
    "adjudicated_fact": ("adjudicated_facts", ["doc_id", "node_id", "predicate", "object", "qualifiers", "from_facts", "tier"]),
    "attribute": ("attributes", ["doc_id", "node_id", "attribute", "value", "from_facts", "tier"]),
    "contradiction": ("contradictions", ["doc_id", "node_id", "note", "from_facts", "holds", "because"]),
    "ledger": ("ledger", ["doc_id", "a", "a_unit", "b", "b_unit", "verdict", "how", "evidence"]),
    "candidate": ("candidates", ["doc_id", "a", "a_unit", "b", "b_unit", "round", "tier", "reason", "name_score",
                                 "cooc_score", "combined"]),
}


def column(value):
    """A value as SQLite stores it: nested values as JSON text, booleans as integers."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return int(value)
    return value


def texts_of(export_documents, doc_ids):
    """doc_id -> text, from Step 0, for the documents asked for."""
    texts = {}
    with Path(export_documents).open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["doc_id"] in doc_ids:
                texts[row["doc_id"]] = row["text"]
    return texts


def build_store(step1, export_documents, path):
    """The store from a Step 1 folder and Step 0's documents.jsonl; every quote proven at load."""
    if path.exists():
        path.unlink()
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    docs = read_jsonl(step1 / "documents.jsonl")
    texts = texts_of(export_documents, {d["doc_id"] for d in docs})
    missing = [d["doc_id"] for d in docs if d["doc_id"] not in texts]
    if missing:
        raise SystemExit(f"{len(missing)} documents have no text in Step 0, first {missing[0]}")

    checked = 0
    for table, (file, fields) in TABLES.items():
        rows = read_jsonl(step1 / f"{file}.jsonl")
        for r in rows:
            values = [column(r.get(f)) for f in fields]
            if table == "document":
                values.append(texts[r["doc_id"]])
            if table == "fact" and r["quote"] is not None:          # a document-record fact has no quote by rule
                if texts[r["doc_id"]][r["quote_start"]:r["quote_end"]] != r["quote"]:
                    raise SystemExit(f"quote of {r['fact_id']} does not slice to its text; load refused")
                checked += 1
            db.execute(f"insert into {table} values ({', '.join('?' * len(values))})", values)
    for r in read_jsonl(step1 / "rejections.jsonl"):
        db.execute("insert into rejection values (?,?,?,?,?)", (r["doc_id"], r["stage"], r.get("unit_id"), r["category"], column(r)))
    for r in read_jsonl(step1 / "completions.jsonl"):
        db.execute("insert into completion values (?,?)", (r["doc_id"], column(r)))
    db.commit()

    try:
        db.executescript(FTS)
        fts = "built"
    except sqlite3.OperationalError as e:
        fts = f"not built ({e})"
    db.commit()

    off = 0
    for doc_id, row in db.execute("select doc_id, row from completion"):
        stored = json.loads(row)["counts"]["facts_stored"]
        have = db.execute("select count(*) from fact where doc_id = ? and quote is not null", (doc_id,)).fetchone()[0]
        off += have != stored
    counts = {t: db.execute(f"select count(*) from {t}").fetchone()[0] for t in ("document", "node", "fact", "cell", "abstract")}
    db.close()
    print(f"store: {counts}; {checked} quotes checked, all slice to their text; FTS5 {fts}; "
          f"{'counts equal the completion records' if not off else f'{off} documents differ from their completion record'}")
    return counts

# %% [markdown]
# ## Block 5: the embedding sidecar
#
# The texts that get a vector, in row order: every fact as one line, every sentence of every
# cell, abstract and parent summary with its entity in front. The array is one float16 `.npy`
# beside the store; the row map and the header are written in one transaction after it, so a
# crash leaves either both or neither, and `load_sidecar` refuses a mismatch. The model is
# fetched once and runs on CPU; search is a linear scan of the array.

# %%
MODEL = "BAAI/bge-small-en-v1.5"
DIMENSION = 384
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")
EMBEDDER = None


def embedder():
    """The model, loaded on first use (fastembed fetches it once, then reads its cache)."""
    global EMBEDDER
    if EMBEDDER is None:
        from fastembed import TextEmbedding
        EMBEDDER = TextEmbedding(MODEL)
    return EMBEDDER


def embed(texts):
    import numpy
    return numpy.asarray(list(embedder().embed(texts, batch_size=256)), dtype=numpy.float32)


def sentences(text):
    return [s for s in SENTENCE.split((text or "").strip()) if s.strip()]


def fact_line(f, names, doc):
    """A fact as the sentence a question would match: subject, predicate, object, qualifiers, date, title."""
    subject = names.get(f["subject"], f["subject"])
    if f["direction"] == "mentioned":                       # a chat minor's fact, carried by its session
        subject = json.loads(f["provenance"] or "{}").get("subject_name") or subject
    obj = names.get(f["object"], f["object"]) if f["object_is_node"] else f["object"]
    line = f"{subject} {f['predicate'].replace('_', ' ')} {obj}"
    if f["qualifiers"]:
        line += f" ({f['qualifiers']})"
    if f["occurred_at"]:
        line += f", {f['occurred_at']}"
    if not is_identifier(doc["title"], doc["source_uri"]):
        line += f", {doc['title']}"
    return line


def prefix(entity, doc):
    return f"{entity}: " if is_identifier(doc["title"], doc["source_uri"]) else f"{entity}, {doc['title']}: "


def sidecar_texts(db):
    """(record, doc_id, record_id, ordinal, text) for every row the array holds, in order."""
    docs = {r[0]: {"title": r[1], "source_uri": r[2]} for r in db.execute("select doc_id, title, source_uri from document")}
    names = {(d, n): name for d, n, name in db.execute("select doc_id, node_id, name from node")}
    rows = []
    fields = ["doc_id", "fact_id", "subject", "predicate", "object", "object_is_node", "qualifiers", "occurred_at", "direction", "provenance"]
    for row in db.execute(f"select {', '.join(fields)} from fact order by doc_id, fact_id"):
        f = dict(zip(fields, row))
        local = {f["subject"]: names.get((f["doc_id"], f["subject"]), f["subject"]),
                 f["object"]: names.get((f["doc_id"], f["object"]), f["object"])}
        rows.append(("fact", f["doc_id"], f["fact_id"], 0, fact_line(f, local, docs[f["doc_id"]])))
    for doc_id, node_id, unit_id, text in db.execute("select doc_id, node_id, unit_id, text from cell order by rowid"):
        for i, s in enumerate(sentences(text)):
            rows.append(("cell", doc_id, f"{node_id}@{unit_id}", i, prefix(names.get((doc_id, node_id), node_id), docs[doc_id]) + s))
    for doc_id, node_id, text in db.execute("select doc_id, node_id, text from abstract order by rowid"):
        for i, s in enumerate(sentences(text)):
            rows.append(("abstract", doc_id, node_id, i, prefix(names.get((doc_id, node_id), node_id), docs[doc_id]) + s))
    for parent_id, name, summary in db.execute("select parent_id, name, summary from parent order by parent_id"):
        for i, s in enumerate(sentences(summary)):
            rows.append(("parent", None, str(parent_id), i, f"{name}: " + s))
    return rows


def build_sidecar(store):
    """The array beside the store, then its map and header in one transaction."""
    import numpy
    db = sqlite3.connect(store)
    rows = sidecar_texts(db)
    vectors = numpy.zeros((len(rows), DIMENSION), dtype=numpy.float16)
    for start in range(0, len(rows), 1024):
        vectors[start:start + 1024] = embed([r[4] for r in rows[start:start + 1024]]).astype(numpy.float16)
    numpy.save(store.with_suffix(".npy"), vectors)
    db.execute("delete from vec_row")
    db.execute("delete from vec_header")
    db.executemany("insert into vec_row values (?,?,?,?,?,?)", [(i, *r) for i, r in enumerate(rows)])
    db.execute("insert into vec_header values (?,?,?)", (MODEL, DIMENSION, now()))
    db.commit()
    db.close()
    by_record = {}
    for r in rows:
        by_record[r[0]] = by_record.get(r[0], 0) + 1
    print(f"sidecar: {vectors.shape} float16; rows by record {by_record}")


def load_sidecar(store):
    """The array, memory-mapped, and the open store; a mismatch with the header or the map refuses."""
    import numpy
    db = sqlite3.connect(store)
    header = db.execute("select model, dimension from vec_header").fetchone()
    array = numpy.load(store.with_suffix(".npy"), mmap_mode="r")
    n = db.execute("select count(*) from vec_row").fetchone()[0]
    if header != (MODEL, DIMENSION) or array.shape != (n, DIMENSION):
        raise SystemExit(f"sidecar mismatch: header {header}, array {array.shape}, rows {n}; rebuild it")
    return db, array

# %% [markdown]
# ## Block 6: the global layer
#
# The corpus is read once: every child (an entity node that is not the document itself and
# not the user of a chat) with its name, aliases, kind, summary or facts, the cast it shares
# units with, and its is_a links to siblings. Parents live in memory during the build and are
# written at the end. The judge reads texts and never scores; the rewrite may only pick a name
# a child carries. Prompts state rules, never cases.

# %%
JUDGE = """You are deciding whether an entity found in one document is an instance of a global entity that other
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


def read_corpus(db):
    """docs (with their children in attach order), children, and each cast name's rarity."""
    docs = {r[0]: {"title": r[1], "source_uri": r[2], "occurred_at": r[3], "children": []}
            for r in db.execute("select doc_id, title, source_uri, occurred_at from document")}
    chats = {r[0] for r in db.execute("select distinct doc_id from unit where kind in ('user', 'assistant')")}
    position = dict(db.execute("select unit_id, position from unit"))

    children = {}
    for doc_id, node_id, name, kind, created in db.execute("select doc_id, node_id, name, kind, created_from_unit from node"):
        if node_id.endswith(":doc") or fold(name) == "user":
            continue
        children[(doc_id, node_id)] = {"doc_id": doc_id, "node_id": node_id, "name": name, "kind": kind,
                                       "first_unit": position.get(created, 0), "aliases": [], "facts": [],
                                       "abstract": None, "cast": set(), "links": set(), "chat": doc_id in chats}
    for doc_id, alias, node_id in db.execute("select doc_id, alias, node_id from alias"):
        child = children.get((doc_id, node_id))
        if child and alias != child["name"]:
            child["aliases"].append(alias)
    for doc_id, node_id, text in db.execute("select doc_id, node_id, text from abstract"):
        if (doc_id, node_id) in children:
            children[(doc_id, node_id)]["abstract"] = text
    query = "select doc_id, subject, predicate, object, object_is_node, qualifiers from fact where quote is not null order by doc_id, fact_id"
    for doc_id, subject, predicate, obj, is_node, qualifiers in db.execute(query):
        child = children.get((doc_id, subject))
        if child is None:
            continue
        target = children.get((doc_id, obj)) if is_node else None
        value = target["name"] if target else obj
        child["facts"].append(f"{predicate.replace('_', ' ')} {value}" + (f" ({qualifiers})" if qualifiers else ""))
        if target is not None and predicate == "is_a":              # the ingestor's own link between two children
            child["links"].add(obj)
            target["links"].add(subject)

    members = {}                                                     # the cast: names sharing a unit
    for doc_id, subject, units in db.execute("select doc_id, subject, units from edge where predicate = 'appears_in'"):
        if (doc_id, subject) in children:
            for unit in json.loads(units or "[]"):
                members.setdefault((doc_id, unit), []).append(subject)
    for (doc_id, unit), ids in members.items():
        names = {fold(children[(doc_id, i)]["name"]) for i in ids}
        for i in ids:
            children[(doc_id, i)]["cast"] |= names - {fold(children[(doc_id, i)]["name"])}
    docs_with = {}
    for child in children.values():
        docs_with.setdefault(fold(child["name"]), set()).add(child["doc_id"])
    rarity = {name: math.log(len(docs) / (1 + len(ds))) for name, ds in docs_with.items()}

    for child in children.values():
        docs[child["doc_id"]]["children"].append(child)
    for doc in docs.values():                                        # by first unit; linked children last
        doc["children"].sort(key=child_order)
    return docs, children, rarity


def child_order(child):
    return (1 if child["links"] else 0, child["first_unit"], child["node_id"])


def doc_order(item):
    doc_id, doc = item
    return (first_year(doc["occurred_at"]), doc["source_uri"])


def child_text(child, doc):
    """What the judge, the rewrite and the vector see of a child."""
    lines = [f"name: {child['name']}", f"kind: {child['kind']}"]
    if child["aliases"]:
        lines.append("also called: " + "; ".join(child["aliases"][:15]))
    if not is_identifier(doc["title"], doc["source_uri"]):
        lines.append(f"document: {doc['title']}")
    if child["abstract"]:
        lines.append("summary: " + child["abstract"])
    elif child["facts"]:
        lines.append("facts: " + "; ".join(child["facts"][:FACTS_SHOWN]))
    return "\n".join(lines)


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a or b) else 0.0


def rare_jaccard(a, b, rarity):
    """Jaccard with each name weighted by its rarity over the loaded documents."""
    either = sum(rarity.get(name, 0.0) for name in a | b)
    return sum(rarity.get(name, 0.0) for name in a & b) / either if either else 0.0


# the build's state: parents in memory, the edges drawn, the offers logged
PARENTS = []          # dicts: name, kind, aliases, summary [(child key, line)], children [keys], cast, vec, version, alive
EDGES = {}            # child key -> parent
OFFERS = []           # every logged offer row


def parent_text(p):
    lines = [f"name: {p['name']}", f"kind: {p['kind']}", "also called: " + "; ".join(sorted(p["aliases"])[:20])]
    return "\n".join(lines + [line for (_, line) in p["summary"]])


def proper(alias):
    """An alias that names rather than describes: after a leading article, some word is capitalised.
    "Tippetarius" and "the Scarecrow" count; "the girl", "he" and "the old woman" do not."""
    words = alias.split()
    if words and words[0].casefold() in ("the", "a", "an"):
        words = words[1:]
    return any(w[:1].isupper() for w in words)


def lexical_names(name, aliases):
    """The forms a lexical match may fire on: the name, and the aliases that are names."""
    return {fold(name)} | {fold(a) for a in aliases if proper(a)}


def parent_names(p):
    return lexical_names(p["name"], p["aliases"])


def cast_line(names):
    """The cast reaches the judge as names only when the cast signal is in the arm."""
    return ", ".join(sorted(names)[:25]) if "cast" in SIGNALS else "(not shown)"


def score(child, doc, vec, pass_no, exclude=None):
    """Every live parent scored for a child; the offered ones (at most K) and a few below the floor logged."""
    import numpy
    live = [p for p in PARENTS if p["alive"] and p is not exclude]
    if not live:
        return []
    sims = numpy.stack([p["vec"] for p in live]) @ vec
    child_names = lexical_names(child["name"], child["aliases"])
    text = fold(child_text(child, doc))
    rows = []
    for p, sim in zip(live, sims):
        names = parent_names(p)
        lexical = 1.0 if child_names & names else (0.5 if any(n and n in text for n in names) else 0.0)
        linked = any(key[0] == child["doc_id"] and key[1] in child["links"] for key in p["children"])
        offered = (("lexical" in SIGNALS and lexical == 1.0) or ("vector" in SIGNALS and sim >= VECTOR_FLOOR)
                   or ("identity" in SIGNALS and linked))
        rows.append({"doc_id": child["doc_id"], "node_id": child["node_id"], "parent": p, "parent_version": p["version"],
                     "pass": pass_no, "lexical": lexical, "vector": float(sim), "cast": jaccard(child["cast"], p["cast"]),
                     "cast_rare": rare_jaccard(child["cast"], p["cast"], RARITY), "identity": int(linked),
                     "offered": int(offered), "verdict": None, "reason": None})
    rows.sort(key=strongest_first)
    offered = [r for r in rows if r["offered"]][:K]
    OFFERS.extend(offered + [r for r in rows if not r["offered"]][:BELOW_FLOOR_LOGGED])
    return offered


def strongest_first(row):
    return (not row["offered"], -row["vector"])


def judge(child, doc, offered, pass_no):
    """One call over texts; the verdict is written onto the offered rows. The parent joined, or None."""
    listing = "\n".join(f"[{n + 1}]\n{parent_text(r['parent'])}\nAppears beside: {cast_line(r['parent']['cast'])}\n"
                        for n, r in enumerate(offered))
    prompt = JUDGE.format(child=child_text(child, doc), child_cast=cast_line(child["cast"]), parents=listing)
    reply = generate(prompt, {"attach": None, "reason": str}, "judge", model=LUNA if child["chat"] else TERRA,
                     effort="medium", ctx={"doc": child["doc_id"][:8], "node": child["node_id"], "pass": pass_no})
    choice = reply.get("attach") if reply else None
    if isinstance(choice, str) and choice.strip().isdigit():
        choice = int(choice)
    picked = offered[choice - 1]["parent"] if isinstance(choice, int) and 1 <= choice <= len(offered) else None
    for r in offered:
        r["verdict"] = "attach" if r["parent"] is picked else "apart"
        r["reason"] = reply.get("reason") if reply else "no reply"
    return picked


def found(child, doc, vec):
    """A new parent as a copy of the child; no call."""
    key = (child["doc_id"], child["node_id"])
    line = f"In {doc['title']}: " + (child["abstract"] or "; ".join(child["facts"][:FACTS_SHOWN]) or child["name"])
    p = {"name": child["name"], "kind": child["kind"], "aliases": {child["name"], *child["aliases"]},
         "summary": [(key, line)], "children": [key], "cast": set(child["cast"]), "vec": vec, "version": 1, "alive": True}
    PARENTS.append(p)
    EDGES[key] = p
    return p


def attach(child, doc, p):
    """The parent gains the child; one call rewrites its name, kind and the line for this document."""
    key = (child["doc_id"], child["node_id"])
    prompt = REWRITE.format(parent=parent_text(p), child=child_text(child, doc) + f"\ndocument: {doc['title']}")
    reply = generate(prompt, {"name": str, "kind": str, "line": str}, "rewrite", effort="low",
                     ctx={"doc": child["doc_id"][:8], "node": child["node_id"], "parent": PARENTS.index(p)})
    p["children"].append(key)
    p["aliases"] |= {child["name"], *child["aliases"]}
    p["cast"] |= child["cast"]
    if reply and fold(reply["name"]) in parent_names(p):            # a name no child carries is refused
        p["name"] = reply["name"]
    if reply and reply.get("kind"):
        p["kind"] = reply["kind"]
    p["summary"].append((key, reply["line"] if reply and reply.get("line") else f"In {doc['title']}: {child['name']}."))
    p["version"] += 1
    p["vec"] = embed([parent_text(p)])[0]
    EDGES[key] = p


def place(child, doc, pass_no, exclude=None):
    """Offer, judge, attach or found. The parent the child is under afterwards."""
    vec = embed([child_text(child, doc)])[0]
    offered = score(child, doc, vec, pass_no, exclude)
    picked = judge(child, doc, offered, pass_no) if offered else None
    if picked is not None:
        attach(child, doc, picked)
        return picked
    return None if exclude is not None else found(child, doc, vec)


def build_parents(store):
    """Both passes over the store, then the tables."""
    global RARITY
    PARENTS.clear()
    EDGES.clear()
    OFFERS.clear()
    db = sqlite3.connect(store)
    docs, children, RARITY = read_corpus(db)
    order = sorted(docs.items(), key=doc_order)
    print(f"{len(order)} documents, {len(children)} children; signals {sorted(SIGNALS)}")

    for n, (doc_id, doc) in enumerate(order):
        for child in doc["children"]:
            place(child, doc, 1)
        alive = sum(p["alive"] for p in PARENTS)
        print(f"  [{n + 1}/{len(order)}] {(doc['title'] or doc_id)[:40]:40} children {len(doc['children']):3}  parents {alive:5}  ${SPENT:.2f}")

    founders = [(key, p) for key, p in EDGES.items() if len(p["children"]) == 1]
    moved = 0
    for key, own in founders:
        child = children[key]
        if place(child, docs[key[0]], 2, exclude=own) is not None:
            own["alive"] = False
            moved += 1
    print(f"pass 2: {len(founders)} founders offered again, {moved} moved; parents {sum(p['alive'] for p in PARENTS)}; ${SPENT:.2f}")
    write_parents(db)
    db.close()


def write_parents(db):
    for table in ("parent", "instance_of", "offer"):
        db.execute(f"delete from {table}")
    for i, p in enumerate(PARENTS):
        if p["alive"]:
            summary = "\n".join(f"[{d[:8]}:{n}] {line}" for ((d, n), line) in p["summary"])
            first = p["children"][0]
            db.execute("insert into parent values (?,?,?,?,?,?,?)",
                       (i, p["name"], p["kind"], column(sorted(p["aliases"])), summary, p["version"], f"{first[0][:8]}:{first[1]}"))
    winning = {(r["doc_id"], r["node_id"]): r for r in OFFERS if r["verdict"] == "attach"}
    for (doc_id, node_id), p in EDGES.items():
        r = winning.get((doc_id, node_id))
        scores = {k: r[k] for k in ("lexical", "vector", "cast", "cast_rare", "identity")} if r else None
        db.execute("insert into instance_of values (?,?,?,?,?,?)",
                   (doc_id, node_id, PARENTS.index(p), r["pass"] if r else 1, r["reason"] if r else "founded", column(scores)))
    for r in OFFERS:
        db.execute("insert into offer values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (r["doc_id"], r["node_id"], PARENTS.index(r["parent"]), r["parent_version"], r["pass"], r["lexical"],
                    r["vector"], r["cast"], r["cast_rare"], r["identity"], r["offered"], r["verdict"], r["reason"]))
    db.commit()
    alive = [p for p in PARENTS if p["alive"]]
    multi = sum(1 for p in alive if len(p["children"]) > 1)
    print(f"written: {len(alive)} parents ({multi} with two or more children), {len(EDGES)} up-edges, {len(OFFERS)} offer rows")

# %% [markdown]
# ## Block 7: run
#
# The store, the sidecar, the parents, the sidecar again with the parents' summaries, and a
# receipt. Without a key the parents are skipped and the rest still builds.

# %%
if __name__ == "__main__":
    if STEP1 is None or EXPORT is None:
        raise SystemExit("attach it494-threadatlas-step1 and it494-threadatlas-step0, or set STEP1 and EXPORT")
    started = now()
    counts = build_store(STEP1, EXPORT / "documents.jsonl", STORE)
    build_sidecar(STORE)
    if KEY:
        build_parents(STORE)
        build_sidecar(STORE)
    db = sqlite3.connect(STORE)
    receipt = {"version": VERSION, "started_at": started, "finished_at": now(), "signals": sorted(SIGNALS),
               "store": counts, "parents": db.execute("select count(*) from parent").fetchone()[0],
               "parents_with_two_or_more": db.execute("select count(*) from (select parent_id from instance_of group by parent_id having count(*) > 1)").fetchone()[0],
               "up_edges": db.execute("select count(*) from instance_of").fetchone()[0],
               "offers": db.execute("select count(*) from offer").fetchone()[0],
               "vectors": db.execute("select count(*) from vec_row").fetchone()[0], "cost": round(SPENT, 4)}
    db.close()
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))

# %% [markdown]
# ## Block 8: reading it back
#
# The parents that gathered more than one instance, and the one a question would reach first.

# %%
if __name__ == "__main__" and STORE.exists():
    db = sqlite3.connect(STORE)
    query = """select p.name, p.kind, count(*) as n, group_concat(substr(i.doc_id, 1, 8) || ':' || i.node_id, ' ')
               from parent p join instance_of i on i.parent_id = p.parent_id group by p.parent_id having n > 1 order by n desc limit 25"""
    for name, kind, n, members in db.execute(query):
        print(f"{n:3}  {name:35} {kind:15} {members}")
    for name, kind, summary in db.execute("select name, kind, summary from parent where name like 'Ozma%' or name = 'Tip'"):
        print(f"\n{name} ({kind})\n{summary}")
    db.close()
