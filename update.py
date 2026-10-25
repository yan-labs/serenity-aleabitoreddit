#!/usr/bin/env python3
"""Incremental archive updater: merge new tweets, dedupe, refresh CSV + ticker_stats.

Primary (Grok Bot / unattended): `python3 update.py --from-json path` merges an
X API or connector JSON dump (archive-shaped list, or `{ "data": [...] }` with
optional `includes`; prefer `note_tweet.text` over truncated `text`).
Thin alias: `python3 scripts/ingest_x_posts.py path`.

Optional offline live pull: `python3 update.py` without `--from-json` uses the
public x.com profile / Jina status fallback (no browser cookies). Not the
supported unattended path.

Also: `--repair-public-profile` replaces rows from an older public-profile parser.
Prints a final `NEW=<n>` line; exits 0. Does NOT touch git — the caller commits.
"""
import copy, json, csv, os, re, sys, tempfile
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from scripts.public_x_profile import fetch_public_posts

USER = "aleabitoreddit"
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
ARCH = os.path.join(DATA, "aleabitoreddit_tweets.json")
SYNC_STATE = os.path.join(DATA, "sync_state.json")
def _local_tz():
    """Timezone for `createdAtLocal`. Defaults to UTC+8 (Asia/Shanghai), which
    every existing archive row uses; override with SERENITY_LOCAL_UTC_OFFSET
    (hours, e.g. "9" or "-5.5"). Changing it only affects newly added rows."""
    raw = os.environ.get("SERENITY_LOCAL_UTC_OFFSET", "8")
    try:
        hours = float(raw)
        if not -14 <= hours <= 14:
            raise ValueError
    except ValueError:
        raise SystemExit(f"SERENITY_LOCAL_UTC_OFFSET must be hours in [-14, 14], got {raw!r}")
    return timezone(timedelta(hours=hours))


LOCAL_TZ = _local_tz()
PUBLIC_FALLBACK_DIAGNOSTIC = None
# Keys under which a dict-shaped dump may carry its rows.
DUMP_LIST_KEYS = ("items", "tweets", "results", "data", "posts")


