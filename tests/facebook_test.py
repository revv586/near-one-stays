import copy, json, pathlib, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from facebook_import import merge_facebook, is_automatic_source, ROOT

class FacebookImportTests(unittest.TestCase):
    def test_curated_import_is_idempotent_and_preserves_existing_facts(self):
        original = {'id': 'existing', 'offers': [{'months': 3, 'price': 6500}], 'lastFetchedAt': 'newer'}
        data = {'properties': [copy.deepcopy(original)]}
        feed = json.loads((ROOT / 'dist/data/facebook-posts.json').read_text())
        expected_ids = {p['id'] for p in feed['properties']}
        self.assertGreater(len(expected_ids), 0)
        self.assertEqual(merge_facebook(data), len(expected_ids))
        self.assertEqual(merge_facebook(data), 0)
        self.assertEqual(len(data['properties']), len(expected_ids) + 1)
        self.assertEqual({p['id'] for p in data['properties']}, expected_ids | {'existing'})
        self.assertEqual(data['properties'][0], original)

    def test_private_group_rejected_before_any_record_is_written(self):
        feed = json.loads((ROOT / 'dist/data/facebook-posts.json').read_text())
        feed['groups'][0]['visibility'] = 'private'
        data = {'properties': []}
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'feed.json'
            path.write_text(json.dumps(feed))
            with self.assertRaises(ValueError): merge_facebook(data, path)
        self.assertEqual(data['properties'], [])

    def test_facebook_is_never_sent_to_unattended_http_checker(self):
        self.assertFalse(is_automatic_source({'sourceUrl': 'https://www.facebook.com/groups/1/posts/2/'}))
        self.assertFalse(is_automatic_source({'url': 'https://m.facebook.com/groups/1/'}))
        self.assertTrue(is_automatic_source({'sourceUrl': 'https://www.renthub.in.th/room'}))

    def test_annual_price_and_unverified_route_are_not_promoted(self):
        data = {'properties': []}; merge_facebook(data)
        by_id = {p['id']: p for p in data['properties']}
        annual = by_id['fb-supalai-premier-samyan']
        self.assertEqual(annual['offers'], [])
        self.assertEqual(annual['category'], 'excluded')
        self.assertEqual(by_id['fb-nest-sukhumvit-22']['availableFrom'], '2027-09-22')
        self.assertTrue(all(p['walkingVerified'] is False and p['posterUpdated'] is None for p in data['properties']))
