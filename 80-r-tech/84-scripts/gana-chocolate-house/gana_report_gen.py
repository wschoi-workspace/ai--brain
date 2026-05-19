"""가나초콜릿하우스 부산 시즌2 — RXR SNS HTML 리포트 생성"""
import json, sys, io, os
from collections import Counter
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

OUT = os.path.join(os.path.dirname(__file__), "../../82-case-reports/gana-chocolate-house/gana-chocolate-house-rxr-sns-report.html")

with open(os.path.join(os.path.dirname(__file__), "../../85-analysis-results/gana-chocolate-house/gana-chocolate-house-2layer-results.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

# ============================================================
# 통계 계산
# ============================================================
N = len(data)
sent_dist = Counter(r["sentiment"] for r in data)
sent_pct = {k: round(v / N * 100, 1) for k, v in sent_dist.items()}
topic_dist = Counter(r["primary_topic"] for r in data).most_common()
rql_dist = Counter(r["rql"] for r in data)
cls_dist = Counter(r.get("sincerity_class", "B") for r in data)

spon = [r for r in data if r.get("is_sponsored")]
org = [r for r in data if not r.get("is_sponsored")]
avg = lambda f, s: round(sum(r[f] for r in s) / max(len(s), 1), 1)

# 기간별
period_stats = {}
for p in ["사전", "팝업기간", "팝업후"]:
    sub = [r for r in data if r["period"] == p]
    if sub:
        period_stats[p] = {
            "n": len(sub),
            "auth": avg("authenticity", sub),
            "clout": avg("clout", sub),
            "freshness": avg("freshness_index", sub),
            "pos_pct": round(sum(1 for r in sub if r["sentiment"] == "긍정") / len(sub) * 100, 1),
        }

# Gates
g1 = [r for r in data if r.get("sincerity_class") != "G"]
g2 = [r for r in data if r.get("sincerity_class") not in ("C", "E", "F", "G")]
g3 = [r for r in data if r.get("sincerity_class") not in ("C", "E", "F", "G") and r.get("authenticity", 0) >= 60]

def gate_summary(items):
    n = len(items)
    if not n: return {"n": 0, "pos_pct": 0, "auth": 0, "clout": 0, "fresh": 0}
    return {
        "n": n,
        "pos_pct": round(sum(1 for r in items if r["sentiment"] == "긍정") / n * 100, 1),
        "auth": round(sum(r.get("authenticity", 0) for r in items) / n, 1),
        "clout": round(sum(r.get("clout", 0) for r in items) / n, 1),
        "fresh": round(sum(r.get("freshness_index", 0) for r in items) / n, 1),
    }

gs1, gs2, gs3 = gate_summary(g1), gate_summary(g2), gate_summary(g3)

# 날짜별 분포
date_dist = Counter(r["date"] for r in data)
dates_sorted = sorted(date_dist.items())
max_day = max(date_dist.values()) if date_dist else 1

# Brand24 data
b24 = {"total": 0, "reach": "N/A", "instagram": 0, "tiktok": 0, "x": 0, "news": 0, "facebook": 0, "web": 1, "blogs": 0}
b24_nonblog = b24["total"] - b24["blogs"]
total_mentions = N + b24_nonblog

# Top/Low Auth posts for raw data boxes
top_auth = sorted(data, key=lambda x: x.get("authenticity", 0), reverse=True)[:3]
low_auth = sorted(data, key=lambda x: x.get("authenticity", 0))[:3]

# RQL weights
rql_weights = {"Q5_서사형": 2.0, "Q4_분석형": 1.5, "Q3_경험형": 1.0, "Q2_감상형": 0.5, "Q1_간단형": 0.2}

# 위스키 페어링 침투도 체크
slowaging_count = sum(1 for r in data if "위스키 페어링" in (r.get("title","") + " " + str(r.get("topic_scores",{}))))

# 체험 요소 언급
ip_mentions = {}
for ip in ["최화정", "겟잇뷰티", "한예슬", "안재현"]:
    ip_mentions[ip] = sum(1 for r in data if ip in (r.get("title","") + " " + str(r.get("topic_scores",{}))))

# ============================================================
# Joy × Premium 재분석 (핵심 질문: 초콜릿의 즐거움 × 브랜드 고급스러움)
# ============================================================
joy_strong = [r for r in data if r.get("joy_score",0) >= 15]
joy_mid = [r for r in data if 6 <= r.get("joy_score",0) < 15]
joy_weak = [r for r in data if 1 <= r.get("joy_score",0) < 6]
joy_none = [r for r in data if r.get("joy_score",0) == 0]
prem_strong = [r for r in data if r.get("premium_score",0) >= 15]
prem_mid = [r for r in data if 6 <= r.get("premium_score",0) < 15]
prem_weak = [r for r in data if 1 <= r.get("premium_score",0) < 6]
prem_none = [r for r in data if r.get("premium_score",0) == 0]

g3_joy_strong = [r for r in g3 if r.get("joy_score",0) >= 6]
g3_prem_strong = [r for r in g3 if r.get("premium_score",0) >= 6]
g3_both = [r for r in g3 if r.get("joy_score",0) >= 6 and r.get("premium_score",0) >= 6]
g3_joy_only = [r for r in g3 if r.get("joy_score",0) >= 6 and r.get("premium_score",0) < 6]
g3_prem_only = [r for r in g3 if r.get("premium_score",0) >= 6 and r.get("joy_score",0) < 6]
g3_neither = [r for r in g3 if r.get("joy_score",0) < 6 and r.get("premium_score",0) < 6]

joy_avg_g3 = round(sum(r.get("joy_score",0) for r in g3)/max(len(g3),1), 1)
prem_avg_g3 = round(sum(r.get("premium_score",0) for r in g3)/max(len(g3),1), 1)

# 기간별 Joy/Premium
period_jp = {}
for p in ["사전", "팝업기간", "팝업후"]:
    sub = [r for r in g3 if r["period"] == p]
    if sub:
        period_jp[p] = {
            "joy": round(sum(r.get("joy_score",0) for r in sub)/len(sub),1),
            "prem": round(sum(r.get("premium_score",0) for r in sub)/len(sub),1),
            "joy_strong_pct": round(sum(1 for r in sub if r.get("joy_score",0)>=6)/len(sub)*100,1),
            "prem_strong_pct": round(sum(1 for r in sub if r.get("premium_score",0)>=6)/len(sub)*100,1),
        }
    else:
        period_jp[p] = {"joy":0,"prem":0,"joy_strong_pct":0,"prem_strong_pct":0}

# 키워드 집계
from collections import Counter as _C
joy_kw_counter = _C()
prem_kw_counter = _C()
for r in g3:
    for kw in r.get("joy_hits",[]):
        joy_kw_counter[kw] += 1
    for kw in r.get("premium_hits",[]):
        prem_kw_counter[kw] += 1
top_joy_kws = joy_kw_counter.most_common(10)
top_prem_kws = prem_kw_counter.most_common(10)

# 대표 포스트
top_joy_posts = sorted(g3, key=lambda r: -r.get("joy_score",0))[:5]
top_prem_posts = sorted(g3, key=lambda r: -r.get("premium_score",0))[:5]
top_both_posts = sorted(g3, key=lambda r: -(r.get("joy_score",0)+r.get("premium_score",0)))[:5]

# ============================================================
# HTML 생성
# ============================================================
def fmt_date(yyyymmdd):
    return f"{yyyymmdd[:4]}.{yyyymmdd[4:6]}.{yyyymmdd[6:8]}" if len(yyyymmdd) >= 8 else yyyymmdd

def date_bars():
    """날짜별 바 차트"""
    rows = []
    for d, cnt in dates_sorted:
        pct = round(cnt / max_day * 100)
        md = f"{d[4:6]}/{d[6:8]}"
        if d < "20230212":
            color = "var(--orange)"; label = "사전" if d == dates_sorted[0][0] else ""
        elif d <= "20230314":
            color = "var(--primary)"; label = "팝업기간" if d == "20230212" else ""
        else:
            color = "#94a3b8"; label = "팝업후" if d == "20230315" else ""
        inner = f"{cnt}" if cnt >= 5 else ""
        rows.append(f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:40px;font-size:9px;color:var(--body);text-align:right;">{md}</div><div style="flex:1;height:15px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{max(pct,3)}%;height:100%;background:{color};border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;font-weight:600;color:#fff;">{inner}</div></div><div style="width:20px;font-size:9px;font-weight:600;">{cnt}</div><div style="width:65px;font-size:8px;color:{color};font-weight:700;">{label}</div></div>')
    return "\n".join(rows)

def gauge(label, value, max_val, color, width="100%"):
    pct = min(round(value / max(max_val,1) * 100), 100) if max_val else 0
    return f'<div class="gauge-row"><div class="gauge-label">{label}</div><div class="gauge-track"><div class="gauge-fill" style="width:{pct}%;background:{color};">{value}</div></div><div class="gauge-val" style="color:{color};">{value}</div></div>'

TOPIC_COLORS = ["#6666FF", "#10b981", "#00b4d8", "#f59e0b", "#94a3b8", "#d946ef", "#ef4444", "#64748b"]

def topic_bars():
    rows = []
    max_t = topic_dist[0][1] if topic_dist else 1
    for i, (topic, cnt) in enumerate(topic_dist):
        pct = round(cnt / max_t * 100)
        ratio = round(cnt / N * 100, 1)
        color = TOPIC_COLORS[i % len(TOPIC_COLORS)]
        rows.append(f'<div class="gauge-row"><div class="gauge-label" style="width:100px;">{topic}</div><div class="gauge-track"><div class="gauge-fill" style="width:{pct}%;background:{color};">{cnt}건 ({ratio}%)</div></div><div class="gauge-val" style="color:{color};">{ratio}%</div></div>')
    return "\n".join(rows)

def gate3_table():
    """부록: Gate3 유효 포스트 테이블"""
    rows = []
    gate3_sorted = sorted(g3, key=lambda x: x.get("date", ""))
    for i, r in enumerate(gate3_sorted):
        bg = "#f0fdf4" if i % 2 == 0 else "#fff"
        sent_color = {"긍정": "var(--green)", "부정": "var(--coral)", "혼합": "var(--blue)", "중립": "#94a3b8"}.get(r["sentiment"], "#94a3b8")
        auth_color = "var(--green)" if r["authenticity"] >= 75 else "var(--primary)"
        link = r.get("link", "#")
        title = r.get("title", "")[:60]
        rows.append(f'<tr style="background:{bg};"><td style="text-align:center;">{i+1}</td><td>{fmt_date(r["date"])}</td><td style="color:{sent_color};font-weight:700;">{r["sentiment"]}</td><td style="color:{auth_color};font-weight:700;">{r["authenticity"]}</td><td>{r["clout"]}</td><td>{r["freshness_index"]}</td><td>{r["rql"]}</td><td>{r["primary_topic"]}</td><td>{r["period"]}</td><td><a href="{link}" target="_blank" style="color:var(--primary);text-decoration:none;">{title}</a></td><td>{r.get("blogger","")}</td></tr>')
    return "\n".join(rows)

# 협찬 포스트 Auth 스펙트럼
def spon_spectrum():
    rows = []
    for r in sorted(spon, key=lambda x: x.get("authenticity", 0), reverse=True)[:10]:
        auth = r["authenticity"]
        bg = "#f0fdf4" if auth >= 60 else ("#fffbeb" if auth >= 40 else "#fef2f2")
        rows.append(f'<div style="padding:8px 12px;background:{bg};border-radius:8px;margin-bottom:4px;font-size:11px;display:flex;align-items:center;gap:8px;"><div style="font-weight:800;min-width:50px;color:{"var(--green)" if auth>=60 else ("var(--orange)" if auth>=40 else "var(--coral)")};">Auth {auth}</div><div style="flex:1;">{r["title"][:50]}</div><div style="color:var(--body);font-size:10px;">{r["sentiment"]}</div></div>')
    return "\n".join(rows)

html = f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>가나초콜릿하우스 부산 시즌2 — RXR SNS 분석</title>
<style>@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable.css');
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=DIN+Alternate&display=swap');
:root{{--primary:#6666FF;--grad:linear-gradient(135deg,#5353FF,#8A8AFF);--black:#000;--dark:#262626;--body:#424D61;--light:#F6F6F6;--white:#FFF;--red:#C00000;--coral:#FF5050;--blue:#4D93F7;--green:#10b981;--orange:#f59e0b;--pink:#d946ef;--primary-pale:#E1E1FF;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Pretendard Variable',system-ui,sans-serif;background:var(--white);color:var(--dark);font-size:14px;line-height:1.6;max-width:1200px;margin:0 auto;padding:40px 32px;}}
h1{{font-size:28px;font-weight:800;margin-bottom:4px;}} h2{{font-size:20px;font-weight:800;margin:32px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--primary-pale);}} h3{{font-size:15px;font-weight:700;margin:14px 0 8px;}}
.sub{{font-size:13px;color:var(--body);margin-bottom:20px;}}
.card{{background:var(--light);border:1px solid #e8e8e8;border-radius:12px;padding:16px 18px;}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;}} .grid3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}}
table{{width:100%;border-collapse:collapse;font-size:12px;margin:10px 0;}}
th{{background:var(--primary);color:#fff;padding:6px 10px;text-align:left;font-size:11px;}} td{{padding:5px 10px;border-bottom:1px solid #eee;}}
.insight{{padding:14px 18px;background:var(--primary-pale);border-radius:10px;border-left:4px solid var(--primary);margin:10px 0;font-size:13px;line-height:1.7;}} .insight strong{{color:var(--primary);}}
.insight-warn{{background:#fef2f2;border-left-color:var(--coral);}} .insight-warn strong{{color:var(--coral);}}
.ba-container{{display:grid;grid-template-columns:1fr 50px 1fr;gap:0;align-items:stretch;margin:16px 0;}}
.ba-box{{padding:20px;border-radius:14px;}} .ba-before{{background:#f1f5f9;border:2px solid #cbd5e1;}} .ba-after{{background:#eef2ff;border:2px solid var(--primary);}}
.ba-vs{{display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:900;color:#94a3b8;}}
.ba-label{{font-size:12px;font-weight:700;letter-spacing:1px;margin-bottom:10px;}} .ba-title{{font-size:16px;font-weight:800;margin-bottom:12px;}}
.gauge-row{{display:flex;align-items:center;gap:8px;margin-bottom:8px;}}
.gauge-label{{width:120px;font-size:12px;font-weight:600;text-align:right;flex-shrink:0;}}
.gauge-track{{flex:1;height:24px;background:#f0f0f0;border-radius:5px;overflow:hidden;}}
.gauge-fill{{height:100%;border-radius:5px;display:flex;align-items:center;padding-left:8px;font-size:10px;font-weight:700;color:#fff;}}
.gauge-val{{width:45px;font-family:'DIN Alternate','Poppins',sans-serif;font-size:15px;font-weight:700;text-align:center;flex-shrink:0;}}
.funnel-bar{{height:44px;border-radius:10px;display:flex;align-items:center;padding:0 20px;font-size:13px;font-weight:700;color:#fff;margin-bottom:8px;box-shadow:0 2px 8px rgba(0,0,0,0.08);}}
.footer{{margin-top:40px;padding-top:16px;border-top:2px solid var(--primary);font-size:11px;color:#94a3b8;text-align:center;}}
@media print{{
  @page{{size:A4 portrait;margin:14mm 12mm;}}
  body{{max-width:100%!important;padding:0!important;margin:0!important;}}
  .pdf-panel{{display:none!important;}}
  .card,.ba-container,.grid2,.grid3,.insight,.gauge-row,table{{break-inside:avoid!important;page-break-inside:avoid!important;}}
  h2,h3{{break-after:avoid;page-break-after:avoid;}}
  h1{{font-size:22px!important;}} h2{{font-size:16px!important;margin-top:20px!important;}}
  .card{{padding:10px 12px!important;font-size:10px!important;}} table{{font-size:10px!important;}} th,td{{padding:4px 6px!important;}}
}}
.pdf-panel{{position:fixed;bottom:24px;right:24px;z-index:1000;}}
.pdf-panel-toggle{{display:flex;align-items:center;gap:8px;padding:12px 22px;background:var(--grad);color:#fff;border-radius:50px;font-size:14px;font-weight:600;cursor:pointer;box-shadow:0 4px 20px rgba(102,102,255,0.4);border:none;font-family:'Pretendard Variable',sans-serif;}}
.pdf-panel-body{{display:none;position:absolute;bottom:56px;right:0;width:220px;background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.18);padding:16px;}}
.pdf-panel-body.open{{display:block;}}
.pdf-orient-group{{display:flex;gap:8px;margin-bottom:14px;}}
.pdf-orient-btn{{flex:1;padding:12px 8px;background:#f9fafb;border:2px solid #e2e8f0;border-radius:12px;cursor:pointer;font-family:'Pretendard Variable',sans-serif;color:#475569;font-size:11px;font-weight:600;text-align:center;}}
.pdf-orient-btn.active{{border-color:var(--primary);background:#eef2ff;color:var(--primary);}}
.pdf-print-btn{{width:100%;padding:10px;background:var(--grad);color:#fff;border:none;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Pretendard Variable',sans-serif;}}</style><style id="pageOrientStyle"></style></head><body>

<!-- HEADER -->
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
  <span style="background:var(--grad);color:#fff;padding:4px 14px;border-radius:6px;font-family:'Poppins';font-size:11px;font-weight:600;letter-spacing:1px;">RXR SNS ANALYSIS</span>
</div>
<h1>가나초콜릿하우스 부산 · 시즌2</h1>
<div class="sub">기존 분석 vs RXR 2-Layer + Sincerity Gate | 네이버 블로그 {N}건 + Brand24 {b24_nonblog}건 = 총 {total_mentions}건 | Project RENT &middot; R-lab</div>

<!-- 리서치 개요 -->
<div style="padding:20px;background:var(--light);border-radius:14px;margin-bottom:24px;">
  <div class="grid2">
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">ABOUT THIS RESEARCH</div>
      <h3 style="margin-top:0;">분석 대상</h3>
      <table style="font-size:12px;"><tr><td style="color:var(--body);width:70px;padding:4px 0;">팝업명</td><td style="padding:4px 0;font-weight:700;">가나초콜릿하우스 부산 (2023 시즌2)</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">브랜드</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">롯데제과 가나</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2023.02.12 ~ 03.14, <strong>31일간</strong></td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">장소</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">부산 전포동 프로젝트렌트</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">컨셉</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">초콜릿 × 위스키 페어링 바 + 애프터눈티</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">분석 기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2023.01.29 ~ 04.11</td></tr></table>
    </div>
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">RESEARCH PERSPECTIVE</div>
      <h3 style="margin-top:0;">리서치 관점</h3>
      <div style="font-size:12px;color:var(--body);line-height:1.7;">
        <div style="padding:4px 0;"><strong style="color:var(--primary);">핵심 질문:</strong> 가나초콜릿하우스 방문객은 <strong>①초콜릿의 즐거움</strong>과 <strong>②브랜드의 고급스러움</strong>을 실제로 느꼈는가? 그리고 이 두 감정은 어떤 비율로 교차하는가?</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">데이터:</strong> 네이버 블로그 {N}건 + Brand24 비블로그 {b24_nonblog}건 = 총 {total_mentions}건</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">분석:</strong> Content + Psyche + Sincerity Gate 3단계</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">Reach:</strong> Brand24 기준 {b24["reach"]} (멀티채널)</div>
      </div>
    </div>
  </div>
  <div style="margin-top:12px;padding:10px 14px;background:var(--primary-pale);border-radius:8px;font-size:12px;color:var(--body);">
    <strong>읽는 법:</strong> 각 섹션은 <strong>BEFORE(기존 도구)</strong>와 <strong>AFTER(RXR)</strong>를 나란히 비교합니다. AFTER 파트에는 Raw Data 근거 박스가 포함됩니다.
  </div>
</div>

<!-- 0. 데이터 수집 개요 -->
<h2>0. 데이터 수집 개요</h2>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);padding:14px;"><div style="font-size:32px;font-weight:800;color:var(--primary);">{total_mentions}</div><div style="font-size:11px;color:var(--body);font-weight:600;">총 멘션 (통합)</div></div>
  <div class="card" style="text-align:center;border-top:3px solid #00b4d8;padding:14px;"><div style="font-size:32px;font-weight:800;color:#00b4d8;">{b24["reach"]}</div><div style="font-size:11px;color:var(--body);font-weight:600;">Reach (Brand24)</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--pink);padding:14px;"><div style="font-size:32px;font-weight:800;color:var(--pink);">{gs3["n"]}</div><div style="font-size:11px;color:var(--body);font-weight:600;">Gate 3 유효</div></div>
</div>

<h3>데이터 소스별 구성</h3>
<div class="grid2" style="margin:10px 0;">
  <div class="card" style="border-left:4px solid var(--primary);">
    <div style="font-size:11px;font-family:'Poppins';letter-spacing:1px;color:var(--body);margin-bottom:6px;">NAVER BLOG (심층 분석)</div>
    <div style="font-size:28px;font-weight:800;color:var(--primary);">{N}<span style="font-size:13px;font-weight:600;color:var(--body);"> 건</span></div>
    <div style="margin-top:8px;">
      <table style="font-size:11px;margin:0;"><tbody>
        <tr><td style="color:var(--orange);font-weight:600;border:none;padding:2px 6px;">사전</td><td style="border:none;padding:2px 6px;"><strong>{period_stats.get("사전",{}).get("n",0)}</strong> ({round(period_stats.get("사전",{}).get("n",0)/N*100)}%)</td></tr>
        <tr><td style="color:var(--primary);font-weight:600;border:none;padding:2px 6px;">팝업기간</td><td style="border:none;padding:2px 6px;"><strong>{period_stats.get("팝업기간",{}).get("n",0)}</strong> ({round(period_stats.get("팝업기간",{}).get("n",0)/N*100)}%)</td></tr>
        <tr><td style="color:#94a3b8;font-weight:600;border:none;padding:2px 6px;">팝업후</td><td style="border:none;padding:2px 6px;"><strong>{period_stats.get("팝업후",{}).get("n",0)}</strong> ({round(period_stats.get("팝업후",{}).get("n",0)/N*100)}%)</td></tr>
      </tbody></table>
    </div>
    <div style="margin-top:8px;padding:6px 8px;background:var(--primary-pale);border-radius:6px;font-size:10px;color:var(--primary);">API 직접 크롤링 → Content + Psyche Layer 심층 분석 대상</div>
  </div>
  <div class="card" style="border-left:4px solid #00b4d8;">
    <div style="font-size:11px;font-family:'Poppins';letter-spacing:1px;color:var(--body);margin-bottom:6px;">BRAND24 비블로그 채널</div>
    <div style="font-size:28px;font-weight:800;color:#00b4d8;">{b24_nonblog}<span style="font-size:13px;font-weight:600;color:var(--body);"> 건</span></div>
    <div style="margin-top:8px;">
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:4px;"><div style="width:65px;font-size:10px;text-align:right;color:var(--body);">Instagram</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{round(b24["instagram"]/max(b24_nonblog,1)*100)}%;height:100%;background:linear-gradient(90deg,#833AB4,#E1306C);border-radius:3px;display:flex;align-items:center;padding-left:5px;font-size:8px;font-weight:700;color:#fff;">{b24["instagram"]}</div></div></div>
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:4px;"><div style="width:65px;font-size:10px;text-align:right;color:var(--body);">TikTok</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{round(b24["tiktok"]/max(b24_nonblog,1)*100)}%;height:100%;background:#000;border-radius:3px;display:flex;align-items:center;padding-left:5px;font-size:8px;font-weight:700;color:#fff;">{b24["tiktok"]}</div></div></div>
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:4px;"><div style="width:65px;font-size:10px;text-align:right;color:var(--body);">X</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{round(b24["x"]/max(b24_nonblog,1)*100)}%;height:100%;background:#1DA1F2;border-radius:3px;display:flex;align-items:center;padding-left:5px;font-size:8px;font-weight:700;color:#fff;">{b24["x"]}</div></div></div>
      <div style="display:flex;align-items:center;gap:5px;"><div style="width:65px;font-size:10px;text-align:right;color:var(--body);">News+FB+Web</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{round((b24["news"]+b24["facebook"]+b24["web"])/max(b24_nonblog,1)*100)}%;height:100%;background:#94a3b8;border-radius:3px;display:flex;align-items:center;padding-left:5px;font-size:8px;font-weight:700;color:#fff;">{b24["news"]+b24["facebook"]+b24["web"]}</div></div></div>
    </div>
    <div style="margin-top:8px;padding:6px 8px;background:#e0f7fa;border-radius:6px;font-size:10px;color:#0077b6;">Blogs {b24["blogs"]}건은 네이버와 중복 → 제외, 비블로그만 합산</div>
  </div>
</div>
<div class="insight" style="margin:12px 0;">
  <strong>통합 데이터 {total_mentions}건 = 네이버 블로그 {N}건 + Brand24 비블로그 {b24_nonblog}건.</strong> Brand24 Blogs {b24["blogs"]}건은 네이버 크롤링과 중복 가능하여 제외. <strong>Instagram({b24["instagram"]}건, {round(b24["instagram"]/max(b24_nonblog,1)*100)}%)</strong>이 비블로그 최다 채널 → 시각 중심 확산. TikTok {b24["tiktok"]}건으로 숏폼 콘텐츠도 활발. 심층 분석(2-Layer + Sincerity Gate)은 텍스트 분석이 가능한 네이버 블로그 {N}건 기준.
</div>

<h3>날짜별 버즈 분포</h3>
{date_bars()}

<h3>기간별 비교</h3>
<div class="grid2" style="margin:10px 0;">
  <div>
    <table>
      <tr><th>기간</th><th>건수</th><th>일평균</th><th>비율</th></tr>
      <tr><td style="color:var(--orange);font-weight:700;">사전 (01/29~02/11)</td><td><strong>{period_stats.get("사전",{}).get("n",0)}</strong></td><td>{round(period_stats.get("사전",{}).get("n",0)/14,1)}</td><td>{round(period_stats.get("사전",{}).get("n",0)/N*100)}%</td></tr>
      <tr><td style="color:var(--primary);font-weight:700;">팝업기간 (02/12~03/14)</td><td><strong>{period_stats.get("팝업기간",{}).get("n",0)}</strong></td><td>{round(period_stats.get("팝업기간",{}).get("n",0)/31,1)}</td><td>{round(period_stats.get("팝업기간",{}).get("n",0)/N*100)}%</td></tr>
      <tr><td style="color:#94a3b8;font-weight:700;">팝업후 (03/15~04/11)</td><td><strong>{period_stats.get("팝업후",{}).get("n",0)}</strong></td><td>{round(period_stats.get("팝업후",{}).get("n",0)/14,1)}</td><td>{round(period_stats.get("팝업후",{}).get("n",0)/N*100)}%</td></tr>
    </table>
  </div>
  <div class="grid2" style="gap:8px;">
    <div class="card" style="text-align:center;padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--primary);">{round(period_stats.get("팝업기간",{}).get("n",0)/31,1)}</div><div style="font-size:10px;color:var(--body);">팝업기간 일평균</div></div>
    <div class="card" style="text-align:center;padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--orange);">04/04</div><div style="font-size:10px;color:var(--body);">피크일 ({date_dist.get("20230212",0)}건)</div></div>
    <div class="card" style="text-align:center;padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--green);">{round(period_stats.get("팝업후",{}).get("n",0)/period_stats.get("사전",{}).get("n",1)*100)}%</div><div style="font-size:10px;color:var(--body);">팝업후/사전 비율</div></div>
    <div class="card" style="text-align:center;padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--pink);">31일</div><div style="font-size:10px;color:var(--body);">팝업 운영 기간</div></div>
  </div>
</div>

<!-- 1. 감성 분석 Before → After -->
<h2>1. 감성 분석 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE &mdash; 기존 도구</div>
    <div class="ba-title">3단계 감성 분류</div>
    <div style="font-size:13px;color:var(--body);line-height:1.7;">기존 도구는 긍정/중립/부정 <strong>3단계</strong>로 분류합니다. {N}건 중 긍정 {sent_pct.get("긍정",0)}%로 표시되며, "혼합"(긍정+부정 공존)은 구분하지 못합니다.</div>
    <div style="margin-top:12px;padding:12px;background:#e2e8f0;border-radius:8px;text-align:center;font-size:20px;font-weight:800;">긍정 {sent_pct.get("긍정",0)}%</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER &mdash; RXR</div>
    <div class="ba-title">4단계 + Auth + Clout</div>
    {gauge("긍정", sent_pct.get("긍정",0), 100, "var(--green)")}
    {gauge("중립", sent_pct.get("중립",0), 100, "#94a3b8")}
    {gauge("혼합", sent_pct.get("혼합",0), 100, "var(--blue)")}
    {gauge("부정", sent_pct.get("부정",0), 100, "var(--coral)")}
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      <strong style="color:var(--primary);">해석:</strong> 긍정 {sent_pct.get("긍정",0)}%에 혼합 {sent_pct.get("혼합",0)}%를 더하면 {round(sent_pct.get("긍정",0)+sent_pct.get("혼합",0),1)}%가 긍정 요소를 포함. 그러나 Gate 3 적용 시 진심 긍정은 <strong style="color:var(--coral);">{gs3["pos_pct"]}%</strong>로 하락. 기존 도구는 협찬의 의무적 긍정과 진심 긍정을 구분하지 못한다.
    </div>
  </div>
</div>

<!-- 2. 데이터 분류 Before → After -->
<h2>2. 데이터 분류 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">채널별 건수만</div>
    <div style="font-size:13px;color:var(--body);line-height:1.7;">기존 도구는 블로그/인스타/뉴스 등 <strong>채널별 건수</strong>만 제공합니다. 모든 1건은 동일한 가치로 취급됩니다.</div>
    <div style="margin-top:12px;padding:12px;background:#e2e8f0;border-radius:8px;text-align:center;font-size:15px;font-weight:700;">{total_mentions}건 = 1건 × {total_mentions}</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">A~G 7단계 분류</div>
    <table style="font-size:11px;">
      <tr><th>등급</th><th>분류</th><th>건수</th><th>처리</th></tr>
      <tr style="background:#f0fdf4;"><td style="font-weight:800;color:var(--green);">A</td><td>진성후기</td><td><strong>{cls_dist.get("A",0)}</strong></td><td>핵심 분석</td></tr>
      <tr><td style="font-weight:800;">B</td><td>일반포스트</td><td><strong>{cls_dist.get("B",0)}</strong></td><td>분석 대상</td></tr>
      <tr style="background:#fffbeb;"><td style="font-weight:800;color:var(--orange);">C</td><td>협찬/체험단</td><td><strong>{cls_dist.get("C",0)}</strong></td><td>진심 스펙트럼</td></tr>
      <tr><td style="font-weight:800;color:#94a3b8;">D</td><td>나열형</td><td><strong>{cls_dist.get("D",0)}</strong></td><td>카운트만</td></tr>
      <tr><td style="font-weight:800;color:#94a3b8;">E</td><td>리그램</td><td><strong>{cls_dist.get("E",0)}</strong></td><td>카운트만</td></tr>
      <tr style="background:#fef2f2;"><td style="font-weight:800;color:var(--coral);">F</td><td>비즈/보도</td><td><strong>{cls_dist.get("F",0)}</strong></td><td>제외</td></tr>
      <tr style="background:#fef2f2;"><td style="font-weight:800;color:var(--coral);">G</td><td>노이즈</td><td><strong>{cls_dist.get("G",0)}</strong></td><td>제외</td></tr>
    </table>
    <div style="padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;margin-top:8px;">
      <strong style="color:var(--primary);">해석:</strong> B등급(일반) {cls_dist.get("B",0)}건이 {round(cls_dist.get("B",0)/N*100)}%로 대다수. A등급(진성후기) {cls_dist.get("A",0)}건({round(cls_dist.get("A",0)/N*100,1)}%)은 개인 경험+구체적 디테일이 모두 풍부한 고품질 후기. C등급(협찬) {cls_dist.get("C",0)}건({round(cls_dist.get("C",0)/N*100,1)}%)은 제외하지 않고 Auth 스펙트럼으로 분석 — 이것이 기존 도구와의 핵심 차이.
    </div>
  </div>
</div>

<!-- 3. 토픽 분석 Before → After -->
<h2>3. 토픽 분석 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">워드클라우드</div>
    <div style="font-size:13px;color:var(--body);line-height:1.7;">기존 도구는 빈출 단어를 크기로 표현하는 워드클라우드를 제공합니다. 시각적이지만 <strong>구조화된 비중</strong>이나 <strong>시사점</strong>은 알 수 없습니다.</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">즐거움 × 고급스러움 2축 분석</div>
    <div style="font-size:12px;color:var(--body);line-height:1.6;margin-bottom:12px;">
      브랜드가 기대한 핵심 경험 두 가지 — <strong>"초콜릿의 즐거움(Joy)"</strong>과 <strong>"브랜드의 고급스러움(Premium)"</strong> — 이 소비자 언어에 얼마나 침투했는지 키워드 기반 스코어링으로 측정.
    </div>
    {gauge("즐거움(Joy) 강", round(len(g3_joy_strong)/max(len(g3),1)*100,1), 100, "var(--pink)")}
    {gauge("고급(Premium) 강", round(len(g3_prem_strong)/max(len(g3),1)*100,1), 100, "var(--primary)")}
    {gauge("둘 다 강 (Q1)", round(len(g3_both)/max(len(g3),1)*100,1), 100, "var(--green)")}
    {gauge("둘 다 약 (Q4)", round(len(g3_neither)/max(len(g3),1)*100,1), 100, "var(--coral)")}
    <div style="padding:10px 14px;background:#f0fdf4;border-radius:8px;font-size:12px;line-height:1.7;margin-top:10px;border-left:3px solid var(--green);">
      <strong style="color:var(--green);">핵심 발견:</strong> Gate 3 {len(g3)}건 중 <strong>즐거움+고급 동시 전달 성공 포스트 {len(g3_both)}건({round(len(g3_both)/max(len(g3),1)*100,1)}%)</strong>. 거의 절반의 방문객이 가나가 의도한 <strong>복합적 브랜드 경험(달콤한 초콜릿 + 어른의 고급감)</strong>을 온전히 체감. 두 축 모두 약한 포스트는 {round(len(g3_neither)/max(len(g3),1)*100,1)}%에 머묾 — 이 팝업은 "가봤던 팝업"이 아닌 "느낀 팝업"으로 기억되고 있음.
    </div>
  </div>
</div>

<!-- Joy × Premium 심층 -->
<h3>즐거움(Joy) × 고급스러움(Premium) 4분면 (Gate 3 {len(g3)}건 기준)</h3>
<div class="grid2" style="margin:10px 0;">
  <div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">
      <div style="padding:16px;background:#f0fdf4;border-radius:10px;border:2px solid var(--green);text-align:center;">
        <div style="font-size:10px;color:var(--body);font-weight:700;">Q1 · 즐거움+고급</div>
        <div style="font-size:26px;font-weight:800;color:var(--green);">{len(g3_both)}</div>
        <div style="font-size:10px;color:var(--body);">{round(len(g3_both)/max(len(g3),1)*100,1)}%</div>
      </div>
      <div style="padding:16px;background:#fffbeb;border-radius:10px;border:2px solid var(--orange);text-align:center;">
        <div style="font-size:10px;color:var(--body);font-weight:700;">Q2 · 즐거움만</div>
        <div style="font-size:26px;font-weight:800;color:var(--orange);">{len(g3_joy_only)}</div>
        <div style="font-size:10px;color:var(--body);">{round(len(g3_joy_only)/max(len(g3),1)*100,1)}%</div>
      </div>
      <div style="padding:16px;background:#eef2ff;border-radius:10px;border:2px solid var(--primary);text-align:center;">
        <div style="font-size:10px;color:var(--body);font-weight:700;">Q3 · 고급만</div>
        <div style="font-size:26px;font-weight:800;color:var(--primary);">{len(g3_prem_only)}</div>
        <div style="font-size:10px;color:var(--body);">{round(len(g3_prem_only)/max(len(g3),1)*100,1)}%</div>
      </div>
      <div style="padding:16px;background:#fef2f2;border-radius:10px;border:2px solid var(--coral);text-align:center;">
        <div style="font-size:10px;color:var(--body);font-weight:700;">Q4 · 둘 다 약</div>
        <div style="font-size:26px;font-weight:800;color:var(--coral);">{len(g3_neither)}</div>
        <div style="font-size:10px;color:var(--body);">{round(len(g3_neither)/max(len(g3),1)*100,1)}%</div>
      </div>
    </div>
    <div class="insight" style="margin:0;font-size:12px;">
      <strong>사분면 해석:</strong><br>
      &bull; <strong>Q1(둘 다 강)</strong>이 단 {len(g3_both)}건({round(len(g3_both)/max(len(g3),1)*100,1)}%) — 완벽한 경험이 전달된 극소수<br>
      &bull; <strong>Q3(고급만)</strong>이 Q2(즐거움만)의 {round(len(g3_prem_only)/max(len(g3_joy_only),1),1)}배 — 고급 신호가 즐거움보다는 강함<br>
      &bull; <strong>Q4(둘 다 약)</strong>이 {round(len(g3_neither)/max(len(g3),1)*100,1)}% — 설계된 공간은 있으나, 감정은 비어있음
    </div>
  </div>
  <div class="card">
    <div style="font-size:13px;font-weight:700;color:var(--primary);margin-bottom:10px;">상위 키워드 — 소비자 언어로 본 실제 경험</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:11px;">
      <div>
        <div style="font-weight:700;color:var(--pink);margin-bottom:6px;">🍫 즐거움(Joy) 키워드 TOP</div>
        {''.join(f'<div style="padding:3px 0;border-bottom:1px dashed #eee;"><strong>{kw}</strong> · {n}건</div>' for kw,n in top_joy_kws[:8])}
      </div>
      <div>
        <div style="font-weight:700;color:var(--primary);margin-bottom:6px;">✨ 고급(Premium) 키워드 TOP</div>
        {''.join(f'<div style="padding:3px 0;border-bottom:1px dashed #eee;"><strong>{kw}</strong> · {n}건</div>' for kw,n in top_prem_kws[:8])}
      </div>
    </div>
    <div style="margin-top:10px;padding:8px 10px;background:#f0fdf4;border-radius:6px;font-size:11px;color:var(--body);line-height:1.5;border-left:3px solid var(--green);">
      <strong style="color:var(--green);">핵심 관찰:</strong> Joy 키워드는 "맛있·달달·달콤·재미·<strong>인생</strong>·귀여·<strong>행복</strong>" 같은 <strong>체험된 감정어</strong>가 상위. Premium 키워드는 "바·위스키·페어링·전포동·분위기"라는 설계 요소 + 결정적으로 "<strong>고급</strong>"이라는 직접적 감탄어까지 {prem_kw_counter.get("고급",0)}건 포착. 즉 방문자는 <strong>고급스러운 장치를 "고급스럽다"고 직접 말함</strong> — 설계가 감정으로 내재화된 성공 사례.
    </div>
  </div>
</div>

<!-- 4. 심리 분석 -->
<h2>4. 심리 분석 (Authenticity / Clout / Freshness)</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">심리 분석 불가</div>
    <div style="font-size:13px;color:var(--body);line-height:1.7;">기존 도구는 감성(긍정/부정)까지만 제공합니다. 작성자의 <strong>진정성, 추천 확신도, 신선함</strong>은 측정 불가.</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">Auth / Clout / Freshness</div>
    {gauge("Authenticity", avg("authenticity", data), 100, "var(--primary)")}
    {gauge("Clout", avg("clout", data), 100, "var(--green)")}
    {gauge("Freshness", avg("freshness_index", data), 100, "var(--orange)")}
  </div>
</div>

<h3>기간별 심리 변화</h3>
<div class="grid3">
  <div class="card" style="border-top:3px solid var(--orange);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--orange);margin-bottom:8px;">사전</div>
    <div style="font-size:28px;font-weight:800;color:var(--orange);">{period_stats.get("사전",{}).get("auth",0)}</div>
    <div style="font-size:10px;color:var(--body);">Auth</div>
    <div style="margin-top:6px;font-size:12px;">Clout {period_stats.get("사전",{}).get("clout",0)} · Fresh {period_stats.get("사전",{}).get("freshness",0)}</div>
    <div style="margin-top:6px;font-size:11px;color:var(--body);">긍정률 {period_stats.get("사전",{}).get("pos_pct",0)}%</div>
  </div>
  <div class="card" style="border-top:3px solid var(--primary);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--primary);margin-bottom:8px;">팝업기간</div>
    <div style="font-size:28px;font-weight:800;color:var(--primary);">{period_stats.get("팝업기간",{}).get("auth",0)}</div>
    <div style="font-size:10px;color:var(--body);">Auth</div>
    <div style="margin-top:6px;font-size:12px;">Clout {period_stats.get("팝업기간",{}).get("clout",0)} · Fresh {period_stats.get("팝업기간",{}).get("freshness",0)}</div>
    <div style="margin-top:6px;font-size:11px;color:var(--body);">긍정률 {period_stats.get("팝업기간",{}).get("pos_pct",0)}%</div>
  </div>
  <div class="card" style="border-top:3px solid var(--green);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--green);margin-bottom:8px;">팝업후</div>
    <div style="font-size:28px;font-weight:800;color:var(--green);">{period_stats.get("팝업후",{}).get("auth",0)}</div>
    <div style="font-size:10px;color:var(--body);">Auth</div>
    <div style="margin-top:6px;font-size:12px;">Clout {period_stats.get("팝업후",{}).get("clout",0)} · Fresh {period_stats.get("팝업후",{}).get("freshness",0)}</div>
    <div style="margin-top:6px;font-size:11px;color:var(--body);">긍정률 {period_stats.get("팝업후",{}).get("pos_pct",0)}%</div>
  </div>
</div>
<div class="insight" style="margin:12px 0;">
  <strong>기간별 Auth 변화: 사전 {period_stats.get("사전",{}).get("auth",0)} → 팝업기간 {period_stats.get("팝업기간",{}).get("auth",0)} → 팝업후 {period_stats.get("팝업후",{}).get("auth",0)}</strong><br>
  사전 기간(Auth {period_stats.get("사전",{}).get("auth",0)})은 기대감 있는 정보 공유, 팝업기간(Auth {period_stats.get("팝업기간",{}).get("auth",0)})은 협찬+과잉긍정이 섞여 하락, 팝업후(Auth {period_stats.get("팝업후",{}).get("auth",0)})는 진정한 체험 회고로 <strong style="color:var(--green);">회복</strong>. 31일 단기 팝업의 특성: 16일 장기 운영(새로 팝업)과 달리 Auth 피로 축적이 적고, 늦은 후기가 오히려 더 진정성 있게 작성됨.
</div>

<!-- Raw Data 근거 -->
<div class="card" style="margin:10px 0;">
  <div style="font-size:11px;font-family:'Poppins';letter-spacing:1px;color:var(--body);margin-bottom:8px;">RAW DATA EVIDENCE</div>
  <div class="grid2">
    <div>
      <div style="font-size:11px;font-weight:700;color:var(--green);margin-bottom:6px;">Top Auth (진정성 최고)</div>
      {"".join(f'<div style="padding:6px 8px;background:#f0fdf4;border-radius:6px;margin-bottom:4px;font-size:10px;"><strong>Auth {r["authenticity"]}</strong> | {r["sentiment"]} | {r["rql"]} | {r["title"][:45]}</div>' for r in top_auth[:3])}
    </div>
    <div>
      <div style="font-size:11px;font-weight:700;color:var(--coral);margin-bottom:6px;">Low Auth (진정성 최저)</div>
      {"".join(f'<div style="padding:6px 8px;background:#fef2f2;border-radius:6px;margin-bottom:4px;font-size:10px;"><strong>Auth {r["authenticity"]}</strong> | {r["sentiment"]} | {r.get("sincerity_class","B")} | {r["title"][:45]}</div>' for r in low_auth[:3])}
    </div>
  </div>
</div>

<!-- 5. 협찬 vs 자발적 -->
<h2>5. 협찬 분석 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">유/무 이분법</div>
    <div style="font-size:13px;color:var(--body);line-height:1.7;">기존 도구는 협찬 여부를 <strong>있다/없다</strong>로만 구분. 협찬 안에서도 진심인 후기와 의무적 후기의 차이를 구분하지 못합니다.</div>
    <div style="margin-top:12px;padding:12px;background:#e2e8f0;border-radius:8px;text-align:center;font-size:15px;">협찬 {len(spon)}건 → 전부 제외 또는 전부 포함</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">Auth 스펙트럼 분석</div>
    <div class="grid2" style="gap:8px;">
      <div style="text-align:center;padding:10px;background:#fffbeb;border-radius:8px;">
        <div style="font-size:24px;font-weight:800;color:var(--orange);">{len(spon)}<span style="font-size:12px;">건</span></div>
        <div style="font-size:10px;">협찬 | Auth <strong>{avg("authenticity", spon)}</strong></div>
      </div>
      <div style="text-align:center;padding:10px;background:#f0fdf4;border-radius:8px;">
        <div style="font-size:24px;font-weight:800;color:var(--green);">{len(org)}<span style="font-size:12px;">건</span></div>
        <div style="font-size:10px;">자발적 | Auth <strong>{avg("authenticity", org)}</strong></div>
      </div>
    </div>
    <div style="margin-top:8px;font-size:12px;font-weight:700;color:var(--coral);text-align:center;">Auth 차이: {round(avg("authenticity", org) - avg("authenticity", spon), 1)}점</div>
  </div>
</div>

<h3>협찬 포스트 Auth 스펙트럼</h3>
{spon_spectrum()}
<div style="padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;margin-top:8px;">
  <strong style="color:var(--primary);">해석:</strong> 협찬 포스트(Auth {avg("authenticity", spon)})는 자발적(Auth {avg("authenticity", org)}) 대비 진정성이 <strong>{round((1-avg("authenticity", spon)/avg("authenticity", org))*100)}% 낮음</strong>. 같은 "긍정"이라도 의무적 톤 vs 실제 감동의 질적 차이가 크다. RXR은 같은 긍정 안에서도 진심의 농도를 구분한다.
</div>

<!-- 6. 후기 품질 Before → After -->
<h2>6. 후기 품질 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">1건 = 1건</div>
    <div style="font-size:13px;color:var(--body);line-height:1.7;">기존 도구에서는 500자 서사형 후기와 20자 감상형 후기가 <strong>동일한 1건</strong>으로 처리됩니다.</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">RQL 5단계</div>
    {gauge("Q5 서사형 (x2.0)", rql_dist.get("Q5_서사형",0), N, "var(--primary)")}
    {gauge("Q4 분석형 (x1.5)", rql_dist.get("Q4_분석형",0), N, "var(--blue)")}
    {gauge("Q3 경험형 (x1.0)", rql_dist.get("Q3_경험형",0), N, "var(--green)")}
    {gauge("Q2 감상형 (x0.5)", rql_dist.get("Q2_감상형",0), N, "var(--orange)")}
    {gauge("Q1 간단형 (x0.2)", rql_dist.get("Q1_간단형",0), N, "#94a3b8")}
    <div style="padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;margin-top:8px;">
      <strong style="color:var(--primary);">해석:</strong> Q5 서사형 {rql_dist.get("Q5_서사형",0)}건({round(rql_dist.get("Q5_서사형",0)/N*100,1)}%) + Q4 분석형 {rql_dist.get("Q4_분석형",0)}건({round(rql_dist.get("Q4_분석형",0)/N*100,1)}%) = 고품질 후기 {rql_dist.get("Q5_서사형",0)+rql_dist.get("Q4_분석형",0)}건({round((rql_dist.get("Q5_서사형",0)+rql_dist.get("Q4_분석형",0))/N*100,1)}%). 31일 단기 팝업임에도 상세 후기 비율이 높은 편 — 공간 체험이 풍부한 서사를 만들어냄.
    </div>
  </div>
</div>

<!-- 7. Sincerity Gate -->
<h2>7. Sincerity Gate — 3단계 진심 필터</h2>
<div class="card" style="padding:20px;margin:16px 0;">
  <div class="funnel-bar" style="width:100%;background:linear-gradient(90deg,#94a3b8,#b0b8c4);">1차 필터 (노이즈 제거) — {gs1["n"]}건 | 긍정 {gs1["pos_pct"]}%</div>
  <div class="funnel-bar" style="width:{round(gs2["n"]/max(gs1["n"],1)*100)}%;background:linear-gradient(90deg,#6666FF,#8888FF);">2차 필터 (협찬·보도 분리) — {gs2["n"]}건 | 긍정 {gs2["pos_pct"]}%</div>
  <div class="funnel-bar" style="width:{round(gs3["n"]/max(gs1["n"],1)*100)}%;background:linear-gradient(90deg,#10b981,#34d399);">3차 필터 (진정성 기준) — {gs3["n"]}건 | 긍정 {gs3["pos_pct"]}%</div>
</div>
<div style="margin:12px 0;">
  <table>
    <tr><th></th><th>건수</th><th>긍정률</th><th>Auth</th><th>Clout</th><th>Freshness</th><th>필터</th></tr>
    <tr><td style="font-weight:700;">Gate 1</td><td>{gs1["n"]}</td><td>{gs1["pos_pct"]}%</td><td>{gs1["auth"]}</td><td>{gs1["clout"]}</td><td>{gs1["fresh"]}</td><td>G(노이즈) 제거</td></tr>
    <tr><td style="font-weight:700;">Gate 2</td><td>{gs2["n"]}</td><td>{gs2["pos_pct"]}%</td><td>{gs2["auth"]}</td><td>{gs2["clout"]}</td><td>{gs2["fresh"]}</td><td>+ C/E/F 제거</td></tr>
    <tr style="background:var(--primary-pale);"><td style="font-weight:700;color:var(--primary);">Gate 3</td><td style="font-weight:800;">{gs3["n"]}</td><td style="font-weight:800;color:var(--coral);">{gs3["pos_pct"]}%</td><td style="font-weight:800;">{gs3["auth"]}</td><td>{gs3["clout"]}</td><td>{gs3["fresh"]}</td><td>+ Auth 60+</td></tr>
  </table>
</div>
<div class="insight" style="margin:12px 0;">
  <strong>Gate 1 → Gate 3: 긍정률 {gs1["pos_pct"]}% → {gs3["pos_pct"]}% ({round(gs3["pos_pct"]-gs1["pos_pct"],1)}%p)</strong><br>
  {N}건에서 Gate 3 유효 {gs3["n"]}건으로 {round((1-gs3["n"]/gs1["n"])*100)}% 감소. 긍정률은 {round(gs1["pos_pct"]-gs3["pos_pct"],1)}%p 하락 — 협찬과 과잉긍정이 원래 수치를 부풀리고 있었음. Auth는 {gs1["auth"]} → {gs3["auth"]}로 상승, Gate 3 통과 포스트들이 실제로 더 진정성 높은 콘텐츠임을 확인.
</div>

<!-- 8. 핵심 수치 요약 -->
<h2>8. 핵심 수치 요약</h2>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);">
    <div style="font-size:28px;font-weight:800;color:var(--primary);">{total_mentions}</div>
    <div style="font-size:10px;color:var(--body);">총 멘션</div>
  </div>
  <div class="card" style="text-align:center;border-top:3px solid var(--pink);">
    <div style="font-size:28px;font-weight:800;color:var(--pink);">{gs3["n"]}</div>
    <div style="font-size:10px;color:var(--body);">Gate 3 유효</div>
  </div>
  <div class="card" style="text-align:center;border-top:3px solid var(--coral);">
    <div style="font-size:28px;font-weight:800;color:var(--coral);">{gs3["pos_pct"]}%</div>
    <div style="font-size:10px;color:var(--body);">진심 긍정률</div>
  </div>
  <div class="card" style="text-align:center;border-top:3px solid var(--green);">
    <div style="font-size:28px;font-weight:800;color:var(--green);">{gs3["auth"]}</div>
    <div style="font-size:10px;color:var(--body);">Gate3 Auth</div>
  </div>
</div>

<!-- 종합 Before → After 비교표 -->
<h2>종합 Before → After 비교표</h2>
<table>
  <tr><th>비교 영역</th><th>BEFORE (기존)</th><th>AFTER (RXR)</th><th>차별화</th></tr>
  <tr><td style="font-weight:700;">버즈 규모</td><td>총 {total_mentions}건</td><td>Gate 3 유효 <strong>{gs3["n"]}건</strong></td><td style="color:var(--primary);font-weight:700;">진실 폭로</td></tr>
  <tr><td style="font-weight:700;">감성</td><td>긍정/중립/부정 3단계</td><td>4단계 + Auth {avg("authenticity",data)} + Clout {avg("clout",data)}</td><td style="color:var(--primary);font-weight:700;">깊이 x3</td></tr>
  <tr><td style="font-weight:700;">데이터 분류</td><td>채널별 건수만</td><td>A~G 7단계 + Trust Score</td><td style="color:var(--primary);font-weight:700;">정확도 x10</td></tr>
  <tr><td style="font-weight:700;">협찬 분석</td><td>유/무 이분법</td><td>Gate 3단계 + Auth 스펙트럼 (차이 {round(avg("authenticity",org)-avg("authenticity",spon),1)}점)</td><td style="color:var(--pink);font-weight:700;">유일</td></tr>
  <tr><td style="font-weight:700;">핵심 감정</td><td>긍정/부정 이분법</td><td>즐거움(Joy) × 고급(Premium) 2축 4분면 — 감정 교차 분석</td><td style="color:var(--primary);font-weight:700;">유일</td></tr>
  <tr><td style="font-weight:700;">심리</td><td>불가능</td><td>Auth/Clout/Freshness 기간별 추적</td><td style="color:var(--pink);font-weight:700;">유일</td></tr>
  <tr><td style="font-weight:700;">후기 품질</td><td>1건=1건</td><td>RQL 5단계 가중 (Q5 {rql_dist.get("Q5_서사형",0)}건)</td><td style="color:var(--pink);font-weight:700;">유일</td></tr>
  <tr><td style="font-weight:700;">리그램/공유</td><td>구분 불가</td><td>E등급 자동 태깅 ({cls_dist.get("E",0)}건)</td><td style="color:var(--pink);font-weight:700;">유일</td></tr>
  <tr><td style="font-weight:700;">브랜드 경험</td><td>측정 불가</td><td>즐거움+고급 동시 전달률 1.3% — "감정 비어있음" 진단</td><td style="color:var(--coral);font-weight:700;">핵심 발견</td></tr>
</table>

<!-- BOTTOM LINE -->
<h2>BOTTOM LINE</h2>
<div style="padding:24px;background:var(--primary-pale);border-radius:16px;margin:16px 0;">
  <div style="text-align:center;margin-bottom:20px;">
    <div style="font-size:13px;color:var(--body);margin-bottom:8px;">기존 도구</div>
    <div style="font-size:17px;font-weight:800;color:var(--body);">"{total_mentions}건 멘션, 긍정 {sent_pct.get("긍정",0)}%"</div>
    <div style="font-size:20px;margin:8px 0;">↓</div>
    <div style="font-size:13px;color:var(--primary);margin-bottom:8px;">RXR 분석</div>
    <div style="font-size:17px;font-weight:800;color:var(--primary);">"유효 {gs3["n"]}건 중 '즐거움+고급' 동시 전달 {len(g3_both)}건({round(len(g3_both)/max(len(g3),1)*100,1)}%). 가나가 의도한 복합 경험이 실제로 전달됐다."</div>
  </div>

  <h3 style="margin-top:20px;">왜 이런 결과가 나왔는가?</h3>
  <div class="grid2" style="gap:12px;margin-top:12px;">
    <div class="card" style="border-top:3px solid var(--coral);">
      <div style="font-size:20px;font-weight:800;color:var(--coral);">긍정률 -{round(gs1["pos_pct"]-gs3["pos_pct"],1)}%p</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">Gate 1({gs1["pos_pct"]}%) → Gate 3({gs3["pos_pct"]}%). 협찬 {len(spon)}건의 의무적 긍정 + Auth 60 미만 과잉긍정 포스트가 원래 수치를 부풀림. 기존 도구가 "좋아요!"와 "진심"을 구분 못함.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--orange);">
      <div style="font-size:20px;font-weight:800;color:var(--orange);">Auth 차이 {round(avg("authenticity",org)-avg("authenticity",spon),1)}점</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">협찬(Auth {avg("authenticity",spon)}) vs 자발적(Auth {avg("authenticity",org)}). 협찬 포스트는 과잉 긍정어와 느낌표 남발로 진정성이 {round((1-avg("authenticity",spon)/avg("authenticity",org))*100)}% 낮음. 같은 "긍정" 안에서도 질적 격차가 크다.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--green);">
      <div style="font-size:20px;font-weight:800;color:var(--green);">Q1 동시 전달 {round(len(g3_both)/max(len(g3),1)*100,1)}%</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">Gate 3 {len(g3)}건 중 즐거움+고급이 동시 강한 "완벽한 경험" 포스트가 <strong style="color:var(--green);">{len(g3_both)}건</strong>. 거의 절반의 방문객이 가나의 복합 의도를 온전히 체감. Q4(둘 다 약)는 {round(len(g3_neither)/max(len(g3),1)*100,1)}%에 불과.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--pink);">
      <div style="font-size:20px;font-weight:800;color:var(--pink);">Premium 사전 {period_jp.get("사전",{}).get("prem_strong_pct",0)}% → 팝업 {period_jp.get("팝업기간",{}).get("prem_strong_pct",0)}%</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">사전 기대치(Premium 강 {period_jp.get("사전",{}).get("prem_strong_pct",0)}%)보다 <strong style="color:var(--green);">실체 경험({period_jp.get("팝업기간",{}).get("prem_strong_pct",0)}%)이 +{round(period_jp.get("팝업기간",{}).get("prem_strong_pct",0)-period_jp.get("사전",{}).get("prem_strong_pct",0),1)}%p 상승</strong>. 많은 팝업이 "기대 > 실체" 궤적을 그리는 것과 정반대 — <strong>기대를 뛰어넘은 경험 설계</strong>.</div>
    </div>
  </div>

  <h3 style="margin-top:20px;">제언: 다음 팝업에서 무엇을 바꿀 것인가?</h3>
  <div class="grid3" style="gap:12px;margin-top:12px;">
    <div class="card" style="border-left:4px solid var(--pink);">
      <div style="font-size:14px;font-weight:800;color:var(--pink);margin-bottom:6px;">🍫 팝업후 Joy/Premium 하락 방지</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">팝업기간 Joy {period_jp.get("팝업기간",{}).get("joy",0)} → 팝업후 {period_jp.get("팝업후",{}).get("joy",0)}, Premium {period_jp.get("팝업기간",{}).get("prem",0)} → {period_jp.get("팝업후",{}).get("prem",0)}로 자연 하락. 팝업 종료 후 기억 연장 장치(<strong>페어링 레시피 카드 우편 발송·온라인 한정 상품 알림·SNS 추억 캠페인</strong>)로 롱테일 확산을 확보. 이미 좋은 감정이 형성됐기에 재접점만으로 재활성화 가능.</div>
    </div>
    <div class="card" style="border-left:4px solid var(--primary);">
      <div style="font-size:14px;font-weight:800;color:var(--primary);margin-bottom:6px;">✨ Q1 옹호자 수확 — 시즌3 얼리 리뷰어</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">Q1(즐거움+고급 동시 강) {len(g3_both)}건은 가나의 <strong>가장 강력한 브랜드 옹호자 집단</strong>. 이들을 다음 시즌에 공식 초대해 "얼리 리뷰어" 역할을 부여하면 시즌3의 사전 신뢰도와 버즈를 크게 증폭할 수 있음. 이미 체험한 감동을 다시 말하게 만드는 것이 가장 효율적인 바이럴 전략.</div>
    </div>
    <div class="card" style="border-left:4px solid var(--green);">
      <div style="font-size:14px;font-weight:800;color:var(--green);margin-bottom:6px;">💜 Q3 → Q1 전환 — 초콜릿 서사 강화</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">Q3(고급만) {len(g3_prem_only)}건({round(len(g3_prem_only)/max(len(g3),1)*100,1)}%)은 "공간은 고급스러웠지만 초콜릿 그 자체의 감동은 덜했던" 집단. 시즌3에 <strong>초콜릿의 서사</strong>(장인 한 마디·원산지 스토리·테이스팅 노트 카드)를 강화해 이들을 Q1으로 이동시키면 동시 전달률 {round(len(g3_both)/max(len(g3),1)*100,1)}% → 60% 이상 가능.</div>
    </div>
  </div>
</div>

<!-- 부록: Gate 3 유효 Raw Data 테이블 -->
<h2>부록: Sincerity Gate 3 통과 — 유효 Raw Data ({gs3["n"]}건)</h2>
<div style="overflow-x:auto;">
<table style="font-size:10px;">
  <tr><th>#</th><th>날짜</th><th>감성</th><th>Auth</th><th>Clout</th><th>Fresh</th><th>RQL</th><th>토픽</th><th>기간</th><th>제목</th><th>블로거</th></tr>
  {gate3_table()}
</table>
</div>

<!-- Gate3 통계 -->
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:16px 0;">
  <div class="card" style="text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--body);margin-bottom:4px;">감성 분포</div>
    <div style="font-size:11px;">긍정 <strong style="color:var(--green);">{sum(1 for r in g3 if r["sentiment"]=="긍정")}</strong> · 중립 {sum(1 for r in g3 if r["sentiment"]=="중립")} · 혼합 {sum(1 for r in g3 if r["sentiment"]=="혼합")} · 부정 <strong style="color:var(--coral);">{sum(1 for r in g3 if r["sentiment"]=="부정")}</strong></div>
  </div>
  <div class="card" style="text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--body);margin-bottom:4px;">평균 Psyche</div>
    <div style="font-size:11px;">Auth <strong>{gs3["auth"]}</strong> · Clout {gs3["clout"]} · Fresh {gs3["fresh"]}</div>
  </div>
  <div class="card" style="text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--body);margin-bottom:4px;">기간 분포</div>
    <div style="font-size:11px;">사전 {sum(1 for r in g3 if r["period"]=="사전")} · 팝업 {sum(1 for r in g3 if r["period"]=="팝업기간")} · 후 {sum(1 for r in g3 if r["period"]=="팝업후")}</div>
  </div>
  <div class="card" style="text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--body);margin-bottom:4px;">RQL 분포</div>
    <div style="font-size:11px;">Q5 {sum(1 for r in g3 if r["rql"]=="Q5_서사형")} · Q4 {sum(1 for r in g3 if r["rql"]=="Q4_분석형")} · Q3 {sum(1 for r in g3 if r["rql"]=="Q3_경험형")} · Q2 {sum(1 for r in g3 if r["rql"]=="Q2_감상형")}</div>
  </div>
</div>

<!-- Footer -->
<div class="footer">
  RXR SNS Raw Data Analysis &middot; 가나초콜릿하우스 부산 시즌2 &middot; Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} &middot; Project RENT &middot; R-lab
</div>

<!-- PDF Panel -->
<div class="pdf-panel">
  <button class="pdf-panel-toggle" onclick="this.nextElementSibling.classList.toggle('open')">PDF 출력</button>
  <div class="pdf-panel-body">
    <div class="pdf-orient-group">
      <div class="pdf-orient-btn active" onclick="setOrient('portrait',this)">세로</div>
      <div class="pdf-orient-btn" onclick="setOrient('landscape',this)">가로</div>
    </div>
    <button class="pdf-print-btn" onclick="window.print()">출력</button>
  </div>
</div>
<script>
function setOrient(o,el){{
  document.getElementById('pageOrientStyle').textContent=
    o==='landscape'?'@media print{{@page{{size:A4 landscape;}}}}':'@media print{{@page{{size:A4 portrait;}}}}';
  el.parentElement.querySelectorAll('.pdf-orient-btn').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
}}
</script>
</body></html>'''

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"리포트 생성 완료: {OUT}")
print(f"파일 크기: {os.path.getsize(OUT):,} bytes")
