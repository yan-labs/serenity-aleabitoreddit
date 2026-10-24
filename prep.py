#!/usr/bin/env python3
"""Condense the tweet archive into monthly chunks + compute the $ticker universe.

Reads data/aleabitoreddit_tweets.json, writes data/chunks/<YYYY-MM>.txt and
data/ticker_stats.txt. Run from the repo root: `python3 prep.py`.

ticker_stats.txt is produced by `update.write_ticker_stats` so `prep.py` and
`update.py` always emit byte-identical stats (no reorder churn in git diffs).
"""
import json, os
from collections import defaultdict

from update import USER, sort_key, write_ticker_stats

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SRC = os.path.join(DATA, "aleabitoreddit_tweets.json")
CHUNK_DIR = os.path.join(DATA, "chunks")


def line(t):
    m = t.get("metrics") or {}
    d = (t.get("createdAtISO") or "")[:16].replace("T", " ")
    txt = (t.get("text") or "").replace("\n", " ").strip()
    qt = t.get("quotedTweet") or {}
    q = ""
    if qt.get("text"):
        q = f"  [QT @{(qt.get('author') or {}).get('screenName','?')}: {qt['text'].replace(chr(10),' ').strip()[:280]}]"
    return f"[{d}] ♥{m.get('likes',0)} \U0001F441{m.get('views',0)} ↻{m.get('retweets',0)} {txt}{q}"


def main():
    os.makedirs(CHUNK_DIR, exist_ok=True)
    with open(SRC, encoding="utf-8") as f:
        tweets = json.load(f)
    tweets = [t for t in tweets if (t.get("author") or {}).get("screenName", "").lower() == USER]
    tweets.sort(key=sort_key)

    write_ticker_stats(tweets)

    by_month = defaultdict(list)
    for t in tweets:
        by_month[(t.get("createdAtISO") or "")[:7]].append(t)

    for mo in sorted(by_month):
        with open(os.path.join(CHUNK_DIR, f"{mo}.txt"), "w", encoding="utf-8") as f:
            f.write(f"# Serenity (@{USER}) tweets — {mo} — {len(by_month[mo])} tweets\n\n")
            for t in by_month[mo]:
                f.write(line(t) + "\n")

    with open(os.path.join(DATA, "ticker_stats.txt"), encoding="utf-8") as f:
        n_tickers = sum(1 for row in f.read().splitlines()[4:] if row.strip())
    print(f"{len(tweets)} tweets -> {len(by_month)} monthly chunks; {n_tickers} tickers (>=2 mentions)")


if __name__ == "__main__":
    main()
