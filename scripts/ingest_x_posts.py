#!/usr/bin/env python3
"""Thin CLI for Grok Bot: merge an X API JSON dump into the Serenity archive.

Same merge/dedupe/CSV/ticker_stats/sync_state path as:

  python3 update.py --from-json <dump.json>

Accepts archive-shaped rows or X API `{ "data": [...], "includes": {...} }`.
Prints machine-readable `NEW=<n>` and `NEW_IDS=...` (via update.py).

Usage:
  python3 scripts/ingest_x_posts.py /tmp/new_posts.json
  python3 scripts/ingest_x_posts.py --help
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
UPDATE_PY = os.path.join(ROOT, "update.py")


def usage(code: int = 0) -> None:
    print(
        "Usage: python3 scripts/ingest_x_posts.py <dump.json>\n"
        "\n"
        "Merge/dedupe by tweet id into data/aleabitoreddit_tweets.json,\n"
        "refresh CSV + ticker_stats, advance data/sync_state.json.\n"
        "Delegates to: python3 update.py --from-json <dump.json>\n"
        "\n"
        "Dump shapes: list of archive rows, or "
        '{ "data": [...], "includes": {...} }.\n'
        "Does not commit or distill — caller does that.",
        file=sys.stderr if code else sys.stdout,
    )
    raise SystemExit(code)


def main(argv: list[str]) -> int:
    args = [a for a in argv if a]
    if not args or args[0] in ("-h", "--help"):
        usage(0 if args and args[0] in ("-h", "--help") else 1)
    if len(args) != 1:
        usage(1)
    path = args[0]
    if not os.path.isfile(path):
        print(f"PULL_ERROR dump not found: {path}", file=sys.stderr)
        print("NEW=0")
        print("NEW_IDS=")
        return 1
    proc = subprocess.run(
        [sys.executable, UPDATE_PY, "--from-json", path],
        cwd=ROOT,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
