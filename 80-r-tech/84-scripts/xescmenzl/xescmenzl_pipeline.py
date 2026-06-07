"""
세스크멘슬 SNS 분석 파이프라인 v1.0
크롤링 → Sincerity Filter → 2-Layer → Linguistic Layer → 리포트

사용법:
  python xescmenzl_pipeline.py [--days 90] [--skip-crawl] [--skip-linguistic]

전체 파이프라인:
  1. xescmenzl_crawl.py 실행 (데이터 수집 + 2-Layer 분석)
  2. Linguistic Layer 분석 (regex 기반 경량 + LLM 보정)
  3. LAI/EDS 산출 + Psyche Layer 보정
  4. 요약 리포트 생성
"""

import json
import re
import sys
import os
import math
from datetime import datetime
from pathlib import Path
from collections import Counter

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / '10-projects' / '29-xescmenzl-sns' / 'config.json'


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================
# Linguistic Layer: 로컬 regex 기반 분석
# ============================================================

def analyze_sensory(text, config):
    """감각어 밀도 분석"""
    sensory_vocab = config.get('linguistic_layer', {}).get('sensory_vocabulary', {})
    all_sensory = []
    for category, words in sensory_vocab.items():
        for w in words:
            all_sensory.extend(re.findall(re.escape(w), text.lower()))

    word_count = max(len(text.split()), 1)
    density = len(all_sensory) / word_count * 100
    return {
        'words_found': list(set(all_sensory)),
        'count': len(all_sensory),
        'density': round(density, 2),
    }


def analyze_function_words(text):
    """기능어 패턴 분석 (Pennebaker 기반)"""
    first_person = len(re.findall(r'나는|내가|저는|제가|난\s|전\s|나의|내\s', text))
    we_person = len(re.findall(r'우리|같이|함께|다같이', text))
    reader_directed = len(re.findall(r'여러분|당신|너희|분들', text))

    # 조사 패턴
    iga = len(re.findall(r'[가-힣]이\s|[가-힣]가\s', text))
    eunneun = len(re.findall(r'[가-힣]은\s|[가-힣]는\s', text))
    eseo = len(re.findall(r'에서', text))
    boda = len(re.findall(r'보다', text))

    word_count = max(len(text.split()), 1)
    first_ratio = round(first_person / word_count * 100, 2)

    return {
        'first_person': first_person,
        'first_person_ratio': first_ratio,
        'we_person': we_person,
        'reader_directed': reader_directed,
        'particle_iga': iga,
        'particle_eunneun': eunneun,
        'particle_eseo': eseo,
        'particle_boda': boda,
    }


def analyze_certainty(text, config):
    """확신도 스펙트럼 분석"""
    cert_config = config.get('linguistic_layer', {}).get('certainty_markers', {})
    high_markers = cert_config.get('high', [])
    hedge_markers = cert_config.get('hedge', [])

    text_lower = text.lower()
    high_found = [m for m in high_markers if m in text_lower]
    hedge_found = [m for m in hedge_markers if m in text_lower]

    high_count = sum(text_lower.count(m) for m in high_markers)
    hedge_count = sum(text_lower.count(m) for m in hedge_markers)
    total = max(high_count + hedge_count, 1)

    return {
        'high_markers': high_found,
        'hedge_markers': hedge_found,
        'high_count': high_count,
        'hedge_count': hedge_count,
        'certainty_ratio': round(high_count / total * 100, 1),
    }


def analyze_discourse(text, config):
    """담화 표지 분석"""
    disc_config = config.get('linguistic_layer', {}).get('discourse_markers', {})
    text_lower = text.lower()

    contrast = [m for m in disc_config.get('contrast', []) if m in text_lower]
    conditional = [m for m in disc_config.get('conditional', []) if m in text_lower]
    causal = [m for m in disc_config.get('causal', []) if m in text_lower]

    contrast_count = sum(text_lower.count(m) for m in disc_config.get('contrast', []))
    cond_count = sum(text_lower.count(m) for m in disc_config.get('conditional', []))
    causal_count = sum(text_lower.count(m) for m in disc_config.get('causal', []))

    score = min(contrast_count * 15 + cond_count * 12 + causal_count * 10, 100)

    return {
        'contrast_markers': contrast,
        'conditional_markers': conditional,
        'causal_markers': causal,
        'discourse_score': score,
    }


