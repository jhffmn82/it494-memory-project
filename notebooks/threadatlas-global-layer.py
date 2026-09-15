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
# `threadatlas.sqlite`, `threadatlas.npy`, `build.sqlite`, `calls.jsonl`, `receipt.json` and the wiki
# pages in the output folder. Retrieval is its own pipeline over the store (`docs/retrieval.md`).
#
# ## The store
#
# The serving store keeps what a question or a page reads. The document's text stays in Step 0
# and is used at load to prove every quote. The build's evidence goes to `build.sqlite` beside it.
#
# | table | columns | meaning |
# |---|---|---|
# | `document` | doc_id, title, author, occurred_at, source_uri | the filter's unit; the date on every item |
# | `unit` | unit_id, doc_id, position, label, kind, occurred_at | order inside a document; a chapter's or a turn's label |
# | `node` | doc_id, node_id, name, kind | a document's entity |
# | `alias` | doc_id, node_id, alias | its surface forms |
# | `fact` | doc_id, fact_id, subject, subject_name, predicate, object, object_is_node, qualifiers, unit_id, quote, quote_start, quote_end, occurred_at, direction | a claim with its verbatim quote |
# | `adjudicated_fact` | doc_id, node_id, predicate, object, qualifiers, from_facts | the ingestor's consolidation, for the wiki |
# | `cell`, `abstract` | doc_id, node_id, unit_id, text; doc_id, node_id, text | the narratives |
# | `parent` | parent_id, name, kind, aliases, summary | a global entity: derived fields only |
# | `instance_of` | doc_id, node_id, parent_id | the up-edge, owned by the document |
# | `collection`, `document_in` | collection_id, name, abstract; doc_id, collection_id | a body of work and its documents |
# | `vec_header`, `vec_row` | model, dimension, built_at; row, record, doc_id, record_id, ordinal | what each row of the array is |
# | `search` | record, doc_id, record_id, text (FTS5) | one row per record: a fact's line and quote, a cell, an abstract |
#
# `build.sqlite`: `pair` (every candidate pair, its four signals, whether it was offered, the
# judge's verdict and reason) and `merge` (every union in order). With the Step 1 dataset's own
# diagnostics they are the full audit of why an entity is under its parent.
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
#             document's text at its offsets, or the load stops; one search row per record
# embed       one vector per fact line and per narrative sentence, and one per child (an
#             entity node that is not the document itself and not the user of a chat)
# nominate    candidate pairs of children, each once: the NEAREST other-document children by
#             vector (block matrix products, never a scan in Python), every two children
#             sharing a name or a naming alias (by index), and every is_a link between two
#             children of one document; each pair scored on four signals: lexical (a name or
#             alias match), vector (cosine of the two texts), cast (overlap of the names each
#             appears beside), identity (the document says one is the other); a pair is
#             OFFERED when a named signal clears its floor
# cluster     log n bottom up: every child starts as its own cluster; the offered pairs are
#             ranked by strength (an is_a link first, with no floor; then a name match; then
#             the cosine); each round every cluster takes its best eligible partner, the pairs
#             disjoint, the whole round is judged in parallel (one call about the pair's two
#             instances, each shown with what is already united with it as context: same or
#             different, with a reason), the pairs ruled same merge, and the next round is
#             drawn from the merged pool; a pair whose children already share a cluster is
#             skipped, a pair between clusters that hold any pair ruled different is blocked;
#             until a round finds no pair; every pair and verdict is logged
# mentions    a final pass over the finished clusters: a cluster whose name or alias is a
#             document's title, or whose text is nearest a document's abstract over the floor,
#             is offered that document; the judge rules with the document as the other side;
#             a cluster ruled a mention becomes that document's children, the document's own
#             node its anchor, and the parent takes the document's title
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
# ## The ablation, exactly
#
# Nomination and the floor never change between arms; the arm is what the judge is shown.
# `SIGNALS` without `cast` is the arm L+V+I: the judge sees the two entities' texts alone.
# With `cast` it is L+V+I+C: the judge also sees the names each entity appears beside. The
# question the two arms answer is whether relational evidence buys anything on top of an
# embedding nomination and a language-model judge. Dropping `lexical`, `vector` or `identity`
# from `SIGNALS` changes nomination instead and is a different experiment. The vector floor
# (0.75) was set on 2026-09-14 from the distribution of cosines over the test store and a
# handful of pairs read by eye (a true pair at 0.78, a false pair at 0.76); it is frozen here
# and is not tuned against the Oz key.
#
# After the build, two invariants hold or the run stops: every up-edge points at a written
# parent, and every child has an up-edge.
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
DOCUMENT_FLOOR = 0.85      # cosine at which a cluster is offered a document on the vector alone; a work is usually mentioned by its title
NEAREST = 8                # nearest other-document children by vector nominated per child
FACTS_SHOWN = 12           # facts of a child shown to the judge and the parent writer
SIDE_SHOWN = 6             # instances shown per side to the judge: the nominated one, then up to five united with it
GROUP_SHOWN = 20           # instances shown to the call that writes a parent, most facts first
PORTAL_ENTITIES = 200      # entities listed on a portal page, and pages written beside it
WORKERS = 16               # judge calls in flight at once; a round is judged WORKERS at a time
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
# The serving store holds what a question or a page reads and nothing else: thirteen tables and
# one full-text table with a row per record. The document's text stays in Step 0; the load
# slices every quote against it and does not keep it. What the build learned on the way (every
# candidate pair with its scores and the judge's verdict, every union) goes to `build.sqlite`
# beside the store, and Step 1's own diagnostics stay in the Step 1 dataset.

# %%
SCHEMA = """
create table document (doc_id text primary key, title text, author text, occurred_at text, source_uri text);
create table unit (unit_id text primary key, doc_id text, position integer, label text, kind text, occurred_at text);
create table node (doc_id text, node_id text, name text, kind text, primary key (doc_id, node_id));
create table alias (doc_id text, node_id text, alias text);
create table fact (doc_id text, fact_id text, subject text, subject_name text, predicate text, object text,
    object_is_node integer, qualifiers text, unit_id text, quote text, quote_start integer, quote_end integer,
    occurred_at text, direction text, primary key (doc_id, fact_id));
create table adjudicated_fact (doc_id text, node_id text, predicate text, object text, qualifiers text, from_facts text);
create table cell (doc_id text, node_id text, unit_id text, text text);
create table abstract (doc_id text, node_id text, text text);

create table parent (parent_id integer primary key, name text, kind text, aliases text, summary text);
create table instance_of (doc_id text, node_id text, parent_id integer, primary key (doc_id, node_id));
create table collection (collection_id integer primary key, name text, abstract text);
create table document_in (doc_id text, collection_id integer, primary key (doc_id, collection_id));

create table vec_header (model text, dimension integer, built_at text);
create table vec_row (row integer primary key, record text, doc_id text, record_id text, ordinal integer);
create virtual table search using fts5(record unindexed, doc_id unindexed, record_id unindexed, text);
"""

BUILD_SCHEMA = """
create table pair (doc_a text, node_a text, doc_b text, node_b text, lexical real, vector real, cast real,
    cast_rare real, identity integer, offered integer, verdict text, reason text);
create table merge (round integer, doc_a text, node_a text, doc_b text, node_b text, kept text, joined text);
"""

# %% [markdown]
# ## Block 5: loading the store
#
# The Step 1 rows go in with the columns the store keeps; a fact's quote is re-sliced from the
# document's text at its offsets and the load stops on the first mismatch (a document-record
# fact has no quote by rule and is not checked). Then the `search` rows, one per record, and a
# check that the facts and cells per document equal the completion records the ingestor wrote.

# %%
def column(value):
    """A value as SQLite stores it: nested values as JSON text, booleans as integers."""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return int(value)
    return value


def texts_of(export_documents, doc_ids):
    """doc_id -> text, from Step 0, for the documents asked for; used at load and not kept."""
    texts = {}
    with Path(export_documents).open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["doc_id"] in doc_ids:
                texts[row["doc_id"]] = row["text"]
    return texts


# the Step 1 file behind each table, and the row the store keeps of each record
ROWS = {
    "document": ("documents", ["doc_id", "title", "author", "occurred_at", "source_uri"]),
    "unit": ("units", ["unit_id", "doc_id", "position", "label", "kind", "occurred_at"]),
    "node": ("nodes", ["doc_id", "node_id", "name", "kind"]),
    "alias": ("aliases", ["doc_id", "node_id", "alias"]),
    "adjudicated_fact": ("adjudicated_facts", ["doc_id", "node_id", "predicate", "object", "qualifiers", "from_facts"]),
    "cell": ("cells", ["doc_id", "node_id", "unit_id", "text"]),
    "abstract": ("abstracts", ["doc_id", "node_id", "text"]),
}


