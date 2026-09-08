# %% [markdown]
# # FactLedger ingestor: one document at a time, from the extractor's export to a document package
#
# The extractor wrote `documents.jsonl` (the text, once), `units.jsonl` (ranges into that text)
# and `pieces.jsonl` (the split plan, with the author of each turn). This notebook reads one
# document at a time and writes one **document package**: the entities the document is about,
# every mention with its span, every fact with a verbatim quote located at document offsets,
# a narrative cell per entity per unit, the document's abstract, and a dossier per major entity
# for the merge that comes next. Nothing here looks at a second document.
#
# Every unit is read on its own, with no look back. All merging happens at the end: the
# unit-local entities are reconciled bottom up through a priority queue of pairs and the facts
# of each major are consolidated; predicates stay as the model wrote them. Block 1 finds the files.
# Block 2 is the model interface, block 3 tests the connection. Block 4 is ids and helpers,
# block 5 the quote gate, block 6 the prompts. Block 7 derives one unit. Block 8 reconciles,
# block 9 folds the abstract and decides salience, block 10 writes the package. Block 11 is
# the pipeline as one function with flags that print each step. Block 12 names documents and
# reads a package back for the roll-up and the graph. Blocks 13 to 16 are the runs (a sample of
# chat sessions first, then Oz book 1, five papers, and a Greek play with a novel), each writing
# a roll-up beside every package it makes; block 17 draws the graphs.
#
# **On Kaggle:** attach the export dataset (`jhffmn/it494-factledger-step0`) and, for the
# reference papers whose text it withholds, the private PDFs (`jhffmn/it494-reference-papers`);
# attach `OPENAI_API_KEY` under Add-ons > Secrets, turn Internet on, run block 3 to see the
# connection work, then blocks 13 to 15. The packages land under `/kaggle/working/packages`.
# To continue a stopped run, make a dataset from that output and attach it: finished packages
# are copied in and skipped.

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
import shutil
import sys
import time
import unicodedata
from datetime import datetime, timezone
from contextlib import redirect_stdout
from pathlib import Path

INGESTOR = "factledger-ingestor 0.8"
KAGGLE_EXPORTS = (Path("/kaggle/input/datasets/jhffmn/it494-factledger-step0"), Path("/kaggle/input/it494-factledger-step0"))
KAGGLE_PAPERS = (Path("/kaggle/input/datasets/jhffmn/it494-reference-papers"), Path("/kaggle/input/it494-reference-papers"))
LOCAL_EXPORT, LOCAL_PAPERS = Path("data/export"), Path("papers")
KAGGLE_OUT, LOCAL_OUT = Path("/kaggle/working/packages"), Path("data/packages")

if hasattr(sys.stdout, "reconfigure"):            # a console that is not UTF-8 must not end the run
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def choose_export():
    if os.environ.get("EXPORT"):
        return Path(os.environ["EXPORT"])
    for path in KAGGLE_EXPORTS:
        if path.exists():
            return path
    if LOCAL_EXPORT.exists():
        return LOCAL_EXPORT
    raise SystemExit("no export found: attach the dataset on Kaggle, or set EXPORT to a folder holding documents.jsonl")


def choose_out():
    if os.environ.get("OUT"):
        return Path(os.environ["OUT"])
    if Path("/kaggle/working").exists():
        return KAGGLE_OUT
    return LOCAL_OUT


def choose_papers():
    """The folder holding the reference papers' PDFs, or None."""
    if os.environ.get("PAPERS"):
        return Path(os.environ["PAPERS"])
    for path in KAGGLE_PAPERS + (LOCAL_PAPERS,):
        if path.exists():
            return path
    return None


def read_jsonl(path):
    """One dict per non-empty line."""
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_own_jsonl(path):
    """The ingestor's own files, which a killed session can leave cut short: the rows up to the
    first line that does not parse."""
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                break
    return rows


def pdf_text(data):
    """The extractor's reading of a PDF, kept verbatim so the export's offsets resolve: PyMuPDF's
    text layer page by page, pages joined with a newline. PyMuPDF is imported only here."""
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
    copied = 0
    root = Path("/kaggle/input")
    if not root.exists():
        return copied
    for folder in root.rglob("packages"):
        for src in folder.rglob("*.jsonl"):
            if src.name in ("manifest.jsonl", "calls.jsonl", "rejections.jsonl", "retries.jsonl"):
                continue
            dst = OUT / src.relative_to(folder)
            if not dst.exists():
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


def position_of_row(row):
    return row["position"]


def group_by_document(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["doc_id"], []).append(row)
    for group in grouped.values():
        group.sort(key=position_of_row)
    return grouped


def load_document(uri, by_uri, units, pieces):
    """The document with its text, its units and its pieces in order. One seek."""
    entry = by_uri[uri]
    with (EXPORT / "documents.jsonl").open("rb") as f:
        f.seek(entry["offset"])
        doc = json.loads(f.readline().decode("utf-8"))
    assert doc["doc_id"] == entry["doc_id"]
    doc["units"] = units.get(doc["doc_id"], [])
    doc["pieces"] = pieces.get(doc["doc_id"], [])
    doc["text_rebuilt"] = doc["text"] is None
    if doc["text_rebuilt"]:
        doc["text"] = withheld_text(doc)
        if doc["units"] and doc["units"][-1]["end"] != len(doc["text"]):
            raise ValueError(f"{uri}: the rebuilt text has {len(doc['text']):,} chars but the units end at"
                             f" {doc['units'][-1]['end']:,}; the PDF was read differently from the extractor")
    for u in doc["units"]:                        # every unit must be a real slice of the text
        assert 0 <= u["start"] < u["end"] <= len(doc["text"]), (uri, u["position"])
        assert doc["text"][u["start"]:u["end"]].strip(), (uri, u["position"])
    return doc


def find_document(name):
    """The source_uri of the document called `name`: by title (an exact title first, then a
    title containing it), else by the end of its source_uri; None when nothing matches."""
    wanted = name.casefold()
    exact, partial = [], []
    for uri, entry in BY_URI.items():
        title = (entry["title"] or "").casefold()
        if title == wanted:
            exact.append(uri)
        elif wanted in title:
            partial.append(uri)
    matches = exact or partial
    if len(matches) > 1:
        print(f"{name!r} matches {len(matches)} titles; taking the first: {[BY_URI[u]['title'] for u in matches]}")
    if matches:
        return matches[0]
    for uri in BY_URI:
        if uri.endswith(name):
            return uri
    return None


EXPORT, OUT, PAPERS = choose_export(), choose_out(), choose_papers()
OUT.mkdir(parents=True, exist_ok=True)
SEEDED = seed_from_prior_output()
BY_URI = index_documents()
PAPERS_ROWS = {row["doc_id"]: row for row in read_jsonl(EXPORT / "papers.jsonl")} if (EXPORT / "papers.jsonl").exists() else {}
UNITS = group_by_document(read_jsonl(EXPORT / "units.jsonl"))
PIECES = group_by_document(read_jsonl(EXPORT / "pieces.jsonl"))
print(f"export {EXPORT}: {len(BY_URI)} documents, {sum(len(g) for g in UNITS.values())} units,"
      f" {sum(len(g) for g in PIECES.values())} pieces; packages to {OUT}")
if PAPERS_ROWS:
    print(f"{len(PAPERS_ROWS)} documents have their text withheld; their PDFs are"
          f" {'under ' + str(PAPERS) if PAPERS else 'NOT attached: attach jhffmn/it494-reference-papers to read them'}")
if SEEDED:
    print(f"{SEEDED} files seeded from a previous run's output")

# %%
# Block 2: the model interface: generate(prompt, schema).
#
# The key comes from the OPENAI_API_KEY environment variable, else from the Kaggle secret of
# that name. Raw HTTP. The API rejects temperature, so reasoning_effort steers it. Every call
# is logged to calls.jsonl the moment it returns, with model, tokens, latency and cost. A
# reply that does not fit its schema is asked for once more with the error appended, then
# rejected; the first miss is logged in retries.jsonl. A timeout, a 429 or a 5xx is retried
# three times; a 429 for exhausted quota ends the run like the spend stop, which is checked
# before every call. Independent calls (the entity abstracts, the adjudications) run WORKERS
# at a time; the logs take one lock.
import http.client
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

LUNA = "gpt-5.6-luna"                      # derive
TERRA = "gpt-5.6-terra"                    # judge, folds, adjudication
PRICE = {LUNA: (0.20, 1.20), TERRA: (2.00, 12.00)}          # $ per million tokens in, out
SPEND_STOP = float(os.environ.get("SPEND_STOP", "25"))
BLOCK_START = 0.0                 # what had been spent when this block began
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

CALLS, REJECTIONS, RETRIES = [], [], []
LOG_LOCK = threading.Lock()
REPLIES, REPLIES_LOCK, IN_FLIGHT = {}, threading.Lock(), {}   # per document: what it has already paid for


class SpendStop(Exception):
    pass


class SchemaError(ValueError):
    pass


def record(name, row):
    """Append one row to a run log under OUT, so it survives whatever ends the session."""
    with LOG_LOCK:
        with (OUT / name).open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def call_thunk(thunk):
    """in_parallel over calls that take no argument of their own."""
    return thunk()


def in_parallel(function, items, width=None):
    """function over each item, `width` at a time (WORKERS when not said), results in the items'
    order. An error in one (a spend stop included) is raised once the calls in flight have
    returned."""
    width = max(width or WORKERS, 1)
    if width <= 1 or len(items) <= 1:
        return [function(item) for item in items]
    with ThreadPoolExecutor(max_workers=width) as pool:
        return list(pool.map(function, items))


def spend():
    return sum(c["cost"] for c in CALLS)


def document_spend(doc, since=0):
    """(cost, calls) for one document's own calls logged since `since`. Documents run together, so
    a global delta counts its neighbours' calls as its own; and a document derived twice in one
    session must not count the first derivation's calls again (fixed 09-07)."""
    rows = [c for c in CALLS[since:] if c.get("doc") == doc["source_uri"]]
    return sum(c["cost"] for c in rows), len(rows)


def unit_spend(doc, position):
    """(cost, calls) for one unit's own calls, read back from the log. The units derive together
    now, so a unit's spend is no longer the difference between two moments."""
    rows = [c for c in CALLS if c.get("doc") == doc["source_uri"] and c.get("unit") == position]
    return sum(c["cost"] for c in rows), len(rows)


def start_block(budget):
    """A run block's own budget, counted from here. The stop is per block, not per session:
    a later block's budget cannot be eaten by an earlier one (ruling of 09-07)."""
    global SPEND_STOP, BLOCK_START
    SPEND_STOP, BLOCK_START = budget, spend()


def check_schema(value, schema, path="$"):
    """A small validator for the reply shapes in block 6: type, required keys, items, enum.
    Raises SchemaError naming the path, which goes back to the model on the retry."""
    allowed = schema.get("type", "object")
    if not isinstance(allowed, list):
        allowed = [allowed]
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


TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "integer": int, "number": (int, float)}


def is_of_type(value, name):
    if name == "null":
        return value is None
    if name == "boolean":
        return isinstance(value, bool)
    if name not in TYPES:
        return False
    return isinstance(value, TYPES[name]) and not isinstance(value, bool)


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
    if spend() - BLOCK_START >= SPEND_STOP:
        raise SpendStop(f"spending stop: ${spend() - BLOCK_START:.2f} of ${SPEND_STOP:.2f} for this block")
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
    """The reply as a dict that fits `schema`, or None after one retry with the error appended.
    A reply this document has already bought is returned from its sidecar instead of bought
    again: units were checkpointed one at a time, but everything after the last unit was not
    checkpointed at all, and a spending stop there threw away the judge and the adjudication
    (fixed 09-07)."""
    ctx = ctx or {}
    uri, key = ctx.get("doc"), h(stage, model, effort, prompt)
    if uri is not None and key in REPLIES.get(uri, {}):
        return REPLIES[uri][key]
    error = ""
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
            if uri is not None:
                remember_reply(uri, key, reply)
            return reply
        except (SchemaError, ValueError, TypeError, KeyError, IndexError) as e:
            error = f"{type(e).__name__}: {e}"
            if attempt == 0:
                row = {"stage": stage, "category": "schema", "detail": error[:200], **ctx}
                RETRIES.append(row)
                record("retries.jsonl", row)
                prompt = prompt + f"\n\nYour previous reply did not fit the required shape ({error}). Reply again, in exactly the shape asked for."
    row = {"stage": stage, "category": "schema", "detail": error[:200], **ctx}
    REJECTIONS.append(row)
    record("rejections.jsonl", row)
    return None


