"""
정원오 SNS 멘션 크롤러 v1.0
네이버 블로그 검색 API → 본문 크롤링 → 3-Stage 분류 → Sincerity Filter → 2-Layer

사용법:
  python jungwono_crawl.py [--start-date 20260109] [--end-date 20260409]

필요 환경변수 (.env):
  NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
"""

import json
import re
import sys
import os
import html
import time
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent
CONFIG_PATH = PROJECT_ROOT / '10-projects' / '27-jungwono-sns' / 'config.json'
ENV_PATH = PROJECT_ROOT / '.env'


def load_env(env_path):
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env[key.strip()] = val.strip()
    return env


def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================
# 네이버 검색 API
# ============================================================
def naver_blog_search(query, client_id, client_secret, display=100, start=1, sort='sim'):
    url = 'https://openapi.naver.com/v1/search/blog.json'
    params = urllib.parse.urlencode({
        'query': query,
        'display': display,
        'start': start,
        'sort': sort,
    })
    req = urllib.request.Request(f'{url}?{params}', headers={
        'X-Naver-Client-Id': client_id,
        'X-Naver-Client-Secret': client_secret,
    })
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"  [ERROR] API 호출 실패: {e}")
        return {'items': []}


def crawl_naver_blogs(queries, client_id, client_secret, config):
    crawl_config = config.get('crawl', {}).get('naver', {})
    display = crawl_config.get('display', 100)
    max_start = crawl_config.get('max_start', 901)
    delay = crawl_config.get('delay_seconds', 0.3)

    all_posts = {}

    for query in queries:
        for sort_mode in ['sim', 'date']:
            print(f"  검색: '{query}' (sort={sort_mode})")
            for start in range(1, max_start + 1, display):
                result = naver_blog_search(
                    query, client_id, client_secret,
                    display=display, start=start, sort=sort_mode
                )
                items = result.get('items', [])
                if not items:
                    break

                for item in items:
                    link = item.get('link', '')
                    if link and link not in all_posts:
                        all_posts[link] = item

                time.sleep(delay)

                if len(items) < display:
                    break

            print(f"    → 누적: {len(all_posts)}건")

    return list(all_posts.values())


# ============================================================
# 날짜 필터 (기간 지정 가능)
# ============================================================
def filter_by_date_range(posts, start_date, end_date):
    """지정 기간 내 포스트 필터"""
    filtered = []
    for post in posts:
        postdate = post.get('postdate', '')
        if postdate and start_date <= postdate <= end_date:
            filtered.append(post)
    return filtered


def assign_stage(postdate, config):
    """포스트를 3-Stage에 할당"""
    stages = config.get('analysis', {}).get('stages', {})
    for stage_key, stage_info in stages.items():
        if stage_info['start'] <= postdate <= stage_info['end']:
            return stage_key, stage_info['name']
    return 'unknown', '기간외'


# ============================================================
# 관련성 필터
# ============================================================
def filter_by_relevance(posts, config):
    brand_name = config['brand']['name']
    aliases = config['brand'].get('aliases', [])
    noise = config['search'].get('noise_exclusion', [])

    all_keywords = [brand_name] + aliases
    filtered = []

    for post in posts:
        title = re.sub(r'<[^>]+>', '', post.get('title', '')).lower()
        desc = re.sub(r'<[^>]+>', '', post.get('description', '')).lower()
        text = title + ' ' + desc

        has_brand = any(kw.lower() in text for kw in all_keywords)
        if not has_brand:
            continue

        is_noise = any(n.lower() in text for n in noise)
        if is_noise:
            continue

        filtered.append(post)

    return filtered


# ============================================================
# 본문 크롤링
# ============================================================
def fetch_blog_content(url, max_len=5000):
    try:
        if 'blog.naver.com' in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
        })
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('utf-8', errors='ignore')

        patterns = [
            r'class="se-main-container">(.*?)</div>\s*</div>\s*</div>',
            r'class="post[_-]?view.*?">(.*?)</div>\s*(?:</div>){2,}',
            r'class="se-component se-text.*?">(.*?)</div>',
            r'<div class="content">(.*?)</div>',
        ]

        text = ''
        for pat in patterns:
            matches = re.findall(pat, raw, re.DOTALL)
            if matches:
                combined = ' '.join(matches)
                text = re.sub(r'<[^>]+>', ' ', combined)
                text = html.unescape(text)
                text = re.sub(r'\s+', ' ', text).strip()
                if len(text) > 100:
                    break

        if not text or len(text) < 50:
            match = re.search(r'<body.*?>(.*?)</body>', raw, re.DOTALL)
            if match:
                text = re.sub(r'<script.*?</script>', '', match.group(1), flags=re.DOTALL)
                text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
                text = re.sub(r'<[^>]+>', ' ', text)
                text = html.unescape(text)
                text = re.sub(r'\s+', ' ', text).strip()

        return text[:max_len]
    except Exception:
        return ''