def load_facts(db, step1, texts):
    """Every fact, its quote proven against the text; the number checked."""
    checked = 0
    for r in read_jsonl(step1 / "facts.jsonl"):
        if r["quote"] is not None:
            if texts[r["doc_id"]][r["quote_start"]:r["quote_end"]] != r["quote"]:
                raise SystemExit(f"quote of {r['fact_id']} does not slice to its text; load refused")
            checked += 1
        db.execute("insert into fact values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (r["doc_id"], r["fact_id"], r["subject"], r["provenance"].get("subject_name"), r["predicate"], r["object"],
                    int(r["object_is_node"]), r["qualifiers"], r["unit_id"], r["quote"], r["quote_start"], r["quote_end"],
                    r["occurred_at"], r["direction"]))
    return checked


def load_search(db):
    """One search row per record: a fact's line and quote, a cell's text, an abstract's text."""
    docs = {r[0]: {"title": r[1], "source_uri": r[2]} for r in db.execute("select doc_id, title, source_uri from document")}
    names = {(d, n): name for d, n, name in db.execute("select doc_id, node_id, name from node")}
    fields = ["doc_id", "fact_id", "subject", "subject_name", "predicate", "object", "object_is_node", "qualifiers", "occurred_at", "direction", "quote"]
    rows = []
    for row in db.execute(f"select {', '.join(fields)} from fact"):
        f = dict(zip(fields, row))
        local = {f["subject"]: names.get((f["doc_id"], f["subject"]), f["subject"]),
                 f["object"]: names.get((f["doc_id"], f["object"]), f["object"])}
        rows.append(("fact", f["doc_id"], f["fact_id"], fact_line(f, local, docs[f["doc_id"]]) + ("\n" + f["quote"] if f["quote"] else "")))
    rows += [("cell", d, f"{n}@{u}", text) for d, n, u, text in db.execute("select doc_id, node_id, unit_id, text from cell")]
    rows += [("abstract", d, n, text) for d, n, text in db.execute("select doc_id, node_id, text from abstract")]
    db.executemany("insert into search values (?,?,?,?)", rows)
    return len(rows)


def check_counts(step1, db):
    """Documents whose stored facts or cells differ from their completion record."""
    off = 0
    for r in read_jsonl(step1 / "completions.jsonl"):
        counts = r["counts"]
        facts = db.execute("select count(*) from fact where doc_id = ? and quote is not null", (r["doc_id"],)).fetchone()[0]
        cells = db.execute("select count(*) from cell where doc_id = ?", (r["doc_id"],)).fetchone()[0]
        off += facts != counts["facts_stored"] or cells != counts["cells"]
    return off


