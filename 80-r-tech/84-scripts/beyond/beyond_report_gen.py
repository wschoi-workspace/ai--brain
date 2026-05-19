"""비욘드(BEYOND) 팝업스토어 — RXR SNS HTML 리포트 3종 생성 (내부/외부/잠금)"""
import json, sys, io, os, hashlib, base64
from collections import Counter
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = os.path.dirname(__file__)
with open(os.path.join(BASE, "beyond-popup-2layer-results.json"), "r", encoding="utf-8") as f:
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

# Top/Low Auth posts
top_auth = sorted(data, key=lambda x: x.get("authenticity", 0), reverse=True)[:3]
low_auth = sorted(data, key=lambda x: x.get("authenticity", 0))[:3]

# 친환경 관련 토픽 통계
eco_count = sum(1 for r in data if r.get("primary_topic") == "친환경/지속가능성")
refill_count = sum(1 for r in data if r.get("primary_topic") == "리필/용기")
product_count = sum(1 for r in data if r.get("primary_topic") == "제품/성분")
eco_pct = round(eco_count / N * 100, 1)
refill_pct = round(refill_count / N * 100, 1)
product_pct = round(product_count / N * 100, 1)
eco_total = eco_count + refill_count
eco_total_pct = round(eco_total / N * 100, 1)

# 친환경 관련 포스트 Auth
eco_posts = [r for r in data if r.get("primary_topic") in ("친환경/지속가능성", "리필/용기")]
non_eco_posts = [r for r in data if r.get("primary_topic") not in ("친환경/지속가능성", "리필/용기")]
eco_auth = avg("authenticity", eco_posts) if eco_posts else 0
non_eco_auth = avg("authenticity", non_eco_posts) if non_eco_posts else 0

# Pre-compute period stats for f-string safety
ps_pre = period_stats.get("사전", {"n":0,"auth":0,"clout":0,"freshness":0,"pos_pct":0})
ps_dur = period_stats.get("팝업기간", {"n":0,"auth":0,"clout":0,"freshness":0,"pos_pct":0})
ps_post = period_stats.get("팝업후", {"n":0,"auth":0,"clout":0,"freshness":0,"pos_pct":0})

ps_pre_n = ps_pre["n"]
ps_pre_auth = ps_pre["auth"]
ps_pre_clout = ps_pre["clout"]
ps_pre_fresh = ps_pre["freshness"]
ps_pre_pos = ps_pre["pos_pct"]
ps_dur_n = ps_dur["n"]
ps_dur_auth = ps_dur["auth"]
ps_dur_clout = ps_dur["clout"]
ps_dur_fresh = ps_dur["freshness"]
ps_dur_pos = ps_dur["pos_pct"]
ps_post_n = ps_post["n"]
ps_post_auth = ps_post["auth"]
ps_post_clout = ps_post["clout"]
ps_post_fresh = ps_post["freshness"]
ps_post_pos = ps_post["pos_pct"]

# Pre-compute sent pct for f-string safety
sent_pos = sent_pct.get("긍정", 0)
sent_neu = sent_pct.get("중립", 0)
sent_mix = sent_pct.get("혼합", 0)
sent_neg = sent_pct.get("부정", 0)

# Pre-compute cls_dist
cls_A = cls_dist.get("A", 0)
cls_B = cls_dist.get("B", 0)
cls_C = cls_dist.get("C", 0)
cls_D = cls_dist.get("D", 0)
cls_E = cls_dist.get("E", 0)
cls_F = cls_dist.get("F", 0)
cls_G = cls_dist.get("G", 0)

# Pre-compute rql_dist
rql_q5 = rql_dist.get("Q5_서사형", 0)
rql_q4 = rql_dist.get("Q4_분석형", 0)
rql_q3 = rql_dist.get("Q3_경험형", 0)
rql_q2 = rql_dist.get("Q2_감상형", 0)
rql_q1 = rql_dist.get("Q1_간단형", 0)
rql_high = rql_q5 + rql_q4
rql_high_pct = round(rql_high / N * 100, 1)

# Sponsored/Organic avgs
spon_auth = avg("authenticity", spon) if spon else 0
org_auth = avg("authenticity", org) if org else 0
auth_diff = round(org_auth - spon_auth, 1)
auth_diff_pct = round((1 - spon_auth / max(org_auth, 1)) * 100)

# Overall avgs
overall_auth = avg("authenticity", data)
overall_clout = avg("clout", data)
overall_fresh = avg("freshness_index", data)

# Auth diff post→dur
auth_change = round(ps_post_auth - ps_dur_auth, 1)

# 부정 관련 분석 (그린워싱 체크)
neg_posts = [r for r in data if r["sentiment"] == "부정"]
neg_eco = [r for r in neg_posts if r.get("primary_topic") in ("친환경/지속가능성", "리필/용기")]

# Period ratios
ps_pre_ratio = round(ps_pre_n / N * 100) if N else 0
ps_dur_ratio = round(ps_dur_n / N * 100) if N else 0
ps_post_ratio = round(ps_post_n / N * 100) if N else 0

# Auth level converter
def auth_level(v):
    if v >= 75: return "매우 높음"
    if v >= 60: return "높음"
    if v >= 45: return "보통"
    if v >= 30: return "낮음"
    return "매우 낮음"

auth_pre_level = auth_level(ps_pre_auth)
auth_dur_level = auth_level(ps_dur_auth)
auth_post_level = auth_level(ps_post_auth)
clout_pre_level = auth_level(ps_pre_clout)
clout_dur_level = auth_level(ps_dur_clout)
clout_post_level = auth_level(ps_post_clout)

# topic top
topic_top_name = topic_dist[0][0] if topic_dist else ""
topic_top_cnt = topic_dist[0][1] if topic_dist else 0
topic_top_pct = round(topic_top_cnt / N * 100, 1) if N else 0

# Gate pos drop
gate_pos_drop = round(gs1["pos_pct"] - gs3["pos_pct"], 1)
gate_n_drop_pct = round((1 - gs3["n"] / max(gs1["n"], 1)) * 100)

# ============================================================
# Helper functions
# ============================================================
def fmt_date(yyyymmdd):
    return f"{yyyymmdd[:4]}.{yyyymmdd[4:6]}.{yyyymmdd[6:8]}" if len(yyyymmdd) >= 8 else yyyymmdd

