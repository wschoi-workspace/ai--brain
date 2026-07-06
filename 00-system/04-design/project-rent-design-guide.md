# PROJECT RENT — DESIGN SYSTEM

> 최종 업데이트: 2026-06-03
> 기준 자료: FILAMENT&CO Design System v1 구조 + 프로젝트렌트 IR Deck V7
> 포인트 컬러: 청보라 `#6C5CE7`

---

## 1. Brand Statement

- **회사명**: PROJECT RENT (프로젝트렌트)
- **슬로건**: End of design / Movement of Business
- **서비스**: 리테일 미디어 스토어 플랫폼 (오프라인 마케팅 서비스 플랫폼)
- **키워드**: Retail Media, Pop-up Store, Immersive Retail Experience, OMO마케팅

### Brand Values

| Value | 설명 |
|-------|------|
| **Retail as Media** | 매장을 "판매처"가 아닌 "미디어"로 설계합니다. 공간이 곧 콘텐츠이자 채널. |
| **Editorial Discipline** | Dezeen·Wallpaper\* 톤의 매거진 문법. 영문 라벨 + 한글 타이틀 + 본문의 3단 위계. 포인트 컬러는 한 장에 한 군데. |
| **Modular Scalability** | 단발 팝업이 아닌 반복 가능한 모듈형 플랫폼. 시즌·브랜드·지역별 재조합 설계. |

---

## 2. Color Palette — 10-Color System

### Core Colors

| 이름 | HEX | CSS Variable | 용도 |
|------|------|-------------|------|
| **BG** | `#1A1A1A` | `--bg` | 슬라이드 기본 배경 |
| **BG-2** | `#111111` | `--bg-2` | 섹션 안쪽 음영 |
| **BG-3** | `#222222` | `--bg-3` | 카드 배경 |
| **FG** | `#F5F0EB` | `--fg` | 본문 · 제목 크림 |
| **FG-2** | `#C9C2BA` | `--fg-2` | 보조 본문 |
| **FG-3** | `#7A7570` | `--fg-3` | 라벨 · 메타 |
| **Accent** | `#6C5CE7` | `--accent` | ★ 포인트 극소량 (청보라) |
| **Warm** | `#E9DCC8` | `--warm` | 따뜻한 스톤 |
| **Rust** | `#B86C4A` | `--rust` | 러스트 · 코르텐 |
| **Green** | `#8FA37E` | `--green` | 세이지 · Gantt · 성공 상태 |

### Line / Border

| 이름 | HEX | CSS Variable | 용도 |
|------|------|-------------|------|
| Line | `#333333` | `--line` | 기본 구분선 |
| Line-2 | `#2A2A2A` | `--line-2` | 미세 구분선, 카드 테두리 |

### Accent 계열 확장 (청보라)

| 역할 | 이름 | HEX | 용도 |
|------|------|-----|------|
| **Primary** | 청보라 | `#6C5CE7` | CTA, 강조, 타이틀 포인트, 아이콘 |
| Primary Dark | 딥 퍼플 | `#5A4BD1` | Hover, Active 상태, 진한 강조 |
| Primary Light | 라이트 퍼플 | `#A29BFE` | 배경 틴트, 태그, 보조 강조 |
| Primary Subtle | 페일 퍼플 | `#EDE9FE` | 라이트 모드 카드 배경, 섹션 구분 |

### Semantic Colors

| 역할 | HEX | 용도 |
|------|-----|------|
| 성공/긍정 | `#8FA37E` (--green) | 상승, 완료, 긍정 지표 |
| 경고/주의 | `#D9A34B` (--amber) | 주의, 대기, 보류 |
| 부정/하락 | `#E17055` | 하락, 오류, 부정 지표 |
| 정보 | `#6F8AA3` (--blue) | 정보성 강조, 보조 링크 |

### 차트 컬러 팔레트

데이터 시각화 시 아래 순서로 사용:
```
1차: #6C5CE7 (청보라)
2차: #A29BFE (라이트 퍼플)
3차: #6F8AA3 (블루)
4차: #8FA37E (세이지)
5차: #D9A34B (앰버)
6차: #E17055 (코랄)
```

### CSS Variables 선언

```css
:root {
  --bg: #1A1A1A;
  --bg-2: #111;
  --bg-3: #222;
  --fg: #F5F0EB;
  --fg-2: #C9C2BA;
  --fg-3: #7A7570;
  --line: #333;
  --line-2: #2a2a2a;
  --accent: #6C5CE7;
  --warm: #E9DCC8;
  --stone: #A89E90;
  --charcoal: #2B2B2B;
  --rust: #B86C4A;
  --green: #8FA37E;
  --blue: #6F8AA3;
  --amber: #D9A34B;
  --duration-fast: 150ms;
  --duration-base: 250ms;
  --duration-slow: 400ms;
  --ease-out: cubic-bezier(.2, .8, .2, 1);
}
```

---

## 3. Typography — Pretendard Scale

### 서체

모든 텍스트에 **Pretendard Variable** 사용. 웹/앱/문서/프레젠테이션 통일.

```css
font-family: 'Pretendard Variable', 'Pretendard', -apple-system, sans-serif;
```