def build_store(step1, export_documents, path):
    """The serving store from a Step 1 folder and Step 0's documents.jsonl; build.sqlite beside it."""
    for old in (path, path.with_name("build.sqlite")):
        if old.exists():
            old.unlink()
    db = sqlite3.connect(path)
    db.executescript(SCHEMA)
    sqlite3.connect(path.with_name("build.sqlite")).executescript(BUILD_SCHEMA)
    for table, (file, fields) in ROWS.items():
        db.executemany(f"insert into {table} values ({', '.join('?' * len(fields))})",
                       [[column(r.get(f)) for f in fields] for r in read_jsonl(step1 / f"{file}.jsonl")])
    doc_ids = {r[0] for r in db.execute("select doc_id from document")}
    texts = texts_of(export_documents, doc_ids)
    missing = doc_ids - set(texts)
    if missing:
        raise SystemExit(f"{len(missing)} documents have no text in Step 0, first {sorted(missing)[0][:8]}")
    checked = load_facts(db, step1, texts)
    searchable = load_search(db)
    db.commit()
    off = check_counts(step1, db)
    counts = {t: db.execute(f"select count(*) from {t}").fetchone()[0] for t in ("document", "node", "fact", "cell", "abstract")}
    db.close()
    print(f"store: {counts}; {checked} quotes checked, all slice to their text; {searchable} search rows; "
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


def fact_text(f, names):
    """A fact as a clause: subject, predicate, object, qualifiers."""
    subject = names.get(f["subject"], f["subject"])
    if f["direction"] == "mentioned" and f["subject_name"]:    # a chat minor's fact, carried by its session
        subject = f["subject_name"]
    obj = names.get(f["object"], f["object"]) if f["object_is_node"] else f["object"]
    line = f"{subject} {f['predicate'].replace('_', ' ')} {obj}"
    return line + (f" ({f['qualifiers']})" if f["qualifiers"] else "")


def fact_line(f, names, doc):
    """A fact as the sentence a question would match: the clause, then its date and its document's title."""
    line = fact_text(f, names)
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
    fields = ["doc_id", "fact_id", "subject", "subject_name", "predicate", "object", "object_is_node", "qualifiers", "occurred_at", "direction"]
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
    db.executemany("insert into vec_row values (?,?,?,?,?)", [(i, *r[:4]) for i, r in enumerate(rows)])
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
    rows = [tuple(r) + ("",) for r in db.execute("select record, doc_id, record_id, ordinal from vec_row where record != 'parent' order by row")]
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
# A child is an entity node that is not the user of a chat. A document with a title is read
# the same way under its own node, kept apart from the clustering and used by the final pass
# that makes a document the parent of its mentions. Each is read once with its name, aliases,
# kind, summary or facts, the cast it shares units with,
# and its is_a links to siblings (the ingestor's own link: an is_a fact whose object is
# another node of the document). A cast name's rarity over the loaded documents, the log of
# (documents plus one) over (documents holding it plus one), weights the second co-occurrence
# score; a name in every document weighs almost nothing and none weighs less than zero.

# %%
def read_children(db):
    """Every child with its aliases, abstract and facts; is_a links between siblings. A document
    with a title is a child too, under its own node, so a mention of a book or a paper in another
    document can join the document itself."""
    chats = {r[0] for r in db.execute("select distinct doc_id from unit where kind in ('user', 'assistant')")}
    titled = {d for d, t, u in db.execute("select doc_id, title, source_uri from document") if not is_identifier(t, u)}
    children = {}
    for doc_id, node_id, name, kind in db.execute("select doc_id, node_id, name, kind from node"):
        if fold(name) == "user" or (node_id.endswith(":doc") and doc_id not in titled):
            continue
        children[(doc_id, node_id)] = {"doc_id": doc_id, "node_id": node_id, "name": name, "kind": kind,
                                       "aliases": [], "facts": [],
                                       "abstract": None, "cast": set(), "links": set(), "chat": doc_id in chats,
                                       "document": node_id.endswith(":doc")}
    for doc_id, alias, node_id in db.execute("select doc_id, alias, node_id from alias"):
        child = children.get((doc_id, node_id))
        if child and alias != child["name"]:
            child["aliases"].append(alias)
    for doc_id, node_id, text in db.execute("select doc_id, node_id, text from abstract"):
        if (doc_id, node_id) in children:
            children[(doc_id, node_id)]["abstract"] = text
    query = "select doc_id, subject, predicate, object, object_is_node, qualifiers, quote from fact order by doc_id, fact_id"
    for doc_id, subject, predicate, obj, is_node, qualifiers, quote in db.execute(query):
        child = children.get((doc_id, subject))
        if child is None or (quote is None and not child["document"]):
            continue
        target = children.get((doc_id, obj)) if is_node else None
        value = target["name"] if target else obj
        child["facts"].append(f"{predicate.replace('_', ' ')} {value}" + (f" ({qualifiers})" if qualifiers else ""))
        if target is not None and predicate == "is_a":
            child["links"].add(obj)
            target["links"].add(subject)
    return children


def read_casts(step1, children):
    """Each child's cast, the folded names of the children it shares a unit with, from the
    Step 1 edges (the store does not keep them)."""
    members = {}
    for e in read_jsonl(step1 / "edges.jsonl"):
        if e["predicate"] == "appears_in" and (e["doc_id"], e["subject"]) in children:
            for unit in e.get("units") or []:
                members.setdefault((e["doc_id"], unit), []).append(e["subject"])
    for (doc_id, unit), ids in members.items():
        names = {fold(children[(doc_id, i)]["name"]) for i in ids}
        for i in ids:
            children[(doc_id, i)]["cast"] |= names - {fold(children[(doc_id, i)]["name"])}
        whole = children.get((doc_id, f"{doc_id[:8]}:doc"))
        if whole is not None:
            whole["cast"] |= names


def read_corpus(db, step1):
    """docs, children and each cast name's rarity (log of documents over documents holding the name)."""
    docs = {r[0]: {"title": r[1], "source_uri": r[2], "occurred_at": r[3]}
            for r in db.execute("select doc_id, title, source_uri, occurred_at from document")}
    children = read_children(db)
    read_casts(step1, children)
    docs_with = {}
    for child in children.values():
        docs_with.setdefault(fold(child["name"]), set()).add(child["doc_id"])
    rarity = {name: math.log((len(docs) + 1) / (len(ds) + 1)) for name, ds in docs_with.items()}   # nonnegative, smoothed
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


def priority(pair):
    """A pair's place in the queue, as hard tiers: an is_a link before any name match before any
    cosine, and the cosine only within a tier."""
    return (pair["identity"], pair["lexical"], pair["vector"])

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
# Log n bottom up. Every child starts as its own cluster. Each round, every cluster takes its
# single best eligible partner (the offered pairs walked strongest first, a cluster in at most
# one pair), the whole round is judged in parallel, the pairs ruled same merge, and the next
# round is drawn from the merged pool, so the cluster count falls round by round. A pair whose
# two children already share a cluster is skipped; a pair between two clusters that hold any
# pair ruled different is blocked; a pair ruled different is never offered again.

# %%
class Clusters:
    """Union-find over children, with the members of each cluster and the pairs ruled different."""

    def __init__(self, keys):
        self.leader = {key: key for key in keys}
        self.members = {key: [key] for key in keys}
        self.different = set()
        self.joined = {}
        self.merges = []

    def find(self, key):
        while self.leader[key] != key:
            self.leader[key] = self.leader[self.leader[key]]
            key = self.leader[key]
        return key

    def unite(self, a, b, pair, round_no):
        """Join two clusters on a pair ruled same; the union is logged, and every member not yet
        joined through an earlier union remembers this one as the reason it is where it is."""
        keep, gone = (a, b) if a < b else (b, a)
        for member in self.members[a] + self.members[b]:
            self.joined.setdefault(member, pair)
        self.merges.append((round_no, pair["a"], pair["b"], keep, gone))
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


def next_round(offered, clusters):
    """Each cluster's best eligible pair this round, the pairs disjoint: walking the offered
    pairs strongest first, a pair is taken when neither of its clusters is taken yet."""
    taken, batch = set(), []
    for pair in offered:
        if pair["verdict"] is not None:
            continue
        la, lb = clusters.find(pair["a"]), clusters.find(pair["b"])
        if la == lb:
            pair["verdict"] = "skipped"                          # already one cluster through other pairs
        elif clusters.blocked(la, lb):
            pair["verdict"] = "blocked"                          # their clusters hold a pair ruled different
        elif la not in taken and lb not in taken:
            taken.add(la)
            taken.add(lb)
            batch.append((pair, list(clusters.members[la]), list(clusters.members[lb])))
    return batch


def cluster(keys, pairs, children, docs):
    """Log n bottom up: round by round, every cluster meets its best eligible partner, the whole
    round is judged in parallel, the pairs ruled same merge, and the next round is drawn from
    the merged pool; until a round finds no pair. Every child's cluster, keyed by its leader."""
    clusters = Clusters(keys)
    offered = sorted((p for p in pairs if p["offered"]), key=priority, reverse=True)
    rounds, judged, united = 0, 0, 0
    while True:
        batch = next_round(offered, clusters)
        if not batch:
            break
        in_parallel(judge_pair, [(pair, a, b, children, docs) for pair, a, b in batch])
        for pair, _, _ in batch:
            la, lb = clusters.find(pair["a"]), clusters.find(pair["b"])
            if pair["verdict"] == "same" and la != lb:
                clusters.unite(la, lb, pair, rounds + 1)
                united += 1
            elif pair["verdict"] == "different":
                clusters.different.add((min(pair["a"], pair["b"]), max(pair["a"], pair["b"])))
        judged += len(batch)
        rounds += 1
        alive = len(clusters.members)
        print(f"  round {rounds}: {len(batch)} pairs judged, {united} united so far, {alive} clusters; ${SPENT:.2f}")
    print(f"clustered in {rounds} rounds: {judged} judged, {united} united, {len(clusters.different)} ruled different; ${SPENT:.2f}")
    return clusters

# %% [markdown]
# ## Block 13: writing the parents
#
# Two kinds of parent. An entity parent stands over one finished cluster: a cluster of one is a
# copy of its child with no call; two or more instances get one call that picks the name and
# kind from what the instances carry (a name no instance carries is refused) and writes one
# line per instance. A document parent stands over the document's own node and every cluster
# the judge ruled a mention of that document: it takes the document's title and the kind
# `document`, no naming call, and one call writes the instance lines when there are mentions.
# The mentions pass runs after the clustering is finished and never puts a document into it:
# each finished cluster is offered at most one titled document, and the judge rules with the
# document as the other side. Then the tables, and two invariants.

# %%
def best_offer(members, children, documents, by_title, sims, index):
    """The one document a cluster is offered, or None: a document whose title equals a member's
    name or naming alias; else the document whose abstract is nearest a member's text over
    DOCUMENT_FLOOR. Returns (lexical, cosine, member, document index)."""
    import numpy
    best = None
    for m in members:
        forms = [children[m]["name"]] + [a for a in children[m]["aliases"] if proper(a)]
        for j in [j for form in forms for j in by_title.get(fold(form), [])]:
            best = (1.0, float(sims[index[m], j]), m, j)
        if best is None or best[0] < 1.0:
            j = int(numpy.argmax(sims[index[m]]))
            if sims[index[m], j] >= DOCUMENT_FLOOR and (best is None or sims[index[m], j] > best[1]):
                best = (0.0, float(sims[index[m], j]), m, j)
    return best


def attach_mentions(groups, keys, vectors, documents, children, docs, rarity, pairs):
    """The pass after clustering: which finished clusters are mentions of a document in the
    corpus. Every offer is judged like any pair (the cluster's members on one side, the document
    on the other) and logged in `pair`. Returns document key -> the leaders of the clusters ruled
    its mentions, so a document with two mention clusters gets both under it."""
    if not documents:
        return {}
    doc_vectors = embed([child_text(children[key], docs[key[0]]) for key in documents])
    sims = vectors @ doc_vectors.T                                 # child by document
    index = {key: i for i, key in enumerate(keys)}
    by_title = {}
    for j, key in enumerate(documents):
        by_title.setdefault(fold(children[key]["name"]), []).append(j)
    offers = []
    for leader, members in groups.items():
        best = best_offer(members, children, documents, by_title, sims, index)
        if best is not None:
            lexical, sim, m, j = best
            pair = score_pair(children[m], children[documents[j]], set(), sim, rarity)
            pair["lexical"], pair["offered"] = lexical, 1
            pairs.append(pair)
            offers.append((leader, documents[j], pair, list(members)))
    in_parallel(judge_pair, [(pair, members, [doc_key], children, docs) for _, doc_key, pair, members in offers])
    mentions = {}
    for leader, doc_key, pair, _ in offers:
        if pair["verdict"] == "same":
            mentions.setdefault(doc_key, []).append(leader)
    print(f"mentions: {len(offers)} clusters offered a document, {sum(len(v) for v in mentions.values())} ruled its mentions, "
          f"{len(mentions)} documents with mentions")
    return mentions


def alone(members, children, docs):
    first = children[members[0]]
    doc = docs[first["doc_id"]]
    line = f"In {doc['title']}: " + (first["abstract"] or "; ".join(first["facts"][:FACTS_SHOWN]) or first["name"])
    return {"name": first["name"], "kind": first["kind"], "aliases": {first["name"], *first["aliases"]},
            "summary": [(members[0], line)], "children": members, "calls": 0}


def instance_lines(members, children, docs, reply):
    """One summary line per instance, tagged later with the instance's id: the call's line when
    it wrote one, else a plain line naming the instance in its document."""
    lines = reply["lines"] if reply and isinstance(reply["lines"], list) else []
    summary = []
    for n, key in enumerate(members):
        line = lines[n] if n < len(lines) and isinstance(lines[n], str) and lines[n].strip() else None
        summary.append((key, line or f"In {docs[key[0]]['title']}: {children[key]['name']}."))
    return summary


def write_parent(members, children, docs):
    """A parent from its instances, most facts first. A document parent (its first member is the
    document's own node) keeps the document's title and the kind `document`; the call only
    writes the instance lines. An entity parent lets the call pick the name and kind too."""
    document = children[members[0]]["document"]
    members = members[:1] + sorted(members[1:], key=most_facts_first(children)) if document else sorted(members, key=most_facts_first(children))
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
    if document:
        name, kind = first["name"], "document"
    else:
        name = reply["name"] if reply and fold(reply["name"]) in {fold(a) for a in aliases} else first["name"]
        kind = reply["kind"] if reply and reply.get("kind") else first["kind"]
    return {"name": name, "kind": kind, "aliases": aliases, "summary": instance_lines(members, children, docs, reply),
            "children": members, "calls": 1}


def write_tables(db, store, parents, pairs, clusters):
    """The parents and up-edges into the store; the pairs and unions into build.sqlite."""
    db.execute("delete from parent")
    db.execute("delete from instance_of")
    for i, p in enumerate(parents):
        summary = "\n".join(f"[{node_id}] {line}" for ((_, node_id), line) in p["summary"])   # a node id carries its document's tag
        db.execute("insert into parent values (?,?,?,?,?)", (i, p["name"], p["kind"], column(sorted(p["aliases"])), summary))
        db.executemany("insert into instance_of values (?,?,?)", [(key[0], key[1], i) for key in p["children"]])
    db.commit()
    orphans = db.execute("select count(*) from instance_of i left join parent p on p.parent_id = i.parent_id where p.parent_id is null").fetchone()[0]
    unplaced = db.execute("""select count(*) from node n left join instance_of i on i.doc_id = n.doc_id and i.node_id = n.node_id
                             where n.node_id not like '%:doc' and n.name != 'user' and i.parent_id is null""").fetchone()[0]
    if orphans or unplaced:
        raise SystemExit(f"invariant broken: {orphans} up-edges point at no written parent, {unplaced} children have no up-edge")
    log = sqlite3.connect(store.with_name("build.sqlite"))
    log.execute("delete from pair")
    log.execute("delete from merge")
    log.executemany("insert into pair values (?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(p["a"][0], p["a"][1], p["b"][0], p["b"][1], p["lexical"], p["vector"], p["cast"], p["cast_rare"],
                      p["identity"], p["offered"], p["verdict"], p["reason"]) for p in pairs])
    log.executemany("insert into merge values (?,?,?,?,?,?,?)",
                    [(r, a[0], a[1], b[0], b[1], keep[1], gone[1]) for r, a, b, keep, gone in clusters.merges])
    log.commit()
    log.close()


