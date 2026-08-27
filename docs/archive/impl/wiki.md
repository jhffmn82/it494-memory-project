> **SUPERSEDED 2026-08-28** by `03_design.md` and `05_fall_plan.md`. These module specs were written against the superseded data model and build plan. Their end-of-file gap lists were never absorbed until 08-28; the surviving items (the `Mention` record, `Rejection.target`, `Rejection.unit_id`, `Run.answer_text`, `merged_into`) are now in `03_design.md`.
> Kept for the record; do not build from it. Index: `docs/README.md`.

# Implementation: Wiki generator and structure comparison

The wiki is a projection of the store, not a subsystem (build plan, stage 9): it renders what the pipeline already made, plus one piece of real analysis, the structure-versus-fan-wiki comparison from the testing outline. It is read-only over the store, writes only to `site/` and `wiki/`, and runs against a half-built store from the distiller's first week: the standing progress demo.

## Modules

`wiki/store_reader.py`. Read-only loaders; no other wiki module touches store files directly.
`load_store(store_dir) -> Store`: parses entities, aliases, fact rows, merge ledger, segment spans, and document titles; fails loudly on any malformed line.
`current_attributes(store, entity_id) -> dict[attr, AttrView]`: later-assertion-wins per subject-predicate; each AttrView carries value, superseding chain, and merge ledger trail.
`attributes_at(store, entity_id, position) -> dict`: same, truncated at a narrative position (asserted_at).
`members_of(store, group_id) -> list[entity_id]`: query over membership-class fact rows (member_of, allegiance; whitelist in config).
`quote_for(store, fact_id) -> (quote, seg_id, doc_title)`: the receipt behind any rendered claim.

`wiki/render.py`. jinja2 templates, static HTML, no server.
`build_site(store_dir, out_dir) -> SiteReport`: renders everything that exists; returns page and link counts.
`render_entity_page(store, entity_id) -> str`: attributes with fact rows and quotes expandable; superseded values struck through beside their superseding row.
`render_group_page(store, group_id) -> str`: membership list, each row linking member page and source quote.
`render_timeline_page(store, entity_id) -> str`: fact rows in asserted_at order, merge points and supersessions marked.
`render_index(store) -> str`: all entities by kind, all groups, build timestamp.

`wiki/align.py`. Entity alignment against the fan wiki, deterministic first.
`load_fanwiki(dump_path) -> list[WikiPage]`: parses a MediaWiki dump into title, redirect titles, and infobox key-value pairs; absent a published dump, fall back to the API for titles, redirects, and mapped infobox fields.
`align(store, wiki_pages) -> list[Alignment]`: exact and normalized name matching over canonical names plus the alias ledger; redirects count as wiki-side aliases.
`align_residue(store, wiki_pages, unmatched, tier) -> list[Alignment]`: model call for ambiguous leftovers only, through `generate` (contract below).

`wiki/compare.py`. The measured half.
`entity_coverage(alignments, wiki_pages, store) -> Coverage`: matched, harness-missed, harness-only counts and rates.
`relation_recall(alignments, store, mapping) -> Recall`: per-predicate recall of wiki infobox relations under a frozen predicate-to-infobox-field mapping.
`timeline_agreement(alignments, store, wiki_events) -> Agreement`: pairwise ordering agreement on aligned events; wiki_events is roughly thirty events hand-transcribed from the wiki's chronology pages, since infoboxes carry no event sequences.
`write_comparison(out_dir)`: comparison.jsonl plus a markdown report with the disagreement list.

`wiki/portraits.py`. Optional, last.
`appearance_description(store, entity_id, tier) -> str | Rejection`: composes a portrait prompt from appearance-class attributes via `generate`.
`fetch_portrait(desc, entity_id, out_dir) -> path`: image API call; writes the image and a manifest line naming its source fact rows.

## Data touched

Reads: Entity page, Alias record, Fact row (same_as and supersession chains included), Merge ledger entry, Segment and Document through quote_for. Leaves and rollups only if an arc-navigation sidebar is added. Writes nothing into the store.

Three schema notes: no Alignment object exists in 10_data_model, so define `{align_id, entity_id, wiki_title, method: alias|model, score}` locally as `wiki/alignments.jsonl`, promoted if the comparison becomes load-bearing for the paper; appearance-class and membership-class predicates are unmarked (small config whitelists, not a schema change); WikiPage is external data and stays outside the store.

## Contracts

Two model calls, both through `generate` and its standard rule: validate against the schema, retry once with the error appended, then record a Rejection.

Alignment residue: schema `{wiki_title: str, entity_id: str|null, confident: bool, evidence: str}`. Reject if a non-null entity_id is not in the store, if evidence is empty while confident is true, or if the same wiki_title returns two entities across the batch (null means no match and is valid). Non-confident results land in a manual-review file, never in alignments.jsonl.

Portrait description: schema `{description: str, fact_ids: [str]}`. Reject mechanically if any cited fact_id is not an appearance-class row for that entity; the converse (a description naming an uncited attribute) is not machine-checkable and runs as a logged eye check per portrait, acceptable for a demo-only feature. A wrong portrait must trace to a wrong extraction.

## Build sequence

1. load_store, current_attributes, attributes_at over a fixture store: the Scabbers rows from 10_data_model plus the merge artifacts MAINTAIN would write (re-attached superseded row, alias mapping, ledger entry), hand-authored, the raw rows carrying different subject ids (the wiki performs no merges). Test: current_attributes(pettigrew_e01) returns animagus, not rat; attributes_at(pettigrew_e01, ch03) returns rat.
2. quote_for, render_entity_page, build_site skeleton and index; runs the day organize emits its first entities. Test: every quote on a rendered page string-matches its segment source.
3. members_of, group and timeline pages, cross-links. Test: link checker over the built site, zero dead links; the Scabbers timeline shows the same_as merge point.
4. Supersession rendering: struck-through prior values. Test: the fixture supersession renders both states; showpiece page reviewed by eye.
5. load_fanwiki and deterministic align on the measured corpus dump. Test: twenty alignments spot-checked by hand; alias-ledger matches agree with manual judgment.
6. align_residue, then compare.py metrics with the predicate mapping frozen in writing before scoring. Test: metrics recompute identically from alignments.jsonl (pure functions over files).
7. Portraits, only if hours remain. Test: every manifest line's fact_ids resolve and are appearance-class.

## Risks

Parsing the fan wiki is the real work: the generator is small, a MediaWiki dump with hand-edited infobox templates is not, and the sub-step can quietly outgrow the component. Timebox: titles and redirects first (enough for entity coverage), infoboxes only for the frozen mapping's predicates.

Relation recall can be a manufactured number: infobox fields do not map one-to-one onto predicates. Freeze the mapping before looking at scores, report per-predicate, adjudicate disagreements by the text, and report harness-right cases rather than discarding them.

Alignment lives or dies on minor characters, where the certified questions live. The deterministic pass will cover the famous names, the residue will be large, and the manual-review file is real reading time.

## Done means

One command builds the site; the report shows page counts and zero dead links. Demo corpus: a logged human-eyes pass, the supersession showpiece rendering both states, every attribute expandable to fact rows and quotes. Measured corpus: comparison.jsonl and its report with three numbers (entity coverage rate, per-predicate relation recall, timeline ordering agreement), an alignment file with method per row, and the adjudicated disagreement list. Portraits, if built, ship with a manifest tracing every image to its fact rows; if cut, the cut is logged the day it happens. The halves gate separately: the demo bar is fall's; the measured bar inherits the cold-corpus schedule and may land in spring without this component being late.