def analyze_pragmatics(text):
    """화용론적 분석"""
    indirect_neg = re.findall(r'나쁘진\s*않|별로\s*안|그렇게\s*좋진|막\s*그런', text)
    litotes = re.findall(r'안\s*나쁘|못할\s*것도\s*없|나쁘지\s*않', text)
    rhetorical = re.findall(r'안\s*\S+\s*수\s*있|어떻게\s*안|왜\s*안', text)
    conditional_rec = re.findall(r'좋아하\S*면\s*(?:추천|강추|좋)', text)
    implicit_comp = re.findall(r'다른\s*껌\S*\s*(?:다르|달리|비해|보다)', text)

    sentiment_reclass = None
    if indirect_neg:
        sentiment_reclass = 'neutral→mixed'
    elif litotes:
        sentiment_reclass = 'neutral→mixed(긍정기울)'

    return {
        'indirect_negatives': indirect_neg,
        'litotes': litotes,
        'rhetorical_questions': rhetorical,
        'conditional_recommendations': conditional_rec,
        'implicit_comparisons': implicit_comp,
        'sentiment_reclassification': sentiment_reclass,
    }


def analyze_register(text, config):
    """문체 레지스터 분석"""
    reg_config = config.get('linguistic_layer', {}).get('register_patterns', {})

    # 문장 단위 분할
    sentences = re.split(r'[.!?。]\s*', text)
    sentences = [s for s in sentences if len(s.strip()) > 5]

    if not sentences:
        return {
            'dominant': '판별불가',
            'formal_ratio': 0,
            'polite_ratio': 0,
            'casual_ratio': 0,
            'consistency': 0,
            'template_suspect': False,
        }

    formal_pats = reg_config.get('formal', [])
    polite_pats = reg_config.get('polite_informal', [])
    casual_pats = reg_config.get('casual', [])

    registers = []
    for sent in sentences:
        formal_score = sum(1 for p in formal_pats if p in sent)
        polite_score = sum(1 for p in polite_pats if p in sent)
        casual_score = sum(1 for p in casual_pats if p in sent)

        if formal_score > polite_score and formal_score > casual_score:
            registers.append('합쇼체')
        elif casual_score > polite_score:
            registers.append('해체')
        elif polite_score > 0:
            registers.append('해요체')
        else:
            registers.append('판별불가')

    valid_registers = [r for r in registers if r != '판별불가']
    if not valid_registers:
        return {
            'dominant': '판별불가',
            'formal_ratio': 0,
            'polite_ratio': 0,
            'casual_ratio': 0,
            'consistency': 0,
            'template_suspect': False,
        }

    reg_count = Counter(valid_registers)
    dominant = reg_count.most_common(1)[0][0]
    total = len(valid_registers)

    formal_ratio = round(reg_count.get('합쇼체', 0) / total * 100, 1)
    polite_ratio = round(reg_count.get('해요체', 0) / total * 100, 1)
    casual_ratio = round(reg_count.get('해체', 0) / total * 100, 1)
    consistency = round(reg_count.most_common(1)[0][1] / total * 100, 1)

    template_suspect = consistency > 95 and dominant == '합쇼체'

    return {
        'dominant': dominant,
        'formal_ratio': formal_ratio,
        'polite_ratio': polite_ratio,
        'casual_ratio': casual_ratio,
        'consistency': consistency,
        'template_suspect': template_suspect,
    }


# ============================================================
# 복합 지표: LAI & EDS
# ============================================================

