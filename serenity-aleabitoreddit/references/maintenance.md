# Skill Maintenance Playbook

Use this when updating the archive-derived skill from new @aleabitoreddit posts.
The goal is to keep the skill current without turning it into a noisy transcript.

## Maintenance Standard

1. **Reuse before creating.** Check existing `SKILL.md`, `references/*.md`, and
   `analysis/*.md` before adding new structure. Extend the closest existing
   section unless a repeated pattern clearly needs a new reference.
2. **Require durable evidence.** Promote a new post into the skill only when it
   adds at least one durable item:
   - a repeated workflow or decision rule;
   - a changed stance, new catalyst, or explicit invalidation;
   - a supply-chain link, bottleneck, customer, foundry, contract, or timing
     marker;
   - a track-record update that changes calibration;
   - terminology or framing likely to recur in future user questions.
3. **Choose the smallest useful change.**
   - Update `data/` for every new tweet.
   - Update `track-record.md` for dated calls, validations, reversals, and
     calibration events.
   - Update `theses.md` for ticker-specific stance, evidence, risk, and latest
     view changes.
   - Update `methodology.md` only for reusable principles, checklists, and
     anti-patterns.
   - Update `SKILL.md` only for entry-point routing, workflows, or risk framing
     that users need immediately.
4. **Skip weak packaging.** Do not add a skill note when a post is only a joke,
   short reaction, duplicate victory lap, one-off reply, or low-evidence opinion
   unless it materially changes a thesis or method.
5. **Keep provenance compact.** Mention the date and the concrete signal, not a
   long quote. Preserve full text in `data/aleabitoreddit_tweets.json`.
   For X Articles, do not commit the full article text. Store only metadata,
   short summaries, durable thesis deltas, and portfolio-use rules in
   `references/articles.md`.
6. **Avoid broad rewrites.** Make focused edits grounded in the latest posts.
   Split or reorganize only when repeated maintenance pain shows the current
   reference is too crowded or ambiguous.

## Update Checklist

Before committing:

1. **Primary path (Grok Bot):** pull posts with the X connector / API, write a
   JSON dump, then merge:
   `python3 update.py --from-json path/to/posts.json` (archive-shaped list, or
   `{ "data": [...], "includes": {...} }` from `get_users_posts` /
   `get_posts_by_ids`; prefer `note_tweet.text` over truncated `text`).
   **Optional legacy only:** `python3 update.py` without `--from-json` still
   tries `xreach`, then the public `https://x.com/aleabitoreddit` profile
   (status ids / text / `created_at_ms`) and Jina status pages for unparsed
   rows. Do not use that live pull for unattended refresh; record the source
   in the run report if you do. The profile parser follows the status-specific
   RSC `Tweet` object and its `user_results` reference, and prefers linked
   `NoteTweet` text — never the first `full_text` in a shared response window.
2. Refresh JSON, CSV, and ticker stats.
3. Fetch any newly visible X Article share tweets or article bodies with
   authenticated access. Keep full article text out of the repo; summarize only
   durable thesis deltas.
4. Classify each new post:
   - `data-only`
   - `track-record`
   - `ticker thesis`
   - `methodology`
   - `entry-point workflow`
   - `article summary`
   - `skip skill update`
5. Make the smallest reference edit that captures the durable change.
6. Verify counts in `README.md` and `SKILL.md`.
7. Run `python3 check_repo.py` to catch archive/reference consistency issues.
8. Commit only when there is new data or a meaningful skill improvement.

## Commit Guidance

- Use `data: incremental tweet update (+<n>) <UTC ISO timestamp>` for data-only
  changes.
- Use `skill/data: incremental tweet update (+<n>) <UTC ISO timestamp>` when the
  skill or references also change.
- Do not create empty commits.

## Unattended updates

Supported path is **Grok Bot only** (no GitHub Actions / Codex heartbeat):

1. Routine wakes (e.g. morning and evening Asia/Shanghai).
2. Pull @aleabitoreddit via the X connector / API since `data/sync_state.json`
   `last_tweet_id`.
3. `python3 update.py --from-json <dump.json>` → refresh JSON/CSV/ticker stats.
4. Distill durable signals per this playbook (`theses.md`, `track-record.md`,
   period `analysis/` when needed).
5. `python3 check_repo.py`, then commit and push when there is new data or a
   meaningful skill improvement.

See `scripts/github-workflows/README.md` for why CI is not the supported path.
xreach / public-profile / Jina remain optional manual fallbacks only.
