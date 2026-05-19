"""
가나초콜릿하우스 재분석: 초콜릿의 즐거움(Joy) × 브랜드 고급스러움(Premium)
각 포스트를 Joy/Premium 2축으로 재스코어링
"""
import json, os, sys, io, re
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = '80-r-tech/85-analysis-results/gana-chocolate-house'
DATA_PATH = os.path.join(BASE, 'gana-chocolate-house-2layer-results.json')
RAW_PATH = os.path.join(BASE, 'gana-chocolate-house-naver-filtered.json')

with open(DATA_PATH, 'r', encoding='utf-8') as f:
    flat = json.load(f)

# 본문 매핑 (url → full_content, canonical pipeline format)
with open(RAW_PATH, 'r', encoding='utf-8') as f:
    raw_posts = json.load(f)
content_map = {p.get('link',''): (p.get('full_content','') or '') for p in raw_posts}

# ===== Joy (초콜릿의 즐거움) =====
JOY_KEYWORDS = {
    # 맛/달콤함
    '달콤': 3, '달달': 3, '달아': 2, '달콤함': 3, '단맛': 2,
    '맛있': 3, '맛나': 2, '존맛': 3, '맛집': 1, '너무 맛': 3,
    '진짜 맛': 3, '인생 초콜릿': 4, '인생': 2,
    # 감각
    '부드러': 3, '부드럽': 3, '녹아': 3, '사르르': 4, '스르르': 3,
    '진한': 2, '풍미': 3, '향긋': 2, '향이': 2, '식감': 2,
    # 감정
    '행복': 3, '행복해': 4, '즐거': 3, '신나': 3, '설레': 3,
    '기대': 2, '기분 좋': 3, '기분좋': 3, '재밌': 2, '재미': 2,
    '웃음': 2, '미소': 2, '힐링': 3, '치유': 2,
    # 예쁨/귀여움
    '귀여': 2, '예쁘': 2, '이쁘': 2, '사랑스러': 3, '사랑스럽': 3,
    '아기자기': 3, '깜찍': 2,
    # 강조
    '너무너무': 2, '진짜': 1, '완전': 1, '대박': 2, '최고': 2,
    '강추': 2, '꼭 가': 2,
}

# ===== Premium (브랜드 고급스러움) =====
PREMIUM_KEYWORDS = {
    # 고급 어휘
    '고급': 4, '고급스러': 5, '고급져': 4, '고급진': 4, '고급스럽': 5,
    '럭셔리': 5, '프리미엄': 5, '명품': 4, '하이엔드': 4,
    # 세련/우아
    '세련': 4, '우아': 4, '격조': 4, '클래식': 3, '시크': 3,
    '모던': 2, '미니멀': 2, '심플': 1,
    # 감성/무드
    '감성': 2, '무드': 3, '분위기': 2, '감각적': 3, '고상': 3,
    '차분': 2, '고요': 2,
    # 디테일/퀄리티
    '퀄리티': 3, '정성': 3, '장인': 4, '섬세': 3, '정교': 3,
    '디테일': 2, '완성도': 3,
    # 공간/인테리어 (고급 맥락)
    '인테리어': 1, '디자인': 1, '공간': 1, '조명': 1,
    # 어른 지향
    '어른': 3, '성인': 2, '어른스러': 4, '어른스럽': 4, '어른만': 3,
    '위스키': 2, '위스키바': 3, '바': 1, '페어링': 3, '칵테일': 2,
    '애프터눈티': 3, '티세트': 3, '애프터눈 티': 3,
    # 특별함
    '특별': 3, '색다른': 3, '남다른': 3, '이색': 2, '독특': 2,
    '흔치 않': 3, '쉽게 볼 수 없': 3,
    # 브랜드 가치
    '가치': 2, '소장': 3, '간직': 2, '기억': 1,
    # 한정/희소
    '한정': 3, '리미티드': 3, '오직': 2, '단독': 2,
    # 프로젝트렌트 자체
    '프로젝트렌트': 2, '프로젝트 렌트': 2, '전포동': 1,
    # 롯데제과 헤리티지
    '오래': 2, '헤리티지': 4, '역사': 2, '전통': 2, '50년': 3, '롯데': 1,
}

