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
# reads a package back for the roll-up and the graph. Blocks 13 and 14 are the runs (Oz book 1;
# five papers, Zep first), each ending in a roll-up per document; block 15 draws the graphs.
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
from pathlib import Path

INGESTOR = "factledger-ingestor 0.6"
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
# Block 2: the model interface: generate(prompt, schema) and embed(texts).
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
EMBED_MODEL = "text-embedding-3-small"
PRICE = {LUNA: (0.20, 1.20), TERRA: (2.00, 12.00), EMBED_MODEL: (0.02, 0.0)}   # $ per million tokens in, out
SPEND_STOP = float(os.environ.get("SPEND_STOP", "25"))
WORKERS = int(os.environ.get("WORKERS", "4"))

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


class SpendStop(Exception):
    pass


class SchemaError(ValueError):
    pass


def record(name, row):
    """Append one row to a run log under OUT, so it survives whatever ends the session."""
    with LOG_LOCK:
        with (OUT / name).open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def in_parallel(function, items):
    """function over each item, WORKERS at a time, results in the items' order. An error in one
    (a spend stop included) is raised once the calls in flight have returned."""
    if WORKERS <= 1 or len(items) <= 1:
        return [function(item) for item in items]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        return list(pool.map(function, items))


def spend():
    return sum(c["cost"] for c in CALLS)


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


def is_of_type(value, name):
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "string":
        return isinstance(value, str)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "null":
        return value is None
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return False


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
    if spend() >= SPEND_STOP:
        raise SpendStop(f"spending stop: ${spend():.2f} of ${SPEND_STOP:.2f}")
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


def embedding_index(row):
    return row["index"]


def embed(texts, stage="embed", ctx=None):
    """One vector per text, in batches of a hundred, each request logged like any call."""
    vectors = []
    for start in range(0, len(texts), 100):
        batch = texts[start:start + 100]
        body = call("https://api.openai.com/v1/embeddings", {"model": EMBED_MODEL, "input": batch}, EMBED_MODEL, stage, ctx or {},
                    sum(len(t) for t in batch))
        for row in sorted(body["data"], key=embedding_index):
            vectors.append(row["embedding"])
    return vectors


print(f"models {LUNA} (derive), {TERRA} (judge), {EMBED_MODEL}; key {'present' if KEY else 'MISSING'}")

# %%
# Block 3: test the connection before anything spends. One tiny call to each endpoint.
if __name__ == "__main__":
    if not KEY:
        print("no key: attach OPENAI_API_KEY under Add-ons > Secrets, then rerun this cell")
    else:
        ping = generate('Reply with exactly the JSON object {"ok": true}.', {"type": "object", "required": ["ok"]}, "ping", ctx={"doc": "connection test"})
        vector = embed(["connection test"], ctx={"doc": "connection test"})
        print(f"chat reply {ping}; embedding of {len(vector[0])} dimensions; {len(CALLS)} calls, ${spend():.5f}")

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


def names_in(text):
    """The names a summary or abstract emits, for the fabrication check: runs of capitalised
    words. A run that opens a sentence is counted from its second word; its first word counts
    only when it also appears capitalised inside some sentence, so 'The' is never a name."""
    names, openers = [], []
    run, run_opens, sentence_start = [], False, True
    for token in text.split():
        word = token.strip("\"'“”‘’()[]")
        tail = ""
        while word and word[-1] in ".,;:!?":
            tail = word[-1] + tail
            word = word[:-1]
        capital = word[:1].isupper()
        if capital:
            if not run:
                run_opens = sentence_start
            run.append(word)
        if run and (not capital or tail):
            (openers if run_opens else names).append(run)
            run = []
        sentence_start = any(ch in ".!?" for ch in tail)
    if run:
        (openers if run_opens else names).append(run)
    found = {" ".join(r) for r in names}
    heads = []
    for r in openers:
        heads.append(r[0])
        if len(r) > 1:
            found.add(" ".join(r[1:]))
    inside = {w for name in found for w in name.split()}
    for head in heads:
        if head in inside:
            found.add(head)
    return sorted(found)


def missing_names(text, children):
    """Names emitted by a fold that appear in none of its children, case ignored."""
    pool = " ".join(children).casefold()
    return [name for name in names_in(text) if name.casefold() not in pool]


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


def words_only(s):
    words = []
    for token in s.split():
        word = "".join(ch for ch in token if is_word_char(ch))
        if word:
            words.append(word)
    return words


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
    ntext, back = normalised_unit(text, cache)
    nneedle, _ = normalised(needle)
    hits = []
    i = text.find(needle)
    while i >= 0:
        hits.append((i, i + len(needle)))
        i = text.find(needle, i + 1)
    i = ntext.find(nneedle) if nneedle else -1
    while i >= 0:
        hits.append((back[i], back[i + len(nneedle) - 1] + 1))
        i = ntext.find(nneedle, i + 1)
    for start, end in hits:
        before = text[start - 1] if start > 0 else " "
        after = text[end] if end < len(text) else " "
        if not is_word_char(before) and not is_word_char(after):
            return start, end
    return None, None


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
            taken.append(j)
            i, j = i + 1, j + 1
        elif table[i + 1][j] >= table[i][j + 1]:
            i += 1
        else:
            j += 1
    return len(taken), (taken[0] if taken else 0), (taken[-1] if taken else 0)


def words_hit(text, quote, cache):
    """The shortest passage holding at least WORDS_NEEDED of the quote's words in order, no
    longer than the quote plus three words; (start, end) or (None, None)."""
    wanted = words_only(normalised(quote)[0])
    if len(wanted) < 4:
        return None, None
    ntext, back = normalised_unit(text, cache)
    words, i = [], 0                                 # (word, start in ntext, end in ntext)
    while i < len(ntext):
        if is_word_char(ntext[i]):
            j = i
            while j < len(ntext) and is_word_char(ntext[j]):
                j += 1
            words.append((ntext[i:j], i, j))
            i = j
        else:
            i += 1
    needed, best = max(4, int(WORDS_NEEDED * len(wanted) + 0.999)), None
    for at in range(len(words)):
        if words[at][0] != wanted[0] and words[at][0] not in wanted:
            continue
        window = [w[0] for w in words[at:at + len(wanted) + 3]]
        matched, first, last = in_order(wanted, window)
        if matched >= needed and (best is None or (matched, first - last) > (best[0], best[1] - best[2])):
            best = (matched, at + first, at + last)
    if best is None:
        return None, None
    return back[words[best[1]][1]], back[words[best[2]][2] - 1] + 1


def locate(text, quote, cache=None):
    """(start, end, how) with offsets into `text`, or (None, None, why)."""
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
            return first, last, "pieces"
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

