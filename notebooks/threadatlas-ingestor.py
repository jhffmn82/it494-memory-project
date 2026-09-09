# %% [markdown]
# # ThreadAtlas ingestor
#
# One document at a time, from the extractor's export to a **document package**: the entities
# the document is about, every fact with a verbatim quote located at document offsets, a
# narrative cell per entity per unit, the document's abstract, and an abstract per major entity.
# Nothing here looks at a second document.
#
# ## What comes in
#
# The export folder (`EXPORT`, the Kaggle dataset, or `data/export`) holds three JSONL files,
# one row per line, written by the extractor. A fourth is optional.
#
# `documents.jsonl`, one row per document:
#
# | field | meaning |
# |---|---|
# | `doc_id` | the sha256 of the file bytes; every other row joins on it |
# | `source_uri` | corpus and file name, for example `it494-narrative-corpora-raw/oz/01_55.txt` |
# | `sha256`, `title`, `author`, `source_class`, `occurred_at`, `loader`, `ingested_at`, `flags` | what the extractor knew about the file |
# | `text` | the whole text, or `null` for a reference paper (then `papers.jsonl` says which PDF to read) |
#
# `units.jsonl`, one row per unit, the size-bounded runs the extractor cut the text into:
#
# | field | meaning |
# |---|---|
# | `unit_id`, `doc_id`, `position` | its id, its document, its place in reading order |
# | `label` | a human label, such as a chapter title or a range of turns |
# | `start`, `end` | character offsets into the document text |
# | `occurred_at`, `occurred_until` | when it was said, when the file carries times |
#
# `pieces.jsonl`, one row per natural piece (a chapter, a turn, a section) inside a unit:
#
# | field | meaning |
# |---|---|
# | `doc_id`, `unit_id`, `position`, `start`, `end` | where it is |
# | `kind` | `body`, `front_matter`, `license`, `references`, `turn`, and so on; a unit's kind is the kind of most of its characters |
# | `author` | the speaker of a chat turn, else `null` |
# | `occurred_at` | the time of a turn, else `null` |
#
# `papers.jsonl` (optional): `doc_id`, `file`, `pdf_sha256` for each document whose text is withheld.
#
# ## What goes out
#
# One package per document at `packages/<corpus>/<file>/<file>.jsonl`, every line one record with a
# `record` field: `document`, `unit`, `piece`, `node`, `alias`, `edge`, `profile`, `cell`,
# `abstract`, `adjudicated_fact`, `attribute`, `contradiction`, `fact`, `rejection`, `ledger`,
# `candidate`, and a final `completion` with the counts. A `roll-up.txt` is written beside it.
# The run logs sit at the top of the output folder: `calls.jsonl` (every model call with its
# cost), `retries.jsonl` and `rejections.jsonl` (replies that did not fit their shape),
# `ingest.log` and `receipt.json`.
#
# Ids minted here are readable: `<first 8 chars of doc_id>:doc` for the document node,
# `...:n<index>` for an entity node, `...:u<unit position>:f<n>` for a fact.
#
# ## The algorithm for a document of many units
#
# ```
# ingest(doc):
#     triage      ask once which kinds of unit are not the work (front matter, references, ...)
#                 and leave those units out
#     for each unit kept, WORKERS at a time:
#         entities    ask for the entities in the unit, each with its surface forms
#                     keep an entity only if one of its forms is found in the unit text
#         facts       ask for facts about those entities, each with a verbatim quote
#                     keep a fact only if its quote is located in the unit text;
#                     a quote that crosses a change of speaker is cut into one fact per voice
#         cells       ask for a unit summary and one narrative cell per major entity
#     reconcile   unit-local entities become document entities:
#                     same proper name and kind: united at once, no call
#                     other candidate pairs (a shared surface form, a shared name word, one
#                     said to be the other) are scored and queued, strongest first;
#                     round by round the judge answers same / different / unsure, ten pairs a call
#     fold        the abstract is a summary of the unit summaries;
#                 every major entity gets its own abstract
#     adjudicate  each major with 4 or more facts: one call consolidates them into facts,
#                 attributes and contradictions, each pointing at the raw facts behind it;
#                 majors with fewer facts keep their raw facts, and all those facts are
#                 checked against their passages in one call
#     verify      every fact a check flagged gets a second look: it stands, is reworded to what
#                 its passage does say, or is dropped; what is kept is checked once more
#     write       the package, then the roll-up
# ```
#
# ## The algorithm for a document of one unit (a chat session)
#
# ```
# ingest(doc):
#     triage      no call: front matter and licenses go by rule
#     the unit    entities; then facts and cells asked together
#     reconcile   nothing to merge: every unit-local entity is a document entity
#     fold        the unit summary is the abstract; a major's own cell is its abstract; no calls
#     adjudicate  nothing to consolidate: every fact is checked in one support call
#     verify      as above
#     write       the package
# ```
# About four calls a document instead of twenty-five.
#
# ## On Kaggle
#
# Attach the export dataset (`jhffmn/it494-threadatlas-step0`) and, for the reference papers
# whose text it withholds, the private PDFs (`jhffmn/it494-reference-papers`). Attach
# `OPENAI_API_KEY` under Add-ons > Secrets, turn Internet on, run block 3 to see the connection
# work, then the run blocks. The packages land under `/kaggle/working/packages`. To continue a
# stopped run, make a dataset from that output and attach it: finished packages are copied in
# and skipped.

# %% [markdown]
# ## Block 1: files
#
# Finds the export, the output folder and the papers folder, indexes `documents.jsonl` by byte
# offset so a document is read back with one seek, and loads the units and pieces grouped by
# document. `load_document(uri)` returns one document with its text, its units (each stamped
# with its kind) and its pieces. A reference paper's text is rebuilt from its PDF the way the
# extractor read it.

# %%
# Block 1: where things are, and how a document is read.
#
# The export is read from the first of these that exists: the EXPORT environment variable,
# the Kaggle dataset, the local folder. documents.jsonl is indexed once (doc_id, title, byte
# offset) and a document is read back with one seek. The public export withholds the
# reference papers' text; it is rebuilt from the PDF exactly as the extractor read it.
import hashlib
import json
import os
import re
import shutil
import sys
import time
import unicodedata
from datetime import datetime, timezone
from contextlib import redirect_stdout
from pathlib import Path

INGESTOR = "threadatlas-ingestor 0.9"
KAGGLE_EXPORTS = (Path("/kaggle/input/datasets/jhffmn/it494-threadatlas-step0"), Path("/kaggle/input/it494-threadatlas-step0"))
KAGGLE_PAPERS = (Path("/kaggle/input/datasets/jhffmn/it494-reference-papers"), Path("/kaggle/input/it494-reference-papers"))
LOCAL_EXPORT, LOCAL_PAPERS = Path("data/export"), Path("papers")
KAGGLE_OUT, LOCAL_OUT = Path("/kaggle/working/packages"), Path("data/packages")
BOILERPLATE = ("front_matter", "license")   # never the work, whatever the document

if hasattr(sys.stdout, "reconfigure"):            # a console that is not UTF-8 must not end the run
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def first_existing(variable, *candidates):
    """The folder the environment names, else the first candidate that exists, else None."""
    if os.environ.get(variable):
        return Path(os.environ[variable])
    return next((p for p in candidates if p.exists()), None)


def read_jsonl(path, tolerant=False):
    """One dict per non-empty line. The ingestor's own files can be cut short by a killed
    session, so `tolerant` stops at the first line that does not parse."""
    rows = []
    with Path(path).open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                if not tolerant:
                    raise
                break
    return rows


def pdf_text(data):
    """The extractor's reading of a PDF, kept verbatim so the export's offsets resolve: PyMuPDF's
    text layer page by page, pages joined with a newline."""
    try:
        import pymupdf
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pymupdf"], check=True)
        import pymupdf
    return "\n".join(page.get_text() for page in pymupdf.open(stream=data, filetype="pdf"))


def withheld_text(doc):
    """The text of a document the export withholds: the PDF papers.jsonl names, found under
    PAPERS, checked against the recorded sha256, read the extractor's way."""
    row = PAPERS_ROWS.get(doc["doc_id"])
    if row is None:
        raise ValueError(f"{doc['source_uri']}: the text is withheld and papers.jsonl does not name its PDF")
    if PAPERS is None:
        raise ValueError(f"{doc['source_uri']}: the text is withheld; attach the papers dataset"
                         " (jhffmn/it494-reference-papers) or set PAPERS to the folder of PDFs")
    path = PAPERS / row["file"]
    if not path.exists():
        raise ValueError(f"{doc['source_uri']}: the text is withheld and {path} is not there")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != row["pdf_sha256"]:
        raise ValueError(f"{doc['source_uri']}: {path.name} is not the PDF the export was made from (its sha256 differs)")
    return pdf_text(data)


def seed_from_prior_output():
    """On Kaggle a new session starts empty. If an earlier run's output was attached as a
    dataset, its packages are copied in first, so they are skipped rather than paid for again."""
    copied, root = 0, Path("/kaggle/input")
    if not root.exists():
        return 0
    for folder in root.rglob("packages"):
        for src in folder.rglob("*.jsonl"):
            dst = OUT / src.relative_to(folder)
            if src.parent != folder and not dst.exists():      # the run logs at the top level stay behind
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                copied += 1
    return copied


def index_documents():
    """source_uri -> {doc_id, title, author, offset}; the byte offset lets load_document seek."""
    index, offset = {}, 0
    with (EXPORT / "documents.jsonl").open("rb") as f:
        for raw in f:
            if raw.strip():
                doc = json.loads(raw.decode("utf-8"))
                index[doc["source_uri"]] = {"doc_id": doc["doc_id"], "title": doc["title"], "author": doc["author"], "offset": offset}
            offset += len(raw)
    return index


def by_document(rows):
    """{doc_id: rows in position order}."""
    grouped = {}
    for row in rows:
        grouped.setdefault(row["doc_id"], []).append(row)
    for group in grouped.values():
        group.sort(key=lambda r: r["position"])
    return grouped


def unit_kind(pieces, unit):
    """The kind of most of the unit's characters, from its pieces; 'body' when it has none.
    Code never branches on it: it is shown to the judge that decides which kinds to read."""
    chars = {}
    for p in pieces:
        if p["unit_id"] == unit["unit_id"]:
            chars[p["kind"]] = chars.get(p["kind"], 0) + p["end"] - p["start"]
    return max(chars, key=chars.get) if chars else "body"


def load_document(uri):
    """The document with its text, its units (each with its kind) and its pieces in order."""
    entry = BY_URI[uri]
    with (EXPORT / "documents.jsonl").open("rb") as f:
        f.seek(entry["offset"])
        doc = json.loads(f.readline().decode("utf-8"))
    assert doc["doc_id"] == entry["doc_id"]
    doc["units"] = [dict(u) for u in UNITS.get(doc["doc_id"], [])]
    doc["pieces"] = PIECES.get(doc["doc_id"], [])
    doc["text_rebuilt"] = doc["text"] is None
    if doc["text_rebuilt"]:
        doc["text"] = withheld_text(doc)
        if doc["units"] and doc["units"][-1]["end"] != len(doc["text"]):
            raise ValueError(f"{uri}: the rebuilt text has {len(doc['text']):,} chars but the units end at"
                             f" {doc['units'][-1]['end']:,}; the PDF was read differently from the extractor")
    for u in doc["units"]:                        # every unit must be a real slice of the text
        assert 0 <= u["start"] < u["end"] <= len(doc["text"]), (uri, u["position"])
        assert doc["text"][u["start"]:u["end"]].strip(), (uri, u["position"])
        u["kind"] = unit_kind(doc["pieces"], u)
    return doc


def find_document(name):
    """The source_uri of the document called `name`: by title (an exact title first, then a
    title containing it), else by the end of its source_uri; None when nothing matches."""
    wanted = name.casefold()
    exact = [uri for uri, e in BY_URI.items() if (e["title"] or "").casefold() == wanted]
    partial = [uri for uri, e in BY_URI.items() if wanted in (e["title"] or "").casefold()]
    matches = exact or partial
    if len(matches) > 1:
        print(f"{name!r} matches {len(matches)} titles; taking the first: {[BY_URI[u]['title'] for u in matches]}")
    if matches:
        return matches[0]
    return next((uri for uri in BY_URI if uri.endswith(name)), None)


EXPORT = first_existing("EXPORT", *KAGGLE_EXPORTS, LOCAL_EXPORT)
if EXPORT is None:
    raise SystemExit("no export found: attach the dataset on Kaggle, or set EXPORT to a folder holding documents.jsonl")
OUT = first_existing("OUT") or (KAGGLE_OUT if Path("/kaggle/working").exists() else LOCAL_OUT)
PAPERS = first_existing("PAPERS", *KAGGLE_PAPERS, LOCAL_PAPERS)
OUT.mkdir(parents=True, exist_ok=True)
SEEDED = seed_from_prior_output()
BY_URI = index_documents()
PAPERS_ROWS = {row["doc_id"]: row for row in read_jsonl(EXPORT / "papers.jsonl")} if (EXPORT / "papers.jsonl").exists() else {}
UNITS = by_document(read_jsonl(EXPORT / "units.jsonl"))
PIECES = by_document(read_jsonl(EXPORT / "pieces.jsonl"))
print(f"export {EXPORT}: {len(BY_URI)} documents, {sum(len(g) for g in UNITS.values())} units,"
      f" {sum(len(g) for g in PIECES.values())} pieces; packages to {OUT}")
if PAPERS_ROWS:
    print(f"{len(PAPERS_ROWS)} documents have their text withheld; their PDFs are"
          f" {'under ' + str(PAPERS) if PAPERS else 'NOT attached: attach jhffmn/it494-reference-papers to read them'}")
if SEEDED:
    print(f"{SEEDED} files seeded from a previous run's output")

# %% [markdown]
# ## Block 2: the model
#
# `generate(prompt, schema, stage)` is the one way the notebook talks to a model. It posts the
# prompt, checks the reply against the shape it must have, asks once more with the error
# appended if it does not fit, and returns `None` if it still does not. Every call is logged to
# `calls.jsonl` with its cost. `spend()` reads that log back. `start_block(budget)` sets a
# spending stop for one run block. `in_parallel` runs independent calls `WORKERS` at a time.

# %%
# Block 2: the model interface: generate(prompt, schema).
#
# The key comes from the OPENAI_API_KEY environment variable, else from the Kaggle secret of
# that name. Raw HTTP. The API rejects temperature, so reasoning_effort steers it. Every call
# is logged to calls.jsonl the moment it returns, with model, tokens, latency and cost. A
# reply that does not fit its schema is asked for once more with the error appended, then
# rejected; the first miss is logged in retries.jsonl. A timeout, a 429 or a 5xx is retried
# three times; a 429 for exhausted quota ends the run like the spend stop, which is checked
# before every call. Independent calls run WORKERS at a time; the logs take one lock.
import http.client
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

LUNA = "gpt-5.6-luna"                      # derive, support checks, corrections
TERRA = "gpt-5.6-terra"                    # judge, folds, adjudication
PRICE = {LUNA: (0.20, 1.20), TERRA: (2.00, 12.00)}          # $ per million tokens in, out
SPEND_STOP = float(os.environ.get("SPEND_STOP", "25"))     # a run block's budget, counted from start_block
BLOCK_START = 0.0                                          # what had been spent when the block began
WORKERS = int(os.environ.get("WORKERS", "4"))
DOCS_AT_ONCE = int(os.environ.get("DOCS_AT_ONCE", "1"))    # documents ingested together

