"""새로중앙박물관 RXR SNS 분석 — 전체 리포트 (이클립스 템플릿 기준)"""
import json, sys
from collections import Counter
from pathlib import Path

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

with open(r'C:\Users\insig\do-better-workspace\30-knowledge\saero-popup-2layer-results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

gate3 = sorted([d for d in data if d['authenticity'] >= 60 and not d['is_sponsored']], key=lambda x: -x['authenticity'])
spon = sorted([d for d in data if d['is_sponsored']], key=lambda x: -x['authenticity'])
org = [d for d in data if not d['is_sponsored']]

# 통계
total = len(data)
g3_sents = Counter(d['sentiment'] for d in gate3)
g3_rqls = Counter(d['rql'] for d in gate3)
g3_avg_auth = sum(d['authenticity'] for d in gate3) / len(gate3)
g3_avg_clout = sum(d['clout'] for d in gate3) / len(gate3)
all_sents = Counter(d['sentiment'] for d in data)
all_rqls = Counter(d['rql'] for d in data)
all_topics = Counter(d['primary_topic'] for d in data)

# ========== 부분 HTML 생성 함수들 ==========

def make_date_bars():
    dd = [('03/07',1),('03/08',1),('03/09',2),('03/10',3),('03/11',6),('03/12',4),('03/13',2),('03/14',4),('03/15',6),('03/16',4),('03/17',1),('03/18',4),('03/19',3),('03/20',4),('03/21',8),('03/22',12),('03/23',15),('03/24',13),('03/25',21),('03/26',20),('03/27',13),('03/28',18),('03/29',15),('03/30',10),('03/31',20),('04/01',8),('04/02',15),('04/03',10),('04/04',18),('04/05',8),('04/06',8),('04/07',4)]
    mx = 21
    out = ""
    for dt, cnt in dd:
        pct = cnt/mx*100
        m, d = dt.split('/')
        raw = f"202603{d}" if m=='03' else f"202604{d}"
        if raw < '20260321': color, note = 'var(--orange)', ('이벤트 전' if dt=='03/07' else '')
        elif raw <= '20260405': color = 'var(--primary)'; note = '★ 시작' if dt=='03/21' else ('★ 피크' if cnt==21 else '')
        else: color, note = '#94a3b8', ('이벤트 후' if dt=='04/06' else '')
        ns = f'color:{color};font-weight:700;' if note else ''
        bt = str(cnt) if cnt >= 6 else ''
        out += f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:40px;font-size:9px;color:var(--body);text-align:right;">{dt}</div><div style="flex:1;height:15px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;font-weight:600;color:#fff;">{bt}</div></div><div style="width:20px;font-size:9px;font-weight:600;">{cnt}</div><div style="width:65px;font-size:8px;{ns}">{note}</div></div>\n'
        if dt == '03/20': out += '<div style="height:3px;border-bottom:2px solid var(--primary);margin:2px 0;"></div>\n'
        elif dt == '04/05': out += '<div style="height:3px;border-bottom:2px dashed #ddd;margin:2px 0;"></div>\n'
    return out

def make_spon_details():
    out = ""
    for d in spon:
        a = d['authenticity']
        ac = '#059669' if a >= 55 else '#f59e0b' if a >= 30 else '#dc2626'
        bg = '#ecfdf5' if a >= 55 else '#fef3c7' if a >= 30 else '#fee2e2'
        out += f'<div style="padding:5px 8px;background:{bg};border-radius:6px;margin-bottom:3px;font-size:11px;"><strong style="color:{ac};">Auth {a}</strong> — "{d["title"][:42]}" ({d["date"][4:6]}/{d["date"][6:]}) · 느낌표 {d["exclamation"]}개 · Clout {d["clout"]}</div>\n'
    return out

def make_appendix():
    out = ""
    for i, d in enumerate(gate3):
        title = d['title'][:55].replace('&','&amp;').replace('<','&lt;')
        df = f"{d['date'][:4]}-{d['date'][4:6]}-{d['date'][6:]}"
        sc = '#059669' if d['sentiment']=='긍정' else '#dc2626' if d['sentiment']=='부정' else '#6666FF' if d['sentiment']=='혼합' else '#94a3b8'
        ac = '#059669' if d['authenticity']>=75 else '#6666FF'
        bg = '#f0fdf4' if i%2==0 else '#fff'
        blogger = d.get('blogger','')[:14].replace('&','&amp;')
        period = d.get('period','')[:6]
        out += f'<tr style="background:{bg};"><td style="padding:3px 4px;text-align:center;">{i+1}</td><td style="padding:3px 4px;">{df}</td><td style="padding:3px 4px;color:{sc};font-weight:600;">{d["sentiment"]}</td><td style="padding:3px 4px;text-align:center;"><strong style="color:{ac};">{d["authenticity"]}</strong></td><td style="padding:3px 4px;text-align:center;">{d["clout"]}</td><td style="padding:3px 4px;text-align:center;">{d["freshness_index"]}</td><td style="padding:3px 4px;">{d["rql"].replace("_"," ")}</td><td style="padding:3px 4px;">{d["primary_topic"]}</td><td style="padding:3px 4px;">{period}</td><td style="padding:3px 4px;"><a href="{d.get("link","")}" target="_blank" style="color:#6666FF;text-decoration:none;">{title}</a></td><td style="padding:3px 4px;color:#94a3b8;">{blogger}</td></tr>\n'
    return out

# ========== 이클립스 before-after.html을 읽어서 템플릿으로 사용 ==========
# 대신 새로 데이터로 직접 생성

css = """@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable.css');
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
  .ba-container{gap:0!important;} .ba-box{padding:14px!important;font-size:11px!important;}
}
.pdf-panel{position:fixed;bottom:24px;right:24px;z-index:1000;}
.pdf-panel-toggle{display:flex;align-items:center;gap:8px;padding:12px 22px;background:var(--grad);color:#fff;border-radius:50px;font-size:14px;font-weight:600;cursor:pointer;box-shadow:0 4px 20px rgba(102,102,255,0.4);border:none;font-family:'Pretendard Variable',sans-serif;}
.pdf-panel-body{display:none;position:absolute;bottom:56px;right:0;width:220px;background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,0.18);padding:16px;}
.pdf-panel-body.open{display:block;}
.pdf-orient-group{display:flex;gap:8px;margin-bottom:14px;}
.pdf-orient-btn{flex:1;padding:12px 8px;background:#f9fafb;border:2px solid #e2e8f0;border-radius:12px;cursor:pointer;font-family:'Pretendard Variable',sans-serif;color:#475569;font-size:11px;font-weight:600;text-align:center;}
.pdf-orient-btn.active{border-color:var(--primary);background:#eef2ff;color:var(--primary);}
.pdf-print-btn{width:100%;padding:10px;background:var(--grad);color:#fff;border:none;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Pretendard Variable',sans-serif;}"""

avg_auth_org = sum(d['authenticity'] for d in org)/len(org)
avg_auth_spon = sum(d['authenticity'] for d in spon)/len(spon) if spon else 0

html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>새로중앙박물관 — RXR SNS 분석 (Full)</title>
<style>{css}</style><style id="pageOrientStyle"></style></head><body>

<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
  <span style="background:var(--grad);color:#fff;padding:4px 14px;border-radius:6px;font-family:'Poppins';font-size:11px;font-weight:600;letter-spacing:1px;">RXR SNS ANALYSIS</span>
</div>
<h1>새로중앙박물관 — 천년의 비법서 도난 사건</h1>
<div class="sub">기존 분석 vs RXR 2-Layer + Sincerity Gate | 네이버 블로그 281건 | Project RENT · R-lab</div>

<!-- 리서치 개요 -->
<div style="padding:20px;background:var(--light);border-radius:14px;margin-bottom:24px;">
  <div class="grid2">
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">ABOUT THIS RESEARCH</div>
      <h3 style="margin-top:0;">분석 대상</h3>
      <table style="font-size:12px;"><tr><td style="color:var(--body);width:70px;padding:4px 0;">팝업명</td><td style="padding:4px 0;font-weight:700;">새로중앙박물관 — 천년의 비법서 도난 사건</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">브랜드</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">새로 (롯데칠성음료)</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2026.03.21 ~ 04.05, <strong>16일간</strong></td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">장소</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">서울 성수동 더가베</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">컨셉</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">방탈출형 미션 + 소주 시음 + 럭키드로우 + 침착맨 콜라보</td></tr><tr><td style="color:var(--body);padding:4px 0;border-top:1px solid #e8e8e8;">분석 기간</td><td style="padding:4px 0;border-top:1px solid #e8e8e8;">2026.03.07 ~ 04.07</td></tr></table>
    </div>
    <div>
      <div style="font-size:11px;font-family:'Poppins';letter-spacing:2px;color:var(--body);margin-bottom:6px;">RESEARCH PERSPECTIVE</div>
      <h3 style="margin-top:0;">리서치 관점</h3>
      <div style="font-size:12px;color:var(--body);line-height:1.7;">
        <div style="padding:4px 0;"><strong style="color:var(--primary);">핵심 질문:</strong> 기존 도구의 숫자와 RXR 분석의 인사이트가 얼마나 다른가?</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">데이터:</strong> 네이버 블로그 281건 (정밀 필터)</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">분석:</strong> Content + Psyche + Sincerity Gate 3단계</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">비교:</strong> 이클립스 월드 팝업과 교차 비교</div>
      </div>
    </div>
  </div>
  <div style="margin-top:12px;padding:10px 14px;background:var(--primary-pale);border-radius:8px;font-size:12px;color:var(--body);">
    📖 <strong>읽는 법:</strong> 각 섹션은 <strong>BEFORE(기존 도구)</strong>와 <strong>AFTER(RXR)</strong>를 나란히 비교합니다. AFTER 파트에는 📊 Raw Data 근거 박스가 포함됩니다.
  </div>
</div>

<!-- 0. 데이터 수집 개요 -->
<h2>0. 데이터 수집 개요</h2>
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--primary);">281</div><div style="font-size:10px;color:var(--body);">네이버 블로그</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--green);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--green);">224</div><div style="font-size:10px;color:var(--body);">이벤트 기간</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--orange);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--orange);">45</div><div style="font-size:10px;color:var(--body);">이벤트 전</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--pink);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--pink);">204</div><div style="font-size:10px;color:var(--body);">Gate 3 유효</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--blue);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--blue);">16일</div><div style="font-size:10px;color:var(--body);">운영 기간</div></div>
</div>
<h3>날짜별 버즈 분포</h3>
{make_date_bars()}
<div class="grid2" style="margin-top:12px;">
  <div><h3>기간별 비교</h3><table><thead><tr><th>기간</th><th>건수</th><th>일평균</th><th>비율</th></tr></thead><tbody><tr><td style="color:var(--orange);font-weight:700;">이벤트 전</td><td><strong>45</strong></td><td>3.2</td><td>16%</td></tr><tr><td style="color:var(--primary);font-weight:700;">이벤트 기간</td><td><strong>224</strong></td><td>14.0</td><td>80%</td></tr><tr><td style="color:#94a3b8;">이벤트 후</td><td><strong>12</strong></td><td>6.0</td><td>4%</td></tr><tr style="background:var(--primary-pale);"><td style="font-weight:700;">합계</td><td style="font-weight:700;color:var(--primary);">281</td><td></td><td>100%</td></tr></tbody></table></div>
  <div><h3>핵심 패턴</h3><div style="font-size:12px;line-height:1.7;"><div style="padding:5px 8px;background:var(--light);border-radius:6px;margin-bottom:4px;border-left:3px solid var(--primary);"><strong style="color:var(--primary);">이벤트 기간 80%</strong> — 실제 체험 후기 대부분 (이클립스 15%와 대조)</div><div style="padding:5px 8px;background:var(--light);border-radius:6px;margin-bottom:4px;border-left:3px solid var(--orange);"><strong style="color:var(--orange);">사전 버즈 16%</strong> — 신제품 출시 없어 사전 화제 적음</div><div style="padding:5px 8px;background:var(--light);border-radius:6px;border-left:3px solid var(--green);"><strong style="color:var(--green);">3/25 피크 21건</strong> — 주말 방문 후기 폭발</div></div></div>