TRIAGE_SCHEMA = {"type": "object", "required": ["exclude"], "properties": {"exclude": {"type": "array", "items": {
    "type": "object", "required": ["kind", "reason"], "properties": {"kind": {"type": "string"}, "reason": {"type": "string"}}}}}}

ADJUDICATE_SCHEMA = {"type": "object", "required": ["facts", "attributes", "contradictions"], "properties": {
    "unsupported": {"type": "array"},
    "facts": {"type": "array", "items": {"type": "object", "required": ["predicate", "object", "from"], "properties": {
        "predicate": {"type": "string"}, "object": {"type": "string"}, "qualifiers": {"type": ["string", "null"]}, "from": {"type": "array"}}}},
    "attributes": {"type": "array", "items": {"type": "object", "required": ["attribute", "value", "from"], "properties": {
        "attribute": {"type": "string"}, "value": {"type": ["string", "null"]}, "from": {"type": "array"}}}},
    "contradictions": {"type": "array", "items": {"type": "object", "required": ["note", "from"], "properties": {
        "note": {"type": "string"}, "from": {"type": "array"}}}}}}

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
- kind: one lowercase word: person, group, place, object, event, topic, or another if none fits
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
- qualifiers: a short phrase for role, manner, or condition, else null
- quote: one verbatim substring of the text that supports the fact, copied exactly as it appears, punctuation and all; an ellipsis (...) may skip words between two verbatim pieces
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


def adjudicate_prompt(name, kinds, facts, cells):
    return f"""Below is everything one document says about one entity, {name} ({', '.join(kinds)}): its facts, numbered, each with the unit it came from and the words it rests on, then its narrative cells in reading order. The units were read one at a time, so the facts repeat, overlap and sometimes disagree, and some are stated from the side of a lesser thing (marked inverse: the entity is the object of that statement). A line marked (about X) is what the document says of a lesser thing X that another line ties to the entity; it is not a fact of the entity itself: fold it into the object or qualifiers of the fact or attribute that names X (Boq, the richest Munchkin), and point "from" at it as well.

Write the entity's consolidated record:
- "facts": each durable relationship or fact stated once, with "predicate" (lowercase_snake_case, present tense, as the listed facts name it), "object", "qualifiers" (or null), and "from": the numbers of every listed fact it is drawn from. A fact drawn from nothing listed is not allowed.
- "attributes": what the entity is, has or is like, as "attribute", "value" (or null when the attribute stands on its own) and "from", folding the lesser things named in the facts into the entity itself: a house that has a cellar has the attribute cellar, not a relationship to one.
- "contradictions": where listed facts disagree, a one-sentence "note" and the "from" numbers; do not resolve them.
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


def derive_unit(doc, unit, ctx):
    text, base, cache = unit["text"], unit["start"], {}
    rec = {"unit_id": unit["unit_id"], "position": unit["position"], "label": unit["label"], "kind": unit["kind"],
           "entities": [], "dropped_entities": [], "mentions": [], "facts": [], "rejected_facts": [], "profile": [],
           "summary": None, "cells": [], "shared_spans": 0, "ambiguous_voice": 0, "empty": False}

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
                                "major": e.get("salience") == "major", "forms": forms, "mentions": len(spans)})
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
    reply = generate(fact_prompt(unit, names, majors), FACT_SCHEMA, "facts", ctx=ctx)
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
        elif start is None:
            rejection["category"] = how
        elif (subject, predicate, norm(obj)) in seen:
            rejection["category"] = "duplicate"
        else:
            seen.add((subject, predicate, norm(obj)))
            quote = text[start:end]
            voices = {author_at(doc, base + at) for at in occurrences(text, quote)}
            rec["ambiguous_voice"] += len(voices) > 1     # the same words in two voices: no voice is claimed
            rec["facts"].append({"fact_id": h(unit["unit_id"], subject, predicate, obj, base + start, base + end),
                                 "subject": subject, "predicate": predicate, "object": obj, "object_is_entity": obj in names,
                                 "qualifiers": f.get("qualifiers") or None, "unit_id": unit["unit_id"], "quote": quote,
                                 "quote_start": base + start, "quote_end": base + end, "matched_by": how,
                                 "valid_from": stated_date(f.get("valid_from"), quote), "valid_to": stated_date(f.get("valid_to"), quote),
                                 "author": None if len(voices) > 1 else author_at(doc, base + start),
                                 "voice_ambiguous": len(voices) > 1, "tier": LUNA})
            continue
        rec["rejected_facts"].append(rejection)

    # 3. summary and cells, one call, for the unit's major entities (the model's salience call)
    reply = generate(cells_prompt(unit, majors), CELLS_SCHEMA, "cells", ctx=ctx)
    if reply:
        rec["summary"] = " ".join(reply["summary"].split())
        for c in reply["cells"]:
            if c["entity"] in majors and c["text"].strip():
                rec["cells"].append({"entity": c["entity"], "text": " ".join(c["text"].split())})
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
# co-occurrence and profile scores. The judge takes ten pairs a call from the top of the queue,
# every cluster's dossier sent once; same unites, different stays apart, unsure waits for one
# last look against the finished clusters, where unsure means apart. Every decision is a
# ledger row with its evidence.
import difflib

TIER = {"shared_surface": 1.0, "is_a_link": 0.85, "shared_word": 0.5}
PAIRS_PER_CALL = 10
SCORE_WEIGHTS = (0.6, 0.25, 0.15)                  # name, co-occurrence, profile


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
    w_name, w_cooc, w_profile = SCORE_WEIGHTS
    return name, cooc, profile, w_name * name + w_cooc * cooc + w_profile * profile


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


def nominate(locals_, clusters):
    """The priority queue: every pair of locals from different units, not already one cluster,
    with at least one unit-major, a reason, and no anchor between them; strongest first.
    [(tier, combined score, a, b, reason, scores)]."""
    queue = []
    for a in locals_:
        for b in locals_[:a["id"]]:
            if b["ui"] == a["ui"] or not (a["major"] or b["major"]) or clusters.same(a["id"], b["id"]):
                continue
            reason = candidate_reason(a, b)
            if reason is None or anchored(a, b) or anchored(b, a):
                continue
            scores = score_pair(a, b, reason)
            queue.append((TIER[reason], scores[3], b["id"], a["id"], reason, scores))
    queue.sort(key=by_priority)
    return queue


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
    {pair number: (verdict, reason)} in batch order."""
    roots = sorted({r for pair in batch for r in pair})
    number = {r: n for n, r in enumerate(roots, 1)}
    members = {r: [l for l in locals_ if clusters.find(l["id"]) == r] for r in roots}
    dossiers = "\n\n".join(f"[{number[r]}]\n{dossier(members[r])}" for r in roots)
    pairs = "\n".join(f"PAIR {n}: [{number[a]}] and [{number[b]}]" for n, (a, b) in enumerate(batch, 1))
    reply = generate(JUDGE_PROMPT + "\nDOSSIERS\n" + dossiers + "\n\nPAIRS\n" + pairs, JUDGE_SCHEMA, "judge", model=TERRA, effort="medium", ctx=ctx)
    verdicts = {}
    for v in (reply or {}).get("verdicts", []):
        try:
            verdicts[int(v["pair"]) - 1] = (v["verdict"], v.get("reason", ""))
        except (TypeError, ValueError):
            pass
    return verdicts


