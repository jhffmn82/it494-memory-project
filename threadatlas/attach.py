"""The global layer: parents and up-edges over the store (docs/global-layer.md).

    python -m threadatlas.attach <store.sqlite> [signals]

`signals` is the arm: a comma-joined subset of lexical,vector,cast,identity (default all four).
Only the named signals may put a parent over the offer floor; every score is logged regardless,
so the log replays under any arm.

Documents are taken by date then source_uri, undated last; within a document, children by
first unit. A chat's children first pass a salience call; the rest become leaves. Each child is
offered the parents over the floor (at most K, by vector similarity) and the judge rules
attach or not on texts alone; a child with nothing offered founds a parent as a copy of itself.
An attach rewrites the parent (name, kind, one summary line for this document) in one call and
refreshes its vector. Two children of one document are never offered to each other; both may
land under one parent. After every document, a second pass re-offers every founder once. The
parent, instance_of, offer and leaf tables are rewritten from scratch each run; run
threadatlas.embed afterwards so the parents' summaries join the sidecar.
"""
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

import numpy

from threadatlas import model as llm
from threadatlas.embed import MODEL, DIMENSION, is_identifier

K = 5                    # parents offered to the judge at most
VECTOR_FLOOR = 0.80      # cosine over bge-small; tuned on the test packages, log carries the rest
BELOW_FLOOR_LOGGED = 3   # candidates under the floor logged per child, so the floor can be tuned
FACTS_SHOWN = 12         # facts of a child shown to the judge and the rewrite
WORD = re.compile(r"[a-z0-9]+")


def first_year(date):
    if not date:
        return 10 ** 9
    head = date.split("/")[0].rstrip("~")
    m = re.match(r"-?\d{4}", head)
    return int(m.group(0)) if m else 10 ** 9


def fold(s):
    return " ".join(WORD.findall((s or "").casefold()))


# ---------------------------------------------------------------- the store, read once

class Corpus:
    def __init__(self, db):
        self.db = db
        self.docs = {}
        for row in db.execute("select doc_id, title, source_uri, occurred_at from document"):
            self.docs[row[0]] = {"title": row[1], "source_uri": row[2], "occurred_at": row[3]}
        self.unit_kind = {}
        for unit_id, doc_id, kind, position in db.execute("select unit_id, doc_id, kind, position from unit"):
            self.unit_kind[unit_id] = (kind, position)
        self.nodes = {}
        for doc_id, node_id, name, kind, created in db.execute("select doc_id, node_id, name, kind, created_from_unit from node"):
            self.nodes[(doc_id, node_id)] = {"name": name, "kind": kind, "first_unit": self.unit_kind.get(created, ("", 0))[1],
                                             "aliases": [], "facts": [], "abstract": None, "cast": set(), "identity": set()}
        for doc_id, alias, node_id in db.execute("select doc_id, alias, node_id from alias"):
            if (doc_id, node_id) in self.nodes:
                self.nodes[(doc_id, node_id)]["aliases"].append(alias)
        for doc_id, node_id, text in db.execute("select doc_id, node_id, text from abstract"):
            if (doc_id, node_id) in self.nodes:
                self.nodes[(doc_id, node_id)]["abstract"] = text
        for doc_id, subject, predicate, obj, is_node, qualifiers, date in db.execute(
                "select doc_id, subject, predicate, object, object_is_node, qualifiers, occurred_at from fact order by doc_id, fact_id"):
            node = self.nodes.get((doc_id, subject))
            if node is None:
                continue
            value = self.nodes[(doc_id, obj)]["name"] if is_node and (doc_id, obj) in self.nodes else obj
            node["facts"].append(f"{predicate.replace('_', ' ')} {value}" + (f" ({qualifiers})" if qualifiers else ""))
            # the ingestor's own link: an is_a fact whose object is another node of the document
            if is_node and predicate == "is_a" and (doc_id, obj) in self.nodes:
                node["identity"].add(obj)
                self.nodes[(doc_id, obj)]["identity"].add(subject)
        # the cast: names sharing a unit, from the appears_in edges
        by_unit = {}
        for doc_id, subject, units in self.db.execute("select doc_id, subject, units from edge where predicate = 'appears_in'"):
            if (doc_id, subject) not in self.nodes:
                continue
            for u in json.loads(units or "[]"):
                by_unit.setdefault((doc_id, u), []).append(subject)
        for (doc_id, u), members in by_unit.items():
            for a in members:
                for b in members:
                    if a != b:
                        self.nodes[(doc_id, a)]["cast"].add(fold(self.nodes[(doc_id, b)]["name"]))
        # rarity of a cast name over the loaded documents
        docs_with = {}
        for (doc_id, node_id), node in self.nodes.items():
            docs_with.setdefault(fold(node["name"]), set()).add(doc_id)
        n = len(self.docs)
        self.rarity = {name: math.log(n / (1 + len(ds))) for name, ds in docs_with.items()}

    def is_chat(self, doc_id):
        row = self.db.execute("select kind from unit where doc_id = ? limit 1", (doc_id,)).fetchone()
        return row is not None and row[0] in ("user", "assistant")

    def ordered_docs(self):
        def key(doc_id):
            return (first_year(self.docs[doc_id]["occurred_at"]), self.docs[doc_id]["source_uri"])
        return sorted(self.docs, key=key)

    def children(self, doc_id):
        out = [(node_id, node) for (d, node_id), node in self.nodes.items() if d == doc_id]
        out = [(nid, n) for nid, n in out if not nid.endswith(":doc") and fold(n["name"]) != "user"]
        out.sort(key=lambda_free_key)
        return out