def calculate_lai(sensory, function_words, certainty, register, text):
    """LAI (Linguistic Authenticity Index) 산출"""

    # 1. 감각어 밀도 정규화 (0~1, cap at 10/100단어)
    sensory_norm = min(sensory['density'] / 10.0, 1.0)

    # 2. 헤징 자연도 (certainty 20~60이 최적)
    cert = certainty['certainty_ratio']
    if 20 <= cert <= 60:
        hedging_nat = 1.0
    elif cert < 20:
        hedging_nat = max(0, cert / 20)
    else:
        hedging_nat = max(0, 1 - (cert - 60) / 40)

    # 3. 레지스터 변동성 (75% 근처가 자연스러움)
    cons = register['consistency']
    if cons == 0:
        reg_var = 0.5
    else:
        reg_var = max(0, 1 - abs(cons - 75) / 25)
        reg_var = min(reg_var, 1.0)

    # 4. 시간 근접 표지
    temporal_markers = ['오늘', '아까', '방금', '지금', '어제', '아까전']
    has_temporal = any(m in text for m in temporal_markers)
    temporal = 1.0 if has_temporal else 0.0

    # 5. 1인칭 자연도 (5~15%가 자연스러움)
    fp_ratio = function_words['first_person_ratio']
    if 5 <= fp_ratio <= 15:
        fp_nat = 1.0
    elif fp_ratio < 5:
        fp_nat = max(0, fp_ratio / 5)
    else:
        fp_nat = max(0, 1 - (fp_ratio - 15) / 15)

    lai = round(
        sensory_norm * 30 +
        hedging_nat * 20 +
        reg_var * 20 +
        temporal * 15 +
        fp_nat * 15,
        1
    )
    return lai


def calculate_eds(discourse, pragmatics, text):
    """EDS (Engagement Depth Score) 산출"""
    word_count = max(len(text.split()), 1)
    sentences = re.split(r'[.!?。]\s*', text)
    sent_count = max(len([s for s in sentences if len(s.strip()) > 5]), 1)

    # 1. 은유/비유 밀도 (간접 추정: 감각적 비유 패턴)
    metaphors = re.findall(
        r'처럼|같은|마치|느낌이|듯한|비슷한|연상|떠오르',
        text
    )
    metaphor_density = min(len(metaphors) / sent_count, 1.0)

    # 2. 담화 복잡성
    discourse_norm = min(discourse['discourse_score'] / 100, 1.0)

    # 3. 한정 표지 밀도 ("개인적으로", "제 입장에서", "취향 차이")
    qualifiers = re.findall(
        r'개인적으로|제 입장|내 생각|취향|주관적|솔직히|사실은',
        text
    )
    qual_density = min(len(qualifiers) / sent_count, 1.0)

    # 4. 구체적 디테일 밀도 (숫자, 장소명, 시간 표현)
    details = re.findall(
        r'\d+[원개알통팩분시간일]|편의점|마트|올리브영|쿠팡|다이소|약국',
        text
    )
    detail_density = min(len(details) / sent_count, 1.0)

    eds = round(
        metaphor_density * 25 +
        discourse_norm * 25 +
        qual_density * 25 +
        detail_density * 25,
        1
    )
    return eds


# ============================================================
# Psyche Layer 보정
# ============================================================

