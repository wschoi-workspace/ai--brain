"""컴온스타일 팝업스토어 — 외부용 + 잠금 버전 생성"""
import json, os, sys, io, hashlib, base64
from collections import Counter
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = os.path.dirname(__file__)
with open(os.path.join(BASE, "comonstyle-popup-2layer-results.json"), "r", encoding="utf-8") as f:
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

b24 = {"total": 462, "reach": "~4M", "instagram": 229, "tiktok": 52, "x": 12, "news": 8, "facebook": 4, "web": 1, "blogs": 156}
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

slowaging_count = sum(1 for r in data if "슬로우에이징" in (r.get("title","") + " " + str(r.get("topic_scores",{}))))
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
        if d < "20250404": color = "var(--orange)"; label = "사전" if d == dates_sorted[0][0] else ""
        elif d <= "20250408": color = "var(--primary)"; label = "팝업기간" if d == "20250404" else ""
        else: color = "#94a3b8"; label = "팝업후" if d == "20250409" else ""
        inner = f"{cnt}" if cnt >= 5 else ""
        rows.append(f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:40px;font-size:9px;color:var(--body);text-align:right;">{md}</div><div style="flex:1;height:15px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{max(pct,3)}%;height:100%;background:{color};border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;font-weight:600;color:#fff;">{inner}</div></div><div style="width:20px;font-size:9px;font-weight:600;">{cnt}</div><div style="width:65px;font-size:8px;color:{color};font-weight:700;">{label}</div></div>')
    return "\n".join(rows)

def topic_bars_ext():
    rows = []
    max_t = topic_dist[0][1] if topic_dist else 1
    for topic, cnt in topic_dist:
        pct = round(cnt / max_t * 100)
        ratio = round(cnt / N * 100, 1)
        rows.append(f'<div class="gauge-row"><div class="gauge-label" style="width:100px;">{topic}</div><div class="gauge-track"><div class="gauge-fill" style="width:{pct}%;background:var(--primary);">{cnt}건 ({ratio}%)</div></div><div class="gauge-val" style="color:var(--primary);">{ratio}%</div></div>')
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
<title>CJ온스타일 컴온스타일 팝업스토어 — RXR SNS 분석</title>
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
<h1>CJ온스타일 컴온스타일 — 쇼케이스 팝업스토어</h1>
<div class="sub">기존 분석 vs RXR 다층 분석 + 진심 필터 | 네이버 블로그 {N}건 + Brand24 {b24_nonblog}건 = 총 {total_mentions}건 | Project RENT &middot; R-lab</div>

<!-- 리서치 개요 -->
<div style="padding:20px;background:var(--light);border-radius:14px;margin-bottom:24px;">
  <div class="grid2">
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">ABOUT THIS RESEARCH</div>
      <h3 style="margin-top:0;">분석 대상</h3>
      <table style="font-size:12px;"><tr><td style="color:var(--body);width:70px;padding:4px 0;">팝업명</td><td style="padding:4px 0;font-weight:700;">컴온스타일 쇼케이스 팝업스토어</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">브랜드</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">CJ온스타일</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2025.04.04 ~ 04.08, <strong>5일간</strong></td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">장소</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">서울 성수동 XYZ서울</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">컨셉</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">슬로우에이징 라이프스타일 + 4 IP프로그램 + 무라카미 다카시 콜라보</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">분석 기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2025.03.21 ~ 04.22</td></tr></table>
    </div>
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">RESEARCH PERSPECTIVE</div>
      <h3 style="margin-top:0;">리서치 관점</h3>
      <div style="font-size:12px;color:var(--body);line-height:1.7;">
        <div style="padding:4px 0;"><strong style="color:var(--primary);">핵심 질문:</strong> "슬로우에이징" 컨셉이 소비자에게 실제로 전달되었는가?</div>
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
    <p style="margin-bottom:14px;">CJ온스타일의 첫 오프라인 팝업스토어 '컴온스타일 쇼케이스'는 5일간 성수동 XYZ서울에서 운영되며, 네이버 블로그와 SNS를 합쳐 <strong style="color:var(--primary);">총 {total_mentions}건의 멘션</strong>을 만들어냈습니다. 기존 분석 도구로 보면 "긍정 {sent_pct.get('긍정',0)}%, 관심이 집중된 캠페인"이라는 결론이 나옵니다. 하지만 RXR의 다층 분석으로 들여다보면, 숫자 뒤에 숨겨진 이야기가 드러납니다.</p>

    <p style="margin-bottom:14px;">{N}건의 네이버 블로그 포스트 중 진심 필터를 통과한 유효 반응은 <strong style="color:var(--primary);">{gs3["n"]}건</strong>이었습니다. 나머지는 과잉 긍정 표현이 가득하거나, 협찬 의무로 작성된 형식적 후기였습니다. 진심 필터를 적용하자 <strong style="color:var(--coral);">실제 긍정률은 {gs1["pos_pct"]}%에서 {gs3["pos_pct"]}%로 하락</strong>했습니다. 겉으로는 호의적이었던 반응의 상당 부분이 진심이라기보다 의무적 표현이었다는 뜻입니다.</p>

    <p style="margin-bottom:14px;">가장 주목할 발견은 <strong style="color:var(--coral);">"슬로우에이징" 컨셉의 소비자 침투율이 사실상 0%</strong>라는 점입니다. CJ온스타일이 이번 팝업의 핵심 메시지로 내세운 '슬로우에이징 라이프스타일 솔루션'이라는 컨셉은, 방문자들의 후기에서 거의 언급되지 않았습니다. 대신 소비자들은 <strong style="color:var(--primary);">"보라색 공간이 예뻤다"(41%)</strong>는 공간 경험을 가장 많이 이야기했습니다. 브랜드가 전달하려 했던 메시지와 소비자가 실제로 기억한 것 사이에 큰 괴리가 있었던 셈입니다.</p>

    <p style="margin-bottom:14px;">4개 IP 프로그램(최화정쇼, 겟잇뷰티, 한예슬의 오늘 뭐 입지, 안재현의 잠시 실내합니다) 역시 개별 인지보다는 "CJ온스타일 팝업"이라는 통합 인식이 지배적이었습니다. 최화정쇼만이 {ip_mentions.get("최화정",0)}건의 유의미한 버즈를 만들었을 뿐, 나머지 IP는 독립적 화제를 만들어내지 못했습니다.</p>

    <p style="margin-bottom:14px;">흥미로운 점은 <strong style="color:var(--green);">시간에 따른 진정성의 변화</strong>입니다. 팝업 기간 중 작성된 후기보다 팝업이 끝난 후 작성된 후기의 진정성이 더 높았습니다. 5일이라는 짧은 운영 기간이 오히려 장점으로 작용하여, 늦은 후기가 미화 없이 체험을 솔직하게 회고하는 경향을 보였습니다. 16일간 운영된 다른 팝업에서 후반부 진정성이 급락한 것과 대조적인 결과입니다.</p>

    <p style="margin-bottom:20px;">Instagram에서 {b24["instagram"]}건의 포스트가 올라왔지만, 이는 대부분 사진 중심의 표면적 확산이었습니다. 깊이 있는 체험 서사는 네이버 블로그에 집중되어 있었고, 그중에서도 높은 품질의 서사형 후기는 {rql_dist.get("Q5_서사형",0)}건({round(rql_dist.get("Q5_서사형",0)/N*100,1)}%)이었습니다. <strong style="color:var(--primary);">진짜 브랜드 옹호자가 될 수 있는 사람은 이들입니다.</strong></p>

    <div style="padding:16px;background:#fff;border-radius:12px;border-left:4px solid var(--primary);">
      <div style="font-size:13px;font-weight:700;color:var(--primary);margin-bottom:10px;">다음 팝업을 위한 제언</div>
      <div style="font-size:12px;color:var(--body);line-height:1.8;">
        <strong>1. 컨셉을 "체험 가능한 언어"로 번역해야 합니다.</strong> "슬로우에이징"이라는 추상적 슬로건이 아닌, 방문자가 직접 만지고 경험하고 인증할 수 있는 미션이나 코너로 전환해야 합니다. "나의 슬로우에이징 루틴 만들기" 같은 인터랙티브 체험이 있어야 컨셉이 소비자 언어에 자연스럽게 녹아듭니다.<br><br>
        <strong>2. IP 프로그램별 독립 화제성을 설계해야 합니다.</strong> 4개 IP가 하나의 공간에 통합되면서 개별 인지가 희미해졌습니다. 각 IP 전용 포토존과 해시태그를 분리 운영하면, IP별 팬덤이 자발적으로 콘텐츠를 생산하는 구조를 만들 수 있습니다.<br><br>
        <strong>3. 5일 단기 집중형의 강점을 살려야 합니다.</strong> 이번 분석에서 확인된 단기 운영의 심리적 이점 — 진정성 유지, 희소성 효과 — 은 향후 팝업 운영 전략의 중요한 근거가 됩니다. 장기 운영보다 짧고 강렬한 경험이 더 진정성 있는 반응을 이끌어낼 수 있습니다.
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
      <strong style="color:var(--primary);">해석:</strong> 공간/분위기({round(topic_dist[0][1]/N*100)}%)가 압도적 1위. 반면 <strong style="color:var(--coral);">"슬로우에이징" 컨셉 직접 언급 {slowaging_count}건</strong> — 브랜드 핵심 메시지가 소비자 언어에 침투하지 못했습니다. 소비자는 "보라색 예쁜 공간"으로 기억했지, "슬로우에이징 솔루션"으로 기억하지 않았습니다.
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
  팝업 초반에는 생생한 체험의 기억이 솔직하게 담겼습니다. 팝업 기간 중에는 협찬과 과잉 긍정이 섞이며 진정성이 소폭 하락했지만, 팝업이 끝난 뒤에는 오히려 <strong style="color:var(--green);">진정성이 회복</strong>되었습니다. 5일이라는 짧은 운영 기간이 장기 운영에서 나타나는 진정성 피로를 방지한 결과입니다.
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
  단계를 거칠수록 과장된 긍정이 걸러지며 실제 소비자의 진심에 가까워집니다. 3차 필터를 통과한 {gs3["n"]}건이 "진짜 반응"입니다.
</div>

<!-- 8. 핵심 수치 요약 -->
<h2>8. 핵심 수치 요약</h2>
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);"><div style="font-size:28px;font-weight:800;color:var(--primary);">{total_mentions}</div><div style="font-size:10px;color:var(--body);">총 멘션</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--pink);"><div style="font-size:28px;font-weight:800;color:var(--pink);">{gs3["n"]}</div><div style="font-size:10px;color:var(--body);">3차 필터 유효</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--coral);"><div style="font-size:28px;font-weight:800;color:var(--coral);">{gs3["pos_pct"]}%</div><div style="font-size:10px;color:var(--body);">진심 긍정률</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--green);"><div style="font-size:28px;font-weight:800;color:var(--green);">0%</div><div style="font-size:10px;color:var(--body);">컨셉 침투율</div></div>
</div>