</div>

<!-- 1. 감성 분석 Before→After -->
<h2>1. 감성 분석 — "좋았나요?"에서 "진심이었나요?"로</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE — 기존 도구</div>
    <div class="ba-title" style="color:#475569;">감성 분류: 3단계</div>
    <div style="display:flex;gap:8px;margin:12px 0;"><div style="flex:1;text-align:center;padding:10px;background:#fff;border-radius:8px;"><div style="font-size:24px;font-weight:800;color:var(--green);">50%</div><div style="font-size:10px;">긍정</div></div><div style="flex:1;text-align:center;padding:10px;background:#fff;border-radius:8px;"><div style="font-size:24px;font-weight:800;color:#94a3b8;">49%</div><div style="font-size:10px;">중립</div></div><div style="flex:1;text-align:center;padding:10px;background:#fff;border-radius:8px;"><div style="font-size:24px;font-weight:800;color:var(--red);">1%</div><div style="font-size:10px;">부정</div></div></div>
    <div style="padding:8px;background:#e2e8f0;border-radius:6px;font-size:12px;color:#475569;text-align:center;">"긍정 50%니까 절반이 좋아했네요"<br><strong>끝. 더 이상 알 수 없음.</strong></div>
  </div>
  <div class="ba-vs">→</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER — RXR 2-Layer</div>
    <div class="ba-title" style="color:var(--primary);">감성 4단계 + 진정성 + 추천 확신도</div>
    <div style="display:flex;gap:6px;margin:10px 0;"><div style="flex:1;text-align:center;padding:8px;background:#fff;border-radius:8px;"><div style="font-size:20px;font-weight:800;color:var(--green);">50%</div><div style="font-size:9px;">긍정</div></div><div style="flex:1;text-align:center;padding:8px;background:#fff;border-radius:8px;"><div style="font-size:20px;font-weight:800;color:#94a3b8;">36%</div><div style="font-size:9px;">중립</div></div><div style="flex:1;text-align:center;padding:8px;background:#fff;border-radius:8px;"><div style="font-size:20px;font-weight:800;color:var(--primary);">12%</div><div style="font-size:9px;">혼합</div></div><div style="flex:1;text-align:center;padding:8px;background:#fff;border-radius:8px;"><div style="font-size:20px;font-weight:800;color:var(--red);">1%</div><div style="font-size:9px;">부정</div></div></div>
    <div style="padding:8px;background:#eef2ff;border-radius:6px;font-size:12px;color:var(--primary);">→ "긍정 50%이나 <strong>Auth 58.4</strong> → 과장 기미"<br>→ "<strong>Clout 49.8</strong> → 적극 추천까지는 안 감"<br>→ <strong>"화제성은 있으나 옹호자 전환은 미달"</strong></div>
  </div>
