#!/usr/bin/env python3
"""Incremental archive updater: pull latest tweets, merge (dedupe), refresh CSV + ticker_stats.

Requires xreach authenticated via an Agent Reach browser profile.
Run from the repo root: `python3 update.py`. Prints a final `NEW=<n>` line; exits 0.
Run `python3 update.py --repair-full-text` repeatedly to backfill X Note Tweet text.
Does NOT touch git — the caller decides whether to commit/push based on NEW.
"""
import json, csv, os, re, shutil, subprocess, sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from scripts.public_x_profile import fetch_public_posts

USER = "aleabitoreddit"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ARCH = os.path.join(DATA, "aleabitoreddit_tweets.json")
SYNC_STATE = os.path.join(DATA, "sync_state.json")
FULL_TEXT_HELPER = os.path.join(HERE, "scripts", "xreach_note_text.mjs")
# Issue #2 reported the affected xreach Note Tweet period from this timestamp.
FULL_TEXT_REPAIR_START = "2026-06-30T00:00:00+00:00"
FULL_TEXT_REPAIR_BATCH_SIZE = 20
LOCAL_TZ = timezone(timedelta(hours=8))
XREACH_AUTH_FAILED = False
PUBLIC_FALLBACK_DIAGNOSTIC = None

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

def parse_tool_json(stdout):
    data = json.loads(stdout)
    if isinstance(data, dict):
        return data.get("items") or data.get("tweets") or data.get("results") or data.get("data") or []
    return data if isinstance(data, list) else []

