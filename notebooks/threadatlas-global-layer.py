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
# | `parent` | `parent_id`, `name`, `kind`, `aliases`, `summary`, `instances`, `first` | a global entity: a name and kind chosen from its instances, the union of their aliases, one summary line per instance tagged with the instance's id, how many instances it has, the first of them |
# | `instance_of` | `doc_id`, `node_id`, `parent_id`, `reason`, `scores` | the up-edge from a document's entity to its parent, owned by the document: the judge's reason on the pair that joined it (or `alone`), and that pair's scores |
# | `pair` | `doc_a`, `node_a`, `doc_b`, `node_b`, `lexical`, `vector`, `cast`, `cast_rare`, `identity`, `offered`, `verdict`, `reason` | every nominated pair of children: the four signals, whether it cleared the floor, and the judge's verdict; the grouping replays from this table under any subset of the signals |
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
# embed       one vector per fact line and per narrative sentence, and one per child (an
#             entity node that is not the document itself and not the user of a chat)
# nominate    candidate pairs of children, each once: the NEAREST other-document children by
#             vector (block matrix products, never a scan in Python), every two children
#             sharing a name or a naming alias (by index), and every is_a link between two
#             children of one document; each pair scored on four signals: lexical (a name or
#             alias match), vector (cosine of the two texts), cast (overlap of the names each
#             appears beside), identity (the document says one is the other); a pair is
#             OFFERED when a named signal clears its floor
# cluster     bottom up, as the ingestor reconciles a document: every child starts as its own
#             cluster in the pool; every offered pair goes into a heap by strength (an is_a
#             link first, with no floor; then a name match; then the cosine); pop a batch,
#             skip a pair whose children already share a cluster and a pair between two
#             clusters that hold any pair ruled different, judge the rest in parallel (one
#             call about the pair's two instances, each shown with what is already united
#             with it as context: same or different, with a reason), unite the pairs ruled same
#             and put the clusters back in the pool for the pairs still queued; until no valid
#             pair remains; every pair and verdict is logged, and a pair ruled different is a
#             constraint the clusters keep
# write       a group of one is a parent copied from its child, no call; a group of two or
#             more gets one call that picks the name and kind from what the instances carry
#             (a name no instance carries is refused) and writes one line per instance
# embed       the parents' summaries join the sidecar
# ```
#
# The user of a chat is never a child. Grouping is transitive, so one wrong "same" chains
# two entities into one parent; only judged pairs join, and the size of every group is in the
# receipt. Every call is logged with its cost, and the run stops at a spending limit. A
# document arriving later (the nightly pull) attaches through the same nomination against
# the parents that exist; that path is the next build.
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
# may put a pair in front of the judge. Every signal is logged whatever the arm.

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

VECTOR_FLOOR = 0.75        # cosine over bge-small at which a pair is offered on the vector alone: loose, the judge is the gate
NEAREST = 8                # nearest other-document children by vector nominated per child
FACTS_SHOWN = 12           # facts of a child shown to the judge and the parent writer
SIDE_SHOWN = 6             # instances shown per side to the judge: the nominated one, then up to five united with it
GROUP_SHOWN = 20           # instances shown to the call that writes a parent, most facts first
WORKERS = 8                # judge calls in flight at once; a batch pops twice that many pairs from the queue
SIGNALS = set(os.environ.get("SIGNALS", "lexical,vector,cast,identity").split(","))
SPEND_STOP = float(os.environ.get("SPEND_STOP", "25"))     # the test set judges about 2,500 pairs, most on Terra: near $3

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
import threading
import urllib.error
import urllib.request

LUNA = "gpt-5.6-luna"                   # the parent writer, and the judge when a chat is on either side
TERRA = "gpt-5.6-terra"                 # the judge for pairs of book and paper children
SERVICE_TIER = "flex"
PRICE = {"flex": {LUNA: (0.10, 0.60), TERRA: (1.00, 6.00)},          # $ per million tokens in, out
         "default": {LUNA: (0.20, 1.20), TERRA: (2.00, 12.00)}}