</div>
<div style="padding:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;">
  <div style="font-size:12px;font-weight:700;color:var(--primary);margin-bottom:8px;">📊 왜 이런 수치? — Raw Data 근거</div>
  <div class="grid2">
    <div style="padding:8px;background:#ecfdf5;border-radius:8px;border-left:3px solid var(--green);"><div style="font-size:11px;font-weight:700;color:var(--green);">✅ Auth 최고: 88점</div><div style="font-size:10px;color:var(--body);line-height:1.5;">"침착맨 x 새로 팝업 후기" — Q5 서사형, 구체적 경험 + 균형 평가 = <strong>진정성 높음</strong></div></div>
    <div style="padding:8px;background:#fef2f2;border-radius:8px;border-left:3px solid var(--coral);"><div style="font-size:11px;font-weight:700;color:var(--coral);">⚠️ Auth 최저: 10점</div><div style="font-size:10px;color:var(--body);line-height:1.5;">"날씨가 좋으면 찾아갈게요 3월간슘삐" — 느낌표 <strong>132개!</strong> 극단 과잉 = <strong>비진정</strong></div></div>
  </div>
</div>

<!-- 2. 데이터 분류 Before→After -->
<h2>2. 데이터 분류 — "몇 건?"에서 "어떤 건?"으로</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title" style="color:#475569;">단순 카운팅</div>
    <div style="text-align:center;margin:16px 0;"><div style="font-size:48px;font-weight:800;color:#475569;">281건</div><div style="font-size:13px;color:#94a3b8;">Total Blog Posts</div></div>
    <div style="padding:8px;background:#e2e8f0;border-radius:6px;font-size:12px;color:#475569;text-align:center;">"281건 블로그 후기입니다"<br><strong>그 중 광고는? 노이즈는?</strong></div>
  </div>
  <div class="ba-vs">→</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title" style="color:var(--primary);">7단계 분류 + Trust Score</div>
    <div style="font-size:12px;line-height:1.8;margin:10px 0;">
      <div style="color:var(--green);font-weight:600;">✅ A 자발적: 276건 (98%) → 순수 반응</div>
      <div style="color:var(--orange);font-weight:600;">⚠️ C 협찬: 5건 (2%) → 진심 스펙트럼 분석</div>
    </div>
    <div style="padding:8px;background:#eef2ff;border-radius:6px;font-size:12px;color:var(--primary);"><strong>"276건 자발적 중 Auth 58.7, 협찬 5건은 Auth 37.8 — 차이 20.9점"</strong></div>
  </div>
