#!/usr/bin/env python3
"""윤선생 트랙A 강한 정제 v3.
(1) 동음이의·무관 도메인 강제거 (2) 영어교육 맥락 positive 필터
(3) 가맹점 교사 마케팅 vs 학부모 자생 후기 분리 (Sincerity).
출력: 진짜 학부모 자생 후기 풀 + 가맹마케팅 풀 + 규모 보고."""
import json, re, os
from collections import Counter
BASE = os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")
clean = json.load(open(os.path.join(BASE,"yoonsam-trackA-clean.json")))
def txt(r): return r["title"]+" "+r["description"]

# (1) 동음이의·무관 도메인 — 윤선생이 영어가 아닌 맥락
OFFTOPIC = re.compile(
 r"투자|주식|배터리|반도체|전고체|레이더|자율주행|종목|매수|매도|佛投|불투|마진율|양산|전구체|반도체|"
 r"집밥|반찬|레시피|돈까스|떡볶이|오리불고기|사우나|온탕|착샷|PD ?72|"
 r"마스크|KF94|안경원|국민행복카드|카드사|청구할인|피킹률|"
 r"몰몬교|그리스도후기성도|용선생|화백|여행 ?(갔|다녀)|일본 여행|도쿄|"
 r"인테리어|리모델링|간판|큐리매쓰|수학학원 간판|수학원")

# (2) 영어교육 맥락 필수 (positive)
ONTOPIC = re.compile(
 r"영어|파닉스|학습지|영어교실|베이직|스마트랜드|레벨테스트|리딩|어학|영단어|문법|회화|"
 r"영어학원|스피킹|파닉|읽기|듣기|쓰기|원어민|커리큘럼|영어유치원|영유")

# (3) 가맹점 교사 마케팅 신호 (Sincerity 낮음 → 자생 아님)
MARKETING = re.compile(
 r"쌤입니다|선생님입니다|센터입니다|센터장|원장입니다|입니다\.?\s*$|"
 r"상담\s?(문의|신청|환영|예약)|전화\s?상담|문의\s?(주세요|환영|바랍|전화)|"
 r"등록\s?(문의|환영|상담)|모집(합니다|중|안내)|체험\s?(신청|수업\s?신청|예약)|"
 r"\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4}|"            # 전화번호
 r"#.*점\b|#.*센터\b|#.*동영어|지점|우리집앞영어교실 .*쌤|해밀센터|스마트랜드 .*센터|"
 r"오픈\s?이벤트|가맹|창업|소자본|여성창업|교육창업|선생님을?\s?모집")

yoon_all = [r for r in clean if r["primary_bucket"].startswith(("bm_","exclude","englvl"))]
offtopic=0; not_eng=0
parent=[]; marketing=[]
for r in yoon_all:
    t=txt(r)
    if OFFTOPIC.search(t): offtopic+=1; continue
    if not ONTOPIC.search(t): not_eng+=1; continue
    if MARKETING.search(t) or r["official"] or r["sponsored"]:
        r["src"]="가맹마케팅"; marketing.append(r)
    else:
        r["src"]="학부모자생"; parent.append(r)

def dist(rows,key):
    c=Counter()
    for r in rows:
        v=r[key]
        for x in (v if isinstance(v,list) else [v]):
            if x is not None: c[x]+=1
    return dict(c.most_common())

YEARS=["2022","2023","2024","2025","2026"]
report = {
 "원본_윤선생버킷": len(yoon_all),
 "제거_동음이의무관": offtopic,
 "제거_영어맥락아님": not_eng,
 "가맹마케팅_분리": len(marketing),
 "학부모자생_확정": len(parent),
 "자생_연도분포": {y:sum(1 for r in parent if r["year"]==y) for y in YEARS},
 "자생_BM분포": dist(parent,"bm"),
 "마케팅_BM분포": dist(marketing,"bm"),
}
json.dump(parent, open(os.path.join(BASE,"yoonsam-parent-organic.json"),"w"), ensure_ascii=False, indent=1)
json.dump(marketing, open(os.path.join(BASE,"yoonsam-franchise-mktg.json"),"w"), ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False, indent=2))
