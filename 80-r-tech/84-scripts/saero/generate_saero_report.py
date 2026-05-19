"""새로중앙박물관 RXR SNS 분석 HTML 리포트 생성"""
import json, sys
from collections import Counter

sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

with open(r'C:\Users\insig\do-better-workspace\30-knowledge\saero-popup-2layer-results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

gate3 = sorted([d for d in data if d['authenticity'] >= 60 and not d['is_sponsored']], key=lambda x: -x['authenticity'])
spon = [d for d in data if d['is_sponsored']]

# Gate 3 부록 행
appendix_rows = ""
for i, d in enumerate(gate3):
    title = d['title'][:55].replace('&', '&amp;').replace('<', '&lt;')
    date = d['date']
    df = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    a, c, f_ = d['authenticity'], d['clout'], d['freshness_index']
    s, rql, topic = d['sentiment'], d['rql'].replace('_', ' '), d['primary_topic']
    period = d.get('period', '')[:6]
    link, blogger = d.get('link', ''), d.get('blogger', '')[:14].replace('&', '&amp;')
    sc = '#059669' if s == '긍정' else '#dc2626' if s == '부정' else '#6666FF' if s == '혼합' else '#94a3b8'
    ac = '#059669' if a >= 75 else '#6666FF'
    bg = '#f0fdf4' if i % 2 == 0 else '#fff'
    appendix_rows += f'<tr style="background:{bg};"><td style="padding:3px 4px;text-align:center;">{i+1}</td><td style="padding:3px 4px;">{df}</td><td style="padding:3px 4px;color:{sc};font-weight:600;">{s}</td><td style="padding:3px 4px;text-align:center;"><strong style="color:{ac};">{a}</strong></td><td style="padding:3px 4px;text-align:center;">{c}</td><td style="padding:3px 4px;text-align:center;">{f_}</td><td style="padding:3px 4px;">{rql}</td><td style="padding:3px 4px;">{topic}</td><td style="padding:3px 4px;">{period}</td><td style="padding:3px 4px;"><a href="{link}" target="_blank" style="color:#6666FF;text-decoration:none;">{title}</a></td><td style="padding:3px 4px;color:#94a3b8;">{blogger}</td></tr>\n'

g3_sents = Counter(d['sentiment'] for d in gate3)
g3_rqls = Counter(d['rql'] for d in gate3)
g3_avg_auth = sum(d['authenticity'] for d in gate3) / len(gate3)
g3_avg_clout = sum(d['clout'] for d in gate3) / len(gate3)

# 날짜별 바 차트
date_data = [
    ('03/07', 1), ('03/08', 1), ('03/09', 2), ('03/10', 3), ('03/11', 6), ('03/12', 4),
    ('03/13', 2), ('03/14', 4), ('03/15', 6), ('03/16', 4), ('03/17', 1), ('03/18', 4),
    ('03/19', 3), ('03/20', 4), ('03/21', 8), ('03/22', 12), ('03/23', 15), ('03/24', 13),
    ('03/25', 21), ('03/26', 20), ('03/27', 13), ('03/28', 18), ('03/29', 15), ('03/30', 10),
    ('03/31', 20), ('04/01', 8), ('04/02', 15), ('04/03', 10), ('04/04', 18), ('04/05', 8),
    ('04/06', 8), ('04/07', 4),
]
max_cnt = 21
date_bars = ""
for dt, cnt in date_data:
    pct = cnt / max_cnt * 100
    m, d_num = dt.split('/')
    raw = f"202603{d_num}" if m == '03' else f"202604{d_num}"
    if raw < '20260321':
        color, note = 'var(--orange)', ('이벤트 전' if dt == '03/07' else '')
    elif raw <= '20260405':
        color = 'var(--primary)'
        note = '★ 시작' if dt == '03/21' else ('★ 피크' if cnt == 21 else '')
    else:
        color, note = '#94a3b8', ('이벤트 후' if dt == '04/06' else '')
    ns = f'color:{color};font-weight:700;' if note else 'color:#94a3b8;'
    bt = str(cnt) if cnt >= 6 else ''
    date_bars += f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:2px;"><div style="width:40px;font-size:9px;color:var(--body);text-align:right;">{dt}</div><div style="flex:1;height:15px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:3px;display:flex;align-items:center;padding-left:4px;font-size:8px;font-weight:600;color:#fff;">{bt}</div></div><div style="width:20px;font-size:9px;font-weight:600;">{cnt}</div><div style="width:65px;font-size:8px;{ns}">{note}</div></div>\n'
    if dt == '03/20':
        date_bars += '<div style="height:3px;border-bottom:2px solid var(--primary);margin:2px 0;"></div>\n'
    elif dt == '04/05':
        date_bars += '<div style="height:3px;border-bottom:2px dashed #ddd;margin:2px 0;"></div>\n'

# 협찬 상세
spon_details = ""
for d in sorted(spon, key=lambda x: -x['authenticity']):
    a = d['authenticity']
    ac = '#059669' if a >= 55 else '#f59e0b' if a >= 30 else '#dc2626'
    bg = '#ecfdf5' if a >= 55 else '#fef3c7' if a >= 30 else '#fee2e2'
    spon_details += f'<div style="padding:5px 8px;background:{bg};border-radius:6px;margin-bottom:3px;font-size:11px;"><strong style="color:{ac};">Auth {a}</strong> — "{d["title"][:42]}" ({d["date"][4:6]}/{d["date"][6:]}) · 느낌표 {d["exclamation"]}개</div>\n'

# HTML 읽기 — 이클립스 before-after 템플릿 참고하여 생성
html_path = r'C:\Users\insig\do-better-workspace\30-knowledge\saero-popup-rxr-sns-report.html'

# CSS는 이클립스 리포트와 동일한 구조
html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>새로중앙박물관 — RXR SNS 분석</title>
<style>
  @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable.css');
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
    .card,.grid2,.grid3,.insight,.gauge-row,table{{break-inside:avoid!important;page-break-inside:avoid!important;}}
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
  .pdf-print-btn{{width:100%;padding:10px;background:var(--grad);color:#fff;border:none;border-radius:10px;font-size:13px;font-weight:600;cursor:pointer;font-family:'Pretendard Variable',sans-serif;}}
</style>
<style id="pageOrientStyle"></style>
</head>
<body>

<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
  <span style="background:var(--grad);color:#fff;padding:4px 14px;border-radius:6px;font-family:'Poppins';font-size:11px;font-weight:600;letter-spacing:1px;">RXR SNS ANALYSIS</span>
</div>
<h1>새로중앙박물관 — 천년의 비법서 도난 사건</h1>
<div class="sub">RXR 2-Layer + Sincerity Gate 분석 | 네이버 블로그 281건 | Project RENT · R-lab</div>

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
        <div style="padding:4px 0;"><strong style="color:var(--primary);">핵심 질문:</strong> 새로중앙박물관 SNS 반응 중 "진짜 반응"은?</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">데이터:</strong> 네이버 블로그 281건 (정밀 필터)</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">분석:</strong> Content + Psyche + Sincerity Gate 3단계</div>
        <div style="padding:4px 0;border-top:1px solid #e8e8e8;"><strong style="color:var(--primary);">비교:</strong> 이클립스 월드 팝업과 교차 비교</div>
      </div>
    </div>
  </div>
</div>

<!-- 데이터 개요 -->
<h2>0. 데이터 수집 개요</h2>
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:12px 0;">
  <div class="card" style="text-align:center;border-top:3px solid var(--primary);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--primary);">281</div><div style="font-size:10px;color:var(--body);">네이버 블로그</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--green);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--green);">224</div><div style="font-size:10px;color:var(--body);">이벤트 기간</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--orange);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--orange);">45</div><div style="font-size:10px;color:var(--body);">이벤트 전</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--pink);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--pink);">204</div><div style="font-size:10px;color:var(--body);">Gate 3 유효</div></div>
  <div class="card" style="text-align:center;border-top:3px solid var(--blue);padding:12px;"><div style="font-size:24px;font-weight:800;color:var(--blue);">16일</div><div style="font-size:10px;color:var(--body);">운영 기간</div></div>
