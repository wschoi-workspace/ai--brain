#!/usr/bin/env python3
"""트랙C — 화상 영어 경쟁사 수집 (윤선생베이직 직접 경쟁).
브랜드: 시원스쿨 / 윙크 / 천재교육 / 캠블리키즈."""
import os, json, re, time, html, urllib.parse, urllib.request
ENV={}
for line in open(os.path.expanduser("~/do-better-workspace/.env")):
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); ENV[k.strip()]=v.strip()
CID,CSEC=ENV["NAVER_CLIENT_ID"],ENV["NAVER_CLIENT_SECRET"]
BASE=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")

QUERIES={
 "시원스쿨":  ["시원스쿨 키즈 후기","시원스쿨 영어 후기","시원스쿨 단점","시원스쿨 화상","시원스쿨 효과","시원스쿨 비추","시원스쿨 레벨","시원스쿨 어린이"],
 "윙크":     ["윙크 영어 후기","윙크 화상영어","윙크 영어 단점","윙크 영어 효과","윙크 학습 후기","윙크 영어 비추","윙크 한글나라 영어"],
 "천재교육":  ["천재교육 영어 후기","밀크티 영어 후기","천재 화상영어","천재교육 영어 단점","밀크티 초등 영어","천재교육 영어 효과","천재 밀크티 비추"],
 "캠블리키즈": ["캠블리키즈 후기","캠블리 키즈 영어","캠블리 화상영어 후기","캠블리키즈 단점","캠블리 효과","캠블리키즈 비추","캠블리키즈 레벨","캠블리 어린이 영어"],
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
                if link in seen: seen[link]["matched"].append(f"{brand}:{q}"); continue
                pd=it.get("postdate","")
                seen[link]={"title":strip(it.get("title","")),"description":strip(it.get("description","")),
                    "link":link,"bloggername":it.get("bloggername",""),"bloggerlink":it.get("bloggerlink",""),
                    "postdate":pd,"year":pd[:4] if len(pd)>=4 else "미상",
                    "brand":brand,"primary_query":q,"matched":[f"{brand}:{q}"]}
                got+=1
            time.sleep(0.12)
        print(f"  {brand:8s} | {q:20s} → 신규 {got}")
recs=list(seen.values())
from collections import Counter
bd=Counter(r["brand"] for r in recs); yd=Counter(r["year"] for r in recs if r["year"] in ["2022","2023","2024","2025","2026"])
json.dump(recs, open(BASE+"/trackC-naver-raw.json","w"), ensure_ascii=False, indent=1)
print(f"\n총 {len(recs)}건 / 브랜드:{dict(bd)} / 연도:{dict(sorted(yd.items()))}")