def reconcile(records, ctx, watch=False):
    """The document's entities from its unit-locals: (entities, ledger, candidates, stats)."""
    locals_ = locals_of(records)
    clusters = Clusters(len(locals_))
    ledger, candidates = [], []

    # 1. the same proper name and kind: one entity, no judge
    first_named = {}
    for l in locals_:
        if not l["named"]:
            continue
        key = (norm(l["name"]), l["kind"])
        if key in first_named:
            clusters.unite(first_named[key]["id"], l["id"])
            ledger.append(ledger_row(locals_, first_named[key]["id"], l["id"], "same", "same_name", f"both named {l['name']!r}, both {l['kind']}"))
        else:
            first_named[key] = l

    # 2. the queue, and the scores logged for every pair in it
    queue = nominate(locals_, clusters)
    for tier, combined, i, j, reason, (name, cooc, profile, _) in queue:
        candidates.append({"a": locals_[i]["name"], "a_unit": locals_[i]["ui"], "b": locals_[j]["name"], "b_unit": locals_[j]["ui"],
                           "tier": tier, "reason": reason, "name_score": round(name, 3), "cooc_score": round(cooc, 3),
                           "profile_score": round(profile, 3), "combined": round(combined, 3)})
    if watch:
        print(f"judge: {len(locals_)} unit-locals, {len(ledger)} same-name unions, {len(queue)} pairs queued, {PAIRS_PER_CALL} a call")

    # 3. the judge, from the top of the queue; same unites, different stays apart, unsure waits
    apart, deferred, judged, calls = [], [], 0, 0

    def decide(batch, final):
        nonlocal judged, calls
        verdicts = judge(batch, locals_, clusters, ctx)
        calls += 1
        judged += len(batch)
        for n, (ra, rb) in enumerate(batch):
            verdict, reason = verdicts.get(n, ("unsure", "no verdict returned"))
            if verdict == "same":
                clusters.unite(ra, rb)
            elif verdict == "different" or final:
                apart.append((ra, rb))
            else:
                deferred.append((ra, rb))
            ledger.append(ledger_row(locals_, ra, rb, verdict, "judged again" if final else "judged", reason))

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

    batches([(i, j) for tier, combined, i, j, reason, scores in queue], final=False)

    # 4. the deferred pairs' last look against the finished clusters
    last_look, deferred = list(deferred), []
    batches(last_look, final=True)
    stats = {"locals": len(locals_), "candidate_pairs": len(queue), "judged_pairs": judged, "judge_calls": calls}
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
        entities.append({"name": best_name(counts), "kinds": sorted({l["kind"] for l in members}), "named": any(l["named"] for l in members),
                         "units": sorted({l["ui"] for l in members}), "unit_ids": unit_ids, "first_unit": unit_ids[0],
                         "names": sorted({l["name"] for l in members}), "surfaces": sorted({s for l in members for s in l["surfaces"]}),
                         "first_unit_of": first_unit_of, "members": [(l["ui"], l["name"]) for l in members],
                         "n_facts": sum(l["n_facts"] for l in members), "is_a": sorted({x for l in members for x in l["is_a"]})})
    return entities

# %%
# Block 9: fold the document.
#
# The abstract folds from the unit summaries under BUILD's bound (at most half the child words,
# capped at 400) with the fabrication check; a rejected fold is asked for once more with the
# missing names listed, then left unstamped. Salience is reassessed against the abstract:
# named there, as whole words, is major; with no abstract, two units or two facts decide. A
# major seen in fewer units and with fewer facts than the numbers below is demoted to minor.
# Majors get a dossier with an embedding and their own abstract.
DEMOTE_UNITS, DEMOTE_FACTS = 2, 3


