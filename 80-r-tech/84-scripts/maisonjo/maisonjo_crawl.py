"""
메종조 SNS 크롤러 v1.0
네이버 블로그 검색 API → 본문 크롤링 → 관련성 필터링 → JSON 저장

사용법:
  python maisonjo_crawl.py [--days 90] [--output data/2026-06-07]

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

# UTF-8 출력
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

# ============================================================
# 경로 설정
# ============================================================
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent  # do-better-workspace
CONFIG_PATH = PROJECT_ROOT / '10-projects' / '29-maisonjo-sns' / 'config.json'
ENV_PATH = PROJECT_ROOT / '.env'


def load_env(env_path):
    """간단한 .env 파서"""
    env = {}
    if env_path.exists():
        for line in env_path.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                env[key.strip()] = val.strip()
    return env


def load_config(config_path):
    """config.json 로드"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================
# 네이버 검색 API
# ============================================================
def naver_blog_search(query, client_id, client_secret, display=100, start=1, sort='sim'):
    """네이버 블로그 검색 API 호출"""
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
    """전체 키워드에 대해 네이버 블로그 크롤링"""
    crawl_config = config.get('crawl', {}).get('naver', {})
    display = crawl_config.get('display', 100)
    max_start = crawl_config.get('max_start', 901)
    delay = crawl_config.get('delay_seconds', 0.3)

    all_posts = {}  # link를 키로 중복 제거

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

                # 더 이상 결과가 없으면 중단
                if len(items) < display:
                    break

            print(f"    → 누적: {len(all_posts)}건")

    return list(all_posts.values())


# ============================================================
# 날짜 필터
# ============================================================
def filter_by_date(posts, days_back=30):
    """최근 N일 이내 포스트만 필터"""
    cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
    filtered = []
    for post in posts:
        postdate = post.get('postdate', '')
        if postdate >= cutoff:
            filtered.append(post)
    return filtered


# ============================================================
# 관련성 필터
# ============================================================
def filter_by_relevance(posts, config):
    """브랜드 관련 포스트만 필터"""
    brand_name = config['brand']['name']
    aliases = config['brand'].get('aliases', [])
    noise = config['search'].get('noise_exclusion', [])

    all_keywords = [brand_name] + aliases
    filtered = []

    for post in posts:
        title = re.sub(r'<[^>]+>', '', post.get('title', '')).lower()
        desc = re.sub(r'<[^>]+>', '', post.get('description', '')).lower()
        text = title + ' ' + desc

        # 브랜드 키워드 포함 여부
        has_brand = any(kw.lower() in text for kw in all_keywords)
        if not has_brand:
            continue

        # 노이즈 제외
        is_noise = any(n.lower() in text for n in noise)
        if is_noise:
            continue

        filtered.append(post)

    return filtered


