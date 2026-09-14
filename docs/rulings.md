# Rulings ledger

Every design ruling that shapes ThreadAtlas, one line each, in the order made, grouped by
subject. The daily logs under `log/` are snapshots of their day and are never edited; this
ledger is the recency layer over them. **On any subject, the latest line is current truth.**
Superseded lines stay so the path is visible and a rejected idea is not raised again.

Columns: the date the ruling was made; the ruling; where it is recorded (`code` means it lives
only in the notebook that ran, `chat` means it was ruled in conversation and first written down
here on 2026-09-13); its status. A new ruling is a new line, never an edit of an old one.

## Corpus and artifacts

| date | ruling | recorded | status |
|---|---|---|---|
| 09-02 | The corpus is public domain literature (Oz, Holmes, Greek and Roman), so it can be published; copyrighted modern fiction is excluded. | log/2026-09-02/README.md:24 | stands |
| 09-04 | `chinese/` is out; the Thebaid is removed; greek is 31 files. | log/2026-09-04/inventory.md rulings 1 and 2 | stands |
| 09-04 | GraphRAG-Bench's 20 contexts are unpacked to 20 text files, as is. | inventory.md ruling 5 | stands |
| 09-04 | The papers are the 142 reference PDFs in a private Kaggle dataset; the extractor reads a PDF like any other file. | inventory.md ruling 6 | superseded 09-09: the paper corpus is the 100 CC-BY kg-rag-cc papers, inside the public raw dataset, text carried in full |
| 09-04 | The public dataset's license is MIT with attribution in the manifests. | inventory.md ruling 7 | superseded 09-09 for the raw dataset: the label is "other", three licenses by folder (log/2026-09-09/README.md) |
| 09-04 | The manifest is packaging, never an input. | inventory.md ruling 8 | stands; block 1 reads it only to verify bytes |
| 09-04 | The extractor lives on Kaggle for now; eventually a desktop tool. | inventory.md ruling 11 | stands |
| 09-04 | LongMemEval is fall; the evaluation is scored at the evaluation step. | inventory.md ruling 13 | stands |
| 09-08 | The system is ThreadAtlas; narrative cells are the primary representation; the wiki is a read model; document-local entities attach to global parents. | log/2026-09-08/threadatlas-decision.md:17-26 | stands; cell primacy narrowed for chats on 09-12 (chats get no cells) |
| 09-09 | The papers corpus is 100 CC-BY papers gathered from OpenAlex, with `attribution.jsonl` in the export; nothing is withheld. | log/2026-09-09/README.md | stands |
| 09-09 | Block 13 runs the first three Oz books, not one. | log/2026-09-09/README.md | stands |
| 09-10 | Block 12 runs one user's whole LongMemEval history (gpt4_2ba83207) as the test input for the global step. | log/2026-09-10/decisions-ingestor-1.7.md:14-15 | extended 09-11 and 09-12: the answer sessions of 13 other questions are loaded with it (71 sessions) |
| 09-13 | Raw dataset v4 carries `longmemeval_s.json`; the extractor unpacks it itself. | log/2026-09-13/README.md | stands |
| 09-13 | A Step 1 dataset is made from the ingestor's run and documented like Step 0: `dataset/step1/`, packed by `scripts/pack_step1_public.py`, published as `jhffmn/it494-threadatlas-step1`. | chat; log/2026-09-13/global-layer.md | stands |

## Step 0: what the extractor is

| date | ruling | recorded | status |
|---|---|---|---|
| 09-04 | The extractor sees a raw file and nothing else: no manifest, no metadata, no question set, no per-corpus branch; the format is sniffed from the bytes. | log/2026-09-04/inventory.md, the governing rule | stands |
| 09-04 | Source class follows the sniffed format: chat to `record`, paper to `published`, book to `canonical`. | inventory.md ruling 9 | narrowed 09-05: a text document takes the model's answer |
| 09-05 | No font sizes and no code deciding where a break may go: the document's non-blank lines are numbered and shown whole in one call; the model answers by line number and copies the line; code verifies the copy. | log/2026-09-05/README.md ruling 2 | stands |
| 09-05 | Keep every byte: regions are labels in the piece's `kind`, pieces tile the document. | 09-05/README.md ruling 3 | stands |
| 09-05 | Sentences are the address unit when a file has no usable lines. | 09-05/README.md ruling 4 | stands |
| 09-05 | Units are the model's too: sub-split over 4,000 words, merge short pieces, group the outline; a group over the cap is dissolved. | 09-05/README.md ruling 5 | stands; a group is also cut where the kind or the date changes (1.8) |
| 09-05 | A publication becomes the author when no person is named, flagged. | 09-05/README.md ruling 9 | stands |
| 09-05 | Retry on a flag: Luna again; Terra only for a document under 80,000 tokens. | 09-05/README.md ruling 11 | stands |
| 09-09 | A record naming a file outside the raw dataset is refused, not truncated. | log/2026-09-09/README.md | stands |
| 09-13 | Every model call runs on OpenAI's Flex tier. | log/2026-09-13/README.md | stands |

