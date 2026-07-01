#!/usr/bin/env python3
"""윤선생 트랙A — 토픽 키워드 빈도 + 신호 광의 재추출 + 대표인용 추출.
정성 해석을 위한 근거 텍스트를 버킷/감성/연도별로 뽑는다."""
import json, re, os
from collections import Counter, defaultdict

BASE = os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")
clean = json.load(open(os.path.join(BASE,"yoonsam-trackA-clean.json")))
def txt(r): return r["title"]+" "+r["description"]

organic = [r for r in clean if not r["official"] and not r["sponsored"]]
yoon = [r for r in organic if r["primary_bucket"].startswith(("bm_","exclude","englvl"))]

# --- 토픽 키워드 사전 (도메인) : 윤선생 자생 멘션에서 빈도 ---
TOPICS = {
 "매일·습관": r"매일|꾸준|습관|루틴|하루 ?[0-9]",
 "발음·파닉스": r"발음|파닉스|소리|음가",
 "말하기·회화·자신감": r"말하기|회화|스피킹|자신감|말문|입이 ?트",
 "관리·케어(선생님)": r"선생님|관리|케어|피드백|첨삭|전화 ?(테스트|확인)|아침 ?전화",
 "레벨테스트·진단": r"레벨 ?테스트|레벨테스트|진단|레벨업|단계",
 "교재·커리큘럼": r"교재|커리큘럼|단계별|체계|스마트랜드|베플리|사운드펀|북",
 "화상·온라인": r"화상|비대면|온라인 ?수업|줌|원격",
 "방문수업": r"방문|집으로|선생님이 ?(와|오)",
 "가격·비용": r"비용|가격|학습비|회비|원\b|만원|가성비",
 "아웃풋·성과": r"아웃풋|성과|결과|실력|점수|레벨 ?향상|향상",
 "흥미·재미": r"재밌|재미있|즐겁|흥미|좋아해|놀이",
 "AI·디지털": r"AI|에이아이|인공지능|스마트|앱\b|디지털|음성인식",
}
def topic_freq(rows):
    c=Counter()
    for r in rows:
        t=txt(r)
        for name,rx in TOPICS.items():
            if re.search(rx,t): c[name]+=1
    return dict(c.most_common())

# --- 사전경로 광의 재추출 ---
PRIOR2 = {
 "영유·어학원 경험": r"영유|영어유치원|어학원|국제학교|킨더|영어 ?유치원",
 "타학습지 경험": r"구몬|눈높이|재능|튼튼영어|빨간펜|기탄|문방|씽크빅|학습지",
 "엄마표·홈스쿨": r"엄마표|아빠표|홈스쿨|흘려듣기|집중듣기|집에서 ?(가르|시작|영어)",
 "동네학원·공부방": r"동네 ?학원|공부방|보습학원|학원 ?다니다|학원 ?보내",
 "처음·첫영어": r"처음 ?영어|첫 ?영어|영어 ?처음|영어 ?입문|영어 ?노출 ?(처음|시작)|영어가 ?처음",
}
def prior_freq(rows):
    c=Counter()
    for r in rows:
        t=txt(r)
        for name,rx in PRIOR2.items():
            if re.search(rx,t): c[name]+=1
    return dict(c.most_common())

# --- 배제사유 광의 (exclude 버킷 + 전체 부정) ---
EXCL2 = {
 "약정·해지·위약금": r"약정|위약금|해지|환불|계약 ?기간|중도 ?해지",
 "가격·가성비 부담": r"비싸|가격 ?부담|돈 ?아깝|가성비|학원비|부담스럽|비용 ?부담",
 "효과·아웃풋 의심": r"효과 ?(없|의문|미미)|실력 ?안|안 ?늘|아웃풋|말이 ?안|성과 ?(없|미미)|제자리",
 "혼자독학·자기주도 부담": r"혼자 ?(해야|앉|하는)|자기주도.{0,4}안|스스로 ?안|엄마 ?손|관리 ?안 ?되",
 "화상·비대면 거부감": r"화상.{0,8}(별로|싫|거부|불편|집중 ?안|산만)|비대면.{0,8}(별로|싫|불편)",
 "방문 부담·불편": r"방문.{0,8}(부담|불편|스트레스|싫|귀찮|눈치)|선생님 ?(오시|방문).{0,6}부담",
 "끼워팔기·영업·강매": r"끼워팔|패드.{0,6}(세트|구매)|세트.{0,6}구매|영업|강매|결제 ?유도|권유 ?부담",
 "교재·콘텐츠 불만": r"교재.{0,6}(별로|구식|노후|오래|부실)|지루|흥미 ?없|콘텐츠 ?부족|반복.{0,4}지루",
 "성과편차·아이성향": r"아이 ?성향|안 ?맞|편차|애마다|기질|집중 ?못",
}
def excl_freq(rows):
    c=Counter()
    for r in rows:
        t=txt(r)
        for name,rx in EXCL2.items():
            if re.search(rx,t): c[name]+=1
    return dict(c.most_common())

def quotes(rows, n=12, maxlen=160):
    out=[]
    for r in rows[:n]:
        out.append(f"[{r['year']}|{r['bm']}|{r['senti']}] {r['description'][:maxlen]}")
    return out

exclude_bucket = [r for r in yoon if r["primary_bucket"]=="exclude"]
neg = [r for r in yoon if r["senti"]=="부"]
englvl_bucket = [r for r in yoon if r["primary_bucket"]=="englvl"]
bangmun = [r for r in yoon if r["bm"]=="교실(방문)"]
basic = [r for r in yoon if r["bm"]=="베이직(화상)"]
common = [r for r in yoon if r["bm"]=="공통"]

result = {
 "토픽_전체": topic_freq(yoon),
 "토픽_교실방문": topic_freq(bangmun),
 "토픽_베이직화상": topic_freq(basic),
 "토픽_공통": topic_freq(common),
 "사전경로_광의(englvl+전체)": prior_freq(yoon),
 "사전경로_englvl버킷": prior_freq(englvl_bucket),
 "배제_광의(exclude버킷)": excl_freq(exclude_bucket),
 "배제_광의(전체부정)": excl_freq(neg),
 "_샘플_부정_2026": quotes([r for r in neg if r["year"]=="2026"]),
 "_샘플_부정_2025": quotes([r for r in neg if r["year"]=="2025"]),
 "_샘플_배제버킷": quotes(exclude_bucket, 15),
 "_샘플_영유경험": quotes([r for r in yoon if re.search(PRIOR2["영유·어학원 경험"], txt(r))], 12),
 "_샘플_타학습지": quotes([r for r in yoon if re.search(PRIOR2["타학습지 경험"], txt(r))], 12),
 "_샘플_초1이전시작": quotes([r for r in englvl_bucket if r["start"]=="초1이전"], 10),
}
json.dump(result, open(os.path.join(BASE,"yoonsam-trackA-topics.json"),"w"), ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False, indent=2))
