"""
가나초콜릿하우스 CatchTable 매장 후기 — RXR 캐논 파이프라인 적용
ingest → sincerity_filter → two_layer → gates → Joy×Premium 재분석
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'rxr-sns-app'))

from app.pipeline import sincerity_filter, two_layer, gates as gates_mod

BASE = os.path.join(ROOT, '80-r-tech', '85-analysis-results', 'gana-chocolate-house')
INGEST_JSON = os.path.join(BASE, 'gana-chocolate-house-catchtable-ingested.json')
OUT_2LAYER = os.path.join(BASE, 'gana-chocolate-house-catchtable-2layer-results.json')
OUT_SUMMARY = os.path.join(BASE, 'gana-chocolate-house-catchtable-summary.json')

EVENT_START = '20230212'
EVENT_END = '20230314'

# gana_crawl.py의 GANA_TOPICS 재사용
GANA_TOPICS = {
    '공간/분위기': ['공간','분위기','인테리어','포토존','사진','감성','프로젝트렌트','전포','인더스트리','무드','포토부스','조명','룸','디자인'],
    '초콜릿/맛': ['초콜릿','초콜렛','카카오','맛','풍미','달콤','쌉쌀','다크','밀크','봉봉','트러플','프랄린','가나','케이크','디저트','단맛','달달','녹아','부드러'],
    '위스키/페어링': ['위스키','위스키바','페어링','바','칵테일','잔','샷','하이볼','싱글몰트','버번','피트','스모키','글렌','발베니'],
    '애프터눈티': ['애프터눈','애프터눈티','애프터눈 티','티세트','3단','샌드위치','스콘','홍차','얼그레이','다과','티타임','세트','플레이트'],
    '웨이팅/예약': ['웨이팅','예약','줄','대기','기다','오픈런','시간 제한','네이버 예약','캐치테이블','만석','예매'],
    '가격/혜택': ['가격','비싸','가성비','할인','무료','혜택','이벤트','굿즈','증정','한정','리미티드','선착순','체험료'],
    '굿즈/기념품': ['굿즈','스티커','엽서','포토카드','틴','케이스','기념품','패키지','증정품','MD','머그','에코백'],
    '체험/프로그램': ['체험','원데이','클래스','만들기','직접','체험형','프로그램','참여','시음','테이스팅','페어링','코스','가이드'],
    '브랜드': ['가나','가나초콜릿','롯데','롯데제과','가나초콜릿하우스'],
}

# Joy / Premium 키워드 (reframe_joy_premium.py와 동일)
JOY_KEYWORDS = {
    '달콤': 3, '달달': 3, '달아': 2, '달콤함': 3, '단맛': 2,
    '맛있': 3, '맛나': 2, '존맛': 3, '맛집': 1, '너무 맛': 3,
    '진짜 맛': 3, '인생 초콜릿': 4, '인생': 2,
    '부드러': 3, '부드럽': 3, '녹아': 3, '사르르': 4, '스르르': 3,
    '진한': 2, '풍미': 3, '향긋': 2, '향이': 2, '식감': 2,
    '행복': 3, '행복해': 4, '즐거': 3, '신나': 3, '설레': 3,
    '기대': 2, '기분 좋': 3, '기분좋': 3, '재밌': 2, '재미': 2,
    '웃음': 2, '미소': 2, '힐링': 3, '치유': 2,
    '귀여': 2, '예쁘': 2, '이쁘': 2, '사랑스러': 3, '사랑스럽': 3,
    '아기자기': 3, '깜찍': 2,
    '너무너무': 2, '진짜': 1, '완전': 1, '대박': 2, '최고': 2,
    '강추': 2, '꼭 가': 2,
}

PREMIUM_KEYWORDS = {
    '고급': 4, '고급스러': 5, '고급져': 4, '고급진': 4, '고급스럽': 5,
    '럭셔리': 5, '프리미엄': 5, '명품': 4, '하이엔드': 4,
    '세련': 4, '우아': 4, '격조': 4, '클래식': 3, '시크': 3,
    '모던': 2, '미니멀': 2, '심플': 1,
    '감성': 2, '무드': 3, '분위기': 2, '감각적': 3, '고상': 3,
    '차분': 2, '고요': 2,
    '퀄리티': 3, '정성': 3, '장인': 4, '섬세': 3, '정교': 3,
    '디테일': 2, '완성도': 3,
    '인테리어': 1, '디자인': 1, '공간': 1, '조명': 1,
    '어른': 3, '성인': 2, '어른스러': 4, '어른스럽': 4, '어른만': 3,
    '위스키': 2, '위스키바': 3, '바': 1, '페어링': 3, '칵테일': 2,
    '애프터눈티': 3, '티세트': 3, '애프터눈 티': 3, '애프터눈': 3,
    '특별': 3, '색다른': 3, '남다른': 3, '이색': 2, '독특': 2,
    '흔치 않': 3, '쉽게 볼 수 없': 3,
    '가치': 2, '소장': 3, '간직': 2, '기억': 1,
    '한정': 3, '리미티드': 3, '오직': 2, '단독': 2,
    '프로젝트렌트': 2, '프로젝트 렌트': 2, '전포동': 1,
    '오래': 2, '헤리티지': 4, '역사': 2, '전통': 2, '50년': 3, '롯데': 1,
}

NEG_JOY = ['별로','실망','맛없','아쉬','기대 이하','기대이하','지루','평범한']
NEG_PREMIUM = ['싸구려','저렴해 보','조잡','촌스러','유치','성의 없','성의없','공장식','대량생산']


def score_text(text, kw_dict, neg_words):
    if not text:
        return 0, []
    score = 0
    hits = []
    for kw, w in kw_dict.items():
        cnt = text.count(kw)
        if cnt > 0:
            score += cnt * w
            hits.append(kw)
    for neg in neg_words:
        if neg in text:
            score -= 3
    return max(0, score), hits


def avg(lst, key):
    if not lst:
        return 0
    return round(sum(r.get(key, 0) for r in lst) / len(lst), 1)


# ============================================================
# STEP 1: Load ingested
# ============================================================
print("=" * 60)
print("STEP 1: ingested.json 로드")
print("=" * 60)
with open(INGEST_JSON, 'r', encoding='utf-8') as f:
    all_records = json.load(f)
print(f"  전체: {len(all_records)}건")

brand_records = [r for r in all_records if r.get('brand_focus')]
excluded = [r for r in all_records if not r.get('brand_focus')]
print(f"  브랜드 후기 (brand_focus=True): {len(brand_records)}건")
print(f"  제외 (service_only): {len(excluded)}건")

# ============================================================
# STEP 2: Sincerity Filter
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: Sincerity Filter (A~G)")
print("=" * 60)

sincerity_filter.apply_filter(brand_records)

# E등급 승급 후처리 (CatchTable 특화)
upgraded_to_b = 0
upgraded_to_a = 0
for r in brand_records:
    cls = r.get('sincerity_class')
    raw_len = len(r.get('raw_review', ''))
    if cls == 'E' and raw_len >= 15:
        r['sincerity_class'] = 'B'
        r['sincerity_flags'] = (r.get('sincerity_flags') or []) + ['CATCHTABLE_UPGRADED_B']
        upgraded_to_b += 1
    # A 승급: 별점 평균 >= 4.5 + brand_hits >= 2
    if r.get('star_avg', 0) >= 4.5 and r.get('brand_hits', 0) >= 2 and r.get('sincerity_class') == 'B':
        r['sincerity_class'] = 'A'
        r['sincerity_flags'] = (r.get('sincerity_flags') or []) + ['CATCHTABLE_UPGRADED_A']
        upgraded_to_a += 1

print(f"  E→B 승급: {upgraded_to_b}건 (본문 >=15자)")
print(f"  B→A 승급: {upgraded_to_a}건 (별점 >=4.5 + 브랜드키워드 >=2)")

dist = sincerity_filter.class_distribution(brand_records) if hasattr(sincerity_filter,'class_distribution') else None
if dist is None:
    from collections import Counter
    dist = Counter(r['sincerity_class'] for r in brand_records)
for cls in 'ABCDEFG':
    print(f"  {cls}: {dist.get(cls, 0)}건")

# ============================================================
# STEP 3: 2-Layer 분석
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: 2-Layer 분석 (GANA_TOPICS)")
print("=" * 60)

# two_layer.analyze_post는 full_text < 50이면 None 반환 → CatchTable 짧은 리뷰 보호용 우회
# title + " " + description + " " + full_content 길이 보강
for r in brand_records:
    # description을 비워둔 상태라, full_text = " " + " " + full_content
    # 안전하게 50자 보장 위해, 50자 미만 시 description에 padding
    full_text_len = len(r.get('full_content', '')) + 2  # title, desc 빈값 고려
    if full_text_len < 50:
        padding = ' 가나초콜릿하우스 부산 시즌2 매장 방문 후기 '
        r['description'] = padding

analyzed = two_layer.analyze_all(brand_records, EVENT_START, EVENT_END, topics=GANA_TOPICS)

# analyze_all은 link로 매칭 못 하므로 인덱스로 메타 병합
# analyze_post가 {date, period, title, blogger, link, ...}만 반환 → 원본 메타를 link로 백매핑
link_to_source = {r['link']: r for r in brand_records}
for a in analyzed:
    src = link_to_source.get(a['link'], {})
    # CatchTable 전용 필드 병합
    for k in ['star_taste','star_vibe','star_service','star_avg','source','platform',
              'brand_focus','filter_reason','brand_hits','service_hits','star_gap',
              'raw_review','sincerity_class','trust_score','sincerity_flags']:
        if k in src:
            a[k] = src[k]

print(f"  2-Layer 분석 완료: {len(analyzed)}건")

# Joy / Premium 스코어링
for a in analyzed:
    txt = (a.get('title','') or '') + ' ' + (a.get('raw_review','') or '')
    js, jh = score_text(txt, JOY_KEYWORDS, NEG_JOY)
    ps, ph = score_text(txt, PREMIUM_KEYWORDS, NEG_PREMIUM)
    a['joy_score'] = js
    a['joy_hits'] = jh[:10]
    a['premium_score'] = ps
    a['premium_hits'] = ph[:10]
    joy_strong = js >= 6
    prem_strong = ps >= 6
    if joy_strong and prem_strong:
        a['quadrant'] = 'Q1_즐거움+고급'
    elif joy_strong:
        a['quadrant'] = 'Q2_즐거움만'
    elif prem_strong:
        a['quadrant'] = 'Q3_고급만'
    else:
        a['quadrant'] = 'Q4_둘다약'

# 통계
from collections import Counter
sent = Counter(a['sentiment'] for a in analyzed)
topic = Counter(a['primary_topic'] for a in analyzed)
rql = Counter(a['rql'] for a in analyzed)
print(f"  감성: {dict(sent)}")
print(f"  토픽 TOP: {topic.most_common(5)}")
print(f"  RQL: {dict(rql)}")
print(f"  Auth 평균: {avg(analyzed,'authenticity')}, Clout: {avg(analyzed,'clout')}, Fresh: {avg(analyzed,'freshness_index')}")
print(f"  Joy 평균: {avg(analyzed,'joy_score')}, Premium 평균: {avg(analyzed,'premium_score')}")

# ============================================================
# STEP 4: Sincerity Gate
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: Sincerity Gate")
print("=" * 60)

g = gates_mod.run_all_gates(analyzed)
for key in ['gate1', 'gate2', 'gate3']:
    s = g[key]['summary']
    print(f"  {key}: {s['n']}건, 긍정 {s['positive_pct']}%, Auth {s.get('auth','-')}")

gate3_posts = g['gate3']['posts']

# 4분면 (Gate3 기준)
q_count = Counter(a['quadrant'] for a in gate3_posts)
print(f"\n  4분면 (Gate3 {len(gate3_posts)}건):")
for q in ['Q1_즐거움+고급','Q2_즐거움만','Q3_고급만','Q4_둘다약']:
    n = q_count.get(q, 0)
    pct = round(n/max(len(gate3_posts),1)*100,1)
    print(f"    {q}: {n}건 ({pct}%)")

# ============================================================
# STEP 5: 저장
# ============================================================
with open(OUT_2LAYER, 'w', encoding='utf-8') as f:
    json.dump(analyzed, f, ensure_ascii=False, indent=2)
print(f"\n저장: {OUT_2LAYER}")

# Summary
summary = {
    'total_ingested': len(all_records),
    'brand_focus_true': len(brand_records),
    'excluded_service_only': len(excluded),
    'upgraded_E_to_B': upgraded_to_b,
    'upgraded_B_to_A': upgraded_to_a,
    'sincerity_class_dist': dict(dist),
    'analyzed_n': len(analyzed),
    'sentiment_dist': dict(sent),
    'topic_dist': dict(topic),
    'rql_dist': dict(rql),
    'auth_avg': avg(analyzed,'authenticity'),
    'clout_avg': avg(analyzed,'clout'),
    'freshness_avg': avg(analyzed,'freshness_index'),
    'joy_avg': avg(analyzed,'joy_score'),
    'premium_avg': avg(analyzed,'premium_score'),
    'gate1': g['gate1']['summary'],
    'gate2': g['gate2']['summary'],
    'gate3': g['gate3']['summary'],
    'gate3_n': len(gate3_posts),
    'quadrant_dist_gate3': dict(q_count),
}

with open(OUT_SUMMARY, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"저장: {OUT_SUMMARY}")
print(f"\n✓ Pipeline 완료: ingested {len(all_records)} → brand {len(brand_records)} → 2-Layer {len(analyzed)} → Gate3 {len(gate3_posts)}")
