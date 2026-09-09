# %% [markdown]
# # FactLedger extractor
#
# One raw file at a time, to a **split plan**: which document the file is, where it divides, and
# what kind of text each part is. No entities, no facts, no summaries; those are the ingestor's
# job. This is Step 0.
#
# **The one rule: the extractor sees a raw file and nothing else.** The format is sniffed from
# the bytes. There is no filename convention, no per-corpus branch, and no hand-written rule
# about where a publisher's boilerplate ends. Every boundary in the output is a decision the
# model made and code verified; code never decides where a break may go, and the model never
# returns a character offset. The manifests are packaging and an answer key, read in block 1 to
# prove the mounted bytes are the uploaded bytes, and never again.
#
# ## What comes in
#
# One mount (`RAW`, the public raw dataset), one folder per corpus, each with a `manifest.json`
# recording every file's source URL, byte count and sha256:
#
# | corpus | files | shape |
# |---|---|---|
# | `longmemeval` | 19,206 | one JSON per assistant chat session |
# | `kg-rag-cc` | 100 | CC-BY papers on knowledge graphs and RAG, PDFs under `pdf/` |
# | `greek` | 31 | Greek and Roman literature, including OCR'd institutional scans |
# | `oz` | 29 | the Oz books |
# | `graphrag-bench` | 20 | GraphRAG-Bench novel contexts |
# | `holmes` | 9 | the Sherlock Holmes volumes |
#
# Three shapes are sniffed from the first bytes, and nothing else about a file is consulted:
#
# | sniffed as | how it is read |
# |---|---|
# | PDF | the text layer, pages joined by one newline (PyMuPDF, the one dependency) |
# | chat JSON | rendered `role: content` per turn under a session header, turn spans kept |
# | plain text | the bytes decoded as UTF-8, unchanged |
#
# ## What goes out
#
# `/kaggle/working/splits.jsonl` holds one record per document as it finishes, so a stopped run
# resumes; `export/` holds the dataset. All offsets everywhere are **document offsets**,
# character indices into `documents.text` for the same `doc_id`, one coordinate system, so any
# piece, unit or later fact quote resolves with a single slice.
#
# `documents.jsonl`, one row per document:
#
# | field | meaning |
# |---|---|
# | `doc_id` | the sha256 of the file bytes; every other row joins on it |
# | `source_uri` | mount, corpus and file, for example `it494-narrative-corpora-raw/oz/01_55.txt` |
# | `title`, `author`, `occurred_at` | what the model read off the page and a pointer proved |
# | `source_class` | `record` for a chat, `published` for a PDF, the model's answer for plain text |
# | `text` | the decoded string, whole, for every document |
# | `sha256`, `ingested_at`, `loader`, `flags` | provenance, and what the gates could not verify |
#
# `units.jsonl`, one row per unit, the size-bounded runs the pieces were grouped into:
#
# | field | meaning |
# |---|---|
# | `unit_id`, `doc_id`, `position` | its id, its document, its place in reading order |
# | `label` | a human label: a chapter title, or a range of turns |
# | `start`, `end` | character offsets into the document text |
# | `occurred_at`, `occurred_until` | when it was said, when the file carries times |
#
# `pieces.jsonl`, one row per natural piece (a chapter, a section, a turn) inside a unit:
#
# | field | meaning |
# |---|---|
# | `doc_id`, `unit_id`, `position`, `start`, `end` | where it is |
# | `kind` | six regions of a written document (`front_matter`, `body`, `notes`, `references`, `appendix`, `license`) or two turns of a conversation (`user`, `assistant`) |
# | `author` | the speaker of a chat turn, else `null` |
# | `occurred_at` | the time of a turn, else `null` |
#
# `receipt.json`: the run's own counts and cost, written by the run.
#
# Checked at export on every document, not asserted: pieces and units each **tile** their
# document with no gaps and no overlaps, a unit **never mixes kinds**, `unit_id` is unique, and
# every unit's slice is a real, non-empty slice of the text.
#
# ## The algorithm for a document that must be read
#
# ```
# extract(file):
#     read        sniff the container from the bytes and decode it to one string
#     address     number the document's own non-blank lines; a file with no usable lines
#                 (a PDF text layer that puts one word on a line) is numbered by sentence
#     ask once    one call over the whole document, for
#                     source_class, title, author, source, date  each a pointer plus its value
#                     toc_count                                  what the contents list promises
#                     regions                                    where front matter ends, body
#                                                                begins, and notes, references,
#                                                                appendix and license sit
#                     pieces                                     the chapters, sections, scenes
#                 a document that defeats Luna twice is asked once more on Terra, if it fits
#     gate        the model points at a line BY NUMBER AND COPIES ITS TEXT, so a pointer
#                 resolves only when the copy names the line: the line itself, its first eight
#                 words, a run of five or more of its words, or a two-line heading copied whole
#                     wrong number, text found nearby -> recovered and counted
#                     text nowhere                    -> dropped and counted
#                 nothing the model asserted without a verified pointer reaches the output
#     sub-split   a piece over CAP_WORDS goes back as numbered lines and is cut at the breaks
#                 the model points at, up to three rounds; one it cannot break stays whole
#     merge short a piece under SHORT_WORDS is offered with its text: it joins the piece
#                 before, the piece after, or stands alone
#     group       the outline goes back and the model groups consecutive pieces into units, a
#                 section with its subsections, never two peers merely because they fit;
#                 code then checks the groups cover the outline in order, dissolves a group
#                 over the cap, and cuts any group where the kind changes
#     write       one record to splits.jsonl; the export tiles and checks it
# ```
#
# ## The algorithm for a chat session
#
# ```
# extract(chat):
#     no call. The session already states its own boundaries.
#     pieces      the turns; the role is the author
#     units       runs of turns under CAP_WORDS, never a lone turn, never spanning a change of
#                 day, a tail under TAIL_FLOOR merged back into the unit before it
#     header      the session header is front matter and a unit of its own
# ```
#
# 19,206 of the 19,395 documents cost nothing to split.
#
# ## On Kaggle
#
# Attach the raw dataset (`jhffmn/it494-narrative-corpora-raw`), which carries every corpus
# including the papers. Attach `OPENAI_API_KEY` under Add-ons > Secrets and turn Internet on.
# Run block 3 to see the connection work, then the blocks in order. Finished documents are
# appended to `splits.jsonl` and skipped on a restart, so to continue a stopped run, make a
# dataset from that output and attach it. `REDO_ALL` re-asks clean records an older loader
# wrote; a hard spending stop halts the run, and running out of API credit is fatal by design,
# so a dead key cannot walk the corpus writing empty flagged records.


# %%
# Block 1: inputs and integrity.
# Mount the raw dataset, count files per folder, and check every file's sha256 against the
# folder manifest. The manifests are used here only to prove the Kaggle copies are the bytes
# that were uploaded; the extractor itself never reads them.
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def mount(slug):
    """Kaggle mounts inputs at /kaggle/input/<slug> or, in newer sessions,
    /kaggle/input/datasets/<owner>/<slug>. Take whichever exists."""
    for candidate in (Path("/kaggle/input") / slug, Path("/kaggle/input/datasets/jhffmn") / slug):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError(slug)


RAW = mount("it494-narrative-corpora-raw")
SIDECARS = ("manifest.json", "LICENSE", "README.md")   # packaging, never a document


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(folder):
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    # each manifest names its rows for its own corpus: works, papers, or files
    rows = manifest.get("works") or manifest.get("papers") or manifest["files"]
    # relative posix paths, so a corpus that keeps its files in a subfolder (kg-rag-cc/pdf) checks too
    on_disk = {p.relative_to(folder).as_posix() for p in folder.rglob("*")
               if p.is_file() and p.name not in SIDECARS}
    listed = {r["file"] for r in rows}
    # Kaggle inputs are a network filesystem: one file at a time, 19,206 files take tens of
    # minutes; 32 concurrent reads take about a minute.
    with ThreadPoolExecutor(max_workers=32) as pool:
        digests = list(pool.map(sha256, [folder / r["file"] for r in rows]))
    bad = [r["file"] for r, d in zip(rows, digests) if d != r["sha256"]]
    print(f"{folder.name:<28} files {len(on_disk):>6}  listed {len(listed):>6}"
          f"  mismatched {len(bad)}  unlisted {len(on_disk - listed)}  missing {len(listed - on_disk)}")
    return bad


