#!/usr/bin/env python3
"""윤선생 트랙A — 정제·태깅·집계.
노이즈 제거 → BM 태깅 → 자사/협찬 추정 → 배제·영어수준 신호 추출 → 연도별 집계.
출력: 정제 JSON + 분석용 버킷별 대표 인용 + 집계 메타."""
import json, re, os
from collections import Counter, defaultdict

BASE = os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")
d = json.load(open(os.path.join(BASE, "yoonsam-trackA-naver-raw.json")))

def txt(r): return (r["title"] + " " + r["description"])

# --- 1) 노이즈 제외 ---
NOISE = re.compile(r"맛집|불고기|오리|술집|카페 후기|메뉴|간판|시트지|인테리어|리모델링|철거|상가\b|올리모델링|"
                   r"큐리매쓰|수학학원 간판|분양|부동산|매물|네일|미용실|헤어|펜션|숙소|호텔")
# 경쟁사 버킷은 윤선생 무관 가능하므로 노이즈만, 윤선생 버킷은 추가로 윤선생 영어 맥락 필요
def is_noise(r):
    t = txt(r)
    if NOISE.search(t): return True
    return False

# --- 2) 자사/센터 공식·홍보 추정 (진정성 낮음) ---
OFFICIAL = re.compile(r"센터입니다|센터에서|지점입니다|학습관|공식블로그|등록 문의|상담 문의|상담 환영|"
                      r"문의 ?주세요|모집합니다|모집중|오픈 이벤트|가맹|원장입니다|선생님을 모집|상담신청")
SPONSORED = re.compile(r"협찬|제공받|원고료|체험단|소정의|업체로부터|대가를|광고 ?포함|유료광고|애드포스트|"
                       r"무료로 제공|지원받아|서포터즈")

# --- 3) BM 태깅 ---
def bm_tag(r):
    t = txt(r)
    basic = bool(re.search(r"베이직|화상|비대면|줌\b|ZOOM|원격|온라인 수업|온라인수업", t))
    bangmun = bool(re.search(r"방문|선생님이 (와|오)|집으로|주\s?[1-3]회 방문|1:1 방문|방문선생|방문 수업|방문수업|영어교실", t))
    soop = bool(re.search(r"영어숲|학원|등원|센터 등록|어학원", t))
    if basic and not bangmun: return "베이직(화상)"
    if bangmun and not basic: return "교실(방문)"
    if soop and not (basic or bangmun): return "영어숲(학원)"
    if basic and bangmun: return "복합언급"
    return "공통"

# --- 4) 감성 (description 키워드 룰, 약한 신호 — 정성검증 필요) ---
POS = re.compile(r"좋아요|좋았|만족|추천|효과|늘었|향상|즐겁|재밌|재미있|꾸준|도움|성장|발전|자신감|칭찬|최고|강추|잘 ?늘")
NEG = re.compile(r"별로|비추|단점|아쉽|불만|후회|그만|끊|해지|위약금|환불|실망|효과 ?없|안 ?늘|돈 ?아깝|최악|짜증|스트레스|부담")
def senti(r):
    t = txt(r); p=len(POS.findall(t)); n=len(NEG.findall(t))
    if p>n: return "긍"
    if n>p: return "부"
    return "중"

# --- 5) 영어수준 신호 ---
START_AGE = [
    ("초1이전", re.compile(r"[4-7]살|[4-7]세|유아|유치원|미취학|취학 ?전|6세|7세|5세|4세|영아|아기")),
    ("초1~2",  re.compile(r"초1|초등 ?1|1학년|초2|초등 ?2|2학년|여덟살|8살|일곱살")),
    ("초3~4",  re.compile(r"초3|초등 ?3|3학년|초4|초등 ?4|4학년")),
    ("초4이후", re.compile(r"초5|초등 ?5|5학년|초6|6학년|중1|중학|고등")),
]
def start_bucket(r):
    t = txt(r)
    for name, rx in START_AGE:
        if rx.search(t): return name
    return None
PRIOR = [
    ("영유졸업→",   re.compile(r"영유.{0,6}(졸업|나온|나와|끝|마치|수료)|영어유치원.{0,6}(졸업|나온|끝)")),
    ("타학습지이탈→", re.compile(r"(구몬|눈높이|재능|튼튼영어|빨간펜|기탄|문방).{0,12}(하다가|그만|끊|에서|다니다|하다)")),
    ("엄마표→",     re.compile(r"엄마표|흘려듣기|집중듣기|집에서 ?하다")),
    ("처음영어→",   re.compile(r"처음 ?영어|첫 ?영어|영어 ?처음|영어 ?입문|영어 시작이|노출 ?처음")),
]
def prior_path(r):
    t = txt(r)
    for name, rx in PRIOR:
        if rx.search(t): return name
    return None

