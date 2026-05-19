"""컴온스타일 팝업스토어 — 네이버 블로그 크롤링 + 분석 파이프라인"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rxr-sns-app'))
os.environ.setdefault('NAVER_CLIENT_ID', 'W7iBMjaP5ge1kR6RlgyW')
os.environ.setdefault('NAVER_CLIENT_SECRET', 'gB2C5WUvl6')

from app.pipeline import naver_crawler, sincerity_filter, two_layer, gates as gates_mod

# ============================================================
# 설정
# ============================================================
KEYWORDS = [
    "컴온스타일 팝업",
    "컴온스타일 팝업스토어",
    "CJ온스타일 팝업 성수",
    "컴온스타일 성수",
    "컴온스타일 XYZ서울",
    "컴온스타일 쇼케이스 팝업",
    "최화정쇼 팝업",
    "겟잇뷰티 팝업",
    "오하나하타케 CJ",
    "컴온스타일 오프라인",
]

MUST_KW = ["팝업", "성수", "XYZ", "오프라인", "방문", "다녀", "현장", "쇼케이스"]
START = "20250321"
END   = "20250422"
EVENT_START = "20250404"
EVENT_END   = "20250408"

OUT_DIR = os.path.dirname(__file__)

COMONSTYLE_TOPICS = {
    '공간/분위기': ['공간', '분위기', '인테리어', '보라색', '보라', '퍼플', '포토존', '사진', '감성', 'XYZ', '성수'],
    '뷰티/화장품': ['겟잇뷰티', '뷰티', '화장품', '리쥬리프', '리터니티', '오데어', '다이슨', '글램팜', '뷰티클래스', '스킨케어', '메이크업'],
    '패션': ['한예슬', '패션', '오하나하타케', '오하나', '무라카미', '다카시', '옷', '코디'],
    '식품/건강': ['최화정', '최화정쇼', '슬로우에이징', '식품', '건강', '먹거리', '시식'],
    '리빙': ['안재현', '잠시 실내합니다', '리빙', '소품', '가구', '생활'],
    '체험/이벤트': ['스탬프', '컴온뷰티박스', '전자태그', '현장 특가', '이벤트', '체험', '참여', '굿즈'],
    'IP프로그램': ['최화정쇼', '겟잇뷰티', '한예슬', '오늘 뭐 입지', '안재현', '잠시 실내합니다'],
    '가격/혜택': ['무료', '공짜', '증정', '혜택', '선물', '할인', '특가'],
}

# 팝업 특화 G등급 필터용
POPUP_SIGNALS = ['팝업', '성수', 'XYZ', '오프라인', '방문', '다녀왔', '현장', '쇼케이스',
                 '슬로우에이징존', '하이라이트존', '뷰티백스테이지', '스탬프',
                 '컴온뷰티박스', '무라카미', '오하나하타케', '최화정', '한예슬', '안재현', '겟잇뷰티',
                 '다녀', '갔다', '갔는데', '방문했', '구경']
ONLINE_ONLY = ['방송 시간', '라방', '라이브방송', '쿠폰코드', '앱 전용', '온라인 특가',
               '방송시간', '라이브 방송', '생방송']


def apply_popup_g_filter(posts):
    """팝업 무관 온라인 쇼핑 콘텐츠를 G등급으로 재분류"""
    for p in posts:
        text = (p.get("full_content", "") + " " + p.get("title", "") + " " + p.get("description", "")).lower()
        popup_hits = sum(1 for s in POPUP_SIGNALS if s in text)
        online_hits = sum(1 for s in ONLINE_ONLY if s in text)
        if popup_hits == 0 and online_hits >= 1:
            p["sincerity_class"] = "G"
            p["sincerity_flags"] = p.get("sincerity_flags", []) + ["OFF_TOPIC_ONLINE"]
            p["trust_score"] = max(0, p.get("trust_score", 100) - 30)


def save(data, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  → 저장: {filename} ({len(data)}건)")


# ============================================================
# STEP 1: 네이버 검색
# ============================================================
print("=" * 60)
print("STEP 1: 네이버 블로그 검색")
print("=" * 60)

raw = naver_crawler.collect_all(
    keywords=KEYWORDS,
    start_yyyymmdd=START,
    end_yyyymmdd=END,
    must_keywords=MUST_KW,
    max_per_keyword=300,
)
print(f"  검색 결과: {len(raw)}건 (중복 제거 + 날짜/관련성 필터 후)")
save(raw, "comonstyle-popup-naver-raw.json")

if not raw:
    print("검색 결과 없음 — 키워드를 확인하세요")
    sys.exit(1)

# ============================================================
# STEP 2: 본문 크롤링
# ============================================================
print("\n" + "=" * 60)
print(f"STEP 2: 본문 크롤링 ({len(raw)}건)")
print("=" * 60)

def progress(done, total):
    print(f"  크롤링: {done}/{total}", end='\r')

naver_crawler.crawl_full_content(raw, delay=0.3, on_progress=progress)
print()

# 본문 크롤링 성공률
has_content = sum(1 for p in raw if len(p.get("full_content", "")) > 50)
print(f"  본문 확보: {has_content}/{len(raw)}건")
save(raw, "comonstyle-popup-naver-filtered.json")

# ============================================================
# STEP 3: Sincerity Filter (A~G)
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Sincerity Filter")
print("=" * 60)

sincerity_filter.apply_filter(raw)
apply_popup_g_filter(raw)  # G등급 팝업 특화 필터

dist = sincerity_filter.class_distribution(raw)
for cls in "ABCDEFG":
    print(f"  {cls}: {dist.get(cls, 0)}건")

# ============================================================
# STEP 4: 2-Layer 분석
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: 2-Layer 분석")
print("=" * 60)

analyzed = two_layer.analyze_all(raw, EVENT_START, EVENT_END, topics=COMONSTYLE_TOPICS)

# sincerity 정보 머지
link_to_meta = {p.get("link"): p for p in raw}
for r in analyzed:
    meta = link_to_meta.get(r.get("link"))
    if meta:
        r["sincerity_class"] = meta.get("sincerity_class")
        r["trust_score"] = meta.get("trust_score")
        r["sincerity_flags"] = meta.get("sincerity_flags", [])

print(f"  분석 완료: {len(analyzed)}건")
save(analyzed, "comonstyle-popup-2layer-results.json")

stats = two_layer.aggregate_stats(analyzed)
print(f"\n  감성: {stats.get('sentiment_pct', {})}")
print(f"  토픽: {stats.get('topic_dist', {})}")
print(f"  RQL: {stats.get('rql_dist', {})}")
print(f"  Auth: {stats.get('avg_auth', 0)} / Clout: {stats.get('avg_clout', 0)} / Fresh: {stats.get('avg_freshness', 0)}")
print(f"  협찬: {stats.get('sponsored_count', 0)}건 (Auth {stats.get('sponsored_avg_auth', 0)}) vs 자발적: {stats.get('organic_count', 0)}건 (Auth {stats.get('organic_avg_auth', 0)})")

# 기간별
print("\n  기간별:")
for period, ps in stats.get("period_stats", {}).items():
    print(f"    {period}: {ps['n']}건, 긍정 {ps['positive_pct']}%, Auth {ps['auth']}, Clout {ps['clout']}, Fresh {ps['freshness']}")

# ============================================================
# STEP 5: Sincerity Gate
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: Sincerity Gate")
print("=" * 60)

gates = gates_mod.run_all_gates(analyzed)
for g in ["gate1", "gate2", "gate3"]:
    s = gates[g]["summary"]
    print(f"  {g}: {s['n']}건, 긍정 {s['positive_pct']}%, Auth {s.get('auth', '-')}, Clout {s.get('clout', '-')}")

print("\n✅ 크롤링 + 분석 완료!")
print(f"총 {len(raw)}건 수집 → {len(analyzed)}건 분석 → Gate3 {gates['gate3']['summary']['n']}건 유효")
