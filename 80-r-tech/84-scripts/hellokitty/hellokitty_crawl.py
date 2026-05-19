"""헬로키티 × 지수 팝업스토어 (KREAM 도산, CJ온스타일) — RXR SNS 분석 파이프라인"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rxr-sns-app'))
os.environ.setdefault('NAVER_CLIENT_ID', 'W7iBMjaP5ge1kR6RlgyW')
os.environ.setdefault('NAVER_CLIENT_SECRET', 'gB2C5WUvl6')

from app.pipeline import naver_crawler, sincerity_filter, two_layer, gates as gates_mod

# ============================================================
# 설정
# ============================================================
KEYWORDS = [
    "헬로키티 지수 팝업",
    "헬로키티 지수 팝업스토어",
    "헬로키티x지수 팝업",
    "헬로키티 크림 팝업",
    "지수 크림 도산",
    "KREAM 도산 헬로키티",
    "크림 도산 팝업",
    "헬로키티 KREAM 팝업",
    "CJ온스타일 헬로키티 지수",
    "지수 헬로키티 교환일기",
    "지수 슈몬",
    "헬로키티 지수 굿즈",
    "헬로키티 지수 후기",
    "헬로키티 지수 웨이팅",
]

# 반드시 포함되어야 할 맥락 키워드 (OR)
MUST_KW = ["팝업", "크림", "KREAM", "도산", "교환일기", "슈몬", "지수", "CJ온스타일", "웨이팅", "다녀", "방문"]

START = "20251231"
END   = "20260219"
EVENT_START = "20260114"
EVENT_END   = "20260122"  # 기사 확인: 실제 1/14~1/22

OUT_DIR = os.path.dirname(__file__)

HELLOKITTY_TOPICS = {
    '공간/분위기': ['공간', '분위기', '인테리어', '핑크', '포토존', '포토부스', '사진', '감성', '도산', '플래그십', '매장', '디스플레이'],
    '컨셉/스토리': ['교환일기', '일기', '오더시트', '편지', '텍스트힙', '우정', '친구', '슈몬', '캐릭터', '지수가 그린'],
    '굿즈/제품': ['굿즈', '머그컵', '텀블러', '인형', '키링', '가방', '에코백', '볼펜', '필통', '다이어리', '스티커', '굿즈', '한정판', '리셀'],
    '지수/팬덤': ['지수', 'JISOO', '블랙핑크', 'BLACKPINK', '블핑', '팬', '지수팬', '직접 참석', '오픈 행사'],
    '웨이팅/예약': ['웨이팅', '대기', '줄', '오픈런', '예약', '사전예약', '네이버예약', '대기시간', '5시간', '3시간', '2시간'],
    '가격/혜택': ['가격', '비싸', '저렴', '가성비', '구매', '결제', '품절', '솔드아웃', '재입고'],
    '크림/CJ': ['크림', 'KREAM', 'CJ온스타일', '온스타일', '판매처', '공식', '유통'],
    '헬로키티IP': ['헬로키티', 'Hello Kitty', '키티', '산리오', '50주년', '캐릭터'],
}

POPUP_SIGNALS = [
    '팝업', '도산', 'KREAM', '크림', '교환일기', '슈몬', '웨이팅', '대기', '다녀왔', '방문', '갔다',
    '굿즈', '머그컵', '텀블러', '인형', '키링', '포토부스', '오더시트', '직접 참석', '플래그십',
]
ONLINE_ONLY = [
    '방송 시간', '라방', '라이브방송', '쿠폰코드', '앱 전용', '온라인 특가',
    '방송시간', '라이브 방송', '생방송', '홈쇼핑', '무료배송', '최저가',
]


def apply_popup_g_filter(posts):
    """팝업 무관 온라인/리셀 콘텐츠를 G등급으로 재분류"""
    for p in posts:
        text = (p.get("full_content", "") + " " + p.get("title", "") + " " + p.get("description", "")).lower()
        popup_hits = sum(1 for s in POPUP_SIGNALS if s.lower() in text)
        online_hits = sum(1 for s in ONLINE_ONLY if s.lower() in text)
        if popup_hits == 0 and online_hits >= 1:
            p["sincerity_class"] = "G"
            p["sincerity_flags"] = p.get("sincerity_flags", []) + ["OFF_TOPIC_ONLINE"]
            p["trust_score"] = max(0, p.get("trust_score", 100) - 30)


def save(data, filename):
    path = os.path.join(OUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  → 저장: {filename} ({len(data) if hasattr(data,'__len__') else '?'}건)")


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
    max_per_keyword=400,
)
print(f"  검색 결과: {len(raw)}건 (중복 제거 + 날짜/관련성 필터 후)")
save(raw, "hellokitty-jisoo-popup-naver-raw.json")

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

has_content = sum(1 for p in raw if len(p.get("full_content", "")) > 50)
print(f"  본문 확보: {has_content}/{len(raw)}건")
save(raw, "hellokitty-jisoo-popup-naver-filtered.json")

# ============================================================
# STEP 3: Sincerity Filter
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Sincerity Filter")
print("=" * 60)

sincerity_filter.apply_filter(raw)
apply_popup_g_filter(raw)

dist = sincerity_filter.class_distribution(raw)
for cls in "ABCDEFG":
    print(f"  {cls}: {dist.get(cls, 0)}건")

save(raw, "hellokitty-jisoo-popup-sincerity-filtered.json")

# ============================================================
# STEP 4: 2-Layer 분석
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: 2-Layer 분석")
print("=" * 60)

analyzed = two_layer.analyze_all(raw, EVENT_START, EVENT_END, topics=HELLOKITTY_TOPICS)

link_to_meta = {p.get("link"): p for p in raw}
for r in analyzed:
    meta = link_to_meta.get(r.get("link"))
    if meta:
        r["sincerity_class"] = meta.get("sincerity_class")
        r["trust_score"] = meta.get("trust_score")
        r["sincerity_flags"] = meta.get("sincerity_flags", [])

print(f"  분석 완료: {len(analyzed)}건")
save(analyzed, "hellokitty-jisoo-popup-2layer-results.json")

stats = two_layer.aggregate_stats(analyzed)
print(f"\n  감성: {stats.get('sentiment_pct', {})}")
print(f"  토픽: {stats.get('topic_dist', {})}")
print(f"  RQL: {stats.get('rql_dist', {})}")
print(f"  Auth: {stats.get('avg_auth', 0)} / Clout: {stats.get('avg_clout', 0)} / Fresh: {stats.get('avg_freshness', 0)}")
print(f"  협찬: {stats.get('sponsored_count', 0)}건 (Auth {stats.get('sponsored_avg_auth', 0)}) vs 자발적: {stats.get('organic_count', 0)}건 (Auth {stats.get('organic_avg_auth', 0)})")

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

# 전체 stats 저장
final = {
    "stats": stats,
    "gates": {k: v["summary"] for k, v in gates.items()},
    "class_dist": dist,
    "total_raw": len(raw),
    "total_analyzed": len(analyzed),
    "gate3_posts": gates["gate3"].get("posts", [])[:300],  # 부록용
}
save(final, "hellokitty-jisoo-popup-final-stats.json")

print("\n✅ 크롤링 + 분석 완료!")
print(f"총 {len(raw)}건 수집 → {len(analyzed)}건 분석 → Gate3 {gates['gate3']['summary']['n']}건 유효")
