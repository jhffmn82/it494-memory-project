# %% [markdown]
# # ThreadAtlas retrieval, draft
#
# The query path of `docs/retrieval.md` over the serving store and nothing else of the build.
# Parked here on 2026-09-15 when retrieval left the global-layer notebook; not yet shaped into
# blocks, not yet run as its own kernel. What it reads: `threadatlas.sqlite` and, until the
# vectors move inside it or the dataset carries both, `threadatlas.npy` beside it. The helpers
# below are copied from the global-layer notebook so this file imports nothing from it.

# %%
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

STORE = Path(os.environ.get("STORE", "data/global/threadatlas.sqlite"))
OUT = STORE.parent
MODEL = "BAAI/bge-small-en-v1.5"
DIMENSION = 384
EMBEDDER = None
LUNA = "gpt-5.6-luna"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_identifier(title, source_uri):
    """A chat's title is its session id, which is not a title."""
    return title is None or title == Path(source_uri).stem


def fact_text(f, names):
    """A fact as a clause: subject, predicate, object, qualifiers."""
    subject = names.get(f["subject"], f["subject"])
    if f["direction"] == "mentioned" and f["subject_name"]:
        subject = f["subject_name"]
    obj = names.get(f["object"], f["object"]) if f["object_is_node"] else f["object"]
    line = f"{subject} {f['predicate'].replace('_', ' ')} {obj}"
    return line + (f" ({f['qualifiers']})" if f["qualifiers"] else "")


def embed(texts):
    """Vectors for texts, float32; the model loads on first use."""
    global EMBEDDER
    import numpy
    if EMBEDDER is None:
        from fastembed import TextEmbedding
        EMBEDDER = TextEmbedding(MODEL)
    return numpy.asarray(list(EMBEDDER.embed(texts, batch_size=256)), dtype=numpy.float32)


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


def generate(prompt, schema, stage, model=LUNA, effort="low", ctx=None):
    """The reader call; the global-layer notebook's block 2 is the shape to copy in when this runs."""
    raise NotImplementedError("the model block is not in this draft")

# %% [markdown]
# ## Retrieval
#
# The query path of `docs/retrieval.md`. Two entry
# scans inside the filter, each returning records: the vector arm (cosine of the question
# against every row, a record scored by its best sentence) and the keyword arm (BM25 over the
# `search` table, one row per record). Reciprocal rank fusion orders the entry records. One hop
# from each entry along three edges (the record's entity, its unit and the two beside it, its
# parent's other children inside the filter), the top K_HOP per edge by the neighbour's own
# score. Every record in the pool is then scored on its own vector, discounted once per hop,
# and packed whole in that order until the budget is spent. A parent summary can be an entry
# hit; it routes to its children's records and is never packed. One JSON line per question
# goes to `questions.jsonl`, enough to rebuild the context byte for byte.

# %%
K_ENTRY = 20               # entry records per arm
K_HOP = 10                 # neighbours per edge per entry, by their own score
DISCOUNT = 0.8             # per hop
RRF_K = 60                 # reciprocal rank fusion constant (Cormack, Clarke and Buettcher 2009)
BUDGET = int(os.environ.get("BUDGET", "6000"))                 # reader tokens, the 15 percent margin already taken
QUERY_PREFIX = os.environ.get("QUERY_PREFIX", "")              # BGE's instruction for short queries, tuned on the 14 questions then frozen
TOKENIZER = None

ANSWER = """Answer the question from the records below and nothing else. Every record is dated and names its
document. If the records do not answer it, say so. Reply with a JSON object: {{"answer": "<a short answer>"}}.

Records:
{context}

Question: {question}"""


def open_index(store):
    """What a question reads: the store, the array in memory as float32, and the maps between rows and records."""
    import numpy
    db, array = load_sidecar(store)
    keys, rows = [], {}
    for row, record, doc_id, record_id in db.execute("select row, record, doc_id, record_id from vec_row order by row"):
        key = (record, doc_id, record_id)
        keys.append(key)
        rows.setdefault(key, []).append(row)
    parent_docs = {}
    for doc_id, parent_id in db.execute("select doc_id, parent_id from instance_of"):
        parent_docs.setdefault(str(parent_id), set()).add(doc_id)
    docs = {r[0]: {"title": r[1], "source_uri": r[2], "occurred_at": r[3]}
            for r in db.execute("select doc_id, title, source_uri, occurred_at from document")}
    names = {(d, n): name for d, n, name in db.execute("select doc_id, node_id, name from node")}
    return {"db": db, "array": numpy.asarray(array, dtype=numpy.float32), "keys": keys, "rows": rows,
            "parent_docs": parent_docs, "docs": docs, "names": names}