def fold(what, children, ctx, stage="fold", allowed=None):
    """(text, missing names, limit); text is None when the fold was rejected twice. `allowed`
    are names the prompt itself supplies, which count as present."""
    child_words = sum(word_count(c) for c in children)
    limit = min(400, max(1, child_words // 2))
    asked = limit if limit < 12 else limit * 9 // 10
    prompt, missing = fold_prompt(what, children, asked), []
    for attempt in range(2):
        reply = generate(prompt, FOLD_SCHEMA, stage, model=TERRA, ctx=ctx)
        if not reply:
            return None, [], limit
        text = " ".join(reply["summary"].split())
        missing = missing_names(text, children + (allowed or []))
        over = word_count(text) > limit
        if not missing and not over:
            return text, [], limit
        if attempt == 0:
            complaint = []
            if missing:
                complaint.append(f"used names that do not appear in the records ({', '.join(missing[:8])})")
            if over:
                complaint.append(f"ran to {word_count(text)} words against a limit of {limit}")
            prompt += "\n\nYour previous summary " + " and ".join(complaint) + ". Write it again using only names from the records, within the limit."
    return None, missing or ["(over length)"], limit


def salience_order(item):
    return (not item[0], -item[1], -item[2])


def fold_document(doc, records, entities, ctx):
    out = {"abstract": None, "abstract_rejected": None, "majors": [], "minors": [], "dossiers": [], "entity_abstracts": [],
           "entity_abstract_rejected": [], "demoted": []}
    work = [r for r in records if r["summary"]]
    summaries = [f"[{r['label']}] {r['summary']}" for r in work]
    if len(summaries) == 1:                       # one summarised unit: its summary is the abstract, no call
        text, missing, limit, tier = work[0]["summary"], [], None, LUNA
    elif summaries:
        text, missing, limit = fold("one document", summaries, ctx)
        tier = TERRA
    else:
        text, missing, limit, tier = None, ["(no unit summaries)"], None, None
    if text:
        out["abstract"] = {"text": text, "children_hash": h(*summaries), "limit": limit, "tier": tier}
    else:
        out["abstract_rejected"] = missing

    # salience against the abstract; without one, the tie-breakers decide and the node says so
    abstract, ranked = (text or "").casefold(), []
    for e in entities:
        in_abstract = any(whole_word(s, abstract) for s in e["surfaces"] if len(s) >= 2) if text else None
        major = in_abstract if text else (len(e["units"]) >= 2 or e["n_facts"] >= 2)
        ranked.append((major, len(e["units"]), e["n_facts"], in_abstract, e))
    ranked.sort(key=salience_order)
    for major, n_units, n_facts, in_abstract, e in ranked:
        demoted = major and len(records) >= DEMOTE_UNITS and n_units < DEMOTE_UNITS and n_facts < DEMOTE_FACTS
        e["major"] = major and not demoted
        e["rank"] = {"in_abstract": in_abstract, "units": n_units, "facts": n_facts, "demoted": demoted}
        (out["majors"] if e["major"] else out["minors"]).append(e)
        if demoted:
            out["demoted"].append(e["name"])

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
    for e in out["majors"]:
        facts, cells = list(dict.fromkeys(facts_of.get(e["index"], []))), cells_of.get(e["index"], [])
        others = [n for n in e["names"] if n != e["name"]]
        text = "\n".join([f"name: {e['name']}", f"also: {', '.join(others)[:300]}", f"kinds: {', '.join(e['kinds'])}",
                          f"is: {', '.join(e['is_a'][:6])}", f"facts: {'; '.join(facts[:20])}", f"cells: {' '.join(cells)[:1500]}"])
        out["dossiers"].append({"entity": e["name"], "first_unit": e["first_unit"], "kinds": e["kinds"], "text": text, "children": facts + cells})
    if out["dossiers"] and KEY:
        for d, vector in zip(out["dossiers"], embed([d["text"] for d in out["dossiers"]], ctx=ctx)):
            d["embedding"] = vector

    def abstract_of(pair):
        """(text, missing names, tier); two records or fewer stand as the abstract without a call."""
        e, d = pair
        if not d["children"]:
            return None, [], None
        if len(d["children"]) <= 2:
            return " ".join(c.split("] ", 1)[-1] for c in d["children"]), [], LUNA
        text, missing, _ = fold(f"one entity, {e['name']}", d["children"], {**ctx, "entity": e["name"]}, stage="entity_abstract",
                                allowed=e["names"] + e["surfaces"])
        return text, missing, TERRA

    pairs = list(zip(out["majors"], out["dossiers"]))
    for (e, d), (text, missing, tier) in zip(pairs, in_parallel(abstract_of, pairs)):
        if not d["children"]:
            continue
        if text:
            out["entity_abstracts"].append({"entity": e["name"], "first_unit": e["first_unit"], "kinds": e["kinds"], "text": text,
                                            "children_hash": h(*d["children"]), "tier": tier})
        else:
            out["entity_abstract_rejected"].append({"entity": e["name"], "missing": missing})
    return out

# %%
# Block 10: the package. One JSONL file per document mirroring the raw layout, every line one
# record with a "record" field, ending in a completion record whose input_hash says which
# extractor output it came from. Minors have no node. A fact lands on the major that is its
# subject (forward), or on the major a minor's fact points at (inverse); a minor's own facts
# ride into the major it is tied to (about), under the first fact that ties them; a fact of a
# minor tied to no major is not stored.


def package_path(doc):
    parts = doc["source_uri"].split("/")
    return OUT / (parts[-2] if len(parts) > 1 else "misc") / (Path(parts[-1]).stem + ".jsonl")


def sidecar_path(doc):
    """Unit records checkpointed while a document is in flight."""
    return package_path(doc).with_suffix(".units.jsonl")


def input_hash(doc):
    return h(doc["doc_id"], *[u["unit_id"] for u in doc["units"]], INGESTOR)


def entity_key(entity):
    """What tells one document entity from another with the same name: first unit and kinds."""
    return entity["name"], entity["first_unit"], "/".join(entity["kinds"])


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


def write_package(doc, records, entities, folded, adjudicated, ledger, candidates, excluded, stats):
    path = package_path(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    scope, written_at, doc_node = doc["doc_id"], datetime.now(timezone.utc).isoformat(timespec="seconds"), h(doc["doc_id"], "document")
    lines = [{"record": "package", "doc_id": doc["doc_id"], "source_uri": doc["source_uri"], "ingestor": INGESTOR,
              "loader": doc.get("loader"), "input_hash": input_hash(doc), "written_at": written_at},
             {"record": "document", "doc_id": doc["doc_id"], "source_uri": doc["source_uri"], "sha256": doc["sha256"], "title": doc["title"],
              "author": doc["author"], "source_class": doc["source_class"], "ingested_at": doc["ingested_at"], "occurred_at": doc["occurred_at"],
              "loader": doc["loader"], "flags": doc.get("flags", []), "text_length": len(doc["text"])}]
    lines += [{"record": "unit", **u} for u in doc["units"]] + [{"record": "piece", **p} for p in doc["pieces"]]
    lines.append({"record": "node", "node_id": doc_node, "name": doc.get("title") or doc["source_uri"], "kind": "document",
                  "created_from_unit": doc["units"][0]["unit_id"] if doc["units"] else None, "provenance": {"ingestor": INGESTOR}})

    # nodes, aliases and edges for the majors; the map from a unit-local name to its node
    node_of, position_of = {}, {u["unit_id"]: u["position"] for u in doc["units"]}
    for e in entities:
        nid = node_id_of(doc, e) if e["major"] else None
        for ui, local_name in e["members"]:
            node_of[(ui, local_name)] = nid
        if not e["major"]:
            continue
        lines.append({"record": "node", "node_id": nid, "name": e["name"], "kind": "/".join(e["kinds"]),
                      "created_from_unit": min(e["unit_ids"], key=position_of.get),
                      "provenance": {"ingestor": INGESTOR, "salience": e["rank"], "names": e["names"][:12]}})
        for form, uid in e["first_unit_of"].items():
            lines.append({"record": "alias", "alias": form, "node_id": nid, "first_seen_unit": uid, "evidence_quote": None})
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
                lines.append({"record": "profile", "node_id": nid, "attribute": p["attribute"], "value": p["value"], "confidence": 0.5, "from_unit": p["from_unit"]})
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

    # the adjudicated record of each major, its predicates as the model wrote them
    for e in folded["majors"]:
        nid, result = node_id_of(doc, e), adjudicated.get(e["index"], {"facts": [], "attributes": [], "contradictions": []})
        for item in result["facts"]:
            lines.append({"record": "adjudicated_fact", "node_id": nid, "predicate": snake_case(item["predicate"]) or "related_to",
                          "object": item["object"], "qualifiers": item.get("qualifiers") or None, "from_facts": item["from_facts"], "tier": TERRA})
        for item in result["attributes"]:
            lines.append({"record": "attribute", "node_id": nid, "attribute": item["attribute"], "value": item["value"], "from_facts": item["from_facts"], "tier": TERRA})
        for item in result["contradictions"]:
            lines.append({"record": "contradiction", "node_id": nid, "note": item["note"], "from_facts": item["from_facts"]})

    # the document level: abstracts, dossiers, the ledger, the candidates
    if folded["abstract"]:
        lines.append({"record": "abstract", "node_id": doc_node, "scope_id": scope, "text": folded["abstract"]["text"],
                      "children_hash": folded["abstract"]["children_hash"], "tier": folded["abstract"]["tier"], "updated_at": written_at})
    for a in folded["entity_abstracts"]:
        lines.append({"record": "abstract", "node_id": node_id_of(doc, {"name": a["entity"], "first_unit": a["first_unit"], "kinds": a["kinds"]}),
                      "scope_id": scope, "text": a["text"], "children_hash": a["children_hash"], "tier": a["tier"], "updated_at": written_at})
    for d in folded["dossiers"]:
        lines.append({"record": "dossier", "node_id": node_id_of(doc, {"name": d["entity"], "first_unit": d["first_unit"], "kinds": d["kinds"]}),
                      "text": d["text"], "embedding_model": EMBED_MODEL if "embedding" in d else None, "embedding": d.get("embedding")})
    lines += [{"record": "ledger", **entry} for entry in ledger] + [{"record": "candidate", **entry} for entry in candidates]

    # facts, each under the major it lands on; a fact the adjudication set aside is ranked unsupported
    landed, landed_ids, riding = landings(records, folded), set(), 0
    unsupported = {stored_id for result in adjudicated.values() for stored_id in result.get("unsupported", [])}
    for e in folded["majors"]:
        nid = node_id_of(doc, e)
        for f, direction, label, stored_id, tying in landed[e["index"]]:
            landed_ids.add(f["fact_id"])
            riding += direction == "about"
            object_node = node_of.get((position_of[f["unit_id"]], f["object"])) if f["object_is_entity"] else None
            if direction == "forward":
                obj, is_node = object_node or f["object"], object_node is not None
            else:                                     # inverse: the minor's name is the value; about: the minor's own fact
                obj, is_node = (f["subject"] if direction == "inverse" else f["object"]), False
            lines.append({"record": "fact", "fact_id": stored_id, "subject": nid, "predicate": f["predicate"], "object": obj,
                          "object_is_node": is_node, "direction": direction, "qualifiers": f["qualifiers"],
                          "rank": "unsupported" if stored_id in unsupported else "active",
                          "unit_id": f["unit_id"], "quote": f["quote"], "quote_start": f["quote_start"], "quote_end": f["quote_end"],
                          "valid_from": f["valid_from"], "valid_to": f["valid_to"], "tier": f["tier"], "author": f["author"],
                          "provenance": {"ingestor": INGESTOR, "matched_by": f["matched_by"], "subject_name": f["subject"],
                                         "voice_ambiguous": f["voice_ambiguous"], "rides_on": tying,
                                         "copy_of": f["fact_id"] if direction == "about" else None}})
    lines.append({"record": "predicate_census", "predicates": predicate_census(records)})
    for r in records:
        lines += [{"record": "rejection", "stage": "facts", "unit_id": r["unit_id"], **x} for x in r["rejected_facts"]]
        lines += [{"record": "rejection", "stage": "entities", "unit_id": r["unit_id"], **x} for x in r["dropped_entities"]]

    counts = {"units": len(records), "entities": len(entities), "majors": len(folded["majors"]), "minors": len(folded["minors"]),
              "mentions": sum(len(r["mentions"]) for r in records), "facts_kept": sum(len(r["facts"]) for r in records),
              "facts_stored": sum(1 for l in lines if l["record"] == "fact"),
              "facts_minor_subject": sum(len(r["facts"]) for r in records) - len(landed_ids), "facts_riding": riding,
              "facts_rejected": sum(len(r["rejected_facts"]) for r in records), "cells": sum(1 for l in lines if l["record"] == "cell"),
              "shared_spans": sum(r["shared_spans"] for r in records), "ambiguous_voice": sum(r["ambiguous_voice"] for r in records),
              "empty_units": sum(r["empty"] for r in records), "units_excluded": len(excluded), "demoted": len(folded["demoted"]),
              "adjudicated_facts": sum(1 for l in lines if l["record"] == "adjudicated_fact"),
              "attributes": sum(1 for l in lines if l["record"] == "attribute"),
              "contradictions": sum(1 for l in lines if l["record"] == "contradiction"),
              "adjudication_dropped": sum(a.get("dropped", 0) for a in adjudicated.values()),
              "adjudications_skipped": sum(1 for a in adjudicated.values() if a.get("skipped")),
              "adjudications_rejected": sum(1 for a in adjudicated.values() if a.get("rejected")),
              "facts_unsupported": sum(1 for l in lines if l["record"] == "fact" and l["rank"] == "unsupported"),
              "predicates_distinct": len({snake_case(item["predicate"]) for a in adjudicated.values() for item in a.get("facts", [])}),
              "abstract": folded["abstract"] is not None}
    lines.append({"record": "completion", "doc_id": doc["doc_id"], "input_hash": input_hash(doc), "ingestor": INGESTOR, "counts": counts,
                  "stats": stats, "empty": counts["facts_stored"] == 0 and counts["cells"] == 0, "excluded": excluded,
                  "demoted": folded["demoted"], "abstract_rejected": folded["abstract_rejected"],
                  "entity_abstract_rejected": folded["entity_abstract_rejected"]})
    path.write_text("\n".join(json.dumps(l, ensure_ascii=False) for l in lines) + "\n", encoding="utf-8", newline="\n")
    return path, counts


def completed(doc):
    """The completion record of an existing package for this exact input, else None."""
    path = package_path(doc)
    if not path.exists():
        return None
    rows = read_own_jsonl(path)
    if rows and rows[-1].get("record") == "completion" and rows[-1].get("input_hash") == input_hash(doc):
        return rows[-1]
    return None

# %%
# Block 11: the pipeline as one function, ingest(doc, diag).
#
# The steps in order: triage (which kinds of unit to read), derive_unit for each unit kept,
# each checkpointed as it lands, then, all at the end, reconcile, fold_document, adjudicate,
# write_package. `diag` is a dict of flags naming what to print as it
# happens: triage, units, entities, facts, rejections, cells, reconcile, ledger, fold,
# adjudicate, package. A finished package for the same input is skipped; a document stopped
# mid-way resumes from the units its sidecar holds. Every document appends an entry to
# ingest.log and a row to manifest.jsonl; the receipt sums the packages on disk.
LOG, MANIFEST = OUT / "ingest.log", OUT / "manifest.jsonl"
DIAG_ALL = {"triage": True, "units": True, "entities": True, "facts": True, "rejections": True, "cells": True,
            "reconcile": True, "ledger": False, "fold": True, "adjudicate": True, "package": True}
RESULTS = []                                  # (source_uri, records, counts, stats) for every document this session ingested
ADJUDICATE_MIN_FACTS = 4                      # fewer than this, all in one unit: nothing to consolidate, the raw facts stand


def append_sidecar(doc, row):
    side = sidecar_path(doc)
    side.parent.mkdir(parents=True, exist_ok=True)
    with side.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ingestor": INGESTOR, "input_hash": input_hash(doc), **row}, ensure_ascii=False) + "\n")


def checkpointed(doc):
    """What a previous attempt left in its sidecar, when it belongs to this input: (the kinds
    triage left out, the unit records in order, their cost, their calls, the triage flags)."""
    side = sidecar_path(doc)
    rows = [row for row in read_own_jsonl(side) if row.get("ingestor") == INGESTOR and row.get("input_hash") == input_hash(doc)] if side.exists() else []
    if not rows or "triage" not in rows[0]:
        return None, [], 0.0, 0, []
    excluded = rows[0]["triage"]
    kept_ids = [u["unit_id"] for u in doc["units"] if unit_kind(doc, u) not in excluded]
    kept, cost, calls = [], rows[0].get("cost", 0.0), rows[0].get("calls", 0)
    for row in rows[1:]:
        if "rec" in row and len(kept) < len(kept_ids) and row["rec"]["unit_id"] == kept_ids[len(kept)]:
            kept.append(row["rec"])
            cost += row.get("cost", 0.0)
            calls += row.get("calls", 0)
    return excluded, kept, cost, calls, rows[0].get("flags", [])


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
    if sum(len(kinds[kind]) for kind in excluded) >= len(doc["units"]):
        flags.append(f"triage would leave out every unit ({len(doc['units'])}); ignored")
        excluded = {}
    return excluded, flags


def valid_sources(numbers, n):
    """The fact numbers an adjudicated item points at, as distinct integers within 1..n."""
    good = []
    for x in numbers if isinstance(numbers, list) else []:
        if isinstance(x, str) and x.strip().isdigit():
            x = int(x)
        if isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= n and x not in good:
            good.append(x)
    return good


def adjudicate(records, folded, ctx, watch=False):
    """One call per document-major over its landed facts and its cells; the consolidated facts,
    attributes and contradictions point at the raw facts by number. Keyed by entity index."""
    member_index = {(ui, local_name): e["index"] for e in folded["majors"] for ui, local_name in e["members"]}
    landed, cells_of = landings(records, folded), {e["index"]: [] for e in folded["majors"]}
    for r in records:
        for c in r["cells"]:
            if member_index.get((r["position"], c["entity"])) is not None:
                cells_of[member_index[(r["position"], c["entity"])]].append(f"[{r['label']}] {c['text']}")

    def adjudicate_one(e):
        raws = landed[e["index"]]
        result = {"facts": [], "attributes": [], "contradictions": [], "unsupported": [], "dropped": 0, "raw": len(raws),
                  "riding": sum(1 for x in raws if x[1] == "about"), "skipped": None, "rejected": False}
        if not raws:
            return result
        if len(raws) < ADJUDICATE_MIN_FACTS and len({f["unit_id"] for f, direction, label, stored_id, tying in raws}) == 1:
            result["skipped"] = f"fewer than {ADJUDICATE_MIN_FACTS} facts, one unit: the raw facts stand"
            return result
        listing = []
        for n, (f, direction, label, stored_id, tying) in enumerate(raws, 1):
            if direction == "forward":
                line = f"{n}. {e['name']} {f['predicate']} {f['object']}"
            elif direction == "inverse":
                line = f"{n}. (inverse) {f['subject']} {f['predicate']} {e['name']}"
            else:
                line = f"{n}. (about {f['subject']}) {f['subject']} {f['predicate']} {f['object']}"
            listing.append(line + (f" [{f['qualifiers']}]" if f["qualifiers"] else "") + f"  ({label}: \"{' '.join(f['quote'].split())[:120]}\")")
        reply = generate(adjudicate_prompt(e["name"], e["kinds"], listing, cells_of[e["index"]]), ADJUDICATE_SCHEMA, "adjudicate",
                         model=TERRA, effort="medium", ctx={**ctx, "entity": e["name"]})
        result["rejected"] = reply is None
        ids = [stored_id for f, direction, label, stored_id, tying in raws]
        result["unsupported"] = [ids[n - 1] for n in valid_sources((reply or {}).get("unsupported"), len(ids))]
        for key in ("facts", "attributes", "contradictions"):
            for item in (reply or {}).get(key, []):
                sources = valid_sources(item.get("from"), len(ids))
                if not sources:
                    result["dropped"] += 1
                    continue
                kept = {k: v for k, v in item.items() if k != "from"}
                kept["from_facts"] = [ids[n - 1] for n in sources]
                result[key].append(kept)
        return result

    if watch:
        print(f"adjudicate: {len(folded['majors'])} majors, {WORKERS} at a time; fewer than {ADJUDICATE_MIN_FACTS} facts in one unit is not sent")
    return {e["index"]: result for e, result in zip(folded["majors"], in_parallel(adjudicate_one, folded["majors"]))}


def show_unit(rec, unit, diag, unit_cost, total_cost):
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
    if diag.get("entities"):
        for e in rec["entities"]:
            print(f"    {e['name'][:34]:<34} {e['kind'][:9]:<9} {'named' if e['named'] else 'unnamed':<8}"
                  f" {'major' if e['major'] else 'minor':<6} x{e['mentions']:<3} forms: {' | '.join(e['forms'][:4])[:70]}")
        for d in rec["dropped_entities"]:
            print(f"    DROPPED {d['name'][:34]}: {d['why']} {d['forms'][:3]}")
    if diag.get("facts"):
        for f in rec["facts"]:
            print(f"    {f['subject']} -{f['predicate']}-> {f['object']}{' [' + f['qualifiers'] + ']' if f['qualifiers'] else ''}"
                  f"  ({f['matched_by']}{', voice ambiguous' if f['voice_ambiguous'] else ''})  \"{' '.join(f['quote'].split())[:90]}\"")
    if diag.get("rejections"):
        for x in rec["rejected_facts"]:
            print(f"    REJECTED {x['category']}: {x['subject']} -{x['predicate']}-> {x['object']}  \"{' '.join(x['quote'].split())[:90]}\"")
    if diag.get("cells") and rec["summary"]:
        print(f"    SUMMARY {rec['summary']}")
        for c in rec["cells"]:
            print(f"    [{c['entity']}] {c['text']}")


def show_reconcile(entities, ledger, stats, diag):
    by_how = {}
    for entry in ledger:
        by_how[f"{entry['how']} {entry['verdict']}"] = by_how.get(f"{entry['how']} {entry['verdict']}", 0) + 1
    print(f"reconcile: {stats['locals']} unit-locals -> {len(entities)} document entities; ledger {counts_text(by_how)};"
          f" {stats['candidate_pairs']} pairs queued, {stats['judged_pairs']} judged in {stats['judge_calls']} calls")
    if diag.get("ledger"):
        for entry in ledger:
            print(f"    {entry['verdict']:<9} {entry['how']:<12} {entry['a'][:28]:<28} (u{entry['a_unit']}) ~ {entry['b'][:28]:<28} (u{entry['b_unit']})  {str(entry['evidence'])[:70]}")


def show_fold(folded):
    if folded["abstract"]:
        print(f"abstract ({word_count(folded['abstract']['text'])} words, limit {folded['abstract']['limit']}): {folded['abstract']['text']}")
    else:
        print(f"abstract REJECTED: {folded['abstract_rejected']}")
    print(f"salience: {len(folded['majors'])} major, {len(folded['minors'])} minor, {len(folded['demoted'])} demoted;"
          f" {len(folded['entity_abstracts'])} entity abstracts, {len(folded['entity_abstract_rejected'])} rejected")
    if folded["demoted"]:
        print(f"    demoted to minor (fewer than {DEMOTE_UNITS} units and {DEMOTE_FACTS} facts): {', '.join(folded['demoted'])[:200]}")
    for x in folded["entity_abstract_rejected"]:
        print(f"    entity abstract REJECTED for {x['entity']}: names not in its records {x['missing']}")
    for e in folded["majors"]:
        why = "in abstract" if e["rank"]["in_abstract"] else ("by tie-break" if e["rank"]["in_abstract"] is None else "?")
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
          f" {total['contradictions']} contradictions; {total['unsupported']} raw facts set aside as unsupported by their passage;"
          f" {total['dropped']} dropped; {sum(1 for a in adjudicated.values() if a['skipped'])} majors left to their raw facts")
def ingest(doc, ctx=None, diag=None):
    """One document, start to finish: the units on their own, then everything merged at the end."""
    diag, ctx = diag or {}, {"doc": doc["source_uri"], **(ctx or {})}
    calls_before, spend_before = len(CALLS), spend()

    # which kinds of unit to read: the sidecar's answer when resuming, else the judge's
    excluded, records, cost_before, calls_before_stop, flags = checkpointed(doc)
    if excluded is None:
        if sidecar_path(doc).exists():
            sidecar_path(doc).unlink()
        spend_at, calls_at = spend(), len(CALLS)
        excluded, flags = triage(doc, ctx)
        append_sidecar(doc, {"triage": excluded, "flags": flags, "cost": round(spend() - spend_at, 6), "calls": len(CALLS) - calls_at})
    kept, left_out = [], []
    for u in doc["units"]:
        kind = unit_kind(doc, u)
        if kind in excluded:
            left_out.append({"position": u["position"], "kind": kind, "label": u["label"], "reason": excluded[kind]})
        else:
            kept.append(u)
    if diag.get("triage"):
        counts = {}
        for u in doc["units"]:
            counts[unit_kind(doc, u)] = counts.get(unit_kind(doc, u), 0) + 1
        print(f"triage: {counts_text(counts)}; " + (f"left out {len(left_out)} unit(s)" if left_out else "nothing left out"))
        for kind, reason in excluded.items():
            print(f"    {kind}: {reason}")
        for flag in flags:
            print(f"    FLAG {flag}")

    # the units, each on its own, checkpointed as it lands
    if records and diag.get("units"):
        print(f"resuming {doc['source_uri']} from {len(records)} checkpointed units")
    for u in kept[len(records):]:
        unit = {**u, "text": doc["text"][u["start"]:u["end"]], "kind": unit_kind(doc, u)}
        spend_at, calls_at = spend(), len(CALLS)
        rec = derive_unit(doc, unit, {**ctx, "unit": u["position"]})
        records.append(rec)
        append_sidecar(doc, {"rec": rec, "cost": round(spend() - spend_at, 6), "calls": len(CALLS) - calls_at})
        if diag.get("units"):
            show_unit(rec, unit, diag, spend() - spend_at, spend() - spend_before)

    # the document, all at the end: reconcile, fold, salience, adjudicate, predicates, write
    entities, ledger, candidates, stats = reconcile(records, ctx, watch=bool(diag.get("reconcile")))
    if diag.get("reconcile"):
        show_reconcile(entities, ledger, stats, diag)
    folded = fold_document(doc, records, entities, ctx)
    if diag.get("fold"):
        show_fold(folded)
    adjudicated = adjudicate(records, folded, ctx, watch=bool(diag.get("adjudicate")))
    if diag.get("adjudicate"):
        show_adjudication(folded, adjudicated)
    stats.update({"calls": len(CALLS) - calls_before + calls_before_stop, "cost": round(spend() - spend_before + cost_before, 4),
                  "matched_by": {}, "rejected_by": {}, "units_excluded": len(left_out), "triage_flags": flags})
    for r in records:
        for f in r["facts"]:
            stats["matched_by"][f["matched_by"]] = stats["matched_by"].get(f["matched_by"], 0) + 1
        for x in r["rejected_facts"]:
            stats["rejected_by"][x["category"]] = stats["rejected_by"].get(x["category"], 0) + 1
    path, counts = write_package(doc, records, entities, folded, adjudicated, ledger, candidates, left_out, stats)
    if sidecar_path(doc).exists():
        sidecar_path(doc).unlink()
    if diag.get("package"):
        print(f"package {path}: {counts}")
    RESULTS.append((doc["source_uri"], records, counts, stats))
    return path, counts, stats, records, entities, folded


def note(text):
    print(text)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(text + "\n\n")


def run(uris, diag=None, stop_on_error=False):
    if not KEY:
        raise SystemExit("no OPENAI_API_KEY: set it in the environment, or attach it as a Kaggle secret")
    done = skipped = 0
    for uri in uris:
        if uri not in BY_URI:
            note(f"not in export: {uri}")
            continue
        spend_before = spend()
        try:
            doc = load_document(uri, BY_URI, UNITS, PIECES)
            if completed(doc):
                skipped += 1
                continue
            if diag and diag.get("units"):
                print(f"\n=== {uri}: {len(doc['units'])} units, {len(doc['text']):,} chars{' (text rebuilt from the PDF)' if doc['text_rebuilt'] else ''},"
                      f" author {doc.get('author')!r}, date {doc.get('occurred_at')} ===")
            path, counts, stats, records, entities, folded = ingest(doc, diag=diag)
            with MANIFEST.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"doc_id": doc["doc_id"], "source_uri": uri, "package": str(path.relative_to(OUT)).replace("\\", "/"),
                                    "input_hash": input_hash(doc), "counts": counts, "cost": stats["cost"]}) + "\n")
            abstract = folded["abstract"]["text"][:200] if folded["abstract"] else f"REJECTED {folded['abstract_rejected']}"
            entry = [f"{uri}  units {counts['units']}  entities {counts['entities']} ({counts['majors']} major)  mentions {counts['mentions']}"
                     f"  facts {counts['facts_kept']} kept / {counts['facts_rejected']} rejected / {counts['facts_stored']} stored"
                     f"  cells {counts['cells']}  calls {stats['calls']}  ${stats['cost']:.3f}",
                     f"    matched {stats['matched_by']}  rejected {stats['rejected_by']}  locals {stats['locals']}"
                     f" pairs {stats['candidate_pairs']} judged {stats['judged_pairs']}", f"    abstract: {abstract}"]
            entry += [f"    {e['name'][:36]:<36} {'/'.join(e['kinds'])[:16]:<16} units {len(e['units']):>3} facts {e['n_facts']:>3}" for e in folded["majors"][:12]]
            note("\n".join(entry + [f"    -> {path}"]))
        except SpendStop as e:
            note(f"{uri}: {e} after ${spend() - spend_before:.3f} on this document; its finished units are checkpointed and the run stops here")
            break
        except Exception as e:
            if stop_on_error:
                raise
            note(f"{uri}  ERROR {type(e).__name__}: {e}")
            continue
        done += 1
    print(f"done {done}  skipped (already complete) {skipped}  spent ${spend():.2f} this session")
    return done, skipped