CDN:
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable.min.css">
```

### 타이포 스케일 (3-Weight 체계: 200 · 300 · 500)

| 레벨 | 크기 | 굵기 | 행간 | letter-spacing | 용도 |
|------|------|------|------|---------------|------|
| **H1 / Cover** | 108px | 200 (ExtraLight) | 0.95 | -0.04em | 커버 타이틀 |
| **H2 / Section** | 44px | 500 (Medium) | 1.1 | -0.025em | 섹션 타이틀 |
| **H3 / Option** | 32px | 300 (Light) | 1.2 | -0.02em | 옵션·서브 타이틀 |
| **Body** | 14px | 300 (Light) | 1.7 | -0.01em | 본문 |
| **Label** | 11px | 400 (Regular) | 1.0 | 0.25em | 아이브로우·메타·라벨 |

### 한글/영문 위계 패턴

매거진 문법의 3단 위계:
```
영문 라벨 (Label, 작게, FG-3)
────────────────────────────
한글 타이틀 (H2/H3, 크게, FG)
────────────────────────────
본문 설명 (Body, 중간, FG-2)
```

### Label 스타일

```css
.label {
  font-size: 11px;
  letter-spacing: 0.25em;
  color: var(--fg-3);
  text-transform: uppercase;
}
```

### Eyebrow 스타일

```css
.eyebrow {
  font-size: 11px;
  letter-spacing: 0.3em;
  color: var(--fg-3);
  text-transform: uppercase;
}
```

### 타이포 규칙

- **제목**: FG(`#F5F0EB`) 기본, 강조 시 Accent(`#6C5CE7`)
- **본문**: FG-2(`#C9C2BA`) 기본
- **라벨/메타**: FG-3(`#7A7570`)
- **강조**: Accent 컬러 극소량. 한 슬라이드에 청보라 2곳 이상 금지
- **영문**: Pretendard 그대로 사용 + text-transform: uppercase
- **순수 검정 금지**: `#000000` 사용 금지 → `#1A1A1A` 사용

---

## 4. Layout System — 12-Column Grid

> v2 — grid-system.md 통합, 2026-06-08

### Core Principle

모든 레이아웃 결정은 수학적으로 설명 가능해야 한다.

이 시스템이 우선하는 것:
- 구조적 일관성
- 공간적 균형
- 수직 리듬
- 수평 정렬
- 모듈형 구성
- 예측 가능한 레이아웃 동작
- 적응형 컴포넌트 조직

목표는 시각적 장식이 아니다.

목표는: 다음과 관계없이 시각적으로 안정된 레이아웃을 만드는 것이다.
- 콘텐츠 양
- 컴포넌트 수
- 텍스트 길이
- 이미지 비율
- 반응형 스케일링

모든 오브젝트는 명확한 공간 논리 안에 존재해야 한다.
**구조가 미학보다 먼저다.**

### Primary Grid

```css
.layout-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 14px;
}
```

| Context | Margin | Gutter | Columns | Max Width |
|---------|--------|--------|---------|-----------|
| Slide (1920×1080) | 40–60px | 14px | 12 | 1440px |
| 스크롤 매거진 | 120px (좌우) | 14px | 12 | 1440px |
| 반응형 (<1200px) | 60px (좌우) | 14px | 12 | — |
| Card / Component | — | 14px | auto | 8px base |

그리드 외부에 오브젝트를 배치하지 않는다.

### Section 구조

```css
.sec {
  padding: 100px 120px 120px;
  max-width: 1440px;
  margin: 0 auto;
}
```

### Alignment System

#### 수평 정렬

모든 오브젝트는 다음에 정렬해야 한다:
- 컬럼 엣지
- 컬럼 센터
- 또는 공유된 수직 축

임의 배치를 피한다. 오브젝트는 정렬 논리를 통해 시각적으로 연결되어야 한다.

#### 수직 정렬

모든 타이포그래피와 컴포넌트는 다음을 따른다:
- 베이스라인 리듬
- 일관된 수직 간격
- 예측 가능한 스태킹 구조

랜덤 수직 간격을 피한다. 모든 섹션은 수학적으로 관련되어 보여야 한다.

#### 교차 정렬 규칙

여러 행의 컴포넌트가 있을 때:
- 상단 엣지는 수평으로 정렬
- 좌측 엣지는 수직으로 정렬
- 내부 콘텐츠(레이블, 값, 아이콘)는 베이스라인을 공유

### Spacing Rules

#### 간격 스케일 (8px 기반)

8px 시스템에서 파생된 간격 값만 사용:

| 토큰 | 값 | 용도 |
|------|-----|------|
| xs | 4px | 내부 촘촘한 간격 |
| sm | 8px | 아이콘↔텍스트, 인라인 간격 |
| md | 16px | 컴포넌트 내부 패딩 (소) |
| lg | 24px | 컴포넌트 내부 패딩 (기본) |
| xl | 32px | 섹션 간격 (소) |
| 2xl | 48px | 섹션 간격 (대) |
| 3xl | 64px | 주요 섹션 분리 |

임의 간격 값은 사용하지 않는다.

#### 컴포넌트 내부 패딩

모든 컴포넌트는 다음을 유지해야 한다:
- 모든 면에 동일한 내부 패딩
- 대칭적 콘텐츠 간격
- 시각적 균형

| 컴포넌트 크기 | 패딩 | 예시 |
|-------------|------|------|
| Small | 16px | 태그, 배지 |
| Medium | 24px | KPI 카드, 버튼 그룹 |
| Large | 32px | 섹션 컨테이너, 히어로 |

### Component Construction

#### Box Logic

모든 컴포넌트는 명확한 직사각형 경계 안에 존재한다.

규칙:
- 모든 콘텐츠는 정의된 박스 안에 포함되어야 한다
- 박스는 그리드 라인을 따라 시각적으로 스냅되어야 한다
- 박스 경계 밖에 떠 있는 오브젝트는 없다
- 불규칙한 엣지 관계는 없다

#### 컴포넌트 동작

컴포넌트는:
- 그리드 컬럼 내에서 비례적으로 확장
- 어떤 너비에서도 내부 구조 유지
- 콘텐츠 양에 관계없이 정렬 보존
- 스케일링 시 일관된 패딩 비율 유지

#### Adaptive Layout Rule

**컴포넌트 수가 레이아웃 리듬을 깨면 안 된다.**

컴포넌트 수가 변경될 때:
- 아이템 간 동일한 간격 보존
- 시각적 리듬과 비율 보존
- 그리드 연속성 보존
- 레이아웃을 수학적으로 재계산

| 개수 | 레이아웃 전략 |
|------|-------------|
| 1 | 중앙 정렬 또는 전체 너비 |
| 2 | 6+6 컬럼 |
| 3 | 4+4+4 컬럼 |
| 4 | 3+3+3+3 컬럼 또는 6+6 × 2행 |
| 5+ | 4+4+4 × 행, 또는 3+3+3+3 × 행 |