def build_parents(store, step1):
    """Embed every child, nominate and score the pairs, cluster, write the parents and the tables."""
    db = sqlite3.connect(store)
    docs, children, rarity = read_corpus(db, step1)
    keys = sorted(key for key in children if not children[key]["document"])
    documents = sorted(key for key in children if children[key]["document"])
    print(f"{len(docs)} documents, {len(keys)} children, {len(documents)} titled documents; signals {sorted(SIGNALS)}")
    vectors = embed([child_text(children[key], docs[key[0]]) for key in keys])
    pairs = [score_pair(children[keys[i]], children[keys[j]], hows, float(vectors[i] @ vectors[j]), rarity)
             for (i, j), hows in nominate(keys, children, vectors).items()]
    print(f"{len(pairs)} pairs nominated, {sum(p['offered'] for p in pairs)} offered to the judge")
    clusters = cluster(keys, pairs, children, docs)
    groups = clusters.groups(keys)
    multi = [m for m in groups.values() if len(m) > 1]
    print(f"{len(groups)} groups, {len(multi)} with two or more instances, the largest {max((len(m) for m in multi), default=1)}")
    mentions = attach_mentions(groups, keys, vectors, documents, children, docs, rarity, pairs)
    for doc_key in documents:                            # a document is a parent: its own node first, then its mentions
        groups[doc_key] = [doc_key] + [m for leader in mentions.get(doc_key, []) for m in groups.pop(leader)]
    parents = in_parallel(write_parent, [(members, children, docs) for members in groups.values()])
    write_tables(db, store, parents, pairs, clusters)
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
        build_parents(STORE, STEP1)
        extend_sidecar(STORE)
    db = sqlite3.connect(STORE)
    log = sqlite3.connect(STORE.with_name("build.sqlite"))
    sizes = "select count(*) as n from instance_of group by parent_id"
    receipt = {"version": VERSION, "started_at": started, "finished_at": now(), "signals": sorted(SIGNALS),
               "store": counts, "parents": db.execute("select count(*) from parent").fetchone()[0],
               "parents_with_two_or_more": db.execute(f"select count(*) from ({sizes}) where n > 1").fetchone()[0],
               "largest_group": db.execute(f"select max(n) from ({sizes})").fetchone()[0],
               "up_edges": db.execute("select count(*) from instance_of").fetchone()[0],
               "pairs": log.execute("select count(*) from pair").fetchone()[0],
               "pairs_judged": log.execute("select count(*) from pair where verdict in ('same', 'different')").fetchone()[0],
               "pairs_same": log.execute("select count(*) from pair where verdict = 'same'").fetchone()[0],
               "pairs_blocked": log.execute("select count(*) from pair where verdict = 'blocked'").fetchone()[0],
               "vectors": db.execute("select count(*) from vec_row").fetchone()[0], "cost": round(SPENT, 4)}
    db.close()
    log.close()
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
    query = """select p.parent_id, p.name, p.kind, count(*) as n from parent p join instance_of i on i.parent_id = p.parent_id
               group by p.parent_id having n > 1 order by n desc"""
    for pid, name, kind, n in db.execute(query).fetchall():
        members = [m for (m,) in db.execute("select node_id from instance_of where parent_id = ?", (pid,))]
        kinds = {kinds_of[m] for m in members}
        mixed += len(kinds) > 1 and not kinds <= {"person", "character"}
        print(f"{n:3}  {name:35} {kind:15} {' '.join(members)}")
    print(f"\nclusters mixing kinds beyond person and character: {mixed}")
    for name, kind, summary in db.execute("select name, kind, summary from parent where name like 'Ozma%' or name = 'Tip'"):
        print(f"\n{name} ({kind})\n{summary}")
    db.close()

# %% [markdown]
# ## Block 15b: the Oz key
#
# The one external key: Wikipedia's list of the characters L. Frank Baum created (CC BY-SA 4.0,
# `jhffmn/it494-threadatlas-oz-key`; built by `scripts/build_oz_key.py`, the hand-added aliases
# counted). A child of one of the three Oz books matches a character when its name or an alias
# folds to one of the character's names. The key says which matched children are one identity;
# the store says which share a parent. Scored over cross-document pairs of matched children:
# recall (pairs of one character under one parent), wrong joins (pairs of two characters under
# one parent), and per character the number of parents its children span. Children the key does
# not name (places, objects, events, the minor cast) are outside the score.

# %%
KAGGLE_OZ_KEY = (Path("/kaggle/input/datasets/jhffmn/it494-threadatlas-oz-key"), Path("/kaggle/input/it494-threadatlas-oz-key"))
OZ_KEY = first_existing("OZ_KEY", *KAGGLE_OZ_KEY) or Path("data/benchmarks/oz-key")


def read_key(folder):
    """fold(name) -> character, over every character's names; a name two characters share is dropped."""
    key = json.loads((folder / "oz-key.json").read_text(encoding="utf-8"))
    owner, shared = {}, set()
    for c in key["characters"]:
        for alias in c["aliases"]:
            f = fold(alias)
            if f in owner and owner[f] != c["name"]:
                shared.add(f)
            owner.setdefault(f, c["name"])
    for f in shared:
        owner.pop(f, None)
    return key, owner


def match_key(db, key, owner):
    """(doc_id, node_id) -> character, for the children of the key's books whose name or alias the key names."""
    books = {d: t for d, t in db.execute("select doc_id, title from document") if t in key["books"]}
    aliases = {}
    for doc_id, node_id, alias in db.execute("select doc_id, node_id, alias from alias"):
        if doc_id in books:
            aliases.setdefault((doc_id, node_id), []).append(alias)
    matched, unmatched = {}, []
    for doc_id, node_id, name, kind in db.execute("select doc_id, node_id, name, kind from node"):
        if doc_id not in books or node_id.endswith(":doc"):
            continue
        hits = {owner[f] for f in [fold(name)] + [fold(a) for a in aliases.get((doc_id, node_id), [])] if f in owner}
        if len(hits) == 1:
            matched[(doc_id, node_id)] = hits.pop()
        elif kind in ("person", "animal", "creature", "character"):
            unmatched.append((books[doc_id], name, kind, sorted(hits)))
    return books, matched, unmatched