def crawl_full_content(posts, delay=0.3):
    crawled = 0
    for i, post in enumerate(posts):
        content = fetch_blog_content(post.get('link', ''))
        post['full_content'] = content
        if content and len(content) > 100:
            crawled += 1
        time.sleep(delay)
        if (i + 1) % 10 == 0:
            print(f"  본문 크롤링: {i+1}/{len(posts)}건 (확보: {crawled}건)")

    print(f"  본문 크롤링 완료: {crawled}/{len(posts)}건 확보")
    return posts


# ============================================================
# Content Class 분류 (정치인 버전)
# ============================================================
def classify_content_class(post, config):
    text = post.get('full_content', '') or ''
    title = re.sub(r'<[^>]+>', '', post.get('title', ''))
    full_text = (title + ' ' + text).lower()

    analysis = config.get('analysis', {})
    sponsored_markers = analysis.get('sponsored_markers', [])
    experience_signals = analysis.get('experience_signals', [])
    detail_signals = analysis.get('detail_signals', [])

    exp_count = sum(1 for w in experience_signals if w in full_text)
    detail_count = sum(1 for w in detail_signals if w in full_text)
    is_sponsored = any(m in full_text for m in sponsored_markers)

    brand_name = config['brand']['name'].lower()
    aliases = [a.lower() for a in config['brand'].get('aliases', [])]
    has_brand = brand_name in full_text or any(a in full_text for a in aliases)

    if not has_brand:
        return 'G', 'OFF_TOPIC'

    # 나열형 정보
    listing_markers = ['총정리', '리스트', '모음', 'best', 'top', '프로필', '나무위키', '학력', '이력']
    if any(m in title.lower() for m in listing_markers):
        return 'D', 'LISTING'

    # 리그램/단순공유
    regram_markers = ['리그램', '퍼옴', 'repost', '공유합니다']
    non_hash_text = re.sub(r'#\S+', '', full_text).strip()
    if any(m in full_text for m in regram_markers) or len(non_hash_text) < 30:
        return 'E', 'REGRAM'

    # 보도자료/뉴스 전재
    press_phrases = ['보도자료', '관계자는', '밝혔다', '라고 전했다', '공식 발표', '기자', '특파원', '뉴스']
    press_count = sum(1 for p in press_phrases if p in full_text)
    if press_count >= 3:
        return 'F', 'PRESS_COPY'

    # 정치광고/선거광고
    if is_sponsored:
        return 'C', 'SPONSORED'

    # 진성 의견 vs 일반 포스트
    if exp_count >= 2 and detail_count >= 3:
        return 'A', 'AUTHENTIC'
    else:
        return 'B', 'GENERAL'


# ============================================================
# Trust Score
# ============================================================
def calculate_trust_score(post, content_class, flag, config):
    score = 100
    text = post.get('full_content', '') or ''
    full_text = (re.sub(r'<[^>]+>', '', post.get('title', '')) + ' ' + text).lower()

    analysis = config.get('analysis', {})
    experience_signals = analysis.get('experience_signals', [])
    detail_signals = analysis.get('detail_signals', [])

    flag_penalties = {
        'REGRAM': -30, 'PRESS_COPY': -35, 'BIZ_SUSPECT': -25,
        'LISTING': -20, 'SPONSORED': -15, 'OFF_TOPIC': -30,
    }
    score += flag_penalties.get(flag, 0)

    if len(full_text) < 20:
        score -= 20

    exp_count = sum(1 for w in experience_signals if w in full_text)
    detail_count = sum(1 for w in detail_signals if w in full_text)

    if exp_count >= 2:
        score += 15
    if detail_count >= 3:
        score += 10

    return max(0, min(100, score))


# ============================================================
# 호칭 분석 (정치인 특화)
# ============================================================
def analyze_appellation(post, config):
    """호칭 변화 분석 — 심리적 거리두기 지표"""
    text = post.get('full_content', '') or ''
    title = re.sub(r'<[^>]+>', '', post.get('title', ''))
    full_text = title + ' ' + text

    tracking = config.get('analysis', {}).get('appellation_tracking', {})
    found = {}

    for category, patterns in tracking.items():
        count = 0
        for pat in patterns:
            count += len(re.findall(re.escape(pat), full_text))
        if count > 0:
            found[category] = count

    # 지배적 호칭 결정
    if found:
        dominant = max(found, key=found.get)
    else:
        dominant = 'unknown'

    return {
        'appellation_counts': found,
        'dominant_appellation': dominant,
    }