</div>

<h3>날짜별 버즈 분포</h3>
{date_bars}

<div class="grid2" style="margin-top:12px;">
  <div>
    <h3>기간별 비교</h3>
    <table><thead><tr><th>기간</th><th>건수</th><th>일평균</th><th>비율</th></tr></thead><tbody>
      <tr><td style="color:var(--orange);font-weight:700;">이벤트 전</td><td><strong>45</strong></td><td>3.2</td><td>16%</td></tr>
      <tr><td style="color:var(--primary);font-weight:700;">이벤트 기간</td><td><strong>224</strong></td><td>14.0</td><td>80%</td></tr>
      <tr><td style="color:#94a3b8;">이벤트 후</td><td><strong>12</strong></td><td>6.0</td><td>4%</td></tr>
      <tr style="background:var(--primary-pale);"><td style="font-weight:700;">합계</td><td style="font-weight:700;color:var(--primary);">281</td><td></td><td>100%</td></tr>
    </tbody></table>
  </div>
  <div>
    <h3>핵심 패턴</h3>
    <div style="font-size:12px;line-height:1.7;">
      <div style="padding:5px 8px;background:var(--light);border-radius:6px;margin-bottom:4px;border-left:3px solid var(--primary);"><strong style="color:var(--primary);">이벤트 기간 80%</strong> — 실제 체험 후기 대부분 (이클립스 15%와 대조)</div>
      <div style="padding:5px 8px;background:var(--light);border-radius:6px;margin-bottom:4px;border-left:3px solid var(--orange);"><strong style="color:var(--orange);">사전 버즈 16%</strong> — 신제품 출시 없어 사전 화제 적음</div>
      <div style="padding:5px 8px;background:var(--light);border-radius:6px;border-left:3px solid var(--green);"><strong style="color:var(--green);">3/25 피크 21건</strong> — 주말 방문 후기 폭발</div>
    </div>
  </div>