## Units, pieces and dates

| date | ruling | recorded | status |
|---|---|---|---|
| 09-04 | The document holds its text once; units are character ranges into it; every offset is a document offset. | log/2026-09-04/README.md:26-31 | stands |
| 09-04 | A document is an entity in its own right; two documents never merge. | 09-04/README.md:24-25 | stands |
| 09-04 | Units carry a time range `occurred_at` to `occurred_until`, and a unit never spans a day change. | 09-04/README.md:117-121 | superseded 09-09 (`occurred_until` dropped) and 09-10 (no day cut) |
| 09-04 | Unknown dates stay null, never inferred. | 09-04/README.md:119-121 | superseded 09-13: a work's date is looked up when its page states none |
| 09-05 | No dates on text or PDF pieces; the unit carries the document's date. | log/2026-09-05/README.md ruling 6 | superseded 09-13: every piece takes the date of the work it lies in |
| 09-05 | The date asked for is the original work's, never the edition's or translation's. | 09-05/README.md ruling 6 | stands, restated 09-13 |
| 09-05 | No inferred dates; a document whose file states no date stays null. | 09-05/README.md ruling 7 | superseded 09-13 |
| 09-09 | `occurred_until` is gone from the unit and the fact: the two ends never differed. | log/2026-09-09/README.md; fa48997 | stands |
| 09-10 | A unit is a snapshot in time and carries one time. | log/2026-09-10/chat-rulings.md:43-44 | stands |
| 09-13 | Every unit and every fact is dated wherever the source allows; a document takes its earliest unit's date. The 09-10 wording that left multi-date sessions undated was not an informed ruling and is not cited. | chat; log/2026-09-13/README.md | stands |
| 09-13 | Books are dated by when the work was written, BC and approximate included: the page first, then a web search, then null with the reason in the flags. | chat; code (extractor 1.8) | stands |
| 09-13 | `occurred_at` forms: `YYYY`, `YYYY-MM`, `YYYY-MM-DD`, a timestamp, a signed BC year counting a year zero, a trailing `~` for approximate, `/` joining the ends of a range; the date's source goes in the document's flags. | code (extractor 1.8); dataset/step0/SCHEMA.md:9-15 | stands |
| 09-13 | A volume of several works is dated work by work, and a unit never spans two dates. | code (extractor 1.8) | stands |

## Chats