# ============================================================
# 본문 크롤링 (기존 rxr_2layer_analysis.py 로직 재활용)
# ============================================================
def fetch_blog_content(url, max_len=5000):
    """네이버 블로그 모바일 버전에서 본문 텍스트 추출"""
    try:
        if 'blog.naver.com' in url:
            url = url.replace('blog.naver.com', 'm.blog.naver.com')
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)'
        })
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('utf-8', errors='ignore')

        # 본문 추출 패턴 (스마트에디터 → 구형 에디터 → 범용 순)
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
            # 최후 수단: body 전체에서 추출
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
    """전체 포스트 본문 크롤링"""
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
# Content Class 분류 (Sincerity Filter 1차)
# ============================================================
def classify_content_class(post, config):
    """Content Class A~G 분류"""
    text = post.get('full_content', '') or ''
    title = re.sub(r'<[^>]+>', '', post.get('title', ''))
    full_text = (title + ' ' + text).lower()

    analysis = config.get('analysis', {})
    sponsored_markers = analysis.get('sponsored_markers', [])
    experience_signals = analysis.get('experience_signals', [])
    detail_signals = analysis.get('detail_signals', [])

    # 각 신호 카운트
    exp_count = sum(1 for w in experience_signals if w in full_text)
    detail_count = sum(1 for w in detail_signals if w in full_text)
    is_sponsored = any(m in full_text for m in sponsored_markers)

    # 노이즈 체크: 브랜드 키워드 미포함
    brand_name = config['brand']['name'].lower()
    aliases = [a.lower() for a in config['brand'].get('aliases', [])]
    has_brand = brand_name in full_text or any(a in full_text for a in aliases)

    if not has_brand:
        return 'G', 'OFF_TOPIC'

    # 나열형 정보
    listing_markers = ['총정리', '리스트', '모음', 'best', 'top']
    if any(m in title.lower() for m in listing_markers):
        return 'D', 'LISTING'

    # 리그램/단순공유
    regram_markers = ['리그램', '퍼옴', 'repost']
    non_hash_text = re.sub(r'#\S+', '', full_text).strip()
    if any(m in full_text for m in regram_markers) or len(non_hash_text) < 30:
        return 'E', 'REGRAM'

    # 보도자료
    press_phrases = ['보도자료', '출시', '관계자는', '밝혔다', '라고 전했다', '공식 발표']
    press_count = sum(1 for p in press_phrases if p in full_text)
    if press_count >= 3:
        return 'F', 'PRESS_COPY'

    # 비즈니스
    biz_markers = ['공식', '판매처', '구매링크', '할인코드', '쿠폰']
    biz_count = sum(1 for m in biz_markers if m in full_text)
    if biz_count >= 2:
        return 'F', 'BIZ_SUSPECT'

    # 협찬
    if is_sponsored:
        return 'C', 'SPONSORED'

    # 진성후기 vs 일반포스트
    if exp_count >= 2 and detail_count >= 3:
        return 'A', 'AUTHENTIC'
    else:
        return 'B', 'GENERAL'


# ============================================================
# Trust Score 산출
# ============================================================
def calculate_trust_score(post, content_class, flag, config):
    """Trust Score 0~100 산출"""
    score = 100
    text = post.get('full_content', '') or ''
    full_text = (re.sub(r'<[^>]+>', '', post.get('title', '')) + ' ' + text).lower()

    analysis = config.get('analysis', {})
    experience_signals = analysis.get('experience_signals', [])
    detail_signals = analysis.get('detail_signals', [])

    # 감점
    flag_penalties = {
        'REGRAM': -30, 'PRESS_COPY': -35, 'BIZ_SUSPECT': -25,
        'LISTING': -20, 'SPONSORED': -15, 'OFF_TOPIC': -30,
    }
    score += flag_penalties.get(flag, 0)

    if len(full_text) < 20:
        score -= 20  # TOO_SHORT

    # 가점
    exp_count = sum(1 for w in experience_signals if w in full_text)
    detail_count = sum(1 for w in detail_signals if w in full_text)

    if exp_count >= 2:
        score += 15  # PERSONAL_EXP
    if detail_count >= 3:
        score += 10  # DETAILED

    return max(0, min(100, score))


# ============================================================
# 2-Layer 분석 (Content Layer + Psyche Layer)
# ============================================================
def analyze_2layer(post, config):
    """Content Layer + Psyche Layer 분석"""
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

    # RQL (Review Quality Level)
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

    # 대명사 패턴
    first_person = len(re.findall(r'나는|내가|저는|제가|난\s|전\s', full_text))
    we_person = len(re.findall(r'우리|같이|함께|다같이', full_text))

    # 조사 패턴 → Freshness Index (CLT 기반)
    iga_count = len(re.findall(r'[가-힣]이\s|[가-힣]가\s', full_text))
    eunneun_count = len(re.findall(r'[가-힣]은\s|[가-힣]는\s', full_text))
    total_particles = iga_count + eunneun_count
    freshness = round(iga_count / max(total_particles, 1) * 100, 1)

    # 감정어 다양성
    all_sentiment_words = pos_words + neg_words
    emotion_words_found = [w for w in all_sentiment_words if w in full_lower]
    emotion_diversity = len(set(emotion_words_found))

    # 과잉 표현 감지
    extreme_pos_words = ['진짜', '너무너무', '완전', '대박', '미쳤', '최고의', '인생']
    extreme_pos = sum(full_lower.count(w) for w in extreme_pos_words)
    exclamation = full_text.count('!') + full_text.count('ㅋㅋ')

    # 협찬 감지
    sponsored_markers = analysis.get('sponsored_markers', [])
    is_sponsored = any(m in full_lower for m in sponsored_markers)

    # Authenticity (0~100)
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
        auth_score += 15  # ELM 중심경로 신호
    auth_score = max(10, min(95, auth_score))

    # Clout (0~100)
    clout_score = 40
    recommend_words = ['추천', '꼭', '강추', '가보세요', '사세요', '놓치지', '꼭 사']
    rec_count = sum(1 for w in recommend_words if w in full_lower)
    if rec_count > 0:
        clout_score += rec_count * 15
    if we_person > first_person:
        clout_score += 10
    # 조건부 추천
    conditional_rec = len(re.findall(r'라면\s*(추천|강추|좋)', full_text))
    if conditional_rec > 0:
        clout_score += 10
    # 예방 초점 추천 (손실 회피)
    prevention_rec = sum(1 for w in ['안 사면 후회', '놓치면', '없어지기 전'] if w in full_lower)
    if prevention_rec > 0:
        clout_score += 8
    clout_score = max(10, min(95, clout_score))

    return {
        'word_count': word_count,
        # Content Layer
        'primary_topic': primary_topic,
        'topic_scores': dict(top_topics),
        'sentiment': sentiment,
        'pos_count': pos_count,
        'neg_count': neg_count,
        'rql': rql,
        'rql_weight': rql_weight,
        'is_sponsored': is_sponsored,
        # Psyche Layer
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
    }


