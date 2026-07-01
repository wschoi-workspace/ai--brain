#!/usr/bin/env python3
"""② 영어수준 — 본문 기반 시작시점×동기 매트릭스 재추출 (스니펫 한계 돌파)."""
import json, re, os
from collections import Counter
B=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam/")
rows=json.load(open(B+"q2-body.json"))
def bd(r): return r.get("body","")

# 1인칭 학부모/학습자 화자 게이트 (가맹 마케팅 본문 제외)
MKT=re.compile(r"상담\s?(문의|예약|신청)|등록\s?문의|문의\s?(주세요|환영|바랍)|수강\s?문의|모집\s?(중|안내|합니다)|"
 r"전화\s?(상담|문의)|\d{2,3}[-.\s]?\d{3,4}[-.\s]?\d{4}|카카오\s?채널|네이버\s?예약|위치|오시는\s?길|"
 r"저희\s?(센터|학원|교습소)|원장입니다|쌤입니다|선생님입니다|공식\s?블로그|체험\s?수업\s?신청")
def is_parent(r):
    b=bd(r)
    # 1인칭 회고/육아 신호
    voice=re.search(r"우리\s?(아이|아들|딸|애)|제\s?(아이|딸|아들)|저는|제가|엄마표|내돈내산|어릴\s?때|초등학교\s?때|둘째|첫째", b)
    return bool(voice) and not bool(MKT.search(b[:600]))

# 시작연령 → 버킷 (본문에서 '시작/부터' 근처 나이 우선)
def start_bucket(b):
    # 개월(유아)
    if re.search(r"(\d{2})\s?개월.{0,10}(부터|시작|때)", b) or re.search(r"(돌|두\s?돌|세\s?돌).{0,8}(부터|시작)", b): return "초1이전"
    for pat,bucket in [
        (r"([4-7])\s?살.{0,12}(부터|시작|때)","초1이전"),(r"([4-7])\s?세.{0,12}(부터|시작|때)","초1이전"),
        (r"(유아|유치원|미취학|취학\s?전|어린이집).{0,14}(부터|시작|영어)","초1이전"),
        (r"(초1|초등\s?1|1학년|여덟\s?살|8\s?살)","초1~2"),(r"(초2|초등\s?2|2학년|아홉\s?살|9\s?살)","초1~2"),
        (r"(초3|초등\s?3|3학년|열\s?살|10\s?살)","초3~4"),(r"(초4|초등\s?4|4학년|11\s?살)","초3~4"),
        (r"(초5|초등\s?5|5학년|초6|6학년|중1|중학)","초4이후"),
    ]:
        if re.search(pat,b): return bucket
    return None

MOT_INT=re.compile(r"흥미|재미있|재밌|좋아해|거부감|즐겁|놀이|기초\s?(부터|다지|만회)|파닉스\s?부터|처음\s?영어|입문|자신감|습관\s?(들|형성)|영어랑\s?친해|노출")
MOT_RES=re.compile(r"선행|내신|시험|점수|성적|레벨\s?업|상위|뒤처지지|앞서|대비|결과|아웃풋|등급|수능|영재|특목|경시|input|인풋")
def motive(b):
    i=len(MOT_INT.findall(b)); r=len(MOT_RES.findall(b))
    if i>r and i>0: return "흥미·기초만회"
    if r>i and r>0: return "결과·선행"
    if i==r and i>0: return "혼합"
    return None

PRIOR={"영유·어학원졸업→":r"영유.{0,8}(졸업|나온|나와|끝|수료|마치)|영어유치원.{0,8}(졸업|나온|끝)|어학원.{0,8}(다니다|끊|그만|졸업)",
 "타학습지이탈→":r"(구몬|눈높이|재능|튼튼영어|빨간펜|기탄|씽크빅).{0,14}(하다가|그만|끊|에서|다니다|했었|하다)",
 "엄마표→":r"엄마표|아빠표|홈스쿨|흘려듣기|집중듣기|집에서\s?(가르|하다)",
 "처음영어→":r"처음\s?영어|첫\s?영어|영어\s?(가\s?)?처음|영어\s?입문|영어\s?노출\s?(처음|시작)"}

parent=[r for r in rows if is_parent(r)]
mat=Counter(); pri=Counter(); buckets=Counter(); unknown_mot=0; samples={}
for r in parent:
    b=bd(r); sb=start_bucket(b)
    if not sb: continue
    buckets[sb]+=1
    mv=motive(b)
    speed={"초1이전":"빨리","초1~2":"평균","초3~4":"늦게","초4이후":"늦게"}[sb]
    if mv: mat[(speed,mv)]+=1
    else: unknown_mot+=1
    for nm,rx in PRIOR.items():
        if re.search(rx,b): pri[nm]+=1
    # 대표 샘플 저장
    key=(speed,mv)
    if mv and key not in samples:
        m=re.search(r".{0,40}(시작|부터|처음).{0,60}", b); samples[key]=(r["year"], (m.group(0).strip() if m else b[:90]))

total_aged=sum(buckets.values())
print(f"본문 크롤 {len(rows)} → 1인칭 자생 {len(parent)} → 시작연령 확정 {total_aged}")
print("시작시점 버킷:",dict(buckets))
print(f"동기 미상: {unknown_mot}/{total_aged} ({unknown_mot/total_aged*100:.0f}%)  [이전 스니펫: 83%]")
print("\n매트릭스 (시작속도×동기):")
for sp in ["빨리","평균","늦게"]:
    print(f"  {sp}: 흥미·기초만회={mat.get((sp,'흥미·기초만회'),0)} / 결과·선행={mat.get((sp,'결과·선행'),0)} / 혼합={mat.get((sp,'혼합'),0)}")
print("\n사전경로:",dict(pri.most_common()))
print("\n대표샘플:")
for k,v in list(samples.items())[:8]: print(f"  {k}: [{v[0]}] {v[1][:80]}")
out={"crawled":len(rows),"parent":len(parent),"aged":total_aged,"buckets":dict(buckets),
 "unknown_motive_pct":round(unknown_mot/total_aged*100),"matrix":{f"{k[0]}×{k[1]}":v for k,v in mat.items()},
 "prior":dict(pri.most_common())}
json.dump(out, open(B+"q2-result.json","w"), ensure_ascii=False, indent=2)
