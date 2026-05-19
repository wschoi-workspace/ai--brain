"""비욘드 팝업스토어 — 네이버 블로그 크롤링 + 분석 파이프라인"""
import sys, os, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rxr-sns-app'))
os.environ.setdefault('NAVER_CLIENT_ID', 'W7iBMjaP5ge1kR6RlgyW')
os.environ.setdefault('NAVER_CLIENT_SECRET', 'gB2C5WUvl6')

from app.pipeline import naver_crawler, sincerity_filter, two_layer, gates as gates_mod

# ============================================================
# 설정
# ============================================================
KEYWORDS = [
    "비욘드 팝업스토어",
    "비욘드 팝업 성수",
    "BEYOND 팝업스토어",
    "LG생활건강 비욘드 팝업",
    "비욘드 성수동",
    "비욘드 서울숲",
    "비욘드 Less plastic",
    "비욘드 친환경 팝업",
    "비욘드 리필",
    "비욘드 클린뷰티 팝업",
    "비욘드 팝업 후기",
    "비욘드 플라스틱",
]

MUST_KW = ["팝업", "성수", "서울숲", "방문", "다녀", "현장", "체험", "리필"]
START = "20230511"
END   = "20230702"
EVENT_START = "20230525"
EVENT_END   = "20230618"

OUT_DIR = os.path.dirname(__file__)

BEYOND_TOPICS = {
    '친환경/지속가능성': ['친환경', '지속가능', '에코', '환경', '리사이클', '재활용', '업사이클', '제로웨이스트', 'Less plastic', '플라스틱 줄이', '종이', '자연', '클린'],
    '리필/용기': ['리필', '리필제품', '용기', '플라스틱', '교환', '자판기', '코인', '한정판 보틀', '분리배출'],
    '공간/분위기': ['공간', '분위기', '인테리어', '종이로', '디자인', '포토존', '사진', '감성', '예쁘'],
    '제품/성분': ['바디워시', '샴푸', '비욘드', '유기농', '천연', '성분', '보습', '향', '로션'],
    '체험/클래스': ['향주머니', '가드닝', '클래스', '수업', '만들기', '체험', '워크숍'],
    '브랜드 가치': ['사명감', '가치', '철학', '비전', '메시지', '캠페인', '실천'],
    '가격/혜택': ['무료', '증정', '혜택', '이벤트', '선물', '할인'],
}

# 팝업 특화 G등급 필터
POPUP_SIGNALS = ['팝업', '성수', '서울숲', '방문', '다녀왔', '현장', '체험', '리필', '종이',
                 'Less plastic', '교환', '자판기', '향주머니', '가드닝', '클래스',
                 '다녀', '갔다', '갔는데', '방문했', '구경', '오픈', '전시']
PRODUCT_ONLY = ['구매후기', '배송', '쿠팡', '올리브영 구매', '온라인 구매', '택배']


def apply_popup_g_filter(posts):
    """팝업 무관 제품 리뷰를 G등급으로 재분류"""
    for p in posts:
        text = (p.get("full_content", "") + " " + p.get("title", "") + " " + p.get("description", "")).lower()
        popup_hits = sum(1 for s in POPUP_SIGNALS if s.lower() in text)
        product_only_hits = sum(1 for s in PRODUCT_ONLY if s.lower() in text)
        if popup_hits == 0 and product_only_hits >= 1:
            p["sincerity_class"] = "G"
            p["sincerity_flags"] = p.get("sincerity_flags", []) + ["OFF_TOPIC_PRODUCT_REVIEW"]
            p["trust_score"] = max(0, p.get("trust_score", 100) - 30)


