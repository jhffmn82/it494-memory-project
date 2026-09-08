"""Offline checks for the ingestor: no network. The model is a script that reads the unit text
and answers with real substrings, plus the bad answers the gate must catch. Run from the
repository root with the export in data/export.

    python log/2026-09-06/test_ingestor.py

Every check prints PASS or FAIL; the last line counts them.
"""
import json
import os
import time
import re
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(".").resolve()
SCR = Path(os.environ.get("SCR") or (ROOT / "data" / "packages-test"))
shutil.rmtree(SCR, ignore_errors=True)
SCR.mkdir(parents=True)
os.environ["OUT"] = str(SCR)
os.environ.setdefault("EXPORT", str(ROOT / "data" / "export"))
os.environ["OPENAI_API_KEY"] = "test-key-never-sent"        # nothing is sent: the calls are stubbed

src = Path("notebooks/factledger-ingestor.py").read_text(encoding="utf-8")
cells = src.split("\n# %%\n")
block = {int(m.group(1)): c for c in cells for m in [re.search(r"^# Block (\d+):", c, re.M)] if m}
ns = {"__name__": "ingestor_under_test"}
for b in sorted(block):
    exec(block[b], ns)

results = []


def check(name, ok, detail=""):
    ok = bool(ok)
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


# ---------------------------------------------------------------- the scripted model
CAP = re.compile(r"(?<![\w'’])([A-Z][a-z]{2,})(?![\w'’])")
STOP = {"The", "And", "But", "She", "His", "Her", "They", "Then", "When", "There", "This", "That", "With", "For", "Not", "You", "Now", "How", "Oh", "Yes", "What", "Why", "Who", "All"}
script = {"bad_fold": 0, "judge": "by_name", "stop_at": None}


def unit_text_of(prompt):
    m = re.match(r"TEXT \((.*?)\):\n(.*?)\n\nAbove is one unit", prompt, re.S)
    return m.group(2) if m else None


def first_sentence_with(text, name):
    for m in re.finditer(r"[^.!?\n]*\b" + re.escape(name) + r"\b[^.!?\n]*[.!?]?", text):
        s = m.group(0).strip()
        if 20 < len(s) < 300:
            return s
    return None


