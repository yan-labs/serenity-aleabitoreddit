"""Golden tests for update.normalize_x_api_post.

tests/fixtures/normalize_golden.json was recorded from the pre-refactor
implementation; any change to the archive row shape must be deliberate.
"""
import copy
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import update  # noqa: E402

with open(os.path.join(ROOT, "tests", "fixtures", "normalize_golden.json"), encoding="utf-8") as f:
    GOLDEN = json.load(f)


class NormalizeGoldenTests(unittest.TestCase):
    def test_matches_recorded_output(self):
        for name, case in GOLDEN.items():
            with self.subTest(case=name):
                got = update.normalize_x_api_post(copy.deepcopy(case["input"]), case["includes"])
                self.assertEqual(got, case["expected"])
                # Key order is what json.dump writes into the archive.
                self.assertEqual(list(got), list(case["expected"]))

    def test_note_tweet_keeps_leading_mentions(self):
        got = update.normalize_x_api_post(GOLDEN["x_api_full"]["input"], GOLDEN["x_api_full"]["includes"])
        self.assertEqual(got["text"], "@a @b full long body $NBIS")


if __name__ == "__main__":
    unittest.main()
