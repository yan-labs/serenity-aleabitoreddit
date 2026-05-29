---
name: serenity-aleabitoreddit
description: >
  Apply trader Serenity's (@aleabitoreddit) AI/semiconductor supply-chain
  analytical lens to US-stock ideas and market judgment. Use this skill whenever
  evaluating a stock decision (buy / sell / hold / size); forming an outlook on
  any AI, semiconductor, optical/CPO, memory, power/grid, or neocloud name;
  mentioning any ticker in Serenity's universe (NBIS, AXTI, LITE, SIVE, COHR,
  AAOI, IREN, CRWV, MU, SNDK, NVDA, TSM, MRVL, AVGO, INTC, SOI, IQE, TSEM, CIFR,
  XLU, VST, CEG, EWY, etc.); asking "what would Serenity think", "is this a real
  bottleneck", or wanting a supply-chain / bottleneck read on a thesis.
  Decision-support only — never auto-trades and never places or cancels orders.
---

# Serenity Supply-Chain Lens (@aleabitoreddit)

> **⚠️ STEP 0 — ALWAYS REFRESH BEFORE USE. This skill goes stale within ~30 minutes.**
> Its theses, track record, and analysis are regenerated from @aleabitoreddit's
> live feed roughly every half hour, so the copy on disk is very likely out of
> date by the time you read it. **Before** reading any `references/*.md` /
> `analysis/*.md` file or giving any view, pull the latest version first:
>
> ```bash
> skills update serenity-aleabitoreddit -y    # auto-detects project vs global scope
> ```
>
> Then read the refreshed reference files and proceed. Only if the update
> genuinely fails (offline / network error / command missing) should you fall
> back to the cached copy — and if you do, say explicitly that the data may be
> stale.

