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
# Every stage is a function that returns something you can read: what the model said, what
# code kept, what it rejected and why. Blocks 1 to 3 are plumbing. Block 4 is the quote gate.
# Blocks 5 to 7 derive one unit. Block 8 folds a document. Block 9 writes the package. Block 10
# runs the corpus, resumable. Block 11 names the test variety and block 12 is the run. The
# script form (`# %%` cells) is the thing to edit; the notebook is generated from it.
#
# **On Kaggle:** attach the extractor's export as a dataset (a folder holding
# `documents.jsonl`, `units.jsonl`, `pieces.jsonl`; block 1 finds it anywhere under
# `/kaggle/input`), attach `OPENAI_API_KEY` under Add-ons > Secrets, turn Internet on under
# Settings, set `RUN` and `SPEND_STOP` in block 12, and Save & Run All so the packages under
# `/kaggle/working/packages` are kept as the version's output. To continue a run that stopped,
# attach that version's output as an input (Add Input > Your Work) before the next Save & Run
# All: finished packages are copied in and skipped, and only the unfinished documents are paid
# for. Every model call is logged to `calls.jsonl` as it is made; the stop is checked before
# each one.

# %%
# Block 1: inputs. The export lives under /kaggle/input on Kaggle or wherever EXPORT points
# locally; packages go under /kaggle/working or OUT. Records are read lazily by document, since
# documents.jsonl carries every byte of the corpus. A previous version's output attached as an
# input seeds OUT, so a run continues where the last one stopped.
import hashlib
import json
import os
import re
import shutil
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

INGESTOR = "factledger-ingestor 0.2"
if hasattr(sys.stdout, "reconfigure"):                       # a console that is not UTF-8 must not end the run
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def find_export():
    env = os.environ.get("EXPORT")
    if env:
        return Path(env)
    for root in (Path("/kaggle/input"), Path("data/export")):
        hits = sorted(root.rglob("units.jsonl")) if root.exists() else []
        if hits:
            return hits[0].parent
    raise SystemExit("no export found: set EXPORT to the folder holding documents.jsonl, units.jsonl, pieces.jsonl")


EXPORT = find_export()
OUT = Path(os.environ.get("OUT") or ("/kaggle/working/packages" if Path("/kaggle/working").exists() else "data/packages"))
OUT.mkdir(parents=True, exist_ok=True)


def seed_from_prior_output():
    """Every package (and every partial-document sidecar) under a 'packages' folder attached as
    an input is copied into OUT when OUT does not have it yet; the run logs of that session are
    not, since they belong to it. Returns how many files were copied."""
    root = Path("/kaggle/input")
    copied = 0
    if not root.exists():
        return copied
    for prior in root.rglob("packages"):
        if not prior.is_dir():
            continue
        for src in prior.rglob("*.jsonl"):
            if src.name in ("manifest.jsonl", "calls.jsonl", "rejections.jsonl"):
                continue
            dst = OUT / src.relative_to(prior)
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, dst)
                copied += 1
    return copied


SEEDED = seed_from_prior_output()


def read_jsonl(path):
    with path.open(encoding="utf-8") as f:
        for line in f:                          # never splitlines(): document text can hold U+2028
            if line.strip():
                yield json.loads(line)


def index_export():
    """source_uri -> doc_id, plus units and pieces grouped by doc_id, without holding any text."""
    units, pieces, by_uri = {}, {}, {}
    for u in read_jsonl(EXPORT / "units.jsonl"):
        units.setdefault(u["doc_id"], []).append(u)
    for p in read_jsonl(EXPORT / "pieces.jsonl"):
        pieces.setdefault(p["doc_id"], []).append(p)
    with (EXPORT / "documents.jsonl").open("rb") as f:          # bytes, so the offset seeks exactly on any line ending
        offset = 0
        for raw in f:
            head = raw[:400].decode("utf-8", errors="replace")
            m = re.search(r'"doc_id": "([0-9a-f]{64})", "source_uri": "([^"]*)"', head)
            if m:
                by_uri[m.group(2)] = (m.group(1), offset)
            offset += len(raw)
    for d in units.values():
        d.sort(key=lambda u: u["position"])
    for d in pieces.values():
        d.sort(key=lambda p: p["position"])
    return by_uri, units, pieces


def load_document(uri, by_uri, units, pieces):
    """The document with its text, its units in order and its pieces in order. One seek."""
    doc_id, offset = by_uri[uri]
    with (EXPORT / "documents.jsonl").open("rb") as f:
        f.seek(offset)
        doc = json.loads(f.readline().decode("utf-8"))
    assert doc["doc_id"] == doc_id
    doc["units"] = units.get(doc_id, [])
    doc["pieces"] = pieces.get(doc_id, [])
    text = doc["text"]
    for u in doc["units"]:                                  # round trip: every unit is a real slice
        assert 0 <= u["start"] < u["end"] <= len(text) and text[u["start"]:u["end"]].strip(), (uri, u["position"])
    return doc


BY_URI, UNITS, PIECES = index_export()
print(f"export {EXPORT}: {len(BY_URI)} documents, {sum(map(len, UNITS.values()))} units, {sum(map(len, PIECES.values()))} pieces;"
      f" packages to {OUT}" + (f", {SEEDED} files seeded from a previous run" if SEEDED else ""))

# %%
# Block 2: the two model interfaces, generate(prompt, schema) and embed(texts). Raw HTTP; the
# API rejects temperature, so reasoning_effort steers it. Every call is appended to CALLS and to
# calls.jsonl on disk the moment it returns, with model, tokens, latency and cost, so a killed
# session loses nothing. A reply that fails the schema is asked for once more with the error
# appended, then counted as a rejection. A timeout, connection error, truncated body, 429 or
# 5xx is retried three times; a 429 for exhausted quota ends the run like the spend stop; any
# other non-200 raises with the response body. The stop is checked before every call.
import http.client
import urllib.error
import urllib.request

LUNA, TERRA = "gpt-5.6-luna", "gpt-5.6-terra"
EMBED_MODEL = "text-embedding-3-small"
PRICE = {LUNA: (0.20, 1.20), TERRA: (2.00, 12.00), EMBED_MODEL: (0.02, 0.0)}   # $ per M tokens in, out
SPEND_STOP = float(os.environ.get("SPEND_STOP", "25"))
KEY = os.environ.get("OPENAI_API_KEY")
if not KEY and Path("/kaggle").exists():
    try:
        from kaggle_secrets import UserSecretsClient
        KEY = UserSecretsClient().get_secret("OPENAI_API_KEY")
    except Exception:
        KEY = None
CALLS = []                       # every call this session: stage, model, in, out, seconds, cost, doc, unit
REJECTIONS = []                  # every rejected reply this session: stage, category, doc, unit, detail


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
    """A small validator for the reply shapes below: type, required keys, item type, enum,
    nullable. Raises SchemaError naming the path, which goes back to the model on the retry."""
    types = {"object": dict, "array": list, "string": str, "number": (int, float), "integer": int, "boolean": bool, "null": type(None)}
    allowed = schema.get("type", "object")
    allowed = allowed if isinstance(allowed, list) else [allowed]
    if not any(isinstance(value, types[t]) and not (t in ("number", "integer") and isinstance(value, bool)) for t in allowed):
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


def post(url, payload, timeout=300):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8")


def logged(row):
    CALLS.append(row)
    record("calls.jsonl", row)