def calculate_psyche_adjustments(sensory, function_words, certainty,
                                  discourse, pragmatics, register,
                                  existing_result):
    """Linguistic Layer 기반 Psyche Layer 보정값 산출"""
    auth_delta = 0
    clout_delta = 0
    freshness_delta = 0
    trust_delta = 0
    rql_upgrade = False
    sentiment_reclass = None

    # 감각어 밀도 > 3/100단어 → Auth +8
    if sensory['density'] > 3:
        auth_delta += 8

    # 1인칭 자연 범위 5~15% → Auth +5
    if 5 <= function_words['first_person_ratio'] <= 15:
        auth_delta += 5

    # 확신도 스펙트럼 보정
    cert = certainty['certainty_ratio']
    extreme_pos = existing_result.get('extreme_pos', 0)

    if 20 <= cert <= 60:
        auth_delta += 5  # 균형잡힌 헤징 = 가장 진정성 높은 구간
    elif cert > 80 and extreme_pos > 5:
        auth_delta -= 5  # 과잉 확신 + 과잉 긍정

    # 시간근접 표지 → Freshness +5
    temporal_markers = ['오늘', '아까', '방금', '지금', '어제']
    text = existing_result.get('full_content', '') or ''
    if any(m in text for m in temporal_markers):
        freshness_delta += 5

    # 합쇼체 일관 = 템플릿 의심 → Trust -10
    if register['template_suspect']:
        trust_delta -= 10

    # 자연스러운 레지스터 전환 → Auth +3
    if 60 <= register['consistency'] <= 85:
        auth_delta += 3

    # 대조 표지 ≥ 2개 → Auth +5
    if len(discourse.get('contrast_markers', [])) >= 2:
        auth_delta += 5

    # 담화 복잡성 높으면 RQL 승격 고려
    if discourse['discourse_score'] >= 40:
        current_rql = existing_result.get('rql', '')
        if current_rql == 'Q3_경험형':
            rql_upgrade = True

    # 화용론적 감성 재분류
    if pragmatics.get('sentiment_reclassification'):
        sentiment_reclass = pragmatics['sentiment_reclassification']

    # 조건부 추천 → Clout +10
    if pragmatics.get('conditional_recommendations'):
        clout_delta += 10

    return {
        'auth_delta': auth_delta,
        'clout_delta': clout_delta,
        'freshness_delta': freshness_delta,
        'trust_delta': trust_delta,
        'rql_upgrade': rql_upgrade,
        'sentiment_reclassify': sentiment_reclass,
    }


# ============================================================
# 통합 Linguistic Analysis
# ============================================================

def linguistic_analyze(post, config):
    """단일 포스트에 대한 전체 Linguistic Layer 분석"""
    text = post.get('full_content', '') or ''
    if len(text) < 50:
        return None

    sensory = analyze_sensory(text, config)
    func_words = analyze_function_words(text)
    certainty = analyze_certainty(text, config)
    discourse = analyze_discourse(text, config)
    pragmatics = analyze_pragmatics(text)
    register = analyze_register(text, config)

    lai = calculate_lai(sensory, func_words, certainty, register, text)
    eds = calculate_eds(discourse, pragmatics, text)

    auth = post.get('authenticity', 60)
    lai_auth_gap = lai - auth

    flag = None
    if abs(lai_auth_gap) > 20:
        if lai > auth:
            flag = 'AUTH_UNDERESTIMATE'
        else:
            flag = 'POSSIBLE_CRAFTED'

    adjustments = calculate_psyche_adjustments(
        sensory, func_words, certainty, discourse, pragmatics, register, post
    )

    return {
        'morphological': {
            'sensory_density': sensory['density'],
            'sensory_words': sensory['words_found'],
            'sensory_count': sensory['count'],
        },
        'function_words': func_words,
        'certainty': certainty,
        'discourse': discourse,
        'pragmatics': pragmatics,
        'register': register,
        'composite': {
            'LAI': lai,
            'EDS': eds,
            'lai_auth_gap': round(lai_auth_gap, 1),
            'flag': flag,
        },
        'psyche_adjustments': adjustments,
    }


# ============================================================
# 보정 적용
# ============================================================