CALLS = OUT / "calls.jsonl"
SPENT = 0.0
LOG_LOCK = threading.Lock()

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
    with LOG_LOCK:                                    # calls run in parallel
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
    """`schema` maps each required key to its type, or None for any. The first problem, or None."""
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


def in_parallel(function, jobs):
    """function(*job) for every job, WORKERS at a time; the results in the jobs' order."""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return list(pool.map(function, *zip(*jobs))) if jobs else []


print(f"models {LUNA} (parent writer, chat judge), {TERRA} (book and paper judge); {SERVICE_TIER} tier; key {'present' if KEY else 'MISSING'}")

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
# ## Block 4: the store's schema
#
# Every Step 1 record type is a table with the same fields (`flags`, `provenance`, `units` and
# the other nested values as JSON text), the documents' text from Step 0 is stored once, and
# the parent, up-edge, pair and sidecar tables are declared here, filled by the later blocks,
# so the whole schema is in one place. `TABLES` names the Step 1 file behind each table and
# the fields in column order.

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
    instances integer, first text);
create table instance_of (doc_id text, node_id text, parent_id integer, reason text, scores text,
    primary key (doc_id, node_id));
create table pair (doc_a text, node_a text, doc_b text, node_b text, lexical real, vector real, cast real,
    cast_rare real, identity integer, offered integer, verdict text, reason text);

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

# %% [markdown]
# ## Block 5: loading the store
#
# The Step 1 rows go in as they are; a fact's quote is re-sliced from the document's text at
# its offsets and the load stops on the first mismatch (a document-record fact has no quote by
# rule and is not checked). Then FTS5, and a check that the facts and cells per document equal
# the completion records the ingestor wrote.

# %%
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


def load_table(db, table, step1, texts):
    """One Step 1 file into its table; every quoted fact proven against the text. Quotes checked."""
    file, fields = TABLES[table]
    checked = 0
    for r in read_jsonl(step1 / f"{file}.jsonl"):
        values = [column(r.get(f)) for f in fields]
        if table == "document":
            values.append(texts[r["doc_id"]])
        if table == "fact" and r["quote"] is not None:
            if texts[r["doc_id"]][r["quote_start"]:r["quote_end"]] != r["quote"]:
                raise SystemExit(f"quote of {r['fact_id']} does not slice to its text; load refused")
            checked += 1
        db.execute(f"insert into {table} values ({', '.join('?' * len(values))})", values)
    return checked


def check_counts(db):
    """Documents whose stored facts or cells differ from their completion record."""
    off = 0
    for doc_id, row in db.execute("select doc_id, row from completion"):
        counts = json.loads(row)["counts"]
        facts = db.execute("select count(*) from fact where doc_id = ? and quote is not null", (doc_id,)).fetchone()[0]
        cells = db.execute("select count(*) from cell where doc_id = ?", (doc_id,)).fetchone()[0]
        off += facts != counts["facts_stored"] or cells != counts["cells"]
    return off


def build_store(step1, export_documents, path):
    """The store from a Step 1 folder and Step 0's documents.jsonl."""
    if path.exists():
        path.unlink()
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    docs = read_jsonl(step1 / "documents.jsonl")
    texts = texts_of(export_documents, {d["doc_id"] for d in docs})
    missing = [d["doc_id"] for d in docs if d["doc_id"] not in texts]
    if missing:
        raise SystemExit(f"{len(missing)} documents have no text in Step 0, first {missing[0]}")
    checked = sum(load_table(db, table, step1, texts) for table in TABLES)
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
    off = check_counts(db)
    counts = {t: db.execute(f"select count(*) from {t}").fetchone()[0] for t in ("document", "node", "fact", "cell", "abstract")}
    db.close()
    print(f"store: {counts}; {checked} quotes checked, all slice to their text; FTS5 {fts}; "
          f"{'counts equal the completion records' if not off else f'{off} documents differ from their completion record'}")
    return counts

