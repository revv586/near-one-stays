"""Merge reviewed public Facebook posts, without using a signed-in session in CI."""
import copy, hashlib, json, pathlib, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]

def merge_facebook(data, path=None):
    path = path or ROOT / 'dist/data/facebook-posts.json'
    if not path.exists():
        return 0
    feed = json.loads(path.read_text())
    groups = {g['id']: g for g in feed['groups']}
    seen = set()
    for p in feed['properties']:
        u = urllib.parse.urlsplit(p['sourceUrl'])
        group = groups.get(p['facebookGroupId'])
        expected = f"/groups/{p['facebookGroupId']}/posts/"
        if not group or group.get('visibility') != 'public' or u.scheme != 'https' or u.hostname != 'www.facebook.com' or not u.path.startswith(expected) or u.query:
            raise ValueError('Only reviewed public group posts with canonical links may be imported')
        if p['id'] in seen or p.get('sourceMode') != 'manual' or p.get('ownerConfirmed') is not False:
            raise ValueError('Duplicate post or unsupported source mode')
        seen.add(p['id'])
    count = 0
    by_id = {p['id']: p for p in data['properties']}
    for p in feed['properties']:
        revision = hashlib.sha256(json.dumps(p, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        old = by_id.get(p['id'])
        if old and old.get('curationRevision') == revision:
            continue
        item = copy.deepcopy(p)
        item['curationRevision'] = revision
        if old:
            data['properties'][data['properties'].index(old)] = item
        else:
            data['properties'].append(item)
        count += 1
    data['facebookResearch'] = {k: v for k, v in feed.items() if k != 'properties'}
    return count

def is_automatic_source(p):
    host = (urllib.parse.urlsplit(p.get('sourceUrl', p.get('url', ''))).hostname or '').lower()
    return p.get('sourceMode') != 'manual' and host not in {'facebook.com', 'www.facebook.com', 'm.facebook.com'}
