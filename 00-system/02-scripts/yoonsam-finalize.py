#!/usr/bin/env python3
"""배제보강 정제 + 시간흐름(STEP5) + 경쟁사(STEP6) 집계 정리."""
import json, re, os
from collections import Counter
BASE=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")
def txt(r): return r["title"]+" "+r["description"]

OFFTOPIC=re.compile(r"투자|주식|배터리|반도체|전고체|레이더|자율주행|종목|매수|매도|佛投|불투|마진율|양산|전구체|"
 r"집밥|반찬|레시피|돈까스|떡볶이|오리불고기|사우나|온탕|착샷|마스크|KF94|안경원|국민행복카드|카드사|청구할인|"
 r"몰몬교|용선생|화백|일본 여행|도쿄|인테리어|리모델링|간판|큐리매쓰|수학학원 간판|수학원|네일|미용실|펜션")
ONTOPIC=re.compile(r"영어|파닉스|학습지|영어교실|베이직|스마트랜드|레벨테스트|리딩|어학|영단어|문법|회화|"
 r"영어학원|스피킹|읽기|듣기|쓰기|원어민|커리큘럼|영어유치원|영유|전집|패드|화상")
MARKETING=re.compile(r"쌤입니다|선생님입니다|센터입니다|센터장|원장입니다|상담\s?(문의|신청|환영|예약)|"
 r"전화\s?상담|문의\s?(주세요|환영|바랍|전화)|등록\s?(문의|환영)|모집(합니다|중|안내)|체험\s?(신청|예약)|"
 r"\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4}|가맹|창업|소자본|여성창업|선생님을?\s?모집")

# --- 배제보강 정제 ---
boost=json.load(open(os.path.join(BASE,"yoonsam-exclude-boost-raw.json")))
excl_parent=[]; off=0; noteng=0; mktg=0
for r in boost:
    t=txt(r)
    if OFFTOPIC.search(t): off+=1; continue
    if not ONTOPIC.search(t): noteng+=1; continue
    if MARKETING.search(t): mktg+=1; continue
    excl_parent.append(r)

# 배제사유 클러스터 (정독 보조용 광의)
EXCL={
 "전집·패드·세트 필수구매": r"전집.{0,8}(필수|구매|사야|부담)|패드.{0,8}(필수|세트|구매)|세트.{0,8}(구매|사야)|기기.{0,6}구매",
 "가격·가성비 부담": r"비싸|가격 ?부담|돈 ?아깝|가성비|학원비|부담스럽|비용 ?부담|인건비",
 "혼자독학·관리부담": r"혼자 ?(해야|앉|하는|하다)|자기주도.{0,4}안|스스로 ?안|엄마 ?(손|가|직접)|관리 ?안 ?되|방문.{0,4}없",
 "효과·아웃풋 의심": r"효과 ?(없|의문|미미|글쎄)|실력 ?안|안 ?늘|아웃풋|말이 ?안|성과 ?(없|미미)|제자리|머리가",
 "체험·맛보기 부재": r"체험.{0,6}(없|안|부재)|맛보기 ?없|레벨테스트.{0,6}없",
 "화상·비대면 거부감": r"화상.{0,10}(별로|싫|거부|불편|집중 ?안|산만|아쉽)|비대면.{0,8}(별로|싫|불편)",
 "약정·해지·위약금": r"약정|위약금|해지|환불|계약 ?기간|중도 ?해지",
 "경쟁사 비교후 타사선택": r"(눈높이|구몬|튼튼|잉에그|화상영어|퍼플|캠블리).{0,12}(선택|결정|하기로|골랐|로 ?갔)",
}
def cl(rows):
    c=Counter()
    for r in rows:
        t=txt(r)
        for n,rx in EXCL.items():
            if re.search(rx,t): c[n]+=1
    return dict(c.most_common())

YEARS=["2022","2023","2024","2025","2026"]
def yc(rows,rx):
    return {y:sum(1 for r in rows if r["year"]==y and re.search(rx,txt(r))) for y in YEARS}

# --- STEP5 시간흐름: parent-organic 기준 ---
parent=json.load(open(os.path.join(BASE,"yoonsam-parent-organic.json")))
POS=re.compile(r"좋아요|좋았|만족|추천|효과 ?(좋|있)|늘었|향상|즐겁|재밌|재미있|꾸준|도움|자신감|강추|최고")
NEG=re.compile(r"별로|비추|단점|아쉽|불만|후회|그만|끊|해지|위약금|환불|실망|효과 ?없|안 ?늘|돈 ?아깝|부담|스트레스")
def senti_re(r):
    t=txt(r); p=len(POS.findall(t)); n=len(NEG.findall(t))
    return "긍" if p>n else "부" if n>p else "중"
timeflow={y:{"총": sum(1 for r in parent if r["year"]==y)} for y in YEARS}
for y in YEARS:
    rows=[r for r in parent if r["year"]==y]
    sc=Counter(senti_re(r) for r in rows)
    timeflow[y].update({"긍":sc.get("긍",0),"중":sc.get("중",0),"부":sc.get("부",0)})
# 신규/소멸 토픽 신호: 연도별 키워드
def kw_year(kw):
    return {y:sum(1 for r in parent if r["year"]==y and re.search(kw,txt(r))) for y in YEARS}
topic_trend={
 "AI·디지털(스마트베플리/음성)": kw_year(r"AI|인공지능|음성인식|스마트베플리|디지털"),
 "화상·비대면": kw_year(r"화상|비대면|줌"),
 "무약정·3무": kw_year(r"무약정|약정 ?없|3무"),
 "전집·패드": kw_year(r"전집|패드"),
 "파닉스": kw_year(r"파닉스"),
}

# --- STEP6 경쟁사: clean.json ---
clean=json.load(open(os.path.join(BASE,"yoonsam-trackA-clean.json")))
def comp(bucket):
    rows=[r for r in clean if r["primary_bucket"]==bucket and not r["official"] and not r["sponsored"]
          and not OFFTOPIC.search(txt(r)) and ONTOPIC.search(txt(r)) and not MARKETING.search(txt(r))]
    sc=Counter(senti_re(r) for r in rows)
    yr={y:sum(1 for r in rows if r["year"]==y) for y in YEARS}
    return {"N":len(rows),"감성":dict(sc),"연도":yr}

out={
 "배제보강_원본": len(boost),"배제보강_offtopic제거":off,"배제보강_영어아님":noteng,"배제보강_마케팅제거":mktg,
 "배제보강_자생확정": len(excl_parent),
 "배제클러스터(보강자생)": cl(excl_parent),
 "배제클러스터_연도_전집패드": yc(excl_parent,EXCL["전집·패드·세트 필수구매"]),
 "배제클러스터_연도_관리부담": yc(excl_parent,EXCL["혼자독학·관리부담"]),
 "배제클러스터_연도_화상거부": yc(excl_parent,EXCL["화상·비대면 거부감"]),
 "STEP5_시간흐름_자생": timeflow,
 "STEP5_토픽추이": topic_trend,
 "STEP6_눈높이": comp("comp_nunnopi"),
 "STEP6_재능": comp("comp_jaeneung"),
}
# 배제보강 자생 저장(워커 정독용)
json.dump(excl_parent, open(os.path.join(BASE,"yoonsam-exclude-parent.json"),"w"), ensure_ascii=False, indent=1)
json.dump(out, open(os.path.join(BASE,"yoonsam-final-agg.json"),"w"), ensure_ascii=False, indent=2)
print(json.dumps(out, ensure_ascii=False, indent=2))
