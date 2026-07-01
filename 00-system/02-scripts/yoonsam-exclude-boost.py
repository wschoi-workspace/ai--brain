#!/usr/bin/env python3
"""배제사유 표적 보강 수집 + 기존 raw 병합. '패스/대신/전집/패드/vs' 직접 쿼리."""
import os, json, re, time, html, urllib.parse, urllib.request
ENV={}
for line in open(os.path.expanduser("~/do-better-workspace/.env")):
    line=line.strip()
    if line and not line.startswith("#") and "=" in line:
        k,v=line.split("=",1); ENV[k.strip()]=v.strip()
CID,CSEC=ENV["NAVER_CLIENT_ID"],ENV["NAVER_CLIENT_SECRET"]
BASE=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")

QUERIES=["윤선생 패스","윤선생 대신","윤선생 말고","윤선생 거른","윤선생 안 하는 이유",
 "윤선생 전집","윤선생 패드 필수","윤선생 화상 단점","윤선생 베이직 단점",
 "윤선생 vs 눈높이","윤선생 vs 구몬","윤선생 vs 화상영어","윤선생 끊고","윤선생 안 시키는",
 "윤선생 고민 후기","윤선생 별로인","윤선생 비교"]

def strip(s): return html.unescape(re.sub(r"<[^>]+>","",s)).strip()
def search(q,start=1):
    url="https://openapi.naver.com/v1/search/blog.json?"+urllib.parse.urlencode(
        {"query":q,"display":100,"start":start,"sort":"sim"})
    req=urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id",CID); req.add_header("X-Naver-Client-Secret",CSEC)
    with urllib.request.urlopen(req,timeout=15) as r: return json.loads(r.read().decode())

existing=json.load(open(os.path.join(BASE,"yoonsam-trackA-naver-raw.json")))
seen={r["link"] for r in existing}
new=[]
for q in QUERIES:
    got=0
    for start in (1,101):
        try: res=search(q,start)
        except Exception as e: print(f"! {q}: {e}"); break
        items=res.get("items",[])
        if not items: break
        for it in items:
            link=it.get("link","")
            if link in seen: continue
            seen.add(link)
            pd=it.get("postdate","")
            new.append({"title":strip(it.get("title","")),"description":strip(it.get("description","")),
                "link":link,"bloggername":it.get("bloggername",""),"bloggerlink":it.get("bloggerlink",""),
                "postdate":pd,"year":pd[:4] if len(pd)>=4 else "미상",
                "primary_bucket":"exclude_boost","primary_query":q,"matched":[f"exclude_boost:{q}"]})
            got+=1
        time.sleep(0.12)
    print(f"  {q:20s} → 신규 {got}")
print(f"\n배제보강 신규 {len(new)}건")
json.dump(new, open(os.path.join(BASE,"yoonsam-exclude-boost-raw.json"),"w"), ensure_ascii=False, indent=1)
