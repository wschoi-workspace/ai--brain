"""가나초콜릿하우스 부산 시즌2 — 네이버 블로그 크롤링 + 분석 파이프라인 (canonical)"""
import sys, os, json

# canonical pipeline 경로: 프로젝트 루트의 rxr-sns-app
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'rxr-sns-app'))

# .env 로드
def _load_env():
    env_path = os.path.join(ROOT, '.env')
    if os.path.exists(env_path):
        with open(env_path,'r',encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    k, _, v = line.strip().partition('=')
                    os.environ.setdefault(k, v)
_load_env()

from app.pipeline import naver_crawler, sincerity_filter, two_layer, gates as gates_mod

# ============================================================
# 설정
# ============================================================
KEYWORDS = [
    "가나초콜릿하우스",
    "가나초콜릿하우스 부산",
    "초콜릿하우스 부산",
    "가나초콜릿 팝업",
    "가나초콜릿하우스 전포",
    "가나 전포동 팝업",
    "가나초콜릿 위스키바",
    "프로젝트렌트 가나초콜릿",
    "프로젝트렌트 초콜릿",
    "가나초콜릿 애프터눈티",
    "전포동 가나 팝업",
    "부산 초콜릿 팝업",
]

MUST_KW = ["팝업", "전포", "프로젝트렌트", "방문", "다녀", "초콜릿하우스", "오프라인", "부산"]
START = "20230129"
END   = "20230411"
EVENT_START = "20230212"
EVENT_END   = "20230314"

OUT_DIR = os.path.join(ROOT, '80-r-tech', '85-analysis-results', 'gana-chocolate-house')
os.makedirs(OUT_DIR, exist_ok=True)

GANA_TOPICS = {
    '공간/분위기': ['공간','분위기','인테리어','포토존','사진','감성','프로젝트렌트','전포','인더스트리','무드','포토부스','조명','룸','디자인'],
    '초콜릿/맛': ['초콜릿','초콜렛','카카오','맛','풍미','달콤','쌉쌀','다크','밀크','봉봉','트러플','프랄린','가나','케이크','디저트','단맛','달달','녹아','부드러'],
    '위스키/페어링': ['위스키','위스키바','페어링','바','칵테일','잔','샷','하이볼','싱글몰트','버번','피트','스모키','글렌','발베니'],
    '애프터눈티': ['애프터눈','애프터눈티','애프터눈 티','티세트','3단','샌드위치','스콘','홍차','얼그레이','다과','티타임','세트','플레이트'],
    '웨이팅/예약': ['웨이팅','예약','줄','대기','기다','오픈런','시간 제한','네이버 예약','캐치테이블','만석','예매'],
    '가격/혜택': ['가격','비싸','가성비','할인','무료','혜택','이벤트','굿즈','증정','한정','리미티드','선착순','체험료'],
    '굿즈/기념품': ['굿즈','스티커','엽서','포토카드','틴','케이스','기념품','패키지','증정품','MD','머그','에코백'],
    '체험/프로그램': ['체험','원데이','클래스','만들기','직접','체험형','프로그램','참여','시음','테이스팅','페어링','코스','가이드'],
    '브랜드': ['가나','가나초콜릿','롯데','롯데제과','가나초콜릿하우스'],
}

# 팝업 특화 G등급 필터용
POPUP_SIGNALS = [
    '팝업','전포','프로젝트렌트','방문','다녀왔','다녀','갔다','갔는데','현장','오프라인',
    '초콜릿하우스','가나초콜릿하우스','부산','구경','가봤','다녀옴','예약','가나','롯데제과',
    '위스키','페어링','애프터눈','바','전포동',
]
ONLINE_ONLY = [
    '온라인 특가','앱 전용','쿠폰코드','라이브방송','라방','생방송','방송 시간','홈쇼핑','모바일 한정',
]


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
save(raw, "gana-chocolate-house-naver-raw.json")

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
save(raw, "gana-chocolate-house-naver-filtered.json")

# ============================================================
# STEP 3: Sincerity Filter (A~G)
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: Sincerity Filter")
print("=" * 60)

sincerity_filter.apply_filter(raw)
apply_popup_g_filter(raw)

dist = sincerity_filter.class_distribution(raw)
for cls in "ABCDEFG":
    print(f"  {cls}: {dist.get(cls, 0)}건")

# ============================================================
# STEP 4: 2-Layer 분석
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: 2-Layer 분석")
print("=" * 60)

analyzed = two_layer.analyze_all(raw, EVENT_START, EVENT_END, topics=GANA_TOPICS)

link_to_meta = {p.get("link"): p for p in raw}
for r in analyzed:
    meta = link_to_meta.get(r.get("link"))
    if meta:
        r["sincerity_class"] = meta.get("sincerity_class")
        r["trust_score"] = meta.get("trust_score")
        r["sincerity_flags"] = meta.get("sincerity_flags", [])

print(f"  분석 완료: {len(analyzed)}건")
save(analyzed, "gana-chocolate-house-2layer-results.json")

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

print("\n✅ 크롤링 + 분석 완료!")
print(f"총 {len(raw)}건 수집 → {len(analyzed)}건 분석 → Gate3 {gates['gate3']['summary']['n']}건 유효")
