#!/usr/bin/env python3
"""③ 배제 — 본문 700건 1차 분류(광고/이탈/배제/무관) + 배제후보 추출."""
import json, re, os
from collections import Counter
B=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam/")
rows=json.load(open(B+"q3-body.json"))
def bd(r): return r.get("body","")

MKT=re.compile(r"상담\s?(문의|예약|신청)|등록\s?문의|문의\s?(주세요|환영|바랍)|모집\s?(중|안내|합니다)|"
 r"전화\s?(상담|문의)|\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4}|카카오\s?채널|네이버\s?예약|오시는\s?길|"
 r"저희\s?(센터|학원|교습소|지점)|원장입니다|쌤입니다|선생님입니다|공식\s?블로그|체험\s?수업\s?신청|"
 r"수강료\s?안내|개원|오픈\s?이벤트|등록\s?(이벤트|혜택)|레벨테스트\s?(신청|예약)")
# 1인칭 소비자 화자
VOICE=re.compile(r"우리\s?(아이|아들|딸|애)|제\s?(아이|딸|아들)|저는|제가|엄마표|내돈내산|어릴\s?때|둘째|첫째|우리집")
# 이탈(써본 뒤 그만둠)
CHURN=re.compile(r"(윤선생).{0,30}(끊었|그만뒀|그만두|중단했|해지했|관뒀)|(\d년|개월).{0,12}(하다가|다니다가).{0,12}(끊|그만)")
# 배제(고려했지만 진입 안함)
EXCL=re.compile(r"안\s?시키|안\s?했|안\s?하기|패스|대신|말고|거른|걸렀|제외|뺐|안\s?보내|고민.{0,20}(다른|결국|선택)|"
 r"전집.{0,10}부담|패드.{0,10}(필수|부담)|비싸서\s?(안|못|패스)|체험.{0,8}없어")

def classify(r):
    b=bd(r)
    if MKT.search(b[:700]) and not VOICE.search(b): return "광고"
    if not VOICE.search(b): return "무관/광고"
    if CHURN.search(b): return "이탈"
    if EXCL.search(b): return "배제"
    return "기타자생"

cls=Counter(); excl_cand=[]
for r in rows:
    c=classify(r); cls[c]+=1
    if c=="배제": excl_cand.append(r)

# 배제후보 클러스터 1차(본문)
CL={"전집·패드 필수구매":r"전집.{0,12}(필수|구매|사야|부담|값)|패드.{0,12}(필수|구매|부담)|세트.{0,10}구매|기기\s?구매",
 "가격·가성비":r"비싸|가격\s?부담|돈\s?아깝|가성비|학원비|부담스럽|인건비|too\s?expensive",
 "혼자독학·관리부담":r"혼자\s?(해야|하는|앉)|자기주도.{0,6}안|스스로\s?안|엄마\s?(손|가\s?직접|몫)|관리\s?안|방문\s?없",
 "효과·아웃풋 의심":r"효과\s?(없|의문|글쎄|미미)|안\s?늘|제자리|아웃풋\s?안|말\s?안|실력\s?(차이|안)",
 "체험·맛보기 부재":r"체험.{0,8}(없|안\s?되|부재)|맛보기\s?없|시범\s?없",
 "화상·비대면 거부감":r"화상.{0,10}(별로|싫|거부|불편|집중\s?안|산만|걱정)|비대면.{0,10}(별로|불편|걱정)",
 "약정·해지":r"약정|위약금|해지\s?(어렵|안)|환불\s?(안|어렵)",
 "경쟁사 선호":r"(눈높이|구몬|튼튼|잉에그|캠블리|화상영어|퍼플|학원).{0,14}(선택|결정|하기로|골랐|보내|로\s?갔)"}
clc=Counter()
for r in excl_cand:
    b=bd(r)
    for nm,rx in CL.items():
        if re.search(rx,b): clc[nm]+=1

print(f"③ 본문 {len(rows)}건 1차 분류:")
for k,v in cls.most_common(): print(f"  {k}: {v}")
print(f"\n배제후보 {len(excl_cand)}건 → 클러스터(본문 1차, 복수가능):")
for k,v in clc.most_common(): print(f"  {k}: {v}")
# 워커용: 배제후보 본문 저장(앞 1200자)
slim=[{"year":r["year"],"link":r["link"],"body":bd(r)[:1200]} for r in excl_cand]
json.dump(slim, open(B+"q3-exclude-candidates.json","w"), ensure_ascii=False, indent=1)
print(f"\n저장: q3-exclude-candidates.json ({len(slim)}건, 워커 정독용)")