def stub_generate(prompt, schema, stage, model=None, effort="low", ctx=None):
    if script["stop_at"] is not None and len(ns["CALLS"]) >= script["stop_at"]:
        raise ns["SpendStop"]("test stop")
    if script.get("stop_at_unit") is not None and (ctx or {}).get("unit") == script["stop_at_unit"]:
        raise ns["SpendStop"]("test stop at a unit")
    if script.get("stop_in_adjudication") and stage == "adjudicate":
        script["adjudications_seen"] = script.get("adjudications_seen", 0) + 1
        if script["adjudications_seen"] >= 2:
            raise ns["SpendStop"]("test stop inside the adjudication")
    ns["log_call"]({"stage": stage, "model": model or "stub", "in": len(prompt) // 4, "out": 50, "seconds": 0.0, "cost": 0.001, **(ctx or {})})
    text = unit_text_of(prompt)
    if stage == "entities":
        if len(text.split()) < 20:                              # a chat header: nothing to name, as the model would find
            return {"entities": []}
        counts = {}
        for w in CAP.findall(text):
            if w not in STOP:
                counts[w] = counts.get(w, 0) + 1
        names = sorted(counts, key=lambda w: -counts[w])[:6]
        unnamed = len(text) % 3 == 0                               # every third unit's entities are unnamed: nothing unites on sight, the judge is exercised
        ents = [{"name": n, "named": (not unnamed) and i < len(names) - 1,      # the last is never named: it stays a minor, so it can state an inverse fact (P1b)
                 "kind": "person", "salience": "major" if i < 3 else "minor", "surface_forms": [n],
                 "profile": {"gender": "female" if n == "Dorothy" else None, "animacy": "animate", "role": None}} for i, n in enumerate(names)]
        ents.append({"name": "Phantom", "named": True, "kind": "person", "surface_forms": ["Zzyzx Qwerty"], "profile": None})
        if names:                                                   # every span of this one is already the first entity's
            ents.append({"name": "Shadow", "named": True, "kind": "person", "surface_forms": [names[0]], "profile": None})
        return {"entities": ents}
    if stage == "facts":
        names = re.search(r"ENTITIES: (.*)", prompt).group(1).split(", ")
        facts = []
        for n in names:
            q = first_sentence_with(text, n)
            if q:
                facts.append({"subject": n, "predicate": "is_a", "object": "character", "qualifiers": None, "quote": q, "valid_from": None, "valid_to": None})
        if len(names) > 3:                                                 # a minor's fact about a major: lands on the major, inverse
            q = first_sentence_with(text, names[3])
            if q:
                facts.append({"subject": names[3], "predicate": "knows", "object": names[0], "qualifiers": None, "quote": q, "valid_from": None, "valid_to": None})
        m = re.search(r"^user: (.{30,120}?)(?=[.!?\n])", text, re.M)       # a chat: one fact must come from the user's own turn
        if m and facts:
            facts.append({"subject": facts[0]["subject"], "predicate": "asked_about", "object": "something", "qualifiers": None, "quote": m.group(1), "valid_from": None, "valid_to": None})
        turns = [ln for ln in text.split("\n") if ln.startswith(("user: ", "assistant: "))]
        if len(turns) >= 2 and facts:                                      # a quote whose pieces lie in two turns: one fact per voice (decision 46)
            first, second = turns[0].split(": ", 1)[1].split(), turns[1].split(": ", 1)[1].split()
            if len(first) >= 3 and len(second) >= 3:
                facts.append({"subject": facts[0]["subject"], "predicate": "spans", "object": "two voices", "qualifiers": None,
                              "quote": " ".join(first[:3]) + " ... " + " ".join(second[:3]), "valid_from": None, "valid_to": None})
        if facts:
            good = facts[0]["quote"]
            n0 = facts[0]["subject"]
            words = good.split()
            facts += [
                {"subject": n0, "predicate": "Has Trait", "object": "brave", "qualifiers": "at times", "quote": re.sub(r" ", "  ", good, count=2), "valid_from": "1900", "valid_to": None},   # whitespace
                {"subject": n0, "predicate": "lives_in", "object": "Kansas", "qualifiers": None, "quote": good.replace("'", "’").swapcase(), "valid_from": None, "valid_to": None},   # normalisation
                {"subject": n0, "predicate": "says", "object": "hello", "qualifiers": None, "quote": " ".join(words[:-2]) + " something else entirely", "valid_from": None, "valid_to": None},   # paraphrase
                {"subject": n0, "predicate": "eats", "object": "cake", "qualifiers": None, "quote": "the purple giraffe danced on the moon tonight", "valid_from": None, "valid_to": None},   # not found
                {"subject": "Nobody Listed", "predicate": "is_a", "object": "ghost", "qualifiers": None, "quote": good, "valid_from": None, "valid_to": None},   # unlisted subject
                {"subject": n0, "predicate": "is_a", "object": "Character", "qualifiers": None, "quote": good, "valid_from": None, "valid_to": None},   # duplicate
                {"subject": "The " + n0.upper(), "predicate": "is_called", "object": "loudly", "qualifiers": None, "quote": good, "valid_from": None, "valid_to": None},   # the listed name, written loosely
                {"subject": n0, "predicate": "is_quoted_as", "object": "wrapped", "qualifiers": None, "quote": "“" + good + "”", "valid_from": None, "valid_to": None},   # the model's own quotation marks
            ]
            if len(words) >= 6:
                facts.append({"subject": n0, "predicate": "is_cited_with", "object": "an ellipsis", "qualifiers": None,
                              "quote": " ".join(words[:2]) + " ... " + " ".join(words[-2:]), "valid_from": None, "valid_to": None})   # two verbatim pieces
            if len(words) >= 8:
                loose = " ".join(words[1:] + ["zzz"])                                                # the first word dropped, one added at the end: found by its words
                middle = " ".join(words[:3] + ["zzz"] + words[3:])                                  # a word invented inside the run: refused (decision 47)
                facts.append({"subject": n0, "predicate": "is_cited_loosely", "object": "with an invented middle", "qualifiers": None, "quote": middle, "valid_from": None, "valid_to": None})
                facts.append({"subject": n0, "predicate": "is_cited_loosely", "object": "and supported", "qualifiers": None, "quote": loose, "valid_from": None, "valid_to": None})
                facts.append({"subject": n0, "predicate": "is_cited_loosely", "object": "an unsupported claim", "qualifiers": None, "quote": loose, "valid_from": None, "valid_to": None})
                facts.append({"subject": n0, "predicate": "cannot_be_fixed", "object": "an unfixable claim", "qualifiers": None, "quote": loose, "valid_from": None, "valid_to": None})   # flagged, and the correction refuses it: dumped
            if len(names) > 4 and len(words) >= 8:
                inverse_subject = names[-1]
                # a lesser thing speaking about a major: lands inverse, so its object slot holds
                # the minor's name and a correction must not be able to overwrite it (P1)
                facts.append({"subject": inverse_subject, "predicate": "is_cited_loosely_toward", "object": n0, "qualifiers": None,
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
            same = script["judge"] == "all_same" or (script["judge"] == "by_name" and set(dossiers[a].split(", ")) & set(dossiers[b].split(", ")))
            verdict = "same" if same else "different"
            if "Toto" in dossiers[a] or "Toto" in dossiers[b]:                 # the judge can never settle Toto: deferred, then judged again
                verdict = "unsure"
            out.append({"pair": int(n), "verdict": verdict, "reason": "stub"})
        return {"verdicts": out}
    if stage == "triage":                                        # leave out the kinds that are not the work
        kinds = re.findall(r"^KIND ([^:]+):", prompt, re.M)
        return {"exclude": [{"kind": k, "reason": "not the work"} for k in kinds if k in ("license", "front_matter", "references")]}
    if stage == "support":                                       # the small support-only call: the same rule as the adjudication's
        listing = prompt.split("FACTS:\n", 1)[1]
        return {"unsupported": [int(k) for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M)
                                if "an unsupported claim" in line or "an unfixable claim" in line
                                or "is_cited_loosely_toward" in line]}
    if stage == "correct":                                       # the passage is fixed; the claim moves to fit it (R3)
        listing = prompt.split("STATEMENTS:" + chr(10), 1)[1]
        out = []
        for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M):
            if "loosely" in line:                                # correctable: a real claim the passage does carry
                out.append({"fact": int(k), "subject": line.split(" is_cited_loosely")[0].split(". ", 1)[-1].strip(),
                            "predicate": "is_cited_loosely", "object": "a corrected claim", "qualifiers": None})
            elif "restate_me" in line:                           # answered, but the answer says nothing: dumped anyway
                out.append({"fact": int(k), "subject": "x", "predicate": "restate_me", "object": "restate_me", "qualifiers": None})
            # anything else is left out of the reply entirely: not correctable, so dumped
        return {"corrections": out}
    if stage == "adjudicate":
        listing = prompt.split("FACTS:\n", 1)[1].split("\nCELLS:")[0]
        n = len(re.findall(r"^\d+\. ", listing, re.M))
        unsupported = [int(k) for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M)
                       if "an unsupported claim" in line
                       or "is_cited_loosely_toward" in line          # an inverse landing: only this call sees it
                       or "an unfixable claim" in line]
        # a riding line is NOT flagged here, but the minor's own support call will condemn it, so
        # the major may cite a fact the correction pass then dumps: the pointer P2 has to clean up
        doomed = [int(k) for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M)
                  if "an unfixable claim" in line]
        return {"facts": [{"predicate": "is_a", "object": "character", "qualifiers": None, "from": [1]},
                          {"predicate": "lives_in", "object": "Kansas", "qualifiers": None, "from": [1]},
                          {"predicate": "lives_at", "object": "the farm", "qualifiers": None, "from": [1]},   # the pairwise judge folds this into lives_in
                          *[{"predicate": f"trait_{k}", "object": "some", "qualifiers": None, "from": [1]} for k in range(min(n // 3, 20))],   # a spread that grows with the facts: a book judges predicates, a chat does not
                          {"predicate": "bogus", "object": "nothing", "qualifiers": None, "from": [999]},   # points at nothing: dropped
                          *([{"predicate": "rests_on_a_doomed_fact", "object": "x", "qualifiers": None, "from": [1] + doomed[:1]}] if doomed else [])],
                "attributes": [{"attribute": "kind", "value": "character", "from": list(range(1, min(n, 3) + 1))},
                               {"attribute": "standing alone", "value": None, "from": [1]}],
                "contradictions": ([{"note": "two homes", "from": [1, 2], "holds": 2, "because": "the later unit"},
                                    {"note": "out of range", "from": [1, 2], "holds": 999, "because": "nonsense"}]
                                   + ([{"note": "holds a fact the correction will dump", "from": [1, doomed[0]],
                                        "holds": doomed[0], "because": "the one the minor condemned"}] if doomed else [])
                                   if n >= 2 else []),
                "unsupported": unsupported}
    if stage in ("fold", "entity_abstract"):
        records = prompt.split("RECORDS:\n", 1)[1]
        names = sorted(set(CAP.findall(records)) - STOP)[:5]
        if script["bad_fold"] > 0:                          # each bad answer spends one; the retry is bad too while any remain
            script["bad_fold"] -= 1
            summary = f"A tale of {', '.join(names)} and Rumpelstiltskin."
        else:
            summary = f"A record of {', '.join(names)}."
        if stage == "entity_abstract":                      # one kind for the merged entity (ruling of 09-07)
            return {"summary": summary, "kind": "PERSON "}
        return {"summary": summary}
    raise AssertionError(stage)


real_generate = ns["generate"]                                   # kept for the retry check below
ns["generate"] = stub_generate

# ---------------------------------------------------------------- unit checks of the helpers
locate, normalised, surface_spans = ns["locate"], ns["normalised"], ns["surface_spans"]
t = "The ﬁrst “quoted” line—done.\nSecond   line here."
s, e, how = locate(t, "quoted")
check("locate exact", (s, e, how) == (t.index("quoted"), t.index("quoted") + 6, "exact"))
s, e, how = locate(t, "Second line here")
check("locate across whitespace, on the normalised path", how == "normalised" and t[s:e] == "Second   line here")
s, e, how = locate(t, 'the FIRST "quoted" line-done')
check("locate through NFKC, curly quotes, dash and case, offsets in the original", how == "normalised" and t[s:e] == "The ﬁrst “quoted” line—done", repr(t[s:e] if s is not None else how))
check("locate paraphrase classified", locate(t, "Second line here today")[2] == "paraphrase")
check("locate not found classified", locate(t, "purple giraffe moon")[2] == "not_found")
check("locate empty", locate(t, "  ")[2] == "empty")
hy = "the recon-\nciliation of names is\nhard."
s, e, how = locate(hy, "reconciliation of names")
check("locate bridges a hyphenated line break and stores the original slice", how == "normalised" and hy[s:e] == "recon-\nciliation of names", repr(hy[s:e] if s is not None else how))
ell = "Quelala was a boy. He was said to be the best and wisest man in all the land."
s, e, how = locate(ell, "Quelala ... the best and wisest man")
check("a quote with an ellipsis is found piece by piece and the stored quote spans the pieces", how == "pieces" and ell[s:e] == "Quelala was a boy. He was said to be the best and wisest man", repr(ell[s:e] if s is not None else how))
check("an ellipsis whose pieces are out of order is not found", locate(ell, "wisest man ... Quelala")[2] in ("paraphrase", "not_found"))
oz3 = "She bade her friends good-bye, and again started along the road of yellow brick. When she had gone several miles she thought she would stop to rest."
s, e, how = locate(oz3, "she started along the road of yellow brick.")
check("a citation reworded at its edge is found by its words and the stored quote is the text's own passage", how == "words" and oz3[s:e] == "started along the road of yellow brick", repr(oz3[s:e] if s is not None else how))
check("a citation missing too many words is not found by its words", locate(oz3, "she started along the road to the City of Emeralds today")[2] in ("paraphrase", "not_found"))
check("a bare quote is found as whole words, not inside a longer word", locate("Ozma ruled. The Wizard said he was Oz.", '"Oz"') == (35, 37, "unwrapped"))
check("a matched pair of marks comes off and the text's own apostrophe stays", locate("’Tis a fine day, said Toto.", '"’Tis a fine day"') == (0, 15, "unwrapped"))
check("a lone apostrophe at the end is the text's own and stays", locate("They crossed the Winkies’ land at noon.", "the Winkies’")[2] == "exact")
check("occurrences finds every verbatim recurrence", ns["occurrences"]("a b a b a", "a b") == [0, 4])
check("whole_word", ns["whole_word"]("her", "with her hat") and not ns["whole_word"]("her", "the heron"))
nt, back = normalised("ﬁx")
check("normalised map expands a ligature", nt == "fix" and back == [0, 0, 1])
check("surface_spans whole words only", surface_spans("Tim and Timothy and Tim.", "Tim") == [(0, 3), (20, 23)])
check("surface_spans normalised", surface_spans("the “Boy” ran", '"boy"') == [(4, 9)])
try:
    ns["check_schema"]({"facts": [{"subject": 1}]}, ns["FACT_SCHEMA"])
    check("check_schema catches a wrong type", False)
except ns["SchemaError"] as err:
    check("check_schema names the failing path", "$.facts[0]" in str(err), str(err))
check("stated_date needs the year in the quote", ns["stated_date"]("1900-05", "in 1900 he") == "1900-05" and ns["stated_date"]("1901", "in 1900 he") is None and ns["stated_date"]("soon", "x") is None)
check("staleness: a changed child changes the hash", ns["h"]("a", "b") != ns["h"]("a", "c") and ns["h"]("a", "b") == ns["h"]("a", "b"))

# ---------------------------------------------------------------- Oz book 1 through the stub
BY_URI, UNITS, PIECES = ns["BY_URI"], ns["UNITS"], ns["PIECES"]


def uri_of(suffix):
    return next(u for u in BY_URI if u.endswith(suffix))


OZ = uri_of("/oz/01_55.txt")
check("export indexed with Oz 1 present", OZ in BY_URI)
doc = ns["load_document"](OZ, BY_URI, UNITS, PIECES)
check("Oz 1 units tile in order", all(a["end"] <= b["start"] for a, b in zip(doc["units"], doc["units"][1:])) and len(doc["units"]) > 5, len(doc["units"]))
path, counts, stats, records, entities, folded = ns["ingest"](doc)
text = doc["text"]
lines = list(ns["read_jsonl"](path))
by = {}
for l in lines:
    by.setdefault(l["record"], []).append(l)
check("package written with the document first and a completion last", lines[-1]["record"] == "completion" and lines[0]["record"] == "document")
facts = by.get("fact", [])
check("facts stored", len(facts) > 0, len(facts))
check("every fact's offsets slice to exactly its quote", all(text[f["quote_start"]:f["quote_end"]] == f["quote"] for f in facts))
unit_range = {u["unit_id"]: (u["start"], u["end"]) for u in doc["units"]}
check("every quote lies inside its unit", all(unit_range[f["unit_id"]][0] <= f["quote_start"] < f["quote_end"] <= unit_range[f["unit_id"]][1] for f in facts))
check("the match paths exercised: exact, normalised, unwrapped, pieces", set(stats["matched_by"]) >= {"exact", "normalised", "unwrapped", "pieces"}, stats["matched_by"])
check("every fact's quote is the text's own words whatever path found it", all(text[f["quote_start"]:f["quote_end"]] == f["quote"] for f in facts))
unsupported_ids = {f["fact_id"] for f in facts if f["rank"] == "unsupported"}
check("a loosely cited fact is found by its words and stored, marked words", any(f["provenance"]["matched_by"] == "words" and f["object"] == "and supported" and f["rank"] == "active" for f in facts))
check("a quote with a word invented inside the run is refused, not matched by its words (decision 47)", not any(f["object"] == "with an invented middle" for f in facts) and any(r.get("object") == "with an invented middle" for r in by.get("rejection", [])))
check("no fact is written with a flag: every stored fact is active (R3)",
      facts and all(f["rank"] == "active" for f in facts))
check("a fact its passage does not state is corrected against that passage, keeping its quote (R3)",
      any(f["object"] == "a corrected claim" and f["provenance"]["corrected_from"]["object"] == "an unsupported claim" for f in facts)
      and not any(f["object"] == "an unsupported claim" for f in facts))
check("a fact that could not be corrected is dumped, not stored, and recorded as a rejection (R3)",
      lines[-1]["counts"]["facts_dumped"] > 0
      and any(r["record"] == "rejection" and r["stage"] == "verify" and r["category"] == "unsupported" for r in lines))
check("a correction that says nothing is refused and the fact dumped with it (R3)",
      not any(f["predicate"] == "restate_me" for f in facts))
check("the flagged, corrected and dumped counts agree", lines[-1]["counts"]["facts_flagged"] ==
      lines[-1]["counts"]["facts_corrected"] + lines[-1]["counts"]["facts_dumped"])
check("a fact its passage does state is left alone", any(f["object"] == "and supported" and not f["provenance"]["corrected_from"] for f in facts))
check("rejections classified: paraphrase, not_found, unlisted_subject, duplicate", set(stats["rejected_by"]) >= {"paraphrase", "not_found", "unlisted_subject", "duplicate"}, stats["rejected_by"])
check("predicate normalised to snake_case", any(f["predicate"] == "has_trait" for f in facts))
check("valid_from kept only when the quote states the year", all(f["valid_from"] is None for f in facts if "1900" not in f["quote"]))
mentions = by.get("mention", [])
check("every mention has a span that slices to its surface", mentions and all(text[m["start"]:m["end"]] == m["surface"] for m in mentions))
minor_names = {e["name"] for e in folded["minors"]}
node_ids = {n["node_id"] for n in by["node"]}
check("major mentions carry a node that exists", all(m["node_id"] in node_ids for m in mentions if m["node_id"]))
check("phantom entity dropped for no surface form", any(x["category"] == "no_surface_form" and x["name"] == "Phantom" for x in by.get("rejection", [])))
check("an entity whose every span is already claimed is dropped and the spans counted", any(x["category"] == "span_claimed" and x["name"] == "Shadow" for x in by.get("rejection", [])) and lines[-1]["counts"]["shared_spans"] > 0)
check("mention ids are unique within the package", len({m["mention_id"] for m in mentions}) == len(mentions))
check("cell ids are unique within the package", len({c["cell_id"] for c in by.get("cell", [])}) == len(by.get("cell", [])))
check("alias rows carry the verbatim form with the unit it first appeared in", by.get("alias") and all(a["first_seen_unit"] in unit_range for a in by["alias"]))
check("every call was written to calls.jsonl as it was made", (ns["OUT"] / "calls.jsonl").exists() and sum(1 for _ in ns["read_jsonl"](ns["OUT"] / "calls.jsonl")) == len(ns["CALLS"]))
check("every fact subject is a node", all(f["subject"] in node_ids for f in facts))
check("a fact to a minor keeps the minor's name as its value", all(not f["object_is_node"] for f in facts if f["object"] not in node_ids))
check("voice: every fact carries the document author for a novel", all(f["author"] == doc["author"] for f in facts), doc["author"])
cells = by.get("cell", [])
doc_node = ns["h"](doc["doc_id"], "document")
check("a unit summary cell on the document node per derived unit", sum(1 for c in cells if c["node_id"] == doc_node) == len(records))
unit_majors = {(r["unit_id"], e["name"]) for r in records for e in r["entities"] if e["major"]}
check("cells only for the unit's major entities, the model's salience call", all(all((c["unit_id"], n) in unit_majors for n in c["provenance"]["entity_names"]) for c in cells if c["node_id"] != doc_node))
abstracts = by.get("abstract", [])
doc_abs = [a for a in abstracts if a["node_id"] == doc_node]
work = [r for r in records if r["summary"]]
check("document abstract present, folded from the derived units' summaries", len(doc_abs) == 1 and doc_abs[0]["text"])
check("triage left out the front matter and the license, and those units were never derived", {x["kind"] for x in lines[-1]["excluded"]} == {"front_matter", "license"} and lines[-1]["counts"]["units_excluded"] == 2 and len(records) == len(doc["units"]) - 2 and all(r["kind"] == "body" for r in records))
check("the abstract is shorter than the summaries it folds", 0 < ns["word_count"](doc_abs[0]["text"]) <= max(400, sum(ns["word_count"](r["summary"]) for r in work)))
check("every queued pair carries the demo's tier and three separate scores", by.get("candidate") and all(c["tier"] in (1.0, 0.85, 0.5) and {"name_score", "cooc_score", "profile_score", "combined"} <= set(c) for c in by["candidate"]) and any(c["stage"] == "judge" for c in ns["CALLS"]))
check("each round's pairs are strongest first, and no entity is in two pairs of one round",
      all([(-c["tier"], -c["combined"]) for c in by["candidate"] if c["round"] == n] == sorted((-c["tier"], -c["combined"]) for c in by["candidate"] if c["round"] == n)
          for n in {c["round"] for c in by["candidate"]})
      and all(len([x for c in by["candidate"] if c["round"] == n for x in ((c["a"], c["a_unit"]), (c["b"], c["b_unit"]))])
              == len({x for c in by["candidate"] if c["round"] == n for x in ((c["a"], c["a_unit"]), (c["b"], c["b_unit"]))})
              for n in {c["round"] for c in by["candidate"]}))
check("never minor against minor in the queue", all(any(e["major"] and e["name"] in (c["a"], c["b"]) and r["position"] in (c["a_unit"], c["b_unit"]) for r in records for e in r["entities"]) for c in by["candidate"]))
check("a pair the judge could not settle was judged once more at the end", any(l["how"] == "judged again" for l in by.get("ledger", [])))
check("two named locals with the same name and kind unite on sight, no judge", any(l["how"] == "same_name" and l["verdict"] == "same" for l in by["ledger"]))
check("an object points at a node only when that node is in this package (E3, restated for R6)",
      all(f["object"] in {l["node_id"] for l in lines if l["record"] == "node"} for f in facts if f["object_is_node"]))
check("salience alone decides a major: every major is one a unit called major",
      folded["majors"] and all(e["unit_major"] for e in folded["majors"])
      and not any(e["unit_major"] for e in folded["minors"] if not e["rank"].get("no_abstract")))
check("decision 52 is the only demotion left, and it is about having no content, not about salience (P4)",
      all(not e["rank"].get("no_abstract") or e["n_facts"] == 0 for e in folded["minors"]))
inverse = [f for f in facts if f["direction"] == "inverse"]
check("a minor's fact about a major lands on the major, marked inverse, with the minor's name as its value", inverse and all(f["subject"] in node_ids and not f["object_is_node"] and f["object"] not in node_ids for f in inverse))
adjudicated = by.get("adjudicated_fact", [])
fact_ids_of = {}
for f in facts:
    fact_ids_of.setdefault(f["subject"], set()).add(f["fact_id"])
check("nothing rides: a fact is stored once, under the major it lands on (ruling of 09-07)",
      not any(f["direction"] == "about" for f in facts)
      and len({f["fact_id"] for f in facts}) == len(facts))
check("a fact between two lesser things is not stored, and the count says so", lines[-1]["counts"]["facts_no_major"] > 0)
loosely = [f for f in facts if f["predicate"] == "is_called"]
check("a subject written with another case or a leading article is the listed entity", loosely and all(not f["provenance"]["subject_name"].startswith("The ") for f in loosely))
check("a quote wrapped in the model's own quotation marks is found once they come off, and says so", any(f["provenance"]["matched_by"] == "unwrapped" and f["quote"][:1] not in "“\"" for f in facts))
check("a quote cited with an ellipsis is kept, its stored quote spanning the pieces", any(f["provenance"]["matched_by"] == "pieces" and " " in f["quote"] for f in facts))
check("adjudicated predicates are the model's own, unmerged, in snake_case", {"lives_in", "lives_at"} <= {a["predicate"] for a in adjudicated} and not any(r["record"] == "predicate_merge" for r in lines) and "predicate_raw" not in adjudicated[0])
check("no consolidated fact rests only on facts the same reply set aside; a source set aside is not cited (decision 45)",
      adjudicated and all(not (set(a["from_facts"]) & unsupported_ids) for a in adjudicated), len(unsupported_ids))
check("a flagged fact is corrected or dumped wherever it landed (C5)",
      not any(f["object"] in ("an unsupported claim", "an unfixable claim") for f in facts))
raw_by_id = {f["fact_id"]: f for f in facts}
check("a consolidated fact's sources are the raw facts it was drawn from, not any facts of the node (A17)",
      any(a["predicate"] == "is_a" for a in adjudicated)
      and all(all(raw_by_id[i]["predicate"] == "is_a" for i in a["from_facts"] if i in raw_by_id)
              for a in adjudicated if a["predicate"] == "is_a"))
check("every adjudicated fact points only at raw facts of its own node", adjudicated and all(set(a["from_facts"]) <= fact_ids_of.get(a["node_id"], set()) for a in adjudicated))
check("attributes point at raw facts too, and an item pointing at nothing was dropped and counted",
      by.get("attribute") and all(set(a["from_facts"]) <= fact_ids_of.get(a["node_id"], set()) for a in by["attribute"])
      and lines[-1]["counts"]["adjudication_dropped"] > 0)
units_by_id = {u["unit_id"]: u for u in doc["units"]}
check("an adjudicated attribute may stand without a value", any(a["value"] is None for a in by.get("attribute", [])))
check("a fact that could not be corrected is ABSENT from the fact rows, not merely recorded (P6)",
      not any(f["object"] == "an unfixable claim" for f in facts),
      [f["object"] for f in facts if f["object"] == "an unfixable claim"][:3])
stored_ids = {f["fact_id"] for f in facts}
dangling = [(r["record"], i) for r in lines if r["record"] in ("adjudicated_fact", "attribute", "contradiction")
            for i in r["from_facts"] if i not in stored_ids]
check("nothing points at a fact the package does not carry (P2)", not dangling, dangling[:3])
check("a contradiction never holds a fact the package does not carry (P2)",
      all(c["holds"] in stored_ids for c in by.get("contradiction", []) if c["holds"] is not None))
check("a contradiction the judge could not number resolves to nothing rather than to a wrong fact (R4, P7)",
      any(c["holds"] is None for c in by.get("contradiction", []))
      and any(c["holds"] is not None for c in by.get("contradiction", [])), len(by.get("contradiction", [])))
inverse_corrected = [f for f in facts if f["direction"] == "inverse" and f["provenance"]["corrected_from"]]
check("an inverse fact's object is the other entity's name, and a correction cannot overwrite it (P1)",
      inverse_corrected and all(f["object"] == f["provenance"]["subject_name"] for f in facts if f["direction"] == "inverse"),
      len(inverse_corrected))
check("a corrected fact keeps the offsets its quote was gated on (P1)",
      all(doc["text"][f["quote_start"]:f["quote_end"]] == f["quote"] for f in facts))
check("a fact carries when it was said, from its unit, beside when it is true (R2)",
      facts and all("occurred_at" in f and "occurred_until" in f for f in facts)
      and all(f["occurred_at"] == units_by_id[f["unit_id"]].get("occurred_at") for f in facts))
check("a contradiction carries the document's own resolution, and the facts it names stay active (R4)",
      all(c["holds"] in (None, *c["from_facts"]) for c in by.get("contradiction", []))
      and all(f["rank"] == "active" for f in facts))
check("support_calls counts calls, not entities (C3)",
      lines[-1]["counts"]["support_calls"] == len([c for c in ns["CALLS"] if c["stage"] == "support" and c.get("doc") == doc["source_uri"]]))
import io, contextlib
buffer = io.StringIO()
with contextlib.redirect_stdout(buffer):
    ns["rollup"](path, top=2)
printed = buffer.getvalue()
written = path.with_name("roll-up.txt").read_text(encoding="utf-8")
check("the roll-up reads a finished package back and writes it, abstract, units, majors and the audit",
      "ROLL-UP" in written and "MAJOR ENTITIES" in written and "consolidated facts" in written, written[:80])
check("the roll-up is a file beside the package, not a second copy of the log (ruling of 09-07)",
      "ROLL-UP" not in printed and "roll-up.txt" in printed and len(printed) < 200, printed[:120])

# ---------------------------------------------------------------- the 09-07 rulings
rows = list(ns["read_jsonl"](path))
kinds = [r["kind"] for r in rows if r["record"] == "node" and r["kind"] != "document"]
positions = [r["position"] for r in rows if r["record"] == "unit"]
check("the units land in reading order though they derive WORKERS at a time (ruling of 09-07)",
      positions == sorted(positions) and len(positions) > ns["WORKERS"], positions[:8])
check("a merged entity carries one kind, not the joined set (ruling of 09-07)",
      kinds and not any("/" in k for k in kinds), kinds[:4])
check("the kind the entity abstract answered is the kind stored, cased down",
      all(k == "person" for k in kinds), sorted(set(kinds)))
# an inverse fact names the other entity in "object" and in subject_name both, so it is only a
# self reference when the fact is stated forward
restating = [r for r in rows if r["record"] == "fact" and r["direction"] == "forward"
             and not r["object_is_node"]
             and str(r["object"]).strip().casefold() == r["provenance"].get("subject_name", "").strip().casefold()]
check("a fact whose object restates its subject is rejected at the gate, and says why",
      not restating or any(r["record"] == "rejection" and r["category"] == "self_reference" for r in rows),
      [(r["provenance"]["subject_name"], r["predicate"], r["object"]) for r in restating[:3]])

spent_before = ns["spend"]()
ns["start_block"](0.25)
check("a block's budget is counted from the block's start, not the session's (ruling of 09-07)",
      spent_before > 0 and ns["BLOCK_START"] == spent_before and ns["SPEND_STOP"] == 0.25,
      (spent_before, ns["BLOCK_START"], ns["SPEND_STOP"]))
check("each document keeps its own folder, named after its file, with the package inside it",
      path.parent.name == "01_55" and path.name == "01_55.jsonl" and path.parent.parent.name == "oz")
check("two entities the judge kept apart never share a node id (decision 48)",
      len({n["node_id"] for n in by["node"]}) == len(by["node"]))
check("the fact counters close: stored is what landed plus the riding copies",
      lines[-1]["counts"]["facts_kept"]
      == lines[-1]["counts"]["facts_stored"] + lines[-1]["counts"]["facts_no_major"] + lines[-1]["counts"]["facts_dumped"],
      {k: lines[-1]["counts"][k] for k in ("facts_kept", "facts_stored", "facts_no_major", "facts_dumped")})
check("an entity the document cannot summarise is not a major, and its facts ride (decision 52)",
      all(any(a["record"] == "abstract" and a["node_id"] == ns["node_id_of"](doc, e) for a in lines) for e in folded["majors"])
      and all(not e["rank"].get("no_abstract") for e in folded["majors"]))
check("a profile row carries no constant confidence (decision 62)", all("confidence" not in p for p in by.get("profile", [])))
check("ledger rows carry evidence", by.get("ledger") and all(l["evidence"] for l in by["ledger"]))
check("edges: has_unit per unit and appears_in per major", sum(1 for e in by["edge"] if e["predicate"] == "has_unit") == len(doc["units"]) and sum(1 for e in by["edge"] if e["predicate"] == "appears_in") == len(folded["majors"]))
check("completion counts consistent", lines[-1]["counts"]["facts_stored"] == len(facts) and lines[-1]["counts"]["mentions"] == len(mentions))
check("no unit saw another: no entity prompt carried a roster, no cells prompt a previous summary", not any("ESTABLISHED SO FAR" in c.get("detail", "") for c in ns["RETRIES"]) and "ESTABLISHED" not in ns["entity_prompt"]({"label": "x", "text": "y"}) and "PREVIOUS" not in ns["cells_prompt"]({"label": "x", "text": "y"}, ["a"]))

# ---------------------------------------------------------------- re-run mints nothing
before = path.read_bytes()
done, skipped = ns["run"]([OZ])
check("re-run over unchanged input is skipped by input_hash", done == 0 and skipped == 1 and path.read_bytes() == before)


def stable(p):
    out = []
    for l in ns["read_jsonl"](p):
        l.pop("written_at", None)
        l.pop("updated_at", None)
        if l["record"] == "completion":
            l["stats"].pop("calls", None)
        out.append(json.dumps(l, sort_keys=True))
    return out


path.unlink()
ns["CALLS"].clear()
path2, *_ = ns["ingest"](doc)
first = stable(path2)
path2.unlink()
path3, *_ = ns["ingest"](doc)
check("two derivations with the same answers agree line for line (ids are content hashes)", first == stable(path3))

# ---------------------------------------------------------------- a chat session: two voices in one unit
chat_uris = [u for u in BY_URI if "/longmemeval/" in u]
picked = None
for uri in chat_uris[:400]:
    d = ns["load_document"](uri, BY_URI, UNITS, PIECES)
    turns_unit = d["units"][-1]["unit_id"] if d["units"] else None
    if {"user", "assistant"} <= {p["kind"] for p in d["pieces"] if p["unit_id"] == turns_unit} and len(d["units"]) == 2 and 8 <= len(d["pieces"]) <= 14:
        picked = d
        break
check("a chat session with user and assistant turns inside one unit found (the header is the other unit)", picked is not None)
if picked:
    p, c, st, recs, ents, fd = ns["ingest"](picked)
    rows = list(ns["read_jsonl"](p))
    cf = [r for r in rows if r["record"] == "fact"]
    pieces = picked["pieces"]

    def piece_author(off):
        return next(pp["author"] for pp in pieces if pp["start"] <= off < pp["end"])
    check("chat: every fact's author is the author of the piece holding its quote, or null when the same words occur in two voices",
          cf and all(f["author"] == piece_author(f["quote_start"]) or (f["author"] is None and f["provenance"]["voice_ambiguous"]) for f in cf))
    check("chat: facts from both voices, user and assistant", {f["author"] for f in cf} >= {"user", "assistant"}, {f["author"] for f in cf})
    check("chat: no fact's quote spans two voices, its last character answering to the same speaker as its first",
          cf and all(piece_author(f["quote_start"]) == piece_author(f["quote_end"] - 1) for f in cf))
    check("chat: a quote whose pieces lie in two turns is stored once per voice, each with that voice's words (decision 46)",
          len([f for f in cf if f["object"] == "two voices"]) == 2
          and {f["author"] for f in cf if f["object"] == "two voices"} == {"user", "assistant"}
          and rows[-1]["counts"]["facts_split_by_voice"] == 1)
    check("chat: triage leaves out the header unit, the turns unit's summary is the abstract, no fold call",
          rows[-1]["counts"]["units_excluded"] == 1 and rows[-1]["counts"]["units"] == 1
          and any(r["record"] == "abstract" and r["node_id"] == ns["h"](picked["doc_id"], "document") for r in rows)
          and not any(cc["stage"] == "fold" for cc in ns["CALLS"] if cc.get("doc") == picked["source_uri"]))
    check("chat: a major with fewer than four facts is not consolidated, but its passages are still read on the cheap model (decision 43)",
          rows[-1]["counts"]["adjudications_skipped"] >= 1
          and any(cc["stage"] == "support" for cc in ns["CALLS"] if cc.get("doc") == picked["source_uri"]),
          sorted({cc["stage"] for cc in ns["CALLS"] if cc.get("doc") == picked["source_uri"]}))
    check("chat: unit carries the session date and facts inherit nothing invented", all(f["valid_from"] is None for f in cf) and picked["units"][0]["occurred_at"] == picked["occurred_at"])

# ---------------------------------------------------------------- a paper
paper = ns["load_document"](uri_of("/dong2005-reference-reconciliation.pdf"), BY_URI, UNITS, PIECES)
p, c, st, recs, ents, fd = ns["ingest"](paper)
rows = list(ns["read_jsonl"](p))
pf = [r for r in rows if r["record"] == "fact"]
check("paper: facts located through PDF ligatures (ﬁ) and offsets slice to the quote", pf and all(paper["text"][f["quote_start"]:f["quote_end"]] == f["quote"] for f in pf))
check("paper: author is the document author (published voice)", pf and all(f["author"] == paper["author"] for f in pf), paper["author"])
check("paper: first unit derived like any other (no branch on kind)", recs[0]["summary"] is not None)

# ---------------------------------------------------------------- the summary stands as written
script["bad_fold"] = 2
p, c, st, recs, ents, fd = ns["ingest"](ns["load_document"](uri_of("/oz/02_54.txt"), BY_URI, UNITS, PIECES))
rows = list(ns["read_jsonl"](p))
doc_abstract = [r for r in rows if r["record"] == "abstract" and r["node_id"] == ns["h"](rows[0]["doc_id"], "document")]
check("a summary naming something the records do not is still stamped, not rejected (decision 65)",
      len(doc_abstract) == 1 and "Rumpelstiltskin" in doc_abstract[0]["text"], doc_abstract[0]["text"][:60] if doc_abstract else None)
check("an entity with nothing to summarise is not a major (decision 52)",
      all(any(a["record"] == "abstract" and a["node_id"] == r["node_id"] for a in rows) for r in rows if r["record"] == "node" and r["kind"] != "document"))
script["bad_fold"] = 0

# ---------------------------------------------------------------- the two fixes of 09-07
near = "alpha " + ("word " * 20) + "omega"
far = "alpha " + ("word " * 200) + "omega"
s1, e1, h1 = ns["locate"](near, "alpha ... omega")
s2, e2, h2 = ns["locate"](far, "alpha ... omega")
check("a quote whose two halves are close is still a pieces match", h1 == "pieces" and s1 == 0, (s1, e1, h1))
check("a quote whose halves are further apart than the cap is refused (ruling of 09-07)",
      s2 is None and h2 == "span_too_wide", (s2, h2))
check("no other path can outrun the cap: every one matches a single run of text",
      ns["locate"](near, "alpha")[2] == "exact" and ns["QUOTE_SPAN_MAX"] >= 300)
opening = ns["support_prompt"](["1. a b c  (\"q\")"]).split(chr(10))[0]
check("the support check asks whether a passage states a statement, naming no entity (fixed 09-07)",
      "about" not in opening, opening[:90])

# ---------------------------------------------------------------- one reading: the short path
one = ns["load_document"](uri_of("/oz/03_486.txt"), BY_URI, UNITS, PIECES)
body = [x for x in one["units"] if ns["unit_kind"](one, x) not in ns["BOILERPLATE"]]
one["units"] = [x for x in one["units"] if ns["unit_kind"](one, x) in ns["BOILERPLATE"]] + body[:1]
check("a document whose boilerplate leaves one unit is read once, not merged",
      ns["one_reading"](one) and len(one["units"]) >= 1, [ns["unit_kind"](one, x) for x in one["units"]])
at = len(ns["CALLS"])
light_path, light_counts, light_stats, light_records, _, light_folded = ns["ingest"](one)
stages = [c["stage"] for c in ns["CALLS"][at:]]
light_rows = list(ns["read_jsonl"](light_path))
check("the short path buys no triage, no entity abstract and no adjudication",
      not {"triage", "entity_abstract", "adjudicate"} & set(stages), sorted(set(stages)))
check("its facts are verified in a single pass over the whole document",
      stages.count("support") == 1, stages)
check("four calls a document, and a fifth only when something needed correcting (R3)",
      len(stages) == 4 + (1 if stages.count("correct") else 0)
      and stages.count("correct") <= 1
      and (stages.count("correct") == 1) == (rows[-1]["counts"]["facts_flagged"] > 0), stages)
# two or fewer children still stand as the abstract; what C9 forbids is the long degenerate
# case, an entity with no cell whose abstract is a run of predicate strings and nothing else
bad_abstracts = [r["text"][:70] for r in rows if r["record"] == "abstract"
                 and "." not in r["text"] and r["text"].count("_") >= 3]
check("no entity abstract is a run of three or more predicate strings (C9)",
      not bad_abstracts, bad_abstracts[:3])
check("nothing is consolidated, so the facts stand with their quotes",
      not any(r["record"] in ("adjudicated_fact", "attribute") for r in light_rows)
      and all(r["quote"] for r in light_rows if r["record"] == "fact")
      and light_counts["facts_stored"] > 0, light_counts["facts_stored"])
light_celled = {r["node_id"] for r in light_rows if r["record"] == "cell"}
light_abstracted = {r["node_id"] for r in light_rows if r["record"] == "abstract"}
check("a major with a cell gets an abstract from it without a call; one with no cell may have none (C9)",
      all(r["node_id"] in light_abstracted for r in light_rows
          if r["record"] == "node" and r["kind"] != "document" and r["node_id"] in light_celled))
check("a one-reading document reports its majors with their abstracts and facts (ruling of 09-07)",
      light_stats.get("one_reading") is True, light_stats.get("one_reading"))
lines = ns["one_reading_report"](light_records, light_folded)
noise = {"stage": "facts", "model": ns["LUNA"], "in": 1, "out": 1, "seconds": 0.1, "cost": 9.99,
         "doc": "somebody/else.txt", "unit": 0}
ns["CALLS"].append(noise)
own_cost, own_calls = ns["document_spend"]({"source_uri": "somebody/else.txt"})
ns["CALLS"].remove(noise)
check("a document's cost counts only its own calls, not its neighbours' (fixed 09-07)",
      own_calls == 1 and abs(own_cost - 9.99) < 1e-9 and light_stats["cost"] < 1.0,
      (own_calls, own_cost, light_stats["cost"]))
check("the report names every major and lists facts under them",
      len([x for x in lines if not x.strip().startswith("-")]) >= len(light_folded["majors"])
      and any(x.strip().startswith("- ") and "->" in x for x in lines), lines[:3])
check("a many-unit document is untouched by the short path",
      not ns["one_reading"](ns["load_document"](OZ, BY_URI, UNITS, PIECES)))

# ---------------------------------------------------------------- the spend stop writes nothing
gr = ns["load_document"](uri_of("/graphrag-bench/Novel-40700.txt"), BY_URI, UNITS, PIECES)
gr_kept = [u["position"] for u in gr["units"] if ns["unit_kind"](gr, u) not in ("license", "front_matter", "references")]
script["stop_at_unit"] = gr_kept[3]
done, skipped = ns["run"]([gr["source_uri"]])
script["stop_at_unit"] = None
check("a spending stop mid-document writes no package: the document is re-ingested, not resumed",
      done == 0 and not ns["package_path"](gr).exists())
done, skipped = ns["run"]([gr["source_uri"]])
check("and the next run ingests it whole",
      done == 1 and list(ns["read_jsonl"](ns["package_path"](gr)))[-1]["record"] == "completion")

# ---------------------------------------------------------------- the receipt
rec = ns["receipt"]()
check("receipt sums matched_by and rejected_by across documents and costs from the packages", rec["documents"] >= 5 and rec["matched_by"].get("exact", 0) > 0 and rec["rejected_by"].get("not_found", 0) > 0 and rec["cost_of_packages"] > 0)

# withheld text: the public export ships the reference papers with null text and a papers.jsonl
# row naming the PDF; the ingestor reads the PDF back exactly as the extractor did
zep_uri = ns["find_document"]("rasmussen2025-zep.pdf")
if zep_uri and Path("papers").exists():
    real = ns["load_document"](zep_uri, ns["BY_URI"], ns["UNITS"], ns["PIECES"])
    withheld = {"doc_id": real["doc_id"], "source_uri": real["source_uri"], "text": None}
    saved_rows, saved_papers = ns["PAPERS_ROWS"], ns["PAPERS"]
    ns["PAPERS_ROWS"] = {real["doc_id"]: {"file": "rasmussen2025-zep.pdf", "pdf_sha256": real["sha256"]}}
    try:
        import pymupdf
        ns["PAPERS"] = Path("papers")
        check("a withheld text is rebuilt from its PDF exactly as the extractor read it", ns["withheld_text"](withheld) == real["text"])
        ns["PAPERS_ROWS"][real["doc_id"]]["pdf_sha256"] = "0" * 64
        try:
            ns["withheld_text"](withheld)
            check("a PDF that does not hash to the export's record is refused", False)
        except ValueError as e:
            check("a PDF that does not hash to the export's record is refused", "sha256" in str(e))
    except ImportError:
        print("SKIP  withheld text rebuild (PyMuPDF not installed)")
    ns["PAPERS"] = None
    try:
        ns["withheld_text"](withheld)
        check("without the papers dataset a withheld text is a clear error, not a crash", False)
    except ValueError as e:
        check("without the papers dataset a withheld text is a clear error, not a crash", "attach" in str(e))
    ns["PAPERS_ROWS"], ns["PAPERS"] = saved_rows, saved_papers
else:
    print("SKIP  withheld text checks (no Zep paper or no papers/ folder)")

# reconciliation's own rules, on records written by hand so the verdicts can be scripted
def one_local(position, name, kind, named, major, forms, is_a):
    return {"unit_id": f"u{position}", "position": position, "label": f"unit {position}", "kind": "chapter",
            "entities": [{"name": name, "kind": kind, "named": named, "major": major, "forms": forms}],
            "facts": [{"subject": name, "predicate": "is_a", "object": is_a, "object_is_entity": False,
                       "qualifiers": None, "quote": "q", "unit_id": f"u{position}"}] if is_a else [],
            "profile": [], "cells": [], "summary": "s", "mentions": [], "rejected_facts": [], "dropped_entities": [],
            "shared_spans": 0, "ambiguous_voice": 0, "split_by_voice": 0, "empty": False}


def scripted_judge(answers):
    def judge(batch, locals_, clusters, ctx):
        out = {}
        for n, (ra, rb) in enumerate(batch):
            pair = frozenset((locals_[ra]["name"], locals_[rb]["name"]))
            out[n] = answers.get(pair, ("unsure", "no rule"))
        return out, 0            # (verdicts, numbers out of range)
    return judge


saved_judge = ns["judge"]

# A and B ruled different; C then judged the same as both: the second union is refused
ns["judge"] = scripted_judge({frozenset(("Al", "Bo")): ("different", "two men"),
                              frozenset(("Al", "Cy")): ("same", "one man"),
                              frozenset(("Bo", "Cy")): ("same", "one man")})
recs = [one_local(1, "Al", "person", False, True, ["Al", "the man"], ""),
        one_local(2, "Bo", "person", False, True, ["Bo", "the man"], ""),
        one_local(3, "Cy", "person", False, True, ["Cy", "the man"], "")]
ents, ledger, cands, st = ns["reconcile"](recs, {"doc": "t"})
groups = [sorted(e["names"]) for e in ents]
check("a pair the judge ruled different never ends in one cluster, whatever a later verdict says",
      not any({"Al", "Bo"} <= set(g) for g in groups) and any(r["verdict"] == "different" for r in ledger), groups)

# two locals of one unit are two things: their clusters are never paired
two_in_one = one_local(1, "Al", "person", False, True, ["Al", "the man"], "")
two_in_one["entities"].append({"name": "Bo", "kind": "person", "named": False, "major": True, "forms": ["Bo", "the man"]})
ns["judge"] = scripted_judge({frozenset(("Al", "Bo")): ("same", "should never be asked")})
ents2, ledger2, cands2, st2 = ns["reconcile"]([two_in_one], {"doc": "t"})
check("two locals the same unit listed apart are never nominated, so the judge is never asked",
      st2["candidate_pairs"] == 0 and st2["judge_calls"] == 0 and len(ents2) == 2)

# the same proper name and kind, with is_a that conflicts: the judge decides instead of an instant union
ns["judge"] = scripted_judge({frozenset(("Ajax", "Ajax")): ("different", "son of Oileus against son of Telamon")})
ajax = [one_local(1, "Ajax", "person", True, True, ["Ajax"], "son of Oileus"),
        one_local(2, "Ajax", "person", True, True, ["Ajax"], "son of Telamon")]
ents3, ledger3, cands3, st3 = ns["reconcile"](ajax, {"doc": "t"})
check("the same proper name and kind with conflicting is_a goes to the judge, not an instant union (decision 49)",
      len(ents3) == 2 and st3["judge_calls"] == 1 and any(r["how"] == "same_name_conflicting_is_a" for r in ledger3))

# the same proper name and kind with is_a that agrees: united on sight, no call
ns["judge"] = scripted_judge({})
agree = [one_local(1, "Ajax", "person", True, True, ["Ajax"], "warrior"),
         one_local(2, "Ajax", "person", True, True, ["Ajax"], "warrior")]
ents4, ledger4, cands4, st4 = ns["reconcile"](agree, {"doc": "t"})
check("the same proper name and kind that agree unite on sight, with no judge call",
      len(ents4) == 1 and st4["judge_calls"] == 0 and any(r["how"] == "same_name" for r in ledger4))

ns["judge"] = saved_judge

# a first reply that misses the shape is logged as a retry, and the second reply is used
bodies = [{"choices": [{"message": {"content": json.dumps({"summary": 7})}}]},
          {"choices": [{"message": {"content": json.dumps({"summary": "fine"})}}]}]


def fake_call(url, payload, model, stage, ctx, prompt_chars):
    return bodies.pop(0)


bad_twice = [{"choices": [{"message": {"content": json.dumps({"summary": 7})}}]},
             {"choices": [{"message": {"content": json.dumps({"summary": None})}}]}]


def failing_call(url, payload, model, stage, ctx, prompt_chars):
    return bad_twice.pop(0)


saved_call, ns["call"] = ns["call"], failing_call
rejected_before = len(ns["REJECTIONS"])
twice_refused = real_generate("p", ns["FOLD_SCHEMA"], "fold", ctx={"doc": "t"}) is None and len(ns["REJECTIONS"]) == rejected_before + 1
ns["call"] = saved_call

saved_call, ns["call"] = ns["call"], fake_call
before = len(ns["RETRIES"])
reply = real_generate("p", ns["FOLD_SCHEMA"], "fold", ctx={"doc": "t"})
ns["call"] = saved_call
check("a reply that misses the shape twice is refused, and the refusal is recorded (E4)", twice_refused, twice_refused)
check("a reply that misses the shape is asked for again, and the miss is logged as a retry", reply == {"summary": "fine"} and len(ns["RETRIES"]) == before + 1 and "expected string" in ns["RETRIES"][-1]["detail"] and (SCR / "retries.jsonl").exists())


# independent calls run several at a time, results in order, and a stop inside one still ends the run
def doubled(x):
    return x * 2


def stops_at_two(x):
    if x == 2:
        raise ns["SpendStop"]("test stop in a worker")
    return x


check("in_parallel keeps the items' order", ns["WORKERS"] >= 2 and ns["in_parallel"](doubled, [3, 1, 2, 5, 4]) == [6, 2, 4, 10, 8])

import threading
seen, seen_lock = [], threading.Lock()


def busy(n):
    with seen_lock:
        seen.append(threading.current_thread().name)
    time.sleep(0.05)
    return n


ns["in_parallel"](busy, list(range(12)), width=6)
check("in_parallel runs as wide as it is asked, not as wide as WORKERS (ruling of 09-07)",
      len(set(seen)) > ns["WORKERS"], (len(set(seen)), ns["WORKERS"]))
try:
    ns["in_parallel"](stops_at_two, [1, 2, 3, 4, 5])
    check("a spend stop inside a worker is raised to the caller", False)
except ns["SpendStop"]:
    check("a spend stop inside a worker is raised to the caller", True)

# ------------------------------------------------------- the fixes of 09-07, one check each

# C7 -- a quote is cut where the speaker changes, not at every piece boundary
one_voice = {"pieces": [{"start": 0, "author": None}, {"start": 45, "author": None}]}
two_voices = {"pieces": [{"start": 0, "author": "Ann"}, {"start": 45, "author": "Bo"}]}
sentence = "We evaluate Zep on the LongMemEval benchmark. Zep reduces latency by 90 percent"
check("a quote crossing two pieces of one author is kept whole (C7)",
      ns["voice_spans"](one_voice, 0, sentence, 0, len(sentence)) == [(0, len(sentence))],
      ns["voice_spans"](one_voice, 0, sentence, 0, len(sentence)))
check("a quote crossing a change of speaker is still cut in two (decision 46 stands)",
      len(ns["voice_spans"](two_voices, 0, sentence, 0, len(sentence))) == 2)

# C1 -- a pair already judged is out of the scoring, so its slot goes to the next candidate
locs = ns["locals_of"](records)
fresh_clusters = ns["Clusters"](len(locs))
first_queue, _ = ns["pair_up"](locs, fresh_clusters, set())
first_key = frozenset((first_queue[0][2], first_queue[0][3])) if first_queue else None
second_queue, _ = ns["pair_up"](locs, fresh_clusters, set(), {first_key}) if first_key else ([], 0)
check("a pair judged in an earlier round is not offered again (C1)",
      bool(first_queue) and all(frozenset((q[2], q[3])) != first_key for q in second_queue))
check("and the round is not left empty because of it: another pair takes the slot (C1)",
      bool(first_queue) and bool(second_queue), (len(first_queue), len(second_queue)))

# B2 -- a "different" is applied before any "same" in the same batch
batch_abc = [(1, 2), (2, 3), (1, 3)]
verdicts_abc = {0: ("same", "a"), 1: ("same", "b"), 2: ("different", "c")}
check("constraints are applied before merges within one batch (B2)",
      [v for n, ra, rb, v, why in ns["constraints_first"](batch_abc, verdicts_abc)] == ["different", "same", "same"])
check("a pair with no verdict at all still comes back, deferred (B2)",
      ns["constraints_first"]([(1, 2)], {})[0][3] == "unsure")

# C8 -- a pair number outside the batch is refused rather than read as another pair
check("a judge verdict numbered outside its batch is refused (C8)",
      ns["valid_sources"]([14], 10) == [] and ns["valid_sources"](["3"], 10) == [3] and ns["valid_sources"]([0], 10) == [])

# C2 and C4 -- a refusal is reported, and the listing is batched
made = []
kept_generate = ns["generate"]


def one_reply(reply):
    def fake(prompt, schema, stage, model=None, effort="low", ctx=None):
        made.append(stage)
        return reply
    return fake


many = [({"subject": "S", "predicate": "p", "object": "o", "qualifiers": None, "quote": "q"}, f"id{i}")
        for i in range(ns["VERIFY_BATCH"] * 2 + 1)]
ns["generate"] = one_reply({"unsupported": []})
flagged_ids, refused, n_calls = ns["unsupported_of"](many, {})
check("the verification listing is batched, not sent as one unbounded prompt (C4)",
      n_calls == 3 and len(made) == 3, (n_calls, ns["VERIFY_BATCH"], len(many)))
ns["generate"] = one_reply(None)
flagged_ids, refused, n_calls = ns["unsupported_of"](many[:2], {})
check("a refused verification is reported, not read as a clean pass (C2)", refused and flagged_ids == [])
ns["generate"] = kept_generate

# B1 and R1 -- one sentence about qualifiers, one about what a passage states, in both prompts
fact_text = ns["fact_prompt"]({"label": "L", "text": "T"}, ["A"], ["A"])
support_text = ns["support_prompt"](["1. a b c"])
check("the fact prompt types qualifiers and forbids an object, as the adjudication prompt does (B1)",
      "as a string, else null; never an object" in fact_text)
check("the fact prompt and the support prompt carry the same standard for a quote (R1)",
      ns["QUOTE_RULE"] in fact_text and ns["QUOTE_RULE"] in support_text)
check("the support prompt teaches the rule, not an instance from any corpus (R1, ruling of 09-07)",
      "carries the figure but not the claim" in support_text
      and not any(word in support_text for word in ("deletion", "Boq", "Dorothy", "Zep")))
check("no prompt carries an example lifted from a document (ruling of 09-07)",
      not any(word in ns["adjudicate_prompt"]("N", ["k"], ["1. a"], ["c"]) for word in ("Boq", "Munchkin", "Dorothy")))

# R3 -- a correction is not taken on trust
raw_fact = {"subject": "Zep", "predicate": "reduces", "object": "latency", "qualifiers": None}
check("a correction whose object restates its subject is refused (R3)",
      ns["corrected_fact"](raw_fact, {"subject": "Zep", "predicate": "is_a", "object": "Zep"}) is None)
check("a correction whose object restates its predicate is refused (R3)",
      ns["corrected_fact"](raw_fact, {"predicate": "reduces_latency", "object": "reduces latency"}) is None)
check("a bare boolean is refused as a corrected object (R3)",
      ns["corrected_fact"](raw_fact, {"predicate": "is_fast", "object": "true"}) is None)
check("a correction that moves the subject is refused: it is a different fact, not this one corrected (P1)",
      ns["corrected_fact"](raw_fact, {"subject": "the house", "predicate": "falls_on", "object": "the Witch"}) is None)
check("a correction naming the same subject in another case is still accepted (P1)",
      ns["corrected_fact"](raw_fact, {"subject": "ZEP", "predicate": "reduces_latency_by", "object": "90 percent"}) is not None)
check("a correction that says something is kept, and keeps the fact's subject when none is given (R3)",
      ns["corrected_fact"](raw_fact, {"predicate": "reduces_latency_by", "object": "90 percent"})
      == {"subject": "Zep", "predicate": "reduces_latency_by", "object": "90 percent", "qualifiers": None})

# ---------------------------------------------------- the ordering this file cannot otherwise see
sys.path.insert(0, str(ROOT / "scripts"))
import check_cell_order

forward = check_cell_order.offences(src)
check("no cell can reach a name a later cell defines: the battery execs one namespace, the notebook does not",
      not forward, [f"cell {c} reaches {n!r} from cell {d}" for c, n, d in forward][:4])

print(f"\n{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
