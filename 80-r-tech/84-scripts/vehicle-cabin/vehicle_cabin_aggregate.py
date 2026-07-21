"""
차량 실내 공조/냄새/공기질 — Gate3 집계 + 교차분석 + 대표후기 추출
analysis-results.json → Gate3 필터 → 브랜드×토픽×감성 교차 → 토픽별 대표후기 → aggregate.json
"""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

DATA = Path(__file__).parent.parent.parent.parent / '10-projects' / '37-hyundai-rxr-cabin-air' / 'data' / '2026-07-17'
results = json.loads((DATA / 'analysis-results.json').read_text(encoding='utf-8'))

# Gate 3: 광고성 전량 제외(C/D/E/F/G) + Auth 60+
gate3 = [r for r in results
         if r.get('content_class') in ('A', 'B')
         and r.get('authenticity', 0) >= 60]
print(f"Gate3 대상: {len(gate3)}건")

TOPICS = ['냄새_새차증후군','냄새_곰팡이_에어컨','냄새_외부유입_흡연',
          '공조_냉난방성능','공조_풍량_풍향','공조_온도제어_편차','공조_성에_김서림',
          '공기질_미세먼지_필터','공기질_환기_내외기','공기질_건강_민감']
SENTS = ['긍정','혼합','중립','부정']
BRANDS = ['현대','기아','제네시스','테슬라','BMW','벤츠','아우디','볼보','폭스바겐','쉐보레','르노','KGM']

# 토픽 × 감성
topic_sent = defaultdict(lambda: Counter())
for r in gate3:
    topic_sent[r.get('primary_topic','기타')][r.get('sentiment','중립')] += 1

# 브랜드 × 토픽 (미상 제외)
brand_topic = defaultdict(lambda: Counter())
brand_sent = defaultdict(lambda: Counter())
for r in gate3:
    b = r.get('brand','미상')
    if b == '미상':
        continue
    brand_topic[b][r.get('primary_topic','기타')] += 1
    brand_sent[b][r.get('sentiment','중립')] += 1

# 3대 축 롤업
AXIS_MAP = {
    '냄새': ['냄새_새차증후군','냄새_곰팡이_에어컨','냄새_외부유입_흡연'],
    '공조': ['공조_냉난방성능','공조_풍량_풍향','공조_온도제어_편차','공조_성에_김서림'],
    '공기질': ['공기질_미세먼지_필터','공기질_환기_내외기','공기질_건강_민감'],
}
axis_sent = defaultdict(lambda: Counter())
for r in gate3:
    t = r.get('primary_topic','기타')
    for axis, subs in AXIS_MAP.items():
        if t in subs:
            axis_sent[axis][r.get('sentiment','중립')] += 1

# 토픽별 대표 후기 (부정+혼합 우선, Auth·RQL 높은 순, 본문 발췌)
def excerpt(r, kw_topic):
    txt = re.sub(r'\s+',' ', r.get('full_content','') or '').strip()
    # 토픽 키워드 주변 발췌 시도
    return txt[:220]

reps = {}
for topic in TOPICS:
    cands = [r for r in gate3 if r.get('primary_topic')==topic
             and r.get('sentiment') in ('부정','혼합')
             and len(r.get('full_content','') or '') > 200]
    cands.sort(key=lambda r: (r.get('authenticity',0), r.get('rql_weight',0), r.get('word_count',0)), reverse=True)
    reps[topic] = [{
        'title': r['title'], 'brand': r.get('brand','미상'),
        'sentiment': r.get('sentiment'), 'auth': r.get('authenticity'),
        'rql': r.get('rql'), 'date': r.get('date'), 'link': r.get('link'),
        'excerpt': excerpt(r, topic),
    } for r in cands[:6]]

out = {
    'gate3_count': len(gate3),
    'topic_sentiment': {t: dict(topic_sent[t]) for t in topic_sent},
    'axis_sentiment': {a: dict(axis_sent[a]) for a in axis_sent},
    'brand_topic': {b: dict(brand_topic[b]) for b in BRANDS if b in brand_topic},
    'brand_sentiment': {b: dict(brand_sent[b]) for b in BRANDS if b in brand_sent},
    'representative_quotes': reps,
}
(DATA / 'aggregate.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')

# 콘솔 요약
print("\n=== 3대 축 × 감성 (Gate3) ===")
for a in ['냄새','공조','공기질']:
    d = axis_sent[a]; tot=sum(d.values())
    print(f"  {a} (n={tot}): 부정 {d['부정']}({d['부정']/max(tot,1)*100:.0f}%) 혼합 {d['혼합']}({d['혼합']/max(tot,1)*100:.0f}%) 긍정 {d['긍정']}({d['긍정']/max(tot,1)*100:.0f}%)")

print("\n=== 토픽 × 감성 (Gate3, 부정률 순) ===")
rows=[]
for t in TOPICS:
    d=topic_sent[t]; tot=sum(d.values())
    if tot==0: continue
    negrate=d['부정']/tot*100
    rows.append((negrate,t,tot,d))
for negrate,t,tot,d in sorted(rows, reverse=True):
    print(f"  {t} (n={tot}): 부정 {negrate:.0f}% / 혼합 {d['혼합']/tot*100:.0f}% / 긍정 {d['긍정']/tot*100:.0f}%")

print("\n=== 브랜드 × 감성 (Gate3, 상위 8) ===")
for b in sorted(brand_sent, key=lambda x: -sum(brand_sent[x].values()))[:8]:
    d=brand_sent[b]; tot=sum(d.values())
    print(f"  {b} (n={tot}): 부정 {d['부정']/tot*100:.0f}% / 혼합 {d['혼합']/tot*100:.0f}% / 긍정 {d['긍정']/tot*100:.0f}%")

print(f"\n저장: {DATA/'aggregate.json'}")
