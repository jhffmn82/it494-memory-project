"""Offline checks for the rewritten ingestor (0.9): no network. The scripted model in
scripted_model.py answers every prompt with real substrings of the unit plus the bad answers
the gates must catch. Run from the repository root with the export in data/export:

    python log/2026-09-08/test_ingestor.py

Every check prints PASS or FAIL; the last line counts them. Writes under data/packages-test/.
"""
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_model import ROOT, chat_doc, load, make_stub

sys.stdout.reconfigure(encoding="utf-8")
SCR = ROOT / "data" / "packages-test" / "battery"
ns = load(ROOT / "notebooks" / "factledger-ingestor.py", SCR)
real_generate = ns["generate"]
ns["generate"] = make_stub(ns)
results = []


def check(name, ok, detail=""):
    ok = bool(ok)
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail and not ok else ""))


def uri_of(suffix):
    return next(u for u in ns["BY_URI"] if u.endswith(suffix))


def rows_of(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


# ---------------------------------------------------------------- the quote gate and the helpers
locate, normalised, surface_spans = ns["locate"], ns["normalised"], ns["surface_spans"]
t = "The ﬁrst “quoted” line—done.\nSecond   line here."
s, e, how = locate(t, "quoted")
check("locate exact", (s, e, how) == (t.index("quoted"), t.index("quoted") + 6, "exact"))
s, e, how = locate(t, "Second line here")
check("locate across whitespace, on the normalised path", how == "normalised" and t[s:e] == "Second   line here")
s, e, how = locate(t, 'the FIRST "quoted" line-done')
check("locate through NFKC, curly quotes, dash and case, offsets in the original", how == "normalised" and t[s:e] == "The ﬁrst “quoted” line—done")
check("locate paraphrase classified", locate(t, "Second line here today")[2] == "paraphrase")
check("locate not found classified", locate(t, "purple giraffe moon")[2] == "not_found")
check("locate empty", locate(t, "  ")[2] == "empty")
hy = "the recon-\nciliation of names is\nhard."
s, e, how = locate(hy, "reconciliation of names")
check("locate bridges a hyphenated line break and stores the original slice", how == "normalised" and hy[s:e] == "recon-\nciliation of names")
ell = "Quelala was a boy. He was said to be the best and wisest man in all the land."
check("a quote written with an ellipsis is refused, not stitched across the gap", locate(ell, "Quelala ... the best and wisest man")[2] in ("paraphrase", "not_found"))
oz3 = "She bade her friends good-bye, and again started along the road of yellow brick. When she had gone several miles she thought she would stop to rest."
s, e, how = locate(oz3, "she started along the road of yellow brick.")
check("a citation reworded at its edge is found by its words and the stored quote is the text's own", how == "words" and oz3[s:e] == "started along the road of yellow brick")
check("a citation missing too many words is not found by its words", locate(oz3, "she started along the road to the City of Emeralds today")[2] in ("paraphrase", "not_found"))
check("a bare quote is found as whole words, not inside a longer word", locate("Ozma ruled. The Wizard said he was Oz.", '"Oz"') == (35, 37, "unwrapped"))
check("a matched pair of marks comes off and the text's own apostrophe stays", locate("’Tis a fine day, said Toto.", '"’Tis a fine day"') == (0, 15, "unwrapped"))
check("occurrences finds every verbatim recurrence", ns["occurrences"]("a b a b a", "a b") == [0, 4])
nt, back = normalised("ﬁx")
check("normalised map expands a ligature", nt == "fix" and back == [0, 0, 1])
check("surface_spans whole words only", surface_spans("Tim and Timothy and Tim.", "Tim", {}) == [(0, 3), (20, 23)])
check("surface_spans normalised", surface_spans("the “Boy” ran", '"boy"', {}) == [(4, 9)])
try:
    ns["check_schema"]({"facts": [{"subject": 1}]}, ns["FACT_SCHEMA"])
    check("check_schema catches a wrong type", False)
except ns["SchemaError"] as err:
    check("check_schema names the failing path", "$.facts[0]" in str(err), str(err))
check("stated_date needs the year in the quote", ns["stated_date"]("1900-05", "in 1900 he") == "1900-05" and ns["stated_date"]("1901", "in 1900 he") is None)
check("snake_case", ns["snake_case"]("Has  Trait!") == "has_trait" and ns["snake_case"]("!!") == "")
check("loose_name drops an article and case", ns["loose_name"]("The  SCARECROW") == "scarecrow")
check("statement_number reads a number, a string, and '3.'", [ns["statement_number"](x, 5) for x in ({"number": 3}, {"number": "3."}, {"fact": "4)"}, {"number": 9}, {})] == [3, 3, 4, None, None])
check("valid_numbers keeps distinct integers in range", ns["valid_numbers"]([1, "2", 2, 0, 9, True, "x"], 5) == [1, 2])
fixed, why = ns["corrected_fact"]({"subject": "Lion", "predicate": "p", "object": "o"}, {"predicate": "Lives In", "object": "Kansas"})
check("corrected_fact keeps the subject and snake_cases the predicate", fixed == {"subject": "Lion", "predicate": "lives_in", "object": "Kansas", "qualifiers": None} and why is None)
check("corrected_fact refuses a moved subject, a bare boolean, and a restatement",
      [ns["corrected_fact"]({"subject": "Lion", "predicate": "p", "object": "o"}, item)[1] for item in
       ({"subject": "Toto", "object": "x"}, {"object": "TRUE"}, {"predicate": "is lion", "object": "is_lion"}, {"object": ""})]
      == ["subject moved", "bare boolean", "object restates subject or predicate", "no object"])

# ---------------------------------------------------------------- a synthetic chat: the one-reading path
ns["WATCH"] = False
chat = chat_doc(ns, old=False)
check("a chat session is one reading", ns["one_reading"](chat))
path, counts, stats, records, entities, folded = ns["ingest"](chat)
rows = rows_of(path)
by = ns["grouped"](rows, "record")
check("the short path spends no triage, judge, fold or adjudication call",
      not {c["stage"] for c in ns["CALLS"]} & {"triage", "judge", "fold", "entity_abstract", "adjudicate"}, sorted({c["stage"] for c in ns["CALLS"]}))
check("the short path is entities, facts, cells, one support call, one correction, one check",
      [c["stage"] for c in ns["CALLS"]] == ["entities", "facts", "cells", "support", "correct", "verify"], [c["stage"] for c in ns["CALLS"]])
check("the header unit was left out by rule, without a call", counts["units_excluded"] == 1 and rows[-1]["excluded"][0]["kind"] == "front_matter")
facts = by["fact"]
check("every stored quote is a verbatim slice at its offsets", all(chat["text"][f["quote_start"]:f["quote_end"]] == f["quote"] for f in facts))
spans = [f for f in facts if f["predicate"] == "spans"]
check("a quote across a change of speaker is one fact per voice, each with its author",
      len(spans) == 2 and {f["author"] for f in spans} == {"user", "assistant"}, [(f["author"], f["quote"]) for f in spans])
check("a fact from the user's own turn carries the user's voice", any(f["predicate"] == "asked_about" and f["author"] == "user" for f in facts))
check("ids are readable: doc node, entity nodes, unit-numbered facts",
      all(n["node_id"].endswith(":doc") for n in by["node"] if n["kind"] == "document")
      and all(n["node_id"].split(":")[1].startswith("n") for n in by["node"] if n["kind"] != "document")
      and all(f["fact_id"].split(":")[1:] and f["fact_id"].split(":")[1] == "u1" for f in facts), [f["fact_id"] for f in facts[:3]])
check("no record carries a hash id of its own",
      not any(len(str(r.get(k, ""))) == 64 for r in rows for k in ("node_id", "fact_id", "cell_id", "mention_id") if r["record"] not in ("document", "unit", "piece")))
check("mentions are counted, not written", counts["mentions"] > 0 and "mention" not in by)
rejected = {(r["category"], r["predicate"]) for r in by["rejection"] if r["stage"] == "facts"}
check("the gates reject a paraphrase, an invented quote, an unlisted subject, a duplicate, a self reference, an ellipsis, an invented middle",
      {("paraphrase", "says"), ("not_found", "eats"), ("unlisted_subject", "is_a"), ("duplicate", "is_a"), ("self_reference", "self"),
       ("paraphrase", "is_cited_with")} <= rejected and rejected & {("paraphrase", "is_cited_loosely"), ("not_found", "is_cited_loosely")}, rejected)
dropped = {r["name"]: r["category"] for r in by["rejection"] if r["stage"] == "entities"}
check("an entity with no surface form in the unit is dropped, and one whose spans are all claimed",
      dropped.get("Phantom") == "no_surface_form" and dropped.get("Shadow") == "span_claimed", dropped)
predicates = {f["predicate"]: f for f in facts}
check("a fact the support check flagged and the second look upheld is stored as written", "is_cited_well" in predicates)
check("a fact the second look reworded is stored corrected, with the original in provenance",
      predicates.get("is_cited_loosely", {}).get("object") == "a corrected claim" or any(f["provenance"]["corrected_from"] for f in facts))
check("a fact the second look dropped, and one the third check failed, are dumped as rejections",
      {r["predicate"] for r in by["rejection"] if r["stage"] == "verify"} == {"cannot_be_fixed", "fails_twice"},
      {r["predicate"] for r in by["rejection"] if r["stage"] == "verify"})
check("a correction that restates the predicate is refused and the fact stands", predicates.get("restate_me", {}).get("object") == "restate me")
check("the counts add up", counts["facts_kept"] == counts["facts_stored"] + counts["facts_no_major"] + counts["facts_dumped"]
      and counts["facts_flagged"] == counts["facts_upheld"] + counts["facts_corrected"] + counts["facts_dumped"], counts)
check("the unit summary is the abstract on the short path, and a major's cell is its own abstract",
      folded["abstract"]["tier"] == ns["LUNA"] and len(by["abstract"]) == 1 + len(by["node"]) - 1)
check("completed() sees the finished package and skips it", ns["completed"](chat))
chat["units"].append({**chat["units"][-1], "unit_id": "u2", "position": 2})
check("completed() does not skip a document whose units changed", not ns["completed"](chat))
ns["INGESTOR"] = "someone else 1.0"
chat["units"].pop()
check("completed() still skips a package another version wrote: a version bump re-buys nothing (09-08)",
      ns["completed"](chat))
ns["INGESTOR"] = "factledger-ingestor 0.9"
# the defects this code has actually shipped, each of which its battery could not fail on
kept_objects = {f["object"] for f in by["fact"]}
check("a dumped fact is absent from the fact rows, not merely recorded as a rejection",
      not (kept_objects & {r["object"] for r in by.get("rejection", []) if r.get("stage") == "verify"}))
check("salience alone decides a major: carrying a proper name does not promote one",
      all(any(l["major"] for l in records[e["members"][0][0] - 1]["entities"]
              if l["name"] == e["members"][0][1]) for e in folded["majors"])
      if folded["majors"] else False)
check("an entity with nothing to summarise is not a major (decision 52)",
      all(e["children"] for e in folded["majors"]))
kept_generate = ns["generate"]


def refuses(prompt, schema, stage, model=None, effort="low", ctx=None):
    return None


ns["generate"] = refuses
one_fact = {"subject": "S", "predicate": "p", "object": "o", "qualifiers": None, "quote": "q"}
back, _, refusal_notes = ns["corrections_of"]({"f1": one_fact, "f2": one_fact}, {})
ns["generate"] = kept_generate
check("a refused correction call leaves every flagged fact standing, and says so",
      back == {"f1": None, "f2": None} and refusal_notes.get("call refused") == 2, (back, refusal_notes))
# a refused SECOND check is not evidence against a rewording either: its facts stand. This walks
# verify() itself, because the guard the mutation removes lives there, not in the calls it makes.
kept_generate2, kept_flagged = ns["generate"], ns["flagged_facts"]
one_fact = {"subject": "S", "predicate": "p", "object": "o", "qualifiers": None, "quote": "q"}


def one_flagged(records_, folded_, adjudicated_):
    return {"f1": one_fact}


def answers_then_refuses(prompt, schema, stage, model=None, effort="low", ctx=None):
    if stage == "verify":
        return None
    if stage == "correct":
        return {"corrections": [{"number": 1, "verdict": "stands"}]}
    return {"unsupported": []}


ns["generate"], ns["flagged_facts"] = answers_then_refuses, one_flagged
_, kept_corrections, _, verify_notes = ns["verify"](None, None, None, {})
ns["generate"], ns["flagged_facts"] = kept_generate2, kept_flagged
check("a refused second check leaves the facts it could not judge standing, and says so",
      kept_corrections == {"f1": None} and verify_notes.get("failed the second check") == 0,
      (kept_corrections, verify_notes))

report = ns["one_reading_report"](records, folded)
check("the one-reading report names every major with its abstract", len([l for l in report if not l.strip().startswith("-")]) >= 2 * len(folded["majors"]))
ns["CALLS"].clear()

# ---------------------------------------------------------------- Oz book 1: the full path
oz = ns["load_document"](uri_of("/oz/01_55.txt"))
check("a book is not one reading", not ns["one_reading"](oz) and all("kind" in u for u in oz["units"]))
buffer = io.StringIO()
ns["WATCH"] = True
with redirect_stdout(buffer):
    path, counts, stats, records, entities, folded = ns["ingest"](oz)
ns["WATCH"] = False
trace = buffer.getvalue()
rows = rows_of(path)
by = ns["grouped"](rows, "record")
stages = {c["stage"] for c in ns["CALLS"]}
check("the full path triages, judges, folds, adjudicates, supports, corrects and verifies",
      {"triage", "entities", "facts", "cells", "judge", "fold", "entity_abstract", "adjudicate", "support", "correct", "verify"} <= stages, stages)
check("triage left out the front matter and the license", {x["kind"] for x in rows[-1]["excluded"]} == {"front_matter", "license"}, rows[-1]["excluded"])
check("the narration names every stage", all(word in trace for word in ("triage:", "judge round", "reconcile:", "abstract (", "salience:", "adjudicate:", "support:", "correct:", "package ")))
check("every stored quote is a verbatim slice at its offsets", all(oz["text"][f["quote_start"]:f["quote_end"]] == f["quote"] for f in by["fact"]))
check("every fact lands on a node the package has", {f["subject"] for f in by["fact"]} <= {n["node_id"] for n in by["node"]})
check("an object that is a major is written as its node", any(f["object_is_node"] and f["object"] in {n["node_id"] for n in by["node"]} for f in by["fact"]))
check("an inverse landing keeps the lesser thing's name as its value", any(f["direction"] == "inverse" and not f["object_is_node"] for f in by["fact"]))
fact_ids = {f["fact_id"] for f in by["fact"]}
check("every adjudicated fact, attribute and contradiction points only at facts the package carries",
      all(set(r["from_facts"]) <= fact_ids for k in ("adjudicated_fact", "attribute", "contradiction") for r in by.get(k, [])))
check("an adjudicated item pointing at nothing is dropped, and one whose only source was dumped", not any(r["predicate"] in ("bogus", "rests_on_a_doomed_fact") for r in by["adjudicated_fact"]))
check("a contradiction says which fact holds, from its own sources, or null", all(r["holds"] in (None, *r["from_facts"]) for r in by["contradiction"])
      and any(r["holds"] for r in by["contradiction"]) and not any(r["note"] == "holds a doomed fact" and r["holds"] for r in by["contradiction"]))
check("majors with fewer than four facts stand and are checked together in one support call", counts["support_calls"] == 1 and "support" in stages)
check("the abstract came from a Terra fold within its limit", folded["abstract"]["tier"] == ns["TERRA"] and folded["abstract"]["limit"] <= 400)
check("every major has one kind, lower case", all(n["kind"] == n["kind"].lower().strip() for n in by["node"]))
check("the ledger records same-name unions and judge verdicts with evidence",
      {"same_name", "judged"} <= {l["how"] for l in by["ledger"]} and all(l["evidence"] for l in by["ledger"]))
check("Toto, whom the judge cannot settle, is judged again on the last look", any(l["how"] == "judged again" and "Toto" in (l["a"], l["b"]) for l in by["ledger"]))
check("every candidate carries its three scores", all(all(k in c for k in ("name_score", "cooc_score", "combined")) for c in by["candidate"]))
check("no package line is a profile record: nothing asserts about the world without a quote (09-09)",
      "profile" not in by and not any(r.get("record") == "profile" for r in rows))
one = {"name": "Dorothy", "cooc": {"Toto", "Scarecrow"}}
two = {"name": "Dorothy", "cooc": {"Toto", "Lion"}}
scored = ns["score_pair"](one, two, "same_name")
check("the pair score is 0.7 name and 0.3 co-occurrence, and its weights sum to one (09-09)",
      len(scored) == 3
      and abs(scored[-1] - (0.7 * scored[0] + 0.3 * scored[1])) < 1e-9
      and abs(ns["score_pair"]({"name": "x", "cooc": {"a"}}, {"name": "x", "cooc": {"a"}}, "shared_surface")[-1] - 1.0) < 1e-9,
      scored)
check("a unit never pairs its own two entities", all(l["a_unit"] != l["b_unit"] or l["verdict"] != "same" for l in by["ledger"]))
check("the possession 'hat (X's hat)' is never a candidate against its anchor", not any("hat (" in c["a"] + c["b"] for c in by["candidate"]))
check("one unit summary cell per unit read, on the document node", sum(1 for c in by["cell"] if c["provenance"].get("kind") == "unit_summary") == counts["units"])
check("the receipt sums the packages on disk", ns["receipt"]()["documents"] == 2)
rollup = ns["rollup_text"]
buffer = io.StringIO()
with redirect_stdout(buffer):
    rollup(path)
check("the roll-up prints the abstract, the unit summaries, the majors and the raw facts", all(w in buffer.getvalue() for w in ("ABSTRACT", "UNIT SUMMARIES", "MAJOR ENTITIES", "raw facts (")))
ns["CALLS"].clear()

# ---------------------------------------------------------------- the model interface, without a network
calls = []


def fake_call(url, payload, model, stage, ctx, prompt_chars):
    calls.append(payload["messages"][0]["content"])
    content = '{"facts": [{"subject": 1}]}' if len(calls) == 1 else '{"facts": []}'
    return {"choices": [{"message": {"content": content}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5}, "model": model}


ns["call"] = fake_call
reply = real_generate("prompt", ns["FACT_SCHEMA"], "facts")
check("generate retries once with the error appended and returns the good reply", reply == {"facts": []} and len(calls) == 2 and "did not fit" in calls[1] and "$.facts[0]" in calls[1])
check("the miss is counted as a retry, not a rejection", ns["MISSES"]["retries"] >= 1)
calls.clear()
ns["call"] = lambda *a, **k: {"choices": [{"message": {"content": "not json"}}], "usage": {}}
check("two bad replies are a rejection and None", real_generate("prompt", ns["FACT_SCHEMA"], "facts") is None and ns["MISSES"]["rejections"] >= 1)


def stops(*a, **k):
    raise ns["SpendStop"]("test stop")


ns["generate"] = stops
result = ns["one_document"](uri_of("/oz/01_55.txt").replace("01_55", "02_54"))
check("a spend stop is reported, not raised, and names the document", result.get("stop") and "02_54" in result["text"], result)
ns["generate"] = make_stub(ns)

# the chat block of 09-08 died on a corrected fact whose qualifiers were a list. CORRECT_SCHEMA
# asks only for an array of answers, so nothing types that field.
raw_one = {"subject": "Zep", "predicate": "reduces", "object": "latency", "qualifiers": None, "quote": "q"}
listed, _ = ns["corrected_fact"](raw_one, {"predicate": "reduces_latency_by", "object": "90 percent",
                                           "qualifiers": ["on LongMemEval", "against a baseline"]})
plain, _ = ns["corrected_fact"](raw_one, {"predicate": "reduces_latency_by", "object": "90 percent",
                                          "qualifiers": "on LongMemEval"})
empty, _ = ns["corrected_fact"](raw_one, {"predicate": "reduces_latency_by", "object": "90 percent"})
check("a corrected fact's qualifiers are one string or None, whatever the model answered",
      isinstance(listed["qualifiers"], str) and isinstance(plain["qualifiers"], str)
      and empty["qualifiers"] is None, (listed["qualifiers"], plain["qualifiers"], empty["qualifiers"]))

# and a roll-up that falls over reports itself instead of taking the run with it
broken = SCR / "not-a-package.jsonl"
broken.write_text('{"record": "nonsense"}\n', encoding="utf-8")
try:
    ns["rollup"](broken)
    rollup_survived = True
except Exception:
    rollup_survived = False
check("a roll-up that cannot be written reports it and the run carries on", rollup_survived)

print(f"\n{sum(results)} of {len(results)} checks pass")
sys.exit(0 if all(results) else 1)