def score_key(db, books, matched):
    """The score: cross-document pairs of one character united or split; pairs of two characters joined."""
    parent = {(d, n): p for d, n, p in db.execute("select doc_id, node_id, parent_id from instance_of")}
    by_character = {}
    for child, character in matched.items():
        by_character.setdefault(character, []).append(child)
    rows, united, split, joined = [], 0, 0, []
    for character, children in sorted(by_character.items()):
        docs = {c[0] for c in children}
        parents = {parent.get(c) for c in children}
        pairs = [(a, b) for i, a in enumerate(children) for b in children[i + 1:] if a[0] != b[0]]
        same = sum(parent.get(a) == parent.get(b) for a, b in pairs)
        united += same
        split += len(pairs) - same
        rows.append((character, len(children), len(docs), len(parents), same, len(pairs) - same))
    children = sorted(matched)
    for i, a in enumerate(children):
        for b in children[i + 1:]:
            if matched[a] != matched[b] and parent.get(a) == parent.get(b) and parent.get(a) is not None:
                joined.append((matched[a], matched[b], books[a[0]], books[b[0]]))
    return rows, united, split, joined


def report_key(store):
    """Match, score, print and write oz-score.json beside the store."""
    key, owner = read_key(OZ_KEY)
    db = sqlite3.connect(store)
    books, matched, unmatched = match_key(db, key, owner)
    rows, united, split, joined = score_key(db, books, matched)
    db.close()
    scorable = [r for r in rows if r[2] > 1]
    recall = united / (united + split) if united + split else None
    print(f"key: {len(key['characters'])} characters, revision {key['revision']}; {len(books)} books in the store; "
          f"{len(matched)} children matched, {len(unmatched)} named persons or animals unmatched")
    print(f"{len(scorable)} characters in two or more books; cross-document pairs: {united} united, {split} split; "
          f"recall {recall if recall is None else round(recall, 3)}; {len(joined)} wrong joins")
    print(f"{'character':34} children  docs  parents  united  split")
    for character, n, docs, parents, same, apart in scorable:
        flag = "" if parents == 1 else "  <- split" if parents > 1 else ""
        print(f"{character:34} {n:8} {docs:5} {parents:8} {same:7} {apart:6}{flag}")
    for a, b, da, dbk in joined[:20]:
        print(f"  wrong join: {a} ({da}) with {b} ({dbk})")
    for book, name, kind, hits in unmatched[:40]:
        print(f"  unmatched: {name} ({kind}, {book}){' ambiguous ' + str(hits) if hits else ''}")
    score = {"revision": key["revision"], "matched": len(matched), "unmatched_named": len(unmatched), "scorable": len(scorable),
             "united": united, "split": split, "recall": recall, "wrong_joins": len(joined),
             "characters": [{"character": c, "children": n, "documents": d, "parents": p, "united": u, "split": s} for c, n, d, p, u, s in rows],
             "joined": [list(j) for j in joined], "unmatched": [list(u) for u in unmatched]}
    (store.parent / "oz-score.json").write_text(json.dumps(score, ensure_ascii=False, indent=1), encoding="utf-8")
    return score


if __name__ == "__main__" and STORE.exists() and (OZ_KEY / "oz-key.json").exists():
    report_key(STORE)

# %% [markdown]
# ## Block 16: collections, a parent for each body of work
#
# A collection is a parent over documents, the entry point of a portal in the wiki. It is
# seeded by the entities: every parent held by two or more documents names a group of
# documents; groups that share at least `OVERLAP` of the smaller group's documents merge into
# one collection (so a group inside a larger one always joins it); a document belongs to every collection whose seed parents it holds, so a
# session about a store and a trip sits under both. A collection always has more than one
# document. One call per collection names the body of work the way a reader would (a series,
# a field, one person's history) and writes an abstract of what the documents are and which
# entities span them, from the documents' abstracts and the shared parents; it asserts nothing
# beyond them. Without a key the name is "Works around" the most distinctive shared parent and
# the abstract the counts; a keyed run replaces both.
# Tables: `collection` (id, name, abstract) and `document_in`
# (doc_id, collection_id), one row per membership.

# %%
OVERLAP = 0.5              # two seed groups merge when their shared documents are this share of the smaller group or more

COLLECTION = """Below are the documents of one body of work, found because they share the entities listed after
them, and the abstract of each. Name the body of work the way a reader would look for it: a series by its
series name, papers by their field, one person's chat sessions by what they are about. Then write an
abstract of three to five sentences saying what the documents are, what they cover, and which entities
recur across them. Say only what the abstracts below say; name nothing that is not in them.

Documents:
{documents}

Entities shared across them, most distinctive first:
{parents}

Reply with a JSON object: {{"name": "<name>", "abstract": "<three to five sentences>"}}."""

COLLECTION_SCHEMA = """
delete from collection;
delete from document_in;
"""


def parent_groups(db):
    """parent_id -> the documents holding it, for parents held by two or more documents."""
    holders = {}
    for doc_id, parent_id in db.execute("select doc_id, parent_id from instance_of"):
        holders.setdefault(parent_id, set()).add(doc_id)
    return {pid: ds for pid, ds in holders.items() if len(ds) > 1}


def collection_groups(groups):
    """Seed groups merged when the smaller shares OVERLAP of its documents with the other; each collection as (seed parents, documents)."""
    leader = {pid: pid for pid in groups}

    def find(pid):
        while leader[pid] != pid:
            leader[pid] = leader[leader[pid]]
            pid = leader[pid]
        return pid

    pids = sorted(groups)
    for i, a in enumerate(pids):
        for b in pids[i + 1:]:
            if len(groups[a] & groups[b]) / min(len(groups[a]), len(groups[b])) >= OVERLAP:
                ra, rb = find(a), find(b)
                if ra != rb:
                    leader[max(ra, rb)] = min(ra, rb)
    merged = {}
    for pid in pids:
        seeds, docs = merged.setdefault(find(pid), ([], set()))
        seeds.append(pid)
        docs |= groups[pid]
    return sorted(merged.values(), key=collection_size, reverse=True)


def collection_size(item):
    return (len(item[1]), len(item[0]))


def shared_parents(db, group):
    """The parents held by two or more documents of the group, most distinctive first."""
    placeholders = ", ".join("?" * len(group))
    rows = db.execute(f"""select p.parent_id, p.name, p.kind, count(distinct i.doc_id) as n
                          from instance_of i join parent p on p.parent_id = i.parent_id
                          where i.doc_id in ({placeholders}) group by p.parent_id having n > 1""", list(group)).fetchall()
    total = db.execute("select count(*) from document").fetchone()[0]
    held = {pid: db.execute("select count(distinct doc_id) from instance_of where parent_id = ?", (pid,)).fetchone()[0] for pid, _, _, _ in rows}
    return sorted(rows, key=weight_of(total, held), reverse=True)


def weight_of(total, held):
    def weight(row):
        return row[3] * math.log(total / held[row[0]])
    return weight


def write_collection(db, group):
    """One collection named and described; the counts when there is no key."""
    group = sorted(group)
    marks = ", ".join("?" * len(group))
    titles = db.execute(f"select doc_id, title, occurred_at from document where doc_id in ({marks}) order by occurred_at", group).fetchall()
    abstracts = dict(db.execute(f"select doc_id, text from abstract where node_id like '%:doc' and doc_id in ({marks})", group).fetchall())
    parents = shared_parents(db, group)
    listing = "\n\n".join(f"- {title} ({date}): {(abstracts.get(doc_id) or '')[:500]}" for doc_id, title, date in titles)
    named = ", ".join(f"{name} ({kind}, in {n} of them)" for _, name, kind, n in parents[:15])
    reply = None
    if KEY:
        reply = generate(COLLECTION.format(documents=listing, parents=named or "(none)"), {"name": str, "abstract": str}, "collection",
                         effort="low", ctx={"documents": len(group)})
    if reply:
        return reply["name"], reply["abstract"], "call"
    name = f"Works around {parents[0][1]}" if parents else "Works"
    abstract = f"{len(group)} documents, from {titles[0][2]} to {titles[-1][2]}, sharing {len(parents)} entities: {named}."
    return name, abstract, "counts"


def build_collections(store):
    """The collections and their memberships, written from scratch."""
    db = sqlite3.connect(store)
    db.executescript(COLLECTION_SCHEMA)
    collections = collection_groups(parent_groups(db))
    for i, (seeds, docs) in enumerate(collections):
        name, abstract, how = write_collection(db, docs)
        db.execute("insert into collection values (?,?,?)", (i, name, abstract))
        db.executemany("insert into document_in values (?,?)", [(d, i) for d in sorted(docs)])
        print(f"  collection {i}: {name} ({len(docs)} documents from {len(seeds)} seed parents, {how})")
    db.commit()
    shared = db.execute("select count(*) from (select doc_id from document_in group by doc_id having count(*) > 1)").fetchone()[0]
    db.close()
    print(f"collections: {len(collections)}; documents in more than one: {shared}; ${SPENT:.2f}")


if __name__ == "__main__" and STORE.exists():
    build_collections(STORE)

