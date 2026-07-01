#!/usr/bin/env python3
"""윤선생 RXR 심화분석 — 네이버 블로그 검색 API 수집 (트랙 A)
WebSearch(US색인)가 한국 자생 커뮤니티에 못 닿는 문제를 우회.
쿼리 세트별로 블로그 멘션을 연도(postdate) 태깅하여 수집·저장."""
import os, json, re, time, html, urllib.parse, urllib.request

# --- .env 로드 ---
ENV = {}
with open(os.path.expanduser("~/do-better-workspace/.env")) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            ENV[k.strip()] = v.strip()

CID = ENV["NAVER_CLIENT_ID"]
CSEC = ENV["NAVER_CLIENT_SECRET"]
OUTDIR = os.path.expanduser("~/do-better-workspace/80-r-tech/85-analysis-results/yoonsam")
os.makedirs(OUTDIR, exist_ok=True)

# --- 트랙 A 쿼리 세트 (목적별 태깅) ---
QUERIES = {
    "bm_general":   ["윤선생 후기", "윤선생 영어 후기", "윤선생 효과"],
    "bm_bangmun":   ["윤선생 방문", "윤선생 방문 후기", "윤선생 영어교실", "윤선생 선생님 방문"],
    "bm_basic":     ["윤선생 베이직", "윤선생 화상", "윤선생 비대면", "윤선생 베이직 후기"],
    "exclude":      ["윤선생 단점", "윤선생 비추", "윤선생 고민", "윤선생 그만", "윤선생 끊고", "윤선생 vs", "윤선생 솔직 후기"],
    "englvl":       ["윤선생 몇살", "윤선생 시작 나이", "윤선생 영유", "윤선생 파닉스 시작", "윤선생 7살", "윤선생 초1"],
    "comp_nunnopi": ["눈높이영어 후기", "눈높이 영어 단점", "눈높이 방문 영어", "눈높이 영어 효과"],
    "comp_jaeneung":["재능스스로영어", "재능교육 영어 후기", "재능 영어 단점", "재능스스로 영어 후기"],
}

def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return html.unescape(s).strip()

def search_blog(query, display=100, start=1):
    url = "https://openapi.naver.com/v1/search/blog.json?" + urllib.parse.urlencode(
        {"query": query, "display": display, "start": start, "sort": "date"})
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", CID)
    req.add_header("X-Naver-Client-Secret", CSEC)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))

seen = {}   # link -> record (중복 제거)
per_query_count = {}

for bucket, qs in QUERIES.items():
    for q in qs:
        got = 0
        for start in (1, 101):   # 최대 200건/쿼리
            try:
                res = search_blog(q, display=100, start=start)
            except Exception as e:
                print(f"  ! {q} (start={start}) 실패: {e}")
                break
            items = res.get("items", [])
            if not items:
                break
            for it in items:
                link = it.get("link", "")
                title = strip_tags(it.get("title", ""))
                desc = strip_tags(it.get("description", ""))
                pdate = it.get("postdate", "")  # YYYYMMDD
                year = pdate[:4] if len(pdate) >= 4 else "미상"
                if link in seen:
                    # 어느 버킷/쿼리에서 잡혔는지 추가 기록
                    seen[link]["matched"].append(f"{bucket}:{q}")
                    continue
                seen[link] = {
                    "title": title, "description": desc, "link": link,
                    "bloggername": it.get("bloggername", ""),
                    "bloggerlink": it.get("bloggerlink", ""),
                    "postdate": pdate, "year": year,
                    "primary_bucket": bucket, "primary_query": q,
                    "matched": [f"{bucket}:{q}"],
                }
                got += 1
            time.sleep(0.12)
        per_query_count[f"{bucket}:{q}"] = got
        print(f"  {bucket:14s} | {q:18s} → 신규 {got}건")

records = list(seen.values())

# --- 연도/버킷 분포 집계 ---
from collections import Counter
year_dist = Counter(r["year"] for r in records)
bucket_dist = Counter(r["primary_bucket"] for r in records)

raw_path = os.path.join(OUTDIR, "yoonsam-trackA-naver-raw.json")
with open(raw_path, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

meta = {
    "collected_total": len(records),
    "per_query": per_query_count,
    "year_distribution": dict(sorted(year_dist.items())),
    "bucket_distribution": dict(bucket_dist),
}
with open(os.path.join(OUTDIR, "yoonsam-trackA-meta.json"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

print("\n=== 수집 완료 ===")
print(f"총 고유 멘션: {len(records)}건")
print(f"연도분포: {dict(sorted(year_dist.items()))}")
print(f"버킷분포: {dict(bucket_dist)}")
print(f"저장: {raw_path}")