# %% [markdown]
# ## Block 6: what gets a vector
#
# The texts of the sidecar, in row order: every fact as one line, every sentence of every
# cell and abstract with its entity in front (and the title, when the document has a title
# rather than a session id), and, once the parents exist, every sentence of every parent
# summary with the parent's name in front.

# %%
MODEL = "BAAI/bge-small-en-v1.5"
DIMENSION = 384
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


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


def document_texts(db):
    """(record, doc_id, record_id, ordinal, text) for every fact, cell and abstract row, in order."""
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
    return rows


def parent_texts(db):
    """(record, doc_id, record_id, ordinal, text) for every parent summary sentence."""
    rows = []
    for parent_id, name, summary in db.execute("select parent_id, name, summary from parent order by parent_id"):
        for i, s in enumerate(sentences(summary)):
            rows.append(("parent", None, str(parent_id), i, f"{name}: " + s))
    return rows

# %% [markdown]
# ## Block 7: the embedding sidecar
#
# The array is one float16 `.npy` beside the store; the row map and the header are written in
# one transaction after it, so a crash leaves either both or neither, and `load_sidecar`
# refuses a mismatch. The model is fetched once and runs on CPU. Built once over the
# documents; when the parents exist their rows are appended rather than everything redone.

# %%
EMBEDDER = None


def embed(texts):
    """Vectors for texts, float32; the model loads on first use."""
    global EMBEDDER
    import numpy
    if EMBEDDER is None:
        from fastembed import TextEmbedding
        EMBEDDER = TextEmbedding(MODEL)
    return numpy.asarray(list(EMBEDDER.embed(texts, batch_size=256)), dtype=numpy.float32)


def write_sidecar(db, store, rows, vectors):
    """The array, then its map and header in one transaction."""
    import numpy
    numpy.save(store.with_suffix(".npy"), vectors)
    db.execute("delete from vec_row")
    db.execute("delete from vec_header")
    db.executemany("insert into vec_row values (?,?,?,?,?,?)", [(i, *r) for i, r in enumerate(rows)])
    db.execute("insert into vec_header values (?,?,?)", (MODEL, DIMENSION, now()))
    db.commit()
    by_record = {}
    for r in rows:
        by_record[r[0]] = by_record.get(r[0], 0) + 1
    print(f"sidecar: {vectors.shape} float16; rows by record {by_record}")


def build_sidecar(store):
    """Every document row embedded; the array written."""
    import numpy
    db = sqlite3.connect(store)
    rows = document_texts(db)
    vectors = embed([r[4] for r in rows]).astype(numpy.float16)
    write_sidecar(db, store, rows, vectors)
    db.close()


def extend_sidecar(store):
    """The parents' rows appended to the array the documents already have."""
    import numpy
    db = sqlite3.connect(store)
    rows = [tuple(r) for r in db.execute("select record, doc_id, record_id, ordinal, text from vec_row where record != 'parent' order by row")]
    have = numpy.load(store.with_suffix(".npy"))[:len(rows)]
    added = parent_texts(db)
    vectors = numpy.vstack([have, embed([r[4] for r in added]).astype(numpy.float16)]) if added else have
    write_sidecar(db, store, rows + added, vectors)
    db.close()


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
# ## Block 8: reading the corpus
#
# A child is an entity node that is not the document itself and not the user of a chat. Each
# is read once with its name, aliases, kind, summary or facts, the cast it shares units with,
# and its is_a links to siblings (the ingestor's own link: an is_a fact whose object is
# another node of the document). A cast name's rarity over the loaded documents weights the
# second co-occurrence score.

# %%
def read_children(db):
    """Every child with its aliases, abstract and facts; is_a links between siblings."""
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
        if target is not None and predicate == "is_a":
            child["links"].add(obj)
            target["links"].add(subject)
    return children


def read_casts(db, children):
    """Each child's cast, the folded names of the children it shares a unit with."""
    members = {}
    for doc_id, subject, units in db.execute("select doc_id, subject, units from edge where predicate = 'appears_in'"):
        if (doc_id, subject) in children:
            for unit in json.loads(units or "[]"):
                members.setdefault((doc_id, unit), []).append(subject)
    for (doc_id, unit), ids in members.items():
        names = {fold(children[(doc_id, i)]["name"]) for i in ids}
        for i in ids:
            children[(doc_id, i)]["cast"] |= names - {fold(children[(doc_id, i)]["name"])}