# ============================================================
# 통계 출력
# ============================================================
def print_statistics(results):
    """분석 결과 통계 출력"""
    if not results:
        print("분석 결과가 없습니다.")
        return

    print(f"\n총 분석 건수: {len(results)}건")

    # Content Class 분포
    print("\n--- Content Class 분포 ---")
    class_dist = Counter(r['content_class'] for r in results)
    for cls in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        c = class_dist.get(cls, 0)
        bar = '█' * c
        print(f"  {cls}: {bar} {c}건")

    # 유효 분석 대상 (A+B+C)
    valid = [r for r in results if r['content_class'] in ('A', 'B', 'C')]
    print(f"\n유효 분석 대상 (A+B+C): {len(valid)}건")

    if not valid:
        return

    # 토픽 분포
    print("\n--- 토픽 분포 ---")
    topic_dist = Counter(r.get('primary_topic', '기타') for r in valid)
    for t, c in topic_dist.most_common():
        bar = '█' * c
        print(f"  {t}: {bar} {c}건")

    # 감성 분포
    print("\n--- 감성 분포 ---")
    sent_dist = Counter(r.get('sentiment', '중립') for r in valid)
    for s in ['긍정', '혼합', '중립', '부정']:
        c = sent_dist.get(s, 0)
        pct = c / len(valid) * 100
        print(f"  {s}: {c}건 ({pct:.0f}%)")

    # RQL 분포
    print("\n--- RQL 분포 ---")
    rql_dist = Counter(r.get('rql', 'Q1_간단형') for r in valid)
    total_asset = sum(r.get('rql_weight', 0.2) for r in valid)
    for q in ['Q5_서사형', 'Q4_분석형', 'Q3_경험형', 'Q2_감상형', 'Q1_간단형']:
        c = rql_dist.get(q, 0)
        print(f"  {q}: {c}건")
    print(f"  리뷰 자산값: {total_asset:.1f} (평균 {total_asset/len(valid):.2f})")

    # Psyche Layer 평균
    print("\n--- Psyche Layer 평균 ---")
    avg_auth = sum(r.get('authenticity', 0) for r in valid) / len(valid)
    avg_clout = sum(r.get('clout', 0) for r in valid) / len(valid)
    avg_fresh = sum(r.get('freshness_index', 0) for r in valid) / len(valid)
    print(f"  Authenticity: {avg_auth:.1f}")
    print(f"  Clout: {avg_clout:.1f}")
    print(f"  Freshness Index: {avg_fresh:.1f}")

    # 협찬 vs 자발적
    print("\n--- 협찬 vs 자발적 ---")
    sponsored = [r for r in valid if r.get('is_sponsored')]
    organic = [r for r in valid if not r.get('is_sponsored')]
    print(f"  자발적: {len(organic)}건")
    print(f"  협찬: {len(sponsored)}건")
    if sponsored and organic:
        avg_s = sum(r['authenticity'] for r in sponsored) / len(sponsored)
        avg_o = sum(r['authenticity'] for r in organic) / len(organic)
        print(f"  자발적 Auth 평균: {avg_o:.1f} / 협찬 Auth 평균: {avg_s:.1f}")