for name in ("oz", "holmes", "greek", "graphrag-bench", "longmemeval", "kg-rag-cc"):
    check(RAW / name)


# %%
# Block 2: file type, then raw text.
#
# Two steps, by bytes only. Nothing here decides what the text is about; that is the model's
# job later.
#   1. file_kind(data): look at the first bytes and name the container: pdf, json, or text.
#   2. to_text(path): turn the container into one string, the document text.
#        pdf  -> the text layer, page by page (PyMuPDF, the one dependency)
#        json -> if it holds chat turns, one "role: content" block per turn under a header
#                of the session id and dates. We also keep where each turn starts and ends
#                in that string, so a chat can be cut into units without a model.
#        text -> the bytes decoded as UTF-8, unchanged
import json

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf          # PyMuPDF before 1.24.3 has only its old module name
    except ImportError:
        import subprocess
        import sys
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pymupdf"], check=True)
        import pymupdf


def file_kind(data):
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.lstrip()[:1] in (b"{", b"["):
        return "json"
    return "text"


def pdf_text(data):
    doc = pymupdf.open(stream=data, filetype="pdf")
    return "\n".join(page.get_text() for page in doc)


def chat_turns(obj):
    """The list of {role, content} turns inside a chat JSON, wherever it sits; None if absent."""
    if isinstance(obj, list) and obj and all(isinstance(t, dict) and "role" in t and "content" in t for t in obj):
        return obj
    if isinstance(obj, dict):
        for value in obj.values():
            found = chat_turns(value)
            if found:
                return found
    return None


def chat_text(obj, turns):
    """Header lines, a blank line, then 'role: content' per turn. Returns the text and the
    (start, end) of each turn inside it."""
    header = [f"session_id: {obj['session_id']}"] if "session_id" in obj else []
    header += [f"date: {d}" for d in obj.get("dates", [])]
    text = "\n".join(header) + "\n\n"
    spans = []
    for turn in turns:
        start = len(text)
        text += f"{turn['role']}: {turn['content']}\n\n"
        spans.append((start, len(text)))
    return text, spans


def to_text(path):
    data = path.read_bytes()
    doc = {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(),
           "kind": file_kind(data), "text": "", "turns": None, "dates": []}
    if doc["kind"] == "pdf":
        doc["text"] = pdf_text(data)
    elif doc["kind"] == "json":
        obj = json.loads(data)
        turns = chat_turns(obj)
        if turns is None:
            doc["kind"], doc["text"] = "text", data.decode("utf-8", errors="replace")
        else:
            doc["kind"] = "chat"
            doc["text"], doc["turns"] = chat_text(obj, turns)
            doc["dates"] = list(obj.get("dates", []))
    else:
        doc["text"] = data.decode("utf-8", errors="replace")
    return doc


# One of each, to see the shape.
for path in [RAW / "oz" / "01_55.txt", RAW / "graphrag-bench" / "Novel-30752.txt",
             RAW / "longmemeval" / "sharegpt_yywfIrx_0.json", RAW / "longmemeval" / "001cefa7_2.json",
             RAW / "kg-rag-cc" / "pdf" / "001_2024.eacl-demo.16.pdf"]:
    d = to_text(path)
    turns = len(d["turns"]) if d["turns"] else "-"
    print(f"{path.name:<26} {d['kind']:<5} {len(d['text']):>8,} chars  turns {turns:>3}  dates {d['dates']}")
    print("    " + repr(d["text"][:70]))


# %%
# Block 3: the model call.
import json
import threading
import time

import requests
from kaggle_secrets import UserSecretsClient

MODEL = "gpt-5.6-luna"
RETRY = "gpt-5.6-terra"
RETRY_MAX_TOKENS = 80_000     # Terra is ten times Luna's price: only a document under this many tokens gets it
PRICE = {"gpt-5.6-luna": (0.20, 1.20), "gpt-5.6-terra": (2.00, 12.00)}   # $ per M tokens in, out
SPEND_STOP = 25.00                                                       # dollars; the run halts past this
try:
    KEY = UserSecretsClient().get_secret("OPENAI_API_KEY")
except Exception:                        # a 400 here means the secret is not attached to this notebook
    KEY = None
    print("OPENAI_API_KEY is not attached to this notebook: Add-ons > Secrets, tick Attach; Settings > Internet on")
calls = []


class TooLong(Exception):
    """The document does not fit the model's context in one call."""


class SpendStop(Exception):
    """The run must stop: the session has spent SPEND_STOP, or the account is out of credits.
    Block 8 writes the documents in flight and leaves the rest for the next session."""


def spend():
    return sum(c["cost"] for c in calls)


BILL = {}                                        # thread -> the document its calls belong to


def bill_to(name):
    """Every call this thread makes from here counts against `name`."""
    BILL[threading.get_ident()] = name


def spent_on(name):
    return sum(c["cost"] for c in calls if c.get("bill") == name)