def call(url, payload, model, stage, ctx, prompt_chars):
    """One HTTP exchange with the retry policy; returns the parsed body. Cost is logged here."""
    if not KEY:
        raise RuntimeError("no OPENAI_API_KEY in the environment (or attached as a Kaggle secret)")
    if spend() >= SPEND_STOP:
        raise SpendStop(f"spending stop: ${spend():.2f} of ${SPEND_STOP:.2f}")
    p_in, p_out = PRICE[model]
    t0 = time.time()
    for attempt in range(3):
        try:
            status, text = post(url, payload)
        except urllib.error.HTTPError as e:
            status, text = e.code, e.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
            # the server may have finished and billed the request: count the input as spent
            logged({"stage": stage, "model": model, "in": prompt_chars // 4, "out": 0, "seconds": round(time.time() - t0, 1),
                    "cost": prompt_chars // 4 * p_in / 1e6, "timeout": True, **ctx})
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
    u = body.get("usage", {})
    n_in, n_out = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    logged({"stage": stage, "model": body.get("model", model), "in": n_in, "out": n_out,
            "seconds": round(time.time() - t0, 1), "cost": (n_in * p_in + n_out * p_out) / 1e6, **ctx})
    return body


def generate(prompt, schema, stage, model=LUNA, effort="low", ctx=None):
    """The reply as a dict that passes `schema`, or None after one retry with the error appended
    (the rejection is logged). Every prompt asks for JSON; the API's JSON mode guarantees a parse
    when there is content; a refusal has none and is treated as a bad shape."""
    ctx = ctx or {}
    for attempt in range(2):
        body = call("https://api.openai.com/v1/chat/completions",
                    {"model": model, "reasoning_effort": effort, "response_format": {"type": "json_object"},
                     "messages": [{"role": "user", "content": prompt}]}, model, stage, ctx, len(prompt))
        try:
            msg = body["choices"][0]["message"]
            if not msg.get("content"):
                raise SchemaError("empty reply" + (f" (refusal: {str(msg.get('refusal'))[:120]})" if msg.get("refusal") else ""))
            reply = json.loads(msg["content"])
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


def embed(texts, stage="embed", ctx=None):
    """One vector per text, from the embedding endpoint, in batches the endpoint accepts (at
    most 256 texts and about 200,000 tokens a request), each request logged like any call."""
    out = []
    batch, size = [], 0
    for t in list(texts) + [None]:
        if t is None or (batch and (len(batch) >= 256 or size + len(t) // 4 > 200_000)):
            if batch:
                body = call("https://api.openai.com/v1/embeddings", {"model": EMBED_MODEL, "input": batch},
                            EMBED_MODEL, stage, ctx or {}, sum(len(x) for x in batch))
                out += [d["embedding"] for d in sorted(body["data"], key=lambda d: d["index"])]
            batch, size = [], 0
        if t is not None:
            batch.append(t)
            size += len(t) // 4
    return out


print(f"models {LUNA} (derive), {TERRA} (judge), {EMBED_MODEL}; key {'present' if KEY else 'MISSING'}")

# %%
# Block 3: ids and text helpers. Every id is a content hash, so re-deriving unchanged input
# mints the same ids and a corrected unit changes one id and not every id after it.


def h(*parts):
    return hashlib.sha256("\n".join(str(p) for p in parts).encode("utf-8")).hexdigest()


def norm(s):
    return " ".join(str(s or "").split()).casefold()


def word_count(s):
    return len(s.split())


def names_in(text):
    """Capitalised runs in a summary or abstract: the names it emits, for the fabrication check.
    A one-word run that opens a sentence counts as a name only when the same word also appears
    capitalised inside a sentence, so 'The' and 'Then' are not names and a name that only ever
    opens a sentence is missed rather than invented."""
    runs = [(m.start(), m.group(1)) for m in re.finditer(r"(?<![\w'’])([A-Z][\w'’\-]*(?:\s+[A-Z][\w'’\-]*)*)", text)]
    opens = {m.start(1) for m in re.finditer(r"(?:^|[.!?]\s+)([A-Z])", text)}
    names, heads = set(), []
    for at, r in runs:
        if at in opens:                       # the first word opens a sentence; what follows it is inside one
            head, _, rest = r.partition(" ")
            heads.append(head)
            if rest:
                names.add(rest)
        else:
            names.add(r)
    inside = {w for n in names for w in n.split()}
    names |= {hd for hd in heads if hd in inside}
    return sorted(names)


def missing_names(text, children):
    """Names emitted by a fold that appear in none of its children, case-insensitively."""
    pool = " ".join(children).casefold()
    return [n for n in names_in(text) if n.casefold() not in pool]


def whole_word(needle, haystack):
    """The needle's words in order, as whole words, anywhere in the haystack."""
    pattern = r"(?<!\w)" + r"\s+".join(re.escape(w) for w in needle.split()) + r"(?!\w)"
    return re.search(pattern, haystack) is not None

# %%
# Block 4: the quote gate. locate(unit_text, quote) returns (start, end) inside the unit, or a
# rejection category. Three ways to match, tried in order and each named, so the receipt says
# how many quotes needed which: exact substring; the same words across any whitespace; the same
# characters after NFKC, straight quotes, one dash, a hyphenated line break closed up, and case
# folding, matched on a normalised copy of the unit whose every character maps back to an
# offset in the original. The stored offsets always index the original text. A quote that
# matches none is classified: paraphrase when most of its words are there in order, else not
# found. Nothing here reaches the store.

QUOTES = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "‒": "-", "−": "-", "‐": "-", "‑": "-",
          "­": "", " ": " "}
HYPHEN_BREAK = re.compile(r"[^\W\d_]-\r?\n(?=[^\W\d_])")   # 'recon-\nciliation': a word wrapped at a hyphen


def normalised(text):
    """(normalised string, map from each normalised index to an original index). NFKC can expand
    one character to several (a ligature to two letters), so the map is built per character; a
    soft hyphen and a hyphenated line break inside a word emit nothing."""
    skip = set()
    for m in HYPHEN_BREAK.finditer(text):
        skip.update(range(m.start() + 1, m.end()))
    out, back = [], []
    for i, ch in enumerate(text):
        if i in skip:
            continue
        for c in unicodedata.normalize("NFKC", QUOTES.get(ch, ch)).casefold():
            out.append(c)
            back.append(i)
    return "".join(out), back


def normalised_of(text, cache):
    if cache is None:
        return normalised(text)
    if "norm" not in cache:
        cache["norm"] = normalised(text)
    return cache["norm"]


def locate(text, quote, cache=None):
    """(start, end, how) with offsets into `text`, or (None, None, category)."""
    q = (quote or "").strip()
    if not q:
        return None, None, "empty"
    i = text.find(q)
    if i >= 0:
        return i, i + len(q), "exact"
    words = q.split()
    m = re.search(r"\s+".join(re.escape(w) for w in words), text)
    if m:
        return m.start(), m.end(), "whitespace"
    ntext, back = normalised_of(text, cache)
    nq, _ = normalised(q)
    nwords = nq.split()
    m = re.search(r"\s+".join(re.escape(w) for w in nwords), ntext)
    if m:
        return back[m.start()], back[m.end() - 1] + 1, "normalised"
    # classification of the miss: how much of the quote is there, in order, punctuation aside
    bare = re.findall(r"\w+", nq)
    j = 0
    for w in re.findall(r"\w+", ntext):
        if j < len(bare) and w == bare[j]:
            j += 1
    share = j / max(1, len(bare))
    return None, None, "paraphrase" if share >= 0.7 else "not_found"


def occurrences(text, found):
    """Every start offset at which the located string recurs verbatim, the first one included."""
    return [m.start() for m in re.finditer(re.escape(found), text)] if found else []


def surface_spans(text, surface, cache=None):
    """Every occurrence of a surface form in the unit, as (start, end) pairs, whole words only."""
    s = (surface or "").strip()
    if not s:
        return []
    pattern = r"(?<!\w)" + r"\s+".join(re.escape(w) for w in s.split()) + r"(?!\w)"
    hits = [(m.start(), m.end()) for m in re.finditer(pattern, text)]
    if hits:
        return hits
    ntext, back = normalised_of(text, cache)
    ns, _ = normalised(s)
    pattern = r"(?<!\w)" + r"\s+".join(re.escape(w) for w in ns.split()) + r"(?!\w)"
    return [(back[m.start()], back[m.end() - 1] + 1) for m in re.finditer(pattern, ntext)]

# %%
# Block 5: the prompts. Three per unit (entities with their surface forms and profile, facts
# with quotes, summary and cells), one judge, one fold. None of them knows what kind of
# document it is reading. The roster is what the document has established so far: entities
# that earned a place (a fact or a second mention) and the predicates already in use, both
# offered as suggestions the model may continue or ignore, the most recently seen first.

ENTITY_SCHEMA = {"type": "object", "required": ["entities"], "properties": {"entities": {"type": "array", "items": {
    "type": "object", "required": ["name", "named", "kind", "surface_forms"], "properties": {
        "name": {"type": "string"}, "named": {"type": "boolean"}, "kind": {"type": "string"},
        "surface_forms": {"type": "array", "items": {"type": "string"}},
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

ROSTER_SHOWN = 60


def roster_text(roster):
    if not roster["entities"]:
        return ""
    lines = [f"- {e['name']} ({e['kind']}; forms: {', '.join(e['forms'][:5])}" + (f"; is: {', '.join(e['is_a'][:3])}" if e["is_a"] else "") + ")"
             for e in roster["entities"][:ROSTER_SHOWN]]
    return "\n\nESTABLISHED SO FAR IN THIS DOCUMENT (continue one of these when the text means the same thing; name a new one when it does not):\n" + "\n".join(lines)


def entity_prompt(unit, roster):
    return f"""TEXT ({unit['label']}):
{unit['text']}

Above is one unit of a longer document. Identify the entities it involves: each person, group, place, thing, event, or topic that acts, is acted upon, or is discussed in its own right, plus any named person, place, group, or thing, however briefly mentioned. Parts, components, and possessions of a listed entity are not entities; they belong inside that entity's facts.

Return JSON {{"entities": [{{"name", "named", "kind", "surface_forms", "continues", "profile"}}]}} where:
- name: for a named entity, the fullest name the text uses; for an unnamed one, a head word plus a parenthetical anchoring it to a named entity, like "car (Sam's car)"
- named: true if the text gives it a proper name
- kind: one lowercase word: person, group, place, object, event, topic, or another if none fits
- surface_forms: every distinct verbatim string the text uses to refer to it, copied exactly, bare pronouns excluded; a string that refers to two different entities in this text is listed under only one of them
- continues: the name of the established entity this one is, exactly as listed below, or null if it is new to the document
- profile: attributes you infer from context rather than read in the text, as {{"gender", "age_band", "animacy", "role"}} with a value or null each; null when nothing can be inferred{roster_text(roster)}"""


def fact_prompt(unit, names, predicates):
    used = ("\n\nPREDICATES THIS DOCUMENT HAS USED (reuse one when it means the same relation; coin a new one when none does): "
            + ", ".join(predicates[:80])) if predicates else ""
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
- state each relationship once, from the side of the entity the text is about

ENTITIES: {", ".join(names)}{used}"""


def cells_prompt(unit, names, previous):
    context = f"\n\nTHE PREVIOUS UNIT, SUMMARISED (for resolving references only; do not restate it):\n{previous}" if previous else ""
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
# Block 6: derive one unit. Three calls, every gate applied by code, one record back with
# everything the model said and everything code kept or rejected, so a unit can be diagnosed
# on its own. Offsets are document offsets: the unit's start is added to every span. A span is
# one mention: when two entities claim the same occurrence, the first listed keeps it.


def derive_unit(doc, unit, roster, previous_summary, ctx):
    text = unit["text"]
    base = unit["start"]
    cache = {}
    rec = {"unit_id": unit["unit_id"], "position": unit["position"], "label": unit["label"],
           "entities": [], "dropped_entities": [], "mentions": [], "facts": [], "rejected_facts": [],
           "profile": [], "summary": None, "cells": [], "dropped_cells": [], "agreement": None,
           "shared_spans": 0, "ambiguous_voice": 0, "empty": False}

    # 1. entities, with every surface form located; a form not in the unit is dropped
    reply = generate(entity_prompt(unit, roster), ENTITY_SCHEMA, "entities", ctx=ctx)
    roster_names = {e["name"] for e in roster["entities"]}
    seen_names = set()
    claimed = {}                                             # (start, end) -> the entity that got the span
    for e in (reply or {}).get("entities", []):
        name = " ".join(e["name"].split())
        if not name or name in seen_names:
            continue
        forms, spans, found = [], [], False
        for s in dict.fromkeys([f for f in e["surface_forms"] if isinstance(f, str)] + [name]):
            all_hits = surface_spans(text, s, cache)
            found = found or bool(all_hits)
            hits = [ab for ab in all_hits if ab not in claimed and ab not in spans]
            rec["shared_spans"] += sum(1 for ab in all_hits if ab in claimed)
            if hits:
                forms.append(s)
                spans.extend(hits)
        if not spans:
            why = "every span already claimed by an earlier entity" if found else "no surface form in unit"
            rec["dropped_entities"].append({"name": name, "why": why, "forms": e["surface_forms"][:5]})
            continue
        seen_names.add(name)
        for ab in spans:
            claimed[ab] = name
        continues = e.get("continues") if e.get("continues") in roster_names else None
        prof = e.get("profile") if isinstance(e.get("profile"), dict) else {}
        rec["entities"].append({"name": name, "named": bool(e["named"]), "kind": str(e["kind"]).lower(),
                                "forms": forms, "continues": continues, "mentions": len(spans)})
        for a, b in sorted(spans):
            rec["mentions"].append({"mention_id": h(unit["unit_id"], base + a, base + b), "entity": name,
                                    "unit_id": unit["unit_id"], "start": base + a, "end": base + b,
                                    "surface": text[a:b], "resolved_by": "surface"})
        for attr, val in prof.items():
            if val not in (None, "", "null", "unknown"):
                rec["profile"].append({"entity": name, "attribute": str(attr), "value": str(val), "confidence": 0.5, "from_unit": unit["unit_id"]})
    names = [e["name"] for e in rec["entities"]]
    if not names:
        rec["empty"] = True
        return rec

    # 2. facts, each quote located inside the unit, offsets stored as document offsets
    reply = generate(fact_prompt(unit, names, roster["predicates"]), FACT_SCHEMA, "facts", ctx=ctx)
    name_set = set(names)
    seen_facts = set()
    for f in (reply or {}).get("facts", []):
        subject, predicate, obj = f["subject"].strip(), f["predicate"].strip(), str(f["object"]).strip()
        predicate = re.sub(r"[^a-z0-9_]+", "_", predicate.lower()).strip("_") or "related_to"
        start, end, how = locate(text, f["quote"], cache)
        if subject not in name_set:
            rec["rejected_facts"].append({"category": "unlisted_subject", "subject": subject, "predicate": predicate, "object": obj, "quote": f["quote"][:160]})
            continue
        if start is None:
            rec["rejected_facts"].append({"category": how, "subject": subject, "predicate": predicate, "object": obj, "quote": f["quote"][:160]})
            continue
        key = (subject, predicate, norm(obj))
        if key in seen_facts:
            rec["rejected_facts"].append({"category": "duplicate", "subject": subject, "predicate": predicate, "object": obj, "quote": f["quote"][:160]})
            continue
        seen_facts.add(key)
        quote = text[start:end]
        voices = {author_at(doc, base + at) for at in occurrences(text, quote)}
        ambiguous = len(voices) > 1                          # the same words in two voices: no voice is claimed
        author = None if ambiguous else next(iter(voices), author_at(doc, base + start))
        rec["ambiguous_voice"] += ambiguous
        valid_from, valid_to = stated_date(f.get("valid_from"), quote), stated_date(f.get("valid_to"), quote)
        rec["facts"].append({"fact_id": h(unit["unit_id"], subject, predicate, obj, base + start, base + end),
                             "subject": subject, "predicate": predicate, "object": obj,
                             "object_is_entity": obj in name_set, "qualifiers": f.get("qualifiers") or None,
                             "unit_id": unit["unit_id"], "quote": quote, "quote_start": base + start, "quote_end": base + end,
                             "matched_by": how, "valid_from": valid_from, "valid_to": valid_to,
                             "author": author, "voice_ambiguous": ambiguous, "tier": LUNA})

    # 3. summary and cells, one call, for the entities with a fact in this unit
    with_fact = [n for n in names if any(f["subject"] == n or (f["object_is_entity"] and f["object"] == n) for f in rec["facts"])]
    reply = generate(cells_prompt(unit, with_fact or names[:1], previous_summary), CELLS_SCHEMA, "cells", ctx=ctx)
    if reply:
        rec["summary"] = " ".join(reply["summary"].split())
        wanted = set(with_fact)
        for c in reply["cells"]:
            if c["entity"] in wanted and c["text"].strip():
                rec["cells"].append({"entity": c["entity"], "text": " ".join(c["text"].split())})
            else:
                rec["dropped_cells"].append({"entity": c["entity"], "why": "not an above-threshold entity"})
        # the agreement check: which above-threshold entities the summary names, and vice versa
        s = rec["summary"].casefold()
        named_in_summary = [n for n in with_fact if any(whole_word(fm.casefold(), s) for fm in next(e["forms"] for e in rec["entities"] if e["name"] == n))]
        celled = {c["entity"] for c in rec["cells"]}
        rec["agreement"] = {"above_threshold": len(with_fact), "cells": len(celled), "named_in_summary": len(named_in_summary),
                            "in_summary_without_cell": sorted(set(named_in_summary) - celled),
                            "cell_without_summary_name": sorted(celled - set(named_in_summary))}
    rec["empty"] = not rec["facts"] and not rec["cells"]
    return rec


def stated_date(value, quote):
    """An ISO date the model claims the quote states: kept only when its year is in the quote."""
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", value.strip()):
        return None
    value = value.strip()
    return value if value[:4] in quote else None


def author_at(doc, offset):
    """The voice of an offset: the author of the piece holding it, else the document's, else None."""
    for p in doc["pieces"]:
        if p["start"] <= offset < p["end"]:
            return p["author"] or doc.get("author")
    return doc.get("author")


def advance_roster(roster, rec):
    """Entities that earned a place (a fact, or two mentions) and every predicate used, carried
    to the next unit as suggestions, the most recently seen first so the previous unit's new
    entities are always in the window."""
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
        for s in e["forms"] + ([e["name"]] if e["name"] != key else []):
            if s not in entry["forms"]:
                entry["forms"].append(s)
        for f in facts_of.get(e["name"], []):
            if f["predicate"] == "is_a" and f["object"] not in entry["is_a"]:
                entry["is_a"].append(f["object"])
    roster["entities"].sort(key=lambda e: (-e["last_unit"], -e["units"]))
    roster["predicates"] = sorted(roster["predicate_counts"], key=lambda p: -roster["predicate_counts"][p])

# %%
# Block 7: reconcile the document's unit-local entities into document entities. Every local
# starts alone. A declared continuation of a named entity, or two units using the same proper
# name, unites without a judge; every other candidate pair is scored on name, co-occurrence and
# profile, each logged separately; the ambiguous band goes to the judge, ten pairs a call, every
# cluster's dossier sent once. Every decision is a ledger row with its evidence, so a merge can
# be measured and revoked. An unnamed role ("the boy") is never united on its name alone.
import difflib

HIGH, LOW = 0.85, 0.35        # combined score: at or above HIGH unite, below LOW stay apart, between: judge
PARENTHETICAL = re.compile(r"^(.+?)\s*\((.*)\)\s*$")


def name_score(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def words_of(n):
    return {w for w in re.findall(r"[a-z]+", n.casefold()) if len(w) > 3}


def anchored(x, y):
    """x is an unnamed thing anchored to y by its parenthetical ("car (Sam's car)" and "Sam"):
    the anchor's name is inside the parenthetical and nothing else is shared, so the two are
    not candidates for being the same thing."""
    m = PARENTHETICAL.match(x["name"])
    if not m or not y["named"]:
        return False
    head, inner = m.group(1), m.group(2).casefold()
    return norm(y["name"]) in inner and not (words_of(head) & words_of(y["name"])) and not (x["surfaces"] & y["surfaces"])


def reconcile(doc, records, ctx):
    locals_ = []
    for rec in records:
        facts_of = {}
        for f in rec["facts"]:
            facts_of.setdefault(f["subject"], []).append(f)
        profile_of = {}
        for p in rec["profile"]:
            profile_of.setdefault(p["entity"], {})[p["attribute"]] = p["value"].casefold()
        cooc = {e["name"] for e in rec["entities"]}
        for e in rec["entities"]:
            fs = facts_of.get(e["name"], [])
            locals_.append({"id": len(locals_), "ui": rec["position"], "unit_id": rec["unit_id"], "name": e["name"],
                            "kind": e["kind"], "named": e["named"], "continues": e["continues"],
                            "forms": list(dict.fromkeys(e["forms"] + [e["name"]])),
                            "surfaces": {s.casefold() for s in e["forms"]} | {e["name"].casefold()},
                            "is_a": [f["object"] for f in fs if f["predicate"] == "is_a"],
                            "facts": [f"{f['predicate']} {f['object']}" + (f" [{f['qualifiers']}]" if f["qualifiers"] else "") for f in fs],
                            "relations": [f"{f['predicate']} {f['object']}" for f in fs if f["object_is_entity"]],
                            "profile": profile_of.get(e["name"], {}), "cooc": cooc - {e["name"]}, "n_facts": len(fs)})
    parent = list(range(len(locals_)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    ledger, candidates = [], []

    def row(a, b, verdict, how, evidence):
        ledger.append({"a": locals_[a]["name"], "a_unit": locals_[a]["ui"], "b": locals_[b]["name"], "b_unit": locals_[b]["ui"],
                       "verdict": verdict, "how": how, "evidence": evidence})

    def unite(a, b, how, evidence):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
        row(a, b, "same", how, evidence)

    # 1. declared continuations of a named entity, and the same proper name in two units
    by_name = {}
    for l in locals_:
        by_name.setdefault(norm(l["name"]), []).append(l)
    for l in locals_:
        if l["continues"]:
            earlier = [t for t in by_name.get(norm(l["continues"]), []) if t["ui"] < l["ui"]]
            named = [t for t in earlier if t["named"]]
            if named:
                unite(named[-1]["id"], l["id"], "declared", f"unit {l['ui']} continued {l['continues']!r}")
            elif earlier:
                row(earlier[-1]["id"], l["id"], "candidate", "declared", f"unit {l['ui']} continued the unnamed {l['continues']!r}; scored instead")
    for group in by_name.values():
        for a, b in zip(group, group[1:]):
            if a["named"] and b["named"] and find(a["id"]) != find(b["id"]):
                unite(a["id"], b["id"], "same_name", f"{a['name']!r} in units {a['ui']} and {b['ui']}")

    # 2. candidates across units: a shared surface form, a declared continuation of an unnamed
    #    entity, an is_a link, or a shared name word; never a possession against its own anchor
    pairs = {}
    for a in locals_:
        for b in locals_:
            if a["id"] >= b["id"] or a["ui"] == b["ui"] or find(a["id"]) == find(b["id"]):
                continue
            declared = norm(a["continues"] or "") == norm(b["name"]) or norm(b["continues"] or "") == norm(a["name"])
            if not (declared or a["surfaces"] & b["surfaces"] or words_of(a["name"]) & words_of(b["name"])
                    or any(x.casefold() in b["surfaces"] for x in a["is_a"]) or any(x.casefold() in a["surfaces"] for x in b["is_a"])):
                continue
            if anchored(a, b) or anchored(b, a):
                continue
            ns = max(name_score(a["name"], b["name"]), 1.0 if (a["surfaces"] & b["surfaces"] or declared) else 0.0)
            ca, cb = a["cooc"], b["cooc"]
            cs = len(ca & cb) / len(ca | cb) if (ca | cb) else 0.0
            keys = set(a["profile"]) & set(b["profile"])
            ps = (sum(a["profile"][k] == b["profile"][k] for k in keys) / len(keys)) if keys else 0.5
            combined = 0.6 * ns + 0.25 * cs + 0.15 * ps
            pairs[(a["id"], b["id"])] = (ns, cs, ps, combined)
    to_judge = []
    for (i, j), (ns, cs, ps, combined) in sorted(pairs.items(), key=lambda kv: -kv[1][3]):
        decision = "unite" if combined >= HIGH else "apart" if combined < LOW else "judge"
        candidates.append({"a": locals_[i]["name"], "a_unit": locals_[i]["ui"], "b": locals_[j]["name"], "b_unit": locals_[j]["ui"],
                           "name_score": round(ns, 3), "cooc_score": round(cs, 3), "profile_score": round(ps, 3),
                           "combined": round(combined, 3), "threshold": [LOW, HIGH], "decision": decision})
        if decision == "unite":
            unite(i, j, "scored", f"combined {combined:.2f}")
        elif decision == "judge":
            to_judge.append((i, j))

    # 3. the judge, on the ambiguous band, strongest first, dossiers sent once per call
    def members(root):
        return [l for l in locals_ if find(l["id"]) == root]

    def dossier(root):
        ks = members(root)
        take = lambda key, n: sorted({x for l in ks for x in l[key]})[:n]
        return "\n".join([f"names: {', '.join(sorted({l['name'] for l in ks}))}",
                          f"forms: {', '.join(sorted({s for l in ks for s in l['surfaces']})[:12])}",
                          f"kinds: {', '.join(sorted({l['kind'] for l in ks}))}",
                          f"is: {', '.join(take('is_a', 6)) or '(nothing stated)'}",
                          f"facts: {'; '.join(take('facts', 10)) or '(none)'}",
                          f"relations: {'; '.join(take('relations', 10)) or '(none)'}",
                          f"units: {', '.join(str(u) for u in sorted({l['ui'] for l in ks}))}"])

    kept_apart = []                                   # (local, local) pairs the judge ruled different, read through find()

    def ruled_apart(ra, rb):
        return any({find(x), find(y)} == {ra, rb} for x, y in kept_apart)

    k = 0
    while k < len(to_judge):
        batch, keys = [], set()
        while k < len(to_judge) and len(batch) < 10:
            ra, rb = find(to_judge[k][0]), find(to_judge[k][1])
            k += 1
            key = frozenset((ra, rb))
            if ra != rb and key not in keys and not ruled_apart(ra, rb):
                batch.append((ra, rb))
                keys.add(key)
        if not batch:
            continue
        roots = sorted({r for pair in batch for r in pair})
        number = {r: n for n, r in enumerate(roots, 1)}
        prompt = JUDGE_PROMPT + "\nDOSSIERS\n" + "\n\n".join(f"[{number[r]}]\n{dossier(r)}" for r in roots) \
            + "\n\nPAIRS\n" + "\n".join(f"PAIR {n}: [{number[a]}] and [{number[b]}]" for n, (a, b) in enumerate(batch, 1))
        reply = generate(prompt, JUDGE_SCHEMA, "judge", model=TERRA, effort="medium", ctx=ctx)
        verdicts = {}
        for v in (reply or {}).get("verdicts", []):
            try:
                verdicts[int(v["pair"]) - 1] = (v["verdict"], v.get("reason", ""))
            except (TypeError, ValueError):
                pass
        for n, (ra, rb) in enumerate(batch):
            verdict, reason = verdicts.get(n, ("unsure", "no verdict returned"))
            if verdict == "same":
                unite(ra, rb, "judged", reason)
            else:
                kept_apart.append((ra, rb))
                row(ra, rb, verdict, "judged", reason)

    # 4. the document entities
    clusters = {}
    for l in locals_:
        clusters.setdefault(find(l["id"]), []).append(l)
    entities = []
    for ks in clusters.values():
        ks.sort(key=lambda l: l["ui"])
        named = [l for l in ks if l["named"]] or ks
        counts = {}
        for l in named:
            counts[l["name"]] = counts.get(l["name"], 0) + 1
        name = max(counts, key=lambda n: (counts[n], len(n)))
        first_unit_of, unit_ids = {}, []
        for l in ks:
            for f in l["forms"]:
                first_unit_of.setdefault(f, l["unit_id"])
            if l["unit_id"] not in unit_ids:
                unit_ids.append(l["unit_id"])
        entities.append({"name": name, "kinds": sorted({l["kind"] for l in ks}), "named": any(l["named"] for l in ks),
                         "units": sorted({l["ui"] for l in ks}), "unit_ids": unit_ids,
                         "names": sorted({l["name"] for l in ks}), "surfaces": sorted({s for l in ks for s in l["surfaces"]}),
                         "first_unit_of": first_unit_of,
                         "members": [(l["ui"], l["name"]) for l in ks], "n_facts": sum(l["n_facts"] for l in ks),
                         "is_a": sorted({x for l in ks for x in l["is_a"]}), "profile": [l["profile"] for l in ks if l["profile"]]})
    return entities, ledger, candidates, len(locals_), len(pairs), len(to_judge)

# %%
# Block 8: fold the document. The abstract folds from the unit summaries under BUILD's bound
# (at most half the child words, capped at 400) with the fabrication check; a rejected fold is
# asked for once more with the missing names listed, then left unstamped. Salience is
# reassessed against the abstract: named there, as whole words, is major, unit count then fact
# count break ties; with no abstract the tie-breakers decide alone, and the node says so. Majors
# get a dossier with an embedding and their own abstract with children_hash.


def fold(what, children, ctx, stage="fold", model=LUNA, allowed=None):
    """(text, missing names, limit) — text is None when the fold was rejected twice. `allowed`
    are names the prompt itself supplies (the entity being summarised), which count as present."""
    child_words = sum(word_count(c) for c in children)
    limit = min(400, max(1, child_words // 2))
    prompt = fold_prompt(what, children, max(10, limit * 9 // 10))     # asked for a little under the bound code enforces
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
            prompt += ("\n\nYour previous summary " + (f"used names that do not appear in the records ({', '.join(missing[:8])})" if missing else "")
                       + (" and " if missing and over else "") + (f"ran to {word_count(text)} words against a limit of {limit}" if over else "")
                       + ". Write it again using only names from the records, within the limit.")
    return None, missing or ["(over length)"], limit


def children_hash(children):
    return h(*children)


def fold_document(doc, records, entities, ctx):
    out = {"abstract": None, "abstract_rejected": None, "majors": [], "minors": [], "dossiers": [], "entity_abstracts": [], "entity_abstract_rejected": []}
    summaries = [f"[{r['label']}] {r['summary']}" for r in records if r["summary"]]
    if len(summaries) == 1:                                   # one summarised unit: its summary is the abstract, no call
        text, missing, limit = next(r["summary"] for r in records if r["summary"]), [], None
    elif summaries:
        text, missing, limit = fold("one document", summaries, ctx)
    else:
        text, missing, limit = None, ["(no unit summaries)"], None
    if text:
        out["abstract"] = {"text": text, "children_hash": children_hash(summaries), "limit": limit}
    else:
        out["abstract_rejected"] = missing

    # salience against the abstract; without one, the tie-breakers decide and the node says so
    a = (text or "").casefold()
    ranked = []
    for e in entities:
        in_abstract = any(whole_word(s, a) for s in e["surfaces"] if len(s) > 2) if text else None
        major = in_abstract if text else (len(e["units"]) >= 2 or e["n_facts"] >= 2)
        ranked.append((major, len(e["units"]), e["n_facts"], in_abstract, e))
    ranked.sort(key=lambda t: (not t[0], -t[1], -t[2]))
    for major, nu, nf, in_abstract, e in ranked:
        e["major"] = major
        e["rank"] = {"in_abstract": in_abstract, "units": nu, "facts": nf}
        (out["majors"] if major else out["minors"]).append(e)

    # dossiers and per-entity abstracts for the majors
    cells_of, facts_of = {}, {}
    member_names = {(ui, n): e["name"] for e in entities for ui, n in e["members"]}
    for r in records:
        for c in r["cells"]:
            key = member_names.get((r["position"], c["entity"]))
            if key:
                cells_of.setdefault(key, []).append(f"[{r['label']}] {c['text']}")
        for f in r["facts"]:
            key = member_names.get((r["position"], f["subject"]))
            if key:
                facts_of.setdefault(key, []).append(f"{f['predicate']} {f['object']}" + (f" [{f['qualifiers']}]" if f["qualifiers"] else ""))
    texts = []
    for e in out["majors"]:
        children = list(dict.fromkeys(facts_of.get(e["name"], []))) + cells_of.get(e["name"], [])
        d = "\n".join([f"name: {e['name']}", f"also: {', '.join(n for n in e['names'] if n != e['name'])[:300]}",
                       f"kinds: {', '.join(e['kinds'])}", f"is: {', '.join(e['is_a'][:6])}",
                       f"facts: {'; '.join(list(dict.fromkeys(facts_of.get(e['name'], [])))[:20])}",
                       f"cells: {' '.join(cells_of.get(e['name'], []))[:1500]}"])
        out["dossiers"].append({"entity": e["name"], "text": d, "children": children})
        texts.append(d)
    if texts and KEY:
        for dossier, vec in zip(out["dossiers"], embed(texts, ctx=ctx)):
            dossier["embedding"] = vec
    for e, dossier in zip(out["majors"], out["dossiers"]):
        children = dossier["children"]
        if not children:
            continue
        if len(children) <= 2:                                    # too little to fold: the children stand as the abstract
            atext, missing = " ".join(c.split("] ", 1)[-1] for c in children), []
        else:
            atext, missing, _ = fold(f"one entity, {e['name']}", children, ctx, stage="entity_abstract", allowed=e["names"] + e["surfaces"])
        if atext:
            out["entity_abstracts"].append({"entity": e["name"], "text": atext, "children_hash": children_hash(children)})
        else:
            out["entity_abstract_rejected"].append({"entity": e["name"], "missing": missing})
    return out

# %%
# Block 9: the package. One JSONL file per document, mirroring the raw layout
# (raw/oz/01_55.txt -> packages/oz/01_55.jsonl), every line one record with a "record" field
# naming its type, written in the order the merge applies them, ending in a completion record
# whose input_hash says which extractor output it was derived from. Ids are content hashes;
# minors have no node and their mentions carry node_id null. A fact from a major to a minor is
# a property with the minor's name as its value; a fact between two minors is not stored. Two
# locals of one unit that reconcile into one node yield one cell for that unit.


def package_path(doc):
    parts = doc["source_uri"].split("/")
    group = parts[-2] if len(parts) > 1 else "misc"
    group = "papers" if group.startswith("it494-reference-papers") or doc["source_uri"].endswith(".pdf") else group
    return OUT / group / (Path(parts[-1]).stem + ".jsonl")


def sidecar_path(doc):
    """Unit records checkpointed while a document is in flight, so a stop mid-document costs
    only the unit that was running."""
    return package_path(doc).with_suffix(".units.jsonl")


def input_hash(doc):
    return h(doc["doc_id"], *[u["unit_id"] for u in doc["units"]], INGESTOR)


def write_package(doc, records, entities, folded, ledger, candidates, stats):
    path = package_path(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    scope = doc["doc_id"]
    node_of = {}                                                     # (unit position, local name) -> node_id or None
    lines = [{"record": "package", "doc_id": doc["doc_id"], "source_uri": doc["source_uri"], "ingestor": INGESTOR,
              "loader": doc.get("loader"), "input_hash": input_hash(doc), "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
             {"record": "document", **{k: doc[k] for k in ("doc_id", "source_uri", "sha256", "title", "author", "source_class",
                                                          "ingested_at", "occurred_at", "loader")}, "flags": doc.get("flags", []),
              "text_length": len(doc["text"])}]
    lines += [{"record": "unit", **u} for u in doc["units"]]
    lines += [{"record": "piece", **p} for p in doc["pieces"]]
    doc_node = h(doc["doc_id"], "document")
    lines.append({"record": "node", "node_id": doc_node, "name": doc.get("title") or doc["source_uri"], "kind": "document",
                  "created_from_unit": doc["units"][0]["unit_id"] if doc["units"] else None, "provenance": {"ingestor": INGESTOR}})
    position_of = {u["unit_id"]: u["position"] for u in doc["units"]}
    for e in entities:
        nid = h(doc["doc_id"], e["name"]) if e["major"] else None
        for ui, n in e["members"]:
            node_of[(ui, n)] = nid
        if e["major"]:
            first = min(e["unit_ids"], key=lambda uid: position_of[uid])
            lines.append({"record": "node", "node_id": nid, "name": e["name"], "kind": e["kinds"][0] if len(e["kinds"]) == 1 else "/".join(e["kinds"]),
                          "created_from_unit": first,
                          "provenance": {"ingestor": INGESTOR, "salience": e["rank"], "names": e["names"][:12]}})
            for s, uid in e["first_unit_of"].items():
                lines.append({"record": "alias", "alias": s, "node_id": nid, "first_seen_unit": uid, "evidence_quote": None})
            lines.append({"record": "edge", "predicate": "appears_in", "subject": nid, "object": doc_node, "units": e["unit_ids"]})
    for u in doc["units"]:
        lines.append({"record": "edge", "predicate": "has_unit", "subject": doc_node, "object": u["unit_id"], "position": u["position"]})
    dropped_minor = 0
    for r in records:
        for m in r["mentions"]:
            lines.append({"record": "mention", "mention_id": m["mention_id"], "node_id": node_of.get((r["position"], m["entity"])),
                          "unit_id": m["unit_id"], "start": m["start"], "end": m["end"], "surface": m["surface"], "resolved_by": m["resolved_by"]})
        seen_profile = set()
        for p in r["profile"]:
            nid = node_of.get((r["position"], p["entity"]))
            key = (nid, p["attribute"], p["value"])
            if nid and key not in seen_profile:
                seen_profile.add(key)
                lines.append({"record": "profile", "node_id": nid, "attribute": p["attribute"], "value": p["value"],
                              "confidence": p["confidence"], "from_unit": p["from_unit"]})
        for f in r["facts"]:
            s_node = node_of.get((r["position"], f["subject"]))
            o_node = node_of.get((r["position"], f["object"])) if f["object_is_entity"] else None
            if s_node is None:
                dropped_minor += 1
                continue
            lines.append({"record": "fact", "fact_id": f["fact_id"], "subject": s_node, "predicate": f["predicate"],
                          "object": o_node or f["object"], "object_is_node": o_node is not None, "qualifiers": f["qualifiers"],
                          "rank": "active", "unit_id": f["unit_id"], "quote": f["quote"], "quote_start": f["quote_start"],
                          "quote_end": f["quote_end"], "valid_from": f["valid_from"], "valid_to": f["valid_to"], "tier": f["tier"],
                          "author": f["author"], "provenance": {"ingestor": INGESTOR, "matched_by": f["matched_by"], "subject_name": f["subject"],
                                                                "voice_ambiguous": f["voice_ambiguous"]}})
        if r["summary"]:
            lines.append({"record": "cell", "cell_id": h(doc_node, r["unit_id"]), "node_id": doc_node, "unit_id": r["unit_id"],
                          "scope_id": scope, "text": r["summary"], "tier": LUNA, "provenance": {"ingestor": INGESTOR, "kind": "unit_summary"}})
        by_node = {}
        for c in r["cells"]:
            nid = node_of.get((r["position"], c["entity"]))
            if nid:
                by_node.setdefault(nid, []).append(c)
        for nid, cs in by_node.items():
            lines.append({"record": "cell", "cell_id": h(nid, r["unit_id"]), "node_id": nid, "unit_id": r["unit_id"],
                          "scope_id": scope, "text": " ".join(c["text"] for c in cs), "tier": LUNA,
                          "provenance": {"ingestor": INGESTOR, "entity_names": [c["entity"] for c in cs]}})
    if folded["abstract"]:
        lines.append({"record": "abstract", "node_id": doc_node, "scope_id": scope, "text": folded["abstract"]["text"],
                      "children_hash": folded["abstract"]["children_hash"], "tier": LUNA, "updated_at": lines[0]["written_at"]})
    for a in folded["entity_abstracts"]:
        lines.append({"record": "abstract", "node_id": h(doc["doc_id"], a["entity"]), "scope_id": scope, "text": a["text"],
                      "children_hash": a["children_hash"], "tier": LUNA, "updated_at": lines[0]["written_at"]})
    for d in folded["dossiers"]:
        lines.append({"record": "dossier", "node_id": h(doc["doc_id"], d["entity"]), "text": d["text"],
                      "embedding_model": EMBED_MODEL if "embedding" in d else None, "embedding": d.get("embedding")})
    lines += [{"record": "ledger", **row} for row in ledger]
    lines += [{"record": "candidate", **row} for row in candidates]
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
    lines.append({"record": "predicate_census", "predicates": census})
    for r in records:
        for x in r["rejected_facts"]:
            lines.append({"record": "rejection", "stage": "facts", "unit_id": r["unit_id"], **x})
        for x in r["dropped_entities"]:
            lines.append({"record": "rejection", "stage": "entities", "category": "no_surface_form" if x["why"].startswith("no ") else "span_claimed",
                          "unit_id": r["unit_id"], **x})
    counts = {"units": len(records), "entities": len(entities), "majors": len(folded["majors"]), "minors": len(folded["minors"]),
              "mentions": sum(len(r["mentions"]) for r in records), "facts_kept": sum(len(r["facts"]) for r in records),
              "facts_stored": sum(1 for l in lines if l["record"] == "fact"), "facts_minor_subject": dropped_minor,
              "facts_rejected": sum(len(r["rejected_facts"]) for r in records), "cells": sum(1 for l in lines if l["record"] == "cell"),
              "shared_spans": sum(r["shared_spans"] for r in records), "ambiguous_voice": sum(r["ambiguous_voice"] for r in records),
              "empty_units": sum(r["empty"] for r in records), "abstract": folded["abstract"] is not None}
    lines.append({"record": "completion", "doc_id": doc["doc_id"], "input_hash": input_hash(doc), "ingestor": INGESTOR,
                  "counts": counts, "stats": stats, "empty": counts["facts_stored"] == 0 and counts["cells"] == 0,
                  "abstract_rejected": folded["abstract_rejected"], "entity_abstract_rejected": folded["entity_abstract_rejected"]})
    body = "\n".join(json.dumps(l, ensure_ascii=False) for l in lines) + "\n"
    path.write_text(body, encoding="utf-8", newline="\n")
    return path, counts


def completed(doc):
    """The completion record of an existing package for this exact input, else None."""
    path = package_path(doc)
    if not path.exists():
        return None
    last = None
    for line in read_jsonl(path):
        last = line
    return last if last and last.get("record") == "completion" and last.get("input_hash") == input_hash(doc) else None

# %%
# Block 10: one document end to end, then the corpus, resumable. A finished package for the same
# input is skipped, so a rerun mints nothing; a document stopped mid-way resumes from the units
# its sidecar already holds. Every document appends an entry to ingest.log and a row to
# manifest.jsonl; the receipt sums the packages on disk and the calls this session logged.
LOG = OUT / "ingest.log"
MANIFEST = OUT / "manifest.jsonl"


def checkpointed(doc):
    """The unit records a previous attempt at this document left behind, when they belong to
    this input in order; else nothing."""
    side = sidecar_path(doc)
    if not side.exists():
        return []
    rows = [r for r in read_jsonl(side) if r.get("ingestor") == INGESTOR and r.get("input_hash") == input_hash(doc)]
    ids = [u["unit_id"] for u in doc["units"]]
    kept = []
    for r in rows:
        if len(kept) < len(ids) and r["rec"]["unit_id"] == ids[len(kept)]:
            kept.append(r["rec"])
    return kept


def ingest(doc, ctx=None):
    ctx = {"doc": doc["source_uri"], **(ctx or {})}
    before_calls, before_spend = len(CALLS), spend()
    roster = {"entities": [], "predicates": [], "predicate_counts": {}}
    records, previous = checkpointed(doc), None
    for rec in records:                                              # replay what the sidecar holds
        advance_roster(roster, rec)
        previous = rec["summary"] or previous
    side = sidecar_path(doc)
    if not records and side.exists():
        side.unlink()
    for u in doc["units"][len(records):]:
        unit = {**u, "text": doc["text"][u["start"]:u["end"]]}
        rec = derive_unit(doc, unit, roster, previous, {**ctx, "unit": u["position"]})
        records.append(rec)
        side.parent.mkdir(parents=True, exist_ok=True)
        with side.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ingestor": INGESTOR, "input_hash": input_hash(doc), "rec": rec}, ensure_ascii=False) + "\n")
        advance_roster(roster, rec)
        previous = rec["summary"] or previous
    entities, ledger, candidates, n_locals, n_pairs, n_judged = reconcile(doc, records, ctx)
    folded = fold_document(doc, records, entities, ctx)
    stats = {"locals": n_locals, "candidate_pairs": n_pairs, "judged_pairs": n_judged,
             "calls": len(CALLS) - before_calls, "cost": round(spend() - before_spend, 4),
             "matched_by": {}, "rejected_by": {}, "roster_size": len(roster["entities"]), "predicates": len(roster["predicates"])}
    for r in records:
        for f in r["facts"]:
            stats["matched_by"][f["matched_by"]] = stats["matched_by"].get(f["matched_by"], 0) + 1
        for x in r["rejected_facts"]:
            stats["rejected_by"][x["category"]] = stats["rejected_by"].get(x["category"], 0) + 1
    path, counts = write_package(doc, records, entities, folded, ledger, candidates, stats)
    if side.exists():
        side.unlink()
    return path, counts, stats, records, entities, folded


def show(doc, counts, stats, entities, folded, path):
    lines = [f"{doc['source_uri']}  units {counts['units']}  entities {counts['entities']} ({counts['majors']} major)"
             f"  mentions {counts['mentions']}  facts {counts['facts_kept']} kept / {counts['facts_rejected']} rejected"
             f" / {counts['facts_stored']} stored  cells {counts['cells']}  calls {stats['calls']}  ${stats['cost']:.3f}",
             f"    matched {stats['matched_by']}  rejected {stats['rejected_by']}  locals {stats['locals']} pairs {stats['candidate_pairs']} judged {stats['judged_pairs']}",
             f"    abstract: {(folded['abstract'] or {}).get('text', 'REJECTED ' + str(folded['abstract_rejected']))[:200]}"]
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


def run(uris, stop_on_error=False):
    if not KEY and generate.__module__ == __name__:          # the real generate with no key: say so once, not per document
        raise SystemExit("no OPENAI_API_KEY: set it in the environment, or attach it as a Kaggle secret")
    done = skipped = 0
    for uri in uris:
        if uri not in BY_URI:
            note(f"not in export: {uri}")
            continue
        before = spend()
        try:
            doc = load_document(uri, BY_URI, UNITS, PIECES)
            if completed(doc):
                skipped += 1
                continue
            path, counts, stats, records, entities, folded = ingest(doc)
            with MANIFEST.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"doc_id": doc["doc_id"], "source_uri": uri, "package": str(path.relative_to(OUT)).replace("\\", "/"),
                                    "input_hash": input_hash(doc), "counts": counts, "cost": stats["cost"]}) + "\n")
            show(doc, counts, stats, entities, folded, path)
        except SpendStop as e:
            note(f"{uri}: {e} after ${spend() - before:.3f} on this document; its finished units are checkpointed and the run stops here")
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
           "cost_of_packages": 0.0, "cost_this_session": round(spend(), 4), "calls_this_session": len(CALLS), "calls_by_stage": {},
           "schema_rejections_this_session": len(REJECTIONS), "empty_completions": 0, "abstract_rejected": 0, "in_flight_sidecars": []}
    for c in CALLS:
        rec["calls_by_stage"][c["stage"]] = rec["calls_by_stage"].get(c["stage"], 0) + 1
    for path in sorted(OUT.rglob("*.jsonl")):
        if path.parent == OUT:
            continue
        if path.name.endswith(".units.jsonl"):
            rec["in_flight_sidecars"].append(str(path.relative_to(OUT)).replace("\\", "/"))
            continue
        last = None
        for line in read_jsonl(path):
            last = line
        if not last or last.get("record") != "completion":
            continue
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
# Block 11: the test variety. A sampling of every source type the extractor produces, the
# paper and chat paths first-class: three hundred LongMemEval sessions, twenty papers, two
# GraphRAG-Bench texts, three Oz books (the regression fixture against the 09-02 demo), two
# Holmes collections, two Greek works: 329 documents, 1,177 units (a chat is two units, its
# header and its turns). The cheap documents come first, so a run that hits the stop has
# finished the chat and paper paths before the books, where the judge spends most.


def sample(per_group=None):
    def pick(suffixes, n):
        found = [u for s in suffixes for u in BY_URI if u.endswith(s)]
        return found[:n] if n else found
    groups = [
        sorted(u for u in BY_URI if "/longmemeval/" in u)[:per_group or 300],
        sorted(u for u in BY_URI if u.endswith(".pdf"))[:per_group or 20],
        pick(["/graphrag-bench/Novel-30752.txt", "/graphrag-bench/Novel-40700.txt"], per_group),
        pick(["/oz/01_55.txt", "/oz/02_54.txt", "/oz/03_486.txt"], per_group),
        pick(["/holmes/03_1661.txt", "/holmes/05_2852.txt"], per_group),
        pick(["/greek/03_348.txt", "/greek/11_830.txt"], per_group),
    ]
    return [u for g in groups for u in g]


def targets(spec):
    """The documents a run names: "sample" (block 11), "all" (the whole export), or a list of
    source_uri suffixes such as ["/oz/01_55.txt"]."""
    if spec == "sample":
        return sample()
    if spec == "all":
        return sorted(BY_URI)
    return [u for s in spec for u in BY_URI if u.endswith(s)]

# %%
# Block 12: the run. On Kaggle this cell is the run, and it spends money, so its two knobs are
# here in the open: RUN is "sample", "all", or a list of source_uri suffixes; SPEND_STOP ends
# the run past that many dollars. When it fires, the document in flight keeps its finished
# units in a sidecar and is picked up from there next time, and the calls already made are in
# calls.jsonl. Locally the same thing is `python factledger-ingestor.py --sample`, `--sample 2`
# for two of every group, or one or more source_uri suffixes; the stop comes from the
# SPEND_STOP environment variable, default $25.
RUN = ["/oz/01_55.txt"]          # Oz book 1 alone first; then "sample", then "all"
ON_KAGGLE = Path("/kaggle/working").exists()
if ON_KAGGLE:
    SPEND_STOP = 5.00

if __name__ == "__main__" and not ON_KAGGLE and len(sys.argv) > 1:
    RUN = sample(int(sys.argv[2])) if sys.argv[1] == "--sample" and len(sys.argv) > 2 else "sample" if sys.argv[1] == "--sample" else sys.argv[1:]
if ON_KAGGLE or (__name__ == "__main__" and len(sys.argv) > 1):
    uris = targets(RUN)
    print(f"ingesting {len(uris)} documents, stop at ${SPEND_STOP:.2f}")
    try:
        run(uris)
    finally:
        print(json.dumps(receipt(), indent=1)[:3000])