오브젝트를 무작위로 압축하지 않는다. 수학적으로 재계산한다.

#### Equal Distribution Rule

아이템이 한 행을 공유할 때:
- 모든 아이템은 동일한 너비
- 모든 간격은 동일
- 아이템이 균등하게 나눌 수 없으면 행을 사용 (예: 5개 → 3+2)
- 마지막 행은 동일한 아이템 너비를 유지하며 좌측 정렬

### Typography Grid Integration

#### Baseline Rhythm

타이포그래피는 다음을 유지해야 한다:
- 모든 텍스트 블록에서 일관된 줄간격
- 예측 가능한 단락 간격 (8px의 배수)
- 인접 컬럼 간 베이스라인 일관성

| 레벨 | 줄간격 | 단락 후 간격 |
|------|--------|------------|
| Display | 1.0 | 32px |
| H1–H3 | 1.2–1.3 | 24px |
| Body | 1.5–1.6 | 16px |
| Caption | 1.4 | 8px |

#### 텍스트 정렬

기본: **좌측 정렬만 사용**

허용되는 예외:
- KPI 숫자: 카드 내에서 중앙 정렬
- 커버 타이틀: 전체 배경에서 중앙 정렬
- 테이블 셀 숫자: 우측 정렬

피할 것:
- 본문 텍스트의 불필요한 중앙 정렬
- 임의 텍스트 배치
- 같은 섹션 내 혼합 정렬

#### Text Box 동작

텍스트 컨테이너는:
- 그리드 컬럼 엣지에 정렬
- 동일한 패딩 유지
- 불안정한 텍스트 줄바꿈 방지

피할 것:
- 고아 텍스트 (마지막 줄에 단어 하나)
- 고립된 짧은 줄 (컨테이너 너비의 30% 미만)
- 인접 컬럼 간 불균등한 단락 너비

### Image System

#### 이미지 배치

이미지는:
- 그리드 컬럼에 정렬
- 비례적 스케일링 유지
- 일관된 크롭 로직 유지
- 같은 섹션 내에서 일관된 비율 사용

#### Aspect Ratio Standards

| 용도 | 비율 | 예시 |
|------|------|------|
| 히어로 / 커버 | 16:9 | 전체 블리드 배경 |
| 가로형 | 3:2 | 케이스 스터디, 포트폴리오 |
| 정사각형 | 1:1 | 프로필, 아이콘, 썸네일 |
| 세로형 | 2:3 | 제품, 인물 |

피할 것:
- 같은 행에서 무작위 비율 혼합
- 구조적 목적 없는 장식적 오버랩
- 그리드 외부의 불안정한 이미지 배치

#### Image Rhythm

이미지 블록은 다음을 유지해야 한다:
- 행 전체에 걸친 균등한 시각적 무게
- 일관된 간격 (그리드와 동일한 gutter)
- 인접 텍스트와의 구성적 균형

### Visual Density Control

#### Density Principle

레이아웃은 다음처럼 느껴져야 한다:
- 숨쉴 수 있는
- 차분한
- 의도적인

공백은 디자인 시스템의 일부다. 빈 공간을 불필요하게 채우지 않는다.

#### 콘텐츠 배분

- 최대 콘텐츠 영역: 전체 공간의 70–80%
- 최소 공백: 전체 공간의 20–30%
- 어떤 섹션도 다른 섹션보다 현저히 무거워 보이면 안 된다

피할 것:
- 밀집된 클러스터
- 고립된 무거운 섹션
- 좌우 반쪽 간 시각적 불균형

#### 공간을 통한 정보 위계

| 우선순위 | 주변 간격 | 시각적 무게 |
|---------|----------|------------|
| Primary | Large (48–64px) | 고대비, 큰 타입 |
| Secondary | Medium (24–32px) | 일반 무게 |
| Tertiary | Small (16px) | 낮은 대비, 작은 타입 |

### Negative Rules — 금지 체크리스트

절대 피해야 할 것:

- [ ] 구조적 목적 없는 임의 비대칭
- [ ] 유사 요소 간 불일관된 간격
- [ ] 그리드 밖에 떠 있는 오브젝트
- [ ] 정렬을 깨는 장식적 배치
- [ ] 컴포넌트의 임의적 스케일링
- [ ] 컬럼 간 정렬되지 않은 텍스트
- [ ] 깨진 베이스라인 리듬
- [ ] 과밀한 구성
- [ ] 과도한 시각적 노이즈 (그림자, 그라디언트, 테두리)
- [ ] 명확한 z-order 논리 없는 요소 중첩

### AI Layout Execution Order

디자인 생성 전 반드시 이 순서를 따른다:

```
1. 그리드 확립 (12-column, 마진, 거터)
2. 간격 리듬 확립 (8px 시스템)
3. 콘텐츠 위계 확립 (primary → secondary → tertiary)
4. 그리드 컬럼 내 컴포넌트 배치
5. 모든 오브젝트 정렬 (수평 + 수직 + 베이스라인)
6. 공간 균형 검증 (콘텐츠 vs 공백 비율)
7. 시각적 리듬 검증 (동일 간격, 일관된 크기)
8. 그 다음 시각적 스타일 적용 (컬러, 타이포, 그림자)
```

**구조 → 정렬 → 리듬 → 스타일.**
구조가 검증되기 전에 스타일을 적용하지 않는다.

### Section Header 패턴

```
┌────────────────────────────────────────────────────┐
│  EYEBROW (11px, FG-3, uppercase)         NO (FG-3) │
│  ─────────────────────────────────────────────────  │
│  Section Title (44px, W500)                        │
│                                                     │
│  [컨텐츠 영역]                                      │
└────────────────────────────────────────────────────┘
```

```css
.sec-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--line-2);
  margin-bottom: 50px;
}
```

### 슬라이드 제안서 레이아웃 (PT형 HTML)

제안서/프레젠테이션을 슬라이드 형태로 제작할 때 적용하는 규칙.
스크롤 매거진과 달리, 각 슬라이드가 뷰포트를 꽉 채우는 구조.

