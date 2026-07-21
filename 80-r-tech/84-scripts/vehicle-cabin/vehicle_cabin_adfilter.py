"""
차량 실내 공조/냄새/공기질 — 광고·업체홍보 강화 필터 (Gate 4)
Gate3(협찬 C 제외 + Auth60+) 결과에서 blog-commerce/업체홍보성 글을 추가 제거.
크롤러 기본 sponsored_markers가 못 잡는: 디테일링/세차/썬팅 업체 홍보, 커머스(할인·재입고·파트너스) 글 제거.
재집계 + 대표후기 재추출 → aggregate_clean.json
"""
import json, re, sys
from pathlib import Path
from collections import Counter, defaultdict

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

DATA = Path(__file__).parent.parent.parent.parent / '10-projects' / '37-hyundai-rxr-cabin-air' / 'data' / '2026-07-17'
results = json.loads((DATA / 'analysis-results.json').read_text(encoding='utf-8'))

# 강한 광고 마커 (1개만 있어도 제외)
STRONG_AD = [
    # 업체/시공 홍보
    '디테일링','출장세차','실내크리닝','특수크리닝','에바크리닝','에어컨 클리닝','에어컨클리닝',
    '썬팅','틴팅','ppf','랩핑','폴리싱','전문점','전문 업체','상담 문의','견적 문의',
    '인사드립니다','매장에 입고','입고되었','입고 되었','작업 입니다','작업입니다','시공 후기','시공했','시공 완료',
    '방문 예약','예약 문의','카톡 문의','전화 주세요','네이버 예약','플레이스',
    # 협찬/커머스
    '제공받','협찬','원고료','체험단','소정의','지원받아','무상 제공','무상제공','대가를 받',
    '수수료를 지급','수수료를 제공','파트너스','쿠팡파트너스','쇼핑커넥트','일환으로 작성','일환으로 수수료',
    '공동구매','공구 진행','스마트스토어','초특가','재입고','최저가','할인 찬스','할인찬스','구매링크','구매 링크',
    '내돈내산 아니','업체로부터','제품을 제공',
]
# 커머스 제품 리뷰 마커 (방향제/디퓨저/탈취제 커머스)
STRONG_AD += ['디퓨저','방향제 추천','방향제추천','무향탈취제','탈취제 추천','탈취제추천',
              '석고 방향제','디퓨저 추천','카테리어','발향력','방향제 후기','제품을 소개','소개하고 싶었']

# 약한 광고 마커 (2개 이상 조합 시 제외)
WEAK_AD = ['할인','고객님','차주분','의뢰','매장','샵','구매','판매','링크','정가','세일','포인트 적립','쿠폰','이벤트','증정']

# 차량 확정 키워드 (하나도 없으면 비차량 글로 제외)
VEHICLE_CONFIRM = ['자동차','차량','차 안','차안','차량용','신차','중고차','전기차','내 차','제 차','운전석','뒷좌석','트렁크',
                   '에바','에바포레이터','공조기','시동','주행','엔진','에어컨 필터','에어컨필터','캐빈필터','디포그','오토에어컨',
                   'ev3','ev6','ev9','아이오닉','캐스퍼','그랜저','쏘렌토','카니발','싼타페','투싼','코나','아반떼','쏘나타',
                   '제네시스','gv70','gv80','테슬라','모델y','모델3','bmw','벤츠','아우디','볼보','폭스바겐','스포티지','셀토스']

# 비차량 노이즈 (집/부동산/일반 건강/반려동물) — 2개 이상이면 제외
NON_VEHICLE_NOISE = ['입주청소','이사청소','입주 청소','아파트','오피스텔','분양','부동산','리첸시아','파밀리에','전용면적','평형',
                     '거실','침실','주방','싱크대','베란다','에어프라이어','제습기','반려동물','강아지','고양이','냥이','원룸',
                     '신축','청약','세대수','발코니','입주민','집 냄새','집냄새','실내 인테리어','정부세종청사','국회']

def is_ad(post):
    text = (post.get('title','') + ' ' + (post.get('full_content','') or '')).lower()
    # 1) 강한 광고 마커
    for m in STRONG_AD:
        if m.lower() in text:
            return True, m
    # 2) 비차량 글: 차량 확정 키워드 전무
    if not any(v.lower() in text for v in VEHICLE_CONFIRM):
        return True, 'NON_VEHICLE(차량확정어없음)'
    # 3) 비차량 노이즈 다수
    noise_hits = [n for n in NON_VEHICLE_NOISE if n.lower() in text]
    if len(noise_hits) >= 2:
        return True, 'NON_VEHICLE(' + '+'.join(noise_hits[:2]) + ')'
    # 4) 약한 광고 마커 2개 이상
    weak_hits = [m for m in WEAK_AD if m.lower() in text]
    if len(weak_hits) >= 2:
        return True, '+'.join(weak_hits[:3])
    return False, None

