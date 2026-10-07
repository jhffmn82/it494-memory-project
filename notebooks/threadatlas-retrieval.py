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
# around the quote, inside the unit (a blank line ends a paragraph). A passage longer than 2,000
# characters is cut to the quote and 1,000 characters on either side. When two facts come from one
# passage, the passage is given once.
#
# ## The algorithm
#
# The design is `docs/retrieval.md`: search decides where to enter, the store's structure decides
# where to move, and facts with their source decide what counts as evidence. Numbers in brackets
# point to the references at the end of the notebook.
#
# ```
# INPUT      question   text
#            filter     a set of documents (a history, a collection, a book), or none
#            asked on   the date the question is asked, when known
# CONSTANTS  K_ENTRY = 20   K_HOP = 10   DISCOUNT = 0.8   RRF_K = 60
#            BUDGET = 12,000 tokens   MAX_PASSAGE = 2,000 characters
#
# 1. SCORE EVERY VECTOR                                                         [4] [3]
#    q = embed(question)                         384 numbers, length 1
#    for each row i of the vector array:
#        sim[i] = q . v[i]                       cosine, one matrix product
#    score(record) = the largest sim[i] among the record's rows
#        a fact has one row; a cell or an abstract has one row per sentence
#
# 2. VECTOR ENTRIES
#    drop every row whose document is outside the filter
#    keep a parent's rows only when one of its instances is inside the filter
#    V = the K_ENTRY records with the highest score        ties broken by record id
#
# 3. KEYWORD ENTRIES                                                            [2]
#    match = the question's words joined by OR
#    W = the K_ENTRY records inside the filter that BM25 ranks best for match
#
# 4. FUSE THE TWO LISTS                                                         [1]
#    for each record r in V or W:
#        rrf(r) = sum, over the lists that hold r, of 1 / (RRF_K + rank of r in that list)
#    entries = the records ordered by rrf, highest first
#
# 5. ROUTE, TRAVERSE, SUBSTANTIATE: ONE HOP FROM EVERY ENTRY                    [5] [6]
#    pool = empty
#    for each entry e that is not a parent:
#        pool[e] = hop 0
#    for each entry e, in order:
#        n = the entity e is about          u = the unit e was read from
#        if e is a fact:
#            edges = { cell:     n's cell in u, when there is one               route
#                      abstract: n's abstract                                   route }
#        if e is a cell:
#            edges = { abstract: n's abstract                                   route
#                      previous: n's cell in the unit before, by position       traverse
#                      next:     n's cell in the unit after                     traverse
#                      facts:    n's facts in u                                 substantiate }
#        if e is an abstract:
#            edges = { cells:    n's cells                                      traverse
#                      facts:    n's facts                                      substantiate }
#        if e is not a parent:
#            edges += { parent:  the abstracts of the other instances of n's parent,
#                                inside the filter                              route }
#        if e is a parent:
#            edges = { children: the abstracts of e's instances inside the filter }
#        for each edge:
#            candidates = the edge's records, without e
#            best = the K_HOP candidates with the highest score(record)
#            for each record r in best:
#                if r is not in pool:  pool[r] = hop 1
#
#    an entity with no abstract of its own (a chat's) uses its document's abstract
#    a document's abstract has the document's own facts and its unit summaries as cells
#
# 6. RANK THE POOL                                                              [7]
#    for each record r in pool:
#        final(r) = score(r) x DISCOUNT ^ hop(r)
#
# 7. BUNDLE, RENDER AND PACK                                                    [8] [5]
#    bundles = for each cell in pool:      the cell, then the pool's facts of the same
#                                          entity in the same unit, in source order
#              for each abstract in pool:  the abstract alone
#              for each fact in pool whose cell is not in pool:  the fact alone
#    a bundle's score is the final score of its first record
#
#    context = empty    used = 0    shown = empty
#    for each bundle b, by score, highest first:
#        text = date | document | unit | the first record's text
#        for each fact f in b with a quote:
#            passage = source_passage(f)
#            if passage is in shown:  text = text + "the same passage as above"
#            else:                    text = text + passage
#        if used + tokens(text) > BUDGET:
#            skip b                              a bundle is packed whole or not at all
#        else:
#            add text to context;  used = used + tokens(text);  add b's passages to shown
#
#    source_passage(fact):                       fact -> unit -> raw text in Step 0
#        text = the document's text in Step 0
#        a, b = the start and end of the fact's unit in text
#        if the unit is a chat turn:  passage = text[a : b]
#        else:                        passage = the paragraph around the quote, inside a..b
#        if passage is longer than MAX_PASSAGE:
#            passage = the quote and MAX_PASSAGE / 2 characters on either side, inside a..b
#        return passage
#
# 8. ANSWER                                                                     [6]
#    answer = reader(question, context, asked on)     the records and nothing else
# ```
#
# ## A walkthrough: one question, step by step
#
# LongMemEval question gpt4_2ba83207 asks, of one user's chat history: *"Which grocery store did I
# spend the most money at in the past month?"* The benchmark's answer is Thrive Market. The user
# mentioned three purchases in three different sessions, and the answer needs all three. The numbers
# below are this notebook's own log for that question.
#
# 1. **The filter.** The history is the 53 sessions under `chats/longmemeval/gpt4_2ba83207/`, from
#    `path_filter`. Every vector outside those 53 documents is masked out. A parent's vector stays
#    only when one of its instances is in the filter.
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
# 5. **One hop.** A chat session has no cells and no entity abstracts, so most edges are empty here.
#    Each fact entry routes up to its session's abstract (12 distinct abstracts join the pool), and
#    the 2 abstract entries pull down their sessions' facts (94 offered, the 10 most similar per
#    abstract taken, 10 new). The parent edge offered 1 record. The pool ends at 56 records: the 34
#    entries, 12 abstracts and 10 facts.
# 6. **Scoring.** Every record in the pool is scored on its own similarity to the question, times
#    0.8 if it was reached by a hop. An entry at 0.60 and a hop record at 0.75 both score 0.60.
# 7. **Bundling and packing.** With no cells, every record here is a bundle of its own. Each is
#    rendered with its date, document, unit and text, a fact with the user's turn it came from, read
#    from Step 0 at the fact's unit. Bundles are added whole, best first, until the next one would
#    pass 12,000 tokens. Here all 56 fit, in 9,066 tokens, 15 of them facts whose turn was already
#    given above. The Walmart $120 fact is second, the Publix $60 fact fourth, and the Thrive Market
#    $150 fact sixteenth, each with the user's own words.
# 8. **The reader.** gpt-5.6-luna gets the 56 bundles, the date the question is asked (2023/05/30),
#    and the question, and answers in JSON. It is told to use the records and nothing else, that a
#    later record is the current one when two disagree, and to fit any advice to what the records
#    say about the user. On its first run it answered Thrive Market.
#
# A book uses the rest of the structure. On Block 9's Dandy Dick question the entries are cells,
# facts and abstracts; from them the hop reaches 9 cells from their facts, 9 abstracts, 5 cells just
# before or after an entry cell, 10 cells from abstracts and 23 facts under cells and abstracts. A
# cell is then packed with its own facts under it, each with its paragraph of the play.
#
# ## The constants
#
# | name | value | what it controls |
# |---|---|---|
# | `K_ENTRY` | 20 | records taken from each entry scan |
# | `K_HOP` | 10 | records taken from each edge of each entry, the most similar first |
# | `DISCOUNT` | 0.8 | the score multiplier for a record reached by a hop |
# | `RRF_K` | 60 | the reciprocal rank fusion constant, as Cormack et al. fixed it |
# | `BUDGET` | 12,000 | tokens of context the reader is given |
# | `MAX_PASSAGE` | 2,000 | characters of source text given with one fact; a longer passage is cut to the quote and 1,000 either side |
#
# `BUDGET` was raised from 6,000 after the first run with the reader (Block 10): on one question
# the long turns given as source passages filled 6,000 tokens and two of the three facts the answer
# needs were cut. The others have not been tuned. All are logged with every question so a run can be
# repeated.
#
# ## What it does not do yet
#
# - Adjudicated claims are not pulled: the store gives them no vector to score and the design no
#   bundle to pack them in.
# - Only the budget has been adjusted, on the 14 tuning questions. Tuning the rest needs a harness
#   that scores answers, which is the next build.
# - By ruling, not this fall: a model reranker, query rewriting, a multi-hop agent, PageRank.
#
# ## Running it
#
# On Kaggle: attach the `it494-threadatlas-store` and `it494-threadatlas-step0` datasets, turn
# Internet on (fastembed fetches the embedding model once), and add an `OPENAI_API_KEY` secret for
# the reader. Block 0 says at once whether the key and the connection work. Without a key
# everything runs except the answer. Locally: set `STORE_DIR` to a folder
# holding the store's two files and `STEP0_DIR` to one holding Step 0's, and run the script.