A reusable analytical lens distilled from **~5,602 tweets (2025-07 to 2026-05)
plus 4 long-form X Articles (2026-01 to 2026-05)** by **Serenity /
[@aleabitoreddit](https://x.com/aleabitoreddit)** — an AI-and-semiconductor
*supply-chain* analyst and trader (~450k followers, ~40k subscribers, ex-Reddit/WSB). Use it to
pressure-test US-stock ideas and to reason about the AI/semi supply chain the
way he does.

> **Decision-support lens, NOT financial advice and NOT an auto-trader.** See
> "Risk & disclaimer framing" below. Always confirm current prices and
> fundamentals yourself — theses decay, and his returns are self-reported and
> unverified.

The raw tweet archive this lens was built from lives at the repo root in `data/`
(`aleabitoreddit_tweets.json` / `.csv`); the period-by-period distillation is in
`analysis/`.

---

## Who Serenity is and what his edge is

He hunts **mispriced upstream supply-chain bottlenecks** before institutions
price them in. The mental model: don't buy the obvious "shovel seller" (NVDA) —
trace the supply chain as far upstream as possible and find the single point of
failure that a hyperscaler will pay *anything* to keep flowing.

His representative chain:
> hyperscaler capex (GOOGL/MSFT/META/AMZN) → ASICs/TPUs → optical transceivers
> (LITE/AAOI/COHR) → InP epiwafer (IQE) → InP substrate (AXTI/Sumitomo) → InP
> feedstock (indium, Vital Materials).

The further upstream and the smaller the market cap, the more underpriced the
chokepoint tends to be relative to the trillions flowing downstream. His biggest
distilled calls — AXTI, SIVE, SOI, LITE, SNDK, the XLU power trade — all came
from this multi-hop "OSINT BOM mapping" process.

He layers several other lenses on top: a **Mag7-customer-concentration filter**,
**signed-contract ARR vs. market-cap mismatch**, a **GAAP-margin war** (real
margins vs. cherry-picked non-GAAP), **dilution/ATM as a disqualifier**, a
**financing-quality spectrum** for neoclouds, and macro overlays (rate cuts,
tariff shocks, war). Full detail in `references/methodology.md`.

**Independent calibration (2026-05-27 recheck):** his true trading win rate is
not independently knowable without broker statements, option-contract history,
position sizes, and full loser disclosure. A local re-score of dated public calls
using Yahoo Finance adjusted-close data found about **61% 30-day directional
accuracy** (30/49), **41% strict 30-day +10%/-10% hits** (20/49), and **54% with
a 20%+ favorable close within 60 days** (29/54). Mature, externally checkable
theses score better: roughly **65-75%** of mature theses were at least partly
validated by later price/fundamental evidence, and his strongest AI photonics /
CPO / InP / memory bottleneck subset looks closer to **75-85%**. Treat those as
rough calibration bands, not a replicable trading return.

**Important caveat:** he trades volatile micro/small-caps that move 20%+ a day,
runs ~1.25–1.5x margin, and self-reports very high YTD returns (237% in
Feb 2026, later 4502.45% YTD on May 26). Those numbers are unverified and carry
obvious survivorship / selection bias. Treat his lens as a source of *questions
to ask*, not signals to copy.

---

## How the reference files are organized

Read progressively — pull in only what the task needs.

| File | What it is | Read it when |
|---|---|---|
| `references/methodology.md` | His framework as ~12 named, transferable principles + a checklist you can run on any new name | Evaluating *how* he thinks, or vetting any ticker (even one he never covered) |
| `references/theses.md` | Per-ticker knowledge base, merged across all periods, grouped by sub-sector, with conviction tier + how it evolved + latest stance | Looking up his actual view on a specific name |
| `references/articles.md` | Compact summaries and durable portfolio-use rules from his long-form X Articles, without redistributing full article text | Checking whether a thesis has article-level backing, especially SIVE, AXTI/materials, robotics/rare earths, or crypto-policy risk |
| `references/track-record.md` | Chronological timeline of his dated calls + an honest calibration note on what worked, what reversed, and the selection-bias caveat | Deciding *how much to weight* his opinion |
| `references/maintenance.md` | Rules for incrementally distilling new posts into the smallest useful skill/reference update | Maintaining this skill from fresh X posts |
| `analysis/*.md` | The six period analyses the lens was synthesized from (provenance) | Going deeper than the merged knowledge base, or auditing a claim |

---

## Workflows

### (a) Evaluate one ticker through his lens

1. Look the ticker up in `references/theses.md`. If present, note his stance,
   conviction tier, how it evolved, and his latest known view. Flag if his view
   reversed (e.g. IREN, CRWV, POET).
2. If the ticker or theme appears in `references/articles.md`, treat that as
   higher-context long-form backing, but still distinguish public evidence from
   inferred customer paths.
3. If he never covered it, run the **checklist** at the bottom of
   `references/methodology.md` — apply his principles to a fresh name.
4. Sanity-check timeliness: his theses are dated. Anything older than a couple of
   months may have decayed — say so, and confirm current price/fundamentals.
5. Weight his opinion using `references/track-record.md` and the calibration
   bands above: his bottleneck theses deserve more weight than event trades,
   old flipped stances, or self-reported options screenshots.
6. Present: his view, the supply-chain read, the bull/bear case, and the risks —
   framed as analysis, never as an order to place.

### (b) Review a portfolio or watchlist against his views

1. Take the list of tickers the reader provides (their holdings, a watchlist, a
   sector basket).
2. For each name, pull his view from `references/theses.md` and bucket into:
   - **Agreements** — he is bullish on it.
   - **Conflicts** — he is bearish/cautious on it (surface his dated reasoning).
   - **Gaps** — his high-conviction names absent from the list (e.g. the
     photonics/CPO chain: SIVE/LITE/COHR/AAOI/SOI/AXTI/TSEM/IQE; NBIS among
     neoclouds; SNDK for memory).
3. Check `references/articles.md` for long-form article support. Article-backed
   signals should raise discussion priority only when they also fit the user's
   risk budget, liquidity, and execution constraints.
4. Produce a prioritized discussion list. Keep it advisory; never generate,
   place, or cancel a trade order.

### (c) Form a forward sector view

1. Identify which of his thematic threads the question touches: photonics/CPO,
   memory/HBM supercycle, neocloud financing quality, power/grid, defense,
   AI-agent hardware, "not-disrupted-by-AI" software.
2. Pull the relevant theses and thread summaries from `references/theses.md`.
3. Note his leading indicators (hyperscaler capex guidance, TSM projections, SMM
   7N indium price, GPU availability, DRAM/NAND spot pricing).
4. State the view with his confidence level and the dated evidence behind it,
   plus what would invalidate it.

---

## Risk & disclaimer framing (state this when giving any view)

- **Self-reported, unverified returns.** His YTD figures, from 237% in Feb 2026
  to 4502.45% on May 26, are his own screenshots. No independent verification
  exists.
- **Estimated public-call calibration, not trading proof.** A 2026-05-27
  recheck found ~61% 30-day directional accuracy on dated public calls, but only
  ~41% strict 30-day +10%/-10% hits. Mature supply-chain theses validated better
  than mechanical copying.
- **Survivorship / selection bias.** A public feed highlights winners. Reversed
  or wrong calls exist (see `references/track-record.md`) and get less airtime.
- **High-volatility micro/small-caps.** Many of his names (AXTI, SIVE, IQE, AAOI)
  move 20%+ in a day, have thin floats, dilution risk, and binary outcomes. His
  position sizing and margin use are not appropriate to copy blindly — he says so
  himself ("build conviction yourself before entering").
- **Theses decay.** Calls are dated. A bottleneck can resolve, a contract can be
  lost, an ATM can be filed. Always re-confirm current price and fundamentals.
- **This is a lens, not a signal feed.** Use it to ask better questions about
  your own ideas. It is explicitly NOT auto-trading, NOT a recommendation to
  buy/sell, and NOT financial advice. Every order is the reader's own manual,
  confirmed decision.
- **No-position idea posts carry lower weight.** If he frames a stock comment as
  exploratory, for fun, or explicitly says he has no position, treat it as a
  process example rather than a high-conviction call.
