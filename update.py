#!/usr/bin/env python3
"""Incremental archive updater: pull latest tweets, merge (dedupe), refresh CSV + ticker_stats.

Requires xreach authenticated via Agent Reach cookies/browser profile.
Run from the repo root: `python3 update.py`. Prints a final `NEW=<n>` line; exits 0.
Does NOT touch git — the caller decides whether to commit/push based on NEW.
"""
import json, csv, os, re, subprocess
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

def xreach_json(args, timeout=180):
    try:
        p = subprocess.run(["xreach", *args, "--json"], capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0:
            print(f"PULL_ERROR {' '.join(args)}: {(p.stderr or p.stdout).strip()}")
            return []
        data = json.loads(p.stdout)
    except Exception as e:
        print(f"PULL_ERROR {' '.join(args)}: {e}")
        return []
    if isinstance(data, dict):
        return data.get("items") or data.get("tweets") or data.get("results") or data.get("data") or []
    return data if isinstance(data, list) else []

def normalize_xreach(t):
    if t.get("author", {}).get("screenName", "").lower() == USER:
        return t
    user = t.get("user") or {}
    out = {
        "id": str(t.get("id")),
        "text": t.get("text") or "",
        "author": {
            "id": user.get("restId") or user.get("id"),
            "name": user.get("name") or "Serenity",
            "screenName": user.get("screenName") or USER,
            "profileImageUrl": user.get("profileImageUrl"),
            "verified": user.get("isBlueVerified"),
        },
        "metrics": {
            "likes": t.get("likeCount"),
            "retweets": t.get("retweetCount"),
            "replies": t.get("replyCount"),
            "quotes": t.get("quoteCount"),
            "views": t.get("viewCount"),
            "bookmarks": t.get("bookmarkCount"),
        },
        "createdAt": t.get("createdAt"),
        "media": t.get("media") or [],
        "urls": t.get("urls") or [],
        "isRetweet": t.get("isRetweet"),
        "retweetedBy": None,
        "lang": t.get("lang"),
        "score": t.get("score"),
    }
    for key in ("isQuote", "isReply", "inReplyToTweetId", "inReplyToUserId", "conversationId"):
        if key in t:
            out[key] = t.get(key)
    if t.get("quotedTweet"):
        out["quotedTweet"] = t.get("quotedTweet")
    return ensure_times(out)

def pull(n=100, since=None):
    raw = xreach_json(["tweets", f"@{USER}", "-n", str(n)])
    if since:
        raw.extend(xreach_json([
            "search", f"from:{USER} since:{since}", "--type", "latest",
            "-n", str(n), "--all", "--max-pages", "3"
        ], timeout=240))
    rows, seen = [], set()
    for t in raw:
        if not isinstance(t, dict) or not t.get("id"):
            continue
        row = normalize_xreach(t)
        if row.get("author", {}).get("screenName", "").lower() != USER:
            continue
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        rows.append(row)
    return rows

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
    newest = max((parse_time(t) for t in arch if parse_time(t)), default=None)
    since = newest.astimezone(timezone.utc).date().isoformat() if newest else None
    new = [ensure_times(t) for t in pull(since=since) if t["id"] not in have]
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
