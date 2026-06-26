#!/usr/bin/env python3
"""Lightweight repository consistency checks.

This is intentionally dependency-free so maintainers can run it before committing
incremental archive or skill updates.
"""
import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SKILL = ROOT / "serenity-aleabitoreddit"
USER = "aleabitoreddit"
MIN_THESES_LINES = 500
REQUIRED_THESIS_TICKERS = {
    "AAOI",
    "ARM",
    "AXTI",
    "COHR",
    "INTC",
    "LITE",
    "MRVL",
    "NBIS",
    "SIVE",
}


def fail(message):
    print(f"FAIL: {message}")
    return 1


def read_text(path):
    return path.read_text(encoding="utf-8")


def main():
    errors = 0

    tweets_path = DATA / "aleabitoreddit_tweets.json"
    csv_path = DATA / "aleabitoreddit_tweets.csv"
    theses_path = SKILL / "references" / "theses.md"
    readme_path = ROOT / "README.md"
    skill_path = SKILL / "SKILL.md"
    sync_state_path = DATA / "sync_state.json"

    tweets = json.loads(read_text(tweets_path))
    if not isinstance(tweets, list):
        errors += fail(f"{tweets_path} must contain a JSON list")
        tweets = []

    ids = [str(row.get("id")) for row in tweets if row.get("id")]
    duplicate_count = len(ids) - len(set(ids))
    if duplicate_count:
        errors += fail(f"{tweets_path} has {duplicate_count} duplicate tweet ids")

    bad_authors = [
        row.get("id")
        for row in tweets
        if (row.get("author") or {}).get("screenName", "").lower() != USER
    ]
    if bad_authors:
        errors += fail(f"{tweets_path} contains {len(bad_authors)} non-{USER} rows")

    with csv_path.open(newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    csv_ids = [row.get("id") for row in csv_rows if row.get("id")]
    if len(csv_rows) != len(tweets):
        errors += fail(f"CSV row count {len(csv_rows)} != JSON row count {len(tweets)}")
    if set(csv_ids) != set(ids):
        errors += fail("CSV and JSON tweet id sets differ")

    if sync_state_path.exists():
        sync_state = json.loads(read_text(sync_state_path))
        last_tweet_id = str(sync_state.get("last_tweet_id") or "")
        if last_tweet_id and last_tweet_id not in set(ids):
            print(
                "WARN: sync_state.json last_tweet_id is not present in the raw "
                "tweet archive"
            )

    tweet_count = f"{len(tweets):,}"
    readme = read_text(readme_path)
    skill = read_text(skill_path)
    for path, text in ((readme_path, readme), (skill_path, skill)):
        if tweet_count not in text:
            errors += fail(f"{path} does not mention current tweet count {tweet_count}")

    theses = read_text(theses_path)
    thesis_lines = theses.splitlines()
    if len(thesis_lines) < MIN_THESES_LINES:
        errors += fail(
            f"{theses_path} has only {len(thesis_lines)} lines; expected at least "
            f"{MIN_THESES_LINES}"
        )

    headings = {
        match.group(1).upper()
        for match in re.finditer(r"^###\s+(?:\$)?([A-Z][A-Z0-9]{1,5})\b", theses, re.M)
    }
    missing = sorted(REQUIRED_THESIS_TICKERS - headings)
    if missing:
        errors += fail(f"{theses_path} is missing required thesis headings: {missing}")

    if errors:
        return 1
    print(
        f"OK: {len(tweets)} tweets, {len(csv_rows)} CSV rows, "
        f"{len(thesis_lines)} thesis lines"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
