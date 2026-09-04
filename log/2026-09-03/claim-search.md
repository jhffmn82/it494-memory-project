# Adversarial search: the voice-lineage collision rule

2026-09-03. Candidate stated by Justin and searched the same day, per the house rule that an
absence claim needs a documented search. Four parallel probes (agent memory systems; KG
provenance and truth discovery; arXiv and ACL 2024 to 2026; dialogue, belief revision, and
argumentation), about 100 queries, every hit read at the primary source (code, paper HTML or
PDF, or the platform's own help pages). The three load-bearing citations below were re-fetched
and quoted directly before this was written.

## The candidate

Two facts collide when they share a subject and a functional predicate and differ in object.
Same voice and later time: SUPERSEDED (both trace through produced_by to the same author or
speaker). Different voices: CONTESTED (both kept, both served with their source class, higher
class first, nothing invalidated; only the user deprecates). No model call decides. The
assistant's own turns are structurally unable to invalidate the user's.

## Verdict: PARTIALLY OCCUPIED. Not a novelty claim. Two narrow pieces survive as measurements.

### What is already done, with the source

**The same-voice / different-voice rule itself is published, in the conversational setting.**
Chen, Lau and Frermann, "CIG: Measuring Conversational Information Gain in Deliberative
Dialogues with Semantic Memory Dynamics", arXiv:2604.15647 (Apr 2026), section 4, extending
Mem0 to multi-party dialogue: "we restrict operations to the same-speaker subset"; "If S(A) is
empty or contains only neutral relations, we trigger ADD ... this ensures that parallel framings
or contested claims from other participants are preserved as distinct entries." Same-speaker
contradictions replace the old claim. Two differences from the candidate: the contradiction
relation is decided by "An LLM-based NLI judge", and the setting is multi-party human
deliberation, not a user and an assistant. The rule is instrumentation for their metric, not
their contribution.

**The rule is also stated as a design rule for documents.** Miodrag Cekikj, "Making the Knowledge
Layer a Graph You Actually Traverse", Towards Data Science, 2026-08-20: "a newer version of the
same rule from the same authority expires the old edge automatically, because that is
versioning, not disagreement"; "two current sources, different authorities, incompatible
statements is surfaced, recorded as an unresolved contradiction object with an accountable
owner, and never resolved by the machine." Practitioner article, not peer reviewed, insurance
policy domain, no source-class ordering.

**Same-author-only supersession is a decade old in nanopublications.** Kuhn et al., "Semantic
micro-contributions with decentralized nanopublication services", PeerJ CS 2021: "updated
versions and retractions should only be considered valid if authorized by the author of the
original nanopublication ... we only consider them valid if the retraction or update is signed
with the same key pair"; new versions declared with npx:supersedes. Conflicting nanopublications
by different authors coexist with no adjudication.

**Contested values coexisting with references, human-only deprecation with a mandatory reason,
end-time qualifiers for outdated-but-correct values: Wikidata policy** (Help:Statements,
Help:Ranking, Help:Deprecation). The rank field in SCHEMA.md is Wikidata's rank system by name.

**Recording speaker or source class on memories is common.** Mem0 `attributed_to` user/assistant;
MemOS origin signatures (user input vs inference output); Eywa (arXiv:2605.30771) speaker role on
evidence records; Google ADK event author USER/MODEL/TOOL; TMA-NM (arXiv:2606.24322) origin in
{user, trusted_tool, agent, untrusted_external} as an integrity lattice; MemTX (arXiv:2607.23929)
numeric source authority where "a higher-authority candidate supersedes the old record ... equal
authority from different sources is quarantined for user review."

**"User statement outranks agent inference" is stated repeatedly.** The 2603.07670 survey
recommends "source attribution (user statement >> agent inference)"; Infini Memory
(arXiv:2606.10677) enforces it by prompt; Google's Sessions and Memory whitepaper (Nov 2025)
has a trust hierarchy where "higher-trust sources override lower-trust ones"; XTrace XMem blog:
"a user-stated preference outranks an LLM inference".

**Model-free supersession is well occupied, by time.** arXiv:2606.01435 "Don't Ask the LLM to
Track Freshness" (max over serial numbers), MemStrata 2606.26511, TEPA 2608.07429, GPM
2608.12476 (same user, same attribute, explicit supersedes edge). All speaker-blind or
single-user.

**The principle that speakers may disagree with each other but not with themselves** is in
Beyer, Loaiciga and Schlangen (NAACL 2021) as a test suite, in Farkas and Bruce 2010 as
per-speaker commitment sets kept out of the common ground, and in Hamblin and Walton-Krabbe
commitment stores, where only the owner retracts.

**The opposite design is the mainstream.** Zep/Graphiti: an LLM identifies contradictions and
"consistently prioritizes new information", source-blind (arXiv:2501.13956; edge_operations.py
and dedupe_edges.py read). Mem0: LLM picks ADD/UPDATE/DELETE with no role in the update prompt.
Letta: last write wins, agent tool call rewrites blocks. LangMem, A-MEM: LLM judgment. Truth
discovery (TruthFinder, Knowledge Vault, Li et al. 2016) adjudicates by estimated source
reliability. GPM withholds unresolved sides from the public projection; MemTX quarantines them.

### What no probe found, stated with the searches that failed

1. **One system applying the voice-lineage rule uniformly across conversations and documents**,
   with the user/assistant split as one case of it. CIG does conversations; Cekikj does documents;
   nanopublications do signed assertions. Queries 12, 19 (probe 2), 20 (probe 3), 5 and 21
   (probe 4) returned nothing combining them.
2. **Contested pairs SERVED, both sides, with attribution, at read time.** Every structural system
   found either resolves (time, authority order, trust score), quarantines (MemTX), withholds
   (GPM), or audits the loser out of default reads (TOKI). Eywa's read path "does not decide which
   of two active state facts is the current truth" and has no attribution rendering. Queries 8,
   12, 18 (probe 3) and 27 (probe 2).
3. **A source-class ladder over document kinds** (canonical, published, record, authored, user
   turn, assistant turn, tool output). Found: role sets (user/assistant/tool), numeric authority,
   summary-vs-raw tiers. Not found: document-kind classes used to order a contested pair.
   Queries 6 and 17 (probe 3).
4. **Any benchmark separating user-self-update from assistant-contradicts-user.** LongMemEval,
   LoCoMo, MemoryAgentBench, MemConflict, BEAM, GroupMemBench, AgentMemBench all resolve by
   recency or do not evaluate conflicts. GroupMemBench (arXiv:2605.14498) names the gap
   ("speaker-grounded belief tracking") and does not fill it.
5. **Belief revision using source identity as the switch between revision and merging.**
   Hunter-Booth 2015, Singleton-Booth 2022, Ebrahimi 2017 use source identity to weight trust
   and still resolve. Nobody ties Katsuno-Mendelzon update-vs-revision to speaker identity.

Caveats: the DASFAA 2012 "Provenance Based Conflict Handling Strategies" chapter, Noy et al. 2019
(industry KGs), and Konieczny et al. 2023 "Belief Reconfiguration" were paywalled and read only
as snippets; a same-source rule hidden in any of them cannot be excluded.

## What this means for the paper

- **Do not write "we introduce" for the rule.** CIG, Cekikj, and nanopublications are cited as
  the rule's prior statements, with the candidate positioned as their unification and as the
  first application to the user/assistant boundary in an assistant's memory. That is a framing
  sentence, not a contribution.
- **Two measurements survive as contributions in the rigor-over-novelty frame** (per
  docs/RESEARCH.md and the 08-28 decision):
  - **The cost and effect of refusing model adjudication.** Same store, same corpus, two
    collision policies: voice-lineage (no model) versus LLM-judged invalidation (the Zep design).
    Report knowledge-update accuracy on LongMemEval's 78 questions (where both designs agree,
    same voice) and, separately, the count of user facts invalidated by assistant turns under
    each policy on the local transcript smoke test and on GraphRAG-Bench's own answer traces.
    No one has published the second number.
  - **Interference on contested pairs in a mixed store.** In the combined store (plan section 5),
    count contested pairs by source-class pairing (canonical vs canonical, published vs
    published, user vs assistant) and measure whether serving both with attribution changes
    answer accuracy against resolving by recency. This is the oracle-vs-_s shape with source
    class as the variable.
- **Cite against, explicitly:** CIG 2604.15647, Cekikj 2026, Kuhn et al. 2021, Wikidata
  Help:Ranking, TMA-NM 2606.24322, MemTX 2607.23929, GPM 2608.12476, Eywa 2605.30771, TOKI
  2606.06240, GroupMemBench 2605.14498, Zep 2501.13956, the 2603.07670 survey.
- **Add to the reading list, unread in full and close to this work:** CIG 2604.15647 (section 4
  is a page), GroupMemBench 2605.14498, MemTX 2607.23929, "When Memory Becomes Authority"
  2608.01679 (system/user/assistant/tool roles, "not an intrinsic ranking").

## The design does not change

The rule stays in the build because it is right for the tool, and the search confirms the
mainstream does the opposite. What changed is only the sentence the paper is allowed to say
about it.
