"""Differential check: the ingestor as it ran on Kaggle at 0.8 and the rewritten one, driven by
the same scripted model over the same documents, the packages compared by content (the new one
mints readable ids instead of hashes, so ids are mapped back to what they name). Run from the
repository root with the export in data/export:

    python log/2026-09-08/diff_ingestor.py [DOC_SUFFIX ...]

With no documents named it runs the synthetic chat session, Oz book 1, the Dong 2005 paper and
a Greek play. Writes under data/packages-test/.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripted_model import ROOT, load, make_stub, run_one

OLD = Path(__file__).resolve().parent / "factledger-ingestor-0.8-as-run.py"
NEW = ROOT / "notebooks" / "factledger-ingestor.py"
SCR = ROOT / "data" / "packages-test"
DEFAULT = ["chat", "/oz/01_55.txt", "/dong2005-reference-reconciliation.pdf", "/greek/22_35173.txt"]


def normalise(rows):
    """The package with its ids replaced by content, as a dict of sorted record lists."""
    by = {}
    for r in rows:
        by.setdefault(r["record"], []).append(r)
    name_of = {n["node_id"]: n["name"] for n in by.get("node", [])}
    fact_key = {}
    for f in by.get("fact", []):
        fact_key[f["fact_id"]] = (f["unit_id"], f["provenance"]["subject_name"], f["quote_start"], f["quote_end"], f["predicate"], name_of.get(f["object"], f["object"]))
    out = {}

    def nid(x):
        return name_of.get(x, x)

    def fids(xs):
        return sorted(str(fact_key.get(x, ("?", x))) for x in xs)

    for kind, rs in by.items():
        items = []
        for r in rs:
            r = dict(r)
            if isinstance(r.get("provenance"), dict):
                r["provenance"] = {k: v for k, v in r["provenance"].items() if k not in ("ingestor", "salience")}
            if kind == "unit":
                r.pop("kind", None)
            if kind == "node":
                r["node_id"] = nid(r["node_id"])
            if kind in ("alias", "profile", "cell", "abstract", "adjudicated_fact", "attribute", "contradiction"):
                r["node_id"] = nid(r["node_id"])
                r.pop("cell_id", None)
                r.pop("updated_at", None)
            if kind == "edge":
                r["subject"], r["object"] = nid(r["subject"]), nid(r["object"])
            if kind == "fact":
                r["fact_id"] = str(fact_key[r["fact_id"]])
                r["subject"] = nid(r["subject"])
                if r["object_is_node"]:
                    r["object"] = nid(r["object"])
            if kind in ("adjudicated_fact", "attribute", "contradiction"):
                r["from_facts"] = fids(r["from_facts"])
                if kind == "contradiction":
                    r["holds"] = fids([r["holds"]])[0] if r["holds"] else None
            if kind == "completion":
                r.pop("input_hash", None)
                r.pop("ingestor", None)
                r["stats"] = {k: v for k, v in r["stats"].items() if k not in ("cost", "calls")}
                r["counts"] = r["counts"]
            items.append(json.dumps(r, sort_keys=True, ensure_ascii=False))
        out[kind] = sorted(items)
    return out


def compare(a, b, label):
    ok = True
    for kind in sorted(set(a) | set(b)):
        xa, xb = a.get(kind, []), b.get(kind, [])
        if kind == "completion":
            ca, cb = json.loads(xa[0]), json.loads(xb[0])
            shared = set(ca["counts"]) & set(cb["counts"])
            bad = {k: (ca["counts"][k], cb["counts"][k]) for k in shared if ca["counts"][k] != cb["counts"][k]}
            if bad:
                ok = False
                print(f"  {label} completion counts differ: {bad}")
            shared = set(ca["stats"]) & set(cb["stats"])
            bad = {k: (ca["stats"][k], cb["stats"][k]) for k in shared if ca["stats"][k] != cb["stats"][k]}
            if bad:
                ok = False
                print(f"  {label} completion stats differ: {bad}")
            for k in ("excluded", "demoted", "empty"):
                if ca[k] != cb[k]:
                    ok = False
                    print(f"  {label} completion {k} differ: {ca[k]} vs {cb[k]}")
            continue
        if xa != xb:
            ok = False
            only_a, only_b = sorted(set(xa) - set(xb)), sorted(set(xb) - set(xa))
            print(f"  {label} {kind}: {len(xa)} old vs {len(xb)} new; {len(only_a)} only old, {len(only_b)} only new")
            for x in only_a[:3]:
                print(f"      OLD {x[:300]}")
            for x in only_b[:3]:
                print(f"      NEW {x[:300]}")
    return ok


if __name__ == "__main__":
    old_ns = load(OLD, SCR / "old")
    new_ns = load(NEW, SCR / "new")
    old_ns["generate"], new_ns["generate"] = make_stub(old_ns), make_stub(new_ns)
    all_ok = True
    for suffix in sys.argv[1:] or DEFAULT:
        uri = "chat" if suffix == "chat" else next(u for u in old_ns["BY_URI"] if u.endswith(suffix))
        print(f"== {uri}")
        rows_a, counts_a, stats_a = run_one(old_ns, uri, True)
        rows_b, counts_b, stats_b = run_one(new_ns, uri, False)
        calls_a = [c["stage"] for c in old_ns["CALLS"]]
        calls_b = [c["stage"] for c in new_ns["CALLS"]]
        old_ns["CALLS"].clear()
        new_ns["CALLS"].clear()
        if calls_a != calls_b:
            all_ok = False
            print(f"  call sequence differs: old {len(calls_a)} {calls_a[:40]}\n                         new {len(calls_b)} {calls_b[:40]}")
        else:
            print(f"  {len(calls_a)} calls, same sequence")
        ok = compare(normalise(rows_a), normalise(rows_b), suffix)
        print(f"  {'SAME' if ok else 'DIFFERENT'}: {counts_b}")
        all_ok = all_ok and ok
    print("ALL SAME" if all_ok else "DIFFERENCES FOUND")
