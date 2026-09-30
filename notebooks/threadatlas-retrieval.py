# %% [markdown]
# # ThreadAtlas retrieval
#
# Given a question and the documents to search, find the stored records that answer it and hand
# them, whole and dated, to a reader model, each fact with the passage of the source it was read
# from. This notebook reads the store the global layer built, and the documents' text from Step 0
# by reference: the store keeps a fact's unit and offsets, Step 0 keeps the text they point into.
# No model call until the reader. The same code runs on a book, a series of books, or one user's
# chat history; nothing branches on the question or the corpus.
#
# ## What comes in
#
# The public dataset [ThreadAtlas Step 2: Serving Store](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-store):
# `threadatlas.sqlite` and `threadatlas.npy`, written by the
# [global-layer notebook](https://www.kaggle.com/code/jhffmn/threadatlas-global-layer) on 2026-09-15.
# 81 documents, 6,929 facts, 1,826 cells, 891 abstracts, 1,313 parents, 15,739 vectors.
#
# The public dataset [ThreadAtlas Step 0](https://www.kaggle.com/datasets/jhffmn/it494-threadatlas-step0):
# `documents.jsonl` (every document's full text) and `units.jsonl` (each unit's start and end in
# it). Only the store's 81 documents are read.
#
# | table | what retrieval uses it for |
# |---|---|
# | `document` | the title and date printed on every record; the filter is a set of `doc_id` |
# | `unit` | a record's chapter or chat turn, its date, and which units sit beside it |
# | `node` | the name of the entity a record is about |
# | `fact`, `cell`, `abstract` | the three kinds of record the reader can be given; a fact's `unit_id`, `quote_start` and `quote_end` point into the Step 0 text |
# | `parent`, `instance_of` | the same entity in other documents |
# | `collection`, `document_in` | a named set of documents, used as a filter |
# | `vec_row` | which record each row of `threadatlas.npy` belongs to |
# | `search` | the FTS5 full-text index, one row per record |
#
# ## What goes out
#
# `questions.jsonl`: one line per question with everything needed to rebuild the context: the
# entries and the scan that found each, every record reached and how, its score, whether it was
# packed, and the context itself. `calls.jsonl`: the reader's calls with their cost. The printout
# shows the first entries, the first records of the context, and the answer.
#
# ## Records and vectors
#
# A **record** is one thing the reader can be shown: a **fact** (a subject, predicate and object
# with the verbatim quote it was read from), a **cell** (what one unit says about one entity), or an
# **abstract** (a document's or an entity's summary). A fact has one vector. A cell or an abstract has
# one vector per sentence. A **parent** summary has vectors too, but a parent is never shown to the
# reader: finding one only leads to its instances. A record's similarity to the question is the
# similarity of its **best** sentence, and a record is always packed whole, never cut.
#
# A fact goes down to its source: fact, then its unit, then the raw text of that unit in Step 0.
# The reader gets the fact and the **passage** it was read from. For a chat the passage is the whole
# turn, since a turn is one unit. For a book or paper, whose units are chapters, it is the paragraph
# around the quote, inside the unit. A passage longer than 2,000 characters is cut to the 2,000
# around the quote. When two facts come from one passage, the passage is given once.
#
# ## The algorithm
#
# ```
# retrieve(question, filter):
#     q = embed(question)                                   bge-small-en-v1.5, 384 numbers
#     similarity of q to every vector                       one matrix product
#
#     vector entries  = the 20 records inside the filter with the most similar best sentence
#     keyword entries = the 20 records inside the filter BM25 ranks best for the question's words
#     entries = both lists fused by reciprocal rank: a record scores 1 / (60 + rank) in each list
#
#     pool = the entries (hop 0)
#     for each entry, three edges:
#         entity    every other record of the same entity in the same document
#         unit      every record of the same unit and of the units just before and after it
#         parent    every record of the same entity in the other documents of the filter
#         add the 10 most similar records of each edge to the pool (hop 1)
#
#     score of a record = its own similarity x 0.8 for each hop
#     render every record as  date | document | unit | text
#         a fact also carries its source passage: fact -> unit -> the raw text in Step 0
#     pack records whole, best score first, until 6,000 tokens are used
#         a passage already packed is not repeated
#     reader(question + packed records) -> answer
# ```
#
# ## A walkthrough: one question, step by step
#
# LongMemEval question gpt4_2ba83207 asks, of one user's chat history: *"Which grocery store did I
# spend the most money at in the past month?"* The benchmark's answer is Thrive Market. The user
# mentioned three purchases in three different sessions, and the answer needs all three. The numbers
# below are this notebook's own log for that question.
#
# 1. **The filter.** The history is the 53 sessions under `chats/longmemeval/gpt4_2ba83207/`. Every
#    vector outside those 53 documents is masked out. A parent's vector stays only when one of its
#    instances is in the filter.
# 2. **The vector scan.** The question becomes one 384-number vector, and one matrix product gives
#    its cosine with all 15,739 rows. Each record takes the score of its best row, and the 20 best
#    records are the vector entries. The best one, at 0.70, is the fact *user went grocery shopping
#    at Walmart*.
# 3. **The keyword scan.** The question's words are joined with OR and searched in the FTS5 index,
#    ranked by BM25, inside the filter. The 20 best are the keyword entries. The same Walmart fact is
#    first here too.
# 4. **Fusing the two lists.** Reciprocal rank fusion gives each record 1 / (60 + rank) for every
#    list it is in. The Walmart fact is first in both: 1/61 + 1/61 = 0.0328. A fact from the Thrive
#    Market session, sixth by vector and eleventh by keyword, gets 1/66 + 1/71 = 0.0292. The two lists
#    share 6 records, so there are 34 entries: 32 facts and 2 session abstracts.
# 5. **One hop.** From each entry the three edges offered 448 records of the same entity, 358
#    records of the same or a neighbouring turn, and 1 record through a parent. The 10 most similar
#    per edge join the pool, which ends at 250 records: the 34 entries, 116 reached through the
#    entity and 100 through the unit.
# 6. **Scoring.** Every record in the pool is scored on its own similarity to the question, times
#    0.8 if it was reached by a hop. An entry at 0.60 and a hop record at 0.75 both score 0.60.
# 7. **Packing.** Each record is rendered with its date, document, unit and text. A fact also gets
#    the turn it came from, read from Step 0 at the fact's unit. Records are added whole, best first,
#    until the next one would pass 6,000 tokens. 32 records went in: 30 entries and 2 reached by the
#    hop, 10 of them facts whose turn was already given above. The Walmart $120 fact is second, the
#    Publix $60 fact fourth, and the Thrive Market $150 fact sixteenth, each with the user's own words.
#    The last record packed scored 0.51.
# 8. **The reader.** gpt-5.6-luna gets the 32 records and the question and answers in JSON. It is
#    told to use the records and nothing else.
#
# The Oz question in Block 9 ("Who is Tip, and what becomes of him?", filtered to the three Oz
# books) shows the other side: there the parent edge offered 1,972 records, since the Scarecrow, the
# Tin Woodman and others are one parent across the three books, and 88 of them reached the pool.
#
# ## The constants
#
# | name | value | what it controls |
# |---|---|---|
# | `K_ENTRY` | 20 | records taken from each entry scan |
# | `K_HOP` | 10 | records taken from each edge of each entry |
# | `DISCOUNT` | 0.8 | the score multiplier for a record reached by a hop |
# | `RRF_K` | 60 | the reciprocal rank fusion constant, as Cormack et al. fixed it |
# | `BUDGET` | 6,000 | tokens of context the reader is given |
# | `MAX_PASSAGE` | 2,000 | characters of source text given with one fact |
#
# None of them has been tuned. They are logged with every question so a run can be repeated.
#
# ## Where it comes from
#
# None of the steps is new. Each is a standard technique, and the combination is close to what
# published graph memory systems already do.
#
# - **Two scans fused by rank.** Hybrid lexical and dense retrieval, fused with reciprocal rank
#   fusion: G. V. Cormack, C. L. A. Clarke and S. Buettcher, "Reciprocal Rank Fusion outperforms
#   Condorcet and individual Rank Learning Methods", SIGIR 2009, where k = 60 was fixed during a
#   pilot study. S. Bruch, S. Gai and A. Ingber, "An Analysis of Fusion Functions for Hybrid
#   Retrieval" (arXiv 2210.11934, 2023), find that a tuned weighted sum of the two scores does
#   better than RRF.
# - **A record scored by its best sentence.** MaxP: Z. Dai and J. Callan, "Deeper Text Understanding
#   for IR with Contextual Neural Language Modeling", SIGIR 2019, which scores a document by its best
#   passage.
# - **Embed small, return large.** Sentence-window retrieval, as in LlamaIndex's
#   `SentenceWindowNodeParser`: the vector is a sentence, the model reads the text around it.
# - **Enter a graph by similarity, expand to the neighbours, fill a token budget.** Microsoft
#   GraphRAG's local search (https://microsoft.github.io/graphrag/query/local_search/) enters through
#   the entities most similar to the query, pulls their relationships and source text, and cuts the
#   candidates to a fixed context window. LightRAG (Z. Guo et al., arXiv 2410.05779, 2024) adds the
#   one-hop neighbours of what it retrieves. HippoRAG (B. Jimenez Gutierrez et al., NeurIPS 2024)
#   spreads from the query's entities by Personalized PageRank instead of a fixed hop.
# - **The closest match.** Zep (P. Rasmussen et al., "Zep: A Temporal Knowledge Graph Architecture
#   for Agent Memory", arXiv 2501.13956, 2025) searches by cosine similarity, BM25 and breadth-first
#   search over n hops, reranks with RRF among others, and gives the model each fact with its date
#   range. That is this path's shape, and Zep reports on LongMemEval, one of the two benchmarks here.
# - **A score that shrinks with each hop.** Spreading activation, long used in information
#   retrieval (F. Crestani, "Application of Spreading Activation Techniques in Information
#   Retrieval", Artificial Intelligence Review 11, 1997).
#
# What ThreadAtlas adds is not the search but what it searches: records that each belong to one
# document and carry a verbatim quote, and a tree of parents that links the same entity across
# documents without merging them. The parent edge is the one part to measure, by running the same
# questions with `parent=False`.
#
# ## What it does not do yet
#
# - The reader is not told the date the question is asked, so "the past month" has no anchor.
# - The design in `docs/retrieval.md` (route, traverse, substantiate, bundles) is not built; this
#   is the one-hop version.
# - No reranker and no tuned constants.
#
# ## Running it
#
# On Kaggle: attach the `it494-threadatlas-store` and `it494-threadatlas-step0` datasets, turn
# Internet on (fastembed fetches the embedding model once), and add an `OPENAI_API_KEY` secret for
# the reader. Without a key everything runs except the answer. Locally: set `STORE_DIR` to a folder
# holding the store's two files and `STEP0_DIR` to one holding Step 0's, and run the script.