</div>

<!-- 3. 토픽 분석 Before→After -->
<h2>3. 토픽 분석 — "워드클라우드"에서 "구조화된 인사이트"로</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title" style="color:#475569;">워드클라우드</div>
    <div style="text-align:center;padding:14px;background:#fff;border-radius:8px;margin:10px 0;"><span style="font-size:22px;font-weight:800;">새로</span> <span style="font-size:16px;">소주</span> <span style="font-size:14px;color:#94a3b8;">성수</span> <span style="font-size:13px;color:#94a3b8;">팝업</span> <span style="font-size:18px;">박물관</span> <span style="font-size:12px;color:#94a3b8;">방탈출</span></div>
    <div style="font-size:12px;color:#94a3b8;text-align:center;"><strong style="color:#475569;">그래서 뭘 해야 하는데?</strong></div>
  </div>
  <div class="ba-vs">→</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title" style="color:var(--primary);">구조화된 토픽 비중</div>
    <div style="margin:8px 0;">
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:75px;font-size:10px;text-align:right;color:var(--primary);font-weight:700;">제품/소주 68%</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:68%;height:100%;background:var(--primary);border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;color:#fff;font-weight:600;">190건</div></div></div>
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:75px;font-size:10px;text-align:right;">공간 15%</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:15.3%;height:100%;background:var(--green);border-radius:3px;"></div></div><div style="font-size:9px;">43</div></div>
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:75px;font-size:10px;text-align:right;">웨이팅 8%</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:7.8%;height:100%;background:var(--orange);border-radius:3px;"></div></div><div style="font-size:9px;">22</div></div>
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:75px;font-size:10px;text-align:right;">방탈출 7%</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:7.5%;height:100%;background:var(--pink);border-radius:3px;"></div></div><div style="font-size:9px;">21</div></div>
    </div>
    <div style="padding:8px;background:#eef2ff;border-radius:6px;font-size:12px;color:var(--primary);"><strong>"방탈출이 핵심 컨셉인데 7%만 → 체험이 제품에 묻힘. 체험 화제화 전략 필요."</strong></div>
  </div>
</div>

