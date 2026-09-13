"""Extractor 1.7 -> 1.8, the dates rebuild: block 0 unpacks LongMemEval into dated histories, a chat
turn carries its own timestamp, every book and paper piece takes the date of the work it lies in
(the page's, else a web search's), a unit never spans a date change, the document takes its
earliest unit, and every call runs on the Flex tier. Each old string must be found exactly once.

    python make_18.py <extractor 1.7 .py> <block0_unpack.py> <out .py>
"""
import sys
from pathlib import Path

SRC, BLOCK0, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
raw = SRC.read_bytes().decode("utf-8")
crlf = "\r\n" in raw
text = raw.replace("\r\n", "\n")
block0 = BLOCK0.read_text(encoding="utf-8").replace("\r\n", "\n").rstrip("\n") + "\n\n\n"

CHANGES = [
    # ---- the header
    (r'''# One mount (`RAW`, the public raw dataset), one folder per corpus, each with a `manifest.json`
# recording every file's source URL, byte count and sha256:
#
# | corpus | files | shape |
# |---|---|---|
# | `longmemeval` | 19,206 | one JSON per assistant chat session |
''',
     r'''# One mount (`RAW`, the public raw dataset), one folder per corpus, each with a `manifest.json`
# recording every file's source URL, byte count and sha256. Block 0 first unpacks LongMemEval's
# benchmark file into chat histories under `/kaggle/temp/chats`, one folder per history:
#
# | corpus | files | shape |
# |---|---|---|
# | `longmemeval` | 25,112 | chat sessions in 500 histories, every turn timestamped (block 0) |
'''),
    (r'''# | chat JSON | one block per turn: a `SESSION <id> TURN <n> <date>` line, then `role: content`; turn spans kept |''',
     r'''# | chat JSON | one block per turn that says something: a `SESSION <id> TURN <n> <time>` line, then `role: content`; turn spans and times kept |'''),
    (r'''# | `source_uri` | mount, corpus and file, for example `it494-narrative-corpora-raw/oz/01_55.txt` |
# | `title`, `author`, `occurred_at` | what the model read off the page and a pointer proved |
''',
     r'''# | `source_uri` | mount, corpus and file, for example `it494-narrative-corpora-raw/oz/01_55.txt`; a chat is `chats/longmemeval/<history>/<session>.json` |
# | `title`, `author` | what the model read off the page and a pointer proved; a chat's title is its session id |
# | `occurred_at` | the earliest of its units' dates |
'''),
    (r'''# | `label` | a human label: a chapter title, or for a chat the line that opens the turn, `SESSION <id> TURN <n> <date>` |''',
     r'''# | `label` | a human label: a chapter title, or for a chat the line that opens the turn, `SESSION <id> TURN <n> <time>` |'''),
    (r'''# | `occurred_at` | the document's date for a document that was read; for a chat, the session's date when it has exactly one, else `null` |''',
     r'''# | `occurred_at` | for a document that was read, the date of the work the unit belongs to; for a chat, the turn's time |'''),
    (r'''# | `occurred_at` | a chat turn's time, its session's date when the session has exactly one; else `null` |''',
     r'''# | `occurred_at` | a chat turn's time; for a document that was read, the date of the work the piece belongs to |'''),
    (r'''#                     source_class, title, author, source, date  each a pointer plus its value
#                     toc_count                                  what the contents list promises
''',
     r'''#                     source_class, title, author, source        each a pointer plus its value
#                     works                                      each work the document holds,
#                                                                with the date its page states
#                     toc_count                                  what the contents list promises
'''),
    (r'''#                 nothing the model asserted without a verified pointer reaches the output
''',
     r'''#                 nothing the model asserted without a verified pointer reaches the output
#     date        each work takes the date its page states; a work whose page states none is
#                 looked up on the web by its title and author; every piece takes its work's date
'''),
    (r'''#                 over the cap, and cuts any group where the kind changes
''',
     r'''#                 over the cap, and cuts any group where the kind or the date changes
'''),
    (r'''#     units       one per turn, named by the line that opens it: SESSION <id> TURN <n> <date>
#     time        the session's date when it has one; none when the benchmark placed it on
#                 several, since each of those dates belongs to a question
# ```
#
# 19,206 of the 19,395 documents cost nothing to split.
''',
     r'''#     skip        an empty session, and a turn that says nothing; both are counted
#     units       one per turn, named by the line that opens it: SESSION <id> TURN <n> <time>
#     time        each turn's own timestamp; the document takes the earliest
# ```
#
# Chats cost nothing to split; the books and papers cost the model's calls and the date lookups.
'''),
    (r'''# Attach the raw dataset (`jhffmn/it494-narrative-corpora-raw`), which carries every corpus
# including the papers. Attach `OPENAI_API_KEY` under Add-ons > Secrets and turn Internet on.
''',
     r'''# Attach the raw dataset (`jhffmn/it494-narrative-corpora-raw`), which carries every corpus,
# including the papers and the LongMemEval benchmark file. Attach `OPENAI_API_KEY` under
# Add-ons > Secrets and turn Internet on. Every model call runs on OpenAI's Flex tier.
'''),
    # ---- block 0, before block 1
    (r'''# %%
# Block 1: inputs and integrity.
''', block0 + r'''# %%
# Block 1: inputs and integrity.
'''),
    (r'''SIDECARS = ("manifest.json", "LICENSE", "README.md")   # packaging, never a document''',
     r'''SIDECARS = ("manifest.json", "LICENSE", "README.md", "longmemeval_s.json")   # packaging and sources, never a document'''),
    # ---- block 2: a chat turn carries its own time; empty turns and sessions
    (r'''#        json -> if it holds chat turns, one block per turn: a "SESSION <id> TURN <n> <date>"
#                line, then "role: content". We also keep where each turn starts and ends
#                in that string, so a chat can be cut into units without a model.
''',
     r'''#        json -> if it holds chat turns, one block per turn that says something: a
#                "SESSION <id> TURN <n> <time>" line, then "role: content". We also keep where
#                each turn starts and ends in that string, and its timestamp, so a chat can be
#                cut into dated units without a model. A session with no turns is an empty chat.
'''),
    (r'''def chat_text(obj, turns):
    """One block per turn: a line naming it, SESSION <id> TURN <n> <date>, then 'role: content'
    and a blank line. The date is the session's own when it has exactly one; a session placed on
    several dates names none. Returns the text and (start, end, role) for each turn, which tile
    the text from 0."""
    sid = obj.get("session_id") if isinstance(obj, dict) else None
    dates = obj.get("dates", []) if isinstance(obj, dict) else []
    stamp = f" {dates[0]}" if len(dates) == 1 else ""
    text, spans = "", []
    for i, turn in enumerate(turns):
        start = len(text)
        name = f"SESSION {sid} TURN {i + 1}" if sid is not None else f"TURN {i + 1}"
        text += f"{name}{stamp}\n{turn['role']}: {turn['content']}\n\n"
        spans.append((start, len(text), turn["role"]))
    return text, spans
''',
     r'''def chat_text(obj, turns):
    """One block per turn that says something: a line naming it, SESSION <id> TURN <n> <time>, then
    'role: content' and a blank line. n is the turn's place in the file, so a skipped empty turn
    leaves a gap rather than renumbering the rest. Returns the text and (start, end, role, time)
    for each turn written, which tile the text from 0."""
    sid = obj.get("session_id") if isinstance(obj, dict) else None
    text, spans = "", []
    for i, turn in enumerate(turns):
        if not str(turn["content"]).replace(chr(0x200B), "").strip():   # a turn that says nothing
            continue
        when = str(turn.get("timestamp") or "").strip()
        name = f"SESSION {sid} TURN {i + 1}" if sid is not None else f"TURN {i + 1}"
        start = len(text)
        text += f"{name} {when}".rstrip() + f"\n{turn['role']}: {turn['content']}\n\n"
        spans.append((start, len(text), turn["role"], when or None))
    return text, spans
'''),
    (r'''           "kind": file_kind(data), "text": "", "turns": None, "dates": [], "session_id": None}
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
''',
     r'''           "kind": file_kind(data), "text": "", "turns": None, "skipped_turns": 0, "session_id": None}
    if doc["kind"] == "pdf":
        doc["text"] = pdf_text(data)
    elif doc["kind"] == "json":
        obj = json.loads(data)
        turns = chat_turns(obj)
        empty = isinstance(obj, dict) and obj.get("turns") == []      # a session with no turns is still a chat
        if turns is None and not empty:
            doc["kind"], doc["text"] = "text", data.decode("utf-8", errors="replace")
        else:
            doc["kind"] = "chat"
            doc["text"], doc["turns"] = chat_text(obj, turns or [])
            doc["skipped_turns"] = len(turns or []) - len(doc["turns"])
'''),
    (r'''for path in [RAW / "oz" / "01_55.txt", RAW / "graphrag-bench" / "Novel-30752.txt",
             RAW / "longmemeval" / "sharegpt_yywfIrx_0.json", RAW / "longmemeval" / "001cefa7_2.json",
             RAW / "kg-rag-cc" / "pdf" / "001_2024.eacl-demo.16.pdf"]:
    d = to_text(path)
    turns = len(d["turns"]) if d["turns"] else "-"
    print(f"{path.name:<26} {d['kind']:<5} {len(d['text']):>8,} chars  turns {turns:>3}  dates {d['dates']}")
''',
     r'''for path in [RAW / "oz" / "01_55.txt", RAW / "graphrag-bench" / "Novel-30752.txt",
             *sorted((CHATS / "longmemeval").glob("*/*.json"))[:2],
             RAW / "kg-rag-cc" / "pdf" / "001_2024.eacl-demo.16.pdf"]:
    d = to_text(path)
    turns = len(d["turns"]) if d["turns"] else "-"
    print(f"{path.name:<26} {d['kind']:<5} {len(d['text']):>8,} chars  turns {turns:>3}  empty turns skipped {d['skipped_turns']}")
'''),
    # ---- block 3: Flex for every call, and the date lookup
    (r'''import json
import threading
import time

import requests
''',
     r'''import json
import re
import threading
import time

import requests
'''),
    (r'''PRICE = {"gpt-5.6-luna": (0.20, 1.20), "gpt-5.6-terra": (2.00, 12.00)}   # $ per M tokens in, out''',
     r'''PRICE = {"flex": {"gpt-5.6-luna": (0.10, 0.60), "gpt-5.6-terra": (1.00, 6.00)},        # $ per M tokens in, out,
         "default": {"gpt-5.6-luna": (0.20, 1.20), "gpt-5.6-terra": (2.00, 12.00)}}    # by the tier that served the call
SEARCH_FEE = 0.01                                                        # dollars per web search: $10 per 1,000'''),
    (r'''def generate(prompt, model=MODEL, effort="low"):
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


print(f"model {MODEL}, retry {MODEL} then {RETRY} under {RETRY_MAX_TOKENS:,} tokens, spend stop ${SPEND_STOP:.2f}, key {'present' if KEY else 'MISSING'}")''',
     r'''def post(url, payload, model, prompt_chars, flex=True):
    """One call to OpenAI, on the Flex tier unless told otherwise; (body, seconds). A timeout,
    connection error, 429 or 5xx is retried three times with a pause (Flex answers 429 when it
    has no capacity); no key or no credits stops the run; any other non-200 raises with the body."""
    if not KEY:
        raise RuntimeError("no OPENAI_API_KEY: attach it under Add-ons > Secrets and rerun block 3")
    if spend() >= SPEND_STOP:
        raise SpendStop(f"spending stop: ${spend():.2f}")
    t0 = time.time()
    for attempt in range(3):
        try:
            r = requests.post(url, headers={"Authorization": f"Bearer {KEY}"}, timeout=900,
                              json={**payload, "service_tier": "flex"} if flex else payload)
        except (requests.Timeout, requests.ConnectionError):
            # the server may have finished and billed the request: count the input as spent
            calls.append({"model": model, "in": prompt_chars // 4, "out": 0, "seconds": round(time.time() - t0, 1),
                          "bill": BILL.get(threading.get_ident()), "timeout": True,
                          "cost": prompt_chars // 4 * PRICE["default"][model][0] / 1e6})
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
    return r.json(), round(time.time() - t0, 1)


def log_call(body, model, tokens_in, tokens_out, seconds, searches=0):
    """The call's cost at the price of the tier that served it, plus its web searches."""
    p_in, p_out = PRICE.get(body.get("service_tier"), PRICE["default"])[model]
    calls.append({"model": model, "tier": body.get("service_tier"), "in": tokens_in, "out": tokens_out, "searches": searches,
                  "seconds": seconds, "bill": BILL.get(threading.get_ident()),
                  "cost": (tokens_in * p_in + tokens_out * p_out) / 1e6 + searches * SEARCH_FEE})


def generate(prompt, model=MODEL, effort="low"):
    """One JSON-mode call; the reply parsed, the cost logged. The API rejects temperature."""
    body, seconds = post("https://api.openai.com/v1/chat/completions",
                         {"model": model, "reasoning_effort": effort, "response_format": {"type": "json_object"},
                          "messages": [{"role": "user", "content": prompt}]}, model, len(prompt))
    u = body["usage"]
    log_call(body, model, u["prompt_tokens"], u["completion_tokens"], seconds)
    return json.loads(body["choices"][0]["message"]["content"])


# A date value: YYYY, YYYY-MM or YYYY-MM-DD, a signed year before the common era (counting a year
# zero), ~ after an approximate date, and a range as two such dates joined by /.
DATE_FORM = re.compile(r"-?\d{4}(-\d{2}(-\d{2})?)?~?(/-?\d{4}(-\d{2}(-\d{2})?)?~?)?")

LOOKUP_PROMPT = """Search the web for when this work was written.

Title: %s
Author: %s

Give the date the work itself was written, or first published when that is all the sources give; never the date of a translation, an edition, a transcription or an ebook. Answer with JSON only: {"date": "...", "source": "the URL the date is taken from"}, or {"date": null, "source": null} when no source gives a date. Write the date as YYYY, YYYY-MM or YYYY-MM-DD. A year before the common era is a signed year counting a year zero, so 1 BC is 0000 and 2 BC is -0001. Put ~ after a date that is approximate, and write a range as its two ends joined by /."""


def lookup_date(title, author):
    """(date, source) for one work, from one web search on its title and author; (None, why)
    when the search gives no date. Web search is asked on Flex first, and on the standard tier
    only if Flex refuses it."""
    if not title:
        return None, "no title to search on"
    prompt = LOOKUP_PROMPT % (title, author or "not named")
    payload = {"model": MODEL, "reasoning": {"effort": "low"}, "tools": [{"type": "web_search"}], "input": prompt}
    try:
        body, seconds = post("https://api.openai.com/v1/responses", payload, MODEL, len(prompt))
    except RuntimeError as e:
        if "service_tier" not in str(e) and "flex" not in str(e).lower():
            raise
        body, seconds = post("https://api.openai.com/v1/responses", payload, MODEL, len(prompt), flex=False)
    output = body.get("output") or []
    u = body.get("usage") or {}
    log_call(body, MODEL, u.get("input_tokens", 0), u.get("output_tokens", 0), seconds,
             searches=sum(1 for item in output if item.get("type") == "web_search_call"))
    content = [c for item in output if item.get("type") == "message" for c in item.get("content") or []]
    answer = "".join(c.get("text") or "" for c in content)
    cited = [a.get("url") for c in content for a in c.get("annotations") or [] if a.get("type") == "url_citation"]
    try:
        reply = json.loads(answer[answer.index("{"):answer.rindex("}") + 1])
    except ValueError:
        return None, "the search did not answer in JSON"
    date = str(reply.get("date") or "").strip()
    if not DATE_FORM.fullmatch(date):
        return None, "the search found no date"
    return date, str(reply.get("source") or (cited[0] if cited else "a web search"))


print(f"model {MODEL}, retry {MODEL} then {RETRY} under {RETRY_MAX_TOKENS:,} tokens, every call on the Flex tier,"
      f" spend stop ${SPEND_STOP:.2f}, key {'present' if KEY else 'MISSING'}")'''),
    # ---- block 5: the works and their dates
    (r'''# move, or remove a boundary. Pieces carry no date of their own: a text or PDF unit takes
# the document's date.
''',
     r'''# move, or remove a boundary. Every piece takes the date of the work it lies in: the date its
# page states, else one looked up on the web (block 7).
'''),
    (r'''  "date": {"index": n, "text": "...", "iso": "YYYY" or "YYYY-MM" or "YYYY-MM-DD"} or null: the line giving the date the work was written or first published, or sent; for a translation or a later edition, the original work's date when the file gives it; never a transcription or ebook release date; null when the file states none,
''',
     r'''  "works": [{"index": n, "text": "...", "title": "the work's title as it should read", "author": "its author's name when it is not the document's, else null", "date": {"index": n, "text": "...", "value": "..."} or null}, ...]: every separate work the document holds, in order, each pointed at the line where it begins. A separate work is one its author wrote as a whole of its own, such as a book, a play, a story, a poem, a letter, a treatise or a paper; the chapters, scenes and sections of one work are not separate works, and a document that is one work lists that one. A work's date points at the line stating when that work itself was written, or first published when that is all the file gives; never the date of a translation, an edition, a transcription or an ebook; null when the file states none. Write its value as YYYY, YYYY-MM or YYYY-MM-DD; a year before the common era is a signed year counting a year zero, so 1 BC is 0000 and 2 BC is -0001; put ~ after an approximate date, and write a range as its two ends joined by /,
'''),
    # ---- block 6: works from the reply, the page-date gate for the new forms
    (r'''ADVISORY = {"metadata", "shape", "dates", "too long", "merging", "grouping"}''',
     r'''ADVISORY = {"metadata", "shape", "dates", "date", "too long", "merging", "grouping"}'''),
    (r'''def pieces_from_reply(text, r, addrs, stats):
''',
     r'''def rendered(r, key, field):
    """The model's rendering of a pointer (title, name), else the line it pointed at."""
    v = r.get(key) or {}
    return (v.get(field) or v.get("text")) if isinstance(v, dict) else None


def works_from_reply(text, r, addrs):
    """The works the document holds, in order, each as {start, title, author, date}: where it
    begins, its title and author as the model rendered them, and the date its page states,
    checked like any other pointer. A document that names no work is one work, its own, at 0."""
    works = {}
    for w in as_list(r.get("works")):
        span = resolve(w, text, addrs, fresh_stats(addrs, None), loose=True) if isinstance(w, dict) else None
        if span is None or span[0] in works:
            continue
        d, date = w.get("date"), None
        where = resolve(d, text, addrs, fresh_stats(addrs, None), loose=True) if isinstance(d, dict) else None
        if where is not None:
            date = date_ok(text[slice(*where)], str(d.get("value") or ""))
        works[span[0]] = {"start": span[0], "title": str(w.get("title") or "").strip() or None,
                          "author": str(w.get("author") or "").strip() or None, "date": date}
    if not works:
        works[0] = {"start": 0, "title": rendered(r, "title", "title"), "author": None, "date": None}
    return [works[s] for s in sorted(works)]


def pieces_from_reply(text, r, addrs, stats):
'''),
    (r'''    starts = sorted({s for s, _ in regions} | set(heads))
    pieces = []
    for s, e in zip(starts, starts[1:] + [len(text)]):
        kind = [k for rs, k in regions if rs <= s][-1]
        label = heads.get(s, "opening" if kind == "body" else kind.replace("_", " "))
        pieces.append(piece(s, e, label, kind))
''',
     r'''    works = works_from_reply(text, r, addrs)
    stats["works"] = works
    titled = {w["start"]: w["title"] for w in works if w["title"]}
    starts = sorted({s for s, _ in regions} | set(heads) | {w["start"] for w in works})   # a work begins a piece
    pieces = []
    for s, e in zip(starts, starts[1:] + [len(text)]):
        kind = [k for rs, k in regions if rs <= s][-1]
        label = heads.get(s) or titled.get(s) or ("opening" if kind == "body" else kind.replace("_", " "))
        pieces.append(piece(s, e, label, kind))
'''),
    (r'''def date_ok(line, iso):
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
''',
     r'''def date_ok(line, value):
    """The value to keep, checked against the line the model read it from: its first year must be
    on that line as the line would print it (405 for the signed year -0404), and a month or day is
    kept only when the line names the month. None when the year is not there, so a date the model
    inferred from elsewhere is never stored."""
    if not DATE_FORM.fullmatch(value):
        return None
    first = value.split("/")[0].rstrip("~")
    year = int(first[:5]) if first.startswith("-") else int(first[:4])
    if str(year if year > 0 else 1 - year) not in line:
        return None
    if year > 0 and len(first) > 4:
        m, low = int(first[5:7]), line.lower()
        if not (1 <= m <= 12 and (MONTHS[m - 1] in low or re.search(rf"\b0?{m}\b", low))):
            return first[:4]
    return value
'''),
    (r'''    """Title, author, source and date pointers, checked like every other, but counted into a''',
     r'''    """Title, author and source pointers, checked like every other, but counted into a'''),
    (r'''    for key in ("title", "author", "source", "date"):
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
''',
     r'''    for key in ("title", "author", "source"):
        v = r.get(key)
        if v is None:
            continue
        span = resolve(v, text, addrs, fresh_stats(addrs, None), loose=True) if isinstance(v, dict) else None
        if span is None:
'''),
    # ---- block 7: a unit never spans a date change; the work dates; chat turn times
    (r'''# A text or PDF unit carries the document's date. Chat pieces are the turns, built from the
# turn spans block 2 kept, with the role as author. A chat unit is one turn, with no model
# call, and its label is the line that opens it: SESSION <id> TURN <n> <date>. Its time is the
# session's date when the session has one. A session the benchmark placed on several dates
# keeps none, on the document, its units and its turns alike, because each of those dates
# belongs to a question and the evaluation supplies it.
''',
     r'''# A text or PDF piece takes the date of the work it lies in (date_works), and a unit never spans
# two dates: a change of date cuts a unit as a change of kind does. Chat pieces are the turns,
# built from the turn spans block 2 kept, with the role as author and the turn's own timestamp
# as its time. A chat unit is one turn, with no model call, and its label is the line that opens
# it: SESSION <id> TURN <n> <time>.
'''),
    (r'''            if pieces[j]["kind"] != pieces[i]["kind"]:      # the model's region boundary stands''',
     r'''            if (pieces[j]["kind"], pieces[j]["occurred_at"]) != (pieces[i]["kind"], pieces[i]["occurred_at"]):   # a region boundary or a change of date stands'''),
    (r'''    """The run cut wherever the kind changes, so a unit never holds two kinds. Returns the run
    itself when it is already of one kind, which is how the caller counts the cuts."""
    parts, part = [], [run[0]]
    for i in run[1:]:
        if pieces[i]["kind"] == pieces[part[-1]]["kind"]:''',
     r'''    """The run cut wherever the kind or the date changes, so a unit never holds two kinds or two
    dates. Returns the run itself when it is already whole, which is how the caller counts the cuts."""
    parts, part = [], [run[0]]
    for i in run[1:]:
        if (pieces[i]["kind"], pieces[i]["occurred_at"]) == (pieces[part[-1]]["kind"], pieces[part[-1]]["occurred_at"]):'''),
    (r'''        flags.append(f"grouping: {mixed} group(s) cut where the kind changed")''',
     r'''        flags.append(f"grouping: {mixed} group(s) cut where the kind or the date changed")'''),
    (r'''def parse_time(value):
''',
     r'''def date_works(doc, pieces, reply, stats, flags):
    """Every piece takes the date of the work it lies in: the date the work's page states, else the
    one a web search on its title and author finds, else none. Anything before the first work
    takes the first work's date. Each work's date, and where it came from, goes in the flags."""
    works = stats.get("works") or [{"start": 0, "title": rendered(reply, "title", "title"), "author": None, "date": None}]
    author = rendered(reply, "author", "name")
    name = BILL.get(threading.get_ident())

    def one(work):
        if work["date"]:
            return work["date"], "the page"
        bill_to(name)
        try:
            return lookup_date(work["title"], work["author"] or author)
        except (RuntimeError, requests.RequestException) as e:        # one failed lookup must not lose the document
            return None, f"the lookup failed: {str(e)[:80]}"

    with ThreadPoolExecutor(max_workers=min(FANOUT, len(works))) as pool:
        found = list(pool.map(one, works))
    for work, (date, source) in zip(works, found):
        work["date"], work["source"] = date, source
        flags.append(f"date: {work['title'] or 'the document'}: {date} from {source}" if date
                     else f"date: {work['title'] or 'the document'}: none, {source}")
    for p in pieces:
        before = [w for w in works if w["start"] <= p["start"]]
        p["occurred_at"] = (before[-1] if before else works[0])["date"]
    stats["works"] = works


def parse_time(value):
'''),
    (r'''def chat_pieces(doc):
    """One piece per turn, labelled by the line that opens it, with the role block 2 recorded as
    author. The time is the session's date when it has exactly one. A session the benchmark
    placed on several dates keeps none: each of those dates belongs to a question, and the
    evaluation supplies it per question."""
    dates = sorted(set(t for t in (parse_time(d) for d in doc["dates"]) if t))
    when = dates[0] if len(dates) == 1 else None
    text = doc["text"]
    pieces = [piece(s, e, text[s:text.index("\n", s)], kind=role, author=role, occurred_at=when)
              for s, e, role in doc["turns"]]
    flags = [f"dates: {len(dates)} session dates, none kept"] if len(dates) > 1 else []
    return pieces, flags
''',
     r'''def chat_pieces(doc):
    """One piece per turn that says something, labelled by the line that opens it, with the role
    as author and the turn's own timestamp as its time. A turn whose time cannot be read, a skipped
    empty turn, and a session with no turns at all are flagged."""
    text = doc["text"]
    pieces = [piece(s, e, text[s:text.index("\n", s)], kind=role, author=role, occurred_at=parse_time(when) if when else None)
              for s, e, role, when in doc["turns"]]
    if not pieces:
        return [], ["empty session: no turns"]
    flags = []
    undated = sum(1 for p in pieces if p["occurred_at"] is None)
    if undated:
        flags.append(f"date: {undated} turn(s) with no time the file gives")
    if doc["skipped_turns"]:
        flags.append(f"empty turns: {doc['skipped_turns']} skipped")
    return pieces, flags
'''),
    (r'''def units_from_runs(pieces, runs, text):
    units = []
    for i, run in enumerate(runs):
        ps = [pieces[j] for j in run]
        times = [q["occurred_at"] for q in ps if q["occurred_at"]]
        label = ps[0]["label"] if len(ps) == 1 else f"{ps[0]['label']} .. {ps[-1]['label']}"
        units.append({"position": i, "start": ps[0]["start"], "end": ps[-1]["end"], "label": label,
                      "occurred_at": min(times) if times else None,''',
     r'''def date_key(value):
    """A date value as a sortable key, by its first moment: -0404~ before 0100, a range by its start."""
    first = value.split("/")[0].rstrip("~")
    if first.startswith("-"):
        return int(first[:5]), first[5:]
    return int(first[:4]), first[4:]


def units_from_runs(pieces, runs, text):
    units = []
    for i, run in enumerate(runs):
        ps = [pieces[j] for j in run]
        times = [q["occurred_at"] for q in ps if q["occurred_at"]]
        label = ps[0]["label"] if len(ps) == 1 else f"{ps[0]['label']} .. {ps[-1]['label']}"
        units.append({"position": i, "start": ps[0]["start"], "end": ps[-1]["end"], "label": label,
                      "occurred_at": min(times, key=date_key) if times else None,'''),
    # ---- block 8: chats from block 0, the date step in the run, 1.8
    (r'''# read, so a new Kaggle session starts empty and asks every document again. Chats need no model
# call. Texts and PDFs print a full entry; chats print one line per hundred. The spend stop
''',
     r'''# read, so a new Kaggle session starts empty and asks every document again. Chats are read from
# the histories block 0 unpacked and need no model call. Texts and PDFs print a full entry; chats
# print one line per hundred and every flagged one. The spend stop
'''),
    (r'''LOADER = "threadatlas-extractor 1.7"''', r'''LOADER = "threadatlas-extractor 1.8"'''),
    (r'''def rel_of(path):
    """'raw/oz/01_55.txt' or 'raw/kg-rag-cc/pdf/001_x.pdf': the same name on any Kaggle mount."""
    return f"raw/{path.relative_to(RAW).as_posix()}"
''',
     r'''def rel_of(path):
    """'raw/oz/01_55.txt', 'raw/kg-rag-cc/pdf/001_x.pdf', or 'chats/longmemeval/<history>/<session>.json'
    for a chat block 0 unpacked: the same name on any Kaggle mount."""
    if path.is_relative_to(CHATS):
        return f"chats/{path.relative_to(CHATS).as_posix()}"
    return f"raw/{path.relative_to(RAW).as_posix()}"
'''),
    (r'''        return Path(record["path"])                          # a record written before files were named
    if not rel.startswith("raw/"):
''',
     r'''        return Path(record["path"])                          # a record written before files were named
    if rel.startswith("chats/"):
        return CHATS / rel[6:]
    if not rel.startswith("raw/"):
'''),
    (r'''def iso_of(reply):
    d = reply.get("date") if isinstance(reply, dict) else None
    return d.get("iso") if isinstance(d, dict) else None


''', r''''''),
    (r'''def rendered(r, key, field):
    """The model's rendering of a pointer (title, name), else the line it pointed at."""
    v = r.get(key) or {}
    return (v.get(field) or v.get("text")) if isinstance(v, dict) else None


def show(doc, record):''',
     r'''def show(doc, record):'''),
    (r'''             f" | date {iso_of(r)}"''', r'''             f" | works {len(st.get('works') or [])}"'''),
    (r'''      + sorted(p for p in RAW.glob("longmemeval/*.json") if p.name != "manifest.json")''',
     r'''      + sorted(CHATS.glob("longmemeval/*/*.json"))'''),
    (r'''            reply, stats = {}, {"addresses": None}
            runs = chat_runs(pieces, doc["text"])
        else:
            pieces, reply, flags, stats = split(doc)
''',
     r'''            reply, stats = {}, {"addresses": None, "skipped_turns": doc["skipped_turns"]}
            runs = chat_runs(pieces, doc["text"])
        else:
            pieces, reply, flags, stats = split(doc)
            date_works(doc, pieces, reply, stats, flags)      # every piece takes its work's date
'''),
    (r'''        if doc["kind"] != "chat":                    # a text or PDF unit carries the document's date
            for u in units:
                u["occurred_at"] = iso_of(reply)
            stats["short_units"]''',
     r'''        if doc["kind"] != "chat":
            stats["short_units"]'''),
    # ---- block 9: the document takes its earliest unit; empty sessions and turns counted
    (r'''#                    reused session dates, pointer mismatches, recoveries and duplicates, over-cap''',
     r'''#                    empty sessions and turns, pointer mismatches, recoveries and duplicates, over-cap'''),
    (r'''           "duplicate_files": [], "unknown_author": 0, "unknown_date": 0, "ambiguous_date": 0,''',
     r'''           "duplicate_files": [], "unknown_author": 0, "unknown_date": 0, "empty_sessions": 0, "empty_turns": 0,'''),
    (r'''        text, doc_id, r = doc["text"], doc["sha256"], record["reply"]
        if doc_id in exported:''',
     r'''        text, doc_id, r = doc["text"], doc["sha256"], record["reply"]
        if doc["kind"] == "chat" and not record["pieces"]:     # an empty session: counted, and exported as nothing
            receipt["empty_sessions"] += 1
            continue
        if doc_id in exported:'''),
    (r'''        src = f"{RAW.name}/{rel[4:]}"''',
     r'''        src = rel if rel.startswith("chats/") else f"{RAW.name}/{rel[4:]}"'''),
    (r'''        occurred = iso_of(r) or None''',
     r'''        times = [u["occurred_at"] for u in record["units"] if u["occurred_at"]]
        occurred = min(times, key=date_key) if times else None      # the earliest of its units'''),
    (r'''        if doc["kind"] == "chat":                        # the session's one date, as block 7 gives its units
            dates = sorted(set(t for t in (parse_time(d) for d in doc["dates"]) if t))
            occurred = dates[0] if len(dates) == 1 else None
''',
     r'''        if doc["kind"] == "chat":
'''),
    (r'''        receipt["unknown_date"] += occurred is None and doc["kind"] != "chat"
        receipt["ambiguous_date"] += any(f.split(":")[0] in ("dates", "ambiguous date") for f in flags)''',
     r'''        receipt["unknown_date"] += occurred is None
        receipt["empty_turns"] += (record.get("stats") or {}).get("skipped_turns", 0)'''),
    (r'''      f"  reused dates {receipt['ambiguous_date']}"''',
     r'''      f"  empty sessions {receipt['empty_sessions']}  empty turns {receipt['empty_turns']}"'''),
]

for old, new in CHANGES:
    n = text.count(old)
    assert n == 1, (n, old[:100])
    text = text.replace(old, new)
for gone in ("iso_of", 'doc["dates"]', "ambiguous_date", "1.7\""):
    assert gone not in text, gone
OUT.write_bytes((text.replace("\n", "\r\n") if crlf else text).encode("utf-8"))
print(len(CHANGES), "changes applied ->", OUT)