def date_bars():
    rows = []
    for d, cnt in dates_sorted:
        pct = round(cnt / max_day * 100)
        md = f"{d[4:6]}/{d[6:8]}"
        if d < "20230525":
            color = "var(--orange)"; label = "사전" if d == dates_sorted[0][0] else ""
        elif d <= "20230618":
            color = "var(--primary)"; label = "팝업기간" if d == "20230525" else ""
        else:
            color = "#94a3b8"; label = "팝업후" if d == "20230619" else ""
        inner = f"{cnt}" if cnt >= 5 else ""
        rows.append(f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:40px;font-size:9px;color:var(--body);text-align:right;">{md}</div><div style="flex:1;height:15px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{max(pct,3)}%;height:100%;background:{color};border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;font-weight:600;color:#fff;">{inner}</div></div><div style="width:20px;font-size:9px;font-weight:600;">{cnt}</div><div style="width:65px;font-size:8px;color:{color};font-weight:700;">{label}</div></div>')
    return "\n".join(rows)

def gauge(label, value, max_val, color, width="100%"):
    pct = min(round(value / max(max_val, 1) * 100), 100)
    return f'<div class="gauge-row"><div class="gauge-label">{label}</div><div class="gauge-track"><div class="gauge-fill" style="width:{pct}%;background:{color};">{value}</div></div><div class="gauge-val" style="color:{color};">{value}</div></div>'

def topic_bars():
    rows = []
    max_t = topic_dist[0][1] if topic_dist else 1
    for topic, cnt in topic_dist:
        pct = round(cnt / max_t * 100)
        ratio = round(cnt / N * 100, 1)
        rows.append(f'<div class="gauge-row"><div class="gauge-label" style="width:120px;">{topic}</div><div class="gauge-track"><div class="gauge-fill" style="width:{pct}%;background:var(--primary);">{cnt}건 ({ratio}%)</div></div><div class="gauge-val" style="color:var(--primary);">{ratio}%</div></div>')
    return "\n".join(rows)

def gate3_table():
    rows = []
    gate3_sorted = sorted(g3, key=lambda x: x.get("date", ""))
    for i, r in enumerate(gate3_sorted):
        bg = "#f0fdf4" if i % 2 == 0 else "#fff"
        sent_color_map = {"긍정": "var(--green)", "부정": "var(--coral)", "혼합": "var(--blue)", "중립": "#94a3b8"}
        sc = sent_color_map.get(r["sentiment"], "#94a3b8")
        auth_color = "var(--green)" if r["authenticity"] >= 75 else "var(--primary)"
        link = r.get("link", "#")
        title = r.get("title", "")[:60]
        rows.append(f'<tr style="background:{bg};"><td style="text-align:center;">{i+1}</td><td>{fmt_date(r["date"])}</td><td style="color:{sc};font-weight:700;">{r["sentiment"]}</td><td style="color:{auth_color};font-weight:700;">{r["authenticity"]}</td><td>{r["clout"]}</td><td>{r["freshness_index"]}</td><td>{r["rql"]}</td><td>{r["primary_topic"]}</td><td>{r["period"]}</td><td><a href="{link}" target="_blank" style="color:var(--primary);text-decoration:none;">{title}</a></td><td>{r.get("blogger","")}</td></tr>')
    return "\n".join(rows)

def spon_spectrum():
    rows = []
    for r in sorted(spon, key=lambda x: x.get("authenticity", 0), reverse=True)[:10]:
        auth = r["authenticity"]
        bg = "#f0fdf4" if auth >= 60 else ("#fffbeb" if auth >= 40 else "#fef2f2")
        color = "var(--green)" if auth >= 60 else ("var(--orange)" if auth >= 40 else "var(--coral)")
        rows.append(f'<div style="padding:8px 12px;background:{bg};border-radius:8px;margin-bottom:4px;font-size:11px;display:flex;align-items:center;gap:8px;"><div style="font-weight:800;min-width:50px;color:{color};">Auth {auth}</div><div style="flex:1;">{r["title"][:50]}</div><div style="color:var(--body);font-size:10px;">{r["sentiment"]}</div></div>')
    return "\n".join(rows)

# Highlight cards for external
high_auth_posts = sorted(g3, key=lambda x: x.get("authenticity", 0), reverse=True)[:10]
low_auth_all = sorted(data, key=lambda x: x.get("authenticity", 0))[:10]

def highlight_cards(items, style="high"):
    cards = []
    for r in items:
        auth = r.get("authenticity", 0)
        level = auth_level(auth)
        bg = "#f0fdf4" if style == "high" else "#fef2f2"
        border_color = "var(--green)" if style == "high" else "var(--coral)"
        sent = r.get("sentiment", "중립")
        sent_color_map = {"긍정":"var(--green)","부정":"var(--coral)","혼합":"var(--blue)","중립":"#94a3b8"}
        sc = sent_color_map.get(sent, "#94a3b8")
        rql = r.get("rql","").replace("_"," ")
        cards.append(f'''<div style="padding:12px 16px;background:{bg};border-radius:10px;border-left:4px solid {border_color};margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span style="font-size:11px;font-weight:700;color:{border_color};">진정성 {level}</span>
            <span style="font-size:10px;color:var(--body);">{fmt_date(r.get("date",""))}</span>
          </div>
          <div style="font-size:13px;font-weight:600;margin-bottom:4px;">{r.get("title","")[:55]}</div>
          <div style="font-size:10px;color:var(--body);display:flex;gap:12px;">
            <span style="color:{sc};font-weight:600;">{sent}</span>
            <span>{rql}</span>
            <span>{r.get("primary_topic","")}</span>
          </div>
        </div>''')
    return "\n".join(cards)

# Gate3 stats for appendix
g3_pos = sum(1 for r in g3 if r["sentiment"] == "긍정")
g3_neu = sum(1 for r in g3 if r["sentiment"] == "중립")
g3_mix = sum(1 for r in g3 if r["sentiment"] == "혼합")
g3_neg = sum(1 for r in g3 if r["sentiment"] == "부정")
g3_pre = sum(1 for r in g3 if r["period"] == "사전")
g3_dur = sum(1 for r in g3 if r["period"] == "팝업기간")
g3_post = sum(1 for r in g3 if r["period"] == "팝업후")
g3_rql5 = sum(1 for r in g3 if r["rql"] == "Q5_서사형")
g3_rql4 = sum(1 for r in g3 if r["rql"] == "Q4_분석형")
g3_rql3 = sum(1 for r in g3 if r["rql"] == "Q3_경험형")
g3_rql2 = sum(1 for r in g3 if r["rql"] == "Q2_감상형")

# ============================================================
# CSS (shared)
# ============================================================
CSS = '''@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable.css');
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=DIN+Alternate&display=swap');
:root{--primary:#6666FF;--grad:linear-gradient(135deg,#5353FF,#8A8AFF);--black:#000;--dark:#262626;--body:#424D61;--light:#F6F6F6;--white:#FFF;--red:#C00000;--coral:#FF5050;--blue:#4D93F7;--green:#10b981;--orange:#f59e0b;--pink:#d946ef;--primary-pale:#E1E1FF;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Pretendard Variable',system-ui,sans-serif;background:var(--white);color:var(--dark);font-size:14px;line-height:1.6;max-width:1200px;margin:0 auto;padding:40px 32px;}
h1{font-size:28px;font-weight:800;margin-bottom:4px;} h2{font-size:20px;font-weight:800;margin:32px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--primary-pale);} h3{font-size:15px;font-weight:700;margin:14px 0 8px;}
.sub{font-size:13px;color:var(--body);margin-bottom:20px;}
.card{background:var(--light);border:1px solid #e8e8e8;border-radius:12px;padding:16px 18px;}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;} .grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}
table{width:100%;border-collapse:collapse;font-size:12px;margin:10px 0;}
th{background:var(--primary);color:#fff;padding:6px 10px;text-align:left;font-size:11px;} td{padding:5px 10px;border-bottom:1px solid #eee;}
.insight{padding:14px 18px;background:var(--primary-pale);border-radius:10px;border-left:4px solid var(--primary);margin:10px 0;font-size:13px;line-height:1.7;} .insight strong{color:var(--primary);}
.insight-warn{background:#fef2f2;border-left-color:var(--coral);} .insight-warn strong{color:var(--coral);}
.ba-container{display:grid;grid-template-columns:1fr 50px 1fr;gap:0;align-items:stretch;margin:16px 0;}
.ba-box{padding:20px;border-radius:14px;} .ba-before{background:#f1f5f9;border:2px solid #cbd5e1;} .ba-after{background:#eef2ff;border:2px solid var(--primary);}
.ba-vs{display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:900;color:#94a3b8;}
.ba-label{font-size:12px;font-weight:700;letter-spacing:1px;margin-bottom:10px;} .ba-title{font-size:16px;font-weight:800;margin-bottom:12px;}
.gauge-row{display:flex;align-items:center;gap:8px;margin-bottom:8px;}
.gauge-label{width:120px;font-size:12px;font-weight:600;text-align:right;flex-shrink:0;}
.gauge-track{flex:1;height:24px;background:#f0f0f0;border-radius:5px;overflow:hidden;}
.gauge-fill{height:100%;border-radius:5px;display:flex;align-items:center;padding-left:8px;font-size:10px;font-weight:700;color:#fff;}
.gauge-val{width:45px;font-family:'DIN Alternate','Poppins',sans-serif;font-size:15px;font-weight:700;text-align:center;flex-shrink:0;}
.footer{margin-top:40px;padding-top:16px;border-top:2px solid var(--primary);font-size:11px;color:#94a3b8;text-align:center;}
@media print{
  @page{size:A4 portrait;margin:14mm 12mm;}
  body{max-width:100%!important;padding:0!important;margin:0!important;}
  .pdf-panel{display:none!important;}
  .card,.ba-container,.grid2,.grid3,.insight,.gauge-row,table{break-inside:avoid!important;page-break-inside:avoid!important;}
  h2,h3{break-after:avoid;page-break-after:avoid;}
  h1{font-size:22px!important;} h2{font-size:16px!important;margin-top:20px!important;}
  .card{padding:10px 12px!important;font-size:10px!important;} table{font-size:10px!important;} th,td{padding:4px 6px!important;}
}
.pdf-panel{position:fixed;bottom:24px;right:24px;z-index:1000;}
.pdf-panel-toggle{display:flex;align-items:center;gap:8px;padding:12px 22px;background:var(--grad);color:#fff;border-radius:50px;font-size:14px;font-weight:600;cursor:pointer;box-shadow:0 4px 20px rgba(102,102,255,0.4);border:none;font-family:'Pretendard Variable',sans-serif;}
.pdf-panel-body{display:none;position:absolute;bottom:56px;right:0;width:220px;background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.18);padding:16px;}
.pdf-panel-body.open{display:block;}
.pdf-orient-group{display:flex;gap:8px;margin-bottom:14px;}
.pdf-orient-btn{flex:1;padding:12px 8px;background:#f9fafb;border:2px solid #e2e8f0;border-radius:12px;cursor:pointer;font-family:'Pretendard Variable',sans-serif;color:#475569;font-size:11px;font-weight:600;text-align:center;}
.pdf-orient-btn.active{border-color:var(--primary);background:#eef2ff;color:var(--primary);}
.pdf-print-btn{width:100%;padding:10px;background:var(--grad);color:#fff;border:none;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Pretendard Variable',sans-serif;}'''

PDF_PANEL = '''<div class="pdf-panel">
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
function setOrient(o,el){
  document.getElementById('pageOrientStyle').textContent=
    o==='landscape'?'@media print{@page{size:A4 landscape;}}':'@media print{@page{size:A4 portrait;}}';
  el.parentElement.querySelectorAll('.pdf-orient-btn').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
}
</script>'''

# pre-computed daily avg for popup period (25 days)
dur_daily_avg = round(ps_dur_n / 25, 1)
pre_days = 14  # 05/11 ~ 05/24
post_days = 14  # 06/19 ~ 07/02
pre_daily_avg = round(ps_pre_n / max(pre_days, 1), 1)
post_daily_avg = round(ps_post_n / max(post_days, 1), 1)

# ============================================================
# 1. 내부용 HTML
# ============================================================
internal_html = f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>비욘드 팝업스토어 — RXR SNS 분석</title>
<style>{CSS}</style><style id="pageOrientStyle"></style></head><body>

<!-- HEADER -->
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
  <span style="background:var(--grad);color:#fff;padding:4px 14px;border-radius:6px;font-family:'Poppins';font-size:11px;font-weight:600;letter-spacing:1px;">RXR SNS ANALYSIS</span>
</div>
<h1>LG생활건강 비욘드(BEYOND) — "Less plastic, Paper is enough" 팝업스토어</h1>
<div class="sub">기존 분석 vs RXR 2-Layer + Sincerity Gate | 네이버 블로그 {N}건 | Project RENT &middot; R-lab</div>

<!-- 리서치 개요 -->
<div style="padding:20px;background:var(--light);border-radius:14px;margin-bottom:24px;">
  <div class="grid2">
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">ABOUT THIS RESEARCH</div>
      <h3 style="margin-top:0;">분석 대상</h3>
      <table style="font-size:12px;"><tr><td style="color:var(--body);width:70px;padding:4px 0;">팝업명</td><td style="padding:4px 0;font-weight:700;">비욘드 팝업스토어 "Less plastic, Paper is enough"</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">브랜드</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">LG생활건강 / 비욘드(BEYOND)</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2023.05.25 ~ 06.18, <strong>25일간</strong></td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">장소</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">서울 성수동 서울숲길</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">컨셉</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">친환경 / 지속가능성 / 클린뷰티 — "플라스틱 줄이고 종이면 충분하다"</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">분석 기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2023.05.11 ~ 07.02</td></tr></table>
    </div>
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">RESEARCH PERSPECTIVE</div>
      <h3 style="margin-top:0;">리서치 관점</h3>
      <div style="font-size:12px;color:var(--body);line-height:1.7;">
        <div style="padding:4px 0;"><strong style="color:var(--primary);">핵심 질문:</strong> "친환경/지속가능성" 컨셉이 소비자 언어에 침투했는가? 체험이 진정성 있는 인식 변화를 이끌었는가?</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">데이터:</strong> 네이버 블로그 {N}건 (팝업 특화 Brand24 데이터 없음)</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">분석:</strong> Content + Psyche + Sincerity Gate 3단계</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">특이사항:</strong> 25일 장기 운영 + 친환경 체험 중심 → Auth 피로 여부 관찰</div>
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
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);padding:14px;"><div style="font-size:32px;font-weight:800;color:var(--primary);">{N}</div><div style="font-size:11px;color:var(--body);font-weight:600;">네이버 블로그 총 멘션</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--green);padding:14px;"><div style="font-size:32px;font-weight:800;color:var(--green);">25일</div><div style="font-size:11px;color:var(--body);font-weight:600;">팝업 운영 기간</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--pink);padding:14px;"><div style="font-size:32px;font-weight:800;color:var(--pink);">{gs3["n"]}</div><div style="font-size:11px;color:var(--body);font-weight:600;">Gate 3 유효</div></div>
</div>

