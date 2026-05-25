# Serenity's Methodology — the reusable lens

His analytical framework distilled into named, transferable principles. Each one
states *what it is*, *the signal he looks for*, *how to apply it*, and a short
dated example from the corpus. A runnable checklist is at the bottom.

> Use this file to vet any name — including ones he never tweeted about. The
> principles are the durable part; the specific tickers decay.

## Table of contents

1. [Bottleneck hunting (the core lens)](#1-bottleneck-hunting-the-core-lens)
2. [Multi-hop BOM / OSINT supply-chain mapping](#2-multi-hop-bom--osint-supply-chain-mapping)
3. [Signed-contract ARR vs. market-cap mismatch](#3-signed-contract-arr-vs-market-cap-mismatch)
4. [Mag7 customer-concentration filter](#4-mag7-customer-concentration-filter)
5. [The GAAP-margin war](#5-the-gaap-margin-war)
6. [Qualification cycle vs. TTM revenue](#6-qualification-cycle-vs-ttm-revenue)
7. [Dilution / ATM calendar as a disqualifier](#7-dilution--atm-calendar-as-a-disqualifier)
8. [Counterparty / financing-quality spectrum](#8-counterparty--financing-quality-spectrum)
9. [Short-squeeze setup (profitable-grower variant)](#9-short-squeeze-setup-profitable-grower-variant)
10. [Tariff/macro-shock-as-buy](#10-tariffmacro-shock-as-buy)
11. [Institutional lag / dark-pool & flow reading](#11-institutional-lag--dark-pool--flow-reading)
12. [Vega / IV mispricing (options structure)](#12-vega--iv-mispricing-options-structure)
13. [Conviction tiering, sizing, and timing](#13-conviction-tiering-sizing-and-timing)
14. [Anti-patterns he calls out](#14-anti-patterns-he-calls-out)
15. [The checklist (run this on any new name)](#15-the-checklist-run-this-on-any-new-name)

---

## 1. Bottleneck hunting (the core lens)

- **What:** Find the single point of failure in a fast-growing supply chain —
  the upstream chokepoint a downstream buyer must pay through rather than design
  around. "Who is the *real* bottleneck?"
- **Signal:** A supplier with sole- or near-sole-source position, pricing power,
  no near-term qualified substitute, in a TAM expanding on AI capex, still small
  cap. He distinguishes *quantity* (how much supply) from *price* (monopoly
  pricing power): "You don't need to produce 3000% more material… just increase
  the prices."
- **Apply:** For any thesis, ask "if this layer stopped shipping, what breaks
  downstream, and is there a second source?" The fewer substitutes and the
  bigger the downstream dependency, the better the asymmetry. He compares each
  new bottleneck to historical price-spike precedents (Neon gas +2000% in 2022;
  Dysprosium +2300% in 2010; HBM 2024-25).
- **Example:** AXTI (2025-12-26) — "the entire AI industry will likely be
  bottlenecked by AXTI ($700M)…" framing InP substrate control as the chokepoint
  for $15T+ of hyperscaler value. ("Strait of $AXTI" analogy to Strait of
  Hormuz, March 2026.)

## 2. Multi-hop BOM / OSINT supply-chain mapping

- **What:** Build a Bill-of-Materials for hyperscaler infrastructure by chaining
  hops from capex commitment down to feedstock, then identify who chokes each
  layer. He notes AI chatbots fail at this because the connections are obscured
  multi-hop.
- **Signal:** Conference slides (OFC, GTC, JP Morgan fireside), investor decks,
  SEC filings, LinkedIn job postings, partner-section changes on startup
  websites, BOM-percentage estimates.
- **Apply:** Map the chain explicitly. Estimate what % of cluster BOM flows to
  the supplier — a cheap component (optical ~8-12% of a TPU BOM) means
  hyperscalers will pay through a price hike rather than cut AI capex.
- **Example:** Ayar Labs quietly removed LITE and MTSI from its website partner
  section, leaving only SIVE (April 2026) — read as Sivers becoming Ayar's
  primary merchant laser supplier, before any press release.

## 3. Signed-contract ARR vs. market-cap mismatch

- **What:** Price stocks on forward ARR implied by signed take-or-pay contracts,
  not trailing multiples. Contract signing flips a name from "watch" to "high
  conviction."
- **Signal:** A multi-year hyperscaler contract worth a large multiple of
  current revenue, against a market cap that hasn't re-rated.
- **Apply:** Compare contracted forward revenue to market cap. If a 300%+ ARR
  contract only moved the stock 45%, the dilution to fund it was "already priced
  in" — the post-announcement dip is the entry.
- **Example:** NBIS after the $17B MSFT contract (2025-09): "before $50 NBIS was
  speculation… now it's pure scaling," projecting $5-6B 2026 revenue at ~70%
  margins vs. ~$24-26B market cap.

## 4. Mag7 customer-concentration filter

- **What:** His highest-conviction qualifier early on: "who are the customers?"
  Mag7 presence as a moat/demand signal.
- **Signal:** A small-cap with systemic exposure to multiple Mag7 buyers.
- **Apply:** Use Mag7-customer presence as a *positive* concentration signal for
  demand durability — but pair it with #8 (counterparty quality) and watch the
  flip side: single-customer concentration is a *risk* (see POET losing MRVL).
- **Example:** ALAB launched as "the only small cap with systemic exposure to 5
  of the Mag7" (2025-07-28).

## 5. The GAAP-margin war

- **What:** Compare companies on GAAP gross margin, never cherry-picked non-GAAP
  or single-line margins. A market inefficiency thesis: if most investors
  compare non-GAAP, the honest discloser is systematically undervalued.
- **Signal:** A margin disclosure that strips SBC, depreciation, or restricts to
  one revenue line = uninformative for cross-company ranking.
- **Apply:** Re-rank peers on true GAAP margins before deciding who is "best in
  class." Software/orchestration ownership is the margin wedge in neoclouds.
- **Example:** IREN's "92% gross margins" flagged as hardware-specific non-GAAP
  vs. NBIS's 71.2% GAAP (Nov 2025) — "NBIS's quality is disguised because its
  disclosure is more honest."

## 6. Qualification cycle vs. TTM revenue

- **What:** Don't judge a pre-volume-ramp company by current financials. Enter
  during *qualification* (design wins, foundry partnerships, guidance language),
  before volume shows in reported revenue.
- **Signal:** Conference design wins, foundry qualification, earnings-call
  guidance — TAM expansion at an architectural inflection, not current burn.
- **Apply:** For frontier names, model forward TAM at the inflection, not
  trailing revenue. "Modeling on current revenue is the equivalent of modeling
  Celestial at $50m because of no CPO revenue in 2025."
- **Example:** SIVE, AEHR, LPK, AXTI all entered pre-ramp on qualification
  evidence. "Nobody cares about current earnings unless there's something
  extremely bad" (April 30, re: LPK miss).

## 7. Dilution / ATM calendar as a disqualifier

- **What:** Large active ATMs (at-the-market share offerings), especially paired
  with executive SBC awards, are treated as structurally disqualifying — retail
  equity gets diluted to fund the buildout.
- **Signal:** ATM size vs. market cap; SBC running alongside; management track
  record of prior dilution. He reads SEC EDGAR for lockup/dilution terms.
- **Apply:** Treat a big active ATM as a ceiling on the stock. Distinguish
  *destructive* dilution (open-market ATM dumping) from *acceptable* (small
  one-time strategic listing dilution; a strategic investor retiring debt).
- **Example:** IREN $6B ATM at ~$11.7B MC = ~51% dilution overhang → "AMC of
  datacenters," explicit bear (March 2026). Contrast: SIVE's 2.5% NASDAQ-listing
  dilution viewed positively; IQE's MTSI $45M deal positive (retired debt).

## 8. Counterparty / financing-quality spectrum

- **What:** Within one sub-sector, the *tenant's creditworthiness* and the
  *financing structure* determine the equity path, not just the operations.
- **Signal:** Who backstops the contracts? AAA hyperscaler vs. a cash-burning AI
  lab. How is the buildout funded? NVDA funding + convertibles > colo model >
  ATM > credit-card debt.
- **Apply:** Rank neoclouds by financing quality:
  `NBIS (NVDA + convertibles) > CIFR/WULF (colo, GOOGL/AMZN backstop) > IREN
  (ATM) > CRWV (heavy debt interest)`. Flag OpenAI-counterparty exposure
  (ORCL/CRWV) as a risk because OpenAI's FCF can't cover its commitments.
- **Example:** Dec 2025 ORCL/CRWV "OpenAI contagion" selloff called a buying
  opportunity for MSFT/META-backstopped names (NBIS, IREN) while avoiding the
  OpenAI-dependent ones.

## 9. Short-squeeze setup (profitable-grower variant)

- **What:** High short interest on a *profitable, growing* company is an
  anomaly that resolves upward; high SI on a *zombie* is dangerous.
- **Signal:** 35%+ float short with borrow utilization near limits, against
  improving fundamentals and a near-term catalyst. Tracks SI as a squeeze timer,
  not a standalone direction.
- **Apply:** Pair SI with fundamentals. Profitable + growing + trapped shorts =
  asymmetric upside; unprofitable + high SI = avoid.
- **Example:** HIMS at 42% SI on an "11B, profitable, fast-growing company…
  potential to make history on a short squeeze" (2025-09-12). Re-flagged on the
  2026-03 NVO-partnership flip.

## 10. Tariff/macro-shock-as-buy

- **What:** Algorithmic risk-off selloffs on macro headlines are entries when
  the fundamental thesis is committed multi-year capex that doesn't respond to
  the shock within ~12 months.
- **Signal:** A broad -8% to -15% sector flush on a tariff/geopolitical
  headline, with the underlying demand contracted years out.
- **Apply:** Separate "algorithmic risk-off" from "fundamental re-rating." Buy
  the former; respect the latter. He overlays macro as a *tilt* (rate cuts →
  small-cap/growth; war → pre-position oil/defense, then rotate profits into the
  high-beta selloff), not a reason to abandon theses.
- **Example:** Oct 10 2025 tariff escalation — added NBIS leaps at $98.8 into the
  flush, called it "the best entry point of 2025." Caveat: by March 2026 he
  admitted the Iran conflict genuinely hurt his rate-cut-dependent XLU/EWY longs
  — macro can break a thesis when it changes the rate path.

## 11. Institutional lag / dark-pool & flow reading

- **What:** Retail can discover supply-chain chokepoints 4-6 weeks before
  institutions accumulate; X commentary lags fundamentals 1-3 days, institutional
  research 2-4 weeks. The window between data release and narrative absorption is
  the edge.
- **Signal:** Sustained block/dark-pool buying at discounted levels; later
  13F/holdings disclosures confirming the thesis after his public post.
- **Apply:** Treat his (or your) early supply-chain map as the lead; treat later
  analyst upgrades and fund accumulation as *lagging validation*, not new info.
- **Example:** Morgan Stanley ended up a 6.5% holder of SOI, Point72/MTSI bought
  IQE float — all *after* his public theses (April-May 2026). Also reads option
  open-interest/MM flushes as short-term timing.

## 12. Vega / IV mispricing (options structure)

- **What:** Find ETFs/indexes where market makers price implied volatility on
  stale long-run historical averages that no longer reflect new structural
  volatility — then buy long-dated leaps for vega expansion.
- **Signal:** Cheap IV on a name whose realized vol or constituent exposure has
  structurally changed; OTM long-dated leaps for convex leverage.
- **Apply:** Look for "boring" wrappers with hidden new volatility. Rule of
  thumb on entry: prefers low IV (he cites buying calls mainly at ~10-35% IV);
  for XLU he warned "if IV is elevated above 17.5%, probably stay away."
- **Example:** EWY 2028 leaps bought at 32% IV (priced on a decade of flat
  Korean returns) while EWY is effectively 50%+ Samsung/SK Hynix; IV expanded to
  44-47% in a week. XLU OTM 2-year leaps at 14-16% IV on the AI-power thesis.
  **High-risk, advanced — note this is leveraged options, not appropriate to
  copy without understanding the structure.**

## 13. Conviction tiering, sizing, and timing

- **What:** Explicit tiering (S/A/B/C/D/F lists) and conviction-scaled sizing;
  smaller size on binary microcaps; calls instead of shares when a name could go
  to zero (e.g. China export-ban risk).
- **Signal:** "Fundamentally de-risked" (Mag7 counterparty + locked take-or-pay
  contract) = top tier and bigger size; execution/dilution/binary risk = small
  size or defined-risk options.
- **Apply:** Size to conviction *and* to how binary the outcome is. He repeatedly
  warns: these names move 20%+ a day, "build conviction yourself before you
  enter," "don't have high concentration in small caps." Holds for LTCG when
  catalysts are ≥12 months out. Goes off margin during macro uncertainty.
- **Example:** "Calls are actually safer than shares" on AXTI given China export
  risk (2025-12-30); SIVE flagged "wouldn't put too much concentration into
  them" for average accounts.

## 14. Anti-patterns he calls out

- **Standalone technical analysis** — "TA is snake oil without fundamentals,
  catalysts, macro." "Float and fundamentals > lines on a chart."
- **Credentialed certainty without supply-chain fluency** — May 2026 media
  critique: credentials or background matter less than whether the person can
  reason correctly about CW laser nuances, valuation, InP substrate moats, and
  crucible-processing constraints. Treat confident commentary that conflates
  these layers as noise even when it comes from polished media voices.
- **Insider sales as a bear signal** — explicitly "the dumbest metric" / noise.
- **Conflating supply-chain layers** — substrate ≠ epiwafer ≠ feedstock; foundry
  ≠ module. He corrects these constantly.
- **Reddit/X sentiment** — "IGNORE the sentiment since it's usually wrong."
- **Chasing the already-frontrun event** — buying oil/defense at ATHs *after* a
  war headline instead of pre-positioning.
- **Cult/financial-engineering valuations** — PLTR ("large part of profit is
  just interest income"); SNAP (SBC-funded buybacks masking negative true FCF).

---

## 15. The checklist (run this on any new name)

Score a candidate against his lens. The more "yes", the more it fits his style —
none of this is a buy signal on its own.

1. **Bottleneck?** Is it a sole/near-sole-source chokepoint in a growing chain,
   with no near-term qualified substitute and real pricing power?
2. **Upstream & cheap?** Is it upstream of the obvious "shovel seller," and is
   its component a small % of downstream BOM (so buyers pay through price hikes)?
3. **Demand driver?** Is the TAM expanding on hyperscaler AI capex (the master
   leading indicator) or physical-AI/robotics capex rather than a legacy/cyclical
   market? May 2026 framing: Jensen Huang's projected "$3-4T annually" AI capex
   by 2030 is the top-down reason tiny upstream chokepoints can re-rate.
4. **Contracts & counterparty?** Are there signed multi-year contracts, and is
   the tenant creditworthy (AAA hyperscaler, not a cash-burning lab)?
5. **Real margins?** Do the GAAP margins (not cherry-picked non-GAAP) support
   the quality claim?
6. **Financing quality?** Any large active ATM + SBC overhang, or worrying debt
   interest? (Disqualifier.) Or is dilution small/strategic/debt-retiring?
7. **Stage?** Is it pre-volume-ramp (qualification design wins) and therefore
   mispriced on TTM revenue, or already crowded/frontrun?
8. **Catalyst & timing?** Is there a dated catalyst (earnings, conference, MSCI
   inclusion, policy/EO) within a tradable window?
9. **Market cap headroom?** Small enough (<~$3B at call for his moonshots) that
   institutional re-rating is still ahead?
10. **Validation lag?** Is institutional/analyst coverage still behind the
    supply-chain evidence (an edge), or already in (priced)?
11. **Risk & sizing fit?** How binary is it (dilution, single-customer, China
    export, restructuring)? Size accordingly; consider defined-risk options.
12. **Macro overlay?** Does the current rate path / tariff / war regime help or
    hurt this specific thesis right now?

Then: confirm current price and fundamentals, weight using
`track-record.md`, and present as analysis — never as an order.