<!-- 4. 심리 분석 -->
<h2>4. 심리 분석 — 기존에 불가능했던 영역</h2>
<div style="text-align:center;margin:10px 0;padding:8px;background:#fef2f2;border-radius:8px;font-size:13px;font-weight:700;color:var(--coral);">BEFORE: 이 분석 자체가 불가능 — 어떤 기존 도구도 제공하지 않음</div>
<div class="gauge-row"><div class="gauge-label" style="color:var(--primary);">Authenticity<br><span style="font-size:10px;color:var(--body);">진정성</span></div><div class="gauge-track"><div class="gauge-fill" style="width:58.4%;background:var(--primary);">58.4</div></div><div class="gauge-val" style="color:var(--primary);">58.4</div></div>
<div class="gauge-row"><div class="gauge-label" style="color:var(--green);">Clout<br><span style="font-size:10px;color:var(--body);">추천 확신도</span></div><div class="gauge-track"><div class="gauge-fill" style="width:49.8%;background:var(--green);">49.8</div></div><div class="gauge-val" style="color:var(--green);">49.8</div></div>
<div class="gauge-row"><div class="gauge-label" style="color:var(--orange);">Freshness<br><span style="font-size:10px;color:var(--body);">신선함</span></div><div class="gauge-track"><div class="gauge-fill" style="width:43.1%;background:var(--orange);">43.1</div></div><div class="gauge-val" style="color:var(--orange);">43.1</div></div>

<h3>기간별 심리 변화</h3>
<table><thead><tr><th>기간</th><th>N</th><th>Auth</th><th>Clout</th><th>Fresh</th><th>해석</th></tr></thead><tbody>
  <tr><td style="color:var(--orange);font-weight:700;">이벤트 전</td><td>45</td><td><strong style="color:var(--green);">66.4</strong></td><td>49.1</td><td>41.9</td><td style="font-size:11px;">기대감, 솔직</td></tr>
  <tr style="background:#eef2ff;"><td style="color:var(--primary);font-weight:700;">이벤트 기간</td><td>224</td><td>57.4</td><td>49.9</td><td style="color:var(--green);font-weight:700;">43.1</td><td style="font-size:11px;">경험, Fresh↑</td></tr>
  <tr><td style="color:#94a3b8;font-weight:700;">이벤트 후</td><td>12</td><td><strong style="color:var(--coral);">46.2</strong></td><td>50.8</td><td>46.2</td><td style="font-size:11px;color:var(--coral);font-weight:700;">Auth -20점!</td></tr>
</tbody></table>
<div class="insight-warn insight"><strong>Auth 이벤트전 66.4 → 이벤트후 46.2 (-20점) 급락.</strong> 이클립스(-5점)보다 4배. 16일 장기 운영 → <strong>후반부 후기의 기억 과장/미화가 심각.</strong></div>
<div style="padding:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;margin-top:10px;">
  <div style="font-size:12px;font-weight:700;color:var(--primary);margin-bottom:8px;">📊 기간별 차이 근거</div>
  <div class="grid3">
    <div style="padding:8px;background:#fff7ed;border-radius:8px;border-top:3px solid var(--orange);"><div style="font-size:11px;font-weight:700;color:var(--orange);">이벤트 전 (Auth 66.4)</div><div style="font-size:10px;color:var(--body);line-height:1.5;">Auth 88 "안 가면 후회하는 새로..." 솔직한 기대 + 구체적 정보</div></div>
    <div style="padding:8px;background:#eef2ff;border-radius:8px;border-top:3px solid var(--primary);"><div style="font-size:11px;font-weight:700;color:var(--primary);">이벤트 기간 (Auth 57.4)</div><div style="font-size:10px;color:var(--body);line-height:1.5;">Auth 88 "침착맨 후기" + Auth 10 과장글 혼재</div></div>
    <div style="padding:8px;background:#f1f5f9;border-radius:8px;border-top:3px solid #94a3b8;"><div style="font-size:11px;font-weight:700;color:#94a3b8;">이벤트 후 (Auth 46.2)</div><div style="font-size:10px;color:var(--body);line-height:1.5;">느낌표 132개 포스트 등 과잉 회상 집중</div></div>
  </div>
</div>

<!-- 5. 협찬 분석 -->
<h2>5. 협찬 분석 — "있다/없다"에서 "진심의 스펙트럼"으로</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title" style="color:#475569;">협찬 표기 유무 확인</div>
    <div style="text-align:center;padding:16px;"><div style="font-size:14px;color:var(--body);">"#광고" 표기?</div><div style="display:flex;justify-content:center;gap:16px;margin:10px 0;"><div style="padding:10px 20px;background:#fff;border-radius:8px;">✅ 협찬</div><div style="padding:10px 20px;background:#fff;border-radius:8px;">❌ 자발적</div></div></div>
    <div style="padding:8px;background:#e2e8f0;border-radius:6px;font-size:12px;color:#475569;text-align:center;"><strong>협찬이면 제외? → 유의미한 데이터 손실</strong></div>
  </div>
  <div class="ba-vs">→</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title" style="color:var(--primary);">진심 스펙트럼</div>
    <div style="margin:8px 0;">
      <div class="gauge-row" style="margin-bottom:6px;"><div style="width:80px;font-size:11px;">자발적 (276건)</div><div class="gauge-track" style="height:20px;"><div class="gauge-fill" style="width:58.7%;background:var(--green);height:100%;">Auth {avg_auth_org:.1f}</div></div><div style="width:40px;font-size:13px;font-weight:700;color:var(--green);text-align:center;">{avg_auth_org:.1f}</div></div>
      <div class="gauge-row" style="margin-bottom:6px;"><div style="width:80px;font-size:11px;">협찬 (5건)</div><div class="gauge-track" style="height:20px;"><div class="gauge-fill" style="width:{avg_auth_spon:.1f}%;background:var(--orange);height:100%;">Auth {avg_auth_spon:.1f}</div></div><div style="width:40px;font-size:13px;font-weight:700;color:var(--orange);text-align:center;">{avg_auth_spon:.1f}</div></div>
    </div>
    <div style="padding:8px;background:#eef2ff;border-radius:6px;font-size:12px;color:var(--primary);"><strong>Auth 차이 20.9점</strong> — 이클립스(10.5점)보다 2배 큰 격차</div>
  </div>
