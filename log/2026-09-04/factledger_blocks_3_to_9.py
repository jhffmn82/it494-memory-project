# %%
# Block 3: the model call.
import json
import time

import requests
from kaggle_secrets import UserSecretsClient

MODEL = "gpt-5.6-luna"
RETRY = "gpt-5.6-terra"
PRICE = {"gpt-5.6-luna": (0.20, 1.20), "gpt-5.6-terra": (2.00, 12.00)}   # $ per M tokens in, out
SPEND_STOP = 8.00                                                        # dollars; the run halts past this
KEY = UserSecretsClient().get_secret("OPENAI_API_KEY")
calls = []


def spend():
    return sum(c["cost"] for c in calls)


def generate(prompt, model=MODEL, effort="low"):
    """One JSON-mode call; the reply parsed, the cost logged. The API rejects temperature.
    A timeout, connection error, 429, or 5xx is retried three times with a pause; any other
    non-200 raises with the response body."""
    if spend() >= SPEND_STOP:
        raise RuntimeError(f"spending stop: ${spend():.2f}")
    t0 = time.time()
    for attempt in range(3):
        try:
            r = requests.post("https://api.openai.com/v1/chat/completions",
                              headers={"Authorization": f"Bearer {KEY}"}, timeout=300,
                              json={"model": model, "reasoning_effort": effort,
                                    "response_format": {"type": "json_object"},
                                    "messages": [{"role": "user", "content": prompt}]})
        except (requests.Timeout, requests.ConnectionError):
            if attempt == 2:
                raise
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code == 429 or r.status_code >= 500:
            if attempt == 2:
                raise RuntimeError(f"OpenAI {r.status_code}: {r.text}")
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code != 200:
            raise RuntimeError(f"OpenAI {r.status_code}: {r.text}")
        break
    body = r.json()
    u, (p_in, p_out) = body["usage"], PRICE[model]
    calls.append({"model": body["model"], "in": u["prompt_tokens"], "out": u["completion_tokens"],
                  "seconds": round(time.time() - t0, 1),
                  "cost": (u["prompt_tokens"] * p_in + u["completion_tokens"] * p_out) / 1e6})
    return json.loads(body["choices"][0]["message"]["content"])


print(f"model {MODEL}, retry {RETRY}, spend stop ${SPEND_STOP:.2f}, key {'present' if KEY else 'MISSING'}")


# %%
# Block 4: the candidate list. Code decides where the model may point; the model only chooses.
# A candidate is a place a heading, a title line, or a body boundary could be. The text is read
# as blocks, the runs of lines between blank lines: a block of at most BLOCK_LINES short lines
# is a candidate (a chapter heading, a two-line heading, a scene marker, a one-line paragraph),
# and a longer block is prose and is skipped. The first HEAD and last TAIL lines are candidates
# one by one regardless, because the preamble, the contents list, and the end matter live
# there. A document without lines (a whole book on one line) is cut into sentences and the
# short ones of two words or more are the candidates. A candidate is a (start, end) span in the
# document text; the model sees "[i] text" and answers with i.
import re

SHORT = 80              # characters; a longer line is prose
BLOCK_LINES = 3         # a block with more lines than this is a paragraph
HEAD, TAIL = 200, 60    # lines kept as candidates at either end regardless
MAX_CANDIDATES = 2500   # past this the document is not asked; it gets fixed windows and a flag


def line_spans(text):
    spans, start = [], 0
    for line in text.split("\n"):
        spans.append((start, start + len(line)))
        start += len(line) + 1
    return spans


def candidates(text):
    has_lines = text.count("\n") >= len(text) / 500
    if not has_lines:
        return [(m.start(), m.end()) for m in re.finditer(r"[^.!?]+[.!?]*", text)
                if m.end() - m.start() <= SHORT and len(m.group().split()) >= 2]
    spans = line_spans(text)
    out, block = [], []
    for i, (s, e) in enumerate(spans + [(len(text), len(text))]):
        edge = i < HEAD or i >= len(spans) - TAIL
        if text[s:e].strip() and i < len(spans):
            block.append((s, e))
            if edge and e - s <= SHORT:
                out.append((s, e))
            continue
        if block and len(block) <= BLOCK_LINES and all(b - a <= SHORT for a, b in block) and block[0] not in out:
            out.append(block[0])
        block = []
    return sorted(set(out))