print(f"models {LUNA} (derive), {TERRA} (judge and fold); key {'present' if KEY else 'MISSING'}")

# %%
# Block 3: test the connection before anything spends. One tiny call.
if __name__ == "__main__":
    if not KEY:
        print("no key: attach OPENAI_API_KEY under Add-ons > Secrets, then rerun this cell")
    else:
        ping = generate('Reply with exactly the JSON object {"ok": true}.', {"type": "object", "required": ["ok"]}, "ping", ctx={"doc": "connection test"})
        print(f"chat reply {ping}; {len(CALLS)} calls, ${spend():.5f}")

# %%
# Block 4: ids and small text helpers. Every id is a content hash, so re-deriving unchanged
# input mints the same ids.


def h(*parts):
    return hashlib.sha256("\n".join(str(p) for p in parts).encode("utf-8")).hexdigest()


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


def whole_word(needle, haystack):
    """Is `needle` in `haystack` as whole words (case as given)?"""
    start = 0
    while True:
        i = haystack.find(needle, start)
        if i < 0:
            return False
        before = haystack[i - 1] if i > 0 else " "
        after = haystack[i + len(needle)] if i + len(needle) < len(haystack) else " "
        if not is_word_char(before) and not is_word_char(after):
            return True
        start = i + 1


BOILERPLATE = ("front_matter", "license")   # never the work, whatever the document


def one_reading(doc):
    """True when setting the boilerplate aside leaves a single unit to read. Such a document has
    nothing to merge, so it takes the short path (ruling of 09-07)."""
    return sum(1 for u in doc["units"] if unit_kind(doc, u) not in BOILERPLATE) == 1


def boilerplate_of(doc):
    """(excluded, flags) for a one-reading document: the same shape triage returns, by rule and
    without a call, because with one unit to read there is no choice to make."""
    excluded = {}
    for u in doc["units"]:
        kind = unit_kind(doc, u)
        if kind in BOILERPLATE:
            excluded[kind] = f"{kind.replace('_', ' ')}: not the work itself"
    return excluded, []


def unit_kind(doc, unit):
    """The kind of most of the unit's characters, from its pieces; 'body' when it has none.
    Code never branches on it: it is shown to the judge that decides which kinds to read."""
    chars = {}
    for p in doc["pieces"]:
        if p["unit_id"] == unit["unit_id"]:
            chars[p["kind"]] = chars.get(p["kind"], 0) + p["end"] - p["start"]
    if not chars:
        return "body"
    return max(chars, key=chars.get)


def first_line(text):
    for line in text.split("\n"):
        if line.strip():
            return " ".join(line.split())[:120]
    return ""


def counts_text(counter):
    """'exact 6, normalised 2' from a dict of counts; 'none' when empty."""
    if not counter:
        return "none"
    return ", ".join(f"{k} {v}" for k, v in counter.items())

# %%
# Block 5: the quote gate.
#
# locate(unit_text, quote) says where the quote is inside the unit, or why it is not. The ways
# it can match, each named so the receipt says how many quotes needed which: `exact`, the
# substring as written; `normalised`, the same after both sides are normalised (one space for
# any whitespace, NFKC, straight quotes, one dash, a hyphenated line break closed, case
# folded), matched on a copy that maps every character back to its original offset;
# `unwrapped`, once the quotation marks the model wrapped it in come off, as whole words;
# `pieces`, a quote with an ellipsis, each piece verbatim and in order, the stored quote being
# the passage from the first piece to the last; `words`, the shortest passage holding at least
# WORDS_NEEDED of the quote's words in order, within three words of the quote's length, so a
# citation the model reworded at the edges still lands and the stored quote is the text's own
# words. Anything else is `paraphrase` (most of its words are there, in order, somewhere) or
# `not_found`. Stored offsets always index the original.

REPLACEMENTS = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "‒": "-", "−": "-", "‐": "-", "‑": "-", "­": "", " ": " "}
QUOTE_PAIRS = {"“": "”", '"': '"', "‘": "’", "'": "'"}
WORDS_NEEDED = 0.85                                  # the share of a quote's words a `words` match must hold, in order


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
    if cache is None:
        return normalised(text)
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


def find_after(text, needle, cache, at=0):
    """(start, end, how) of the first exact or normalised hit of `needle` at or after `at`."""
    needle = needle.strip()
    if not needle:
        return None, None, "empty"
    i = text.find(needle, at)
    if i >= 0:
        return i, i + len(needle), "exact"
    ntext, back = normalised_unit(text, cache)
    nneedle, _ = normalised(needle)
    i = ntext.find(nneedle, len([b for b in back if b < at])) if nneedle else -1
    if i >= 0:
        return back[i], back[i + len(nneedle) - 1] + 1, "normalised"
    return None, None, classify_miss(ntext, nneedle)


def classify_miss(ntext, nquote):
    """'paraphrase' when at least seven in ten of the quote's words appear in order, else
    'not_found'."""
    wanted, matched = words_only(nquote), 0
    for word in words_only(ntext):
        if matched < len(wanted) and word == wanted[matched]:
            matched += 1
    return "paraphrase" if matched >= 0.7 * max(1, len(wanted)) else "not_found"


def whole_word_hit(text, needle, cache):
    """The first place `needle` occurs as whole words, exact or normalised."""
    spans = surface_spans(text, needle, cache)
    return spans[0] if spans else (None, None)


def in_order(wanted, have):
    """How many of `wanted` occur in `have` in order (the longest common subsequence), with the
    first and last positions in `have` that take part."""
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
        if words[at][0] != wanted[0] and words[at][0] not in wanted:
            continue
        window = [w[0] for w in words[at:at + len(wanted) + 3]]
        matched, first, last, spanned = in_order(wanted, window)
        if matched >= needed and spanned == matched and (best is None or (matched, first - last) > (best[0], best[1] - best[2])):
            best = (matched, at + first, at + last)
    if best is None:
        return None, None
    return back[words[best[1]][1]], back[words[best[2]][2] - 1] + 1


QUOTE_SPAN_MAX = 400      # no match by any other path reached 300 on the run of 09-07


def locate(text, quote, cache=None):
    """(start, end, how) with offsets into `text`, or (None, None, why). A quote may skip words
    with an ellipsis, so its two halves can be found far apart; a span wider than QUOTE_SPAN_MAX
    is refused, because a quote that runs to a chapter does not show the fact it is cited for."""
    written = (quote or "").strip()
    start, end, how = find_after(text, written, cache)
    if start is not None:
        return start, end, how
    bare = unwrapped(written)
    if bare and bare != written:
        start, end = whole_word_hit(text, bare, cache)
        if start is not None:
            return start, end, "unwrapped"
    pieces = [p.strip() for p in bare.replace("…", "...").split("...") if p.strip()]
    if len(pieces) > 1:
        at, first, last = 0, None, None
        for piece in pieces:
            s, e, _ = find_after(text, piece, cache, at)
            if s is None:
                break
            first, last, at = (s if first is None else first), e, e
        else:
            if last - first > QUOTE_SPAN_MAX:
                return None, None, "span_too_wide"
            return first, last, "pieces"
    start, end = words_hit(text, bare, cache)
    if start is not None:
        return start, end, "words"
    return None, None, how


def sentence_at(text, start, end):
    """The sentence holding a span, so an alias can carry the words it was first read in."""
    left = max(text.rfind(mark, 0, start) for mark in (". ", "! ", "? ", "\n"))
    right = min((at for at in (text.find(mark, end) for mark in (". ", "! ", "? ", "\n")) if at >= 0), default=-1)
    return text[left + 1 if left >= 0 else 0:right + 1 if right >= 0 else len(text)].strip()


def occurrences(text, found):
    """Every offset at which the located string recurs verbatim, the first one included."""
    starts, i = [], text.find(found) if found else -1
    while i >= 0:
        starts.append(i)
        i = text.find(found, i + 1)
    return starts


def surface_spans(text, surface, cache=None):
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

# %%
# Block 6: the prompts. One triage per document (which kinds of unit to read), three per unit
# (entities with surface forms, salience and profile; facts with quotes; summary and cells),
# one judge over entity pairs, one fold, one adjudication per major. None of them knows what
# kind of document it is reading, and none sees another unit.

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

SUPPORT_SCHEMA = {"type": "object", "required": ["unsupported"], "properties": {"unsupported": {"type": "array"}}}
CORRECT_SCHEMA = {"type": "object", "required": ["corrections"], "properties": {"corrections": {"type": "array", "items": {
    "type": "object", "required": ["fact"], "properties": {
        "fact": {"type": ["integer", "string"]}, "subject": {"type": ["string", "null"]},
        "predicate": {"type": ["string", "null"]}, "object": {"type": ["string", "null"]},
        "qualifiers": {"type": ["string", "null"]}}}}}}
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


def correct_prompt(facts):
    return f"""Below are statements one document makes, numbered, each with the passage it rests on. A check found that the passage does not state the statement as it is written. The passage is fixed and is not in question; the statement is what may be wrong.

For each one you can, restate it so that its own passage states it: give "subject", "predicate" (lowercase_snake_case, present tense) and "object" that the passage does carry, with "qualifiers" or null. {QUOTE_RULE}.

Leave a statement out of your answer entirely when its passage carries no durable fact at all. A statement that cannot be corrected is dropped, and that is the right outcome: a vague restatement that merely mentions the subject is worse than dropping it. Never restate a fact as a remark about the passage or about the document.

Return JSON {{"corrections": [{{"fact", "subject", "predicate", "object", "qualifiers"}}]}}

STATEMENTS:
{chr(10).join(facts)}"""


def fold_prompt(what, children, limit):
    return f"""Below are the records of {what}, in reading order. Write one summary of the whole in at most {limit} words: what it is, who and what matter most, and how it unfolds from beginning to end. Ground every statement only in these records; use no outside knowledge and no name that does not appear below.

Return JSON {{"summary": "..."}}

RECORDS:
{chr(10).join(children)}"""


def support_prompt(facts):
    return f"""Below are statements one document makes, numbered, each with the passage it rests on.

Return JSON {{"unsupported": [numbers]}}: the numbers of the facts whose own passage does not state them (a loose citation that says something else, or only part of it).

{QUOTE_RULE}. A bare value is the usual near miss: a number quoted without the heading or label that names what it measures carries the figure but not the claim, and does not state it. Only call a fact unsupported when its passage genuinely does not carry the claim. Return an empty list when every passage states its fact.

FACTS:
{chr(10).join(facts)}"""


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

# %%
# Block 7: derive one unit. Three calls, every gate applied by code, and one record back with
# everything the model said and everything code kept or rejected. Offsets are document
# offsets: the unit's start is added to every span. A span is one mention: when two entities
# claim the same occurrence, the first one listed keeps it. Nothing from another unit is seen.


