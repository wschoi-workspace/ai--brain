#!/usr/bin/env python3
"""5개 브랜드 인식 차원 매트릭스 + 시간흐름.
브랜드: 윤선생 / 눈높이 / 재능 / 삼성영어 / 뮤엠영어 (정상JLS 참조).
각 브랜드 자생 풀 정제 → 9개 인식 차원 언급률·감성 → 연도별(24/25/26) 추이."""
import json, re, os
from collections import Counter, defaultdict
BASE=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")
def t(r): return r.get("title","")+" "+r.get("description","")
YRS=["2022","2023","2024","2025","2026"]

# 공통 정제
ON=re.compile(r"영어|파닉스|학습지|화상|방문|레벨|리딩|단어|문법|회화|원어민|발음|학원|어학|읽기|듣기|쓰기|수업|교재|아이|초등|유아")
MKTG=re.compile(r"쌤입니다|선생님입니다|센터입니다|원장입니다|상담\s?(문의|신청|환영|예약)|문의\s?(주세요|환영|바랍)|"
 r"등록\s?문의|모집(합니다|중|안내)|체험\s?(신청|예약)|\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4}|가맹|창업|소자본|여성창업")
# 브랜드별 동음이의 노이즈
OFF={
 "공통": r"맛집|불고기|레시피|마스크|KF94|안경원|간판|인테리어|리모델링|네일|펜션|여행 ?(갔|다녀)|주식|코인",
 "삼성영어": r"삼성전자|갤럭시|반도체|삼성물산|삼성동|삼성역|삼성카드|삼성생명|삼성서울병원|이재용|삼성바이오|삼성중공업|삼성SDI|주가",
 "재능": r"재능기부|재능마켓|숨고|크몽|재능있|재능을 ?기부|탤런트",
 "정상JLS": r"정상 ?컨디션|정상 ?체중|정상 ?범위|정상 ?작동|혈압 ?정상|정상 ?궤도|산 ?정상|등산",
}
POS=re.compile(r"좋아요|좋았|만족|추천|효과 ?(좋|있)|늘었|향상|즐겁|재밌|재미있|꾸준|도움|자신감|강추|최고|잘 ?(늘|해|함)")
NEG=re.compile(r"별로|비추|단점|아쉽|불만|후회|그만|끊|해지|위약금|환불|실망|효과 ?없|안 ?늘|돈 ?아깝|부담|스트레스|최악")
def senti(r):
    x=t(r); p=len(POS.findall(x)); n=len(NEG.findall(x))
    return "긍" if p>n else "부" if n>p else "중"
def is_clean(r, brand):
    x=t(r)
    if re.search(OFF["공통"],x): return False
    if brand in OFF and re.search(OFF[brand],x): return False
    if not ON.search(x): return False
    if MKTG.search(x): return False
    return True

# 인식 차원 9종
DIM={
 "발음·원어민성": r"발음|파닉스|원어민|네이티브|소리|음가|콩글리시|네이티브",
 "관리·케어":    r"관리|케어|선생님이|피드백|첨삭|꼼꼼|챙겨|밀착|관리해|선생님께서",
 "가격·가성비":  r"가격|비용|학원비|회비|가성비|비싸|저렴|만원|월 ?\d|수강료|교재비",
 "자기주도·습관": r"자기주도|스스로|습관|매일|꾸준|루틴|혼자",
 "디지털·AI":    r"AI|인공지능|스마트|앱\b|패드|디지털|음성인식|화상|온라인|줌|태블릿|기기",
 "효과·아웃풋":  r"효과|실력|향상|아웃풋|성과|점수|레벨업|결과|늘었|말문|말하기",
 "흥미·재미":    r"재밌|재미있|즐겁|흥미|놀이|좋아해|신나|흥미로",
 "신뢰·전통":    r"전통|오래|믿을|신뢰|역사|\d+년째|\d+년 ?전통|대기업|브랜드|유명",
 "접근성·편의":  r"방문|화상|등원|센터|집에서|집으로|가까|동네|통원|픽업|셔틀",
}
def dim_profile(rows):
    N=len(rows); out={}
    for d,rx in DIM.items():
        hit=[r for r in rows if re.search(rx,t(r))]
        h=len(hit)
        sc=Counter(senti(r) for r in hit)
        out[d]={"n":h,"rate":round(h/N*100,1) if N else 0,
                "pos":sc.get("긍",0),"neg":sc.get("부",0),
                "pos_rate":round(sc.get("긍",0)/h*100) if h else 0,
                "neg_rate":round(sc.get("부",0)/h*100) if h else 0}
    return out