<h3>데이터 소스</h3>
<div class="card" style="border-left:4px solid var(--primary);margin:10px 0;">
  <div style="font-size:11px;font-family:'Poppins';letter-spacing:1px;color:var(--body);margin-bottom:6px;">NAVER BLOG (심층 분석)</div>
  <div style="font-size:28px;font-weight:800;color:var(--primary);">{N}<span style="font-size:13px;font-weight:600;color:var(--body);"> 건</span></div>
  <div style="margin-top:8px;">
    <table style="font-size:11px;margin:0;"><tbody>
      <tr><td style="color:var(--orange);font-weight:600;border:none;padding:2px 6px;">사전</td><td style="border:none;padding:2px 6px;"><strong>{ps_pre_n}</strong> ({ps_pre_ratio}%)</td></tr>
      <tr><td style="color:var(--primary);font-weight:600;border:none;padding:2px 6px;">팝업기간</td><td style="border:none;padding:2px 6px;"><strong>{ps_dur_n}</strong> ({ps_dur_ratio}%)</td></tr>
      <tr><td style="color:#94a3b8;font-weight:600;border:none;padding:2px 6px;">팝업후</td><td style="border:none;padding:2px 6px;"><strong>{ps_post_n}</strong> ({ps_post_ratio}%)</td></tr>
    </tbody></table>
  </div>
  <div style="margin-top:8px;padding:6px 8px;background:var(--primary-pale);border-radius:6px;font-size:10px;color:var(--primary);">API 직접 크롤링 → Content + Psyche Layer 심층 분석 | Brand24 팝업 특화 데이터 없음 (LG생활건강 전체 583건은 참고용)</div>
</div>

<h3>날짜별 버즈 분포</h3>
{date_bars()}

<h3>기간별 비교</h3>
<div class="grid2" style="margin:10px 0;">
  <div>
    <table>
      <tr><th>기간</th><th>건수</th><th>일평균</th><th>비율</th></tr>
      <tr><td style="color:var(--orange);font-weight:700;">사전 (05/11~05/24)</td><td><strong>{ps_pre_n}</strong></td><td>{pre_daily_avg}</td><td>{ps_pre_ratio}%</td></tr>
      <tr><td style="color:var(--primary);font-weight:700;">팝업기간 (05/25~06/18)</td><td><strong>{ps_dur_n}</strong></td><td>{dur_daily_avg}</td><td>{ps_dur_ratio}%</td></tr>
      <tr><td style="color:#94a3b8;font-weight:700;">팝업후 (06/19~07/02)</td><td><strong>{ps_post_n}</strong></td><td>{post_daily_avg}</td><td>{ps_post_ratio}%</td></tr>
    </table>
  </div>
  <div class="grid2" style="gap:8px;">
    <div class="card" style="text-align:center;padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--primary);">{dur_daily_avg}</div><div style="font-size:10px;color:var(--body);">팝업기간 일평균</div></div>
    <div class="card" style="text-align:center;padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--green);">{eco_pct}%</div><div style="font-size:10px;color:var(--body);">친환경 침투도</div></div>
    <div class="card" style="text-align:center;padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--orange);">{overall_auth}</div><div style="font-size:10px;color:var(--body);">전체 Auth</div></div>
    <div class="card" style="text-align:center;padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--pink);">25일</div><div style="font-size:10px;color:var(--body);">팝업 운영 기간</div></div>
  </div>
</div>

<!-- 1. 감성 분석 Before -> After -->
<h2>1. 감성 분석 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE — 기존 도구</div>
    <div class="ba-title">3단계 감성 분류</div>
    <div style="font-size:13px;color:var(--body);line-height:1.7;">기존 도구는 긍정/중립/부정 <strong>3단계</strong>로 분류합니다. {N}건 중 긍정 {sent_pos}%로 표시되며, "혼합"(긍정+부정 공존)은 구분하지 못합니다.</div>
    <div style="margin-top:12px;padding:12px;background:#e2e8f0;border-radius:8px;text-align:center;font-size:20px;font-weight:800;">긍정 {sent_pos}%</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER — RXR</div>
    <div class="ba-title">4단계 + Auth + Clout</div>
    {gauge("긍정", sent_pos, 100, "var(--green)")}
    {gauge("중립", sent_neu, 100, "#94a3b8")}
    {gauge("혼합", sent_mix, 100, "var(--blue)")}
    {gauge("부정", sent_neg, 100, "var(--coral)")}
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      <strong style="color:var(--primary);">해석:</strong> 긍정 {sent_pos}%에 혼합 {sent_mix}%를 더하면 {round(sent_pos + sent_mix, 1)}%가 긍정 요소를 포함. 그러나 Gate 3 적용 시 진심 긍정은 <strong style="color:var(--coral);">{gs3["pos_pct"]}%</strong>로 하락. 중립이 {sent_neu}%로 과반 — 친환경 팝업의 특성상 "정보 전달형" 포스트가 많았음.
    </div>
  </div>
</div>

<!-- 2. 데이터 분류 Before -> After -->
<h2>2. 데이터 분류 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">채널별 건수만</div>
    <div style="font-size:13px;color:var(--body);line-height:1.7;">기존 도구는 블로그/인스타/뉴스 등 <strong>채널별 건수</strong>만 제공합니다. 모든 1건은 동일한 가치로 취급됩니다.</div>
    <div style="margin-top:12px;padding:12px;background:#e2e8f0;border-radius:8px;text-align:center;font-size:15px;font-weight:700;">{N}건 = 1건 x {N}</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">A~G 7단계 분류</div>
    <table style="font-size:11px;">
      <tr><th>등급</th><th>분류</th><th>건수</th><th>처리</th></tr>
      <tr style="background:#f0fdf4;"><td style="font-weight:800;color:var(--green);">A</td><td>진성후기</td><td><strong>{cls_A}</strong></td><td>핵심 분석</td></tr>
      <tr><td style="font-weight:800;">B</td><td>일반포스트</td><td><strong>{cls_B}</strong></td><td>분석 대상</td></tr>
      <tr style="background:#fffbeb;"><td style="font-weight:800;color:var(--orange);">C</td><td>협찬/체험단</td><td><strong>{cls_C}</strong></td><td>진심 스펙트럼</td></tr>
      <tr><td style="font-weight:800;color:#94a3b8;">D</td><td>나열형</td><td><strong>{cls_D}</strong></td><td>카운트만</td></tr>
      <tr><td style="font-weight:800;color:#94a3b8;">E</td><td>리그램</td><td><strong>{cls_E}</strong></td><td>카운트만</td></tr>
      <tr style="background:#fef2f2;"><td style="font-weight:800;color:var(--coral);">F</td><td>비즈/보도</td><td><strong>{cls_F}</strong></td><td>제외</td></tr>
      <tr style="background:#fef2f2;"><td style="font-weight:800;color:var(--coral);">G</td><td>노이즈</td><td><strong>{cls_G}</strong></td><td>제외</td></tr>
    </table>
    <div style="padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;margin-top:8px;">
      <strong style="color:var(--primary);">해석:</strong> B등급(일반) {cls_B}건이 {round(cls_B/N*100)}%로 대다수. A등급(진성후기) {cls_A}건({round(cls_A/N*100,1)}%)은 개인 경험+구체적 디테일이 풍부한 고품질 후기. C등급(협찬) {cls_C}건({round(cls_C/N*100,1)}%)은 제외하지 않고 Auth 스펙트럼으로 분석.
    </div>
  </div>
</div>

<!-- 3. 토픽 분석 Before -> After -->
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
    <div class="ba-title">구조화 토픽 비중</div>
    {topic_bars()}
    <div style="padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;margin-top:10px;">
      <strong style="color:var(--primary);">해석:</strong> <strong>제품/성분({product_pct}%)</strong>이 1위지만, <strong style="color:var(--green);">친환경/지속가능성({eco_pct}%) + 리필/용기({refill_pct}%) = {eco_total_pct}%</strong>가 친환경 관련 토픽 합계. 컨셉 침투도 {eco_pct}%는 컴온스타일의 "슬로우에이징" 0%와 비교하면 <strong>의미 있는 수준</strong>의 컨셉 전달. 체험형 친환경 팝업의 효과가 확인됨.
    </div>
  </div>
</div>