def derive_unit(doc, unit, ctx, light=False):
    text, base, cache = unit["text"], unit["start"], {}
    rec = {"unit_id": unit["unit_id"], "position": unit["position"], "label": unit["label"], "kind": unit["kind"],
           "entities": [], "dropped_entities": [], "mentions": [], "facts": [], "rejected_facts": [], "profile": [],
           "summary": None, "cells": [], "cells_unlisted": 0, "shared_spans": 0, "ambiguous_voice": 0, "split_by_voice": 0, "empty": False}

    # 1. entities, each surface form located; a form that is not in the unit is dropped
    reply = generate(entity_prompt(unit), ENTITY_SCHEMA, "entities", ctx=ctx)
    claimed = {}                                  # (start, end) -> the entity that got the span
    for e in (reply or {}).get("entities", []):
        name = " ".join(e["name"].split())
        if not name or name in {x["name"] for x in rec["entities"]}:
            continue
        forms, spans, found_any = [], [], False
        for surface in dict.fromkeys([s for s in e["surface_forms"] if isinstance(s, str)] + [name]):
            all_hits = surface_spans(text, surface, cache)
            found_any = found_any or bool(all_hits)
            free_hits = [span for span in all_hits if span not in claimed and span not in spans]
            rec["shared_spans"] += sum(1 for span in all_hits if span in claimed)
            if free_hits:
                forms.append(surface)
                spans.extend(free_hits)
        if not spans:
            why = "every span already claimed by an earlier entity" if found_any else "no surface form in unit"
            rec["dropped_entities"].append({"name": name, "why": why, "category": "span_claimed" if found_any else "no_surface_form",
                                            "forms": e["surface_forms"][:5]})
            continue
        for span in spans:
            claimed[span] = name
        rec["entities"].append({"name": name, "named": bool(e["named"]), "kind": str(e["kind"]).lower(),
                                "major": str(e.get("salience") or "").strip().casefold() == "major", "forms": forms, "mentions": len(spans)})
        for start, end in sorted(spans):
            rec["mentions"].append({"mention_id": h(unit["unit_id"], base + start, base + end), "entity": name, "unit_id": unit["unit_id"],
                                    "start": base + start, "end": base + end, "surface": text[start:end], "resolved_by": "surface"})
        profile = e.get("profile") if isinstance(e.get("profile"), dict) else {}
        for attribute, value in profile.items():
            if value not in (None, "", "null", "unknown"):
                rec["profile"].append({"entity": name, "attribute": str(attribute), "value": str(value), "from_unit": unit["unit_id"]})
    names = [e["name"] for e in rec["entities"]]
    if not names:
        rec["empty"] = True
        return rec

    # 2. facts, each quote located inside the unit; a subject or object written loosely
    #    (case, a leading article) is the listed entity, unless two listed names collide
    majors = [e["name"] for e in rec["entities"] if e["major"]]
    def ask_facts():
        return generate(fact_prompt(unit, names, majors), FACT_SCHEMA, "facts", ctx=ctx)

    def ask_cells():
        return generate(cells_prompt(unit, majors), CELLS_SCHEMA, "cells", ctx=ctx)

    # both take the entity list and nothing else, so on the one-reading path they are asked
    # together; a many-unit document already runs its units WORKERS at a time
    reply, cells_reply = in_parallel(call_thunk, [ask_facts, ask_cells]) if light else (ask_facts(), None)
    loose_count = {}
    for name in names:
        loose_count[loose_name(name)] = loose_count.get(loose_name(name), 0) + 1
    listed = {loose_name(name): name for name in names if loose_count[loose_name(name)] == 1}
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
            rejection["category"] = "ambiguous_subject" if loose_name(written) in loose_count else "unlisted_subject"
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
                rec["ambiguous_voice"] += len(voices) > 1  # the same words in two voices: no voice is claimed
                rec["facts"].append({"fact_id": h(unit["unit_id"], subject, predicate, obj, base + s0, base + e0),
                                     "subject": subject, "predicate": predicate, "object": obj, "object_is_entity": obj in names,
                                     "qualifiers": f.get("qualifiers") or None, "unit_id": unit["unit_id"], "quote": quote,
                                     "quote_start": base + s0, "quote_end": base + e0, "matched_by": how,
                                     "valid_from": stated_date(f.get("valid_from"), quote), "valid_to": stated_date(f.get("valid_to"), quote),
                                     "author": None if len(voices) > 1 else author,
                                     "voice_ambiguous": len(voices) > 1, "tier": LUNA})
                stored += 1
            rec["split_by_voice"] += stored > 1
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
            elif c["text"].strip():
                rec["cells_unlisted"] += 1
    rec["empty"] = not rec["facts"] and not rec["cells"]
    return rec


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


def voice_spans(doc, base, text, start, end):
    """A quote may not span a change of speaker (decision 46): the located span cut where the
    speaker changes, each cut trimmed of whitespace, as offsets into the unit. A boundary
    between two pieces of one author is not a change of speaker and is not a cut; cutting
    there split a quote whose halves then collided on one author, so only the first was
    stored and the fact could lose the words that stated it (fixed 09-07)."""
    marks = sorted(pp["start"] for pp in doc["pieces"])
    speaker = {pp["start"]: pp.get("author") for pp in doc["pieces"]}
    inside = []
    for k, at in enumerate(marks):
        if k and start < at - base < end and speaker[at] != speaker[marks[k - 1]]:
            inside.append(at - base)
    cuts, spans = [start] + inside + [end], []
    for k in range(len(cuts) - 1):
        s0, e0 = cuts[k], cuts[k + 1]
        while s0 < e0 and text[s0].isspace():
            s0 += 1
        while e0 > s0 and text[e0 - 1].isspace():
            e0 -= 1
        if e0 > s0:
            spans.append((s0, e0))
    return spans


def author_at(doc, offset):
    """The voice of an offset: the author of the piece holding it, else the document's."""
    for p in doc["pieces"]:
        if p["start"] <= offset < p["end"]:
            return p["author"] or doc.get("author")
    return doc.get("author")

# %%
# Block 8: reconcile the document's unit-local entities into document entities, bottom up, at
# the end, as the 09-02 demo did.
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


def by_priority(item):
    return (-item[0], -item[1])


def best_name(counts):
    """The most used name, the longest on a tie."""
    best = None
    for name, n in counts.items():
        if best is None or (n, len(name)) > (counts[best], len(best)):
            best = name
    return best


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

    def same(self, a, b):
        return self.find(a) == self.find(b)


def ledger_row(locals_, a, b, verdict, how, evidence):
    return {"a": locals_[a]["name"], "a_unit": locals_[a]["ui"], "b": locals_[b]["name"], "b_unit": locals_[b]["ui"],
            "verdict": verdict, "how": how, "evidence": evidence}


def cluster_members(locals_, clusters):
    """The locals of each cluster, by its root."""
    groups = {}
    for l in locals_:
        groups.setdefault(clusters.find(l["id"]), []).append(l)
    return groups


def ineligible(members, ra, rb, ruled_apart):
    """Two clusters are never paired when they hold a local from one unit (that unit already
    listed them as two things) or a pair the judge ruled different (decisions 44 and 51)."""
    here, there = members.get(ra, []), members.get(rb, [])
    if {x["ui"] for x in here} & {y["ui"] for y in there}:
        return True
    for x in here:
        for y in there:
            if frozenset((x["id"], y["id"])) in ruled_apart:
                return True
    return False


def constraints_first(batch, verdicts):
    """One batch as (n, ra, rb, verdict, reason), the "different" verdicts first. A "different"
    is a constraint and a "same" is a merge, so applying the constraints first makes the batch
    order-independent: in batch order, on the last look, two earlier "same" verdicts could unite
    the two sides that a later "different" ruled apart (fixed 09-07)."""
    rank, order = {"different": 0, "same": 1, "unsure": 2}, []
    for n, (ra, rb) in enumerate(batch):
        verdict, reason = verdicts.get(n, ("unsure", "no verdict returned"))
        order.append((rank.get(verdict, 2), n, ra, rb, verdict, reason))
    order.sort()
    return [(n, ra, rb, verdict, reason) for _, n, ra, rb, verdict, reason in order]