# %% [markdown]
# ## Block 1: files and settings
#
# Where the store and the Step 0 text are, where the output goes, and the constants the walkthrough
# names.

# %%
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

VERSION = "threadatlas-retrieval 0.3"

try:
    import fastembed
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "fastembed"], check=True)
try:
    import tiktoken
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "tiktoken"], check=True)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

places_to_look = [
    Path(os.environ.get("STORE_DIR", "data/global")),
    Path("/kaggle/input/datasets/jhffmn/it494-threadatlas-store"),
    Path("/kaggle/input/it494-threadatlas-store"),
]
STORE_DIR = None
for folder in places_to_look:
    if (folder / "threadatlas.sqlite").exists():
        STORE_DIR = folder
        break
if STORE_DIR is None:
    raise SystemExit("threadatlas.sqlite not found: attach the it494-threadatlas-store dataset")

places_to_look = [
    Path(os.environ.get("STEP0_DIR", "data/step0")),
    Path("/kaggle/input/datasets/jhffmn/it494-threadatlas-step0"),
    Path("/kaggle/input/it494-threadatlas-step0"),
]
STEP0_DIR = None
for folder in places_to_look:
    if (folder / "documents.jsonl").exists():
        STEP0_DIR = folder
        break
if STEP0_DIR is None:
    raise SystemExit("documents.jsonl not found: attach the it494-threadatlas-step0 dataset")

