#!/usr/bin/env python3
from pathlib import Path
"""하부①②③ → 외부 공유본 + 잠금본 일괄 빌더 (통합본과 동일 보안 처리)."""
import re, base64, datetime, os
K=str(Path.home()/"do-better-workspace"/"30-knowledge")+"/"
PW="projectrent2026"
EXPIRY=(datetime.date(2026,6,19)+datetime.timedelta(days=30)).isoformat()

FILES=[
 ("rxr-윤선생-하부①-BM분리-20260618.html","윤선생 하부① BM별 분리 (외부 공유본)"),
 ("rxr-윤선생-하부②-영어수준-20260618.html","윤선생 하부② 영어수준 정량추정 (외부 공유본)"),
 ("rxr-윤선생-하부③-배제사유-20260618.html","윤선생 하부③ 배제사유 (외부 공유본)"),
]

V3=[
 ("RXR 2-LAYER","RXR DUAL-LAYER"),
 ("RXR 2-Layer + 시간·BM축 확장","RXR 이중 계층 분석 + 시간·BM축 확장"),
 ("RXR 2-Layer Brand Review","RXR 이중 계층 브랜드 분석"),
 ("Content Layer","표현 계층"),("Psyche Layer","심층 심리 계층"),
 ("(Sincerity)","(다단 정제)"),("Sincerity Filter","다단 정제 절차"),
 ("RXR 2-Layer","RXR 이중 계층 분석"),("2-Layer","이중 계층 분석"),
]
WM_CSS="""
  body::before{content:"";position:fixed;inset:0;z-index:1;pointer-events:none;
    background-image:repeating-linear-gradient(-30deg,rgba(102,102,255,.05) 0 2px,transparent 2px 220px);}
  .wm-badge{position:fixed;top:10px;right:14px;z-index:60;background:rgba(232,80,107,.93);color:#fff;
    font-size:11px;font-weight:800;letter-spacing:.5px;padding:5px 11px;border-radius:6px;font-family:'Pretendard Variable',system-ui,sans-serif;}
  .wm-tile{position:fixed;inset:0;z-index:0;pointer-events:none;overflow:hidden;opacity:.05;}
  .wm-tile span{position:absolute;font-size:34px;font-weight:900;color:#6666FF;transform:rotate(-30deg);white-space:nowrap;}
  @media print{.wm-badge{position:fixed}body::before{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""
def build_external(h, title):
    for a,b in V3: h=h.replace(a,b)
    # 네비바 제거
    h=re.sub(r'<div class="toolbar">.*?</div>\s*','',h,count=1,flags=re.S)
    # 내부 참조 마스킹 (스크립트·json·경로)
    h=re.sub(r'<code>80-r-tech[^<]*</code>','<code>(내부 로우데이터)</code>',h)
    h=re.sub(r'<code>[^<]*\.json[^<]*</code>','<code>(내부 로우데이터)</code>',h)
    h=re.sub(r'yoonsam-[a-z0-9\-]+\.py','(분석 스크립트)',h)
    h=re.sub(r'[a-z0-9\-]+\.json','(내부 데이터)',h)
    h=re.sub(r'·<code>(분석 스크립트)</code>','',h)
    # 타이틀
    h=re.sub(r'<title>.*?</title>',f'<title>{title} | Project Rent</title>',h,count=1,flags=re.S)
    # 워터마크
    h=h.replace("</style>",WM_CSS+"</style>",1)
    tiles='<div class="wm-tile">'+''.join(
        f'<span style="top:{r*16}%;left:{(c*30-10)}%">CONFIDENTIAL · Project Rent</span>'
        for r in range(7) for c in range(4))+'</div>'
    h=h.replace("<body>",'<body>\n<div class="wm-badge">CONFIDENTIAL · 외부 공유본</div>\n'+tiles,1)
    return h

def build_locked(h):
    b64=base64.b64encode(h.encode("utf-8")).decode("ascii")
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>윤선생 RXR 분석 (보안 문서) | Project Rent</title>
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css" rel="stylesheet">
<style>
 body{{font-family:'Pretendard Variable',system-ui,sans-serif;background:linear-gradient(135deg,#16161f,#27214d 60%,#4a3fd6);margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;color:#fff}}
 .box{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:18px;padding:40px 38px;max-width:420px;width:90%;text-align:center;backdrop-filter:blur(10px)}}
 .brand{{font-size:22px;font-weight:900;color:#a99dff}} h1{{font-size:18px;margin:14px 0 6px;font-weight:800}}
 p{{font-size:13px;color:#cbc8e6;line-height:1.6;margin:6px 0}}
 input{{width:100%;padding:12px 14px;border-radius:10px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.1);color:#fff;font-size:15px;margin-top:16px;box-sizing:border-box;text-align:center;letter-spacing:2px}}
 button{{width:100%;padding:12px;border:none;border-radius:10px;background:#6666FF;color:#fff;font-weight:800;font-size:15px;margin-top:12px;cursor:pointer;font-family:inherit}} button:hover{{background:#4a3fd6}}
 .err{{color:#ff9db0;font-size:12.5px;margin-top:10px;min-height:16px}}
 .meta{{font-size:11px;color:#9a93c9;margin-top:18px;border-top:1px solid rgba(255,255,255,.12);padding-top:14px}}
</style></head><body>
<div class="box"><div class="brand">RXR</div>
 <h1>🔒 보안 문서 — 윤선생 브랜드 인식 분석</h1>
 <p>본 리포트는 <b>프로젝트 렌트</b>의 지적재산이며 비밀번호로 보호됩니다.<br>전달받은 비밀번호를 입력해 주세요.</p>
 <input id="pw" type="password" placeholder="비밀번호" onkeydown="if(event.key==='Enter')unlock()" autofocus>
 <button onclick="unlock()">열기</button><div class="err" id="err"></div>
 <div class="meta">유효기간: ~{EXPIRY} · 무단 공유·복제·배포 금지<br>문의 ws.choi@project-rent.com · © Project Rent</div></div>
<script>
var EXPIRY="{EXPIRY}",PW="{PW}",DATA="{b64}";
function unlock(){{
 var t=new Date(),e=new Date(EXPIRY+"T23:59:59");
 if(t>e){{document.getElementById('err').textContent="유효기간이 만료된 문서입니다. 재발급을 요청해 주세요.";return;}}
 if(document.getElementById('pw').value!==PW){{document.getElementById('err').textContent="비밀번호가 올바르지 않습니다.";return;}}
 try{{var b=atob(DATA),u=new Uint8Array(b.length);for(var i=0;i<b.length;i++)u[i]=b.charCodeAt(i);
  document.open();document.write(new TextDecoder('utf-8').decode(u));document.close();
 }}catch(err){{document.getElementById('err').textContent="문서 로딩 오류: "+err;}}
}}
</script></body></html>"""

for fn,title in FILES:
    src=open(K+fn,encoding="utf-8").read()
    ext=build_external(src,title)
    extn=fn.replace(".html","-external.html"); open(K+extn,"w",encoding="utf-8").write(ext)
    lock=build_locked(ext); lockn=fn.replace(".html","-locked.html"); open(K+lockn,"w",encoding="utf-8").write(lock)
    leftover = ".py" in ext or bool(re.search(r'q[23]-|cafe-naver',ext))
    print(f"{fn} → external({len(ext)}자)·locked({len(lock)}자) | 잔존스크립트/경로:{'⚠있음' if leftover else '없음'}")
print(f"\n비번:{PW} · 만료:{EXPIRY}")
