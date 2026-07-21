"""
차량 실내 공기질·냄새·공조 후기 크롤러 v1.0 (주제 기반 + 브랜드 태깅)
네이버 블로그 검색 API → 본문 크롤링 → 주제 관련성 필터 → 브랜드 태깅 → Sincerity Filter → 2-Layer → JSON

브랜드 SNS 크롤러(xylitol_crawl.py)를 주제(topic) 모드로 개조:
  - 관련성 필터: vehicle_keywords AND issue_keywords (브랜드명 대신 주제 매칭)
  - 브랜드 태깅: config.brands 기준으로 포스트별 브랜드 라벨 부여

사용법:
  python3 vehicle_cabin_crawl.py [--days 180] [--output data/2026-07-17] [--skip-content]

필요 환경변수 (.env): NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
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
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent  # do-better-workspace
CONFIG_PATH = PROJECT_ROOT / '10-projects' / '37-hyundai-rxr-cabin-air' / 'config.json'
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
        'query': query, 'display': display, 'start': start, 'sort': sort,
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
                result = naver_blog_search(query, client_id, client_secret,
                                           display=display, start=start, sort=sort_mode)
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


def filter_by_date(posts, days_back=180):
    cutoff = (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
    return [p for p in posts if p.get('postdate', '') >= cutoff]


# ============================================================
# 주제 관련성 필터 (vehicle AND issue)
# ============================================================
def is_topic_relevant(text, config):
    tr = config.get('topic_relevance', {})
    vehicle_kws = [k.lower() for k in tr.get('vehicle_keywords', [])]
    issue_kws = [k.lower() for k in tr.get('issue_keywords', [])]
    has_vehicle = any(k in text for k in vehicle_kws)
    has_issue = any(k in text for k in issue_kws)
    return has_vehicle and has_issue


def filter_by_relevance(posts, config, use_content=False):
    """주제 관련성 필터: 차량 키워드 AND 이슈 키워드. noise 제외."""
    noise = [n.lower() for n in config['search'].get('noise_exclusion', [])]
    filtered = []
    for post in posts:
        title = re.sub(r'<[^>]+>', '', post.get('title', '')).lower()
        desc = re.sub(r'<[^>]+>', '', post.get('description', '')).lower()
        content = (post.get('full_content', '') or '').lower() if use_content else ''
        text = title + ' ' + desc + ' ' + content

        if not is_topic_relevant(text, config):
            continue
        if any(n in text for n in noise):
            continue
        filtered.append(post)
    return filtered


# ============================================================
# 브랜드 태깅
# ============================================================
def tag_brand(post, config):
    """포스트 텍스트에서 브랜드 감지. 다중 매칭 시 등장 횟수 최다 브랜드. 없으면 '미상'."""
    text = (re.sub(r'<[^>]+>', '', post.get('title', '')) + ' '
            + re.sub(r'<[^>]+>', '', post.get('description', '')) + ' '
            + (post.get('full_content', '') or '')).lower()
    scores = {}
    for b in config.get('brands', []):
        name = b['name']
        keys = [name.lower()] + [a.lower() for a in b.get('aliases', [])]
        cnt = sum(text.count(k) for k in keys)
        if cnt > 0:
            scores[name] = cnt
    if not scores:
        return '미상', {}
    top = max(scores.items(), key=lambda x: x[1])[0]
    return top, scores


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
        if (i + 1) % 20 == 0:
            print(f"  본문 크롤링: {i+1}/{len(posts)}건 (확보: {crawled}건)")
    print(f"  본문 크롤링 완료: {crawled}/{len(posts)}건 확보")
    return posts


# ============================================================
# Content Class 분류 (Sincerity Filter 1차) — 주제 모드
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

    # 주제 관련성 (브랜드명 대신 주제 매칭)
    if not is_topic_relevant(full_text, config):
        return 'G', 'OFF_TOPIC'

    listing_markers = ['총정리', '리스트', '모음', 'best', 'top', '순위', '추천 순위']
    if any(m in title.lower() for m in listing_markers):
        return 'D', 'LISTING'

    regram_markers = ['리그램', '퍼옴', 'repost']
    non_hash_text = re.sub(r'#\S+', '', full_text).strip()
    if any(m in full_text for m in regram_markers) or len(non_hash_text) < 30:
        return 'E', 'REGRAM'

    press_phrases = ['보도자료', '출시했다', '관계자는', '밝혔다', '라고 전했다', '공식 발표', '출시한다']
    press_count = sum(1 for p in press_phrases if p in full_text)
    if press_count >= 3:
        return 'F', 'PRESS_COPY'

    biz_markers = ['공식판매', '판매처', '구매링크', '할인코드', '쿠폰', '최저가', '견적 문의', '상담 문의', '전화 주세요', '카톡 문의']
    biz_count = sum(1 for m in biz_markers if m in full_text)
    if biz_count >= 2:
        return 'F', 'BIZ_SUSPECT'

    if is_sponsored:
        return 'C', 'SPONSORED'

    if exp_count >= 2 and detail_count >= 3:
        return 'A', 'AUTHENTIC'
    return 'B', 'GENERAL'


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
# 2-Layer 분석
# ============================================================
def analyze_2layer(post, config):
    text = post.get('full_content', '') or ''
    title = re.sub(r'<[^>]+>', '', post.get('title', ''))
    full_text = title + ' ' + text
    full_lower = full_text.lower()
    analysis = config.get('analysis', {})

    topic_scores = {}
    for topic, keywords in analysis.get('topics', {}).items():
        score = sum(full_lower.count(kw) for kw in keywords)
        if score > 0:
            topic_scores[topic] = score
    top_topics = sorted(topic_scores.items(), key=lambda x: -x[1])[:3]
    primary_topic = top_topics[0][0] if top_topics else '기타'

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

    word_count = len(full_text.split())
    detail_signals = analysis.get('detail_signals', [])
    exp_signals = analysis.get('experience_signals', [])
    has_detail = sum(1 for w in detail_signals if w in full_lower)
    has_personal = sum(1 for w in exp_signals if w in full_lower)
    if word_count > 500 and has_detail >= 3 and has_personal >= 1:
        rql, rql_weight = 'Q5_서사형', 2.0
    elif word_count > 300 and has_detail >= 2:
        rql, rql_weight = 'Q4_분석형', 1.5
    elif word_count > 150 and (has_detail >= 1 or has_personal >= 1):
        rql, rql_weight = 'Q3_경험형', 1.0
    elif word_count > 50:
        rql, rql_weight = 'Q2_감상형', 0.5
    else:
        rql, rql_weight = 'Q1_간단형', 0.2

    first_person = len(re.findall(r'나는|내가|저는|제가|난\s|전\s', full_text))
    we_person = len(re.findall(r'우리|같이|함께|다같이', full_text))
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

    clout_score = 40
    recommend_words = ['추천', '꼭', '강추', '해보세요', '사세요', '놓치지', '비추']
    rec_count = sum(1 for w in recommend_words if w in full_lower)
    if rec_count > 0:
        clout_score += rec_count * 15
    if we_person > first_person:
        clout_score += 10
    conditional_rec = len(re.findall(r'라면\s*(추천|강추|좋)', full_text))
    if conditional_rec > 0:
        clout_score += 10
    clout_score = max(10, min(95, clout_score))

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
    }


def print_statistics(results):
    if not results:
        print("분석 결과가 없습니다.")
        return
    print(f"\n총 분석 건수: {len(results)}건")
    print("\n--- Content Class 분포 ---")
    class_dist = Counter(r['content_class'] for r in results)
    for cls in ['A', 'B', 'C', 'D', 'E', 'F', 'G']:
        c = class_dist.get(cls, 0)
        print(f"  {cls}: {'█'*c} {c}건")
    valid = [r for r in results if r['content_class'] in ('A', 'B', 'C')]
    print(f"\n유효 분석 대상 (A+B+C): {len(valid)}건")
    if not valid:
        return
    print("\n--- 브랜드 분포 ---")
    brand_dist = Counter(r.get('brand', '미상') for r in valid)
    for b, c in brand_dist.most_common():
        print(f"  {b}: {'█'*c} {c}건")
    print("\n--- 토픽 분포 ---")
    topic_dist = Counter(r.get('primary_topic', '기타') for r in valid)
    for t, c in topic_dist.most_common():
        print(f"  {t}: {'█'*c} {c}건")
    print("\n--- 감성 분포 ---")
    sent_dist = Counter(r.get('sentiment', '중립') for r in valid)
    for s in ['긍정', '혼합', '중립', '부정']:
        c = sent_dist.get(s, 0)
        print(f"  {s}: {c}건 ({c/len(valid)*100:.0f}%)")
    avg_auth = sum(r.get('authenticity', 0) for r in valid) / len(valid)
    print(f"\n--- Psyche 평균 --- Auth {avg_auth:.1f}")
    # Gate 3
    gate3 = [r for r in valid if r['content_class'] in ('A', 'B') and r.get('authenticity', 0) >= 60]
    print(f"\n--- Gate 3 (협찬제외 + Auth60+): {len(gate3)}건 ---")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='차량 실내 공조/냄새/공기질 크롤러')
    parser.add_argument('--days', type=int, default=180, help='크롤링 기간 (최근 N일)')
    parser.add_argument('--output', type=str, default=None)
    parser.add_argument('--skip-content', action='store_true')
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    config = load_config(CONFIG_PATH)
    client_id = env.get('NAVER_CLIENT_ID')
    client_secret = env.get('NAVER_CLIENT_SECRET')
    if not client_id or not client_secret:
        print("[ERROR] .env에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 필요")
        sys.exit(1)

    today = datetime.now().strftime('%Y-%m-%d')
    output_dir = Path(args.output) if args.output else (PROJECT_ROOT / config['output']['data_dir'] / today)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"차량 실내 공조/냄새/공기질 크롤러 v1.0 — {today}")
    print(f"기간: 최근 {args.days}일")
    print("=" * 60)

    print("\n[STEP 1] 네이버 블로그 검색")
    queries = config['search']['queries']
    raw_posts = crawl_naver_blogs(queries, client_id, client_secret, config)
    print(f"  총 수집: {len(raw_posts)}건 (중복 제거 후)")

    print("\n[STEP 2] 필터링")
    date_filtered = filter_by_date(raw_posts, days_back=args.days)
    print(f"  날짜 필터 (최근 {args.days}일): {len(date_filtered)}건")
    # 1차 관련성 (제목+요약 기준)
    relevance_filtered = filter_by_relevance(date_filtered, config, use_content=False)
    print(f"  주제 관련성 필터 (제목+요약): {len(relevance_filtered)}건")

    raw_path = output_dir / 'naver-raw.json'
    with open(raw_path, 'w', encoding='utf-8') as f:
        json.dump(relevance_filtered, f, ensure_ascii=False, indent=2)
    print(f"  저장: {raw_path}")

    if not args.skip_content:
        print(f"\n[STEP 3] 본문 크롤링 ({len(relevance_filtered)}건)")
        crawl_full_content(relevance_filtered, delay=config['crawl']['naver']['delay_seconds'])
        # 본문 확보 후 2차 관련성 재필터 (본문 포함)
        relevance_filtered = filter_by_relevance(relevance_filtered, config, use_content=True)
        print(f"  본문 반영 관련성 재필터: {len(relevance_filtered)}건")
        enriched_path = output_dir / 'naver-enriched.json'
        with open(enriched_path, 'w', encoding='utf-8') as f:
            json.dump(relevance_filtered, f, ensure_ascii=False, indent=2)
        print(f"  본문 포함 데이터 저장: {enriched_path}")

    print("\n[STEP 4] Sincerity Filter + 브랜드 태깅 + 2-Layer")
    results = []
    for post in relevance_filtered:
        content_class, flag = classify_content_class(post, config)
        trust_score = calculate_trust_score(post, content_class, flag, config)
        brand, brand_scores = tag_brand(post, config)
        result = {
            'date': post.get('postdate', ''),
            'title': re.sub(r'<[^>]+>', '', post.get('title', '')),
            'blogger': post.get('bloggername', ''),
            'link': post.get('link', ''),
            'full_content': post.get('full_content', ''),
            'content_class': content_class,
            'content_flag': flag,
            'trust_score': trust_score,
            'brand': brand,
            'brand_scores': brand_scores,
        }
        if content_class in ('A', 'B', 'C'):
            result.update(analyze_2layer(post, config))
        results.append(result)

    print("\n[STEP 5] 분석 결과 통계")
    print_statistics(results)

    results_path = output_dir / 'analysis-results.json'
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n저장 완료: {results_path}")

    valid = [r for r in results if r.get('content_class') in ('A', 'B', 'C')]
    gate3 = [r for r in valid if r['content_class'] in ('A', 'B') and r.get('authenticity', 0) >= 60]
    summary = {
        'date': today,
        'days': args.days,
        'total_crawled': len(raw_posts),
        'after_date_filter': len(date_filtered),
        'after_relevance': len(relevance_filtered),
        'content_class_dist': dict(Counter(r['content_class'] for r in results)),
        'valid_count': len(valid),
        'gate3_count': len(gate3),
        'brand_dist': dict(Counter(r.get('brand', '미상') for r in valid)),
        'topic_dist': dict(Counter(r.get('primary_topic', '기타') for r in valid)),
        'sentiment_dist': dict(Counter(r.get('sentiment', '중립') for r in valid)) if valid else {},
    }
    with open(output_dir / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"요약 저장: {output_dir / 'summary.json'}")
    print(f"\n{'='*60}\n완료! 유효 {len(valid)}건 / Gate3 {len(gate3)}건 / 전체 {len(results)}건\n{'='*60}")


if __name__ == '__main__':
    main()