def save(data, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  -> 저장: {filename} ({len(data)}건)")


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
save(raw, "beyond-popup-naver-raw.json")

if not raw:
    print("검색 결과 없음 -- 키워드를 확인하세요")
    sys.exit(1)

# ============================================================
# STEP 2: 본문 크롤링
# ============================================================
print(f"\nSTEP 2: 본문 크롤링 ({len(raw)}건)")
print("=" * 60)

def progress(done, total):
    print(f"  크롤링: {done}/{total}", end='\r')

naver_crawler.crawl_full_content(raw, delay=0.3, on_progress=progress)
print()

has_content = sum(1 for p in raw if len(p.get("full_content", "")) > 50)
print(f"  본문 확보: {has_content}/{len(raw)}건")
save(raw, "beyond-popup-naver-filtered.json")

# ============================================================
# STEP 3: Sincerity Filter (A~G)
# ============================================================
print(f"\nSTEP 3: Sincerity Filter")
print("=" * 60)

sincerity_filter.apply_filter(raw)
apply_popup_g_filter(raw)

dist = sincerity_filter.class_distribution(raw)
for cls in "ABCDEFG":
    print(f"  {cls}: {dist.get(cls, 0)}건")

# ============================================================
# STEP 4: 2-Layer 분석
# ============================================================
print(f"\nSTEP 4: 2-Layer 분석")
print("=" * 60)

analyzed = two_layer.analyze_all(raw, EVENT_START, EVENT_END, topics=BEYOND_TOPICS)

link_to_meta = {p.get("link"): p for p in raw}
for r in analyzed:
    meta = link_to_meta.get(r.get("link"))
    if meta:
        r["sincerity_class"] = meta.get("sincerity_class")
        r["trust_score"] = meta.get("trust_score")
        r["sincerity_flags"] = meta.get("sincerity_flags", [])

print(f"  분석 완료: {len(analyzed)}건")
save(analyzed, "beyond-popup-2layer-results.json")

stats = two_layer.aggregate_stats(analyzed)
print(f"\n  감성: {stats.get('sentiment_pct', {})}")
print(f"  토픽: {stats.get('topic_dist', {})}")
print(f"  RQL: {stats.get('rql_dist', {})}")
print(f"  Auth: {stats.get('avg_auth', 0)} / Clout: {stats.get('avg_clout', 0)} / Fresh: {stats.get('avg_freshness', 0)}")
print(f"  협찬: {stats.get('sponsored_count', 0)}건 (Auth {stats.get('sponsored_avg_auth', 0)}) vs 자발적: {stats.get('organic_count', 0)}건 (Auth {stats.get('organic_avg_auth', 0)})")

# 친환경 토픽 침투도
eco_count = sum(1 for r in analyzed if '친환경' in r.get('primary_topic', ''))
refill_count = sum(1 for r in analyzed if '리필' in r.get('primary_topic', ''))
print(f"\n  [친환경 침투도]")
print(f"  친환경/지속가능성 토픽: {eco_count}건 ({round(eco_count/max(len(analyzed),1)*100,1)}%)")
print(f"  리필/용기 토픽: {refill_count}건 ({round(refill_count/max(len(analyzed),1)*100,1)}%)")

print("\n  기간별:")
for period, ps in stats.get("period_stats", {}).items():
    print(f"    {period}: {ps['n']}건, 긍정 {ps['positive_pct']}%, Auth {ps['auth']}, Clout {ps['clout']}, Fresh {ps['freshness']}")

# ============================================================
# STEP 5: Sincerity Gate
# ============================================================
print(f"\nSTEP 5: Sincerity Gate")
print("=" * 60)

gates = gates_mod.run_all_gates(analyzed)
for g in ["gate1", "gate2", "gate3"]:
    s = gates[g]["summary"]
    print(f"  {g}: {s['n']}건, 긍정 {s['positive_pct']}%, Auth {s.get('auth', '-')}, Clout {s.get('clout', '-')}")

print(f"\n[완료] 크롤링 + 분석 완료!")
print(f"총 {len(raw)}건 수집 -> {len(analyzed)}건 분석 -> Gate3 {gates['gate3']['summary']['n']}건 유효")
