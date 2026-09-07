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
# Every step is a function. Block 1 finds the files. Block 2 is the model interface and block 3
# tests the connection. Block 4 is ids and helpers. Block 5 is the quote gate. Block 6 holds the
# prompts. Block 7 derives one unit and block 8 reconciles a document's entities. Block 9 folds
# the abstract and decides salience. Block 10 writes the package. Block 11 is the pipeline as one
# function: a judge decides which kinds of unit to read, the units are derived, the entities
# reconciled, the abstract folded, each major adjudicated, the package written, with flags that
# print each step as it happens. Block 12 names documents and block 13 is the run.
#
# **On Kaggle:** attach the export dataset (`jhffmn/it494-factledger-step0`) and, to read the
# reference papers whose text it withholds, the private PDFs (`jhffmn/it494-reference-papers`);
# attach `OPENAI_API_KEY` under Add-ons > Secrets, turn Internet on under Settings, run block 3 to see
# the connection work, set `RUN` and `SPEND_STOP` in block 13, and Save & Run All. The packages
# land under `/kaggle/working/packages` and are kept as the version's output. To continue a
# stopped run, make a dataset from that output and attach it: finished packages are copied in
# and skipped.

# %%
# Block 1: where things are, and how a document is read.
#
# The export is read from the first of these that exists: the EXPORT environment variable,
# the Kaggle dataset, the local folder. Packages are written under OUT. documents.jsonl holds
# every byte of the corpus, so it is indexed once (doc_id, title, byte offset per document)
# and a document is read back with one seek when it is wanted.
import hashlib
import json
import os
import shutil
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

INGESTOR = "factledger-ingestor 0.4"
KAGGLE_EXPORTS = (Path("/kaggle/input/datasets/jhffmn/it494-factledger-step0"),   # Kaggle mounts a dataset at either
                  Path("/kaggle/input/it494-factledger-step0"))
LOCAL_EXPORT = Path("data/export")
KAGGLE_OUT = Path("/kaggle/working/packages")
LOCAL_OUT = Path("data/packages")
KAGGLE_PAPERS = (Path("/kaggle/input/datasets/jhffmn/it494-reference-papers"),   # the private PDFs, either mount
                 Path("/kaggle/input/it494-reference-papers"))
LOCAL_PAPERS = Path("papers")

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
    """The folder holding the reference papers' PDFs, or None. The public export withholds
    their text, so it is read back from the PDF when one of them is wanted."""
    if os.environ.get("PAPERS"):
        return Path(os.environ["PAPERS"])
    for path in KAGGLE_PAPERS + (LOCAL_PAPERS,):
        if path.exists():
            return path
    return None


def index_papers():
    """doc_id -> the papers.jsonl row (file, pdf_sha256, source_url) for every document whose
    text the export withholds; empty when the export withholds nothing."""
    path = EXPORT / "papers.jsonl"
    if not path.exists():
        return {}
    return {row["doc_id"]: row for row in read_jsonl(path)}


def pdf_reader():
    """PyMuPDF, the extractor's one dependency, imported only when a withheld text is wanted."""
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf                # PyMuPDF before 1.24.3 has only its old module name
        except ImportError:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pymupdf"], check=True)
            import pymupdf
    return pymupdf


def pdf_text(data):
    """The extractor's reading of a PDF, kept verbatim so the export's offsets resolve: the text
    layer page by page, pages joined with a newline."""
    doc = pdf_reader().open(stream=data, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def withheld_text(doc):
    """The text of a document the export withholds: the PDF that papers.jsonl names, found
    under PAPERS, checked against the recorded sha256, read the extractor's way."""
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


EXPORT = choose_export()
OUT = choose_out()
PAPERS = choose_papers()
OUT.mkdir(parents=True, exist_ok=True)


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


def seed_from_prior_output():
    """On Kaggle a new session starts with an empty working folder. If an earlier run's output
    was attached as a dataset, its packages are copied in first, so they are skipped rather than
    paid for again. The earlier run's own logs are not copied. Returns how many files came in."""
    copied = 0
    root = Path("/kaggle/input")
    if not root.exists():
        return copied
    for folder in root.rglob("packages"):
        if not folder.is_dir():
            continue
        for src in folder.rglob("*.jsonl"):
            if src.name in ("manifest.jsonl", "calls.jsonl", "rejections.jsonl"):
                continue
            dst = OUT / src.relative_to(folder)
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                copied += 1
    return copied


def index_documents():
    """source_uri -> {doc_id, title, author, offset}. Each line is parsed once and its text is
    dropped; the byte offset lets load_document seek straight to it later."""
    index = {}
    offset = 0
    with (EXPORT / "documents.jsonl").open("rb") as f:
        for raw in f:
            if raw.strip():
                doc = json.loads(raw.decode("utf-8"))
                index[doc["source_uri"]] = {"doc_id": doc["doc_id"], "title": doc["title"],
                                            "author": doc["author"], "offset": offset}
            offset += len(raw)
    return index


def position_of_row(row):
    return row["position"]


def group_by_document(rows):
    """The units (or pieces) of the export grouped by doc_id, each group in position order."""
    grouped = {}
    for row in rows:
        grouped.setdefault(row["doc_id"], []).append(row)
    for group in grouped.values():
        group.sort(key=position_of_row)
    return grouped


def load_document(uri, by_uri, units, pieces):
    """The document with its text, its units in order and its pieces in order. One seek."""
    entry = by_uri[uri]
    with (EXPORT / "documents.jsonl").open("rb") as f:
        f.seek(entry["offset"])
        doc = json.loads(f.readline().decode("utf-8"))
    assert doc["doc_id"] == entry["doc_id"]
    doc["units"] = units.get(doc["doc_id"], [])
    doc["pieces"] = pieces.get(doc["doc_id"], [])
    doc["text_rebuilt"] = doc["text"] is None
    if doc["text_rebuilt"]:                       # the export withholds it: read the PDF the extractor's way
        doc["text"] = withheld_text(doc)
        if doc["units"] and doc["units"][-1]["end"] != len(doc["text"]):
            raise ValueError(f"{uri}: the rebuilt text has {len(doc['text']):,} chars but the units end at"
                             f" {doc['units'][-1]['end']:,}; the PDF was read differently from the extractor")
    for u in doc["units"]:                        # every unit must be a real slice of the text
        assert 0 <= u["start"] < u["end"] <= len(doc["text"]), (uri, u["position"])
        assert doc["text"][u["start"]:u["end"]].strip(), (uri, u["position"])
    return doc


def find_document(name):
    """The source_uri of the document called `name`: by title (case ignored, an exact title
    first, then a title containing it), else by the end of its source_uri. None when nothing
    matches; when several titles match, they are listed and the first is taken."""
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


SEEDED = seed_from_prior_output()
BY_URI = index_documents()
PAPERS_ROWS = index_papers()
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
# that name. Raw HTTP to the API. The API rejects temperature, so reasoning_effort steers it.
# Every call is appended to CALLS and to calls.jsonl on disk the moment it returns, with model,
# tokens, latency and cost. A reply that does not fit its schema is asked for once more with
# the error appended, then counted as a rejection. A timeout, a dropped connection, a 429 or a
# 5xx is retried three times; a 429 for exhausted quota ends the run like the spend stop. The
# stop is checked before every call.
import http.client
import urllib.error
import urllib.request

LUNA = "gpt-5.6-luna"                      # derive, fold
TERRA = "gpt-5.6-terra"                    # the judge
EMBED_MODEL = "text-embedding-3-small"
PRICE = {LUNA: (0.20, 1.20), TERRA: (2.00, 12.00), EMBED_MODEL: (0.02, 0.0)}   # $ per million tokens in, out
SPEND_STOP = float(os.environ.get("SPEND_STOP", "25"))

KEY = os.environ.get("OPENAI_API_KEY")
if not KEY:
    try:
        from kaggle_secrets import UserSecretsClient
        KEY = UserSecretsClient().get_secret("OPENAI_API_KEY")
    except ImportError:                      # not on Kaggle
        KEY = None
    except Exception:                        # on Kaggle, but the secret is not attached to this notebook
        KEY = None
        print("OPENAI_API_KEY is not attached to this notebook: Add-ons > Secrets, tick Attach; Settings > Internet on")

CALLS = []                                 # every call this session
REJECTIONS = []                            # every reply rejected this session


class SpendStop(Exception):
    pass


class SchemaError(ValueError):
    pass


def record(name, row):
    """Append one row to a run log under OUT, so it survives whatever ends the session."""
    with (OUT / name).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def spend():
    return sum(c["cost"] for c in CALLS)


def check_schema(value, schema, path="$"):
    """A small validator for the reply shapes in block 6: type, required keys, item type, enum.
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
    """One HTTP POST; the status and the body text."""
    data = json.dumps(payload).encode("utf-8")
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    request = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.status, response.read().decode("utf-8")


def log_call(row):
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
            log_call({"stage": stage, "model": model, "in": prompt_chars // 4, "out": 0,
                      "seconds": round(time.time() - started, 1), "cost": prompt_chars // 4 * price_in / 1e6,
                      "timeout": True, **ctx})
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
    tokens_in = usage.get("prompt_tokens", 0)
    tokens_out = usage.get("completion_tokens", 0)
    log_call({"stage": stage, "model": body.get("model", model), "in": tokens_in, "out": tokens_out,
              "seconds": round(time.time() - started, 1),
              "cost": (tokens_in * price_in + tokens_out * price_out) / 1e6, **ctx})
    return body


def generate(prompt, schema, stage, model=LUNA, effort="low", ctx=None):
    """The reply as a dict that fits `schema`, or None after one retry with the error appended
    (the rejection is logged). Every prompt asks for JSON, and JSON mode guarantees a parse when
    there is content; a refusal has no content and is treated as a bad shape."""
    ctx = ctx or {}
    error = ""
    for attempt in range(2):
        body = call("https://api.openai.com/v1/chat/completions",
                    {"model": model, "reasoning_effort": effort, "response_format": {"type": "json_object"},
                     "messages": [{"role": "user", "content": prompt}]},
                    model, stage, ctx, len(prompt))
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
        body = call("https://api.openai.com/v1/embeddings", {"model": EMBED_MODEL, "input": batch},
                    EMBED_MODEL, stage, ctx or {}, sum(len(t) for t in batch))
        for row in sorted(body["data"], key=embedding_index):
            vectors.append(row["embedding"])
    return vectors


print(f"models {LUNA} (derive), {TERRA} (judge), {EMBED_MODEL}; key {'present' if KEY else 'MISSING'}")

# %%
# Block 3: test the connection before anything spends. One tiny call to each endpoint; the
# reply, the tokens and the cost are printed. If this cell fails, fix the secret or the
# Internet setting before running block 13.
if __name__ == "__main__":
    if not KEY:
        print("no key: attach OPENAI_API_KEY under Add-ons > Secrets, then rerun this cell")
    else:
        ping = generate('Reply with exactly the JSON object {"ok": true}.', {"type": "object", "required": ["ok"]},
                        "ping", ctx={"doc": "connection test"})
        vector = embed(["connection test"], ctx={"doc": "connection test"})
        print(f"chat reply {ping}; embedding of {len(vector[0])} dimensions; {len(CALLS)} calls, ${spend():.5f}")

# %%
# Block 4: ids and small text helpers.
#
# Every id is a content hash, so re-deriving unchanged input mints the same ids, and a
# corrected unit changes one id and not every id after it.


def h(*parts):
    return hashlib.sha256("\n".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def norm(s):
    """One space between words, case folded."""
    return " ".join(str(s or "").split()).casefold()


def word_count(s):
    return len(s.split())


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
    return "".join(out).strip("_") or "related_to"


def names_in(text):
    """The names a summary or abstract emits, for the fabrication check: runs of capitalised
    words. A run that opens a sentence is counted from its second word; its first word counts
    only when it also appears capitalised inside some sentence, so 'The' and 'Then' are never
    names and a name that only ever opens a sentence is missed rather than invented."""
    names, openers = [], []
    run, run_opens, sentence_start = [], False, True
    for token in text.split():
        word = token.strip("\"'“”‘’()[]")               # quotes and brackets around the word
        tail = ""
        while word and word[-1] in ".,;:!?":            # punctuation after the word
            tail = word[-1] + tail
            word = word[:-1]
        capital = word[:1].isupper()
        if capital:
            if not run:
                run_opens = sentence_start
            run.append(word)
        if run and (not capital or tail):              # a lowercase word or any punctuation ends the run
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
    """The kind of most of the unit's characters, from its pieces (the extractor's regions, or
    the voice of a chat turn); 'body' when it has none. Code never branches on it: it is shown
    to the judge that decides which kinds of unit to read (block 11)."""
    chars = {}
    for p in doc["pieces"]:
        if p["unit_id"] == unit["unit_id"]:
            chars[p["kind"]] = chars.get(p["kind"], 0) + p["end"] - p["start"]
    if not chars:
        return "body"
    return max(chars, key=chars.get)


def first_line(text):
    """The first non-empty line of a text, whitespace collapsed, at most 120 characters."""
    for line in text.split("\n"):
        if line.strip():
            return " ".join(line.split())[:120]
    return ""

# %%
# Block 5: the quote gate.
#
# locate(unit_text, quote) returns where the quote is inside the unit, or why it is not. Two
# ways to match, each named so the receipt says how many quotes needed which: the exact
# substring; else the same text after normalising both sides (one space for any run of
# whitespace, NFKC, straight quotes, one kind of dash, a hyphenated line break closed up,
# case folded). The normalised copy of the unit carries, for each of its characters, the
# offset of the original character it came from, so a match maps back to offsets in the
# original text. The stored offsets always index the original. A quote that matches neither
# way is classified: 'paraphrase' when most of its words are there in order, else 'not_found'.

REPLACEMENTS = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "‒": "-", "−": "-", "‐": "-", "‑": "-",
                "­": "", " ": " "}


def hyphen_breaks(text):
    """The offsets of the hyphen and line-break characters in every 'word-\\nword' run, so a
    word the PDF wrapped at a hyphen reads whole. A letter must stand on both sides."""
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
    out, back = [], []
    in_space = True                                 # leading whitespace is dropped
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
        for c in unicodedata.normalize("NFKC", ch).casefold():     # one character can become several
            out.append(c)
            back.append(i)
    if out and out[-1] == " ":                      # trailing whitespace is dropped
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
    """The words of s with punctuation stripped, empty ones dropped."""
    words = []
    for token in s.split():
        word = "".join(ch for ch in token if is_word_char(ch))
        if word:
            words.append(word)
    return words


def classify_miss(ntext, nquote):
    """'paraphrase' when at least seven in ten of the quote's words appear in order in the unit,
    punctuation aside, else 'not_found'."""
    wanted = words_only(nquote)
    matched = 0
    for word in words_only(ntext):
        if matched < len(wanted) and word == wanted[matched]:
            matched += 1
    if matched >= 0.7 * max(1, len(wanted)):
        return "paraphrase"
    return "not_found"


def locate(text, quote, cache=None):
    """(start, end, 'exact' or 'normalised') with offsets into `text`, or (None, None, why)."""
    quote = (quote or "").strip()
    if not quote:
        return None, None, "empty"
    i = text.find(quote)
    if i >= 0:
        return i, i + len(quote), "exact"
    ntext, back = normalised_unit(text, cache)
    nquote, _ = normalised(quote)
    if not nquote:
        return None, None, "not_found"
    i = ntext.find(nquote)
    if i >= 0:
        return back[i], back[i + len(nquote) - 1] + 1, "normalised"
    return None, None, classify_miss(ntext, nquote)


def occurrences(text, found):
    """Every offset at which the located string recurs verbatim, the first one included."""
    if not found:
        return []
    starts = []
    i = text.find(found)
    while i >= 0:
        starts.append(i)
        i = text.find(found, i + 1)
    return starts


def surface_spans(text, surface, cache=None):
    """Every whole-word occurrence of a surface form in the unit, as (start, end) offsets into
    the original text, found on the normalised copy so case and quotes do not matter."""
    nsurface, _ = normalised(surface or "")
    if not nsurface:
        return []
    ntext, back = normalised_unit(text, cache)
    spans = []
    i = ntext.find(nsurface)
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
# (entities with their surface forms, salience and profile; facts with quotes; summary and
# cells), one judge, one fold, one adjudication per major entity. None of them knows what
# kind of document it is reading. The roster is what the document has established so far: entities
# that earned a place (a fact or a second mention) and the predicates already in use, both
# offered as suggestions the model may continue or ignore, the most recently seen first.

ENTITY_SCHEMA = {"type": "object", "required": ["entities"], "properties": {"entities": {"type": "array", "items": {
    "type": "object", "required": ["name", "named", "kind", "surface_forms"], "properties": {
        "name": {"type": "string"}, "named": {"type": "boolean"}, "kind": {"type": "string"},
        "surface_forms": {"type": "array", "items": {"type": "string"}},
        "salience": {"type": ["string", "null"]},
        "continues": {"type": ["string", "null"]},
        "profile": {"type": ["object", "null"]}}}}}}

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
    "type": "object", "required": ["kind", "reason"], "properties": {
        "kind": {"type": "string"}, "reason": {"type": "string"}}}}}}

ADJUDICATE_SCHEMA = {"type": "object", "required": ["facts", "attributes", "contradictions"], "properties": {
    "facts": {"type": "array", "items": {"type": "object", "required": ["predicate", "object", "from"], "properties": {
        "predicate": {"type": "string"}, "object": {"type": "string"}, "qualifiers": {"type": ["string", "null"]},
        "from": {"type": "array"}}}},
    "attributes": {"type": "array", "items": {"type": "object", "required": ["attribute", "value", "from"], "properties": {
        "attribute": {"type": "string"}, "value": {"type": "string"}, "from": {"type": "array"}}}},
    "contradictions": {"type": "array", "items": {"type": "object", "required": ["note", "from"], "properties": {
        "note": {"type": "string"}, "from": {"type": "array"}}}}}}


def triage_prompt(doc, kinds):
    """kinds: {kind: [(position, label, words, first line), ...]} for every unit of the document."""
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


def adjudicate_prompt(name, kinds, facts, cells, predicates):
    """facts: numbered lines; cells: in reading order; predicates: the names the document used."""
    return f"""Below is everything one document says about one entity, {name} ({', '.join(kinds)}): its facts, numbered, each with the unit it came from and the words it rests on, then its narrative cells in reading order. The units were read one at a time, so the facts repeat, overlap and sometimes disagree, and some are stated from the side of a lesser thing (marked inverse: the entity is the object of that statement).

