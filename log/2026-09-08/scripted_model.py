"""The scripted model the offline checks drive the ingestor with: no network. It reads the unit
text out of each prompt and answers with real substrings, plus the bad answers the gates must
catch (a paraphrase, an invented quote, an unlisted subject, a duplicate, a loose citation, a
fact its passage does not state, a correction that says nothing). Shared by test_ingestor.py
and diff_ingestor.py. `load(path, out)` execs a notebook script into a namespace."""
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
os.environ.setdefault("EXPORT", str(ROOT / "data" / "export"))
os.environ["OPENAI_API_KEY"] = "test-key-never-sent"
os.environ["WORKERS"] = "1"                     # one at a time, so the scripted replies land in a fixed order
sys.stdout.reconfigure(encoding="utf-8")

CAP = re.compile(r"(?<![\w'’])([A-Z][a-z]{2,})(?![\w'’])")
STOP = {"The", "And", "But", "She", "His", "Her", "They", "Then", "When", "There", "This", "That", "With", "For", "Not", "You", "Now", "How", "Oh", "Yes", "What", "Why", "Who", "All"}


def load(path, out):
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    os.environ["OUT"] = str(out)
    src = Path(path).read_text(encoding="utf-8")
    cells = src.split("\n# %%\n")
    block = {int(m.group(1)): c for c in cells for m in [re.search(r"^# Block (\d+):", c, re.M)] if m}
    ns = {"__name__": "ingestor_under_test"}
    for b in sorted(block):
        exec(block[b], ns)
    ns["WATCH"] = False
    return ns


def unit_text_of(prompt):
    m = re.match(r"TEXT \((.*?)\):\n(.*?)\n\nAbove is one unit", prompt, re.S)
    return m.group(2) if m else None


def first_sentence_with(text, name):
    for m in re.finditer(r"[^.!?\n]*\b" + re.escape(name) + r"\b[^.!?\n]*[.!?]?", text):
        s = m.group(0).strip()
        if 20 < len(s) < 300:
            return s
    return None


