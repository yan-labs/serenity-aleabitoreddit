# Unattended updates: Grok Bot (not CI)

Archive refresh is owned by **Grok Bot**, not GitHub Actions:

1. Routine (morning / evening Asia/Shanghai) wakes the bot.
2. Pull @aleabitoreddit via the X connector / API since `data/sync_state.json`
   `last_tweet_id`.
3. `python3 update.py --from-json <dump.json>`
4. Distill per `serenity-aleabitoreddit/references/maintenance.md`.
5. `python3 check_repo.py`, then commit and push when there is something new.

Do **not** add `.github/workflows/` here unless you intentionally want CI and
have a token with the `workflow` scope. Older Codex heartbeat CI skeletons are
retired; public-profile / Jina remain an optional offline fallback inside
`update.py` only.