def read_corpus(db):
    """docs, children and each cast name's rarity (log of documents over documents holding the name)."""
    docs = {r[0]: {"title": r[1], "source_uri": r[2], "occurred_at": r[3]}
            for r in db.execute("select doc_id, title, source_uri, occurred_at from document")}
    children = read_children(db)
    read_casts(db, children)
    docs_with = {}
    for child in children.values():
        docs_with.setdefault(fold(child["name"]), set()).add(child["doc_id"])
    rarity = {name: math.log(len(docs) / (1 + len(ds))) for name, ds in docs_with.items()}
    return docs, children, rarity


def child_text(child, doc):
    """What the judge, the parent writer and the vector see of a child."""
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


def most_facts_first(children):
    def key_of(key):
        return (-len(children[key]["facts"]), key)
    return key_of

# %% [markdown]
# ## Block 9: the two prompts
#
# Rules, never cases. The judge sees texts and casts as names, never scores. The writer may
# only pick a name an instance carries; code refuses any other.

# %%
JUDGE = """You are deciding whether two entities are the same person, place, thing or concept, or different
things with a similar name or description. Each is described only by what its document says. Under an
entity, "also united with it" lists other documents' instances already judged to be the same thing as
it; they are context for what the entity is, and the question is not about them. Say same only when
the first entity and the second entity themselves are one thing, even under different names, spellings
or roles, and even when one document knows it under a name the other never uses. Say different when
they are different things that share a name or a word, when one is a part, a possession, a place or an
event of the other, or when nothing in their own descriptions connects them. A disagreement in kind or
role is not by itself a reason to say different; a contradiction in identity is. The reason must speak
of the first entity and the second entity, not of the instances united with them.

The first entity:
{first}
Appears beside: {first_cast}

The second entity:
{second}
Appears beside: {second_cast}

Reply with a JSON object: {{"same": true or false, "reason": "<one sentence>"}}."""

WRITE = """A global entity is described by its instances, the entities that documents hold of it. Below are the
instances of one global entity, numbered. Give it a name and a kind, and write one line per instance
saying what part that instance played in its document. The name must be one the instances actually use
(a name or an alias listed below), the one a reader would look for first. The kind is one or two words.
Each line says only what that instance's description says, in the third person, naming the document.

{instances}

Reply with a JSON object: {{"name": "<name>", "kind": "<kind>", "lines": [<{n} strings, one per instance, in order>]}}."""

# %% [markdown]
# ## Block 10: nominating pairs
#
# Which pairs of children are worth a judge. Three routes, each pair once: the NEAREST
# other-document children by vector, from block matrix products over every child; every two
# children sharing a name or a naming alias, by index (an alias names when a word after any
# article is capitalised: "Tippetarius" and "the Scarecrow" count, "the girl" does not); and
# every is_a link between two children of one document. Every nominated pair is scored on the
# four signals and logged; it is offered when a named signal clears its floor.

# %%
def proper(alias):
    words = alias.split()
    if words and words[0].casefold() in ("the", "a", "an"):
        words = words[1:]
    return any(w[:1].isupper() for w in words)


def lexical_names(child):
    """The forms a lexical match may fire on: the name, and the aliases that are names."""
    return {fold(child["name"])} | {fold(a) for a in child["aliases"] if proper(a)}


def nearest_pairs(keys, vectors, add):
    """Each child's NEAREST other-document children by cosine, in blocks of 2,048 rows."""
    import numpy
    docs_of = numpy.array([hash(key[0]) for key in keys])
    for start in range(0, len(keys), 2048):
        sims = vectors[start:start + 2048] @ vectors.T
        sims[docs_of[start:start + 2048, None] == docs_of[None, :]] = -1.0       # never two of one document by vector
        for row, i in enumerate(range(start, min(start + 2048, len(keys)))):
            for j in numpy.argpartition(-sims[row], NEAREST)[:NEAREST]:
                add(i, int(j), "vector")