| date | ruling | recorded | status |
|---|---|---|---|
| 09-04 | LongMemEval `_s` is the source; a session is a document; one JSON file per distinct non-empty session; the oracle file and `has_answer` are not used. | log/2026-09-04/inventory.md ruling 3 | source and session-as-document stand; one file per distinct session superseded 09-13 |
| 09-04 | Units are turn groups cut by size at turn boundaries, never a turn alone, a short tail merged back. | inventory.md ruling 4 | superseded 09-10 |
| 09-04 | Turn-as-unit was weighed and declined. | 09-04/README.md:129-131 | reversed 09-10 |
| 09-05 | The chat header is a `front_matter` piece. | log/2026-09-05/README.md ruling 8 | superseded 09-10: there is no header piece |
| 09-09 | A chat's title is the session id its file states; a title is the source's own name, an identifier counts, and a title is never parsed from a filename. Author stays null on a chat. | log/2026-09-09/README.md; fa48997 | stands |
| 09-10 | The ingestor rerun is held until chat preprocessing is redesigned. | log/2026-09-10/chat-rulings.md:39 | discharged 09-10 (1.7 ran) |
| 09-10 | A chat document is a conversation; every turn keeps its speaker, position and time; a history is an ordering over conversations. | chat-rulings.md:40-42 | stands |
| 09-10 | A chat unit is an exchange (a user turn and the reply). | chat-rulings.md:45-46 | superseded the same day by ruling 7 |
| 09-10 | Chats are preprocessed by a script specific to LongMemEval, not the general extractor. | chat-rulings.md:47-48 | partly superseded 09-13: block 0 unpacks the benchmark file, then the general extractor reads the result like any chat |
| 09-10 | A LongMemEval session is a document titled by its session id; a turn is a unit named `SESSION <id> TURN <n> <date>`; a session placed on several dates keeps none. | chat-rulings.md:54-60 | the unit shape stands; the undated case superseded 09-13 |
| 09-10 | The evaluation filters by the question's haystack session ids, never by date. | chat-rulings.md:57-59 | stands (no evaluation built yet) |
| 09-10 | The output schema must carry Gemini, Grok, Claude and OpenAI chats: a conversation with a title, a time and an author, each unit with its own time. The placement record and a `tool` piece kind were PROPOSED and never ruled. | chat-rulings.md:49-52 | stands as a requirement; the proposed records are open |
| 09-08 | Review rulings 4 (the set node) and 6 (a controlled predicate list at Step 2) were asked for and never ruled. | log/2026-09-08/review.md | open |
| 09-13 | LongMemEval is unpacked into one folder per history; a session used by several histories is a separate document in each, dated as that history dates it; nothing from the test itself is written. | chat; code (extractor 1.8, block 0) | stands |
| 09-13 | Each chat turn carries its own timestamp; empty sessions and empty turns are skipped and counted. | code (extractor 1.8) | stands |

## Step 1: reading a document

| date | ruling | recorded | status |
|---|---|---|---|
| 09-06 | Every unit is derived; nothing branches on kind. | log/2026-09-06/audit.md decision 13 | superseded 09-07: triage leaves out kinds that are not the work |
| 09-06 | Predicates are the model's own strings; there is no controlled list at Step 1 and predicates are never merged or renamed. | log/2026-09-06/decisions-ingestor-0.5.md 12, 39, 41; audit.md 32 | stands; ruled repeatedly, do not raise merging again |
| 09-06 | A running roster carried across units (rolling reconciliation). | decisions-ingestor-0.5.md 2, 13 | superseded 09-07 by decisions 31 and 33: no look back; reconciliation at the end of the document |
| 09-07 | A small entity's facts (under 4) get a Luna support call; a major with 4 or more is adjudicated on Terra. | log/2026-09-07/decisions-ingestor-0.7.md 43 | stands |
| 09-07 | Triage may not leave out more than half a document; front matter is triage's decision, not a rule. | decisions-ingestor-0.7.md 63; log/2026-09-07/ingestor.md:149-160 | the half guard stands; front matter and license are excluded by rule in 1.7 (`BOILERPLATE`), so that half is superseded by code |
| 09-07 | Triage of references and appendices stands as it is, inconsistency across documents accepted. | log/2026-09-07/ingestor.md:164-165 | stands |
| 09-07 | Two pruning rules and no queue cap: entities of one unit are never paired, and a pair ruled different is not offered again (decision 44); scored candidate rows stay in the package (decision 57). | decisions-ingestor-0.7.md 44, 57 | stands (`ineligible()`, `candidate` records) |
| 09-07 | The spending stop is a per-block budget; the roll-up is written beside its package. | ingestor.md:149-156 | stands |
| 09-07 | Kind is an open vocabulary, and a merged entity settles on one kind. | ingestor.md:170-176 | stands |
| 09-07 | The embedding interface stays (decision 64, withdrawn). | decisions-ingestor-0.7.md 64 | reversed the same day: the removal was applied (ingestor.md:177); the ingestor has no `embed()` |
| 09-07 | The one-reading path: a document of one unit takes about four calls; every chat is two units. | log/2026-09-07/ingestor.md:90-126 | superseded 09-10 (chats have many units) and again 09-12 |
| 09-08 | Ids are readable (`<doc_id[:8]>:doc`, `:n<i>`, `:u<n>:f<n>`), not content hashes. | log/2026-09-08/README.md:15-22 | stands |
| 09-10 | The ingestor work lands on `claude/kg-rag-cc-corpus`. | log/2026-09-10/decisions-ingestor-1.7.md:5-6 | stands |
| 09-10 | A chat has many units, so it takes the full path with the roll-up, not the one-reading shortcut. | decisions-ingestor-1.7.md:11-13 | reversed 09-12 |
| 09-10 | Chat edits: the user is a standing major on a user turn; a speaker note in the fact prompt and `user stated` facts; chat majors take their cells as abstracts; no consolidation in chats; triage never offers turns; run times in the receipt. | log/2026-09-11/README.md ruling 9 (confirmed as rulings) | user-major and stated facts stand; cells-as-abstracts and the rest superseded 09-12 by the one-call reading |
| 09-11 | Try the Flex tier; the judge and the document abstract go on Luna for chats only. | log/2026-09-11/README.md ruling 3 | tier stands; the chat judge and fold are gone since 09-12 |
| 09-11 | No reply cache. Fix the ellipsis prompt first; no quote widening. | 09-11/README.md rulings 4, 5 | stands |
| 09-11 | Version label `threadatlas-ingestor 1.7`. | 09-11/README.md ruling 7 | stands |
| 09-11 | The complexity audit's four groups are approved as separate diffs: cuts, restructure, no speaker-cut code, no chat graphs. | 09-11/README.md ruling 8 | stands, applied as prune steps 10 to 17 |
| 09-11 | `reconcile` stays at 99 lines; it is not split. | 09-11/README.md ruling 11 | stands |
| 09-12 | The assistant's specifics are facts. | log/2026-09-12/README.md ruling 1 | stands |
| 09-12 | The chat fact prompt is narrowed: a user turn yields the user's own details and stated facts; an assistant turn the specifics it gives the user; books and papers keep the general instruction. | 09-12/README.md ruling 3 | stands, carried into the session prompt |
| 09-12 | A chat session is read in one Luna call (stretches of 40,000 characters for a long one); each fact is tied to its turn; no judge, cells or fold for chats; the reading's summary is the abstract. | 09-12/README.md ruling 4; code | stands |
| 09-12 | Every user sentence stating a detail becomes one stated fact quoting the whole sentence. | 09-12/README.md ruling 5 | stands |
| 09-12 | Step 1 is frozen on this version; its packages feed the global merge. | 09-12/README.md ruling 7 | stands |
| 09-13 | Block 12 selects sessions by path (history folder plus answer paths), never by title. | log/2026-09-13/README.md; e15623d | stands |