def collection_docs(db, name):
    """The filter for a collection: its documents' ids."""
    return {d for (d,) in db.execute("select i.doc_id from document_in i join collection c on c.collection_id = i.collection_id where c.name = ?", (name,))}


def row_mask(index, doc_filter, parent_on):
    """Rows inside the filter; a parent's rows only when the hop is on and a child's document is inside."""
    import numpy
    keep = numpy.ones(len(index["keys"]), dtype=bool)
    for i, (record, doc_id, record_id) in enumerate(index["keys"]):
        if record == "parent":
            keep[i] = parent_on and (doc_filter is None or bool(index["parent_docs"].get(record_id, set()) & doc_filter))
        elif doc_filter is not None:
            keep[i] = doc_id in doc_filter
    return keep


def own_score(index, scores, key):
    """A record's score against the question: its best sentence's cosine; 0 for a record with no vector."""
    rows = index["rows"].get(key)
    return float(scores[rows].max()) if rows else 0.0


def vector_entries(index, scores, mask):
    """The K_ENTRY records with the best sentence inside the filter."""
    import numpy
    masked = numpy.where(mask, scores, -numpy.inf)
    ranked, seen = [], set()
    for row in numpy.argsort(-masked):
        if masked[row] == -numpy.inf or len(ranked) == K_ENTRY:
            break
        key = index["keys"][row]
        if key not in seen:
            seen.add(key)
            ranked.append(key)
    return ranked


def fts_query(question):
    """The question's words joined by OR; FTS5's own syntax never reaches the engine."""
    return " OR ".join(f'"{w}"' for w in re.findall(r"\w+", question))


def keyword_entries(db, question, doc_filter):
    """The K_ENTRY records BM25 ranks best inside the filter; bm25() is negative, so ascending is best first."""
    query = fts_query(question)
    if not query:
        return []
    sql, args = "select record, doc_id, record_id from search where search match ?", [query]
    if doc_filter is not None:
        sql += f" and doc_id in ({', '.join('?' * len(doc_filter))})"
        args += sorted(doc_filter)
    sql += " order by bm25(search) limit ?"
    args.append(K_ENTRY)
    return [tuple(r) for r in db.execute(sql, args)]


def fuse(vector, keyword):
    """Reciprocal rank fusion: each record scores 1 / (RRF_K + rank) in every arm that lists it."""
    score = {}
    for ranked in (vector, keyword):
        for rank, key in enumerate(ranked, 1):
            score[key] = score.get(key, 0.0) + 1 / (RRF_K + rank)
    return sorted(score, key=score.get, reverse=True), score


def node_records(db, doc_id, node_id):
    """Every record of one entity: its facts, its cells, its abstract."""
    keys = [("fact", doc_id, f) for (f,) in db.execute("select fact_id from fact where doc_id = ? and subject = ?", (doc_id, node_id))]
    keys += [("cell", doc_id, f"{node_id}@{u}") for (u,) in db.execute("select unit_id from cell where doc_id = ? and node_id = ?", (doc_id, node_id))]
    keys += [("abstract", doc_id, node_id) for _ in db.execute("select 1 from abstract where doc_id = ? and node_id = ?", (doc_id, node_id))]
    return keys


def unit_records(db, doc_id, unit_id):
    """Every record of a unit and of the units beside it (position plus or minus one)."""
    position = db.execute("select position from unit where unit_id = ?", (unit_id,)).fetchone()
    if position is None:
        return []
    units = [u for (u,) in db.execute("select unit_id from unit where doc_id = ? and position between ? and ?",
                                      (doc_id, position[0] - 1, position[0] + 1))]
    marks = ", ".join("?" * len(units))
    keys = [("fact", doc_id, f) for (f,) in db.execute(f"select fact_id from fact where doc_id = ? and unit_id in ({marks})", [doc_id, *units])]
    keys += [("cell", doc_id, f"{n}@{u}") for n, u in db.execute(f"select node_id, unit_id from cell where doc_id = ? and unit_id in ({marks})", [doc_id, *units])]
    return keys