#### 슬라이드 기본 구조

```css
.slide {
  width: 100vw;
  height: 100vh;
  max-width: 1920px;
  overflow: hidden;
  background: var(--bg);
  padding: 60px 80px 80px;
  display: flex;
  flex-direction: column;
  position: relative;
}
```

#### 핵심 규칙: 헤드카피 상단 고정 + 콘텐츠 아래 정렬

```
┌─────────────────────────────────────┐
│  EYEBROW — sec-head                 │ ← 상단 고정
│  ─────────────────────────────────  │
│  헤드카피 H2                        │ ← slide-head
│  서브카피 2~3줄 (포인트 설명)         │
│                                     │
│            (자동 여백)               │ ← flex: 1
│                                     │
│  ┌─────┐ ┌─────┐ ┌─────┐          │
│  │ KPI │ │ KPI │ │ Card│          │ ← slide-body
│  └─────┘ └─────┘ └─────┘          │   (justify-content: flex-end)
│  노트/백업 데이터                    │
│  ──────────────────────────────    │
│  BRAND DIAGNOSIS 2026          30  │ ← slide-footer (absolute)
└─────────────────────────────────────┘
```

```css
.slide-head { flex-shrink: 0; }
.slide-body { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; }

.slide-footer {
  position: absolute;
  bottom: 30px;
  left: 80px;
  right: 80px;
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  letter-spacing: 0.2em;
  color: var(--fg-3);
  text-transform: uppercase;
  border-top: 1px solid var(--line-2);
  padding-top: 14px;
}
```

#### slide-head 구성

헤드카피+서브카피는 상단에 고정. 이 슬라이드의 핵심 메시지를 즉시 전달.

```html
<div class="slide-head">
  <div class="sec-head">
    <span class="eyebrow">SECTION 01 — CONTEXT</span>
    <span class="eyebrow">02</span>
  </div>
  <h2>헤드카피 — 선언형 또는 질문형</h2>
  <p class="body mt-12">
    서브카피 2~3줄. 이 슬라이드에서 말하려는 포인트가 무엇인지,<br>
    왜 이 데이터를 보여주는지, 어떤 결론으로 이어지는지를 직관적으로 설명.
  </p>
</div>
```

#### slide-body 구성

데이터/카드/차트/테이블은 아래쪽에 붙음. 정보의 양에 따라 자연스럽게 배치.

```html
<div class="slide-body">
  <div class="grid-3 mt-24">
    <!-- KPI 카드, 테이블, 차트 등 -->
  </div>
  <div class="note">백업 데이터 또는 출처</div>
</div>
```

#### 슬라이드 타입

| 타입 | 클래스 | 배경 | 용도 |
|------|--------|------|------|
| 일반 | `.slide` | `var(--bg)` #1A1A1A | 대부분의 슬라이드 |
| 강조 (Peak) | `.slide--dark` | `var(--bg-2)` #111 | 감정 피크, 핵심 메시지 |
| 커버 | `.slide--cover` | `var(--bg-2)` + center | 첫 페이지, 마지막 비전 |
| 간지 | `.slide--divider` | `var(--bg)` + center | 챕터 전환 |

커버/간지/Peak 슬라이드는 slide-head/slide-body 구조 대신 중앙 정렬 사용.

#### 서브카피 작성 규칙

| 규칙 | 설명 |
|------|------|
| **구체적으로** | "Auth 83.5" → "리뷰의 솔직함·경험 깊이를 측정하는 진정성 지수 (Auth) 83.5" |
| **축약 금지** | "온라인 멘션 비중" → "온라인 제품 구매 후기 비중 (현재는 매장 방문기만 축적)" |
| **왜 보여주는지** | 데이터 나열이 아니라 "이 수치가 의미하는 바"를 서브카피에서 미리 안내 |
| **2~3줄 제한** | 서브카피는 본문이 아님. 핵심 포인트만 압축. 상세는 slide-body에서 |

#### 키보드 네비게이션 (필수 내장)

모든 슬라이드 제안서에 아래 기능을 JS로 내장:

| 키 | 동작 |
|---|---|
| `→` `↓` `Space` `PageDown` | 다음 슬라이드 |
| `←` `↑` `PageUp` | 이전 슬라이드 |
| `Home` / `End` | 첫/마지막 슬라이드 |
| `F` | 풀스크린 토글 |
| `H` | 하단 네비바 숨기기/보이기 |
| `E` | 편집 모드 토글 (텍스트 직접 수정) |
| `Esc` | 편집 모드 해제 |
| `Cmd+S` | 편집 내용 포함 HTML 다운로드 |

마우스: 화면 오른쪽 30% 클릭 → 다음, 왼쪽 30% → 이전.

하단 네비바: PREV / 페이지 카운터 / NEXT / EDIT / SAVE 버튼 + 상단 progress bar.

#### 인쇄/캡처 대응

```css
@media print {
  html, body { overflow: visible; height: auto; }
  .slide { display: flex !important; }  /* 모든 슬라이드 표시 */
  .nav-bar, .nav-progress, .edit-indicator { display: none !important; }
}
```

#### 포인트 컬러 사용 규칙 (슬라이드)

- 30장 기준 **10~13곳에서만** accent(`#6C5CE7`) 사용
- "포인트가 나타나면 반드시 의미가 있다" 원칙
- Hero Number, Peak 슬라이드 핵심 수치, 핵심 전환 텍스트에만 적용
- 나머지는 `--fg`, `--fg-2`, `--fg-3` + semantic color(`--green`, `--red`, `--amber`)

#### 레퍼런스 제안서

| 프로젝트 | 파일 | 비고 |
|---------|------|------|
| 세스크멘슬 브랜드 진단 | `10-projects/29-xescmenzl-sns/reports/xescmenzl-brand-proposal-2026-06-08.html` | 30p, 최초 적용 사례 |

---

### Column Span Reference