NEG_JOY = ['별로', '실망', '맛없', '아쉬', '기대 이하', '기대이하', '지루', '맛이 평범', '평범한']
NEG_PREMIUM = ['싸구려', '저렴해 보', '조잡', '촌스러', '유치', '성의 없', '성의없', '공장식', '대량생산']

def score_text(text, keyword_dict, neg_words):
    if not text: return 0, []
    score = 0
    hits = []
    for kw, weight in keyword_dict.items():
        cnt = text.count(kw)
        if cnt > 0:
            score += cnt * weight
            hits.append(kw)
    for neg in neg_words:
        if neg in text:
            score -= 3
    return max(0, score), hits

# ===== 전체 점수화 =====
joy_scores = []
prem_scores = []
for rec in flat:
    content = content_map.get(rec.get('link',''), '')
    text = (rec.get('title','') + ' ' + content)
    js, jh = score_text(text, JOY_KEYWORDS, NEG_JOY)
    ps, ph = score_text(text, PREMIUM_KEYWORDS, NEG_PREMIUM)
    rec['joy_score'] = js
    rec['joy_hits'] = jh[:10]
    rec['premium_score'] = ps
    rec['premium_hits'] = ph[:10]
    # 강도 등급
    rec['joy_level'] = '강' if js >= 15 else '중' if js >= 6 else '약' if js >= 1 else '없음'
    rec['premium_level'] = '강' if ps >= 15 else '중' if ps >= 6 else '약' if ps >= 1 else '없음'
    # 4분면
    joy_strong = js >= 6
    prem_strong = ps >= 6
    if joy_strong and prem_strong:
        rec['quadrant'] = 'Q1_즐거움+고급'
    elif joy_strong:
        rec['quadrant'] = 'Q2_즐거움만'
    elif prem_strong:
        rec['quadrant'] = 'Q3_고급만'
    else:
        rec['quadrant'] = 'Q4_둘다약'
    joy_scores.append(js)
    prem_scores.append(ps)

# ===== 집계 =====
N = len(flat)
gate3 = [r for r in flat if (r.get('sincerity_class') or 'B') not in ('C','E','F','G') and r.get('authenticity',0) >= 60]
G = len(gate3)

def avg(lst, key):
    vals = [r[key] for r in lst]
    return round(sum(vals)/max(len(vals),1), 1)

def pct_level(lst, key, level):
    return round(sum(1 for r in lst if r[key] == level) / max(len(lst),1) * 100, 1)

# 기간별
period_stats = {}
for p in ['사전','팝업기간','팝업후']:
    sub = [r for r in gate3 if r['period']==p]
    if sub:
        period_stats[p] = {
            'n': len(sub),
            'joy_avg': avg(sub,'joy_score'),
            'prem_avg': avg(sub,'premium_score'),
            'joy_strong_pct': round(sum(1 for r in sub if r['joy_score']>=6)/len(sub)*100,1),
            'prem_strong_pct': round(sum(1 for r in sub if r['premium_score']>=6)/len(sub)*100,1),
        }

# 4분면 분포 (Gate3 기준)
quad_dist = Counter(r['quadrant'] for r in gate3)

# 상위 keyword 추출
joy_kw_counter = Counter()
prem_kw_counter = Counter()
for r in gate3:
    for kw in r['joy_hits']:
        joy_kw_counter[kw] += 1
    for kw in r['premium_hits']:
        prem_kw_counter[kw] += 1

# 대표 포스트
top_joy = sorted(gate3, key=lambda r: -r['joy_score'])[:10]
top_prem = sorted(gate3, key=lambda r: -r['premium_score'])[:10]
top_both = sorted(gate3, key=lambda r: -(r['joy_score']+r['premium_score']))[:10]

# ===== 출력 =====
print(f"===== Joy × Premium 재분석 =====")
print(f"전체: {N}건 / Gate3 유효: {G}건")
print(f"\n[전체 {N}건]")
print(f"  Joy 평균: {avg(flat,'joy_score')} / 강 {pct_level(flat,'joy_level','강')}% / 중 {pct_level(flat,'joy_level','중')}% / 약 {pct_level(flat,'joy_level','약')}% / 없음 {pct_level(flat,'joy_level','없음')}%")
print(f"  Premium 평균: {avg(flat,'premium_score')} / 강 {pct_level(flat,'premium_level','강')}% / 중 {pct_level(flat,'premium_level','중')}% / 약 {pct_level(flat,'premium_level','약')}% / 없음 {pct_level(flat,'premium_level','없음')}%")

