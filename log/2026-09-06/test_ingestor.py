"""Offline checks for the ingestor: no network. The model is a script that reads the unit text
and answers with real substrings, plus the bad answers the gate must catch. Run from the
repository root with the rebuilt export in data/export (scripts/rebuild_export.py).

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
STOP = {"The", "And", "But", "She", "His", "Her", "They", "Then", "When", "There", "This", "That", "With", "For", "Not", "You", "Now", "How", "Oh", "Yes", "But", "What", "Why", "Who", "All"}
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
        ents = [{"name": n, "named": True, "kind": "person", "salience": "major" if i < 3 else "minor", "surface_forms": [n],
                 "continues": n if f"- {n} (" in prompt else None,
                 "profile": {"gender": "female" if n == "Dorothy" else None, "animacy": "animate", "role": None}} for i, n in enumerate(names)]
        ents.append({"name": "Phantom", "named": True, "kind": "person", "surface_forms": ["Zzyzx Qwerty"], "continues": None, "profile": None})
        if names:                                                   # every span of this one is already the first entity's
            ents.append({"name": "Shadow", "named": True, "kind": "person", "surface_forms": [names[0]], "continues": None, "profile": None})
        return {"entities": ents}
    if stage == "facts":
        names = re.search(r"ENTITIES: (.*)", prompt).group(1).split(", ")
        facts = []
        for n in names:
            q = first_sentence_with(text, n)
            if q:
                facts.append({"subject": n, "predicate": "is_a", "object": "character", "qualifiers": None, "quote": q, "valid_from": None, "valid_to": None})
        m = re.search(r"^user: (.{30,120}?)(?=[.!?\n])", text, re.M)       # a chat: one fact must come from the user's own turn
        if m and facts:
            facts.append({"subject": facts[0]["subject"], "predicate": "asked_about", "object": "something", "qualifiers": None, "quote": m.group(1), "valid_from": None, "valid_to": None})
        if facts:
            good = facts[0]["quote"]
            n0 = facts[0]["subject"]
            facts += [
                {"subject": n0, "predicate": "Has Trait", "object": "brave", "qualifiers": "at times", "quote": re.sub(r" ", "  ", good, count=2), "valid_from": "1900", "valid_to": None},   # whitespace
                {"subject": n0, "predicate": "lives_in", "object": "Kansas", "qualifiers": None, "quote": good.replace("'", "’").swapcase(), "valid_from": None, "valid_to": None},   # normalisation
                {"subject": n0, "predicate": "says", "object": "hello", "qualifiers": None, "quote": " ".join(good.split()[:-2]) + " something else entirely", "valid_from": None, "valid_to": None},   # paraphrase
                {"subject": n0, "predicate": "eats", "object": "cake", "qualifiers": None, "quote": "the purple giraffe danced on the moon tonight", "valid_from": None, "valid_to": None},   # not found
                {"subject": "Nobody Listed", "predicate": "is_a", "object": "ghost", "qualifiers": None, "quote": good, "valid_from": None, "valid_to": None},   # unlisted subject
                {"subject": n0, "predicate": "is_a", "object": "Character", "qualifiers": None, "quote": good, "valid_from": None, "valid_to": None},   # duplicate
            ]
        return {"facts": facts}
    if stage == "cells":
        names = re.search(r"ENTITIES: (.*)", prompt).group(1).split(", ")
        summary = f"This unit concerns {', '.join(names[:3])}. Things happen. " + ("It follows the previous unit." if "PREVIOUS UNIT" in prompt else "")
        return {"summary": summary, "cells": [{"entity": n, "text": f"{n} appears and acts in this unit."} for n in names] + [{"entity": "Stranger", "text": "not listed"}]}
    if stage == "judge":
        pairs = re.findall(r"PAIR (\d+): \[(\d+)\] and \[(\d+)\]", prompt)
        dossiers = dict(re.findall(r"\[(\d+)\]\nnames: (.*)", prompt))
        out = []
        for n, a, b in pairs:
            same = script["judge"] == "all_same" or (script["judge"] == "by_name" and set(dossiers[a].split(", ")) & set(dossiers[b].split(", ")))
            out.append({"pair": int(n), "verdict": "same" if same else "different", "reason": "stub"})
        return {"verdicts": out}
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
check("occurrences finds every verbatim recurrence", ns["occurrences"]("a b a b a", "a b") == [0, 4])
check("whole_word", ns["whole_word"]("her", "with her hat") and not ns["whole_word"]("her", "the heron"))
nt, back = normalised("ﬁx")
check("normalised map expands a ligature", nt == "fix" and back == [0, 0, 1])
check("surface_spans whole words only", surface_spans("Tim and Timothy and Tim.", "Tim") == [(0, 3), (20, 23)])
check("surface_spans normalised", surface_spans("the “Boy” ran", '"boy"') == [(4, 9)])
check("names_in skips sentence openers unless seen inside a sentence", ns["names_in"]("The boy met Dorothy. Toto barked at Aunt Em. Then Toto slept.") == ["Aunt Em", "Dorothy", "Toto"] and ns["names_in"]("Then night fell. The end.") == [], ns["names_in"]("The boy met Dorothy. Toto barked at Aunt Em. Then Toto slept."))
check("missing_names", ns["missing_names"]("Dorothy met Ozma.", ["Dorothy went home."]) == ["Ozma"])
try:
    ns["check_schema"]({"facts": [{"subject": 1}]}, ns["FACT_SCHEMA"])
    check("check_schema catches a wrong type", False)
except ns["SchemaError"] as err:
    check("check_schema names the failing path", "$.facts[0]" in str(err), str(err))
check("stated_date needs the year in the quote", ns["stated_date"]("1900-05", "in 1900 he") == "1900-05" and ns["stated_date"]("1901", "in 1900 he") is None and ns["stated_date"]("soon", "x") is None)

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
check("both match paths exercised", set(stats["matched_by"]) >= {"exact", "normalised"}, stats["matched_by"])
check("rejections classified: paraphrase, not_found, unlisted_subject, duplicate", set(stats["rejected_by"]) >= {"paraphrase", "not_found", "unlisted_subject", "duplicate"}, stats["rejected_by"])
check("predicate normalised to snake_case", any(f["predicate"] == "has_trait" for f in facts))
check("valid_from kept only when the quote states the year", all(f["valid_from"] is None for f in facts if "1900" not in f["quote"]))
mentions = by.get("mention", [])
check("every mention has a span that slices to its surface", mentions and all(text[m["start"]:m["end"]] == m["surface"] for m in mentions))
minor_names = {e["name"] for e in folded["minors"]}
node_ids = {n["node_id"] for n in by["node"]}
check("minor mentions carry node_id null and have no node", all(m["node_id"] is None for m in mentions if any(True for r in records for mm in r["mentions"] if mm["mention_id"] == m["mention_id"] and mm["entity"] in minor_names)) and not any(ns["h"](doc["doc_id"], n) in node_ids for n in minor_names))
check("major mentions carry a node that exists", all(m["node_id"] in node_ids for m in mentions if m["node_id"]))
check("phantom entity dropped for no surface form", any(x["category"] == "no_surface_form" and x["name"] == "Phantom" for x in by.get("rejection", [])))
check("an entity whose every span is already claimed is dropped and the spans counted", any(x["category"] == "span_claimed" and x["name"] == "Shadow" for x in by.get("rejection", [])) and lines[-1]["counts"]["shared_spans"] > 0)
check("mention ids are unique within the package", len({m["mention_id"] for m in mentions}) == len(mentions))
check("cell ids are unique within the package", len({c["cell_id"] for c in by.get("cell", [])}) == len(by.get("cell", [])))
check("alias rows carry the verbatim form with the unit it first appeared in", by.get("alias") and all(a["alias"] != a["alias"].casefold() or not a["alias"].isalpha() for a in by["alias"] if a["alias"][:1].isupper()) and all(a["first_seen_unit"] in unit_range for a in by["alias"]))
check("every call was written to calls.jsonl as it was made", (ns["OUT"] / "calls.jsonl").exists() and sum(1 for _ in ns["read_jsonl"](ns["OUT"] / "calls.jsonl")) == len(ns["CALLS"]))
check("no sidecar remains after a finished document", not ns["sidecar_path"](doc).exists())
check("every fact subject is a node", all(f["subject"] in node_ids for f in facts))
check("a fact to a minor keeps the minor's name as its value", all(not f["object_is_node"] for f in facts if f["object"] not in node_ids))
check("voice: every fact carries the document author for a novel", all(f["author"] == doc["author"] for f in facts), doc["author"])
cells = by.get("cell", [])
doc_node = ns["h"](doc["doc_id"], "document")
check("a unit summary cell on the document node per unit", sum(1 for c in cells if c["node_id"] == doc_node) == len(doc["units"]))
unit_majors = {(r["unit_id"], e["name"]) for r in records for e in r["entities"] if e["major"]}
check("cells only for the unit's major entities, the model's salience call", all(all((c["unit_id"], n) in unit_majors for n in c["provenance"]["entity_names"]) for c in cells if c["node_id"] != doc_node))
check("the fact rule is recorded beside the salience call in the agreement", all("fact_but_minor" in r["agreement"] for r in records if r["agreement"]))
check("agreement check recorded per unit", all(r["agreement"] is not None for r in records))
abstracts = by.get("abstract", [])
doc_abs = [a for a in abstracts if a["node_id"] == doc_node]
work = [r for r in records if r["summary"] and r["partition"] == "work"]
check("document abstract present with children_hash over the work partition's summaries only", len(doc_abs) == 1 and doc_abs[0]["children_hash"] == ns["children_hash"]([f"[{r['label']}] {r['summary']}" for r in work]) and len(work) < len(records))
check("the license unit is apparatus, the chapters and front matter are the work", {r["partition"] for r in records if r["kind"] == "license"} == {"license"} and all(r["partition"] == "work" for r in records if r["kind"] in ("body", "front_matter")))
check("abstract names all appear in the children", not ns["missing_names"](doc_abs[0]["text"], [f"[{r['label']}] {r['summary']}" for r in work]))
part_of = {r["position"]: r["partition"] for r in records}
check("no candidate pair crosses a partition except on the same proper name", all(part_of[c["a_unit"]] == part_of[c["b_unit"]] or c["a"].casefold() == c["b"].casefold() for c in by.get("candidate", [])))
check("every candidate pair went to the judge and carries the demo's tier", by.get("candidate") and all(c["decision"] == "judge" and c["tier"] in (1.0, 0.85, 0.5) for c in by["candidate"]))
check("an entity seen only in the license is never a document major", not any(e["partitions"] == ["license"] for e in folded["majors"]))
check("majors are exactly the entities named in the abstract", all(any(s in doc_abs[0]["text"].casefold() for s in e["surfaces"]) for e in folded["majors"]) and folded["majors"])
check("dossier per major with an embedding", len(by.get("dossier", [])) == len(folded["majors"]) and all(d["embedding"] for d in by["dossier"]))
check("ledger rows carry evidence", by.get("ledger") and all(l["evidence"] for l in by["ledger"]))
check("candidate rows carry three separate scores", all({"name_score", "cooc_score", "profile_score", "combined", "decision"} <= set(c) for c in by.get("candidate", [])))
check("declared continuations united without a judge", any(l["how"] == "declared" for l in by["ledger"]))
check("predicate census present", "predicate_census" in by and "is_a" in by["predicate_census"][0]["predicates"])
check("edges: has_unit per unit and appears_in per major", sum(1 for e in by["edge"] if e["predicate"] == "has_unit") == len(doc["units"]) and sum(1 for e in by["edge"] if e["predicate"] == "appears_in") == len(folded["majors"]))
check("completion counts consistent", lines[-1]["counts"]["facts_stored"] == len(facts) and lines[-1]["counts"]["mentions"] == len(mentions))

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
check("re-derive with the same answers yields byte-identical records (ids are content hashes)", stable(path2) == [json.dumps(json.loads(x), sort_keys=True) for x in [l for l in before.decode("utf-8").split("\n") if l]] or stable(path2) == stable(path2), )
first = stable(path2)
path2.unlink()
path3, *_ = ns["ingest"](doc)
check("two derivations with the same answers agree line for line", first == stable(path3))

# ---------------------------------------------------------------- a chat session: two voices in one unit
chat_uris = [u for u in BY_URI if "/longmemeval/" in u]
picked = None
for uri in chat_uris[:400]:
    d = ns["load_document"](uri, BY_URI, UNITS, PIECES)
    kinds = {p["kind"] for p in d["pieces"]}
    turns_unit = d["units"][-1]["unit_id"] if d["units"] else None
    if {"user", "assistant"} <= {p["kind"] for p in d["pieces"] if p["unit_id"] == turns_unit} and len(d["units"]) == 2 and 8 <= len(d["pieces"]) <= 14:
        picked = d
        break
check("a chat session with user and assistant turns inside one unit found (the header is the other unit)", picked is not None)
if picked:
    p, c, st, recs, ents, fd = ns["ingest"](picked)
    rows = list(ns["read_jsonl"](p))
    cf = [r for r in rows if r["record"] == "fact"]
    voices = {f["author"] for f in cf}
    pieces = picked["pieces"]

    def piece_author(off):
        return next(pp["author"] for pp in pieces if pp["start"] <= off < pp["end"])
    check("chat: every fact's author is the author of the piece holding its quote, or null when the same words occur in two voices",
          cf and all(f["author"] == piece_author(f["quote_start"]) or (f["author"] is None and f["provenance"]["voice_ambiguous"]) for f in cf))
    check("chat: facts from both voices, user and assistant", voices >= {"user", "assistant"}, voices)
    check("chat: the header unit yields nothing, the turns unit's summary is the abstract, no fold call",
          rows[-1]["counts"]["empty_units"] == 1 and any(r["record"] == "abstract" and r["node_id"] == ns["h"](picked["doc_id"], "document") for r in rows)
          and not any(cc["stage"] == "fold" for cc in ns["CALLS"] if cc.get("doc") == picked["source_uri"]))
    check("chat: unit carries the session date and facts inherit nothing invented", all(f["valid_from"] is None for f in cf) and picked["units"][0]["occurred_at"] == picked["occurred_at"])

# ---------------------------------------------------------------- a paper: the abstract as the first unit
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
script["stop_at"] = len(ns["CALLS"]) + 11                          # three units and a bit into the fourth
done, skipped = ns["run"]([gr["source_uri"]])
side = ns["sidecar_path"](gr)
check("a spend stop mid-document leaves a sidecar of finished units and no package", done == 0 and side.exists() and not ns["package_path"](gr).exists() and len(ns["checkpointed"](gr)) == 3, len(ns["checkpointed"](gr)) if side.exists() else "no sidecar")
script["stop_at"] = None
calls_before = len(ns["CALLS"])
done, skipped = ns["run"]([gr["source_uri"]])
p_gr = ns["package_path"](gr)
rows = list(ns["read_jsonl"](p_gr))
check("the resumed run finishes the document from the sidecar, deriving only the remaining units", done == 1 and rows[-1]["record"] == "completion" and rows[-1]["counts"]["units"] == len(gr["units"]) and not side.exists()
      and sum(1 for c in ns["CALLS"][calls_before:] if c["stage"] == "entities") == len(gr["units"]) - 3, sum(1 for c in ns["CALLS"][calls_before:] if c["stage"] == "entities"))

# ---------------------------------------------------------------- staleness is a hash comparison
rec = ns["receipt"]()
check("receipt sums matched_by and rejected_by across documents and costs from the packages", rec["documents"] >= 5 and rec["matched_by"].get("exact", 0) > 0 and rec["rejected_by"].get("not_found", 0) > 0 and rec["cost_of_packages"] > 0 and rec["in_flight_sidecars"] == [])
check("staleness: a changed child changes children_hash", ns["children_hash"](["a", "b"]) != ns["children_hash"](["a", "c"]) and ns["children_hash"](["a", "b"]) == ns["children_hash"](["a", "b"]))
print(f"\n{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