def receipt():
    """Sums over every package on disk, plus the calls this session logged."""
    rec = {"ingestor": INGESTOR, "documents": 0, "by_group": {}, "counts": {}, "matched_by": {}, "rejected_by": {}, "cost_of_packages": 0.0,
           "cost_this_session": round(spend(), 4), "calls_this_session": len(CALLS), "calls_by_stage": {},
           "schema_rejections_this_session": len(REJECTIONS), "schema_retries_this_session": len(RETRIES), "in_flight_sidecars": []}
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
        rec["by_group"][path.parent.name] = rec["by_group"].get(path.parent.name, 0) + 1
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
    """A package's records grouped by record type."""
    by = {}
    for row in read_jsonl(Path(path)):
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
    """The final roll-up of one package."""
    by = read_package(path)
    doc, units = by["document"][0], sorted(by.get("unit", []), key=position_of_row)
    label_of = {u["unit_id"]: f"[{u['position']}] {u['label']}" for u in units}
    position = {u["unit_id"]: u["position"] for u in units}
    doc_node = h(doc["doc_id"], "document")
    abstracts = {a["node_id"]: a["text"] for a in by.get("abstract", [])}
    cells_of, facts_of = grouped(by.get("cell", []), "node_id"), grouped(by.get("fact", []), "subject")
    adjudicated_of, attributes_of = grouped(by.get("adjudicated_fact", []), "node_id"), grouped(by.get("attribute", []), "node_id")
    contradictions_of, aliases_of, profile_of = grouped(by.get("contradiction", []), "node_id"), grouped(by.get("alias", []), "node_id"), grouped(by.get("profile", []), "node_id")
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
        for attribute, value in dict.fromkeys((p["attribute"], p["value"]) for p in profile_of.get(nid, [])):
            print(f"profile: {attribute} = {value}")
        if nid in abstracts:
            print(f"abstract: {abstracts[nid]}")
        if cells_of.get(nid):
            print("narrative:")
            for c in sorted(cells_of[nid], key=cell_position(position)):
                print(f"    {label_of.get(c['unit_id'], c['unit_id'])}: {c['text']}")
        if adjudicated_of.get(nid):
            print(f"consolidated facts ({len(adjudicated_of[nid])}):")
            for a in adjudicated_of[nid]:
                raw = f" (raw {a['predicate_raw']})" if a["predicate_raw"] != a["predicate"] else ""
                print(f"    {a['predicate']}{raw} -> {a['object']}{' [' + a['qualifiers'] + ']' if a.get('qualifiers') else ''}  <- {len(a['from_facts'])} raw")
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