def listing(text, cands):
    return "\n".join(f"[{i}] {' '.join(text[s:e].split())}" for i, (s, e) in enumerate(cands))


for path in [RAW / "oz" / "01_55.txt", RAW / "greek" / "03_348.txt", RAW / "graphrag-bench" / "Novel-30752.txt",
             PAPERS / "edge2024-graphrag.pdf"]:
    d = to_text(path)
    c = candidates(d["text"])
    print(f"{path.name:<26} {len(d['text']):>9,} chars  {len(c):>5} candidates  {len(listing(d['text'], c)):>7,} chars to the model")


# %%
# Block 5: the question. One call per document. Every pointer is a number and the line's text,
# so the number can be checked and, when it is off by a few, recovered from the text.
PROMPT = """Below is a numbered list of lines from one document: every short line that stands on its own, plus the document's opening and closing lines. Prose lines are omitted. Answer with JSON only. Point at a line by its number and copy its text exactly as listed, so a program can check the number. Never invent a line.

{
  "source_class": "canonical" (a published literary or classic work), "published" (a paper, article, or report), or "authored" (a person's own notes, email, letters, drafts),
  "title": {"index": n, "text": "..."} or null,
  "author": {"index": n, "text": "..."} or null,
  "date": {"index": n, "text": "...", "iso": "YYYY" or "YYYY-MM" or "YYYY-MM-DD"} or null: the line giving the date the work was written, published, or sent; not a transcription or ebook release date,
  "contents": {"first": {"index": n, "text": "..."}, "last": {"index": n, "text": "..."}} or null: the first and last lines of the contents list, if there is one,
  "toc_count": the number of pieces the contents list gives, or null,
  "body_start": {"index": n, "text": "..."}: the first line of the work itself. Publisher notices, the contents list, and transcriber's or translator's notes are not the work; an author's own preface or introduction is,
  "end_matter_start": {"index": n, "text": "..."} or null: the first line of what follows the work (references, license, index, notes, advertisements),
  "pieces": [{"index": n, "text": "...", "title": "a short title", "date": "YYYY-MM-DD" or null}, ...]
}

Pieces are the document's own divisions: chapters, acts and scenes, sections, dated entries, poems, stories. A paper's pieces are its sections, the abstract first. Point at the line where each piece begins in the work, never at its entry in the contents list. A piece gets a date only when its own heading states one, as a diary day or a dated letter does.

%s
"""


def ask(text, cands, model=MODEL):
    return generate(PROMPT % listing(text, cands), model)


# %%
# Block 6: pieces from the answer, and the gates.
#   resolve   a pointer becomes a candidate span: its index when the text there matches, else
#             the nearest candidate within WINDOW whose text matches (counted as recovered),
#             else nothing (counted as unresolved).
#   pieces_from_reply   headings between body start and end matter, not inside the contents
#             list, sorted; the gap before the first heading is the opening piece; a piece
#             under FLOOR words is a heading with no text and folds into the next.
#   gates     count against the contents list, coverage (no piece holds most of the body),
#             every pointer resolved. A failed gate is a flag, never a drop.
#   split     candidates, one call, gates; on a flag one more call on the retry model, keeping
#             the answer with fewer flags; too many candidates means fixed windows and a flag.
FLOOR = 15          # words; below it a piece is only a heading
WINDOW = 5          # candidates either side searched when an index and its text disagree
WINDOW_WORDS = 4000  # the fixed window when the model cannot be asked


def norm(s):
    return " ".join(str(s or "").split()).casefold()


