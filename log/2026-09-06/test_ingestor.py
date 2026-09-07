"""Offline checks for the ingestor: no network. The model is a script that reads the unit text
and answers with real substrings, plus the bad answers the gate must catch. Run from the
repository root with the export in data/export.

    python log/2026-09-06/test_ingestor.py

Every check prints PASS or FAIL; the last line counts them.
"""
import json
import os
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
os.environ["OPENAI_API_KEY"] = "test-key-never-sent"        # so embed() runs through the stub

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
        ents = [{"name": n, "named": not unnamed, "kind": "person", "salience": "major" if i < 3 else "minor", "surface_forms": [n],
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
        return {"unsupported": [int(k) for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M) if "an unsupported claim" in line]}
    if stage == "adjudicate":
        listing = prompt.split("FACTS:\n", 1)[1].split("\nCELLS:")[0]
        n = len(re.findall(r"^\d+\. ", listing, re.M))
        unsupported = [int(k) for k, line in re.findall(r"^(\d+)\. (.*)$", listing, re.M) if "an unsupported claim" in line]
        return {"facts": [{"predicate": "is_a", "object": "character", "qualifiers": None, "from": [1]},
                          {"predicate": "lives_in", "object": "Kansas", "qualifiers": None, "from": [1]},
                          {"predicate": "lives_at", "object": "the farm", "qualifiers": None, "from": [1]},   # the pairwise judge folds this into lives_in
                          *[{"predicate": f"trait_{k}", "object": "some", "qualifiers": None, "from": [1]} for k in range(min(n // 3, 20))],   # a spread that grows with the facts: a book judges predicates, a chat does not
                          {"predicate": "bogus", "object": "nothing", "qualifiers": None, "from": [999]}],   # points at nothing: dropped
                "attributes": [{"attribute": "kind", "value": "character", "from": list(range(1, min(n, 3) + 1))},
                               {"attribute": "standing alone", "value": None, "from": [1]}],
                "contradictions": [], "unsupported": unsupported}
    if stage in ("fold", "entity_abstract"):
        records = prompt.split("RECORDS:\n", 1)[1]
        names = sorted(set(CAP.findall(records)) - STOP)[:5]
        if script["bad_fold"] > 0:                          # each bad answer spends one; the retry is bad too while any remain
            script["bad_fold"] -= 1
            return {"summary": f"A tale of {', '.join(names)} and Rumpelstiltskin."}
        return {"summary": f"A record of {', '.join(names)}."}
    raise AssertionError(stage)


def stub_embed(texts, stage="embed", ctx=None):
    return [[float(int(ns["h"](t)[:8], 16) % 1000) / 1000.0] * 4 for t in texts]


real_generate = ns["generate"]                                   # kept for the retry check below
ns["generate"], ns["embed"] = stub_generate, stub_embed

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
check("names_in skips sentence openers unless seen inside a sentence", ns["names_in"]("The boy met Dorothy. Toto barked at Aunt Em. Then Toto slept.") == ["Aunt Em", "Dorothy", "Toto"] and ns["names_in"]("Then night fell. The end.") == [])
check("missing_names", ns["missing_names"]("Dorothy met Ozma.", ["Dorothy went home."]) == ["Ozma"])
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
check("package written with a completion last", lines[-1]["record"] == "completion" and lines[0]["record"] == "package")
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
check("a fact the adjudication finds unsupported by its passage stays with its quote, ranked unsupported, and is counted", any(f["object"] == "an unsupported claim" and f["rank"] == "unsupported" for f in facts) and lines[-1]["counts"]["facts_unsupported"] > 0 and not any(f["object"] == "and supported" and f["rank"] == "unsupported" for f in facts))
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
check("no sidecar remains after a finished document", not ns["sidecar_path"](doc).exists())
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
check("document abstract present with children_hash over the derived units' summaries", len(doc_abs) == 1 and doc_abs[0]["children_hash"] == ns["h"](*[f"[{r['label']}] {r['summary']}" for r in work]))
check("triage left out the front matter and the license, and those units were never derived", {x["kind"] for x in lines[-1]["excluded"]} == {"front_matter", "license"} and lines[-1]["counts"]["units_excluded"] == 2 and len(records) == len(doc["units"]) - 2 and all(r["kind"] == "body" for r in records))
check("abstract names all appear in the children", not ns["missing_names"](doc_abs[0]["text"], [f"[{r['label']}] {r['summary']}" for r in work]))
check("every queued pair carries the demo's tier and three separate scores", by.get("candidate") and all(c["tier"] in (1.0, 0.85, 0.5) and {"name_score", "cooc_score", "profile_score", "combined"} <= set(c) for c in by["candidate"]) and any(c["stage"] == "judge" for c in ns["CALLS"]))
check("the queue is strongest first", [(-c["tier"], -c["combined"]) for c in by["candidate"]] == sorted((-c["tier"], -c["combined"]) for c in by["candidate"]))
check("never minor against minor in the queue", all(any(e["major"] and e["name"] in (c["a"], c["b"]) and r["position"] in (c["a_unit"], c["b_unit"]) for r in records for e in r["entities"]) for c in by["candidate"]))
check("a pair the judge could not settle was judged once more at the end", any(l["how"] == "judged again" for l in by.get("ledger", [])))
check("two named locals with the same name and kind unite on sight, no judge", any(l["how"] == "same_name" and l["verdict"] == "same" for l in by["ledger"]))
check("a low-salience major was demoted to minor and has no node", lines[-1]["counts"]["demoted"] > 0 and all(not e["major"] for e in folded["minors"] if e["rank"]["demoted"]) and all(e["rank"]["demoted"] is False for e in folded["majors"]))
inverse = [f for f in facts if f["direction"] == "inverse"]
check("a minor's fact about a major lands on the major, marked inverse, with the minor's name as its value", inverse and all(f["subject"] in node_ids and not f["object_is_node"] and f["object"] not in node_ids for f in inverse))
adjudicated = by.get("adjudicated_fact", [])
fact_ids_of = {}
for f in facts:
    fact_ids_of.setdefault(f["subject"], set()).add(f["fact_id"])
about = [f for f in facts if f["direction"] == "about"]
check("a minor's own fact rides into the major it is tied to, marked about, under an id of its own", about and all(f["subject"] in node_ids and not f["object_is_node"] and f["fact_id"] != f["provenance"]["copy_of"] for f in about) and lines[-1]["counts"]["facts_riding"] == len(about))
check("a riding fact names the fact it rides under, a stored fact of the same node", all(f["provenance"]["rides_on"] in fact_ids_of.get(f["subject"], set()) for f in about))
check("a minor tied to no major keeps nothing, and the count says so", lines[-1]["counts"]["facts_minor_subject"] > 0)
loosely = [f for f in facts if f["predicate"] == "is_called"]
check("a subject written with another case or a leading article is the listed entity", loosely and all(not f["provenance"]["subject_name"].startswith("The ") for f in loosely))
check("a quote wrapped in the model's own quotation marks is found once they come off, and says so", any(f["provenance"]["matched_by"] == "unwrapped" and f["quote"][:1] not in "“\"" for f in facts))
check("a quote cited with an ellipsis is kept, its stored quote spanning the pieces", any(f["provenance"]["matched_by"] == "pieces" and " " in f["quote"] for f in facts))
check("adjudicated predicates are the model's own, unmerged, in snake_case", {"lives_in", "lives_at"} <= {a["predicate"] for a in adjudicated} and not any(r["record"] == "predicate_merge" for r in lines) and "predicate_raw" not in adjudicated[0])
check("no consolidated fact rests only on facts the same reply set aside; a source set aside is not cited (decision 45)",
      adjudicated and all(not (set(a["from_facts"]) & unsupported_ids) for a in adjudicated), len(unsupported_ids))
check("every entity with facts of its own had them read before anything rode: a minor's unsupported fact rides ranked unsupported (decision 50)",
      any(f["direction"] == "about" and f["rank"] == "unsupported" for f in facts)
      or not any(f["direction"] == "about" for f in facts))
check("every adjudicated fact points only at raw facts of its own node", adjudicated and all(set(a["from_facts"]) <= fact_ids_of.get(a["node_id"], set()) for a in adjudicated))
check("attributes point at raw facts too, and an item pointing at nothing was dropped and counted", by.get("attribute") and all(set(a["from_facts"]) <= fact_ids_of.get(a["node_id"], set()) for a in by["attribute"]) and lines[-1]["counts"]["adjudication_dropped"] == len(folded["majors"]))
check("an adjudicated attribute may stand without a value", any(a["value"] is None for a in by.get("attribute", [])))
# a kill mid-write leaves a torn last line in the sidecar: the resume must still accumulate
side = ns["sidecar_path"](doc)
torn_resume_ok = None
if side.exists():
    torn_resume_ok = False
else:
    rows_before = None
    ns["append_sidecar"](doc, {"triage": {}, "cost": 0.0, "calls": 0, "flags": []})
    ns["append_sidecar"](doc, {"rec": {"unit_id": doc["units"][0]["unit_id"]}, "cost": 0.0, "calls": 0})
    with side.open("a", encoding="utf-8") as f:
        f.write('{"rec": {"unit_id": "cut off her')                       # the kill
    ns["checkpointed"](doc)                                               # the resume reads first: the torn line goes
    ns["append_sidecar"](doc, {"rec": {"unit_id": doc["units"][1]["unit_id"]}, "cost": 0.0, "calls": 0})
    excluded_, kept_, cost_, calls_, flags_ = ns["checkpointed"](doc)
    torn_resume_ok = [k["unit_id"] for k in kept_] == [u["unit_id"] for u in doc["units"][:2]]
    side.unlink()

check("each document keeps its own folder, named after its file, with the package inside it",
      path.parent.name == "01_55" and path.name == "01_55.jsonl" and path.parent.parent.name == "oz")
check("two entities the judge kept apart never share a node id (decision 48)",
      len({n["node_id"] for n in by["node"]}) == len(by["node"]))
check("a torn sidecar line does not hide the units a resume appends behind it (A14)", torn_resume_ok, torn_resume_ok)
check("an entity the document cannot summarise is not a major, and its facts ride (decision 52)",
      all(any(a["record"] == "abstract" and a["node_id"] == ns["node_id_of"](doc, e) for a in lines) for e in folded["majors"])
      and all(not e["rank"].get("no_abstract") for e in folded["majors"]))
check("majors are exactly the entities named in the abstract", all(any(s in doc_abs[0]["text"].casefold() for s in e["surfaces"]) for e in folded["majors"]) and folded["majors"])
check("dossier per major with an embedding", len(by.get("dossier", [])) == len(folded["majors"]) and all(d["embedding"] for d in by["dossier"]))
check("ledger rows carry evidence", by.get("ledger") and all(l["evidence"] for l in by["ledger"]))
check("predicate census present", "predicate_census" in by and "is_a" in by["predicate_census"][0]["predicates"])
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

# ---------------------------------------------------------------- rejected fold is not stamped, then retried
script["bad_fold"] = 2
p, c, st, recs, ents, fd = ns["ingest"](ns["load_document"](uri_of("/oz/02_54.txt"), BY_URI, UNITS, PIECES))
rows = list(ns["read_jsonl"](p))
check("a fold that keeps a fabricated name after one retry is not stamped", not any(r["record"] == "abstract" and r["node_id"] == ns["h"](rows[0]["doc_id"], "document") for r in rows) and rows[-1]["abstract_rejected"] == ["Rumpelstiltskin"], rows[-1]["abstract_rejected"])
check("with no abstract the tie-breakers decide salience and the node says so", rows[-1]["counts"]["majors"] > 0 and all(r["provenance"]["salience"]["in_abstract"] is None for r in rows if r["record"] == "node" and r["kind"] != "document") and any(r["record"] == "fact" for r in rows))
script["bad_fold"] = 1
p, c, st, recs, ents, fd = ns["ingest"](ns["load_document"](uri_of("/oz/03_486.txt"), BY_URI, UNITS, PIECES))
rows = list(ns["read_jsonl"](p))
check("a fold rejected once is retried with the missing names and then stamped", any(r["record"] == "abstract" and r["node_id"] == ns["h"](rows[0]["doc_id"], "document") for r in rows))

# ---------------------------------------------------------------- the spend stop mid-document, then a resume from the sidecar
gr = ns["load_document"](uri_of("/graphrag-bench/Novel-40700.txt"), BY_URI, UNITS, PIECES)
triage_calls = 1 if len({ns["unit_kind"](gr, u) for u in gr["units"]}) > 1 else 0
gr_kept = [u["position"] for u in gr["units"] if ns["unit_kind"](gr, u) not in ("license", "front_matter", "references")]
script["stop_at_unit"] = gr_kept[3]                                # three units finished, the fourth's first call stops
calls_at_stop = len(ns["CALLS"])
done, skipped = ns["run"]([gr["source_uri"]])
script["stop_at_unit"] = None
first_three = sum(1 for c in ns["CALLS"][calls_at_stop:] if c.get("unit") in gr_kept[:3])
side = ns["sidecar_path"](gr)
check("a spend stop mid-document leaves a sidecar of the triage and the finished units, and no package", done == 0 and side.exists() and not ns["package_path"](gr).exists() and len(ns["checkpointed"](gr)[1]) == 3, len(ns["checkpointed"](gr)[1]) if side.exists() else "no sidecar")
check("the sidecar carries the cost and the calls of the triage and of the units it holds", ns["checkpointed"](gr)[2] > 0 and ns["checkpointed"](gr)[3] == first_three + triage_calls, (ns["checkpointed"](gr)[3], first_three, triage_calls))
calls_before = len(ns["CALLS"])
done, skipped = ns["run"]([gr["source_uri"]])
rows = list(ns["read_jsonl"](ns["package_path"](gr)))
check("the resumed run reuses the triage and finishes the document from the sidecar, deriving only the remaining units", done == 1 and rows[-1]["record"] == "completion" and not side.exists()
      and not any(c["stage"] == "triage" for c in ns["CALLS"][calls_before:])
      and sum(1 for c in ns["CALLS"][calls_before:] if c["stage"] == "entities") == rows[-1]["counts"]["units"] - 3, sum(1 for c in ns["CALLS"][calls_before:] if c["stage"] == "entities"))
check("the completion's cost and calls include the units paid for before the stop", rows[-1]["stats"]["calls"] > len(ns["CALLS"]) - calls_before and rows[-1]["stats"]["cost"] > sum(c["cost"] for c in ns["CALLS"][calls_before:]))
side_cut = ns["sidecar_path"](gr)
side_cut.write_text('{"ingestor": "x", "input_hash": "y", "triage": {}}\n{"ingestor": "x", "input_hash": "y", "rec": {"unit_id": "z", "broken', encoding="utf-8")
check("a sidecar cut short by a kill does not poison the document", ns["checkpointed"](gr)[:4] == (None, [], 0.0, 0))
side_cut.unlink()

# a stop inside the adjudication keeps every unit; the resume derives none of them again
gr2 = ns["load_document"](uri_of("/graphrag-bench/Novel-30752.txt"), BY_URI, UNITS, PIECES)
script["stop_in_adjudication"], script["adjudications_seen"] = True, 0
done, skipped = ns["run"]([gr2["source_uri"]])
check("a stop inside the adjudication leaves every unit in the sidecar", done == 0 and ns["sidecar_path"](gr2).exists() and len(ns["checkpointed"](gr2)[1]) == rows[-1]["counts"]["units"] or len(ns["checkpointed"](gr2)[1]) > 0)
script["stop_in_adjudication"] = False
calls_before2 = len(ns["CALLS"])
done, skipped = ns["run"]([gr2["source_uri"]])
after = [c["stage"] for c in ns["CALLS"][calls_before2:]]
check("the resumed document derives no unit again and merges at the end", done == 1 and not ns["sidecar_path"](gr2).exists() and not any(st in ("entities", "facts", "cells", "triage") for st in after) and "adjudicate" in after, after)

# ---------------------------------------------------------------- the receipt
rec = ns["receipt"]()
check("receipt sums matched_by and rejected_by across documents and costs from the packages", rec["documents"] >= 5 and rec["matched_by"].get("exact", 0) > 0 and rec["rejected_by"].get("not_found", 0) > 0 and rec["cost_of_packages"] > 0 and rec["in_flight_sidecars"] == [])

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
        return out
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
check("a union that would join a pair the judge ruled different is refused, and the ledger says so",
      not any(sorted(g) == ["Al", "Bo", "Cy"] for g in groups) and any(r["how"] == "refused" for r in ledger), groups)

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


saved_call, ns["call"] = ns["call"], fake_call
before = len(ns["RETRIES"])
reply = real_generate("p", ns["FOLD_SCHEMA"], "fold", ctx={"doc": "t"})
ns["call"] = saved_call
check("a reply that misses the shape is asked for again, and the miss is logged as a retry", reply == {"summary": "fine"} and len(ns["RETRIES"]) == before + 1 and "expected string" in ns["RETRIES"][-1]["detail"] and (SCR / "retries.jsonl").exists())


# independent calls run several at a time, results in order, and a stop inside one still ends the run
def doubled(x):
    return x * 2


def stops_at_two(x):
    if x == 2:
        raise ns["SpendStop"]("test stop in a worker")
    return x


check("in_parallel keeps the items' order", ns["WORKERS"] >= 2 and ns["in_parallel"](doubled, [3, 1, 2, 5, 4]) == [6, 2, 4, 10, 8])
try:
    ns["in_parallel"](stops_at_two, [1, 2, 3, 4, 5])
    check("a spend stop inside a worker is raised to the caller", False)
except ns["SpendStop"]:
    check("a spend stop inside a worker is raised to the caller", True)

print(f"\n{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