</div>
<div style="padding:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;">
  <div style="font-size:12px;font-weight:700;color:var(--primary);margin-bottom:6px;">📊 협찬 5건 상세</div>
  {make_spon_details()}
</div>

<!-- 6. 후기 품질 Before→After -->
<h2>6. 후기 품질 — "몇 건?"에서 "얼마나 깊은 건?"으로</h2>
<div class="ba-container">
  <div class="ba-box ba-before">
    <div class="ba-label" style="color:#94a3b8;">BEFORE</div>
    <div class="ba-title" style="color:#475569;">단순 건수</div>
    <div style="text-align:center;padding:18px;"><div style="font-size:44px;font-weight:800;color:#475569;">281건</div><div style="font-size:12px;color:#94a3b8;">"⭐ 좋아요" 1건 = "500자 서사" 1건<br><strong style="color:#475569;">같은 1건으로 취급</strong></div></div>
  </div>
  <div class="ba-vs">→</div>
  <div class="ba-box ba-after">
    <div class="ba-label" style="color:var(--primary);">AFTER</div>
    <div class="ba-title" style="color:var(--primary);">RQL 5단계 가중</div>
    <div style="margin:8px 0;">
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:80px;font-size:10px;text-align:right;color:var(--primary);font-weight:700;">Q5 서사형 ×2.0</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:25.6%;height:100%;background:var(--primary);border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;color:#fff;font-weight:600;">72건</div></div></div>
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:80px;font-size:10px;text-align:right;">Q4 분석형 ×1.5</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:29.5%;height:100%;background:var(--blue);border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;color:#fff;font-weight:600;">83건</div></div></div>
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:80px;font-size:10px;text-align:right;">Q3 경험형 ×1.0</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:15.7%;height:100%;background:var(--green);border-radius:3px;"></div></div><div style="font-size:9px;">44</div></div>
      <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:80px;font-size:10px;text-align:right;color:#94a3b8;">Q2 감상형 ×0.5</div><div style="flex:1;height:16px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:28.8%;height:100%;background:var(--orange);border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;color:#fff;font-weight:600;">81건</div></div></div>
    </div>
    <div style="padding:8px;background:#eef2ff;border-radius:6px;font-size:12px;color:var(--primary);"><strong>"Q4+Q5 깊은 후기 55% (155건) — 방탈출 체험이 긴 서사를 유도"</strong></div>
  </div>
</div>
<div style="padding:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;">
  <div style="font-size:12px;font-weight:700;color:var(--primary);margin-bottom:6px;">📊 RQL 등급별 실제 포스트</div>
  <div style="font-size:11px;line-height:1.7;">
    <div style="padding:5px 8px;background:#eef2ff;border-radius:6px;margin-bottom:4px;"><strong style="color:var(--primary);">Q5 서사형</strong> — "새로 중앙박물관 팝업 새로 소주 천년의 비법서 도난 사건..." Auth 88, 694자 → <strong>긴 서사+개인경험+디테일</strong></div>
    <div style="padding:5px 8px;background:#f1f5f9;border-radius:6px;"><strong style="color:#94a3b8;">Q2 감상형</strong> — 짧은 한줄 감상 또는 사진 위주 포스트 → <strong>분석 가치 낮음 (×0.5)</strong></div>
  </div>
</div>