def name_pairs(keys, children, add):
    """Every two children of different documents sharing a name or a naming alias."""
    by_name = {}
    for i, key in enumerate(keys):
        for name in lexical_names(children[key]):
            by_name.setdefault(name, []).append(i)
    for members in by_name.values():
        for i in members:
            for j in members:
                if i < j and keys[i][0] != keys[j][0]:
                    add(i, j, "lexical")


def link_pairs(keys, children, add):
    """Every is_a link between two children of one document."""
    index = {key: i for i, key in enumerate(keys)}
    for i, key in enumerate(keys):
        for node_id in children[key]["links"]:
            j = index.get((key[0], node_id))
            if j is not None:
                add(i, j, "identity")


def nominate(keys, children, vectors):
    """(i, j) -> the routes that nominated the pair."""
    pairs = {}

    def add(i, j, how):
        a, b = (i, j) if i < j else (j, i)
        pairs.setdefault((a, b), set()).add(how)

    nearest_pairs(keys, vectors, add)
    name_pairs(keys, children, add)
    link_pairs(keys, children, add)
    return pairs


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a or b) else 0.0


def rare_jaccard(a, b, rarity):
    """Jaccard with each name weighted by its rarity over the loaded documents."""
    either = sum(rarity.get(name, 0.0) for name in a | b)
    return sum(rarity.get(name, 0.0) for name in a & b) / either if either else 0.0


def score_pair(a, b, hows, sim, rarity):
    """One pair on every signal, and whether a named signal puts it in front of the judge."""
    lexical = 1.0 if lexical_names(a) & lexical_names(b) else 0.0
    identity = int("identity" in hows)
    offered = (("lexical" in SIGNALS and lexical == 1.0) or ("vector" in SIGNALS and sim >= VECTOR_FLOOR)
               or ("identity" in SIGNALS and identity))
    return {"a": (a["doc_id"], a["node_id"]), "b": (b["doc_id"], b["node_id"]), "lexical": lexical, "vector": sim,
            "cast": jaccard(a["cast"], b["cast"]), "cast_rare": rare_jaccard(a["cast"], b["cast"], rarity),
            "identity": identity, "offered": int(offered), "verdict": None, "reason": None}


TIER = {"identity": 2.0, "lexical": 1.0, "vector": 0.0}     # what a pair is offered on, strongest first


def priority(pair):
    """A pair's place in the queue: the strongest signal it was offered on, then its cosine."""
    tier = TIER["identity"] if pair["identity"] else (TIER["lexical"] if pair["lexical"] == 1.0 else TIER["vector"])
    return tier + pair["vector"]

# %% [markdown]
# ## Block 11: the judge
#
# One call about the pair's two instances. Each side shows the nominated instance first and,
# underneath, the instances already united with it, as context only. A pair with a chat on
# either side goes to Luna, the rest to Terra. The verdict is written onto the pair.

# %%
def side_text(key, members, children, docs):
    """One side as the judge sees it."""
    text = child_text(children[key], docs[key[0]])
    others = sorted((m for m in members if m != key), key=most_facts_first(children))[:SIDE_SHOWN - 1]
    if others:
        lines = [f"  - {children[m]['name']} ({children[m]['kind']}) in {docs[m[0]]['title']}: "
                 + (children[m]["abstract"] or "; ".join(children[m]["facts"][:4]) or "")[:300] for m in others]
        text += "\nalso united with it, in other documents (context only):\n" + "\n".join(lines)
    if len(members) - 1 > len(others):
        text += f"\n  - and {len(members) - 1 - len(others)} more"
    return text


def cast_line(names):
    """The cast reaches the judge as names only when the cast signal is in the arm."""
    return ", ".join(sorted(names)[:25]) if "cast" in SIGNALS else "(not shown)"


