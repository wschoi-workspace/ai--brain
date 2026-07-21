"""
차량 실내 공조/냄새/공기질 — 심화 지표 (Gate 퍼널 감성변화 · 심리게이지 · 협찬대비 · RQL)
analysis-results.json → 각 Gate 단계별 감성/심리 지표 → deep.json
"""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
DATA = Path(__file__).parent.parent.parent.parent / '10-projects' / '37-hyundai-rxr-cabin-air' / 'data' / '2026-07-17'
results = json.loads((DATA / 'analysis-results.json').read_text(encoding='utf-8'))

# ---- 광고필터 로직 재사용 (adfilter와 동일 기준) ----
STRONG_AD = ['디테일링','출장세차','실내크리닝','특수크리닝','에바크리닝','에어컨 클리닝','에어컨클리닝',
    '썬팅','틴팅','ppf','랩핑','폴리싱','전문점','전문 업체','상담 문의','견적 문의',
    '인사드립니다','매장에 입고','입고되었','입고 되었','작업 입니다','작업입니다','시공 후기','시공했','시공 완료',
    '방문 예약','예약 문의','카톡 문의','전화 주세요','네이버 예약','플레이스',
    '제공받','협찬','원고료','체험단','소정의','지원받아','무상 제공','무상제공','대가를 받',
    '수수료를 지급','수수료를 제공','파트너스','쿠팡파트너스','쇼핑커넥트','일환으로 작성','일환으로 수수료',
    '공동구매','공구 진행','스마트스토어','초특가','재입고','최저가','할인 찬스','할인찬스','구매링크','구매 링크',
    '내돈내산 아니','업체로부터','제품을 제공',
    '디퓨저','방향제 추천','방향제추천','무향탈취제','탈취제 추천','탈취제추천',
    '석고 방향제','디퓨저 추천','카테리어','발향력','방향제 후기','제품을 소개','소개하고 싶었']
WEAK_AD = ['할인','고객님','차주분','의뢰','매장','샵','구매','판매','링크','정가','세일','포인트 적립','쿠폰','이벤트','증정']
VEHICLE_CONFIRM = ['자동차','차량','차 안','차안','차량용','신차','중고차','전기차','내 차','제 차','운전석','뒷좌석','트렁크',
    '에바','에바포레이터','공조기','시동','주행','엔진','에어컨 필터','에어컨필터','캐빈필터','디포그','오토에어컨',
    'ev3','ev6','ev9','아이오닉','캐스퍼','그랜저','쏘렌토','카니발','싼타페','투싼','코나','아반떼','쏘나타',
    '제네시스','gv70','gv80','테슬라','모델y','모델3','bmw','벤츠','아우디','볼보','폭스바겐','스포티지','셀토스']
NON_VEHICLE_NOISE = ['입주청소','이사청소','입주 청소','아파트','오피스텔','분양','부동산','리첸시아','파밀리에','전용면적','평형',
    '거실','침실','주방','싱크대','베란다','에어프라이어','제습기','반려동물','강아지','고양이','냥이','원룸',
    '신축','청약','세대수','발코니','입주민','집 냄새','집냄새','실내 인테리어','정부세종청사','국회']

def is_ad(post):
    text = (post.get('title','') + ' ' + (post.get('full_content','') or '')).lower()
    if any(m.lower() in text for m in STRONG_AD): return True
    if not any(v.lower() in text for v in VEHICLE_CONFIRM): return True
    if len([n for n in NON_VEHICLE_NOISE if n.lower() in text]) >= 2: return True
    if len([m for m in WEAK_AD if m.lower() in text]) >= 2: return True
    return False

def sent_pct(posts):
    c = Counter(p.get('sentiment','중립') for p in posts)
    tot = max(len(posts),1)
    return {s: round(c.get(s,0)/tot*100,1) for s in ['긍정','혼합','중립','부정']}, len(posts)