# %% [markdown]
# ## Block 17: the collection figure
#
# The collections as parents and their documents as leaves, a document in two collections
# between its hubs: each collection a hub on a ring with its documents fanned around it. Drawn
# from the store, written as an SVG beside it, shown inline at the end of the block.

# %%
def slug(name, number=None):
    """A file name from a name, with the record's number so two parents named alike never collide."""
    base = re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-")
    return base if number is None else f"{base}-{number}"


def doc_slug(doc_id):
    return "doc-" + doc_id[:12]


def crumbs(db, doc_ids):
    """'Part of' the collections these documents belong to, each a link up to its portal."""
    marks = ", ".join("?" * len(doc_ids))
    rows = db.execute(f"""select distinct c.collection_id, c.name from document_in i join collection c on c.collection_id = i.collection_id
                          where i.doc_id in ({marks}) order by c.name""", list(doc_ids)).fetchall()
    if not rows:
        return ""
    return "Part of " + ", ".join(f'<a href="{slug(name, f"c{cid}")}.html">{escape(name)}</a>' for cid, name in rows)


def draw_collection_radial(store, out):
    """The static figure: collections on a ring, their documents fanned around each."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import pyplot
    db = sqlite3.connect(store)
    titles = dict(db.execute("select doc_id, title from document"))
    hubs = [{"id": f"c{c}", "label": name} for c, name in db.execute("select collection_id, name from collection")]
    members = {}
    for d, c in db.execute("select doc_id, collection_id from document_in"):
        members.setdefault(f"c{c}", []).append(d)
    db.close()
    count = {}
    for ds in members.values():
        for d in ds:
            count[d] = count.get(d, 0) + 1
    docs = {d: {"label": titles[d], "shared": n > 1} for d, n in count.items()}
    links = [{"source": h, "target": d} for h, ds in members.items() for d in ds]
    pos = {}
    R = 10.0
    for i, hub in enumerate(hubs):
        angle = 2 * math.pi * i / len(hubs)
        pos[hub["id"]] = (R * math.cos(angle), R * math.sin(angle))
    for hub in hubs:
        hx, hy = pos[hub["id"]]
        own = [d for d in members[hub["id"]] if not docs[d]["shared"]]
        base = math.atan2(hy, hx)
        for j, d in enumerate(own):
            a = base + (j - (len(own) - 1) / 2) * (math.pi / max(len(own), 4))
            pos[d] = (hx + 3.2 * math.cos(a), hy + 3.2 * math.sin(a))
    for d, n in docs.items():
        if n["shared"]:
            xs = [pos[h["id"]] for h in hubs if d in members[h["id"]]]
            pos[d] = (sum(x for x, _ in xs) / len(xs) * 0.55, sum(y for _, y in xs) / len(xs) * 0.55)
    figure, axis = pyplot.subplots(figsize=(15, 15))
    for l in links:
        (x1, y1), (x2, y2) = pos[l["source"]], pos[l["target"]]
        axis.plot([x1, x2], [y1, y2], color="#9aa5b1", linewidth=0.9, alpha=0.7, zorder=1)
    for d, n in docs.items():
        x, y = pos[d]
        axis.scatter([x], [y], s=70, c="#e0a73b" if n["shared"] else "#7aa6c2", edgecolors="white", zorder=2)
        axis.annotate(n["label"][:30], (x, y), fontsize=7, xytext=(5, 3), textcoords="offset points", color="#23303f")
    for hub in hubs:
        x, y = pos[hub["id"]]
        axis.scatter([x], [y], s=700, c="#b4552a", edgecolors="white", linewidths=2, zorder=3)
        axis.annotate(hub["label"][:38], (x, y), fontsize=10, fontweight="bold", ha="center", xytext=(0, 16), textcoords="offset points", color="#1f3d4a")
    axis.set_aspect("equal")
    axis.set_axis_off()
    axis.set_title("collections and their documents (gold: a document in more than one collection)", color="#1f3d4a")
    figure.savefig(out / "collection-radial.svg", bbox_inches="tight", facecolor="#fbf7f0")
    pyplot.close(figure)
    print(f"collection-radial.svg: {len(hubs)} collections, {len(docs)} documents")


def show_figure(path):
    """The figure inline when this runs in a notebook; nothing otherwise."""
    try:
        from IPython.display import SVG, display
        display(SVG(filename=str(path)))
    except ImportError:
        pass


if __name__ == "__main__" and STORE.exists():
    draw_collection_radial(STORE, OUT)
    show_figure(OUT / "collection-radial.svg")

# %% [markdown]
# ## Block 18: a wiki page
#
# One function renders a page for any parent from the store: the parent's paragraph (its
# summary lines) at the top; then a section per instance with the instance's abstract and its
# cells as paragraphs in unit order, each under its unit's label (a chapter, or a chat turn's
# time), a summary of the entity's part in that document; and, on the right, the instance's
# facts in order of appearance: the consolidated facts where the ingestor wrote them, each
# opening to the raw facts and quotes behind it, else the raw facts one line per distinct claim. Read only; nothing is written back. The run writes a sample page beside the store;
# the Ozma page is the mock-up kept in the repository under `docs/wiki/`.

# %%
def sentence(fact, names):
    """A fact as a sentence: subject, predicate, object, qualifiers."""
    subject = names.get(fact["subject"], fact["subject"])
    obj = names.get(fact["object"], fact["object"]) if fact["object_is_node"] else fact["object"]
    line = f"{subject} {fact['predicate'].replace('_', ' ')} {obj}"
    if fact["qualifiers"]:
        line += f" ({fact['qualifiers']})"
    return line[0].upper() + line[1:] + "."


def escape(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


PALETTES = {
    "harbour": "--ink: #23303f; --muted: #6b7484; --accent: #b4552a; --band: #1f3d4a; --band-ink: #f6f1e7; --band-muted: #b8c6bf; --paper: #fbf7f0; --card: #f1ebdf; --link: #1f5f8b;",
    "parchment": "--ink: #2e2419; --muted: #7a6a58; --accent: #8c2f2f; --band: #efe6d3; --band-ink: #2e2419; --band-muted: #7a6a58; --paper: #f8f3e8; --card: #efe6d3; --link: #5b3d8c;",
    "emerald": "--ink: #1c2a24; --muted: #5f716a; --accent: #c99a2e; --band: #163f34; --band-ink: #f4f1e6; --band-muted: #b7cbc1; --paper: #f7f6f1; --card: #e9efe8; --link: #1f6b56;",
    "slate": "--ink: #1f2933; --muted: #6b7a88; --accent: #b0532c; --band: #e6edf4; --band-ink: #1f2933; --band-muted: #5d6f82; --paper: #ffffff; --card: #f6f7f9; --link: #2455a4; --rule: #e4e7eb; --tint: #c9d6e3;",
}
PALETTE = os.environ.get("PALETTE", "slate")

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{name}</title>
<style>
:root {{ {palette} }}
body {{ font-family: Georgia, "Times New Roman", serif; margin: 0; color: var(--ink); background: var(--paper); line-height: 1.5; }}
header {{ background: var(--band); color: var(--band-ink); padding: 1.6rem 0; border-bottom: 2px solid var(--tint, var(--rule, #e4e7eb)); }}
header .inner {{ max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }}
header h1 {{ font-size: 2.2rem; margin: 0; font-weight: normal; letter-spacing: 0.01em; }}
header .kind {{ color: var(--band-muted); font-style: italic; margin-top: 0.3rem; }}
header .aliases {{ color: var(--band-muted); font-size: 0.85rem; margin-top: 0.5rem; }}
header .crumb {{ color: var(--band-muted); font-size: 0.9rem; margin-top: 0.4rem; }} header .crumb a {{ color: var(--band-ink); }}
.wrap {{ display: flex; gap: 2.5rem; max-width: 1200px; margin: 0 auto; padding: 1.5rem; }}
main {{ flex: 3; min-width: 0; }}
aside {{ flex: 1.3; min-width: 280px; font-size: 0.9rem; background: var(--card); border: 1px solid var(--tint, var(--rule, #e4e7eb)); border-radius: 6px; padding: 1rem 1.2rem; align-self: flex-start; }}
aside h2 {{ margin-top: 0; }}
h2 {{ font-size: 1.25rem; color: var(--ink); border-bottom: 1px solid var(--tint, var(--rule, #e4e7eb)); padding-bottom: 0.2rem; margin-top: 2.2rem; }}
h3 {{ font-size: 0.95rem; color: var(--accent); margin: 1.4rem 0 0.4rem; text-transform: uppercase; letter-spacing: 0.06em; }}
h4 {{ font-size: 0.8rem; color: var(--accent); margin: 1.1rem 0 0.1rem; font-weight: normal; text-transform: uppercase; letter-spacing: 0.08em; }}
.lead {{ font-size: 1.1rem; color: var(--ink); }}
.cell {{ margin: 0.3rem 0 0.8rem; }} .doc {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 0.4rem; }}
.facts p, details {{ margin: 0.45rem 0; }} summary {{ cursor: pointer; color: var(--ink); }} summary:hover {{ color: var(--accent); }}
details p {{ margin: 0.3rem 0 0.3rem 1rem; }}
.quote {{ color: var(--muted); font-size: 0.8rem; display: block; margin-top: 0.15rem; font-style: italic; }}
a {{ color: var(--link); text-decoration: none; }} a:hover {{ text-decoration: underline; }}
aside li {{ margin: 0.35rem 0; }} aside ul {{ padding-left: 1.1rem; }}
</style></head><body>
<header><div class="inner"><h1>{name}</h1><div class="kind">{kind}, in {n} {documents}</div><div class="crumb">{crumb}</div><div class="aliases">Also called: {aliases}</div></div></header>
<div class="wrap">
<main>
<p class="lead">{lead}</p>
{sections}
</main>
<aside><h2>Facts, in order of appearance</h2><div class="facts">{facts}</div></aside>
</div></body></html>
"""


