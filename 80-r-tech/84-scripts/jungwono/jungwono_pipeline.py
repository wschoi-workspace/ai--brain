"""
정원오 SNS 분석 파이프라인 v1.0
크롤링 → Sincerity Filter → 2-Layer → Linguistic Layer → 리포트

사용법:
  python jungwono_pipeline.py [--skip-crawl] [--skip-linguistic]
  python jungwono_pipeline.py --start-date 20260109 --end-date 20260409
"""

import json
import re
import sys
import math
from datetime import datetime
from pathlib import Path
from collections import Counter

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / '10-projects' / '27-jungwono-sns' / 'config.json'


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================
# Linguistic Layer: 로컬 regex 기반 분석
# ============================================================

def analyze_sensory(text, config):
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
    first_person = len(re.findall(r'나는|내가|저는|제가|난\s|전\s|나의|내\s', text))
    we_person = len(re.findall(r'우리|같이|함께|다같이|시민|주민', text))
    reader_directed = len(re.findall(r'여러분|당신|너희|분들|국민', text))

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
    indirect_neg = re.findall(r'나쁘진\s*않|별로\s*안|그렇게\s*좋진|막\s*그런|못할\s*것도', text)
    litotes = re.findall(r'안\s*나쁘|못할\s*것도\s*없|나쁘지\s*않', text)
    rhetorical = re.findall(r'안\s*\S+\s*수\s*있|어떻게\s*안|왜\s*안|도대체', text)
    conditional_rec = re.findall(r'된다면\s*(?:지지|찍|뽑|투표)|라면\s*(?:지지|응원)', text)
    implicit_comp = re.findall(r'다른\s*후보\S*\s*(?:다르|달리|비해|보다)|오세훈\S*\s*보다', text)

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
    reg_config = config.get('linguistic_layer', {}).get('register_patterns', {})

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
    sensory_norm = min(sensory['density'] / 10.0, 1.0)

    cert = certainty['certainty_ratio']
    if 20 <= cert <= 60:
        hedging_nat = 1.0
    elif cert < 20:
        hedging_nat = max(0, cert / 20)
    else:
        hedging_nat = max(0, 1 - (cert - 60) / 40)

    cons = register['consistency']
    if cons == 0:
        reg_var = 0.5
    else:
        reg_var = max(0, 1 - abs(cons - 75) / 25)
        reg_var = min(reg_var, 1.0)

    temporal_markers = ['오늘', '아까', '방금', '지금', '어제', '아까전', '최근', '요즘']
    has_temporal = any(m in text for m in temporal_markers)
    temporal = 1.0 if has_temporal else 0.0

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
    word_count = max(len(text.split()), 1)
    sentences = re.split(r'[.!?。]\s*', text)
    sent_count = max(len([s for s in sentences if len(s.strip()) > 5]), 1)

    metaphors = re.findall(r'처럼|같은|마치|느낌이|듯한|비슷한|연상|떠오르', text)
    metaphor_density = min(len(metaphors) / sent_count, 1.0)

    discourse_norm = min(discourse['discourse_score'] / 100, 1.0)

    qualifiers = re.findall(
        r'개인적으로|제 입장|내 생각|취향|주관적|솔직히|사실은|객관적으로|냉정히',
        text
    )
    qual_density = min(len(qualifiers) / sent_count, 1.0)

    details = re.findall(
        r'\d+[억만원건명%표석]|성동구|성수동|서울시|민주당|국민의힘|경선|투표|선거',
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
    auth_delta = 0
    clout_delta = 0
    freshness_delta = 0
    trust_delta = 0
    rql_upgrade = False
    sentiment_reclass = None

    if sensory['density'] > 3:
        auth_delta += 8

    if 5 <= function_words['first_person_ratio'] <= 15:
        auth_delta += 5

    cert = certainty['certainty_ratio']
    extreme_pos = existing_result.get('extreme_pos', 0)

    if 20 <= cert <= 60:
        auth_delta += 5
    elif cert > 80 and extreme_pos > 5:
        auth_delta -= 5

    temporal_markers = ['오늘', '아까', '방금', '지금', '어제', '최근', '요즘']
    text = existing_result.get('full_content', '') or ''
    if any(m in text for m in temporal_markers):
        freshness_delta += 5

    if register['template_suspect']:
        trust_delta -= 10

    if 60 <= register['consistency'] <= 85:
        auth_delta += 3

    if len(discourse.get('contrast_markers', [])) >= 2:
        auth_delta += 5

    if discourse['discourse_score'] >= 40:
        current_rql = existing_result.get('rql', '')
        if current_rql == 'Q3_경험형':
            rql_upgrade = True

    if pragmatics.get('sentiment_reclassification'):
        sentiment_reclass = pragmatics['sentiment_reclassification']

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
    adj = linguistic['psyche_adjustments']
    enhanced = dict(result)

    auth = enhanced.get('authenticity', 60) + adj['auth_delta']
    enhanced['authenticity'] = max(10, min(95, auth))
    enhanced['auth_delta'] = adj['auth_delta']

    clout = enhanced.get('clout', 40) + adj['clout_delta']
    enhanced['clout'] = max(10, min(95, clout))
    enhanced['clout_delta'] = adj['clout_delta']

    fresh = enhanced.get('freshness_index', 50) + adj['freshness_delta']
    enhanced['freshness_index'] = max(0, min(100, fresh))

    trust = enhanced.get('trust_score', 70) + adj['trust_delta']
    enhanced['trust_score'] = max(0, min(100, trust))

    if adj['rql_upgrade'] and enhanced.get('rql') == 'Q3_경험형':
        enhanced['rql'] = 'Q4_분석형(승격)'
        enhanced['rql_weight'] = 1.5

    if adj['sentiment_reclassify']:
        if adj['sentiment_reclassify'] == 'neutral→mixed':
            if enhanced.get('sentiment') == '중립':
                enhanced['sentiment'] = '혼합'
        elif adj['sentiment_reclassify'] == 'neutral→mixed(긍정기울)':
            if enhanced.get('sentiment') == '중립':
                enhanced['sentiment'] = '혼합'

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
# 메인 파이프라인
# ============================================================

def main():
    import argparse
    import subprocess

    parser = argparse.ArgumentParser(description='정원오 SNS 분석 파이프라인')
    parser.add_argument('--start-date', type=str, default='20260109')
    parser.add_argument('--end-date', type=str, default='20260409')
    parser.add_argument('--skip-crawl', action='store_true')
    parser.add_argument('--skip-linguistic', action='store_true')
    parser.add_argument('--data-dir', type=str, default=None)
    args = parser.parse_args()

    config = load_config()
    today = datetime.now().strftime('%Y-%m-%d')

    print("=" * 60)
    print(f"정원오 SNS 분석 파이프라인 v1.0 — {today}")
    print(f"기간: {args.start_date} ~ {args.end_date}")
    print("=" * 60)

    # Phase 1: 크롤링
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = PROJECT_ROOT / config['output']['data_dir'] / today

    if not args.skip_crawl:
        print("\n[Phase 1] 데이터 크롤링")
        crawl_script = SCRIPT_DIR / 'jungwono_crawl.py'
        result = subprocess.run(
            [sys.executable, str(crawl_script),
             '--start-date', args.start_date,
             '--end-date', args.end_date],
            cwd=str(SCRIPT_DIR),
            capture_output=False,
        )
        if result.returncode != 0:
            print("[ERROR] 크롤링 실패")
            sys.exit(1)
    else:
        print("\n[Phase 1] 크롤링 생략 (기존 데이터 사용)")

    # Phase 2: Linguistic Layer
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

            ling = linguistic_analyze(result, config)
            if ling:
                enhanced = apply_adjustments(result, ling)
                enhanced_results.append(enhanced)
                linguistic_data.append({
                    'title': result.get('title', ''),
                    'link': result.get('link', ''),
                    'stage': result.get('stage', ''),
                    **ling,
                })
                valid_count += 1
            else:
                enhanced_results.append(result)

            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{len(results)}건 처리...")

        print(f"  Linguistic 분석 완료: {valid_count}건")

        ling_path = data_dir / 'linguistic-results.json'
        with open(ling_path, 'w', encoding='utf-8') as f:
            json.dump(linguistic_data, f, ensure_ascii=False, indent=2)

        enhanced_path = data_dir / 'analysis-results-enhanced.json'
        with open(enhanced_path, 'w', encoding='utf-8') as f:
            json.dump(enhanced_results, f, ensure_ascii=False, indent=2)
        print(f"  저장: {enhanced_path}")

        results = enhanced_results
    else:
        print("\n[Phase 2] Linguistic Layer 생략")

    # Phase 3: 완료 요약
    valid = [r for r in results if r.get('content_class') in ('A', 'B', 'C')]
    stages = config.get('analysis', {}).get('stages', {})

    print(f"\n{'='*60}")
    print(f"=== 정원오 SNS Mention Analysis ===")
    print(f"전체: {len(results)}건 → 유효 A+B+C: {len(valid)}건 (유효율 {len(valid)/max(len(results),1)*100:.0f}%)")

    if valid:
        avg_auth_raw = sum(r.get('authenticity', 0) - r.get('auth_delta', 0) for r in valid) / len(valid)
        avg_auth = sum(r.get('authenticity', 0) for r in valid) / len(valid)
        avg_lai = sum(r.get('LAI', 0) for r in valid) / len(valid)
        avg_eds = sum(r.get('EDS', 0) for r in valid) / len(valid)
        avg_clout = sum(r.get('clout', 0) for r in valid) / len(valid)
        avg_fresh = sum(r.get('freshness_index', 0) for r in valid) / len(valid)

        print(f"\n[기존 RXR]  Auth {avg_auth_raw:.1f} / Clout {avg_clout:.1f} / Freshness {avg_fresh:.1f}")
        print(f"[+ Linguistic] Auth {avg_auth:.1f} (+{avg_auth - avg_auth_raw:.1f}) / LAI {avg_lai:.1f} / EDS {avg_eds:.1f}")

        sent_dist = Counter(r.get('sentiment', '중립') for r in valid)
        total_valid = len(valid)
        print(f"\n감성: 긍정 {sent_dist.get('긍정',0)/total_valid*100:.0f}% / 혼합 {sent_dist.get('혼합',0)/total_valid*100:.0f}% / 중립 {sent_dist.get('중립',0)/total_valid*100:.0f}% / 부정 {sent_dist.get('부정',0)/total_valid*100:.0f}%")

        rql_upgraded = sum(1 for r in valid if r.get('rql', '').endswith('(승격)'))
        print(f"RQL 승격: {rql_upgraded}건 (Q3→Q4)")

        reg_dist = Counter(r.get('register_dominant', '판별불가') for r in valid if r.get('register_dominant'))
        if reg_dist:
            total_reg = sum(reg_dist.values())
            print(f"문체: " + " / ".join(f"{k} {v/total_reg*100:.0f}%" for k, v in reg_dist.most_common()))

        flagged = sum(1 for r in valid if r.get('linguistic_flag'))
        print(f"LAI-Auth 괴리 플래그: {flagged}건")

        # Stage별 요약
        for stage_key in sorted(stages.keys()):
            stage_info = stages[stage_key]
            stage_posts = [r for r in valid if r.get('stage') == stage_key]
            if not stage_posts:
                continue
            s_sent = Counter(r.get('sentiment', '중립') for r in stage_posts)
            s_stance = Counter(r.get('stance', '관찰') for r in stage_posts)
            s_auth = sum(r.get('authenticity', 0) for r in stage_posts) / len(stage_posts)
            s_lai = sum(r.get('LAI', 0) for r in stage_posts) / len(stage_posts)
            print(f"\n  [{stage_info['name']}] {len(stage_posts)}건 | 긍정 {s_sent.get('긍정',0)/len(stage_posts)*100:.0f}% 부정 {s_sent.get('부정',0)/len(stage_posts)*100:.0f}% | Auth {s_auth:.0f} LAI {s_lai:.0f} | Stance: {dict(s_stance)}")

    print(f"\n{'='*60}")


if __name__ == '__main__':
    main()