def children_records(db, parent_id, doc_filter, skip=None):
    """The records of a parent's children inside the filter, one child skipped."""
    keys = []
    for d, n in db.execute("select doc_id, node_id from instance_of where parent_id = ?", (parent_id,)):
        if (d, n) != skip and (doc_filter is None or d in doc_filter):
            keys += node_records(db, d, n)
    return keys


def edges(index, entry, doc_filter, parent_on):
    """The neighbours of an entry record, by edge. A parent entry has one edge, to its children."""
    db = index["db"]
    record, doc_id, record_id = entry
    if record == "parent":
        return {"children": children_records(db, int(record_id), doc_filter)}
    if record == "fact":
        node_id, unit_id = db.execute("select subject, unit_id from fact where doc_id = ? and fact_id = ?", (doc_id, record_id)).fetchone()
    elif record == "cell":
        node_id, unit_id = record_id.split("@")
    else:
        node_id, unit_id = record_id, None
    out = {"node": node_records(db, doc_id, node_id), "document": unit_records(db, doc_id, unit_id) if unit_id else []}
    if parent_on:
        parent = db.execute("select parent_id from instance_of where doc_id = ? and node_id = ?", (doc_id, node_id)).fetchone()
        out["parent"] = children_records(db, parent[0], doc_filter, skip=(doc_id, node_id)) if parent else []
    return out


def expand(index, scores, entries, doc_filter, parent_on):
    """The pool: entries at hop 0, then per entry and edge the K_HOP neighbours with the best own
    score at hop 1, the first route kept; and per edge how many neighbours were eligible."""
    pool = {key: {"hops": 0, "route": "entry"} for key in entries if key[0] != "parent"}
    eligible = []
    for entry in entries:
        for edge, keys in edges(index, entry, doc_filter, parent_on).items():
            ranked = sorted((-own_score(index, scores, k), k) for k in set(keys) if k != entry)
            eligible.append({"entry": list(entry), "edge": edge, "eligible": len(ranked)})
            for _, key in ranked[:K_HOP]:
                pool.setdefault(key, {"hops": 1, "route": [edge, list(entry)]})
    return pool, eligible


def render(index, key):
    """A record as the reader sees it: date | document | unit | text. One function, shared with the log."""
    db, docs, names = index["db"], index["docs"], index["names"]
    record, doc_id, record_id = key
    doc = docs[doc_id]
    title = doc_id[:8] if is_identifier(doc["title"], doc["source_uri"]) else doc["title"]
    if record == "fact":
        fields = ["doc_id", "fact_id", "subject", "subject_name", "predicate", "object", "object_is_node", "qualifiers", "occurred_at", "direction", "quote", "unit_id"]
        f = dict(zip(fields, db.execute(f"select {', '.join(fields)} from fact where doc_id = ? and fact_id = ?", (doc_id, record_id)).fetchone()))
        local = {f["subject"]: names.get((doc_id, f["subject"]), f["subject"]), f["object"]: names.get((doc_id, f["object"]), f["object"])}
        unit = db.execute("select label, occurred_at from unit where unit_id = ?", (f["unit_id"],)).fetchone() or (None, None)
        date = f["occurred_at"] or unit[1] or doc["occurred_at"]
        text = fact_text(f, local) + (f'\n  quote: "{f["quote"]}"' if f["quote"] else "")
        return f"{date} | {title} | {unit[0] or 'record'} | {text}"
    if record == "cell":
        node_id, unit_id = record_id.split("@")
        text = db.execute("select text from cell where doc_id = ? and node_id = ? and unit_id = ?", (doc_id, node_id, unit_id)).fetchone()[0]
        unit = db.execute("select label, occurred_at from unit where unit_id = ?", (unit_id,)).fetchone() or (None, None)
        return f"{unit[1] or doc['occurred_at']} | {title} | {unit[0] or unit_id[:8]} | {names.get((doc_id, node_id), node_id)}: {text}"
    text = db.execute("select text from abstract where doc_id = ? and node_id = ?", (doc_id, record_id)).fetchone()[0]
    return f"{doc['occurred_at']} | {title} | abstract | {names.get((doc_id, record_id), record_id)}: {text}"