Write the entity's consolidated record:
- "facts": each durable relationship or fact stated once, with "predicate" (lowercase_snake_case, present tense, reusing a name from the list below where one fits), "object", "qualifiers" (or null), and "from": the numbers of every listed fact it is drawn from. A fact drawn from nothing listed is not allowed.
- "attributes": what the entity is, has or is like, as "attribute", "value" and "from", folding the lesser things named in the facts into the entity itself: a house that has a cellar has the attribute cellar, not a relationship to one.
- "contradictions": where listed facts disagree, a one-sentence "note" and the "from" numbers; do not resolve them.

Return JSON {{"facts": [...], "attributes": [...], "contradictions": [...]}}

PREDICATES THE DOCUMENT USED: {', '.join(predicates)}

FACTS:
{chr(10).join(facts)}

CELLS:
{chr(10).join(cells) or '(none)'}"""

ROSTER_SHOWN = 60


def roster_text(roster):
    if not roster["entities"]:
        return ""
    lines = []
    for e in roster["entities"][:ROSTER_SHOWN]:
        line = f"- {e['name']} ({e['kind']}; forms: {', '.join(e['forms'][:5])}"
        if e["is_a"]:
            line += f"; is: {', '.join(e['is_a'][:3])}"
        lines.append(line + ")")
    return ("\n\nESTABLISHED SO FAR IN THIS DOCUMENT (continue one of these when the text means the same thing;"
            " name a new one when it does not):\n" + "\n".join(lines))


def entity_prompt(unit, roster):
    return f"""TEXT ({unit['label']}):
{unit['text']}

Above is one unit of a longer document. Identify the entities it involves: each person, group, place, thing, event, or topic that acts, is acted upon, or is discussed in its own right, plus any named person, place, group, or thing, however briefly mentioned. Parts, components, and possessions of a listed entity are not entities; they belong inside that entity's facts.

Return JSON {{"entities": [{{"name", "named", "kind", "salience", "surface_forms", "continues", "profile"}}]}} where:
- name: for a named entity, the fullest name the text uses; for an unnamed one, a head word plus a parenthetical anchoring it to a named entity, like "car (Sam's car)"
- named: true if the text gives it a proper name
- kind: one lowercase word: person, group, place, object, event, topic, or another if none fits
- salience: "major" only if it would appear in a two-sentence summary of this text, else "minor"
- surface_forms: every distinct verbatim string the text uses to refer to it, copied exactly, bare pronouns excluded; a string that refers to two different entities in this text is listed under only one of them
- continues: the name of the established entity this one is, exactly as listed below, or null if it is new to the document
- profile: attributes you infer from context rather than read in the text, as {{"gender", "age_band", "animacy", "role"}} with a value or null each; null when nothing can be inferred{roster_text(roster)}"""


def fact_prompt(unit, names, majors, predicates):
    used = ""
    if predicates:
        used = ("\n\nPREDICATES THIS DOCUMENT HAS USED (reuse one when it means the same relation; coin a new one when none does): "
                + ", ".join(predicates[:80]))
    return f"""TEXT ({unit['label']}):
{unit['text']}

Above is one unit of a longer document; below, the entities identified in it. For each entity, distill every durable fact the text states about it: what it is, its attributes, its states, its situation, its parts and possessions, its relationships to the other listed entities. Not moment-to-moment actions or passing remarks; a lasting disposition, habit, or position counts.

