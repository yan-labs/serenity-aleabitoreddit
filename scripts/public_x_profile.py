"""Read public X profile/status pages without browser credentials.

The X command-line connector is useful when its session is healthy, but it is
not a safe single point of failure for an unattended public archive.  This
module reads the exact post data embedded in the public profile HTML first and
uses Jina only to fill gaps.  It never reads cookies, local storage, or browser
profiles.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import ast
import base64
import html
import re
import subprocess


USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131 Safari/537.36"


def fetch_url(url, timeout=35):
    """Fetch a public page with curl and return its text."""
    result = subprocess.run(
        [
            "curl", "-L", "-sS", "--fail-with-body", "--retry", "2",
            "--retry-delay", "1", "--retry-connrefused", "--connect-timeout",
            "10", "--max-time", str(timeout), "-A", USER_AGENT, url,
        ],
        capture_output=True,
        text=True,
        timeout=timeout + 5,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "curl failed").strip()
        raise RuntimeError(detail[:300])
    if not result.stdout.strip():
        raise RuntimeError("empty response")
    return result.stdout


def extract_profile_status_ids(profile_html, username, limit=20):
    """Return exact target-account status ids in page order, deduplicated."""
    username = username.lstrip("@").strip()
    escaped = re.escape(username)
    ids = []

    # Current public profile pages expose these links in several HTML/JSON
    # forms.  Restrict the first pass to the target account so quoted posts do
    # not become false archive entries.
    target_pattern = re.compile(
        rf"(?:https?://(?:www\.)?(?:x|twitter)\.com)?/{escaped}/status/(\d+)",
        re.IGNORECASE,
    )
    for match in target_pattern.finditer(profile_html.replace(r"\/", "/")):
        if match.group(1) not in ids:
            ids.append(match.group(1))
        if len(ids) >= limit:
            return ids

    # Some public profile renderings omit links and expose only entry ids.  In
    # that case they all belong to the rendered profile, so use them as a
    # bounded fallback.
    if not ids:
        for match in re.finditer(r"entry_id\s*:\s*[\"']tweet-(\d+)", profile_html):
            if match.group(1) not in ids:
                ids.append(match.group(1))
            if len(ids) >= limit:
                break
    return ids


def _js_string(page, field):
    """Return a quoted string field from X's server-rendered data blob."""
    match = re.search(
        rf'\b{re.escape(field)}:"((?:\\.|[^"\\])*)"',
        page,
    )
    return match.group(1) if match else None


def _js_int(page, field):
    match = re.search(rf'\b{re.escape(field)}:(?:"(\d+)"|(\d+))', page)
    if not match:
        return None
    return int(match.group(1) or match.group(2))


def _decode_js_string(value):
    if value is None:
        return ""
    try:
        # X uses JavaScript-style escapes in the RSC payload.  Python's literal
        # parser handles the common \\n, \\', \\" and unicode escapes while
        # preserving literal non-ASCII characters such as emoji.
        return html.unescape(ast.literal_eval('"' + value + '"'))
    except (SyntaxError, ValueError):
        return html.unescape(value).replace(r"\n", "\n").replace(r'\"', '"').replace(r"\'", "'")


