#!/usr/bin/env python3
"""윤선생 통합 허브 → 외부 공유본 + 잠금본 빌더.
v3 용어변환 + 부록(스크립트·경로) 삭제 + 하부인덱스/네비바 제거 + CONFIDENTIAL 워터마크 + base64 잠금(비번·30일)."""
import re, base64, datetime, os
K="/Users/choi_ai/do-better-workspace/30-knowledge/"
src=open(K+"rxr-analysis-윤선생-심화-통합-20260618.html",encoding="utf-8").read()
h=src

# 1) v3 용어 변환 (특허 청구항 정합)
repl=[
 ("RXR 2-LAYER · DEEP DIVE · INTEGRATED (TRACK A+B)","RXR DUAL-LAYER · INTEGRATED BRAND REVIEW"),
 ("RXR 2-Layer + 시간·BM축 확장","RXR 이중 계층 분석 + 시간·BM축 확장"),
 ("RXR 2-Layer Brand Review — 멘션 관찰 기반 방향성 분석","RXR 이중 계층 브랜드 분석 — 멘션 관찰 기반 방향성 분석"),
 ("BM별 분리(Content Layer: 토픽·감성 / Psyche Layer: 동기·프로파일)","BM별 분리(표현 계층: 토픽·감성 / 심층 심리 계층: 동기·프로파일)"),
 ("가맹 마케팅 분리(Sincerity)","가맹 마케팅 분리(다단 정제)"),
 ("RXR 2-Layer","RXR 이중 계층 분석"),
 ("2-Layer","이중 계층 분석"),
]
for a,b in repl: h=h.replace(a,b)

# 2) 네비바(toolbar) 제거 — 공유/캡처용 네비바 제거 규칙
h=re.sub(r'<div class="toolbar">.*?</div>\s*', '', h, count=1, flags=re.S)

# 3) 하부 레포트 인덱스 카드 제거(내부 상대링크) — SEC00 직전까지
h=re.sub(r'<div class="card" style="border:2px solid #6666FF;background:#faf9ff">.*?(?=<!-- SEC 00 방법론)', '', h, count=1, flags=re.S)

# 4) 부록 '수집·정제 파이프라인' 카드 제거(스크립트명·내부경로·로우데이터 노출 차단) — 검증출처 카드 직전까지
h=re.sub(r'<div class="card">\s*<h3>수집·정제 파이프라인</h3>.*?(?=<div class="card">\s*<h3>검증 출처)', '', h, count=1, flags=re.S)

# 5) 잔존 내부경로/스크립트 표기 보호(혹시 남은 것)
h=re.sub(r'<code>80-r-tech[^<]*</code>', '<code>(내부 로우데이터)</code>', h)
h=re.sub(r'yoonsam-[a-z\-]+\.py', '(분석 스크립트)', h)

# 6) 타이틀/하단표기 외부본 표시
h=h.replace("<title>윤선생 RXR 심화분석 통합 — 5개 브랜드 인식 차원·시간흐름 | Project Rent</title>",
            "<title>윤선생 RXR 브랜드 인식 분석 (외부 공유본) | Project Rent</title>")