## Facts and quotes

| date | ruling | recorded | status |
|---|---|---|---|
| 09-06 | Every stored fact carries a verbatim quote located in its unit; a quote that is not found is rejected and logged, never stored. | SCHEMA.md; log/2026-09-06/decisions-ingestor-0.5.md | stands |
| 09-06 | An ellipsis quote is kept as pieces. | decisions-ingestor-0.5.md 34 | reversed 09-08: `locate` refuses an ellipsis |
| 09-06 | The `words` path takes only edge rewording. | decisions-ingestor-0.5.md 36; 0.7 decision 47 | stands |
| 09-07 | A quote must state its fact (R1); an unsupported fact is corrected against its passage or dumped, never stored with a flag or a rank (R3). | log/2026-09-07/decisions-ingestor-0.8.md R1, R3 | stands |
| 09-07 | A fact whose object restates its subject is rejected as `self_reference`. | log/2026-09-07/ingestor.md:170 | stands |
| 09-07 | A fact carries `occurred_at` and `occurred_until` copied from its unit (R2). | decisions-ingestor-0.8.md R2 | half superseded 09-09: `occurred_at` only |
| 09-07 | A quote may not span a change of speaker (decision 46). | decisions-ingestor-0.7.md 46 | moot since 09-10 (a chat unit is one turn); the code was dropped 09-11 (B7) |
| 09-11 | A flagged fact the correction step skips is dropped. | log/2026-09-11/README.md ruling 10 | stands |
| 09-12 | Duplicate stated facts are dropped (`drop_repeated_stated`). | code | stands |

## Salience, majors and minors

