> **SUPERSEDED 2026-08-28** by `05_fall_plan.md`, whose cost model corrects three arithmetic errors in this file (the 70x spread is 146x, batched output is 1.29M not 1.5M, and the batching saving is 2.33x not 3x).
> Kept for the record; do not build from it. Index: `docs/README.md`.

# Cost and model selection

**2026-08-27.** Rates are **perishable** — every figure below was fetched on this date and must
be re-checked before it appears in a budget or a paper. Sources are named per table.

---

## What drives cost

Per unit the pipeline makes: one entity pass, one fact pass, and N cell calls where N is the
number of above-threshold nodes in that unit. **Each call re-sends the unit text**, so the corpus
is read once per call.

Oz sizing: ~600 units, ~1.27M words ≈ 1.7M tokens, ~2,800 tokens per unit, ~5 major nodes per
unit.

| | Input | Output |
|---|---|---|
| entity pass | 2,700 | 300 |
| fact pass | 2,700 | 600 |
| 5 **separate** cell calls | 13,500 | 1,250 |
| per unit | ~19,000 | ~2,150 |
| × 600 units | **11.4M** | **1.3M** |

**Cell calls are ~70% of input and the cost is avoidable.** Batch them — one call emitting all N
cells for a unit — and per-unit input falls from 13,500 to 2,700.

| Batched | Input | Output |
|---|---|---|
| Oz | **~5.1M** | ~1.5M |
| All four corpora (6.8M words) | **~27M** | ~8M |

Roughly 3× on the dominant term, from one design decision. Build it in from the start.

---

## Rates, fetched 2026-08-27

**Anthropic** (from the bundled `claude-api` skill table, cached 2026-06-24):

| Model | ID | In $/M | Out $/M |
|---|---|---|---|
| Fable 5 / Mythos 5 | `claude-fable-5` | 10.00 | 50.00 |
| Opus 5 | `claude-opus-5` | 5.00 | 25.00 |
| Sonnet 5 | `claude-sonnet-5` | 2.00 | 10.00 |
| Haiku 4.5 | `claude-haiku-4-5` | 1.00 | 5.00 |

**OpenAI** (developers.openai.com/api/docs/pricing): gpt-5.6-sol 4.00/20.00 · gpt-5.5 5.00/30.00 ·
o1 15.00/60.00 · gpt-4.1 2.00/8.00 · gpt-4o 2.50/10.00 · gpt-4o-mini 0.15/0.60 ·
gpt-5-nano 0.05/0.40.

**Google** (ai.google.dev/gemini-api/docs/pricing): Gemini 3.1 Pro Preview 4.00/18.00 ·
3.5 Flash 1.50/9.00 · 2.5 Flash 0.30/2.50 · 2.5 Flash-Lite 0.10/0.40.
**`[verify]`** — the page rendered a header reading "as of Jan 1, 2027," which does not match the
fetch date. Either forward-dated pricing or a misread.

**xAI** (docs.x.ai/docs/models), <200k-token band, which is always the applicable one here since
units run ~2,800 tokens: grok-4.6 2.00/6.00 · grok-4.3 1.25/2.50 · grok-build-0.1 1.00/2.00.

**Batch discount is 50%** on Anthropic, OpenAI and Google. **None is documented for xAI**, which
matters more than the headline rate — this workload is pure offline bulk, exactly what batch
pricing exists for.

---

## Full four-corpus run (~27M in, ~8M out), all via Batch where available

| Provider | Model | **Full run** |
|---|---|---|
| Anthropic | Fable 5 | $335 |
| Anthropic | Opus 5 | $168 |
| OpenAI | gpt-5.6-sol | $134 |
| Google | Gemini 3.1 Pro | $126 |
| xAI | grok-4.6 *(no batch)* | $102 |
| Anthropic | Sonnet 5 | $67 |
| OpenAI | gpt-4.1 | $59 |
| Google | Gemini 3.5 Flash | $56 |
| xAI | grok-4.3 *(no batch)* | $54 |
| Anthropic | Haiku 4.5 | $34 |
| Google | Gemini 2.5 Flash | $14 |
| OpenAI | gpt-4o-mini | $4.40 |
| Google | Gemini 2.5 Flash-Lite | $2.95 |
| OpenAI | gpt-5-nano | $2.30 |

**Oz alone, batched:** ~$6 Haiku, ~$13 Sonnet 5, ~$32 Opus 5.
**Oz book 1 — the pilot** (24 units, ~57k tokens): **under $1** on Sonnet 5. All three tiers over
it, which is what produces the sensitivity numbers, costs about **$3**.

---

## What this changes

**The spread is roughly 70×.** The entire corpus costs $2.30 at the bottom and $335 at the top.

That reframes the tier-sensitivity experiment. It is not an academic question about which stages
need a frontier model — **it is a 70× cost decision**. If a cheap tier holds entity spotting, the
corpus runs for the price of a sandwich and can be re-run every time the pipeline changes. If it
cannot, iteration gets rationed at $60–170 a pass.

**And the binding constraint is hours, not budget** — which the feasibility review already
concluded from the other side.

---

## Why not run everything on the top tier

The cost is survivable. The methodology is not.

The remaining contribution is **measurement**. "We ran it on the best model available" is not a
measurement: it reports a ceiling and gives a reader nothing to act on. **The spread is the
finding**, and running everything on Fable 5 erases it — $335 spent to produce a number nobody
can use.

Defensible shape: iterate on the cheapest tier that works, **report at minimum two tiers**, and
reserve the top tier for the judge — which has to differ from every writer anyway, and which is
cheap because judging is far fewer tokens than generating.

---

## Tier assignment by stage

See `docs/18` for the full table. The rule, restated:

**Spend where errors propagate; economise where they are recoverable.**

Not "spend more at higher abstraction." Coreference sits at the bottom of the stack and is the
one sub-task cheap models genuinely fail; a corrupted entity registry costs a re-ingest, while a
mediocre abstract costs one call to regenerate.

Both expensive categories — coreference and abstract refold — are **low-volume**, so this is
affordable. The cost driver is cell generation, which is also the layer where a bad output is one
cheap regeneration away.

---

## Operational constraints

**The fact layer has failed twice on credit balance.** That is a live operational fact, not a
hypothetical. Instrument spend per run and set a hard stop before starting a full pass. The
`Run` record already carries `tokens_in`, `tokens_out` and `latency_ms`, so this is a query
rather than new logging.

**Local models are free and will fail on format, not comprehension.** Risk #2 in the feasibility
review predicts 30–40% rejection on strict nested JSON from 7B instruct models. Grammar-
constrained decoding — Ollama's native mode, or `outlines`, whose paper (Willard 2023) is already
in `papers/` — makes malformed output structurally impossible. Measure format failure and
comprehension failure **separately**, because they have different remedies and conflating them
sends you after the wrong one.

**Not verified:** prompt caching multipliers. Caching the unit once and making N calls against it
would cut input further, but with batch already at 50% and cells batched, it is a second-order
optimisation. Worth checking only if a full run somehow gets expensive.

**Not verifiable by me:** the capability of any post-cutoff model named above, particularly on
strict structured output. Prices can be quoted; quality cannot. That is what the $3 pilot is for.
