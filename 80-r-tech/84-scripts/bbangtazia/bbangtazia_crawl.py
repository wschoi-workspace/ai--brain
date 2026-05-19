"""빵타지아성수 — 네이버 블로그 크롤링 + Sincerity Filter + 2-Layer 분석 파이프라인"""
import os, sys, json, time, re, math
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from html.parser import HTMLParser
from datetime import datetime, timedelta

# ============================================================
# .env 로드
# ============================================================
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def _load_env():
    env_path = os.path.join(ROOT, '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    k, _, v = line.strip().partition('=')
                    os.environ.setdefault(k.strip(), v.strip())
_load_env()

NAVER_CLIENT_ID = os.environ.get('NAVER_CLIENT_ID', '')
NAVER_CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET', '')
if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
    print("ERROR: NAVER_CLIENT_ID / NAVER_CLIENT_SECRET not found in .env")
    sys.exit(1)

OUT_DIR = os.path.join(ROOT, '80-r-tech', '85-analysis-results', 'bbangtazia')
os.makedirs(OUT_DIR, exist_ok=True)

# ============================================================
# 설정
# ============================================================
KEYWORDS = [
    "빵타지아 팝업",
    "빵타지아 성수",
    "빵타지아부산",
    "빵타지아 부산 in 성수",
    "빵타지아 프로젝트렌트",
    "빵타지아 후기",
    "빵타지아성수",
    "성수 빵타지아",
    "빵타지아 부산 팝업",
    "빵타지아 바스켓성수",
    "부산빵지순례 성수",
]

MUST_KW = ["팝업", "성수", "프로젝트렌트", "방문", "다녀", "빵타지아", "오프라인", "바스켓", "부산", "빵지순례"]

EVENT_START = "20260410"
EVENT_END   = "20260411"
# 분석 기간: 사전 2주 ~ 오늘(사후 12일)
START = "20260327"
END   = "20260423"

TOPICS = {
    '공간/분위기': ['공간', '분위기', '인테리어', '포토존', '사진', '감성', '프로젝트렌트', '성수', '바스켓', '무드', '포토', '조명', '예쁜', '예뻤', '핫플', '핫한', '플레이스', '카페', '뷰', '외관'],
    '빵/제품': ['빵', '베이커리', '바게트', '크루아상', '식빵', '소금빵', '크림', '맛', '풍미', '식감', '겉바속촉', '발효', '밀가루', '버터', '구움', '구워', '반죽', '빵집', '제과', '페이스트리', '타르트', '스콘', '케이크', '디저트', '맛있', '달콤', '고소', '담백', '쫄깃'],
    '웨이팅/구매': ['웨이팅', '줄', '대기', '기다', '오픈런', '줄서', '완판', '품절', '매진', '구매', '가격', '원', '개', '봉지', '포장', '택배', '선착순'],
    '브랜드/부산': ['부산', '남천동', '수영구', '광안리', '빵지순례', '부산빵', '로컬', '부산맛집', '본점', '원조'],
}

POPUP_SIGNALS = [
    '팝업', '성수', '프로젝트렌트', '방문', '다녀왔', '다녀', '갔다', '갔는데', '현장',
    '빵타지아', '바스켓', '부산', '빵지순례', '베이커리', '오픈런', '웨이팅',
]

# ============================================================
# 네이버 검색 API
# ============================================================
def naver_search(query, display=100, start=1, sort='sim'):
    url = f"https://openapi.naver.com/v1/search/blog.json?query={quote(query)}&display={display}&start={start}&sort={sort}"
    req = Request(url)
    req.add_header('X-Naver-Client-Id', NAVER_CLIENT_ID)
    req.add_header('X-Naver-Client-Secret', NAVER_CLIENT_SECRET)
    try:
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except (HTTPError, URLError) as e:
        print(f"  API 오류: {e}")
        return None

def strip_html(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#039;', "'")
    return text.strip()

def parse_date(datestr):
    """네이버 API 날짜 'Thu, 10 Apr 2026 ...' → 'YYYYMMDD'"""
    try:
        # RFC 2822 형식
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(datestr)
        return dt.strftime('%Y%m%d')
    except Exception:
        return datestr[:8] if len(datestr) >= 8 else datestr

def collect_all():
    """키워드별 검색 → 중복 제거 → 날짜+관련성 필터"""
    seen_links = set()
    results = []

    for kw in KEYWORDS:
        for sort in ['sim', 'date']:
            for start_idx in range(1, 901, 100):
                data = naver_search(kw, display=100, start=start_idx, sort=sort)
                if not data or not data.get('items'):
                    break

                for item in data['items']:
                    link = item.get('link', '')
                    if link in seen_links:
                        continue

                    # 날짜 필터
                    post_date = parse_date(item.get('postdate', ''))
                    if post_date < START or post_date > END:
                        continue

                    title = strip_html(item.get('title', ''))
                    desc = strip_html(item.get('description', ''))
                    combined = (title + ' ' + desc).lower()

                    # 관련성 필터: must_kw 중 1개 이상 포함
                    if not any(mk in combined for mk in MUST_KW):
                        continue

                    seen_links.add(link)
                    results.append({
                        'title': title,
                        'description': desc,
                        'link': link,
                        'bloggername': strip_html(item.get('bloggername', '')),
                        'bloggerlink': item.get('bloggerlink', ''),
                        'postdate': post_date,
                        'keyword': kw,
                        'full_content': '',
                    })

                if len(data.get('items', [])) < 100:
                    break
                time.sleep(0.15)

        print(f"  [{kw}] 누적: {len(results)}건")

    print(f"\n  총 수집: {len(results)}건 (중복 제거 + 날짜/관련성 필터 후)")
    return results


# ============================================================
# 본문 크롤링
# ============================================================
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            t = data.strip()
            if t:
                self.texts.append(t)

    def get_text(self):
        return ' '.join(self.texts)

def crawl_content(url, retries=2):
    """블로그 모바일 버전에서 본문 텍스트 추출"""
    mobile_url = url.replace('blog.naver.com/', 'm.blog.naver.com/')

    for attempt in range(retries + 1):
        try:
            req = Request(mobile_url, headers={
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
            })
            with urlopen(req, timeout=10) as resp:
                html = resp.read().decode('utf-8', errors='ignore')

            # se-main-container (스마트에디터)
            patterns = [
                r'class="se-main-container"[^>]*>(.*?)</div>\s*</div>\s*</div>',
                r'class="post-view"[^>]*>(.*?)</div>',
                r'class="se-component se-text"[^>]*>(.*?)</div>',
            ]

            for pattern in patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    extractor = TextExtractor()
                    extractor.feed(match.group(1))
                    text = extractor.get_text()
                    if len(text) > 30:
                        return text

            # fallback: body 전체
            extractor = TextExtractor()
            extractor.feed(html)
            text = extractor.get_text()
            if len(text) > 50:
                return text[:5000]

        except Exception as e:
            if attempt < retries:
                time.sleep(1)
            continue

    return ''


def crawl_all_content(posts, delay=0.4):
    total = len(posts)
    for i, p in enumerate(posts):
        content = crawl_content(p['link'])
        p['full_content'] = content
        p['content_length'] = len(content)
        print(f"  크롤링: {i+1}/{total} ({len(content)}자)", end='\r')
        time.sleep(delay)
    print()


# ============================================================
# Sincerity Filter (A~G)
# ============================================================
PERSONAL_EXP = ['다녀왔', '갔는데', '먹어봤', '줄 서', '웨이팅', '친구랑', '데이트', '다녀온', '가봤', '갔다', '먹었', '사왔', '줄서', '방문했', '다녀옴', '가봄']
DETAIL_SIGNALS = ['분', '시간', '층', '원', '개', '맛이', '식감', '가격', '종류', '메뉴', '크기', '무게']
SPONSORED_MARKERS = ['제공받', '#광고', '#ad', '체험단', '서포터즈', '원고료', '소정의', '협찬', '지원받']
LISTING_MARKERS = ['총정리', '리스트', '모음', 'BEST', '가볼만한곳', '가볼만한 곳', '추천 리스트']
REGRAM_MARKERS = ['리그램', '퍼옴', 'repost']
PRESS_MARKERS = ['보도자료', '공식 발표', '오픈 일정', '운영 시간', '위치 안내', '입장 안내', '공식 홈페이지']
BIZ_MARKERS = ['공식', '판매처', '구매링크', '할인코드', '프로모션 코드']

def count_matches(text, markers):
    return sum(1 for m in markers if m in text)

def classify_sincerity(post):
    text = (post.get('full_content', '') + ' ' + post.get('title', '') + ' ' + post.get('description', '')).lower()
    title = post.get('title', '').lower()
    content = post.get('full_content', '')

    # G: 노이즈
    popup_hits = sum(1 for s in POPUP_SIGNALS if s.lower() in text)
    if popup_hits == 0:
        return 'G', ['OFF_TOPIC'], 0

    flags = []
    trust = 100

    # E: 리그램
    regram = count_matches(text, REGRAM_MARKERS)
    non_hash = re.sub(r'#\S+', '', content).strip()
    hashtag_count = len(re.findall(r'#\S+', content))
    if regram > 0:
        flags.append('REGRAM')
        trust -= 30
        return 'E', flags, max(0, trust)
    if len(non_hash) < 30 and hashtag_count >= 3:
        flags.append('HASHTAG_ONLY')
        trust -= 25
        return 'E', flags, max(0, trust)
    if len(content) < 20:
        flags.append('TOO_SHORT')
        trust -= 20
        return 'E', flags, max(0, trust)

    # F: 비즈니스/보도자료
    press_hits = count_matches(text, PRESS_MARKERS)
    biz_hits = count_matches(text, BIZ_MARKERS)
    if press_hits >= 3:
        flags.append('PRESS_COPY')
        trust -= 35
        return 'F', flags, max(0, trust)
    if press_hits >= 2:
        flags.append('PRESS_PARTIAL')
        trust -= 15
    if biz_hits >= 2:
        flags.append('BIZ_SUSPECT')
        trust -= 25
        return 'F', flags, max(0, trust)

    # D: 나열형
    listing = any(m in title for m in LISTING_MARKERS)
    if listing:
        flags.append('LISTING')
        trust -= 20
        return 'D', flags, max(0, trust)

    # C: 협찬
    sponsored = count_matches(text, SPONSORED_MARKERS)
    if sponsored > 0:
        flags.append('SPONSORED')
        trust -= 15

    # A vs B
    personal = count_matches(text, PERSONAL_EXP)
    detail = count_matches(text, DETAIL_SIGNALS)

    if personal >= 2:
        flags.append('PERSONAL_EXP')
        trust += 15
    if detail >= 3:
        flags.append('DETAILED')
        trust += 10

    trust = max(0, min(100, trust))

    if sponsored > 0:
        return 'C', flags, trust

    if personal >= 2 and detail >= 3:
        return 'A', flags, trust

    return 'B', flags, trust


def apply_sincerity_filter(posts):
    for p in posts:
        cls, flags, trust = classify_sincerity(p)
        p['sincerity_class'] = cls
        p['sincerity_flags'] = flags
        p['trust_score'] = trust


# ============================================================
# 2-Layer 분석
# ============================================================
POSITIVE_KW = ['좋았', '좋아', '맛있', '예쁘', '예뻤', '만족', '추천', '최고', '행복', '감동', '멋진', '멋있', '훌륭', '대만족', '완벽', '사랑', '기대 이상', '가볼만', '꼭 가', '강추']
NEGATIVE_KW = ['별로', '실망', '아쉬', '아쉬웠', '후회', '비싸', '불편', '최악', '짜증', '화남', '혼잡', '복잡', '줄이 길', '웨이팅 길', '기다림', '부족', '실패']
EXCESS_POSITIVE = ['진짜', '너무너무', '완전', '대박', '미쳤', '최고의', '인생', '역대급', '레전드', '미친']

def analyze_sentiment(text):
    pos = count_matches(text, POSITIVE_KW)
    neg = count_matches(text, NEGATIVE_KW)
    if pos > 0 and neg > 0:
        return '혼합', pos, neg
    if pos > neg:
        return '긍정', pos, neg
    if neg > pos:
        return '부정', pos, neg
    return '중립', pos, neg

def analyze_topics(text):
    topic_scores = {}
    for topic, keywords in TOPICS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            topic_scores[topic] = score

    if not topic_scores:
        return '공간/분위기'  # default
    return max(topic_scores, key=topic_scores.get)

def analyze_rql(post):
    content = post.get('full_content', '')
    length = len(content)
    text = content.lower()
    personal = count_matches(text, PERSONAL_EXP)
    detail = count_matches(text, DETAIL_SIGNALS)

    if length >= 500 and detail >= 3 and personal >= 1:
        return 'Q5', 2.0
    if length >= 300 and detail >= 2:
        return 'Q4', 1.5
    if length >= 150 and (detail >= 1 or personal >= 1):
        return 'Q3', 1.0
    if length >= 50:
        return 'Q2', 0.5
    return 'Q1', 0.2

def analyze_psyche(post):
    content = post.get('full_content', '')
    text = content.lower() if content else ''
    title = post.get('title', '').lower()
    combined = text + ' ' + title

    # === Authenticity ===
    auth = 60
    sponsored = 'SPONSORED' in post.get('sincerity_flags', [])
    if sponsored:
        auth -= 15

    excess = sum(1 for e in EXCESS_POSITIVE if e in combined)
    if excess > 5:
        auth -= (excess - 5) * 3

    excl_count = combined.count('!')
    if excl_count > 10:
        auth -= (excl_count - 10) * 2

    personal = count_matches(combined, PERSONAL_EXP)
    detail = count_matches(combined, DETAIL_SIGNALS)

    if personal >= 2:
        auth += 10
    if detail >= 3:
        auth += 10

    # 균형 평가 (긍부정 공존)
    pos = count_matches(combined, POSITIVE_KW)
    neg = count_matches(combined, NEGATIVE_KW)
    if pos > 0 and neg > 0:
        auth += 15

    auth = max(10, min(95, auth))

    # === Clout ===
    clout = 40
    recommend_kw = ['추천', '꼭 가', '강추', '가보세요', '가봐', '드셔보', '먹어보']
    clout += sum(15 for r in recommend_kw if r in combined)

    # 1인칭 vs 복수형
    first_person = len(re.findall(r'나는|내가|저는|제가|난|전', combined))
    plural = len(re.findall(r'우리|같이|함께', combined))
    if plural > first_person:
        clout += 10

    # 제3자 경험
    third_party = len(re.findall(r'친구가|같이 간|데려갔|데려간', combined))
    clout += third_party * 12

    # 예방 초점
    prevention = len(re.findall(r'안 가면|놓치면|없어지기|후회할', combined))
    clout += prevention * 8

    # 조건부 추천
    conditional = len(re.findall(r'라면 강추|하는 분|좋아하면|좋아한다면', combined))
    clout += conditional * 10

    # 정체성 선언
    identity = len(re.findall(r'덕후|팬|애호가|러버|매니아', combined))
    clout += identity * 12

    clout = max(10, min(95, clout))

    # === Freshness ===
    # "이/가" vs "은/는" 조사 패턴
    iga = len(re.findall(r'[가-힣]이\s|[가-힣]가\s', combined))
    eunneun = len(re.findall(r'[가-힣]은\s|[가-힣]는\s', combined))
    total_particles = iga + eunneun
    freshness = (iga / total_particles * 100) if total_particles > 0 else 50
    freshness = max(10, min(95, freshness))

    # === 대명사 ===
    pronouns = {
        'first_person': first_person,
        'plural': plural,
        'place': len(re.findall(r'여기|이곳|이 공간|이 매장|이 가게', combined)),
    }

    return {
        'auth': round(auth, 1),
        'clout': round(clout, 1),
        'freshness': round(freshness, 1),
        'excess_positive': excess,
        'exclamation_count': excl_count,
        'pronouns': pronouns,
    }


def classify_period(postdate):
    d = postdate
    if d < EVENT_START:
        return '사전'
    elif d <= EVENT_END:
        return '이벤트'
    else:
        return '사후'


def analyze_all(posts):
    for p in posts:
        text = (p.get('full_content', '') + ' ' + p.get('title', '')).lower()

        # Content Layer
        sentiment, pos_score, neg_score = analyze_sentiment(text)
        p['sentiment'] = sentiment
        p['pos_score'] = pos_score
        p['neg_score'] = neg_score
        p['topic'] = analyze_topics(text)
        rql, rql_weight = analyze_rql(p)
        p['rql'] = rql
        p['rql_weight'] = rql_weight

        # Psyche Layer
        psyche = analyze_psyche(p)
        p.update(psyche)

        # 기간 분류
        p['period'] = classify_period(p.get('postdate', ''))

    return posts


# ============================================================
# Sincerity Gate
# ============================================================
def apply_gates(posts):
    # Gate 1: G(노이즈) 제거
    gate1 = [p for p in posts if p.get('sincerity_class') != 'G']

    # Gate 2: + D(나열) + E(리그램) + F(비즈니스) 제거  [C는 유지]
    gate2 = [p for p in gate1 if p.get('sincerity_class') in ('A', 'B', 'C')]

    # Gate 3: Auth 60+ 필터
    gate3 = [p for p in gate2 if p.get('auth', 0) >= 60]

    def stats(subset):
        n = len(subset)
        if n == 0:
            return {'n': 0, 'positive_pct': 0, 'avg_auth': 0, 'avg_clout': 0, 'avg_freshness': 0}
        pos = sum(1 for p in subset if p.get('sentiment') == '긍정')
        return {
            'n': n,
            'positive_pct': round(pos / n * 100, 1),
            'avg_auth': round(sum(p.get('auth', 0) for p in subset) / n, 1),
            'avg_clout': round(sum(p.get('clout', 0) for p in subset) / n, 1),
            'avg_freshness': round(sum(p.get('freshness', 0) for p in subset) / n, 1),
        }

    return {
        'gate1': {'posts': gate1, 'stats': stats(gate1)},
        'gate2': {'posts': gate2, 'stats': stats(gate2)},
        'gate3': {'posts': gate3, 'stats': stats(gate3)},
    }


# ============================================================
# 집계
# ============================================================
def aggregate(posts, gates):
    total = len(posts)

    # Content Class 분포
    class_dist = {}
    for p in posts:
        cls = p.get('sincerity_class', '?')
        class_dist[cls] = class_dist.get(cls, 0) + 1

    # 감성 분포
    sentiment_dist = {}
    for p in posts:
        s = p.get('sentiment', '중립')
        sentiment_dist[s] = sentiment_dist.get(s, 0) + 1

    # 토픽 분포
    topic_dist = {}
    for p in posts:
        t = p.get('topic', '기타')
        topic_dist[t] = topic_dist.get(t, 0) + 1

    # RQL 분포
    rql_dist = {}
    rql_asset = 0
    for p in posts:
        r = p.get('rql', 'Q1')
        rql_dist[r] = rql_dist.get(r, 0) + 1
        rql_asset += p.get('rql_weight', 0.2)

    # 기간별 통계
    period_stats = {}
    for period in ['사전', '이벤트', '사후']:
        subset = [p for p in posts if p.get('period') == period]
        n = len(subset)
        if n == 0:
            period_stats[period] = {'n': 0, 'positive_pct': 0, 'auth': 0, 'clout': 0, 'freshness': 0}
            continue
        pos = sum(1 for p in subset if p.get('sentiment') == '긍정')
        period_stats[period] = {
            'n': n,
            'positive_pct': round(pos / n * 100, 1),
            'auth': round(sum(p.get('auth', 0) for p in subset) / n, 1),
            'clout': round(sum(p.get('clout', 0) for p in subset) / n, 1),
            'freshness': round(sum(p.get('freshness', 0) for p in subset) / n, 1),
        }

    # 협찬 vs 자발
    sponsored = [p for p in posts if p.get('sincerity_class') == 'C']
    organic = [p for p in posts if p.get('sincerity_class') in ('A', 'B')]

    def avg_auth(subset):
        if not subset:
            return 0
        return round(sum(p.get('auth', 0) for p in subset) / len(subset), 1)

    # 날짜별 분포
    date_dist = {}
    for p in posts:
        d = p.get('postdate', '')
        date_dist[d] = date_dist.get(d, 0) + 1

    return {
        'total': total,
        'class_dist': class_dist,
        'sentiment_dist': sentiment_dist,
        'topic_dist': topic_dist,
        'rql_dist': rql_dist,
        'rql_asset': round(rql_asset, 1),
        'rql_density': round(rql_asset / total, 2) if total > 0 else 0,
        'period_stats': period_stats,
        'date_dist': dict(sorted(date_dist.items())),
        'sponsored_count': len(sponsored),
        'sponsored_avg_auth': avg_auth(sponsored),
        'organic_count': len(organic),
        'organic_avg_auth': avg_auth(organic),
        'gates': {
            'gate1': gates['gate1']['stats'],
            'gate2': gates['gate2']['stats'],
            'gate3': gates['gate3']['stats'],
        },
    }


# ============================================================
# 저장
# ============================================================
def save(data, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  -> 저장: {path}")


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("빵타지아성수 — RXR SNS Raw Data Analysis")
    print(f"분석 기간: {START} ~ {END}")
    print(f"이벤트: {EVENT_START} ~ {EVENT_END}")
    print("=" * 60)

    # STEP 1: 네이버 검색
    print("\nSTEP 1: 네이버 블로그 검색")
    print("-" * 40)
    posts = collect_all()
    save(posts, "bbangtazia-naver-raw.json")

    if not posts:
        print("검색 결과 없음 — 키워드를 확인하세요")
        sys.exit(1)

    # STEP 2: 본문 크롤링
    print(f"\nSTEP 2: 본문 크롤링 ({len(posts)}건)")
    print("-" * 40)
    crawl_all_content(posts, delay=0.4)
    has_content = sum(1 for p in posts if len(p.get('full_content', '')) > 50)
    print(f"  본문 확보: {has_content}/{len(posts)}건")
    save(posts, "bbangtazia-naver-filtered.json")

    # STEP 3: Sincerity Filter
    print(f"\nSTEP 3: Sincerity Filter")
    print("-" * 40)
    apply_sincerity_filter(posts)
    for cls in 'ABCDEFG':
        cnt = sum(1 for p in posts if p.get('sincerity_class') == cls)
        print(f"  {cls}: {cnt}건")
    save(posts, "bbangtazia-sincerity-filtered.json")

    # STEP 4: 2-Layer 분석
    print(f"\nSTEP 4: 2-Layer 분석")
    print("-" * 40)
    analyze_all(posts)
    save(posts, "bbangtazia-2layer-results.json")

    # STEP 5: Sincerity Gate
    print(f"\nSTEP 5: Sincerity Gate")
    print("-" * 40)
    gates = apply_gates(posts)
    for g in ['gate1', 'gate2', 'gate3']:
        s = gates[g]['stats']
        print(f"  {g}: {s['n']}건, 긍정 {s['positive_pct']}%, Auth {s['avg_auth']}")

    # STEP 6: 집계
    print(f"\nSTEP 6: 집계")
    print("-" * 40)
    stats = aggregate(posts, gates)
    save(stats, "bbangtazia-stats.json")

    print(f"\n{'=' * 60}")
    print(f"완료! 총 {stats['total']}건")
    print(f"  Class: {stats['class_dist']}")
    print(f"  감성: {stats['sentiment_dist']}")
    print(f"  토픽: {stats['topic_dist']}")
    print(f"  RQL: {stats['rql_dist']} (자산값: {stats['rql_asset']})")
    print(f"  Gate 1→3: {stats['gates']['gate1']['n']}→{stats['gates']['gate2']['n']}→{stats['gates']['gate3']['n']}")
    print(f"  협찬 {stats['sponsored_count']}건 (Auth {stats['sponsored_avg_auth']}) vs 자발 {stats['organic_count']}건 (Auth {stats['organic_avg_auth']})")
    print(f"\n기간별:")
    for period, ps in stats['period_stats'].items():
        print(f"  {period}: {ps['n']}건, 긍정 {ps['positive_pct']}%, Auth {ps['auth']}, Clout {ps['clout']}, Fresh {ps['freshness']}")
    print(f"\n날짜별: {stats['date_dist']}")
    print(f"{'=' * 60}")
