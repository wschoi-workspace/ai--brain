# -*- coding: utf-8 -*-
"""불교 brand-analysis — 네이버 블로그 멘션 크롤러 (3군 비교)"""
import os, json, re, time, urllib.request, urllib.parse

ENV = '/Users/choi_ai/do-better-workspace/.env'
OUT = '/Users/choi_ai/do-better-workspace/10-projects/30-buddhism-brand-analysis/data/naver-raw.json'

def load_env(p):
    e = {}
    for line in open(p, encoding='utf-8'):
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1); e[k.strip()] = v.strip().strip('"').strip("'")
    return e

env = load_env(ENV)
CID = env.get('NAVER_CLIENT_ID'); CSEC = env.get('NAVER_CLIENT_SECRET')
assert CID and CSEC, "네이버 키 없음"

def strip_tags(s):
    s = re.sub(r'<[^>]+>', '', s or '')
    return (s.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
             .replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')).strip()

def search(query, start=1, display=100, sort='date'):
    url = 'https://openapi.naver.com/v1/search/blog.json?' + urllib.parse.urlencode(
        {'query': query, 'display': display, 'start': start, 'sort': sort})
    req = urllib.request.Request(url, headers={'X-Naver-Client-Id': CID, 'X-Naver-Client-Secret': CSEC})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)

GROUPS = {
    '불교': ['템플스테이 후기', '사찰 명상', '힙불교', '불교 MZ', '사찰음식', '봉은사'],
    '기독교': ['교회 청년', '기독교 신앙', '성당 미사', '천주교 영성'],
    '명상웰니스': ['명상 앱', '마음챙김', '번아웃 힐링', '마인드풀니스', '명상 후기'],
}

out = {}
for g, queries in GROUPS.items():
    items, seen = [], set()
    for q in queries:
        for start in (1, 101):  # 200건/키워드
            try:
                r = search(q, start=start)
                for it in r.get('items', []):
                    link = it.get('link', '')
                    if link in seen: continue
                    seen.add(link)
                    items.append({
                        'group': g, 'query': q,
                        'title': strip_tags(it.get('title', '')),
                        'desc': strip_tags(it.get('description', '')),
                        'date': it.get('postdate', ''),
                        'blogger': it.get('bloggername', ''),
                        'link': link,
                    })
                time.sleep(0.25)
            except Exception as e:
                print('  err', q, start, e); time.sleep(1.0)
    out[g] = items
    print(f'{g}: {len(items)}건')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('총:', sum(len(v) for v in out.values()), '→', OUT)
