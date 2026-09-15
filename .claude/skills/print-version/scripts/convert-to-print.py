#!/usr/bin/env python3
"""R다크 테마 HTML → 인쇄용 화이트 출력본 변환 스크립트

Usage:
  python3 convert-to-print.py <폴더경로>       # 폴더 내 모든 HTML 일괄 변환
  python3 convert-to-print.py <파일경로.html>   # 단일 파일 변환
"""
import re, os, sys, glob

# ── 색상 매핑 (R다크 → 출력본) ──
DARK_TO_LIGHT = {
    "--bg:#1A1A1A":   "--bg:#FFFFFF",
    "--bg-2:#111":    "--bg-2:#F2F1ED",
    "--bg-3:#222":    "--bg-3:#F6F5F1",
    "--fg:#F5F0EB":   "--fg:#1A1A1A",
    "--fg-2:#C9C2BA": "--fg-2:#2B2B2B",
    "--fg-3:#7A7570": "--fg-3:#655F57",
    "--line:#333":    "--line:#D5D0C8",
    "--line-2:#2a2a2a": "--line-2:#E6E2DB",
    "--accent-light:#A29BFE": "--accent-light:#5848C8",
    "--accent-sub:rgba(108,92,231,.08)": "--accent-sub:rgba(108,92,231,.07)",
    "--warm:#E9DCC8": "--warm:#917B4A",
    "--green:#8FA37E": "--green:#5C7A4A",
    "--blue:#6F8AA3":  "--blue:#4A6A88",
    "--amber:#D9A34B": "--amber:#A8761A",
    "--red:#E17055":   "--red:#C24E34",
}

# ── 리포트형(세로 스크롤 문서) 매핑 ──
# 슬라이드 덱은 --fg/--bg-2 체계지만, 분석·검토 문서는 --ink/--surface/--pv 체계를 쓴다.
# 변수명이 달라 위 매핑이 걸리지 않으면 흰 배경에 흰 글씨가 되므로 별도로 처리한다.
DOC_DARK_TO_LIGHT = {
    "--bg:#1A1A1A":       "--bg:#FFFFFF",
    "--surface:#212121":  "--surface:#FAF9F6",
    "--surface2:#282828": "--surface2:#F1EFE9",
    "--line:#333":        "--line:#D5D0C8",
    "--ink:#F5F5F5":      "--ink:#1A1A1A",
    "--ink2:#B8B8B8":     "--ink2:#3C3A37",
    "--ink3:#7A7A7A":     "--ink3:#6B655D",
    "--pv-l:#8B7DEE":     "--pv-l:#5B4CD6",
    "--pv-ll:#A29BFE":    "--pv-ll:#4E3FA0",
    # pill 배경이 옅은 rgba라 글자를 충분히 진하게 해야 대비 4.5:1을 넘긴다
    "--good:#4CAF7D":     "--good:#1F6B42",
    "--warn:#E8A33D":     "--warn:#7A5100",
    "--crit:#E05C5C":     "--crit:#A62A2A",
    # 변수를 거치지 않고 박힌 색 — 밝은 배경에서 반드시 뒤집어야 하는 것들
    "#2A2A2A":  "#E6E2DB",   # 표 구분선
    "#262626":  "#DDD8D0",   # 히트맵 격자
    "#2E2E2E":  "#EAE6DE",   # pill.mute 배경
    "#3E3E3E":  "#B5AFA5",   # bar-fill.mute
    "#FFD9D9":  "#8B2020",   # 히트맵 적자칸 글자
    "rgba(255,255,255,.02)": "rgba(0,0,0,.02)",   # 표 hover
}

# 화면·인쇄 공통 보정. 다크에서 흰 글자를 얹던 칸은 배경이 옅어지므로 글자를 뒤집는다.
DOC_EXTRA_CSS = """
.hm .h4,.hm .h5{color:#1A1A1A}
.hm .h4{background:rgba(108,92,231,.30)}
.hm .h5{background:rgba(108,92,231,.46);font-weight:700}
"""

DOC_PRINT_CSS = """
@page{size:A4;margin:14mm 12mm}
@media print{
  html,body{background:#fff!important}
  .wrap{max-width:none!important;padding:0!important}
  section{break-inside:auto;page-break-inside:auto;margin-bottom:26px!important}
  h2,h3{break-after:avoid;page-break-after:avoid}
  .card,.co,.stat,table{break-inside:avoid;page-break-inside:avoid}
  .tw{overflow:visible!important}
  header{padding-top:0!important}
  *{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
}
"""

PAGE_BG = "#E9E7E2"   # 슬라이드 바깥 페이지 바탕색

BODY_REPLACEMENTS = {
    "font-weight:300": "font-weight:400",
}


def strip_balanced_block(html, opener):
    """중첩 중괄호를 고려해 `opener`로 시작하는 블록을 통째로 제거.

    `@media print{...}` 안에 `.slide{...}` 같은 중첩 규칙이 있으면
    `[^}]*` 정규식은 첫 `}`에서 끊겨 나머지가 전역 CSS로 새어나온다.
    """
    i = html.find(opener)
    if i < 0:
        return html
    depth, j = 0, i
    while j < len(html):
        if html[j] == "{":
            depth += 1
        elif html[j] == "}":
            depth -= 1
            if depth == 0:
                j += 1
                break
        j += 1
    return html[:i] + html[j:]