<!-- 4. 친환경 컨셉 침투도 분석 (NEW) -->
<h2>4. 친환경 컨셉 침투도 분석</h2>
<div style="padding:20px;background:linear-gradient(135deg,#ecfdf5,#f0fdf4);border-radius:14px;border:2px solid var(--green);margin:16px 0;">
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;">
    <div style="text-align:center;"><div style="font-size:28px;font-weight:800;color:var(--green);">{eco_pct}%</div><div style="font-size:10px;color:var(--body);">친환경/지속가능성</div></div>
    <div style="text-align:center;"><div style="font-size:28px;font-weight:800;color:#00b4d8;">{refill_pct}%</div><div style="font-size:10px;color:var(--body);">리필/용기</div></div>
    <div style="text-align:center;"><div style="font-size:28px;font-weight:800;color:var(--primary);">{eco_total_pct}%</div><div style="font-size:10px;color:var(--body);">친환경 토픽 합계</div></div>
    <div style="text-align:center;"><div style="font-size:28px;font-weight:800;color:var(--orange);">{product_pct}%</div><div style="font-size:10px;color:var(--body);">제품/성분</div></div>
  </div>

  <h3 style="color:var(--green);">제품 vs 친환경 — 어느 쪽이 더 강한 인상을 남겼는가?</h3>
  <div class="grid2" style="margin:10px 0;gap:12px;">
    <div class="card" style="border-top:3px solid var(--orange);">
      <div style="font-size:16px;font-weight:800;color:var(--orange);">제품/성분 1위 ({product_count}건, {product_pct}%)</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">리필 제품(PET 대비 37g 감축), 샴푸·바디워시·핸드크림 등 구체적 제품 경험이 가장 많은 토픽. 비욘드의 제품력 자체에 대한 관심이 높았음.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--green);">
      <div style="font-size:16px;font-weight:800;color:var(--green);">친환경 합계 ({eco_total}건, {eco_total_pct}%)</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">친환경/지속가능성({eco_count}건) + 리필/용기({refill_count}건). "종이로 만든 공간", "플라스틱 교환 자판기", "유기농 향주머니" 등 <strong>체험형 컨셉이 소비자 언어에 침투</strong>한 증거.</div>
    </div>
  </div>

  <h3 style="color:var(--green);">친환경 포스트 vs 비친환경 포스트 심리 비교</h3>
  <div class="grid2" style="gap:8px;">
    <div style="text-align:center;padding:10px;background:#fff;border-radius:8px;">
      <div style="font-size:24px;font-weight:800;color:var(--green);">Auth {eco_auth}</div>
      <div style="font-size:10px;">친환경 토픽 ({eco_total}건)</div>
    </div>
    <div style="text-align:center;padding:10px;background:#fff;border-radius:8px;">
      <div style="font-size:24px;font-weight:800;color:var(--body);">Auth {non_eco_auth}</div>
      <div style="font-size:10px;">비친환경 토픽 ({N - eco_total}건)</div>
    </div>
  </div>

  <div class="insight" style="margin:12px 0;background:#fff;">
    <strong style="color:var(--green);">그린워싱 인식 여부:</strong> 부정 포스트 {len(neg_posts)}건 중 친환경 토픽 관련 부정은 {len(neg_eco)}건. 전체 부정률 {sent_neg}%는 낮은 수준이며, 소비자는 비욘드의 친환경 노력을 <strong>그린워싱이 아닌 진정성 있는 시도</strong>로 인식한 것으로 판단됨. 종이로 구현한 공간, 실제 리필 제품 판매, 플라스틱 교환 자판기 등 <strong>구체적 실천</strong>이 진정성을 뒷받침함.
  </div>

  <div class="insight" style="background:#fffbeb;border-left-color:var(--orange);">
    <strong style="color:var(--orange);">컴온스타일과의 비교:</strong> 컴온스타일의 "슬로우에이징" 컨셉 침투도 0% vs 비욘드의 친환경 침투도 {eco_pct}%. 차이의 원인: 비욘드는 "종이 공간", "리필", "플라스틱 교환" 등 <strong>눈에 보이고 손으로 만지는 체험</strong>으로 컨셉을 구현. 슬로우에이징은 추상적 슬로건에 그쳐 체험→언어 전환이 이뤄지지 않음.
  </div>
</div>

<!-- 5. 심리 분석 -->
<h2>5. 심리 분석 (Authenticity / Clout / Freshness)</h2>
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
    {gauge("Authenticity", overall_auth, 100, "var(--primary)")}
    {gauge("Clout", overall_clout, 100, "var(--green)")}
    {gauge("Freshness", overall_fresh, 100, "var(--orange)")}
  </div>
</div>

<h3>기간별 심리 변화</h3>
<div class="grid3">
  <div class="card" style="border-top:3px solid var(--orange);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--orange);margin-bottom:8px;">사전</div>
    <div style="font-size:28px;font-weight:800;color:var(--orange);">{ps_pre_auth}</div>
    <div style="font-size:10px;color:var(--body);">Auth</div>
    <div style="margin-top:6px;font-size:12px;">Clout {ps_pre_clout} · Fresh {ps_pre_fresh}</div>
    <div style="margin-top:6px;font-size:11px;color:var(--body);">긍정률 {ps_pre_pos}%</div>
  </div>
  <div class="card" style="border-top:3px solid var(--primary);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--primary);margin-bottom:8px;">팝업기간</div>
    <div style="font-size:28px;font-weight:800;color:var(--primary);">{ps_dur_auth}</div>
    <div style="font-size:10px;color:var(--body);">Auth</div>
    <div style="margin-top:6px;font-size:12px;">Clout {ps_dur_clout} · Fresh {ps_dur_fresh}</div>
    <div style="margin-top:6px;font-size:11px;color:var(--body);">긍정률 {ps_dur_pos}%</div>
  </div>
  <div class="card" style="border-top:3px solid var(--green);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--green);margin-bottom:8px;">팝업후</div>
    <div style="font-size:28px;font-weight:800;color:var(--green);">{ps_post_auth}</div>
    <div style="font-size:10px;color:var(--body);">Auth</div>
    <div style="margin-top:6px;font-size:12px;">Clout {ps_post_clout} · Fresh {ps_post_fresh}</div>
    <div style="margin-top:6px;font-size:11px;color:var(--body);">긍정률 {ps_post_pos}%</div>
  </div>
</div>
<div class="insight" style="margin:12px 0;">
  <strong>기간별 Auth 변화: 사전 {ps_pre_auth} → 팝업기간 {ps_dur_auth} → 팝업후 {ps_post_auth}</strong><br>
  <strong style="color:var(--green);">25일 장기 운영에도 Auth 피로가 없다.</strong> 사전(Auth {ps_pre_auth}) 대비 팝업기간(Auth {ps_dur_auth}) 상승, 팝업후(Auth {ps_post_auth})까지 유지 또는 상승. 이는 16일 운영한 새로 팝업이나 5일 운영한 컴온스타일과 다른 패턴으로, <strong>친환경 가치가 진정성을 지탱하는 힘</strong>으로 작용. 25일간 방문자가 "진짜 좋은 의미의 팝업"이라는 인식을 유지했음을 의미.
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

<!-- 6. 협찬 vs 자발적 -->
<h2>6. 협찬 분석 Before → After</h2>
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
        <div style="font-size:10px;">협찬 | Auth <strong>{spon_auth}</strong></div>
      </div>
      <div style="text-align:center;padding:10px;background:#f0fdf4;border-radius:8px;">
        <div style="font-size:24px;font-weight:800;color:var(--green);">{len(org)}<span style="font-size:12px;">건</span></div>
        <div style="font-size:10px;">자발적 | Auth <strong>{org_auth}</strong></div>
      </div>
    </div>
    <div style="margin-top:8px;font-size:12px;font-weight:700;color:var(--coral);text-align:center;">Auth 차이: {auth_diff}점</div>
  </div>
</div>

<h3>협찬 포스트 Auth 스펙트럼</h3>
{spon_spectrum()}
<div style="padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;margin-top:8px;">
  <strong style="color:var(--primary);">해석:</strong> 협찬 포스트(Auth {spon_auth})는 자발적(Auth {org_auth}) 대비 진정성이 <strong>{auth_diff_pct}% 낮음</strong>. 그러나 {len(spon)}건으로 전체의 {round(len(spon)/N*100,1)}%에 불과하며, 대다수({len(org)}건, {round(len(org)/N*100,1)}%)가 자발적 후기. 친환경 팝업의 특성상 "자발적으로 공유하고 싶은" 동기가 강했음.
</div>

<!-- 7. 후기 품질 Before -> After -->
<h2>7. 후기 품질 Before → After</h2>
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
    {gauge("Q5 서사형 (x2.0)", rql_q5, N, "var(--primary)")}
    {gauge("Q4 분석형 (x1.5)", rql_q4, N, "var(--blue)")}
    {gauge("Q3 경험형 (x1.0)", rql_q3, N, "var(--green)")}
    {gauge("Q2 감상형 (x0.5)", rql_q2, N, "var(--orange)")}
    {gauge("Q1 간단형 (x0.2)", rql_q1, N, "#94a3b8")}
    <div style="padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;margin-top:8px;">
      <strong style="color:var(--primary);">해석:</strong> Q5 서사형 {rql_q5}건({round(rql_q5/N*100,1)}%) + Q4 분석형 {rql_q4}건({round(rql_q4/N*100,1)}%) = 고품질 후기 {rql_high}건({rql_high_pct}%). 친환경 체험이 상세한 서사를 이끌어내는 데 효과적이지만, Q5 비율을 높이려면 "공유 가능한 인증" 장치가 필요.
    </div>
  </div>
</div>

<!-- 8. Sincerity Gate -->
<h2>8. Sincerity Gate — 3단계 진심 필터</h2>
<div style="margin:16px 0;">
  <div style="display:flex;align-items:center;gap:4px;margin-bottom:12px;">
    <div style="flex:{gs1["n"]};height:48px;background:var(--primary-pale);border-radius:10px 0 0 10px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:var(--primary);">Gate 1: {gs1["n"]}건</div>
    <div style="flex:{gs2["n"]};height:48px;background:#c7d2fe;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:var(--primary);">Gate 2: {gs2["n"]}건</div>
    <div style="flex:{gs3["n"]};height:48px;background:var(--primary);border-radius:0 10px 10px 0;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;">Gate 3: {gs3["n"]}건</div>
  </div>
  <table>
    <tr><th></th><th>건수</th><th>긍정률</th><th>Auth</th><th>Clout</th><th>Freshness</th><th>필터</th></tr>
    <tr><td style="font-weight:700;">Gate 1</td><td>{gs1["n"]}</td><td>{gs1["pos_pct"]}%</td><td>{gs1["auth"]}</td><td>{gs1["clout"]}</td><td>{gs1["fresh"]}</td><td>G(노이즈) 제거</td></tr>
    <tr><td style="font-weight:700;">Gate 2</td><td>{gs2["n"]}</td><td>{gs2["pos_pct"]}%</td><td>{gs2["auth"]}</td><td>{gs2["clout"]}</td><td>{gs2["fresh"]}</td><td>+ C/E/F 제거</td></tr>
    <tr style="background:var(--primary-pale);"><td style="font-weight:700;color:var(--primary);">Gate 3</td><td style="font-weight:800;">{gs3["n"]}</td><td style="font-weight:800;color:var(--coral);">{gs3["pos_pct"]}%</td><td style="font-weight:800;">{gs3["auth"]}</td><td>{gs3["clout"]}</td><td>{gs3["fresh"]}</td><td>+ Auth 60+</td></tr>
  </table>