def pair_up(locals_, clusters, ruled_apart, seen_pairs=None):
    """One round of the clustering, Justin's rule: every entity still in consideration is scored
    against every other, the pairs at or above SIMILAR_ENOUGH are filtered by eligibility, and
    the strongest is taken with both its sides leaving consideration, until no eligible pair
    remains. (the pairs taken, how many were eligible).

    A pair already judged and not merged is not a candidate, so its slot goes to the next-best
    one; skipping it after the round was chosen let two unsure pairs block their four entities
    from ever being compared to each other, and the rounds then ended with nothing fresh
    (fixed 09-07)."""
    seen_pairs = seen_pairs or set()
    members, scored = cluster_members(locals_, clusters), []
    for a in locals_:
        for b in locals_[:a["id"]]:
            ra, rb = clusters.find(a["id"]), clusters.find(b["id"])
            if ra == rb or not (a["major"] or b["major"]):
                continue
            reason = candidate_reason(a, b)
            if reason is None or anchored(a, b) or anchored(b, a):
                continue
            scores = score_pair(a, b, reason)
            if scores[3] < SIMILAR_ENOUGH or ineligible(members, ra, rb, ruled_apart):
                continue
            if frozenset((ra, rb)) in seen_pairs:      # judged in an earlier round and not merged
                continue
            scored.append((TIER[reason], scores[3], b["id"], a["id"], reason, scores))
    scored.sort(key=by_priority)
    taken, queue = set(), []
    for entry in scored:
        tier, combined, i, j, reason, scores = entry
        ra, rb = clusters.find(i), clusters.find(j)
        if ra in taken or rb in taken:             # both sides leave consideration for this round
            continue
        taken.add(ra)
        taken.add(rb)
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
    ({pair number: (verdict, reason)} in batch order, how many numbers were out of range). The
    prompt numbers dossiers and pairs separately, so a model answering by the dossier writes to
    a key nothing reads and the pair it judged falls through to the default (fixed 09-07)."""
    roots = sorted({r for pair in batch for r in pair})
    number = {r: n for n, r in enumerate(roots, 1)}
    members = {r: [l for l in locals_ if clusters.find(l["id"]) == r] for r in roots}
    dossiers = "\n\n".join(f"[{number[r]}]\n{dossier(members[r])}" for r in roots)
    pairs = "\n".join(f"PAIR {n}: [{number[a]}] and [{number[b]}]" for n, (a, b) in enumerate(batch, 1))
    reply = generate(JUDGE_PROMPT + "\nDOSSIERS\n" + dossiers + "\n\nPAIRS\n" + pairs, JUDGE_SCHEMA, "judge", model=TERRA, effort="medium", ctx=ctx)
    verdicts, misnumbered = {}, 0
    for v in (reply or {}).get("verdicts", []):
        numbered = valid_sources([v.get("pair")], len(batch))
        if not numbered:
            misnumbered += 1
            continue
        verdicts[numbered[0] - 1] = (v["verdict"], v.get("reason", ""))
    return verdicts, misnumbered


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
        key = (norm(l["name"]), l["kind"])
        first = first_named.get(key)
        if first is None:
            first_named[key] = l
        elif first["is_a"] and l["is_a"] and not set(first["is_a"]) & set(l["is_a"]):
            ledger.append(ledger_row(locals_, first["id"], l["id"], "unsure", "same_name_conflicting_is_a",
                                     f"both named {l['name']!r} but {first['is_a'][:2]} against {l['is_a'][:2]}: the judge decides"))
        else:
            clusters.unite(first["id"], l["id"])
            ledger.append(ledger_row(locals_, first["id"], l["id"], "same", "same_name", f"both named {l['name']!r}, both {l['kind']}"))

    # 2. the judge over the queue: same unites, different stays apart, unsure waits for the last
    #    look. A union that would join a pair already ruled different is refused.
    apart, deferred, judged, calls, rounds, queued, misnumbered = [], [], 0, 0, 0, 0, 0

    def decide(batch, final):
        nonlocal judged, calls, misnumbered
        verdicts, bad = judge(batch, locals_, clusters, ctx)
        members = cluster_members(locals_, clusters)
        calls += 1
        judged += len(batch)
        misnumbered += bad
        for n, ra, rb, verdict, reason in constraints_first(batch, verdicts):
            how = "judged again" if final else "judged"
            if verdict == "same" and ineligible(members, clusters.find(ra), clusters.find(rb), ruled_apart):
                # a guard the pairing rules should make unreachable: one pair to an entity a round
                how, reason = "refused", reason + "; would join locals a unit kept apart or the judge ruled different"
                apart.append((ra, rb))
                ruled_apart.add(frozenset((ra, rb)))
            elif verdict == "same":
                clusters.unite(ra, rb)
                members = cluster_members(locals_, clusters)
            elif verdict == "different" or final:
                apart.append((ra, rb))
                ruled_apart.add(frozenset((ra, rb)))
            else:
                deferred.append((ra, rb))
            ledger.append(ledger_row(locals_, ra, rb, verdict, how, reason))

    def batches(pairs, final):
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
                if watch and calls % 5 == 0:
                    print(f"    judge call {calls}: {k} of {len(pairs)} pairs seen, ${spend():.2f} spent this session")

    # 3. round after round, each pairing off the entities still in consideration; the merges of
    #    one round cannot conflict, since no entity is in two of its pairs. Stop when a round
    #    queues nothing, which is when nothing eligible is left above the threshold.
    seen_pairs = set()
    while True:
        queue, eligible = pair_up(locals_, clusters, ruled_apart, seen_pairs)
        fresh = []
        for tier, combined, i, j, reason, (name, cooc, profile, _) in queue:
            seen_pairs.add(frozenset((clusters.find(i), clusters.find(j))))
            fresh.append((i, j))
            candidates.append({"a": locals_[i]["name"], "a_unit": locals_[i]["ui"], "b": locals_[j]["name"], "b_unit": locals_[j]["ui"],
                               "round": rounds + 1, "tier": tier, "reason": reason, "name_score": round(name, 3),
                               "cooc_score": round(cooc, 3), "profile_score": round(profile, 3), "combined": round(combined, 3)})
        if not fresh:
            break
        rounds, queued = rounds + 1, queued + len(fresh)
        if watch:
            print(f"judge round {rounds}: {eligible} eligible pairs, {len(fresh)} taken (one to an entity), {PAIRS_PER_CALL} a call")
        batches(fresh, final=False)

    # 4. the deferred pairs' last look against the finished clusters
    last_look, deferred = list(deferred), []
    batches(last_look, final=True)
    stats = {"locals": len(locals_), "candidate_pairs": queued, "judged_pairs": judged, "judge_calls": calls,
             "judge_rounds": rounds, "judge_misnumbered": misnumbered}
    return cluster_entities(locals_, clusters), ledger, candidates, stats


def cluster_entities(locals_, clusters):
    """One document entity per cluster: its canonical name (the most used proper name, the
    longest on a tie), its names, forms, units and facts, and where each form first appeared."""
    groups = {}
    for l in locals_:
        groups.setdefault(clusters.find(l["id"]), []).append(l)
    entities = []
    for members in groups.values():
        named = [l for l in members if l["named"]] or members
        counts = {}
        for l in named:
            counts[l["name"]] = counts.get(l["name"], 0) + 1
        first_unit_of, unit_ids = {}, []
        for l in members:
            for form in l["forms"]:
                first_unit_of.setdefault(form, l["unit_id"])
            if l["unit_id"] not in unit_ids:
                unit_ids.append(l["unit_id"])
        kind_counts = {}
        for l in members:
            kind_counts[l["kind"]] = kind_counts.get(l["kind"], 0) + 1
        kinds_read = [kind for _, kind in sorted((-n, kind) for kind, n in kind_counts.items())]
        entities.append({"name": best_name(counts), "kinds": kinds_read, "named": any(l["named"] for l in members),
                         "unit_major": any(l["major"] for l in members),      # major in some unit: never taken back
                         "units": sorted({l["ui"] for l in members}), "unit_ids": unit_ids, "first_unit": unit_ids[0],
                         "names": sorted({l["name"] for l in members}), "surfaces": sorted({s for l in members for s in l["surfaces"]}),
                         "first_unit_of": first_unit_of, "members": [(l["ui"], l["name"]) for l in members],
                         "n_facts": sum(l["n_facts"] for l in members), "is_a": sorted({x for l in members for x in l["is_a"]})})
    return entities

# %%
# Block 9: fold the document.
#
# The abstract is a summary of the unit summaries, asked for in at most half their words and
# no more than 400, and it stands as written (decision 65). Salience is read from the abstract:
# named there, as whole words, is major; with no abstract, two units or two facts decide. A
# major seen in fewer units and with fewer facts than the numbers below is demoted to minor.
# Majors get a dossier and their own abstract.
# Nothing demotes (ruling of 09-07). Promotion is: a unit called it major, the abstract names it,
# or it carries a proper name. Bare unit and fact counts do NOT promote -- an unnamed thing that
# recurs is still scenery, and minting nodes for scenery is what R5 refused.


def fold(what, children, ctx, stage="fold"):
    """The summary of these records, and the length it was asked for. The summary stands as
    written: the prompt asks for the records' own names and a length, and neither is enforced
    after the fact (decision 65). None only when the model did not answer."""
    limit = min(400, max(20, sum(word_count(c) for c in children) // 2))
    reply = generate(fold_prompt(what, children, limit), FOLD_SCHEMA, stage, model=TERRA, ctx=ctx)
    if not reply:
        return None, limit
    return " ".join(reply["summary"].split()), limit


def salience_order(item):
    return (not item[0], -item[1], -item[2])


def fold_document(records, entities, ctx, light=False):
    out = {"abstract": None, "majors": [], "minors": [], "dossiers": [], "entity_abstracts": [],
           "demoted": [], "by_abstract_only": 0, "cells_of": {}}
    work = [r for r in records if r["summary"]]
    summaries = [f"[{r['label']}] {r['summary']}" for r in work]
    if len(summaries) == 1:                       # one summarised unit: its summary is the abstract, no call
        text, limit, tier = work[0]["summary"], None, LUNA
    elif summaries:
        text, limit = fold("one document", summaries, ctx)
        tier = TERRA
    else:
        text, limit, tier = None, None, None
    if text:
        out["abstract"] = {"text": text, "children_hash": h(*summaries), "limit": limit, "tier": tier}

    # salience is a union of promotions and nothing is ever demoted (ruling of 09-07): an entity
    # is a document-major if anything made it one -- a unit called it major, the abstract names
    # it, it carries a proper name, or it clears the thresholds. Being in the abstract used to be
    # the only route, which made the abstract's word limit the document's entity budget.
    abstract, ranked = (text or "").casefold(), []
    for e in entities:
        in_abstract = any(whole_word(s, abstract) for s in e["surfaces"] if len(s) >= 2) if text else None
        major = bool(in_abstract) or e["unit_major"] or e["named"]
        ranked.append((major, len(e["units"]), e["n_facts"], in_abstract, e))
    ranked.sort(key=salience_order)
    out["by_abstract_only"] = sum(1 for major, n_units, n_facts, in_abstract, e in ranked if in_abstract)
    for major, n_units, n_facts, in_abstract, e in ranked:
        e["major"] = major
        e["rank"] = {"in_abstract": in_abstract, "unit_major": e["unit_major"], "named": e["named"],
                     "units": n_units, "facts": n_facts, "no_abstract": False}
        (out["majors"] if e["major"] else out["minors"]).append(e)

    # dossiers and per-entity abstracts for the majors, keyed by index (two clusters may share a name)
    for i, e in enumerate(entities):
        e["index"] = i
    member_of = {(ui, local_name): e["index"] for e in entities for ui, local_name in e["members"]}
    cells_of, facts_of = {}, {}
    for r in records:
        for c in r["cells"]:
            if member_of.get((r["position"], c["entity"])) is not None:
                cells_of.setdefault(member_of[(r["position"], c["entity"])], []).append(f"[{r['label']}] {c['text']}")
        for f in r["facts"]:
            if member_of.get((r["position"], f["subject"])) is not None:
                facts_of.setdefault(member_of[(r["position"], f["subject"])], []).append(fact_text(f))
    out["cells_of"] = cells_of
    for e in out["majors"]:
        facts, cells = list(dict.fromkeys(facts_of.get(e["index"], []))), cells_of.get(e["index"], [])
        others = [n for n in e["names"] if n != e["name"]]
        text = "\n".join([f"name: {e['name']}", f"also: {', '.join(others)[:300]}", f"kinds: {', '.join(e['kinds'])}",
                          f"is: {', '.join(e['is_a'][:6])}", f"facts: {'; '.join(facts[:20])}", f"cells: {' '.join(cells)[:1500]}"])
        out["dossiers"].append({"entity": e["name"], "name": e["name"], "first_unit": e["first_unit"], "kinds": e["kinds"],
                                "first_mention": e["first_mention"], "text": text, "children": facts + cells})
    def abstract_of(pair):
        """(text, kind, tier); two records or fewer stand as the abstract without a call, and
        keep the kind their units read most often."""
        e, d = pair
        if light:                     # one reading: the entity's own cell is its abstract, no call
            cells = cells_of.get(e["index"], [])
            if not cells and len(d["children"]) > 2:
                # its children are facts, and a run of predicate strings is not a summary of
                # anything; better no abstract than "is_a language supports type_hints" (09-07)
                return None, None, LUNA
            said = " ".join(c.split("] ", 1)[-1] for c in (cells or d["children"]))
            return said or None, None, LUNA
        if len(d["children"]) <= 2:
            return " ".join(c.split("] ", 1)[-1] for c in d["children"]), None, LUNA
        limit = min(400, max(20, sum(word_count(c) for c in d["children"]) // 2))
        reply = generate(entity_abstract_prompt(e["name"], e["kinds"], d["children"], limit),
                         ENTITY_ABSTRACT_SCHEMA, "entity_abstract", model=TERRA, ctx={**ctx, "entity": e["name"]})
        if not reply:
            return None, None, TERRA
        return " ".join(reply["summary"].split()), str(reply["kind"]).strip().lower() or None, TERRA

    # an entity with nothing to summarise, no facts and no cells, is not a major (decision 52):
    # it falls to minor and its facts ride into the majors, as any minor's do
    pairs = [(e, d) for e, d in zip(out["majors"], out["dossiers"]) if d["children"]]
    for (e, d) in [(e, d) for e, d in zip(out["majors"], out["dossiers"]) if not d["children"]]:
        e["major"] = False
        e["rank"]["no_abstract"] = True
        out["minors"].append(e)
        out["demoted"].append(e["name"])
    for (e, d), (text, kind, tier) in zip(pairs, in_parallel(abstract_of, pairs)):
        e["kind"] = kind or e["kinds"][0]     # one kind for the merged entity; the units' most common if no call
        if text:
            out["entity_abstracts"].append({"entity": e["name"], "name": e["name"], "first_unit": e["first_unit"], "kinds": e["kinds"],
                                            "first_mention": e["first_mention"], "text": text, "children_hash": h(*d["children"]), "tier": tier})
    out["majors"] = [e for e, d in pairs]
    out["dossiers"] = [d for e, d in pairs]
    return out

# %%
# Block 10: the package. One JSONL file per document mirroring the raw layout, every line one
# record with a "record" field, ending in a completion record whose input_hash says which
# extractor output it came from. Minors have no node. A fact lands on the major that is its
# subject (forward), or on the major a minor's fact points at (inverse); a minor's own facts
# ride into the major it is tied to (about), under the first fact that ties them; a fact of a
# minor tied to no major is not stored.


def package_path(doc):
    """Every document keeps its own folder, named after its file: the package, the unit sidecar
    and the graph sit together, under the corpus the document came from."""
    parts = doc["source_uri"].split("/")
    stem = Path(parts[-1]).stem
    return OUT / (parts[-2] if len(parts) > 1 else "misc") / stem / (stem + ".jsonl")


def sidecar_path(doc):
    """Unit records checkpointed while a document is in flight."""
    return package_path(doc).with_suffix(".units.jsonl")


def derive_signature():
    """What a checkpointed unit depends on, as one string: the words the derive path will send,
    the models it will send them to, and the constant that gates which quotes it keeps. INGESTOR
    was the whole label, and a hand-typed version string does not move when the code under it
    does -- it stayed at 0.7 across eight commits that changed this path (A12; fixed 09-07)."""
    sample = {"label": "L", "text": "T"}
    return h(INGESTOR, LUNA, TERRA, QUOTE_SPAN_MAX,
             entity_prompt(sample), fact_prompt(sample, ["A"], ["A"]), cells_prompt(sample, ["A"]))


def input_hash(doc):
    return h(doc["doc_id"], *[u["unit_id"] for u in doc["units"]], derive_signature())


def first_mention(records, entity):
    """Where the entity's chosen name is first mentioned in the document; its first mention under
    any of its names when that name was never a surface, else its first unit (decision 48)."""
    wanted, mine, any_mine = norm(entity["name"]), [], []
    members = {(ui, local_name) for ui, local_name in entity["members"]}
    for r in records:
        for m in r["mentions"]:
            if (r["position"], m["entity"]) not in members:
                continue
            any_mine.append(m["start"])
            if norm(m["surface"]) == wanted:
                mine.append(m["start"])
    if mine:
        return str(min(mine))
    if any_mine:
        return str(min(any_mine))
    return entity["first_unit"]


def stamp_first_mention(records, entities):
    """Every entity carries where its name first appears, which is what its node id is built on."""
    for e in entities:
        e["first_mention"] = first_mention(records, e)


def entity_key(entity):
    """What names one document entity: the moniker and where the document first mentions it."""
    return entity["name"], entity["first_mention"]


def node_id_of(doc, entity):
    return h(doc["doc_id"], *entity_key(entity))


def predicate_census(records):
    """Every raw predicate the document used, with count and samples, for the merge across documents."""
    census = {}
    for r in records:
        for f in r["facts"]:
            c = census.setdefault(f["predicate"], {"count": 0, "objects": [], "object_is_entity": 0})
            c["count"] += 1
            c["object_is_entity"] += f["object_is_entity"]
            if f["object"] not in c["objects"] and len(c["objects"]) < 6:
                c["objects"].append(f["object"])
    return census


def landings(records, folded):
    """Where every kept fact lands: {major index: [(fact, direction, unit label, stored id, the
    fact it rides under or None)]}."""
    entity_of = {(ui, local_name): e["index"] for e in folded["majors"] + folded["minors"] for ui, local_name in e["members"]}
    major = {e["index"]: e for e in folded["majors"]}
    own_of = {}                                   # a minor's facts about itself, in reading order
    for r in records:
        for f in r["facts"]:
            subject = entity_of.get((r["position"], f["subject"]))
            obj = entity_of.get((r["position"], f["object"])) if f["object_is_entity"] else None
            if subject is not None and subject not in major and obj not in major:
                own_of.setdefault(subject, []).append((f, r["label"]))
    landed, attached = {index: [] for index in major}, set()
    for r in records:
        for f in r["facts"]:
            subject = entity_of.get((r["position"], f["subject"]))
            obj = entity_of.get((r["position"], f["object"])) if f["object_is_entity"] else None
            if subject in major:
                node, direction, minor = subject, "forward", obj if obj is not None and obj not in major else None
            elif obj in major:
                node, direction, minor = obj, "inverse", subject
            else:
                continue
            landed[node].append((f, direction, r["label"], f["fact_id"], None))
            if minor is not None and (node, minor) not in attached:
                attached.add((node, minor))
                for g, label in own_of.get(minor, []):
                    landed[node].append((g, "about", label, h(g["fact_id"], "rides into", *entity_key(major[node])), f["fact_id"]))
    return landed


def write_package(doc, records, entities, folded, adjudicated, ledger, candidates, excluded, stats,
                  flagged=None, corrections=None):
    path = package_path(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    scope, written_at, doc_node = doc["doc_id"], datetime.now(timezone.utc).isoformat(timespec="seconds"), h(doc["doc_id"], "document")
    lines = [{"record": "document", "doc_id": doc["doc_id"], "source_uri": doc["source_uri"], "sha256": doc["sha256"], "title": doc["title"],
              "author": doc["author"], "source_class": doc["source_class"], "ingested_at": doc["ingested_at"], "occurred_at": doc["occurred_at"],
              "loader": doc["loader"], "flags": doc.get("flags", []), "text_length": len(doc["text"])}]
    lines += [{"record": "unit", **u} for u in doc["units"]] + [{"record": "piece", **p} for p in doc["pieces"]]
    lines.append({"record": "node", "node_id": doc_node, "name": doc.get("title") or doc["source_uri"], "kind": "document",
                  "created_from_unit": doc["units"][0]["unit_id"] if doc["units"] else None, "provenance": {"ingestor": INGESTOR}})

    # the sentence each surface form was first read in, so an alias carries its own evidence
    first_words = {}
    for r in records:
        for m in r["mentions"]:
            key = (m["unit_id"], norm(m["surface"]))
            if key not in first_words:
                first_words[key] = sentence_at(doc["text"], m["start"], m["end"])

    # nodes, aliases and edges for the majors; the map from a unit-local name to its node
    node_of, position_of, minted = {}, {u["unit_id"]: u["position"] for u in doc["units"]}, {}
    for e in entities:
        nid = node_id_of(doc, e) if e["major"] else None
        if nid is not None and nid in minted:       # two entities the judge kept apart may never share a node
            raise ValueError(f"{doc['source_uri']}: {e['name']!r} and {minted[nid]!r} would share one node id")
        if nid is not None:
            minted[nid] = e["name"]
        for ui, local_name in e["members"]:
            node_of[(ui, local_name)] = nid
        if not e["major"]:
            continue
        lines.append({"record": "node", "node_id": nid, "name": e["name"], "kind": e.get("kind") or e["kinds"][0],
                      "created_from_unit": min(e["unit_ids"], key=position_of.get),
                      "named": e["named"],       # a proper name somewhere in the document: Step 2's both-named rule
                      "provenance": {"ingestor": INGESTOR, "salience": e["rank"], "names": e["names"][:12]}})
        for form, uid in e["first_unit_of"].items():
            lines.append({"record": "alias", "alias": form, "node_id": nid, "first_seen_unit": uid,
                          "evidence_quote": first_words.get((uid, norm(form)))})
        lines.append({"record": "edge", "predicate": "appears_in", "subject": nid, "object": doc_node, "units": e["unit_ids"]})
    for u in doc["units"]:
        lines.append({"record": "edge", "predicate": "has_unit", "subject": doc_node, "object": u["unit_id"], "position": u["position"]})

    # per unit: mentions, profiles, the summary cell, the entity cells
    for r in records:
        for m in r["mentions"]:
            lines.append({"record": "mention", "mention_id": m["mention_id"], "node_id": node_of.get((r["position"], m["entity"])),
                          "unit_id": m["unit_id"], "start": m["start"], "end": m["end"], "surface": m["surface"], "resolved_by": m["resolved_by"]})
        seen_profile = set()
        for p in r["profile"]:
            nid = node_of.get((r["position"], p["entity"]))
            if nid and (nid, p["attribute"], p["value"]) not in seen_profile:
                seen_profile.add((nid, p["attribute"], p["value"]))
                lines.append({"record": "profile", "node_id": nid, "attribute": p["attribute"], "value": p["value"], "from_unit": p["from_unit"]})
        if r["summary"]:
            lines.append({"record": "cell", "cell_id": h(doc_node, r["unit_id"]), "node_id": doc_node, "unit_id": r["unit_id"], "scope_id": scope,
                          "text": r["summary"], "tier": LUNA, "provenance": {"ingestor": INGESTOR, "kind": "unit_summary"}})
        cells_by_node = {}
        for c in r["cells"]:
            if node_of.get((r["position"], c["entity"])):
                cells_by_node.setdefault(node_of[(r["position"], c["entity"])], []).append(c)
        for nid, cells in cells_by_node.items():
            lines.append({"record": "cell", "cell_id": h(nid, r["unit_id"]), "node_id": nid, "unit_id": r["unit_id"], "scope_id": scope,
                          "text": " ".join(c["text"] for c in cells), "tier": LUNA,
                          "provenance": {"ingestor": INGESTOR, "entity_names": [c["entity"] for c in cells]}})

    # what the correction pass will dump, known before anything points at it: an adjudicated
    # item, an attribute or a contradiction may not cite a fact this package will not carry (P2)
    flagged, corrections = flagged or {}, corrections or {}
    dumped_ids, stranded = set(flagged) - set(corrections), 0

    # the adjudicated record of each major, its predicates as the model wrote them
    for e in folded["majors"]:
        nid, result = node_id_of(doc, e), adjudicated.get(e["index"], {"facts": [], "attributes": [], "contradictions": []})
        for item in result["facts"]:
            sources = [i for i in item["from_facts"] if i not in dumped_ids]
            if not sources:                              # every fact it rested on was dumped (P2)
                stranded += 1
                continue
            lines.append({"record": "adjudicated_fact", "node_id": nid, "predicate": snake_case(item["predicate"]) or "related_to",
                          "object": item["object"], "qualifiers": item.get("qualifiers") or None, "from_facts": sources, "tier": TERRA})
        for item in result["attributes"]:
            sources = [i for i in item["from_facts"] if i not in dumped_ids]
            if not sources:
                stranded += 1
                continue
            lines.append({"record": "attribute", "node_id": nid, "attribute": item["attribute"], "value": item["value"], "from_facts": sources, "tier": TERRA})
        for item in result["contradictions"]:
            # the document's own resolution, recorded here and not on the fact: both facts stay
            # active, and the global layer sees that this document said both things (R4, 09-07)
            sources = [i for i in item["from_facts"] if i not in dumped_ids]
            if len(sources) < 2:            # with a source dumped there is nothing left to disagree (P2)
                stranded += 1
                continue
            holds = item.get("holds_fact") if item.get("holds_fact") in sources else None
            lines.append({"record": "contradiction", "node_id": nid, "note": item["note"], "from_facts": sources,
                          "holds": holds, "because": (item.get("because") or None) if holds else None})

    # the document level: abstracts, dossiers, the ledger, the candidates
    if folded["abstract"]:
        lines.append({"record": "abstract", "node_id": doc_node, "scope_id": scope, "text": folded["abstract"]["text"],
                      "children_hash": folded["abstract"]["children_hash"], "tier": folded["abstract"]["tier"], "updated_at": written_at})
    for a in folded["entity_abstracts"]:
        lines.append({"record": "abstract", "node_id": node_id_of(doc, a),
                      "scope_id": scope, "text": a["text"], "children_hash": a["children_hash"], "tier": a["tier"], "updated_at": written_at})
    for d in folded["dossiers"]:
        lines.append({"record": "dossier", "node_id": node_id_of(doc, d),
                      "text": d["text"]})
    lines += [{"record": "ledger", **entry} for entry in ledger] + [{"record": "candidate", **entry} for entry in candidates]

    # facts, each under the major it lands on. A fact whose passage does not state it is written
    # only if it was corrected against that passage; otherwise it is dumped and recorded as a
    # rejection, never written with a flag (R3, ruling of 09-07)
    when_of = {u["unit_id"]: (u.get("occurred_at"), u.get("occurred_until")) for u in doc["units"]}
    landed, landed_ids, riding = landings(records, folded), set(), 0
    dumped = []
    for e in folded["majors"]:
        nid = node_id_of(doc, e)
        for f, direction, label, stored_id, tying in landed[e["index"]]:
            fix = corrections.get(stored_id)
            if stored_id in flagged and fix is None:          # its passage does not state it and it could not be corrected
                dumped.append({"record": "rejection", "stage": "verify", "unit_id": f["unit_id"], "category": "unsupported",
                               "subject": f["subject"], "predicate": f["predicate"], "object": f["object"],
                               "quote": f["quote"], "why": "the passage does not state it and it could not be corrected"})
                continue
            landed_ids.add(f["fact_id"])
            riding += direction == "about"
            object_node = node_of.get((position_of[f["unit_id"]], f["object"])) if f["object_is_entity"] else None
            # a correction may move the predicate, the qualifiers and the object; it may not move
            # the subject (corrected_fact refuses that), and on an inverse landing the object slot
            # structurally holds the other entity's name, so it is not the correction's to set (P1)
            if direction == "forward":
                obj, is_node = (fix["object"], False) if fix else (object_node or f["object"], object_node is not None)
            elif direction == "inverse":
                obj, is_node = f["subject"], False
            else:                                     # about: the minor's own fact, riding into this major
                obj, is_node = (fix["object"] if fix else f["object"]), False
            lines.append({"record": "fact", "fact_id": stored_id, "subject": nid,
                          "predicate": fix["predicate"] if fix else f["predicate"], "object": obj,
                          "object_is_node": is_node, "direction": direction,
                          "qualifiers": fix["qualifiers"] if fix else f["qualifiers"],
                          "rank": "active",
                          "unit_id": f["unit_id"], "quote": f["quote"], "quote_start": f["quote_start"], "quote_end": f["quote_end"],
                          "valid_from": f["valid_from"], "valid_to": f["valid_to"],
                          # when it was said, from its unit; valid_from/valid_to are when it is true (R2, 09-07)
                          "occurred_at": when_of.get(f["unit_id"], (None, None))[0],
                          "occurred_until": when_of.get(f["unit_id"], (None, None))[1],
                          "tier": f["tier"], "author": f["author"],
                          "provenance": {"ingestor": INGESTOR, "matched_by": f["matched_by"], "subject_name": f["subject"],
                                         "voice_ambiguous": f["voice_ambiguous"], "rides_on": tying,
                                         "copy_of": f["fact_id"] if direction == "about" else None,
                                         "corrected_from": {"predicate": f["predicate"], "object": f["object"],
                                                            "qualifiers": f["qualifiers"]} if fix else None}})
    lines.append({"record": "predicate_census", "predicates": predicate_census(records)})
    lines += dumped
    for r in records:
        lines += [{"record": "rejection", "stage": "facts", "unit_id": r["unit_id"], **x} for x in r["rejected_facts"]]
        lines += [{"record": "rejection", "stage": "entities", "unit_id": r["unit_id"], **x} for x in r["dropped_entities"]]

    counts = {"units": len(records), "entities": len(entities), "majors": len(folded["majors"]), "minors": len(folded["minors"]),
              "mentions": sum(len(r["mentions"]) for r in records), "facts_kept": sum(len(r["facts"]) for r in records),
              "facts_stored": sum(1 for l in lines if l["record"] == "fact"),   # landed + riding copies
              "facts_landed": sum(1 for l in lines if l["record"] == "fact" and l["direction"] != "about"),
              "facts_minor_subject": sum(len(r["facts"]) for r in records) - len(landed_ids), "facts_riding": riding,
              "facts_riding_sources": len({f["fact_id"] for e in folded["majors"] for f, direction, label, stored_id, tying in landed[e["index"]] if direction == "about"}),
              "facts_rejected": sum(len(r["rejected_facts"]) for r in records) + len(dumped), "cells": sum(1 for l in lines if l["record"] == "cell"),
              "cells_unlisted": sum(r.get("cells_unlisted", 0) for r in records),
              "shared_spans": sum(r["shared_spans"] for r in records), "ambiguous_voice": sum(r["ambiguous_voice"] for r in records),
              "facts_split_by_voice": sum(r["split_by_voice"] for r in records),
              "empty_units": sum(r["empty"] for r in records), "units_excluded": len(excluded), "demoted": len(folded["demoted"]),
              "adjudicated_facts": sum(1 for l in lines if l["record"] == "adjudicated_fact"),
              "attributes": sum(1 for l in lines if l["record"] == "attribute"),
              "contradictions": sum(1 for l in lines if l["record"] == "contradiction"),
              "contradictions_resolved": sum(1 for l in lines if l["record"] == "contradiction" and l["holds"]),
              "adjudication_dropped": sum(a.get("dropped", 0) for a in adjudicated.values()),
              "adjudications_skipped": sum(1 for e in folded["majors"] if adjudicated.get(e["index"], {}).get("skipped")),
              "support_calls": sum(a.get("support_calls", 0) for a in adjudicated.values()),
              "adjudications_rejected": sum(1 for a in adjudicated.values() if a.get("rejected")),
              "facts_flagged": len(flagged), "facts_corrected": len(corrections), "facts_dumped": len(dumped),
              "adjudication_stranded": stranded,        # items whose every source was dumped (P2)
              "has_abstract": folded["abstract"] is not None}
    lines.append({"record": "completion", "doc_id": doc["doc_id"], "input_hash": input_hash(doc), "ingestor": INGESTOR, "counts": counts,
                  "stats": stats, "empty": counts["facts_stored"] == 0 and counts["cells"] == 0, "excluded": excluded,
                  "demoted": folded["demoted"]})
    path.write_text("\n".join(json.dumps(l, ensure_ascii=False) for l in lines) + "\n", encoding="utf-8", newline="\n")
    return path, counts


def completed(doc):
    """Is there already a finished package for this exact input?"""
    path = package_path(doc)
    rows = read_own_jsonl(path) if path.exists() else []
    return bool(rows) and rows[-1].get("record") == "completion" and rows[-1].get("input_hash") == input_hash(doc)

# %%
# Block 11: the pipeline as one function, ingest(doc).
#
# The steps in order: triage (which kinds of unit to read), derive_unit for each unit kept,
# each checkpointed as it lands, then, all at the end, reconcile, fold_document, adjudicate,
# write_package. WATCH says whether the run narrates what it
# happens: triage, units, entities, facts, rejections, cells, reconcile, ledger, fold,
# adjudicate, package. A finished package for the same input is skipped; a document stopped
# mid-way resumes from the units its sidecar holds. Every document appends an entry to
# ingest.log and a row to manifest.jsonl; the receipt sums the packages on disk.
LOG = OUT / "ingest.log"
WATCH = True                                  # narrate each stage as the run goes
RESULTS = []                                  # (source_uri, records, counts, stats) for every document this session ingested
ADJUDICATE_MIN_FACTS = 4                      # fewer than this: nothing to consolidate, so a support call instead


def remember_reply(uri, key, reply):
    """One bought reply, held for this run and written beside the document so a resume has it."""
    doc = IN_FLIGHT.get(uri)
    with REPLIES_LOCK:
        REPLIES.setdefault(uri, {})[key] = reply
        if doc is not None:
            append_sidecar(doc, {"cached": key, "reply": reply})


def sidecar_rows(doc):
    """The rows of this document's sidecar that belong to this input, torn last line dropped."""
    side = sidecar_path(doc)
    if side.exists():
        data = side.read_bytes()                  # a kill mid-write leaves a torn last line: drop it,
        if not data.endswith(b"\n"):             # or the resume appends behind it and is never read past
            side.write_bytes(data[:data.rfind(b"\n") + 1])
    if not side.exists():
        return []
    return [row for row in read_own_jsonl(side)
            if row.get("ingestor") == INGESTOR and row.get("input_hash") == input_hash(doc)]