| date | ruling | recorded | status |
|---|---|---|---|
| 09-04 | Salience is decided per document at the end of ingestion; only document-majors carry a dossier into the merge. | log/2026-09-04/README.md:19-22 | the merge budget behind it is gone; superseded 09-07 |
| 09-04 | Minors stay mentions with a null `node_id`; a fact between two minors is not stored. | 09-04/README.md:131-134 | minors have no node (stands); mentions not written since 09-08 |
| 09-06 | A fact whose subject is minor is not stored. | log/2026-09-06/audit.md 9, 24 | reversed by 27 (riding), then restored 09-11 |
| 09-06 | Riding: a minor's fact rides to the major it concerns (`direction: about`). | decisions-ingestor-0.5.md 11; audit.md 27 | dropped 09-07 by a9bff5b without a ruling; ruled gone 09-11 |
| 09-07 | An entity is a document-major if a unit called it major, or the abstract names it, or it carries a proper name (R6). | decisions-ingestor-0.8.md R6 | narrowed the same night (dcd11c0): only a unit's call promotes; the abstract and proper names do not |
| 09-07 | An entity with nothing to summarise (no facts, no cells) is not a major (decision 52). | decisions-ingestor-0.7.md 52 | stands |
| 09-11 | A fact whose subject is minor in every unit is not stored; the completion record keeps the count. | log/2026-09-11/README.md ruling 1 | stands |
| 09-12 | The user is a standing major on a user turn; the global merge will not make a `user` entity. | log/2026-09-11/README.md ruling 9; log/2026-09-10 (chat) | stands |

## Entities, identity and the global layer

| date | ruling | recorded | status |
|---|---|---|---|
| 09-03 | Global merge: corpus-global nodes, nearest-k candidates, a merge judge on the strong tier; communities deferred. | log/2026-09-03/README.md:28-52, 111-116 | superseded 09-07 (no merge); communities removed 09-04 |
| 09-04 | Community grouping is removed, not deferred. | log/2026-09-04/README.md:15-18 | stands |
| 09-06 | Same proper name and kind unite with no call; other pairs are scored (0.6 name, 0.25 co-occurrence, 0.15 profile) and judged. | log/2026-09-06/audit.md 10 | scores superseded 09-09 (0.7 name, 0.3 co-occurrence); judge round by round since decision 53 |
| 09-07 | Nothing is ever merged; it is a tree. A fact, an edge and a child node belong to one document; a parent holds no asserted content, owns no edges, and every sentence on it reduces to "N of M children say X". Dorothy is the class; each Dorothy in a book is an instance; the class is induced from its instances and has no authority over them. | docs/entity-resolution.md:161-236 (the settled section); log/README.md 09-07 entry | stands; the derived fields are a name, a kind and an abstract since 09-09 |
| 09-07 | An instant match needs both sides named, and only when nothing in `is_a` conflicts (decisions 14, 49). | decisions-ingestor-0.7.md 49 | stands |
| 09-07 | Round-by-round pairing at `SIMILAR_ENOUGH = 0.35`, strongest first, ten pairs a call (decision 53). | decisions-ingestor-0.7.md 53 | stands |
| 09-07 | A node records whether its document named it (decision 61). | decisions-ingestor-0.7.md 61 | reversed hours later (dcd11c0 cut `named`) |
| 09-07 | Contradictions are resolved within a document by the judge, which names in `holds` the fact true at the document's end; across documents nothing is resolved, a parent counts (R4). | decisions-ingestor-0.8.md R4; SCHEMA.md | stands |
| 09-09 | The profile record is dropped and the pair score renormalised. | log/2026-09-09/README.md; 0b6cc81 | stands |
| 09-13 | The first-cut attach rule of the plan (case-folded name and kind; a kind conflict stays apart; the parent named by its most frequent child name; a count-sentence abstract) is superseded by the global-layer design of that night. | chat; log/2026-09-13/global-layer.md; docs/global-layer.md | stands |
| 09-13 | One graph over everything loaded; a test filters at retrieval time on a set of documents. The one-history rule is a retrieval filter, not a build rule. | chat; log/2026-09-13/global-layer.md | stands |
| 09-13 | A parent is its own record, owned by no document: name, kind, the union of its children's aliases, a role summary (one line per document, each tied to a child id), and its instance list. It is rewritten by one model call on every attach, reading the parent as it stands and the new child; a founding child needs no call. The judge picks the name and kind from what the children carry. Kind is redefined at the global layer and never blocks an attachment. | chat; log/2026-09-13/global-layer.md | stands |
| 09-13 | Nomination is a similarity search of the child's text against every parent's text, never an exact-string test; the nearest parents are offered with three logged scores (lexical, vector, cast overlap) and a document's own identity fact as the top nomination; the judge rules attach or found with a reason; the edge carries the reason and the scores. | chat; log/2026-09-13/global-layer.md | stands |
| 09-13 | Co-occurrence is the ingestor's unit-cast Jaccard carried across documents (a rarity-weighted column logged beside it). It keeps same-name entities of different works apart and clusters documents (the 09-08 formula); it is not the uniter. | chat; log/2026-09-13/global-layer.md | stands |
| 09-13 | Chats: one salience call per session at the global layer decides which entities are nominated; the rest stay leaves under the session document. Step 1 is not rerun. Nightly pulls go through the same path. | chat; log/2026-09-13/global-layer.md | stands |
| 09-13 | The attachment key is Wikipedia's list of Baum's Oz characters (CC BY-SA 4.0) and the per-character articles, not hand labels; coverage of majors from the same roster; fact and narrative coverage later. | chat; log/2026-09-13/global-layer.md | stands |
| 09-14 | Two entities of one document are never offered to each other as a pair at the global layer; each is offered parents, and both may land under the same parent, in the first pass or the second pass over founders. | chat; log/2026-09-14/global-layer.md | stands |
| 09-14 | Packages are ingested in order, by the document's date then `source_uri`, and the rules must handle a document arriving out of order (the second pass re-offers every founder). | chat; log/2026-09-14/global-layer.md | stands |
| 09-14 | The attachment ablation is built into the pipeline as arms and run on chosen test sets, never over the entire corpus; which sets is a later ruling. The gold for the document-cluster test is open (parked). | chat; log/2026-09-14/global-layer.md | stands |

