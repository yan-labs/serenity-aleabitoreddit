# Grok Bot — Serenity sync (minimal)

Repo: `yan-labs/serenity-aleabitoreddit`. Target: `@aleabitoreddit`
(`1940360837547565056`). Asia/Shanghai morning + evening routine.

## Steps

1. **Cursor** — read `data/sync_state.json` → `last_tweet_id` / `last_update_time`.
2. **Fetch** — X connector `get_users_posts` (paginate since cursor; prefer
   `note_tweet.text`). Write dump to e.g. `/tmp/new_posts.json`
   (X API `{data, includes}` or archive-shaped list).
3. **Merge** (script only — no agent judgment):
   ```sh
   python3 scripts/ingest_x_posts.py /tmp/new_posts.json
   # equivalent: python3 update.py --from-json /tmp/new_posts.json
   ```
   Expect `NEW=<n>` and `NEW_IDS=id1,id2,...`. Refreshes JSON/CSV/ticker_stats
   and advances `sync_state.json`.
4. **Distill** — **only if `NEW>0`**, and only durable signals:
   per `serenity-aleabitoreddit/references/maintenance.md`
   (smallest edits to `theses.md` / `track-record.md` / period `analysis/`;
   skip jokes, health, one-off replies). Bump tweet counts in README + SKILL.
5. **Check + push**
   ```sh
   python3 check_repo.py
   git add -A && git commit -m "data: incremental tweet update (+N) <UTC ISO>"
   # or skill/data: ... when references change
   git push origin main
   ```
6. **Report** — if `NEW=0` and no distill: stay quiet on routine runs.
   Else: NEW count + short Chinese insight bullets + commit SHA.

## Fallback

`python3 update.py` with no `--from-json` uses public x.com profile / Jina
(short window only). Not the supported unattended path.

## Agent still owns

Distill judgment (what is durable vs skip), article summaries without pasting
full article text, commit message choice, and the user-facing insight summary.