def load_replies(doc):
    """What a stopped attempt already paid for, so the resume does not buy it twice."""
    REPLIES[doc["source_uri"]] = {row["cached"]: row["reply"] for row in sidecar_rows(doc) if "cached" in row}
    return len(REPLIES[doc["source_uri"]])


def append_sidecar(doc, row):
    side = sidecar_path(doc)
    side.parent.mkdir(parents=True, exist_ok=True)
    with side.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ingestor": INGESTOR, "input_hash": input_hash(doc), **row}, ensure_ascii=False) + "\n")


def checkpointed(doc):
    """What a previous attempt left in its sidecar, when it belongs to this input: (the kinds
    triage left out, the unit records in order, their cost, their calls, the triage flags)."""
    rows = sidecar_rows(doc)
    # the triage row is no longer first: triage() buys a reply, and that reply is checkpointed
    # before the triage row is written. Requiring it at index 0 rejected every full-path sidecar
    # and the resume then deleted it, re-buying what it had already paid for (P3, fixed 09-07)
    head = next((row for row in rows if "triage" in row), None)
    if head is None:
        return None, [], 0.0, 0, []
    excluded = head["triage"]
    kept_ids = [u["unit_id"] for u in doc["units"] if unit_kind(doc, u) not in excluded]
    kept, cost, calls = [], head.get("cost", 0.0), head.get("calls", 0)
    for row in rows:
        if "rec" in row and len(kept) < len(kept_ids) and row["rec"]["unit_id"] == kept_ids[len(kept)]:
            kept.append(row["rec"])
            cost += row.get("cost", 0.0)
            calls += row.get("calls", 0)
    return excluded, kept, cost, calls, head.get("flags", [])