</div>
<div class="insight" style="margin:12px 0;">
  <strong>Gate 1 → Gate 3: 긍정률 {gs1["pos_pct"]}% → {gs3["pos_pct"]}% ({round(gs3["pos_pct"]-gs1["pos_pct"],1)}%p)</strong><br>
  {N}건에서 Gate 3 유효 {gs3["n"]}건으로 {gate_n_drop_pct}% 감소. 긍정률은 {gate_pos_drop}%p 하락 — 그러나 이 하락폭(-{gate_pos_drop}%p)은 컴온스타일(-8.4%p)보다 적어, <strong>과장 긍정이 상대적으로 적음</strong>을 의미. 친환경 팝업의 후기가 보다 진실에 가까움.
</div>

<!-- 9. 핵심 수치 요약 -->
<h2>9. 핵심 수치 요약</h2>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);">
    <div style="font-size:28px;font-weight:800;color:var(--primary);">{N}</div>
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
    <div style="font-size:28px;font-weight:800;color:var(--green);">{eco_pct}%</div>
    <div style="font-size:10px;color:var(--body);">친환경 침투도</div>
  </div>
</div>

<!-- 10. 종합 Before -> After 비교표 -->
<h2>10. 종합 Before → After 비교표</h2>
<table>
  <tr><th>비교 영역</th><th>BEFORE (기존)</th><th>AFTER (RXR)</th><th>차별화</th></tr>
  <tr><td style="font-weight:700;">버즈 규모</td><td>총 {N}건</td><td>Gate 3 유효 <strong>{gs3["n"]}건</strong></td><td style="color:var(--primary);font-weight:700;">진실 폭로</td></tr>
  <tr><td style="font-weight:700;">감성</td><td>긍정/중립/부정 3단계</td><td>4단계 + Auth {overall_auth} + Clout {overall_clout}</td><td style="color:var(--primary);font-weight:700;">깊이 x3</td></tr>
  <tr><td style="font-weight:700;">데이터 분류</td><td>채널별 건수만</td><td>A~G 7단계 + Trust Score</td><td style="color:var(--primary);font-weight:700;">정확도 x10</td></tr>
  <tr><td style="font-weight:700;">협찬 분석</td><td>유/무 이분법</td><td>Gate 3단계 + Auth 스펙트럼 (차이 {auth_diff}점)</td><td style="color:var(--pink);font-weight:700;">유일</td></tr>
  <tr><td style="font-weight:700;">토픽</td><td>워드클라우드</td><td>구조화 비중 + 컨셉 침투도 분석</td><td style="color:var(--primary);font-weight:700;">액셔너블</td></tr>
  <tr><td style="font-weight:700;">심리</td><td>불가능</td><td>Auth/Clout/Freshness 기간별 추적</td><td style="color:var(--pink);font-weight:700;">유일</td></tr>
  <tr><td style="font-weight:700;">후기 품질</td><td>1건=1건</td><td>RQL 5단계 가중 (Q5 {rql_q5}건)</td><td style="color:var(--pink);font-weight:700;">유일</td></tr>
  <tr><td style="font-weight:700;">친환경 침투</td><td>측정 불가</td><td>{eco_pct}% 침투 — 체험형 컨셉 전달 성공</td><td style="color:var(--green);font-weight:700;">핵심 발견</td></tr>
  <tr><td style="font-weight:700;">Auth 지속성</td><td>측정 불가</td><td>25일간 Auth 피로 없음 ({ps_pre_auth}→{ps_dur_auth}→{ps_post_auth})</td><td style="color:var(--green);font-weight:700;">핵심 발견</td></tr>
</table>

<!-- 11. BOTTOM LINE -->
<h2>BOTTOM LINE</h2>
<div style="padding:24px;background:var(--primary-pale);border-radius:16px;margin:16px 0;">
  <div style="text-align:center;margin-bottom:20px;">
    <div style="font-size:13px;color:var(--body);margin-bottom:8px;">기존 도구</div>
    <div style="font-size:17px;font-weight:800;color:var(--body);">"{N}건 멘션, 긍정 {sent_pos}%"</div>
    <div style="font-size:20px;margin:8px 0;">↓</div>
    <div style="font-size:13px;color:var(--primary);margin-bottom:8px;">RXR 분석</div>
    <div style="font-size:17px;font-weight:800;color:var(--primary);">"유효 {gs3["n"]}건, 진심 긍정 {gs3["pos_pct"]}%, 친환경 침투 {eco_pct}%"</div>
  </div>

  <h3 style="margin-top:20px;">왜 이런 결과가 나왔는가?</h3>
  <div class="grid2" style="gap:12px;margin-top:12px;">
    <div class="card" style="border-top:3px solid var(--green);">
      <div style="font-size:20px;font-weight:800;color:var(--green);">친환경 침투도 {eco_pct}%</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">체험형 컨셉 전달 성공. "종이 공간", "리필", "플라스틱 교환 자판기" 등 <strong>눈에 보이고 만지는 체험</strong>이 소비자 언어에 자연스럽게 침투. 컴온스타일의 "슬로우에이징" 0%와 극명한 대조.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--coral);">
      <div style="font-size:20px;font-weight:800;color:var(--coral);">긍정률 -{gate_pos_drop}%p</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">Gate 1({gs1["pos_pct"]}%) → Gate 3({gs3["pos_pct"]}%). 과장 긍정이 존재하지만 컴온스타일(-8.4%p)보다 적어 후기의 진실성이 상대적으로 높음.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--primary);">
      <div style="font-size:20px;font-weight:800;color:var(--primary);">25일 Auth 피로 없음</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">Auth {ps_pre_auth} → {ps_dur_auth} → {ps_post_auth}. 25일 장기 운영에도 진정성이 유지 또는 상승. 친환경 가치가 진정성을 지탱하는 힘으로 작용. 장기 팝업에서 Auth 피로가 없는 것은 이례적.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--orange);">
      <div style="font-size:20px;font-weight:800;color:var(--orange);">제품({product_pct}%) vs 친환경({eco_pct}%)</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">제품/성분이 1위이지만 친환경 침투도 {eco_pct}%는 의미 있는 수준. 친환경+리필 합산({eco_total_pct}%)을 보면 제품과 친환경이 <strong>균형 있게 인식</strong>됨. 다만 제품 관심이 친환경 가치를 압도하지 않도록 다음 설계 시 유의.</div>
    </div>
  </div>

  <h3 style="margin-top:20px;">제언: 다음 팝업에서 무엇을 바꿀 것인가?</h3>
  <div class="grid3" style="gap:12px;margin-top:12px;">
    <div class="card" style="border-left:4px solid var(--green);">
      <div style="font-size:14px;font-weight:800;color:var(--green);margin-bottom:6px;">친환경 체험 → 인증/공유형</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">리필 과정 인증샷, 플라스틱 감축량 개인 카드 등 <strong>"내가 줄인 플라스틱 37g" 인증 시스템</strong>. 체험을 공유 가능한 형태로 만들어 자발적 확산 유도. 현재 친환경 체험이 "했다"에 그치지 않고 "보여줬다"까지 확장.</div>
    </div>
    <div class="card" style="border-left:4px solid var(--primary);">
      <div style="font-size:14px;font-weight:800;color:var(--primary);margin-bottom:6px;">제품 체험 + 친환경 메시지 통합</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">제품 체험과 친환경 메시지를 분리하지 말고 통합. <strong>리필하면서 절감량 실시간 시각화</strong>, 종이 포장재로 제품을 직접 감싸는 체험 등. "좋은 제품"과 "좋은 가치"가 하나의 서사로 연결될 때 Q5 서사형 후기가 자연 발생.</div>
    </div>
    <div class="card" style="border-left:4px solid var(--orange);">
      <div style="font-size:14px;font-weight:800;color:var(--orange);margin-bottom:6px;">서사형 후기(Q5) 유도</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">현재 Q5 서사형 {rql_q5}건({round(rql_q5/N*100,1)}%). 친환경 경험은 깊은 서사를 만들 수 있는 소재. <strong>"나의 친환경 여정" 스토리 템플릿 + 리뷰 이벤트</strong>로 Q5 비율 2배 목표. 진성 후기 = 가장 강력한 브랜드 자산.</div>
    </div>
  </div>
</div>

<!-- 12. 부록: Gate 3 유효 Raw Data 테이블 -->
<h2>부록: Sincerity Gate 3 통과 — 유효 Raw Data ({gs3["n"]}건)</h2>
<div style="overflow-x:auto;">
<table style="font-size:10px;">
  <tr><th>#</th><th>날짜</th><th>감성</th><th>Auth</th><th>Clout</th><th>Fresh</th><th>RQL</th><th>토픽</th><th>기간</th><th>제목</th><th>블로거</th></tr>
  {gate3_table()}
</table>
</div>

<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:16px 0;">
  <div class="card" style="text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--body);margin-bottom:4px;">감성 분포</div>
    <div style="font-size:11px;">긍정 <strong style="color:var(--green);">{g3_pos}</strong> · 중립 {g3_neu} · 혼합 {g3_mix} · 부정 <strong style="color:var(--coral);">{g3_neg}</strong></div>
  </div>
  <div class="card" style="text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--body);margin-bottom:4px;">평균 Psyche</div>
    <div style="font-size:11px;">Auth <strong>{gs3["auth"]}</strong> · Clout {gs3["clout"]} · Fresh {gs3["fresh"]}</div>
  </div>
  <div class="card" style="text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--body);margin-bottom:4px;">기간 분포</div>
    <div style="font-size:11px;">사전 {g3_pre} · 팝업 {g3_dur} · 후 {g3_post}</div>
  </div>
  <div class="card" style="text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--body);margin-bottom:4px;">RQL 분포</div>
    <div style="font-size:11px;">Q5 {g3_rql5} · Q4 {g3_rql4} · Q3 {g3_rql3} · Q2 {g3_rql2}</div>
  </div>
</div>