Return JSON {{"facts": [{{"subject", "predicate", "object", "qualifiers", "quote", "valid_from", "valid_to"}}]}} where:
- subject: a name from ENTITIES, exactly as written
- predicate: a lowercase_snake_case relation in the present tense, named the way the text gives it; use is_a for what kind of thing the subject is
- object: another entity's name exactly as written when the fact relates two entities, else a short literal value that does not repeat the predicate; never a bare true or false
- qualifiers: a short phrase for role, manner, or condition, else null
- quote: one verbatim substring of the text that supports the fact, copied exactly as it appears, punctuation and all
- valid_from, valid_to: an ISO date (YYYY, YYYY-MM or YYYY-MM-DD) only when the quote itself states when the fact began or ended; otherwise null. Never infer a date.
- each fact is atomic: one attribute or one relationship, with a bare value rather than a phrase
- a relationship between a major entity and a minor one is stated once, under the major entity; only between two major entities may it be stated from both sides

ENTITIES: {", ".join(names)}
MAJOR: {", ".join(majors)}{used}"""


def cells_prompt(unit, names, previous):
    context = ""
    if previous:
        context = f"\n\nTHE PREVIOUS UNIT, SUMMARISED (for resolving references only; do not restate it):\n{previous}"
    return f"""TEXT ({unit['label']}):
{unit['text']}

Above is one unit of a longer document. Write:
1. "summary": the unit in 3-5 concrete sentences, naming who and what it concerns.
2. "cells": for each entity below, 1-3 sentences in third person on what it does, what happens to it, or what is learned about it in this unit, written so it can be appended to that entity's running record.
Use only what the text says. Use no name that does not appear in the text.

Return JSON {{"summary": "...", "cells": [{{"entity", "text"}}]}}

ENTITIES: {", ".join(names)}{context}"""


JUDGE_PROMPT = """Each PAIR below names two entity clusters built from different units of one document by their numbers in the DOSSIERS list. Decide for each pair whether the two describe the SAME individual thing. Weigh all the evidence: shared names and forms, what each is said to be, its facts, and above all who and what it relates to; a fact stating that one is the other is near-decisive. Kind labels are per-unit guesses and often differ for the same individual, so never decide on them alone. Answer unsure only when the evidence genuinely cannot settle it.

Return JSON {"verdicts": [{"pair": n, "verdict": "same" | "different" | "unsure", "reason": "one sentence"}]}
"""


def fold_prompt(what, children, limit):
    return f"""Below are the records of {what}, in reading order. Write one summary of the whole in at most {limit} words: what it is, who and what matter most, and how it unfolds from beginning to end. Ground every statement only in these records; use no outside knowledge and no name that does not appear below.

Return JSON {{"summary": "..."}}

RECORDS:
{chr(10).join(children)}"""

# %%
# Block 7: derive one unit.
#
# Three calls, every gate applied by code, and one record back with everything the model
# said and everything code kept or rejected, so a unit can be read on its own. Offsets are
# document offsets: the unit's start is added to every span. A span is one mention: when two
# entities claim the same occurrence, the first one listed keeps it.


def derive_unit(doc, unit, roster, previous_summary, ctx):
    text = unit["text"]
    base = unit["start"]
    cache = {}
    rec = {"unit_id": unit["unit_id"], "position": unit["position"], "label": unit["label"],
           "kind": unit["kind"],
           "entities": [], "dropped_entities": [], "mentions": [], "facts": [], "rejected_facts": [],
           "profile": [], "summary": None, "cells": [], "dropped_cells": [], "agreement": None,
           "shared_spans": 0, "ambiguous_voice": 0, "empty": False}

    # 1. entities, each surface form located; a form that is not in the unit is dropped
    reply = generate(entity_prompt(unit, roster), ENTITY_SCHEMA, "entities", ctx=ctx)
    roster_names = {e["name"] for e in roster["entities"]}
    seen_names = set()
    claimed = {}                                  # (start, end) -> the entity that got the span
    for e in (reply or {}).get("entities", []):
        name = " ".join(e["name"].split())
        if not name or name in seen_names:
            continue
        forms, spans, found_any = [], [], False
        candidates = [s for s in e["surface_forms"] if isinstance(s, str)] + [name]
        for surface in dict.fromkeys(candidates):
            all_hits = surface_spans(text, surface, cache)
            found_any = found_any or bool(all_hits)
            free_hits = [span for span in all_hits if span not in claimed and span not in spans]
            rec["shared_spans"] += sum(1 for span in all_hits if span in claimed)
            if free_hits:
                forms.append(surface)
                spans.extend(free_hits)
        if not spans:
            if found_any:
                why, category = "every span already claimed by an earlier entity", "span_claimed"
            else:
                why, category = "no surface form in unit", "no_surface_form"
            rec["dropped_entities"].append({"name": name, "why": why, "category": category, "forms": e["surface_forms"][:5]})
            continue
        seen_names.add(name)
        for span in spans:
            claimed[span] = name
        continues = e.get("continues") if e.get("continues") in roster_names else None
        profile = e.get("profile") if isinstance(e.get("profile"), dict) else {}
        rec["entities"].append({"name": name, "named": bool(e["named"]), "kind": str(e["kind"]).lower(),
                                "major": e.get("salience") == "major",
                                "forms": forms, "continues": continues, "mentions": len(spans)})
        for start, end in sorted(spans):
            rec["mentions"].append({"mention_id": h(unit["unit_id"], base + start, base + end), "entity": name,
                                    "unit_id": unit["unit_id"], "start": base + start, "end": base + end,
                                    "surface": text[start:end], "resolved_by": "surface"})
        for attribute, value in profile.items():
            if value not in (None, "", "null", "unknown"):
                rec["profile"].append({"entity": name, "attribute": str(attribute), "value": str(value),
                                       "confidence": 0.5, "from_unit": unit["unit_id"]})
    names = [e["name"] for e in rec["entities"]]
    if not names:
        rec["empty"] = True
        return rec

    # 2. facts, each quote located inside the unit, offsets stored as document offsets
    majors = [e["name"] for e in rec["entities"] if e["major"]]
    reply = generate(fact_prompt(unit, names, majors, roster["predicates"]), FACT_SCHEMA, "facts", ctx=ctx)
    name_set = set(names)
    seen_facts = set()
    for f in (reply or {}).get("facts", []):
        subject = f["subject"].strip()
        predicate = snake_case(f["predicate"])
        obj = str(f["object"]).strip()
        rejection = {"subject": subject, "predicate": predicate, "object": obj, "quote": f["quote"][:160]}
        start, end, how = locate(text, f["quote"], cache)
        if subject not in name_set:
            rec["rejected_facts"].append({"category": "unlisted_subject", **rejection})
            continue
        if start is None:
            rec["rejected_facts"].append({"category": how, **rejection})
            continue
        key = (subject, predicate, norm(obj))
        if key in seen_facts:
            rec["rejected_facts"].append({"category": "duplicate", **rejection})
            continue
        seen_facts.add(key)
        quote = text[start:end]
        voices = {author_at(doc, base + at) for at in occurrences(text, quote)}
        ambiguous = len(voices) > 1                    # the same words in two voices: no voice is claimed
        author = None if ambiguous else author_at(doc, base + start)
        rec["ambiguous_voice"] += ambiguous
        rec["facts"].append({"fact_id": h(unit["unit_id"], subject, predicate, obj, base + start, base + end),
                             "subject": subject, "predicate": predicate, "object": obj,
                             "object_is_entity": obj in name_set, "qualifiers": f.get("qualifiers") or None,
                             "unit_id": unit["unit_id"], "quote": quote, "quote_start": base + start, "quote_end": base + end,
                             "matched_by": how, "valid_from": stated_date(f.get("valid_from"), quote),
                             "valid_to": stated_date(f.get("valid_to"), quote),
                             "author": author, "voice_ambiguous": ambiguous, "tier": LUNA})

    # 3. summary and cells, one call, for the unit's major entities (the model's salience call,
    #    as the demo did); the entities with a fact are counted beside them as a diagnostic
    with_fact = []
    for name in names:
        for f in rec["facts"]:
            if f["subject"] == name or (f["object_is_entity"] and f["object"] == name):
                with_fact.append(name)
                break
    reply = generate(cells_prompt(unit, majors, previous_summary), CELLS_SCHEMA, "cells", ctx=ctx)
    if reply:
        rec["summary"] = " ".join(reply["summary"].split())
        for c in reply["cells"]:
            if c["entity"] in majors and c["text"].strip():
                rec["cells"].append({"entity": c["entity"], "text": " ".join(c["text"].split())})
            else:
                rec["dropped_cells"].append({"entity": c["entity"], "why": "not a major entity of this unit"})
        rec["agreement"] = agreement(rec, majors, with_fact)
    rec["empty"] = not rec["facts"] and not rec["cells"]
    return rec


def agreement(rec, majors, with_fact):
    """Which unit-majors the summary names, against which got a cell; and how the model's
    salience call compares with the entities that have a fact in the unit."""
    summary = rec["summary"].casefold()
    forms_of = {e["name"]: e["forms"] for e in rec["entities"]}
    named = []
    for name in majors:
        if any(whole_word(form.casefold(), summary) for form in forms_of[name]):
            named.append(name)
    celled = {c["entity"] for c in rec["cells"]}
    return {"majors": len(majors), "cells": len(celled), "named_in_summary": len(named),
            "in_summary_without_cell": sorted(set(named) - celled),
            "cell_without_summary_name": sorted(celled - set(named)),
            "with_fact": len(with_fact),
            "major_without_fact": sorted(set(majors) - set(with_fact)),
            "fact_but_minor": sorted(set(with_fact) - set(majors))}


def stated_date(value, quote):
    """An ISO date the model claims the quote states (YYYY, YYYY-MM or YYYY-MM-DD): kept only
    when its year appears in the quote."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    well_formed = False
    for shape in ("%Y", "%Y-%m", "%Y-%m-%d"):
        try:
            datetime.strptime(value, shape)
            well_formed = True
        except ValueError:
            pass
    if well_formed and value[:4] in quote:
        return value
    return None


def author_at(doc, offset):
    """The voice of an offset: the author of the piece holding it, else the document's, else None."""
    for p in doc["pieces"]:
        if p["start"] <= offset < p["end"]:
            return p["author"] or doc.get("author")
    return doc.get("author")


def roster_order(entry):
    return (-entry["last_unit"], -entry["units"])