def judge_pair(pair, side_a, side_b, children, docs):
    prompt = JUDGE.format(first=side_text(pair["a"], side_a, children, docs), first_cast=cast_line(children[pair["a"]]["cast"]),
                          second=side_text(pair["b"], side_b, children, docs), second_cast=cast_line(children[pair["b"]]["cast"]))
    chat = any(children[key]["chat"] for key in side_a + side_b)
    reply = generate(prompt, {"same": None, "reason": str}, "judge", model=LUNA if chat else TERRA, effort="medium",
                     ctx={"a": f"{pair['a'][0][:8]}:{pair['a'][1]}", "b": f"{pair['b'][0][:8]}:{pair['b'][1]}",
                          "sides": [len(side_a), len(side_b)]})
    same = reply.get("same") if reply else None
    if isinstance(same, str):
        same = same.strip().casefold() in ("true", "yes", "same")
    pair["verdict"] = "same" if same is True else ("different" if reply else "no reply")
    pair["reason"] = reply.get("reason") if reply else None
    return pair

# %% [markdown]
# ## Block 12: clustering
#
# Bottom up, the way the ingestor reconciles a document. Every child starts as its own cluster.
# Every offered pair goes into a heap by strength. Pop a batch: a pair whose two children already
# share a cluster is skipped; a pair between two clusters that hold any pair ruled different is
# blocked; the rest are judged in parallel; the pairs ruled same unite their clusters, which go
# back into the pool for the pairs still queued. Until no valid pair remains.

# %%
class Clusters:
    """Union-find over children, with the members of each cluster and the pairs ruled different."""

    def __init__(self, keys):
        self.leader = {key: key for key in keys}
        self.members = {key: [key] for key in keys}
        self.different = set()

    def find(self, key):
        while self.leader[key] != key:
            self.leader[key] = self.leader[self.leader[key]]
            key = self.leader[key]
        return key

    def unite(self, a, b):
        keep, gone = (a, b) if a < b else (b, a)
        self.leader[gone] = keep
        self.members[keep] += self.members.pop(gone)

    def blocked(self, la, lb):
        """Two clusters may not merge when any member of one was ruled different from any member of the other."""
        small, large = (self.members[la], self.members[lb]) if len(self.members[la]) <= len(self.members[lb]) else (self.members[lb], self.members[la])
        large_set = set(large)
        return any((min(a, b), max(a, b)) in self.different for a in small for b in large_set)

    def groups(self, keys):
        groups = {}
        for key in keys:
            groups.setdefault(self.find(key), []).append(key)
        return groups


def next_batch(heap, clusters):
    """Up to two workers' worth of pairs still worth judging, popped strongest first."""
    import heapq
    batch, seen = [], set()
    while heap and len(batch) < WORKERS * 2:
        _, n, pair = heapq.heappop(heap)
        la, lb = clusters.find(pair["a"]), clusters.find(pair["b"])
        if la == lb:
            pair["verdict"] = "skipped"                          # already one cluster through other pairs
        elif clusters.blocked(la, lb):
            pair["verdict"] = "blocked"                          # their clusters hold a pair ruled different
        elif (min(la, lb), max(la, lb)) in seen:
            heapq.heappush(heap, (-priority(pair) + 1e-6, n, pair))   # the same two clusters, judged once per batch
            break
        else:
            seen.add((min(la, lb), max(la, lb)))
            batch.append((pair, list(clusters.members[la]), list(clusters.members[lb])))
    return batch


def cluster(keys, pairs, children, docs):
    """Every child's cluster after the loop, keyed by its leader."""
    import heapq
    clusters = Clusters(keys)
    heap = [(-priority(p), n, p) for n, p in enumerate(pairs) if p["offered"]]
    heapq.heapify(heap)
    batches, judged, united = 0, 0, 0
    while heap:
        batch = next_batch(heap, clusters)
        if not batch:
            continue
        in_parallel(judge_pair, [(pair, a, b, children, docs) for pair, a, b in batch])
        for pair, _, _ in batch:
            la, lb = clusters.find(pair["a"]), clusters.find(pair["b"])
            if pair["verdict"] == "same" and la != lb:
                clusters.unite(la, lb)
                united += 1
            elif pair["verdict"] == "different":
                clusters.different.add((min(pair["a"], pair["b"]), max(pair["a"], pair["b"])))
        judged += len(batch)
        batches += 1
        if batches % 10 == 0:
            print(f"  batch {batches}: {judged} judged, {united} united, {len(heap)} pairs left; ${SPENT:.2f}")
    print(f"clustered in {batches} batches: {judged} judged, {united} united, {len(clusters.different)} ruled different; ${SPENT:.2f}")
    return clusters.groups(keys)