| Layout | Columns | Use |
|--------|---------|-----|
| Full width | 12 | Hero, cover, full-bleed |
| Two-thirds | 8 | Main content area |
| Half | 6 | Side-by-side comparison |
| One-third | 4 | Sidebar, KPI card |
| Quarter | 3 | Small card, thumbnail |

### 반응형 (@media ≤1200px)

```css
@media (max-width: 1200px) {
  .sec { padding: 80px 60px; }
  .brand-title { font-size: 72px; }
  .sec-head h2 { font-size: 32px; }
  .swatches { grid-template-columns: repeat(3, 1fr); }
  .comp-grid, .editor-grid, .voice-grid { grid-template-columns: 1fr; }
}
```

---

## 5. Component Library

### Color Swatch

```css
.sw {
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  cursor: pointer;
  transition: border-color var(--duration-base) var(--ease-out),
              transform var(--duration-base) var(--ease-out);
}
.sw:hover {
  border-color: var(--fg-3);
  transform: translateY(-2px);
}
.sw .chip { height: 100px; border-bottom: 1px solid var(--line-2); }
.sw .meta { padding: 14px 16px; }
.sw .name { font-size: 11px; letter-spacing: .2em; color: var(--fg-3); text-transform: uppercase; }
.sw .hex { font-size: 14px; color: var(--fg); font-variant-numeric: tabular-nums; }
```

### Info Card

```
┌───────────────────────────────────┐
│  LABEL (10px, FG-3, uppercase)    │
│  Value (17px, FG)                 │
└───────────────────────────────────┘
배경: var(--bg-3)
테두리: 1px var(--line-2)
패딩: 20px
```

### Compare Table

```css
.sample-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.sample-table th {
  font-size: 10px;
  letter-spacing: .2em;
  color: var(--fg-3);
  text-transform: uppercase;
  text-align: left;
  padding: 10px 12px 14px;
  font-weight: 400;
  border-bottom: 1px solid var(--line-2);
}
.sample-table td {
  padding: 12px;
  border-bottom: 1px solid var(--line-2);
  color: var(--fg-2);
}
.sample-table td:first-child {
  color: var(--fg-3);
  font-size: 10px;
  letter-spacing: .15em;
  text-transform: uppercase;
}
```

### Buttons

| 타입 | 배경 | 텍스트 | 테두리 | Hover |
|------|------|--------|--------|-------|
| Primary | `#6C5CE7` | `#111` | `#6C5CE7` | `#8577ED`, `#000` |
| Secondary | transparent | `var(--fg-2)` | `var(--line-2)` | `var(--fg-3)` border, `var(--fg)` text |
| Danger | transparent | `var(--fg-2)` | `var(--line-2)` | `#c0392b` border, `#e74c3c` text |

```css
button {
  background: transparent;
  border: 1px solid var(--line-2);
  color: var(--fg-2);
  padding: 10px 18px;
  font-size: 10px;
  letter-spacing: .25em;
  text-transform: uppercase;
  cursor: pointer;
  font-family: inherit;
  transition: all var(--duration-base) var(--ease-out);
}
button:hover {
  border-color: var(--fg-3);
  color: var(--fg);
  transform: translateY(-2px);
}
button.primary {
  background: var(--accent);
  color: #111;
  border-color: var(--accent);
}
button.primary:hover {
  background: #8577ED;
  color: #000;
}
```

### Swatch Palette (소재 팔레트)

```css
.sample-swatch {
  display: flex;
  gap: 6px;
}
.sample-swatch span {
  flex: 1;
  height: 28px;
  border: 1px solid var(--line-2);
}
```

### Component Grid Layout

```css
.comp-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}
.comp-card {
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  padding: 28px;
}
.comp-card h3 {
  font-size: 13px;
  letter-spacing: .25em;
  color: var(--accent);
  text-transform: uppercase;
  margin-bottom: 18px;
}
```

### Badge (상태 표시)

```css
.badge {
  display: inline-block;
  padding: 3px 10px;
  font-size: 10px;
  letter-spacing: .1em;
  font-weight: 400;
}
.badge-yes  { background: rgba(143,163,126,.12); color: var(--green); }
.badge-no   { background: rgba(225,112,85,.1);   color: var(--red); }
.badge-warn { background: rgba(217,163,75,.12);  color: var(--amber); }
.badge-info { background: var(--accent-subtle);   color: var(--accent-light); border: 1px solid rgba(108,92,231,.2); }
```

### Callout (강조 박스)

```css
.callout {
  background: rgba(108,92,231,.08);
  border-left: 3px solid var(--accent);
  padding: 24px 28px;
  margin: 24px 0;
}
.callout p       { color: var(--fg-2); font-size: 14px; margin: 0; line-height: 1.7; }
.callout strong  { color: var(--accent-light); }

/* 변형 */
.callout-success { background: rgba(143,163,126,.06); border-left-color: var(--green); }
.callout-success strong { color: var(--green); }
.callout-danger  { background: rgba(225,112,85,.06);  border-left-color: var(--red); }
.callout-danger strong  { color: var(--red); }
```

### Case Study (레퍼런스 카드)

보고서에서 레퍼런스 케이스를 소개할 때 사용. 좌측 accent border + 메타 그리드 + insight 박스.

```css
.case-study {
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  border-left: 3px solid var(--accent);
  padding: 28px 28px 20px;
  margin: 16px 0;
}
.case-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
.case-header h4 { font-size: 17px; font-weight: 500; color: var(--fg); }
.case-header .loc { font-size: 12px; color: var(--fg-3); margin-top: 4px; }
.case-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  margin: 16px 0;
  padding: 16px 0;
  border-top: 1px solid var(--line-2);
  border-bottom: 1px solid var(--line-2);
}
.case-meta .ml { font-size: 10px; letter-spacing: .2em; color: var(--fg-3); text-transform: uppercase; margin-bottom: 4px; }
.case-meta .mv { font-size: 13px; color: var(--fg); font-weight: 400; }
.case-insight {
  background: rgba(108,92,231,.08);
  border-left: 2px solid var(--accent);
  padding: 16px 18px;
  margin-top: 16px;
}
.case-insight p { font-size: 13px; color: var(--fg-2); margin: 0; }
.case-insight strong { color: var(--accent-light); }
```