## Time and supersession

| date | ruling | recorded | status |
|---|---|---|---|
| 09-03 | The collision rule: same voice, later time supersedes; different voices are contested; across documents, no model call decides. | log/2026-09-03/README.md:149-163; claim-search.md | within a document superseded by R4 (a model call adjudicates); across documents nothing is built; SCHEMA.md still states the read rule as intent |
| 09-07 | A fact's ordering time is its `valid_from` when stated, else its unit's `occurred_at`, else the document's; an undated fact never supersedes a dated one. | SCHEMA.md (corrected 09-07) | stands as the read rule; no reader is built |
| 09-09 | `valid_to` is held. | log/2026-09-09/README.md | dropped 09-10 |
| 09-10 | `valid_to` is dropped: facts are instances as they occur; nothing decides that one stopped being true. | log/2026-09-10/decisions-ingestor-1.7.md:10 | stands |

## Store and retrieval

| date | ruling | recorded | status |
|---|---|---|---|
| 09-13 | Storage is SQLite; search is a linear scan of embeddings, no index (HNSW, IVF and a k-means tree were weighed and set aside). Vectors live in one float16 `.npy` beside the database, held in memory for the scan; the row map and header are in the database. | chat; log/2026-09-13/global-layer.md | stands |
| 09-13 | Retrieval: two flat scans (facts as rendered lines; narratives as sentences prefixed with their entity and document), one hop of expansion along node, document and parent, rerank with a hop discount, whole items packed by rank; the parent-off arm drops the parent hop. | chat; log/2026-09-13/global-layer.md | stands |

## Records dropped

| date | record | recorded | status |
|---|---|---|---|
| 09-07 | `scope_id`, `children_hash`, `dossier`, `predicate_census`, `evidence_quote`, `named`, the package header, `manifest.jsonl` | dcd11c0; decisions-ingestor-0.7.md 54, 58, 59, 60 | gone |
| 09-08 | `mention` | log/2026-09-08/README.md:31-32 | gone; only a count is kept |
| 09-09 | `profile` | log/2026-09-09/README.md | gone |
| 09-09 | `occurred_until` | log/2026-09-09/README.md | gone |
| 09-10 | `valid_to` | log/2026-09-10/decisions-ingestor-1.7.md:10 | gone |
| 09-11 | The speaker-cut code (decision 46) and chat graphs | log/2026-09-11/README.md ruling 8 | gone |

## Process and style

