#!/usr/bin/env python3
import re, base64

NEW_PW = "RXR-projectrent"

# external : locked 매핑
pairs = [
    ("rxr-analysis-윤선생-심화-통합-20260618-external.html", "rxr-analysis-윤선생-심화-통합-20260618-locked.html"),
    ("rxr-analysis-윤선생영어-20260615-external.html",        "rxr-analysis-윤선생영어-20260615-locked.html"),
    ("rxr-윤선생-하부①-BM분리-20260618-external.html",        "rxr-윤선생-하부①-BM분리-20260618-locked.html"),
    ("rxr-윤선생-하부②-영어수준-20260618-external.html",      "rxr-윤선생-하부②-영어수준-20260618-locked.html"),
    ("rxr-윤선생-하부③-배제사유-20260618-external.html",      "rxr-윤선생-하부③-배제사유-20260618-locked.html"),
]

def strip_watermarks(html):
    # 유형① wm-badge / wm-tile DOM 제거
    html = re.sub(r'<div class="wm-badge">.*?</div>', '', html, flags=re.S)
    html = re.sub(r'<div class="wm-tile">.*?</div>', '', html, flags=re.S)
    # 유형② .watermark DOM 제거
    html = re.sub(r'<div class="watermark"></div>', '', html, flags=re.S)
    # CSS: body::before 줄무늬 워터마크 제거
    html = re.sub(r'body::before\{[^}]*repeating-linear-gradient[^}]*\}', '', html, flags=re.S)
    # CSS: .wm-badge / .wm-tile / .wm-tile span 규칙 제거
    html = re.sub(r'\.wm-badge\{[^}]*\}', '', html, flags=re.S)
    html = re.sub(r'\.wm-tile span\{[^}]*\}', '', html, flags=re.S)
    html = re.sub(r'\.wm-tile\{[^}]*\}', '', html, flags=re.S)
    # CSS: .watermark 규칙 제거 (SVG url 내부에 } 없음)
    html = re.sub(r'\.watermark\{[^}]*\}', '', html, flags=re.S)
    # @media print 안의 .wm-badge / body::before 참조 정리
    html = re.sub(r'@media print\{\.wm-badge\{position:fixed\}body::before\{[^}]*\}[^}]*\}', '', html, flags=re.S)
    return html

for ext, lock in pairs:
    # 1) external 워터마크 제거
    e = open(ext, encoding='utf-8').read()
    e2 = strip_watermarks(e)
    open(ext, 'w', encoding='utf-8').write(e2)

    # 2) locked DATA(또는 D) base64 갱신 + PW 변경
    l = open(lock, encoding='utf-8').read()
    new_b64 = base64.b64encode(e2.encode('utf-8')).decode('ascii')
    # 변수명: DATA 또는 D
    l2, n_data = re.subn(r'(var (?:DATA|D)=")[A-Za-z0-9+/=]+(")', r'\g<1>'+new_b64+r'\g<2>', l)
    if n_data == 0:
        # var EXPIRY=..., PW=..., DATA="..." 형태 (콤마 구분)
        l2, n_data = re.subn(r'((?:DATA|D)=")[A-Za-z0-9+/=]+(")', r'\g<1>'+new_b64+r'\g<2>', l)
    l2, n_pw = re.subn(r'(PW=")[^"]*(")', r'\g<1>'+NEW_PW+r'\g<2>', l2)
    open(lock, 'w', encoding='utf-8').write(l2)
    print(f"OK  {ext[:38]:40} | data_repl={n_data} pw_repl={n_pw}")

print("DONE")