</div>

<!-- Sincerity Gate -->
<h2>1. Sincerity Gate</h2>
<div style="margin:14px 0;">
  <div style="padding:12px 18px;background:var(--light);border-radius:10px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;border:2px solid #e8e8e8;"><div><strong>Gate 1</strong> <span style="font-size:12px;color:var(--body);">전체</span></div><div style="font-size:18px;font-weight:800;">281건 <span style="font-size:12px;color:var(--body);">긍정 50%</span></div></div>
  <div style="text-align:center;font-size:10px;color:var(--coral);padding:2px;">▼ 협찬 제거</div>
  <div style="padding:12px 18px;background:#eef2ff;border-radius:10px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;border:2px solid var(--primary);"><div><strong style="color:var(--primary);">Gate 2</strong> <span style="font-size:12px;">자발적</span></div><div style="font-size:18px;font-weight:800;color:var(--primary);">276건 <span style="font-size:12px;">긍정 49%</span></div></div>
  <div style="text-align:center;font-size:10px;color:var(--coral);padding:2px;">▼ Auth 60 미만 탈락</div>
  <div style="padding:12px 18px;background:var(--primary);border-radius:10px;display:flex;justify-content:space-between;align-items:center;color:#fff;"><div><strong>Gate 3</strong> <span style="font-size:12px;color:rgba(255,255,255,0.7);">진심</span></div><div style="font-size:18px;font-weight:800;">204건 <span style="font-size:12px;color:rgba(255,255,255,0.7);">긍정 38% (-12%p)</span></div></div>
</div>
<div class="insight"><strong>Gate 3 적용 시 긍정률 50%→38% (-12%p).</strong> 이클립스(-13%p)와 거의 동일 → <strong>팝업 버즈의 ~25%가 과장 긍정이라는 일반 패턴.</strong></div>

<!-- Psyche Layer -->
<h2>2. Psyche Layer</h2>
<div class="gauge-row"><div class="gauge-label" style="color:var(--primary);">Authenticity</div><div class="gauge-track"><div class="gauge-fill" style="width:58.4%;background:var(--primary);">58.4</div></div><div class="gauge-val" style="color:var(--primary);">58.4</div></div>
<div class="gauge-row"><div class="gauge-label" style="color:var(--green);">Clout</div><div class="gauge-track"><div class="gauge-fill" style="width:49.8%;background:var(--green);">49.8</div></div><div class="gauge-val" style="color:var(--green);">49.8</div></div>
<div class="gauge-row"><div class="gauge-label" style="color:var(--orange);">Freshness</div><div class="gauge-track"><div class="gauge-fill" style="width:43.1%;background:var(--orange);">43.1</div></div><div class="gauge-val" style="color:var(--orange);">43.1</div></div>

<h3>기간별 심리 변화</h3>
<table><thead><tr><th>기간</th><th>N</th><th>Auth</th><th>Clout</th><th>Fresh</th><th>해석</th></tr></thead><tbody>
  <tr><td style="color:var(--orange);font-weight:700;">이벤트 전</td><td>45</td><td><strong style="color:var(--green);">66.4</strong></td><td>49.1</td><td>41.9</td><td style="font-size:11px;">기대감, 솔직</td></tr>
  <tr style="background:#eef2ff;"><td style="color:var(--primary);font-weight:700;">이벤트 기간</td><td>224</td><td>57.4</td><td>49.9</td><td style="color:var(--green);font-weight:700;">43.1</td><td style="font-size:11px;">경험, Fresh↑</td></tr>
  <tr><td style="color:#94a3b8;font-weight:700;">이벤트 후</td><td>12</td><td><strong style="color:var(--coral);">46.2</strong></td><td>50.8</td><td>46.2</td><td style="font-size:11px;color:var(--coral);font-weight:700;">Auth -20점!</td></tr>