def resolve(pointer, text, cands, stats):
    if not isinstance(pointer, dict):
        return None
    i, want = pointer.get("index"), norm(pointer.get("text"))
    if isinstance(i, int) and 0 <= i < len(cands) and (not want or norm(text[slice(*cands[i])]) == want):
        return cands[i]
    stats["mismatch"] += 1
    if want and isinstance(i, int):
        for j in range(max(0, i - WINDOW), min(len(cands), i + WINDOW + 1)):
            if norm(text[slice(*cands[j])]) == want:
                stats["recovered"] += 1
                return cands[j]
    stats["unresolved"] += 1
    return None


def piece(start, end, label, kind="section", author=None, occurred_at=None):
    return {"start": start, "end": end, "label": label, "kind": kind, "author": author, "occurred_at": occurred_at}


def words(text, p):
    return len(text[p["start"]:p["end"]].split())


def fold(pieces, text):
    out = []
    for p in pieces:
        if out and words(text, out[-1]) < FLOOR:
            prev = out.pop()
            p = {**p, "start": prev["start"], "label": f"{prev['label']} / {p['label']}",
                 "occurred_at": p["occurred_at"] or prev["occurred_at"]}
        out.append(p)
    if len(out) > 1 and words(text, out[-1]) < FLOOR:
        last = out.pop()
        out[-1] = {**out[-1], "end": last["end"]}
    return out


def pieces_from_reply(text, r, cands, stats):
    body = resolve(r.get("body_start"), text, cands, stats)
    end = resolve(r.get("end_matter_start"), text, cands, stats)
    body_start = body[0] if body else 0
    end_at = end[0] if end and end[0] > body_start else len(text)
    contents = r.get("contents") or {}
    first, last = resolve(contents.get("first"), text, cands, stats), resolve(contents.get("last"), text, cands, stats)
    skip = (first[0], last[1]) if first and last and last[1] > first[0] else None
    heads = {}
    for p in r.get("pieces") or []:
        span = resolve(p, text, cands, stats)
        if span is None or not (body_start <= span[0] < end_at) or (skip and skip[0] <= span[0] < skip[1]):
            continue
        heads[span[0]] = (" ".join(str(p.get("title") or text[slice(*span)]).split()), p.get("date") or None)
    starts = sorted(heads)
    pieces = []
    if not starts:
        pieces.append(piece(body_start, end_at, "whole", kind="whole"))
    elif text[body_start:starts[0]].strip():
        pieces.append(piece(body_start, starts[0], "opening", kind="opening"))
    for s, e in zip(starts, starts[1:] + [end_at]):
        label, date = heads[s]
        pieces.append(piece(s, e, label, occurred_at=date))
    return fold(pieces, text), body_start, end_at


def gates(pieces, r, body_start, end_at, stats):
    flags = []
    headed = sum(1 for p in pieces if p["kind"] == "section")
    if isinstance(r.get("toc_count"), int) and headed != r["toc_count"]:
        flags.append(f"count: {headed} pieces, contents says {r['toc_count']}")
    if len(pieces) > 1:
        share = max(p["end"] - p["start"] for p in pieces) / max(1, end_at - body_start)
        if share > 0.6:
            flags.append(f"coverage: one piece holds {share:.0%} of the body")
    if stats["unresolved"]:
        flags.append(f"{stats['unresolved']} pointer(s) matched no line")
    return flags