def apply_adjustments(result, linguistic):
    """Linguistic Layer 보정을 기존 결과에 적용"""
    adj = linguistic['psyche_adjustments']
    enhanced = dict(result)

    # Auth 보정
    auth = enhanced.get('authenticity', 60) + adj['auth_delta']
    enhanced['authenticity'] = max(10, min(95, auth))
    enhanced['auth_delta'] = adj['auth_delta']

    # Clout 보정
    clout = enhanced.get('clout', 40) + adj['clout_delta']
    enhanced['clout'] = max(10, min(95, clout))
    enhanced['clout_delta'] = adj['clout_delta']

    # Freshness 보정
    fresh = enhanced.get('freshness_index', 50) + adj['freshness_delta']
    enhanced['freshness_index'] = max(0, min(100, fresh))

    # Trust 보정
    trust = enhanced.get('trust_score', 70) + adj['trust_delta']
    enhanced['trust_score'] = max(0, min(100, trust))

    # RQL 승격
    if adj['rql_upgrade'] and enhanced.get('rql') == 'Q3_경험형':
        enhanced['rql'] = 'Q4_분석형(승격)'
        enhanced['rql_weight'] = 1.5

    # 감성 재분류
    if adj['sentiment_reclassify']:
        if adj['sentiment_reclassify'] == 'neutral→mixed':
            if enhanced.get('sentiment') == '중립':
                enhanced['sentiment'] = '혼합'
        elif adj['sentiment_reclassify'] == 'neutral→mixed(긍정기울)':
            if enhanced.get('sentiment') == '중립':
                enhanced['sentiment'] = '혼합'

    # Linguistic 데이터 추가
    enhanced['LAI'] = linguistic['composite']['LAI']
    enhanced['EDS'] = linguistic['composite']['EDS']
    enhanced['lai_auth_gap'] = linguistic['composite']['lai_auth_gap']
    enhanced['linguistic_flag'] = linguistic['composite']['flag']
    enhanced['register_dominant'] = linguistic['register']['dominant']
    enhanced['certainty_ratio'] = linguistic['certainty']['certainty_ratio']
    enhanced['discourse_score'] = linguistic['discourse']['discourse_score']
    enhanced['sensory_density'] = linguistic['morphological']['sensory_density']

    return enhanced


# ============================================================
# 요약 리포트 생성
# ============================================================