def triage(doc, ctx):
    """The judge's call on which kinds of unit are not the work: {kind: reason}, plus flags.
    No call when the document has one kind. The answer stands, short of leaving out everything."""
    kinds = {}
    for u in doc["units"]:
        text = doc["text"][u["start"]:u["end"]]
        kinds.setdefault(unit_kind(doc, u), []).append((u["position"], u["label"], word_count(text), first_line(text)))
    if len(kinds) < 2:
        return {}, []
    reply = generate(triage_prompt(doc, kinds), TRIAGE_SCHEMA, "triage", ctx=ctx)
    excluded, flags = {}, []
    if reply is None:
        flags.append("triage reply rejected twice; every kind was read")
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


VERIFY_BATCH = 60           # facts to a verification call; the listing had no bound before 09-07


def unsupported_of(facts, ctx, entity=None):
    """(the stored ids of the facts whose own passage does not state them, whether any batch was
    refused, how many calls it took). The statements are judged one at a time and on their own terms: a fact stated from
    the side of a lesser thing is filed under the entity it points at, so naming that entity in
    the question asked about the wrong half of the statement (fixed 09-07). A refusal is reported
    rather than read as a clean pass, because on the short path this is the document's only
    check; and the listing is batched, because it had no bound (fixed 09-07)."""
    flagged, refused, calls = [], False, 0
    for at in range(0, len(facts), VERIFY_BATCH):
        batch, listing = facts[at:at + VERIFY_BATCH], []
        for n, (f, stored_id) in enumerate(batch, 1):
            listing.append(f"{n}. {f['subject']} {f['predicate']} {f['object']}"
                           + (f" [{f['qualifiers']}]" if f["qualifiers"] else "")
                           + f"  (\"{' '.join(f['quote'].split())}\")")
        reply = generate(support_prompt(listing), SUPPORT_SCHEMA, "support", ctx={**ctx, "entity": entity})
        calls += 1
        if reply is None:
            refused = True             # not a clean pass: the document says so and receipt() filters on it
            continue
        flagged += [batch[n - 1][1] for n in valid_sources(reply.get("unsupported"), len(batch))]
    return flagged, refused, calls


def valid_sources(numbers, n):
    """The fact numbers an adjudicated item points at, as distinct integers within 1..n."""
    good = []
    for x in numbers if isinstance(numbers, list) else []:
        if isinstance(x, str) and x.strip().isdigit():
            x = int(x)
        if isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= n and x not in good:
            good.append(x)
    return good


def adjudicate(records, folded, ctx, watch=False, light=False):
    """One call per document-major over its landed facts and its cells; the consolidated facts,
    attributes and contradictions point at the raw facts by number. Keyed by entity index."""
    landed, cells_of = landings(records, folded), folded["cells_of"]

    def adjudicate_one(e):
        raws = landed[e["index"]]
        result = {"facts": [], "attributes": [], "contradictions": [], "unsupported": [], "dropped": 0, "raw": len(raws),
                  "riding": sum(1 for x in raws if x[1] == "about"), "skipped": None, "rejected": False}
        if not raws:
            return result
        if len(raws) < ADJUDICATE_MIN_FACTS:         # nothing to consolidate, but the passages are still read
            result["skipped"] = f"fewer than {ADJUDICATE_MIN_FACTS} facts: the raw facts stand, their support checked"
            result["unsupported"], result["rejected"], result["support_calls"] = unsupported_of(
                [(f, stored_id) for f, direction, label, stored_id, tying in raws], ctx, entity=e["name"])
            return result
        listing = []
        for n, (f, direction, label, stored_id, tying) in enumerate(raws, 1):
            if direction == "forward":
                line = f"{n}. {e['name']} {f['predicate']} {f['object']}"
            elif direction == "inverse":
                line = f"{n}. (inverse) {f['subject']} {f['predicate']} {e['name']}"
            else:
                line = f"{n}. (about {f['subject']}) {f['subject']} {f['predicate']} {f['object']}"
            listing.append(line + (f" [{f['qualifiers']}]" if f["qualifiers"] else "") + f"  ({label}: \"{' '.join(f['quote'].split())}\")")
        reply = generate(adjudicate_prompt(e["name"], e["kinds"], listing, cells_of.get(e["index"], [])), ADJUDICATE_SCHEMA, "adjudicate",
                         model=TERRA, effort="medium", ctx={**ctx, "entity": e["name"]})
        result["rejected"] = reply is None
        ids = [stored_id for f, direction, label, stored_id, tying in raws]
        result["unsupported"] = [ids[n - 1] for n in valid_sources((reply or {}).get("unsupported"), len(ids))]
        aside = set(result["unsupported"])
        for key in ("facts", "attributes", "contradictions"):
            for item in (reply or {}).get(key, []):
                if key == "contradictions":                    # which of its own sources holds at the end (R4)
                    settles = valid_sources([item.get("holds")], len(ids))
                    item["holds_fact"] = ids[settles[0] - 1] if settles else None
                # a consolidated item is redundant raw facts merged, so one supported source
                # carries it; the ones set aside come out of its sources (decision 45)
                sources = [ids[n - 1] for n in valid_sources(item.get("from"), len(ids))]
                sources = [i for i in sources if i not in aside]
                if not sources:
                    result["dropped"] += 1
                    continue
                kept = {k: v for k, v in item.items() if k != "from"}
                kept["from_facts"] = sources
                result[key].append(kept)
        return result

    minor_index = {(ui, local_name): e["index"] for e in folded["minors"] for ui, local_name in e["members"]}
    own_of = {}
    for r in records:
        for f in r["facts"]:
            index = minor_index.get((r["position"], f["subject"]))
            if index is not None:
                own_of.setdefault(index, []).append((f, f["fact_id"]))

    if light:
        # one reading: nothing to consolidate, so every fact stands and the document's whole
        # fact list is read against its passages in a single call (ruling of 09-07)
        # every landed list already carries each minor's facts as riding copies, under the ids
        # the package will use; listing the minors' own facts again duplicated every rider and
        # named ids no record carries (fixed 09-07)
        every, out = [], {}
        for e in folded["majors"]:
            every += [(f, stored_id) for f, direction, label, stored_id, tying in landed[e["index"]]]
        if watch:
            print(f"verify: {len(every)} facts of the whole document, one pass on {LUNA}")
        flagged, refused, support_calls = unsupported_of(every, ctx) if every else ([], False, 0)
        aside = set(flagged)
        stands = "one reading: the facts stand, verified in one pass"
        for e in folded["majors"]:
            raws = landed[e["index"]]
            out[e["index"]] = {"facts": [], "attributes": [], "contradictions": [], "dropped": 0, "raw": len(raws),
                               "riding": sum(1 for x in raws if x[1] == "about"), "skipped": stands, "rejected": refused,
                               "support_calls": support_calls,
                               "unsupported": [sid for f, direction, label, sid, tying in raws if sid in aside]}
            support_calls = 0                    # the one pass covers the document: counted once
        return out

    def check_one(pair):
        e, own = pair
        flagged, refused, calls = unsupported_of(own, ctx, entity=e["name"])
        return {"facts": [], "attributes": [], "contradictions": [], "raw": len(own), "riding": 0, "dropped": 0,
                "skipped": "not a major: its facts stand, their support checked", "rejected": refused,
                "unsupported": flagged, "support_calls": calls}

    if watch:
        print(f"adjudicate: {len(folded['majors'])} majors, {WORKERS} at a time; fewer than {ADJUDICATE_MIN_FACTS} facts is a support call on {LUNA}")
    out = {e["index"]: result for e, result in zip(folded["majors"], in_parallel(adjudicate_one, folded["majors"]))}

    # every other entity's facts are read where they stand, before any of them rides (decision 50)
    # only the facts that ride are ever written, so only those are worth a call (fixed 09-07)
    rides_somewhere = {f["fact_id"] for e in folded["majors"]
                       for f, direction, label, stored_id, tying in landed[e["index"]] if direction == "about"}
    pairs = []
    for e in folded["minors"]:
        own = [(f, fid) for f, fid in own_of.get(e["index"], []) if fid in rides_somewhere]
        if own:
            pairs.append((e, own))
    if watch and pairs:
        print(f"support: {len(pairs)} minors with facts of their own, checked on {LUNA}")
    for (e, own), result in zip(pairs, in_parallel(check_one, pairs)):
        out[e["index"]] = result
    return out


