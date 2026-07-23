---
name: print-version
description: R다크 테마 HTML 슬라이드 덱을 인쇄용 화이트 배경 출력본으로 변환. "출력본 만들어줘", "출력용으로 변환", "인쇄용", "프린트 버전", "print version", "출력본", "인쇄용으로", "화이트 버전", "밝은 배경으로" 등을 언급하면 자동 실행. HTML 파일 경로나 폴더를 지정하면 일괄 변환. 슬라이드 덱뿐 아니라 R다크 테마(:root에 --bg:#1A1A1A 계열)를 쓰는 모든 HTML에 적용 가능.
---

# Print Version — R다크 → 출력본 변환

R스타일 다크 테마(#1A1A1A 배경) HTML 슬라이드 덱을 인쇄/출력에 최적화된 따뜻한 화이트 버전으로 변환한다.

## 기본 규격

**가로형(Landscape) 16:9 = 1280×720px** — 별도 요청이 없는 한 모든 출력본의 기본 방향.
세로형(Portrait)은 사용자가 명시적으로 요청한 경우에만 적용한다.

## 핵심 원리

CSS 변수 기반 디자인이므로 `:root` 블록의 변수값만 치환하면 전체 색상이 전환된다.
레이아웃, 그리드, 타이포그래피 구조는 그대로 유지되어 콘텐츠 손실이 없다.

## 변환 프로세스

### 1단계: 대상 파일 파악
- 사용자가 폴더를 지정하면 해당 폴더의 `.html` 파일 전체 (이미 `-출력본`이 붙은 파일 제외)
- 특정 파일을 지정하면 해당 파일만
- 지정이 없으면 현재 맥락의 프로젝트 폴더에서 HTML 파일 탐색

### 2단계: 변환 스크립트 실행
`scripts/convert-to-print.py` 스크립트를 사용한다. 사용법:

```bash
python3 <skill-path>/scripts/convert-to-print.py <대상폴더 또는 파일경로>
```

- 폴더를 주면 폴더 내 모든 HTML을 일괄 변환
- 파일을 주면 해당 파일만 변환
- 출력: 같은 폴더에 `원본명-출력본.html`로 저장

### 3단계: 검증
Playwright evaluate로 변환된 파일 1개를 열어 CSS 변수가 정확히 적용되었는지 확인:
- `--bg` = `#FFFFFF`, `--fg` = `#1A1A1A`, `--accent` = `#6C5CE7`
- body 배경 = `#E9E7E2`, font-weight = `400`
- 슬라이드 overflow 없음 확인

## 색상 매핑 (다크 → 출력본)

| 변수 | 다크 (원본) | 출력본 |
|------|------------|--------|
| --bg | #1A1A1A | #FFFFFF |
| --bg-2 | #111 | #F2F1ED |
| --bg-3 | #222 | #F6F5F1 |
| --fg | #F5F0EB | #1A1A1A |
| --fg-2 | #C9C2BA | #2B2B2B |
| --fg-3 | #7A7570 | #655F57 |
| --line | #333 | #D5D0C8 |
| --line-2 | #2a2a2a | #E6E2DB |
| --accent | #6C5CE7 | 유지 |
| --accent-light | #A29BFE | #5848C8 (밝은 배경 가독성) |
| body 배경 | var(--bg) | #E9E7E2 |
| font-weight | 300 | 400 |
| 보조색 | 밝은 톤 | 진한 톤 (인쇄 대비) |

## 추가 처리
- `@page{size:1280px 720px;margin:0}` — 슬라이드 크기에 맞춘 페이지 사이즈
- `@media print` 블록: `page-break-after:always`, `break-after:page`, `height:720px!important` 고정 (슬라이드 1장 = PDF 1페이지 보장)
- `.sub b` font-weight 400 → 500
- 네비게이션 JS/바가 있으면 display:none 처리

### 4단계: PDF 생성 (필수)
HTML 변환 완료 후 Playwright로 모든 출력본을 PDF로 변환한다. **출력본은 항상 HTML + PDF 쌍으로 생성.**

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(f"file://{html_path}")
    page.wait_for_timeout(1500)
    page.pdf(
        path=pdf_path,
        print_background=True,
        prefer_css_page_size=True,  # @page size 반영 (핵심)
        margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
    )
    browser.close()
```

검증: PDF 페이지 수 = HTML 슬라이드 수 일치 확인. 불일치 시 `@page` / `height` CSS 점검.