def dim_year(rows,d):
    rx=DIM[d]
    return {y:sum(1 for r in rows if r["year"]==y and re.search(rx,t(r))) for y in YRS}
def senti_year(rows):
    out={}
    for y in YRS:
        rr=[r for r in rows if r["year"]==y]; sc=Counter(senti(r) for r in rr)
        out[y]={"총":len(rr),"긍":sc.get("긍",0),"중":sc.get("중",0),"부":sc.get("부",0)}
    return out

# 데이터 로드
clean=json.load(open(BASE+"/yoonsam-trackA-clean.json"))
parent=json.load(open(BASE+"/yoonsam-parent-organic.json"))
trackB=json.load(open(BASE+"/trackB-naver-raw.json"))

# 브랜드 풀 구성 (link dedup)
def merge(*pools):
    seen={};
    for pool in pools:
        for r in pool:
            if r["link"] not in seen: seen[r["link"]]=r
    return list(seen.values())

yoon = parent  # 윤선생 전체 자생 (1861)
nun_a = [r for r in clean if r["primary_bucket"]=="comp_nunnopi"]
nun_b = [r for r in trackB if r["brand"]=="눈높이boost"]
jae_a = [r for r in clean if r["primary_bucket"]=="comp_jaeneung"]
jae_b = [r for r in trackB if r["brand"]=="재능boost"]
sam   = [r for r in trackB if r["brand"]=="삼성영어"]
mum   = [r for r in trackB if r["brand"]=="뮤엠영어"]
jls   = [r for r in trackB if r["brand"]=="정상JLS"]

brands_raw={
 "윤선생": (yoon,"공통"),
 "눈높이": (merge(nun_a,nun_b),"공통"),
 "재능":   (merge(jae_a,jae_b),"재능"),
 "삼성영어":(sam,"삼성영어"),
 "뮤엠영어":(mum,"뮤엠영어"),
 "정상JLS":(jls,"정상JLS"),
}
result={"_clean_counts":{}, "차원매트릭스":{}, "감성연도":{}, "차원연도":{}}
cleaned={}
for b,(rows,key) in brands_raw.items():
    cr=[r for r in rows if is_clean(r,key)]
    cleaned[b]=cr
    yd={y:sum(1 for r in cr if r["year"]==y) for y in YRS}
    result["_clean_counts"][b]={"N":len(cr),"연도":yd}
    result["차원매트릭스"][b]=dim_profile(cr)
    result["감성연도"][b]=senti_year(cr)
# 차원별 연도추이 (5개 핵심 브랜드만)
for b in ["윤선생","눈높이","재능","삼성영어","뮤엠영어"]:
    result["차원연도"][b]={d:dim_year(cleaned[b],d) for d in DIM}

json.dump(result, open(BASE+"/perception-matrix.json","w"), ensure_ascii=False, indent=2)
# 콘솔 요약
print("=== 정제 N ===")
for b,v in result["_clean_counts"].items(): print(f"  {b:8s} N={v['N']:5d}  연도{v['연도']}")
print("\n=== 차원 언급률(%) — 브랜드×차원 ===")
dims=list(DIM.keys())
print("브랜드     "+" ".join(f"{d[:4]:>5s}" for d in dims))
for b in ["윤선생","눈높이","재능","삼성영어","뮤엠영어"]:
    m=result["차원매트릭스"][b]
    print(f"{b:8s} "+" ".join(f"{m[d]['rate']:5.1f}" for d in dims))
print("\n=== 차원 부정률(%) ===")
for b in ["윤선생","눈높이","재능","삼성영어","뮤엠영어"]:
    m=result["차원매트릭스"][b]
    print(f"{b:8s} "+" ".join(f"{m[d]['neg_rate']:5d}" for d in dims))