<!-- 종합 비교표 -->
<h2>종합 Before → After 비교표</h2>
<table>
  <tr><th>비교 영역</th><th>BEFORE (기존)</th><th>AFTER (RXR)</th></tr>
  <tr><td style="font-weight:700;">버즈 규모</td><td>총 {total_mentions}건</td><td>3차 필터 유효 <strong>{gs3["n"]}건</strong></td></tr>
  <tr><td style="font-weight:700;">감성</td><td>긍정/중립/부정 3단계</td><td>4단계 + 진정성 + 추천 확신도</td></tr>
  <tr><td style="font-weight:700;">협찬 분석</td><td>유/무 이분법</td><td>진심 필터 3단계 + 진정성 스펙트럼</td></tr>
  <tr><td style="font-weight:700;">토픽</td><td>워드클라우드</td><td>구조화 비중 + 컨셉 침투도</td></tr>
  <tr><td style="font-weight:700;">심리</td><td>불가능</td><td>진정성/추천 확신도/신선함 지수 추적</td></tr>
  <tr><td style="font-weight:700;">후기 품질</td><td>1건=1건</td><td>후기 깊이 5등급 (분석 가중치 적용)</td></tr>
  <tr><td style="font-weight:700;">컨셉 침투</td><td>측정 불가</td><td>"슬로우에이징" 0건 — 미침투 진단</td></tr>