if Path("/kaggle/working").exists():
    OUT = Path("/kaggle/working")
else:
    OUT = STORE_DIR

MODEL = "BAAI/bge-small-en-v1.5"
DIMENSION = 384

K_ENTRY = 20
K_HOP = 10
DISCOUNT = 0.8
RRF_K = 60
BUDGET = int(os.environ.get("BUDGET", "6000"))
QUERY_PREFIX = os.environ.get("QUERY_PREFIX", "")
MAX_PASSAGE = 2000

print(VERSION)
print("store: ", STORE_DIR / "threadatlas.sqlite")
print("text:  ", STEP0_DIR / "documents.jsonl")
print("output:", OUT)

# %% [markdown]
# ## Block 2: opening the store
#
# The store and its vectors, checked against each other, and the lookups every question uses:
# which record each vector row belongs to, which documents each parent reaches, each document's
# title and date, and each entity's name. Then the two filters: a collection by name, and a
# LongMemEval history by its folder. Last, the source text: each of the store's documents from
# Step 0, and the start and end of each of its units.

# %%
def open_store(folder):
    db = sqlite3.connect(folder / "threadatlas.sqlite")
    vectors = np.load(folder / "threadatlas.npy")

    header = db.execute("select model, dimension from vec_header").fetchone()
    row_count = db.execute("select count(*) from vec_row").fetchone()[0]
    if header != (MODEL, DIMENSION) or vectors.shape != (row_count, DIMENSION):
        raise SystemExit(f"the vectors do not match the store: {header}, {vectors.shape}, {row_count} rows")

    record_of_row = []
    rows_of_record = {}
    for row, kind, doc_id, record_id in db.execute("select row, record, doc_id, record_id from vec_row order by row"):
        record = (kind, doc_id, record_id)
        record_of_row.append(record)
        if record not in rows_of_record:
            rows_of_record[record] = []
        rows_of_record[record].append(row)

    documents_of_parent = {}
    for doc_id, parent_id in db.execute("select doc_id, parent_id from instance_of"):
        parent_id = str(parent_id)
        if parent_id not in documents_of_parent:
            documents_of_parent[parent_id] = set()
        documents_of_parent[parent_id].add(doc_id)

    documents = {}
    for doc_id, title, source_uri, occurred_at in db.execute("select doc_id, title, source_uri, occurred_at from document"):
        documents[doc_id] = {"title": title, "source_uri": source_uri, "occurred_at": occurred_at}

    entity_names = {}
    for doc_id, node_id, name in db.execute("select doc_id, node_id, name from node"):
        entity_names[(doc_id, node_id)] = name

    store = {}
    store["db"] = db
    store["vectors"] = vectors.astype(np.float32)
    store["record_of_row"] = record_of_row
    store["rows_of_record"] = rows_of_record
    store["documents_of_parent"] = documents_of_parent
    store["documents"] = documents
    store["entity_names"] = entity_names
    return store