def make_stub(ns):
    def stub_generate(prompt, schema, stage, model=None, effort="low", ctx=None):
        ns["log_call"]({"stage": stage, "model": model or "stub", "in": len(prompt) // 4, "out": 50, "seconds": 0.0, "cost": 0.001, **(ctx or {})})
        text = unit_text_of(prompt)
        if stage == "entities":
            if len(text.split()) < 20:
                return {"entities": []}
            counts = {}
            for w in CAP.findall(text):
                if w not in STOP:
                    counts[w] = counts.get(w, 0) + 1
            names = sorted(counts, key=lambda w: -counts[w])[:6]
            unnamed = len(text) % 3 == 0
            ents = [{"name": n, "named": (not unnamed) and i < len(names) - 1, "kind": "person" if i % 2 else "character",
                     "salience": "major" if i < 3 else "minor", "surface_forms": [n],
                     "profile": {"gender": "female" if n == "Dorothy" else None, "animacy": "animate", "role": None}} for i, n in enumerate(names)]
            ents.append({"name": "Phantom", "named": True, "kind": "person", "surface_forms": ["Zzyzx Qwerty"], "profile": None})
            if names:
                ents.append({"name": "Shadow", "named": True, "kind": "person", "surface_forms": [names[0]], "profile": None})
                ents.append({"name": f"hat ({names[0]}'s hat)", "named": False, "kind": "object", "surface_forms": ["hat"], "profile": None})
            return {"entities": ents}
        if stage == "facts":
            names = re.search(r"ENTITIES: (.*)", prompt).group(1).split(", ")
            facts = []
            for n in names:
                q = first_sentence_with(text, n)
                if q:
                    facts.append({"subject": n, "predicate": "is_a", "object": "character", "qualifiers": None, "quote": q, "valid_from": None, "valid_to": None})
            if len(names) > 3:
                q = first_sentence_with(text, names[3])
                if q:
                    facts.append({"subject": names[3], "predicate": "knows", "object": names[0], "qualifiers": None, "quote": q, "valid_from": None, "valid_to": None})
            if len(names) > 1:
                q = first_sentence_with(text, names[1])
                if q:
                    facts.append({"subject": names[0], "predicate": "is_a", "object": names[1], "qualifiers": None, "quote": q, "valid_from": None, "valid_to": None})
            m = re.search(r"^user: (.{30,120}?)(?=[.!?\n])", text, re.M)
            if m and facts:
                facts.append({"subject": facts[0]["subject"], "predicate": "asked_about", "object": "something", "qualifiers": None, "quote": m.group(1), "valid_from": None, "valid_to": None})
            turns = [ln for ln in text.split("\n") if ln.startswith(("user: ", "assistant: "))]
            if len(turns) >= 2 and facts:
                first, second = turns[0].split(": ", 1)[1].split(), turns[1].split(": ", 1)[1].split()
                head = text.index(turns[0]) + len(turns[0]) - len(" ".join(first[-3:]))
                tail = text.index(turns[1]) + len(turns[1].split(": ", 1)[0]) + 2 + len(" ".join(second[:3]))
                facts.append({"subject": facts[0]["subject"], "predicate": "spans", "object": "two voices", "qualifiers": None,
                              "quote": text[head:tail], "valid_from": None, "valid_to": None})
            if facts:
                good = facts[0]["quote"]
                n0 = facts[0]["subject"]
                words = good.split()
                facts += [
                    {"subject": n0, "predicate": "Has Trait", "object": "brave", "qualifiers": "at times", "quote": re.sub(r" ", "  ", good, count=2), "valid_from": "1900", "valid_to": None},
                    {"subject": n0, "predicate": "lives_in", "object": "Kansas", "qualifiers": None, "quote": good.replace("'", "’").swapcase(), "valid_from": None, "valid_to": None},
                    {"subject": n0, "predicate": "says", "object": "hello", "qualifiers": None, "quote": " ".join(words[:-2]) + " something else entirely", "valid_from": None, "valid_to": None},
                    {"subject": n0, "predicate": "eats", "object": "cake", "qualifiers": None, "quote": "the purple giraffe danced on the moon tonight", "valid_from": None, "valid_to": None},
                    {"subject": "Nobody Listed", "predicate": "is_a", "object": "ghost", "qualifiers": None, "quote": good, "valid_from": None, "valid_to": None},
                    {"subject": n0, "predicate": "is_a", "object": "Character", "qualifiers": None, "quote": good, "valid_from": None, "valid_to": None},
                    {"subject": "The " + n0.upper(), "predicate": "is_called", "object": "loudly", "qualifiers": None, "quote": good, "valid_from": None, "valid_to": None},
                    {"subject": n0, "predicate": "is_quoted_as", "object": "wrapped", "qualifiers": None, "quote": "“" + good + "”", "valid_from": None, "valid_to": None},
                    {"subject": n0, "predicate": "self", "object": n0, "qualifiers": None, "quote": good, "valid_from": None, "valid_to": None},
                ]
                if len(words) >= 6:
                    facts.append({"subject": n0, "predicate": "is_cited_with", "object": "an ellipsis", "qualifiers": None,
                                  "quote": " ".join(words[:2]) + " ... " + " ".join(words[-2:]), "valid_from": None, "valid_to": None})
                if len(words) >= 8:
                    loose = " ".join(words[1:] + ["zzz"])
                    middle = " ".join(words[:3] + ["zzz"] + words[3:])
                    facts.append({"subject": n0, "predicate": "is_cited_loosely", "object": "with an invented middle", "qualifiers": None, "quote": middle, "valid_from": None, "valid_to": None})
                    facts.append({"subject": n0, "predicate": "is_cited_loosely", "object": "and supported", "qualifiers": None, "quote": loose, "valid_from": None, "valid_to": None})
                    facts.append({"subject": n0, "predicate": "is_cited_loosely", "object": "an unsupported claim", "qualifiers": None, "quote": loose, "valid_from": None, "valid_to": None})
                    facts.append({"subject": n0, "predicate": "cannot_be_fixed", "object": "an unfixable claim", "qualifiers": None, "quote": loose, "valid_from": None, "valid_to": None})
                    facts.append({"subject": n0, "predicate": "is_cited_well", "object": "wrongly flagged", "qualifiers": None, "quote": loose, "valid_from": None, "valid_to": None})
                    facts.append({"subject": n0, "predicate": "fails_twice", "object": "a claim the third look rejects", "qualifiers": None, "quote": loose, "valid_from": None, "valid_to": None})
                    facts.append({"subject": n0, "predicate": "restate_me", "object": "restate me", "qualifiers": None, "quote": loose, "valid_from": None, "valid_to": None})
                if len(names) > 4 and len(words) >= 8:
                    facts.append({"subject": names[-1], "predicate": "is_cited_loosely_toward", "object": n0, "qualifiers": None,
                                  "quote": loose, "valid_from": None, "valid_to": None})
            return {"facts": facts}
        if stage == "cells":
            names = re.search(r"ENTITIES: (.*)", prompt).group(1).split(", ")
            return {"summary": f"This unit concerns {', '.join(names[:3])}. Things happen.",
                    "cells": [{"entity": n, "text": f"{n} appears and acts in this unit."} for n in names] + [{"entity": "Stranger", "text": "not listed"}]}
        if stage == "judge":
            pairs = re.findall(r"PAIR (\d+): \[(\d+)\] and \[(\d+)\]", prompt)
            dossiers = dict(re.findall(r"\[(\d+)\]\nnames: (.*)", prompt))
            out = []
            for n, a, b in pairs:
                same = bool(set(dossiers[a].split(", ")) & set(dossiers[b].split(", ")))
                verdict = "same" if same else "different"
                if "Toto" in dossiers[a] or "Toto" in dossiers[b]:
                    verdict = "unsure"
                out.append({"pair": int(n), "verdict": verdict, "reason": "stub"})
            return {"verdicts": out}
        if stage == "triage":
            kinds = re.findall(r"^KIND ([^:]+):", prompt, re.M)
            return {"exclude": [{"kind": k, "reason": "not the work"} for k in kinds if k in ("license", "front_matter", "references")]}
        if stage in ("support", "verify"):
            listing = prompt.split("FACTS:\n", 1)[1]
            words = ("an unsupported claim", "an unfixable claim", "is_cited_loosely_toward", "wrongly flagged", "fails_twice", "restate_me")
            if stage == "verify":
                words = ("fails_twice",)
            return {"unsupported": [int(k) for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M) if any(w in line for w in words)]}
        if stage == "correct":
            listing = prompt.split("STATEMENTS:" + chr(10), 1)[1]
            out = []
            for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M):
                if "is_cited_loosely_toward" in line or "an unsupported claim" in line:
                    out.append({"number": f"{k}.", "verdict": "corrected", "predicate": "is_cited_loosely", "object": "a corrected claim", "qualifiers": None})
                elif "an unfixable claim" in line:
                    out.append({"fact": int(k), "verdict": "drop"})
                elif "restate_me" in line:
                    out.append({"number": int(k), "verdict": "corrected", "predicate": "restate_me", "object": "restate_me"})
                elif "fails_twice" in line:
                    out.append({"number": int(k), "verdict": "corrected", "predicate": "fails_twice", "object": "a reworded claim"})
                else:
                    out.append({"number": int(k), "verdict": "stands"})
            return {"corrections": out}
        if stage == "adjudicate":
            listing = prompt.split("FACTS:\n", 1)[1].split("\nCELLS:")[0]
            n = len(re.findall(r"^\d+\. ", listing, re.M))
            unsupported = [int(k) for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M)
                           if "an unsupported claim" in line or "wrongly flagged" in line or "is_cited_loosely_toward" in line
                           or "an unfixable claim" in line or "fails_twice" in line or "restate_me" in line]
            doomed = [int(k) for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M) if "an unfixable claim" in line]
            return {"facts": [{"predicate": "is_a", "object": "character", "qualifiers": None, "from": [1]},
                              {"predicate": "lives_in", "object": "Kansas", "qualifiers": None, "from": [1, 2]},
                              *[{"predicate": f"trait_{k}", "object": "some", "qualifiers": None, "from": [1]} for k in range(min(n // 3, 20))],
                              {"predicate": "bogus", "object": "nothing", "qualifiers": None, "from": [999]},
                              *([{"predicate": "rests_on_a_doomed_fact", "object": "x", "qualifiers": None, "from": doomed[:1]}] if doomed else [])],
                    "attributes": [{"attribute": "kind", "value": "character", "from": list(range(1, min(n, 3) + 1))},
                                   {"attribute": "standing alone", "value": None, "from": [1]}],
                    "contradictions": ([{"note": "two homes", "from": [1, 2], "holds": 2, "because": "the later unit"},
                                        {"note": "out of range", "from": [1, 2], "holds": 999, "because": "nonsense"}]
                                       + ([{"note": "holds a doomed fact", "from": [1, doomed[0]], "holds": doomed[0], "because": "x"}] if doomed else [])
                                       if n >= 2 else []),
                    "unsupported": unsupported}
        if stage in ("fold", "entity_abstract"):
            records = prompt.split("RECORDS:\n", 1)[1]
            names = sorted(set(CAP.findall(records)) - STOP)[:5]
            summary = f"A record of {', '.join(names)}."
            if stage == "entity_abstract":
                return {"summary": summary, "kind": "PERSON "}
            return {"summary": summary}
        raise AssertionError(stage)
    return stub_generate


def chat_doc(ns, old):
    """A synthetic chat session: a header unit and one body unit of three turns by two speakers."""
    header = "session abc123\n"
    turns = [("user", "Dorothy asked Toto about the Scarecrow and the Lion who lives in Kansas with Glinda today."),
             ("assistant", "The Scarecrow told Dorothy that the Lion lives near the Emerald City with Toto and Glinda."),
             ("user", "Dorothy thanked the Scarecrow and walked with Toto toward Glinda and the Lion again.")]
    text, pieces, at = header, [{"doc_id": "chat", "unit_id": "u0", "position": 0, "kind": "front_matter", "start": 0, "end": len(header), "author": None, "occurred_at": None}], len(header)
    for n, (who, said) in enumerate(turns, 1):
        line = f"{who}: {said}\n"
        pieces.append({"doc_id": "chat", "unit_id": "u1", "position": n, "kind": "turn", "start": at, "end": at + len(line), "author": who, "occurred_at": "2024-01-02"})
        text += line
        at += len(line)
    units = [{"unit_id": "u0", "doc_id": "chat", "position": 0, "label": "session id", "start": 0, "end": len(header), "occurred_at": "2024-01-02", "occurred_until": "2024-01-02"},
             {"unit_id": "u1", "doc_id": "chat", "position": 1, "label": "turns 1-3", "start": len(header), "end": len(text), "occurred_at": "2024-01-02", "occurred_until": "2024-01-02"}]
    doc = {"doc_id": "chat0123456789", "source_uri": "raw/longmemeval/abc123.json", "sha256": "x", "title": None, "author": None, "source_class": "chat",
           "ingested_at": "2026-09-08", "occurred_at": "2024-01-02", "loader": "chat", "flags": [], "text": text, "units": units, "pieces": pieces, "text_rebuilt": False}
    if not old:
        for u in doc["units"]:
            u["kind"] = ns["unit_kind"](pieces, u)
    return doc


def run_one(ns, uri, old):
    if uri == "chat":
        doc = chat_doc(ns, old)
    elif old:
        doc = ns["load_document"](uri, ns["BY_URI"], ns["UNITS"], ns["PIECES"])
    else:
        doc = ns["load_document"](uri)
    path, counts, stats, records, entities, folded = ns["ingest"](doc)
    rows = [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    return rows, counts, stats

