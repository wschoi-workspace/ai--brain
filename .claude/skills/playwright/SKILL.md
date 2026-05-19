---
name: playwright
description: "HTML 파일을 Playwright 브라우저로 렌더링하여 PNG 스크린샷 또는 PDF로 저장. 슬라이드 제작, HTML 캡처, 페이지 스크린샷, PDF 변환 등에 사용. \"스크린샷\", \"캡처\", \"PDF로 저장\", \"슬라이드 캡처\", \"HTML 캡처\", \"playwright\", \"브라우저 캡처\", \"PNG로\", \"화면 저장\", \"렌더링\" 등을 언급하거나 HTML 파일의 스크린샷/PDF 변환을 요청하면 자동 실행."
allowed-tools:
  - mcp__plugin_playwright_playwright__browser_navigate
  - mcp__plugin_playwright_playwright__browser_take_screenshot
  - mcp__plugin_playwright_playwright__browser_run_code
  - mcp__plugin_playwright_playwright__browser_resize
  - mcp__plugin_playwright_playwright__browser_snapshot
  - mcp__plugin_playwright_playwright__browser_close
  - Bash
  - Read
  - Write
  - Glob
---

# Playwright - HTML 렌더링 & 캡처

HTML 파일을 Playwright 브라우저에서 렌더링하고 PNG 스크린샷 또는 PDF로 저장한다.
슬라이드, 보고서, 디자인 시안 등 HTML로 제작한 콘텐츠를 이미지/PDF로 내보내는 용도.

## 핵심 도구

| MCP 도구 | 용도 |
|----------|------|
| `browser_navigate` | HTML 파일 열기 (`file:///` 프로토콜) |
| `browser_resize` | 뷰포트 크기 설정 |
| `browser_take_screenshot` | PNG/JPEG 스크린샷 |
| `browser_run_code` | PDF 저장, 고급 조작 (Playwright API 직접 실행) |
| `browser_close` | 브라우저 닫기 |

## Workflow

### Step 1: 파일 확인

사용자가 지정한 HTML 파일 경로를 확인한다. 경로가 불분명하면 Glob으로 `.html` 파일을 검색한다.

### Step 2: 뷰포트 설정

용도에 따라 뷰포트 크기를 설정한다.

| 용도 | 크기 (px) | 비율 |
|------|-----------|------|
| **슬라이드 (기본)** | 1920 × 1080 | 16:9 |
| **A4 세로** | 1240 × 1754 | A4 |
| **A4 가로** | 1754 × 1240 | A4 가로 |
| **모바일** | 390 × 844 | iPhone 14 |
| **사용자 지정** | 사용자 입력 | - |

사용자가 크기를 지정하지 않으면 슬라이드(1920×1080)를 기본값으로 사용한다.

```
browser_resize → width: 1920, height: 1080
```

### Step 3: HTML 열기

`file:///` 프로토콜로 HTML 파일을 연다.

```
browser_navigate → url: "file:///절대경로/파일.html"
```

### Step 4: 캡처

#### PNG 스크린샷

```
browser_take_screenshot → filename: "output.png", type: "png"
```

- `fullPage: true` → 스크롤 전체 캡처
- `fullPage: false` (기본) → 현재 뷰포트만 캡처

#### PDF 저장

`browser_run_code`로 Playwright의 `page.pdf()` API를 직접 호출한다.

```javascript
async (page) => {
  await page.pdf({
    path: '/절대경로/output.pdf',
    width: '1920px',
    height: '1080px',
    printBackground: true,
    margin: { top: '0px', right: '0px', bottom: '0px', left: '0px' }
  });
  return 'PDF saved';
}
```

- `printBackground: true`는 배경색/이미지를 포함하기 위해 필수
- 슬라이드용 PDF는 margin을 0으로 설정

### Step 5: 멀티 슬라이드 처리

HTML에 여러 슬라이드(섹션)가 있는 경우, 각 슬라이드를 개별 캡처한다.

#### 방법 A: 개별 HTML 파일

각 파일을 순서대로 열어서 캡처한다.

#### 방법 B: 단일 HTML 내 여러 섹션

`browser_run_code`로 각 섹션을 스크롤/표시하면서 개별 캡처한다.

```javascript
async (page) => {
  const slides = await page.$$('.slide');
  for (let i = 0; i < slides.length; i++) {
    await slides[i].scrollIntoViewIfNeeded();
    await slides[i].screenshot({ path: `/절대경로/slide-${i + 1}.png` });
  }
  return `${slides.length} slides captured`;
}
```

#### 방법 C: 전체 PDF (멀티 페이지)

```javascript
async (page) => {
  await page.pdf({
    path: '/절대경로/slides.pdf',
    width: '1920px',
    height: '1080px',
    printBackground: true,
    margin: { top: '0px', right: '0px', bottom: '0px', left: '0px' }
  });
  return 'Multi-page PDF saved';
}
```

### Step 6: 결과 확인

1. 생성된 파일 경로와 크기를 알려준다
2. PNG인 경우 Read 도구로 이미지를 보여준다
3. 필요시 재캡처 (뷰포트 조정, 대기 시간 추가 등)

### Step 7: 정리

작업 완료 후 `browser_close`로 브라우저를 닫는다.

## 웹 폰트 로딩 대기

커스텀 폰트(Google Fonts 등)를 사용하는 HTML은 폰트 로딩 전에 캡처하면 깨질 수 있다.
캡처 전에 폰트 로딩을 기다린다:

```javascript
async (page) => {
  await page.waitForFunction(() => document.fonts.ready);
  // 이후 스크린샷 또는 PDF
}
```

## 애니메이션/전환 효과 처리

CSS 애니메이션이 있는 페이지는 캡처 전에 애니메이션을 비활성화하거나 완료를 기다린다:

```javascript
async (page) => {
  await page.addStyleTag({ content: '*, *::before, *::after { animation: none !important; transition: none !important; }' });
}
```

## Output Naming Rules

| 조건 | 파일명 패턴 |
|------|------------|
| 단일 캡처 | `{원본파일명}.png` 또는 `{원본파일명}.pdf` |
| 멀티 슬라이드 | `{원본파일명}-slide-{번호}.png` |
| 사용자 지정 | 사용자가 지정한 이름 |

출력 파일은 기본적으로 원본 HTML과 같은 디렉토리에 저장한다.
사용자가 다른 경로를 지정하면 해당 경로에 저장한다.