# %% [markdown]
# ## Block 13: writing the parents
#
# A cluster of one is a parent copied from its child, no call. A cluster of two or more gets
# one call that picks the name and kind from what the instances carry and writes one line per
# instance; a name no instance carries is refused. Then the three tables.

# %%
def alone(members, children, docs):
    first = children[members[0]]
    doc = docs[first["doc_id"]]
    line = f"In {doc['title']}: " + (first["abstract"] or "; ".join(first["facts"][:FACTS_SHOWN]) or first["name"])
    return {"name": first["name"], "kind": first["kind"], "aliases": {first["name"], *first["aliases"]},
            "summary": [(members[0], line)], "children": members, "calls": 0}


def write_parent(members, children, docs):
    """A parent from its instances, most facts first."""
    members = sorted(members, key=most_facts_first(children))
    if len(members) == 1:
        return alone(members, children, docs)
    aliases = set()
    for key in members:
        aliases |= {children[key]["name"], *children[key]["aliases"]}
    shown = members[:GROUP_SHOWN]
    listing = "\n\n".join(f"[{n + 1}] {child_text(children[key], docs[key[0]])}\ndocument: {docs[key[0]]['title']}"
                          for n, key in enumerate(shown))
    reply = generate(WRITE.format(instances=listing, n=len(shown)), {"name": str, "kind": str, "lines": list}, "write",
                     effort="low", ctx={"parent": members[0][1], "instances": len(members)})
    first = children[members[0]]
    allowed = {fold(a) for a in aliases}
    name = reply["name"] if reply and fold(reply["name"]) in allowed else first["name"]
    kind = reply["kind"] if reply and reply.get("kind") else first["kind"]
    lines = reply["lines"] if reply and isinstance(reply["lines"], list) else []
    summary = []
    for n, key in enumerate(members):
        line = lines[n] if n < len(lines) and isinstance(lines[n], str) and lines[n].strip() else None
        summary.append((key, line or f"In {docs[key[0]]['title']}: {children[key]['name']}."))
    return {"name": name, "kind": kind, "aliases": aliases, "summary": summary, "children": members, "calls": 1}


def write_tables(db, parents, pairs):
    for table in ("parent", "instance_of", "pair"):
        db.execute(f"delete from {table}")
    joined_by = {}
    for p in pairs:
        if p["verdict"] == "same":
            joined_by.setdefault(p["a"], p)
            joined_by.setdefault(p["b"], p)
    for i, p in enumerate(parents):
        summary = "\n".join(f"[{node_id}] {line}" for ((_, node_id), line) in p["summary"])   # a node id carries its document's tag
        db.execute("insert into parent values (?,?,?,?,?,?,?)",
                   (i, p["name"], p["kind"], column(sorted(p["aliases"])), summary, len(p["children"]), p["children"][0][1]))
        for key in p["children"]:
            r = joined_by.get(key)
            scores = {k: r[k] for k in ("lexical", "vector", "cast", "cast_rare", "identity")} if r else None
            db.execute("insert into instance_of values (?,?,?,?,?)", (key[0], key[1], i, r["reason"] if r else "alone", column(scores)))
    for p in pairs:
        db.execute("insert into pair values (?,?,?,?,?,?,?,?,?,?,?,?)",
                   (p["a"][0], p["a"][1], p["b"][0], p["b"][1], p["lexical"], p["vector"], p["cast"], p["cast_rare"],
                    p["identity"], p["offered"], p["verdict"], p["reason"]))
    db.commit()