# ============================================================
# Stance 분류 (정치인 특화)
# ============================================================
def classify_stance(post, config):
    """지지/양가/관찰/비판 stance 분류"""
    text = post.get('full_content', '') or ''
    full_lower = text.lower()

    stance_markers = config.get('linguistic_layer', {}).get('political_stance_markers', {})
    support_words = stance_markers.get('support', [])
    ambivalent_words = stance_markers.get('ambivalent', [])
    critical_words = stance_markers.get('critical', [])

    sup_count = sum(1 for w in support_words if w in full_lower)
    amb_count = sum(1 for w in ambivalent_words if w in full_lower)
    crit_count = sum(1 for w in critical_words if w in full_lower)

    total = sup_count + amb_count + crit_count
    if total == 0:
        return '관찰'

    if sup_count > crit_count + amb_count:
        return '지지'
    elif crit_count > sup_count:
        return '비판'
    elif amb_count >= sup_count and amb_count >= crit_count:
        return '양가'
    elif sup_count > 0 and crit_count > 0:
        return '양가'
    else:
        return '관찰'


# ============================================================
# 2-Layer 분석 (정치인 버전)
# ============================================================
def analyze_2layer(post, config):
    text = post.get('full_content', '') or ''
    title = re.sub(r'<[^>]+>', '', post.get('title', ''))
    full_text = title + ' ' + text
    full_lower = full_text.lower()

    analysis = config.get('analysis', {})

    # --- Content Layer ---

    # 토픽 분석
    topic_scores = {}
    for topic, keywords in analysis.get('topics', {}).items():
        score = sum(full_lower.count(kw) for kw in keywords)
        if score > 0:
            topic_scores[topic] = score
    top_topics = sorted(topic_scores.items(), key=lambda x: -x[1])[:3]
    primary_topic = top_topics[0][0] if top_topics else '기타'

    # 감성 분석 (4-way)
    pos_words = analysis.get('sentiment', {}).get('positive', [])
    neg_words = analysis.get('sentiment', {}).get('negative', [])
    pos_count = sum(1 for w in pos_words if w in full_lower)
    neg_count = sum(1 for w in neg_words if w in full_lower)

    if pos_count > neg_count + 2:
        sentiment = '긍정'
    elif neg_count > pos_count:
        sentiment = '부정'
    elif pos_count > 0 and neg_count > 0:
        sentiment = '혼합'
    else:
        sentiment = '중립'

    # RQL
    word_count = len(full_text.split())
    detail_signals = analysis.get('detail_signals', [])
    exp_signals = analysis.get('experience_signals', [])
    has_detail = sum(1 for w in detail_signals if w in full_lower)
    has_personal = sum(1 for w in exp_signals if w in full_lower)

    if word_count > 500 and has_detail >= 3 and has_personal >= 1:
        rql = 'Q5_서사형'
        rql_weight = 2.0
    elif word_count > 300 and has_detail >= 2:
        rql = 'Q4_분석형'
        rql_weight = 1.5
    elif word_count > 150 and (has_detail >= 1 or has_personal >= 1):
        rql = 'Q3_경험형'
        rql_weight = 1.0
    elif word_count > 50:
        rql = 'Q2_감상형'
        rql_weight = 0.5
    else:
        rql = 'Q1_간단형'
        rql_weight = 0.2

    # --- Psyche Layer ---

    first_person = len(re.findall(r'나는|내가|저는|제가|난\s|전\s', full_text))
    we_person = len(re.findall(r'우리|같이|함께|다같이|시민|주민', full_text))

    iga_count = len(re.findall(r'[가-힣]이\s|[가-힣]가\s', full_text))
    eunneun_count = len(re.findall(r'[가-힣]은\s|[가-힣]는\s', full_text))
    total_particles = iga_count + eunneun_count
    freshness = round(iga_count / max(total_particles, 1) * 100, 1)

    all_sentiment_words = pos_words + neg_words
    emotion_words_found = [w for w in all_sentiment_words if w in full_lower]
    emotion_diversity = len(set(emotion_words_found))

    extreme_pos_words = ['진짜', '너무너무', '완전', '대박', '미쳤', '최고의', '인생']
    extreme_pos = sum(full_lower.count(w) for w in extreme_pos_words)
    exclamation = full_text.count('!') + full_text.count('ㅋㅋ')

    sponsored_markers = analysis.get('sponsored_markers', [])
    is_sponsored = any(m in full_lower for m in sponsored_markers)

    # Authenticity
    auth_score = 60
    if is_sponsored:
        auth_score -= 15
    if extreme_pos > 5:
        auth_score -= (extreme_pos - 5) * 3
    if exclamation > 10:
        auth_score -= (exclamation - 10) * 2
    if has_personal >= 2:
        auth_score += 10
    if has_detail >= 3:
        auth_score += 10
    if neg_count > 0 and pos_count > 0:
        auth_score += 15
    auth_score = max(10, min(95, auth_score))

    # Clout
    clout_score = 40
    recommend_words = ['지지', '응원', '투표', '찍겠', '뽑겠', '밀어', '파이팅']
    rec_count = sum(1 for w in recommend_words if w in full_lower)
    if rec_count > 0:
        clout_score += rec_count * 12
    if we_person > first_person:
        clout_score += 10
    conditional_rec = len(re.findall(r'된다면\s*(지지|찍|뽑|투표)', full_text))
    if conditional_rec > 0:
        clout_score += 10
    clout_score = max(10, min(95, clout_score))

    # 호칭 + Stance (정치인 특화)
    appellation = analyze_appellation(post, config)
    stance = classify_stance(post, config)

    return {
        'word_count': word_count,
        'primary_topic': primary_topic,
        'topic_scores': dict(top_topics),
        'sentiment': sentiment,
        'pos_count': pos_count,
        'neg_count': neg_count,
        'rql': rql,
        'rql_weight': rql_weight,
        'is_sponsored': is_sponsored,
        'first_person': first_person,
        'we_person': we_person,
        'iga_count': iga_count,
        'eunneun_count': eunneun_count,
        'freshness_index': freshness,
        'emotion_diversity': emotion_diversity,
        'authenticity': auth_score,
        'clout': clout_score,
        'extreme_pos': extreme_pos,
        'exclamation': exclamation,
        'stance': stance,
        'dominant_appellation': appellation['dominant_appellation'],
        'appellation_counts': appellation['appellation_counts'],
    }