# ============================================================
# 메인 실행
# ============================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description='메종조 SNS 크롤러')
    parser.add_argument('--days', type=int, default=30, help='크롤링 기간 (최근 N일)')
    parser.add_argument('--output', type=str, default=None, help='출력 디렉토리')
    parser.add_argument('--skip-content', action='store_true', help='본문 크롤링 생략')
    args = parser.parse_args()

    # 설정 로드
    env = load_env(ENV_PATH)
    config = load_config(CONFIG_PATH)

    client_id = env.get('NAVER_CLIENT_ID')
    client_secret = env.get('NAVER_CLIENT_SECRET')
    if not client_id or not client_secret:
        print("[ERROR] .env에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 필요")
        sys.exit(1)

    # 출력 경로
    today = datetime.now().strftime('%Y-%m-%d')
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = PROJECT_ROOT / config['output']['data_dir'] / today
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"메종조 SNS 크롤러 v1.0 — {today}")
    print(f"기간: 최근 {args.days}일")
    print("=" * 60)

    # STEP 1: 네이버 블로그 검색
    print("\n[STEP 1] 네이버 블로그 검색")
    queries = config['search']['queries']
    raw_posts = crawl_naver_blogs(queries, client_id, client_secret, config)
    print(f"  총 수집: {len(raw_posts)}건 (중복 제거 후)")

    # STEP 2: 날짜 + 관련성 필터
    print("\n[STEP 2] 필터링")
    date_filtered = filter_by_date(raw_posts, days_back=args.days)
    print(f"  날짜 필터 (최근 {args.days}일): {len(date_filtered)}건")

    relevance_filtered = filter_by_relevance(date_filtered, config)
    print(f"  관련성 필터: {len(relevance_filtered)}건")

    # 원본 저장
    raw_path = output_dir / 'naver-raw.json'
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(relevance_filtered, f, ensure_ascii=False, indent=2)
    print(f"  저장: {raw_path}")

    # STEP 3: 본문 크롤링
    if not args.skip_content:
        print(f"\n[STEP 3] 본문 크롤링 ({len(relevance_filtered)}건)")
        crawl_full_content(relevance_filtered, delay=config['crawl']['naver']['delay_seconds'])

        # 본문 포함 데이터 저장 (Linguistic Layer용)
        enriched_path = output_dir / 'naver-enriched.json'
        with open(enriched_path, 'w', encoding='utf-8') as f:
            json.dump(relevance_filtered, f, ensure_ascii=False, indent=2)
        print(f"  본문 포함 데이터 저장: {enriched_path}")

    # STEP 4: Content Class + Trust Score
    print("\n[STEP 4] Sincerity Filter (Content Class + Trust Score)")
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
        }

        # A+B+C만 2-Layer 분석
        if content_class in ('A', 'B', 'C'):
            layer_result = analyze_2layer(post, config)
            result.update(layer_result)

        results.append(result)

    # STEP 5: 통계
    print("\n[STEP 5] 분석 결과 통계")
    print_statistics(results)

    # STEP 6: 저장
    results_path = output_dir / 'analysis-results.json'
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {results_path}")

    # 요약 정보 저장
    valid = [r for r in results if r.get('content_class') in ('A', 'B', 'C')]
    summary = {
        'date': today,
        'total_crawled': len(raw_posts),
        'after_filter': len(relevance_filtered),
        'content_class_dist': dict(Counter(r['content_class'] for r in results)),
        'valid_count': len(valid),
        'sentiment_dist': dict(Counter(r.get('sentiment', '중립') for r in valid)) if valid else {},
        'avg_authenticity': round(sum(r.get('authenticity', 0) for r in valid) / max(len(valid), 1), 1),
        'avg_clout': round(sum(r.get('clout', 0) for r in valid) / max(len(valid), 1), 1),
        'avg_freshness': round(sum(r.get('freshness_index', 0) for r in valid) / max(len(valid), 1), 1),
    }
    summary_path = output_dir / 'summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"요약 저장: {summary_path}")

    print(f"\n{'='*60}")
    print(f"완료! 유효 분석 대상: {len(valid)}건 / 전체 {len(results)}건")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