def collection_filter(store, name):
    sql = """select i.doc_id from document_in i
             join collection c on c.collection_id = i.collection_id
             where c.name = ?"""
    doc_ids = set()
    for (doc_id,) in store["db"].execute(sql, (name,)):
        doc_ids.add(doc_id)
    return doc_ids


def history_filter(store, question_id):
    folder = f"chats/longmemeval/{question_id}/"
    doc_ids = set()
    for doc_id, source_uri in store["db"].execute("select doc_id, source_uri from document"):
        if folder in source_uri:
            doc_ids.add(doc_id)
    return doc_ids


def read_source(store, step0):
    texts = {}
    with open(step0 / "documents.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["doc_id"] in store["documents"]:
                texts[row["doc_id"]] = row["text"]

    unit_bounds = {}
    with open(step0 / "units.jsonl", encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["doc_id"] in store["documents"]:
                unit_bounds[row["unit_id"]] = (row["start"], row["end"])

    missing = 0
    for doc_id in store["documents"]:
        if doc_id not in texts:
            missing += 1
    if missing > 0:
        raise SystemExit(f"{missing} documents in the store have no text in Step 0")

    store["texts"] = texts
    store["unit_bounds"] = unit_bounds


store = open_store(STORE_DIR)
read_source(store, STEP0_DIR)
print(len(store["documents"]), "documents,", len(store["record_of_row"]), "vectors,",
      len(store["unit_bounds"]), "units of text from Step 0")

# %% [markdown]
# ## Block 3: scoring the question against every vector
#
# The question's vector, its similarity to every row, and a record's score as its best row.
# `best_first` is the one sort used everywhere: highest score first, ties broken by the record's
# name, so a run can be repeated exactly.

# %%
EMBEDDER = None


def embed(texts):
    global EMBEDDER
    if EMBEDDER is None:
        from fastembed import TextEmbedding
        EMBEDDER = TextEmbedding(MODEL)
    vectors = list(EMBEDDER.embed(texts, batch_size=256))
    return np.asarray(vectors, dtype=np.float32)


def score_every_row(store, question):
    question_vector = embed([QUERY_PREFIX + question])[0]
    return store["vectors"] @ question_vector


def record_score(store, row_scores, record):
    rows = store["rows_of_record"].get(record)
    if not rows:
        return 0.0
    return float(row_scores[rows].max())


def best_first(records, score_of):
    ranked = []
    for record in records:
        name = []
        for part in record:
            name.append(str(part))
        ranked.append((-score_of[record], tuple(name), record))
    ranked.sort()

    ordered = []
    for item in ranked:
        ordered.append(item[2])
    return ordered

# %% [markdown]
# ## Block 4: the two entry scans
#
# Steps 1 to 4 of the walkthrough: the filter, the vector scan, the keyword scan, and the fusion.

# %%
def rows_in_filter(store, doc_filter, use_parents):
    keep = np.ones(len(store["record_of_row"]), dtype=bool)
    for row in range(len(store["record_of_row"])):
        kind, doc_id, record_id = store["record_of_row"][row]
        if kind == "parent":
            if not use_parents:
                keep[row] = False
            elif doc_filter is not None:
                child_documents = store["documents_of_parent"].get(record_id, set())
                keep[row] = len(child_documents & doc_filter) > 0
        elif doc_filter is not None:
            keep[row] = doc_id in doc_filter
    return keep


def vector_entries(store, row_scores, keep):
    scores = np.where(keep, row_scores, -np.inf)
    best = {}
    for row in np.argsort(-scores, kind="stable"):
        score = float(scores[row])
        if score == -np.inf:
            break
        if len(best) >= K_ENTRY and score < min(best.values()):
            break
        record = store["record_of_row"][row]
        if record not in best:
            best[record] = score
    return best_first(best, best)[:K_ENTRY]


def keyword_entries(store, question, doc_filter):
    words = re.findall(r"\w+", question)
    if len(words) == 0:
        return []
    quoted = []
    for word in words:
        quoted.append('"' + word + '"')
    match = " OR ".join(quoted)

    sql = "select record, doc_id, record_id from search where search match ?"
    args = [match]
    if doc_filter is not None:
        marks = ", ".join(["?"] * len(doc_filter))
        sql += " and doc_id in (" + marks + ")"
        args += sorted(doc_filter)
    sql += " order by bm25(search), record, doc_id, record_id limit ?"
    args.append(K_ENTRY)

    found = []
    for row in store["db"].execute(sql, args):
        found.append(tuple(row))
    return found


def fuse(vector_ranked, keyword_ranked):
    rrf = {}
    for ranked in [vector_ranked, keyword_ranked]:
        rank = 1
        for record in ranked:
            rrf[record] = rrf.get(record, 0.0) + 1 / (RRF_K + rank)
            rank += 1
    return best_first(rrf, rrf), rrf

# %% [markdown]
# ## Block 5: one hop from every entry
#
# Step 5: the three edges of an entry (entity, unit, parent) and the 10 most similar records
# taken from each. A parent found as an entry has one edge only, to its instances.

# %%
def entity_records(db, doc_id, node_id):
    records = []
    for (fact_id,) in db.execute("select fact_id from fact where doc_id = ? and subject = ?", (doc_id, node_id)):
        records.append(("fact", doc_id, fact_id))
    for (unit_id,) in db.execute("select unit_id from cell where doc_id = ? and node_id = ?", (doc_id, node_id)):
        records.append(("cell", doc_id, node_id + "@" + unit_id))
    if db.execute("select 1 from abstract where doc_id = ? and node_id = ?", (doc_id, node_id)).fetchone():
        records.append(("abstract", doc_id, node_id))
    return records


def unit_records(db, doc_id, unit_id):
    found = db.execute("select position from unit where unit_id = ?", (unit_id,)).fetchone()
    if found is None:
        return []
    position = found[0]

    units = []
    for (neighbour,) in db.execute("select unit_id from unit where doc_id = ? and position between ? and ?",
                                   (doc_id, position - 1, position + 1)):
        units.append(neighbour)
    marks = ", ".join(["?"] * len(units))

    records = []
    for (fact_id,) in db.execute("select fact_id from fact where doc_id = ? and unit_id in (" + marks + ")", [doc_id] + units):
        records.append(("fact", doc_id, fact_id))
    for node_id, cell_unit in db.execute("select node_id, unit_id from cell where doc_id = ? and unit_id in (" + marks + ")", [doc_id] + units):
        records.append(("cell", doc_id, node_id + "@" + cell_unit))
    return records


def sibling_records(db, parent_id, doc_filter, skip):
    records = []
    for doc_id, node_id in db.execute("select doc_id, node_id from instance_of where parent_id = ?", (parent_id,)):
        if (doc_id, node_id) == skip:
            continue
        if doc_filter is not None and doc_id not in doc_filter:
            continue
        records += entity_records(db, doc_id, node_id)
    return records


def neighbours(store, entry, doc_filter, use_parents):
    db = store["db"]
    kind, doc_id, record_id = entry

    if kind == "parent":
        return {"parent": sibling_records(db, int(record_id), doc_filter, None)}

    unit_id = None
    if kind == "fact":
        node_id, unit_id = db.execute("select subject, unit_id from fact where doc_id = ? and fact_id = ?",
                                      (doc_id, record_id)).fetchone()
    elif kind == "cell":
        node_id, unit_id = record_id.split("@")
    else:
        node_id = record_id

    edges = {}
    edges["node"] = entity_records(db, doc_id, node_id)
    edges["document"] = []
    if unit_id:
        edges["document"] = unit_records(db, doc_id, unit_id)
    if use_parents:
        edges["parent"] = []
        found = db.execute("select parent_id from instance_of where doc_id = ? and node_id = ?", (doc_id, node_id)).fetchone()
        if found:
            edges["parent"] = sibling_records(db, found[0], doc_filter, (doc_id, node_id))
    return edges


def expand(store, row_scores, entries, doc_filter, use_parents):
    pool = {}
    for record in entries:
        if record[0] != "parent":
            pool[record] = {"hops": 0, "route": "entry"}

    eligible = []
    for entry in entries:
        edges = neighbours(store, entry, doc_filter, use_parents)
        for edge in edges:
            candidates = set(edges[edge])
            candidates.discard(entry)
            scores = {}
            for record in candidates:
                scores[record] = record_score(store, row_scores, record)
            ranked = best_first(candidates, scores)
            eligible.append({"entry": list(entry), "edge": edge, "eligible": len(ranked)})

            for record in ranked[:K_HOP]:
                if record not in pool:
                    pool[record] = {"hops": 1, "route": [edge, list(entry)]}
    return pool, eligible

# %% [markdown]
# ## Block 6: what the reader sees
#
# Steps 6 and 7: each record as one dated line, a fact with its source passage, and the packing to
# the token budget. A chat's title is its session id, so the first 8 characters of its `doc_id` are
# shown instead.

# %%
TOKENIZER = None


def count_tokens(text):
    global TOKENIZER
    if TOKENIZER is None:
        TOKENIZER = tiktoken.get_encoding("o200k_base")
    return len(TOKENIZER.encode(text))


def document_title(store, doc_id):
    document = store["documents"][doc_id]
    title = document["title"]
    if title is None or title == Path(document["source_uri"]).stem:
        return doc_id[:8]
    return title


def unit_label_and_date(db, unit_id):
    found = db.execute("select label, occurred_at from unit where unit_id = ?", (unit_id,)).fetchone()
    if found is None:
        return None, None
    return found[0], found[1]


def source_passage(store, doc_id, unit_id, quote_start, quote_end):
    text = store["texts"][doc_id]
    unit_start, unit_end = store["unit_bounds"][unit_id]
    kind = store["db"].execute("select kind from unit where unit_id = ?", (unit_id,)).fetchone()[0]

    if kind == "user" or kind == "assistant":
        start = unit_start
        end = unit_end
    else:
        start = text.rfind("\n\n", unit_start, quote_start)
        if start == -1:
            start = unit_start
        end = text.find("\n\n", quote_end, unit_end)
        if end == -1:
            end = unit_end

    if end - start > MAX_PASSAGE:
        start = max(unit_start, quote_start - MAX_PASSAGE // 2)
        end = min(unit_end, quote_end + MAX_PASSAGE // 2)
    return start, end, text[start:end].strip()


def fact_line(fact, names):
    subject = names.get(fact["subject"], fact["subject"])
    if fact["direction"] == "mentioned" and fact["subject_name"]:
        subject = fact["subject_name"]
    thing = fact["object"]
    if fact["object_is_node"]:
        thing = names.get(fact["object"], fact["object"])
    line = subject + " " + fact["predicate"].replace("_", " ") + " " + thing
    if fact["qualifiers"]:
        line += " (" + fact["qualifiers"] + ")"
    return line


def render(store, record, shown):
    db = store["db"]
    names = store["entity_names"]
    kind, doc_id, record_id = record
    title = document_title(store, doc_id)
    document_date = store["documents"][doc_id]["occurred_at"]

    if kind == "fact":
        fields = ["subject", "subject_name", "predicate", "object", "object_is_node",
                  "qualifiers", "occurred_at", "direction", "quote", "quote_start", "quote_end", "unit_id"]
        values = db.execute("select " + ", ".join(fields) + " from fact where doc_id = ? and fact_id = ?",
                            (doc_id, record_id)).fetchone()
        fact = {}
        for i in range(len(fields)):
            fact[fields[i]] = values[i]

        local_names = {}
        local_names[fact["subject"]] = names.get((doc_id, fact["subject"]), fact["subject"])
        local_names[fact["object"]] = names.get((doc_id, fact["object"]), fact["object"])

        label, unit_date = unit_label_and_date(db, fact["unit_id"])
        date = fact["occurred_at"] or unit_date or document_date
        text = fact_line(fact, local_names)
        passage = None
        if fact["quote"]:
            start, end, words = source_passage(store, doc_id, fact["unit_id"], fact["quote_start"], fact["quote_end"])
            passage = (doc_id, start, end)
            if passage in shown:
                text += "\n  source: the same passage as above"
            else:
                text += '\n  source: "' + words + '"'
        return f"{date} | {title} | {label or 'record'} | {text}", passage

    if kind == "cell":
        node_id, unit_id = record_id.split("@")
        text = db.execute("select text from cell where doc_id = ? and node_id = ? and unit_id = ?",
                          (doc_id, node_id, unit_id)).fetchone()[0]
        label, unit_date = unit_label_and_date(db, unit_id)
        entity = names.get((doc_id, node_id), node_id)
        return f"{unit_date or document_date} | {title} | {label or unit_id[:8]} | {entity}: {text}", None

    text = db.execute("select text from abstract where doc_id = ? and node_id = ?", (doc_id, record_id)).fetchone()[0]
    entity = names.get((doc_id, record_id), record_id)
    return f"{document_date} | {title} | abstract | {entity}: {text}", None


def pack(store, pool, budget):
    scores = {}
    for record in pool:
        scores[record] = pool[record]["score"]

    context = []
    used = 0
    shown = set()
    for record in best_first(pool, scores):
        text, passage = render(store, record, shown)
        size = count_tokens(text)
        if used + size > budget:
            pool[record]["packed"] = False
            continue
        pool[record]["packed"] = True
        context.append(text)
        used += size
        if passage is not None:
            shown.add(passage)
    return context, used

# %% [markdown]
# ## Block 7: the whole path, and its log
#
# `retrieve` runs steps 1 to 7 and writes one line to `questions.jsonl`. `keyword`, `vector` and
# `parent` turn each part off, which is how the arms of an evaluation are run.

# %%
def rank_in(ranked, record):
    if record in ranked:
        return ranked.index(record) + 1
    return None


def retrieve(store, question, doc_filter=None, keyword=True, vector=True, parent=True, budget=BUDGET):
    row_scores = score_every_row(store, question)
    keep = rows_in_filter(store, doc_filter, parent)

    vector_ranked = []
    if vector:
        vector_ranked = vector_entries(store, row_scores, keep)
    keyword_ranked = []
    if keyword:
        keyword_ranked = keyword_entries(store, question, doc_filter)
    entries, rrf = fuse(vector_ranked, keyword_ranked)

    pool, eligible = expand(store, row_scores, entries, doc_filter, parent)
    for record in pool:
        pool[record]["score"] = record_score(store, row_scores, record) * DISCOUNT ** pool[record]["hops"]
    context, used = pack(store, pool, budget)

    entry_log = []
    for record in entries:
        entry_log.append({"record": list(record), "rank_v": rank_in(vector_ranked, record),
                          "rank_w": rank_in(keyword_ranked, record), "rrf": round(rrf[record], 5)})
    pool_log = []
    for record in pool:
        item = pool[record]
        pool_log.append({"record": list(record), "hops": item["hops"], "route": item["route"],
                         "score": round(item["score"], 4), "packed": item["packed"]})
    filter_log = None
    if doc_filter:
        filter_log = sorted(doc_filter)

    line = {
        "asked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "question": question,
        "filter": filter_log,
        "arms": {"keyword": keyword, "vector": vector, "parent": parent, "budget": budget},
        "constants": {"K_ENTRY": K_ENTRY, "K_HOP": K_HOP, "DISCOUNT": DISCOUNT, "RRF_K": RRF_K, "prefix": QUERY_PREFIX},
        "entries": entry_log,
        "eligible": eligible,
        "pool": pool_log,
        "context": context,
        "tokens": used,
    }
    with open(OUT / "questions.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(line, ensure_ascii=False) + "\n")
    return context, line

# %% [markdown]
# ## Block 8: the reader
#
# Step 8: one call to gpt-5.6-luna on the flex tier, retried when the server is busy, its cost
# written to `calls.jsonl`.

# %%
READER = "gpt-5.6-luna"
PRICES = {"flex": (0.10, 0.60), "default": (0.20, 1.20)}

ANSWER_PROMPT = """Answer the question from the records below and nothing else. Every record is dated and names its
document. If the records do not answer it, say so. Reply with a JSON object: {{"answer": "<a short answer>"}}.

Records:
{context}

Question: {question}"""


def find_key():
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    try:
        from kaggle_secrets import UserSecretsClient
        return UserSecretsClient().get_secret("OPENAI_API_KEY")
    except Exception:
        return None


KEY = find_key()
SPENT = 0.0


def post(payload):
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=900) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            busy = error.code == 429 or error.code >= 500
            if not busy or attempt == 2:
                raise
            time.sleep(15 * (attempt + 1))


def ask_reader(question, context):
    global SPENT
    prompt = ANSWER_PROMPT.format(context="\n".join(context), question=question)
    payload = {
        "model": READER,
        "reasoning_effort": "low",
        "service_tier": "flex",
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": prompt}],
    }
    started = time.time()
    body = post(payload)

    usage = body.get("usage", {})
    price_in, price_out = PRICES.get(body.get("service_tier"), PRICES["default"])
    cost = (usage.get("prompt_tokens", 0) * price_in + usage.get("completion_tokens", 0) * price_out) / 1e6
    SPENT += cost
    call = {"question": question, "model": body.get("model"), "tier": body.get("service_tier"),
            "in": usage.get("prompt_tokens"), "out": usage.get("completion_tokens"),
            "seconds": round(time.time() - started, 1), "cost": cost}
    with open(OUT / "calls.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(call) + "\n")

    try:
        return json.loads(body["choices"][0]["message"]["content"])["answer"]
    except (ValueError, KeyError, TypeError):
        return None


if KEY:
    print("reader", READER, "on the flex tier; key present")
else:
    print("reader", READER, "; no key: retrieval runs, the reader does not")

# %% [markdown]
# ## Block 9: two questions
#
# A book question over the three Oz books, and the walkthrough's question over its history.

# %%
def show(question, doc_filter, where):
    context, line = retrieve(store, question, doc_filter)
    print()
    print(question)
    print(f"  in {where}: {len(line['entries'])} entries, {len(line['pool'])} in the pool, "
          f"{len(context)} packed in {line['tokens']} tokens")

    for entry in line["entries"][:8]:
        record = tuple(entry["record"])
        if record[0] == "parent":
            shown = "parent " + record[2]
        else:
            shown = render(store, record, set())[0][:110]
        print(f"  entry {record[0]:8} v{entry['rank_v'] or '-'} w{entry['rank_w'] or '-'}  {shown}")

    for text in context[:6]:
        print("  |", text[:160].replace("\n", " "))

    if KEY:
        print("  answer:", ask_reader(question, context))


show("Who is Tip, and what becomes of him?", collection_filter(store, "Oz series"), "the Oz series")
show("Which grocery store did I spend the most money at in the past month?",
     history_filter(store, "gpt4_2ba83207"), "history gpt4_2ba83207")
print()
print(f"reader cost ${SPENT:.4f}")