# Gate3 (협찬 C 제외 + Auth60+)
gate3 = [r for r in results if r.get('content_class') in ('A','B') and r.get('authenticity',0) >= 60]
print(f"Gate3 (기존): {len(gate3)}건")

# Gate4: 광고 추가 제거
clean, removed = [], []
for r in gate3:
    ad, marker = is_ad(r)
    if ad:
        removed.append((marker, r))
    else:
        clean.append(r)
print(f"Gate4 광고 추가 제거: -{len(removed)}건 → {len(clean)}건")

# 제거 마커 분포 (상위)
rm_dist = Counter(m for m,_ in removed)
print("\n제거 마커 상위 15:")
for m,c in rm_dist.most_common(15):
    print(f"  {m}: {c}")

TOPICS = ['냄새_새차증후군','냄새_곰팡이_에어컨','냄새_외부유입_흡연',
          '공조_냉난방성능','공조_풍량_풍향','공조_온도제어_편차','공조_성에_김서림',
          '공기질_미세먼지_필터','공기질_환기_내외기','공기질_건강_민감']
BRANDS = ['현대','기아','제네시스','테슬라','BMW','벤츠','아우디','볼보','폭스바겐','쉐보레','르노','KGM']
AXIS_MAP = {
    '냄새':['냄새_새차증후군','냄새_곰팡이_에어컨','냄새_외부유입_흡연'],
    '공조':['공조_냉난방성능','공조_풍량_풍향','공조_온도제어_편차','공조_성에_김서림'],
    '공기질':['공기질_미세먼지_필터','공기질_환기_내외기','공기질_건강_민감'],
}

topic_sent = defaultdict(Counter); axis_sent = defaultdict(Counter)
brand_topic = defaultdict(Counter); brand_sent = defaultdict(Counter)
for r in clean:
    t = r.get('primary_topic','기타'); s = r.get('sentiment','중립'); b = r.get('brand','미상')
    topic_sent[t][s]+=1
    for a,subs in AXIS_MAP.items():
        if t in subs: axis_sent[a][s]+=1
    if b!='미상':
        brand_topic[b][t]+=1; brand_sent[b][s]+=1

def excerpt(r):
    return re.sub(r'\s+',' ', r.get('full_content','') or '').strip()[:260]

reps = {}
for topic in TOPICS:
    cands = [r for r in clean if r.get('primary_topic')==topic
             and r.get('sentiment') in ('부정','혼합')
             and len(r.get('full_content','') or '')>200]
    cands.sort(key=lambda r:(r.get('authenticity',0), r.get('rql_weight',0), r.get('word_count',0)), reverse=True)
    reps[topic] = [{'title':r['title'],'brand':r.get('brand','미상'),'sentiment':r.get('sentiment'),
                    'auth':r.get('authenticity'),'rql':r.get('rql'),'date':r.get('date'),
                    'link':r.get('link'),'excerpt':excerpt(r)} for r in cands[:8]]

out = {
    'gate3_prev': len(gate3), 'gate4_clean': len(clean), 'ad_removed': len(removed),
    'topic_sentiment': {t:dict(topic_sent[t]) for t in topic_sent},
    'axis_sentiment': {a:dict(axis_sent[a]) for a in axis_sent},
    'brand_topic': {b:dict(brand_topic[b]) for b in BRANDS if b in brand_topic},
    'brand_sentiment': {b:dict(brand_sent[b]) for b in BRANDS if b in brand_sent},
    'representative_quotes': reps,
}
(DATA/'aggregate_clean.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')

print("\n=== 3대 축 × 감성 (Gate4 clean) ===")
for a in ['냄새','공조','공기질']:
    d=axis_sent[a]; tot=sum(d.values())
    print(f"  {a} (n={tot}): 부정 {d['부정']/max(tot,1)*100:.0f}% / 혼합 {d['혼합']/max(tot,1)*100:.0f}% / 긍정 {d['긍정']/max(tot,1)*100:.0f}%")

print("\n=== 토픽 × 감성 (Gate4 clean, 부정률 순) ===")
rows=[]
for t in TOPICS:
    d=topic_sent[t]; tot=sum(d.values())
    if tot==0: continue
    rows.append((d['부정']/tot*100,t,tot,d))
for nr,t,tot,d in sorted(rows,reverse=True):
    print(f"  {t} (n={tot}): 부정 {nr:.0f}% / 혼합 {d['혼합']/tot*100:.0f}% / 긍정 {d['긍정']/tot*100:.0f}%")

print("\n=== 브랜드 × 감성 (Gate4 clean, 상위 8) ===")
for b in sorted(brand_sent,key=lambda x:-sum(brand_sent[x].values()))[:8]:
    d=brand_sent[b]; tot=sum(d.values())
    print(f"  {b} (n={tot}): 부정 {d['부정']/tot*100:.0f}% / 혼합 {d['혼합']/tot*100:.0f}% / 긍정 {d['긍정']/tot*100:.0f}%")
print(f"\n저장: {DATA/'aggregate_clean.json'}")
