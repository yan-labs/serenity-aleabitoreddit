"""Regression tests for update.py merge / sync-state behaviour."""
import contextlib
import copy
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import update  # noqa: E402


def row(tid, iso, text="hello $NBIS"):
    return {
        "id": tid,
        "text": text,
        "author": {"screenName": "aleabitoreddit"},
        "metrics": {},
        "createdAtISO": iso,
        "createdAtLocal": "x",
    }


class UpdateTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = self.tmp.name
        self.arch = os.path.join(d, "aleabitoreddit_tweets.json")
        self.state = os.path.join(d, "sync_state.json")
        with open(self.arch, "w") as f:
            json.dump([row("1", "2026-10-01T00:00:00Z")], f)
        with open(self.state, "w") as f:
            json.dump({"last_tweet_id": "1", "source_health": {"status": "ok"}}, f)
        self.patches = [
            mock.patch.object(update, "DATA", d),
            mock.patch.object(update, "ARCH", self.arch),
            mock.patch.object(update, "SYNC_STATE", self.state),
            mock.patch.object(update, "PUBLIC_FALLBACK_DIAGNOSTIC", None),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def run_main(self, *argv):
        out = io.StringIO()
        code = 0
        with mock.patch.object(sys, "argv", ["update.py", *argv]), contextlib.redirect_stdout(out):
            try:
                update.main()
            except SystemExit as exc:
                code = exc.code or 0
        return code, out.getvalue()

    def dump(self, obj):
        path = os.path.join(self.tmp.name, "dump.json")
        with open(path, "w") as f:
            json.dump(obj, f)
        return path

    def state_health(self):
        with open(self.state) as f:
            return json.load(f)["source_health"]

    def test_merges_new_rows_and_advances_cursor(self):
        code, out = self.run_main("--from-json", self.dump([row("2", "2026-10-02T00:00:00Z")]))
        self.assertEqual(code, 0)
        self.assertIn("NEW=1", out)
        self.assertIn("NEW_IDS=2", out)
        with open(self.state) as f:
            self.assertEqual(json.load(f)["last_tweet_id"], "2")

    def test_unrecognised_dump_fails_without_stamping_health(self):
        before = self.state_health()
        code, out = self.run_main("--from-json", self.dump({"foo": 1}))
        self.assertEqual(code, 1)
        self.assertIn("PULL_ERROR", out)
        self.assertIn("NEW=0", out)
        self.assertEqual(self.state_health(), before)

    def test_empty_x_api_page_is_a_healthy_empty_check(self):
        code, out = self.run_main("--from-json", self.dump({"meta": {"result_count": 0}}))
        self.assertEqual(code, 0)
        self.assertEqual(self.state_health()["status"], "ok")

    def test_failed_public_pull_is_reported_stale(self):
        boom = mock.Mock(side_effect=RuntimeError("network down"))
        with mock.patch.object(update, "fetch_public_posts", boom):
            code, out = self.run_main()
        self.assertEqual(code, 0)
        health = self.state_health()
        self.assertEqual(health["status"], "error")
        self.assertEqual(health["freshness"], "stale")
        self.assertIn("network down", health["errors"][0])
        with open(self.state) as f:
            self.assertEqual(json.load(f)["last_tweet_id"], "1")

    def test_missing_timestamps_are_backfilled_and_saved(self):
        with open(self.arch, "w") as f:
            json.dump([{"id": "1", "text": "x", "author": {"screenName": "aleabitoreddit"},
                        "createdAt": "Mon Oct 19 10:34:45 +0000 2026"}], f)
        self.run_main("--from-json", self.dump([]))
        with open(self.arch) as f:
            saved = json.load(f)[0]
        self.assertEqual(saved["createdAtISO"], "2026-10-19T10:34:45Z")
        self.assertIn("createdAtLocal", saved)

    def test_noop_run_does_not_rewrite_archive(self):
        before = open(self.arch).read()
        self.run_main("--from-json", self.dump([row("1", "2026-10-01T00:00:00Z")]))
        self.assertEqual(open(self.arch).read(), before)

    def test_ticker_stats_tie_break_is_deterministic(self):
        rows = [row("1", "2026-10-01T00:00:00Z", "$BBB $AAA"), row("2", "2026-10-02T00:00:00Z", "$AAA $BBB")]
        update.write_ticker_stats(rows)
        first = open(os.path.join(self.tmp.name, "ticker_stats.txt")).read()
        update.write_ticker_stats(list(reversed(copy.deepcopy(rows))))
        second = open(os.path.join(self.tmp.name, "ticker_stats.txt")).read()
        self.assertEqual(first, second)
        self.assertLess(first.index("AAA"), first.index("BBB"))


class LocalTzTests(unittest.TestCase):
    def test_default_is_utc_plus_8(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SERENITY_LOCAL_UTC_OFFSET", None)
            self.assertEqual(update._local_tz().utcoffset(None).total_seconds(), 8 * 3600)

    def test_override_and_validation(self):
        with mock.patch.dict(os.environ, {"SERENITY_LOCAL_UTC_OFFSET": "-5.5"}):
            self.assertEqual(update._local_tz().utcoffset(None).total_seconds(), -5.5 * 3600)
        for bad in ("abc", "20"):
            with mock.patch.dict(os.environ, {"SERENITY_LOCAL_UTC_OFFSET": bad}):
                with self.assertRaises(SystemExit):
                    update._local_tz()


if __name__ == "__main__":
    unittest.main()
