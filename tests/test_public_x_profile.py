import base64
import unittest

from scripts.public_x_profile import (
    extract_profile_status_ids,
    parse_profile_posts,
    parse_status_page,
)


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

    def test_parses_public_profile_rsc_post_without_jina(self):
        profile = r'''
        <div data-href="/aleabitoreddit/status/555"></div>
        "TweetResults:555" $R[1]={result:$R[2]={rest_id:"555",
        details:$R[3]={full_text:"New \'$NVDA\nline"},
        created_at_ms:1789149425000, media_url_https:"https://pbs.twimg.com/media/a.jpg"}}
        '''
        posts = parse_profile_posts(
            profile,
            "aleabitoreddit",
            "1940360837547565056",
            "Serenity",
        )
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["id"], "555")
        self.assertEqual(posts[0]["createdAtISO"], "2026-09-11T17:57:05Z")
        self.assertEqual(posts[0]["text"], "New '$NVDA\nline")
        self.assertEqual(posts[0]["media"][0]["url"], "https://pbs.twimg.com/media/a.jpg")

    def test_binds_target_tweet_instead_of_adjacent_quoted_tweet(self):
        user_id = "1940360837547565056"
        target_id = "666"
        quoted_id = "777"
        target_token = base64.b64encode(f"Tweet:{target_id}".encode()).decode()
        quoted_token = base64.b64encode(f"Tweet:{quoted_id}".encode()).decode()
        user_ref = base64.b64encode(f"UserResults:{user_id}".encode()).decode()

        def rsc(key, number, body):
            return f'"{key}":$R[{number}]={{{body}}},'

        profile = (
            f'<a href="/aleabitoreddit/status/{target_id}"></a>'
            + rsc(
                f"TweetResults:{target_id}",
                1,
                f'result:$R[2]={{__ref:"{target_token}"}}',
            )
            + rsc(
                target_token,
                3,
                f'__typename:"Tweet",rest_id:"{target_id}",'
                f'core:$R[4]={{__ref:"client:{target_token}:core"}},'
                f'legacy:$R[5]={{__ref:"client:{target_token}:legacy"}},'
                f'details:$R[6]={{__ref:"client:{target_token}:details"}},'
                f'counts:$R[7]={{__ref:"client:{target_token}:counts"}},'
                f'views:$R[8]={{__ref:"client:{target_token}:views"}},'
                f'quoted_tweet_results:$R[9]={{__ref:"TweetResults:{quoted_id}"}},'
                'reply_to_results:null,note_tweet:null',
            )
            + rsc(
                f"client:{target_token}:core",
                10,
                f'__typename:"TweetCore",user_results:$R[11]={{__ref:"{user_ref}"}}',
            )
            + rsc(f"client:{target_token}:legacy", 12, '__typename:"LegacyTweet",lang:"en",retweeted_status_results:null')
            + rsc(f"client:{target_token}:details", 13, 'full_text:"Target-authored text",created_at_ms:1789305790000')
            + rsc(f"client:{target_token}:counts", 14, 'favorite_count:4,retweet_count:1,reply_count:2,quote_count:0,bookmark_count:3')
            + rsc(f"client:{target_token}:views", 15, 'count:"99"')
            + rsc(
                f"TweetResults:{quoted_id}",
                16,
                f'result:$R[17]={{__ref:"{quoted_token}"}}',
            )
            + rsc(
                quoted_token,
                18,
                f'rest_id:"{quoted_id}",details:$R[19]={{full_text:"WRONG QUOTED TEXT",created_at_ms:1789306606000}}',
            )
        )
        posts = parse_profile_posts(profile, "aleabitoreddit", user_id, "Serenity")
        self.assertEqual([post["id"] for post in posts], [target_id])
        self.assertEqual(posts[0]["text"], "Target-authored text")
        self.assertEqual(posts[0]["createdAtISO"], "2026-09-13T13:23:10Z")

    def test_prefers_full_note_tweet_text_over_truncated_details(self):
        user_id = "1940360837547565056"
        status_id = "888"
        token = base64.b64encode(f"Tweet:{status_id}".encode()).decode()
        user_ref = base64.b64encode(f"UserResults:{user_id}".encode()).decode()
        note_data_key = f"client:{token}:note_tweet"
        note_results_key = "NoteTweetResults:888"
        note_object_key = "NoteTweet:888"

        def rsc(key, number, body):
            return f'"{key}":$R[{number}]={{{body}}},'

        full_text = "Full NoteTweet text with $NVDA and $AVGO beyond the 280-char excerpt."
        profile = (
            f'<a href="/aleabitoreddit/status/{status_id}"></a>'
            + rsc(f"TweetResults:{status_id}", 1, f'result:$R[2]={{__ref:"{token}"}}')
            + rsc(
                token,
                3,
                f'__typename:"Tweet",rest_id:"{status_id}",'
                f'core:$R[4]={{__ref:"client:{token}:core"}},'
                f'details:$R[5]={{__ref:"client:{token}:details"}},'
                f'note_tweet:$R[6]={{__ref:"{note_data_key}"}},'
                'legacy:null,counts:null,views:null,quoted_tweet_results:null,reply_to_results:null',
            )
            + rsc(f"client:{token}:core", 7, f'user_results:$R[8]={{__ref:"{user_ref}"}}')
            + rsc(f"client:{token}:details", 9, 'full_text:"Truncated NoteTweet excerpt",created_at_ms:1789330276000')
            + rsc(note_data_key, 10, f'note_tweet_results:$R[11]={{__ref:"{note_results_key}"}}')
            + rsc(note_results_key, 12, f'result:$R[13]={{__ref:"{note_object_key}"}}')
            + rsc(note_object_key, 14, f'text:"{full_text}"')
        )
        posts = parse_profile_posts(profile, "aleabitoreddit", user_id, "Serenity")
        self.assertEqual(posts[0]["text"], full_text)

    def test_skips_profile_tweet_when_author_reference_does_not_match(self):
        requested_user_id = "1940360837547565056"
        status_id = "889"
        token = base64.b64encode(f"Tweet:{status_id}".encode()).decode()
        wrong_user_ref = base64.b64encode("UserResults:1227552975561863169".encode()).decode()

        def rsc(key, number, body):
            return f'"{key}":$R[{number}]={{{body}}},'

        profile = (
            f'<a href="/aleabitoreddit/status/{status_id}"></a>'
            + rsc(f"TweetResults:{status_id}", 1, f'result:$R[2]={{__ref:"{token}"}}')
            + rsc(token, 3, f'core:$R[4]={{__ref:"client:{token}:core"}},details:$R[5]={{__ref:"client:{token}:details"}}')
            + rsc(f"client:{token}:core", 6, f'user_results:$R[7]={{__ref:"{wrong_user_ref}"}}')
            + rsc(f"client:{token}:details", 8, 'full_text:"Wrong author",created_at_ms:1789305790000')
        )
        self.assertEqual(
            parse_profile_posts(profile, "aleabitoreddit", requested_user_id, "Serenity"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