KEY = os.environ.get("OPENAI_API_KEY")
if not KEY:
    try:
        from kaggle_secrets import UserSecretsClient
        KEY = UserSecretsClient().get_secret("OPENAI_API_KEY")
    except ImportError:                      # not on Kaggle
        KEY = None
    except Exception:                        # on Kaggle, but the secret is not attached
        KEY = None
        print("OPENAI_API_KEY is not attached to this notebook: Add-ons > Secrets, tick Attach; Settings > Internet on")

CALLS = []                                   # every call this session, in the order it returned
MISSES = {"retries": 0, "rejections": 0}     # replies that did not fit their schema
LOG_LOCK = threading.Lock()
TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float)}


class SpendStop(Exception):
    pass


class SchemaError(ValueError):
    pass


def record(name, row):
    """Append one row to a run log under OUT, so it survives whatever ends the session."""
    with LOG_LOCK:
        with (OUT / name).open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def in_parallel(function, items, width=None):
    """function over each item, `width` at a time (WORKERS when not said), results in the items'
    order. An error in one (a spend stop included) is raised once the calls in flight have
    returned."""
    width = max(width or WORKERS, 1)
    if width <= 1 or len(items) <= 1:
        return [function(item) for item in items]
    with ThreadPoolExecutor(max_workers=width) as pool:
        return list(pool.map(function, items))


def spend(doc=None, unit=None, since=0):
    """($, calls) logged since `since`; only one document's own calls when `doc` is given, only
    one unit's when `unit` is too. Documents run together, so a global delta would count a
    neighbour's calls as a document's own."""
    rows = [c for c in CALLS[since:] if (doc is None or c.get("doc") == doc) and (unit is None or c.get("unit") == unit)]
    return sum(c["cost"] for c in rows), len(rows)


def start_block(budget):
    """A run block's own budget, counted from here. The stop is per block, not per session:
    a later block's budget cannot be eaten by an earlier one (ruling of 09-07)."""
    global SPEND_STOP, BLOCK_START
    SPEND_STOP, BLOCK_START = budget, spend()[0]


def is_of_type(value, name):
    if name == "null":
        return value is None
    if name == "boolean":
        return isinstance(value, bool)
    return name in TYPES and isinstance(value, TYPES[name]) and not isinstance(value, bool)


