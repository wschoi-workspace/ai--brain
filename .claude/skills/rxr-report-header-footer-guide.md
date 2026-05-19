# RXR 리포트 공통 헤더·푸터 가이드 (Portable)

> **목적**: 다른 PC·다른 환경(Claude Code, Cursor, ChatGPT, 수동 작성 등)에서도 동일한 RXR 리포트 브랜딩이 나오도록 만든 자기완결형(self-contained) 가이드.
>
> **버전**: v4.1 (2026-04-22 기준)
> **소유자**: 프로젝트 렌트(Project Rent) / 최원석 (ws.choi@project-rent.com)
> **적용 대상**: `rxr-analysis`, `rxr-sns-analysis`, `rxr-sns-analysis-compare`, `-follow`, `-value`, `rxr-survey-analysis`, `rxr-progress` 등 모든 RXR 엔진 기반 HTML 리포트

---

## 0. TL;DR — 다른 PC에서 즉시 적용하는 방법

1. 이 파일 한 장만 다른 PC로 복사 → AI에게 "이 가이드대로 RXR 리포트 헤더·푸터 적용해줘" 지시.
2. AI는 아래 §2(헤더 HTML)와 §3(푸터 HTML)을 **수정 없이** 그대로 복사 → 리포트 HTML에 삽입.
3. **헤더**: `<body>` 안 첫 `<h1>` **바로 앞**에 삽입.
4. **푸터**: `</body>` **바로 앞**에 삽입.
5. §4 불변 요소 점검(이메일/회사명/컬러) → 끝.

---

## 1. 적용 원칙 (Why & Where)

### Why — 이 규정이 존재하는 이유
RXR 리포트는 **프로젝트 렌트(Project Rent)의 독자 분석 엔진**을 기반으로 생성되는 IP 산출물이다. 따라서 모든 출력물에 다음 3가지가 자동으로 따라가야 한다:
1. **소유 고지** — 누가 만든 분석인지 (Project Rent)
2. **기술 고지** — 어떤 엔진을 썼는지 (독자분석 AI 엔진 / Intellectual Property)
3. **문의처** — 외부 문의·재배포 요청 창구 (ws.choi@project-rent.com)

### Where — 어디에 적용하는가
모든 RXR 계열 스킬이 생성하는 **모든 HTML 리포트**:
- 내부용 원본: `{이벤트명}-rxr-sns-report.html`
- 외부 배포용: `{이벤트명}-rxr-sns-report-external.html`
- 잠금용 (base64 인코딩): `{이벤트명}-rxr-sns-report-locked.html`
- 비교/추적/가치 리포트: `-compare.html`, `-follow.html`, `-value.html`
- 설문 분석: `rxr-survey-{브랜드}.html`
- 퍼널 통합: `rxr-progress-{브랜드}.html`

### 샌드위치 구조
```
┌─────────────────────────────────┐
│ [헤더] RXR │ AI intention ...    │  ← §2
├─────────────────────────────────┤
│ <h1> 리포트 제목                 │
│ 본문 콘텐츠                      │
│ ...                             │
├─────────────────────────────────┤
│ [푸터 ①] 분석 고지              │
│ [푸터 ②] IP 지적재산권 고지     │  ← §3
│ [푸터 ③] 문의처 + ©             │
└─────────────────────────────────┘
```

---

## 2. 공통 헤더 브랜딩 (v4.1 — 수정 금지)

### 2-1. 위치
`<body>` 안 **첫 번째 `<h1>` 태그 바로 앞** (리포트 제목 위).

### 2-2. HTML 템플릿 (그대로 복사 사용)

```html
<div style="display:flex;align-items:center;gap:10px;margin:0 0 20px 0;padding:0;background:transparent;border:none;font-family:'Pretendard Variable',system-ui,sans-serif;">
  <strong style="font-size:19px;color:#6666FF;letter-spacing:-0.6px;font-weight:900;line-height:1;">RXR</strong>
  <span style="display:inline-block;width:1.5px;height:18px;background:#6666FF;"></span>
  <strong style="font-size:19px;color:#1a1a1a;letter-spacing:-0.6px;font-weight:900;line-height:1;">AI intention</strong>
  <strong style="font-size:19px;color:#9a9a9a;letter-spacing:-0.6px;font-weight:900;line-height:1;">analysis solution</strong>
  <div style="flex:1"></div>
  <span style="font-size:12px;color:#888;font-weight:500;white-space:nowrap;">_by</span>
  <strong style="font-size:13px;color:#6666FF;font-weight:700;letter-spacing:-0.1px;white-space:nowrap;">Project Rent</strong>
  <span style="display:inline-block;width:1.5px;height:18px;background:#6666FF;"></span>
</div>
```