### KPI 카드

```css
.kpi-grid   { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin: 24px 0; }
.kpi-grid-3 { grid-template-columns: repeat(3, 1fr); }

.kpi {
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  padding: 24px;
  text-align: center;
}
.kpi:hover     { border-color: var(--accent); }
.kpi .kpi-label { font-size: 10px; letter-spacing: .2em; color: var(--fg-3); text-transform: uppercase; margin-bottom: 8px; }
.kpi .kpi-value { font-size: 36px; font-weight: 200; color: var(--accent); line-height: 1.1; letter-spacing: -0.02em; }
.kpi .kpi-unit  { font-size: 16px; font-weight: 300; color: var(--fg-2); }
.kpi .kpi-sub   { font-size: 11px; color: var(--fg-3); margin-top: 6px; }
```

### Hero Number (대형 숫자 강조)

```css
.hero-number       { text-align: center; margin: 40px 0 24px; }
.hero-number .value { font-size: 72px; font-weight: 200; color: var(--accent); letter-spacing: -0.03em; line-height: 1; }
.hero-number .unit  { font-size: 24px; font-weight: 300; color: var(--fg-2); }
.hero-number .sub   { font-size: 13px; color: var(--fg-3); margin-top: 8px; }
```

### Steps (순서형 프로세스)

```css
.steps { margin: 24px 0; }
.step  { display: flex; gap: 18px; padding: 20px 0; border-bottom: 1px solid var(--line-2); }
.step:last-child { border-bottom: none; }
.step-num {
  width: 36px; height: 36px;
  background: var(--accent);
  color: var(--bg);
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 500;
  flex-shrink: 0;
}
.step-content h4 { font-size: 15px; font-weight: 500; color: var(--fg); margin: 0 0 6px; }
.step-content p  { font-size: 13px; color: var(--fg-2); margin: 0; }
.step-content .step-target { font-size: 11px; color: var(--accent-light); letter-spacing: .1em; margin-top: 6px; }
```

### Law Diagram (법규 중첩 레이어)

3단 중첩 레이어로 법적 관계를 시각화. 컬러 코딩: green(유연) > amber(중간) > red(제약적).

```css
.law-diagram { background: var(--bg-2); border: 1px solid var(--line-2); padding: 32px; margin: 24px 0; }
.law-layer   { border: 1px solid var(--line-2); padding: 20px; margin: 12px 0; position: relative; }
.law-layer.outer { border-color: var(--green); background: rgba(143,163,126,.03); }
.law-layer.mid   { border-color: var(--amber); background: rgba(217,163,75,.03);  margin: 12px; }
.law-layer.inner { border-color: var(--red);   background: rgba(225,112,85,.03);  margin: 12px; }
.law-layer-label {
  position: absolute; top: -9px; left: 16px;
  background: var(--bg-2); padding: 0 8px;
  font-size: 10px; letter-spacing: .2em; text-transform: uppercase;
}
.law-layer.outer .law-layer-label { color: var(--green); }
.law-layer.mid   .law-layer-label { color: var(--amber); }
.law-layer.inner .law-layer-label { color: var(--red); }
.law-core {
  text-align: center; padding: 16px;
  background: rgba(108,92,231,.08);
  border: 1px solid rgba(108,92,231,.2);
  margin-top: 14px;
}
.law-core p { color: var(--accent-light); font-weight: 500; font-size: 13px; }
```

### Floor Plan (공간 배치도)

컬러 코딩된 셀 그리드로 공간 배치를 시각화.

```css
.floor-plan  { background: var(--bg-2); border: 1px solid var(--line-2); padding: 32px; margin: 24px 0; }
.floor-label {
  font-size: 11px; font-weight: 500; letter-spacing: .2em;
  color: var(--accent); text-transform: uppercase;
  padding: 8px 14px;
  background: rgba(108,92,231,.08);
  border: 1px solid rgba(108,92,231,.15);
  display: inline-block; margin-bottom: 16px;
}
.floor-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
.floor-cell {
  padding: 18px 14px; text-align: center; min-height: 90px;
  display: flex; flex-direction: column; justify-content: center;
  border: 1px solid var(--line-2);
}
/* 영역별 컬러 코딩 */
.floor-cell.fb         { background: rgba(143,163,126,.06); border-color: rgba(143,163,126,.25); }
.floor-cell.exhibit    { background: rgba(108,92,231,.05);  border-color: rgba(108,92,231,.2); }
.floor-cell.shop       { background: rgba(217,163,75,.06);  border-color: rgba(217,163,75,.25); }
.floor-cell.meditation { background: rgba(111,138,163,.06); border-color: rgba(111,138,163,.25); }
.floor-cell.rental     { background: rgba(225,112,85,.05);  border-color: rgba(225,112,85,.2); }
.floor-cell .cell-name { font-size: 12px; font-weight: 500; color: var(--fg); }
.floor-cell .cell-area { font-size: 10px; color: var(--fg-3); margin-top: 4px; }
```

### Interpretation Scale (시나리오 비교)

3단 스케일 카드. 좁음(red) / 중간(amber) / 넓음(green) 의미 부여.

```css
.interpretation { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin: 24px 0; }
.interp-card    { padding: 28px; text-align: center; border: 1px solid var(--line-2); }
.interp-card.narrow { background: rgba(225,112,85,.04);  border-color: rgba(225,112,85,.2); }
.interp-card.mid    { background: rgba(217,163,75,.04);  border-color: rgba(217,163,75,.2); }
.interp-card.wide   { background: rgba(143,163,126,.04); border-color: rgba(143,163,126,.2); }
.interp-card .interp-label { font-size: 10px; letter-spacing: .25em; text-transform: uppercase; margin-bottom: 10px; }
.interp-card.narrow .interp-label { color: var(--red); }
.interp-card.mid    .interp-label { color: var(--amber); }
.interp-card.wide   .interp-label { color: var(--green); }
.interp-card .interp-value { font-size: 36px; font-weight: 200; color: var(--fg); letter-spacing: -0.02em; }
.interp-card .interp-unit  { font-size: 16px; font-weight: 300; }
.interp-card .interp-desc  { font-size: 12px; color: var(--fg-3); margin-top: 10px; }
```