def generate(prompt, model=MODEL, effort="low"):
    """One JSON-mode call; the reply parsed, the cost logged. The API rejects temperature.
    A timeout, connection error, 429, or 5xx is retried three times with a pause; any other
    non-200 raises with the response body."""
    if not KEY:
        raise RuntimeError("no OPENAI_API_KEY: attach it under Add-ons > Secrets and rerun block 3")
    if spend() >= SPEND_STOP:
        raise SpendStop(f"spending stop: ${spend():.2f}")
    p_in, p_out = PRICE[model]
    t0 = time.time()
    for attempt in range(3):
        try:
            r = requests.post("https://api.openai.com/v1/chat/completions",
                              headers={"Authorization": f"Bearer {KEY}"}, timeout=300,
                              json={"model": model, "reasoning_effort": effort,
                                    "response_format": {"type": "json_object"},
                                    "messages": [{"role": "user", "content": prompt}]})
        except (requests.Timeout, requests.ConnectionError):
            # the server may have finished and billed the request: count the input as spent
            calls.append({"model": model, "in": len(prompt) // 4, "out": 0, "seconds": round(time.time() - t0, 1),
                          "bill": BILL.get(threading.get_ident()), "timeout": True,
                          "cost": len(prompt) // 4 * p_in / 1e6})
            if attempt == 2:
                raise
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code in (401, 403) or (r.status_code == 429 and "quota" in r.text.lower()):
            raise SpendStop(f"OpenAI {r.status_code}: {r.text[:120]}")   # no credits or no key: stop
        if r.status_code == 429 or r.status_code >= 500:                 # busy: wait and try again
            if attempt == 2:
                raise RuntimeError(f"OpenAI {r.status_code}: {r.text}")
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code != 200:
            if r.status_code == 400 and "context" in r.text.lower():
                raise TooLong(r.text[:200])
            raise RuntimeError(f"OpenAI {r.status_code}: {r.text}")
        break
    body = r.json()
    u = body["usage"]
    calls.append({"model": body["model"], "in": u["prompt_tokens"], "out": u["completion_tokens"],
                  "seconds": round(time.time() - t0, 1), "bill": BILL.get(threading.get_ident()),
                  "cost": (u["prompt_tokens"] * p_in + u["completion_tokens"] * p_out) / 1e6})
    return json.loads(body["choices"][0]["message"]["content"])


print(f"model {MODEL}, retry {MODEL} then {RETRY} under {RETRY_MAX_TOKENS:,} tokens, spend stop ${SPEND_STOP:.2f}, key {'present' if KEY else 'MISSING'}")


# %%
# Block 4: the address list. Every non-blank line of the document, numbered. The model points
# at lines by number; code never decides where a break may be. A document without lines (a
# whole book on one string) is addressed by sentence instead. An address is a (start, end)
# span in the document text; the model sees "[i] text" and answers with i and the text.
import re


def addresses(text):
    """Line spans, or sentence spans when the file has no lines to speak of, or when its lines
    are one word each: a PDF text layer that breaks every word onto its own line is not giving
    us lines, and numbering them costs more than the text it numbers."""
    lines = [l for l in text.split("\n") if l.strip()]
    per_line = sum(len(l.split()) for l in lines) / max(1, len(lines))
    has_lines = text.count("\n") >= len(text) / 500 and per_line >= 2
    if not has_lines:
        return [(m.start(), m.end()) for m in re.finditer(r"[^.!?]+[.!?]*", text) if m.group().strip()]
    out, start = [], 0
    for line in text.split("\n"):
        if line.strip():
            out.append((start, start + len(line)))
        start += len(line) + 1
    return out


def listing(text, addrs):
    return "\n".join(f"[{i}] {' '.join(text[s:e].split())}" for i, (s, e) in enumerate(addrs))


for path in [RAW / "oz" / "01_55.txt", RAW / "greek" / "03_348.txt", RAW / "graphrag-bench" / "Novel-30752.txt",
             RAW / "kg-rag-cc" / "pdf" / "001_2024.eacl-demo.16.pdf"]:
    d = to_text(path)
    a = addresses(d["text"])
    n = len(listing(d["text"], a))
    print(f"{path.name:<26} {len(d['text']):>9,} chars  {len(a):>6,} addresses  {n:>9,} chars to the model  (~{n // 4:,} tokens)")


# %%
# Block 5: the question. One call per document, the whole document in it. Every pointer is a
# number and the line's text, so the number can be checked and, when it is off by a few,
# recovered from the text. Regions and pieces are the model's decisions; code does not add,
# move, or remove a boundary. Pieces carry no date of their own: a text or PDF unit takes
# the document's date.
PROMPT = """Below is one document as numbered lines. Answer with JSON only. Point at a line by its number and copy its text exactly as listed (a long line may be cut after its first eight words), so a program can check the number. Never invent a line.

{
  "source_class": "canonical" (a published literary or classic work), "published" (a paper, article, or report), or "authored" (a person's own notes, email, letters, drafts),
  "title": {"index": n, "text": "...", "title": "the title as it should read"} or null,
  "author": {"index": n, "text": "...", "name": "the person's name as it should read"} or null,
  "source": {"index": n, "text": "...", "name": "..."} or null: the publication or organization the text comes from (a newspaper, a journal, an agency), when the text names one; never the transcriber or ebook publisher,
  "date": {"index": n, "text": "...", "iso": "YYYY" or "YYYY-MM" or "YYYY-MM-DD"} or null: the line giving the date the work was written or first published, or sent; for a translation or a later edition, the original work's date when the file gives it; never a transcription or ebook release date; null when the file states none,
  "toc_count": the number of pieces the contents list gives, or null,
  "regions": [{"index": n, "text": "...", "kind": "..."}, ...],
  "pieces": [{"index": n, "text": "..."}, ...]
}

Regions tile the document in order, each running from its line to the next region's line; the first region begins at line 0. Kinds: "front_matter" (publisher notices, the contents list, transcriber's or translator's notes; an author's own preface or introduction is body), "body" (the work itself), "notes" (footnotes, endnotes, commentary, wherever they fall), "references" (a bibliography or reference list), "appendix" (the work's own appendices), "license" (ebook or license boilerplate). Give every region the document has: a scholarly edition may alternate body and notes several times, and a paper's appendices usually follow its references.

Pieces are the document's own divisions: chapters, acts and scenes, sections, dated entries, poems, stories, in every region that has them. A paper's pieces are its sections, the abstract first, and its appendix sections. Point at the line where each piece begins in the text, never at its entry in the contents list. A heading that runs over two lines (a number on one line, its title on the next) is one piece: point at its first line.

%s
"""


def ask(text, addrs, model=MODEL):
    return generate(PROMPT % listing(text, addrs), model)


# %%
# Block 6: pieces from the answer, and the gates.
#   resolve   a pointer becomes an address span: its index when the text there matches, else
#             the nearest address within WINDOW whose text matches (counted as recovered),
#             else nothing (counted as unresolved). A copy matches its line whole, as the
#             line's first eight words, or as a run of five words or more inside it, so a
#             short copy like "CHAPTER I" must match exactly while a longer one may drop the
#             line's opening quotation mark or marker; an empty copy verifies nothing.
#             Two pointers on one line count as duplicate.
#   pieces_from_reply   every region start and every piece start is a boundary; the spans
#             between consecutive boundaries are the pieces, each with the kind of the region
#             it lies in and the heading's own words as its label. Nothing is dropped: the
#             pieces tile the document from its first byte to its last.
#   verify_meta   title, author, source and date go through the same check as every other
#             pointer, and the date's year must appear on its line; one that fails is nulled,
#             so nothing the model invented is exported.
#   gates     a body region present, fewer headed pieces than the contents count, coverage (no
#             body piece holds most of the body when a contents list says there are
#             divisions), every pointer resolved, every region kind known, the first region
#             at line 0, and the document pointers. A failed gate is a flag, never a drop;
#             a metadata or shape flag alone does not buy a retry.
#   split     addresses, one call, gates; on a flag one more call on the same model, and a
#             third on the retry model when the document is under RETRY_MAX_TOKENS; the answer
#             kept is the one with a body region and the fewest flags. A document too long for
#             one call is one piece of kind "whole" and a flag.
KINDS = ("front_matter", "body", "notes", "references", "appendix", "license")
WINDOW = 5          # addresses either side searched when an index and its text disagree
CAP_WORDS = 4000    # a unit stays under this; block 7 splits and groups against it
TAIL_FLOOR = CAP_WORDS // 3   # a last run of turns under this joins the unit before it


def norm(s):
    return " ".join(str(s or "").split()).casefold()


def cut8(s):
    return " ".join(s.split()[:8])


def clean(want):
    """The model's copy with a listing prefix '[i] ' and a trailing ellipsis removed; tried
    only after the copy as given, because a line can begin with '[1]' or end in '...' itself."""
    w = re.sub(r"^\[\d+\]\s*", "", norm(want))
    return re.sub(r"\s*(\.\.\.|…)$", "", w).strip()


def words_of(s):
    return re.findall(r"[^\W_]+", s)


def matches(text, span, want, loose=False):
    """Does the copy name this line? Three ways, in order: it is the line, it is the line's
    first eight words (the prompt allows a long line to be cut there), or its words are a run
    of five or more inside the line. Five keeps a short heading strict, so "CHAPTER I" cannot
    answer for "CHAPTER II". `loose` allows a substring and is used only for the title, author
    and date, which are a few words inside a longer line."""
    if not want:
        return False
    line = norm(text[slice(*span)])
    if want == line or want == cut8(line) or (loose and want in line):
        return True
    w, l = words_of(want), words_of(line)
    return len(w) >= 5 and any(l[i:i + len(w)] == w for i in range(len(l) - len(w) + 1))


def as_int(v):
    """A line number from the model: an integer, or a string of digits. Anything else is not a
    number and the caller counts it."""
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    return int(v) if isinstance(v, str) and v.strip().isdigit() else None


def as_list(v):
    return v if isinstance(v, list) else []


def wrapped_hit(text, addrs, wants):
    """The address holding a copy that wraps across lines. The line-by-line checks cannot see
    it, so the text itself is searched once, whitespace-flexibly, and only a copy of five words
    or more appearing exactly once places a boundary."""
    for w in wants:
        parts = w.split()[:12]
        if len(parts) < 5:
            continue
        hits = list(re.finditer(r"\s+".join(re.escape(p) for p in parts), text, re.I))
        if len(hits) == 1:
            return max((a for a in addrs if a[0] <= hits[0].start()), default=None)
    return None


def resolve(pointer, text, addrs, stats, loose=False):
    """A pointer's address span. The copy may be the line, its first eight words, a prefix of
    five words or more, or a sentence that runs on into the next two lines (the model points
    into wrapped prose when it splits a long piece). A wrong index still resolves when the copy
    names exactly one line in the document."""
    if not isinstance(pointer, dict):
        return None
    i = as_int(pointer.get("index"))
    wants = list(dict.fromkeys(w for w in (norm(pointer.get("text")), clean(pointer.get("text"))) if w))

    def at(j):
        """The copy names line j: the line itself, the next line joined to it (a heading written
        over two lines), or a copy of five words or more that begins inside line j and wraps
        into the next two. The model is asked for a line and answers with a sentence, and a
        sentence both starts mid line and runs on; beginning inside line j is what makes this
        line the answer rather than the one the sentence ends in."""
        if any(matches(text, addrs[j], w, loose) for w in wants):
            return True
        two = norm(" ".join(text[slice(*addrs[k])] for k in range(j, min(j + 2, len(addrs)))))
        three = norm(" ".join(text[slice(*addrs[k])] for k in range(j, min(j + 3, len(addrs)))))
        here = len(norm(text[slice(*addrs[j])]))
        for w in wants:
            if w == two:
                return True
            if len(w.split()) >= 5 and 0 <= three.find(w) < here:
                return True
        return False

    if not wants:                                    # nothing to check the number against
        stats["mismatch"] += 1
        stats["unresolved"] += 1
        return None
    if i is not None and 0 <= i < len(addrs) and at(i):
        return addrs[i]
    stats["mismatch"] += 1
    if i is not None:
        for d in range(1, WINDOW + 1):               # nearest first
            for j in (i - d, i + d):
                if 0 <= j < len(addrs) and at(j):
                    stats["recovered"] += 1
                    return addrs[j]
    hits = [j for j in range(len(addrs)) if any(matches(text, addrs[j], w) for w in wants)]
    if len(hits) == 1:                               # strictly, so a one-word copy cannot wander
        stats["recovered"] += 1
        return addrs[hits[0]]
    span = wrapped_hit(text, addrs, wants)           # the copy is a sentence, and a sentence wraps
    if span is not None:
        stats["recovered"] += 1
        return span
    stats["unresolved"] += 1
    if len(stats.setdefault("unresolved_samples", [])) < 6:   # what the model actually sent, for the log
        stats["unresolved_samples"].append({"index": pointer.get("index"), "text": str(pointer.get("text") or "")[:80]})
    return None


def label_at(text, addrs, k):
    """The pointed line's words; a rule of dashes or stars, with no letter or digit in any
    script, takes the next line's words."""
    label = " ".join(text[slice(*addrs[k])].split())
    if not re.search(r"[^\W_]", label) and k + 1 < len(addrs):
        label = " ".join(text[slice(*addrs[k + 1])].split())
    return label


# Every flag reads "kind: what happened". These kinds describe the document, or record a
# fallback that is a fine answer in itself, so they buy no call in this session or the next.
# The kinds not listed are the model answering badly, which another sample may fix: "pointers",
# "count", "coverage", "regions", "over cap", and the two "... answer" kinds below.
ADVISORY = {"metadata", "shape", "dates", "too long", "merging", "grouping"}


def advisory(flag):
    return flag.split(":")[0] in ADVISORY


def piece(start, end, label, kind, author=None, occurred_at=None):
    return {"start": start, "end": end, "label": label, "kind": kind, "author": author, "occurred_at": occurred_at}


def words(text, p):
    return len(text[p["start"]:p["end"]].split())


def pieces_from_reply(text, r, addrs, stats):
    at_index = {start: i for i, (start, _) in enumerate(addrs)}
    regions, unknown = [], []
    for g in as_list(r.get("regions")):
        span = resolve(g, text, addrs, stats)
        if span is None:
            continue
        kind = g.get("kind")
        if kind not in KINDS:                            # the boundary is kept under the model's own word, and flagged
            kind = (norm(kind).replace(" ", "_")[:20] if isinstance(kind, str) and kind.strip() else "unknown")
            unknown.append(kind)
        regions.append((span[0], kind))
    regions.sort()
    if not regions:
        regions = [(0, "whole")]
    stats["first_region_at"] = at_index.get(regions[0][0], 0)              # its line number
    stats["unknown_kinds"] = unknown
    regions[0] = (0, regions[0][1])                      # the first region runs from the first byte
    heads = {}
    for q in as_list(r.get("pieces")):
        span = resolve(q, text, addrs, stats)
        if span is None:
            continue
        if span[0] in heads:
            stats["duplicate"] += 1
        heads[span[0]] = label_at(text, addrs, at_index[span[0]])
    starts = sorted({s for s, _ in regions} | set(heads))
    pieces = []
    for s, e in zip(starts, starts[1:] + [len(text)]):
        kind = [k for rs, k in regions if rs <= s][-1]
        label = heads.get(s, "opening" if kind == "body" else kind.replace("_", " "))
        pieces.append(piece(s, e, label, kind))
    stats["headed"] = sum(1 for q in pieces if q["start"] in heads)
    stats["body_share"] = round(sum(q["end"] - q["start"] for q in pieces if q["kind"] == "body") / max(1, len(text)), 3)
    return pieces


MONTHS = ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec")


def date_ok(line, iso):
    """The iso to keep, checked against the line the model read it from: the year must be on
    that line as digits, and a month or day is kept only when the line names the month. None
    when the year is not there, so a date the model inferred from elsewhere is never stored."""
    if not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", iso) or iso[:4] not in line:
        return None
    if len(iso) > 4:
        m, low = int(iso[5:7]), line.lower()
        if not (1 <= m <= 12 and (MONTHS[m - 1] in low or re.search(rf"\b0?{m}\b", low))):
            return iso[:4]
    return iso


def fresh_stats(addrs, model):
    return {"addresses": len(addrs), "mismatch": 0, "recovered": 0, "unresolved": 0, "duplicate": 0, "model": model}


def verify_meta(text, r, addrs, stats):
    """Title, author, source and date pointers, checked like every other, but counted into a
    scratch dict so a failure here is flagged and nulled rather than bought back with a whole
    document call. Nothing the model invented is exported."""
    for key in ("title", "author", "source", "date"):
        v = r.get(key)
        if v is None:
            continue
        span = resolve(v, text, addrs, fresh_stats(addrs, None), loose=True) if isinstance(v, dict) else None
        if span is not None and key == "date":
            kept = date_ok(text[slice(*span)], str(v.get("iso") or ""))
            if kept is None:
                span = None
            else:
                v["iso"] = kept
        if span is None:
            r[key] = None
            stats["meta_unresolved"] = stats.get("meta_unresolved", 0) + 1
            stats.setdefault("meta_nulled", []).append(key)


def gates(pieces, r, stats, text):
    flags = []
    body = [q for q in pieces if q["kind"] == "body"]
    if not body:
        flags.append("no body region")
    toc = as_int(r.get("toc_count"))
    if toc is not None and stats["headed"] < toc:     # more pieces than the contents lists is not an error:
        flags.append(f"count: {stats['headed']} headed pieces, contents says {toc}")
    if body and sum(words(text, q) for q in body) > CAP_WORDS:
        share = max(q["end"] - q["start"] for q in body) / max(1, sum(q["end"] - q["start"] for q in body))
        if share > 0.6:                                  # a retry only when a contents list says there are divisions
            kind = "coverage" if toc is not None and toc > 1 else "shape"
            flags.append(f"{kind}: one piece holds {share:.0%} of the body")
    if stats["unresolved"]:
        flags.append(f"pointers: {stats['unresolved']} matched no line")
    if stats.get("meta_unresolved"):
        flags.append(f"metadata: {stats['meta_unresolved']} pointer(s) matched no line")
    if stats.get("unknown_kinds"):
        flags.append(f"regions: unknown kind(s) {', '.join(sorted(set(stats['unknown_kinds'])))}")
    if stats.get("first_region_at", 0) > 0:
        flags.append(f"regions: first begins at line {stats['first_region_at']}, not 0")
    return flags


def split(doc):
    """pieces, reply, flags, stats for one text or PDF document."""
    text = doc["text"]
    addrs = addresses(text)
    tokens = len(listing(text, addrs)) // 4
    attempts = [MODEL, MODEL] + ([RETRY] if tokens < RETRY_MAX_TOKENS else [])
    best = None
    for model in attempts:
        stats = fresh_stats(addrs, model)
        try:
            r = ask(text, addrs, model)
        except TooLong:
            break
        if not isinstance(r, dict):
            r = {}
        verify_meta(text, r, addrs, stats)
        pieces = pieces_from_reply(text, r, addrs, stats)
        flags = gates(pieces, r, stats, text)
        assert pieces[0]["start"] == 0 and pieces[-1]["end"] == len(text) \
            and all(a["end"] == b["start"] for a, b in zip(pieces, pieces[1:]))     # the pieces tile the text
        retry = [f for f in flags if not advisory(f)]
        rank = ("no body region" in flags, len(retry), len(flags))
        if best is None or rank < best[0]:
            best = (rank, pieces, r, flags, stats)
        if not retry:
            break
    if best is None:
        return ([piece(0, len(text), "whole document", "whole")], {},
                [f"too long: about {tokens:,} tokens for one call"], {**fresh_stats(addrs, None), "too_long": True})
    return best[1:]


# %%
# Block 7: units. The model decides these too, in three calls.
#   subsplit  a piece over CAP_WORDS is shown to the model as numbered lines and it points at
#             the natural breaks inside; a part still over the cap is split again, DEPTH times
#             at most. A piece the model cannot break stays whole; block 8 flags it. The parts
#             carry the piece they came from, so grouping keeps them apart.
#   merge_short   every piece under SHORT_WORDS is offered to the model with its text; it joins
#             the piece before, the piece after, or stands alone, as the model says.
#   group     the outline (every piece with its kind, words, and heading) goes to the model,
#             which groups consecutive pieces into units: a piece with the pieces under it
#             (a section with its subsections, a chapter with its scenes, a play with its
#             notes), never two peers merely because they fit, each unit under the cap. Code
#             checks that the groups cover the outline in order; a group over the cap is
#             dissolved into its pieces and flagged; a grouping that does not cover the
#             outline is dropped for one unit per piece and flagged.
# A text or PDF unit carries the document's date. Chat pieces are the turns, built from the
# turn spans block 2 kept, with the role as author and the session date as time when there is
# one, after a front_matter piece for the header. A chat unit is a run of at least two turns
# under the cap, never across a day change, the short tail merged into the unit before it, with
# no model call; the header opens the first turn's unit. Voice does not depend on where a unit
# ends: every turn is its own piece and carries its own author. A session the benchmark reused
# carries several dates and takes the one it started on, on the document, its units and its
# turns alike.
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

DEPTH = 3            # rounds of splitting a piece that stays over the cap
FANOUT = 8           # sub-splits of one document in flight at once

SPLIT_PROMPT = """Below is one piece of a document as numbered lines: "%s", about %d words, over the limit of %d words for one unit. Point at the lines where it naturally breaks (a scene change, a section, a new episode, a new topic) so that no part is over the limit, using as few breaks as that allows. A break is the first line of the paragraph where the new part begins. Answer with JSON only: {"breaks": [{"index": n, "text": "..."}, ...]}. Point at a line by its number and copy that line's text exactly as listed (a long line may be cut after its first eight words). Never invent a line.

%s
"""

GROUP_PROMPT = """Below is the outline of one document: its pieces in order, each with its kind, its length in words, and its heading. Group consecutive pieces into units. A unit is one piece together with the pieces that belong under it: a section with its subsections, a chapter with its scenes. Never join two peers (two chapters, two top-level sections) merely because they fit, and never join pieces of different kinds: a unit is all body, or all notes, or all appendix. Pieces marked (part) are the parts of one piece already split for length: they stay separate and never rejoin. A unit must stay under %d words; a single piece over that stands alone. Every piece belongs to exactly one unit, in order, with no gaps. Answer with JSON only: {"units": [{"first": n, "last": n}, ...]}, where first and last are piece numbers from the list.

%s
"""


SHORT_WORDS = 100    # a piece under this is offered to the model to merge with a neighbour

MERGE_PROMPT = """Below are the pieces of one document in order, each with its kind, its length in words, and its heading; every piece under %d words also shows its whole text. Decide for each short piece whether it belongs with the piece before it, with the piece after it, or stands on its own: a bare heading, a part title, or a title line belongs with what follows it; a closing line or a sliver cut off a paragraph belongs with what precedes it; a short poem, letter, entry, or note that is a piece in its own right stands alone. Answer with JSON only: {"merges": [{"index": n, "into": "previous" or "next" or "alone"}, ...]}, one entry per short piece, index from the list.

%s
"""


def subsplit(text, p, stats, depth=0):
    """The piece, or its parts, each under the cap wherever the model found a break."""
    if words(text, p) <= CAP_WORDS or depth >= DEPTH:
        return [p]
    addrs = [(p["start"] + s, p["start"] + e) for s, e in addresses(text[p["start"]:p["end"]])]
    at_index = {start: i for i, (start, _) in enumerate(addrs)}
    cuts = {}
    for attempt in range(2):                             # one more try when no break resolved
        try:
            r = generate(SPLIT_PROMPT % (p["label"], words(text, p), CAP_WORDS, listing(text, addrs)))
        except TooLong:
            return [p]
        for b in as_list(r.get("breaks") if isinstance(r, dict) else None):
            span = resolve(b, text, addrs, stats)
            if span and p["start"] < span[0] < p["end"]:
                cuts[span[0]] = label_at(text, addrs, at_index[span[0]])
        if cuts:
            break
    if not cuts:
        return [p]
    stats["subsplits"] = stats.get("subsplits", 0) + 1
    starts = [p["start"]] + sorted(cuts)
    parts = [{**piece(s, e, p["label"] if s == p["start"] else cuts[s][:80], p["kind"], p["author"], p["occurred_at"]),
              "part": p.get("part") or p["label"][:40]}                  # parts of one piece stay apart in grouping
             for s, e in zip(starts, starts[1:] + [p["end"]])]
    return [q for part in parts for q in subsplit(text, part, stats, depth + 1)]


def merge_stats(into, other):
    """One thread's counts folded into the document's."""
    for key, value in other.items():
        if isinstance(value, int) and key != "addresses":
            into[key] = into.get(key, 0) + value
        elif isinstance(value, list):
            into.setdefault(key, []).extend(value)
    into["unresolved_samples"] = into.get("unresolved_samples", [])[:6]
    return into


def subsplit_all(text, pieces, stats):
    """Every over-cap piece split at once. The pieces are independent, so the calls go out
    together; each thread counts into its own stats and they are folded in afterwards, in
    piece order, so a rerun of the same answers gives the same numbers."""
    over = [i for i, p in enumerate(pieces) if words(text, p) > CAP_WORDS]
    if not over:
        return pieces
    mine = {i: fresh_stats([], stats.get("model")) for i in over}
    name = BILL.get(threading.get_ident())       # the parts bill to the document they came from

    def one(i):
        bill_to(name)
        return subsplit(text, pieces[i], mine[i])

    with ThreadPoolExecutor(max_workers=min(FANOUT, len(over))) as pool:
        parts = dict(zip(over, pool.map(one, over)))
    for i in over:
        merge_stats(stats, {k: v for k, v in mine[i].items() if k != "addresses"})
    return [q for i, p in enumerate(pieces) for q in (parts[i] if i in parts else [p])]


def outline(text, pieces, show_short=False):
    lines = []
    for i, q in enumerate(pieces):
        part = f" (part of {q['part']})" if q.get("part") else ""
        lines.append(f"[{i}] {q['kind']} | {words(text, q)} words | {q['label'][:80]}{part}")
        if show_short and words(text, q) < SHORT_WORDS:
            lines.append("    text: " + " ".join(text[q["start"]:q["end"]].split())[:600])
    return "\n".join(lines)


def merge_short(text, pieces, stats, flags):
    """Every piece under SHORT_WORDS is offered to the model, which joins it to the piece
    before, to the piece after, or leaves it alone. A join is always between neighbours, so
    the answers mark which gaps close and one sweep rebuilds the list; no answer is applied
    against a list another answer already changed. A join across a region boundary, or one
    that would carry a piece past the cap, is left alone and flagged."""
    short = {i for i, q in enumerate(pieces) if words(text, q) < SHORT_WORDS}
    if not short or len(pieces) == 1:
        return pieces
    try:
        r = generate(MERGE_PROMPT % (SHORT_WORDS, outline(text, pieces, show_short=True)))
    except TooLong:
        flags.append("merging: outline too long; short pieces left alone")
        return pieces
    closes = [False] * len(pieces)                   # closes[i]: pieces i and i+1 become one
    back = set()                                     # a piece that asked to join what precedes it
    crossed, odd = 0, []
    for m in as_list(r.get("merges") if isinstance(r, dict) else None):
        i = as_int(m.get("index")) if isinstance(m, dict) else None
        how = norm(m.get("into")) if isinstance(m, dict) else ""
        if i not in short or how not in ("previous", "next", "alone"):
            odd.append(str(m.get("into") if isinstance(m, dict) else m)[:20])
        elif how != "alone":
            j = i + 1 if how == "next" else i - 1
            if not 0 <= j < len(pieces):
                continue
            if pieces[j]["kind"] != pieces[i]["kind"]:      # the model's region boundary stands
                crossed += 1
            else:
                closes[min(i, j)] = True
                if how == "previous":
                    back.add(i)
    if odd:
        flags.append(f"merging answer: {len(odd)} not understood: {', '.join(sorted(set(odd))[:4])}")
    if crossed:
        flags.append(f"merging: join across a region boundary left alone, {crossed}")

    runs, run = [], [0]
    for i in range(len(pieces) - 1):
        if closes[i]:
            run.append(i + 1)
        else:
            runs.append(run)
            run = [i + 1]
    runs.append(run)

    out = []
    for idx in runs:
        if len(idx) == 1:
            out.append(pieces[idx[0]])
            continue
        already_over = any(words(text, pieces[k]) > CAP_WORDS for k in idx)
        if not already_over and sum(words(text, pieces[k]) for k in idx) > CAP_WORDS:
            flags.append(f"merging: over cap, left alone: {pieces[idx[0]]['label'][:40]}")
            out.extend(pieces[k] for k in idx)
            continue
        # Every piece in a run shares its kind, and text and PDF pieces carry no author or
        # time, so the first piece's fields stand for the run; only the label is composed. A
        # heading that joins what follows keeps its words. A sliver that joins a longer
        # neighbour disappears into it, but two short pieces joining each other (a heading
        # written over two lines) both keep theirs. A label code gave a piece is dropped.
        has_long = any(words(text, pieces[k]) >= SHORT_WORDS for k in idx)
        named = [pieces[k]["label"] for k in idx if not (has_long and k in back)
                 and pieces[k]["label"] not in ("opening", pieces[k]["kind"].replace("_", " "))]
        out.append({**pieces[idx[0]], "end": pieces[idx[-1]]["end"],
                    "label": (" / ".join(named) or pieces[idx[0]]["label"])[:120]})
    stats["merged"] = len(pieces) - len(out)
    return out


def split_by_kind(pieces, run):
    """The run cut wherever the kind changes, so a unit never holds two kinds. Returns the run
    itself when it is already of one kind, which is how the caller counts the cuts."""
    parts, part = [], [run[0]]
    for i in run[1:]:
        if pieces[i]["kind"] == pieces[part[-1]]["kind"]:
            part.append(i)
        else:
            parts.append(part)
            part = [i]
    parts.append(part)
    return [run] if len(parts) == 1 else parts


def group(text, pieces, stats, flags):
    """Runs of piece indices as the model grouped them, cut where the kind changes."""
    if len(pieces) == 1:
        return [[0]]
    try:
        r = generate(GROUP_PROMPT % (CAP_WORDS, outline(text, pieces)))
    except TooLong:
        flags.append("grouping: outline too long, one unit per piece")
        return [[i] for i in range(len(pieces))]
    runs, expect = [], 0
    for u in as_list(r.get("units") if isinstance(r, dict) else None):
        a, b = (as_int(u.get("first")), as_int(u.get("last"))) if isinstance(u, dict) else (None, None)
        if a is None or b is None or a != expect or not a <= b < len(pieces):
            break
        runs.append(list(range(a, b + 1)))
        expect = b + 1
    if expect != len(pieces):
        flags.append(f"grouping answer: covered {expect} of {len(pieces)} pieces; one unit per piece")
        return [[i] for i in range(len(pieces))]
    out, mixed = [], 0
    for run in runs:
        parts = split_by_kind(pieces, run)        # a unit is all of one kind
        mixed += len(parts) > 1 or parts[0] is not run
        for part in parts:
            if len(part) > 1 and sum(words(text, pieces[i]) for i in part) > CAP_WORDS:
                flags.append(f"grouping: dissolved a group over the cap: {pieces[part[0]]['label'][:40]} .. {pieces[part[-1]]['label'][:40]}")
                out.extend([[i] for i in part])
            else:
                out.append(part)
    if mixed:
        flags.append(f"grouping: {mixed} group(s) cut where the kind changed")
    stats["groups"] = len(out)
    return out


def parse_time(value):
    """ISO 8601, or the 'yyyy/mm/dd (Dow) hh:mm' form; None when it is neither."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except (ValueError, AttributeError):
        pass
    parts = value.replace("/", " ").replace(":", " ").split()
    try:
        y, mo, d = int(parts[0]), int(parts[1]), int(parts[2])
        h, mi = (int(parts[-2]), int(parts[-1])) if len(parts) >= 5 else (0, 0)
        return datetime(y, mo, d, h, mi).isoformat()
    except (ValueError, IndexError):
        return None


def chat_pieces(doc):
    """The header as front matter, then one piece per turn. The role is read back from the
    'role: ' prefix block 2 wrote. A session reused by the benchmark carries several dates;
    the document, its units and its turns take the one it started on."""
    text = doc["text"]
    dates = sorted(t for t in (parse_time(d) for d in doc["dates"]) if t)
    when = dates[0] if dates else None
    pieces = [piece(0, doc["turns"][0][0], "front matter", "front_matter", occurred_at=when)]   # the header block 2 wrote
    for i, (s, e) in enumerate(doc["turns"]):
        role = text[s:e].split(":", 1)[0].strip()
        pieces.append(piece(s, e, f"turn {i + 1}", kind=role, author=role, occurred_at=when))
    flags = [f"dates: {len(dates)} session dates, {when[:10]} kept"] if len(dates) > 1 else []
    return pieces, flags


def day(t):
    return (t or "")[:10]


def chat_runs(pieces, text):
    """Runs of piece indices: at least two turns each unless a day changes, under the cap where
    two turns allow it, the short tail merged into the unit before it. Index 0 is the header,
    which is front matter, and so is a unit of its own: a unit is all of one kind."""
    runs, run, size = [], [], 0
    for i, q in enumerate(pieces[1:], start=1):
        w = words(text, q)
        turns = len(run)
        new_day = bool(run) and day(q["occurred_at"]) != day(pieces[run[-1]]["occurred_at"])
        if run and (new_day or (size + w > CAP_WORDS and turns >= 2)):
            runs.append(run)
            run, size = [], 0
        run.append(i)
        size += w
    if run:
        same_day = runs and day(pieces[run[0]]["occurred_at"]) == day(pieces[runs[-1][-1]]["occurred_at"])
        if runs and same_day and (size < TAIL_FLOOR or len(run) < 2):   # a short tail, or a lone turn
            runs[-1].extend(run)
        else:
            runs.append(run)
    return [[0]] + runs


def units_from_runs(pieces, runs, text):
    units = []
    for i, run in enumerate(runs):
        ps = [pieces[j] for j in run]
        times = [q["occurred_at"] for q in ps if q["occurred_at"]]
        label = ps[0]["label"] if len(ps) == 1 else f"{ps[0]['label']} .. {ps[-1]['label']}"
        units.append({"position": i, "start": ps[0]["start"], "end": ps[-1]["end"], "label": label,
                      "occurred_at": min(times) if times else None, "occurred_until": max(times) if times else None,
                      "pieces": len(ps), "words": sum(words(text, q) for q in ps)})
        for q in ps:
            q["unit"] = i
    return units


# %%
# Block 8: every document in the raw dataset, resumable. Each finished document is appended to
# splits.jsonl as one record: file (dataset-relative), path, sha256, kind, reply, pieces, units,
# flags, stats, cost. On a rerun a document is skipped by file name before it is read when its
# last record was written by this loader AND is clean or carries only advisory flags (metadata,
# shape), or is a chat (a chat's flags cannot change), or it has been asked in two sessions
# already; otherwise it is tried again, and the last record per file wins. A record an older
# loader wrote is always redone, because a code change is exactly what a resume must not keep. Chats need
# no model call. Texts and PDFs print a full entry; chats print one line per hundred. The spend
# stop writes the document in flight as a flagged record, so its cost is kept, and ends the loop.
import threading

SPLITS = Path("/kaggle/working/splits.jsonl")
LOG = Path("/kaggle/working/splits.log")
# Every record says which loader wrote it, so a resume can tell one build from another. Keep
# this in step with the code: 1.1 and 1.2 both shipped under the 1.0 label, so running the
# older notebook after a newer one could not tell the work had been done and asked the whole
# corpus again.
LOADER = "factledger-extractor 1.5"
REDO_ALL = False                        # True also re-asks clean records an older loader wrote


def rel_of(path):
    """'raw/oz/01_55.txt' or 'raw/kg-rag-cc/pdf/001_x.pdf': the same name on any Kaggle mount."""
    return f"raw/{path.relative_to(RAW).as_posix()}"


def path_of(record):
    rel = record.get("file")
    if rel is None:
        return Path(record["path"])                          # a record written before files were named
    return RAW / rel[4:]


def iso_of(reply):
    d = reply.get("date") if isinstance(reply, dict) else None
    return d.get("iso") if isinstance(d, dict) else None


def read_splits():
    """The last record per file, each carrying tries: how many records the file has."""
    latest, tries = {}, {}
    if SPLITS.exists():
        for line in SPLITS.read_text(encoding="utf-8").split("\n"):   # never splitlines(): text can hold U+2028
            if line:
                record = json.loads(line)
                if "flags" not in record:                              # rows from an earlier design are skipped
                    continue
                key = record.get("file") or rel_of(Path(record["path"]))
                record["file"] = key
                tries[key] = tries.get(key, 0) + 1
                record["tries"] = tries[key]
                latest[key] = record
    return latest


def rendered(r, key, field):
    """The model's rendering of a pointer (title, name), else the line it pointed at."""
    v = r.get(key) or {}
    return (v.get(field) or v.get("text")) if isinstance(v, dict) else None


def show(doc, record):
    text, r, pieces, units = doc["text"], record["reply"], record["pieces"], record["units"]
    st = record["stats"]
    lines = [f"{Path(record['path']).name}  {'FLAGGED' if record['flags'] else 'ok'}  pieces {len(pieces)}  units {len(units)}"
             f"  addresses {st.get('addresses')}  mismatch {st.get('mismatch', 0)} recovered {st.get('recovered', 0)}"
             f" duplicate {st.get('duplicate', 0)}  subsplits {st.get('subsplits', 0)} merged {st.get('merged', 0)}"
             f" groups {st.get('groups', 0)} short units {st.get('short_units', 0)}  model {st.get('model', '-')}  ${record['cost']:.3f}",
             f"    class {r.get('source_class')} | title {rendered(r, 'title', 'title')!r}"
             f" | author {rendered(r, 'author', 'name')!r} | source {rendered(r, 'source', 'name')!r}"
             f" | date {iso_of(r)}"
             f" | toc {r.get('toc_count')} | body {st.get('body_share', 0):.0%} of {len(text):,} chars"]
    for p in pieces:
        snippet = " ".join(text[p["start"]:p["start"] + 90].split())[:60]
        lines.append(f"    {p['start']:>8} {words(text, p):>6} w  u{p.get('unit', 0):<3} {p['kind'][:12]:<12} {p['label'][:40]:<40} | {snippet}")
    lines += [f"    FLAG {f}" for f in record["flags"]]
    lines += [f"    unresolved [{u['index']}] {u['text']}" for u in st.get("unresolved_samples", [])]
    entry = "\n".join(lines) + "\n"
    print(entry)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")


paths = sorted(RAW.glob("oz/*.txt")) + sorted(RAW.glob("holmes/*.txt")) + sorted(RAW.glob("greek/*.txt")) \
      + sorted(RAW.glob("graphrag-bench/*.txt")) + sorted(RAW.glob("kg-rag-cc/pdf/*.pdf")) \
      + sorted(p for p in RAW.glob("longmemeval/*.json") if p.name != "manifest.json")
latest = read_splits()
def settled(rec):
    """A record needs no further call: it is clean or only advisory, or it is a chat (whose
    flags cannot change), or it has been asked in two sessions already."""
    return all(advisory(f) for f in rec["flags"]) or rec.get("kind") == "chat" or rec["tries"] >= 2


done = {key for key, rec in latest.items() if settled(rec) and (rec.get("loader") == LOADER or not REDO_ALL)}
older = sum(1 for key, rec in latest.items() if settled(rec) and rec.get("loader") != LOADER)
print(f"{LOADER}: {len(done)} documents already settled"
      + (f", {older} of them written by an older loader and kept (REDO_ALL is False)" if older and not REDO_ALL
         else f"; REDO_ALL is True, so {older} written by an older loader are asked again" if older else ""))
DOCUMENTS = 6        # documents in flight at once; each may fan out FANOUT sub-splits
lock = threading.Lock()
stop = threading.Event()                         # set once the spend stop trips
counted = {"chats": 0}


def run_one(path):
    """One document, start to record. Returns the record, or None when there is nothing to do.
    Every task is queued at once, so the stop is a flag every task checks: once it is set,
    the rest return untouched and are picked up by the next session's resume."""
    rel = rel_of(path)
    if rel in done or stop.is_set():
        return None
    bill_to(rel)
    doc, stopped = None, False
    try:
        doc = to_text(path)
        if doc["kind"] == "chat":
            pieces, flags = chat_pieces(doc)
            reply, stats = {}, {"addresses": None}
            runs = chat_runs(pieces, doc["text"])
        else:
            pieces, reply, flags, stats = split(doc)
            unresolved = stats["unresolved"]
            if not stats.get("too_long"):
                pieces = subsplit_all(doc["text"], pieces, stats)
            if stats["unresolved"] > unresolved:
                flags.append(f"pointers: {stats['unresolved'] - unresolved} break(s) matched no line")
            pieces = merge_short(doc["text"], pieces, stats, flags)
            for q in pieces:
                if words(doc["text"], q) > CAP_WORDS:
                    flags.append(f"over cap: {q['label'][:40]} ({words(doc['text'], q):,} words)")
            runs = group(doc["text"], pieces, stats, flags)
        units = units_from_runs(pieces, runs, doc["text"])
        if doc["kind"] != "chat":                    # a text or PDF unit carries the document's date
            for u in units:
                u["occurred_at"] = u["occurred_until"] = iso_of(reply)
            stats["short_units"] = sum(1 for u in units if u["words"] < SHORT_WORDS)
    except SpendStop as e:                       # keep what it cost, flagged; it is redone next session
        stopped = True
        stop.set()
        pieces = [piece(0, len(doc["text"]), "whole document", kind="whole")]
        units, reply, stats = units_from_runs(pieces, [[0]], doc["text"]), {}, {}
        flags = [f"spend stop: {e}; not finished"]
    except Exception as e:                       # one document must not end a two-hour run
        if doc is None:                          # the file itself could not be read or parsed
            doc = {"text": "", "sha256": hashlib.sha256(rel.encode("utf-8")).hexdigest(), "kind": "error", "turns": None, "dates": []}
        pieces = [piece(0, len(doc["text"]), "whole document", kind="whole")]
        units, reply, stats = units_from_runs(pieces, [[0]], doc["text"]), {}, {}
        flags = [f"run error: {type(e).__name__}: {str(e)[:200]}"]
    record = {"file": rel, "path": str(path), "sha256": doc["sha256"], "kind": doc["kind"], "loader": LOADER,
              "reply": reply, "pieces": pieces, "units": units, "flags": flags, "stats": stats,
              "cost": round(spent_on(rel), 4)}
    with lock:                                   # one writer, and one document's log at a time
        with SPLITS.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        done.add(rel)
        if doc["kind"] == "chat":
            counted["chats"] += 1
            if flags or counted["chats"] % 100 == 0:
                print(f"{path.name}  {'FLAGGED ' + '; '.join(flags) if flags else 'ok'}  turns {len(pieces)}  units {len(units)}  ({counted['chats']} chats so far)")
        else:
            show(doc, record)
    if stopped:
        print(f"{flags[0]}: stopping; {path.name} is written flagged and will be redone next session")
    return record


with ThreadPoolExecutor(max_workers=DOCUMENTS) as pool:
    for _ in pool.map(run_one, paths):
        pass
print(f"{len(done)} documents in {SPLITS.name}, ${spend():.2f} spent this session"
      + ("; the spend stop trips, the rest wait for the next session" if stop.is_set() else ""))


# %%
# Block 9: export in the schema, plus the receipt. Last record per document wins.
#   documents.jsonl  doc_id, source_uri, sha256, title, author, source_class, text, ingested_at,
#                    occurred_at, loader, flags
#   units.jsonl      unit_id, doc_id, position, label, start, end, occurred_at, occurred_until
#   pieces.jsonl     the piece table of SCHEMA.md: doc_id, unit_id, position, kind, start, end,
#                    author, occurred_at
#   receipt.json     counts by kind, chars by piece kind, flags by kind, unknown authors and dates,
#                    reused session dates, pointer mismatches, recoveries and duplicates, over-cap
#                    units, cost of every call this file holds, not only the winning records
# Files are read 32 at a time: one at a time, 19,206 chats take tens of minutes on Kaggle's
# network filesystem (block 1's own measurement).
from datetime import timezone

OUT = Path("/kaggle/working/export")
OUT.mkdir(parents=True, exist_ok=True)
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")
BY_KIND = {"chat": "record", "pdf": "published"}         # a text document takes the model's answer
CLASSES = {"canonical", "published", "record", "authored", "tool-output"}   # SCHEMA.md


def unit_id(doc_id, text, start, end, seen):
    """Content hash of the slice; the n-th identical slice in one document gets n in the hash."""
    body = text[start:end]
    n = seen.get(body, 0)
    seen[body] = n + 1
    return hashlib.sha256(f"{doc_id}\n{n}\n{body}".encode("utf-8")).hexdigest()


def spent_in(splits):
    """Every call the file paid for, including records later replaced."""
    total = 0.0
    if splits.exists():
        for line in splits.read_text(encoding="utf-8").split("\n"):
            if line:
                total += json.loads(line).get("cost", 0)
    return total


def load(record):
    """The document for a record; a file that cannot be read now is an empty error document."""
    try:
        return to_text(path_of(record))
    except Exception:
        return {"text": "", "sha256": record["sha256"], "kind": "error", "turns": None, "dates": []}


records = list(read_splits().values())
receipt = {"documents": 0, "units": 0, "pieces": 0, "by_kind": {}, "chars_by_kind": {}, "flags_by_kind": {}, "flagged": [],
           "duplicate_files": [], "unknown_author": 0, "unknown_date": 0, "ambiguous_date": 0,
           "mismatch": 0, "recovered": 0, "unresolved": 0, "duplicate": 0, "meta_unresolved": 0,
           "over_cap_read": 0, "over_cap_chat": 0, "short_read": 0, "short_chat": 0,
           "total_chars": 0, "read_chars": 0, "cost": round(spent_in(SPLITS), 3)}
files = {name: (OUT / f"{name}.jsonl").open("w", encoding="utf-8") for name in ("documents", "units", "pieces")}
exported = {}                                            # doc_id -> file: identical bytes are one document

with ThreadPoolExecutor(max_workers=32) as pool:
    docs = pool.map(load, records)
    for record, doc in zip(records, docs):
        text, doc_id, r = doc["text"], doc["sha256"], record["reply"]
        if doc_id in exported:                           # same bytes as a file already exported: same doc_id, one row
            receipt["duplicate_files"].append({"file": record["file"], "same_as": exported[doc_id]})
            continue
        exported[doc_id] = record["file"]
        rel = record.get("file") or rel_of(Path(record["path"]))
        src = f"{RAW.name}/{rel[4:]}"
        title = rendered(r, "title", "title")
        author = rendered(r, "author", "name")
        occurred = iso_of(r) or None
        flags = list(record["flags"])
        if author is None and "author" not in (record.get("stats") or {}).get("meta_nulled", []) \
                and rendered(r, "source", "name"):
            author = rendered(r, "source", "name")     # no person named at all: the publication is the voice
            flags.append("author is a publication")
        if doc["kind"] == "chat":                        # the date it started on, as block 7 gives its units
            dates = sorted(t for t in (parse_time(d) for d in doc["dates"]) if t)
            occurred = dates[0] if dates else None
        source_class = BY_KIND.get(doc["kind"], r.get("source_class") if isinstance(r, dict) else None)
        if source_class not in CLASSES:
            flags.append("source_class unknown")
            source_class = None
        files["documents"].write(json.dumps({"doc_id": doc_id, "source_uri": src, "sha256": doc_id, "title": title,
                                             "author": author, "source_class": source_class, "text": text, "ingested_at": NOW,
                                             "occurred_at": occurred, "loader": LOADER, "flags": flags}, ensure_ascii=False) + "\n")
        ids, seen = [], {}
        for u in record["units"] if doc["kind"] != "error" else []:     # an unreadable file has no real slice to export
            uid = unit_id(doc_id, text, u["start"], u["end"], seen)
            ids.append(uid)
            assert text[u["start"]:u["end"]].strip(), (src, u)          # round trip: every unit is a real slice
            files["units"].write(json.dumps({"unit_id": uid, "doc_id": doc_id, "position": u["position"], "label": u["label"],
                                             "start": u["start"], "end": u["end"], "occurred_at": u["occurred_at"],
                                             "occurred_until": u["occurred_until"]}, ensure_ascii=False) + "\n")
            side = "chat" if doc["kind"] == "chat" else "read"
            receipt[f"over_cap_{side}"] += u["words"] > CAP_WORDS
            receipt[f"short_{side}"] += u["words"] < SHORT_WORDS
        for position, p in enumerate(record["pieces"] if doc["kind"] != "error" else []):
            files["pieces"].write(json.dumps({"doc_id": doc_id, "unit_id": ids[p["unit"]], "position": position,
                                              "kind": p["kind"], "start": p["start"], "end": p["end"],
                                              "author": p["author"], "occurred_at": p["occurred_at"]}, ensure_ascii=False) + "\n")
        st = record["stats"]
        for key in ("mismatch", "recovered", "unresolved", "duplicate", "meta_unresolved"):
            receipt[key] += st.get(key, 0)
        for p in record["pieces"]:
            receipt["chars_by_kind"][p["kind"]] = receipt["chars_by_kind"].get(p["kind"], 0) + (p["end"] - p["start"])
        receipt["documents"] += 1
        receipt["units"] += len(record["units"])
        receipt["pieces"] += len(record["pieces"])
        receipt["by_kind"][doc["kind"]] = receipt["by_kind"].get(doc["kind"], 0) + 1
        receipt["unknown_author"] += author is None and doc["kind"] != "chat"
        receipt["unknown_date"] += occurred is None and doc["kind"] != "chat"
        receipt["ambiguous_date"] += any(f.split(":")[0] in ("dates", "ambiguous date") for f in flags)
        receipt["total_chars"] += len(text)
        receipt["read_chars"] += len(text) if doc["kind"] != "chat" else 0
        for f in flags:
            kind = f.split(":")[0]
            receipt["flags_by_kind"][kind] = receipt["flags_by_kind"].get(kind, 0) + 1
        if flags:
            receipt["flagged"].append({"source_uri": src, "flags": flags})

for f in files.values():
    f.close()
receipt["body_share"] = round(receipt["chars_by_kind"].get("body", 0) / max(1, receipt["read_chars"]), 4)
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"documents {receipt['documents']}  units {receipt['units']}  pieces {receipt['pieces']}  by kind {receipt['by_kind']}")
print(f"pointers: mismatch {receipt['mismatch']}  recovered {receipt['recovered']}"
      f"  unresolved {receipt['unresolved']}  duplicate {receipt['duplicate']}  metadata nulled {receipt['meta_unresolved']}")
if receipt["duplicate_files"]:
    print(f"identical files exported once: {receipt['duplicate_files']}")
print(f"chars by kind: {receipt['chars_by_kind']}")
print(f"body {receipt['body_share']:.1%} of the {receipt['read_chars']:,} chars read from text and PDF;"
      f" chats add {receipt['total_chars'] - receipt['read_chars']:,}")
print(f"flagged {len(receipt['flagged'])} {receipt['flags_by_kind']}  unknown author {receipt['unknown_author']}  unknown date {receipt['unknown_date']}"
      f"  reused dates {receipt['ambiguous_date']}"
      f"  over-cap units {receipt['over_cap_read']} read + {receipt['over_cap_chat']} chat"
      f"  short units {receipt['short_read']} read + {receipt['short_chat']} chat"
      f"  model cost ${receipt['cost']:.2f}")
for entry in receipt["flagged"]:
    if "longmemeval/" not in entry["source_uri"]:
        print(f"    {entry['source_uri']}: {entry['flags']}")