def advance_roster(roster, rec):
    """Entities that earned a place (a fact, or two mentions) and every predicate used, carried
    to the next unit as suggestions, the most recently seen first."""
    facts_of = {}
    for f in rec["facts"]:
        facts_of.setdefault(f["subject"], []).append(f)
        roster["predicate_counts"][f["predicate"]] = roster["predicate_counts"].get(f["predicate"], 0) + 1
    by_name = {e["name"]: e for e in roster["entities"]}
    for e in rec["entities"]:
        key = e["continues"] or e["name"]
        earned = e["name"] in facts_of or e["mentions"] >= 2 or key in by_name
        if not earned:
            continue
        entry = by_name.get(key)
        if entry is None:
            entry = {"name": key, "kind": e["kind"], "forms": [], "is_a": [], "units": 0, "last_unit": rec["position"]}
            by_name[key] = entry
            roster["entities"].append(entry)
        entry["units"] += 1
        entry["last_unit"] = rec["position"]
        for form in e["forms"] + ([e["name"]] if e["name"] != key else []):
            if form not in entry["forms"]:
                entry["forms"].append(form)
        for f in facts_of.get(e["name"], []):
            if f["predicate"] == "is_a" and f["object"] not in entry["is_a"]:
                entry["is_a"].append(f["object"])
    roster["entities"].sort(key=roster_order)
    roster["predicates"] = sorted(roster["predicate_counts"], key=roster["predicate_counts"].get, reverse=True)

# %%
# Block 8: reconcile the document's unit-local entities into document entities, bottom up, as
# the demo did.
#
# Every local starts alone. A declared continuation of a named entity unites without a judge
# (the roster's declared reuse). Every other candidate pair, nominated by a shared name or
# surface form, a fact stating one is the other, or a shared name word, and involving at least
# one unit-major, goes to the judge, strongest first, ten pairs a call, every cluster's dossier
# sent once; an unsure verdict is deferred and judged once more against the finished clusters,
# where unsure means apart. The name, co-occurrence and profile scores are computed and logged
# for every pair but decide nothing. Every decision is a ledger row with its evidence.
import difflib