# --- 6) 배제사유 클러스터 (exclude 버킷 + 부정 멘션) ---
EXCL = [
    ("가격·가성비",   re.compile(r"비싸|가격 ?부담|돈 ?아깝|가성비|학원비.{0,4}육박|비용 ?부담")),
    ("약정·해지",    re.compile(r"약정|위약금|해지|환불|계약")),
    ("효과의심·아웃풋", re.compile(r"효과 ?없|효과 ?의심|실력 ?안|안 ?늘|아웃풋|말하기 ?안|성과 ?없|밑빠진")),
    ("혼자독학·관리", re.compile(r"혼자 ?해야|혼자 ?앉|자기주도.{0,4}안|관리 ?안|엄마 ?손|스스로 ?안")),
    ("화상거부감",   re.compile(r"화상.{0,6}(별로|싫|거부|불편|집중 ?안)|비대면.{0,6}(별로|싫|불편)")),
    ("방문부담",     re.compile(r"방문.{0,6}(부담|불편|스트레스|싫|귀찮)|선생님 ?오시는.{0,4}부담")),
    ("끼워팔기·영업",  re.compile(r"끼워팔|패드.{0,4}세트|세트.{0,4}구매|영업|강매|권유.{0,4}부담")),
    ("교재·콘텐츠",   re.compile(r"교재.{0,4}(별로|구식|노후|오래|지루)|지루|흥미 ?없")),
]
def excl_clusters(r):
    t = txt(r); out=[]
    for name, rx in EXCL:
        if rx.search(t): out.append(name)
    return out

# === 처리 ===
clean=[]; noise=0
for r in d:
    if is_noise(r): noise+=1; continue
    r["bm"] = bm_tag(r)
    r["official"] = bool(OFFICIAL.search(txt(r)))
    r["sponsored"] = bool(SPONSORED.search(txt(r)))
    r["senti"] = senti(r)
    r["start"] = start_bucket(r)
    r["prior"] = prior_path(r)
    r["excl"] = excl_clusters(r)
    clean.append(r)

# 자생(organic) = 자사/협찬 아닌 것
organic = [r for r in clean if not r["official"] and not r["sponsored"]]

def dist(rows, key):
    c=Counter()
    for r in rows:
        v=r[key]
        if isinstance(v,list):
            for x in v: c[x]+=1
        elif v is not None: c[v]+=1
    return dict(c.most_common())

YEARS=["2022","2023","2024","2025","2026"]
def year_cross(rows, key, vals=None):
    table=defaultdict(lambda: Counter())
    for r in rows:
        if r["year"] in YEARS:
            v=r[key]
            for x in (v if isinstance(v,list) else [v]):
                if x is not None: table[x][r["year"]]+=1
    return {k:dict(v) for k,v in table.items()}

# 윤선생 자생만 (경쟁사 제외)
yoon_org = [r for r in organic if r["primary_bucket"].startswith(("bm_","exclude","englvl"))]
nun_org  = [r for r in organic if r["primary_bucket"]=="comp_nunnopi"]
jae_org  = [r for r in organic if r["primary_bucket"]=="comp_jaeneung"]

summary = {
    "raw_total": len(d), "noise_removed": noise, "clean_total": len(clean),
    "organic_total": len(organic), "official": sum(r["official"] for r in clean),
    "sponsored": sum(r["sponsored"] for r in clean),
    "yoon_organic": len(yoon_org), "nunnopi_organic": len(nun_org), "jaeneung_organic": len(jae_org),
    "--- 윤선생 자생 ---":"",
    "BM분포": dist(yoon_org,"bm"),
    "감성분포": dist(yoon_org,"senti"),
    "감성×연도": year_cross(yoon_org,"senti"),
    "시작시점분포": dist([r for r in yoon_org if r["start"]],"start"),
    "사전경로분포": dist([r for r in yoon_org if r["prior"]],"prior"),
    "배제클러스터": dist(yoon_org,"excl"),
    "배제클러스터×연도": year_cross(yoon_org,"excl"),
    "BM별감성": {bm:dist([r for r in yoon_org if r["bm"]==bm],"senti") for bm in ["교실(방문)","베이직(화상)","공통","영어숲(학원)","복합언급"]},
    "--- 경쟁사 자생 ---":"",
    "눈높이_감성": dist(nun_org,"senti"), "재능_감성": dist(jae_org,"senti"),
    "눈높이_배제": dist(nun_org,"excl"), "재능_배제": dist(jae_org,"excl"),
}

json.dump(clean, open(os.path.join(BASE,"yoonsam-trackA-clean.json"),"w"), ensure_ascii=False, indent=1)
json.dump(summary, open(os.path.join(BASE,"yoonsam-trackA-summary.json"),"w"), ensure_ascii=False, indent=2)

print(json.dumps(summary, ensure_ascii=False, indent=2))
