"""가나 데이터를 컴온스타일 포맷(flat records)으로 변환"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

IN = '30-knowledge/gana-chocolate-house/gana-2layer-results.json'
OUT_DIR = '80-r-tech/85-analysis-results/gana-chocolate-house'
os.makedirs(OUT_DIR, exist_ok=True)

with open(IN, 'r', encoding='utf-8') as f:
    src = json.load(f)

posts = src['posts']

SENT_MAP = {'positive':'긍정','negative':'부정','mixed':'혼합','neutral':'중립'}
PERIOD_MAP = {'pre':'사전','event':'팝업기간','post':'팝업후'}
RQL_MAP = {'Q5':'Q5_서사형','Q4':'Q4_분석형','Q3':'Q3_경험형','Q2':'Q2_감상형','Q1':'Q1_간단형'}

flat = []
for p in posts:
    ps = p.get('psyche',{})
    sc = p.get('sincerity',{})
    date_str = p.get('_date','').replace('-','')
    flat.append({
        'date': date_str,
        'period': PERIOD_MAP.get(p.get('_period',''), ''),
        'title': p.get('title',''),
        'blogger': p.get('bloggername',''),
        'link': p.get('link',''),
        'primary_topic': p.get('topic','기타'),
        'topic_scores': p.get('topic_dist',{}),
        'sentiment': SENT_MAP.get(p.get('sentiment','neutral'), '중립'),
        'pos_count': p.get('pos_n',0),
        'neg_count': p.get('neg_n',0),
        'is_sponsored': sc.get('content_class') == 'C' or sc.get('_sponsored', False),
        'rql': RQL_MAP.get(p.get('rql','Q1'), 'Q1_간단형'),
        'word_count': len(p.get('_content','') or ''),
        'has_detail': sc.get('_detail', 0),
        'has_personal': sc.get('_personal', 0),
        'first_person': ps.get('first_person',0),
        'we_person': ps.get('plural',0),
        'place_ref': ps.get('place',0),
        'iga_count': 0,
        'eunneun_count': 0,
        'freshness_index': ps.get('freshness', 50),
        'authenticity': ps.get('authenticity', 60),
        'clout': ps.get('clout', 40),
        'extreme_pos': ps.get('over_positive',0),
        'exclamation': ps.get('exclamation',0),
        'sincerity_class': sc.get('content_class','B'),
        'trust_score': sc.get('trust_score',100),
        'sincerity_flags': sc.get('flags',[]),
    })

out_path = os.path.join(OUT_DIR, 'gana-chocolate-house-2layer-results.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(flat, f, ensure_ascii=False, indent=2)
print(f"변환 완료: {len(flat)}건 → {out_path}")

# 원본 raw/filtered/with-content 복사
import shutil
for name in ['gana-naver-raw.json','gana-naver-filtered.json','gana-naver-with-content.json']:
    src_path = f'30-knowledge/gana-chocolate-house/{name}'
    if os.path.exists(src_path):
        shutil.copy(src_path, os.path.join(OUT_DIR, name.replace('gana-','gana-chocolate-house-')))
        print(f"복사: {name}")
