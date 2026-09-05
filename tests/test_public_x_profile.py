import unittest

from scripts.public_x_profile import extract_profile_status_ids, parse_status_page


class PublicXProfileTests(unittest.TestCase):
    def test_extracts_only_target_profile_statuses_in_page_order(self):
        html = '''
        <div data-href="/aleabitoreddit/status/222"></div>
        <div data-href="/other/status/999"></div>
        entry_id:"tweet-222"
        <div data-href="/aleabitoreddit/status/111"></div>
        '''
        self.assertEqual(
            extract_profile_status_ids(html, "aleabitoreddit"), ["222", "111"]
        )

    def test_parses_standard_jina_status_page(self):
        page = '''
Title: Serenity (@aleabitoreddit) on X
URL Source: http://x.com/aleabitoreddit/status/222
Published Time: 2026-09-05T01:02:03.000Z
Markdown Content:
## Post
# Serenity on X: "New $NVDA supply note"
*   [@aleabitoreddit](http://x.com/aleabitoreddit) New $NVDA supply note
'''
        post = parse_status_page(page, "aleabitoreddit", "1940360837547565056", "Serenity", "222")
        self.assertEqual(post["id"], "222")
        self.assertEqual(post["createdAtISO"], "2026-09-05T01:02:03Z")
        self.assertEqual(post["text"], "New $NVDA supply note")

    def test_parses_long_page_without_title_heading(self):
        page = '''
URL Source: http://x.com/aleabitoreddit/status/333
Published Time: 2026-09-05T02:03:04.000Z
Markdown Content:
Long supply-chain note with [a link](https://example.com).
'''
        post = parse_status_page(page, "aleabitoreddit", "1940360837547565056", "Serenity", "333")
        self.assertIn("Long supply-chain note with a link.", post["text"])

    def test_extracts_visible_text_from_login_wrapped_page(self):
        page = '''
URL Source: http://x.com/aleabitoreddit/status/444
Published Time: 2026-09-05T03:04:05.000Z
Markdown Content:
[](http://x.com/)
## Post
[Log in](https://x.com/i/jf/onboarding/web)
*   [![Image 1](https://pbs.twimg.com/profile_images/avatar.jpg)](http://x.com/aleabitoreddit) [Serenity](http://x.com/aleabitoreddit) [@aleabitoreddit](http://x.com/aleabitoreddit)   Visible public excerpt…
'''
        post = parse_status_page(page, "aleabitoreddit", "1940360837547565056", "Serenity", "444")
        self.assertEqual(post["text"], "Visible public excerpt…")


if __name__ == "__main__":
    unittest.main()