</tbody></table>
<div class="insight-warn insight"><strong>Auth 이벤트전 66.4 → 이벤트후 46.2 (-20점) 급락.</strong> 이클립스(-5점)보다 4배 급격. 16일 장기 운영 → <strong>후반부 후기의 기억 과장/미화가 심각</strong>.</div>

<!-- 협찬 -->
<h2>3. 협찬 vs 자발적</h2>
<div style="display:grid;grid-template-columns:1fr 40px 1fr;gap:0;align-items:stretch;margin:12px 0;">
  <div style="padding:16px;background:#ecfdf5;border:2px solid var(--green);border-radius:14px;text-align:center;"><div style="font-size:11px;font-weight:700;color:var(--green);">자발적</div><div style="font-size:28px;font-weight:800;color:var(--green);">276건</div><div style="margin-top:6px;">Auth <strong>58.7</strong></div></div>
  <div style="display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:900;color:#94a3b8;">VS</div>
  <div style="padding:16px;background:#fef3c7;border:2px solid var(--orange);border-radius:14px;text-align:center;"><div style="font-size:11px;font-weight:700;color:var(--orange);">협찬</div><div style="font-size:28px;font-weight:800;color:var(--orange);">5건</div><div style="margin-top:6px;">Auth <strong style="color:var(--coral);">37.8</strong> <span style="font-size:10px;color:var(--coral);">(-20.9!)</span></div></div>
</div>
<div style="padding:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;margin-bottom:12px;">
  <div style="font-size:12px;font-weight:700;color:var(--primary);margin-bottom:6px;">📊 협찬 5건 상세</div>
  {spon_details}
</div>

<!-- 토픽 -->
<h2>4. Content Layer — 토픽</h2>
<div style="margin:10px 0;">
  <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:85px;font-size:11px;text-align:right;font-weight:600;color:var(--primary);">제품/소주 68%</div><div style="flex:1;height:18px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:68%;height:100%;background:var(--primary);border-radius:3px;display:flex;align-items:center;padding-left:5px;font-size:8px;font-weight:600;color:#fff;">190건</div></div></div>
  <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:85px;font-size:11px;text-align:right;">공간/분위기</div><div style="flex:1;height:18px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:15.3%;height:100%;background:var(--green);border-radius:3px;display:flex;align-items:center;padding-left:5px;font-size:8px;font-weight:600;color:#fff;">43건</div></div></div>
  <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:85px;font-size:11px;text-align:right;">웨이팅/예약</div><div style="flex:1;height:18px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:7.8%;height:100%;background:var(--orange);border-radius:3px;"></div></div><div style="font-size:10px;">22</div></div>
  <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px;"><div style="width:85px;font-size:11px;text-align:right;">방탈출/미션</div><div style="flex:1;height:18px;background:#f0f0f0;border-radius:3px;overflow:hidden;"><div style="width:7.5%;height:100%;background:var(--pink);border-radius:3px;"></div></div><div style="font-size:10px;">21</div></div>
</div>
<div class="insight"><strong>이클립스와 동일:</strong> 제품(68%) 압도, 방탈출(7%) 부차적. 팝업의 핵심 컨셉(방탈출)이 버즈에서 묻힘.</div>

<!-- 이클립스 비교 -->
<h2>5. 이클립스 월드와 비교</h2>
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
<div class="insight"><strong>교차 발견:</strong> Gate 하락폭(-12~13%p) 두 팝업 동일 → <strong>"SNS 버즈의 ~25%가 과장 긍정"이라는 일반 법칙.</strong> 새로는 서사형 후기 2.6배 → 방탈출 체험이 깊은 후기를 유도.</div>