# 7) CONFIDENTIAL 워터마크(고정 배지 + 반복 사선 워터마크) 주입
WM_CSS="""
  body::before{content:"";position:fixed;inset:0;z-index:1;pointer-events:none;
    background-image:repeating-linear-gradient(-30deg,rgba(102,102,255,.05) 0 2px,transparent 2px 220px);}
  .wm-badge{position:fixed;top:10px;right:14px;z-index:60;background:rgba(232,80,107,.93);color:#fff;
    font-size:11px;font-weight:800;letter-spacing:.5px;padding:5px 11px;border-radius:6px;font-family:'Pretendard Variable',system-ui,sans-serif;}
  .wm-tile{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;opacity:.05;}
  .wm-tile span{position:absolute;font-size:34px;font-weight:900;color:#6666FF;transform:rotate(-30deg);white-space:nowrap;}
  @media print{.wm-badge{position:fixed}body::before{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""
h=h.replace("</style>", WM_CSS+"</style>",1)
tiles='<div class="wm-tile">'+''.join(
    f'<span style="top:{r*16}%;left:{(c*30-10)}%">CONFIDENTIAL · Project Rent</span>' for r in range(7) for c in range(4))+'</div>'
h=h.replace("<body>", '<body>\n<div class="wm-badge">CONFIDENTIAL · 외부 공유본</div>\n'+tiles,1)

ext_path=K+"rxr-analysis-윤선생-심화-통합-20260618-external.html"
open(ext_path,"w",encoding="utf-8").write(h)
print("외부본 저장:",ext_path,f"({len(h)}자)")

# 8) 잠금본 (base64 + 비번 + 30일 만료)
PW="projectrent2026"
expiry=(datetime.date(2026,6,19)+datetime.timedelta(days=30)).isoformat()
b64=base64.b64encode(h.encode("utf-8")).decode("ascii")
locked=f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>윤선생 RXR 분석 (보안 문서) | Project Rent</title>
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" rel="stylesheet">
<style>
 body{{font-family:'Pretendard Variable',system-ui,sans-serif;background:linear-gradient(135deg,#16161f,#27214d 60%,#4a3fd6);margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;color:#fff}}
 .box{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:18px;padding:40px 38px;max-width:420px;width:90%;text-align:center;backdrop-filter:blur(10px)}}
 .brand{{font-size:22px;font-weight:900;color:#a99dff;letter-spacing:-.5px}}
 h1{{font-size:18px;margin:14px 0 6px;font-weight:800}}
 p{{font-size:13px;color:#cbc8e6;line-height:1.6;margin:6px 0}}
 input{{width:100%;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.1);color:#fff;font-size:15px;margin-top:16px;box-sizing:border-box;text-align:center;letter-spacing:2px}}
 button{{width:100%;padding:12px;border:none;border-radius:10px;background:#6666FF;color:#fff;font-weight:800;font-size:15px;margin-top:12px;cursor:pointer;font-family:inherit}}
 button:hover{{background:#4a3fd6}}
 .err{{color:#ff9db0;font-size:12.5px;margin-top:10px;min-height:16px}}
 .meta{{font-size:11px;color:#9a93c9;margin-top:18px;border-top:1px solid rgba(255,255,255,.12);padding-top:14px}}
</style></head><body>
<div class="box">
 <div class="brand">RXR</div>
 <h1>🔒 보안 문서 — 윤선생 브랜드 인식 분석</h1>
 <p>본 리포트는 <b>프로젝트 렌트</b>의 지적재산이며 비밀번호로 보호됩니다.<br>전달받은 비밀번호를 입력해 주세요.</p>
 <input id="pw" type="password" placeholder="비밀번호" onkeydown="if(event.key==='Enter')unlock()" autofocus>
 <button onclick="unlock()">열기</button>
 <div class="err" id="err"></div>
 <div class="meta">유효기간: ~{expiry} · 무단 공유·복제·배포 금지<br>문의 ws.choi@project-rent.com · © Project Rent</div>
</div>
<script>
var EXPIRY="{expiry}", PW="{PW}", DATA="{b64}";
function unlock(){{
  var today=new Date(); var exp=new Date(EXPIRY+"T23:59:59");
  if(today>exp){{document.getElementById('err').textContent="유효기간이 만료된 문서입니다. 재발급을 요청해 주세요.";return;}}
  if(document.getElementById('pw').value!==PW){{document.getElementById('err').textContent="비밀번호가 올바르지 않습니다.";return;}}
  try{{
    var bin=atob(DATA);var bytes=new Uint8Array(bin.length);
    for(var i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
    var html=new TextDecoder('utf-8').decode(bytes);
    document.open();document.write(html);document.close();
  }}catch(e){{document.getElementById('err').textContent="문서 로딩 오류: "+e;}}
}}
</script></body></html>"""
locked_path=K+"rxr-analysis-윤선생-심화-통합-20260618-locked.html"
open(locked_path,"w",encoding="utf-8").write(locked)
print("잠금본 저장:",locked_path,f"(원문 {len(h)} → base64 {len(b64)})")
print("비밀번호:",PW,"| 만료:",expiry)