DOCUMENT = PAGE.replace("<div class=\"kind\">{kind}, in {n} {documents}</div><div class=\"crumb\">{crumb}</div><div class=\"aliases\">Also called: {aliases}</div>",
                        "<div class=\"kind\">{record}</div><div class=\"crumb\">{crumb}</div><div class=\"aliases\">{uri}</div>").replace(
    "<aside><h2>Facts, in order of appearance</h2><div class=\"facts\">{facts}</div></aside>",
    "<aside><h2>Entities in this document ({n})</h2><ul>{entities}</ul></aside>").replace("{name}", "{title}").replace("{sections}", "{summaries}")


def document_page(db, doc_id):
    """The HTML of one document's page: its record, its abstract, its unit summaries in order,
    and the entities it holds, each linking to its parent's page."""
    title, author, date, uri = db.execute("select title, author, occurred_at, source_uri from document where doc_id = ?", (doc_id,)).fetchone()
    tag = doc_id[:8]
    abstract = db.execute("select text from abstract where doc_id = ? and node_id = ?", (doc_id, f"{tag}:doc")).fetchone()
    cells = db.execute("""select c.text, u.label from cell c join unit u on u.unit_id = c.unit_id
                          where c.doc_id = ? and c.node_id = ? order by u.position""", (doc_id, f"{tag}:doc")).fetchall()
    if not cells:                                   # a chat has no unit summaries; its turns' facts stand in
        cells = db.execute("""select group_concat(f.object, ' '), u.label from fact f join unit u on u.unit_id = f.unit_id
                              where f.doc_id = ? and f.direction = 'mentioned' group by u.position order by u.position""", (doc_id,)).fetchall()
    summaries = "".join(f'<h4>{escape(unit_heading(label))}</h4><p class="cell">{escape(text)}</p>' for text, label in cells)
    entities = db.execute("""select n.node_id, n.name, n.kind, p.parent_id, p.name,
                             (select count(*) from instance_of j where j.parent_id = p.parent_id) from node n
                             left join instance_of i on i.doc_id = n.doc_id and i.node_id = n.node_id
                             left join parent p on p.parent_id = i.parent_id
                             where n.doc_id = ? and n.node_id != ? and n.name != 'user'
                             order by (select count(*) from fact f where f.doc_id = n.doc_id and f.subject = n.node_id) desc""", (doc_id, f"{tag}:doc")).fetchall()
    items = []
    for node_id, name, kind, pid, pname, instances in entities[:60]:
        link = f'<a href="{slug(pname, pid)}.html">{escape(name)}</a>' if pname else escape(name)
        more = f", with {instances - 1} more" if instances and instances > 1 else ""
        items.append(f'<li>{link} <span class="kind">{escape(kind or "")}{more}</span></li>')
    record = f"{escape(author or 'author unknown')}, {escape(date or 'undated')}"
    return DOCUMENT.format(palette=PALETTES[PALETTE], crumb=crumbs(db, [doc_id]), title=escape(title), record=record, uri=escape(uri),
                           lead=escape(abstract[0] if abstract else ""), summaries=summaries, entities="".join(items), n=len(entities))


def write_document_page(store, out, doc_id):
    db = sqlite3.connect(store)
    (out / "wiki").mkdir(exist_ok=True)
    path = out / "wiki" / (doc_slug(doc_id) + ".html")
    path.write_text(document_page(db, doc_id), encoding="utf-8")
    db.close()
    return path


def unit_heading(label):
    """A cell's heading: the unit's label; a chat turn's label becomes its turn and time."""
    match = re.match(r"SESSION \S+ TURN (\d+) (\S+)", label or "")
    if match:
        return f"turn {match.group(1)}, {match.group(2).replace('T', ' ')}"
    return label or ""


def instance_section(db, doc_id, node_id, title, date, names):
    """One instance: its abstract, then its cells in unit order, each under its unit's label."""
    abstract = db.execute("select text from abstract where doc_id = ? and node_id = ?", (doc_id, node_id)).fetchone()
    cells = db.execute("""select c.text, u.label from cell c join unit u on u.unit_id = c.unit_id
                          where c.doc_id = ? and c.node_id = ? order by u.position""", (doc_id, node_id)).fetchall()
    paragraphs = "".join(f'<h4>{escape(unit_heading(label))}</h4><p class="cell">{escape(text)}</p>' for text, label in cells)
    return (f"<h2>{escape(names.get(node_id, node_id))} in <a href=\"{doc_slug(doc_id)}.html\">{escape(title)}</a></h2>"
            f'<div class="doc">{escape(title)}, {escape(date)}</div>'
            f"<p><em>{escape(abstract[0] if abstract else '')}</em></p>{paragraphs}")


def raw_facts(db, doc_id, node_id):
    """fact_id -> the fact row, in order of appearance."""
    rows = db.execute("""select f.fact_id, f.subject, f.predicate, f.object, f.object_is_node, f.qualifiers, f.quote, u.position
                         from fact f left join unit u on u.unit_id = f.unit_id
                         where f.doc_id = ? and f.subject = ? and f.quote is not null order by u.position, f.fact_id""", (doc_id, node_id)).fetchall()
    return {r[0]: {"subject": r[1], "predicate": r[2], "object": r[3], "object_is_node": r[4], "qualifiers": r[5], "quote": r[6], "position": r[7]}
            for r in rows}


def quoted(fact, names):
    return f'<p>{escape(sentence(fact, names))}<span class="quote">&ldquo;{escape(fact["quote"][:200])}&rdquo;</span></p>'


def instance_facts(db, doc_id, node_id, title, names):
    """One instance's facts. A major the ingestor consolidated shows its adjudicated facts, each
    opening to the raw facts and quotes behind it; otherwise the raw facts, one line per distinct
    claim, with how often it was stated."""
    facts = raw_facts(db, doc_id, node_id)
    parts = [f"<h3>{escape(title)}</h3>"]
    adjudicated = db.execute("select predicate, object, qualifiers, from_facts from adjudicated_fact where doc_id = ? and node_id = ?", (doc_id, node_id)).fetchall()
    if adjudicated:
        rows = []
        for predicate, obj, qualifiers, from_facts in adjudicated:
            behind = [facts[i] for i in json.loads(from_facts) if i in facts]
            first = min((f["position"] or 0 for f in behind), default=10 ** 6)
            rows.append((first, {"subject": node_id, "predicate": predicate, "object": obj, "object_is_node": False, "qualifiers": qualifiers}, behind))
        for _, fact, behind in sorted(rows, key=first_position):
            inner = "".join(quoted(f, names) for f in behind)
            parts.append(f"<details><summary>{escape(sentence(fact, names))}</summary>{inner}</details>")
        return "".join(parts)
    seen = {}
    for fact in facts.values():
        key = (fact["predicate"], fold(fact["object"]))
        if key in seen:
            seen[key]["count"] += 1
        else:
            seen[key] = dict(fact, count=1)
    for fact in seen.values():
        times = f' <span class="quote">stated {fact["count"]} times</span>' if fact["count"] > 1 else ""
        parts.append(f'<p>{escape(sentence(fact, names))}{times}<span class="quote">&ldquo;{escape(fact["quote"][:200])}&rdquo;</span></p>')
    return "".join(parts)


def first_position(row):
    return row[0]


