#!/usr/bin/env python3
"""트랙B + 경쟁사 통합 보강 수집 (네이버 블로그 API).
브랜드: 윤선생영어숲(boost) / 삼성영어 / 뮤엠영어 / 정상JLS(참조) / 눈높이·재능(보강)."""
import os, json, re, time, html, urllib.parse, urllib.request
ENV={}
for line in open(os.path.expanduser("~/do-better-workspace/.env")):
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); ENV[k.strip()]=v.strip()
CID,CSEC=ENV["NAVER_CLIENT_ID"],ENV["NAVER_CLIENT_SECRET"]
BASE=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")

QUERIES={
 "윤선생영어숲": ["윤선생 영어숲 후기","윤선생 영어숲 학원","윤선생영어 센터 후기","윤선생 영어숲 레벨테스트","윤선생 영어숲 단점"],
 "삼성영어":   ["삼성영어 후기","삼성영어 학원","삼성영어 단점","삼성영어 효과","삼성영어 레벨테스트","삼성영어 비추","삼성영어 파닉스","삼성영어 vs","삼성영어 셀레나"],
 "뮤엠영어":   ["뮤엠영어 후기","뮤엠영어 학원","뮤엠영어 단점","뮤엠영어 효과","뮤엠 영어 후기","뮤엠영어 레벨테스트","뮤엠영어 비추","뮤엠영어 화상"],
 "정상JLS":    ["정상제이엘에스 후기","정상 JLS 영어","JLS 영어학원 후기","정상어학원 후기"],
 "눈높이boost":["눈높이 영어 파닉스","눈높이 영어 화상","눈높이 영어 vs","눈높이 영어 단점","눈높이 영어 효과","눈높이 영어 원어민","눈높이 영어 비추"],
 "재능boost":  ["재능스스로 영어 후기","재능 영어 효과","재능교육 영어 단점","JEI 영어","재능스스로펜","재능 영어 원어민","재능 영어 비추"],
}
def strip(s): return html.unescape(re.sub(r"<[^>]+>","",s)).strip()
def search(q,start=1):
    url="https://openapi.naver.com/v1/search/blog.json?"+urllib.parse.urlencode(
        {"query":q,"display":100,"start":start,"sort":"date"})
    req=urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id",CID); req.add_header("X-Naver-Client-Secret",CSEC)
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read().decode())

seen={}
for brand,qs in QUERIES.items():
    for q in qs:
        got=0
        for start in (1,101):
            try: res=search(q,start)
            except Exception as e: print(f"! {q}: {e}"); break
            items=res.get("items",[])
            if not items: break
            for it in items:
                link=it.get("link","")
                if link in seen:
                    seen[link]["matched"].append(f"{brand}:{q}"); continue
                pd=it.get("postdate","")
                seen[link]={"title":strip(it.get("title","")),"description":strip(it.get("description","")),
                    "link":link,"bloggername":it.get("bloggername",""),"bloggerlink":it.get("bloggerlink",""),
                    "postdate":pd,"year":pd[:4] if len(pd)>=4 else "미상",
                    "brand":brand,"primary_query":q,"matched":[f"{brand}:{q}"]}
                got+=1
            time.sleep(0.12)
        print(f"  {brand:14s} | {q:22s} → 신규 {got}")
recs=list(seen.values())
from collections import Counter
bd=Counter(r["brand"] for r in recs); yd=Counter(r["year"] for r in recs if r["year"] in ["2022","2023","2024","2025","2026"])
json.dump(recs, open(os.path.join(BASE,"trackB-naver-raw.json"),"w"), ensure_ascii=False, indent=1)
print(f"\n총 {len(recs)}건 / 브랜드:{dict(bd)} / 연도:{dict(sorted(yd.items()))}")