### TOC (목차)

```css
.toc {
  background: var(--bg-2);
  border: 1px solid var(--line-2);
  padding: 28px 32px;
}
.toc h3 { font-size: 11px; letter-spacing: .3em; color: var(--accent); text-transform: uppercase; margin-bottom: 20px; }
.toc ol { list-style: none; counter-reset: toc; display: grid; grid-template-columns: 1fr 1fr; gap: 0 40px; }
.toc li {
  counter-increment: toc;
  padding: 10px 0;
  border-bottom: 1px solid var(--line-2);
  font-size: 13px;
}
.toc li::before { content: counter(toc, decimal-leading-zero); font-size: 10px; letter-spacing: .15em; color: var(--fg-3); margin-right: 12px; }
.toc a { color: var(--fg-2); }
.toc a:hover { color: var(--accent); }
```

### Sub Heading (섹션 내 소제목)

```css
h3.sub {
  font-size: 18px;
  font-weight: 500;
  color: var(--fg);
  margin: 40px 0 16px;
  letter-spacing: -0.01em;
}
h3.sub::before {
  content: '';
  display: inline-block;
  width: 3px;
  height: 18px;
  background: var(--accent);
  margin-right: 12px;
  vertical-align: text-bottom;
}
```

### Church Grid (2열 정보 카드)

```css
.church-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.church-card { background: var(--bg-3); border: 1px solid var(--line-2); padding: 24px; }
.church-card h4 { font-size: 15px; font-weight: 500; color: var(--fg); margin-bottom: 8px; }
.church-card .lesson {
  background: var(--bg-2);
  border-left: 2px solid var(--accent);
  padding: 12px 14px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--fg-2);
}
.church-card .lesson strong { color: var(--accent-light); }
```

---

## 6. Motion Tokens — Easing & Duration

### Duration

| Token | 값 | CSS Variable | 용도 |
|-------|-----|-------------|------|
| Fast | 150ms | `--duration-fast` | hover states, tiny toggles |
| Base | 250ms | `--duration-base` | card lift, reveals |
| Slow | 400ms | `--duration-slow` | slide transitions, modals |

### Easing Curves

| Token | 값 | CSS Variable | 용도 |
|-------|-----|-------------|------|
| Ease Out | `cubic-bezier(.2, .8, .2, 1)` | `--ease-out` | enter, reveal, hover |
| Ease In-Out | `cubic-bezier(.4, 0, .2, 1)` | — | state 전환 |

### 공통 Transition 패턴

```css
/* 카드 호버 */
transition: border-color var(--duration-base) var(--ease-out),
            transform var(--duration-base) var(--ease-out);

/* 스크롤 리빌 */
.sec {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 700ms var(--ease-out), transform 700ms var(--ease-out);
}
.sec.visible {
  opacity: 1;
  transform: translateY(0);
}
```

### Reduced Motion 대응

```css
@media (prefers-reduced-motion: reduce) {
  .sec { opacity: 1; transform: none; transition: none; }
  * { transition: none !important; animation: none !important; }
}
```

---

## 7. Reference Library 구조

레퍼런스 갤러리 4카테고리 × 4장 = 16장 구성:

| 카테고리 | 테마 | Borrow |
|----------|------|--------|
| Option 01 · Raw | SKWAT & Scaffold | 단관 파이프 · 가설 긴장감 |
| Option 02 · Refined ★ | Blue Bottle & Aesop | 매트 블랙 · 공간의 침묵 |
| Option 03 · Warm | Warm Frame Cafes | 소재 믹스 · 브라스 조인트 |
| Editorial | Magazine Typography | 여백 미학 · 위계 조합 |

### 썸네일 스타일

```css
.ref-thumb {
  aspect-ratio: 3/2;
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  overflow: hidden;
  cursor: pointer;
  transition: transform var(--duration-base) var(--ease-out),
              border-color var(--duration-base) var(--ease-out);
}
.ref-thumb:hover {
  transform: translateY(-3px);
  border-color: var(--accent);
}
.ref-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: grayscale(.15) contrast(1.05);
  transition: transform var(--duration-slow) var(--ease-out);
}
.ref-thumb:hover img {
  transform: scale(1.04);
  filter: grayscale(0) contrast(1.05);
}
```

---

## 8. Voice & Tone — Copy Guide

### Do

- 선언형 짧은 카피 — "누구나 필요할 때, 필요한 곳에 자신만의 매장을."
- 구체적 수치·재료 — "300회 이상의 팝업서비스 이력"
- "왜"를 먼저 — 옵션 소개 전에 해결할 문제를 한 줄로
- 매거진 위계 — 영문 라벨(작게) + 한글 타이틀(크게) + 본문(중간)
- 질문형 또는 선언형 헤드라인 — 짧고 임팩트 있게

### Don't

- 제너릭 히어로 — "Welcome to...", "Unlock the power of..."
- 과도한 감탄사·이모지 금지
- 모호한 형용사 — "혁신적", "종합적", "다채로운"
- 포인트 컬러 남용 — 한 슬라이드에 청보라 2곳 이상
- 단순 복사 — 레퍼런스 그대로가 아닌 재해석 필수

### 숫자 강조 패턴

```
대형 숫자 (Display) + 단위 + 맥락 설명
예: "300회" + "이상의 팝업서비스 이력"
예: "85%" + "재방문 의향률"
```

### 크레딧 표기 규칙

**모든 브랜딩/제안서/전략 자료**의 크레딧은 반드시 **"by Project Rent"**로 표기.

| 위치 | 표기 형식 |
|------|----------|
| 커버 메타 | `By: Project Rent` |
| 푸터/마지막 페이지 | `Project Rent × 2026.06.08` |
| Prepared by | `Prepared by Project Rent · ws.choi@project-rent.com` |