def flagged_facts(records, folded, adjudicated):
    """{stored id: the raw fact behind it} for every fact a verification set aside. A minor's
    verdict names its raw fact, but the package holds that fact only as riding copies, so the
    verdict is carried to those; a fact that rides nowhere names no line here at all."""
    landed, by_stored, rides = landings(records, folded), {}, {}
    for e in folded["majors"]:
        for f, direction, label, stored_id, tying in landed[e["index"]]:
            by_stored[stored_id] = f
            if direction == "about":
                rides.setdefault(f["fact_id"], []).append(stored_id)
    out = {}
    for sid in {x for result in adjudicated.values() for x in result.get("unsupported", [])}:
        for target in rides.get(sid, [sid]):
            if target in by_stored:
                out[target] = by_stored[target]
    return out


def corrected_fact(f, item):
    """A correction that survives the checks a fact must still pass without the gate: it says
    something, its object restates neither its subject nor its predicate, and it is not a bare
    boolean. None when it does not, and the fact is then dumped rather than kept."""
    subject = str(item.get("subject") or f["subject"]).strip()
    predicate = snake_case(str(item.get("predicate") or "")) or f["predicate"]
    obj = str(item.get("object") or "").strip()
    if not subject or not obj or obj.casefold() in ("true", "false"):
        return None
    if norm(subject) != norm(f["subject"]):
        # a correction that moves the subject is a different fact, not this one corrected: the
        # subject decides which node it lands on and whether it rides, and this pass runs after
        # landing, so it cannot be re-landed. Dumped rather than stored under the wrong node (P1)
        return None
    said = norm(obj).replace("_", " ")            # the predicate written as words is still the predicate
    if said == norm(subject).replace("_", " ") or said == norm(predicate).replace("_", " "):
        return None
    return {"subject": subject, "predicate": predicate, "object": obj, "qualifiers": item.get("qualifiers") or None}


def corrections_of(flagged, ctx, watch=False):
    """({stored id: the corrected statement}, calls). The passage is fixed and the claim moves to
    fit it (R3, 09-07); a fact the reply leaves out, or whose correction fails corrected_fact, is
    not corrected and will be dumped rather than written with a flag."""
    items, out, calls = sorted(flagged.items()), {}, 0
    if watch and items:
        print(f"correct: {len(items)} facts their passage does not state, on {LUNA}")
    for at in range(0, len(items), VERIFY_BATCH):
        batch, listing = items[at:at + VERIFY_BATCH], []
        for n, (stored_id, f) in enumerate(batch, 1):
            listing.append(f"{n}. {f['subject']} {f['predicate']} {f['object']}"
                           + (f" [{f['qualifiers']}]" if f["qualifiers"] else "")
                           + f"  (\"{' '.join(f['quote'].split())}\")")
        reply = generate(correct_prompt(listing), CORRECT_SCHEMA, "correct", ctx=ctx)
        calls += 1
        if reply is None:
            continue
        for item in reply.get("corrections", []):
            numbered = valid_sources([item.get("fact")], len(batch))
            if not numbered:
                continue
            stored_id, f = batch[numbered[0] - 1]
            fixed = corrected_fact(f, item)
            if fixed is not None:
                out[stored_id] = fixed
    return out, calls


def show_unit(rec, unit, unit_cost, total_cost):
    """One unit as it lands, in the demo's shape."""
    by_category, by_path = {}, {}
    for x in rec["rejected_facts"]:
        by_category[x["category"]] = by_category.get(x["category"], 0) + 1
    for f in rec["facts"]:
        by_path[f["matched_by"]] = by_path.get(f["matched_by"], 0) + 1
    print(f"[{rec['position']}] {rec['label'][:40]} ({rec['kind']}): {word_count(unit['text']):,} words;"
          f" {len(rec['entities'])} entities ({len(rec['dropped_entities'])} dropped), {len(rec['mentions'])} mentions;"
          f" {len(rec['facts'])} facts kept ({counts_text(by_path)}), {len(rec['rejected_facts'])} rejected ({counts_text(by_category)});"
          f" {len(rec['cells'])} cells; ${unit_cost:.3f} this unit, ${total_cost:.3f} so far")
    if WATCH:
        for e in rec["entities"]:
            print(f"    {e['name'][:34]:<34} {e['kind'][:9]:<9} {'named' if e['named'] else 'unnamed':<8}"
                  f" {'major' if e['major'] else 'minor':<6} x{e['mentions']:<3} forms: {' | '.join(e['forms'][:4])[:70]}")
        for d in rec["dropped_entities"]:
            print(f"    DROPPED {d['name'][:34]}: {d['why']} {d['forms'][:3]}")
    if WATCH:
        for f in rec["facts"]:
            print(f"    {f['subject']} -{f['predicate']}-> {f['object']}{' [' + f['qualifiers'] + ']' if f['qualifiers'] else ''}"
                  f"  ({f['matched_by']}{', voice ambiguous' if f['voice_ambiguous'] else ''})  \"{' '.join(f['quote'].split())[:90]}\"")
    if WATCH:
        for x in rec["rejected_facts"]:
            print(f"    REJECTED {x['category']}: {x['subject']} -{x['predicate']}-> {x['object']}  \"{' '.join(x['quote'].split())[:90]}\"")
    if WATCH and rec["summary"]:
        print(f"    SUMMARY {rec['summary']}")
        for c in rec["cells"]:
            print(f"    [{c['entity']}] {c['text']}")


def show_reconcile(entities, ledger, stats):
    by_how = {}
    for entry in ledger:
        by_how[f"{entry['how']} {entry['verdict']}"] = by_how.get(f"{entry['how']} {entry['verdict']}", 0) + 1
    print(f"reconcile: {stats['locals']} unit-locals -> {len(entities)} document entities; ledger {counts_text(by_how)};"
          f" {stats['candidate_pairs']} pairs queued over {stats['judge_rounds']} rounds, {stats['judged_pairs']} judged in {stats['judge_calls']} calls")
    if False:                                     # every judged pair, line by line
        for entry in ledger:
            print(f"    {entry['verdict']:<9} {entry['how']:<12} {entry['a'][:28]:<28} (u{entry['a_unit']}) ~ {entry['b'][:28]:<28} (u{entry['b_unit']})  {str(entry['evidence'])[:70]}")


def show_fold(folded):
    if folded["abstract"]:
        print(f"abstract ({word_count(folded['abstract']['text'])} words, limit {folded['abstract']['limit']}): {folded['abstract']['text']}")
    else:
        print("abstract: none (no unit summaries)")
    print(f"salience: {len(folded['majors'])} major, {len(folded['minors'])} minor, {len(folded['demoted'])} demoted"
          f" ({sum(1 for e in folded['minors'] if e['rank'].get('no_abstract')) } of them for want of an abstract);"
          f" {len(folded['entity_abstracts'])} entity abstracts")
    if folded["demoted"]:
        print(f"    not majors, nothing to summarise (decision 52): {', '.join(folded['demoted'])[:200]}")
    for e in folded["majors"]:
        rank = e["rank"]
        why = ("in abstract" if rank["in_abstract"] else "major in a unit" if rank["unit_major"]
               else "named" if rank["named"] else "by unit and fact count")
        others = [n for n in e["names"] if n != e["name"]]
        print(f"    {e['name'][:34]:<34} {'/'.join(e['kinds'])[:16]:<16} units {len(e['units']):>3} facts {e['n_facts']:>3}  {why}  "
              + (f"also: {', '.join(others)[:60]}" if others else ""))


def show_adjudication(folded, adjudicated):
    total = {"raw": 0, "riding": 0, "facts": 0, "attributes": 0, "contradictions": 0, "unsupported": 0, "dropped": 0}
    for e in folded["majors"]:
        a = adjudicated.get(e["index"])
        if not a:
            continue
        for key in total:
            total[key] += a[key] if key in ("raw", "riding", "dropped") else len(a.get(key, []))
        if a["skipped"]:
            print(f"    {e['name'][:34]:<34} {a['raw']:>3} raw facts stand: {a['skipped']}")
        else:
            print(f"    {e['name'][:34]:<34} {a['raw']:>3} raw facts -> {len(a['facts']):>3} facts, {len(a['attributes']):>3} attributes,"
                  f" {len(a['contradictions'])} contradictions" + (f", {a['dropped']} dropped for pointing at nothing" if a["dropped"] else ""))
    print(f"adjudicated: {total['raw']} raw facts ({total['riding']} riding in from minors) -> {total['facts']} facts, {total['attributes']} attributes,"
          f" {total['contradictions']} contradictions; {total['unsupported']} raw facts their passage does not state, to be corrected or dumped;"
          f" {total['dropped']} dropped; {sum(1 for a in adjudicated.values() if a['skipped'])} majors left to their raw facts")