def generate_summary_report(results, config, output_dir):
    """마크다운 요약 리포트 생성"""
    today = datetime.now().strftime('%Y-%m-%d')
    brand = config['brand']['name']

    valid = [r for r in results if r.get('content_class') in ('A', 'B', 'C')]
    if not valid:
        return

    # 집계
    total = len(results)
    valid_count = len(valid)
    class_dist = Counter(r['content_class'] for r in results)
    sent_dist = Counter(r.get('sentiment', '중립') for r in valid)
    rql_dist = Counter(r.get('rql', 'Q1_간단형') for r in valid)

    avg_auth = sum(r.get('authenticity', 0) for r in valid) / valid_count
    avg_clout = sum(r.get('clout', 0) for r in valid) / valid_count
    avg_fresh = sum(r.get('freshness_index', 0) for r in valid) / valid_count
    avg_lai = sum(r.get('LAI', 0) for r in valid) / valid_count
    avg_eds = sum(r.get('EDS', 0) for r in valid) / valid_count

    flagged = [r for r in valid if r.get('linguistic_flag')]

    # 토픽 분포
    topic_dist = Counter(r.get('primary_topic', '기타') for r in valid)

    rql_asset = sum(r.get('rql_weight', 0.2) for r in valid)

    report = f"""# {brand} SNS 감정분석 리포트

**분석일:** {today}
**데이터 기간:** 최근 크롤링 데이터

---

## 1. 데이터 개요

| 항목 | 수치 |
|------|------|
| 전체 수집 | {total}건 |
| 유효 분석 대상 (A+B+C) | {valid_count}건 |
| Content Class A (진성후기) | {class_dist.get('A', 0)}건 |
| Content Class B (일반포스트) | {class_dist.get('B', 0)}건 |
| Content Class C (협찬) | {class_dist.get('C', 0)}건 |
| 필터 제외 (D~G) | {sum(class_dist.get(c, 0) for c in 'DEFG')}건 |

---

## 2. 감성 분포

| 감성 | 건수 | 비율 |
|------|------|------|
| 긍정 | {sent_dist.get('긍정', 0)}건 | {sent_dist.get('긍정', 0)/valid_count*100:.0f}% |
| 혼합 | {sent_dist.get('혼합', 0)}건 | {sent_dist.get('혼합', 0)/valid_count*100:.0f}% |
| 중립 | {sent_dist.get('중립', 0)}건 | {sent_dist.get('중립', 0)/valid_count*100:.0f}% |
| 부정 | {sent_dist.get('부정', 0)}건 | {sent_dist.get('부정', 0)/valid_count*100:.0f}% |

---

## 3. 토픽 분포

| 토픽 | 건수 |
|------|------|
"""
    for topic, count in topic_dist.most_common():
        report += f"| {topic} | {count}건 |\n"

    report += f"""
---

## 4. RQL (리뷰 품질 등급)

| 등급 | 건수 | 가중치 |
|------|------|--------|
"""
    for q in ['Q5_서사형', 'Q4_분석형', 'Q4_분석형(승격)', 'Q3_경험형', 'Q2_감상형', 'Q1_간단형']:
        c = rql_dist.get(q, 0)
        if c > 0:
            report += f"| {q} | {c}건 | — |\n"

    report += f"""
**리뷰 자산값:** {rql_asset:.1f} (평균 {rql_asset/valid_count:.2f}/건)

---

## 5. Psyche Layer + Linguistic Layer

| 지표 | 평균 | 해석 |
|------|------|------|
| Authenticity | {avg_auth:.1f} | 진정성 (Linguistic 보정 후) |
| Clout | {avg_clout:.1f} | 추천 확신 강도 |
| Freshness | {avg_fresh:.1f} | 정보 신선도 (CLT 기반) |
| **LAI** | {avg_lai:.1f} | 언어학적 진정성 지수 |
| **EDS** | {avg_eds:.1f} | 인지적 몰입도 |

### LAI-Auth 교차검증

- LAI-Auth 괴리 플래그 (|차이|>20): **{len(flagged)}건**
"""
    if flagged:
        report += "\n| 제목 | Auth | LAI | Gap | 유형 |\n|------|------|-----|-----|------|\n"
        for r in flagged[:10]:
            report += f"| {r.get('title', '')[:30]} | {r.get('authenticity', 0)} | {r.get('LAI', 0)} | {r.get('lai_auth_gap', 0):+.0f} | {r.get('linguistic_flag', '')} |\n"

    report += f"""
---

## 6. 핵심 인사이트

> 이 섹션은 데이터 기반으로 자동 생성된 초안입니다. LLM 심층 해석 필요.

- **전체 건수**: {total}건 중 유효 {valid_count}건 (유효율 {valid_count/max(total,1)*100:.0f}%)
- **감성 기조**: 긍정 {sent_dist.get('긍정', 0)/valid_count*100:.0f}% / 혼합 {sent_dist.get('혼합', 0)/valid_count*100:.0f}% / 부정 {sent_dist.get('부정', 0)/valid_count*100:.0f}%
- **진정성**: Auth {avg_auth:.0f} / LAI {avg_lai:.0f} (교차검증 {('일치' if abs(avg_auth - avg_lai) <= 10 else '경미한 불일치' if abs(avg_auth - avg_lai) <= 20 else '유의미한 괴리')})
- **인게이지먼트 깊이**: EDS 평균 {avg_eds:.0f}

---

*Generated by RXR Linguistic Layer v1.0 — {today}*
"""

    report_path = output_dir / f'{brand}-sns-report-{today}.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"  리포트 저장: {report_path}")
    return report_path


# ============================================================
# 메인 파이프라인
# ============================================================

