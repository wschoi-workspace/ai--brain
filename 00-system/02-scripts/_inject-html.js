async (page) => {
  // HTML을 base64로 인코딩하여 data URI로 로드
  // setContent에 전체 HTML 문자열을 직접 전달
  const htmlContent = String.raw`<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>컨셉 3안 아이디에이션 심화 비교 | 글로벌K존 × 유니원</title>
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --primary: #6C5CE7; --primary-dark: #5A4BD1; --primary-light: #A29BFE;
    --primary-subtle: #EDE9FE; --black: #1A1A2E; --dark-gray: #4A4A68;
    --mid-gray: #7F7F9E; --light-gray: #E8E8F0; --off-white: #F7F7FB;
    --white: #FFFFFF; --success: #00B894; --warning: #FDCB6E;
    --danger: #E17055; --info: #74B9FF;
  }
  body { font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, sans-serif; font-size: 15px; line-height: 1.6; color: var(--black); background: var(--off-white); max-width: 1200px; margin: 0 auto; padding: 0 24px 80px; }
  .hero { background: var(--black); color: var(--white); border-radius: 0 0 24px 24px; padding: 64px 56px 56px; margin: 0 -24px 48px; position: relative; overflow: hidden; }
  .hero::before { content: ''; position: absolute; top: -80px; right: -80px; width: 400px; height: 400px; background: radial-gradient(circle, rgba(108,92,231,0.25) 0%, transparent 70%); pointer-events: none; }
  .hero-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(108,92,231,0.2); border: 1px solid rgba(108,92,231,0.4); color: var(--primary-light); font-size: 12px; font-weight: 500; padding: 5px 14px; border-radius: 20px; margin-bottom: 20px; letter-spacing: 0.03em; }
  .hero h1 { font-size: 36px; font-weight: 700; line-height: 1.2; margin-bottom: 16px; }
  .hero-conclusion { font-size: 16px; color: var(--primary-light); font-weight: 500; margin-bottom: 48px; padding: 14px 20px; background: rgba(108,92,231,0.15); border-left: 3px solid var(--primary); border-radius: 0 8px 8px 0; max-width: 680px; }
  .hero-gauges { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; max-width: 680px; }
  .gauge-card { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 24px 20px; text-align: center; }
  .gauge-card.highlight { background: rgba(108,92,231,0.2); border-color: rgba(108,92,231,0.5); }
  .gauge-ring { position: relative; width: 80px; height: 80px; margin: 0 auto 14px; }
  .gauge-ring svg { transform: rotate(-90deg); }
  .gauge-ring .track { fill: none; stroke: rgba(255,255,255,0.1); stroke-width: 8; }
  .gauge-ring .fill-a { fill: none; stroke: var(--mid-gray); stroke-width: 8; stroke-linecap: round; stroke-dasharray: 188; }
  .gauge-ring .fill-b { fill: none; stroke: var(--primary); stroke-width: 8; stroke-linecap: round; stroke-dasharray: 188; }
  .gauge-ring .fill-c { fill: none; stroke: var(--warning); stroke-width: 8; stroke-linecap: round; stroke-dasharray: 188; }
  .gauge-pct { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 14px; font-weight: 700; color: var(--white); }
  .gauge-label { font-size: 13px; font-weight: 600; color: var(--white); margin-bottom: 4px; }
  .gauge-sub { font-size: 11px; color: rgba(255,255,255,0.5); }
  .hero-date { margin-top: 40px; font-size: 12px; color: rgba(255,255,255,0.35); letter-spacing: 0.05em; }
  .section-header { margin-bottom: 28px; }
  .section-tag { display: inline-block; background: var(--primary-subtle); color: var(--primary); font-size: 11px; font-weight: 600; padding: 4px 12px; border-radius: 6px; letter-spacing: 0.04em; margin-bottom: 10px; text-transform: uppercase; }
  .section-title { font-size: 24px; font-weight: 700; color: var(--black); }
  .section-sub { font-size: 14px; color: var(--dark-gray); margin-top: 6px; }
  .card { background: var(--white); border: 1px solid var(--light-gray); border-radius: 16px; padding: 28px; box-shadow: 0 2px 8px rgba(108,92,231,0.06); }
  .section-block { margin-bottom: 48px; }
  .compare-table { width: 100%; border-collapse: collapse; font-size: 14px; }
  .compare-table th { background: var(--off-white); color: var(--dark-gray); font-weight: 600; padding: 12px 16px; text-align: left; border-bottom: 2px solid var(--light-gray); font-size: 13px; }
  .compare-table th.col-b { background: var(--primary-subtle); color: var(--primary); }
  .compare-table td { padding: 11px 16px; border-bottom: 1px solid var(--light-gray); vertical-align: middle; }
  .compare-table tr:last-child td { border-bottom: none; }
  .compare-table td.col-b { background: rgba(108,92,231,0.03); font-weight: 500; }
  .compare-table .row-label { font-weight: 600; color: var(--black); }
  .compare-table .total-row td { background: var(--off-white); font-weight: 700; border-top: 2px solid var(--light-gray); }
  .compare-table .total-row td.col-b { background: var(--primary-subtle); color: var(--primary); }
  .stars { color: var(--warning); letter-spacing: -1px; }
  .stars.purple { color: var(--primary); }
  .insight-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-top: 20px; }
  .insight-card { border-radius: 12px; padding: 18px 20px; border: 1px solid var(--light-gray); }
  .insight-card.ic-a { border-left: 4px solid var(--mid-gray); background: var(--off-white); }
  .insight-card.ic-b { border-left: 4px solid var(--primary); background: var(--primary-subtle); }
  .insight-card.ic-c { border-left: 4px solid var(--info); background: #EEF5FF; }
  .insight-card-label { font-size: 11px; font-weight: 700; letter-spacing: 0.06em; margin-bottom: 8px; text-transform: uppercase; }
  .ic-a .insight-card-label { color: var(--mid-gray); }
  .ic-b .insight-card-label { color: var(--primary); }
  .ic-c .insight-card-label { color: #4A90E2; }
  .insight-card-text { font-size: 13px; font-weight: 600; color: var(--black); line-height: 1.4; }
  .visitor-bar-wrap { margin-top: 6px; }
  .visitor-bar-label { font-size: 11px; color: var(--dark-gray); margin-bottom: 4px; }
  .visitor-bar-track { height: 6px; background: var(--light-gray); border-radius: 3px; overflow: hidden; }
  .visitor-bar-fill { height: 100%; border-radius: 3px; }
  .omo-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 24px; }
  .omo-card { border-radius: 14px; padding: 22px 20px; border: 1px solid var(--light-gray); }
  .omo-card.omo-a { background: var(--off-white); }
  .omo-card.omo-b { background: var(--primary-subtle); border-color: rgba(108,92,231,0.2); }
  .omo-card.omo-c { background: #EEF5FF; border-color: rgba(74,144,226,0.2); }
  .omo-card-title { font-size: 13px; font-weight: 700; margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
  .omo-a .omo-card-title { color: var(--dark-gray); }
  .omo-b .omo-card-title { color: var(--primary); }
  .omo-c .omo-card-title { color: #4A90E2; }
  .omo-type-badge { font-size: 10px; padding: 2px 8px; border-radius: 10px; font-weight: 600; }
  .omo-a .omo-type-badge { background: var(--light-gray); color: var(--mid-gray); }
  .omo-b .omo-type-badge { background: var(--primary); color: var(--white); }
  .omo-c .omo-type-badge { background: #4A90E2; color: var(--white); }
  .omo-flow { display: flex; flex-direction: column; gap: 6px; }
  .omo-step { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--dark-gray); }
  .omo-step-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
  .omo-a .omo-step-dot { background: var(--mid-gray); }
  .omo-b .omo-step-dot { background: var(--primary); }
  .omo-c .omo-step-dot { background: #4A90E2; }
  .omo-arrow { font-size: 10px; color: var(--mid-gray); padding-left: 14px; }
  .score-chart { display: flex; flex-direction: column; gap: 20px; }
  .score-row-label { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px; }
  .score-row-name { font-size: 13px; font-weight: 600; color: var(--black); }
  .score-row-max { font-size: 11px; color: var(--mid-gray); }
  .score-bars { display: flex; flex-direction: column; gap: 5px; }
  .score-bar-row { display: flex; align-items: center; gap: 10px; }
  .score-bar-tag { font-size: 11px; font-weight: 600; width: 24px; flex-shrink: 0; text-align: right; }
  .score-bar-track { flex: 1; height: 22px; background: var(--off-white); border-radius: 4px; overflow: hidden; }
  .score-bar-fill { height: 100%; border-radius: 4px; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; font-size: 11px; font-weight: 600; color: var(--white); min-width: 32px; }
  .fill-a { background: var(--mid-gray); }
  .fill-b { background: var(--primary); }
  .fill-b.best { background: linear-gradient(90deg, var(--primary), var(--primary-dark)); box-shadow: 0 0 12px rgba(108,92,231,0.4); }
  .fill-c { background: var(--info); }
  .moat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 24px; }
  .moat-card { border-radius: 14px; padding: 22px; text-align: center; border: 1px solid var(--light-gray); }
  .moat-card.moat-low { background: #FFF5F3; border-color: rgba(225,112,85,0.2); }
  .moat-card.moat-high { background: var(--primary-subtle); border-color: rgba(108,92,231,0.2); }
  .moat-card.moat-mid { background: #FFFAF0; border-color: rgba(253,203,110,0.3); }
  .moat-level { font-size: 22px; font-weight: 800; margin-bottom: 6px; }
  .moat-low .moat-level { color: var(--danger); }
  .moat-high .moat-level { color: var(--primary); }
  .moat-mid .moat-level { color: #D4920A; }
  .moat-label { font-size: 13px; font-weight: 700; margin-bottom: 12px; }
  .moat-low .moat-label { color: var(--danger); }
  .moat-high .moat-label { color: var(--primary); }
  .moat-mid .moat-label { color: #D4920A; }
  .moat-line-wrap { display: flex; flex-direction: column; gap: 4px; margin-bottom: 14px; }
  .moat-line { height: 4px; border-radius: 2px; }
  .moat-low .moat-line { background: var(--danger); opacity: 0.4; }
  .moat-high .moat-line { background: var(--primary); }
  .moat-mid .moat-line { background: var(--warning); }
  .moat-defense { font-size: 11px; color: var(--dark-gray); line-height: 1.5; }
  .moat-defense strong { display: block; font-size: 12px; font-weight: 600; margin-bottom: 4px; }
  .scatter-wrap { position: relative; background: var(--off-white); border-radius: 12px; padding: 24px; height: 300px; overflow: hidden; border: 1px solid var(--light-gray); }
  .scatter-axis-x { position: absolute; bottom: 48px; left: 60px; right: 40px; height: 1px; background: var(--light-gray); }
  .scatter-axis-y { position: absolute; left: 60px; top: 24px; bottom: 48px; width: 1px; background: var(--light-gray); }
  .scatter-label-x { position: absolute; bottom: 18px; right: 40px; font-size: 11px; color: var(--mid-gray); font-weight: 500; }
  .scatter-label-y { position: absolute; top: 24px; left: 10px; font-size: 11px; color: var(--mid-gray); font-weight: 500; writing-mode: vertical-rl; transform: rotate(180deg); }
  .scatter-dot { position: absolute; width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; color: var(--white); }
  .scatter-dot.dot-a { background: var(--mid-gray); }
  .scatter-dot.dot-b { background: var(--primary); box-shadow: 0 0 20px rgba(108,92,231,0.5); width: 56px; height: 56px; font-size: 14px; }
  .scatter-dot.dot-c { background: var(--warning); }
  .scatter-dot-label { position: absolute; font-size: 10px; color: var(--dark-gray); font-weight: 600; white-space: nowrap; }
  .scatter-star { position: absolute; font-size: 18px; color: var(--warning); }
  .hybrid-section { background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%); border-radius: 20px; padding: 44px 48px; color: var(--white); margin-bottom: 48px; }
  .hybrid-section .section-tag { background: rgba(255,255,255,0.15); color: var(--white); border: 1px solid rgba(255,255,255,0.2); }
  .hybrid-section .section-title { color: var(--white); font-size: 26px; }
  .hybrid-title-sub { font-size: 15px; color: rgba(255,255,255,0.7); margin-top: 8px; margin-bottom: 36px; }
  .structure-diagram { background: rgba(0,0,0,0.2); border-radius: 14px; padding: 28px 32px; margin-bottom: 32px; }
  .struct-row { display: flex; align-items: center; justify-content: center; gap: 0; margin-bottom: 4px; }
  .struct-box { background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; padding: 10px 18px; font-size: 13px; font-weight: 600; color: var(--white); text-align: center; min-width: 140px; }
  .struct-box .box-sub { font-size: 10px; font-weight: 400; color: rgba(255,255,255,0.65); margin-top: 2px; }
  .struct-arrow { font-size: 18px; color: rgba(255,255,255,0.5); padding: 0 10px; flex-shrink: 0; }
  .struct-gate { background: rgba(253,203,110,0.2); border: 1px dashed rgba(253,203,110,0.5); border-radius: 8px; padding: 8px 14px; font-size: 11px; color: var(--warning); font-weight: 600; }
  .struct-line-wrap { display: flex; justify-content: center; gap: 80px; margin: 4px 0; }
  .struct-line { width: 1px; height: 24px; background: rgba(255,255,255,0.3); }
  .struct-center-box { display: flex; justify-content: center; margin: 4px 0; }
  .struct-data-box { background: rgba(108,92,231,0.4); border: 1px solid rgba(255,255,255,0.4); border-radius: 10px; padding: 10px 24px; font-size: 13px; font-weight: 600; color: var(--white); text-align: center; }
  .struct-data-box .box-sub { font-size: 10px; font-weight: 400; color: rgba(255,255,255,0.65); margin-top: 2px; }
  .hybrid-sub-grids { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .hybrid-sub-card { background: rgba(255,255,255,0.1); border-radius: 12px; padding: 22px; }
  .hybrid-sub-card h4 { font-size: 13px; font-weight: 700; color: rgba(255,255,255,0.9); margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.15); }
  .hybrid-table { width: 100%; font-size: 12px; }
  .hybrid-table th { font-size: 10px; font-weight: 600; color: rgba(255,255,255,0.5); padding: 4px 8px 8px 0; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); text-transform: uppercase; letter-spacing: 0.04em; }
  .hybrid-table td { padding: 7px 8px 7px 0; border-bottom: 1px solid rgba(255,255,255,0.07); color: rgba(255,255,255,0.85); vertical-align: top; line-height: 1.4; }
  .hybrid-table tr:last-child td { border-bottom: none; }
  .hybrid-table td:first-child { font-weight: 500; color: var(--white); white-space: nowrap; }
  .checklist-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
  .checklist-item { background: var(--white); border: 1px solid var(--light-gray); border-radius: 12px; padding: 20px; position: relative; }
  .checklist-item.deadline { border-color: var(--primary); background: var(--primary-subtle); }
  .check-date { font-size: 22px; font-weight: 800; color: var(--primary); line-height: 1; margin-bottom: 6px; }
  .checklist-item.deadline .check-date { color: var(--primary-dark); }
  .check-task { font-size: 13px; font-weight: 600; color: var(--black); line-height: 1.4; }
  .check-dot { position: absolute; top: 20px; right: 20px; width: 8px; height: 8px; border-radius: 50%; background: var(--light-gray); }
  .checklist-item.deadline .check-dot { background: var(--primary); }
  .footer { text-align: center; padding: 28px 0 0; border-top: 1px solid var(--light-gray); font-size: 12px; color: var(--mid-gray); letter-spacing: 0.03em; }
  .footer strong { color: var(--primary); font-weight: 600; }
</style>
</head>
<body>
<section class="hero">
  <div class="hero-badge">RFP IDEATION ANALYSIS</div>
  <h1>컨셉 3안 아이디에이션 심화 비교</h1>
  <div class="hero-conclusion">최종 추천: <strong>B안(HANJI HOUSE × K-CITY) + Living Impact System 하이브리드</strong></div>
  <div class="hero-gauges">
    <div class="gauge-card">
      <div class="gauge-ring">
        <svg width="80" height="80" viewBox="0 0 80 80"><circle class="track" cx="40" cy="40" r="30"/><circle class="fill-a" cx="40" cy="40" r="30" style="stroke-dashoffset:calc(188 - 42)"/></svg>
        <div class="gauge-pct">22%</div>
      </div>
      <div class="gauge-label">A안</div>
      <div class="gauge-sub">수주확률 20–25%</div>
    </div>
    <div class="gauge-card highlight">
      <div class="gauge-ring">
        <svg width="80" height="80" viewBox="0 0 80 80"><circle class="track" cx="40" cy="40" r="30"/><circle class="fill-b" cx="40" cy="40" r="30" style="stroke-dashoffset:calc(188 - 85)"/></svg>
        <div class="gauge-pct">45%</div>
      </div>
      <div class="gauge-label">B안 ★ 추천</div>
      <div class="gauge-sub">수주확률 40–50%</div>
    </div>
    <div class="gauge-card">
      <div class="gauge-ring">
        <svg width="80" height="80" viewBox="0 0 80 80"><circle class="track" cx="40" cy="40" r="30"/><circle class="fill-c" cx="40" cy="40" r="30" style="stroke-dashoffset:calc(188 - 33)"/></svg>
        <div class="gauge-pct">18%</div>
      </div>
      <div class="gauge-label">C안</div>
      <div class="gauge-sub">수주확률 15–20%</div>
    </div>
  </div>
  <div class="hero-date">분석 기준일: 2026-05-31 | 글로벌K존 RFP 대응</div>
</section>

<div class="section-block">
  <div class="section-header"><div class="section-tag">축 1</div><div class="section-title">기대효과 극대화</div><div class="section-sub">EMV·바이럴·B2B·재방문·방문자 증가 5개 지표 비교</div></div>
  <div class="card">
    <table class="compare-table">
      <thead><tr><th style="width:200px">지표</th><th>A안 — K-ARCHIVE</th><th class="col-b">B안 — HANJI HOUSE × K-CITY</th><th>C안 — K-GATEWAY</th></tr></thead>
      <tbody>
        <tr><td class="row-label">EMV 잠재력</td><td><span class="stars">★★★</span><span style="color:var(--light-gray)">★★</span></td><td class="col-b"><span class="stars purple">★★★★★</span></td><td><span class="stars">★★★★</span><span style="color:var(--light-gray)">★</span></td></tr>
        <tr><td class="row-label">SNS 바이럴</td><td><span class="stars">★★</span><span style="color:var(--light-gray)">★★★</span></td><td class="col-b"><span class="stars purple">★★★★★</span></td><td><span class="stars">★★★</span><span style="color:var(--light-gray)">★★</span></td></tr>
        <tr><td class="row-label">B2B / 수출연계</td><td><span class="stars">★★★</span><span style="color:var(--light-gray)">★★</span></td><td class="col-b"><span class="stars purple">★★★★</span><span style="color:rgba(108,92,231,0.2)">★</span></td><td><span class="stars">★★★★★</span></td></tr>
        <tr><td class="row-label">재방문 강도</td><td><span class="stars">★★★</span><span style="color:var(--light-gray)">★★</span></td><td class="col-b"><span class="stars purple">★★★★★</span></td><td><span class="stars">★★★★</span><span style="color:var(--light-gray)">★</span></td></tr>
        <tr><td class="row-label">방문자 증가 예측</td><td>+40%</td><td class="col-b" style="font-weight:700;color:var(--primary)">+150 ~ 200%</td><td>+95 ~ 150%</td></tr>
      </tbody>
    </table>
  </div>
  <div class="insight-cards">
    <div class="insight-card ic-a"><div class="insight-card-label">A안</div><div class="insight-card-text">P1 직격하나 방문 매력 약</div><div class="visitor-bar-wrap"><div class="visitor-bar-label">방문자 증가 +40%</div><div class="visitor-bar-track"><div class="visitor-bar-fill" style="width:20%;background:var(--mid-gray)"></div></div></div></div>
    <div class="insight-card ic-b"><div class="insight-card-label">B안 ★ 추천</div><div class="insight-card-text">공간 자체가 마케팅 스토리</div><div class="visitor-bar-wrap"><div class="visitor-bar-label">방문자 증가 +150~200%</div><div class="visitor-bar-track"><div class="visitor-bar-fill" style="width:100%;background:var(--primary)"></div></div></div></div>
    <div class="insight-card ic-c"><div class="insight-card-label">C안</div><div class="insight-card-text">가장 직접적 수출 연계</div><div class="visitor-bar-wrap"><div class="visitor-bar-label">방문자 증가 +95~150%</div><div class="visitor-bar-track"><div class="visitor-bar-fill" style="width:65%;background:var(--info)"></div></div></div></div>
  </div>
</div>

<div class="section-block">
  <div class="section-header"><div class="section-tag">축 2</div><div class="section-title">OMO 연결 구조</div><div class="section-sub">온·오프라인 전환 흐름과 잔존 자산 비교</div></div>
  <div class="omo-cards">
    <div class="omo-card omo-a"><div class="omo-card-title">A안 <span class="omo-type-badge">정보형</span></div><div class="omo-flow"><div class="omo-step"><div class="omo-step-dot"></div>아카이브 열람</div><div class="omo-arrow">↓</div><div class="omo-step"><div class="omo-step-dot"></div>뉴스레터 구독</div><div class="omo-arrow">↓</div><div class="omo-step"><div class="omo-step-dot"></div>콘텐츠 소비</div><div class="omo-arrow">↓</div><div class="omo-step"><div class="omo-step-dot"></div>재방문 유도</div></div></div>
    <div class="omo-card omo-b"><div class="omo-card-title">B안 <span class="omo-type-badge">공유형</span></div><div class="omo-flow"><div class="omo-step"><div class="omo-step-dot"></div>포토존 경험</div><div class="omo-arrow">↓</div><div class="omo-step"><div class="omo-step-dot"></div>SNS 자발 업로드</div><div class="omo-arrow">↓</div><div class="omo-step"><div class="omo-step-dot"></div>EMV 증폭</div><div class="omo-arrow">↓</div><div class="omo-step"><div class="omo-step-dot"></div>신규 유입 가속</div></div></div>
    <div class="omo-card omo-c"><div class="omo-card-title">C안 <span class="omo-type-badge">거래형</span></div><div class="omo-flow"><div class="omo-step"><div class="omo-step-dot"></div>QR 쇼룸 방문</div><div class="omo-arrow">↓</div><div class="omo-step"><div class="omo-step-dot"></div>온라인 구매</div><div class="omo-arrow">↓</div><div class="omo-step"><div class="omo-step-dot"></div>파트너 루프 형성</div><div class="omo-arrow">↓</div><div class="omo-step"><div class="omo-step-dot"></div>수출 네트워크 연결</div></div></div>
  </div>
  <div class="card">
    <table class="compare-table">
      <thead><tr><th>OMO 차원</th><th>A안</th><th class="col-b">B안</th><th>C안</th></tr></thead>
      <tbody>
        <tr><td class="row-label">O2O 전환 매력도</td><td>중간</td><td class="col-b" style="font-weight:600;color:var(--primary)">최고</td><td>높음</td></tr>
        <tr><td class="row-label">데이터 수집 풍부도</td><td>높음</td><td class="col-b" style="font-weight:600;color:var(--primary)">최고</td><td>중간</td></tr>
        <tr><td class="row-label">현장판매 우회 효과</td><td>약함</td><td class="col-b">중간</td><td style="font-weight:600;color:var(--success)">강함</td></tr>
        <tr><td class="row-label">잔존 자산</td><td>콘텐츠 라이브러리</td><td class="col-b" style="font-weight:600;color:var(--primary)">콘텐츠 + 브랜드 DB</td><td>파트너십 네트워크</td></tr>
      </tbody>
    </table>
  </div>
</div>

<div class="section-block">
  <div class="section-header"><div class="section-tag">축 3</div><div class="section-title">배점 대응력</div><div class="section-sub">RFP 평가 항목별 예상 점수 — 배점 만점 대비 % 기준</div></div>
  <div class="card">
    <div class="score-chart">
      <div class="score-row-wrap"><div class="score-row-label"><span class="score-row-name">사업이해도</span><span class="score-row-max">배점 15점</span></div><div class="score-bars"><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--mid-gray)">A</span><div class="score-bar-track"><div class="score-bar-fill fill-a" style="width:70%">10.5</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--primary)">B</span><div class="score-bar-track"><div class="score-bar-fill fill-b best" style="width:90%">13.5</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--info)">C</span><div class="score-bar-track"><div class="score-bar-fill fill-c" style="width:68%">10.2</div></div></div></div></div>
      <div class="score-row-wrap"><div class="score-row-label"><span class="score-row-name">공간기획·디자인</span><span class="score-row-max">배점 20점</span></div><div class="score-bars"><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--mid-gray)">A</span><div class="score-bar-track"><div class="score-bar-fill fill-a" style="width:66%">13.2</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--primary)">B</span><div class="score-bar-track"><div class="score-bar-fill fill-b best" style="width:94%">18.8</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--info)">C</span><div class="score-bar-track"><div class="score-bar-fill fill-c" style="width:54%">10.8</div></div></div></div></div>
      <div class="score-row-wrap"><div class="score-row-label"><span class="score-row-name">콘텐츠·운영</span><span class="score-row-max">배점 20점</span></div><div class="score-bars"><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--mid-gray)">A</span><div class="score-bar-track"><div class="score-bar-fill fill-a" style="width:76%">15.2</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--primary)">B</span><div class="score-bar-track"><div class="score-bar-fill fill-b best" style="width:78%">15.6</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--info)">C</span><div class="score-bar-track"><div class="score-bar-fill fill-c" style="width:74%">14.8</div></div></div></div></div>
      <div class="score-row-wrap"><div class="score-row-label"><span class="score-row-name">홍보·확산</span><span class="score-row-max">배점 10점</span></div><div class="score-bars"><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--mid-gray)">A</span><div class="score-bar-track"><div class="score-bar-fill fill-a" style="width:58%">5.8</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--primary)">B</span><div class="score-bar-track"><div class="score-bar-fill fill-b best" style="width:83%">8.3</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--info)">C</span><div class="score-bar-track"><div class="score-bar-fill fill-c" style="width:73%">7.3</div></div></div></div></div>
      <div class="score-row-wrap"><div class="score-row-label"><span class="score-row-name">글로벌 실행체계</span><span class="score-row-max">배점 15점</span></div><div class="score-bars"><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--mid-gray)">A</span><div class="score-bar-track"><div class="score-bar-fill fill-a" style="width:74%">11.1</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--primary)">B</span><div class="score-bar-track"><div class="score-bar-fill fill-b" style="width:66%">9.9</div></div></div><div class="score-bar-row"><span class="score-bar-tag" style="color:var(--info)">C</span><div class="score-bar-track"><div class="score-bar-fill fill-c" style="width:66%">9.9</div></div></div></div></div>
    </div>
    <div style="margin-top:24px;padding-top:20px;border-top:2px solid var(--light-gray)">
      <table class="compare-table"><thead><tr><th>정성 소계</th><th>A안</th><th class="col-b">B안</th><th>C안</th></tr></thead><tbody><tr class="total-row"><td class="row-label">총점 (80점 만점)</td><td>55.8점</td><td class="col-b" style="font-size:17px;font-weight:800;">66.1점</td><td>53.0점</td></tr></tbody></table>
    </div>
  </div>
</div>

<div class="section-block">
  <div class="section-header"><div class="section-tag">축 4</div><div class="section-title">경쟁사 모방 난이도 (Moat)</div><div class="section-sub">경쟁사 진입 장벽과 방어선 강도 비교</div></div>
  <div class="moat-grid">
    <div class="moat-card moat-low"><div class="moat-level">LOW</div><div class="moat-label">A안 — 낮은 방어선</div><div class="moat-line-wrap"><div class="moat-line"></div></div><div class="moat-defense"><strong>단일 방어선</strong>콘텐츠 큐레이션 역량<br>6개월 내 경쟁사 모방 가능</div></div>
    <div class="moat-card moat-high"><div class="moat-level">HIGH</div><div class="moat-label">B안 — 3중 방어선</div><div class="moat-line-wrap"><div class="moat-line"></div><div class="moat-line"></div><div class="moat-line"></div></div><div class="moat-defense"><strong>공간실행력 × 브랜드네트워크 × 크리에이티브</strong>3개 역량 동시 보유 필요<br>18개월 이상 모방 소요</div></div>
    <div class="moat-card moat-mid"><div class="moat-level">MID</div><div class="moat-label">C안 — 중간 방어선</div><div class="moat-line-wrap"><div class="moat-line"></div><div class="moat-line"></div></div><div class="moat-defense"><strong>이중 방어선</strong>파트너십 네트워크 + QR 기술<br>12개월 내 모방 가능</div></div>
  </div>
  <div class="card">
    <table class="compare-table">
      <thead><tr><th>경쟁사 유형</th><th>A안 모방 소요</th><th class="col-b">B안 모방 소요</th><th>C안 모방 소요</th></tr></thead>
      <tbody>
        <tr><td class="row-label">대형 전시사</td><td style="color:var(--danger)">3~4개월</td><td class="col-b" style="color:var(--primary);font-weight:600">18개월+</td><td style="color:var(--warning)">8~10개월</td></tr>
        <tr><td class="row-label">에이전시</td><td style="color:var(--danger)">4~6개월</td><td class="col-b" style="color:var(--primary);font-weight:600">24개월+</td><td style="color:var(--warning)">10~12개월</td></tr>
        <tr><td class="row-label">유사 컨소시엄</td><td style="color:var(--warning)">6~8개월</td><td class="col-b" style="color:var(--primary);font-weight:600">12~18개월</td><td style="color:var(--warning)">8~10개월</td></tr>
      </tbody>
    </table>
  </div>
</div>

<div class="section-block">
  <div class="section-header"><div class="section-tag">축 5</div><div class="section-title">Risk–Reward 종합 평가</div><div class="section-sub">리스크 대비 기대 보상 포지셔닝</div></div>
  <div class="card">
    <div class="scatter-wrap">
      <div class="scatter-axis-x"></div>
      <div class="scatter-axis-y"></div>
      <div class="scatter-label-x">리스크 →</div>
      <div class="scatter-label-y">보상 →</div>
      <div style="position:absolute;bottom:28px;left:60px;font-size:10px;color:var(--mid-gray)">낮음</div>
      <div style="position:absolute;bottom:28px;left:50%;transform:translateX(-50%);font-size:10px;color:var(--mid-gray)">중간</div>
      <div style="position:absolute;bottom:28px;right:40px;font-size:10px;color:var(--mid-gray)">높음</div>
      <div style="position:absolute;top:24px;left:18px;font-size:10px;color:var(--mid-gray)">높음</div>
      <div style="position:absolute;top:50%;transform:translateY(-50%);left:18px;font-size:10px;color:var(--mid-gray)">중간</div>
      <div style="position:absolute;bottom:55px;left:18px;font-size:10px;color:var(--mid-gray)">낮음</div>
      <div style="position:absolute;top:36px;left:72px;font-size:10px;color:var(--success);opacity:0.5;font-weight:600">스위트 스팟</div>
      <div style="position:absolute;top:36px;right:52px;font-size:10px;color:var(--danger);opacity:0.5;font-weight:600">하이리스크 존</div>
      <div class="scatter-dot dot-a" style="left:100px;bottom:130px;">A</div>
      <div class="scatter-dot-label" style="left:106px;bottom:108px;">A안</div>
      <div class="scatter-dot dot-b" style="left:calc(50% + 20px);top:50px;">B</div>
      <div class="scatter-dot-label" style="left:calc(50% + 26px);top:108px;color:var(--primary);font-weight:700;">B안 ★</div>
      <div class="scatter-dot dot-c" style="right:80px;bottom:120px;">C</div>
      <div class="scatter-dot-label" style="right:74px;bottom:98px;">C안</div>
      <div class="scatter-star" style="left:calc(50% + 60px);top:40px;">★</div>
    </div>
    <div style="display:flex;gap:20px;margin-top:16px;flex-wrap:wrap;">
      <div style="display:flex;align-items:center;gap:8px;font-size:13px;"><div style="width:12px;height:12px;border-radius:50%;background:var(--mid-gray)"></div>A안 — 낮은 리스크, 중간 보상</div>
      <div style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;color:var(--primary);"><div style="width:14px;height:14px;border-radius:50%;background:var(--primary)"></div>B안 — 중간 리스크, 높은 보상 (추천)</div>
      <div style="display:flex;align-items:center;gap:8px;font-size:13px;"><div style="width:12px;height:12px;border-radius:50%;background:var(--warning)"></div>C안 — 높은 리스크, 중간 보상</div>
    </div>
  </div>
</div>

<div class="hybrid-section">
  <div class="section-tag">최종 추천</div>
  <div class="section-title">HANJI HOUSE × K-CITY + Living Impact System</div>
  <div class="hybrid-title-sub">B안을 기반으로 A안·C안의 핵심 강점을 흡수한 하이브리드 컨셉</div>
  <div class="structure-diagram">
    <div class="struct-row">
      <div class="struct-box">HANJI HOUSE<div class="box-sub">전통공예 아카이브</div></div>
      <div class="struct-arrow">──</div>
      <div class="struct-gate">게이트</div>
      <div class="struct-arrow">──</div>
      <div class="struct-box">K-CITY<div class="box-sub">팝업 브랜드 QR쇼룸</div></div>
    </div>
    <div class="struct-line-wrap"><div class="struct-line"></div><div class="struct-line"></div></div>
    <div style="display:flex;justify-content:center;"><div class="struct-arrow" style="font-size:20px">↓</div></div>
    <div class="struct-center-box"><div class="struct-data-box">Living Impact System<div class="box-sub">4-Layer KPI Dashboard</div></div></div>
  </div>
  <div class="hybrid-sub-grids">
    <div class="hybrid-sub-card">
      <h4>흡수 요소 (A안·C안 → B안)</h4>
      <table class="hybrid-table">
        <thead><tr><th>요소</th><th>출처</th><th>B안 적용</th></tr></thead>
        <tbody>
          <tr><td>Data Dashboard</td><td>A안</td><td>4-Layer KPI 통합</td></tr>
          <tr><td>QR쇼룸 구체화</td><td>C안</td><td>수출연계 측정</td></tr>
          <tr><td>로컬 파트너십</td><td>C안</td><td>K-타운 스토어 연결</td></tr>
        </tbody>
      </table>
    </div>
    <div class="hybrid-sub-card">
      <h4>약점 보완 플랜</h4>
      <table class="hybrid-table">
        <thead><tr><th>약점</th><th>보완</th><th>제안서 반영</th></tr></thead>
        <tbody>
          <tr><td>실행체계 열세</td><td>LED SLA+백업</td><td>리스크 관리 챕터</td></tr>
          <tr><td>운영 복잡도</td><td>공간별 전담</td><td>역할분담표</td></tr>
          <tr><td>비한인 유입</td><td>영문 SNS+로컬미디어</td><td>홍보 섹션</td></tr>
          <tr><td>브랜드 이탈</td><td>유니원 백업풀</td><td>파트너 브랜드 XX개 명시</td></tr>
          <tr><td>성과측정 약</td><td>Dashboard 흡수</td><td>Living Impact 섹션</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>

<div class="section-block">
  <div class="section-header"><div class="section-tag">액션</div><div class="section-title">제출까지 역산 일정</div><div class="section-sub">6/1(월) ~ 6/8(월) 제출 기준</div></div>
  <div class="checklist-grid">
    <div class="checklist-item deadline"><div class="check-dot"></div><div class="check-date">6/1</div><div class="check-task">컨셉 최종 확정<br><small style="font-weight:400;color:var(--dark-gray)">B안 하이브리드 방향 결정</small></div></div>
    <div class="checklist-item"><div class="check-dot"></div><div class="check-date">6/2</div><div class="check-task">실적 요건 확인<br><small style="font-weight:400;color:var(--dark-gray)">양사 합산 실적 서류 검토</small></div></div>
    <div class="checklist-item"><div class="check-dot"></div><div class="check-date">6/3</div><div class="check-task">PM 지정 + 파트 분담<br><small style="font-weight:400;color:var(--dark-gray)">역할분담표 초안 작성</small></div></div>
    <div class="checklist-item"><div class="check-dot"></div><div class="check-date">6/4</div><div class="check-task">현지 파트너 서브컨<br><small style="font-weight:400;color:var(--dark-gray)">로컬 파트너 컨펌 및 MOU</small></div></div>
    <div class="checklist-item"><div class="check-dot"></div><div class="check-date">6/6</div><div class="check-task">투찰가 확정<br><small style="font-weight:400;color:var(--dark-gray)">원가 산출 + 수익률 검토</small></div></div>
    <div class="checklist-item"><div class="check-dot"></div><div class="check-date">6/7</div><div class="check-task">최종 교정<br><small style="font-weight:400;color:var(--dark-gray)">표지·목차·페이지 번호 확인</small></div></div>
  </div>
  <div class="card" style="margin-top:16px;background:var(--black);border:none;text-align:center;padding:20px;">
    <div style="font-size:22px;font-weight:800;color:var(--primary);letter-spacing:0.05em;">6/8 (월) — 제출 D-DAY</div>
    <div style="font-size:13px;color:rgba(255,255,255,0.5);margin-top:6px;">마감 시간 엄수 · 파일 형식 PDF+HWP 병행 확인</div>
  </div>
</div>

<footer class="footer">분석 기준일: 2026-05-31 &nbsp;|&nbsp; <strong>프로젝트렌트 × 유니원</strong> &nbsp;|&nbsp; 본 문서는 RFP 대응 전략 내부 참고용입니다</footer>
</body>
</html>`;

  await page.setContent(htmlContent, { waitUntil: 'networkidle' });
  await page.waitForFunction(() => document.fonts.ready);
  return await page.title();
}