def ingest(doc, ctx=None):
    """One document, start to finish: the units on their own, then everything merged at the end."""
    ctx = {"doc": doc["source_uri"], **(ctx or {})}
    logged_before = len(CALLS)                  # this document's own calls start here
    light = one_reading(doc)          # one unit to read: nothing to merge, so the short path
    IN_FLIGHT[doc["source_uri"]] = doc           # so every reply this document buys is checkpointed
    reused = load_replies(doc)                   # and every reply it already bought is not bought again
    if reused and WATCH:
        print(f"resuming {doc['source_uri']}: {reused} replies already paid for")

    # which kinds of unit to read: the sidecar's answer when resuming, else the judge's
    excluded, records, cost_before, calls_before_stop, flags = checkpointed(doc)   # what a stopped run already paid
    if excluded is None:
        # a sidecar still holding replies for THIS input is not thrown away: sidecar_rows already
        # filtered it by input hash, so what is there was paid for and still applies (P3)
        if sidecar_path(doc).exists() and not REPLIES.get(doc["source_uri"]):
            sidecar_path(doc).unlink()
        spend_at, calls_at = spend(), len(CALLS)
        excluded, flags = boilerplate_of(doc) if light else triage(doc, ctx)
        append_sidecar(doc, {"triage": excluded, "flags": flags, "cost": round(spend() - spend_at, 6), "calls": len(CALLS) - calls_at})
    kept, left_out = [], []
    for u in doc["units"]:
        kind = unit_kind(doc, u)
        if kind in excluded:
            left_out.append({"position": u["position"], "kind": kind, "label": u["label"], "reason": excluded[kind]})
        else:
            kept.append(u)
    if WATCH:
        counts = {}
        for u in doc["units"]:
            counts[unit_kind(doc, u)] = counts.get(unit_kind(doc, u), 0) + 1
        print(f"triage: {counts_text(counts)}; " + (f"left out {len(left_out)} unit(s)" if left_out else "nothing left out"))
        for kind, reason in excluded.items():
            print(f"    {kind}: {reason}")
        for flag in flags:
            print(f"    FLAG {flag}")

    # the units, each on its own, checkpointed as it lands
    if records and WATCH:
        print(f"resuming {doc['source_uri']} from {len(records)} checkpointed units")
    def derive_one(unit):
        try:
            return derive_unit(doc, unit, {**ctx, "unit": unit["position"]}, light=light)
        except SpendStop as stop:
            return stop          # the batch's finished units are still checkpointed; the stop is raised after them

    todo, width = kept[len(records):], max(WORKERS, 1)
    for at in range(0, len(todo), width):        # a batch derives together, then lands in reading order
        batch = [{**u, "text": doc["text"][u["start"]:u["end"]], "kind": unit_kind(doc, u)} for u in todo[at:at + width]]
        for unit, rec in zip(batch, in_parallel(derive_one, batch)):
            if isinstance(rec, SpendStop):
                raise rec
            cost, calls = unit_spend(doc, unit["position"])
            records.append(rec)
            append_sidecar(doc, {"rec": rec, "cost": round(cost, 6), "calls": calls})
            if WATCH:
                show_unit(rec, unit, cost, document_spend(doc, logged_before)[0])

    # the document, all at the end: reconcile, fold, salience, adjudicate, predicates, write
    entities, ledger, candidates, stats = reconcile(records, ctx, watch=WATCH)
    stamp_first_mention(records, entities)        # a node id is the moniker and its first mention
    if WATCH:
        show_reconcile(entities, ledger, stats)
    folded = fold_document(records, entities, ctx, light=light)
    if WATCH:
        show_fold(folded)
    adjudicated = adjudicate(records, folded, ctx, watch=WATCH, light=light)
    if WATCH:
        show_adjudication(folded, adjudicated)
    # a fact its passage does not state is corrected if it can be and dumped if it cannot; it is
    # never written with a flag (R3, ruling of 09-07)
    flagged = flagged_facts(records, folded, adjudicated)
    corrections, correct_calls = corrections_of(flagged, ctx, watch=WATCH) if flagged else ({}, 0)
    if WATCH and flagged:
        print(f"    {len(corrections)} of {len(flagged)} corrected against their passage; {len(flagged) - len(corrections)} dumped")
    own_cost, own_calls = document_spend(doc, logged_before)
    stats.update({"one_reading": light,
                  "calls": own_calls + calls_before_stop, "cost": round(own_cost + cost_before, 4),
                  "matched_by": {}, "rejected_by": {}, "units_excluded": len(left_out), "triage_flags": flags})
    for r in records:
        for f in r["facts"]:
            stats["matched_by"][f["matched_by"]] = stats["matched_by"].get(f["matched_by"], 0) + 1
        for x in r["rejected_facts"]:
            stats["rejected_by"][x["category"]] = stats["rejected_by"].get(x["category"], 0) + 1
    stats["correct_calls"] = correct_calls
    path, counts = write_package(doc, records, entities, folded, adjudicated, ledger, candidates, left_out, stats,
                                 flagged, corrections)
    if sidecar_path(doc).exists():
        sidecar_path(doc).unlink()
    if WATCH:
        print(f"package {path}: {counts}")
    RESULTS.append((doc["source_uri"], records, counts, stats))
    return path, counts, stats, records, entities, folded


def note(text):
    print(text)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(text + "\n\n")


def one_reading_report(records, folded):
    """A one-reading document's majors, each with its abstract and the facts it was given. The
    trace is stilled while documents run together, so this is the whole of what can be read as
    the run goes; the quotes and offsets are in the roll-up beside the package."""
    said = {a["entity"]: a["text"] for a in folded["entity_abstracts"]}
    stated = {}
    for r in records:
        for f in r["facts"]:
            stated.setdefault(f["subject"], []).append(
                f"{f['predicate']} -> {f['object']}" + (f" [{f['qualifiers']}]" if f.get("qualifiers") else ""))
    lines = []
    for e in folded["majors"]:
        own = []
        for ui, local_name in e["members"]:
            own += stated.get(local_name, [])
        lines.append(f"    {e['name'][:44]:<46} {(e.get('kind') or '/'.join(e['kinds']))[:16]}")
        if said.get(e["name"]):
            lines.append(f"        {said[e['name']][:400]}")
        for one in dict.fromkeys(own):
            lines.append(f"        - {one[:150]}")
    return lines


def one_document(uri):
    """One document, start to finish, and what to say about it. Every outcome is returned rather
    than raised, so a batch of documents running together all report."""
    try:
        doc = load_document(uri, BY_URI, UNITS, PIECES)
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
        if stats.get("one_reading"):
            entry += one_reading_report(records, folded)
        else:
            entry += [f"    {e['name'][:36]:<36} {'/'.join(e['kinds'])[:16]:<16} units {len(e['units']):>3} facts {e['n_facts']:>3}" for e in folded["majors"][:12]]
        return {"done": True, "text": "\n".join(entry + [f"    -> {path}"])}
    except SpendStop as e:
        return {"stop": True, "text": f"{uri}: {e} after ${document_spend({'source_uri': uri})[0]:.3f} on this document;"
                                      f" everything it has already paid for is checkpointed and the run stops here"}
    except Exception as e:
        return {"text": f"{uri}  ERROR {type(e).__name__}: {e}"}
    finally:
        IN_FLIGHT.pop(uri, None)                 # the sidecar keeps the replies; memory need not
        REPLIES.pop(uri, None)


def run(uris, at_once=None):
    """Every document named, DOCS_AT_ONCE at a time and reported in the order they were named.
    While more than one runs the per-unit trace is stilled: eight interleaved traces are not a
    log anyone reads, and each document still reports as it lands."""
    global WATCH
    if not KEY:
        raise SystemExit("no OPENAI_API_KEY: set it in the environment, or attach it as a Kaggle secret")
    done = skipped = 0
    todo = []
    for uri in uris:
        if uri in BY_URI:
            todo.append(uri)
        else:
            note(f"not in export: {uri}")
    width = max(at_once or DOCS_AT_ONCE, 1)
    watching, WATCH = WATCH, WATCH and width == 1
    stop = False
    try:
        for at in range(0, len(todo), width):
            batch = todo[at:at + width]
            for result in in_parallel(one_document, batch, width=width):
                if result.get("text"):
                    note(result["text"])
                done += bool(result.get("done"))
                skipped += bool(result.get("skipped"))
                stop = stop or bool(result.get("stop"))
            if stop:
                break
    finally:
        WATCH = watching
    print(f"done {done}  skipped (already complete) {skipped}  spent ${spend():.2f} this session")
    return done, skipped


def receipt():
    """Sums over every package on disk, plus the calls this session logged."""
    rec = {"ingestor": INGESTOR, "documents": 0, "by_group": {}, "counts": {}, "matched_by": {}, "rejected_by": {}, "cost_of_packages": 0.0,
           "cost_this_session": round(spend(), 4), "calls_this_session": len(CALLS), "calls_by_stage": {},
           "schema_rejections_this_session": len(REJECTIONS), "schema_retries_this_session": len(RETRIES),
           "in_flight_sidecars": []}
    for c in CALLS:
        rec["calls_by_stage"][c["stage"]] = rec["calls_by_stage"].get(c["stage"], 0) + 1
    for path in sorted(OUT.rglob("*.jsonl")):
        if path.parent == OUT:
            continue
        if path.name.endswith(".units.jsonl"):
            rec["in_flight_sidecars"].append(str(path.relative_to(OUT)).replace("\\", "/"))
            continue
        rows = read_own_jsonl(path)
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

# %%
# Block 12: naming documents, the test variety, and reading a package back.
#
# targets(spec) turns what a run names into source_uris: "sample" for the test variety, "all"
# for the export, or a list of titles or source_uri endings. rollup(path) prints the final
# roll-up of one package: the abstract, the unit summaries in order, the major entities, then
# everything known about the top five. draw_graph(path) draws the majors as the 09-02 demo did.


def sample(per_group=None):
    chats = sorted(u for u in BY_URI if "/longmemeval/" in u)
    papers = sorted(u for u in BY_URI if u.endswith(".pdf"))
    books = [find_document(b) for b in ("/graphrag-bench/Novel-30752.txt", "/graphrag-bench/Novel-40700.txt", "/oz/01_55.txt", "/oz/02_54.txt",
                                        "/oz/03_486.txt", "/holmes/03_1661.txt", "/holmes/05_2852.txt", "/greek/03_348.txt", "/greek/11_830.txt")]
    if per_group:
        return chats[:per_group] + papers[:per_group] + books[:per_group]
    return chats[:300] + papers[:20] + books


def targets(spec):
    if spec == "sample":
        return sample()
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
    rows = read_own_jsonl(Path(path))
    if not rows or rows[-1].get("record") != "completion":
        raise ValueError(f"{path}: no completion record; the package is unfinished")
    by = {}
    for row in rows:
        by.setdefault(row["record"], []).append(row)
    return by


def grouped(rows, key):
    out = {}
    for row in rows:
        out.setdefault(row.get(key), []).append(row)
    return out


def units_then_facts(item):
    return (-item[0], -item[1])


def ranked_majors(by):
    """The package's major nodes, most units first, then most raw facts: [(units, facts, node)]."""
    units_of = {e["subject"]: len(e["units"]) for e in by.get("edge", []) if e["predicate"] == "appears_in"}
    facts_of = grouped(by.get("fact", []), "subject")
    ranked = [(units_of.get(n["node_id"], 0), len(facts_of.get(n["node_id"], [])), n) for n in by.get("node", []) if n["kind"] != "document"]
    ranked.sort(key=units_then_facts)
    return ranked


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
    doc, units = by["document"][0], sorted(by.get("unit", []), key=position_of_row)
    label_of = {u["unit_id"]: f"[{u['position']}] {u['label']}" for u in units}
    position = {u["unit_id"]: u["position"] for u in units}
    doc_node = h(doc["doc_id"], "document")
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
              f"  attributes {len(attributes_of.get(n['node_id'], [])):>3}  {'in abstract' if n['provenance'].get('salience', {}).get('in_abstract') else 'by tie-break'}")
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
            for c in sorted(cells_of[nid], key=cell_position(position)):
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
                if f["direction"] == "forward":
                    line = f"{f['predicate']} -> {name_of.get(f['object'], f['object'])}"
                elif f["direction"] == "inverse":
                    line = f"(inverse) {who} {f['predicate']} -> {n['name']}"
                else:
                    line = f"(about {who}) {f['predicate']} -> {f['object']}"
                print(f"    {line}{' [' + f['qualifiers'] + ']' if f.get('qualifiers') else ''}  {label_of.get(f['unit_id'], '')} \"{' '.join(f['quote'].split())[:100]}\"")


def cell_position(position):
    def key(cell):
        return position.get(cell["unit_id"], 0)
    return key


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
        nid, edges = n["node_id"], []
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


import random


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

# %%
# Block 13: the run, a spread of chat sessions, first of all. Every one of the 19,206 sessions
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

# %%
# Block 14: the run, Oz book 1.
#
# RUN names the documents, by title or by the end of their source_uri; WATCH in block 11 says
# whether each stage narrates itself; BUDGET ends the block past that many dollars of its own
# spending, the document keeping its finished units in a sidecar for next time. For reference, the 09-02 demo on Oz
# book 1: v3 632 entities, 969 facts, 53 dropped, $1.26; the 0.4 run of 09-06: 358 entities
# (38 major), 869 facts, 74 rejected, $2.23. Each document ends in its roll-up.
RUN = ["The Wonderful Wizard of Oz"]
BUDGET = 5.00


if __name__ == "__main__":
    uris = targets(RUN)
    start_block(BUDGET)
    print(f"ingesting {len(uris)} documents, budget ${BUDGET:.2f}: {[BY_URI[u]['title'] or u for u in uris]}")
    run_and_roll_up(uris)

# %%
# Block 15: the run, five papers, Zep first. The papers' text is withheld from the public
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

# %%
# Block 16: the run, one Greek work and one novel from the GraphRAG benchmark, so the entity and
# fact shapes of a play, a novel and a chat can be read side by side before the merge is built.
OTHERS = ["/greek/22_35173.txt", "/graphrag-bench/Novel-40700.txt"]
BUDGET = 6.00

if __name__ == "__main__" and OTHERS:
    chosen = [find_document(name) for name in OTHERS]
    chosen = [u for u in chosen if u]
    start_block(BUDGET)
    print(f"others: {[BY_URI[u]['title'] or u for u in chosen]}; budget ${BUDGET:.2f} for this block")
    run_and_roll_up(chosen)

# %%
# Block 17: the graphs. One knowledge graph per document ingested this session, drawn the
# 09-02 demo's way and saved beside the packages. Needs networkx and matplotlib, which Kaggle has.
if __name__ == "__main__":
    for uri, records_, counts_, stats_ in RESULTS:
        if package_path({"source_uri": uri}).exists():
            draw_graph(package_path({"source_uri": uri}))