# %% [markdown]
# ## Block 0: the key and the connection
#
# Run this first. It looks for `OPENAI_API_KEY` (the environment, then the Kaggle secret of that
# name) and makes one tiny call to the reader model. It prints one of three things: the key works;
# there is no key, in which case retrieval still runs and the reader does not; or the key or the
# connection failed, with OpenAI's own message, and the run stops here.

# %%
import json
import os
import urllib.error
import urllib.request

READER = "gpt-5.6-luna"


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

if not KEY:
    print("NO KEY: OPENAI_API_KEY is not in the environment or attached as a Kaggle secret.")
    print("Retrieval will run. The reader will not answer.")
    print("On Kaggle: Add-ons, Secrets, tick OPENAI_API_KEY, then Save Version, Save & Run All.")
else:
    payload = {
        "model": READER,
        "reasoning_effort": "low",
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": 'Reply with the JSON object {"ok": true}.'}],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        print("KEY FOUND, CONNECTION WORKS:", body["model"], "replied", body["choices"][0]["message"]["content"])
    except urllib.error.HTTPError as error:
        print("KEY FOUND, BUT OPENAI REFUSED THE CALL: HTTP", error.code)
        print(error.read().decode("utf-8", errors="replace")[:500])
        raise SystemExit("fix the key or the account, then run again")
    except urllib.error.URLError as error:
        print("KEY FOUND, BUT NO CONNECTION TO OPENAI:", error.reason)
        raise SystemExit("turn Internet on in the notebook's settings, then run again")

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

VERSION = "threadatlas-retrieval 0.5"

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
BUDGET = int(os.environ.get("BUDGET", "12000"))
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
# title and date, and each entity's name. Then the two filters: a collection by name, and the
# documents under a path, such as one LongMemEval history's folder. Last, the source text: each of the store's documents from
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
    document_node = {}
    for doc_id, node_id, name, kind in db.execute("select doc_id, node_id, name, kind from node"):
        entity_names[(doc_id, node_id)] = name
        if kind == "document":
            document_node[doc_id] = node_id

    unit_position = {}
    for unit_id, position in db.execute("select unit_id, position from unit"):
        unit_position[unit_id] = position

    store = {}
    store["db"] = db
    store["vectors"] = vectors.astype(np.float32)
    store["record_of_row"] = record_of_row
    store["rows_of_record"] = rows_of_record
    store["documents_of_parent"] = documents_of_parent
    store["documents"] = documents
    store["entity_names"] = entity_names
    store["document_node"] = document_node
    store["unit_position"] = unit_position
    return store


def collection_filter(store, name):
    sql = """select i.doc_id from document_in i
             join collection c on c.collection_id = i.collection_id
             where c.name = ?"""
    doc_ids = set()
    for (doc_id,) in store["db"].execute(sql, (name,)):
        doc_ids.add(doc_id)
    return doc_ids


def path_filter(store, path):
    doc_ids = set()
    for doc_id, source_uri in store["db"].execute("select doc_id, source_uri from document"):
        if path in source_uri:
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
# ## Block 5: route, traverse, substantiate
#
# Step 5: from each entry, one hop along the structure the store holds. `edges_of` gives the edges
# for an entry by its kind; `expand` takes the `K_HOP` most similar records of each edge. A cell is
# named by its entity and unit, `node_id@unit_id`.

# %%
def abstract_above(store, doc_id, node_id):
    db = store["db"]
    if db.execute("select 1 from abstract where doc_id = ? and node_id = ?", (doc_id, node_id)).fetchone():
        return [("abstract", doc_id, node_id)]

    # an entity with no abstract of its own (a chat's) is routed to its document's abstract
    document = store["document_node"].get(doc_id)
    if document and db.execute("select 1 from abstract where doc_id = ? and node_id = ?", (doc_id, document)).fetchone():
        return [("abstract", doc_id, document)]
    return []


def cells_in_order(store, doc_id, node_id):
    units = []
    for (unit_id,) in store["db"].execute("select unit_id from cell where doc_id = ? and node_id = ?", (doc_id, node_id)):
        units.append((store["unit_position"].get(unit_id, 0), unit_id))
    units.sort()

    cells = []
    for position, unit_id in units:
        cells.append(("cell", doc_id, node_id + "@" + unit_id))
    return cells


def facts_in_unit(db, doc_id, node_id, unit_id):
    facts = []
    for (fact_id,) in db.execute("select fact_id from fact where doc_id = ? and subject = ? and unit_id = ?",
                                 (doc_id, node_id, unit_id)):
        facts.append(("fact", doc_id, fact_id))
    return facts


def facts_of(store, doc_id, node_id):
    db = store["db"]
    facts = []
    if node_id == store["document_node"].get(doc_id):
        rows = db.execute("select fact_id from fact where doc_id = ?", (doc_id,))
    else:
        rows = db.execute("select fact_id from fact where doc_id = ? and subject = ?", (doc_id, node_id))
    for (fact_id,) in rows:
        facts.append(("fact", doc_id, fact_id))
    return facts


def instance_abstracts(store, parent_id, doc_filter, skip):
    abstracts = []
    for doc_id, node_id in store["db"].execute("select doc_id, node_id from instance_of where parent_id = ?", (parent_id,)):
        if (doc_id, node_id) == skip:
            continue
        if doc_filter is not None and doc_id not in doc_filter:
            continue
        abstracts += abstract_above(store, doc_id, node_id)
    return abstracts


def edges_of(store, entry, doc_filter, use_parents):
    db = store["db"]
    kind, doc_id, record_id = entry
    edges = {}

    if kind == "parent":
        edges["children"] = instance_abstracts(store, int(record_id), doc_filter, None)
        return edges

    if kind == "fact":
        node_id, unit_id = db.execute("select subject, unit_id from fact where doc_id = ? and fact_id = ?",
                                      (doc_id, record_id)).fetchone()
        edges["cell"] = []
        if unit_id and db.execute("select 1 from cell where doc_id = ? and node_id = ? and unit_id = ?", (doc_id, node_id, unit_id)).fetchone():
            edges["cell"] = [("cell", doc_id, node_id + "@" + unit_id)]
        edges["abstract"] = abstract_above(store, doc_id, node_id)

    elif kind == "cell":
        node_id, unit_id = record_id.split("@")
        edges["abstract"] = abstract_above(store, doc_id, node_id)
        cells = cells_in_order(store, doc_id, node_id)
        here = cells.index(entry)
        edges["previous"] = []
        if here > 0:
            edges["previous"] = [cells[here - 1]]
        edges["next"] = []
        if here + 1 < len(cells):
            edges["next"] = [cells[here + 1]]
        edges["facts"] = facts_in_unit(db, doc_id, node_id, unit_id)

    else:
        node_id = record_id
        edges["cells"] = cells_in_order(store, doc_id, node_id)
        edges["facts"] = facts_of(store, doc_id, node_id)

    if use_parents:
        edges["parent"] = []
        found = db.execute("select parent_id from instance_of where doc_id = ? and node_id = ?", (doc_id, node_id)).fetchone()
        if found:
            edges["parent"] = instance_abstracts(store, found[0], doc_filter, (doc_id, node_id))
    return edges


def expand(store, row_scores, entries, doc_filter, use_parents):
    pool = {}
    for record in entries:
        if record[0] != "parent":
            pool[record] = {"hops": 0, "edge": "entry", "from": None}

    eligible = []
    for entry in entries:
        edges = edges_of(store, entry, doc_filter, use_parents)
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
                    pool[record] = {"hops": 1, "edge": edge, "from": list(entry)}
    return pool, eligible

# %% [markdown]
# ## Block 6: bundles, and what the reader sees
#
# Steps 6 and 7. The pool is grouped into bundles: a cell with the pool's facts of the same entity in
# the same unit, an abstract alone, a fact alone when its cell is not in the pool. A bundle is one
# dated block of text, each fact with the passage of the source it was read from, and bundles are
# packed whole to the token budget. A chat's title is its session id, so the first 8 characters of
# its `doc_id` are shown instead.

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

    start = unit_start
    end = unit_end
    if kind != "user" and kind != "assistant":
        for blank_line in ["\n\n", "\r\n\r\n"]:
            found = text.rfind(blank_line, unit_start, quote_start)
            if found != -1 and found > start:
                start = found
            found = text.find(blank_line, quote_end, unit_end)
            if found != -1 and found < end:
                end = found

    if end - start > MAX_PASSAGE:
        start = max(unit_start, quote_start - MAX_PASSAGE // 2)
        end = min(unit_end, quote_end + MAX_PASSAGE // 2)
    return start, end, text[start:end].strip()


def read_fact(store, doc_id, fact_id):
    fields = ["subject", "subject_name", "predicate", "object", "object_is_node",
              "qualifiers", "occurred_at", "direction", "quote", "quote_start", "quote_end", "unit_id"]
    values = store["db"].execute("select " + ", ".join(fields) + " from fact where doc_id = ? and fact_id = ?",
                                 (doc_id, fact_id)).fetchone()
    fact = {}
    for i in range(len(fields)):
        fact[fields[i]] = values[i]
    return fact


def fact_line(store, doc_id, fact):
    names = store["entity_names"]
    subject = names.get((doc_id, fact["subject"]), fact["subject"])
    if fact["direction"] == "mentioned" and fact["subject_name"]:
        subject = fact["subject_name"]
    thing = fact["object"]
    if fact["object_is_node"]:
        thing = names.get((doc_id, fact["object"]), fact["object"])
    line = subject + " " + fact["predicate"].replace("_", " ") + " " + thing
    if fact["qualifiers"]:
        line += " (" + fact["qualifiers"] + ")"
    return line


def source_line(store, doc_id, fact, shown, indent):
    if not fact["quote"]:
        return "", None
    start, end, words = source_passage(store, doc_id, fact["unit_id"], fact["quote_start"], fact["quote_end"])
    passage = (doc_id, start, end)
    if passage in shown:
        return "\n" + indent + "source: the same passage as above", passage
    return "\n" + indent + 'source: "' + words + '"', passage


def make_bundles(store, pool):
    cell_of = {}
    for record in pool:
        if record[0] == "cell":
            node_id, unit_id = record[2].split("@")
            cell_of[(record[1], node_id, unit_id)] = record

    bundles = {}
    for record in pool:
        if record[0] != "fact":
            bundles[record] = []

    for record in pool:
        if record[0] == "fact":
            fact = read_fact(store, record[1], record[2])
            cell = cell_of.get((record[1], fact["subject"], fact["unit_id"]))
            if cell is None:
                bundles[record] = []
            else:
                bundles[cell].append((fact["quote_start"] or 0, record[2], record))

    for head in bundles:
        bundles[head].sort()
        facts = []
        for item in bundles[head]:
            facts.append(item[2])
        bundles[head] = facts
    return bundles


def render(store, head, facts, shown):
    db = store["db"]
    names = store["entity_names"]
    kind, doc_id, record_id = head
    title = document_title(store, doc_id)
    document_date = store["documents"][doc_id]["occurred_at"]
    passages = []
    seen = set(shown)

    if kind == "fact":
        fact = read_fact(store, doc_id, record_id)
        label, unit_date = unit_label_and_date(db, fact["unit_id"])
        date = fact["occurred_at"] or unit_date or document_date
        source, passage = source_line(store, doc_id, fact, seen, "  ")
        if passage is not None:
            passages.append(passage)
        return f"{date} | {title} | {label or 'record'} | {fact_line(store, doc_id, fact)}" + source, passages

    if kind == "abstract":
        text = db.execute("select text from abstract where doc_id = ? and node_id = ?", (doc_id, record_id)).fetchone()[0]
        entity = names.get((doc_id, record_id), record_id)
        return f"{document_date} | {title} | abstract | {entity}: {text}", passages

    node_id, unit_id = record_id.split("@")
    text = db.execute("select text from cell where doc_id = ? and node_id = ? and unit_id = ?",
                      (doc_id, node_id, unit_id)).fetchone()[0]
    label, unit_date = unit_label_and_date(db, unit_id)
    entity = names.get((doc_id, node_id), node_id)
    block = f"{unit_date or document_date} | {title} | {label or unit_id[:8]} | {entity}: {text}"
    for record in facts:
        fact = read_fact(store, doc_id, record[2])
        source, passage = source_line(store, doc_id, fact, seen, "    ")
        block += "\n  - " + fact_line(store, doc_id, fact) + source
        if passage is not None:
            passages.append(passage)
            seen.add(passage)
    return block, passages


def pack(store, pool, budget):
    bundles = make_bundles(store, pool)
    scores = {}
    for head in bundles:
        scores[head] = pool[head]["score"]

    context = []
    used = 0
    shown = set()
    for head in best_first(bundles, scores):
        text, passages = render(store, head, bundles[head], shown)
        size = count_tokens(text)
        packed = used + size <= budget
        for record in [head] + bundles[head]:
            pool[record]["bundle"] = list(head)
            pool[record]["packed"] = packed
        if not packed:
            continue
        context.append(text)
        used += size
        for passage in passages:
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
        pool_log.append({"record": list(record), "hops": item["hops"], "edge": item["edge"], "from": item["from"],
                         "score": round(item["score"], 4), "bundle": item["bundle"], "packed": item["packed"]})
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
# Step 8: one call to gpt-5.6-luna on the flex tier, with the key Block 0 found, retried when the
# server is busy, its cost written to `calls.jsonl`. When the date a question is asked is known,
# the reader is told it, so that "last week" or "the past month" has something to count from. Two
# sentences of the prompt
# come from the first run of Block 10: a later record is current when two disagree (it had answered
# with an older personal best), and advice is to fit the user's details (it had declined to
# recommend anything, since no record is itself a recommendation).

# %%
PRICES = {"flex": (0.10, 0.60), "default": (0.20, 1.20)}

ANSWER_PROMPT = """Answer the question from the records below and nothing else. Every record is dated and names its
document. If the records do not answer it, say so. When records disagree, the one with the later date is
current. When the question asks for advice or a recommendation, give one that fits what the records say about
the user. Reply with a JSON object: {{"answer": "<a short answer>"}}.

Records:
{context}
{today}
Question: {question}"""


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


def ask_reader(question, context, asked_on=None):
    global SPENT
    today = ""
    if asked_on:
        today = "\nThe question is asked on " + asked_on + ".\n"
    prompt = ANSWER_PROMPT.format(context="\n".join(context), today=today, question=question)
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
    call = {"question": question, "asked_on": asked_on, "model": body.get("model"), "tier": body.get("service_tier"),
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
# ## Block 9: examples
#
# Two questions drawn at random (seed 20260930) from the benchmarks' own questions about documents in
# this store. Each prints three parts: the question, the retrieved text exactly as the model
# receives it, and the model's response (which needs the OPENAI_API_KEY secret). The first is
# LongMemEval question e8a79c70 (its answer, from the benchmark: 2-3 eggs), searched over all 71 chat
# sessions in the store and asked on the benchmark's date for it. The second is a GraphRAG-Bench
# question about the novel Dandy Dick (the benchmark's answer: THE DEAN is also known as Gus).

# %%
RULE = "=" * 100


def heading(title):
    print(RULE)
    print(title)
    print(RULE)


def ask(question, doc_filter, asked_on=None):
    context, line = retrieve(store, question, doc_filter)

    heading("1. QUESTION")
    print(question)
    if asked_on:
        print("asked on", asked_on)
    print()

    heading(f"2. RETRIEVED TEXT GIVEN TO THE MODEL ({len(context)} bundles, {line['tokens']} tokens)")
    for text in context:
        print(text)
        print()

    heading(f"3. MODEL RESPONSE ({READER})")
    if KEY:
        print(ask_reader(question, context, asked_on))
    else:
        print("no OPENAI_API_KEY in this run, so the model was not asked")
    print()

# %%
ask("I was going through our previous conversation about making a classic French omelette, and I wanted "
    "to confirm - how many eggs did you say we need for the recipe?",
    path_filter(store, "chats/longmemeval/"), "2023/05/30 (Tue) 08:29")

# %%
ask("What is the connection between THE DEAN and the character Gus in 'Dandy Dick'?",
    path_filter(store, "graphrag-bench/Novel-40700"))

# %% [markdown]
# ## Block 10: every memory question in the store
#
# The 14 LongMemEval questions whose sessions are in this store, each asked through the same path as
# Block 9, searched inside its own history's folder, and asked on the date the benchmark gives for
# it. Only the prompt and the model's response are printed; the retrieved text is in
# `questions.jsonl`.
#
# This is a check that the path answers, not a benchmark score: only gpt4_2ba83207 has its whole
# history here (53 sessions). The other 13 have their answer sessions alone (1 to 3 of about 50), so
# there is far less to search through than the benchmark gives. These 14 are the tuning questions:
# the first run with the reader (0.4, 2026-10-07) matched the benchmark on 11, and the three misses
# (06878be2, 0a995998, 6a1eabeb) led to the budget and the two prompt sentences of 0.5.
#
# | question | type | the benchmark's answer |
# |---|---|---|
# | 06878be2 | preference | Sony-compatible accessories or high-quality photography gear |
# | 0a995998 | multi-session | 3 |
# | 0e5e2d1a | assistant | 38 subjects |
# | 118b2229 | user | 45 minutes each way |
# | 4c36ccef | assistant | Roscioli |
# | 6a1eabeb | knowledge update | 25 minutes and 50 seconds |
# | 6aeb4375 | knowledge update | four |
# | 7161e7e2 | assistant | 8 am - 4 pm (Day Shift) on Sundays |
# | 8a2466db | preference | resources tailored to Adobe Premiere Pro and its advanced settings |
# | e47becba | user | Business Administration |
# | e8a79c70 | assistant | 2-3 eggs |
# | gpt4_2ba83207 | multi-session | Thrive Market |
# | gpt4_59149c77 | temporal | 7 days (8 including the last day) |
# | gpt4_b5700ca9 | temporal | 4 days |

# %%
MEMORY_QUESTIONS = [
    ("06878be2", "2023/05/30 (Tue) 16:40",
     "Can you suggest some accessories that would complement my current photography setup?"),
    ("0a995998", "2023/02/15 (Wed) 23:50",
     "How many items of clothing do I need to pick up or return from a store?"),
    ("0e5e2d1a", "2023/05/30 (Tue) 18:13",
     "I wanted to follow up on our previous conversation about binaural beats for anxiety and depression. "
     "Can you remind me how many subjects were in the study published in the journal Music and Medicine "
     "that found significant reductions in symptoms of depression, anxiety, and stress?"),
    ("118b2229", "2023/05/30 (Tue) 20:36",
     "How long is my daily commute to work?"),
    ("4c36ccef", "2023/05/30 (Tue) 23:29",
     "Can you remind me of the name of the romantic Italian restaurant in Rome you recommended for dinner?"),
    ("6a1eabeb", "2023/06/25 (Sun) 13:22",
     "What was my personal best time in the charity 5K run?"),
    ("6aeb4375", "2023/10/22 (Sun) 15:38",
     "How many Korean restaurants have I tried in my city?"),
    ("7161e7e2", "2023/05/30 (Tue) 20:16",
     "I'm checking our previous chat about the shift rotation sheet for GM social media agents. "
     "Can you remind me what was the rotation for Admon on a Sunday?"),
    ("8a2466db", "2023/05/30 (Tue) 22:03",
     "Can you recommend some resources where I can learn more about video editing?"),
    ("e47becba", "2023/05/30 (Tue) 23:40",
     "What degree did I graduate with?"),
    ("e8a79c70", "2023/05/30 (Tue) 08:29",
     "I was going through our previous conversation about making a classic French omelette, and I wanted "
     "to confirm - how many eggs did you say we need for the recipe?"),
    ("gpt4_2ba83207", "2023/05/30 (Tue) 22:59",
     "Which grocery store did I spend the most money at in the past month?"),
    ("gpt4_59149c77", "2023/02/01 (Wed) 10:20",
     "How many days passed between my visit to the Museum of Modern Art (MoMA) and the "
     "'Ancient Civilizations' exhibit at the Metropolitan Museum of Art?"),
    ("gpt4_b5700ca9", "2023/04/10 (Mon) 10:28",
     "How many days ago did I attend the Maundy Thursday service at the Episcopal Church?"),
]

for question_id, asked_on, question in MEMORY_QUESTIONS:
    context, line = retrieve(store, question, path_filter(store, "chats/longmemeval/" + question_id + "/"))
    print(RULE)
    print("PROMPT:   asked on", asked_on)
    print("         ", question)
    if KEY:
        print("RESPONSE:", ask_reader(question, context, asked_on))
    else:
        print("RESPONSE: no OPENAI_API_KEY in this run, so the model was not asked")
print(RULE)
print(f"reader cost ${SPENT:.4f}")

# %% [markdown]
# ## References
#
# None of the steps is new. Each is a standard technique, and the combination is close to what
# published graph memory systems already do.
#
# 1. **Reciprocal rank fusion (step 4).** G. V. Cormack, C. L. A. Clarke and S. Buettcher,
#    "Reciprocal Rank Fusion outperforms Condorcet and individual Rank Learning Methods", SIGIR 2009.
#    The formula and k = 60 are theirs. S. Bruch, S. Gai and A. Ingber, "An Analysis of Fusion
#    Functions for Hybrid Retrieval", arXiv 2210.11934, 2023, find that a tuned weighted sum of the
#    two scores does better than RRF.
# 2. **BM25 (step 3).** S. Robertson and H. Zaragoza, "The Probabilistic Relevance Framework: BM25
#    and Beyond", Foundations and Trends in Information Retrieval 3(4), 2009. Here it is SQLite
#    FTS5's built-in `bm25()`.
# 3. **A record scored by its best sentence (step 1).** MaxP: Z. Dai and J. Callan, "Deeper Text
#    Understanding for IR with Contextual Neural Language Modeling", SIGIR 2019, which scores a
#    document by its best passage.
# 4. **The embedding (step 1).** `BAAI/bge-small-en-v1.5`: S. Xiao et al.,
#    "C-Pack: Packaged Resources To Advance General Chinese Embedding", arXiv 2309.07597, 2023.
# 5. **Enter a graph by similarity, expand to the neighbours, fill a token budget (steps 5 and 7).**
#    Microsoft GraphRAG's local search (https://microsoft.github.io/graphrag/query/local_search/)
#    enters through the entities most similar to the query, pulls their relationships and source
#    text, and cuts the candidates to a fixed context window. LightRAG (Z. Guo et al., arXiv
#    2410.05779, 2024) adds the one-hop neighbours of what it retrieves. HippoRAG (B. Jimenez
#    Gutierrez et al., NeurIPS 2024) spreads from the query's entities by Personalized PageRank
#    instead of a fixed hop.
# 6. **The closest match (steps 2 to 5 and 8).** Zep: P. Rasmussen, P. Paliychuk, T. Beauvais, J. Ryan
#    and D. Chalef, "Zep: A Temporal Knowledge Graph Architecture for Agent Memory", arXiv 2501.13956,
#    2025. It searches by cosine similarity, BM25 and breadth-first search over n hops, reranks with
#    RRF among others, and gives the model each fact with its date range. That is this path's shape,
#    and Zep reports on LongMemEval, one of the two benchmarks here.
# 7. **A score that shrinks with each hop (step 6).** Spreading activation: F. Crestani, "Application
#    of Spreading Activation Techniques in Information Retrieval", Artificial Intelligence Review 11,
#    1997.
# 8. **Search small, return large (step 7).** Sentence-window retrieval, as in LlamaIndex's
#    `SentenceWindowNodeParser`: the vector is a sentence, the model reads the text around it. Here
#    the fact is what is found and its passage of the source is what is read.
#
# What ThreadAtlas adds is not the search but what it searches: records that each belong to one
# document and carry a verbatim quote, and a tree of parents that links the same entity across
# documents without merging them. The parent edge is the one part to measure, by running the same
# questions with `parent=False`.
