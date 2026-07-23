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

BODY_REPLACEMENTS = {
    "background:var(--bg)": "background:#E9E7E2",
    "font-weight:300":      "font-weight:400",
}

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


def convert(src_path, dst_path):
    with open(src_path, "r", encoding="utf-8") as f:
        html = f.read()

    if not is_dark_theme(html):
        return None  # 이미 라이트 테마

    # 1) :root CSS 변수 치환
    for dark, light in DARK_TO_LIGHT.items():
        html = html.replace(dark, light)

    # 2) body 스타일 보정
    for old, new in BODY_REPLACEMENTS.items():
        html = html.replace(old, new)

    # 3) @page + @media print 블록 교체
    html = re.sub(r'@page\s*\{[^}]*\}\s*', '', html)
    html = re.sub(r'@media\s+print\s*\{[^}]*\}', '', html)
    html = html.replace("</style>", PRINT_CSS + "</style>")

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