- "Do Better Things"는 워크스페이스명이지 크레딧 주체가 아님
- RXR 리포트는 별도 헤더·푸터 가이드 준수 (이미 Project Rent 명의)
- 클라이언트 내부용이든 외부 전달용이든 동일하게 적용

---

## 9. Navigation

### Fixed Side Nav

```css
.nav {
  position: fixed;
  top: 50%;
  left: 30px;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 14px;
  font-size: 10px;
  letter-spacing: .2em;
  color: var(--fg-3);
  text-transform: uppercase;
}
.nav a {
  color: var(--fg-3);
  text-decoration: none;
  transition: color var(--duration-fast) var(--ease-out);
}
.nav a:hover { color: var(--fg); }
```

### Brand Mark

```css
.brand-mark {
  position: fixed;
  top: 24px;
  right: 30px;
  font-size: 10px;
  letter-spacing: .35em;
  color: var(--fg-3);
}
```

---

## 10. Toast / Feedback

```css
#toast {
  position: fixed;
  bottom: 30px;
  right: 30px;
  background: rgba(20, 20, 20, .92);
  backdrop-filter: blur(10px);
  border: 1px solid var(--accent);
  color: var(--fg);
  padding: 12px 20px;
  font-size: 11px;
  letter-spacing: .2em;
  text-transform: uppercase;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity var(--duration-base) var(--ease-out),
              transform var(--duration-base) var(--ease-out);
  pointer-events: none;
  border-radius: 2px;
}
#toast.show {
  opacity: 1;
  transform: translateY(0);
}
```

---

## 11. Edit Mode (Interactive HTML)

HTML 제안서/디자인시스템 파일에 내장되는 편집 기능:

| 기능 | 설명 |
|------|------|
| 편집 모드 | URL에 `?edit=true` 추가 → contenteditable 토글 |
| 포인트 컬러 변경 | `--accent` CSS Variable 전역 변경 (컬러 피커) |
| 이미지 교체 | 레퍼런스 썸네일 클릭 → 파일 업로드 → base64 내장 |
| HTML 저장 | 편집 UI 제거된 깨끗한 클론 다운로드 |
| 초기화 | localStorage 일괄 삭제 |
| 자동 저장 | 변경 시 400ms 디바운스로 localStorage 자동 저장 |

---

## 12. Footer

```css
footer {
  padding: 80px 120px 60px;
  border-top: 1px solid var(--line-2);
  max-width: 1440px;
  margin: 80px auto 0;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
footer .logo {
  font-size: 13px;
  letter-spacing: .4em;
}
footer .meta {
  font-size: 10px;
  letter-spacing: .2em;
  color: var(--fg-3);
}
```

---

## 13. Print / 캡처 대응

```css
@media print {
  .nav, #toast, .edit-panel { display: none; }
  .sec { opacity: 1; transform: none; }
}

/* PPT 캡처 시 편집 UI 제거 */
body.capturing .edit-panel,
body.capturing #toast { display: none !important; }
```

---

## 14. 적용 범위

이 가이드는 아래 모든 산출물에 기본 적용:
- 컨셉 제안서 / 사업계획서
- IR 덱 / 투자 소개서
- 대시보드 / 웹 UI
- 디자인 시스템 HTML
- 슬라이드 / 프레젠테이션
- 내부 문서 / 보고서
- 마케팅 자료

별도 지시가 없는 한, 모든 디자인 관련 작업에 이 가이드를 따릅니다.

---

## 15. Quick Reference — 자주 쓰는 패턴

### 다크 배경 기본 세트
```css
html, body {
  background: var(--bg);
  color: var(--fg);
  font-family: 'Pretendard Variable', 'Pretendard', -apple-system, sans-serif;
  font-weight: 300;
  letter-spacing: -0.01em;
}
h1, h2, h3, h4 {
  text-wrap: balance;
  font-weight: 500;
}
```

### 카드 기본 패턴
```css
.card {
  background: var(--bg-3);
  border: 1px solid var(--line-2);
  padding: 28px;
  transition: border-color var(--duration-base) var(--ease-out),
              transform var(--duration-base) var(--ease-out);
}
.card:hover {
  border-color: var(--fg-3);
  transform: translateY(-2px);
}
```

### 액센트 강조 라인
```css
border-top: 1px solid var(--accent);  /* 또는 border-left */
```

### Section Head 패턴
```css
.sec-head .eyebrow { font-size: 11px; letter-spacing: .3em; color: var(--fg-3); text-transform: uppercase; }
.sec-head h2 { font-size: 44px; font-weight: 300; letter-spacing: -0.025em; line-height: 1.1; }
.sec-head .no { font-size: 11px; letter-spacing: .2em; color: var(--fg-3); }
```

### Compare Table (비교 매트릭스)

```css
.compare-table thead th { text-align: center; }
.compare-table thead th:first-child { text-align: left; }
.compare-table tbody td { text-align: center; font-size: 13px; }
.compare-table tbody td:first-child { text-align: left; font-weight: 500; color: var(--fg); }
```

---

## 16. Living Examples — 제작 산출물 아카이브

이 디자인 시스템을 적용하여 제작한 산출물 목록.

| 날짜 | 프로젝트 | 산출물 | 경로 | 비고 |
|------|---------|--------|------|------|
| 2026-06-03 | 봉은문화회관 | 공간활용 통합 제언 보고서 | `10-projects/15-bongeunsa/봉은문화회관-공간활용-통합제언-보고서.html` | 10개 섹션 스크롤 매거진, 다크 테마 최초 적용 |

---

*이 가이드는 FILAMENT&CO Design System v1 구조를 기반으로, PROJECT RENT 브랜드에 맞게 포인트 컬러(청보라 #6C5CE7)와 컨텍스트를 적용하여 작성되었습니다.*
*v2 업데이트: grid-system.md의 공간 배치 규칙 전체를 §4 Layout System에 통합 (2026-06-08)*