def draw_graph(path, show=True):
    """The majors of one package as a graph, the 09-02 demo's way: nodes sized by how many
    units they appear in, an edge for every pair that shares a fact (a consolidated fact where
    the major has them, else a raw one), labelled with one of its predicates."""
    import networkx as nx
    import matplotlib
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
    if not show:
        matplotlib.use("Agg")
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
    if show:
        plt.show()
    plt.close()
    print(f"graph of {doc['title'] or doc['source_uri']}: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges; saved {png}")
    return G

# %%
# Block 13: the run, Oz book 1.
#
# RUN names the documents, by title or by the end of their source_uri; DIAG says what to print
# as each unit lands; SPEND_STOP ends the run past that many dollars, the document in flight
# keeping its finished units in a sidecar for next time. For reference, the 09-02 demo on Oz
# book 1: v3 632 entities, 969 facts, 53 dropped, $1.26; the 0.4 run of 09-06: 358 entities
# (38 major), 869 facts, 74 rejected, $2.23. Each document ends in its roll-up.
RUN = ["The Wonderful Wizard of Oz"]
DIAG = dict(DIAG_ALL)
SPEND_STOP = 5.00


def run_and_roll_up(uris, diag, top=5):
    """The run, then the roll-up of every package that exists for the documents named."""
    try:
        run(uris, diag=diag)
    finally:
        print(json.dumps(receipt(), indent=1))
    for uri in uris:
        path = package_path({"source_uri": uri})
        if path.exists():
            rollup(path, top=top)


