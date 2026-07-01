#!/usr/bin/env python3
"""네이버 블로그 본문 크롤링 — ②동기·③배제 보강용.
blog.naver.com/{id}/{logno} → m.blog.naver.com/{id}/{logno} 본문 파싱.
정중 크롤(0.3s), UA헤더, timeout, 실패 skip, 성공률 로깅, 클러스터 상한."""
import os, json, re, time, urllib.request, urllib.error, html as htmlmod
BASE=os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam/")

UA="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"

def to_mobile(link):
    m=re.search(r"blog\.naver\.com/([^/]+)/(\d+)", link)
    if m: return f"https://m.blog.naver.com/{m.group(1)}/{m.group(2)}"
    m=re.search(r"blog\.naver\.com/.*blogId=([^&]+).*logNo=(\d+)", link)
    if m: return f"https://m.blog.naver.com/{m.group(1)}/{m.group(2)}"
    return None

def fetch_body(link):
    url=to_mobile(link)
    if not url: return None
    req=urllib.request.Request(url, headers={"User-Agent":UA})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            raw=r.read().decode("utf-8","ignore")
    except Exception:
        return None
    # 스마트에디터3: se-text-paragraph <p>들 추출
    paras=re.findall(r'class="se-text-paragraph[^"]*"[^>]*>(.*?)</p>', raw, re.S)
    body=" ".join(paras) if paras else None
    # 구에디터 폴백
    if not body:
        m3=re.search(r'id="postViewArea"[^>]*>(.*?)</div>', raw, re.S)
        if m3: body=m3.group(1)
    txt=None
    if body:
        txt=re.sub(r"<[^>]+>"," ", body); txt=htmlmod.unescape(txt); txt=re.sub(r"\s+"," ", txt).strip()
    # og:description 폴백(본문 빈약 시)
    if not txt or len(txt)<30:
        og=re.search(r'<meta property="og:description" content="([^"]*)"', raw)
        txt=htmlmod.unescape(og.group(1)).strip() if og else None
    return txt[:4000] if (txt and len(txt)>30) else None

def crawl(records, label, cap=None):
    if cap: records=records[:cap]
    out=[]; ok=0; fail=0
    for i,r in enumerate(records):
        b=fetch_body(r["link"])
        if b: r=dict(r); r["body"]=b; out.append(r); ok+=1
        else: fail+=1
        time.sleep(0.3)
        if (i+1)%50==0: print(f"  [{label}] {i+1}/{len(records)} (성공 {ok}/실패 {fail})")
    print(f"[{label}] 완료 — 시도 {len(records)} · 성공 {ok} ({ok/len(records)*100:.0f}%) · 실패 {fail}")
    return out

# ② 대상: parent-organic 중 시작연령/사전경로/동기 신호 글
parent=json.load(open(BASE+"yoonsam-parent-organic.json"))
def t(r): return r.get("title","")+" "+r.get("description","")
AGE=re.compile(r"\d살|\d세|유아|유치원|초[1-6]|초등 ?[1-6]|\d학년|미취학|영유|개월")
MOTIVE=re.compile(r"시작|처음|이유|때문|위해|목표|준비|늦|뒤처|기초|선행|흥미|재미|습관")
q2=[r for r in parent if AGE.search(t(r)) and (MOTIVE.search(t(r)) or True)]
# 시작연령 신호 있는 것 우선
q2=[r for r in parent if AGE.search(t(r))]
print(f"② 동기·시작연령 크롤 대상: {len(q2)} (상한 600)")
q2body=crawl(q2,"Q2-영어수준",cap=600)
json.dump(q2body, open(BASE+"q2-body.json","w"), ensure_ascii=False, indent=1)

# ③ 대상: exclude-parent 전체
excl=json.load(open(BASE+"yoonsam-exclude-parent.json"))
print(f"③ 배제 크롤 대상: {len(excl)} (상한 700)")
q3body=crawl(excl,"Q3-배제",cap=700)
json.dump(q3body, open(BASE+"q3-body.json","w"), ensure_ascii=False, indent=1)

print(f"\n저장: q2-body.json({len(q2body)}) · q3-body.json({len(q3body)})")