print(f"\n[Gate3 {G}건 — 진심 필터 통과]")
print(f"  Joy 평균: {avg(gate3,'joy_score')} / 강 {pct_level(gate3,'joy_level','강')}% / 중 {pct_level(gate3,'joy_level','중')}%")
print(f"  Premium 평균: {avg(gate3,'premium_score')} / 강 {pct_level(gate3,'premium_level','강')}% / 중 {pct_level(gate3,'premium_level','중')}%")

print(f"\n[4분면 분포 (Gate3)]")
for q, n in sorted(quad_dist.items()):
    print(f"  {q}: {n}건 ({round(n/G*100,1)}%)")

print(f"\n[기간별 변화 (Gate3)]")
for p, s in period_stats.items():
    print(f"  {p} n={s['n']}: Joy {s['joy_avg']} (강 {s['joy_strong_pct']}%) / Premium {s['prem_avg']} (강 {s['prem_strong_pct']}%)")

print(f"\n[Joy 상위 키워드]")
for kw, n in joy_kw_counter.most_common(15):
    print(f"  {kw}: {n}건")

print(f"\n[Premium 상위 키워드]")
for kw, n in prem_kw_counter.most_common(15):
    print(f"  {kw}: {n}건")

# 저장
with open(DATA_PATH, 'w', encoding='utf-8') as f:
    json.dump(flat, f, ensure_ascii=False, indent=2)

summary = {
    'N': N, 'G': G,
    'overall': {
        'joy_avg': avg(flat,'joy_score'),
        'prem_avg': avg(flat,'premium_score'),
        'joy_strong_pct': pct_level(flat,'joy_level','강'),
        'joy_mid_pct': pct_level(flat,'joy_level','중'),
        'joy_weak_pct': pct_level(flat,'joy_level','약'),
        'joy_none_pct': pct_level(flat,'joy_level','없음'),
        'prem_strong_pct': pct_level(flat,'premium_level','강'),
        'prem_mid_pct': pct_level(flat,'premium_level','중'),
        'prem_weak_pct': pct_level(flat,'premium_level','약'),
        'prem_none_pct': pct_level(flat,'premium_level','없음'),
    },
    'gate3': {
        'joy_avg': avg(gate3,'joy_score'),
        'prem_avg': avg(gate3,'premium_score'),
        'joy_strong_pct': pct_level(gate3,'joy_level','강'),
        'joy_mid_pct': pct_level(gate3,'joy_level','중'),
        'joy_weak_pct': pct_level(gate3,'joy_level','약'),
        'joy_none_pct': pct_level(gate3,'joy_level','없음'),
        'prem_strong_pct': pct_level(gate3,'premium_level','강'),
        'prem_mid_pct': pct_level(gate3,'premium_level','중'),
        'prem_weak_pct': pct_level(gate3,'premium_level','약'),
        'prem_none_pct': pct_level(gate3,'premium_level','없음'),
    },
    'quadrants': dict(quad_dist),
    'period_stats': period_stats,
    'joy_keywords': dict(joy_kw_counter.most_common(20)),
    'prem_keywords': dict(prem_kw_counter.most_common(20)),
    'top_joy_posts': [{'title':r['title'][:80],'date':r['date'],'joy':r['joy_score'],'prem':r['premium_score'],'hits':r['joy_hits'][:6],'link':r['link']} for r in top_joy],
    'top_prem_posts': [{'title':r['title'][:80],'date':r['date'],'joy':r['joy_score'],'prem':r['premium_score'],'hits':r['premium_hits'][:6],'link':r['link']} for r in top_prem],
    'top_both_posts': [{'title':r['title'][:80],'date':r['date'],'joy':r['joy_score'],'prem':r['premium_score'],'link':r['link']} for r in top_both],
}

with open(os.path.join(BASE, 'gana-joy-premium-summary.json'), 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)
print(f"\n저장: gana-joy-premium-summary.json")