def windows(text):
    pieces, start, ws = [], 0, text.split()
    step = max(1, len(text) * WINDOW_WORDS // max(1, len(ws)))
    while start < len(text):
        cut = text.rfind("\n", start, start + step)
        end = len(text) if start + step >= len(text) else (cut + 1 if cut > start else start + step)
        pieces.append(piece(start, end, f"window {len(pieces) + 1}", kind="window"))
        start = end
    return pieces


def split(doc):
    """pieces, reply, flags, stats for one text or PDF document."""
    text = doc["text"]
    cands = candidates(text)
    if len(cands) > MAX_CANDIDATES:
        return windows(text), {}, [f"{len(cands)} candidates, over the cap; fixed windows"], {"candidates": len(cands)}
    best = None
    for model in (MODEL, RETRY):
        stats = {"candidates": len(cands), "mismatch": 0, "recovered": 0, "unresolved": 0, "model": model}
        r = ask(text, cands, model)
        pieces, body_start, end_at = pieces_from_reply(text, r, cands, stats)
        flags = gates(pieces, r, body_start, end_at, stats)
        if best is None or len(flags) < len(best[2]):
            best = (pieces, r, flags, stats)
        if not flags:
            break
    return best


# %%
# Block 7: units, the same way for every document. A unit is a run of consecutive pieces that
# stays under CAP_WORDS, never splits a piece, never crosses a day change when the pieces carry
# times, and a final run under TAIL_FLOOR words merges into the unit before it. A single piece
# over the cap stands alone and is counted. Chat pieces are the turns, built here from the turn
# spans block 2 kept, with the role as author and the session date as time when there is one.
from datetime import datetime

CAP_WORDS = 4000
TAIL_FLOOR = CAP_WORDS // 3


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
    """One piece per turn. The role is read back from the 'role: ' prefix block 2 wrote."""
    text = doc["text"]
    dates = [t for t in (parse_time(d) for d in doc["dates"]) if t]
    when = dates[0] if len(dates) == 1 else None
    pieces = []
    for i, (s, e) in enumerate(doc["turns"]):
        role = text[s:e].split(":", 1)[0].strip()
        pieces.append(piece(s, e, f"turn {i + 1}", kind=role, author=role, occurred_at=when))
    flags = ["ambiguous date: several session dates"] if len(dates) > 1 else []
    return pieces, flags


def day(t):
    return (t or "")[:10]


def units_from(pieces, text):
    runs, run, size = [], [], 0
    for p in pieces:
        w = words(text, p)
        new_day = bool(run) and day(p["occurred_at"]) != day(run[-1]["occurred_at"])
        if run and (size + w > CAP_WORDS or new_day):
            runs.append(run)
            run, size = [], 0
        run.append(p)
        size += w
    if run:
        same_day = runs and day(run[0]["occurred_at"]) == day(runs[-1][-1]["occurred_at"])
        if runs and size < TAIL_FLOOR and same_day:
            runs[-1].extend(run)
        else:
            runs.append(run)
    units = []
    for i, run in enumerate(runs):
        times = [p["occurred_at"] for p in run if p["occurred_at"]]
        label = run[0]["label"] if len(run) == 1 else f"{run[0]['label']} .. {run[-1]['label']}"
        units.append({"position": i, "start": run[0]["start"], "end": run[-1]["end"], "label": label,
                      "occurred_at": min(times) if times else None, "occurred_until": max(times) if times else None,
                      "pieces": len(run), "words": sum(words(text, p) for p in run)})
        for p in run:
            p["unit"] = i
    return units


# %%
# Block 8: every document in both datasets, resumable. Each finished document is appended to
# splits.jsonl as one record: path, sha256, reply, pieces, units, flags, stats, cost. On a
# rerun, clean documents are skipped and flagged ones are tried again; the last record per
# document wins. Chats need no model call. Texts and PDFs print a full entry; chats print one
# line per hundred.
SPLITS = Path("/kaggle/working/splits.jsonl")
LOG = Path("/kaggle/working/splits.log")


def read_splits():
    latest = {}
    if SPLITS.exists():
        for line in SPLITS.read_text(encoding="utf-8").split("\n"):   # never splitlines(): text can hold U+2028
            if line:
                record = json.loads(line)
                latest[record["sha256"]] = record
    return latest


def show(doc, record):
    text, r, pieces, units = doc["text"], record["reply"], record["pieces"], record["units"]
    st = record["stats"]
    lines = [f"{Path(record['path']).name}  {'FLAGGED' if record['flags'] else 'ok'}  pieces {len(pieces)}  units {len(units)}"
             f"  candidates {st.get('candidates')}  mismatch {st.get('mismatch', 0)} recovered {st.get('recovered', 0)}"
             f"  model {st.get('model', '-')}  ${record['cost']:.3f}",
             f"    class {r.get('source_class')} | title {(r.get('title') or {}).get('text')!r}"
             f" | author {(r.get('author') or {}).get('text')!r} | date {(r.get('date') or {}).get('iso')}"
             f" | body {pieces[0]['start']}-{pieces[-1]['end']} of {len(text)} | toc {r.get('toc_count')}"]
    for p in pieces:
        snippet = " ".join(text[p["start"]:p["start"] + 90].split())[:60]
        lines.append(f"    {p['start']:>8} {words(text, p):>6} w  u{p.get('unit', 0):<3} {p['occurred_at'] or '-':<12} {p['label'][:40]:<40} | {snippet}")
    lines += [f"    FLAG {f}" for f in record["flags"]]
    entry = "\n".join(lines) + "\n"
    print(entry)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")


paths = sorted(RAW.glob("oz/*.txt")) + sorted(RAW.glob("holmes/*.txt")) + sorted(RAW.glob("greek/*.txt")) \
      + sorted(RAW.glob("graphrag-bench/*.txt")) + sorted(PAPERS.glob("*.pdf")) + sorted(RAW.glob("longmemeval/*.json"))
latest = read_splits()
done = {sha for sha, rec in latest.items() if not rec["flags"]}
chats = 0
for path in paths:
    doc = to_text(path)
    if doc["sha256"] in done:
        continue
    before = spend()
    try:
        if doc["kind"] == "chat":
            pieces, flags = chat_pieces(doc)
            reply, stats = {}, {"candidates": None}
        else:
            pieces, reply, flags, stats = split(doc)
        units = units_from(pieces, doc["text"])
    except Exception as e:                       # one document must not end a two-hour run
        pieces = [piece(0, len(doc["text"]), "whole document", kind="whole")]
        units, reply, stats = units_from(pieces, doc["text"]), {}, {}
        flags = [f"run error: {type(e).__name__}: {str(e)[:200]}"]
    record = {"path": str(path), "sha256": doc["sha256"], "kind": doc["kind"], "reply": reply, "pieces": pieces,
              "units": units, "flags": flags, "stats": stats, "cost": round(spend() - before, 4)}
    with SPLITS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    done.add(doc["sha256"])
    if doc["kind"] == "chat":
        chats += 1
        if flags or chats % 100 == 0:
            print(f"{path.name}  {'FLAGGED ' + '; '.join(flags) if flags else 'ok'}  turns {len(pieces)}  units {len(units)}  ({chats} chats so far)")
    else:
        show(doc, record)
print(f"{len(done)} documents in {SPLITS.name}, ${spend():.2f} spent this session")


# %%
# Block 9: export in the schema, plus the receipt. Last record per document wins.
#   documents.jsonl  doc_id, source_uri, sha256, title, author, source_class, text, ingested_at,
#                    occurred_at, loader, flags
#   units.jsonl      unit_id, doc_id, position, label, start, end, occurred_at, occurred_until
#   pieces.jsonl     the piece table of SCHEMA.md: doc_id, unit_id, position, kind, start, end,
#                    author, occurred_at
#   receipt.json     counts by kind, flags by kind, unknown authors, ambiguous dates, pointer
#                    mismatches and recoveries, over-cap units, boilerplate share, cost
from datetime import timezone

OUT = Path("/kaggle/working/export")
OUT.mkdir(parents=True, exist_ok=True)
LOADER = "factledger-extractor 0.2"
NOW = datetime.now(timezone.utc).isoformat(timespec="seconds")
SOURCE_CLASS = {"chat": "record", "pdf": "published"}    # text documents take the model's answer


def unit_id(doc_id, text, start, end):
    return hashlib.sha256(f"{doc_id}\n{text[start:end]}".encode("utf-8")).hexdigest()


latest = read_splits()
receipt = {"documents": 0, "units": 0, "pieces": 0, "by_kind": {}, "flags_by_kind": {}, "flagged": [],
           "unknown_author": 0, "ambiguous_date": 0, "mismatch": 0, "recovered": 0, "unresolved": 0,
           "over_cap_units": 0, "boilerplate_chars": 0, "total_chars": 0,
           "cost": round(sum(r["cost"] for r in latest.values()), 3)}
files = {name: (OUT / f"{name}.jsonl").open("w", encoding="utf-8") for name in ("documents", "units", "pieces")}

for record in latest.values():
    path = Path(record["path"])
    doc = to_text(path)
    text, doc_id, r = doc["text"], doc["sha256"], record["reply"]
    rel = f"{RAW.name}/{path.relative_to(RAW).as_posix()}" if RAW in path.parents else f"{PAPERS.name}/{path.name}"
    title = (r.get("title") or {}).get("text")
    author = (r.get("author") or {}).get("text")
    occurred = (r.get("date") or {}).get("iso")
    if doc["kind"] == "chat":
        dates = [t for t in (parse_time(d) for d in doc["dates"]) if t]
        occurred = dates[0] if len(dates) == 1 else None
    source_class = SOURCE_CLASS.get(doc["kind"], r.get("source_class"))
    flags = list(record["flags"])
    if source_class is None:
        flags.append("source_class unknown")
    files["documents"].write(json.dumps({"doc_id": doc_id, "source_uri": rel, "sha256": doc_id, "title": title,
                                         "author": author, "source_class": source_class, "text": text, "ingested_at": NOW,
                                         "occurred_at": occurred, "loader": LOADER, "flags": flags}, ensure_ascii=False) + "\n")
    ids = []
    for u in record["units"]:
        uid = unit_id(doc_id, text, u["start"], u["end"])
        ids.append(uid)
        assert text[u["start"]:u["end"]].strip(), (rel, u)          # round trip: every unit is a real slice
        files["units"].write(json.dumps({"unit_id": uid, "doc_id": doc_id, "position": u["position"], "label": u["label"],
                                         "start": u["start"], "end": u["end"], "occurred_at": u["occurred_at"],
                                         "occurred_until": u["occurred_until"]}, ensure_ascii=False) + "\n")
        receipt["over_cap_units"] += u["words"] > CAP_WORDS
    for position, p in enumerate(record["pieces"]):
        files["pieces"].write(json.dumps({"doc_id": doc_id, "unit_id": ids[p.get("unit", 0)], "position": position,
                                          "kind": p["kind"], "start": p["start"], "end": p["end"],
                                          "author": p["author"], "occurred_at": p["occurred_at"]}, ensure_ascii=False) + "\n")
    st = record["stats"]
    for key in ("mismatch", "recovered", "unresolved"):
        receipt[key] += st.get(key, 0)
    receipt["documents"] += 1
    receipt["units"] += len(record["units"])
    receipt["pieces"] += len(record["pieces"])
    receipt["by_kind"][doc["kind"]] = receipt["by_kind"].get(doc["kind"], 0) + 1
    receipt["unknown_author"] += author is None and doc["kind"] != "chat"
    receipt["ambiguous_date"] += any(f.startswith("ambiguous date") for f in flags)
    receipt["total_chars"] += len(text)
    receipt["boilerplate_chars"] += record["pieces"][0]["start"] + (len(text) - record["pieces"][-1]["end"])
    for f in flags:
        kind = f.split(":")[0]
        receipt["flags_by_kind"][kind] = receipt["flags_by_kind"].get(kind, 0) + 1
    if flags:
        receipt["flagged"].append({"source_uri": rel, "flags": flags})

for f in files.values():
    f.close()
receipt["boilerplate_share"] = round(receipt["boilerplate_chars"] / max(1, receipt["total_chars"]), 4)
(OUT / "receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"documents {receipt['documents']}  units {receipt['units']}  pieces {receipt['pieces']}  by kind {receipt['by_kind']}")
print(f"pointers: mismatch {receipt['mismatch']}  recovered {receipt['recovered']}  unresolved {receipt['unresolved']}")
print(f"flagged {len(receipt['flagged'])} {receipt['flags_by_kind']}  unknown author {receipt['unknown_author']}"
      f"  ambiguous date {receipt['ambiguous_date']}  over-cap units {receipt['over_cap_units']}"
      f"  boilerplate {receipt['boilerplate_share']:.1%}  model cost ${receipt['cost']:.2f}")
for entry in receipt["flagged"]:
    if "longmemeval/" not in entry["source_uri"]:
        print(f"    {entry['source_uri']}: {entry['flags']}")