def lambda_free_key(item):
    return (item[1]["first_unit"], item[0])


def child_text(node, doc):
    lines = [f"name: {node['name']}", f"kind: {node['kind']}"]
    aliases = [a for a in node["aliases"] if a != node["name"]]
    if aliases:
        lines.append("also called: " + "; ".join(aliases[:15]))
    if not is_identifier(doc["title"], doc["source_uri"]):
        lines.append(f"document: {doc['title']}")
    if node["abstract"]:
        lines.append("summary: " + node["abstract"])
    elif node["facts"]:
        lines.append("facts: " + "; ".join(node["facts"][:FACTS_SHOWN]))
    return "\n".join(lines)


# ---------------------------------------------------------------- parents in memory

class Parents:
    def __init__(self):
        self.rows = []                                     # dicts: name, kind, aliases, summary(list of (child key, line)), version, children, cast
        self.vecs = numpy.zeros((0, DIMENSION), dtype=numpy.float32)
        self.alive = []

    def add(self, name, kind, aliases, summary, vec, child):
        self.rows.append({"name": name, "kind": kind, "aliases": set(aliases), "summary": summary,
                          "version": 1, "children": [child], "cast": set()})
        self.vecs = numpy.vstack([self.vecs, vec[None, :]])
        self.alive.append(True)
        return len(self.rows) - 1

    def text(self, i):
        p = self.rows[i]
        return f"name: {p['name']}\nkind: {p['kind']}\nalso called: {'; '.join(sorted(p['aliases'])[:20])}\n" + \
               "\n".join(line for (_, line) in p["summary"])


def cosine(vec, mat):
    return mat @ vec


def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def rare_jaccard(a, b, rarity):
    keys = a | b
    if not keys:
        return 0.0
    both = sum(rarity.get(k, 0.0) for k in a & b)
    either = sum(rarity.get(k, 0.0) for k in keys)
    return both / either if either else 0.0


# ---------------------------------------------------------------- the prompts (rules only)

SALIENCE = """You are sorting the entities a reading found in one chat session between a user and an assistant.
Keep an entity when a person who owns this chat history would want it found again in a later session:
a named person, place, organisation, store, product, work, event, project, or a specific thing the user
owns, plans, attends or returns to. Leave an entity when it is the scaffolding of this one conversation:
a generic category, a section of the assistant's answer, an option among options, a step in a list, an
abstract topic, or anything that would mean nothing without this session around it. When in doubt, leave.

The session's summary:
{abstract}

The entities, each with the facts the reading attached to it:
{entities}

Reply with a JSON object: {{"keep": [<entity name>, ...]}} using the names exactly as given."""

