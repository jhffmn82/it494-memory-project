# Implementation: Wiki generator and structure comparison

Prepared by the assistant.

The wiki is a projection of the store, not a subsystem (build plan, stage 9). Its entire job is to render what the pipeline already made, plus the one piece of real analysis that rides on it: the structure-versus-fan-wiki comparison from the testing outline. Everything here is read-only over the store; the generator writes only to `site/` and `wiki/` output directories. It can run against a half-built store from the first week the distiller emits anything, which is what makes it the standing progress demo.

## Modules

`wiki/store_reader.py`. Read-only loaders; no other wiki module touches store files directly.
`load_store(store_dir) -> Store`: parses entities, aliases, fact rows, merge ledger, plus segment spans and document titles (quote_for and the quote-verification test need them), fails loudly on any malformed line.
`current_attributes(store, entity_id) -> dict[attr, AttrView]`: applies later-assertion-wins per subject-predicate, each AttrView carrying value, superseding chain, and merge ledger trail.
`attributes_at(store, entity_id, position) -> dict`: same, truncated at a narrative position (asserted_at).
`members_of(store, group_id) -> list[entity_id]`: query over membership-class fact rows (member_of, allegiance; the predicate whitelist lives in config, see schema gaps).
`quote_for(store, fact_id) -> (quote, seg_id, doc_title)`: the receipt behind any rendered claim.

`wiki/render.py`. jinja2 templates, static HTML, no server.
`build_site(store_dir, out_dir) -> SiteReport`: renders everything that exists, returns page and link counts.
`render_entity_page(store, entity_id) -> str`: attributes with their fact rows and quotes expandable, superseded values shown struck-through with the superseding row beside them.
`render_group_page(store, group_id) -> str`: membership list, each row linking member page and source quote.
`render_timeline_page(store, entity_id) -> str`: fact rows in asserted_at order, merge points and supersessions marked.
`render_index(store) -> str`: all entities by kind, all groups, build timestamp.

`wiki/align.py`. Entity alignment against the fan wiki, deterministic first.
`load_fanwiki(dump_path) -> list[WikiPage]`: parses a downloaded MediaWiki dump into title, redirect titles, and infobox key-value pairs. Absent a published dump, fall back to the MediaWiki API for titles, redirects, and the mapped infobox fields only.
`align(store, wiki_pages) -> list[Alignment]`: exact and normalized name matching over canonical names plus the alias ledger; redirects count as aliases on the wiki side.
`align_residue(store, wiki_pages, unmatched, tier) -> list[Alignment]`: model call for ambiguous leftovers only, through `generate` which requires the tier (contract below).

`wiki/compare.py`. The measured half.
`entity_coverage(alignments, wiki_pages, store) -> Coverage`: matched, harness-missed, harness-only counts and rates.
`relation_recall(alignments, store, mapping) -> Recall`: per-predicate recall of wiki infobox relations, given a frozen predicate-to-infobox-field mapping.
`timeline_agreement(alignments, store, wiki_events) -> Agreement`: pairwise ordering agreement on aligned events. wiki_events is not parser output (infoboxes carry no event sequences); it is a hand-transcribed list of roughly thirty events from the wiki's chronology pages, logged as hand work.
`write_comparison(out_dir)`: comparison.jsonl plus a markdown report with the disagreement list for text adjudication.

`wiki/portraits.py`. Optional, last.
`appearance_description(store, entity_id, tier) -> str | Rejection`: composes a portrait prompt from appearance-class attributes via `generate`.
`fetch_portrait(desc, entity_id, out_dir) -> path`: image API call, writes image plus a manifest line naming the fact rows behind the description.

## Data touched

Reads: Entity page, Alias record, Fact row (including same_as and supersession chains), Merge ledger entry, Segment and Document (only through quote_for, for source titles). Leaves and node rollups are read only if an arc-navigation sidebar is added; not required. Writes nothing into the store.

Schema gaps to flag: (1) no Alignment object exists in 10_data_model; define `{align_id, entity_id, wiki_title, method: alias|model, score}` locally as `wiki/alignments.jsonl`, promote to the data model if the comparison becomes load-bearing for the paper. (2) Nothing marks which predicates are appearance-class (portraits) or membership-class (group pages); use small whitelists in config, not a schema change. (3) The fan wiki side (WikiPage) is external data with no store schema; it stays outside the store by design.

