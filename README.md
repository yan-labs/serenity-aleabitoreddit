npx skills add yan-labs/serenity-aleabitoreddit

<p align="center">
  <a href="https://x.com/aleabitoreddit">
    <img src="assets/serenity-avatar.jpg" alt="Serenity (@aleabitoreddit)" width="112" height="112">
  </a>
</p>

# serenity-aleabitoreddit

[![skills.sh](https://skills.sh/b/yan-labs/serenity-aleabitoreddit)](https://skills.sh/yan-labs/serenity-aleabitoreddit)

Everything distilled from **Serenity
([@aleabitoreddit](https://x.com/aleabitoreddit))** — a public X trader and
AI/semiconductor *supply-chain* analyst known for tracing hyperscaler capex into
upstream bottlenecks. His recurring research terrain includes optical/CPO and
photonics, InP substrates and compound semis, memory/HBM/NAND, neocloud
financing quality, AI power/grid demand, robotics/physical AI, and overlooked
international supply-chain names.

This repo packages his public work into one self-contained research artifact:
**the raw tweet archive**, **long-form article summaries**, a
**period-by-period distillation**, and a ready-to-use **agent skill** that
applies his analytical lens to US-stock ideas.

Built from **~5,588 tweets** spanning **2025-07-02 → 2026-05-29** plus **4 X
Articles** published in **2026-01 → 2026-05**.

> ⚠️ **Not financial advice. Decision-support only.** This skill never trades and
> never places or cancels orders. Serenity's self-reported returns are unverified
> and carry obvious survivorship/selection bias; his names are volatile
> micro/small-caps. Use the lens to ask better questions, not to copy trades.

## What's in here

| Path | What it is |
|---|---|
| `serenity-aleabitoreddit/SKILL.md` | The agent skill: who he is, his edge, the three workflows, risk framing |
| `serenity-aleabitoreddit/references/methodology.md` | His framework as ~12 named, transferable principles + a checklist for any new name |
| `serenity-aleabitoreddit/references/theses.md` | Per-ticker knowledge base, merged across all periods, grouped by sub-sector, with conviction tiers and how each evolved |
| `serenity-aleabitoreddit/references/articles.md` | Compact summaries and portfolio-use rules for Serenity's long-form X Articles; full article text is intentionally not stored |
| `serenity-aleabitoreddit/references/track-record.md` | Chronological timeline of his dated calls + an honest calibration note |
| `serenity-aleabitoreddit/references/maintenance.md` | Maintenance rules for incrementally distilling new posts into the skill |
| `serenity-aleabitoreddit/analysis/*.md` | The six period analyses the skill was synthesized from (provenance) |
| `data/aleabitoreddit_tweets.json` | Full tweet archive, all fields (text, metrics, quoted tweets, media, timestamps) |
| `data/aleabitoreddit_tweets.csv` | Same archive as a spreadsheet (id, url, time, text, likes, views, etc.) |
| `data/ticker_stats.txt` | His `$ticker` universe by mention count + first/last seen |
| `assets/serenity-avatar.jpg` | Local copy of Serenity's public X avatar used in this README |
| `prep.py` | Condenses the tweet JSON into monthly chunks and recomputes the ticker stats |
| `update.py` | Pulls latest tweets, dedupes by id, and refreshes derived data for incremental updates |

## Use it as a skill

One-command install with [skills.sh](https://skills.sh/):

```bash
npx skills add yan-labs/serenity-aleabitoreddit
```

Or drop the folder into an agent's skills directory:

```bash
# Claude Code (project-local)
cp -r serenity-aleabitoreddit <your-project>/.agents/skills/
ln -s ../../.agents/skills/serenity-aleabitoreddit <your-project>/.claude/skills/serenity-aleabitoreddit
```

It then triggers on questions about AI/semiconductor/optical/memory/power/
neocloud names, supply-chain bottleneck analysis, or evaluating a stock idea.

## His edge, in one line

Don't buy the obvious shovel-seller (NVDA) — trace the supply chain upstream to
the single chokepoint a hyperscaler will pay anything to keep flowing
(optical/CPO, compound-semi substrates, memory, power), where the small market
cap is most mispriced relative to the trillions flowing downstream.

## Provenance

Tweets were collected via the `agent-reach` `twitter-cli` using date-windowed
search (full-day windows with intra-day top-up for high-volume days) to work
around X's pagination/rate limits. X Article bodies were fetched with
authenticated article access and distilled into summaries only; full article text
is not redistributed here. Regenerate the condensed monthly chunks and ticker
stats from the archive with `python3 prep.py`.

---

*This repository contains only public information about @aleabitoreddit, article
metadata, and derived analysis/summaries. It is an independent research artifact
and is not affiliated with, endorsed by, or connected to him.*