def check_schema(value, schema, path="$"):
    """A small validator for the reply shapes in block 5: type, required keys, items, enum.
    Raises SchemaError naming the path, which goes back to the model on the retry."""
    allowed = schema.get("type", "object")
    allowed = allowed if isinstance(allowed, list) else [allowed]
    if not any(is_of_type(value, t) for t in allowed):
        raise SchemaError(f"{path}: expected {'/'.join(allowed)}, got {type(value).__name__}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaError(f"{path}: {value!r} is not one of {schema['enum']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                raise SchemaError(f"{path}.{key}: missing")
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                check_schema(value[key], sub, f"{path}.{key}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            check_schema(item, schema["items"], f"{path}[{i}]")


def post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.status, response.read().decode("utf-8")


def log_call(row):
    with LOG_LOCK:
        CALLS.append(row)
    record("calls.jsonl", row)


def call(url, payload, model, stage, ctx, prompt_chars):
    """One exchange with the API under the retry policy; the parsed body. Cost is logged here."""
    if not KEY:
        raise RuntimeError("no OPENAI_API_KEY in the environment (or attached as a Kaggle secret)")
    spent = spend()[0] - BLOCK_START
    if spent >= SPEND_STOP:
        raise SpendStop(f"spending stop: ${spent:.2f} of ${SPEND_STOP:.2f} for this block")
    price_in, price_out = PRICE[model]
    started = time.time()
    for attempt in range(3):
        try:
            status, text = post(url, payload)
        except urllib.error.HTTPError as error:
            status, text = error.code, error.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            # the server may have finished and billed the request: count the input as spent
            log_call({"stage": stage, "model": model, "in": prompt_chars // 4, "out": 0, "seconds": round(time.time() - started, 1),
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
    usage = body.get("usage", {})
    tokens_in, tokens_out = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    log_call({"stage": stage, "model": body.get("model", model), "in": tokens_in, "out": tokens_out,
              "seconds": round(time.time() - started, 1), "cost": (tokens_in * price_in + tokens_out * price_out) / 1e6, **ctx})
    return body


def generate(prompt, schema, stage, model=LUNA, effort="low", ctx=None):
    """The reply as a dict that fits `schema`, or None after one retry with the error appended."""
    ctx = ctx or {}
    for attempt in range(2):
        body = call("https://api.openai.com/v1/chat/completions",
                    {"model": model, "reasoning_effort": effort, "response_format": {"type": "json_object"},
                     "messages": [{"role": "user", "content": prompt}]}, model, stage, ctx, len(prompt))
        try:
            message = body["choices"][0]["message"]
            if not message.get("content"):
                raise SchemaError("empty reply" + (f" (refusal: {message.get('refusal')})" if message.get("refusal") else ""))
            reply = json.loads(message["content"])
            check_schema(reply, schema)
            return reply
        except (SchemaError, ValueError, TypeError, KeyError, IndexError) as e:
            error = f"{type(e).__name__}: {e}"
            kind = "retries" if attempt == 0 else "rejections"
            MISSES[kind] += 1
            record(f"{kind}.jsonl", {"stage": stage, "category": "schema", "detail": error[:200], **ctx})
            prompt += f"\n\nYour previous reply did not fit the required shape ({error}). Reply again, in exactly the shape asked for."
    return None


print(f"models {LUNA} (derive), {TERRA} (judge and fold); key {'present' if KEY else 'MISSING'}")

# %% [markdown]
# ## Block 3: connection test
#
# One tiny call, so a missing key or a closed network shows up before anything spends.

# %%
# Block 3: test the connection before anything spends. One tiny call.
if __name__ == "__main__":
    if not KEY:
        print("no key: attach OPENAI_API_KEY under Add-ons > Secrets, then rerun this cell")
    else:
        ping = generate('Reply with exactly the JSON object {"ok": true}.', {"type": "object", "required": ["ok"]}, "ping", ctx={"doc": "connection test"})
        print(f"chat reply {ping}; {len(CALLS)} calls, ${spend()[0]:.5f}")

# %% [markdown]
# ## Block 4: text helpers and the quote gate
#
# Small string helpers (`norm`, `snake_case`, `loose_name`, `name_words`) and the gate every
# quote must pass: `locate(text, quote)` returns where the quote is in the unit and how it was
# found (`exact`, `normalised`, `unwrapped`, `words`), or why it was not (`paraphrase`,
# `not_found`, `empty`). `surface_spans` finds every whole-word occurrence of an entity's name.
# The stored quote is always a verbatim slice of the document.

# %%
# Block 4: text helpers, and the quote gate.
#
# locate(unit_text, quote) says where the quote is inside the unit, or why it is not. The ways
# it can match, each named so the receipt says how many quotes needed which: `exact`, the
# substring as written; `normalised`, the same after both sides are normalised (one space for
# any whitespace, NFKC, straight quotes, one dash, a hyphenated line break closed, case
# folded), matched on a copy that maps every character back to its original offset;
# `unwrapped`, once the quotation marks the model wrapped it in come off, as whole words;
# `words`, the shortest passage holding at least WORDS_NEEDED of the quote's words in order,
# within three words of the quote's length, so a citation the model reworded at the edges
# still lands and the stored quote is the text's own words. Anything else is `paraphrase`
# (most of its words are there, in order, somewhere) or `not_found`. Stored offsets always
# index the original.

REPLACEMENTS = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "‒": "-", "−": "-", "‐": "-", "‑": "-", "­": "", " ": " "}
QUOTE_PAIRS = {"“": "”", '"': '"', "‘": "’", "'": "'"}
WORDS_NEEDED = 0.85                                  # the share of a quote's words a `words` match must hold, in order


def norm(s):
    """One space between words, case folded."""
    return " ".join(str(s or "").split()).casefold()


def word_count(s):
    return len(s.split())


def loose_name(name):
    """A name as the model may write it back: case folded, one space between words, a leading
    article dropped, so "The Scarecrow" finds "the Scarecrow"."""
    loose = norm(name)
    for article in ("the ", "a ", "an "):
        if loose.startswith(article):
            return loose[len(article):]
    return loose


def is_word_char(ch):
    return ch.isalnum() or ch == "_"


def snake_case(s):
    """A predicate name as lowercase_snake_case: letters, digits and underscores only."""
    out = []
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != "_":
            out.append("_")
    return "".join(out).strip("_")


def name_words(name):
    """The words of a name longer than three letters, case folded, punctuation stripped."""
    words = set()
    for token in name.replace("_", " ").casefold().split():
        word = "".join(ch for ch in token if ch.isalpha())
        if len(word) > 3:
            words.add(word)
    return words


def first_line(text):
    for line in text.split("\n"):
        if line.strip():
            return " ".join(line.split())[:120]
    return ""


def counts_text(counter):
    """'exact 6, normalised 2' from a dict of counts; 'none' when empty."""
    return ", ".join(f"{k} {v}" for k, v in counter.items()) or "none"


def tally(items):
    """{item: how many times it occurs}, in first-seen order."""
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts


def hyphen_breaks(text):
    """The offsets of the hyphen and line break in every 'word-\\nword' run, so a word the PDF
    wrapped at a hyphen reads whole."""
    skip = set()
    for marker in ("-\n", "-\r\n"):
        i = text.find(marker)
        while i >= 0:
            before = text[i - 1] if i > 0 else ""
            after = text[i + len(marker)] if i + len(marker) < len(text) else ""
            if before.isalpha() and after.isalpha():
                skip.update(range(i, i + len(marker)))
            i = text.find(marker, i + 1)
    return skip


def normalised(text):
    """(normalised string, map from each of its characters to an offset in the original)."""
    skip = hyphen_breaks(text)
    out, back, in_space = [], [], True
    for i, ch in enumerate(text):
        if i in skip:
            continue
        ch = REPLACEMENTS.get(ch, ch)
        if ch.isspace():
            if not in_space:
                out.append(" ")
                back.append(i)
                in_space = True
            continue
        in_space = False
        for c in unicodedata.normalize("NFKC", ch).casefold():
            out.append(c)
            back.append(i)
    if out and out[-1] == " ":
        out.pop()
        back.pop()
    return "".join(out), back


def normalised_unit(text, cache):
    """The unit's normalised copy, computed once per unit."""
    if "norm" not in cache:
        cache["norm"] = normalised(text)
    return cache["norm"]


def word_runs(s):
    """Every run of word characters in `s`, as (word, start, end); the gate's one tokeniser."""
    runs, i = [], 0
    while i < len(s):
        if is_word_char(s[i]):
            j = i
            while j < len(s) and is_word_char(s[j]):
                j += 1
            runs.append((s[i:j], i, j))
            i = j
        else:
            i += 1
    return runs


def words_only(s):
    return [word for word, start, end in word_runs(s)]


def unwrapped(written):
    """One layer of the model's own quotation marks off: a matched pair, or a stray double mark
    at either end. A single mark alone stays, since it may be the text's own apostrophe."""
    if len(written) >= 2 and written[0] in QUOTE_PAIRS and written[-1] == QUOTE_PAIRS[written[0]]:
        return written[1:-1].strip()
    bare = written
    if bare[:1] in "“\"":
        bare = bare[1:]
    if bare[-1:] in "”\"":
        bare = bare[:-1]
    return bare.strip()


def classify_miss(ntext, nquote):
    """'paraphrase' when at least seven in ten of the quote's words appear in order, else
    'not_found'."""
    wanted, matched = words_only(nquote), 0
    for word in words_only(ntext):
        if matched < len(wanted) and word == wanted[matched]:
            matched += 1
    return "paraphrase" if matched >= 0.7 * max(1, len(wanted)) else "not_found"


def find_exact_or_normalised(text, needle, cache):
    """(start, end, how) of the first exact or normalised hit of `needle`, else (None, None, why)."""
    needle = needle.strip()
    if not needle:
        return None, None, "empty"
    i = text.find(needle)
    if i >= 0:
        return i, i + len(needle), "exact"
    ntext, back = normalised_unit(text, cache)
    nneedle, _ = normalised(needle)
    i = ntext.find(nneedle) if nneedle else -1
    if i >= 0:
        return back[i], back[i + len(nneedle) - 1] + 1, "normalised"
    return None, None, classify_miss(ntext, nneedle)


def in_order(wanted, have):
    """How many of `wanted` occur in `have` in order (the longest common subsequence), with the
    first and last positions in `have` that take part, and how many of `wanted` they span."""
    n, m = len(wanted), len(have)
    table = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            table[i][j] = table[i + 1][j + 1] + 1 if wanted[i] == have[j] else max(table[i + 1][j], table[i][j + 1])
    i = j = 0
    taken = []
    while i < n and j < m:
        if wanted[i] == have[j]:
            taken.append((i, j))
            i, j = i + 1, j + 1
        elif table[i + 1][j] >= table[i][j + 1]:
            i += 1
        else:
            j += 1
    if not taken:
        return 0, 0, 0, 0
    return len(taken), taken[0][1], taken[-1][1], taken[-1][0] - taken[0][0] + 1


def words_hit(text, quote, cache):
    """The shortest passage holding at least WORDS_NEEDED of the quote's words in order, no
    longer than the quote plus three words, the quote's own unmatched words falling only at its
    front or its back (decision 47); (start, end) or (None, None)."""
    wanted = words_only(normalised(quote)[0])
    if len(wanted) < 4:
        return None, None
    ntext, back = normalised_unit(text, cache)
    words = word_runs(ntext)
    needed, best = max(4, int(WORDS_NEEDED * len(wanted) + 0.999)), None
    for at in range(len(words)):
        if words[at][0] not in wanted:
            continue
        window = [w[0] for w in words[at:at + len(wanted) + 3]]
        matched, first, last, spanned = in_order(wanted, window)
        if matched >= needed and spanned == matched and (best is None or (matched, first - last) > (best[0], best[1] - best[2])):
            best = (matched, at + first, at + last)
    if best is None:
        return None, None
    return back[words[best[1]][1]], back[words[best[2]][2] - 1] + 1


def surface_spans(text, surface, cache):
    """Every whole-word occurrence of a surface form in the unit, as offsets into the original
    text, found on the normalised copy so case and quotes do not matter."""
    nsurface, _ = normalised(surface or "")
    if not nsurface:
        return []
    ntext, back = normalised_unit(text, cache)
    spans, i = [], ntext.find(nsurface)
    while i >= 0:
        j = i + len(nsurface)
        before = ntext[i - 1] if i > 0 else " "
        after = ntext[j] if j < len(ntext) else " "
        if not is_word_char(before) and not is_word_char(after):
            spans.append((back[i], back[j - 1] + 1))
        i = ntext.find(nsurface, i + 1)
    return spans


def locate(text, quote, cache=None):
    """(start, end, how) with offsets into `text`, or (None, None, why). Every path stores a
    verbatim slice of the document; `words` only differs in how it FINDS one, and whether that
    passage states the fact is the support check's question, not the gate's. A quote written with
    an ellipsis is refused rather than stitched: the span between its pieces holds text the model
    never cited (ruling of 09-08)."""
    cache = {} if cache is None else cache
    written = (quote or "").strip()
    start, end, how = find_exact_or_normalised(text, written, cache)
    if start is not None:
        return start, end, how
    bare = unwrapped(written)
    if bare and bare != written:
        spans = surface_spans(text, bare, cache)
        if spans:
            return spans[0][0], spans[0][1], "unwrapped"
    start, end = words_hit(text, bare, cache)
    if start is not None:
        return start, end, "words"
    return None, None, how


def occurrences(text, found):
    """Every offset at which the located string recurs verbatim, the first one included."""
    starts, i = [], text.find(found) if found else -1
    while i >= 0:
        starts.append(i)
        i = text.find(found, i + 1)
    return starts

# %% [markdown]
# ## Block 5: prompts
#
# Every prompt the notebook sends and the shape each reply must have. Nothing here knows what
# kind of document it is reading, and no prompt sees more than one unit.

# %%
# Block 5: the prompts. One triage per document (which kinds of unit to read), three per unit
# (entities with surface forms, salience and profile; facts with quotes; summary and cells),
# one judge over entity pairs, one fold, one adjudication per major, one support check over
# the facts left standing, one correction pass over the facts the check flagged. None of them
# knows what kind of document it is reading, and none sees another unit.

ENTITY_SCHEMA = {"type": "object", "required": ["entities"], "properties": {"entities": {"type": "array", "items": {
    "type": "object", "required": ["name", "named", "kind", "surface_forms"], "properties": {
        "name": {"type": "string"}, "named": {"type": "boolean"}, "kind": {"type": "string"},
        "surface_forms": {"type": "array", "items": {"type": "string"}},
        "salience": {"type": ["string", "null"]}, "profile": {"type": ["object", "null"]}}}}}}

FACT_SCHEMA = {"type": "object", "required": ["facts"], "properties": {"facts": {"type": "array", "items": {
    "type": "object", "required": ["subject", "predicate", "object", "quote"], "properties": {
        "subject": {"type": "string"}, "predicate": {"type": "string"}, "object": {"type": "string"},
        "qualifiers": {"type": ["string", "null"]}, "quote": {"type": "string"},
        "valid_from": {"type": ["string", "null"]}, "valid_to": {"type": ["string", "null"]}}}}}}

CELLS_SCHEMA = {"type": "object", "required": ["summary", "cells"], "properties": {
    "summary": {"type": "string"},
    "cells": {"type": "array", "items": {"type": "object", "required": ["entity", "text"], "properties": {
        "entity": {"type": "string"}, "text": {"type": "string"}}}}}}

JUDGE_SCHEMA = {"type": "object", "required": ["verdicts"], "properties": {"verdicts": {"type": "array", "items": {
    "type": "object", "required": ["pair", "verdict"], "properties": {
        "pair": {"type": ["integer", "string"]}, "verdict": {"type": "string", "enum": ["same", "different", "unsure"]},
        "reason": {"type": "string"}}}}}}

FOLD_SCHEMA = {"type": "object", "required": ["summary"], "properties": {"summary": {"type": "string"}}}
ENTITY_ABSTRACT_SCHEMA = {"type": "object", "required": ["summary", "kind"], "properties": {
    "summary": {"type": "string"}, "kind": {"type": "string"}}}

TRIAGE_SCHEMA = {"type": "object", "required": ["exclude"], "properties": {"exclude": {"type": "array", "items": {
    "type": "object", "required": ["kind", "reason"], "properties": {"kind": {"type": "string"}, "reason": {"type": "string"}}}}}}

# only the shape the reply must have. Each item is judged on its own below, so one malformed
# entry costs one fact instead of voiding the batch and dumping every fact in it (fixed 09-08).
SUPPORT_SCHEMA = {"type": "object", "required": ["unsupported"], "properties": {"unsupported": {"type": "array"}}}
CORRECT_SCHEMA = {"type": "object", "required": ["corrections"], "properties": {"corrections": {"type": "array"}}}
ADJUDICATE_SCHEMA = {"type": "object", "required": ["facts", "attributes", "contradictions"], "properties": {
    "unsupported": {"type": "array"},
    "facts": {"type": "array", "items": {"type": "object", "required": ["predicate", "object", "from"], "properties": {
        "predicate": {"type": "string"}, "object": {"type": "string"}, "qualifiers": {"type": ["string", "null"]}, "from": {"type": "array"}}}},
    "attributes": {"type": "array", "items": {"type": "object", "required": ["attribute", "value", "from"], "properties": {
        "attribute": {"type": "string"}, "value": {"type": ["string", "null"]}, "from": {"type": "array"}}}},
    "contradictions": {"type": "array", "items": {"type": "object", "required": ["note", "from"], "properties": {
        "note": {"type": "string"}, "from": {"type": "array"},
        "holds": {"type": ["integer", "string", "null"]}, "because": {"type": ["string", "null"]}}}}}}

QUOTE_RULE = ("a passage states a fact when it carries the claim itself, in whatever words the document uses:"
              " it need not repeat the fact's wording, the subject may be a pronoun or a shorter form, and a table row,"
              " a heading or a caption states what it lists")


def triage_prompt(doc, kinds):
    """kinds: {kind: [(position, label, words, first line), ...]} for every unit."""
    lines = []
    for kind, units in kinds.items():
        lines.append(f"KIND {kind}: {len(units)} unit(s)")
        for position, label, words, first in units:
            lines.append(f"  unit {position} ({label[:40]}, {words:,} words): {first}")
        lines.append("")
    return f"""We are building the record of a work: the entities it is about and the facts it states about them, read from its text one unit at a time. Text that is not the work itself, such as publishing boilerplate, a license, a dedication, a table of contents, a reference list, an index, or an appendix of apparatus, would only pollute that record and should not be read at all.

THE DOCUMENT: {doc.get('title') or doc['source_uri']}, by {doc.get('author') or 'an unknown author'}; source class {doc.get('source_class')}; dated {doc.get('occurred_at') or 'unknown'}; {len(doc['units'])} units in all.

Its units, grouped by the kind the splitter gave them, each with its first line:

{chr(10).join(lines)}
Which kinds, if any, should be left out entirely? A kind is left out whole, so keep a kind in when any of its units is part of the work (an abstract, or an introduction by the author, for instance). Return JSON {{"exclude": [{{"kind", "reason"}}]}}; an empty list means read everything."""


def entity_prompt(unit):
    return f"""TEXT ({unit['label']}):
{unit['text']}

Above is one unit of a longer document. Identify the entities it involves: each person, group, place, thing, event, or topic that acts, is acted upon, or is discussed in its own right, plus any named person, place, group, or thing, however briefly mentioned. Parts, components, and possessions of a listed entity are not entities; they belong inside that entity's facts.

Return JSON {{"entities": [{{"name", "named", "kind", "salience", "surface_forms", "profile"}}]}} where:
- name: for a named entity, the fullest name the text uses; for an unnamed one, a head word plus a parenthetical anchoring it to a named entity, like "car (Sam's car)"
- named: true if the text gives it a proper name
- kind: determine the kind classification of this entity, as one lowercase word; examples of kind include but are not limited to person, group, place, object, topic, event
- salience: "major" only if it would appear in a two-sentence summary of this text, else "minor"
- surface_forms: every distinct verbatim string the text uses to refer to it, copied exactly, bare pronouns excluded; a string that refers to two different entities in this text is listed under only one of them
- profile: attributes you infer from context rather than read in the text, as {{"gender", "age_band", "animacy", "role"}} with a value or null each; null when nothing can be inferred"""


def fact_prompt(unit, names, majors):
    return f"""TEXT ({unit['label']}):
{unit['text']}

Above is one unit of a longer document; below, the entities identified in it. For each entity, distill every durable fact the text states about it: what it is, its attributes, its states, its situation, its parts and possessions, its relationships to the other listed entities. Not moment-to-moment actions or passing remarks; a lasting disposition, habit, or position counts.

Return JSON {{"facts": [{{"subject", "predicate", "object", "qualifiers", "quote", "valid_from", "valid_to"}}]}} where:
- subject: a name from ENTITIES, exactly as written
- predicate: a lowercase_snake_case relation in the present tense, named the way the text gives it; use is_a for what kind of thing the subject is
- object: another entity's name exactly as written when the fact relates two entities, else a short literal value that does not repeat the predicate; never a bare true or false
- qualifiers: one short phrase for role, manner or condition, as a string, else null; never an object
- quote: one verbatim substring of the text that STATES the fact, copied exactly as it appears, punctuation and all; an ellipsis (...) may skip words between two verbatim pieces. {QUOTE_RULE}. Quote enough to carry the claim: for a table value, quote the heading it sits under as well as the value
- valid_from, valid_to: an ISO date (YYYY, YYYY-MM or YYYY-MM-DD) only when the quote itself states when the fact began or ended; otherwise null. Never infer a date.
- each fact is atomic: one attribute or one relationship, with a bare value rather than a phrase
- a relationship between a major entity and a minor one is stated once, under the major entity; only between two major entities may it be stated from both sides

ENTITIES: {", ".join(names)}
MAJOR: {", ".join(majors)}"""


def cells_prompt(unit, names):
    return f"""TEXT ({unit['label']}):
{unit['text']}

Above is one unit of a longer document. Write:
1. "summary": the unit in 3-5 concrete sentences, naming who and what it concerns.
2. "cells": for each entity below, 1-3 sentences in third person on what it does, what happens to it, or what is learned about it in this unit, written so it can be appended to that entity's running record.
Use only what the text says. Use no name that does not appear in the text.

Return JSON {{"summary": "...", "cells": [{{"entity", "text"}}]}}

ENTITIES: {", ".join(names)}"""


JUDGE_PROMPT = """Each PAIR below names two entity clusters built from different units of one document by their numbers in the DOSSIERS list. Decide for each pair whether the two describe the SAME individual thing. Weigh all the evidence: shared names and forms, what each is said to be, its facts, and above all who and what it relates to; a fact stating that one is the other is near-decisive. Kind labels are per-unit guesses and often differ for the same individual, so never decide on them alone. Answer unsure only when the evidence genuinely cannot settle it.

Return JSON {"verdicts": [{"pair": n, "verdict": "same" | "different" | "unsure", "reason": "one sentence"}]}
"""


def fold_prompt(what, children, limit):
    return f"""Below are the records of {what}, in reading order. Write one summary of the whole in at most {limit} words: what it is, who and what matter most, and how it unfolds from beginning to end. Ground every statement only in these records; use no outside knowledge and no name that does not appear below.

Return JSON {{"summary": "..."}}

RECORDS:
{chr(10).join(children)}"""


def entity_abstract_prompt(name, kinds, children, limit):
    """The entity's own abstract, and the one kind its merged instances settle on. The units were
    read apart and can name a kind differently; the document decides once, here."""
    return f"""Below are the records of one entity, {name}, in reading order. Reading the units one
at a time, we called it {', '.join(kinds)}.

Write one summary of the whole in at most {limit} words: what it is, what matters most about it, and
how it unfolds from beginning to end. Ground every statement only in these records; use no outside
knowledge and no name that does not appear below.

Then determine the kind classification of this entity, as one lowercase word; examples of kind
include but are not limited to person, group, place, object, topic, event.

Return JSON {{"summary": "...", "kind": "..."}}

RECORDS:
{chr(10).join(children)}"""


def adjudicate_prompt(name, kinds, facts, cells):
    return f"""Below is everything one document says about one entity, {name} ({', '.join(kinds)}): its facts, numbered, each with the unit it came from and the words it rests on, then its narrative cells in reading order. The units were read one at a time, so the facts repeat, overlap and sometimes disagree, and some are stated from the side of a lesser thing (marked inverse: the entity is the object of that statement). A line marked (about X) is what the document says of a lesser thing X that another line ties to the entity; it is not a fact of the entity itself: fold it into the object or qualifiers of the fact or attribute that names X, so that what the document says of X qualifies the entity's own statement, and point "from" at it as well.

Write the entity's consolidated record:
- "facts": each durable relationship or fact stated once, with "predicate" (lowercase_snake_case, present tense, as the listed facts name it), "object" (a string), "qualifiers" (one short phrase for role, manner or condition, as a string, else null; never an object), and "from": the numbers of every listed fact it is drawn from. A fact drawn from nothing listed is not allowed.
- "attributes": what the entity is, has or is like, as "attribute", "value" (or null when the attribute stands on its own) and "from", folding the lesser things named in the facts into the entity itself: a house that has a cellar has the attribute cellar, not a relationship to one.
- "contradictions": where listed facts disagree, a one-sentence "note" and the "from" numbers. This document is a snapshot with an end state, so say which of them holds at the END of it: "holds", the number of that one fact, and "because", one sentence saying how you know. Use null for "holds" when the document genuinely does not settle it. Both facts are kept either way; you are dating them, not deleting one.
- "unsupported": the numbers of listed facts whose own passage does not state them (a loose citation that says something else, or only part of it); draw on none of these.

Return JSON {{"facts": [...], "attributes": [...], "contradictions": [...], "unsupported": [...]}}

FACTS:
{chr(10).join(facts)}

CELLS:
{chr(10).join(cells) or '(none)'}"""


def support_prompt(facts):
    return f"""Below are statements one document makes, numbered, each with the passage it rests on.

Return JSON {{"unsupported": [numbers]}}: the numbers of the facts whose own passage does not state them (a loose citation that says something else, or only part of it).

{QUOTE_RULE}. A bare value is the usual near miss: a number quoted without the heading or label that names what it measures carries the figure but not the claim, and does not state it. Only call a fact unsupported when its passage genuinely does not carry the claim. Return an empty list when every passage states its fact.

FACTS:
{chr(10).join(facts)}"""


def correct_prompt(facts):
    return f"""Below are statements one document makes, numbered, each with the passage it rests on. An earlier and cheaper check suspected the passage does not state the statement. That check is often wrong, and this is the second look: decide each one on the passage in front of you.

{QUOTE_RULE}.

Answer for EVERY statement, with a "verdict":
- "stands": the passage does state the statement as written. This is the right answer whenever the claim is there, even if the passage says it in other words or says more besides.
- "corrected": the passage states something about the same subject, but not this. Give the "predicate" (lowercase_snake_case, present tense) and "object" it does state, with "qualifiers" or null. Keep the subject.
- "drop": the passage says nothing durable about that subject at all.

Return JSON {{"corrections": [{{"number", "verdict", "predicate", "object", "qualifiers"}}]}}, where "number" is the number of the statement you are answering, as it is printed below.

STATEMENTS:
{chr(10).join(facts)}"""

# %% [markdown]
# ## Block 6: one unit
#
# `derive_unit(doc, unit)`: three calls (entities, facts, cells) with every gate applied by code.
# An entity is kept only if a surface form is found; a fact only if its quote is located, and it
# is cut into one fact per voice if the quote crosses a change of speaker. Returns one record
# holding what was kept and what was rejected, with the reason.

# %%
# Block 6: derive one unit. Three calls, every gate applied by code, and one record back with
# everything the model said and everything code kept or rejected. Offsets are document
# offsets: the unit's start is added to every span. A span is one mention: when two entities
# claim the same occurrence, the first one listed keeps it. Nothing from another unit is seen.
#
# Ids are readable and local to the document: a fact is `<doc tag>:u<unit position>:f<n>`, its
# number counting the facts kept in that unit.


def doc_tag(doc):
    """The short form of the extractor's document id that prefixes every id this notebook mints."""
    return doc["doc_id"][:8]


def fact_line(f):
    """One fact as 'subject predicate object [qualifiers]'."""
    return f"{f['subject']} {f['predicate']} {f['object']}" + (f" [{f['qualifiers']}]" if f["qualifiers"] else "")


def quoted(f):
    """A fact's quote on one line, in the quotation marks the prompts print it in."""
    return f"(\"{' '.join(f['quote'].split())}\")"


def author_at(doc, offset):
    """The voice of an offset: the author of the piece holding it, else the document's."""
    for p in doc["pieces"]:
        if p["start"] <= offset < p["end"]:
            return p["author"] or doc.get("author")
    return doc.get("author")


def voice_spans(doc, base, text, start, end):
    """A quote may not span a change of speaker (decision 46): the located span cut where the
    speaker changes, each cut trimmed of whitespace, as offsets into the unit. A boundary
    between two pieces of one author is not a change of speaker and is not a cut."""
    pieces = sorted(doc["pieces"], key=lambda p: p["start"])
    cuts = [start]
    for before, after in zip(pieces, pieces[1:]):
        at = after["start"] - base
        if start < at < end and before.get("author") != after.get("author"):
            cuts.append(at)
    cuts.append(end)
    spans = []
    for s0, e0 in zip(cuts, cuts[1:]):
        while s0 < e0 and text[s0].isspace():
            s0 += 1
        while e0 > s0 and text[e0 - 1].isspace():
            e0 -= 1
        if e0 > s0:
            spans.append((s0, e0))
    return spans


def stated_date(value, quote):
    """An ISO date the model claims the quote states, kept only when its year is in the quote."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    for shape in ("%Y", "%Y-%m", "%Y-%m-%d"):
        try:
            datetime.strptime(value, shape)
            return value if value[:4] in quote else None
        except ValueError:
            pass
    return None


def listed_names(names):
    """{loose form: listed name} for every name whose loose form is its own, so "the Scarecrow"
    finds "The Scarecrow" but a form two names share finds nothing."""
    loose = tally(loose_name(n) for n in names)
    return {loose_name(n): n for n in names if loose[loose_name(n)] == 1}


def derive_unit(doc, unit, ctx, light=False):
    text, base, cache, tag = unit["text"], unit["start"], {}, doc_tag(doc)
    rec = {"unit_id": unit["unit_id"], "position": unit["position"], "label": unit["label"], "kind": unit["kind"],
           "entities": [], "dropped_entities": [], "facts": [], "rejected_facts": [], "profile": [],
           "summary": None, "cells": [], "empty": False}

    # 1. entities, each surface form located; a form that is not in the unit is dropped
    reply = generate(entity_prompt(unit), ENTITY_SCHEMA, "entities", ctx=ctx)
    claimed = set()                               # every (start, end) an earlier entity got
    for e in (reply or {}).get("entities", []):
        name = " ".join(e["name"].split())
        if not name or name in {x["name"] for x in rec["entities"]}:
            continue
        forms, spans, found_any = [], [], False
        for surface in dict.fromkeys([s for s in e["surface_forms"] if isinstance(s, str)] + [name]):
            hits = surface_spans(text, surface, cache)
            found_any = found_any or bool(hits)
            free = [span for span in hits if span not in claimed and span not in spans]
            if free:
                forms.append(surface)
                spans.extend(free)
        if not spans:
            rec["dropped_entities"].append({"name": name, "category": "span_claimed" if found_any else "no_surface_form",
                                            "why": "every span already claimed by an earlier entity" if found_any else "no surface form in unit",
                                            "forms": e["surface_forms"][:5]})
            continue
        claimed.update(spans)
        rec["entities"].append({"name": name, "named": bool(e["named"]), "kind": str(e["kind"]).lower(),
                                "major": str(e.get("salience") or "").strip().casefold() == "major", "forms": forms, "mentions": len(spans)})
        profile = e.get("profile") if isinstance(e.get("profile"), dict) else {}
        for attribute, value in profile.items():
            if value not in (None, "", "null", "unknown"):
                rec["profile"].append({"entity": name, "attribute": str(attribute), "value": str(value), "from_unit": unit["unit_id"]})
    names = [e["name"] for e in rec["entities"]]
    if not names:
        rec["empty"] = True
        return rec
    majors = [e["name"] for e in rec["entities"] if e["major"]]
    listed = listed_names(names)

    # 2. facts, each quote located inside the unit; a subject or object written loosely (case, a
    #    leading article) is the listed entity. Facts and cells take only the entity list, so on
    #    the one-reading path they are asked together; a many-unit document already runs its
    #    units WORKERS at a time
    ask_facts = lambda: generate(fact_prompt(unit, names, majors), FACT_SCHEMA, "facts", ctx=ctx)
    ask_cells = lambda: generate(cells_prompt(unit, majors), CELLS_SCHEMA, "cells", ctx=ctx)
    reply, cells_reply = in_parallel(lambda ask: ask(), [ask_facts, ask_cells]) if light else (ask_facts(), None)
    seen = set()
    for f in (reply or {}).get("facts", []):
        written = str(f["subject"]).strip()
        subject = written if written in names else listed.get(loose_name(written))
        predicate = snake_case(f["predicate"]) or "related_to"
        obj = str(f["object"]).strip()
        if obj not in names and any(ch.isupper() for ch in obj):
            obj = listed.get(loose_name(obj), obj)
        rejection = {"subject": written, "predicate": predicate, "object": obj, "quote": f["quote"][:160]}
        start, end, how = locate(text, f["quote"], cache)
        if subject is None:
            rejection["category"] = "ambiguous_subject" if loose_name(written) in {loose_name(n) for n in names} else "unlisted_subject"
        elif norm(obj) == norm(subject):      # "Table 19 reports Table 19": the object says nothing
            rejection["category"] = "self_reference"
        elif start is None:
            rejection["category"] = how
        else:
            stored = 0                                   # one fact per voice the span covers
            for s0, e0 in voice_spans(doc, base, text, start, end):
                quote, author = text[s0:e0], author_at(doc, base + s0)
                if (subject, predicate, norm(obj), author) in seen:
                    continue
                seen.add((subject, predicate, norm(obj), author))
                voices = {author_at(doc, base + at) for at in occurrences(text, quote)}
                rec["facts"].append({"fact_id": f"{tag}:u{unit['position']}:f{len(rec['facts']) + 1}",
                                     "subject": subject, "predicate": predicate, "object": obj, "object_is_entity": obj in names,
                                     "qualifiers": f.get("qualifiers") or None, "unit_id": unit["unit_id"], "quote": quote,
                                     "quote_start": base + s0, "quote_end": base + e0, "matched_by": how,
                                     "valid_from": stated_date(f.get("valid_from"), quote), "valid_to": stated_date(f.get("valid_to"), quote),
                                     "author": None if len(voices) > 1 else author,    # the same words in two voices: no voice is claimed
                                     "voice_ambiguous": len(voices) > 1, "tier": LUNA})
                stored += 1
            if stored:
                continue
            rejection["category"] = "duplicate"
        rec["rejected_facts"].append(rejection)

    # 3. summary and cells, one call, for the unit's major entities (the model's salience call)
    reply = cells_reply if light else ask_cells()
    if reply:
        rec["summary"] = " ".join(reply["summary"].split())
        for c in reply["cells"]:
            written = str(c["entity"]).strip()
            entity = written if written in majors else listed.get(loose_name(written))
            if entity in majors and c["text"].strip():
                rec["cells"].append({"entity": entity, "text": " ".join(c["text"].split())})
    rec["empty"] = not rec["facts"] and not rec["cells"]
    return rec

# %% [markdown]
# ## Block 7: reconcile
#
# `reconcile(records)` turns the unit-local entities into document entities. Locals with the same
# proper name and kind unite without a call. Other pairs are nominated by a shared surface form,
# a shared name word, or a fact saying one is the other, scored, and paired off round by round,
# strongest first, one pair to an entity; the judge takes ten pairs a call. Every decision is a
# ledger row with its evidence, and every scored pair is a candidate row.

# %%
# Block 7: reconcile the document's unit-local entities into document entities, bottom up, at
# the end.
#
# Every local starts alone. Two named locals with the same name and kind are one entity with
# no judge (an instant match needs both sides named). Every other pair nominated by a shared
# surface form, a fact stating one is the other, or a shared name word, with at least one
# unit-major in it (never minor against minor) and never a possession against its own anchor,
# goes into a priority queue, strongest first: the nomination's tier, then the name,
# co-occurrence and profile scores. Round by round the entities in consideration are paired off,
# strongest first and one pair to an entity; the judge takes ten pairs a call,
# every cluster's dossier sent once; same unites, different stays apart, unsure waits for one
# last look against the finished clusters, where unsure means apart. Every decision is a
# ledger row with its evidence.
import difflib

TIER = {"shared_surface": 1.0, "is_a_link": 0.85, "shared_word": 0.5}
PAIRS_PER_CALL = 10
SIMILAR_ENOUGH = 0.35                              # below this a pair is not worth a judge


def fact_text(f):
    return f"{f['predicate']} {f['object']}" + (f" [{f['qualifiers']}]" if f["qualifiers"] else "")


def locals_of(records):
    """One record per entity per unit, with what the unit said about it."""
    out = []
    for rec in records:
        facts_of, profile_of = {}, {}
        for f in rec["facts"]:
            facts_of.setdefault(f["subject"], []).append(f)
        for p in rec["profile"]:
            profile_of.setdefault(p["entity"], {})[p["attribute"]] = p["value"].casefold()
        names_here = {e["name"] for e in rec["entities"]}
        for e in rec["entities"]:
            facts = facts_of.get(e["name"], [])
            out.append({"id": len(out), "ui": rec["position"], "unit_id": rec["unit_id"], "name": e["name"], "kind": e["kind"],
                        "named": e["named"], "major": e["major"], "forms": list(dict.fromkeys(e["forms"] + [e["name"]])),
                        "surfaces": {s.casefold() for s in e["forms"]} | {e["name"].casefold()},
                        "is_a": [f["object"] for f in facts if f["predicate"] == "is_a"], "facts": [fact_text(f) for f in facts],
                        "relations": [f"{f['predicate']} {f['object']}" for f in facts if f["object_is_entity"]],
                        "profile": profile_of.get(e["name"], {}), "cooc": names_here - {e["name"]}, "n_facts": len(facts)})
    return out


def anchored(x, y):
    """x is an unnamed thing anchored to y by its parenthetical ("car (Sam's car)" and "Sam"):
    not candidates for being the same thing."""
    name = x["name"]
    if not y["named"] or not name.endswith(")") or "(" not in name:
        return False
    head, inner = name[:-1].rsplit("(", 1)
    if norm(y["name"]) not in inner.casefold():
        return False
    return not (name_words(head) & name_words(y["name"])) and not (x["surfaces"] & y["surfaces"])


def candidate_reason(a, b):
    """Why two locals might be the same thing, or None."""
    if a["surfaces"] & b["surfaces"]:
        return "shared_surface"
    if name_words(a["name"]) & name_words(b["name"]):
        return "shared_word"
    if any(x.casefold() in b["surfaces"] for x in a["is_a"]) or any(x.casefold() in a["surfaces"] for x in b["is_a"]):
        return "is_a_link"
    return None


def score_pair(a, b, reason):
    """(name, co-occurrence, profile, combined): the queue's order within a tier."""
    name = 1.0 if reason == "shared_surface" else difflib.SequenceMatcher(None, norm(a["name"]), norm(b["name"])).ratio()
    both = a["cooc"] | b["cooc"]
    cooc = len(a["cooc"] & b["cooc"]) / len(both) if both else 0.0
    shared_keys = set(a["profile"]) & set(b["profile"])
    profile = sum(a["profile"][k] == b["profile"][k] for k in shared_keys) / len(shared_keys) if shared_keys else 0.5
    return name, cooc, profile, 0.6 * name + 0.25 * cooc + 0.15 * profile


class Clusters:
    """Union-find over ids: every id starts alone, unite joins two groups, find gives the root."""

    def __init__(self, count):
        self.parent = list(range(count))

    def find(self, i):
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def unite(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

    def members(self, locals_):
        """{root: its locals}."""
        groups = {}
        for l in locals_:
            groups.setdefault(self.find(l["id"]), []).append(l)
        return groups


def ledger_row(locals_, a, b, verdict, how, evidence):
    return {"a": locals_[a]["name"], "a_unit": locals_[a]["ui"], "b": locals_[b]["name"], "b_unit": locals_[b]["ui"],
            "verdict": verdict, "how": how, "evidence": evidence}


def ineligible(members, ra, rb, ruled_apart):
    """Two clusters are never paired when they hold a local from one unit (that unit already
    listed them as two things) or a pair the judge ruled different (decisions 44 and 51)."""
    here, there = members.get(ra, []), members.get(rb, [])
    if {x["ui"] for x in here} & {y["ui"] for y in there}:
        return True
    return any(frozenset((x["id"], y["id"])) in ruled_apart for x in here for y in there)


def pair_up(locals_, clusters, ruled_apart, seen_pairs):
    """One round of the clustering: every entity still in consideration is scored against every
    other, the pairs at or above SIMILAR_ENOUGH are filtered by eligibility, and the strongest is
    taken with both its sides leaving consideration, until no eligible pair remains. A pair
    already judged and not merged is not a candidate, so its slot goes to the next-best one.
    (the pairs taken as (tier, combined, i, j, reason, scores), how many were eligible)."""
    members, scored = clusters.members(locals_), []
    for a in locals_:
        for b in locals_[:a["id"]]:
            ra, rb = clusters.find(a["id"]), clusters.find(b["id"])
            if ra == rb or not (a["major"] or b["major"]) or frozenset((ra, rb)) in seen_pairs:
                continue
            reason = candidate_reason(a, b)
            if reason is None or anchored(a, b) or anchored(b, a):
                continue
            scores = score_pair(a, b, reason)
            if scores[3] < SIMILAR_ENOUGH or ineligible(members, ra, rb, ruled_apart):
                continue
            scored.append((TIER[reason], scores[3], b["id"], a["id"], reason, scores))
    scored.sort(key=lambda entry: (-entry[0], -entry[1]))
    taken, queue = set(), []
    for entry in scored:
        ra, rb = clusters.find(entry[2]), clusters.find(entry[3])
        if ra not in taken and rb not in taken:        # both sides leave consideration for this round
            taken.update((ra, rb))
            queue.append(entry)
    return queue, len(scored)


def dossier(members):
    """What a cluster is, for the judge."""
    return "\n".join([
        f"names: {', '.join(sorted({l['name'] for l in members}))}",
        f"forms: {', '.join(sorted({s for l in members for s in l['surfaces']})[:12])}",
        f"kinds: {', '.join(sorted({l['kind'] for l in members}))}",
        f"is: {', '.join(sorted({x for l in members for x in l['is_a']})[:6]) or '(nothing stated)'}",
        f"facts: {'; '.join(sorted({x for l in members for x in l['facts']})[:10]) or '(none)'}",
        f"relations: {'; '.join(sorted({x for l in members for x in l['relations']})[:10]) or '(none)'}",
        f"with: {', '.join(sorted({n for l in members for n in l['cooc']})[:10]) or '(nothing)'}",
        f"units: {', '.join(str(u) for u in sorted({l['ui'] for l in members}))}"])


def judge(batch, locals_, clusters, ctx):
    """One Terra call over up to PAIRS_PER_CALL pairs of cluster roots, every dossier sent once;
    ({pair number: (verdict, reason)} in batch order, how many numbers were out of range)."""
    roots = sorted({r for pair in batch for r in pair})
    number = {r: n for n, r in enumerate(roots, 1)}
    members = clusters.members(locals_)
    dossiers = "\n\n".join(f"[{number[r]}]\n{dossier(members[r])}" for r in roots)
    pairs = "\n".join(f"PAIR {n}: [{number[a]}] and [{number[b]}]" for n, (a, b) in enumerate(batch, 1))
    reply = generate(JUDGE_PROMPT + "\nDOSSIERS\n" + dossiers + "\n\nPAIRS\n" + pairs, JUDGE_SCHEMA, "judge", model=TERRA, effort="medium", ctx=ctx)
    verdicts, misnumbered = {}, 0
    for v in (reply or {}).get("verdicts", []):
        numbered = valid_numbers([v.get("pair")], len(batch))
        if numbered:
            verdicts[numbered[0] - 1] = (v["verdict"], v.get("reason", ""))
        else:
            misnumbered += 1
    return verdicts, misnumbered


def valid_numbers(numbers, n):
    """The numbers a reply points at, as distinct integers within 1..n."""
    good = []
    for x in numbers if isinstance(numbers, list) else []:
        if isinstance(x, str) and x.strip().isdigit():
            x = int(x)
        if isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= n and x not in good:
            good.append(x)
    return good


def reconcile(records, ctx, watch=False):
    """The document's entities from its unit-locals: (entities, ledger, candidates, stats)."""
    locals_ = locals_of(records)
    clusters = Clusters(len(locals_))
    ledger, candidates, ruled_apart = [], [], set()

    # 1. the same proper name and kind, nothing in their is_a conflicting: one entity, no judge
    first_named = {}
    for l in locals_:
        if not l["named"]:
            continue
        first = first_named.setdefault((norm(l["name"]), l["kind"]), l)
        if first is l:
            continue
        if first["is_a"] and l["is_a"] and not set(first["is_a"]) & set(l["is_a"]):
            ledger.append(ledger_row(locals_, first["id"], l["id"], "unsure", "same_name_conflicting_is_a",
                                     f"both named {l['name']!r} but {first['is_a'][:2]} against {l['is_a'][:2]}: the judge decides"))
        else:
            clusters.unite(first["id"], l["id"])
            ledger.append(ledger_row(locals_, first["id"], l["id"], "same", "same_name", f"both named {l['name']!r}, both {l['kind']}"))

    # 2. the judge over a batch: same unites, different stays apart, unsure waits for the last
    #    look. The "different" verdicts are applied first, so the batch is order-independent: a
    #    "different" is a constraint and a "same" is a merge, and in batch order two earlier
    #    "same" verdicts could unite the two sides a later "different" ruled apart.
    apart, deferred = [], []
    stats = {"locals": len(locals_), "candidate_pairs": 0, "judged_pairs": 0, "judge_calls": 0, "judge_rounds": 0, "judge_misnumbered": 0}

    def decide(batch, final):
        verdicts, misnumbered = judge(batch, locals_, clusters, ctx)
        stats["judge_calls"] += 1
        stats["judged_pairs"] += len(batch)
        stats["judge_misnumbered"] += misnumbered
        rank = {"different": 0, "same": 1, "unsure": 2}
        answered = [(n, ra, rb, *verdicts.get(n, ("unsure", "no verdict returned"))) for n, (ra, rb) in enumerate(batch)]
        for n, ra, rb, verdict, reason in sorted(answered, key=lambda a: (rank.get(a[3], 2), a[0])):
            how = "judged again" if final else "judged"
            if verdict == "same" and ineligible(clusters.members(locals_), clusters.find(ra), clusters.find(rb), ruled_apart):
                # a guard the pairing rules should make unreachable: one pair to an entity a round
                how, reason = "refused", reason + "; would join locals a unit kept apart or the judge ruled different"
                apart.append((ra, rb))
                ruled_apart.add(frozenset((ra, rb)))
            elif verdict == "same":
                clusters.unite(ra, rb)
            elif verdict == "different" or final:
                apart.append((ra, rb))
                ruled_apart.add(frozenset((ra, rb)))
            else:
                deferred.append((ra, rb))
            ledger.append(ledger_row(locals_, ra, rb, verdict, how, reason))

    def judge_all(pairs, final):
        k = 0
        while k < len(pairs):
            settled = {frozenset((clusters.find(x), clusters.find(y))) for x, y in apart + deferred}
            batch, keys = [], set()
            while k < len(pairs) and len(batch) < PAIRS_PER_CALL:
                ra, rb = clusters.find(pairs[k][0]), clusters.find(pairs[k][1])
                k += 1
                key = frozenset((ra, rb))
                if ra != rb and key not in keys and key not in settled:
                    batch.append((ra, rb))
                    keys.add(key)
            if batch:
                decide(batch, final)
                if watch and stats["judge_calls"] % 5 == 0:
                    print(f"    judge call {stats['judge_calls']}: {k} of {len(pairs)} pairs seen, ${spend()[0]:.2f} spent this session")

    # 3. round after round, each pairing off the entities still in consideration; the merges of
    #    one round cannot conflict, since no entity is in two of its pairs. Stop when a round
    #    queues nothing, which is when nothing eligible is left above the threshold.
    seen_pairs = set()
    while True:
        queue, eligible = pair_up(locals_, clusters, ruled_apart, seen_pairs)
        if not queue:
            break
        stats["judge_rounds"] += 1
        stats["candidate_pairs"] += len(queue)
        fresh = []
        for tier, combined, i, j, reason, (name, cooc, profile, _) in queue:
            seen_pairs.add(frozenset((clusters.find(i), clusters.find(j))))
            fresh.append((i, j))
            candidates.append({"a": locals_[i]["name"], "a_unit": locals_[i]["ui"], "b": locals_[j]["name"], "b_unit": locals_[j]["ui"],
                               "round": stats["judge_rounds"], "tier": tier, "reason": reason, "name_score": round(name, 3),
                               "cooc_score": round(cooc, 3), "profile_score": round(profile, 3), "combined": round(combined, 3)})
        if watch:
            print(f"judge round {stats['judge_rounds']}: {eligible} eligible pairs, {len(fresh)} taken (one to an entity), {PAIRS_PER_CALL} a call")
        judge_all(fresh, final=False)

    # 4. the deferred pairs' last look against the finished clusters
    last_look, deferred = list(deferred), []
    judge_all(last_look, final=True)
    return cluster_entities(locals_, clusters), ledger, candidates, stats


def cluster_entities(locals_, clusters):
    """One document entity per cluster, numbered in order of first appearance: its canonical name
    (the most used proper name, the longest on a tie), its names, forms, units and facts, and
    where each form first appeared."""
    entities = []
    for index, members in enumerate(clusters.members(locals_).values()):
        named = [l for l in members if l["named"]] or members
        counts = tally(l["name"] for l in named)
        first_unit_of, unit_ids = {}, list(dict.fromkeys(l["unit_id"] for l in members))
        for l in members:
            for form in l["forms"]:
                first_unit_of.setdefault(form, l["unit_id"])
        kinds = tally(l["kind"] for l in members)
        entities.append({"index": index, "name": max(counts, key=lambda n: (counts[n], len(n))),
                         "kinds": sorted(kinds, key=lambda k: (-kinds[k], k)), "named": any(l["named"] for l in members),
                         "major": any(l["major"] for l in members),      # major in some unit: a major of the document (ruling of 09-07)
                         "units": sorted({l["ui"] for l in members}), "unit_ids": unit_ids,
                         "names": sorted({l["name"] for l in members}), "surfaces": sorted({s for l in members for s in l["surfaces"]}),
                         "first_unit_of": first_unit_of, "members": [(l["ui"], l["name"]) for l in members],
                         "n_facts": sum(l["n_facts"] for l in members), "is_a": sorted({x for l in members for x in l["is_a"]})})
    return entities

# %% [markdown]
# ## Block 8: fold, adjudicate, verify
#
# `fold_document` writes the abstract and each major's abstract. `adjudicate` consolidates the
# facts of each major with enough of them, and checks the facts of the rest against their
# passages in one call. `verify` gives every flagged fact a second look (stand, reword, drop)
# and checks what is kept once more.

# %%
# Block 8: fold the document, adjudicate its majors, and check the facts against their passages.
#
# The abstract is a summary of the unit summaries, asked for in at most half their words and
# no more than 400, and it stands as written (decision 65). Salience decides a major and
# nothing else does (ruling of 09-07): a unit called it major, so it is a major of the document.
# The one exception is a major with nothing to summarise, no facts and no cells, which falls to
# minor (decision 52). Majors get their own abstract.
#
# Adjudication is one Terra call per major with enough facts: the consolidated facts,
# attributes and contradictions, each pointing at the raw facts it is drawn from. A major with
# fewer than ADJUDICATE_MIN_FACTS facts, and every major of a one-reading document, keeps its
# raw facts as they are; those facts are read against their passages together, in one pass
# (ruling of 09-08). A fact that pass flags gets a second look: it stands, is reworded to what
# the passage does state, or is dropped; a rewording is checked once more before it is kept.
ADJUDICATE_MIN_FACTS = 4                      # fewer than this: nothing to consolidate
VERIFY_BATCH = 60                             # facts to a support or correction call


def one_reading(doc):
    """True when setting the boilerplate aside leaves a single unit to read. Such a document has
    nothing to merge, so it takes the short path (ruling of 09-07)."""
    return sum(1 for u in doc["units"] if u["kind"] not in BOILERPLATE) == 1


def summarise(what, children, ctx, stage="fold"):
    """(summary, the word limit it was asked for); the summary None when the model did not answer."""
    limit = min(400, max(20, sum(word_count(c) for c in children) // 2))
    reply = generate(fold_prompt(what, children, limit), FOLD_SCHEMA, stage, model=TERRA, ctx=ctx)
    return (" ".join(reply["summary"].split()) if reply else None), limit


def fold_document(records, entities, ctx, light=False):
    """The abstract, the majors and minors, each major's cells and its abstract."""
    out = {"abstract": None, "majors": [], "minors": [], "entity_abstracts": [], "demoted": [], "cells_of": {}}
    summarised = [r for r in records if r["summary"]]
    if len(summarised) == 1:                      # one summarised unit: its summary is the abstract, no call
        out["abstract"] = {"text": summarised[0]["summary"], "limit": None, "tier": LUNA}
    elif summarised:
        text, limit = summarise("one document", [f"[{r['label']}] {r['summary']}" for r in summarised], ctx)
        if text:
            out["abstract"] = {"text": text, "limit": limit, "tier": TERRA}

    # each major's cells and facts, by entity index (two clusters may share a name)
    member_of = {(ui, local_name): e["index"] for e in entities for ui, local_name in e["members"]}
    cells_of, facts_of = {}, {}
    for r in records:
        for c in r["cells"]:
            if (r["position"], c["entity"]) in member_of:
                cells_of.setdefault(member_of[(r["position"], c["entity"])], []).append(f"[{r['label']}] {c['text']}")
        for f in r["facts"]:
            if (r["position"], f["subject"]) in member_of:
                facts_of.setdefault(member_of[(r["position"], f["subject"])], []).append(fact_text(f))
    out["cells_of"] = cells_of
    for e in entities:
        e["children"] = list(dict.fromkeys(facts_of.get(e["index"], []))) + cells_of.get(e["index"], [])
        if e["major"] and not e["children"]:      # nothing to summarise: not a major (decision 52)
            e["major"] = False
            out["demoted"].append(e["name"])
        (out["majors"] if e["major"] else out["minors"]).append(e)

    def abstract_of(e):
        """(text, kind, tier). Two records or fewer stand as the abstract without a call; on the
        one-reading path the entity's own cell is its abstract, and an entity with only facts
        gets none, since a run of predicate strings is not a summary of anything (09-07)."""
        cells = cells_of.get(e["index"], [])
        if light:
            if not cells and len(e["children"]) > 2:
                return None, None, LUNA
            return " ".join(c.split("] ", 1)[-1] for c in cells or e["children"]) or None, None, LUNA
        if len(e["children"]) <= 2:
            return " ".join(c.split("] ", 1)[-1] for c in e["children"]), None, LUNA
        limit = min(400, max(20, sum(word_count(c) for c in e["children"]) // 2))
        reply = generate(entity_abstract_prompt(e["name"], e["kinds"], e["children"], limit),
                         ENTITY_ABSTRACT_SCHEMA, "entity_abstract", model=TERRA, ctx={**ctx, "entity": e["name"]})
        if not reply:
            return None, None, TERRA
        return " ".join(reply["summary"].split()), str(reply["kind"]).strip().lower() or None, TERRA

    for e, (text, kind, tier) in zip(out["majors"], in_parallel(abstract_of, out["majors"])):
        e["kind"] = kind or e["kinds"][0]     # one kind for the merged entity; the units' most common if no call
        if text:
            out["entity_abstracts"].append({"index": e["index"], "name": e["name"], "text": text, "tier": tier})
    return out


def landings(records, folded):
    """Where every kept fact lands: {major index: [(fact, direction, unit label)]}. A fact whose
    subject is a major lands forward; one that points AT a major lands under it as inverse, with
    the lesser thing's name as its value. A fact between two lesser things is not stored."""
    entity_of = {(ui, local_name): e["index"] for e in folded["majors"] + folded["minors"] for ui, local_name in e["members"]}
    landed = {e["index"]: [] for e in folded["majors"]}
    for r in records:
        for f in r["facts"]:
            subject = entity_of.get((r["position"], f["subject"]))
            obj = entity_of.get((r["position"], f["object"])) if f["object_is_entity"] else None
            if subject in landed:
                landed[subject].append((f, "forward", r["label"]))
            elif obj in landed:
                landed[obj].append((f, "inverse", r["label"]))
    return landed


def unsupported_of(facts, ctx, stage="support"):
    """(the ids of the facts whose own passage does not state them, whether any batch was
    refused, how many calls it took). `facts` are (fact, id) pairs; each is judged on its own
    terms, subject first, whichever major it landed under. A refusal is reported rather than
    read as a clean pass, because for the facts left standing this is the only check."""
    flagged, refused, calls = [], False, 0
    for at in range(0, len(facts), VERIFY_BATCH):
        batch = facts[at:at + VERIFY_BATCH]
        listing = [f"{n}. {fact_line(f)}  {quoted(f)}" for n, (f, fid) in enumerate(batch, 1)]
        reply = generate(support_prompt(listing), SUPPORT_SCHEMA, stage, ctx=ctx)
        calls += 1
        if reply is None:
            refused = True
            continue
        flagged += [batch[n - 1][1] for n in valid_numbers(reply.get("unsupported"), len(batch))]
    return flagged, refused, calls


def adjudicate(records, folded, ctx, watch=False, light=False):
    """{major index: its consolidated record}: facts, attributes and contradictions pointing at
    raw fact ids, the raw facts set aside as unsupported, and how the major was handled."""
    landed, cells_of = landings(records, folded), folded["cells_of"]
    out, standing, to_judge = {}, [], []
    for e in folded["majors"]:
        raws = landed[e["index"]]
        out[e["index"]] = {"facts": [], "attributes": [], "contradictions": [], "unsupported": [], "dropped": 0,
                           "raw": len(raws), "skipped": None, "rejected": False, "support_calls": 0}
        if light:
            out[e["index"]]["skipped"] = "one reading: the facts stand, verified in one pass"
            standing.append(e)
        elif not raws:
            continue
        elif len(raws) < ADJUDICATE_MIN_FACTS:
            out[e["index"]]["skipped"] = f"fewer than {ADJUDICATE_MIN_FACTS} facts: the raw facts stand, their support checked"
            standing.append(e)
        else:
            to_judge.append(e)

    def adjudicate_one(e):
        raws, result = landed[e["index"]], out[e["index"]]
        listing = []
        for n, (f, direction, label) in enumerate(raws, 1):
            head = f"{e['name']} {f['predicate']} {f['object']}" if direction == "forward" else f"(inverse) {f['subject']} {f['predicate']} {e['name']}"
            listing.append(f"{n}. {head}" + (f" [{f['qualifiers']}]" if f["qualifiers"] else "") + f"  ({label}: \"{' '.join(f['quote'].split())}\")")
        reply = generate(adjudicate_prompt(e["name"], e["kinds"], listing, cells_of.get(e["index"], [])), ADJUDICATE_SCHEMA, "adjudicate",
                         model=TERRA, effort="medium", ctx={**ctx, "entity": e["name"]})
        result["rejected"] = reply is None
        ids = [f["fact_id"] for f, direction, label in raws]
        result["unsupported"] = [ids[n - 1] for n in valid_numbers((reply or {}).get("unsupported"), len(ids))]
        aside = set(result["unsupported"])
        for key in ("facts", "attributes", "contradictions"):
            for item in (reply or {}).get(key, []):
                if key == "contradictions":                    # which of its own sources holds at the end (R4)
                    settles = valid_numbers([item.get("holds")], len(ids))
                    item["holds_fact"] = ids[settles[0] - 1] if settles else None
                # a consolidated item is redundant raw facts merged, so one supported source
                # carries it; the ones set aside come out of its sources (decision 45)
                sources = [ids[n - 1] for n in valid_numbers(item.get("from"), len(ids)) if ids[n - 1] not in aside]
                if not sources:
                    result["dropped"] += 1
                    continue
                result[key].append({**{k: v for k, v in item.items() if k != "from"}, "from_facts": sources})
        return result

    if to_judge:
        if watch:
            print(f"adjudicate: {len(to_judge)} majors, {WORKERS} at a time; {len(standing)} with fewer than {ADJUDICATE_MIN_FACTS} facts stand, checked together after")
        in_parallel(adjudicate_one, to_judge)

    # the facts left to stand are checked in ONE pass over the document. A call an entity was a
    # quarter of a paper's spending to ask the same question of four facts at a time (09-08).
    facts = [(f, f["fact_id"]) for e in standing for f, direction, label in landed[e["index"]]]
    if facts:
        if watch:
            print(f"support: {len(facts)} facts of {len(standing)} entities left to stand, one pass on {LUNA}")
        flagged, refused, calls = unsupported_of(facts, ctx)
        aside = set(flagged)
        for e in standing:
            out[e["index"]]["rejected"] = refused
            out[e["index"]]["unsupported"] = [f["fact_id"] for f, direction, label in landed[e["index"]] if f["fact_id"] in aside]
        out[standing[0]["index"]]["support_calls"] = calls          # the one pass, counted once
    return out


def flagged_facts(records, folded, adjudicated):
    """{fact id: the raw fact} for every fact a check set aside."""
    landed = landings(records, folded)
    by_id = {f["fact_id"]: f for e in folded["majors"] for f, direction, label in landed[e["index"]]}
    flagged = {x for result in adjudicated.values() for x in result["unsupported"]}
    return {fid: by_id[fid] for fid in flagged if fid in by_id}


def corrected_fact(f, item):
    """(the corrected statement, None) when the correction passes the checks a fact must still
    pass without the gate, else (None, why). It must say something, its object may restate
    neither its subject nor its predicate, it may not be a bare boolean, and it may not move the
    subject: the subject decided which node the fact landed on, and this runs after landing."""
    subject = str(item.get("subject") or f["subject"]).strip()
    predicate = snake_case(str(item.get("predicate") or "")) or f["predicate"]
    obj = str(item.get("object") or "").strip()
    if not obj:
        return None, "no object"
    if obj.casefold() in ("true", "false"):
        return None, "bare boolean"
    if norm(subject) != norm(f["subject"]):
        return None, "subject moved"
    said = norm(obj).replace("_", " ")            # the predicate written as words is still the predicate
    if said == norm(subject).replace("_", " ") or said == norm(predicate).replace("_", " "):
        return None, "object restates subject or predicate"
    return {"subject": subject, "predicate": predicate, "object": obj, "qualifiers": item.get("qualifiers") or None}, None


def statement_number(item, n):
    """The statement an answer is about, as a number in 1..n, or None. The model is asked for
    "number"; "fact" is what the field used to be called, and a value like "3." or "3)" is three."""
    for key in ("number", "fact", "n", "id"):
        if key not in item:
            continue
        value = item[key]
        if isinstance(value, str):
            value = re.match(r"\s*(\d*)", value).group(1)
        found = valid_numbers([value], n)
        if found:
            return found[0]
    return None


def corrections_of(flagged, ctx, watch=False):
    """({fact id: the corrected statement, or None to keep it as written}, calls, notes). The
    second look at what the support check flagged: a fact whose passage does state it stands
    unchanged, one whose passage states something else is rewritten to that, and one whose
    passage carries nothing is left out of the result and so dropped. A refused call is not
    evidence against a fact: its batch stands. A fact the reply leaves out is dropped."""
    items, out, calls, notes, told_to_drop = sorted(flagged.items()), {}, 0, {"offered": 0}, set()
    if watch and items:
        print(f"correct: {len(items)} facts their passage does not state, on {LUNA}")
    for at in range(0, len(items), VERIFY_BATCH):
        batch = items[at:at + VERIFY_BATCH]
        listing = [f"{n}. {fact_line(f)}  {quoted(f)}" for n, (fid, f) in enumerate(batch, 1)]
        reply = generate(correct_prompt(listing), CORRECT_SCHEMA, "correct", effort="medium", ctx=ctx)
        calls += 1
        if reply is None:
            notes["call refused"] = notes.get("call refused", 0) + len(batch)
            out.update({fid: None for fid, f in batch})
            continue
        for item in reply.get("corrections", []):
            if not isinstance(item, dict):
                continue
            notes["offered"] += 1
            numbered = statement_number(item, len(batch))
            if numbered is None:
                notes["misnumbered"] = notes.get("misnumbered", 0) + 1
                continue
            fid, f = batch[numbered - 1]
            verdict = str(item.get("verdict") or "").strip().lower()
            if verdict == "drop":
                told_to_drop.add(fid)
            elif verdict != "corrected":                    # "stands", or an answer that cannot be read: the fact stands
                out[fid] = None
                if verdict != "stands":
                    notes["no verdict"] = notes.get("no verdict", 0) + 1
            else:
                fixed, why = corrected_fact(f, item)
                if fixed is None:
                    notes[why] = notes.get(why, 0) + 1
                elif (fixed["predicate"], norm(fixed["object"])) == (f["predicate"], norm(f["object"])):
                    out[fid] = None                         # the same fact back again: it stands
                else:
                    out[fid] = fixed
    unanswered = [fid for fid, f in items if fid not in out and fid not in told_to_drop]
    if unanswered:
        notes["unanswered"] = len(unanswered)
        out.update({fid: None for fid in unanswered})      # no verdict reached it: the fact stands
    if watch:
        unchanged = sum(1 for v in out.values() if v is None)
        print(f"    {len(items)} flagged, {notes['offered']} answered: {unchanged} unchanged, {len(out) - unchanged} reworded,"
              f" {len(items) - len(out)} dropped outright; {notes}")
    return out, calls, notes


def verify(records, folded, adjudicated, ctx, watch=False):
    """The facts a check flagged, and what became of each: ({fact id: raw fact}, {fact id:
    correction or None to keep it as written}, calls, notes). A flagged fact missing from the
    corrections is dumped. Every fact the second look kept, as written or reworded, is checked
    against its passage once more before it is kept (ruling of 09-08); a refused check is not
    evidence against it."""
    flagged = flagged_facts(records, folded, adjudicated)
    if not flagged:
        return {}, {}, 0, {}
    corrections, calls, notes = corrections_of(flagged, ctx, watch=watch)
    if corrections:
        checked = [({**flagged[fid], **(fix or {})}, fid) for fid, fix in corrections.items()]
        failed, refused, more = unsupported_of(checked, ctx, stage="verify")
        calls += more
        if not refused:
            for fid in failed:
                corrections.pop(fid, None)
        notes["failed the second check"] = 0 if refused else len(failed)
        if watch:
            print(f"    {len(checked)} kept facts checked against their passages once more; {len(checked) - len(corrections)} dropped")
    if watch:
        print(f"    {len(corrections)} of {len(flagged)} stand or are corrected against their passage; {len(flagged) - len(corrections)} dumped")
    return flagged, corrections, calls, notes

# %% [markdown]
# ## Block 9: the package
#
# `write_package` lays out every record in order and ends with the completion record.
# `completed(doc)` says whether a finished package by this ingestor over these units already
# exists, so a rerun skips it.

# %%
# Block 9: the package. One JSONL file per document mirroring the raw layout, every line one
# record with a "record" field, ending in a completion record. Minors have no node. A fact
# lands on the major that is its subject (forward), or on the major a minor's fact points at
# (inverse); a fact of a minor tied to no major is not stored. Mentions are not written: they
# were 53% of the package and nothing read them (ruling of 09-08).
#
# Node ids are `<doc tag>:doc` for the document and `<doc tag>:n<index>` for a major, the index
# being the entity's number in reconcile's order; a cell has no id of its own.


def package_path(doc):
    """Every document keeps its own folder, named after its file: the package
    and the graph sit together, under the corpus the document came from."""
    parts = doc["source_uri"].split("/")
    stem = Path(parts[-1]).stem
    return OUT / (parts[-2] if len(parts) > 1 else "misc") / stem / (stem + ".jsonl")


def node_id(doc, entity):
    return f"{doc_tag(doc)}:n{entity['index']}"


def write_package(doc, records, entities, folded, adjudicated, ledger, candidates, excluded, stats, flagged, corrections):
    path = package_path(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    written_at, doc_node = datetime.now(timezone.utc).isoformat(timespec="seconds"), f"{doc_tag(doc)}:doc"
    lines = [{"record": "document", **{k: doc[k] for k in ("doc_id", "source_uri", "sha256", "title", "author", "source_class", "ingested_at", "occurred_at", "loader")},
              "flags": doc.get("flags", []), "text_length": len(doc["text"])}]
    lines += [{"record": "unit", **u} for u in doc["units"]] + [{"record": "piece", **p} for p in doc["pieces"]]
    lines.append({"record": "node", "node_id": doc_node, "name": doc.get("title") or doc["source_uri"], "kind": "document",
                  "created_from_unit": doc["units"][0]["unit_id"] if doc["units"] else None, "provenance": {"ingestor": INGESTOR}})

    # nodes, aliases and edges for the majors; the map from a unit-local name to its node
    node_of, position_of = {}, {u["unit_id"]: u["position"] for u in doc["units"]}
    for e in folded["majors"]:
        nid = node_id(doc, e)
        node_of.update({(ui, local_name): nid for ui, local_name in e["members"]})
        lines.append({"record": "node", "node_id": nid, "name": e["name"], "kind": e["kind"],
                      "created_from_unit": min(e["unit_ids"], key=position_of.get),
                      "provenance": {"ingestor": INGESTOR, "names": e["names"][:12]}})
        lines += [{"record": "alias", "alias": form, "node_id": nid, "first_seen_unit": uid} for form, uid in e["first_unit_of"].items()]
        lines.append({"record": "edge", "predicate": "appears_in", "subject": nid, "object": doc_node, "units": e["unit_ids"]})
    lines += [{"record": "edge", "predicate": "has_unit", "subject": doc_node, "object": u["unit_id"], "position": u["position"]} for u in doc["units"]]

    # per unit: profiles, the summary cell, the entity cells
    for r in records:
        seen_profile = set()
        for p in r["profile"]:
            nid = node_of.get((r["position"], p["entity"]))
            if nid and (nid, p["attribute"], p["value"]) not in seen_profile:
                seen_profile.add((nid, p["attribute"], p["value"]))
                lines.append({"record": "profile", "node_id": nid, "attribute": p["attribute"], "value": p["value"], "from_unit": p["from_unit"]})
        if r["summary"]:
            lines.append({"record": "cell", "node_id": doc_node, "unit_id": r["unit_id"], "text": r["summary"], "tier": LUNA,
                          "provenance": {"ingestor": INGESTOR, "kind": "unit_summary"}})
        cells_by_node = {}
        for c in r["cells"]:
            if node_of.get((r["position"], c["entity"])):
                cells_by_node.setdefault(node_of[(r["position"], c["entity"])], []).append(c)
        for nid, cells in cells_by_node.items():
            lines.append({"record": "cell", "node_id": nid, "unit_id": r["unit_id"], "text": " ".join(c["text"] for c in cells), "tier": LUNA,
                          "provenance": {"ingestor": INGESTOR, "entity_names": [c["entity"] for c in cells]}})

    # the adjudicated record of each major. An item may not cite a fact this package will not
    # carry, so the dumped facts come out of its sources first, and an item left with none goes
    dumped_ids = set(flagged) - set(corrections)
    for e in folded["majors"]:
        nid, result = node_id(doc, e), adjudicated[e["index"]]
        for item in result["facts"]:
            sources = [i for i in item["from_facts"] if i not in dumped_ids]
            if sources:
                lines.append({"record": "adjudicated_fact", "node_id": nid, "predicate": snake_case(item["predicate"]) or "related_to",
                              "object": item["object"], "qualifiers": item.get("qualifiers") or None, "from_facts": sources, "tier": TERRA})
        for item in result["attributes"]:
            sources = [i for i in item["from_facts"] if i not in dumped_ids]
            if sources:
                lines.append({"record": "attribute", "node_id": nid, "attribute": item["attribute"], "value": item["value"], "from_facts": sources, "tier": TERRA})
        for item in result["contradictions"]:
            # the document's own resolution, recorded here and not on the fact: both facts stay
            # active, and the global layer sees that this document said both things (R4, 09-07)
            sources = [i for i in item["from_facts"] if i not in dumped_ids]
            if len(sources) >= 2:
                holds = item.get("holds_fact") if item.get("holds_fact") in sources else None
                lines.append({"record": "contradiction", "node_id": nid, "note": item["note"], "from_facts": sources,
                              "holds": holds, "because": (item.get("because") or None) if holds else None})

    # the document level: abstracts, the ledger, the candidates
    if folded["abstract"]:
        lines.append({"record": "abstract", "node_id": doc_node, "text": folded["abstract"]["text"], "tier": folded["abstract"]["tier"], "updated_at": written_at})
    lines += [{"record": "abstract", "node_id": f"{doc_tag(doc)}:n{a['index']}", "text": a["text"], "tier": a["tier"], "updated_at": written_at}
              for a in folded["entity_abstracts"]]
    lines += [{"record": "ledger", **entry} for entry in ledger] + [{"record": "candidate", **entry} for entry in candidates]

    # facts, each under the major it lands on. A fact whose passage does not state it is written
    # only if it was corrected against that passage; otherwise it is dumped and recorded as a
    # rejection, never written with a flag (R3, ruling of 09-07)
    when_of = {u["unit_id"]: (u.get("occurred_at"), u.get("occurred_until")) for u in doc["units"]}
    landed, stored, dumped = landings(records, folded), 0, []
    for e in folded["majors"]:
        nid = node_id(doc, e)
        for f, direction, label in landed[e["index"]]:
            if f["fact_id"] in dumped_ids:
                dumped.append({"record": "rejection", "stage": "verify", "unit_id": f["unit_id"], "category": "unsupported",
                               "subject": f["subject"], "predicate": f["predicate"], "object": f["object"], "quote": f["quote"],
                               "why": "the passage does not state it and it could not be corrected"})
                continue
            stored += 1
            fix = corrections.get(f["fact_id"])
            object_node = node_of.get((position_of[f["unit_id"]], f["object"])) if f["object_is_entity"] else None
            # a correction may move the predicate, the qualifiers and the object, never the
            # subject; on an inverse landing the object slot holds the other entity's name
            if direction == "inverse":
                obj, is_node = f["subject"], False
            elif fix:
                obj, is_node = fix["object"], False
            else:
                obj, is_node = object_node or f["object"], object_node is not None
            when = when_of.get(f["unit_id"], (None, None))
            lines.append({"record": "fact", "fact_id": f["fact_id"], "subject": nid,
                          "predicate": fix["predicate"] if fix else f["predicate"], "object": obj, "object_is_node": is_node,
                          "direction": direction, "qualifiers": fix["qualifiers"] if fix else f["qualifiers"], "rank": "active",
                          "unit_id": f["unit_id"], "quote": f["quote"], "quote_start": f["quote_start"], "quote_end": f["quote_end"],
                          "valid_from": f["valid_from"], "valid_to": f["valid_to"],       # when it is true
                          "occurred_at": when[0], "occurred_until": when[1],                # when it was said (R2, 09-07)
                          "tier": f["tier"], "author": f["author"],
                          "provenance": {"ingestor": INGESTOR, "matched_by": f["matched_by"], "subject_name": f["subject"],
                                         "voice_ambiguous": f["voice_ambiguous"],
                                         "corrected_from": {k: f[k] for k in ("predicate", "object", "qualifiers")} if fix else None}})
    lines += dumped
    for r in records:
        lines += [{"record": "rejection", "stage": "facts", "unit_id": r["unit_id"], **x} for x in r["rejected_facts"]]
        lines += [{"record": "rejection", "stage": "entities", "unit_id": r["unit_id"], **x} for x in r["dropped_entities"]]

    kept = sum(len(r["facts"]) for r in records)
    written = tally(l["record"] for l in lines)
    counts = {"units": len(records), "entities": len(entities), "majors": len(folded["majors"]), "minors": len(folded["minors"]),
              "mentions": sum(e["mentions"] for r in records for e in r["entities"]),
              "facts_kept": kept, "facts_stored": stored, "facts_no_major": kept - stored - len(dumped),
              "facts_rejected": sum(len(r["rejected_facts"]) for r in records) + len(dumped),
              "cells": written.get("cell", 0), "empty_units": sum(r["empty"] for r in records), "units_excluded": len(excluded),
              "demoted": len(folded["demoted"]), "adjudicated_facts": written.get("adjudicated_fact", 0),
              "attributes": written.get("attribute", 0), "contradictions": written.get("contradiction", 0),
              "contradictions_resolved": sum(1 for l in lines if l["record"] == "contradiction" and l["holds"]),
              "adjudications_rejected": sum(1 for a in adjudicated.values() if a["rejected"]),
              "support_calls": sum(a["support_calls"] for a in adjudicated.values()),
              "facts_flagged": len(flagged), "facts_upheld": sum(1 for v in corrections.values() if v is None),
              "facts_corrected": sum(1 for v in corrections.values() if v is not None), "facts_dumped": len(dumped),
              "has_abstract": folded["abstract"] is not None}
    lines.append({"record": "completion", "doc_id": doc["doc_id"], "ingestor": INGESTOR, "counts": counts, "stats": stats,
                  "empty": stored == 0 and counts["cells"] == 0, "excluded": excluded, "demoted": folded["demoted"]})
    path.write_text("\n".join(json.dumps(l, ensure_ascii=False) for l in lines) + "\n", encoding="utf-8", newline="\n")
    return path, counts


def completed(doc):
    """Is there already a finished package for this document, over these units? The ingestor
    version is NOT part of the question: a package does not stop being finished because the code
    that wrote it moved on, and a corpus run over several days must not re-buy a day's work for a
    version bump (ruling of 09-08)."""
    path = package_path(doc)
    rows = read_jsonl(path, tolerant=True) if path.exists() else []
    if not rows or rows[-1].get("record") != "completion":
        return False
    return [r["unit_id"] for r in rows if r["record"] == "unit"] == [u["unit_id"] for u in doc["units"]]

# %% [markdown]
# ## Block 10: the pipeline
#
# `ingest(doc)` runs the steps in order. `run(uris)` ingests a list of documents, several at a
# time when asked, and appends a line per document to `ingest.log`. `receipt()` sums every
# package on disk. `WATCH` turns the per-stage narration on and off.

# %%
# Block 10: the pipeline as one function, ingest(doc).
#
# The steps in order: triage (which kinds of unit to read), derive_unit for each unit kept,
# then, all at the end, reconcile, fold_document, adjudicate, verify, write_package. WATCH says
# whether the run narrates each stage. A finished package for the same input is skipped. Every
# document appends an entry to ingest.log; the receipt sums the packages on disk.
LOG = OUT / "ingest.log"
WATCH = True                                  # narrate each stage as the run goes
RESULTS = []                                  # (source_uri, records, counts, stats) for every document this session ingested


def triage(doc, ctx):
    """Which kinds of unit are not the work: ({kind: reason}, flags). Boilerplate goes by rule.
    A document with more than one kind left after that asks the judge; the answer stands, short
    of leaving out more than half the document."""
    excluded = {u["kind"]: f"{u['kind'].replace('_', ' ')}: not the work itself" for u in doc["units"] if u["kind"] in BOILERPLATE}
    kinds = {}
    for u in doc["units"]:
        text = doc["text"][u["start"]:u["end"]]
        kinds.setdefault(u["kind"], []).append((u["position"], u["label"], word_count(text), first_line(text)))
    if one_reading(doc):                          # one unit to read: no choice to make, the boilerplate goes by rule
        return excluded, []
    if len(kinds) < 2:
        return {}, []
    reply = generate(triage_prompt(doc, kinds), TRIAGE_SCHEMA, "triage", ctx=ctx)
    excluded, flags = {}, [] if reply else ["triage reply rejected twice; every kind was read"]
    for item in (reply or {}).get("exclude", []):
        named = str(item["kind"]).strip().strip("'\"").casefold()
        matched = [kind for kind in kinds if kind.casefold() == named]
        if matched:
            excluded[matched[0]] = item["reason"]
        else:
            flags.append(f"triage named a kind the document does not have: {item['kind']!r}")
    left_out = sum(len(kinds[kind]) for kind in excluded)
    if left_out * 2 > len(doc["units"]):      # an answer that drops most of a document is a mistake more often than a judgement
        flags.append(f"triage would leave out {left_out} of {len(doc['units'])} units, more than half; ignored")
        excluded = {}
    return excluded, flags


def show_unit(rec, unit, unit_cost, total_cost):
    """One unit as it lands."""
    by_category = tally(x["category"] for x in rec["rejected_facts"])
    by_path = tally(f["matched_by"] for f in rec["facts"])
    print(f"[{rec['position']}] {rec['label'][:40]} ({rec['kind']}): {word_count(unit['text']):,} words;"
          f" {len(rec['entities'])} entities ({len(rec['dropped_entities'])} dropped);"
          f" {len(rec['facts'])} facts kept ({counts_text(by_path)}), {len(rec['rejected_facts'])} rejected ({counts_text(by_category)});"
          f" {len(rec['cells'])} cells; ${unit_cost:.3f} this unit, ${total_cost:.3f} so far")
    for e in rec["entities"]:
        print(f"    {e['name'][:34]:<34} {e['kind'][:9]:<9} {'named' if e['named'] else 'unnamed':<8}"
              f" {'major' if e['major'] else 'minor':<6} x{e['mentions']:<3} forms: {' | '.join(e['forms'][:4])[:70]}")
    for d in rec["dropped_entities"]:
        print(f"    DROPPED {d['name'][:34]}: {d['why']} {d['forms'][:3]}")
    for f in rec["facts"]:
        print(f"    {f['subject']} -{f['predicate']}-> {f['object']}{' [' + f['qualifiers'] + ']' if f['qualifiers'] else ''}"
              f"  ({f['matched_by']}{', voice ambiguous' if f['voice_ambiguous'] else ''})  \"{' '.join(f['quote'].split())[:90]}\"")
    for x in rec["rejected_facts"]:
        print(f"    REJECTED {x['category']}: {x['subject']} -{x['predicate']}-> {x['object']}  \"{' '.join(x['quote'].split())[:90]}\"")
    if rec["summary"]:
        print(f"    SUMMARY {rec['summary']}")
        for c in rec["cells"]:
            print(f"    [{c['entity']}] {c['text']}")


def show_document(entities, ledger, stats, folded, adjudicated):
    by_how = tally(f"{entry['how']} {entry['verdict']}" for entry in ledger)
    print(f"reconcile: {stats['locals']} unit-locals -> {len(entities)} document entities; ledger {counts_text(by_how)};"
          f" {stats['candidate_pairs']} pairs queued over {stats['judge_rounds']} rounds, {stats['judged_pairs']} judged in {stats['judge_calls']} calls")
    if folded["abstract"]:
        print(f"abstract ({word_count(folded['abstract']['text'])} words, limit {folded['abstract']['limit']}): {folded['abstract']['text']}")
    else:
        print("abstract: none (no unit summaries)")
    print(f"salience: {len(folded['majors'])} major, {len(folded['minors'])} minor, {len(folded['demoted'])} demoted for want of anything to summarise;"
          f" {len(folded['entity_abstracts'])} entity abstracts")
    for e in folded["majors"]:
        others = [n for n in e["names"] if n != e["name"]]
        print(f"    {e['name'][:34]:<34} {'/'.join(e['kinds'])[:16]:<16} units {len(e['units']):>3} facts {e['n_facts']:>3}  "
              + (f"also: {', '.join(others)[:60]}" if others else ""))
    total = {"raw": 0, "facts": 0, "attributes": 0, "contradictions": 0, "unsupported": 0, "dropped": 0}
    for e in folded["majors"]:
        a = adjudicated[e["index"]]
        for key in total:
            total[key] += a[key] if key in ("raw", "dropped") else len(a[key])
        if a["skipped"]:
            print(f"    {e['name'][:34]:<34} {a['raw']:>3} raw facts stand: {a['skipped']}")
        else:
            print(f"    {e['name'][:34]:<34} {a['raw']:>3} raw facts -> {len(a['facts']):>3} facts, {len(a['attributes']):>3} attributes,"
                  f" {len(a['contradictions'])} contradictions" + (f", {a['dropped']} dropped for pointing at nothing" if a["dropped"] else ""))
    print(f"adjudicated: {total['raw']} raw facts -> {total['facts']} facts, {total['attributes']} attributes,"
          f" {total['contradictions']} contradictions; {total['unsupported']} raw facts their passage does not state, to be corrected or dumped;"
          f" {total['dropped']} dropped; {sum(1 for a in adjudicated.values() if a['skipped'])} majors left to their raw facts")


def ingest(doc, ctx=None):
    """One document, start to finish: the units on their own, then everything merged at the end.
    (path, counts, stats, records, entities, folded)."""
    ctx = {"doc": doc["source_uri"], **(ctx or {})}
    logged_before = len(CALLS)                  # this document's own calls start here
    light = one_reading(doc)                    # one unit to read: nothing to merge, so the short path

    # which kinds of unit to read
    excluded, flags = triage(doc, ctx)
    kept = [u for u in doc["units"] if u["kind"] not in excluded]
    left_out = [{"position": u["position"], "kind": u["kind"], "label": u["label"], "reason": excluded[u["kind"]]} for u in doc["units"] if u["kind"] in excluded]
    if WATCH:
        print(f"triage: {counts_text(tally(u['kind'] for u in doc['units']))}; " + (f"left out {len(left_out)} unit(s)" if left_out else "nothing left out"))
        for kind, reason in excluded.items():
            print(f"    {kind}: {reason}")
        for flag in flags:
            print(f"    FLAG {flag}")

    # the units, each on its own, WORKERS at a time, landing in reading order
    def derive_one(unit):
        try:
            return derive_unit(doc, unit, {**ctx, "unit": unit["position"]}, light=light)
        except SpendStop as stop:
            return stop          # raised once the rest of the batch has landed

    records, width = [], max(WORKERS, 1)
    for at in range(0, len(kept), width):
        batch = [{**u, "text": doc["text"][u["start"]:u["end"]]} for u in kept[at:at + width]]
        for unit, rec in zip(batch, in_parallel(derive_one, batch)):
            if isinstance(rec, SpendStop):
                raise rec
            records.append(rec)
            if WATCH:
                show_unit(rec, unit, spend(doc["source_uri"], unit["position"])[0], spend(doc["source_uri"], since=logged_before)[0])

    # the document, all at the end: reconcile, fold, adjudicate, verify, write
    entities, ledger, candidates, stats = reconcile(records, ctx, watch=WATCH)
    folded = fold_document(records, entities, ctx, light=light)
    adjudicated = adjudicate(records, folded, ctx, watch=WATCH, light=light)
    if WATCH:
        show_document(entities, ledger, stats, folded, adjudicated)
    flagged, corrections, correct_calls, notes = verify(records, folded, adjudicated, ctx, watch=WATCH)
    cost, calls = spend(doc["source_uri"], since=logged_before)
    stats.update({"one_reading": light, "calls": calls, "cost": round(cost, 4),
                  "matched_by": tally(f["matched_by"] for r in records for f in r["facts"]),
                  "rejected_by": tally(x["category"] for r in records for x in r["rejected_facts"]),
                  "units_excluded": len(left_out), "triage_flags": flags, "correct_calls": correct_calls, "correction_notes": notes})
    path, counts = write_package(doc, records, entities, folded, adjudicated, ledger, candidates, left_out, stats, flagged, corrections)
    if WATCH:
        print(f"package {path}: {counts}")
    RESULTS.append((doc["source_uri"], records, counts, stats))
    return path, counts, stats, records, entities, folded


def note(text):
    print(text)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(text + "\n\n")


def one_reading_report(records, folded):
    """A one-reading document's majors, each with its abstract and the facts it was given: the
    whole of what can be read as the run goes, since the trace is stilled while documents run
    together."""
    said = {a["index"]: a["text"] for a in folded["entity_abstracts"]}
    stated = {}
    for r in records:
        for f in r["facts"]:
            stated.setdefault(f["subject"], []).append(f"{f['predicate']} -> {f['object']}" + (f" [{f['qualifiers']}]" if f["qualifiers"] else ""))
    lines = []
    for e in folded["majors"]:
        lines.append(f"    {e['name'][:44]:<46} {e['kind'][:16]}")
        if said.get(e["index"]):
            lines.append(f"        {said[e['index']][:400]}")
        for one in dict.fromkeys(x for ui, local_name in e["members"] for x in stated.get(local_name, [])):
            lines.append(f"        - {one[:150]}")
    return lines


def one_document(uri):
    """One document, start to finish, and what to say about it. Every outcome is returned rather
    than raised, so a batch of documents running together all report."""
    try:
        doc = load_document(uri)
        if completed(doc):
            return {"skipped": True}
        if WATCH:
            print(f"\n=== {uri}: {len(doc['units'])} units, {len(doc['text']):,} chars{' (text rebuilt from the PDF)' if doc['text_rebuilt'] else ''},"
                  f" author {doc.get('author')!r}, date {doc.get('occurred_at')} ===")
        path, counts, stats, records, entities, folded = ingest(doc)
        abstract = folded["abstract"]["text"][:200] if folded["abstract"] else "(none)"
        entry = [f"{uri}  units {counts['units']}  entities {counts['entities']} ({counts['majors']} major)  mentions {counts['mentions']}"
                 f"  facts {counts['facts_kept']} kept / {counts['facts_rejected']} rejected / {counts['facts_stored']} stored"
                 f"  cells {counts['cells']}  calls {stats['calls']}  ${stats['cost']:.3f}",
                 f"    matched {stats['matched_by']}  rejected {stats['rejected_by']}  locals {stats['locals']}"
                 f" pairs {stats['candidate_pairs']} judged {stats['judged_pairs']}", f"    abstract: {abstract}"]
        if stats["one_reading"]:
            entry += one_reading_report(records, folded)
        else:
            entry += [f"    {e['name'][:36]:<36} {'/'.join(e['kinds'])[:16]:<16} units {len(e['units']):>3} facts {e['n_facts']:>3}" for e in folded["majors"][:12]]
        return {"done": True, "text": "\n".join(entry + [f"    -> {path}"])}
    except SpendStop as e:
        return {"stop": True, "text": f"{uri}: {e} after ${spend(uri)[0]:.3f} on this document; the run stops here"}
    except Exception as e:
        return {"text": f"{uri}  ERROR {type(e).__name__}: {e}"}


def run(uris, at_once=None):
    """Every document named, DOCS_AT_ONCE at a time and reported in the order they were named.
    While more than one runs the per-unit trace is stilled: eight interleaved traces are not a
    log anyone reads, and each document still reports as it lands."""
    global WATCH
    if not KEY:
        raise SystemExit("no OPENAI_API_KEY: set it in the environment, or attach it as a Kaggle secret")
    todo = [uri for uri in uris if uri in BY_URI]
    for uri in uris:
        if uri not in BY_URI:
            note(f"not in export: {uri}")
    width = max(at_once or DOCS_AT_ONCE, 1)
    watching, WATCH = WATCH, WATCH and width == 1
    done = skipped = 0
    try:
        for at in range(0, len(todo), width):
            results = in_parallel(one_document, todo[at:at + width], width=width)
            for result in results:
                if result.get("text"):
                    note(result["text"])
                done += bool(result.get("done"))
                skipped += bool(result.get("skipped"))
            if any(result.get("stop") for result in results):
                break
    finally:
        WATCH = watching
    print(f"done {done}  skipped (already complete) {skipped}  spent ${spend()[0]:.2f} this session")
    return done, skipped


def receipt():
    """Sums over every package on disk, plus the calls this session logged."""
    rec = {"ingestor": INGESTOR, "documents": 0, "by_group": {}, "counts": {}, "matched_by": {}, "rejected_by": {}, "cost_of_packages": 0.0,
           "cost_this_session": round(spend()[0], 4), "calls_this_session": len(CALLS), "calls_by_stage": tally(c["stage"] for c in CALLS),
           "schema_rejections_this_session": MISSES["rejections"], "schema_retries_this_session": MISSES["retries"]}
    for path in sorted(OUT.rglob("*.jsonl")):
        if path.parent == OUT:
            continue
        rows = read_jsonl(path, tolerant=True)
        if not rows or rows[-1].get("record") != "completion":
            continue
        last = rows[-1]
        rec["documents"] += 1
        group = path.parent.parent.name
        rec["by_group"][group] = rec["by_group"].get(group, 0) + 1
        for k, v in last["counts"].items():
            if isinstance(v, (int, bool)):
                rec["counts"][k] = rec["counts"].get(k, 0) + int(v)
        for key in ("matched_by", "rejected_by"):
            for k, v in last["stats"].get(key, {}).items():
                rec[key][k] = rec[key].get(k, 0) + v
        rec["cost_of_packages"] = round(rec["cost_of_packages"] + last["stats"].get("cost", 0), 4)
    (OUT / "receipt.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return rec


def run_and_roll_up(uris, top=5, at_once=None):
    """The run, then the roll-up of every package that exists for the documents named."""
    try:
        run(uris, at_once=at_once)
    finally:
        print(json.dumps(receipt(), indent=1))
    for uri in uris:
        path = package_path({"source_uri": uri})
        if path.exists():
            rollup(path, top=top)

# %% [markdown]
# ## Block 11: reading a package back
#
# `targets(names)` turns titles or file names into source uris. `rollup(path)` writes the
# roll-up beside the package: the abstract, the unit summaries, the majors, and everything
# known about the top five. `draw_graph(path)` draws the majors as a graph.

# %%
# Block 11: naming documents, and reading a package back.
#
# targets(names) turns what a run names into source_uris: "all" for the export, or a list of
# titles or source_uri endings. rollup(path) writes the roll-up of one package beside it: the
# abstract, the unit summaries in order, the major entities, then everything known about the
# top five. draw_graph(path) draws the majors as the 09-02 demo did.
import random


def targets(spec):
    if spec == "all":
        return sorted(BY_URI)
    uris = []
    for name in spec:
        uri = find_document(name)
        if uri is None:
            print(f"no document called {name!r}")
        else:
            uris.append(uri)
    return uris


def read_package(path):
    """A package's records grouped by record type; a package with no completion is not read."""
    rows = read_jsonl(path, tolerant=True)
    if not rows or rows[-1].get("record") != "completion":
        raise ValueError(f"{path}: no completion record; the package is unfinished")
    return grouped(rows, "record")


def grouped(rows, key):
    out = {}
    for row in rows:
        out.setdefault(row.get(key), []).append(row)
    return out


def ranked_majors(by):
    """The package's major nodes, most units first, then most raw facts: [(units, facts, node)]."""
    units_of = {e["subject"]: len(e["units"]) for e in by.get("edge", []) if e["predicate"] == "appears_in"}
    facts_of = grouped(by.get("fact", []), "subject")
    ranked = [(units_of.get(n["node_id"], 0), len(facts_of.get(n["node_id"], [])), n) for n in by.get("node", []) if n["kind"] != "document"]
    return sorted(ranked, key=lambda item: (-item[0], -item[1]))


def rollup(path, top=5):
    """The roll-up written beside its package as roll-up.txt. The per-unit trace on stdout
    already carries every fact and its quote; printing the roll-up too doubled the log."""
    written = Path(path).with_name("roll-up.txt")
    with written.open("w", encoding="utf-8") as handle:
        with redirect_stdout(handle):
            rollup_text(path, top=top)
    print(f"roll-up ({written.stat().st_size:,} bytes) -> {written}")


def rollup_text(path, top=5):
    """The roll-up itself, printed."""
    by = read_package(path)
    doc, units = by["document"][0], sorted(by.get("unit", []), key=lambda u: u["position"])
    label_of = {u["unit_id"]: f"[{u['position']}] {u['label']}" for u in units}
    position = {u["unit_id"]: u["position"] for u in units}
    doc_node = next(n["node_id"] for n in by["node"] if n["kind"] == "document")
    abstracts = {a["node_id"]: a["text"] for a in by.get("abstract", [])}
    cells_of, facts_of = grouped(by.get("cell", []), "node_id"), grouped(by.get("fact", []), "subject")
    adjudicated_of, attributes_of = grouped(by.get("adjudicated_fact", []), "node_id"), grouped(by.get("attribute", []), "node_id")
    contradictions_of, aliases_of = grouped(by.get("contradiction", []), "node_id"), grouped(by.get("alias", []), "node_id")
    name_of = {n["node_id"]: n["name"] for n in by.get("node", [])}

    print(f"\n{'#' * 8} ROLL-UP: {doc['title'] or doc['source_uri']}  ({doc['source_uri']}; {len(units)} units)")
    print("\nABSTRACT")
    print(abstracts.get(doc_node, "(the abstract was rejected)"))
    print("\nUNIT SUMMARIES")
    summary_of = {c["unit_id"]: c["text"] for c in cells_of.get(doc_node, [])}
    for u in units:
        if u["unit_id"] in summary_of:
            print(f"{label_of[u['unit_id']]}: {summary_of[u['unit_id']]}")
    ranked = ranked_majors(by)
    print(f"\nMAJOR ENTITIES ({len(ranked)})")
    for n_units, n_facts, n in ranked:
        print(f"    {n['name'][:36]:<36} {n['kind'][:16]:<16} units {n_units:>3}  raw facts {n_facts:>3}  consolidated {len(adjudicated_of.get(n['node_id'], [])):>3}"
              f"  attributes {len(attributes_of.get(n['node_id'], [])):>3}")
    for n_units, n_facts, n in ranked[:top]:
        nid = n["node_id"]
        print(f"\n{'=' * 8} {n['name']} ({n['kind']}): {n_units} units, {n_facts} raw facts")
        others = [x for x in n["provenance"].get("names", []) if x != n["name"]]
        if others:
            print(f"also called: {', '.join(others)}")
        if aliases_of.get(nid):
            print(f"forms: {' | '.join(a['alias'] for a in aliases_of[nid][:20])}")
        if nid in abstracts:
            print(f"abstract: {abstracts[nid]}")
        if cells_of.get(nid):
            print("narrative:")
            for c in sorted(cells_of[nid], key=lambda c: position.get(c["unit_id"], 0)):
                print(f"    {label_of.get(c['unit_id'], c['unit_id'])}: {c['text']}")
        if adjudicated_of.get(nid):
            print(f"consolidated facts ({len(adjudicated_of[nid])}):")
            for a in adjudicated_of[nid]:
                print(f"    {a['predicate']} -> {a['object']}{' [' + a['qualifiers'] + ']' if a.get('qualifiers') else ''}  <- {len(a['from_facts'])} raw")
        if attributes_of.get(nid):
            print(f"attributes ({len(attributes_of[nid])}):")
            for a in attributes_of[nid]:
                print(f"    {a['attribute']}" + (f": {a['value']}" if a.get("value") else ""))
        for c in contradictions_of.get(nid, []):
            print(f"contradiction: {c['note']}")
        if facts_of.get(nid):
            print(f"raw facts ({len(facts_of[nid])}), each with its quote:")
            for f in facts_of[nid]:
                who = f["provenance"].get("subject_name", "")
                line = f"{f['predicate']} -> {name_of.get(f['object'], f['object'])}" if f["direction"] == "forward" else f"(inverse) {who} {f['predicate']} -> {n['name']}"
                print(f"    {line}{' [' + f['qualifiers'] + ']' if f.get('qualifiers') else ''}  {label_of.get(f['unit_id'], '')} \"{' '.join(f['quote'].split())[:100]}\"")


def draw_graph(path):
    """The majors of one package as a graph, the 09-02 demo's way: nodes sized by how many
    units they appear in, an edge for every pair that shares a fact (a consolidated fact where
    the major has them, else a raw one), labelled with one of its predicates."""
    import networkx as nx
    import matplotlib.pyplot as plt
    by = read_package(path)
    doc, ranked = by["document"][0], ranked_majors(by)
    name_of = {n["node_id"]: n["name"] for units, facts, n in ranked}
    node_by_name = {norm(n["name"]): n["node_id"] for units, facts, n in ranked}
    for a in by.get("alias", []):
        node_by_name.setdefault(norm(a["alias"]), a["node_id"])
    facts_of, adjudicated_of = grouped(by.get("fact", []), "subject"), grouped(by.get("adjudicated_fact", []), "node_id")
    G = nx.Graph()
    for n_units, n_facts, n in ranked:
        G.add_node(n["name"], size=n_units)
    for n_units, n_facts, n in ranked:
        nid = n["node_id"]
        if adjudicated_of.get(nid):
            edges = [(node_by_name.get(norm(a["object"])), a["predicate"]) for a in adjudicated_of[nid]]
        else:
            edges = [(f["object"], f["predicate"]) for f in facts_of.get(nid, []) if f["object_is_node"]]
        for target, predicate in edges:
            if target and target != nid and target in name_of:
                if G.has_edge(n["name"], name_of[target]):
                    G[n["name"]][name_of[target]]["labels"].add(predicate)
                else:
                    G.add_edge(n["name"], name_of[target], labels={predicate})
    pos = nx.spring_layout(G, seed=7, k=1.6)
    plt.figure(figsize=(16, 11))
    nx.draw_networkx_nodes(G, pos, node_size=[300 + 160 * G.nodes[n]["size"] for n in G], node_color="#cfe3f7")
    nx.draw_networkx_edges(G, pos, alpha=0.4)
    nx.draw_networkx_labels(G, pos, font_size=9)
    nx.draw_networkx_edge_labels(G, pos, font_size=7, edge_labels={(a, b): sorted(d["labels"])[0] for a, b, d in G.edges(data=True)})
    plt.title(doc["title"] or doc["source_uri"])
    plt.axis("off")
    png = Path(path).with_name("graph-" + Path(path).stem + ".png")
    plt.savefig(png, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close()
    print(f"graph of {doc['title'] or doc['source_uri']}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges; saved {png}")
    return G

# %% [markdown]
# ## Block 12: run, chat sessions
#
# A sample of LongMemEval sessions, sixteen at a time. Each is one reading, so it takes the short
# path.

# %%
# Block 12: the run, a spread of chat sessions, first of all. Every one of the 19,206 sessions
# is two units, one of them the session id, so each takes the one-reading path: no triage, no
# entity abstract, no adjudication, and one verification pass over its facts. Four calls a
# document instead of twenty-five. The seed is unchanged from the run of 09-07, so the first 40
# of these 200 are the same 40 that run ingested on the full path, and the two are comparable.
# Nothing here reaches across documents: each session is its own package, in its own folder.
CHAT_SAMPLE, CHAT_SEED, CHAT_AT_ONCE = 200, 494, 16
BUDGET = 5.00

if __name__ == "__main__" and CHAT_SAMPLE:
    chats = sorted(u for u in BY_URI if "/longmemeval/" in u)
    random.Random(CHAT_SEED).shuffle(chats)
    chats = sorted(chats[:CHAT_SAMPLE])
    start_block(BUDGET)
    print(f"chats: {len(chats)} sessions sampled from {sum(1 for u in BY_URI if '/longmemeval/' in u):,},"
          f" {CHAT_AT_ONCE} at a time; budget ${BUDGET:.2f} for this block")
    run_and_roll_up(chats, at_once=CHAT_AT_ONCE)

# %% [markdown]
# ## Block 13: run, Oz book 1

# %%
# Block 13: the run, Oz book 1.
#
# RUN names the documents, by title or by the end of their source_uri; WATCH in block 10 says
# whether each stage narrates itself; BUDGET ends the block past that many dollars of its own
# spending. For reference, the 09-02 demo on Oz book 1: v3 632 entities, 969 facts, 53 dropped,
# $1.26; the 0.4 run of 09-06: 358 entities (38 major), 869 facts, 74 rejected, $2.23. Each
# document ends in its roll-up.
RUN = ["The Wonderful Wizard of Oz"]
BUDGET = 5.00

if __name__ == "__main__":
    uris = targets(RUN)
    start_block(BUDGET)
    print(f"ingesting {len(uris)} documents, budget ${BUDGET:.2f}: {[BY_URI[u]['title'] or u for u in uris]}")
    run_and_roll_up(uris)

# %% [markdown]
# ## Block 14: run, five papers

# %%
# Block 14: the run, five papers, Zep first. The papers' text is withheld from the public
# export; block 1 rebuilds it from the private papers dataset, which must be attached.
PAPERS_TO_RUN, SEED, ALWAYS = 5, 494, ["rasmussen2025-zep.pdf"]
BUDGET = 8.00

if __name__ == "__main__" and PAPERS_TO_RUN:
    chosen = [find_document(name) for name in ALWAYS]
    others = sorted(u for u in BY_URI if u.endswith(".pdf") and u not in chosen)
    random.Random(SEED).shuffle(others)
    chosen += others[:PAPERS_TO_RUN - len(chosen)]
    start_block(BUDGET)
    print(f"papers: {[BY_URI[u]['title'] or u for u in chosen]}; budget ${BUDGET:.2f} for this block")
    run_and_roll_up(chosen)

# %% [markdown]
# ## Block 15: run, a Greek play and a novel

# %%
# Block 15: the run, one Greek work and one novel from the GraphRAG benchmark, so the entity and
# fact shapes of a play, a novel and a chat can be read side by side before the merge is built.
OTHERS = ["/greek/22_35173.txt", "/graphrag-bench/Novel-40700.txt"]
BUDGET = 6.00

if __name__ == "__main__" and OTHERS:
    chosen = [u for u in (find_document(name) for name in OTHERS) if u]
    start_block(BUDGET)
    print(f"others: {[BY_URI[u]['title'] or u for u in chosen]}; budget ${BUDGET:.2f} for this block")
    run_and_roll_up(chosen)

# %% [markdown]
# ## Block 16: graphs
#
# One graph per document ingested this session, saved beside its package.

# %%
# Block 16: the graphs. One knowledge graph per document ingested this session, drawn the
# 09-02 demo's way and saved beside the packages. Needs networkx and matplotlib, which Kaggle has.
if __name__ == "__main__":
    for uri, records_, counts_, stats_ in RESULTS:
        if len(records_) < 2:              # a chat session is one reading: a graph of it says nothing
            continue
        if package_path({"source_uri": uri}).exists():
            draw_graph(package_path({"source_uri": uri}))