JUDGE = """You are deciding whether an entity found in one document is an instance of a global entity that other
documents have already established, or something else with a similar name. Both are described only by
what their documents say. Attach when the two descriptions are of the same person, place, thing or
concept, even under different names, spellings or roles, and even when one document knows it under a
name the other never uses. Keep apart when they are different things that share a name or a word, or
when nothing in the descriptions connects them. A disagreement in kind or role is not by itself a reason
to keep apart; a contradiction in identity is.

The entity from its document:
{child}
Appears beside: {child_cast}

The candidates, numbered:
{parents}

Reply with a JSON object: {{"attach": <candidate number or null>, "reason": "<one sentence>"}}."""

REWRITE = """A global entity is described by the instances of it that documents hold. It has just gained a new
instance. Rewrite its name and kind from all its instances, and write one line saying what part the new
instance played in its document. The name must be one the instances actually use (a name or an alias
listed below), the one a reader would look for first. The kind is one or two words. The line must say
only what the new instance's description says, in the third person, naming the document.

The global entity as it stands:
{parent}

The new instance:
{child}

Reply with a JSON object: {{"name": "<name>", "kind": "<kind>", "line": "<one sentence>"}}."""


# ---------------------------------------------------------------- the build

def run(store, signals):
    db = sqlite3.connect(store)
    llm.LOG_PATH = store.with_name("attach-calls.jsonl")
    from fastembed import TextEmbedding
    embedder = TextEmbedding(MODEL)
    corpus = Corpus(db)
    parents = Parents()
    edges = {}                          # (doc_id, node_id) -> parent index
    leaves = []
    offers = []
    order = corpus.ordered_docs()
    print(f"{len(order)} documents, {len(corpus.nodes)} nodes; signals {sorted(signals)}")

    def embed_one(text):
        return numpy.asarray(list(embedder.embed([text]))[0], dtype=numpy.float32)

    def offer(doc_id, node_id, node, vec, pass_no, exclude):
        """Score every live parent; return the offered indexes and log the rows."""
        if not parents.rows:
            return []
        sims = cosine(vec, parents.vecs)
        rows = []
        child_names = {fold(node["name"])} | {fold(a) for a in node["aliases"]}
        text_folded = fold(child_text(node, corpus.docs[doc_id]))
        for i, p in enumerate(parents.rows):
            if not parents.alive[i] or i in exclude:
                continue
            pnames = {fold(p["name"])} | {fold(a) for a in p["aliases"]}
            lexical = 1.0 if child_names & pnames else (0.5 if any(n and n in text_folded for n in pnames) else 0.0)
            vector = float(sims[i])
            cast = jaccard(node["cast"], p["cast"])
            cast_rare = rare_jaccard(node["cast"], p["cast"], corpus.rarity)
            identity = int(any(c[0] == doc_id and c[1] in node["identity"] for c in p["children"]))
            over = (("lexical" in signals and lexical > 0) or ("vector" in signals and vector >= VECTOR_FLOOR)
                    or ("identity" in signals and identity))
            rows.append((over, vector, i, lexical, cast, cast_rare, identity))
        rows.sort(key=offer_sort)
        offered = [r for r in rows if r[0]][:K]
        below = [r for r in rows if not r[0]][:BELOW_FLOOR_LOGGED]
        for over, vector, i, lexical, cast, cast_rare, identity in offered + below:
            offers.append({"doc_id": doc_id, "node_id": node_id, "parent": i, "parent_version": parents.rows[i]["version"],
                           "pass": pass_no, "lexical": lexical, "vector": vector, "cast": cast, "cast_rare": cast_rare,
                           "identity": identity, "offered": int(over), "verdict": None, "reason": None})
        return [r[2] for r in offered]

    def judge(doc_id, node_id, node, offered, pass_no):
        doc = corpus.docs[doc_id]
        # the cast arm: co-occurrence reaches the judge as names, or not at all
        def cast_line(names):
            return ", ".join(sorted(names)[:25]) if "cast" in signals else "(not shown)"
        listing = "\n".join(f"[{n + 1}]\n{parents.text(i)}\nAppears beside: {cast_line(parents.rows[i]['cast'])}\n"
                            for n, i in enumerate(offered))
        prompt = JUDGE.format(child=child_text(node, doc), child_cast=cast_line(node["cast"]), parents=listing)
        tier = llm.LUNA if corpus.is_chat(doc_id) else llm.TERRA
        reply = llm.generate(prompt, {"attach": None, "reason": str}, "judge", model=tier, effort="medium",
                             ctx={"doc": doc_id[:8], "node": node_id, "pass": pass_no})
        choice = reply.get("attach") if reply else None
        if isinstance(choice, str) and choice.strip().isdigit():
            choice = int(choice)
        picked = offered[choice - 1] if isinstance(choice, int) and 1 <= choice <= len(offered) else None
        for o in offers:
            if o["doc_id"] == doc_id and o["node_id"] == node_id and o["pass"] == pass_no and o["offered"]:
                o["verdict"] = "attach" if o["parent"] == picked else "apart"
                o["reason"] = reply.get("reason") if reply else "no reply"
        return picked

    def found(doc_id, node_id, node, vec):
        doc = corpus.docs[doc_id]
        summary = [((doc_id, node_id), f"In {doc['title']}: " + (node["abstract"] or "; ".join(node["facts"][:FACTS_SHOWN]) or node["name"]))]
        i = parents.add(node["name"], node["kind"], [node["name"]] + node["aliases"], summary, vec, (doc_id, node_id))
        parents.rows[i]["cast"] = set(node["cast"])
        edges[(doc_id, node_id)] = i
        return i

    def attach(doc_id, node_id, node, i):
        p = parents.rows[i]
        doc = corpus.docs[doc_id]
        prompt = REWRITE.format(parent=parents.text(i), child=child_text(node, doc) + f"\ndocument: {doc['title']}")
        reply = llm.generate(prompt, {"name": str, "kind": str, "line": str}, "rewrite", model=llm.LUNA, effort="low",
                             ctx={"doc": doc_id[:8], "node": node_id, "parent": i})
        p["children"].append((doc_id, node_id))
        p["aliases"] |= {node["name"], *node["aliases"]}
        p["cast"] |= node["cast"]
        allowed = {fold(a) for a in p["aliases"]}
        if reply and fold(reply["name"]) in allowed:
            p["name"] = reply["name"]
        if reply and reply.get("kind"):
            p["kind"] = reply["kind"]
        line = reply["line"] if reply and reply.get("line") else f"In {doc['title']}: {node['name']}."
        p["summary"].append(((doc_id, node_id), line))
        p["version"] += 1
        parents.vecs[i] = embed_one(parents.text(i))
        edges[(doc_id, node_id)] = i

    def place(doc_id, node_id, node, vec, pass_no, exclude):
        offered = offer(doc_id, node_id, node, vec, pass_no, exclude)
        picked = judge(doc_id, node_id, node, offered, pass_no) if offered else None
        if picked is None:
            return None
        attach(doc_id, node_id, node, picked)
        return picked

    # pass 1
    for n, doc_id in enumerate(order):
        doc = corpus.docs[doc_id]
        children = corpus.children(doc_id)
        if corpus.is_chat(doc_id) and children:
            abstract = db.execute("select text from abstract where doc_id = ? and node_id like '%:doc'", (doc_id,)).fetchone()
            listing = "\n".join(f"- {c[1]['name']}: " + "; ".join(c[1]["facts"][:6]) for c in children)
            reply = llm.generate(SALIENCE.format(abstract=abstract[0] if abstract else "", entities=listing),
                                 {"keep": list}, "salience", model=llm.LUNA, effort="low", ctx={"doc": doc_id[:8]})
            keep = {fold(k) for k in reply["keep"]} if reply else set()
            kept = [c for c in children if fold(c[1]["name"]) in keep]
            leaves.extend((doc_id, c[0], "salience") for c in children if fold(c[1]["name"]) not in keep)
            children = kept
        # children with identity links go after the others (they may point at a sibling not yet placed)
        children.sort(key=identity_last)
        placed_here = set()
        for node_id, node in children:
            vec = embed_one(child_text(node, doc))
            picked = place(doc_id, node_id, node, vec, 1, exclude=set())
            if picked is None:
                picked = found(doc_id, node_id, node, vec)
            placed_here.add(picked)
        print(f"  [{n + 1}/{len(order)}] {doc['title'][:40]:40} children {len(children):3}  parents {sum(parents.alive):5}  spent ${llm.SPENT:.2f}")

    # pass 2: every founder still alone is offered the full set once
    founders = [(key, i) for key, i in edges.items() if len(parents.rows[i]["children"]) == 1]
    print(f"pass 2 over {len(founders)} founders")
    moved = 0
    for (doc_id, node_id), i in founders:
        node = corpus.nodes[(doc_id, node_id)]
        vec = embed_one(child_text(node, corpus.docs[doc_id]))
        picked = place(doc_id, node_id, node, vec, 2, exclude={i})
        if picked is not None:
            parents.alive[i] = False
            moved += 1
    print(f"pass 2 moved {moved}; parents {sum(parents.alive)}; spent ${llm.SPENT:.2f}")

    # write
    db.execute("delete from parent"); db.execute("delete from instance_of"); db.execute("delete from offer"); db.execute("delete from leaf")
    for i, p in enumerate(parents.rows):
        if not parents.alive[i]:
            continue
        summary = "\n".join(f"[{d[:8]}:{nid}] {line}" for ((d, nid), line) in p["summary"])
        db.execute("insert into parent values (?,?,?,?,?,?,?)",
                   (i, p["name"], p["kind"], json.dumps(sorted(p["aliases"]), ensure_ascii=False), summary, p["version"],
                    f"{p['children'][0][0][:8]}:{p['children'][0][1]}"))
    for (doc_id, node_id), i in edges.items():
        last = [o for o in offers if o["doc_id"] == doc_id and o["node_id"] == node_id and o["parent"] == i and o["verdict"] == "attach"]
        reason = last[-1]["reason"] if last else "founded"
        scores = {k: last[-1][k] for k in ("lexical", "vector", "cast", "cast_rare", "identity")} if last else None
        db.execute("insert into instance_of values (?,?,?,?,?,?)",
                   (doc_id, node_id, i, last[-1]["pass"] if last else 1, reason, json.dumps(scores)))
    for o in offers:
        db.execute("insert into offer values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (o["doc_id"], o["node_id"], o["parent"], o["parent_version"], o["pass"], o["lexical"], o["vector"],
                    o["cast"], o["cast_rare"], o["identity"], o["offered"], o["verdict"], o["reason"]))
    db.executemany("insert into leaf values (?,?,?)", leaves)
    db.commit()
    multi = sum(1 for i, p in enumerate(parents.rows) if parents.alive[i] and len(p["children"]) > 1)
    print(f"written: {sum(parents.alive)} parents ({multi} with two or more children), {len(edges)} up-edges, "
          f"{len(offers)} offer rows, {len(leaves)} leaves; ${llm.SPENT:.2f}")
    db.close()


def offer_sort(row):
    return (not row[0], -row[1])


def identity_last(item):
    return (1 if item[1]["identity"] else 0, item[1]["first_unit"], item[0])


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    arm = set(sys.argv[2].split(",")) if len(sys.argv) == 3 else {"lexical", "vector", "cast", "identity"}
    run(Path(sys.argv[1]), arm)