<!-- Footer -->
<div class="footer">
  RXR SNS Raw Data Analysis &middot; LG생활건강 비욘드 팝업스토어 &middot; Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} &middot; Project RENT &middot; R-lab
</div>

{PDF_PANEL}
</body></html>'''

# ============================================================
# 2. 외부용 HTML
# ============================================================
external_html = f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>비욘드 팝업스토어 — RXR SNS 분석</title>
<style>{CSS}</style><style id="pageOrientStyle"></style></head><body>

<!-- HEADER -->
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
  <span style="background:var(--grad);color:#fff;padding:4px 14px;border-radius:6px;font-family:'Poppins';font-size:11px;font-weight:600;letter-spacing:1px;">RXR SNS ANALYSIS</span>
</div>
<h1>LG생활건강 비욘드(BEYOND) — "Less plastic, Paper is enough" 팝업스토어</h1>
<div class="sub">기존 분석 vs RXR 다층 분석 + 진심 필터 | 네이버 블로그 {N}건 | Project RENT &middot; R-lab</div>

<!-- 리서치 개요 -->
<div style="padding:20px;background:var(--light);border-radius:14px;margin-bottom:24px;">
  <div class="grid2">
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">ABOUT THIS RESEARCH</div>
      <h3 style="margin-top:0;">분석 대상</h3>
      <table style="font-size:12px;"><tr><td style="color:var(--body);width:70px;padding:4px 0;">팝업명</td><td style="padding:4px 0;font-weight:700;">비욘드 팝업스토어 "Less plastic, Paper is enough"</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">브랜드</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">LG생활건강 / 비욘드(BEYOND)</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2023.05.25 ~ 06.18, <strong>25일간</strong></td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">장소</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">서울 성수동 서울숲길</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">컨셉</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">친환경 / 지속가능성 / 클린뷰티</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">분석 기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2023.05.11 ~ 07.02</td></tr></table>
    </div>
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">RESEARCH PERSPECTIVE</div>
      <h3 style="margin-top:0;">리서치 관점</h3>
      <div style="font-size:12px;color:var(--body);line-height:1.7;">
        <div style="padding:4px 0;"><strong style="color:var(--primary);">핵심 질문:</strong> "친환경/지속가능성" 컨셉이 소비자에게 실제로 전달되었는가?</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">데이터:</strong> 네이버 블로그 {N}건</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">분석:</strong> 콘텐츠 + 심리 다층 분석 + 진심 필터 3단계</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">특이사항:</strong> 25일 장기 운영 → 진정성 피로 여부 추적</div>
      </div>
    </div>
  </div>
  <div style="margin-top:12px;padding:10px 14px;background:var(--primary-pale);border-radius:8px;font-size:12px;color:var(--body);">
    <strong>읽는 법:</strong> 각 섹션은 <strong>BEFORE(기존 도구)</strong>와 <strong>AFTER(RXR)</strong>를 나란히 비교합니다.
  </div>
</div>

<!-- EXECUTIVE SUMMARY -->
<div style="padding:28px;background:linear-gradient(135deg,#f8f7ff,#eef2ff);border-radius:16px;margin-bottom:28px;border:1px solid var(--primary-pale);">
  <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--primary);margin-bottom:8px;">EXECUTIVE SUMMARY</div>
  <h2 style="margin:0 0 16px;border:none;padding:0;font-size:18px;">이 리포트가 말하는 것</h2>

  <div style="font-size:13px;color:var(--body);line-height:1.9;">
    <p style="margin-bottom:14px;">LG생활건강의 비욘드(BEYOND) 팝업스토어 "Less plastic, Paper is enough"는 25일간 성수동 서울숲길에서 운영되며, 네이버 블로그에서 <strong style="color:var(--primary);">총 {N}건의 멘션</strong>을 만들어냈습니다. 기존 분석 도구로 보면 "긍정 {sent_pos}%, 친환경에 대한 관심이 높은 캠페인"이라는 결론이 나옵니다. 하지만 RXR의 다층 분석으로 들여다보면, 이 팝업이 가진 진짜 의미가 드러납니다.</p>

    <p style="margin-bottom:14px;">{N}건의 포스트 중 진심 필터를 통과한 유효 반응은 <strong style="color:var(--primary);">{gs3["n"]}건</strong>이었습니다. 진심 필터를 적용하자 <strong style="color:var(--coral);">긍정률은 소폭 조정</strong>되었지만, 그 하락폭은 다른 팝업 사례보다 적었습니다. 이는 비욘드 팝업의 후기가 상대적으로 진실에 가까웠음을 의미합니다.</p>

    <p style="margin-bottom:14px;">가장 주목할 발견은 <strong style="color:var(--green);">"친환경/지속가능성" 컨셉의 침투율이 {eco_pct}%</strong>라는 점입니다. 이는 같은 성수동에서 열린 다른 팝업(CJ온스타일 "슬로우에이징" 0%)과 극명하게 대비됩니다. 비욘드는 "종이로 만든 공간", "플라스틱 교환 자판기", "리필 제품 체험" 등 <strong style="color:var(--primary);">눈에 보이고 손으로 만지는 체험</strong>으로 컨셉을 구현했기 때문입니다. 추상적 슬로건이 아닌 구체적 실천이 소비자 언어에 침투하는 열쇠임을 증명한 사례입니다.</p>

    <p style="margin-bottom:14px;">또 하나의 주목할 패턴은 <strong style="color:var(--green);">25일 장기 운영에도 진정성 피로가 없었다</strong>는 점입니다. 보통 팝업스토어는 운영 기간이 길어질수록 후기의 진정성이 하락하는 경향이 있습니다. 하지만 비욘드 팝업은 사전 기간부터 팝업 후까지 진정성 지수가 유지 또는 상승했습니다. 이는 "친환경 가치"라는 컨셉이 일회성 화제가 아닌 <strong>지속 가능한 진정성의 원천</strong>으로 작용했음을 보여줍니다.</p>

    <p style="margin-bottom:14px;">그린워싱(greenwashing) 우려도 거의 없었습니다. 부정 반응 {sent_neg}%는 낮은 수준이며, 소비자들은 비욘드의 노력을 진정성 있는 시도로 받아들였습니다. 종이 공간, 실제 리필 판매, PET 대비 37g 감축이라는 구체적 수치 등이 "말뿐이 아닌 실천"으로 인식된 결과입니다.</p>

    <p style="margin-bottom:20px;">다만, 제품/성분({product_pct}%)이 여전히 가장 큰 토픽이었습니다. 친환경 메시지가 제품 경험에 완전히 통합되지 않고 별도의 체험으로 존재했을 가능성이 있습니다. <strong style="color:var(--primary);">"좋은 제품"과 "좋은 가치"가 하나의 서사로 연결될 때, 비욘드는 클린뷰티 시장에서 진정한 차별화를 이룰 수 있습니다.</strong></p>

    <div style="padding:16px;background:#fff;border-radius:12px;border-left:4px solid var(--primary);">
      <div style="font-size:13px;font-weight:700;color:var(--primary);margin-bottom:10px;">다음 팝업을 위한 제언</div>
      <div style="font-size:12px;color:var(--body);line-height:1.8;">
        <strong>1. 친환경 체험을 "인증/공유 가능한" 형태로 확장.</strong> 리필 과정 인증샷, "내가 줄인 플라스틱" 개인 카드 등 소비자가 자발적으로 공유하고 싶은 장치를 더해야 합니다. 현재 체험이 "했다"에 그치고 있어, "보여줬다"까지 확장하면 서사형 후기 비율을 크게 높일 수 있습니다.<br><br>
        <strong>2. 제품 체험과 친환경 메시지를 통합.</strong> 리필하면서 절감량을 실시간으로 시각화하거나, 종이 포장재로 제품을 직접 감싸는 체험 등. 제품과 가치가 분리되지 않는 서사를 설계해야 합니다.<br><br>
        <strong>3. 25일 장기의 강점 + 서사형 후기 유도.</strong> 이번 분석에서 확인된 장기 운영의 진정성 유지라는 강점을 살리되, "나의 친환경 여정" 스토리 템플릿으로 깊이 있는 후기를 유도하면 가장 강력한 브랜드 자산이 됩니다.
      </div>
    </div>
  </div>
</div>

<!-- 0. 데이터 수집 개요 -->
<h2>0. 데이터 수집 개요</h2>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);padding:14px;"><div style="font-size:32px;font-weight:800;color:var(--primary);">{N}</div><div style="font-size:11px;color:var(--body);font-weight:600;">네이버 블로그 총 멘션</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--green);padding:14px;"><div style="font-size:32px;font-weight:800;color:var(--green);">25일</div><div style="font-size:11px;color:var(--body);font-weight:600;">팝업 운영 기간</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--pink);padding:14px;"><div style="font-size:32px;font-weight:800;color:var(--pink);">{gs3["n"]}</div><div style="font-size:11px;color:var(--body);font-weight:600;">3차 진심 필터 유효</div></div>
</div>

<h3>날짜별 버즈 분포</h3>
{date_bars()}

<!-- 1. 감성 분석 -->
<h2>1. 감성 분석 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">3단계 감성 분류</div>
    <div style="font-size:13px;color:var(--body);line-height:1.7;">기존 도구는 긍정/중립/부정 3단계로 분류합니다. "혼합"(긍정+부정 공존)은 구분하지 못합니다.</div>
    <div style="margin-top:12px;padding:12px;background:#e2e8f0;border-radius:8px;text-align:center;font-size:20px;font-weight:800;">긍정 {sent_pos}%</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">4단계 + 진정성 + 추천 확신도</div>
    {gauge("긍정", sent_pos, 100, "var(--green)")}
    {gauge("중립", sent_neu, 100, "#94a3b8")}
    {gauge("혼합", sent_mix, 100, "var(--blue)")}
    {gauge("부정", sent_neg, 100, "var(--coral)")}
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      <strong style="color:var(--primary);">해석:</strong> 3차 진심 필터 적용 시 진심 긍정은 <strong style="color:var(--coral);">{gs3["pos_pct"]}%</strong>로 조정됩니다. 그러나 하락폭이 다른 사례보다 적어, 후기의 진실성이 상대적으로 높습니다.
    </div>
  </div>
</div>

<!-- 2. 데이터 분류 -->
<h2>2. 데이터 분류 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">채널별 건수만</div>
    <div style="font-size:13px;color:var(--body);">모든 1건이 동일한 가치로 취급됩니다.</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">콘텐츠 유형 분류</div>
    <div style="font-size:12px;line-height:1.8;">
      진성후기 <strong>{cls_A}</strong>건 · 일반 <strong>{cls_B}</strong>건 · 협찬 <strong>{cls_C}</strong>건 · 나열형 <strong>{cls_D}</strong>건 · 기타 <strong>{cls_E + cls_F + cls_G}</strong>건
    </div>
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      <strong style="color:var(--primary);">해석:</strong> 협찬 {cls_C}건은 제외하지 않고 진심 스펙트럼으로 분석합니다. 같은 협찬 안에서도 진정성의 농도가 다르기 때문입니다.
    </div>
  </div>
</div>

<!-- 3. 토픽 분석 -->
<h2>3. 토픽 분석 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">워드클라우드</div>
    <div style="font-size:13px;color:var(--body);">빈출 단어를 크기로 표현. 구조화된 비중이나 시사점은 알 수 없습니다.</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">구조화 토픽 비중</div>
    {topic_bars()}
    <div style="margin-top:10px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      <strong style="color:var(--primary);">해석:</strong> 제품/성분({product_pct}%)이 1위이지만, <strong style="color:var(--green);">친환경/지속가능성({eco_pct}%) + 리필/용기({refill_pct}%) = {eco_total_pct}%</strong>. 체험형 친환경 컨셉이 소비자 언어에 의미 있게 침투했습니다. "종이 공간", "플라스틱 교환" 등 구체적 체험이 추상적 슬로건보다 훨씬 효과적이었습니다.
    </div>
  </div>
</div>

<!-- 4. 친환경 침투도 (외부용) -->
<h2>4. 친환경 컨셉 침투도</h2>
<div style="padding:20px;background:linear-gradient(135deg,#ecfdf5,#f0fdf4);border-radius:14px;border:2px solid var(--green);margin:16px 0;">
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">
    <div style="text-align:center;"><div style="font-size:28px;font-weight:800;color:var(--green);">{eco_pct}%</div><div style="font-size:10px;color:var(--body);">친환경/지속가능성</div></div>
    <div style="text-align:center;"><div style="font-size:28px;font-weight:800;color:#00b4d8;">{refill_pct}%</div><div style="font-size:10px;color:var(--body);">리필/용기</div></div>
    <div style="text-align:center;"><div style="font-size:28px;font-weight:800;color:var(--primary);">{eco_total_pct}%</div><div style="font-size:10px;color:var(--body);">친환경 합계</div></div>
  </div>
  <div class="insight" style="background:#fff;">
    <strong style="color:var(--green);">그린워싱이 아닌 진정성:</strong> 소비자들은 비욘드의 친환경 노력을 진정성 있는 시도로 인식했습니다. 종이로 만든 공간, 실제 리필 제품, 플라스틱 교환 자판기 등 <strong>구체적 실천</strong>이 "말뿐인 마케팅"이 아님을 증명했습니다. 부정 반응 {sent_neg}%는 매우 낮은 수준입니다.
  </div>
</div>

<!-- 5. 심리 분석 -->
<h2>5. 심리 분석</h2>
<div class="grid3">
  <div class="card" style="border-top:3px solid var(--orange);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--orange);margin-bottom:8px;">사전</div>
    <div style="font-size:20px;font-weight:800;">진정성 {auth_pre_level}</div>
    <div style="font-size:11px;color:var(--body);margin-top:4px;">추천 확신도 {clout_pre_level}</div>
  </div>
  <div class="card" style="border-top:3px solid var(--primary);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--primary);margin-bottom:8px;">팝업기간</div>
    <div style="font-size:20px;font-weight:800;">진정성 {auth_dur_level}</div>
    <div style="font-size:11px;color:var(--body);margin-top:4px;">추천 확신도 {clout_dur_level}</div>
  </div>
  <div class="card" style="border-top:3px solid var(--green);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--green);margin-bottom:8px;">팝업후</div>
    <div style="font-size:20px;font-weight:800;">진정성 {auth_post_level}</div>
    <div style="font-size:11px;color:var(--body);margin-top:4px;">추천 확신도 {clout_post_level}</div>
  </div>
</div>
<div class="insight" style="margin:12px 0;">
  <strong style="color:var(--green);">25일 장기 운영에도 진정성 피로가 없습니다.</strong> 사전부터 팝업 후까지 진정성 수준이 유지 또는 상승했습니다. 친환경 가치가 "시간이 지나도 변하지 않는" 진정성의 원천으로 작용한 결과입니다. 다른 팝업에서 흔히 보이는 장기 운영의 피로 현상이 나타나지 않은 것은 주목할 만합니다.
</div>

<!-- 6. 협찬 분석 -->
<h2>6. 협찬 분석 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">유/무 이분법</div>
    <div style="font-size:13px;color:var(--body);">협찬 여부만 구분. 협찬 안에서의 진심 차이는 알 수 없습니다.</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">진정성 스펙트럼 분석</div>
    <div class="grid2" style="gap:8px;">
      <div style="text-align:center;padding:10px;background:#fffbeb;border-radius:8px;">
        <div style="font-size:20px;font-weight:800;color:var(--orange);">{len(spon)}건</div>
        <div style="font-size:10px;">협찬 | 진정성 {auth_level(spon_auth)}</div>
      </div>
      <div style="text-align:center;padding:10px;background:#f0fdf4;border-radius:8px;">
        <div style="font-size:20px;font-weight:800;color:var(--green);">{len(org)}건</div>
        <div style="font-size:10px;">자발적 | 진정성 {auth_level(org_auth)}</div>
      </div>
    </div>
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      자발적 후기가 {round(len(org)/N*100,1)}%로 압도적 다수입니다. 친환경 팝업의 특성상 "스스로 공유하고 싶은" 동기가 강했으며, 자발적 후기의 진정성이 현저히 높습니다.
    </div>
  </div>
</div>

<!-- 7. 후기 품질 -->
<h2>7. 후기 품질 Before → After</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title">1건 = 1건</div>
    <div style="font-size:13px;color:var(--body);">500자 서사형 후기와 20자 감상형 후기가 동일한 1건으로 처리됩니다.</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">후기 깊이 5등급</div>
    <div style="font-size:12px;line-height:1.8;">
      서사형 <strong>{rql_q5}</strong>건 · 분석형 <strong>{rql_q4}</strong>건 · 경험형 <strong>{rql_q3}</strong>건 · 감상형 <strong>{rql_q2}</strong>건 · 간단형 <strong>{rql_q1}</strong>건
    </div>
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      고품질 후기(서사형+분석형) {rql_high}건({rql_high_pct}%). 친환경 체험이 상세한 서사를 이끌어내고 있으며, 인증/공유 장치를 더하면 이 비율을 크게 높일 수 있습니다.
    </div>
  </div>
</div>

<!-- 8. 진심 필터 -->
<h2>8. 진심 필터 — 3단계</h2>
<div style="margin:16px 0;">
  <div style="display:flex;align-items:center;gap:4px;margin-bottom:12px;">
    <div style="flex:{gs1["n"]};height:48px;background:var(--primary-pale);border-radius:10px 0 0 10px;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:var(--primary);">1차: {gs1["n"]}건</div>
    <div style="flex:{gs2["n"]};height:48px;background:#c7d2fe;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:var(--primary);">2차: {gs2["n"]}건</div>
    <div style="flex:{gs3["n"]};height:48px;background:var(--primary);border-radius:0 10px 10px 0;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;">3차: {gs3["n"]}건</div>
  </div>
  <table>
    <tr><th></th><th>건수</th><th>긍정률</th><th>필터</th></tr>
    <tr><td style="font-weight:700;">1차 필터</td><td>{gs1["n"]}</td><td>{gs1["pos_pct"]}%</td><td>노이즈 제거</td></tr>
    <tr><td style="font-weight:700;">2차 필터</td><td>{gs2["n"]}</td><td>{gs2["pos_pct"]}%</td><td>+ 협찬/공유/보도 제거</td></tr>
    <tr style="background:var(--primary-pale);"><td style="font-weight:700;color:var(--primary);">3차 필터</td><td style="font-weight:800;">{gs3["n"]}</td><td style="font-weight:800;color:var(--coral);">{gs3["pos_pct"]}%</td><td>+ 진정성 기준 이상</td></tr>
  </table>
</div>
<div class="insight">
  <strong>1차 → 3차: 긍정률 {gs1["pos_pct"]}% → {gs3["pos_pct"]}% ({round(gs3["pos_pct"]-gs1["pos_pct"],1)}%p)</strong><br>
  하락폭이 다른 팝업 사례(-8.4%p)보다 적어, 비욘드 팝업의 후기가 상대적으로 진실에 가까웠음을 보여줍니다. 3차 필터를 통과한 {gs3["n"]}건이 "진짜 반응"입니다.
</div>

<!-- 9. 핵심 수치 요약 -->
<h2>9. 핵심 수치 요약</h2>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);"><div style="font-size:28px;font-weight:800;color:var(--primary);">{N}</div><div style="font-size:10px;color:var(--body);">총 멘션</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--pink);"><div style="font-size:28px;font-weight:800;color:var(--pink);">{gs3["n"]}</div><div style="font-size:10px;color:var(--body);">3차 필터 유효</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--coral);"><div style="font-size:28px;font-weight:800;color:var(--coral);">{gs3["pos_pct"]}%</div><div style="font-size:10px;color:var(--body);">진심 긍정률</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--green);"><div style="font-size:28px;font-weight:800;color:var(--green);">{eco_pct}%</div><div style="font-size:10px;color:var(--body);">친환경 침투율</div></div>
</div>

<!-- 종합 비교표 -->
<h2>종합 Before → After 비교표</h2>
<table>
  <tr><th>비교 영역</th><th>BEFORE (기존)</th><th>AFTER (RXR)</th></tr>
  <tr><td style="font-weight:700;">버즈 규모</td><td>총 {N}건</td><td>3차 필터 유효 <strong>{gs3["n"]}건</strong></td></tr>
  <tr><td style="font-weight:700;">감성</td><td>긍정/중립/부정 3단계</td><td>4단계 + 진정성 + 추천 확신도</td></tr>
  <tr><td style="font-weight:700;">협찬 분석</td><td>유/무 이분법</td><td>진심 필터 3단계 + 진정성 스펙트럼</td></tr>
  <tr><td style="font-weight:700;">토픽</td><td>워드클라우드</td><td>구조화 비중 + 컨셉 침투도</td></tr>
  <tr><td style="font-weight:700;">심리</td><td>불가능</td><td>진정성/추천 확신도/신선함 지수 추적</td></tr>
  <tr><td style="font-weight:700;">후기 품질</td><td>1건=1건</td><td>후기 깊이 5등급 (분석 가중치 적용)</td></tr>
  <tr><td style="font-weight:700;">친환경 침투</td><td>측정 불가</td><td>{eco_pct}% — 체험형 컨셉 전달 성공</td></tr>
  <tr><td style="font-weight:700;">진정성 지속</td><td>측정 불가</td><td>25일 장기에도 피로 없음</td></tr>
</table>

<!-- BOTTOM LINE -->
<h2>BOTTOM LINE</h2>
<div style="padding:24px;background:var(--primary-pale);border-radius:16px;margin:16px 0;">
  <div style="text-align:center;margin-bottom:20px;">
    <div style="font-size:13px;color:var(--body);margin-bottom:8px;">기존 도구</div>
    <div style="font-size:17px;font-weight:800;color:var(--body);">"{N}건 멘션, 긍정 {sent_pos}%"</div>
    <div style="font-size:20px;margin:8px 0;">↓</div>
    <div style="font-size:13px;color:var(--primary);margin-bottom:8px;">RXR 분석</div>
    <div style="font-size:17px;font-weight:800;color:var(--primary);">"유효 {gs3["n"]}건, 진심 긍정 {gs3["pos_pct"]}%, 친환경 침투 {eco_pct}%"</div>
  </div>

  <h3 style="margin-top:20px;">왜 이런 결과가 나왔는가?</h3>
  <div class="grid2" style="gap:12px;margin-top:12px;">
    <div class="card" style="border-top:3px solid var(--green);">
      <div style="font-size:18px;font-weight:800;color:var(--green);">친환경 컨셉 침투 성공</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">체험형 구현(종이 공간, 리필, 플라스틱 교환)이 소비자 언어에 침투. 추상적 슬로건 대비 압도적 효과.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--coral);">
      <div style="font-size:18px;font-weight:800;color:var(--coral);">과장 긍정 상대적 적음</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">진심 필터 후 긍정률 하락폭이 다른 사례보다 적어, 후기의 진실성이 높습니다.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--primary);">
      <div style="font-size:18px;font-weight:800;color:var(--primary);">25일 진정성 유지</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">친환경 가치가 시간이 지나도 변하지 않는 진정성의 원천으로 작용했습니다.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--orange);">
      <div style="font-size:18px;font-weight:800;color:var(--orange);">제품 vs 친환경 균형</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">제품 관심이 1위이지만 친환경 침투도도 의미 있는 수준. 통합 시 더 강력한 서사 가능.</div>
    </div>
  </div>

  <h3 style="margin-top:20px;">제언: 다음 팝업에서 무엇을 바꿀 것인가?</h3>
  <div class="grid3" style="gap:12px;margin-top:12px;">
    <div class="card" style="border-left:4px solid var(--green);">
      <div style="font-size:14px;font-weight:800;color:var(--green);margin-bottom:6px;">인증/공유형 체험</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">리필 인증샷, 플라스틱 감축량 개인 카드. "했다"에서 "보여줬다"로 확장.</div>
    </div>
    <div class="card" style="border-left:4px solid var(--primary);">
      <div style="font-size:14px;font-weight:800;color:var(--primary);margin-bottom:6px;">제품 + 가치 통합</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">리필하면서 절감량 시각화. "좋은 제품"과 "좋은 가치"를 하나의 서사로.</div>
    </div>
    <div class="card" style="border-left:4px solid var(--orange);">
      <div style="font-size:14px;font-weight:800;color:var(--orange);margin-bottom:6px;">서사형 후기 유도</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">"나의 친환경 여정" 스토리 템플릿으로 깊이 있는 후기를 이끌어내야 합니다.</div>
    </div>
  </div>
</div>

<!-- 부록: 하이라이트 20건 -->
<h2>부록: 하이라이트 후기 20건</h2>
<div class="grid2">
  <div>
    <h3 style="color:var(--green);">진정성 높은 후기 TOP 10</h3>
    {highlight_cards(high_auth_posts, "high")}
  </div>
  <div>
    <h3 style="color:var(--coral);">진정성 낮은 후기 10건</h3>
    {highlight_cards(low_auth_all, "low")}
  </div>
</div>

<!-- Footer -->
<div class="footer">
  RXR SNS Analysis &middot; LG생활건강 비욘드 팝업스토어 &middot; {datetime.now().strftime("%Y-%m-%d")} &middot; Project RENT &middot; R-lab
</div>

{PDF_PANEL}
</body></html>'''