## Contracts

Two model-called parts, both through `generate` with its standard rule: validate against the schema, retry once with the validation error appended, then record a Rejection.

Alignment residue: schema `{wiki_title: str, entity_id: str|null, confident: bool, evidence: str}`. Reject if a non-null entity_id is not in the store, if evidence is empty when confident is true, or if the same wiki_title returns two entities across the batch (null means no match and is valid). Non-confident results land in a manual-review file, never in alignments.jsonl.

Portrait description: schema `{description: str, fact_ids: [str]}`. Reject mechanically if any cited fact_id is not an appearance-class row for that entity; the converse check (the description names an uncited attribute) is not machine-checkable and runs as a logged eye check per portrait, acceptable because portraits are demo-only. This is the receipt trail the demo doc calls the point: a wrong portrait must trace to a wrong extraction.

## Build sequence

1. load_store, current_attributes, attributes_at over a fixture store: the Scabbers rows from 10_data_model plus the merge artifacts maintain would write (re-attached superseded row, alias mapping, ledger entry), hand-authored once, because the raw rows carry different subject ids and the wiki performs no merges. Test: current_attributes(pettigrew_e01) returns animagus not rat; attributes_at(pettigrew_e01, ch03) returns rat.
2. quote_for, render_entity_page, build_site skeleton and index. Runs the day organize emits its first entities. Test: every quote on a rendered page string-matches its segment source.
3. members_of, group and timeline pages, cross-links. Test: link checker over the built site, zero dead links; the Scabbers timeline shows the same_as merge point.
4. Supersession rendering polish: struck-through prior values, showpiece page reviewed by eye. Test: fixture supersession renders both states.
5. load_fanwiki and deterministic align on the measured corpus dump. Test: spot-check twenty alignments by hand; alias-ledger matches agree with manual judgment.
6. align_residue model call, then compare.py metrics with the predicate mapping frozen in writing before scoring. Test: metrics recompute identically from alignments.jsonl (pure functions over files).
7. Portraits, only if hours remain. Test: every manifest line's fact_ids resolve and are appearance-class.

## Sanity risks

Parsing the fan wiki is the real work. The generator is small; a MediaWiki dump with hand-edited infobox templates is not, and this sub-step can quietly outgrow the whole component. Timebox it: titles and redirects first (enough for entity coverage), infoboxes only for the predicates in the frozen mapping.

Relation recall can be a manufactured number. Wiki infobox fields do not map one-to-one onto predicates; freeze the mapping before looking at scores, report per-predicate, and adjudicate disagreements by the text per the testing outline, reporting harness-right cases rather than discarding them.

Alignment lives or dies on minor characters, exactly where the certified questions live. Expect the deterministic pass to cover the famous names and the residue to be large; budget the manual-review file as real reading time.

## Done means

One command builds the site from the store; the build report shows page counts and zero dead links. Demo corpus: human-eyes pass logged, with the supersession showpiece page rendering both states and every attribute expandable to fact rows and quotes. Measured corpus: comparison.jsonl and its report exist with three numbers (entity coverage rate, per-predicate relation recall, timeline ordering agreement), an alignment file with method per row, and the adjudicated disagreement list. Portraits, if built, ship with a manifest tracing every image to its fact rows; if cut, the cut is logged the day it happens per the plan of record. The two halves gate separately: the demo bar is fall's; the measured bar inherits the cold-corpus schedule and may land in spring without this component being late.

## **Sanity check**

Challenged every signature against 10_data_model and every build step against what earlier steps produce. Held: the read-only boundary, the module split, the frozen predicate mapping, the timebox on wiki parsing, the deterministic-first alignment. Fixed: load_store omitted segments and documents that quote_for and the quote test require; the day-one fixture could not pass its own test from the literal Scabbers rows (different subject ids, no merge stage in the wiki), so it now includes maintain's merge artifacts; quote_for and members_of moved to the steps that first need them; wiki_events had no producer and is now declared hand work; the portrait contract's uncited-attribute rejection was unenforceable and is now an eye check; the measured-corpus done bar is gated on the cold-corpus schedule rather than implied for fall.