def tokens(text):
    """The reader's tokenizer when tiktoken is present, else four tokens per three words."""
    global TOKENIZER
    if TOKENIZER is None:
        try:
            import tiktoken
            TOKENIZER = tiktoken.get_encoding("o200k_base")
        except ImportError:
            TOKENIZER = False
    return len(TOKENIZER.encode(text)) if TOKENIZER else len(text.split()) * 4 // 3


def pack(index, pool, budget):
    """Whole records in score order until the budget is spent; a record that does not fit is cut, not trimmed."""
    context, used = [], 0
    for key in sorted(pool, key=score_key(pool), reverse=True):
        text = render(index, key)
        n = tokens(text)
        if used + n > budget:
            pool[key]["packed"] = False
            continue
        pool[key]["packed"] = True
        context.append(text)
        used += n
    return context, used


def score_key(pool):
    """The sort key for a pool: a record's score."""
    def key(record):
        return pool[record]["score"]
    return key


def retrieve(index, question, doc_filter=None, keyword=True, vector=True, parent=True, budget=BUDGET):
    """The context for a question inside a filter, and its log line."""
    q = embed([QUERY_PREFIX + question])[0]
    scores = index["array"] @ q
    mask = row_mask(index, doc_filter, parent)
    V = vector_entries(index, scores, mask) if vector else []
    W = keyword_entries(index["db"], question, doc_filter) if keyword else []
    entries, rrf = fuse(V, W)
    pool, eligible = expand(index, scores, entries, doc_filter, parent)
    for key, item in pool.items():
        item["score"] = own_score(index, scores, key) * DISCOUNT ** item["hops"]
    context, used = pack(index, pool, budget)
    line = {"asked_at": now(), "question": question, "filter": sorted(doc_filter) if doc_filter else None,
            "arms": {"keyword": keyword, "vector": vector, "parent": parent, "budget": budget},
            "constants": {"K_ENTRY": K_ENTRY, "K_HOP": K_HOP, "DISCOUNT": DISCOUNT, "RRF_K": RRF_K, "prefix": QUERY_PREFIX},
            "entries": [{"record": list(k), "rank_v": V.index(k) + 1 if k in V else None, "rank_w": W.index(k) + 1 if k in W else None,
                         "rrf": round(rrf[k], 5)} for k in entries],
            "eligible": eligible,
            "pool": [{"record": list(k), "hops": v["hops"], "route": v["route"], "score": round(v["score"], 4), "packed": v["packed"]}
                     for k, v in pool.items()],
            "context": context, "tokens": used}
    with (OUT / "questions.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return context, line


def answer(question, context):
    """One call to the reader with the packed context; the reply is logged with the call."""
    reply = generate(ANSWER.format(context="\n".join(context), question=question), {"answer": str}, "answer",
                     model=LUNA, effort="low", ctx={"question": question})
    return reply["answer"] if reply else None

# %% [markdown]
# ## A question over the largest collection
#
# The full system (both arms, the parent hop) on one question inside the largest collection;
# the entries with the arm that found them, the pool by hop, and the packed context. The
# reader answers when a key is present.

# %%
if __name__ == "__main__" and STORE.exists():
    index = open_index(STORE)
    collection = index["db"].execute("select name from collection order by (select count(*) from document_in i where i.collection_id = collection.collection_id) desc").fetchone()
    doc_filter = collection_docs(index["db"], collection[0]) if collection else None
    question = "Who is Tip, and what becomes of him?"
    context, line = retrieve(index, question, doc_filter)
    print(f"{question}\n  in {collection[0] if collection else 'every document'}: {len(line['entries'])} entries, "
          f"{len(line['pool'])} in the pool, {len(context)} packed in {line['tokens']} tokens")
    for entry in line["entries"][:8]:
        record = tuple(entry["record"])
        shown = "parent " + record[2] if record[0] == "parent" else render(index, record)[:110]
        print(f"  entry {record[0]:8} v{entry['rank_v'] or '-'} w{entry['rank_w'] or '-'}  {shown}")
    for text in context[:6]:
        print("  |", text[:160].replace("\n", " "))
    if KEY:
        print("  answer:", answer(question, context))