# ============================================================
# 3. 잠금 버전 생성
# ============================================================
PASSWORD = "RXR-projectrent"
pw_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()

b64 = base64.b64encode(external_html.encode("utf-8")).decode("ascii")
CHUNK = 50000
chunks = [b64[i:i+CHUNK] for i in range(0, len(b64), CHUNK)]
chunks_js = ",".join(f'"{c}"' for c in chunks)

locked_html = f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>비욘드 팝업스토어 — RXR SNS 분석 (Protected)</title>
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable.css');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Pretendard Variable',system-ui,sans-serif;background:#f8f7ff;min-height:100vh;display:flex;align-items:center;justify-content:center;}}
.lock-screen{{text-align:center;padding:60px 40px;max-width:420px;width:100%;}}
.lock-icon{{width:80px;height:80px;background:linear-gradient(135deg,#5353FF,#8A8AFF);border-radius:20px;display:flex;align-items:center;justify-content:center;margin:0 auto 24px;box-shadow:0 8px 32px rgba(102,102,255,0.3);}}
.lock-icon svg{{width:36px;height:36px;fill:none;stroke:#fff;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;}}
.lock-title{{font-size:22px;font-weight:800;color:#262626;margin-bottom:8px;}}
.lock-sub{{font-size:13px;color:#64748b;margin-bottom:32px;line-height:1.6;}}
.lock-input{{width:100%;padding:14px 18px;border:2px solid #e2e8f0;border-radius:12px;font-size:15px;font-family:'Pretendard Variable',sans-serif;outline:none;transition:border-color 0.2s;text-align:center;letter-spacing:2px;}}
.lock-input:focus{{border-color:#6666FF;}}
.lock-input.error{{border-color:#FF5050;animation:shake 0.4s;}}
@keyframes shake{{0%,100%{{transform:translateX(0)}}25%{{transform:translateX(-8px)}}75%{{transform:translateX(8px)}}}}
.lock-btn{{width:100%;padding:14px;background:linear-gradient(135deg,#5353FF,#8A8AFF);color:#fff;border:none;border-radius:12px;font-size:15px;font-weight:700;cursor:pointer;margin-top:14px;font-family:'Pretendard Variable',sans-serif;box-shadow:0 4px 16px rgba(102,102,255,0.3);transition:transform 0.1s;}}
.lock-btn:active{{transform:scale(0.98);}}
.lock-error{{color:#FF5050;font-size:12px;margin-top:10px;min-height:18px;}}
.lock-footer{{margin-top:40px;font-size:11px;color:#94a3b8;}}
</style></head><body>

<div class="lock-screen" id="lockScreen">
  <div class="lock-icon">
    <svg viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/><circle cx="12" cy="16" r="1"/></svg>
  </div>
  <div class="lock-title">RXR SNS Analysis</div>
  <div class="lock-sub">LG생활건강 비욘드 — "Less plastic, Paper is enough"<br>이 리포트는 비밀번호로 보호되어 있습니다.</div>
  <input type="password" class="lock-input" id="pwInput" placeholder="비밀번호 입력" autofocus>
  <button class="lock-btn" id="unlockBtn" onclick="unlock()">열기</button>
  <div class="lock-error" id="errorMsg"></div>
  <div class="lock-footer">Project RENT &middot; R-lab &middot; 2025</div>
</div>

<script>
var EC=[{chunks_js}];
var PH="{pw_hash}";

async function sha256(msg){{
  var enc=new TextEncoder().encode(msg);
  var buf=await crypto.subtle.digest('SHA-256',enc);
  return Array.from(new Uint8Array(buf)).map(b=>b.toString(16).padStart(2,'0')).join('');
}}

async function unlock(){{
  var pw=document.getElementById('pwInput').value;
  var h=await sha256(pw);
  if(h===PH){{
    var b64=EC.join('');
    var html=decodeURIComponent(escape(atob(b64)));
    document.open();
    document.write(html);
    document.close();
  }}else{{
    document.getElementById('pwInput').classList.add('error');
    document.getElementById('errorMsg').textContent='비밀번호가 올바르지 않습니다.';
    setTimeout(function(){{document.getElementById('pwInput').classList.remove('error');}},400);
  }}
}}

document.getElementById('pwInput').addEventListener('keyup',function(e){{
  if(e.key==='Enter')unlock();
}});
</script>
</body></html>'''

# ============================================================
# 파일 저장
# ============================================================
internal_path = os.path.join(BASE, "beyond-popup-rxr-sns-report.html")
external_path = os.path.join(BASE, "beyond-popup-rxr-sns-report-external.html")
locked_path = os.path.join(BASE, "beyond-popup-rxr-sns-report-locked.html")

with open(internal_path, "w", encoding="utf-8") as f:
    f.write(internal_html)
print(f"내부용 생성: {internal_path} ({os.path.getsize(internal_path):,} bytes)")

with open(external_path, "w", encoding="utf-8") as f:
    f.write(external_html)
print(f"외부용 생성: {external_path} ({os.path.getsize(external_path):,} bytes)")

with open(locked_path, "w", encoding="utf-8") as f:
    f.write(locked_html)
print(f"잠금 버전 생성: {locked_path} ({os.path.getsize(locked_path):,} bytes)")

print(f"\n총 {N}건 데이터 | Gate3 유효 {gs3['n']}건 | 친환경 침투도 {eco_pct}%")
print(f"비밀번호: {PASSWORD}")
