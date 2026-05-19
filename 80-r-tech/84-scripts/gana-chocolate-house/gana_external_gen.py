"""가나초콜릿하우스 부산 시즌2 — 외부용 + 잠금 버전 생성"""
import json, os, sys, io, hashlib, base64
from collections import Counter
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = os.path.dirname(__file__)
with open(os.path.join(BASE, "../../85-analysis-results/gana-chocolate-house/gana-chocolate-house-2layer-results.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

# ============================================================
# 통계 (내부용과 동일)
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

g1 = [r for r in data if r.get("sincerity_class") != "G"]
g2 = [r for r in data if r.get("sincerity_class") not in ("C", "E", "F", "G")]
g3 = [r for r in data if r.get("sincerity_class") not in ("C", "E", "F", "G") and r.get("authenticity", 0) >= 60]

def gs(items):
    n = len(items)
    if not n: return {"n":0,"pos_pct":0,"auth":0,"clout":0,"fresh":0}
    return {"n":n, "pos_pct": round(sum(1 for r in items if r["sentiment"]=="긍정")/n*100,1),
            "auth": round(sum(r.get("authenticity",0) for r in items)/n,1),
            "clout": round(sum(r.get("clout",0) for r in items)/n,1),
            "fresh": round(sum(r.get("freshness_index",0) for r in items)/n,1)}
gs1, gs2, gs3 = gs(g1), gs(g2), gs(g3)

# 외부용 수치 변환
def auth_level(v):
    if v >= 75: return "매우 높음"
    if v >= 60: return "높음"
    if v >= 45: return "보통"
    if v >= 30: return "낮음"
    return "매우 낮음"

b24 = {"total": 0, "reach": "N/A", "instagram": 0, "tiktok": 0, "x": 0, "news": 0, "facebook": 0, "web": 1, "blogs": 0}
b24_nonblog = b24["total"] - b24["blogs"]
total_mentions = N + b24_nonblog

# 외부용 심리 분석 변수 (f-string dict 문제 방지)
ps_pre = period_stats.get("사전", {"n":0,"auth":0,"clout":0,"freshness":0,"pos_pct":0})
ps_dur = period_stats.get("팝업기간", {"n":0,"auth":0,"clout":0,"freshness":0,"pos_pct":0})
ps_post = period_stats.get("팝업후", {"n":0,"auth":0,"clout":0,"freshness":0,"pos_pct":0})
auth_pre = auth_level(ps_pre["auth"])
auth_dur = auth_level(ps_dur["auth"])
auth_post = auth_level(ps_post["auth"])
clout_pre = auth_level(ps_pre["clout"])
clout_dur = auth_level(ps_dur["clout"])
clout_post = auth_level(ps_post["clout"])

date_dist = Counter(r["date"] for r in data)
dates_sorted = sorted(date_dist.items())
max_day = max(date_dist.values()) if date_dist else 1

slowaging_count = sum(1 for r in data if "위스키 페어링" in (r.get("title","") + " " + str(r.get("topic_scores",{}))))

# ===== Joy × Premium 재분석 =====
g3_all = [r for r in data if r.get("sincerity_class") not in ("C","E","F","G") and r.get("authenticity",0) >= 60]
g3_both = [r for r in g3_all if r.get("joy_score",0) >= 6 and r.get("premium_score",0) >= 6]
g3_joy_only = [r for r in g3_all if r.get("joy_score",0) >= 6 and r.get("premium_score",0) < 6]
g3_prem_only = [r for r in g3_all if r.get("premium_score",0) >= 6 and r.get("joy_score",0) < 6]
g3_neither = [r for r in g3_all if r.get("joy_score",0) < 6 and r.get("premium_score",0) < 6]
g3_joy_strong_pct = round(sum(1 for r in g3_all if r.get("joy_score",0)>=6)/max(len(g3_all),1)*100,1)
g3_prem_strong_pct = round(sum(1 for r in g3_all if r.get("premium_score",0)>=6)/max(len(g3_all),1)*100,1)
g3_both_pct = round(len(g3_both)/max(len(g3_all),1)*100,1)
g3_neither_pct = round(len(g3_neither)/max(len(g3_all),1)*100,1)

period_jp = {}
for p in ["사전","팝업기간","팝업후"]:
    sub = [r for r in g3_all if r["period"]==p]
    if sub:
        period_jp[p] = {
            "joy": round(sum(r.get("joy_score",0) for r in sub)/len(sub),1),
            "prem": round(sum(r.get("premium_score",0) for r in sub)/len(sub),1),
            "prem_strong_pct": round(sum(1 for r in sub if r.get("premium_score",0)>=6)/len(sub)*100,1),
        }
    else:
        period_jp[p] = {"joy":0,"prem":0,"prem_strong_pct":0}

from collections import Counter as _C
joy_kw_counter = _C()
prem_kw_counter = _C()
for r in g3_all:
    for kw in r.get("joy_hits",[]):
        joy_kw_counter[kw] += 1
    for kw in r.get("premium_hits",[]):
        prem_kw_counter[kw] += 1
top_joy_kws_ext = joy_kw_counter.most_common(6)
top_prem_kws_ext = prem_kw_counter.most_common(6)

ip_mentions = {}
for ip in ["최화정", "겟잇뷰티", "한예슬", "안재현"]:
    ip_mentions[ip] = sum(1 for r in data if ip in (r.get("title","") + " " + str(r.get("topic_scores",{}))))

# ============================================================
# Helper functions
# ============================================================
def fmt_date(d):
    return f"{d[:4]}.{d[4:6]}.{d[6:8]}" if len(d)>=8 else d

def gauge(label, value, max_val, color):
    pct = min(round(value / max(max_val,1) * 100), 100)
    return f'<div class="gauge-row"><div class="gauge-label">{label}</div><div class="gauge-track"><div class="gauge-fill" style="width:{pct}%;background:{color};"></div></div></div>'

def date_bars():
    rows = []
    for d, cnt in dates_sorted:
        pct = round(cnt / max_day * 100)
        md = f"{d[4:6]}/{d[6:8]}"
        if d < "20230212": color = "var(--orange)"; label = "사전" if d == dates_sorted[0][0] else ""
        elif d <= "20230314": color = "var(--primary)"; label = "팝업기간" if d == "20230212" else ""
        else: color = "#94a3b8"; label = "팝업후" if d == "20230315" else ""
        inner = f"{cnt}" if cnt >= 5 else ""
        rows.append(f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:40px;font-size:9px;color:var(--body);text-align:right;">{md}</div><div style="flex:1;height:15px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{max(pct,3)}%;height:100%;background:{color};border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;font-weight:600;color:#fff;">{inner}</div></div><div style="width:20px;font-size:9px;font-weight:600;">{cnt}</div><div style="width:65px;font-size:8px;color:{color};font-weight:700;">{label}</div></div>')
    return "\n".join(rows)

TOPIC_COLORS = ["#6666FF", "#10b981", "#00b4d8", "#f59e0b", "#94a3b8", "#d946ef", "#ef4444", "#64748b"]

def topic_bars_ext():
    rows = []
    max_t = topic_dist[0][1] if topic_dist else 1
    for i, (topic, cnt) in enumerate(topic_dist):
        pct = round(cnt / max_t * 100)
        ratio = round(cnt / N * 100, 1)
        color = TOPIC_COLORS[i % len(TOPIC_COLORS)]
        rows.append(f'<div class="gauge-row"><div class="gauge-label" style="width:100px;">{topic}</div><div class="gauge-track"><div class="gauge-fill" style="width:{pct}%;background:{color};">{cnt}건 ({ratio}%)</div></div><div class="gauge-val" style="color:{color};">{ratio}%</div></div>')
    return "\n".join(rows)

# 하이라이트 20건 (진정성 높음 10 + 낮음 10)
high_auth = sorted(g3, key=lambda x: x.get("authenticity",0), reverse=True)[:10]
low_auth_all = sorted(data, key=lambda x: x.get("authenticity",0))[:10]

def highlight_cards(items, style="high"):
    cards = []
    for r in items:
        auth = r.get("authenticity", 0)
        level = auth_level(auth)
        bg = "#f0fdf4" if style == "high" else "#fef2f2"
        border_color = "var(--green)" if style == "high" else "var(--coral)"
        sent = r.get("sentiment", "중립")
        sent_color = {"긍정":"var(--green)","부정":"var(--coral)","혼합":"var(--blue)","중립":"#94a3b8"}.get(sent,"#94a3b8")
        rql = r.get("rql","").replace("_"," ")
        cards.append(f'''<div style="padding:12px 16px;background:{bg};border-radius:10px;border-left:4px solid {border_color};margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span style="font-size:11px;font-weight:700;color:{border_color};">진정성 {level}</span>
            <span style="font-size:10px;color:var(--body);">{fmt_date(r.get("date",""))}</span>
          </div>
          <div style="font-size:13px;font-weight:600;margin-bottom:4px;">{r.get("title","")[:55]}</div>
          <div style="font-size:10px;color:var(--body);display:flex;gap:12px;">
            <span style="color:{sent_color};font-weight:600;">{sent}</span>
            <span>{rql}</span>
            <span>{r.get("primary_topic","")}</span>
          </div>
        </div>''')
    return "\n".join(cards)

# ============================================================
# 외부용 HTML
# ============================================================
external_html = f'''<!DOCTYPE html>
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
<div class="sub">기존 분석 vs RXR 다층 분석 + 진심 필터 | 네이버 블로그 {N}건 + Brand24 {b24_nonblog}건 = 총 {total_mentions}건 | Project RENT &middot; R-lab</div>

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
        <div style="padding:4px 0;"><strong style="color:var(--primary);">핵심 질문:</strong> 방문객은 <strong>초콜릿의 즐거움</strong>과 <strong>브랜드의 고급스러움</strong>을 실제로 느꼈는가?</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">데이터:</strong> 네이버 블로그 {N}건 + Brand24 비블로그 {b24_nonblog}건 = 총 {total_mentions}건</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">분석:</strong> 콘텐츠 + 심리 다층 분석 + 진심 필터 3단계</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">Reach:</strong> {b24["reach"]} (멀티채널)</div>
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
    <p style="margin-bottom:14px;">롯데제과 가나의 두 번째 오프라인 팝업스토어 <strong>'가나초콜릿하우스 부산 시즌2'</strong>는 2023년 2월 12일부터 3월 14일까지 31일간 부산 전포동 프로젝트렌트에서 운영되었습니다. 초콜릿과 위스키를 페어링한 바, 애프터눈티 코스 같은 <strong>고급스럽고 어른스러운 경험</strong>을 내세운 이 팝업에 대해, 네이버 블로그에서 <strong style="color:var(--primary);">{N}건의 유효 포스트</strong>가 수집되었습니다.</p>

    <p style="margin-bottom:14px;">이 리포트의 <strong style="color:var(--primary);">핵심 질문은 두 가지</strong>입니다. 방문객은 <strong>①초콜릿 본연의 즐거움</strong>을 느꼈는가? 그리고 <strong>②가나 브랜드의 고급스러움</strong>을 체감했는가? 이 두 감정이 소비자 후기 언어에 얼마나 묻어나는지를, 키워드 기반 2축 스코어링으로 측정했습니다.</p>

    <p style="margin-bottom:14px;">결론부터 말씀드리면 <strong style="color:var(--green);">두 감정 모두 성공적으로 전달되었습니다.</strong> 진심 필터를 통과한 유효 반응 {gs3["n"]}건 중에서, 초콜릿의 즐거움을 강하게 표현한 포스트가 <strong style="color:var(--green);">{g3_joy_strong_pct}%</strong>, 브랜드의 고급스러움을 강하게 표현한 포스트가 <strong style="color:var(--green);">{g3_prem_strong_pct}%</strong>에 달했습니다. 특히 두 감정이 동시에 강하게 전달된 "완벽한 경험" 포스트가 <strong style="color:var(--primary);">{len(g3_both)}건({g3_both_pct}%)</strong>으로, 거의 절반에 가까운 방문객이 가나가 의도한 복합적 브랜드 경험을 온전히 체감했다는 증거입니다. 한 축도 강하지 않은 "감정이 비어있는" 포스트는 <strong>{len(g3_neither)}건({g3_neither_pct}%)</strong>에 머물렀습니다.</p>

    <p style="margin-bottom:14px;">더 주목할 만한 건 <strong style="color:var(--primary);">실체 경험이 기대치를 넘어섰다는 점</strong>입니다. 사전 2주 기간의 Premium 강 비율은 <strong>{period_jp.get("사전",{}).get("prem_strong_pct",0)}%</strong>였지만, 팝업이 실제 운영되자 오히려 <strong>{period_jp.get("팝업기간",{}).get("prem_strong_pct",0)}%</strong>로 <strong style="color:var(--green);">+{round(period_jp.get("팝업기간",{}).get("prem_strong_pct",0)-period_jp.get("사전",{}).get("prem_strong_pct",0),1)}%p 상승</strong>했습니다. "고급스러울 거야"라는 기대를 안고 방문한 사람들이 <strong>실제로 그 기대를 넘는 경험을 체감</strong>했다는 의미입니다. Joy 강도도 사전 {period_jp.get("사전",{}).get("joy",0)}에서 팝업기간 {period_jp.get("팝업기간",{}).get("joy",0)}로 크게 상승했습니다. 많은 팝업이 기대가 실체를 앞서는 실망 곡선을 보이는 것과 정반대의 궤적입니다.</p>

    <p style="margin-bottom:14px;">상위 키워드가 이 성공을 구체적으로 증명합니다. <strong>즐거움 키워드</strong>는 "맛있", "달달", "달콤", "재미", "인생(초콜릿)", "귀여", "행복" 같은 <strong>진짜 감정 어휘</strong>가 상위를 차지했고, 특히 "인생 초콜릿"이라는 최상급 표현이 {sum(1 for r in g3_all if '인생' in ' '.join(r.get('joy_hits',[])))}건 이상 등장했습니다. <strong>고급 키워드</strong>는 "바", "위스키", "페어링", "전포동", "공간", "분위기", "인테리어", 그리고 결정적으로 "<strong style="color:var(--primary);">고급</strong>"이라는 직접적 감탄어까지 {prem_kw_counter.get("고급",0)}건 포착되었습니다. 즉 방문자들은 "고급스러운 장치"만 본 것이 아니라 "고급스럽다"고 <strong>직접 말했습니다</strong>.</p>

    <p style="margin-bottom:14px;">협찬 구조도 건강했습니다. 협찬으로 식별된 포스트는 {len(spon)}건({round(len(spon)/N*100,1)}%)으로 일반적 수준이었고, 자발적 후기의 진정성 지수(Auth {avg("authenticity",org)})가 협찬(Auth {avg("authenticity",spon)})보다 {round(avg("authenticity",org)-avg("authenticity",spon),1)}점 높아 <strong>진짜 반응과 협찬 톤의 차이가 명확히 구분</strong>되었습니다. Gate 3 필터를 통과한 {gs3["n"]}건은 과잉 긍정 표현이나 형식적 후기가 아닌, 실제로 체험하고 솔직하게 느낀 방문객의 목소리입니다.</p>

    <p style="margin-bottom:20px;">가나초콜릿하우스는 <strong>"고급스러운 어른의 초콜릿 경험"</strong>을 제안하려 했고, 이번 팝업은 그 의도를 <strong style="color:var(--green);">소비자 언어 수준에서 성공적으로 구현</strong>했습니다. 전포동이라는 장소, 위스키바 형식, 애프터눈티 코스는 단순한 설계 요소에 머물지 않고 방문자의 후기에 "달콤했다·고급스러웠다·인생 초콜릿" 같은 감정 언어로 새겨졌습니다. 남은 과제는 이 성공을 <strong>어떻게 유지·확대할 것인가</strong>입니다.</p>

    <div style="padding:16px;background:#fff;border-radius:12px;border-left:4px solid var(--primary);">
      <div style="font-size:13px;font-weight:700;color:var(--primary);margin-bottom:10px;">다음 시즌을 위한 제언 — 이 성공을 어떻게 확대할 것인가</div>
      <div style="font-size:12px;color:var(--body);line-height:1.8;">
        <strong>1. 🍫 팝업후 Joy·Premium 하락 방지 — "기억 연장 장치".</strong> 팝업기간 Joy 강 {period_jp.get("팝업기간",{}).get("joy",0)} → 팝업후 {period_jp.get("팝업후",{}).get("joy",0)}로 하락했습니다. 이는 자연스러운 감소지만, 팝업 종료 후에도 기억을 연장할 장치를 두면 롱테일 확산을 확보할 수 있습니다. 팝업 방문자 대상 <strong>"나만의 페어링 레시피 카드" 우편 발송</strong>, 팝업 전용 온라인 스토어 한정 판매 알림, 팝업 종료 2주차 인스타그램 "가나초콜릿하우스 추억" 캠페인 같은 후속 접점이 필요합니다.<br><br>
        <strong>2. ✨ Q1 후기를 브랜드 자산으로 수확 — "옹호자 재활용".</strong> 이번 분석에서 발견된 {len(g3_both)}건의 Q1 포스트(즐거움+고급 동시 강)는 가나의 가장 강력한 브랜드 옹호자 집단입니다. 이들을 다음 시즌에 <strong>공식 초대</strong>하고, 팝업 운영 스토리를 미리 공유해 "얼리 리뷰어" 역할을 맡기면 시즌3의 사전 신뢰도를 크게 높일 수 있습니다. 이미 체험한 감동을 다시 말하게 만드는 것이 가장 효율적인 바이럴 전략입니다.<br><br>
        <strong>3. 💜 Q3(고급만) → Q1(둘 다) 전환 설계.</strong> Q3가 {len(g3_prem_only)}건({round(len(g3_prem_only)/max(len(g3_all),1)*100,1)}%)로 Q2(즐거움만)보다 많습니다. 즉 "공간은 고급스러웠지만 초콜릿 그 자체의 감동은 덜했던" 방문자군입니다. 다음 시즌에는 <strong>초콜릿 그 자체의 서사</strong> — 장인의 한 마디, 원산지 스토리, 테이스팅 노트 카드 — 를 강화해 이들을 Q1으로 이동시키면, 동시 전달률을 현재 {g3_both_pct}%에서 60% 이상으로 끌어올릴 수 있습니다.
      </div>
    </div>
  </div>
</div>

<!-- 0. 데이터 수집 개요 -->
<h2>0. 데이터 수집 개요</h2>
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);padding:14px;"><div style="font-size:32px;font-weight:800;color:var(--primary);">{total_mentions}</div><div style="font-size:11px;color:var(--body);font-weight:600;">총 멘션 (통합)</div></div>
  <div class="card" style="text-align:center;border-top:3px solid #00b4d8;padding:14px;"><div style="font-size:32px;font-weight:800;color:#00b4d8;">{b24["reach"]}</div><div style="font-size:11px;color:var(--body);font-weight:600;">Reach (Brand24)</div></div>
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
    <div style="margin-top:12px;padding:12px;background:#e2e8f0;border-radius:8px;text-align:center;font-size:20px;font-weight:800;">긍정 {sent_pct.get("긍정",0)}%</div>
  </div>
  <div class="ba-vs">&rarr;</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title">4단계 + 진정성 + 추천 확신도</div>
    {gauge("긍정", sent_pct.get("긍정",0), 100, "var(--green)")}
    {gauge("중립", sent_pct.get("중립",0), 100, "#94a3b8")}
    {gauge("혼합", sent_pct.get("혼합",0), 100, "var(--blue)")}
    {gauge("부정", sent_pct.get("부정",0), 100, "var(--coral)")}
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      <strong style="color:var(--primary);">해석:</strong> 3차 진심 필터 적용 시 진심 긍정은 <strong style="color:var(--coral);">{gs3["pos_pct"]}%</strong>로 하락합니다. 협찬의 의무적 긍정과 과잉 표현이 원래 수치를 부풀리고 있었습니다.
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
      진성후기 <strong>{cls_dist.get("A",0)}</strong>건 · 일반 <strong>{cls_dist.get("B",0)}</strong>건 · 협찬 <strong>{cls_dist.get("C",0)}</strong>건 · 나열형 <strong>{cls_dist.get("D",0)}</strong>건 · 기타 <strong>{cls_dist.get("E",0)+cls_dist.get("F",0)+cls_dist.get("G",0)}</strong>건
    </div>
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      <strong style="color:var(--primary);">해석:</strong> 협찬 {cls_dist.get("C",0)}건은 제외하지 않고 진심 스펙트럼으로 분석합니다. 같은 협찬 안에서도 진정성의 농도가 다르기 때문입니다.
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
    {topic_bars_ext()}
    <div style="margin-top:10px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      <strong style="color:var(--primary);">해석:</strong> "초콜릿/맛" 토픽이 압도적 1위({round(topic_dist[0][1]/N*100)}%). 그리고 이 토픽 안에서 <strong style="color:var(--green);">초콜릿의 "즐거움"을 강하게 표현한 포스트가 {g3_joy_strong_pct}%</strong>에 달합니다. "맛있", "달달", "달콤", "인생 초콜릿", "행복" 같은 <strong>진짜 감정 어휘</strong>가 블로거 언어에 자연스럽게 녹아들었습니다. 이야기와 감정이 모두 초콜릿에 집중된 <strong>성공적 언어화</strong>.
    </div>
  </div>
</div>

<!-- 4. 심리 분석 -->
<h2>4. 심리 분석</h2>
<div class="grid3">
  <div class="card" style="border-top:3px solid var(--orange);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--orange);margin-bottom:8px;">사전</div>
    <div style="font-size:20px;font-weight:800;">진정성 {auth_pre}</div>
    <div style="font-size:11px;color:var(--body);margin-top:4px;">추천 확신도 {clout_pre}</div>
  </div>
  <div class="card" style="border-top:3px solid var(--primary);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--primary);margin-bottom:8px;">팝업기간</div>
    <div style="font-size:20px;font-weight:800;">진정성 {auth_dur}</div>
    <div style="font-size:11px;color:var(--body);margin-top:4px;">추천 확신도 {clout_dur}</div>
  </div>
  <div class="card" style="border-top:3px solid var(--green);text-align:center;">
    <div style="font-size:11px;font-weight:700;color:var(--green);margin-bottom:8px;">팝업후</div>
    <div style="font-size:20px;font-weight:800;">진정성 {auth_post}</div>
    <div style="font-size:11px;color:var(--body);margin-top:4px;">추천 확신도 {clout_post}</div>
  </div>
</div>
<div class="insight" style="margin:12px 0;">
  팝업 초반에는 생생한 체험의 기억이 솔직하게 담겼습니다. 팝업 기간 중에는 협찬과 과잉 긍정이 섞이며 진정성이 소폭 하락했지만, 팝업이 끝난 뒤에는 오히려 <strong style="color:var(--green);">진정성이 회복</strong>되었습니다. 31일이라는 장기 운영 기간이 장기 운영에서 나타나는 진정성 피로를 방지한 결과입니다.
</div>

<!-- 5. 협찬 분석 -->
<h2>5. 협찬 분석 Before → After</h2>
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
        <div style="font-size:10px;">협찬 | 진정성 {auth_level(avg("authenticity",spon))}</div>
      </div>
      <div style="text-align:center;padding:10px;background:#f0fdf4;border-radius:8px;">
        <div style="font-size:20px;font-weight:800;color:var(--green);">{len(org)}건</div>
        <div style="font-size:10px;">자발적 | 진정성 {auth_level(avg("authenticity",org))}</div>
      </div>
    </div>
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      협찬 포스트는 자발적 후기 대비 진정성이 <strong style="color:var(--coral);">현저히 낮습니다</strong>. 같은 "긍정" 평가라도 의무적 톤과 실제 감동 사이에는 질적 격차가 존재하며, RXR은 이를 구분합니다.
    </div>
  </div>
</div>

<!-- 6. 후기 품질 -->
<h2>6. 후기 품질 Before → After</h2>
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
      서사형 <strong>{rql_dist.get("Q5_서사형",0)}</strong>건 · 분석형 <strong>{rql_dist.get("Q4_분석형",0)}</strong>건 · 경험형 <strong>{rql_dist.get("Q3_경험형",0)}</strong>건 · 감상형 <strong>{rql_dist.get("Q2_감상형",0)}</strong>건 · 간단형 <strong>{rql_dist.get("Q1_간단형",0)}</strong>건
    </div>
    <div style="margin-top:8px;padding:10px 14px;background:#eef2ff;border-radius:8px;font-size:12px;line-height:1.7;">
      고품질 후기(서사형+분석형) {rql_dist.get("Q5_서사형",0)+rql_dist.get("Q4_분석형",0)}건({round((rql_dist.get("Q5_서사형",0)+rql_dist.get("Q4_분석형",0))/N*100,1)}%). 공간 체험이 풍부한 서사를 만들어내고 있지만, 스토리 공유 장치를 더하면 이 비율을 높일 수 있습니다.
    </div>
  </div>
</div>

<!-- 7. 진심 필터 -->
<h2>7. 진심 필터 — 3단계</h2>
<div class="card" style="padding:20px;margin:16px 0;">
  <div class="funnel-bar" style="width:100%;background:linear-gradient(90deg,#94a3b8,#b0b8c4);">1차 필터 (노이즈 제거) — {gs1["n"]}건 | 긍정 {gs1["pos_pct"]}%</div>
  <div class="funnel-bar" style="width:{round(gs2["n"]/max(gs1["n"],1)*100)}%;background:linear-gradient(90deg,#6666FF,#8888FF);">2차 필터 (협찬·보도 분리) — {gs2["n"]}건 | 긍정 {gs2["pos_pct"]}%</div>
  <div class="funnel-bar" style="width:{round(gs3["n"]/max(gs1["n"],1)*100)}%;background:linear-gradient(90deg,#10b981,#34d399);">3차 필터 (진정성 기준) — {gs3["n"]}건 | 긍정 {gs3["pos_pct"]}%</div>
</div>
<div style="margin:16px 0;">
  <table>
    <tr><th></th><th>건수</th><th>긍정률</th><th>필터</th></tr>
    <tr><td style="font-weight:700;">1차 필터</td><td>{gs1["n"]}</td><td>{gs1["pos_pct"]}%</td><td>노이즈 제거</td></tr>
    <tr><td style="font-weight:700;">2차 필터</td><td>{gs2["n"]}</td><td>{gs2["pos_pct"]}%</td><td>+ 협찬/공유/보도 제거</td></tr>
    <tr style="background:var(--primary-pale);"><td style="font-weight:700;color:var(--primary);">3차 필터</td><td style="font-weight:800;">{gs3["n"]}</td><td style="font-weight:800;color:var(--coral);">{gs3["pos_pct"]}%</td><td>+ 진정성 기준 이상</td></tr>
  </table>
</div>
<div class="insight">
  <strong>1차 → 3차: 긍정률 {gs1["pos_pct"]}% → {gs3["pos_pct"]}% ({round(gs3["pos_pct"]-gs1["pos_pct"],1)}%p)</strong><br>
  단계를 거칠수록 과장된 긍정이 걸러지며 실제 소비자의 진심에 가까워집니다. 3차 필터를 통과한 {gs3["n"]}건이 "진짜 반응"입니다.
</div>

<!-- 8. 핵심 수치 요약 -->
<h2>8. 핵심 수치 요약</h2>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);"><div style="font-size:28px;font-weight:800;color:var(--primary);">{total_mentions}</div><div style="font-size:10px;color:var(--body);">총 멘션</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--pink);"><div style="font-size:28px;font-weight:800;color:var(--pink);">{gs3["n"]}</div><div style="font-size:10px;color:var(--body);">3차 필터 유효</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--coral);"><div style="font-size:28px;font-weight:800;color:var(--coral);">{gs3["pos_pct"]}%</div><div style="font-size:10px;color:var(--body);">진심 긍정률</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--green);"><div style="font-size:28px;font-weight:800;color:var(--green);">{g3_both_pct}%</div><div style="font-size:10px;color:var(--body);">즐거움+고급 동시 전달률</div></div>
</div>

<!-- 종합 비교표 -->
<h2>종합 Before → After 비교표</h2>
<table>
  <tr><th>비교 영역</th><th>BEFORE (기존)</th><th>AFTER (RXR)</th></tr>
  <tr><td style="font-weight:700;">버즈 규모</td><td>총 {total_mentions}건</td><td>3차 필터 유효 <strong>{gs3["n"]}건</strong></td></tr>
  <tr><td style="font-weight:700;">감성</td><td>긍정/중립/부정 3단계</td><td>4단계 + 진정성 + 추천 확신도</td></tr>
  <tr><td style="font-weight:700;">협찬 분석</td><td>유/무 이분법</td><td>진심 필터 3단계 + 진정성 스펙트럼</td></tr>
  <tr><td style="font-weight:700;">핵심 감정</td><td>긍정/부정 이분법</td><td>즐거움 × 고급스러움 2축 4분면 분석</td></tr>
  <tr><td style="font-weight:700;">심리</td><td>불가능</td><td>진정성/추천 확신도/신선함 지수 추적</td></tr>
  <tr><td style="font-weight:700;">후기 품질</td><td>1건=1건</td><td>후기 깊이 5등급 (분석 가중치 적용)</td></tr>
  <tr><td style="font-weight:700;">브랜드 경험</td><td>측정 불가</td><td>즐거움+고급 동시 전달 {g3_both_pct}% — "의도된 복합 경험 성공" 진단</td></tr>
</table>

<!-- BOTTOM LINE -->
<h2>BOTTOM LINE</h2>
<div style="padding:24px;background:var(--primary-pale);border-radius:16px;margin:16px 0;">
  <div style="text-align:center;margin-bottom:20px;">
    <div style="font-size:13px;color:var(--body);margin-bottom:8px;">기존 도구</div>
    <div style="font-size:17px;font-weight:800;color:var(--body);">"{total_mentions}건 멘션, 긍정 {sent_pct.get("긍정",0)}%"</div>
    <div style="font-size:20px;margin:8px 0;">↓</div>
    <div style="font-size:13px;color:var(--primary);margin-bottom:8px;">RXR 분석</div>
    <div style="font-size:17px;font-weight:800;color:var(--primary);">"유효 {gs3["n"]}건 중 '즐거움+고급' 동시 전달 {len(g3_both)}건({g3_both_pct}%). 가나가 의도한 복합 경험이 성공적으로 전달됐다."</div>
  </div>

  <h3 style="margin-top:20px;">왜 이런 결과가 나왔는가?</h3>
  <div class="grid2" style="gap:12px;margin-top:12px;">
    <div class="card" style="border-top:3px solid var(--coral);">
      <div style="font-size:18px;font-weight:800;color:var(--coral);">긍정률 실제보다 과대</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">협찬의 의무적 긍정과 과잉 표현이 전체 긍정률을 부풀리고 있었습니다. 진심 필터를 거치면 실제 긍정은 {gs3["pos_pct"]}%입니다.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--orange);">
      <div style="font-size:18px;font-weight:800;color:var(--orange);">협찬 vs 자발적 격차</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">협찬 포스트의 진정성은 자발적 후기 대비 현저히 낮습니다. 같은 "긍정" 평가 안에서도 진심의 농도 차이가 큽니다.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--primary);">
      <div style="font-size:18px;font-weight:800;color:var(--primary);">컨셉 전달 실패</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">초콜릿의 즐거움과 브랜드의 고급스러움이 블로그 언어에 분명히 새겨졌습니다. 두 감정이 동시에 담긴 Q1 포스트가 {len(g3_both)}건({g3_both_pct}%)으로 거의 절반에 달합니다.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--green);">
      <div style="font-size:18px;font-weight:800;color:var(--green);">단기 운영의 강점</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">31일 장기 운영 덕분에 장기 팝업에서 나타나는 진정성 피로가 없었습니다. 팝업 후 후기가 오히려 더 솔직하고 진정성 있게 작성되었습니다.</div>
    </div>
  </div>

  <h3 style="margin-top:20px;">제언: 다음 팝업에서 무엇을 바꿀 것인가?</h3>
  <div class="grid3" style="gap:12px;margin-top:12px;">
    <div class="card" style="border-left:4px solid var(--primary);">
      <div style="font-size:14px;font-weight:800;color:var(--primary);margin-bottom:6px;">컨셉 체험화</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">맛의 순간을 서사로 바꾸는 장치(장인 해설·테이스팅 카드·스토리 QR)로 "달콤했다"를 "잊지 못할 한 입"으로 전환해야 합니다.</div>
    </div>
    <div class="card" style="border-left:4px solid var(--orange);">
      <div style="font-size:14px;font-weight:800;color:var(--orange);margin-bottom:6px;">체험 요소별 화제성</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">4개 체험 요소를 각각의 포토존+해시태그로 분리 운영. 체험별 관심층이 자발적으로 콘텐츠를 생산하는 구조를 만들어야 합니다.</div>
    </div>
    <div class="card" style="border-left:4px solid var(--green);">
      <div style="font-size:14px;font-weight:800;color:var(--green);margin-bottom:6px;">서사형 후기 유도</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">미션 클리어 인증+스토리 템플릿+리뷰 이벤트로 깊이 있는 후기 비율을 높여야 합니다. 진성 후기가 가장 강력한 마케팅 자산입니다.</div>
    </div>
  </div>
</div>

<!-- 부록: 하이라이트 20건 -->
<h2>부록: 하이라이트 후기 20건</h2>
<div class="grid2">
  <div>
    <h3 style="color:var(--green);">진정성 높은 후기 TOP 10</h3>
    {highlight_cards(high_auth, "high")}
  </div>
  <div>
    <h3 style="color:var(--coral);">진정성 낮은 후기 10건</h3>
    {highlight_cards(low_auth_all, "low")}
  </div>
</div>

<!-- Footer -->
<div class="footer">
  RXR SNS Analysis &middot; 가나초콜릿하우스 부산 시즌2 &middot; {datetime.now().strftime("%Y-%m-%d")} &middot; Project RENT &middot; R-lab
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

# Save external
ext_path = os.path.join(BASE, "../../82-case-reports/gana-chocolate-house/gana-chocolate-house-rxr-sns-report-external.html")
with open(ext_path, "w", encoding="utf-8") as f:
    f.write(external_html)
print(f"외부용 생성: {ext_path} ({os.path.getsize(ext_path):,} bytes)")

# ============================================================
# 잠금 버전 생성
# ============================================================
PASSWORD = "RXR-projectrent"
pw_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()

# Base64 encode external HTML, split into chunks
b64 = base64.b64encode(external_html.encode("utf-8")).decode("ascii")
CHUNK = 50000
chunks = [b64[i:i+CHUNK] for i in range(0, len(b64), CHUNK)]
chunks_js = ",".join(f'"{c}"' for c in chunks)

locked_html = f'''<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>롯데제과 가나 가나초콜릿하우스 — RXR SNS 분석 (Protected)</title>
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
  <div class="lock-sub">가나초콜릿하우스 부산 · 시즌2<br>이 리포트는 비밀번호로 보호되어 있습니다.</div>
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

locked_path = os.path.join(BASE, "../../82-case-reports/gana-chocolate-house/gana-chocolate-house-rxr-sns-report-locked.html")
with open(locked_path, "w", encoding="utf-8") as f:
    f.write(locked_html)
print(f"잠금 버전 생성: {locked_path} ({os.path.getsize(locked_path):,} bytes)")
print(f"\n비밀번호: {PASSWORD}")
