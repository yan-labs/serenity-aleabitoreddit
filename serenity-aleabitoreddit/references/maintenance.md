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
6. **Avoid broad rewrites.** Make focused edits grounded in the latest posts.
   Split or reorganize only when repeated maintenance pain shows the current
   reference is too crowded or ambiguous.

## Update Checklist

Before committing:

1. Fetch latest posts with `xreach` and dedupe by tweet id.
2. Refresh JSON, CSV, and ticker stats.
3. Classify each new post:
   - `data-only`
   - `track-record`
   - `ticker thesis`
   - `methodology`
   - `entry-point workflow`
   - `skip skill update`
4. Make the smallest reference edit that captures the durable change.
5. Verify counts in `README.md` and `SKILL.md`.
6. Commit only when there is new data or a meaningful skill improvement.

## Commit Guidance

- Use `data: incremental tweet update (+<n>) <UTC ISO timestamp>` for data-only
  changes.
- Use `skill/data: incremental tweet update (+<n>) <UTC ISO timestamp>` when the
  skill or references also change.
- Do not create empty commits.