def xreach_json(args, timeout=180):
    global XREACH_AUTH_FAILED
    if not shutil.which("xreach"):
        return []
    try:
        p = subprocess.run(["xreach", *args, "--json"], capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0:
            detail = (p.stderr or p.stdout).strip()
            if "Could not authenticate you" in detail or "not_authenticated" in detail:
                XREACH_AUTH_FAILED = True
            print(f"PULL_ERROR {' '.join(args)}: {detail}")
            return []
        return parse_tool_json(p.stdout)
    except Exception as e:
        print(f"PULL_ERROR {' '.join(args)}: {e}")
        return []

def xreach_note_text(args, timeout=180):
    if not shutil.which("node") or not shutil.which("xreach") or not os.path.exists(FULL_TEXT_HELPER):
        return {}
    try:
        p = subprocess.run(
            ["node", FULL_TEXT_HELPER, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if p.returncode != 0:
            print(f"FULL_TEXT_ERROR {' '.join(args)}: {(p.stderr or p.stdout).strip()}")
            return {}
        raw = json.loads(p.stdout)
        return {
            str(tweet_id): text
            for tweet_id, text in raw.items()
            if isinstance(text, str) and text
        } if isinstance(raw, dict) else {}
    except Exception as e:
        print(f"FULL_TEXT_ERROR {' '.join(args)}: {e}")
        return {}

def apply_full_text(rows, full_text):
    repaired = 0
    for row in rows:
        text = full_text.get(str(row.get("id")))
        if text and len(text) > len(row.get("text") or ""):
            row["text"] = text
            repaired += 1
    return repaired

def twitter_json(args, timeout=180):
    if not shutil.which("twitter"):
        return []
    try:
        p = subprocess.run(["twitter", *args, "--json"], capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0:
            print(f"PULL_ERROR twitter {' '.join(args)}: {(p.stderr or p.stdout).strip()}")
            return []
        return parse_tool_json(p.stdout)
    except Exception as e:
        print(f"PULL_ERROR twitter {' '.join(args)}: {e}")
        return []

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
    global PUBLIC_FALLBACK_DIAGNOSTIC
    raw = xreach_json(["tweets", f"@{USER}", "-n", str(n)])
    if since and not XREACH_AUTH_FAILED:
        raw.extend(xreach_json([
            "search", f"from:{USER} since:{since}", "--type", "latest",
            "-n", str(n), "--all", "--max-pages", "3"
        ], timeout=240))
    if not raw and not XREACH_AUTH_FAILED:
        raw = twitter_json(["user-posts", f"@{USER}", "-n", str(n)])
        if since:
            raw.extend(twitter_json([
                "search", "--from", USER, "--since", since, "--type", "latest",
                "-n", str(n)
            ], timeout=240))
    if not raw or XREACH_AUTH_FAILED:
        try:
            public_rows, PUBLIC_FALLBACK_DIAGNOSTIC = fetch_public_posts(
                USER, "1940360837547565056", "Serenity", limit=12
            )
            print(
                "FALLBACK_SOURCE=x_public_profile+jina_status "
                f"status_count={len(public_rows)} "
                f"latest_id={PUBLIC_FALLBACK_DIAGNOSTIC.get('latest_id', '')} "
                f"latest_time={PUBLIC_FALLBACK_DIAGNOSTIC.get('latest_time', '')}"
            )
            raw.extend(public_rows)
        except Exception as exc:
            print(f"PULL_ERROR public X fallback: {exc}")
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
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n"); w.writeheader()
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

def needs_public_text_repair(post):
    text = post.get("text") or ""
    return text.startswith("[](http://x.com/)") or "Log inSign up" in text

def main():
    repair_full_text = "--repair-full-text" in sys.argv[1:]
    sync_state = json.load(open(SYNC_STATE)) if os.path.exists(SYNC_STATE) else {}
    sync_state_changed = False
    raw_arch = json.load(open(ARCH))
    arch = [ensure_times(t) for t in raw_arch]
    normalized = arch != raw_arch
    have = {t["id"] for t in arch}
    newest = max((parse_time(t) for t in arch if parse_time(t)), default=None)
    since = newest.astimezone(timezone.utc).date().isoformat() if newest else None
    pulled = [ensure_times(t) for t in pull(since=since)]
    new = [t for t in pulled if t["id"] not in have]
    existing_by_id = {t["id"]: t for t in arch}
    repaired_public = [
        t for t in pulled
        if t["id"] in existing_by_id
        and needs_public_text_repair(existing_by_id[t["id"]])
        and not needs_public_text_repair(t)
    ]
    new.sort(key=sort_key)
    repaired = 0
    if new and not XREACH_AUTH_FAILED:
        repaired += apply_full_text(new, xreach_note_text(["--ids", *(t["id"] for t in new)]))
    if repair_full_text:
        cursor = sync_state.get("note_text_repair_cursor")
        eligible = [
            t for t in arch
            if (t.get("createdAtISO") or "") >= FULL_TEXT_REPAIR_START
            and (not cursor or (t.get("createdAtISO") or "") < cursor)
        ]
        batch = eligible[:FULL_TEXT_REPAIR_BATCH_SIZE]
        if batch:
            affected_ids = [t["id"] for t in batch]
            repaired += apply_full_text(
                arch,
                xreach_note_text(["--ids", *affected_ids], timeout=900),
            )
            sync_state["note_text_repair_cursor"] = batch[-1].get("createdAtISO")
            sync_state["note_text_repair_remaining"] = len(eligible) - len(batch)
            sync_state_changed = True
            print(f"FULL_TEXT_REPAIR_REMAINING={sync_state['note_text_repair_remaining']}")
    if new or repaired_public or normalized or repaired:
        merged = {t["id"]: t for t in arch}
        for t in new:
            merged[t["id"]] = t
        for t in repaired_public:
            merged[t["id"]] = t
        rows = sorted(merged.values(), key=sort_key, reverse=True)
        json.dump(rows, open(ARCH, "w"), ensure_ascii=False, indent=2)
        write_csv(rows)
        write_ticker_stats(rows)
        for t in new:
            print(f"  + {t.get('createdAtISO', '')[:16]} {t['id']} {(t.get('text') or '')[:60].replace(chr(10),' ')}")
        if new:
            print(f"TOTAL={len(rows)} NEWEST={rows[0].get('createdAtISO', '')}")
        if repaired_public:
            print(f"PUBLIC_TEXT_REPAIRED={len(repaired_public)}")
    if repaired:
        print(f"FULL_TEXT_REPAIRED={repaired}")
    if sync_state_changed:
        json.dump(sync_state, open(SYNC_STATE, "w"), ensure_ascii=False, indent=2)
        print()
    print(f"NEW={len(new)}")

if __name__ == "__main__":
    main()
