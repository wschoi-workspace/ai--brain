#!/usr/bin/env python3
"""봉은사 중간산출물 다크→출력본 변환 스크립트"""
import re, os, glob

DIR = os.path.dirname(os.path.abspath(__file__))

# 대상 파일 (이미 출력본인 파일, 스크립트, md 제외)
TARGETS = [
    "00-리서치-종합정리.html",
    "consulting-report-bongeunsa.html",
    "명동1898-덱.html",
    "봉은사-리뉴얼-덱.html",
    "봉은사-상권분석-덱.html",
    "봉은사-일정프로세스-덱.html",
    "봉은사-종합리서치-덱.html",
    "일본-종교공간-덱.html",
    "종교공간BM-덱.html",
    "종교문화공간-덱.html",
    "봉은사-BM-분석-덱.html",
    "봉은사-BM-고도화전략-덱.html",
]

# ── 색상 매핑 (기존 출력본 참조) ──
DARK_TO_LIGHT = {
    # :root 변수값 치환
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
    # 보조 색상 (인쇄 가독성 강화)
    "--warm:#E9DCC8": "--warm:#917B4A",
    "--green:#8FA37E": "--green:#5C7A4A",
    "--blue:#6F8AA3":  "--blue:#4A6A88",
    "--amber:#D9A34B": "--amber:#A8761A",
    "--red:#E17055":   "--red:#C24E34",
}

# body 배경 + font-weight 보정
BODY_REPLACEMENTS = {
    "background:var(--bg)": "background:#E9E7E2",
    "font-weight:300":      "font-weight:400",
}

# @media print 강화 블록
PRINT_CSS = """
@media print{
  html,body{background:#fff!important}
  .slide{margin:0!important;border:none!important;page-break-after:always;page-break-inside:avoid;box-shadow:none!important;overflow:visible!important}
  .slide--cover,.slide--dark{background:var(--bg-2)!important}
  *{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important}
}
"""


def convert(src_path, dst_path):
    with open(src_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1) :root CSS 변수 치환
    for dark, light in DARK_TO_LIGHT.items():
        html = html.replace(dark, light)

    # 2) body 스타일 보정
    for old, new in BODY_REPLACEMENTS.items():
        html = html.replace(old, new)

    # 3) 기존 @media print 블록 제거 후 강화 버전 삽입
    html = re.sub(r'@media\s+print\s*\{[^}]*\}', '', html)
    # </style> 바로 앞에 print CSS 삽입
    html = html.replace("</style>", PRINT_CSS + "</style>")

    # 4) .sub font-weight:300 → 400 (본문 가독성)
    # 5) .sub b font-weight:400 → 500
    html = html.replace(".sub b{color:var(--fg);font-weight:400}", ".sub b{color:var(--fg);font-weight:500}")

    # 6) 푸터 텍스트를 출력본 표준으로 통일 (선택적)
    # — 각 파일의 기존 푸터가 이미 적절하므로 유지

    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(html)

    return dst_path


def main():
    converted = []
    for fname in TARGETS:
        src = os.path.join(DIR, fname)
        if not os.path.exists(src):
            print(f"  SKIP (not found): {fname}")
            continue
        # 출력본 파일명
        base, ext = os.path.splitext(fname)
        dst_name = f"{base}-출력본{ext}"
        dst = os.path.join(DIR, dst_name)
        convert(src, dst)
        converted.append(dst_name)
        print(f"  OK: {fname} → {dst_name}")

    print(f"\n총 {len(converted)}개 변환 완료.")


if __name__ == "__main__":
    main()