# ---- Gate 단계 정의 ----
valid = [r for r in results if r.get('content_class') in ('A','B','C')]  # 2-Layer 분석된 것
g1 = valid                                                    # Gate1: 전체 유효 (G/D/E/F 이미 크롤 단계 분리)
g2 = [r for r in valid if r.get('content_class') != 'C']      # Gate2: 협찬 C 제외
g3 = [r for r in g2 if r.get('authenticity',0) >= 60]         # Gate3: + Auth60
g4 = [r for r in g3 if not is_ad(r)]                          # Gate4: + 광고·비차량 제외

print("=== Gate 퍼널 감성 변화 ===")
funnel = []
for name, g in [('Gate1 전체유효',g1),('Gate2 협찬제외',g2),('Gate3 진정성60+',g3),('Gate4 광고·비차량제외',g4)]:
    pct, n = sent_pct(g)
    funnel.append({'gate':name,'n':n,**pct})
    print(f"  {name} (n={n}): 긍정 {pct['긍정']}% / 혼합 {pct['혼합']}% / 부정 {pct['부정']}%")

# ---- 심리 게이지 (Gate4 clean 기준, 축별) ----
AXIS_MAP = {'냄새':['냄새_새차증후군','냄새_곰팡이_에어컨','냄새_외부유입_흡연'],
    '공조':['공조_냉난방성능','공조_풍량_풍향','공조_온도제어_편차','공조_성에_김서림'],
    '공기질':['공기질_미세먼지_필터','공기질_환기_내외기','공기질_건강_민감']}
def avg(g, key):
    v=[r.get(key,0) for r in g if isinstance(r.get(key),(int,float))]
    return round(sum(v)/max(len(v),1),1)

gauge = {'전체': {'auth':avg(g4,'authenticity'),'clout':avg(g4,'clout'),'freshness':avg(g4,'freshness_index'),'n':len(g4)}}
for axis, subs in AXIS_MAP.items():
    ga = [r for r in g4 if r.get('primary_topic') in subs]
    gauge[axis] = {'auth':avg(ga,'authenticity'),'clout':avg(ga,'clout'),'freshness':avg(ga,'freshness_index'),'n':len(ga)}
print("\n=== 심리 게이지 (Gate4) ===")
for k,v in gauge.items():
    print(f"  {k} (n={v['n']}): Auth {v['auth']} / Clout {v['clout']} / Freshness {v['freshness']}")

# ---- 협찬(C) vs 자발적(Gate4) Auth 대비 ----
sponsored = [r for r in valid if r.get('content_class')=='C']
spon = {'n':len(sponsored),'auth':avg(sponsored,'authenticity'),
        'sent':sent_pct(sponsored)[0]}
organic = {'n':len(g4),'auth':avg(g4,'authenticity'),'sent':sent_pct(g4)[0]}
print(f"\n=== 협찬 vs 자발적 ===")
print(f"  협찬(C) n={spon['n']} Auth {spon['auth']} 긍정 {spon['sent']['긍정']}%")
print(f"  자발적(Gate4) n={organic['n']} Auth {organic['auth']} 긍정 {organic['sent']['긍정']}%")

# ---- RQL 분포 (Gate4) ----
rql = Counter(r.get('rql','Q1_간단형') for r in g4)
asset = round(sum(r.get('rql_weight',0.2) for r in g4),1)
print(f"\n=== RQL (Gate4) === 자산값 {asset}")
for q in ['Q5_서사형','Q4_분석형','Q3_경험형','Q2_감상형','Q1_간단형']:
    print(f"  {q}: {rql.get(q,0)}")

out = {'funnel':funnel,'gauge':gauge,'sponsored':spon,'organic':organic,
       'rql':{q:rql.get(q,0) for q in ['Q5_서사형','Q4_분석형','Q3_경험형','Q2_감상형','Q1_간단형']},'rql_asset':asset}
(DATA/'deep.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(f"\n저장: {DATA/'deep.json'}")