if __name__ == "__main__":
    uris = targets(RUN)
    print(f"ingesting {len(uris)} documents, stop at ${SPEND_STOP:.2f}: {[BY_URI[u]['title'] or u for u in uris]}")
    run_and_roll_up(uris, DIAG)

# %%
# Block 14: the run, five papers, Zep first. The papers' text is withheld from the public
# export; block 1 rebuilds it from the private papers dataset, which must be attached.
import random

PAPERS_TO_RUN, SEED, ALWAYS = 5, 494, ["rasmussen2025-zep.pdf"]
SPEND_STOP = 8.00

if __name__ == "__main__" and PAPERS_TO_RUN:
    chosen = [find_document(name) for name in ALWAYS]
    others = sorted(u for u in BY_URI if u.endswith(".pdf") and u not in chosen)
    random.Random(SEED).shuffle(others)
    chosen += others[:PAPERS_TO_RUN - len(chosen)]
    print(f"papers: {[BY_URI[u]['title'] or u for u in chosen]}; stop at ${SPEND_STOP:.2f} for the session")
    run_and_roll_up(chosen, DIAG_ALL)

# %%
# Block 15: the graphs. One knowledge graph per document ingested this session, drawn the
# 09-02 demo's way and saved beside the packages. Needs networkx and matplotlib, which Kaggle has.
if __name__ == "__main__":
    for uri, records_, counts_, stats_ in RESULTS:
        if package_path({"source_uri": uri}).exists():
            draw_graph(package_path({"source_uri": uri}))