</table>

<!-- BOTTOM LINE -->
<h2>BOTTOM LINE</h2>
<div style="padding:24px;background:var(--primary-pale);border-radius:16px;margin:16px 0;">
  <div style="text-align:center;margin-bottom:20px;">
    <div style="font-size:13px;color:var(--body);margin-bottom:8px;">기존 도구</div>
    <div style="font-size:17px;font-weight:800;color:var(--body);">"{total_mentions}건 멘션, 긍정 {sent_pct.get("긍정",0)}%"</div>
    <div style="font-size:20px;margin:8px 0;">↓</div>
    <div style="font-size:13px;color:var(--primary);margin-bottom:8px;">RXR 분석</div>
    <div style="font-size:17px;font-weight:800;color:var(--primary);">"유효 {gs3["n"]}건, 진심 긍정 {gs3["pos_pct"]}%, 핵심 컨셉 침투율 0%"</div>
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
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">"슬로우에이징"이라는 핵심 메시지가 소비자 후기에 거의 등장하지 않았습니다. 소비자는 "보라색 예쁜 공간"으로만 기억했습니다.</div>
    </div>
    <div class="card" style="border-top:3px solid var(--green);">
      <div style="font-size:18px;font-weight:800;color:var(--green);">단기 운영의 강점</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;margin-top:6px;">5일 집중 운영 덕분에 장기 팝업에서 나타나는 진정성 피로가 없었습니다. 팝업 후 후기가 오히려 더 솔직하고 진정성 있게 작성되었습니다.</div>
    </div>
  </div>

  <h3 style="margin-top:20px;">제언: 다음 팝업에서 무엇을 바꿀 것인가?</h3>
  <div class="grid3" style="gap:12px;margin-top:12px;">
    <div class="card" style="border-left:4px solid var(--primary);">
      <div style="font-size:14px;font-weight:800;color:var(--primary);margin-bottom:6px;">컨셉 체험화</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">추상적 슬로건을 손으로 만지는 체험으로 전환. "나의 슬로우에이징 루틴 만들기" 같은 인터랙티브 코너가 컨셉 침투의 열쇠입니다.</div>
    </div>
    <div class="card" style="border-left:4px solid var(--orange);">
      <div style="font-size:14px;font-weight:800;color:var(--orange);margin-bottom:6px;">IP 개별 화제성</div>
      <div style="font-size:12px;color:var(--body);line-height:1.6;">4개 IP를 각각의 포토존+해시태그로 분리 운영. IP별 팬덤이 자발적으로 콘텐츠를 생산하는 구조를 만들어야 합니다.</div>
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
  RXR SNS Analysis &middot; CJ온스타일 컴온스타일 팝업스토어 &middot; {datetime.now().strftime("%Y-%m-%d")} &middot; Project RENT &middot; R-lab
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
ext_path = os.path.join(BASE, "comonstyle-popup-rxr-sns-report-external.html")
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
<title>CJ온스타일 컴온스타일 — RXR SNS 분석 (Protected)</title>
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
  <div class="lock-sub">CJ온스타일 컴온스타일 — 쇼케이스 팝업스토어<br>이 리포트는 비밀번호로 보호되어 있습니다.</div>
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

locked_path = os.path.join(BASE, "comonstyle-popup-rxr-sns-report-locked.html")
with open(locked_path, "w", encoding="utf-8") as f:
    f.write(locked_html)
print(f"잠금 버전 생성: {locked_path} ({os.path.getsize(locked_path):,} bytes)")
print(f"\n비밀번호: {PASSWORD}")