# ============================================================
# 통계 출력 (3-Stage)
# ============================================================
def print_statistics(results, config):
    if not results:
        print("분석 결과가 없습니다.")
        return

    print(f"\n총 분석 건수: {len(results)}건")

    # Content Class 분포
    print("\n--- Content Class 분포 ---")
    class_dist = Counter(r['content_class'] for r in results)
    for cls in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        c = class_dist.get(cls, 0)
        bar = '█' * min(c, 50)
        print(f"  {cls}: {bar} {c}건")

    # 유효 분석 대상 (A+B+C)
    valid = [r for r in results if r['content_class'] in ('A', 'B', 'C')]
    print(f"\n유효 분석 대상 (A+B+C): {len(valid)}건")

    if not valid:
        return

    # Stage별 분석
    stages = config.get('analysis', {}).get('stages', {})
    for stage_key in sorted(stages.keys()):
        stage_info = stages[stage_key]
        stage_posts = [r for r in valid if r.get('stage') == stage_key]
        if not stage_posts:
            continue

        print(f"\n=== {stage_info['name']} ({stage_key}) — {len(stage_posts)}건 ===")

        # 감성
        sent_dist = Counter(r.get('sentiment', '중립') for r in stage_posts)
        for s in ['긍정', '혼합', '중립', '부정']:
            c = sent_dist.get(s, 0)
            pct = c / len(stage_posts) * 100
            print(f"  {s}: {c}건 ({pct:.0f}%)")

        # Stance
        stance_dist = Counter(r.get('stance', '관찰') for r in stage_posts)
        print(f"  Stance: {dict(stance_dist)}")

        # 토픽
        topic_dist = Counter(r.get('primary_topic', '기타') for r in stage_posts)
        print(f"  토픽: {dict(topic_dist.most_common(3))}")

        # Psyche 평균
        avg_auth = sum(r.get('authenticity', 0) for r in stage_posts) / len(stage_posts)
        avg_clout = sum(r.get('clout', 0) for r in stage_posts) / len(stage_posts)
        print(f"  Auth: {avg_auth:.1f} / Clout: {avg_clout:.1f}")