### 2-3. 시각적 결과
```
RXR │ AI intention analysis solution          _by Project Rent │
[리포트 제목 <h1>]
```

### 2-4. 디자인 스펙
| 요소 | 색상 | 사이즈 | weight |
|------|------|--------|--------|
| `RXR` | 퍼플 `#6666FF` | 19px | 900 |
| 세로 구분선 (좌/우) | 퍼플 `#6666FF` | 1.5×18px | — |
| `AI intention` | 검정 `#1a1a1a` | 19px | 900 |
| `analysis solution` | 회색 `#9a9a9a` | 19px | 900 |
| `_by` | 회색 `#888` | 12px | 500 |
| `Project Rent` | 퍼플 `#6666FF` | 13px | 700 |
| 폰트 | Pretendard Variable | — | — |
| 배경/보더/padding | **모두 0/투명** | — | — |

### 2-5. 좌측 정렬 규정 (중요)
- 배경·보더·padding 모두 제거 → 헤더 텍스트의 왼쪽 끝이 바로 아래 `<h1>` 제목의 왼쪽 끝과 **같은 X 좌표**에서 시작.
- Container의 padding이 있어도 일관된 좌측 정렬이 유지되도록 한다.
- v4 대비 50% 축소된 컴팩트 사이즈 — h1 제목을 시각적으로 압도하지 않도록 보조 브랜딩 역할.

---

## 3. 공통 푸터 — IP 지적재산권 고지 (수정 금지)

### 3-1. 위치
`</body>` 태그 **바로 앞** (모든 본문 콘텐츠 뒤 최하단).

### 3-2. HTML 템플릿 (그대로 복사 사용)

```html
<footer style="max-width:1200px;margin:30px auto;padding:0;font-size:12px;color:#555;font-family:'Pretendard Variable',system-ui,sans-serif;">
  <div style="background:#fafafa;padding:18px 22px;border-radius:10px 10px 0 0;text-align:center;border-bottom:1px solid #eee;line-height:1.7;">
    <p style="margin:0 0 4px;">본 분석은 공개 SNS 데이터에 대한 규칙 기반 텍스트 분석의 결과이며, 모든 수치는 상대 비교용 추정치입니다.</p>
    <p style="margin:0;">공유된 대상자 외 재배포·인용을 금하며, 외부 공개를 원할 경우 분석 주체에게 사전 협의를 요청드립니다.</p>
  </div>
  <div style="background:#F4F3FF;padding:22px 24px;border-left:4px solid #6666FF;text-align:left;line-height:1.8;">
    <div style="font-weight:800;color:#6666FF;font-size:14px;margin-bottom:8px;letter-spacing:-0.3px;">💠 RXR SNS Analysis Solution</div>
    <p style="margin:0;color:#333;font-size:12.5px;">
      본 분석 솔루션은 온·오프라인 리테일 미디어 서비스 <strong style="color:#6666FF;">『프로젝트 렌트(Project Rent)』</strong>가
      자체 설계·운영하는 <strong>독자분석 AI 엔진</strong>을 기반으로 구축된
      정량·정성 통합 SNS 인식 분석 솔루션이며, <strong>프로젝트 렌트의 지적재산(Intellectual Property)</strong>입니다.
      본 리포트에 포함된 분석 프레임, 지표 체계, 용어 정의, 산출 로직 일체는 프로젝트 렌트의 독자 기술이며,
      무단 복제·인용·역공학·재사용을 엄격히 금합니다.
    </p>
  </div>
  <div style="background:#fafafa;padding:16px 22px;border-radius:0 0 10px 10px;text-align:center;font-size:12px;color:#666;">
    📧 <strong>본 솔루션 또는 리포트에 대한 문의</strong>&nbsp;·&nbsp;
    <a href="mailto:ws.choi@project-rent.com" style="color:#6666FF;text-decoration:none;font-weight:700;">ws.choi@project-rent.com</a>
    <div style="margin-top:6px;color:#999;font-size:11px;">© Project Rent. All rights reserved.</div>
  </div>
</footer>
```

