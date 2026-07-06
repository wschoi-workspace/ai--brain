#!/usr/bin/env python3
"""
build-locked.py — 예제집(job-playbook.html)을 보안본으로 빌드.

프로젝트렌트 표준 공유 보안 패턴 적용:
  비밀번호 게이트 + 만료일(new Date 비교) + 워터마크 + 보안공지 + Base64 payload.
원본 콘텐츠를 base64로 감싸 비번 입력 전엔 보이지 않게 하고, 워터마크·보안공지를 주입한다.

사용법:
  python build-locked.py                       # 기본: 만료=오늘+30일, 비번=projectrent2026
  python build-locked.py --expiry 2026-09-30 --pw mypass --watermark "프로젝트렌트 내부공유"
  python build-locked.py --in job-playbook.html --out job-playbook-locked.html
"""
import argparse, base64, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE = Path(__file__).resolve().parent
KST = timezone(timedelta(hours=9))

# 워터마크 + 보안공지를 원본 </body> 직전에 주입
WATERMARK_BLOCK = """
<!-- 보안 주입: 워터마크 + 공지 -->
<style>
  #wm-overlay{{position:fixed;inset:0;pointer-events:none;z-index:9998;overflow:hidden;opacity:.05}}
  #wm-overlay span{{position:absolute;white-space:nowrap;color:#fff;font-size:20px;font-weight:700;
    transform:rotate(-30deg);letter-spacing:.1em}}
  #sec-notice{{position:fixed;left:0;right:0;bottom:0;z-index:9999;
    background:rgba(10,9,19,.92);border-top:1px solid #2e2c40;
    color:#9b97b3;font-size:11.5px;text-align:center;padding:8px 12px;
    font-family:'Pretendard',sans-serif;letter-spacing:.02em}}
  #sec-notice b{{color:#8b7df0}}
  body{{padding-bottom:42px}}
</style>
<div id="wm-overlay">{wm_spans}</div>
<div id="sec-notice">🔒 유효기간 <b>~{expiry}</b> · 본 자료는 AX 교육 수강자 전용 · <b>무단 공유·복제·배포 금지</b> · 문의 ws.choi@project-rent.com · © Project Rent</div>
"""

def make_wm_spans(text):
    spans = []
    # 5열 x 7행 격자로 대각선 배치
    for r in range(7):
        for c in range(5):
            top = r * 15 + 3
            left = c * 22 - 5
            spans.append(f'<span style="top:{top}%;left:{left}%">{text}</span>')
    return "".join(spans)


