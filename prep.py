#!/usr/bin/env python3
"""Condense the tweet archive into monthly chunks + compute the $ticker universe.

Reads data/aleabitoreddit_tweets.json, writes data/chunks/<YYYY-MM>.txt and
data/ticker_stats.txt. Run from the repo root: `python3 prep.py`.
"""
import json, os, re
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SRC = os.path.join(DATA, "aleabitoreddit_tweets.json")
CHUNK_DIR = os.path.join(DATA, "chunks")
os.makedirs(CHUNK_DIR, exist_ok=True)
USER = "aleabitoreddit"

tweets = json.load(open(SRC))
tweets = [t for t in tweets if t.get("author", {}).get("screenName", "").lower() == USER]
tweets.sort(key=lambda t: t.get("createdAtISO", ""))

TICK = re.compile(r"\$([A-Za-z]{1,6})\b")
counts, first, last = Counter(), {}, {}
for t in tweets:
    txt = (t.get("text", "") or "") + " " + ((t.get("quotedTweet") or {}).get("text", "") or "")
    d = (t.get("createdAtISO") or "")[:10]
    for m in set(TICK.findall(txt)):
        u = m.upper()
        counts[u] += 1
        first.setdefault(u, d)
        last[u] = d

with open(os.path.join(DATA, "ticker_stats.txt"), "w") as f:
    f.write(f"Total tweets: {len(tweets)}\nDistinct $tickers: {len(counts)}\n\n")
    f.write("ticker  mentions  first_seen  last_seen\n")
    for tk, c in counts.most_common():
        if c >= 2:
            f.write(f"{tk:8} {c:6}   {first[tk]}  {last[tk]}\n")

by_month = defaultdict(list)
for t in tweets:
    by_month[(t.get("createdAtISO") or "")[:7]].append(t)

def line(t):
    m = t.get("metrics") or {}
    d = (t.get("createdAtISO") or "")[:16].replace("T", " ")
    txt = (t.get("text") or "").replace("\n", " ").strip()
    qt = t.get("quotedTweet") or {}
    q = ""
    if qt.get("text"):
        q = f"  [QT @{(qt.get('author') or {}).get('screenName','?')}: {qt['text'].replace(chr(10),' ').strip()[:280]}]"
    return f"[{d}] ♥{m.get('likes',0)} \U0001F441{m.get('views',0)} ↻{m.get('retweets',0)} {txt}{q}"

for mo in sorted(by_month):
    with open(os.path.join(CHUNK_DIR, f"{mo}.txt"), "w") as f:
        f.write(f"# Serenity (@{USER}) tweets — {mo} — {len(by_month[mo])} tweets\n\n")
        for t in by_month[mo]:
            f.write(line(t) + "\n")

print(f"{len(tweets)} tweets -> {len(by_month)} monthly chunks; "
      f"{sum(1 for c in counts.values() if c>=2)} tickers (>=2 mentions)")