<!-- 7. Sincerity Gate -->
<h2>7. Sincerity Gate — "281건"의 진짜 숫자</h2>
<div style="margin:14px 0;">
  <div style="padding:12px 18px;background:var(--light);border-radius:10px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;border:2px solid #e8e8e8;"><div><strong>Gate 1</strong> <span style="font-size:12px;">전체</span></div><div style="font-size:18px;font-weight:800;">281건 <span style="font-size:12px;color:var(--body);">긍정 50%</span></div></div>
  <div style="text-align:center;font-size:10px;color:var(--coral);padding:2px;">▼ 협찬 5건 제거</div>
  <div style="padding:12px 18px;background:#eef2ff;border-radius:10px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;border:2px solid var(--primary);"><div><strong style="color:var(--primary);">Gate 2</strong> <span style="font-size:12px;">자발적</span></div><div style="font-size:18px;font-weight:800;color:var(--primary);">276건 <span style="font-size:12px;">긍정 49% (-1%p)</span></div></div>
  <div style="text-align:center;font-size:10px;color:var(--coral);padding:2px;">▼ Auth 60 미만 72건 탈락</div>
  <div style="padding:12px 18px;background:var(--primary);border-radius:10px;display:flex;justify-content:space-between;align-items:center;color:#fff;"><div><strong>Gate 3</strong> <span style="font-size:12px;color:rgba(255,255,255,0.7);">진심</span></div><div style="font-size:18px;font-weight:800;">204건 <span style="font-size:12px;color:rgba(255,255,255,0.7);">긍정 38% (-12%p)</span></div></div>
</div>
<div class="insight"><strong>Gate 3 적용 시 긍정률 50%→38% (-12%p).</strong> 과장 긍정 77건 탈락. 이클립스(-13%p)와 거의 동일 → <strong>팝업 버즈의 ~25%가 과장 긍정이라는 일반 패턴.</strong></div>

<!-- 8. 이클립스 비교 -->
<h2>8. 이클립스 월드와 비교</h2>
<table><thead><tr><th>지표</th><th>새로중앙박물관</th><th>이클립스 월드</th><th>비교</th></tr></thead><tbody>
  <tr><td>운영 기간</td><td><strong>16일</strong></td><td>4일</td><td>4배</td></tr>
  <tr><td>수집 건수</td><td><strong>281건</strong></td><td>90건</td><td>3.1배</td></tr>
  <tr><td>긍정률 Gate 1→3</td><td>50%→<strong>38%</strong> (-12)</td><td>46%→33% (-13)</td><td>거의 동일</td></tr>
  <tr><td>Auth 평균</td><td>58.4</td><td>57.2</td><td>유사</td></tr>
  <tr><td>Freshness</td><td><strong style="color:var(--green);">43.1</strong></td><td>39.8</td><td>+3.3</td></tr>
  <tr><td style="color:var(--coral);">협찬 Auth</td><td style="color:var(--coral);"><strong>37.8</strong></td><td>47.6</td><td>-9.8</td></tr>
  <tr><td style="color:var(--coral);">Auth 시간 하락</td><td style="color:var(--coral);"><strong>-20점</strong></td><td>-5점</td><td>4배</td></tr>
  <tr><td>Q5 서사형</td><td><strong>72건 (26%)</strong></td><td>9건 (10%)</td><td>2.6배</td></tr>
</tbody></table>

<!-- 종합 Before→After 비교표 -->
<h2>종합: Before → After 비교표</h2>
<table style="font-size:13px;">
  <thead><tr><th style="width:120px;">분석 영역</th><th style="background:#64748b;">BEFORE (기존)</th><th>AFTER (RXR)</th><th style="width:80px;">차별화</th></tr></thead>
  <tbody>
    <tr><td style="font-weight:700;">버즈 규모</td><td>총 281건</td><td><strong style="color:var(--primary);">Gate 3 유효 204건 (과장 77건 탈락)</strong></td><td style="color:var(--coral);font-weight:700;">진실</td></tr>
    <tr><td style="font-weight:700;">감성</td><td>긍/중/부 3단계</td><td><strong style="color:var(--primary);">4단계 + Auth 58.4 + Clout 49.8</strong></td><td style="color:var(--primary);font-weight:700;">깊이 ×3</td></tr>
    <tr><td style="font-weight:700;">데이터 분류</td><td>건수만</td><td><strong style="color:var(--primary);">A~G 7단계 + Trust Score</strong></td><td style="color:var(--primary);font-weight:700;">정확도</td></tr>
    <tr><td style="font-weight:700;">협찬</td><td>있다/없다</td><td><strong style="color:var(--primary);">진심 스펙트럼 (Auth 10~57)</strong></td><td style="color:var(--primary);font-weight:700;">유일</td></tr>
    <tr><td style="font-weight:700;">리그램</td><td style="color:var(--coral);">구분 불가</td><td><strong style="color:var(--primary);">E등급 자동 태깅</strong></td><td style="color:var(--primary);font-weight:700;">유일</td></tr>
    <tr><td style="font-weight:700;">토픽</td><td>워드클라우드</td><td><strong style="color:var(--primary);">구조화 비중 + 시사점</strong></td><td style="color:var(--primary);font-weight:700;">액셔너블</td></tr>
    <tr><td style="font-weight:700;">심리</td><td style="color:var(--coral);">불가능</td><td><strong style="color:var(--primary);">Auth/Clout/Fresh 시계열</strong></td><td style="color:var(--coral);font-weight:700;">유일</td></tr>
    <tr><td style="font-weight:700;">후기 품질</td><td>1건=1건</td><td><strong style="color:var(--primary);">RQL 5단계 (Q5 72건=26%)</strong></td><td style="color:var(--primary);font-weight:700;">유일</td></tr>
    <tr><td style="font-weight:700;">시계열</td><td>버즈량만</td><td><strong style="color:var(--primary);">Auth -20점 급락 감지</strong></td><td style="color:var(--primary);font-weight:700;">유일</td></tr>
  </tbody>