def name_score(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def name_words(name):
    """The words of a name longer than three letters, case folded, punctuation stripped."""
    words = set()
    for token in name.casefold().split():
        word = "".join(ch for ch in token if ch.isalpha())
        if len(word) > 3:
            words.add(word)
    return words


def anchored(x, y):
    """x is an unnamed thing anchored to y by its parenthetical ("car (Sam's car)" and "Sam"):
    y's name is inside the parenthetical and nothing else is shared, so they are not
    candidates for being the same thing."""
    name = x["name"]
    if not y["named"] or not name.endswith(")") or "(" not in name:
        return False
    head, inner = name[:-1].rsplit("(", 1)
    if norm(y["name"]) not in inner.casefold():
        return False
    return not (name_words(head) & name_words(y["name"])) and not (x["surfaces"] & y["surfaces"])


def fact_text(f):
    text = f"{f['predicate']} {f['object']}"
    if f["qualifiers"]:
        text += f" [{f['qualifiers']}]"
    return text


def locals_of(records):
    """One record per entity per unit, with what the unit said about it."""
    out = []
    for rec in records:
        facts_of = {}
        for f in rec["facts"]:
            facts_of.setdefault(f["subject"], []).append(f)
        profile_of = {}
        for p in rec["profile"]:
            profile_of.setdefault(p["entity"], {})[p["attribute"]] = p["value"].casefold()
        names_here = {e["name"] for e in rec["entities"]}
        for e in rec["entities"]:
            facts = facts_of.get(e["name"], [])
            out.append({"id": len(out), "ui": rec["position"], "unit_id": rec["unit_id"], "name": e["name"],
                        "kind": e["kind"], "named": e["named"], "major": e["major"], "continues": e["continues"],
                        "forms": list(dict.fromkeys(e["forms"] + [e["name"]])),
                        "surfaces": {s.casefold() for s in e["forms"]} | {e["name"].casefold()},
                        "is_a": [f["object"] for f in facts if f["predicate"] == "is_a"],
                        "facts": [fact_text(f) for f in facts],
                        "relations": [f"{f['predicate']} {f['object']}" for f in facts if f["object_is_entity"]],
                        "profile": profile_of.get(e["name"], {}), "cooc": names_here - {e["name"]}, "n_facts": len(facts)})
    return out


def candidate_reason(a, b):
    """Why two locals from different units might be the same thing, or None."""
    if norm(a["continues"] or "") == norm(b["name"]) or norm(b["continues"] or "") == norm(a["name"]):
        return "declared"
    if a["surfaces"] & b["surfaces"]:
        return "shared_surface"
    if name_words(a["name"]) & name_words(b["name"]):
        return "shared_word"
    if any(x.casefold() in b["surfaces"] for x in a["is_a"]) or any(x.casefold() in a["surfaces"] for x in b["is_a"]):
        return "is_a_link"
    return None


def score_pair(a, b, reason):
    """(name, co-occurrence, profile, combined) scores, each kept separately for the ledger."""
    name = name_score(a["name"], b["name"])
    if reason in ("declared", "shared_surface"):
        name = 1.0
    both = a["cooc"] | b["cooc"]
    cooc = len(a["cooc"] & b["cooc"]) / len(both) if both else 0.0
    shared_keys = set(a["profile"]) & set(b["profile"])
    if shared_keys:
        profile = sum(a["profile"][k] == b["profile"][k] for k in shared_keys) / len(shared_keys)
    else:
        profile = 0.5
    w_name, w_cooc, w_profile = SCORE_WEIGHTS
    combined = w_name * name + w_cooc * cooc + w_profile * profile
    return name, cooc, profile, combined


TIER = {"declared": 1.0, "shared_surface": 1.0, "is_a_link": 0.85, "shared_word": 0.5}   # the demo's nomination strengths
PAIRS_PER_CALL = 10                                # candidate pairs per judge call, as the demo did
SCORE_WEIGHTS = (0.6, 0.25, 0.15)                  # name, co-occurrence, profile: logged for every pair, deciding nothing


def tier_of(item):
    return -item[1][0]


def unit_of_local(l):
    return l["ui"]


def best_name(counts):
    """The most used name, the longest on a tie."""
    best = None
    for name, n in counts.items():
        if best is None or (n, len(name)) > (counts[best], len(best)):
            best = name
    return best


class Clusters:
    """The unit-locals grouped as they are found to be the same thing: every local starts alone,
    unite joins two groups, find gives a local's current group (its root)."""

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

    def members(self, root, locals_):
        return [l for l in locals_ if self.find(l["id"]) == root]


def ledger_row(locals_, a, b, verdict, how, evidence):
    return {"a": locals_[a]["name"], "a_unit": locals_[a]["ui"], "b": locals_[b]["name"], "b_unit": locals_[b]["ui"],
            "verdict": verdict, "how": how, "evidence": evidence}


def nominate(locals_, clusters):
    """The candidate pairs, the demo's way: two locals from different units, not already in one
    cluster, at least one of them a unit-major, nominated by a shared surface (1.0), a fact
    stating one is the other (0.85), or a shared name word (0.5), and never a possession against
    its own anchor. {(a, b): (tier, reason, scores)}."""
    pairs = {}
    for a in locals_:
        for b in locals_:
            if a["id"] >= b["id"] or a["ui"] == b["ui"] or clusters.same(a["id"], b["id"]):
                continue
            if not (a["major"] or b["major"]):
                continue
            reason = candidate_reason(a, b)
            if reason is None or anchored(a, b) or anchored(b, a):
                continue
            pairs[(a["id"], b["id"])] = (TIER[reason], reason, score_pair(a, b, reason))
    return pairs


def dossier(members):
    """What a cluster is, for the judge: names, forms, kinds, what it is said to be, its facts
    and relations, the units it appears in."""
    return "\n".join([
        f"names: {', '.join(sorted({l['name'] for l in members}))}",
        f"forms: {', '.join(sorted({s for l in members for s in l['surfaces']})[:12])}",
        f"kinds: {', '.join(sorted({l['kind'] for l in members}))}",
        f"is: {', '.join(sorted({x for l in members for x in l['is_a']})[:6]) or '(nothing stated)'}",
        f"facts: {'; '.join(sorted({x for l in members for x in l['facts']})[:10]) or '(none)'}",
        f"relations: {'; '.join(sorted({x for l in members for x in l['relations']})[:10]) or '(none)'}",
        f"units: {', '.join(str(u) for u in sorted({l['ui'] for l in members}))}"])


def judge(batch, locals_, clusters, ctx):
    """One Terra call over up to PAIRS_PER_CALL pairs of cluster roots, every dossier sent once;
    {pair number: (verdict, reason)} in batch order."""
    roots = sorted({r for pair in batch for r in pair})
    number = {r: n for n, r in enumerate(roots, 1)}
    dossiers = "\n\n".join(f"[{number[r]}]\n{dossier(clusters.members(r, locals_))}" for r in roots)
    pairs = "\n".join(f"PAIR {n}: [{number[a]}] and [{number[b]}]" for n, (a, b) in enumerate(batch, 1))
    prompt = JUDGE_PROMPT + "\nDOSSIERS\n" + dossiers + "\n\nPAIRS\n" + pairs
    reply = generate(prompt, JUDGE_SCHEMA, "judge", model=TERRA, effort="medium", ctx=ctx)
    verdicts = {}
    for v in (reply or {}).get("verdicts", []):
        try:
            verdicts[int(v["pair"]) - 1] = (v["verdict"], v.get("reason", ""))
        except (TypeError, ValueError):
            pass
    return verdicts


def cluster_entities(locals_, clusters):
    """One document entity per cluster: its canonical name (the most used proper name, the
    longest on a tie), its names, forms, units and facts, and where each form first appeared."""
    groups = {}
    for l in locals_:
        groups.setdefault(clusters.find(l["id"]), []).append(l)
    entities = []
    for members in groups.values():
        members.sort(key=unit_of_local)
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
        entities.append({"name": best_name(counts), "kinds": sorted({l["kind"] for l in members}),
                         "named": any(l["named"] for l in members),
                         "units": sorted({l["ui"] for l in members}), "unit_ids": unit_ids, "first_unit": unit_ids[0],
                         "names": sorted({l["name"] for l in members}),
                         "surfaces": sorted({s for l in members for s in l["surfaces"]}),
                         "first_unit_of": first_unit_of, "members": [(l["ui"], l["name"]) for l in members],
                         "n_facts": sum(l["n_facts"] for l in members),
                         "is_a": sorted({x for l in members for x in l["is_a"]}),
                         "profile": [l["profile"] for l in members if l["profile"]]})
    return entities


def reconcile(records, ctx, watch=False):
    """The document's entities from its unit-locals: (entities, ledger, candidates, locals,
    pairs, pairs judged). With `watch`, one line per judge call, since this is the slow step."""
    locals_ = locals_of(records)
    clusters = Clusters(len(locals_))
    ledger, candidates = [], []

    # 1. declared continuations of a named entity unite without a judge
    by_name = {}
    for l in locals_:
        by_name.setdefault(norm(l["name"]), []).append(l)
    for l in locals_:
        if not l["continues"]:
            continue
        earlier = [t for t in by_name.get(norm(l["continues"]), []) if t["ui"] < l["ui"]]
        named = [t for t in earlier if t["named"]]
        if named:
            clusters.unite(named[-1]["id"], l["id"])
            ledger.append(ledger_row(locals_, named[-1]["id"], l["id"], "same", "declared", f"unit {l['ui']} continued {l['continues']!r}"))
        elif earlier:
            ledger.append(ledger_row(locals_, earlier[-1]["id"], l["id"], "candidate", "declared",
                                     f"unit {l['ui']} continued the unnamed {l['continues']!r}; judged instead"))

    # 2. every other candidate pair goes to the judge, strongest first; the scores are logged
    pairs = nominate(locals_, clusters)
    to_judge = []
    for (i, j), (tier, reason, (name, cooc, profile, combined)) in sorted(pairs.items(), key=tier_of):
        candidates.append({"a": locals_[i]["name"], "a_unit": locals_[i]["ui"], "b": locals_[j]["name"], "b_unit": locals_[j]["ui"],
                           "tier": tier, "reason": reason, "name_score": round(name, 3), "cooc_score": round(cooc, 3),
                           "profile_score": round(profile, 3), "combined": round(combined, 3), "decision": "judge"})
        to_judge.append((i, j))

    # 3. the judge, in batches; different stays apart, unsure is deferred to one last look
    kept_apart, deferred = [], []

    def settled(ra, rb):
        for x, y in kept_apart + deferred:
            if {clusters.find(x), clusters.find(y)} == {ra, rb}:
                return True
        return False

    def decide(batch, verdicts, final):
        how = "judged again" if final else "judged"
        for n, (ra, rb) in enumerate(batch):
            verdict, reason = verdicts.get(n, ("unsure", "no verdict returned"))
            if verdict == "same":
                clusters.unite(ra, rb)
            elif verdict == "different" or final:
                kept_apart.append((ra, rb))
            else:
                deferred.append((ra, rb))
            ledger.append(ledger_row(locals_, ra, rb, verdict, how, reason))

    if watch:
        print(f"judge: {len(locals_)} unit-locals, {len(to_judge)} candidate pairs to judge, {PAIRS_PER_CALL} a call")
    k, calls = 0, 0
    while k < len(to_judge):
        batch, keys = [], set()
        while k < len(to_judge) and len(batch) < PAIRS_PER_CALL:
            ra, rb = clusters.find(to_judge[k][0]), clusters.find(to_judge[k][1])
            k += 1
            key = frozenset((ra, rb))
            if ra != rb and key not in keys and not settled(ra, rb):
                batch.append((ra, rb))
                keys.add(key)
        if batch:
            decide(batch, judge(batch, locals_, clusters, ctx), final=False)
            calls += 1
            if watch and calls % 5 == 0:
                same = sum(1 for row in ledger if row["how"] == "judged" and row["verdict"] == "same")
                print(f"    judge call {calls}: {k} of {len(to_judge)} pairs seen, {same} united so far, ${spend():.2f} spent this session")

    # 4. the deferred pairs get one last look against the finished clusters; unsure stays apart
    last_look, seen = [], set()
    still_deferred, deferred = list(deferred), []
    for a, b in still_deferred:
        ra, rb = clusters.find(a), clusters.find(b)
        key = frozenset((ra, rb))
        if ra != rb and key not in seen and not settled(ra, rb):
            last_look.append((ra, rb))
            seen.add(key)
    for at in range(0, len(last_look), PAIRS_PER_CALL):
        batch = last_look[at:at + PAIRS_PER_CALL]
        decide(batch, judge(batch, locals_, clusters, ctx), final=True)

    return cluster_entities(locals_, clusters), ledger, candidates, len(locals_), len(pairs), len(to_judge)

# %%
# Block 9: fold the document.
#
# The abstract folds from the unit summaries under BUILD's bound (at most half the child words,
# capped at 400) with the fabrication check; a rejected fold is asked for once more with the
# missing names listed, then left unstamped. Salience is reassessed against the abstract: named
# there, as whole words, is major, unit count then fact count break ties; with no abstract the
# tie-breakers decide alone, and the node says so. A major of low salience at document level, seen
# in fewer units and with fewer facts than the numbers below, is demoted to minor so the merge is
# never asked to nominate it; in a document with fewer units than the first number (a chat is
# one), the unit count means nothing and no one is demoted. Majors get a dossier with an embedding and their own abstract with
# children_hash.
DEMOTE_UNITS = 2      # a major seen in fewer units than this ...
DEMOTE_FACTS = 3      # ... and with fewer facts than this is demoted to minor


def fold(what, children, ctx, stage="fold", model=TERRA, allowed=None):
    """(text, missing names, limit); text is None when the fold was rejected twice. `allowed`
    are names the prompt itself supplies (the entity being summarised), which count as present.
    The model that wrote the fold is the caller's `model`; a fold that needed no call is Luna's,
    because its text is a Luna unit summary or cell copied whole."""
    child_words = sum(word_count(c) for c in children)
    limit = min(400, max(1, child_words // 2))
    asked = limit if limit < 12 else limit * 9 // 10        # a little under the bound, never over it
    prompt = fold_prompt(what, children, asked)
    missing = []
    for attempt in range(2):
        reply = generate(prompt, FOLD_SCHEMA, stage, model=model, ctx=ctx)
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


def children_hash(children):
    return h(*children)


def salience_order(item):
    major, units, facts = item[0], item[1], item[2]
    return (not major, -units, -facts)


def fold_document(doc, records, entities, ctx):
    out = {"abstract": None, "abstract_rejected": None, "majors": [], "minors": [], "dossiers": [],
           "entity_abstracts": [], "entity_abstract_rejected": []}

    # the abstract, from the unit summaries
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
        out["abstract"] = {"text": text, "children_hash": children_hash(summaries), "limit": limit, "tier": tier}
    else:
        out["abstract_rejected"] = missing

    # salience against the abstract; without one, the tie-breakers decide and the node says so
    abstract = (text or "").casefold()
    ranked = []
    for e in entities:
        if text:
            in_abstract = any(whole_word(s, abstract) for s in e["surfaces"] if len(s) >= 2)
            major = in_abstract
        else:
            in_abstract = None
            major = len(e["units"]) >= 2 or e["n_facts"] >= 2
        ranked.append((major, len(e["units"]), e["n_facts"], in_abstract, e))
    ranked.sort(key=salience_order)
    for major, n_units, n_facts, in_abstract, e in ranked:
        e["major"] = major
        e["rank"] = {"in_abstract": in_abstract, "units": n_units, "facts": n_facts, "demoted": False}
        if major and len(records) >= DEMOTE_UNITS and n_units < DEMOTE_UNITS and n_facts < DEMOTE_FACTS:
            e["major"] = False                    # low salience at document level: demoted to minor
            e["rank"]["demoted"] = True
        if e["major"]:
            out["majors"].append(e)
        else:
            out["minors"].append(e)
    out["demoted"] = [e["name"] for e in out["minors"] if e["rank"]["demoted"]]

    # dossiers and per-entity abstracts for the majors; clusters are keyed by their index,
    # not their name, because two clusters the judge kept apart can share a name
    for i, e in enumerate(entities):
        e["index"] = i
    member_of = {}
    for e in entities:
        for ui, local_name in e["members"]:
            member_of[(ui, local_name)] = e["index"]
    cells_of, facts_of = {}, {}
    for r in records:
        for c in r["cells"]:
            key = member_of.get((r["position"], c["entity"]))
            if key is not None:
                cells_of.setdefault(key, []).append(f"[{r['label']}] {c['text']}")
        for f in r["facts"]:
            key = member_of.get((r["position"], f["subject"]))
            if key is not None:
                facts_of.setdefault(key, []).append(fact_text(f))
    texts = []
    for e in out["majors"]:
        facts = list(dict.fromkeys(facts_of.get(e["index"], [])))
        cells = cells_of.get(e["index"], [])
        others = [n for n in e["names"] if n != e["name"]]
        dossier = "\n".join([f"name: {e['name']}", f"also: {', '.join(others)[:300]}",
                             f"kinds: {', '.join(e['kinds'])}", f"is: {', '.join(e['is_a'][:6])}",
                             f"facts: {'; '.join(facts[:20])}", f"cells: {' '.join(cells)[:1500]}"])
        out["dossiers"].append({"entity": e["name"], "first_unit": e["first_unit"], "text": dossier, "children": facts + cells})
        texts.append(dossier)
    if texts and KEY:
        for dossier, vector in zip(out["dossiers"], embed(texts, ctx=ctx)):
            dossier["embedding"] = vector
    for e, dossier in zip(out["majors"], out["dossiers"]):
        children = dossier["children"]
        if not children:
            continue
        if len(children) <= 2:                    # too little to fold: the children stand as the abstract
            text = " ".join(c.split("] ", 1)[-1] for c in children)
            missing, tier = [], LUNA
        else:
            text, missing, _ = fold(f"one entity, {e['name']}", children, ctx, stage="entity_abstract",
                                    allowed=e["names"] + e["surfaces"])
            tier = TERRA
        if text:
            out["entity_abstracts"].append({"entity": e["name"], "first_unit": e["first_unit"], "text": text,
                                            "children_hash": children_hash(children), "tier": tier})
        else:
            out["entity_abstract_rejected"].append({"entity": e["name"], "missing": missing})
    return out

# %%
# Block 10: the package.
#
# One JSONL file per document, mirroring the raw layout (raw/oz/01_55.txt becomes
# packages/oz/01_55.jsonl, a paper lands under its own folder's name), every line one record with a "record" field naming its type, in the
# order the merge applies them, ending in a completion record whose input_hash says which
# extractor output it came from. Minors have no node and their mentions carry node_id null. A
# fact from a major to a minor is a property with the minor's name as its value; a fact from a
# minor about a major lands on the major, marked inverse; a fact between two minors is not
# stored. The adjudicated record of each major sits beside its raw facts, every item pointing
# at the raw facts it was drawn from. Two locals of one unit reconciled into one node yield one
# cell.


def package_path(doc):
    """packages/<the folder the source sits in>/<its file name>.jsonl"""
    parts = doc["source_uri"].split("/")
    group = parts[-2] if len(parts) > 1 else "misc"
    return OUT / group / (Path(parts[-1]).stem + ".jsonl")


def sidecar_path(doc):
    """Unit records checkpointed while a document is in flight, so a stop mid-document costs
    only the unit that was running."""
    return package_path(doc).with_suffix(".units.jsonl")


def input_hash(doc):
    return h(doc["doc_id"], *[u["unit_id"] for u in doc["units"]], INGESTOR)


def node_id_of(doc, entity):
    """Name plus first unit: two clusters the judge kept apart may share a name."""
    return h(doc["doc_id"], entity["name"], entity["first_unit"])


def predicate_census(records):
    """Every predicate the document used, with its count, sample objects and qualifiers, for
    the merge's consolidation across documents."""
    census = {}
    for r in records:
        for f in r["facts"]:
            c = census.setdefault(f["predicate"], {"count": 0, "objects": [], "qualifiers": [], "object_is_entity": 0})
            c["count"] += 1
            c["object_is_entity"] += f["object_is_entity"]
            if f["object"] not in c["objects"] and len(c["objects"]) < 6:
                c["objects"].append(f["object"])
            if f["qualifiers"] and f["qualifiers"] not in c["qualifiers"] and len(c["qualifiers"]) < 4:
                c["qualifiers"].append(f["qualifiers"])
    return census


def write_package(doc, records, entities, folded, adjudicated, ledger, candidates, excluded, stats):
    path = package_path(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    scope = doc["doc_id"]
    written_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc_node = h(doc["doc_id"], "document")
    lines = []
    lines.append({"record": "package", "doc_id": doc["doc_id"], "source_uri": doc["source_uri"], "ingestor": INGESTOR,
                  "loader": doc.get("loader"), "input_hash": input_hash(doc), "written_at": written_at})
    lines.append({"record": "document", "doc_id": doc["doc_id"], "source_uri": doc["source_uri"], "sha256": doc["sha256"],
                  "title": doc["title"], "author": doc["author"], "source_class": doc["source_class"],
                  "ingested_at": doc["ingested_at"], "occurred_at": doc["occurred_at"], "loader": doc["loader"],
                  "flags": doc.get("flags", []), "text_length": len(doc["text"])})
    for u in doc["units"]:
        lines.append({"record": "unit", **u})
    for p in doc["pieces"]:
        lines.append({"record": "piece", **p})
    lines.append({"record": "node", "node_id": doc_node, "name": doc.get("title") or doc["source_uri"], "kind": "document",
                  "created_from_unit": doc["units"][0]["unit_id"] if doc["units"] else None, "provenance": {"ingestor": INGESTOR}})

    # nodes, aliases and edges for the majors; the map from a unit-local name to its node
    node_of = {}
    position_of = {u["unit_id"]: u["position"] for u in doc["units"]}
    for e in entities:
        nid = node_id_of(doc, e) if e["major"] else None
        for ui, local_name in e["members"]:
            node_of[(ui, local_name)] = nid
        if not e["major"]:
            continue
        first = min(e["unit_ids"], key=position_of.get)
        kind = e["kinds"][0] if len(e["kinds"]) == 1 else "/".join(e["kinds"])
        lines.append({"record": "node", "node_id": nid, "name": e["name"], "kind": kind, "created_from_unit": first,
                      "provenance": {"ingestor": INGESTOR, "salience": e["rank"], "names": e["names"][:12]}})
        for form, uid in e["first_unit_of"].items():
            lines.append({"record": "alias", "alias": form, "node_id": nid, "first_seen_unit": uid, "evidence_quote": None})
        lines.append({"record": "edge", "predicate": "appears_in", "subject": nid, "object": doc_node, "units": e["unit_ids"]})
    for u in doc["units"]:
        lines.append({"record": "edge", "predicate": "has_unit", "subject": doc_node, "object": u["unit_id"], "position": u["position"]})

    # per unit: mentions, profiles, facts, the summary cell, the entity cells
    dropped_minor = 0
    for r in records:
        for m in r["mentions"]:
            lines.append({"record": "mention", "mention_id": m["mention_id"], "node_id": node_of.get((r["position"], m["entity"])),
                          "unit_id": m["unit_id"], "start": m["start"], "end": m["end"], "surface": m["surface"],
                          "resolved_by": m["resolved_by"]})
        seen_profile = set()
        for p in r["profile"]:
            nid = node_of.get((r["position"], p["entity"]))
            key = (nid, p["attribute"], p["value"])
            if nid and key not in seen_profile:
                seen_profile.add(key)
                lines.append({"record": "profile", "node_id": nid, "attribute": p["attribute"], "value": p["value"],
                              "confidence": p["confidence"], "from_unit": p["from_unit"]})
        for f in r["facts"]:
            subject_node = node_of.get((r["position"], f["subject"]))
            object_node = node_of.get((r["position"], f["object"])) if f["object_is_entity"] else None
            if subject_node is not None:
                node, obj, is_node, direction = subject_node, object_node or f["object"], object_node is not None, "forward"
            elif object_node is not None:            # a minor's fact about a major: it lands on the major
                node, obj, is_node, direction = object_node, f["subject"], False, "inverse"
            else:
                dropped_minor += 1
                continue
            lines.append({"record": "fact", "fact_id": f["fact_id"], "subject": node, "predicate": f["predicate"],
                          "object": obj, "object_is_node": is_node, "direction": direction,
                          "qualifiers": f["qualifiers"], "rank": "active", "unit_id": f["unit_id"], "quote": f["quote"],
                          "quote_start": f["quote_start"], "quote_end": f["quote_end"], "valid_from": f["valid_from"],
                          "valid_to": f["valid_to"], "tier": f["tier"], "author": f["author"],
                          "provenance": {"ingestor": INGESTOR, "matched_by": f["matched_by"], "subject_name": f["subject"],
                                         "voice_ambiguous": f["voice_ambiguous"]}})
        if r["summary"]:
            lines.append({"record": "cell", "cell_id": h(doc_node, r["unit_id"]), "node_id": doc_node, "unit_id": r["unit_id"],
                          "scope_id": scope, "text": r["summary"], "tier": LUNA,
                          "provenance": {"ingestor": INGESTOR, "kind": "unit_summary"}})
        cells_by_node = {}
        for c in r["cells"]:
            nid = node_of.get((r["position"], c["entity"]))
            if nid:
                cells_by_node.setdefault(nid, []).append(c)
        for nid, cells in cells_by_node.items():
            lines.append({"record": "cell", "cell_id": h(nid, r["unit_id"]), "node_id": nid, "unit_id": r["unit_id"],
                          "scope_id": scope, "text": " ".join(c["text"] for c in cells), "tier": LUNA,
                          "provenance": {"ingestor": INGESTOR, "entity_names": [c["entity"] for c in cells]}})

    # the adjudicated record of each major
    for e in folded["majors"]:
        nid = node_id_of(doc, e)
        result = adjudicated.get(e["index"], {"facts": [], "attributes": [], "contradictions": []})
        for item in result["facts"]:
            lines.append({"record": "adjudicated_fact", "node_id": nid, "predicate": snake_case(item["predicate"]),
                          "object": item["object"], "qualifiers": item.get("qualifiers") or None,
                          "from_facts": item["from_facts"], "tier": TERRA})
        for item in result["attributes"]:
            lines.append({"record": "attribute", "node_id": nid, "attribute": item["attribute"], "value": item["value"],
                          "from_facts": item["from_facts"], "tier": TERRA})
        for item in result["contradictions"]:
            lines.append({"record": "contradiction", "node_id": nid, "note": item["note"], "from_facts": item["from_facts"]})

    # the document level: abstracts, dossiers, the ledger, the candidates, the census, rejections
    if folded["abstract"]:
        lines.append({"record": "abstract", "node_id": doc_node, "scope_id": scope, "text": folded["abstract"]["text"],
                      "children_hash": folded["abstract"]["children_hash"], "tier": folded["abstract"]["tier"], "updated_at": written_at})
    for a in folded["entity_abstracts"]:
        lines.append({"record": "abstract", "node_id": h(doc["doc_id"], a["entity"], a["first_unit"]), "scope_id": scope,
                      "text": a["text"], "children_hash": a["children_hash"], "tier": a["tier"], "updated_at": written_at})
    for d in folded["dossiers"]:
        lines.append({"record": "dossier", "node_id": h(doc["doc_id"], d["entity"], d["first_unit"]), "text": d["text"],
                      "embedding_model": EMBED_MODEL if "embedding" in d else None, "embedding": d.get("embedding")})
    for entry in ledger:
        lines.append({"record": "ledger", **entry})
    for entry in candidates:
        lines.append({"record": "candidate", **entry})
    lines.append({"record": "predicate_census", "predicates": predicate_census(records)})
    for r in records:
        for x in r["rejected_facts"]:
            lines.append({"record": "rejection", "stage": "facts", "unit_id": r["unit_id"], **x})
        for x in r["dropped_entities"]:
            lines.append({"record": "rejection", "stage": "entities", "unit_id": r["unit_id"], **x})

    counts = {"units": len(records), "entities": len(entities), "majors": len(folded["majors"]), "minors": len(folded["minors"]),
              "mentions": sum(len(r["mentions"]) for r in records), "facts_kept": sum(len(r["facts"]) for r in records),
              "facts_stored": sum(1 for l in lines if l["record"] == "fact"), "facts_minor_subject": dropped_minor,
              "facts_rejected": sum(len(r["rejected_facts"]) for r in records),
              "cells": sum(1 for l in lines if l["record"] == "cell"),
              "shared_spans": sum(r["shared_spans"] for r in records), "ambiguous_voice": sum(r["ambiguous_voice"] for r in records),
              "empty_units": sum(r["empty"] for r in records), "units_excluded": len(excluded),
              "in_summary_without_cell": sum(len(r["agreement"]["in_summary_without_cell"]) for r in records if r["agreement"]),
              "cell_without_summary_name": sum(len(r["agreement"]["cell_without_summary_name"]) for r in records if r["agreement"]),
              "major_without_fact": sum(len(r["agreement"]["major_without_fact"]) for r in records if r["agreement"]),
              "fact_but_minor": sum(len(r["agreement"]["fact_but_minor"]) for r in records if r["agreement"]),
              "demoted": len(folded.get("demoted", [])),
              "adjudicated_facts": sum(1 for l in lines if l["record"] == "adjudicated_fact"),
              "attributes": sum(1 for l in lines if l["record"] == "attribute"),
              "contradictions": sum(1 for l in lines if l["record"] == "contradiction"),
              "adjudication_dropped": sum(a.get("dropped", 0) for a in adjudicated.values()),
              "abstract": folded["abstract"] is not None}
    lines.append({"record": "completion", "doc_id": doc["doc_id"], "input_hash": input_hash(doc), "ingestor": INGESTOR,
                  "counts": counts, "stats": stats, "empty": counts["facts_stored"] == 0 and counts["cells"] == 0,
                  "excluded": excluded, "demoted": folded.get("demoted", []),
                  "abstract_rejected": folded["abstract_rejected"], "entity_abstract_rejected": folded["entity_abstract_rejected"]})
    body = "\n".join(json.dumps(l, ensure_ascii=False) for l in lines) + "\n"
    path.write_text(body, encoding="utf-8", newline="\n")
    return path, counts


def completed(doc):
    """The completion record of an existing package for this exact input, else None."""
    path = package_path(doc)
    if not path.exists():
        return None
    rows = read_own_jsonl(path)
    if not rows:
        return None
    last = rows[-1]
    if last.get("record") == "completion" and last.get("input_hash") == input_hash(doc):
        return last
    return None

# %%
# Block 11: the pipeline as one function, ingest(doc, diag).
#
# It calls the steps in order: triage (which kinds of unit to read), derive_unit for each unit
# kept, then reconcile, fold_document, adjudicate, write_package. `diag` is a dict of flags
# naming what to print as it happens, so a document can be watched unit by unit:
#   triage       the kinds of unit the document has, and which the judge left out and why
#   units        one line per unit as it finishes: counts, match paths, rejections, cost
#   entities     every entity kept in the unit, with its forms and what it continues
#   facts        every fact kept, with its match path and quote
#   rejections   every fact rejected, with its category and the quote that failed
#   cells        the unit summary, the cells, and the summary-versus-cells agreement
#   reconcile    how the unit-locals became document entities, and the judge's verdicts
#   ledger       every ledger row (long)
#   fold         the abstract, the majors and why each is major, the demotions, the entity abstracts
#   adjudicate   each major's consolidated record: how many facts, attributes and contradictions
#   package      the package path and its counts
# A finished package for the same input is skipped, so a rerun mints nothing; a document
# stopped mid-way resumes from the units its sidecar holds. Every document appends an entry
# to ingest.log and a row to manifest.jsonl; the receipt sums the packages on disk.
LOG = OUT / "ingest.log"
MANIFEST = OUT / "manifest.jsonl"
DIAG_ALL = {"triage": True, "units": True, "entities": True, "facts": True, "rejections": True, "cells": True,
            "reconcile": True, "ledger": False, "fold": True, "adjudicate": True, "package": True}
RESULTS = []                     # (source_uri, records, counts, stats) for every document this session ingested


def append_sidecar(doc, row):
    side = sidecar_path(doc)
    side.parent.mkdir(parents=True, exist_ok=True)
    with side.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ingestor": INGESTOR, "input_hash": input_hash(doc), **row}, ensure_ascii=False) + "\n")


def checkpointed(doc):
    """What a previous attempt at this document left in its sidecar, when it belongs to this
    input: (the kinds triage left out, the unit records in order, their cost, their calls).
    (None, [], 0, 0) when there is nothing to resume."""
    side = sidecar_path(doc)
    if not side.exists():
        return None, [], 0.0, 0
    rows = [row for row in read_own_jsonl(side) if row.get("ingestor") == INGESTOR and row.get("input_hash") == input_hash(doc)]
    if not rows or "triage" not in rows[0]:
        return None, [], 0.0, 0
    excluded = rows[0]["triage"]
    kept_ids = [u["unit_id"] for u in doc["units"] if unit_kind(doc, u) not in excluded]
    kept, cost, calls = [], 0.0, 0
    for row in rows[1:]:
        if "rec" in row and len(kept) < len(kept_ids) and row["rec"]["unit_id"] == kept_ids[len(kept)]:
            kept.append(row["rec"])
            cost += row.get("cost", 0.0)
            calls += row.get("calls", 0)
    return excluded, kept, cost, calls


def triage(doc, ctx):
    """The judge's call on which kinds of unit are not the work: {kind: reason}, plus any flags.
    One call per document; none when the document has a single kind, since leaving it out would
    leave nothing. The judge's answer stands whatever it leaves out, short of everything."""
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
        matched = None
        for kind in kinds:
            if kind.casefold() == named:
                matched = kind
        if matched is None:
            flags.append(f"triage named a kind the document does not have: {item['kind']!r}")
        else:
            excluded[matched] = item["reason"]
    left_out = sum(len(kinds[kind]) for kind in excluded)
    if left_out >= len(doc["units"]):                    # the judge may leave out anything but everything
        flags.append(f"triage would leave out every unit ({len(doc['units'])}); ignored")
        excluded = {}
    return excluded, flags


def valid_sources(numbers, n):
    """The fact numbers an adjudicated item points at, as distinct integers within 1..n."""
    if not isinstance(numbers, list):
        return []
    good = []
    for x in numbers:
        if isinstance(x, str) and x.strip().isdigit():
            x = int(x)
        if isinstance(x, int) and not isinstance(x, bool) and 1 <= x <= n and x not in good:
            good.append(x)
    return good


def adjudicate(records, folded, ctx):
    """One call per document-major over everything the document said about it: its raw facts
    (forward, and inverse when the entity was the object of a minor's fact) and its cells. The
    consolidated facts, attributes and contradictions come back pointing at the numbered raw
    facts; an item pointing at nothing listed is dropped and counted. Keyed by entity index."""
    member_index = {}
    for e in folded["majors"]:
        for ui, local_name in e["members"]:
            member_index[(ui, local_name)] = e["index"]
    raw_of = {e["index"]: [] for e in folded["majors"]}
    cells_of = {e["index"]: [] for e in folded["majors"]}
    for r in records:
        for f in r["facts"]:
            as_subject = member_index.get((r["position"], f["subject"]))
            as_object = member_index.get((r["position"], f["object"])) if f["object_is_entity"] else None
            if as_subject is not None:
                raw_of[as_subject].append((f, "forward", r["label"]))
            elif as_object is not None:
                raw_of[as_object].append((f, "inverse", r["label"]))
        for c in r["cells"]:
            index = member_index.get((r["position"], c["entity"]))
            if index is not None:
                cells_of[index].append(f"[{r['label']}] {c['text']}")
    out = {}
    for e in folded["majors"]:
        raws = raw_of[e["index"]]
        result = {"facts": [], "attributes": [], "contradictions": [], "dropped": 0, "raw": len(raws)}
        out[e["index"]] = result
        if not raws:
            continue
        listing = []
        for n, (f, direction, label) in enumerate(raws, 1):
            if direction == "forward":
                line = f"{n}. {e['name']} {f['predicate']} {f['object']}"
            else:
                line = f"{n}. (inverse) {f['subject']} {f['predicate']} {e['name']}"
            if f["qualifiers"]:
                line += f" [{f['qualifiers']}]"
            listing.append(line + f"  ({label}: \"{' '.join(f['quote'].split())[:120]}\")")
        predicates = sorted({f["predicate"] for f, direction, label in raws})
        reply = generate(adjudicate_prompt(e["name"], e["kinds"], listing, cells_of[e["index"]], predicates),
                         ADJUDICATE_SCHEMA, "adjudicate", model=TERRA, effort="medium", ctx=ctx)
        ids = [f["fact_id"] for f, direction, label in raws]
        for key in ("facts", "attributes", "contradictions"):
            for item in (reply or {}).get(key, []):
                sources = valid_sources(item.get("from"), len(ids))
                if not sources:
                    result["dropped"] += 1
                    continue
                kept = dict(item)
                del kept["from"]
                kept["from_facts"] = [ids[n - 1] for n in sources]
                result[key].append(kept)
    return out


def counts_text(counter):
    """'exact 6, normalised 2' from a dict of counts; 'none' when empty."""
    if not counter:
        return "none"
    return ", ".join(f"{k} {v}" for k, v in counter.items())


def show_unit(rec, unit, diag, unit_cost, total_cost):
    """One unit as it lands, in the demo's shape so the two runs read side by side."""
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
            continues = f"= {e['continues'][:24]}" if e["continues"] else ""
            print(f"    {e['name'][:34]:<34} {e['kind'][:9]:<9} {'named' if e['named'] else 'unnamed':<8}"
                  f" {'major' if e['major'] else 'minor':<6} x{e['mentions']:<3} {continues:<27} forms: {' | '.join(e['forms'][:4])[:60]}")
        for d in rec["dropped_entities"]:
            print(f"    DROPPED {d['name'][:34]}: {d['why']} {d['forms'][:3]}")
    if diag.get("facts"):
        for f in rec["facts"]:
            qualifiers = f" [{f['qualifiers']}]" if f["qualifiers"] else ""
            voice = ", voice ambiguous" if f["voice_ambiguous"] else ""
            print(f"    {f['subject']} -{f['predicate']}-> {f['object']}{qualifiers}  ({f['matched_by']}{voice})  \"{' '.join(f['quote'].split())[:90]}\"")
    if diag.get("rejections"):
        for x in rec["rejected_facts"]:
            print(f"    REJECTED {x['category']}: {x['subject']} -{x['predicate']}-> {x['object']}  \"{' '.join(x['quote'].split())[:90]}\"")
    if diag.get("cells") and rec["summary"]:
        print(f"    SUMMARY {rec['summary']}")
        for c in rec["cells"]:
            print(f"    [{c['entity']}] {c['text']}")
        a = rec["agreement"]
        if a:
            print(f"    agreement: {a['majors']} major, {a['cells']} cells, {a['named_in_summary']} named in the summary;"
                  f" in summary without a cell {a['in_summary_without_cell']}; cell not named in summary {a['cell_without_summary_name']}")
            print(f"    salience vs facts: {a['with_fact']} entities with a fact; major without a fact {a['major_without_fact']};"
                  f" fact but minor {a['fact_but_minor']}")


def show_reconcile(entities, ledger, candidates, n_locals, n_pairs, n_judged, diag):
    by_how, by_decision = {}, {}
    for entry in ledger:
        key = f"{entry['how']} {entry['verdict']}"
        by_how[key] = by_how.get(key, 0) + 1
    for c in candidates:
        by_decision[c["decision"]] = by_decision.get(c["decision"], 0) + 1
    print(f"reconcile: {n_locals} unit-locals -> {len(entities)} document entities; ledger {counts_text(by_how)};"
          f" {n_pairs} scored pairs ({counts_text(by_decision)}), {n_judged} sent to the judge")
    if diag.get("ledger"):
        for entry in ledger:
            print(f"    {entry['verdict']:<9} {entry['how']:<10} {entry['a'][:28]:<28} (u{entry['a_unit']}) ~ {entry['b'][:28]:<28} (u{entry['b_unit']})"
                  f"  {str(entry['evidence'])[:70]}")


def show_triage(doc, excluded, left_out, flags):
    kinds = {}
    for u in doc["units"]:
        kind = unit_kind(doc, u)
        kinds[kind] = kinds.get(kind, 0) + 1
    print("triage: " + ", ".join(f"{kind} {n}" for kind, n in kinds.items())
          + (f"; left out {len(left_out)} unit(s)" if left_out else "; nothing left out"))
    for kind, reason in excluded.items():
        print(f"    {kind}: {reason}")
    for flag in flags:
        print(f"    FLAG {flag}")


def show_adjudication(folded, adjudicated):
    total = {"raw": 0, "facts": 0, "attributes": 0, "contradictions": 0, "dropped": 0}
    for e in folded["majors"]:
        a = adjudicated.get(e["index"])
        if not a:
            continue
        for key in total:
            total[key] += a[key] if key in ("raw", "dropped") else len(a[key])
        print(f"    {e['name'][:34]:<34} {a['raw']:>3} raw facts -> {len(a['facts']):>3} facts, {len(a['attributes']):>3} attributes,"
              f" {len(a['contradictions'])} contradictions" + (f", {a['dropped']} dropped for pointing at nothing" if a["dropped"] else ""))
    print(f"adjudicated: {total['raw']} raw facts -> {total['facts']} facts, {total['attributes']} attributes,"
          f" {total['contradictions']} contradictions; {total['dropped']} dropped")


def show_fold(folded, diag):
    if folded["abstract"]:
        a = folded["abstract"]
        print(f"abstract ({word_count(a['text'])} words, limit {a['limit']}): {a['text']}")
    else:
        print(f"abstract REJECTED: {folded['abstract_rejected']}")
    print(f"salience: {len(folded['majors'])} major, {len(folded['minors'])} minor, {len(folded.get('demoted', []))} demoted;"
          f" {len(folded['entity_abstracts'])} entity abstracts, {len(folded['entity_abstract_rejected'])} rejected")
    if folded.get("demoted"):
        print(f"    demoted to minor (fewer than {DEMOTE_UNITS} units and {DEMOTE_FACTS} facts): {', '.join(folded['demoted'])[:200]}")
    for e in folded["majors"]:
        if e["rank"]["in_abstract"]:
            why = "in abstract"
        elif e["rank"]["in_abstract"] is None:
            why = "by tie-break"
        else:
            why = "?"
        others = [n for n in e["names"] if n != e["name"]]
        also = f"also: {', '.join(others)[:60]}" if others else ""
        print(f"    {e['name'][:34]:<34} {'/'.join(e['kinds'])[:16]:<16} units {len(e['units']):>3} facts {e['n_facts']:>3}  {why}  {also}")


def ingest(doc, ctx=None, diag=None):
    """One document, start to finish: the steps in order, each printed as the flags ask."""
    diag = diag or {}
    ctx = {"doc": doc["source_uri"], **(ctx or {})}
    calls_before, spend_before = len(CALLS), spend()

    # which kinds of unit to read: the sidecar's answer when resuming, else the judge's
    excluded, records, cost_before, calls_before_stop = checkpointed(doc)
    flags = []
    if excluded is None:
        side = sidecar_path(doc)
        if side.exists():
            side.unlink()
        excluded, flags = triage(doc, ctx)
        append_sidecar(doc, {"triage": excluded, "flags": flags})
    kept, left_out = [], []
    for u in doc["units"]:
        kind = unit_kind(doc, u)
        if kind in excluded:
            left_out.append({"position": u["position"], "kind": kind, "label": u["label"], "reason": excluded[kind]})
        else:
            kept.append(u)
    if diag.get("triage"):
        show_triage(doc, excluded, left_out, flags)

    # the units, in order, each checkpointed as it lands
    roster = {"entities": [], "predicates": [], "predicate_counts": {}}
    previous = None
    for rec in records:                           # replay what the sidecar holds
        advance_roster(roster, rec)
        previous = rec["summary"] or previous
    if records and diag.get("units"):
        print(f"resuming {doc['source_uri']} from {len(records)} checkpointed units")
    for u in kept[len(records):]:
        unit = {**u, "text": doc["text"][u["start"]:u["end"]], "kind": unit_kind(doc, u)}
        spend_at, calls_at = spend(), len(CALLS)
        rec = derive_unit(doc, unit, roster, previous, {**ctx, "unit": u["position"]})
        records.append(rec)
        append_sidecar(doc, {"rec": rec, "cost": round(spend() - spend_at, 6), "calls": len(CALLS) - calls_at})
        advance_roster(roster, rec)
        previous = rec["summary"] or previous
        if diag.get("units"):
            show_unit(rec, unit, diag, spend() - spend_at, spend() - spend_before)

    # the document: reconcile, fold, salience, adjudicate, write
    entities, ledger, candidates, n_locals, n_pairs, n_judged = reconcile(records, ctx, watch=bool(diag.get("reconcile")))
    if diag.get("reconcile"):
        show_reconcile(entities, ledger, candidates, n_locals, n_pairs, n_judged, diag)
    folded = fold_document(doc, records, entities, ctx)
    if diag.get("fold"):
        show_fold(folded, diag)
    adjudicated = adjudicate(records, folded, ctx)
    if diag.get("adjudicate"):
        show_adjudication(folded, adjudicated)
    stats = {"locals": n_locals, "candidate_pairs": n_pairs, "judged_pairs": n_judged,
             "calls": len(CALLS) - calls_before + calls_before_stop, "cost": round(spend() - spend_before + cost_before, 4),
             "matched_by": {}, "rejected_by": {}, "roster_size": len(roster["entities"]), "predicates": len(roster["predicates"]),
             "units_excluded": len(left_out), "triage_flags": flags}
    for r in records:
        for f in r["facts"]:
            stats["matched_by"][f["matched_by"]] = stats["matched_by"].get(f["matched_by"], 0) + 1
        for x in r["rejected_facts"]:
            stats["rejected_by"][x["category"]] = stats["rejected_by"].get(x["category"], 0) + 1
    path, counts = write_package(doc, records, entities, folded, adjudicated, ledger, candidates, left_out, stats)
    side = sidecar_path(doc)
    if side.exists():
        side.unlink()
    if diag.get("package"):
        print(f"package {path}: {counts}")
    RESULTS.append((doc["source_uri"], records, counts, stats))
    return path, counts, stats, records, entities, folded


def show(doc, counts, stats, entities, folded, path):
    """The end-of-document entry, always printed and appended to ingest.log."""
    if folded["abstract"]:
        abstract = folded["abstract"]["text"][:200]
    else:
        abstract = f"REJECTED {folded['abstract_rejected']}"
    lines = [f"{doc['source_uri']}  units {counts['units']}  entities {counts['entities']} ({counts['majors']} major)"
             f"  mentions {counts['mentions']}  facts {counts['facts_kept']} kept / {counts['facts_rejected']} rejected"
             f" / {counts['facts_stored']} stored  cells {counts['cells']}  calls {stats['calls']}  ${stats['cost']:.3f}",
             f"    matched {stats['matched_by']}  rejected {stats['rejected_by']}  locals {stats['locals']}"
             f" pairs {stats['candidate_pairs']} judged {stats['judged_pairs']}",
             f"    abstract: {abstract}"]
    for e in folded["majors"][:12]:
        lines.append(f"    {e['name'][:36]:<36} {'/'.join(e['kinds'])[:16]:<16} units {len(e['units']):>3} facts {e['n_facts']:>3}")
    lines.append(f"    -> {path}")
    entry = "\n".join(lines) + "\n"
    print(entry)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")


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
                print(f"\n=== {uri}: {len(doc['units'])} units, {len(doc['text']):,} chars{' (text rebuilt from the PDF)' if doc.get('text_rebuilt') else ''},"
                      f" author {doc.get('author')!r}, date {doc.get('occurred_at')} ===")
            path, counts, stats, records, entities, folded = ingest(doc, diag=diag)
            with MANIFEST.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"doc_id": doc["doc_id"], "source_uri": uri,
                                    "package": str(path.relative_to(OUT)).replace("\\", "/"),
                                    "input_hash": input_hash(doc), "counts": counts, "cost": stats["cost"]}) + "\n")
            show(doc, counts, stats, entities, folded, path)
        except SpendStop as e:
            note(f"{uri}: {e} after ${spend() - spend_before:.3f} on this document;"
                 " its finished units are checkpointed and the run stops here")
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
    """Sums over every package on disk, plus the calls this session logged to calls.jsonl."""
    rec = {"ingestor": INGESTOR, "documents": 0, "by_group": {}, "counts": {}, "matched_by": {}, "rejected_by": {},
           "cost_of_packages": 0.0, "cost_this_session": round(spend(), 4), "calls_this_session": len(CALLS),
           "calls_by_stage": {}, "schema_rejections_this_session": len(REJECTIONS), "empty_completions": 0,
           "abstract_rejected": 0, "in_flight_sidecars": []}
    for c in CALLS:
        rec["calls_by_stage"][c["stage"]] = rec["calls_by_stage"].get(c["stage"], 0) + 1
    for path in sorted(OUT.rglob("*.jsonl")):
        if path.parent == OUT:                    # the run's own logs
            continue
        if path.name.endswith(".units.jsonl"):
            rec["in_flight_sidecars"].append(str(path.relative_to(OUT)).replace("\\", "/"))
            continue
        rows = read_own_jsonl(path)
        if not rows or rows[-1].get("record") != "completion":
            continue
        last = rows[-1]
        rec["documents"] += 1
        group = path.parent.name
        rec["by_group"][group] = rec["by_group"].get(group, 0) + 1
        for k, v in last["counts"].items():
            if isinstance(v, (int, bool)):
                rec["counts"][k] = rec["counts"].get(k, 0) + int(v)
        for k, v in last["stats"].get("matched_by", {}).items():
            rec["matched_by"][k] = rec["matched_by"].get(k, 0) + v
        for k, v in last["stats"].get("rejected_by", {}).items():
            rec["rejected_by"][k] = rec["rejected_by"].get(k, 0) + v
        rec["cost_of_packages"] = round(rec["cost_of_packages"] + last["stats"].get("cost", 0), 4)
        rec["empty_completions"] += bool(last.get("empty"))
        rec["abstract_rejected"] += last.get("abstract_rejected") is not None
    (OUT / "receipt.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return rec

# %%
# Block 12: naming documents, and the test variety.
#
# targets(spec) turns what a run names into source_uris: "sample" for the test variety, "all"
# for the export, or a list of titles or source_uri endings, looked up by find_document. The
# test variety samples every source type the extractor produces, the paper and chat paths
# first-class: three hundred LongMemEval sessions, twenty papers, two GraphRAG-Bench texts,
# three Oz books (the regression fixture against the 09-02 demo), two Holmes collections and
# two Greek works, cheapest first, so a run that hits the stop has finished the chat and paper
# paths before the books, where the judge spends most.


def sample(per_group=None):
    chats = sorted(u for u in BY_URI if "/longmemeval/" in u)
    papers = sorted(u for u in BY_URI if u.endswith(".pdf"))
    books = ["/graphrag-bench/Novel-30752.txt", "/graphrag-bench/Novel-40700.txt",
             "/oz/01_55.txt", "/oz/02_54.txt", "/oz/03_486.txt",
             "/holmes/03_1661.txt", "/holmes/05_2852.txt",
             "/greek/03_348.txt", "/greek/11_830.txt"]
    book_uris = [find_document(b) for b in books]
    if per_group:
        return chats[:per_group] + papers[:per_group] + book_uris[:per_group]
    return chats[:300] + papers[:20] + book_uris


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

# %%
# Block 13: the run.
#
# RUN names the documents, by title or by the end of their source_uri; DIAG says what to print
# as each unit lands (block 11 lists the flags); SPEND_STOP ends the run past that many dollars,
# the document in flight keeping its finished units in a sidecar for next time. For reference,
# the 09-02 demo on Oz book 1: v3 632 entities, 969 facts, 53 dropped, $1.26; v4 644, 859, 157,
# $1.72. Later: RUN = "sample" for the test variety, "all" for the corpus.
RUN = ["The Wonderful Wizard of Oz"]
DIAG = dict(DIAG_ALL)
SPEND_STOP = 5.00

if __name__ == "__main__":
    uris = targets(RUN)
    print(f"ingesting {len(uris)} documents, stop at ${SPEND_STOP:.2f}: {[BY_URI[u]['title'] or u for u in uris]}")
    try:
        run(uris, diag=DIAG)
    finally:
        print(json.dumps(receipt(), indent=1))