def build_parents(store):
    """Embed every child, nominate and score the pairs, cluster, write the parents and the tables."""
    db = sqlite3.connect(store)
    docs, children, rarity = read_corpus(db)
    keys = sorted(children)
    print(f"{len(docs)} documents, {len(keys)} children; signals {sorted(SIGNALS)}")
    vectors = embed([child_text(children[key], docs[key[0]]) for key in keys])
    pairs = [score_pair(children[keys[i]], children[keys[j]], hows, float(vectors[i] @ vectors[j]), rarity)
             for (i, j), hows in nominate(keys, children, vectors).items()]
    print(f"{len(pairs)} pairs nominated, {sum(p['offered'] for p in pairs)} offered to the judge")
    groups = cluster(keys, pairs, children, docs)
    multi = [m for m in groups.values() if len(m) > 1]
    print(f"{len(groups)} groups, {len(multi)} with two or more instances, the largest {max((len(m) for m in multi), default=1)}")
    parents = in_parallel(write_parent, [(members, children, docs) for members in groups.values()])
    write_tables(db, parents, pairs)
    db.close()
    print(f"written: {len(parents)} parents ({sum(p['calls'] for p in parents)} written by a call), {len(keys)} up-edges, {len(pairs)} pair rows; ${SPENT:.2f}")

# %% [markdown]
# ## Block 14: run
#
# The store, the sidecar, the parents, the parents' rows added to the sidecar, and a receipt
# with the group sizes. Without a key the parents are skipped and the rest still builds.

# %%
if __name__ == "__main__":
    if STEP1 is None or EXPORT is None:
        raise SystemExit("attach it494-threadatlas-step1 and it494-threadatlas-step0, or set STEP1 and EXPORT")
    started = now()
    counts = build_store(STEP1, EXPORT / "documents.jsonl", STORE)
    build_sidecar(STORE)
    if KEY:
        build_parents(STORE)
        extend_sidecar(STORE)
    db = sqlite3.connect(STORE)
    receipt = {"version": VERSION, "started_at": started, "finished_at": now(), "signals": sorted(SIGNALS),
               "store": counts, "parents": db.execute("select count(*) from parent").fetchone()[0],
               "parents_with_two_or_more": db.execute("select count(*) from parent where instances > 1").fetchone()[0],
               "largest_group": db.execute("select max(instances) from parent").fetchone()[0],
               "up_edges": db.execute("select count(*) from instance_of").fetchone()[0],
               "pairs": db.execute("select count(*) from pair").fetchone()[0],
               "pairs_judged": db.execute("select count(*) from pair where verdict in ('same', 'different')").fetchone()[0],
               "pairs_same": db.execute("select count(*) from pair where verdict = 'same'").fetchone()[0],
               "pairs_blocked": db.execute("select count(*) from pair where verdict = 'blocked'").fetchone()[0],
               "vectors": db.execute("select count(*) from vec_row").fetchone()[0], "cost": round(SPENT, 4)}
    db.close()
    (OUT / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))

# %% [markdown]
# ## Block 15: reading it back
#
# The parents that gathered more than one instance, with their members; the ones named Tip or
# Ozma in full; and how many clusters mix kinds beyond person and character, the quickest sign
# of a chained cluster.

# %%
if __name__ == "__main__" and STORE.exists():
    db = sqlite3.connect(STORE)
    kinds_of = {n: k for n, k in db.execute("select node_id, kind from node")}
    mixed = 0
    for pid, name, kind, n in db.execute("select parent_id, name, kind, instances from parent where instances > 1 order by instances desc"):
        members = [m for (m,) in db.execute("select node_id from instance_of where parent_id = ?", (pid,))]
        kinds = {kinds_of[m] for m in members}
        mixed += len(kinds) > 1 and not kinds <= {"person", "character"}
        print(f"{n:3}  {name:35} {kind:15} {' '.join(members)}")
    print(f"\nclusters mixing kinds beyond person and character: {mixed}")
    for name, kind, summary in db.execute("select name, kind, summary from parent where name like 'Ozma%' or name = 'Tip'"):
        print(f"\n{name} ({kind})\n{summary}")
    db.close()