<!-- BOTTOM LINE -->
<div style="margin:28px 0;padding:20px;background:var(--primary-pale);border-radius:14px;text-align:center;">
  <div style="font-size:12px;color:var(--body);margin-bottom:6px;font-family:'Poppins';letter-spacing:2px;">BOTTOM LINE</div>
  <div style="font-size:17px;font-weight:800;color:var(--primary);line-height:1.6;">281건 중 Gate 3 통과 204건 (73%), 긍정 50%→38%<br>Auth 시간 급락(-20점) = 장기 팝업의 후기 신뢰도 감소<br>방탈출 체험(7%)이 제품(68%)에 묻힘 — 체험 화제화 필요</div>
</div>

<!-- 부록 -->
<h2>부록: Gate 3 유효 Raw Data ({len(gate3)}건)</h2>
<p style="font-size:11px;color:var(--body);margin-bottom:6px;">Auth 60+, 자발적 포스트만.</p>
<table style="font-size:10px;">
<thead><tr style="background:var(--primary);"><th style="padding:3px;color:#fff;text-align:center;width:20px;">#</th><th style="padding:3px;color:#fff;width:60px;">날짜</th><th style="padding:3px;color:#fff;width:30px;">감성</th><th style="padding:3px;color:#fff;width:28px;">Auth</th><th style="padding:3px;color:#fff;width:28px;">Clout</th><th style="padding:3px;color:#fff;width:32px;">Fresh</th><th style="padding:3px;color:#fff;width:52px;">RQL</th><th style="padding:3px;color:#fff;width:52px;">토픽</th><th style="padding:3px;color:#fff;width:42px;">기간</th><th style="padding:3px;color:#fff;">제목</th><th style="padding:3px;color:#fff;width:68px;">블로거</th></tr></thead>
<tbody>
{appendix_rows}</tbody></table>

<div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;">
  <div class="card" style="padding:8px;text-align:center;"><div style="font-size:9px;color:var(--body);">감성</div><div style="font-size:10px;">긍정 <strong style="color:#059669;">{g3_sents.get('긍정',0)}</strong> · 혼합 <strong style="color:#6666FF;">{g3_sents.get('혼합',0)}</strong> · 중립 <strong>{g3_sents.get('중립',0)}</strong></div></div>
  <div class="card" style="padding:8px;text-align:center;"><div style="font-size:9px;color:var(--body);">Psyche</div><div style="font-size:10px;">Auth <strong style="color:var(--primary);">{g3_avg_auth:.1f}</strong> · Clout <strong>{g3_avg_clout:.1f}</strong></div></div>
  <div class="card" style="padding:8px;text-align:center;"><div style="font-size:9px;color:var(--body);">RQL</div><div style="font-size:10px;">Q5 <strong>{g3_rqls.get('Q5_서사형',0)}</strong> · Q4 <strong>{g3_rqls.get('Q4_분석형',0)}</strong> · Q3 <strong>{g3_rqls.get('Q3_경험형',0)}</strong></div></div>
  <div class="card" style="padding:8px;text-align:center;"><div style="font-size:9px;color:var(--body);">총</div><div style="font-size:14px;font-weight:800;color:var(--primary);">{len(gate3)}건</div></div>
</div>

<div class="footer">Project RENT · R-lab · 2026 | RXR 2-Layer + Sincerity Gate | 새로중앙박물관</div>

<!-- PDF Panel -->
<div class="pdf-panel" id="pdfPanel">
  <button class="pdf-panel-toggle" onclick="document.getElementById('pdfBody').classList.toggle('open')">
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>PDF</button>
  <div class="pdf-panel-body" id="pdfBody">
    <div style="font-size:12px;font-weight:700;color:#1e293b;margin-bottom:12px;text-align:center;">PDF 출력</div>
    <div class="pdf-orient-group"><button class="pdf-orient-btn" id="btnL" onclick="setOrient('landscape')">가로</button><button class="pdf-orient-btn active" id="btnP" onclick="setOrient('portrait')">세로</button></div>
    <button class="pdf-print-btn" onclick="window.print()">출력하기</button>
  </div>
</div>
<script>
document.addEventListener('click',function(e){{var p=document.getElementById('pdfPanel');if(p&&!p.contains(e.target))document.getElementById('pdfBody').classList.remove('open');}});
function setOrient(o){{var s=document.getElementById('pageOrientStyle'),bL=document.getElementById('btnL'),bP=document.getElementById('btnP');if(o==='landscape'){{s.textContent='@media print{{@page{{size:A4 landscape;margin:8mm;}}}}';bL.classList.add('active');bP.classList.remove('active');}}else{{s.textContent='';bP.classList.add('active');bL.classList.remove('active');}}}}
</script>
</body></html>"""

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)
print(f'HTML 리포트 생성 완료: {html_path}')