def main():
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(description='세스크멘슬 SNS 분석 파이프라인')
    parser.add_argument('--days', type=int, default=30, help='크롤링 기간')
    parser.add_argument('--skip-crawl', action='store_true', help='크롤링 생략 (기존 데이터 사용)')
    parser.add_argument('--skip-linguistic', action='store_true', help='Linguistic Layer 생략')
    parser.add_argument('--data-dir', type=str, default=None, help='기존 데이터 디렉토리')
    args = parser.parse_args()

    config = load_config()
    today = datetime.now().strftime('%Y-%m-%d')

    print("=" * 60)
    print(f"세스크멘슬 SNS 분석 파이프라인 v1.0 — {today}")
    print("=" * 60)

    # ─── Phase 1: 크롤링 ───
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = PROJECT_ROOT / config['output']['data_dir'] / today

    if not args.skip_crawl:
        print("\n[Phase 1] 데이터 크롤링")
        crawl_script = SCRIPT_DIR / 'xescmenzl_crawl.py'
        result = subprocess.run(
            [sys.executable, str(crawl_script), '--days', str(args.days)],
            cwd=str(SCRIPT_DIR),
            capture_output=False,
        )
        if result.returncode != 0:
            print("[ERROR] 크롤링 실패")
            sys.exit(1)
    else:
        print("\n[Phase 1] 크롤링 생략 (기존 데이터 사용)")

    # ─── Phase 2: Linguistic Layer ───
    results_path = data_dir / 'analysis-results.json'
    if not results_path.exists():
        print(f"[ERROR] 분석 결과 파일 없음: {results_path}")
        sys.exit(1)

    with open(results_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    if not args.skip_linguistic:
        print(f"\n[Phase 2] Linguistic Layer 분석 ({len(results)}건)")
        enhanced_results = []
        linguistic_data = []

        valid_count = 0
        for i, result in enumerate(results):
            if result.get('content_class') not in ('A', 'B', 'C'):
                enhanced_results.append(result)
                continue

            # full_content가 없으면 원본에서 가져옴
            ling = linguistic_analyze(result, config)
            if ling:
                enhanced = apply_adjustments(result, ling)
                enhanced_results.append(enhanced)
                linguistic_data.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    **ling,
                })
                valid_count += 1
            else:
                enhanced_results.append(result)

            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{len(results)}건 처리...")

        print(f"  Linguistic 분석 완료: {valid_count}건")

        # Linguistic 결과 저장
        ling_path = data_dir / 'linguistic-results.json'
        with open(ling_path, 'w', encoding='utf-8') as f:
            json.dump(linguistic_data, f, ensure_ascii=False, indent=2)
        print(f"  저장: {ling_path}")

        # Enhanced 결과 저장
        enhanced_path = data_dir / 'analysis-results-enhanced.json'
        with open(enhanced_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_results, f, ensure_ascii=False, indent=2)
        print(f"  저장: {enhanced_path}")

        results = enhanced_results
    else:
        print("\n[Phase 2] Linguistic Layer 생략")

    # ─── Phase 3: 리포트 생성 ───
    print("\n[Phase 3] 리포트 생성")
    report_dir = PROJECT_ROOT / config['output']['reports_dir']
    report_dir.mkdir(parents=True, exist_ok=True)
    generate_summary_report(results, config, report_dir)

    # ─── 완료 요약 ───
    valid = [r for r in results if r.get('content_class') in ('A', 'B', 'C')]
    print(f"\n{'='*60}")
    print(f"파이프라인 완료!")
    print(f"  전체: {len(results)}건 → 유효: {len(valid)}건")
    if valid:
        avg_auth = sum(r.get('authenticity', 0) for r in valid) / len(valid)
        avg_lai = sum(r.get('LAI', 0) for r in valid) / len(valid)
        avg_eds = sum(r.get('EDS', 0) for r in valid) / len(valid)
        print(f"  Auth 평균: {avg_auth:.1f} / LAI 평균: {avg_lai:.1f} / EDS 평균: {avg_eds:.1f}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