def _balanced_object(page, start):
    """Return one RSC object, respecting braces inside quoted strings."""
    depth = 0
    quote = None
    escaped = False
    for index in range(start, len(page)):
        char = page[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ('"', "'"):
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return page[start:index + 1]
    return ""


def _rsc_definition(page, key):
    """Return the exact object definition for an RSC key, if present."""
    escaped = re.escape(key)
    match = re.search(rf'(?:"{escaped}"|{escaped}):\$R\[\d+\]=\{{', page)
    if not match:
        return ""
    return _balanced_object(page, match.end() - 1)


def _tweet_token(status_id):
    return base64.b64encode(f"Tweet:{status_id}".encode()).decode()


def _decode_ref_id(value):
    """Decode the numeric id carried by an X UserResults reference."""
    if not value:
        return None
    decoded = ""
    try:
        padded = value + "=" * (-len(value) % 4)
        decoded = base64.b64decode(padded).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        pass
    match = re.search(r"(?:UserResults|User):(\d+)", decoded or value)
    return match.group(1) if match else None


def _js_ref(page, field):
    match = re.search(
        rf'\b{re.escape(field)}:\$R\[\d+\]=\{{__ref:"([^"]+)"\}}',
        page,
    )
    return match.group(1) if match else None


def _has_non_null_field(page, field):
    if not page:
        return False
    if re.search(
        rf'\b{re.escape(field)}:\$R\[\d+\]=\{{__ref:"[^"]+"\}}',
        page,
    ):
        return True
    return bool(re.search(rf'\b{re.escape(field)}:(?!null\b)', page))


def _scoped_rsc_objects(page, prefix):
    """Return exact definitions whose keys belong to one tweet."""
    objects = []
    pattern = re.compile(rf'"{re.escape(prefix)}[^"]*":\$R\[\d+\]=\{{')
    for match in pattern.finditer(page):
        value = _balanced_object(page, match.end() - 1)
        if value:
            objects.append(value)
    return objects


def _note_tweet_text(page, token, tweet_obj):
    note_ref = _js_ref(tweet_obj, "note_tweet")
    if not note_ref:
        return None
    note_data = _rsc_definition(page, note_ref)
    results_ref = _js_ref(note_data, "note_tweet_results")
    results = _rsc_definition(page, results_ref) if results_ref else ""
    note_obj_ref = _js_ref(results, "result")
    note_obj = _rsc_definition(page, note_obj_ref) if note_obj_ref else ""
    text_value = _js_string(note_obj, "text")
    return _decode_js_string(text_value) if text_value is not None else None


def _parse_exact_profile_post(profile_html, status_id, username, user_id, display_name):
    """Parse a target Tweet object without mixing in referenced tweets."""
    token = _tweet_token(status_id)
    tweet_obj = _rsc_definition(profile_html, token)
    if not tweet_obj:
        return False, None

    core_ref = _js_ref(tweet_obj, "core")
    core = _rsc_definition(profile_html, core_ref or f"client:{token}:core")
    actual_user_ref = _js_ref(core, "user_results")
    actual_user_id = _decode_ref_id(actual_user_ref)
    if actual_user_id and str(actual_user_id) != str(user_id):
        return True, None

    details_ref = _js_ref(tweet_obj, "details")
    details = _rsc_definition(profile_html, details_ref or f"client:{token}:details")
    legacy_ref = _js_ref(tweet_obj, "legacy")
    legacy = _rsc_definition(profile_html, legacy_ref or f"client:{token}:legacy")
    counts_ref = _js_ref(tweet_obj, "counts")
    counts = _rsc_definition(profile_html, counts_ref or f"client:{token}:counts")
    views_ref = _js_ref(tweet_obj, "views")
    views = _rsc_definition(profile_html, views_ref or f"client:{token}:views")

    created_ms = _js_int(details, "created_at_ms")
    note_text = _note_tweet_text(profile_html, token, tweet_obj)
    text_value = note_text or _decode_js_string(_js_string(details, "full_text"))
    if created_ms is None or not text_value:
        return True, None

    created_at = datetime.fromtimestamp(created_ms / 1000, timezone.utc)
    created_iso = created_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    media_urls = []
    urls = []
    for scoped in _scoped_rsc_objects(profile_html, f"client:{token}:"):
        for media_url in re.findall(r'\bmedia_url_https:"((?:\\.|[^"\\])*)"', scoped):
            decoded = _decode_js_string(media_url)
            if decoded and decoded not in media_urls:
                media_urls.append(decoded)
        for expanded_url in re.findall(r'\bexpanded_url:"((?:\\.|[^"\\])*)"', scoped):
            decoded = _decode_js_string(expanded_url)
            if decoded and decoded not in urls:
                urls.append(decoded)

    metrics = {
        "likes": _js_int(counts, "favorite_count"),
        "retweets": _js_int(counts, "retweet_count"),
        "replies": _js_int(counts, "reply_count"),
        "quotes": _js_int(counts, "quote_count"),
        "views": _js_int(views, "count"),
        "bookmarks": _js_int(counts, "bookmark_count"),
    }
    return True, {
        "id": str(status_id),
        "text": text_value,
        "author": {
            "id": str(user_id),
            "name": display_name,
            "screenName": username,
            "profileImageUrl": None,
            "verified": None,
        },
        "metrics": metrics,
        "createdAt": created_at.strftime("%a %b %d %H:%M:%S +0000 %Y"),
        "createdAtISO": created_iso,
        "media": [{"url": url} for url in media_urls],
        "urls": urls,
        "isRetweet": _has_non_null_field(legacy, "retweeted_status_results"),
        "retweetedBy": None,
        "lang": _js_string(legacy, "lang"),
        "isQuote": _has_non_null_field(tweet_obj, "quoted_tweet_results"),
        "isReply": _has_non_null_field(tweet_obj, "reply_to_results")
        or _has_non_null_field(legacy, "in_reply_to_status_id_str"),
        "sourceUrl": f"https://x.com/{username}/status/{status_id}",
    }


def _tweet_chunk(profile_html, marker_start, status_id, status_ids):
    """Bound one tweet's RSC record before parsing fields from it."""
    window_end = min(len(profile_html), marker_start + 24000)
    window = profile_html[marker_start:window_end]
    rest = re.search(rf'\brest_id:"{re.escape(status_id)}"', window)
    if not rest:
        return ""
    after_rest = marker_start + rest.end()
    end = window_end
    for next_marker in re.finditer(r"TweetResults:(\d+)", profile_html[after_rest:window_end]):
        if next_marker.group(1) in status_ids and next_marker.group(1) != status_id:
            end = after_rest + next_marker.start()
            break
    return profile_html[marker_start:end]


def parse_profile_posts(profile_html, username, user_id, display_name, limit=20):
    """Parse exact public posts embedded in the x.com profile response."""
    username = username.lstrip("@").strip()
    status_ids = extract_profile_status_ids(profile_html, username, limit=limit)
    posts = []
    for status_id in status_ids:
        exact_found, exact_post = _parse_exact_profile_post(
            profile_html, status_id, username, user_id, display_name
        )
        if exact_found:
            if exact_post:
                posts.append(exact_post)
            continue
        marker = f"TweetResults:{status_id}"
        for match in re.finditer(re.escape(marker), profile_html):
            chunk = _tweet_chunk(profile_html, match.start(), status_id, status_ids)
            if not chunk:
                continue
            created_ms = _js_int(chunk, "created_at_ms")
            text_value = _js_string(chunk, "full_text")
            if created_ms is None or text_value is None:
                continue
            created_at = datetime.fromtimestamp(created_ms / 1000, timezone.utc)
            created_iso = created_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
            media_urls = []
            for media_url in re.findall(r'\bmedia_url_https:"((?:\\.|[^"\\])*)"', chunk):
                decoded = _decode_js_string(media_url)
                if decoded and decoded not in media_urls:
                    media_urls.append(decoded)
            urls = []
            for expanded_url in re.findall(r'\bexpanded_url:"((?:\\.|[^"\\])*)"', chunk):
                decoded = _decode_js_string(expanded_url)
                if decoded and decoded not in urls:
                    urls.append(decoded)
            metrics = {
                "likes": _js_int(chunk, "favorite_count"),
                "retweets": _js_int(chunk, "retweet_count"),
                "replies": _js_int(chunk, "reply_count"),
                "quotes": _js_int(chunk, "quote_count"),
                "views": _js_int(chunk, "view_count"),
                "bookmarks": _js_int(chunk, "bookmark_count"),
            }
            posts.append(
                {
                    "id": str(status_id),
                    "text": _decode_js_string(text_value),
                    "author": {
                        "id": str(user_id),
                        "name": display_name,
                        "screenName": username,
                        "profileImageUrl": None,
                        "verified": None,
                    },
                    "metrics": metrics,
                    "createdAt": created_at.strftime("%a %b %d %H:%M:%S +0000 %Y"),
                    "createdAtISO": created_iso,
                    "media": [{"url": url} for url in media_urls],
                    "urls": urls,
                    "isRetweet": bool(re.search(r"\bretweeted_status_results:(?!null\b)", chunk)),
                    "retweetedBy": None,
                    "lang": _js_string(chunk, "lang"),
                    "isQuote": "quoted_status_result" in chunk,
                    "isReply": "in_reply_to_status_id_str" in chunk,
                    "sourceUrl": f"https://x.com/{username}/status/{status_id}",
                }
            )
            break
    posts_by_id = {post["id"]: post for post in posts}
    return [posts_by_id[status_id] for status_id in status_ids if status_id in posts_by_id]


def _iso_time(value):
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _clean_markdown(text, username):
    text = html.unescape(text or "")
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s*(?:[*-]\s*)?@" + re.escape(username) + r"\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*(?:\*\s*)?##\s*Post\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" \t\r\n")


def _media_from_page(page):
    urls = []
    pattern = re.compile(r"https://pbs\.twimg\.com/[^)\s\"']+")
    for url in pattern.findall(page):
        url = html.unescape(url)
        if url not in urls:
            urls.append(url)
    return [{"url": url} for url in urls]


def parse_status_page(page, username, user_id, display_name, status_id):
    """Parse a Jina-rendered public X status into the archive row shape."""
    source_match = re.search(
        rf"(?:URL Source|Source URL):\s*https?://(?:www\.)?(?:x|twitter)\.com/{re.escape(username)}/status/{re.escape(str(status_id))}",
        page,
        re.IGNORECASE,
    )
    if not source_match:
        raise ValueError("status page does not belong to the requested account/status")

    time_match = re.search(r"^Published Time:\s*(\S+)\s*$", page, re.MULTILINE | re.IGNORECASE)
    if not time_match:
        raise ValueError("status page has no Published Time")
    created_at = _iso_time(time_match.group(1))

    quoted = re.search(r"^# .*? on X:\s*\"(.*)\"\s*$", page, re.MULTILINE)
    if quoted:
        text = _clean_markdown(quoted.group(1), username)
    else:
        marker = re.search(r"^Markdown Content:\s*\n(.*)$", page, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if not marker:
            raise ValueError("status page has no Markdown Content")
        body = marker.group(1)
        for footer in ("\n## Relevant people", "\n## Hashtags", "\n## Related", "\nSomething went wrong"):
            body = body.split(footer, 1)[0]
        author_line = re.search(
            rf"\[@{re.escape(username)}\]\([^)]*\)\s+(.*?)(?:\n|$)",
            body,
            re.IGNORECASE,
        )
        text = _clean_markdown(author_line.group(1) if author_line else body, username)
    if not text:
        raise ValueError("status page has empty text")

    return {
        "id": str(status_id),
        "text": text,
        "author": {
            "id": str(user_id),
            "name": display_name,
            "screenName": username,
            "profileImageUrl": None,
            "verified": None,
        },
        "metrics": {
            "likes": None,
            "retweets": None,
            "replies": None,
            "quotes": None,
            "views": None,
            "bookmarks": None,
        },
        "createdAt": created_at,
        "createdAtISO": created_at,
        "media": _media_from_page(page),
        "urls": [],
        "isRetweet": False,
        "isQuote": False,
        "isReply": False,
        "sourceUrl": f"https://x.com/{username}/status/{status_id}",
    }


def fetch_public_posts(username, user_id, display_name, limit=12):
    """Fetch recent public posts and diagnostics without authenticated state."""
    username = username.lstrip("@").strip()
    diagnostics = {
        "source": "x_public_profile+jina_status",
        "profile_url": f"https://x.com/{username}",
        "status_count": 0,
        "errors": [],
    }
    profile_html = ""
    posts = []
    try:
        profile_html = fetch_url(diagnostics["profile_url"])
        status_ids = extract_profile_status_ids(profile_html, username, limit=limit)
        posts = parse_profile_posts(profile_html, username, user_id, display_name, limit=limit)
        diagnostics["profile_parsed_count"] = len(posts)
    except Exception as exc:
        diagnostics["errors"].append(f"x.com profile: {exc}")
        status_ids = []

    if not status_ids:
        jina_profile = f"https://r.jina.ai/http://x.com/{username}"
        try:
            profile_text = fetch_url(jina_profile)
            status_ids = extract_profile_status_ids(profile_text, username, limit=limit)
            diagnostics["profile_source"] = "jina_profile"
        except Exception as exc:
            diagnostics["errors"].append(f"Jina profile: {exc}")
    else:
        diagnostics["profile_source"] = "x.com_profile"

    diagnostics["status_count"] = len(status_ids)
    parsed_ids = {post["id"] for post in posts}
    remaining_ids = [status_id for status_id in status_ids if status_id not in parsed_ids]

    def load_status(status_id):
        url = f"https://r.jina.ai/http://x.com/{username}/status/{status_id}"
        return status_id, fetch_url(url)

    with ThreadPoolExecutor(max_workers=min(4, max(1, len(remaining_ids)))) as pool:
        futures = {pool.submit(load_status, status_id): status_id for status_id in remaining_ids}
        for future in as_completed(futures):
            status_id = futures[future]
            try:
                _, page = future.result()
                posts.append(parse_status_page(page, username, user_id, display_name, status_id))
            except Exception as exc:
                diagnostics["errors"].append(f"status {status_id}: {exc}")

    posts.sort(key=lambda post: post.get("createdAtISO", ""), reverse=True)
    if posts:
        diagnostics["verification_source"] = (
            "x_public_profile_html"
            if diagnostics.get("profile_parsed_count")
            else "jina_status"
        )
        if diagnostics.get("profile_parsed_count"):
            diagnostics["source"] = (
                "x_public_profile_html+jina_status"
                if remaining_ids
                else "x_public_profile_html"
            )
        diagnostics["latest_id"] = posts[0]["id"]
        diagnostics["latest_time"] = posts[0]["createdAtISO"]
    return posts, diagnostics