def set_page_background(html):
    """body(또는 html,body) 선언 블록 안의 background만 페이지 바탕색으로 교체.

    `background:var(--bg)` 전역 치환은 `.slide{background:var(--bg)}` 까지
    바꿔버려 슬라이드가 회색이 된다. body 배경이 `var(--bg)`가 아닌 덱
    (예: `background:#0d0d0d`)도 있으므로 값에 관계없이 교체한다.
    """
    m = re.search(r"(?:html\s*,\s*)?\bbody\s*\{", html)
    if not m:
        return html
    start = m.start()
    depth, j = 0, m.end() - 1
    while j < len(html):
        if html[j] == "{":
            depth += 1
        elif html[j] == "}":
            depth -= 1
            if depth == 0:
                j += 1
                break
        j += 1
    block = html[start:j]
    if "background" in block:
        block = re.sub(r"background\s*:\s*[^;}]+", f"background:{PAGE_BG}", block, count=1)
    else:
        block = block[:-1] + f";background:{PAGE_BG}}}"
    return html[:start] + block + html[j:]

PRINT_CSS = """
@page{size:1280px 720px;margin:0}
@media print{
  html,body{background:#fff!important;margin:0;padding:0}
  .slide{margin:0!important;border:none!important;page-break-after:always;page-break-inside:avoid;break-after:page;box-shadow:none!important;overflow:hidden!important;width:1280px!important;height:720px!important;min-height:720px!important;max-height:720px!important}
  .slide:last-child{page-break-after:auto;break-after:auto}
  .slide--cover,.slide--dark{background:var(--bg-2)!important}
  *{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
}
"""


def is_dark_theme(html):
    """R다크 테마인지 확인 (--bg:#1A1A1A 패턴)"""
    return "--bg:#1A1A1A" in html or "--bg: #1A1A1A" in html


def is_doc_theme(html):
    """리포트형(--ink/--surface 체계, .slide 없음)인지 확인"""
    return ("--ink:#F5F5F5" in html or "--surface:#212121" in html) and 'class="slide' not in html


def convert(src_path, dst_path):
    with open(src_path, "r", encoding="utf-8") as f:
        html = f.read()

    if not is_dark_theme(html):
        return None  # 이미 라이트 테마

    doc_mode = is_doc_theme(html)

    # 1) :root CSS 변수 치환
    for dark, light in (DOC_DARK_TO_LIGHT if doc_mode else DARK_TO_LIGHT).items():
        html = html.replace(dark, light)

    # 2) body 스타일 보정 (배경은 body 선언에만 적용)
    for old, new in BODY_REPLACEMENTS.items():
        html = html.replace(old, new)
    if not doc_mode:
        # 리포트형은 슬라이드 바깥 여백이 없으므로 body를 흰색 그대로 둔다
        html = set_page_background(html)

    # 3) @page + @media print 블록 교체 (중첩 중괄호 안전)
    html = re.sub(r'@page\s*\{[^}]*\}\s*', '', html)
    while "@media print{" in html or "@media print {" in html:
        before = html
        html = strip_balanced_block(html, "@media print{")
        html = strip_balanced_block(html, "@media print {")
        if html == before:
            break
    tail = (DOC_EXTRA_CSS + DOC_PRINT_CSS) if doc_mode else PRINT_CSS
    html = html.replace("</style>", tail + "</style>")

    # 4) 본문 강조 가독성
    html = html.replace(
        ".sub b{color:var(--fg);font-weight:400}",
        ".sub b{color:var(--fg);font-weight:500}"
    )

    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(html)

    return dst_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 convert-to-print.py <폴더 또는 파일>")
        sys.exit(1)

    target = sys.argv[1]
    converted = []

    if os.path.isdir(target):
        html_files = glob.glob(os.path.join(target, "*.html"))
        for src in sorted(html_files):
            fname = os.path.basename(src)
            if "-출력본" in fname:
                continue
            base, ext = os.path.splitext(fname)
            dst = os.path.join(target, f"{base}-출력본{ext}")
            result = convert(src, dst)
            if result:
                converted.append(fname)
                print(f"  OK: {fname} → {base}-출력본{ext}")
            else:
                print(f"  SKIP (not dark theme): {fname}")
    elif os.path.isfile(target):
        fname = os.path.basename(target)
        base, ext = os.path.splitext(fname)
        dst = os.path.join(os.path.dirname(target), f"{base}-출력본{ext}")
        result = convert(target, dst)
        if result:
            converted.append(fname)
            print(f"  OK: {fname} → {base}-출력본{ext}")
        else:
            print(f"  SKIP (not dark theme): {fname}")
    else:
        print(f"  ERROR: {target} not found")
        sys.exit(1)

    print(f"\n총 {len(converted)}개 변환 완료.")


if __name__ == "__main__":
    main()