def wiki_page(db, parent_id):
    """The HTML of one parent's page."""
    name, kind, aliases, summary = db.execute("select name, kind, aliases, summary from parent where parent_id = ?", (parent_id,)).fetchone()
    instances = db.execute("""select i.doc_id, i.node_id, d.title, d.occurred_at from instance_of i join document d on d.doc_id = i.doc_id
                              where i.parent_id = ? order by d.occurred_at, d.source_uri""", (parent_id,)).fetchall()
    names = dict(db.execute("select node_id, name from node"))
    lead = " ".join(line.split("] ", 1)[1] if "] " in line else line for line in summary.split("\n"))
    sections = "".join(instance_section(db, d, n, title, date, names) for d, n, title, date in instances)
    facts = "".join(instance_facts(db, d, n, title, names) for d, n, title, _ in instances)
    return PAGE.format(palette=PALETTES[PALETTE], crumb=crumbs(db, [d for d, _, _, _ in instances]),
                       name=escape(name), kind=escape(kind), n=len(instances), documents="document" if len(instances) == 1 else "documents",
                       aliases=escape(", ".join(json.loads(aliases))), lead=escape(lead), sections=sections, facts=facts)


def write_wiki_page(store, out, name, kind=None):
    """The page for the parent of that name (and kind, when given), written under out/wiki."""
    db = sqlite3.connect(store)
    query = ("select p.parent_id from parent p where p.name = ?" + (" and p.kind = ?" if kind else "")
             + " order by (select count(*) from instance_of i where i.parent_id = p.parent_id) desc")
    row = db.execute(query, (name, kind) if kind else (name,)).fetchone()
    if row is None:
        db.close()
        print(f"no parent named {name}")
        return None
    html = wiki_page(db, row[0])
    db.close()
    (out / "wiki").mkdir(exist_ok=True)
    path = out / "wiki" / (slug(name, row[0]) + ".html")
    path.write_text(html, encoding="utf-8")
    print(f"wrote {path.name}: {len(html)} characters")
    return path


if __name__ == "__main__" and STORE.exists():
    write_wiki_page(STORE, OUT, "Ozma", "person")

# %% [markdown]
# ## Block 19: a portal page
#
# The collection's page, the entry point: its name and abstract, the documents in date order
# with their abstracts, and every entity the documents hold, by relevance (the documents
# holding it, then the facts about it), each linking to its wiki page. The
# entity pages of a collection's shared parents are written beside it so the links resolve.

# %%
PORTAL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{name}</title>
<style>
:root {{ {palette} }}
body {{ font-family: Georgia, "Times New Roman", serif; margin: 0; color: var(--ink); background: var(--paper); line-height: 1.5; }}
header {{ background: var(--band); color: var(--band-ink); padding: 1.6rem 0; border-bottom: 2px solid var(--tint, var(--rule, #e4e7eb)); }}
header .inner {{ max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }}
header h1 {{ font-size: 2.2rem; margin: 0; font-weight: normal; letter-spacing: 0.01em; }}
header .kind {{ color: var(--band-muted); font-style: italic; margin-top: 0.3rem; }}
header .aliases {{ color: var(--band-muted); font-size: 0.85rem; margin-top: 0.5rem; }}
header .crumb {{ color: var(--band-muted); font-size: 0.9rem; margin-top: 0.4rem; }} header .crumb a {{ color: var(--band-ink); }}
.wrap {{ display: flex; gap: 2.5rem; max-width: 1200px; margin: 0 auto; padding: 1.5rem; }}
main {{ flex: 3; min-width: 0; }}
aside {{ flex: 1.3; min-width: 280px; font-size: 0.9rem; background: var(--card); border: 1px solid var(--tint, var(--rule, #e4e7eb)); border-radius: 6px; padding: 1rem 1.2rem; align-self: flex-start; }}
aside h2 {{ margin-top: 0; }}
h2 {{ font-size: 1.25rem; color: var(--ink); border-bottom: 1px solid var(--tint, var(--rule, #e4e7eb)); padding-bottom: 0.2rem; margin-top: 2.2rem; }}
h3 {{ font-size: 0.95rem; color: var(--accent); margin: 1.4rem 0 0.4rem; text-transform: uppercase; letter-spacing: 0.06em; }}
h4 {{ font-size: 0.8rem; color: var(--accent); margin: 1.1rem 0 0.1rem; font-weight: normal; text-transform: uppercase; letter-spacing: 0.08em; }}
.lead {{ font-size: 1.1rem; color: var(--ink); }}
.cell {{ margin: 0.3rem 0 0.8rem; }} .doc {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 0.4rem; }}
.facts p, details {{ margin: 0.45rem 0; }} summary {{ cursor: pointer; color: var(--ink); }} summary:hover {{ color: var(--accent); }}
details p {{ margin: 0.3rem 0 0.3rem 1rem; }}
.quote {{ color: var(--muted); font-size: 0.8rem; display: block; margin-top: 0.15rem; font-style: italic; }}
a {{ color: var(--link); text-decoration: none; }} a:hover {{ text-decoration: underline; }}
aside li {{ margin: 0.35rem 0; }} aside ul {{ padding-left: 1.1rem; }}
</style></head><body>
<header><div class="inner"><h1>{name}</h1><div class="kind">a collection of {n} documents</div></div></header>
<div class="wrap">
<main>
<p class="lead">{abstract}</p>
{sections}
</main>
<aside><h2>Entities in these documents</h2><ul>{parents}</ul></aside>
</div></body></html>
"""


def collection_parents(db, group):
    """Every parent with an instance in the group, by relevance: the documents of the group
    holding it, then how many facts its instances there carry."""
    placeholders = ", ".join("?" * len(group))
    rows = db.execute(f"""select p.parent_id, p.name, p.kind, count(distinct i.doc_id) as docs,
                          (select count(*) from fact f where f.doc_id in ({placeholders}) and f.quote is not null
                           and exists (select 1 from instance_of j where j.parent_id = p.parent_id and j.doc_id = f.doc_id and j.node_id = f.subject)) as facts
                          from instance_of i join parent p on p.parent_id = i.parent_id
                          where i.doc_id in ({placeholders}) group by p.parent_id order by docs desc, facts desc, p.name""",
                      list(group) + list(group)).fetchall()
    return rows


def portal_page(db, collection_id):
    """The HTML of one collection's page."""
    name, abstract = db.execute("select name, abstract from collection where collection_id = ?", (collection_id,)).fetchone()
    group = [d for (d,) in db.execute("select doc_id from document_in where collection_id = ?", (collection_id,))]
    docs = db.execute(f"select doc_id, title, occurred_at from document where doc_id in ({', '.join('?' * len(group))}) order by occurred_at", group).fetchall()
    abstracts = dict(db.execute(f"select doc_id, text from abstract where node_id like '%:doc' and doc_id in ({', '.join('?' * len(group))})", group).fetchall())
    sections = "".join(f"<h2><a href=\"{doc_slug(doc_id)}.html\">{escape(title)}</a></h2><div class=\"doc\">{escape(date)}</div><p>{escape(abstracts.get(doc_id) or '')}</p>"
                       for doc_id, title, date in docs)
    parents = collection_parents(db, group)
    items = "".join(f'<li><a href="{slug(pname, pid)}.html">{escape(pname)}</a> <span class="kind">{escape(kind)}, in {n} of {len(group)}, {facts} facts</span></li>'
                    for pid, pname, kind, n, facts in parents[:PORTAL_ENTITIES])
    return PORTAL.format(palette=PALETTES[PALETTE], name=escape(name), n=len(group), abstract=escape(abstract), sections=sections, parents=items)


def write_portal(store, out, collection_id):
    """The portal page and the pages of its most distinctive shared entities, under out/wiki."""
    db = sqlite3.connect(store)
    name = db.execute("select name from collection where collection_id = ?", (collection_id,)).fetchone()[0]
    (out / "wiki").mkdir(exist_ok=True)
    path = out / "wiki" / (slug(name, f"c{collection_id}") + ".html")
    path.write_text(portal_page(db, collection_id), encoding="utf-8")
    group = [d for (d,) in db.execute("select doc_id from document_in where collection_id = ?", (collection_id,))]
    for pid, pname, _, _, _ in collection_parents(db, group)[:PORTAL_ENTITIES]:
        (out / "wiki" / (slug(pname, pid) + ".html")).write_text(wiki_page(db, pid), encoding="utf-8")
    for doc_id in group:
        (out / "wiki" / (doc_slug(doc_id) + ".html")).write_text(document_page(db, doc_id), encoding="utf-8")
    db.close()
    print(f"wrote {path.name}, its entity pages and its {len(group)} document pages")
    return path


if __name__ == "__main__" and STORE.exists():
    db = sqlite3.connect(STORE)
    largest = db.execute("select collection_id from collection order by (select count(*) from document_in i where i.collection_id = collection.collection_id) desc").fetchall()
    db.close()
    for (cid,) in largest:
        write_portal(STORE, OUT, cid)
