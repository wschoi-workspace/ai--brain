#!/usr/bin/env python3
"""영어숲(학원 BM) 표적 보강 수집 — 자생 후기 N 확대 목적."""
import os, json, re, time, html, urllib.parse, urllib.request
ENV={}
for line in open(os.path.expanduser("~/do-better-workspace/.env")):
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); ENV[k.strip()]=v.strip()
CID,CSEC=ENV["NAVER_CLIENT_ID"],ENV["NAVER_CLIENT_SECRET"]
BASE=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")

QUERIES=["윤선생 영어숲 다녀","윤선생 영어숲 보내","윤선생 영어숲 그만","윤선생 영어숲 vs","윤선생 영어숲 솔직",
 "윤선생 영어학원 후기","윤선생 영어숲 다닌","윤선생 영어숲 등원","윤선생 영어숲 효과","윤선생 영어숲 레벨",
 "윤선생 스마트랜드 후기","윤선생 스마트랜드 다녀","윤선생 igse","윤선생 영어숲 끊","윤선생 영어숲 비추",
 "윤선생 영어숲 학원 후기","윤선생 영어숲 1년","윤선생 영어숲 그룹","윤선생 영어숲 원어민","윤선생 영어숲 내신"]

def strip(s): return html.unescape(re.sub(r"<[^>]+>","",s)).strip()
def search(q,start=1):
    url="https://openapi.naver.com/v1/search/blog.json?"+urllib.parse.urlencode(
        {"query":q,"display":100,"start":start,"sort":"sim"})
    req=urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id",CID); req.add_header("X-Naver-Client-Secret",CSEC)
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read().decode())

# 기존 영어숲 link (중복 제외)
tb=json.load(open(BASE+"/trackB-naver-raw.json"))
clean=json.load(open(BASE+"/yoonsam-trackA-clean.json"))
existing={r["link"] for r in tb} | {r["link"] for r in clean}
new={}
for q in QUERIES:
    got=0
    for start in (1,101):
        try: res=search(q,start)
        except Exception as e: print(f"! {q}: {e}"); break
        items=res.get("items",[])
        if not items: break
        for it in items:
            link=it.get("link","")
            if link in existing or link in new: continue
            pd=it.get("postdate","")
            new[link]={"title":strip(it.get("title","")),"description":strip(it.get("description","")),
                "link":link,"bloggername":it.get("bloggername",""),"bloggerlink":it.get("bloggerlink",""),
                "postdate":pd,"year":pd[:4] if len(pd)>=4 else "미상","brand":"윤선생영어숲","primary_query":q}
            got+=1
        time.sleep(0.12)
    print(f"  {q:22s} → 신규 {got}")
recs=list(new.values())
from collections import Counter
yd=Counter(r["year"] for r in recs if r["year"] in ["2022","2023","2024","2025","2026"])
json.dump(recs, open(BASE+"/soop-boost-raw.json","w"), ensure_ascii=False, indent=1)
print(f"\n영어숲 보강 신규 {len(recs)}건 / 연도:{dict(sorted(yd.items()))}")