def atomic_write(path, write_fn):
    """Write via a temp file in the same dir, then os.replace (no torn files)."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-", suffix=os.path.basename(path))
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            write_fn(f)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_json(path, obj):
    atomic_write(path, lambda f: json.dump(obj, f, ensure_ascii=False, indent=2))


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
        t["createdAtISO"] = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if dt and not t.get("createdAtLocal"):
        t["createdAtLocal"] = dt.astimezone(LOCAL_TZ).strftime("%Y-%m-%d %H:%M")
    return t

def sort_key(t):
    dt = parse_time(t)
    return dt.isoformat() if dt else ""

def _index_includes(includes):
    """Index X API `includes` by media key, user id and post id."""
    media_by_key = {
        m.get("media_key"): m
        for m in (includes.get("media") or [])
        if isinstance(m, dict) and m.get("media_key")
    }
    users_by_id = {
        u.get("id"): u
        for u in (includes.get("users") or [])
        if isinstance(u, dict) and u.get("id")
    }
    posts_by_id = {}
    for key in ("posts", "tweets"):
        for item in (includes.get(key) or []):
            if isinstance(item, dict) and item.get("id"):
                posts_by_id[str(item["id"])] = item
    return media_by_key, users_by_id, posts_by_id


def _note_text(post):
    note = post.get("note_tweet")
    return note.get("text") if isinstance(note, dict) else None


def _post_text(t):
    """Prefer full `note_tweet.text`, keeping leading @mentions from `text`."""
    note = _note_text(t)
    text_body = note or t.get("text") or ""
    trunc = t.get("text") or ""
    if note and trunc.startswith("@") and not text_body.startswith("@"):
        m = re.match(r"^((?:@\w+\s+)+)", trunc)
        if m:
            text_body = m.group(1) + text_body
    return text_body


def _post_datetime(t):
    if t.get("createdAtISO"):
        return datetime.fromisoformat(t["createdAtISO"].replace("Z", "+00:00"))
    created = t.get("created_at") or t.get("createdAt")
    if not created:
        return None
    try:
        return datetime.fromisoformat(str(created).replace("Z", "+00:00").replace(".000", ""))
    except ValueError:
        try:
            return parsedate_to_datetime(created)
        except Exception:
            return None


def _references(t):
    """Return (is_reply, is_quote, reply_to_id, quote_id)."""
    refs = [r for r in (t.get("referenced_tweets") or []) if isinstance(r, dict)]

    def first(kind):
        return next((r.get("id") for r in refs if r.get("type") == kind), None)

    is_reply = bool(t.get("isReply")) or any(r.get("type") == "replied_to" for r in refs)
    is_quote = bool(t.get("isQuote")) or any(r.get("type") == "quoted" for r in refs)
    reply_to = t.get("inReplyToTweetId") or first("replied_to")
    return is_reply, is_quote, reply_to, first("quoted")


def _post_media(t, media_by_key):
    media = t.get("media") if isinstance(t.get("media"), list) else []
    if not media:
        for mk in ((t.get("attachments") or {}).get("media_keys") or []):
            m = media_by_key.get(mk) or {}
            url = m.get("url") or m.get("preview_image_url")
            if url:
                media.append({"url": url})
    return media


def _post_urls(t):
    urls = t.get("urls") if isinstance(t.get("urls"), list) else []
    if not urls:
        for u in ((t.get("entities") or {}).get("urls") or []):
            exp = u.get("expanded_url") or ""
            if exp and "/photo/" not in exp:
                urls.append(exp)
    return urls


def _quoted_post(t, quote_id, posts_by_id, users_by_id):
    quoted = t.get("quotedTweet")
    if quoted is not None or not quote_id:
        return quoted
    qt = posts_by_id.get(str(quote_id))
    if not qt:
        return {"id": str(quote_id)}
    quser = users_by_id.get(qt.get("author_id")) or {}
    return {
        "id": str(qt["id"]),
        "text": _note_text(qt) or qt.get("text") or "",
        "author": {
            "id": qt.get("author_id"),
            "name": quser.get("name"),
            "screenName": quser.get("username"),
        },
    }


# archive metric name -> X API / archive field names, in lookup order
METRIC_KEYS = {
    "likes": ("likes", "like_count"),
    "retweets": ("retweets", "retweet_count", "repost_count"),
    "replies": ("replies", "reply_count"),
    "quotes": ("quotes", "quote_count"),
    "views": ("views", "impression_count"),
    "bookmarks": ("bookmarks", "bookmark_count"),
}


def _post_metrics(t):
    pm = t.get("public_metrics") or t.get("metrics") or {}

    def metric(keys):
        for k in keys:
            if isinstance(pm, dict) and pm.get(k) is not None:
                return pm.get(k)
        return None

    return {name: metric(keys) for name, keys in METRIC_KEYS.items()}


def normalize_x_api_post(t, includes=None):
    """Map an X API v2 post (or already-archive-shaped row) into archive schema.

    The key order of the returned dict is the on-disk order in the archive;
    tests/test_normalize.py pins it.
    """
    includes = includes or {}
    if t.get("author", {}).get("screenName", "").lower() == USER and t.get("createdAtISO"):
        return ensure_times(t)
    media_by_key, users_by_id, posts_by_id = _index_includes(includes)
    dt = _post_datetime(t)
    author_user = users_by_id.get(t.get("author_id")) or {}
    author = t.get("author") if isinstance(t.get("author"), dict) else {}
    is_reply, is_quote, reply_to, quote_id = _references(t)
    quoted = _quoted_post(t, quote_id, posts_by_id, users_by_id)

    out = {
        "id": str(t.get("id")),
        "text": _post_text(t),
        "author": {
            "id": author.get("id") or author_user.get("id") or t.get("author_id"),
            "name": author.get("name") or author_user.get("name") or "Serenity",
            "screenName": author.get("screenName") or author_user.get("username") or USER,
            "profileImageUrl": author.get("profileImageUrl") or author_user.get("profile_image_url"),
            "verified": author.get("verified") if "verified" in author else bool(author_user.get("verified")),
        },
        "metrics": _post_metrics(t),
        "createdAt": t.get("createdAt") or (dt.strftime("%a %b %d %H:%M:%S +0000 %Y") if dt else None),
        "media": _post_media(t, media_by_key),
        "urls": _post_urls(t),
        "isRetweet": bool(t.get("isRetweet")),
        "retweetedBy": t.get("retweetedBy"),
        "lang": t.get("lang"),
        "isQuote": is_quote,
        "isReply": is_reply,
        "conversationId": t.get("conversationId") or t.get("conversation_id"),
    }
    if reply_to:
        out["inReplyToTweetId"] = str(reply_to)
    if t.get("inReplyToUserId"):
        out["inReplyToUserId"] = str(t.get("inReplyToUserId"))
    if quoted is not None:
        out["quotedTweet"] = quoted
    if dt and not out.get("createdAtISO"):
        out["createdAtISO"] = dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return ensure_times(out)


def load_from_json(path):
    try:
        raw = json.load(open(path))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"PULL_ERROR cannot read JSON dump {path}: {exc}") from exc
    includes = {}
    if isinstance(raw, dict):
        includes = raw.get("includes") or {}
        items = next((raw[k] for k in DUMP_LIST_KEYS if raw.get(k)), [])
        if not items and all(k in raw for k in ("id", "text")):
            items = [raw]
        # An X API page with zero results is `{"meta": {"result_count": 0}}`
        # (no `data` key). Anything else without a recognised list is a bad
        # dump — fail loudly instead of stamping a healthy empty check.
        recognised = any(k in raw for k in DUMP_LIST_KEYS) or "meta" in raw or items
        if not recognised:
            raise ValueError(
                f"PULL_ERROR unrecognised JSON dump shape in {path}: "
                f"top-level keys {sorted(raw)[:8]}"
            )
    elif isinstance(raw, list):
        items = raw
    else:
        raise ValueError(f"PULL_ERROR JSON dump {path} must be a list or object")
    rows, seen = [], set()
    for t in items:
        if not isinstance(t, dict) or not t.get("id"):
            continue
        row = normalize_x_api_post(t, includes)
        if row.get("author", {}).get("screenName", "").lower() != USER:
            continue
        if row["id"] in seen:
            continue
        seen.add(row["id"])
        rows.append(row)
    return rows



def pull(n=100, since=None):
    """Optional live pull via public x.com profile / Jina (not the unattended path).

    `since` is accepted for CLI compatibility but unused: the public page only
    exposes a short recent window (~`n` capped at 12).
    """
    global PUBLIC_FALLBACK_DIAGNOSTIC
    raw = []
    try:
        public_rows, PUBLIC_FALLBACK_DIAGNOSTIC = fetch_public_posts(
            USER, "1940360837547565056", "Serenity", limit=min(max(n, 1), 12)
        )
        fallback_source = (PUBLIC_FALLBACK_DIAGNOSTIC or {}).get(
            "source", "x_public_profile+jina_status"
        )
        print(
            f"FALLBACK_SOURCE={fallback_source} "
            f"status_count={len(public_rows)} "
            f"latest_id={PUBLIC_FALLBACK_DIAGNOSTIC.get('latest_id', '')} "
            f"latest_time={PUBLIC_FALLBACK_DIAGNOSTIC.get('latest_time', '')}"
        )
        raw.extend(public_rows)
    except Exception as exc:
        print(f"PULL_ERROR public X fallback: {exc}")
        PUBLIC_FALLBACK_DIAGNOSTIC = {"errors": [str(exc)[:300]], "fatal": True}
    rows, seen = [], set()
    for t in raw:
        if not isinstance(t, dict) or not t.get("id"):
            continue
        row = ensure_times(t)
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
    def write(f):
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
    atomic_write(os.path.join(DATA, "aleabitoreddit_tweets.csv"), write)

TICK = re.compile(r"\$([A-Za-z]{1,6})\b")

def write_ticker_stats(rows):
    """Single source of truth for data/ticker_stats.txt (also used by prep.py).

    Ties are broken alphabetically so reruns produce byte-identical output.
    """
    c, first, last = Counter(), {}, {}
    for t in sorted(rows, key=sort_key):
        txt = (t.get("text", "") or "") + " " + ((t.get("quotedTweet") or {}).get("text", "") or "")
        d = (t.get("createdAtISO") or "")[:10]
        for m in set(TICK.findall(txt)):
            u = m.upper(); c[u] += 1; first.setdefault(u, d); last[u] = d
    def write(f):
        f.write(f"Total tweets: {len(rows)}\nDistinct $tickers: {len(c)}\n\nticker  mentions  first_seen  last_seen\n")
        for tk, n in sorted(c.items(), key=lambda item: (-item[1], item[0])):
            if n >= 2:
                f.write(f"{tk:8} {n:6}   {first[tk]}  {last[tk]}\n")
    atomic_write(os.path.join(DATA, "ticker_stats.txt"), write)

def needs_public_text_repair(post):
    text = post.get("text") or ""
    return text.startswith("[](http://x.com/)") or "Log inSign up" in text

def merge_public_profile_row(previous, current):
    """Keep reliable older optional fields when the public page omits them."""
    merged = dict(current)
    for key, value in previous.items():
        if key not in merged or (merged[key] in (None, "", []) and value not in (None, "", [])):
            merged[key] = value
    for container in ("author", "metrics"):
        old_values = previous.get(container)
        new_values = merged.get(container)
        if isinstance(old_values, dict) and isinstance(new_values, dict):
            for key, value in old_values.items():
                if new_values.get(key) in (None, "", []) and value not in (None, "", []):
                    new_values[key] = value
    old_media = previous.get("media")
    new_media = merged.get("media")
    if isinstance(old_media, list) and isinstance(new_media, list) and old_media and new_media:
        old_by_url = {
            item.get("url"): item
            for item in old_media
            if isinstance(item, dict) and item.get("url")
        }
        combined = []
        seen_urls = set()
        for item in new_media:
            if not isinstance(item, dict):
                combined.append(item)
                continue
            url = item.get("url")
            enriched = dict(old_by_url.get(url, {}))
            enriched.update(item)
            combined.append(enriched)
            if url:
                seen_urls.add(url)
        combined.extend(
            item for item in old_media
            if isinstance(item, dict)
            and item.get("url")
            and item.get("url") not in seen_urls
        )
        merged["media"] = combined
    return merged

def main():
    repair_public_profile = "--repair-public-profile" in sys.argv[1:]
    args = sys.argv[1:]
    from_json = None
    if "--from-json" in args:
        idx = args.index("--from-json")
        if idx + 1 >= len(args):
            print("PULL_ERROR --from-json requires a path")
            print("NEW=0")
            print("NEW_IDS=")
            sys.exit(1)
        from_json = args[idx + 1]
    sync_state = json.load(open(SYNC_STATE)) if os.path.exists(SYNC_STATE) else {}
    sync_state_changed = False
    raw_arch = json.load(open(ARCH))
    # ensure_times mutates in place, so compare against a deep copy; otherwise
    # `normalized` is always False and backfilled timestamps are never saved.
    arch = [ensure_times(t) for t in copy.deepcopy(raw_arch)]
    normalized = arch != raw_arch
    have = {t["id"] for t in arch}
    newest = max((parse_time(t) for t in arch if parse_time(t)), default=None)
    since = newest.astimezone(timezone.utc).date().isoformat() if newest else None
    if from_json:
        try:
            pulled = [ensure_times(t) for t in load_from_json(from_json)]
        except ValueError as exc:
            print(exc)
            print("NEW=0")
            print("NEW_IDS=")
            sys.exit(1)
        print(f"FROM_JSON={from_json} pulled={len(pulled)}")
    else:
        pulled = [ensure_times(t) for t in pull(since=since)]
    new = [t for t in pulled if t["id"] not in have]
    existing_by_id = {t["id"]: t for t in arch}
    repaired_public = [
        t for t in pulled
        if t["id"] in existing_by_id
        and needs_public_text_repair(existing_by_id[t["id"]])
        and not needs_public_text_repair(t)
    ]
    public_profile_repairs = []
    if repair_public_profile and (PUBLIC_FALLBACK_DIAGNOSTIC or {}).get("source") == "x_public_profile_html":
        repaired_ids = {t["id"] for t in repaired_public}
        public_profile_repairs = [
            t for t in pulled
            if t["id"] in existing_by_id
            and t["id"] not in repaired_ids
        ]
    new.sort(key=sort_key)
    if new or repaired_public or public_profile_repairs or normalized:
        merged = {t["id"]: t for t in arch}
        for t in new:
            merged[t["id"]] = t
        for t in repaired_public:
            merged[t["id"]] = merge_public_profile_row(existing_by_id[t["id"]], t)
        for t in public_profile_repairs:
            merged[t["id"]] = merge_public_profile_row(existing_by_id[t["id"]], t)
        rows = sorted(merged.values(), key=sort_key, reverse=True)
        write_json(ARCH, rows)
        write_csv(rows)
        write_ticker_stats(rows)
        for t in new:
            print(f"  + {t.get('createdAtISO', '')[:16]} {t['id']} {(t.get('text') or '')[:60].replace(chr(10),' ')}")
        if new:
            print(f"TOTAL={len(rows)} NEWEST={rows[0].get('createdAtISO', '')}")
        if repaired_public:
            print(f"PUBLIC_TEXT_REPAIRED={len(repaired_public)}")
        if public_profile_repairs:
            print(f"PUBLIC_PROFILE_REPAIRED={len(public_profile_repairs)}")
    checked_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    verification_source = (
        "from_json" if from_json else (
            (PUBLIC_FALLBACK_DIAGNOSTIC or {}).get("verification_source")
            or (PUBLIC_FALLBACK_DIAGNOSTIC or {}).get("source")
            or "x_public_profile+jina_status"
        )
    )
    if new:
        newest_row = max(new, key=lambda t: t.get("createdAtISO") or "")
        sync_state["last_tweet_id"] = newest_row["id"]
        sync_state["last_update_time"] = newest_row.get("createdAtISO")
        sync_state["source_health"] = {
            "status": "ok",
            "direct_status": "ok",
            "verification_source": verification_source,
            "freshness": "verified",
            "latest_returned_id": newest_row["id"],
            "latest_returned_time": newest_row.get("createdAtISO"),
            "new_posts_merged": len(new),
            "checked_time": checked_time,
            "next_action": (
                "Merged via --from-json (Grok Bot / X API primary path)."
                if from_json else
                "Cursor advanced from public-profile live pull."
            ),
        }
        sync_state_changed = True
    elif not from_json and not pulled:
        # The live pull returned nothing. That is a source failure, not a
        # verified "no new posts": keep the cursor and say so explicitly.
        diag = PUBLIC_FALLBACK_DIAGNOSTIC or {}
        health = dict(sync_state.get("source_health") or {})
        health.update({
            "status": "error",
            "direct_status": "error",
            "verification_source": verification_source,
            "freshness": "stale",
            "new_posts_merged": 0,
            "checked_time": checked_time,
            "errors": (diag.get("errors") or ["public fallback returned no posts"])[:5],
            "next_action": "Public-profile live pull returned no posts; cursor kept. "
                           "Use the X connector + --from-json path.",
        })
        sync_state["source_health"] = health
        sync_state_changed = True
    else:
        # Stamp a successful empty check so routines know we ran.
        health = dict(sync_state.get("source_health") or {})
        health.update({
            "status": "ok",
            "direct_status": "ok",
            "verification_source": verification_source,
            "freshness": "verified",
            "new_posts_merged": 0,
            "checked_time": checked_time,
            "errors": [],
            "next_action": (
                "No new posts in --from-json dump."
                if from_json else
                "No new posts from public-profile live pull."
            ),
        })
        if pulled:
            latest = max(pulled, key=lambda t: t.get("createdAtISO") or "")
            health["latest_returned_id"] = latest.get("id")
            health["latest_returned_time"] = latest.get("createdAtISO")
        sync_state["source_health"] = health
        sync_state_changed = True
    if sync_state_changed:
        write_json(SYNC_STATE, sync_state)
        print()
    print(f"NEW={len(new)}")
    print("NEW_IDS=" + ",".join(t["id"] for t in new))

if __name__ == "__main__":
    main()
