#!/usr/bin/env python3
"""Incremental archive updater: pull latest tweets, merge (dedupe), refresh CSV + ticker_stats.

Requires twitter-cli authenticated (env TWITTER_AUTH_TOKEN + TWITTER_CT0 on headless hosts).
Run from the repo root: `python3 update.py`. Prints a final `NEW=<n>` line; exits 0.
Does NOT touch git — the caller decides whether to commit/push based on NEW.
"""
import json, csv, os, re, subprocess, tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

USER = "aleabitoreddit"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ARCH = os.path.join(DATA, "aleabitoreddit_tweets.json")
LOCAL_TZ = timezone(timedelta(hours=8))

def parse_time(t):
    iso = t.get("createdAtISO")
    if iso:
        return datetime.fromisoformat(iso.replace("Z", "+00:00"))
    created = t.get("createdAt")
    if created:
        return parsedate_to_datetime(created)
    return None

def ensure_times(t):
    dt = parse_time(t)
    if dt and not t.get("createdAtISO"):
        t["createdAtISO"] = dt.astimezone(timezone.utc).isoformat()
    if dt and not t.get("createdAtLocal"):
        t["createdAtLocal"] = dt.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")
    return t

def sort_key(t):
    dt = parse_time(t)
    return dt.isoformat() if dt else ""

def pull(n=100):
    tmp = tempfile.mktemp(suffix=".json")
    try:
        subprocess.run(["twitter", "user-posts", USER, "-n", str(n), "-o", tmp],
                       capture_output=True, text=True, timeout=180)
        if os.path.exists(tmp):
            data = json.load(open(tmp))
            return [t for t in data if t.get("author", {}).get("screenName", "").lower() == USER]
    except Exception as e:
        print(f"PULL_ERROR {e}")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return []

def write_csv(rows):
    cols = ["id", "url", "createdAtISO", "createdAtLocal", "lang", "isRetweet",
            "retweetedBy", "likes", "retweets", "replies", "quotes", "views",
            "bookmarks", "media_count", "media_urls", "link_urls",
            "quoted_id", "quoted_author", "quoted_text", "text"]
    def csv_text(text):
        return "\n".join(line.rstrip() for line in (text or "").replace("\r", " ").split("\n"))
    with open(os.path.join(DATA, "aleabitoreddit_tweets.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for t in rows:
            m = t.get("metrics") or {}; media = t.get("media") or []; qt = t.get("quotedTweet") or {}
            w.writerow({
                "id": t.get("id"), "url": f"https://x.com/{USER}/status/{t.get('id')}",
                "createdAtISO": t.get("createdAtISO"), "createdAtLocal": t.get("createdAtLocal"),
                "lang": t.get("lang"), "isRetweet": t.get("isRetweet"), "retweetedBy": t.get("retweetedBy"),
                "likes": m.get("likes"), "retweets": m.get("retweets"), "replies": m.get("replies"),
                "quotes": m.get("quotes"), "views": m.get("views"), "bookmarks": m.get("bookmarks"),
                "media_count": len(media),
                "media_urls": " | ".join(x.get("url", "") for x in media if isinstance(x, dict)),
                "link_urls": " | ".join(t.get("urls") or []),
                "quoted_id": qt.get("id"), "quoted_author": (qt.get("author") or {}).get("screenName"),
                "quoted_text": csv_text(qt.get("text")).replace("\n", " "),
                "text": csv_text(t.get("text"))})

def write_ticker_stats(rows):
    TICK = re.compile(r"\$([A-Za-z]{1,6})\b")
    c, first, last = Counter(), {}, {}
    for t in sorted(rows, key=lambda x: x.get("createdAtISO", "")):
        txt = (t.get("text", "") or "") + " " + ((t.get("quotedTweet") or {}).get("text", "") or "")
        d = (t.get("createdAtISO") or "")[:10]
        for m in set(TICK.findall(txt)):
            u = m.upper(); c[u] += 1; first.setdefault(u, d); last[u] = d
    with open(os.path.join(DATA, "ticker_stats.txt"), "w") as f:
        f.write(f"Total tweets: {len(rows)}\nDistinct $tickers: {len(c)}\n\nticker  mentions  first_seen  last_seen\n")
        for tk, n in sorted(c.items(), key=lambda item: (-item[1], item[0])):
            if n >= 2:
                f.write(f"{tk:8} {n:6}   {first[tk]}  {last[tk]}\n")

def main():
    raw_arch = json.load(open(ARCH))
    arch = [ensure_times(t) for t in raw_arch]
    normalized = arch != raw_arch
    have = {t["id"] for t in arch}
    new = [ensure_times(t) for t in pull() if t["id"] not in have]
    new.sort(key=sort_key)
    if new or normalized:
        merged = {t["id"]: t for t in arch}
        for t in new:
            merged[t["id"]] = t
        rows = sorted(merged.values(), key=sort_key, reverse=True)
        json.dump(rows, open(ARCH, "w"), ensure_ascii=False, indent=2)
        write_csv(rows)
        write_ticker_stats(rows)
        for t in new:
            print(f"  + {t.get('createdAtISO', '')[:16]} {t['id']} {(t.get('text') or '')[:60].replace(chr(10),' ')}")
        if new:
            print(f"TOTAL={len(rows)} NEWEST={rows[0].get('createdAtISO', '')}")
    print(f"NEW={len(new)}")

if __name__ == "__main__":
    main()