| date | ruling | recorded | status |
|---|---|---|---|
| 09-04 | Justin runs all code; rulings are brought one at a time with a recommendation; a ruling stands and a rejected idea does not return. | log/2026-09-04/README.md; log/2026-09-06/devlog-ingestor-0.5.md:157-161 | stands |
| 09-08 | Daily logs are the authoritative record; consolidated docs regenerate after the shape stabilises. | log/2026-09-08/threadatlas-decision.md:28-37 | refined 09-13 |
| 09-12 | The main thread does the git work; a Step 1 thread adds its version after its run. | log/2026-09-12/README.md ruling 2 | stands |
| 09-13 | The logs are snapshots in time, never corrected or annotated; the master documents (SCHEMA, BUILD, docs/, dataset/step0/, README) carry current truth; this ledger records how each ruling changed. | chat; log/2026-09-13/README.md | stands |
| 09-13 | Every fact in the record is stored as it was true; recency on contradictions forms the global truth. The narrative of a ruling is tracked so that a past mistake is not revisited. | chat | stands |
| 09-13 | The PROPOSED SCHEMA.md and BUILD.md of the cleanup are accepted. | log/2026-09-13/questions.md 1 | stands |
| 09-13 | The reference PDFs stay in git history; they are untracked at HEAD and no history is rewritten. | questions.md 2 | stands |
| 09-13 | The global merge reads one LongMemEval history: the packages whose `source_uri` starts with that history's folder. Block 12's other answer sessions are Step 1's check, not the graph's input. | questions.md 5 | stands |
| 09-13 | Merged branches are deleted; the dated logs keep their em dashes; the two root files may move with the reading apparatus. | questions.md 6 to 8 | stands |
| 09-13 | The public repository holds only what a person reads: the plan by stage, the rulings, the logs, the datasets, the notebooks, the reading apparatus. Test batteries, build tooling, the reference PDFs and the archive of superseded scripts stay on the author's machine, untracked. | chat; log/2026-09-13/README.md | stands |
| 09-13 | The global layer is built regardless of which benchmark needs it, and first: the database schema and the embedding follow from it; then the query path; then a harness that tests the query path; only when each has a solution does the full data run, in Kaggle batches (about 36 kernel hours for all chats on the frozen version, less now), the smaller corpora first. Until then every step works on the test packages already on disk, and the full data goes through the ingestor only once the whole pipeline has been tested and tuned on them to the point it is ready for testing; the full run's kernel time is paper-writing time. Testing by the end of September; October for refinement and building the datasets. | chat; docs/execution-plan.md section 1 | stands |
| 09-13 | The plan assumes everything goes as planned; the gates re-price rather than pre-cut, and the mid-October draft is written as the research paper with the resource content as its floor. | chat, on point 1 of the academic audit | stands |
| 09-13 | The fall scope: ingest, the global layer, storage, retrieval, the test harness, test and assessment, plus wiki pages over document clusters (an afternoon, after the numbers); then publish. Maintenance, deployment and a living stream of data are spring. | chat, on point 2 of the academic audit | stands |
| 09-08 | Co-occurrence survives as a signal at the global layer: the resolution ablation is restated at the up-edge as name-only against name plus co-occurrence as inputs to attachment, scored as attachment accuracy; document clusters and related works come from shared entities and meaningful co-occurrence over the document-entity graph. | log/2026-09-08/publishability-review.md:36-62; threadatlas-decision.md:107-121; wiki-projection.md:35-66 | stands; confirmed by Justin 09-13 on point 3 of the audit. The 09-13 line above that cut the resolution ablation was wrong and is superseded by this one. |
| 09-13 | The paper's purpose is a publication for PhD admission to a good program: a peer-reviewed venue, or a submission under review there when applications are read; the arXiv preprint is beside it, not instead of it. | chat, on point 3 of the audit | stands; the venue is an open ruling |
| 09-13 | The paper is submitted to the ECIR 2027 resource track on Nov 2 (build stop Oct 25, paper complete Oct 30, arXiv the day after submission); if rejected on Dec 7, an EACL 2027 workshop on Dec 15, then PVLDB's Jan 1 deadline. | chat; log/2026-09-13/venues.md | stands |
| 09-14 | The parent is the entry point to a wiki page. Its summary is the model-written paragraph of the works the entity appeared in (the role summary, one line per instance, each carrying its child's id); below it the page lists the facts and narratives deterministically, each under the document that owns it. The count-line alternative (outside feedback of 09-14) is declined. | chat, on the global-layer question A | stands |
| standing | No em dashes in any document. No copyrighted modern fiction is named in any public artifact. No lambdas in drafted code. Nothing is published to Kaggle and nothing leaves git history without Justin's yes. | chat | stands |