LOCK_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AX 직무별 예제집 — Protected</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:'Pretendard',system-ui,sans-serif;background:#0f0e17;color:#e7e5f0;
    display:flex;justify-content:center;align-items:center;min-height:100vh}}
  .lock{{text-align:center;max-width:460px;padding:56px 36px}}
  .lock-icon{{font-size:44px;margin-bottom:22px;opacity:.6}}
  .lock-title{{font-size:25px;font-weight:300;letter-spacing:-.5px;margin-bottom:8px}}
  .lock-sub{{font-size:14px;color:#9b97b3;margin-bottom:34px;line-height:1.6}}
  .lock-input{{width:100%;padding:14px 18px;background:#1a1925;border:1px solid #2e2c40;
    color:#e7e5f0;font-size:15px;font-family:inherit;text-align:center;outline:none;border-radius:10px;
    transition:border-color .2s}}
  .lock-input:focus{{border-color:#6C5CE7}}
  .lock-input::placeholder{{color:#7a7570}}
  .lock-btn{{width:100%;padding:14px;margin-top:12px;background:#6C5CE7;border:none;border-radius:10px;
    color:#fff;font-size:12px;font-weight:600;letter-spacing:.25em;text-transform:uppercase;
    cursor:pointer;font-family:inherit;transition:background .15s}}
  .lock-btn:hover{{background:#8577ED}}
  .lock-error{{color:#E17055;font-size:13px;margin-top:12px;display:none}}
  .lock-expired{{color:#E17055}}
  .lock-meta{{font-size:11px;color:#7a7570;margin-top:28px;letter-spacing:.08em;line-height:1.7}}
  .lock-brand{{font-size:11px;color:#3a384a;letter-spacing:.3em;text-transform:uppercase;margin-top:40px}}
</style>
</head>
<body>
<div class="lock" id="lockScreen">
  <div class="lock-icon">&#x1F512;</div>
  <div class="lock-title">AX 직무별 예제집</div>
  <div class="lock-sub" id="lockMsg">
    이 자료는 비밀번호로 보호되어 있습니다.<br>AX 교육 수강자만 열람할 수 있습니다.
  </div>
  <input type="password" class="lock-input" id="pwInput" placeholder="비밀번호 입력" autocomplete="off">
  <button class="lock-btn" id="unlockBtn" onclick="unlock()">UNLOCK</button>
  <div class="lock-error" id="errMsg">비밀번호가 올바르지 않습니다.</div>
  <div class="lock-meta">유효기간: {expiry}까지 · 무단 공유·복제·배포 금지<br>문의 ws.choi@project-rent.com</div>
  <div class="lock-brand">Project Rent</div>
</div>
<script type="text/plain" id="payload">{payload}</script>
<script>
var EXPIRY="{expiry}", HASH="{pw}";
(function(){{
  var now=new Date().toISOString().slice(0,10);
  if(now>EXPIRY){{
    document.getElementById("lockMsg").innerHTML='<span class="lock-expired">이 자료의 열람 기한이 만료되었습니다.<br>재발급이 필요하면 ws.choi@project-rent.com으로 연락해 주세요.</span>';
    document.getElementById("pwInput").disabled=true;
    var b=document.getElementById("unlockBtn");b.disabled=true;b.style.opacity=".3";b.style.cursor="not-allowed";
  }}
}})();
document.getElementById("pwInput").addEventListener("keydown",function(e){{if(e.key==="Enter")unlock()}});
function unlock(){{
  var now=new Date().toISOString().slice(0,10);
  if(now>EXPIRY){{return}}
  if(document.getElementById("pwInput").value===HASH){{
    try{{
      var b64=document.getElementById("payload").textContent.trim();
      var bin=atob(b64), bytes=new Uint8Array(bin.length);
      for(var i=0;i<bin.length;i++)bytes[i]=bin.charCodeAt(i);
      var html=new TextDecoder("utf-8").decode(bytes);
      document.open();document.write(html);document.close();
    }}catch(e){{
      var m=document.getElementById("errMsg");m.style.display="block";m.textContent="복원 오류: "+e.message;
    }}
  }}else{{
    var m=document.getElementById("errMsg");m.style.display="block";
    document.getElementById("pwInput").value="";document.getElementById("pwInput").focus();
  }}
}}
</script>
</body>
</html>
"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default="job-playbook.html")
    ap.add_argument("--out", dest="dst", default="job-playbook-locked.html")
    ap.add_argument("--expiry", help="YYYY-MM-DD (기본: 오늘+30일)")
    ap.add_argument("--pw", default="projectrent2026")
    ap.add_argument("--watermark", default="CONFIDENTIAL · Project Rent")
    args = ap.parse_args()

    expiry = args.expiry or (datetime.now(KST) + timedelta(days=30)).strftime("%Y-%m-%d")

    src = BASE / args.src
    raw = src.read_text(encoding="utf-8")

    # 워터마크 + 보안공지 주입 (</body> 직전)
    inject = WATERMARK_BLOCK.format(wm_spans=make_wm_spans(args.watermark), expiry=expiry)
    if "</body>" in raw:
        raw = raw.replace("</body>", inject + "\n</body>", 1)
    else:
        raw = raw + inject

    # base64 payload
    payload = base64.b64encode(raw.encode("utf-8")).decode("ascii")

    out = LOCK_TEMPLATE.format(payload=payload, expiry=expiry, pw=args.pw)
    (BASE / args.dst).write_text(out, encoding="utf-8")
    print(f"✅ 보안본 생성: {args.dst}")
    print(f"   만료: {expiry} · 비번: {args.pw} · 워터마크: {args.watermark}")
    print(f"   원본 {len(src.read_text(encoding='utf-8'))}자 → payload {len(payload)}자")

if __name__ == "__main__":
    main()