# ============================================================
# 메인
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description='정원오 SNS 멘션 크롤러')
    parser.add_argument('--start-date', type=str, default='20260109', help='시작일 (YYYYMMDD)')
    parser.add_argument('--end-date', type=str, default='20260409', help='종료일 (YYYYMMDD)')
    parser.add_argument('--skip-content', action='store_true', help='본문 크롤링 생략')
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    config = load_config(CONFIG_PATH)

    client_id = env.get('NAVER_CLIENT_ID')
    client_secret = env.get('NAVER_CLIENT_SECRET')
    if not client_id or not client_secret:
        print("[ERROR] .env에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 필요")
        sys.exit(1)

    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = PROJECT_ROOT / config['output']['data_dir'] / today
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"정원오 SNS 멘션 크롤러 v1.0 — {today}")
    print(f"기간: {args.start_date} ~ {args.end_date}")
    print("=" * 60)

    # STEP 1: 검색
    print("\n[STEP 1] 네이버 블로그 검색")
    queries = config['search']['queries']
    raw_posts = crawl_naver_blogs(queries, client_id, client_secret, config)
    print(f"  총 수집: {len(raw_posts)}건 (중복 제거 후)")

    # STEP 2: 필터링
    print("\n[STEP 2] 필터링")
    date_filtered = filter_by_date_range(raw_posts, args.start_date, args.end_date)
    print(f"  날짜 필터 ({args.start_date}~{args.end_date}): {len(date_filtered)}건")

    relevance_filtered = filter_by_relevance(date_filtered, config)
    print(f"  관련성 필터: {len(relevance_filtered)}건")

    # Stage 할당
    for post in relevance_filtered:
        stage_key, stage_name = assign_stage(post.get('postdate', ''), config)
        post['stage'] = stage_key
        post['stage_name'] = stage_name

    stage_dist = Counter(p['stage'] for p in relevance_filtered)
    print(f"  Stage 분포: {dict(stage_dist)}")

    # 원본 저장
    raw_path = output_dir / 'naver-raw.json'
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(relevance_filtered, f, ensure_ascii=False, indent=2)
    print(f"  저장: {raw_path}")

    # STEP 3: 본문 크롤링
    if not args.skip_content:
        print(f"\n[STEP 3] 본문 크롤링 ({len(relevance_filtered)}건)")
        crawl_full_content(relevance_filtered,
                          delay=config['crawl']['naver']['delay_seconds'])

        enriched_path = output_dir / 'naver-enriched.json'
        with open(enriched_path, 'w', encoding='utf-8') as f:
            json.dump(relevance_filtered, f, ensure_ascii=False, indent=2)
        print(f"  본문 포함 데이터 저장: {enriched_path}")

    # STEP 4: Sincerity Filter + 2-Layer
    print("\n[STEP 4] Sincerity Filter + 2-Layer 분석")
    results = []
    for post in relevance_filtered:
        content_class, flag = classify_content_class(post, config)
        trust_score = calculate_trust_score(post, content_class, flag, config)

        result = {
            'date': post.get('postdate', ''),
            'title': re.sub(r'<[^>]+>', '', post.get('title', '')),
            'blogger': post.get('bloggername', ''),
            'link': post.get('link', ''),
            'full_content': post.get('full_content', ''),
            'content_class': content_class,
            'content_flag': flag,
            'trust_score': trust_score,
            'stage': post.get('stage', ''),
            'stage_name': post.get('stage_name', ''),
        }

        if content_class in ('A', 'B', 'C'):
            layer_result = analyze_2layer(post, config)
            result.update(layer_result)

        results.append(result)

    # STEP 5: 통계
    print("\n[STEP 5] 분석 결과 통계")
    print_statistics(results, config)

    # STEP 6: 저장
    results_path = output_dir / 'analysis-results.json'
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {results_path}")

    # 요약
    valid = [r for r in results if r.get('content_class') in ('A', 'B', 'C')]
    summary = {
        'date': today,
        'period': f"{args.start_date}~{args.end_date}",
        'total_crawled': len(raw_posts),
        'after_filter': len(relevance_filtered),
        'content_class_dist': dict(Counter(r['content_class'] for r in results)),
        'valid_count': len(valid),
        'stage_dist': dict(Counter(r.get('stage', '') for r in valid)),
        'sentiment_dist': dict(Counter(r.get('sentiment', '중립') for r in valid)) if valid else {},
        'stance_dist': dict(Counter(r.get('stance', '관찰') for r in valid)) if valid else {},
        'avg_authenticity': round(sum(r.get('authenticity', 0) for r in valid) / max(len(valid), 1), 1),
        'avg_clout': round(sum(r.get('clout', 0) for r in valid) / max(len(valid), 1), 1),
        'avg_freshness': round(sum(r.get('freshness_index', 0) for r in valid) / max(len(valid), 1), 1),
    }
    summary_path = output_dir / 'summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"완료! 유효 분석 대상: {len(valid)}건 / 전체 {len(results)}건")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