</table>

<!-- BOTTOM LINE -->
<div style="margin:28px 0;padding:20px;background:var(--primary-pale);border-radius:14px;text-align:center;">
  <div style="font-size:12px;color:var(--body);margin-bottom:6px;font-family:'Poppins';letter-spacing:2px;">BOTTOM LINE</div>
  <div style="font-size:17px;font-weight:800;color:var(--primary);line-height:1.6;">
    기존: "281건, 긍정 50%"<br>
    RXR: "유효 204건, 진심 긍정 38%, Auth -20점 급락,<br>방탈출(7%)이 소주(68%)에 묻힘 — 체험 화제화 전략 필요"
  </div>
</div>

<!-- 부록 -->
<h2>부록: Gate 3 유효 Raw Data ({len(gate3)}건)</h2>
<p style="font-size:11px;color:var(--body);margin-bottom:6px;">Auth 60+, 자발적 포스트만.</p>
<table style="font-size:10px;">
<thead><tr style="background:var(--primary);"><th style="padding:3px;color:#fff;text-align:center;width:20px;">#</th><th style="padding:3px;color:#fff;width:60px;">날짜</th><th style="padding:3px;color:#fff;width:30px;">감성</th><th style="padding:3px;color:#fff;width:28px;">Auth</th><th style="padding:3px;color:#fff;width:28px;">Clout</th><th style="padding:3px;color:#fff;width:32px;">Fresh</th><th style="padding:3px;color:#fff;width:52px;">RQL</th><th style="padding:3px;color:#fff;width:52px;">토픽</th><th style="padding:3px;color:#fff;width:42px;">기간</th><th style="padding:3px;color:#fff;">제목</th><th style="padding:3px;color:#fff;width:68px;">블로거</th></tr></thead>
<tbody>
{make_appendix()}</tbody></table>
<div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;">
  <div class="card" style="padding:8px;text-align:center;"><div style="font-size:9px;color:var(--body);">감성</div><div style="font-size:10px;">긍정 <strong style="color:#059669;">{g3_sents.get('긍정',0)}</strong> · 혼합 <strong style="color:#6666FF;">{g3_sents.get('혼합',0)}</strong> · 중립 <strong>{g3_sents.get('중립',0)}</strong></div></div>
  <div class="card" style="padding:8px;text-align:center;"><div style="font-size:9px;color:var(--body);">Psyche</div><div style="font-size:10px;">Auth <strong style="color:var(--primary);">{g3_avg_auth:.1f}</strong> · Clout <strong>{g3_avg_clout:.1f}</strong></div></div>
  <div class="card" style="padding:8px;text-align:center;"><div style="font-size:9px;color:var(--body);">RQL</div><div style="font-size:10px;">Q5 <strong>{g3_rqls.get('Q5_서사형',0)}</strong> · Q4 <strong>{g3_rqls.get('Q4_분석형',0)}</strong> · Q3 <strong>{g3_rqls.get('Q3_경험형',0)}</strong></div></div>
  <div class="card" style="padding:8px;text-align:center;"><div style="font-size:9px;color:var(--body);">총</div><div style="font-size:14px;font-weight:800;color:var(--primary);">{len(gate3)}건</div></div>
</div>

<div class="footer">Project RENT · R-lab · 2026 | RXR 2-Layer + Sincerity Gate | 새로중앙박물관</div>

<!-- PDF Panel -->
<div class="pdf-panel" id="pdfPanel"><button class="pdf-panel-toggle" onclick="document.getElementById('pdfBody').classList.toggle('open')"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>PDF</button><div class="pdf-panel-body" id="pdfBody"><div style="font-size:12px;font-weight:700;color:#1e293b;margin-bottom:12px;text-align:center;">PDF 출력</div><div class="pdf-orient-group"><button class="pdf-orient-btn" id="btnL" onclick="setOrient('landscape')">가로</button><button class="pdf-orient-btn active" id="btnP" onclick="setOrient('portrait')">세로</button></div><button class="pdf-print-btn" onclick="window.print()">출력하기</button></div></div>
<script>document.addEventListener('click',function(e){{var p=document.getElementById('pdfPanel');if(p&&!p.contains(e.target))document.getElementById('pdfBody').classList.remove('open');}});function setOrient(o){{var s=document.getElementById('pageOrientStyle'),bL=document.getElementById('btnL'),bP=document.getElementById('btnP');if(o==='landscape'){{s.textContent='@media print{{@page{{size:A4 landscape;margin:8mm;}}}}';bL.classList.add('active');bP.classList.remove('active');}}else{{s.textContent='';bP.classList.add('active');bL.classList.remove('active');}}}}</script>
</body></html>"""

with open(r'C:\Users\insig\do-better-workspace\30-knowledge\saero-popup-rxr-sns-report.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('전체 리포트 생성 완료!')