### 3-3. 푸터 3섹션 구조

| 섹션 | 내용 | 디자인 |
|------|------|--------|
| **① 분석 고지** | 공개 SNS 규칙 기반 분석·상대 추정치, 재배포·인용 금지 | 회색 배경 `#fafafa`, 중앙 정렬, 상단 라운드 |
| **② IP 고지** | 💠 "프로젝트 렌트의 **독자분석 AI 엔진**" + "**지적재산(Intellectual Property)**" + 무단 복제·인용·역공학·재사용 금지 | 퍼플 페일 `#F4F3FF` + 좌측 보더 `#6666FF` 4px |
| **③ 문의처** | 📧 `ws.choi@project-rent.com` (mailto 링크) + © Project Rent | 회색 배경, 중앙 정렬, 하단 라운드 |

---

## 4. 불변 요소 (절대 수정 금지)

| 항목 | 정확한 표기 |
|------|------------|
| **이메일** | `ws.choi@project-rent.com` (반드시 mailto 링크) |
| **회사명 한글** | `프로젝트 렌트(Project Rent)` |
| **회사명 영문** | `Project Rent` |
| **솔루션명** | `RXR SNS Analysis Solution` (헤더는 `AI intention analysis solution`) |
| **기술 명칭** | `독자분석 AI 엔진` |
| **법적 표현** | `지적재산(Intellectual Property)` |
| **금지 동작** | `무단 복제·인용·역공학·재사용을 엄격히 금합니다` |
| **브랜드 컬러** | 퍼플 `#6666FF` (R디자인가이드) |
| **페일 배경** | `#F4F3FF` (IP 고지 섹션) |
| **저작권 표기** | `© Project Rent. All rights reserved.` |
| **폰트** | `Pretendard Variable` → fallback: `system-ui, sans-serif` |

---

## 5. 적용 체크리스트

리포트 HTML을 만든 뒤 아래 9개 항목을 점검:

```
[ ] 1. 헤더가 첫 <h1> 바로 앞에 삽입되었는가?
[ ] 2. 푸터가 </body> 바로 앞에 삽입되었는가?
[ ] 3. 헤더 텍스트 왼쪽이 h1 왼쪽과 같은 X 좌표인가? (배경/보더/padding 0)
[ ] 4. 헤더에 "RXR / AI intention analysis solution / _by Project Rent" 모두 있는가?
[ ] 5. 푸터 3섹션(분석고지 / IP고지 / 문의처)이 모두 있는가?
[ ] 6. 이메일이 mailto 링크로 활성화되어 있는가?
[ ] 7. 퍼플 컬러 #6666FF가 RXR·세로선·Project Rent·IP 보더에 일관 적용되었는가?
[ ] 8. "독자분석 AI 엔진", "지적재산(Intellectual Property)" 문구가 정확한가?
[ ] 9. 인쇄 시(Ctrl+P) 헤더·푸터가 사라지지 않는가? (display:none 금지)
```

---

## 6. 인쇄(PDF) 호환성

- 별도 `@media print` 숨김 처리 **금지** — 인쇄물에도 헤더·푸터 노출 필수.
- 퍼플 페일 배경(`#F4F3FF`)이 인쇄에서 살아나려면 CSS에 `print-color-adjust: exact;` 권장 (선택).
  ```css
  @media print {
    body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
  ```
- 폰트 fallback이 작동하므로 Pretendard가 설치되지 않은 PC에서도 system-ui로 자연스럽게 표시됨.

---

## 7. 외부 배포용 별도 처리

외부 공유 시 **알고리즘 IP 보호**를 위해 별도 버전 생성:
- 파일명: `{이벤트명}-rxr-sns-report-external.html`
- 잠금 버전: `{이벤트명}-rxr-sns-report-locked.html` (base64 인코딩, 암호 보호)
- 잠금 버전은 base64 재인코딩 시 헤더·푸터가 자동 포함됨 — 별도 처리 불필요.
- 외부용에서도 헤더·푸터는 **동일하게** 포함 (소유 고지 강화 목적).
