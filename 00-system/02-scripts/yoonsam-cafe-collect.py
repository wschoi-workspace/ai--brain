#!/usr/bin/env python3
"""맘카페·커뮤니티 배제사유 수집 (네이버 카페 검색 API).
블로그가 못 담는 '안 고른 이유'를 카페 비교·고민 글에서 수집. ※카페 API는 작성일 미제공."""
import os, json, re, time, html, urllib.parse, urllib.request
ENV={}
for line in open(os.path.expanduser("~/do-better-workspace/.env")):
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); ENV[k.strip()]=v.strip()
CID,CSEC=ENV["NAVER_CLIENT_ID"],ENV["NAVER_CLIENT_SECRET"]
BASE=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam/")

QUERIES=["윤선생 안 시키는 이유","윤선생 고민","윤선생 vs 구몬","윤선생 vs 눈높이","윤선생 대신",
 "윤선생 전집 부담","윤선생 패드 부담","윤선생 비추","윤선생 끊고","윤선생 별로","윤선생 단점",
 "윤선생 말고","윤선생 안 했어요","윤선생 화상 고민","윤선생 베이직 고민","윤선생 vs 화상영어",
 "윤선생 그만둔","윤선생 vs 캠블리","윤선생 솔직 후기","윤선생 거른","윤선생 비교 후기"]

def strip(s): return html.unescape(re.sub(r"<[^>]+>","",s)).strip()
def search(q,start=1):
    url="https://openapi.naver.com/v1/search/cafearticle.json?"+urllib.parse.urlencode(
        {"query":q,"display":100,"start":start,"sort":"sim"})
    req=urllib.request.Request(url); req.add_header("X-Naver-Client-Id",CID); req.add_header("X-Naver-Client-Secret",CSEC)
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read().decode())

seen={}
for q in QUERIES:
    got=0
    for start in (1,101):
        try: res=search(q,start)
        except Exception as e: print(f"! {q}: {e}"); break
        items=res.get("items",[])
        if not items: break
        for it in items:
            link=it.get("link","")
            if link in seen: seen[link]["matched"].append(q); continue
            seen[link]={"title":strip(it.get("title","")),"description":strip(it.get("description","")),
                "link":link,"cafename":it.get("cafename",""),"cafeurl":it.get("cafeurl",""),
                "primary_query":q,"matched":[q]}
            got+=1
        time.sleep(0.12)
    print(f"  {q:20s} → 신규 {got}")
recs=list(seen.values())
from collections import Counter
cf=Counter(r["cafename"] for r in recs)
json.dump(recs, open(BASE+"cafe-naver-raw.json","w"), ensure_ascii=False, indent=1)
print(f"\n총 {len(recs)}건 / 상위 카페: {dict(cf.most_common(8))}")
