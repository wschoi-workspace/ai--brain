---
description: "RXR Mention Analysis. 브랜드명 지정 → 네이버 블로그 API 크롤링 → Sincerity Filter(A~G + Trust Score) → 2-Layer(Content+Psyche) → Linguistic Layer(6차원 언어학 분석 + LAI/EDS) → 심리학-언어학 브릿지 보정 → HTML 시각화 리포트. 기존 rxr-sns-analysis의 이벤트/팝업 기반과 달리, 상시 브랜드 멘션 분석에 특화. 감정 수치화 + 언어학적 진정성 교차검증."
allowed-tools: WebSearch, WebFetch, Read, Write, Edit, Bash, Agent, Grep, Glob
---

> **📌 HTML 리포트 헤더·푸터 필수 적용**
> 이 스킬이 생성하는 모든 HTML 리포트에는 반드시 `rxr-report-header-footer-guide.md`의 §2 헤더와 §3 푸터를 **수정 없이 그대로** 삽입해야 합니다.
> - 헤더: `<body>` 안 첫 `<h1>` 바로 앞
> - 푸터: `</body>` 바로 앞
> - 가이드 경로: `.claude/skills/rxr-report-header-footer-guide.md`

# RXR Mention Analysis

브랜드의 SNS/온라인 멘션을 크롤링하고, **Sincerity Filter + 2-Layer + Linguistic Layer**로 분석하여 감정적 인게이지먼트를 수치화하는 통합 파이프라인.

**기존 rxr-sns-analysis와의 차이:**

| 구분 | rxr-sns-analysis | rxr-mention-analysis |
|------|-----------------|---------------------|
| 분석 대상 | 이벤트/팝업 (시한부) | 브랜드 상시 멘션 |
| 기간 설정 | 이벤트 전2주+기간+후4주 | 최근 N일 (기본 30일) |
| 분석 레이어 | 2-Layer (Content+Psyche) | 3-Layer (+ Linguistic) |
| 진정성 검증 | Auth 단일 지표 | Auth + LAI 교차검증 |
| 리뷰 깊이 | 글자수 기반 RQL | + 담화 복잡성 기반 승격 |
| 문체 분석 | 없음 | 레지스터 분류 + 템플릿 탐지 |
| 인지 깊이 | 없음 | EDS (Engagement Depth Score) |
| 이론 기반 | 심리학 (ELM, CLT, eWOM) | + 언어학 (Pennebaker LIWC, 화용론) |

**핵심 철학:** "몇 건 언급되었는가"가 아니라 "어떤 감정으로, 얼마나 진정성 있게, 얼마나 깊이 인게이지되었는가"를 수치화.

---

## 입력 파라미터 확인

사용자 입력에서 아래 정보를 추출합니다. 누락된 항목은 질문하세요:

| 항목 | 필수 | 예시 |
|------|:---:|------|
| **브랜드명** | 필수 | "자이리톨", "새로 소주" |
| **분석 기간** | 선택 (기본: 최근 30일) | "최근 7일", "2026-03-01 ~ 2026-04-26" |
| **경쟁사** | 선택 | "트라이덴트, 후라보노" |
| **카테고리** | 선택 (자동 추론) | "껌", "소주", "화장품" |

---

## 실행 프로세스

### STEP 1: 프로젝트 설정

#### 1-1. 프로젝트 폴더 확인/생성

`10-projects/` 아래에 프로젝트 폴더가 있는지 확인. 없으면 생성:

```
10-projects/{번호}-{브랜드명}-sns/
  config.json    — 검색 키워드, 경쟁사, 분석 파라미터
  data/          — 크롤링 원본 + 처리 데이터
  reports/       — HTML/Excel 리포트
```

#### 1-2. config.json 생성/업데이트

기존 config가 있으면 재활용. 없으면 아래 구조로 생성:

```json
{
  "project": "{브랜드명} SNS 감정분석",
  "version": "1.0.0",
  "created": "{오늘 날짜}",
  "brand": {
    "name": "{브랜드명}",
    "company": "{모회사}",
    "aliases": ["{별칭1}", "{별칭2}"],
    "products": ["{제품1}", "{제품2}"]
  },
  "search": {
    "queries": ["{브랜드명} 후기", "{브랜드명} 추천", "{브랜드명} 리뷰", ...],
    "hashtags": ["#{브랜드명}", ...],
    "noise_exclusion": ["{제외 키워드}"]
  },
  "competitors": {
    "brands": [{"name": "{경쟁사}", "aliases": []}],
    "category_keywords": ["{카테고리 키워드}"]
  },
  "crawl": {
    "platforms": ["naver_blog"],
    "naver": {
      "display": 100,
      "max_start": 901,
      "sort_modes": ["sim", "date"],
      "delay_seconds": 0.3,
      "max_content_length": 5000
    }
  },
  "analysis": {
    "topics": { "{토픽명}": ["{키워드}", ...] },
    "sentiment": {
      "positive": ["{긍정 키워드}"],
      "negative": ["{부정 키워드}"]
    },
    "sponsored_markers": ["제공받", "협찬", "원고료", "체험단", "#광고", "#ad", ...],
    "experience_signals": ["{경험 신호 키워드}"],
    "detail_signals": ["{디테일 키워드}"]
  },
  "linguistic_layer": {
    "certainty_markers": {
      "high": ["확실히", "분명히", "무조건", "진짜", "당연히"],
      "hedge": ["좀", "약간", "것 같아요", "인 듯", "편이에요", "느낌"]
    },
    "discourse_markers": {
      "contrast": ["근데", "그런데", "다만", "아쉬운 점은", "하지만"],
      "conditional": ["라면", "경우에", "좋아하시면"],
      "causal": ["그래서", "덕분에", "때문에"]
    },
    "sensory_vocabulary": {
      "{감각 카테고리}": ["{감각어}"]
    },
    "register_patterns": {
      "formal": ["습니다", "합니다", "됩니다", "입니다"],
      "polite_informal": ["어요", "아요", "에요", "해요", "거든요", "더라고요"],
      "casual": ["ㅋㅋ", "ㅎㅎ", "ㅠㅠ", "임", "음", "함"]
    }
  },
  "output": {
    "data_dir": "10-projects/{번호}-{브랜드명}-sns/data",
    "reports_dir": "10-projects/{번호}-{브랜드명}-sns/reports",
    "scripts_dir": "80-r-tech/84-scripts/{브랜드명}"
  }
}
```

**토픽/감성 키워드는 브랜드 카테고리에 맞게 커스터마이징.** 기존 자이리톨 config(`10-projects/25-xylitol-sns/config.json`)을 참조 템플릿으로 활용.

---

### STEP 2: 네이버 블로그 크롤링

**실행 스크립트:** `80-r-tech/84-scripts/{브랜드명}/{브랜드명}_crawl.py`
기존 크롤러가 없으면 `80-r-tech/84-scripts/xylitol/xylitol_crawl.py`를 복사하여 config 경로만 변경.

```bash
python3 80-r-tech/84-scripts/{브랜드명}/{브랜드명}_crawl.py --days {N}
```

#### 크롤링 프로세스 (자동)

1. **네이버 검색 API** (`.env`의 NAVER_CLIENT_ID/SECRET)
   - 키워드별 최대 1,000건 페이징 (start=1~901, display=100)
   - sim(관련도) + date(최신) 병행
   - 중복 제거 (link 기준)

2. **3단계 필터링**
   - 날짜 필터: 최근 N일 이내
   - 관련성 필터: 브랜드명/별칭 포함 확인
   - 노이즈 제외: noise_exclusion 키워드

3. **본문 크롤링**
   - 네이버 블로그 모바일 버전에서 본문 추출
   - 4-패턴 순차 시도 (se-main-container → post-view → se-component → body)
   - 0.3초 딜레이

**저장:** `data/{날짜}/naver-raw.json`, `data/{날짜}/naver-enriched.json`

---

### STEP 3: Sincerity Filter

#### 3-1. Content Class 분류 (A~G)

| 등급 | 분류 | 감지 방법 | 분석 처리 |
|:---:|------|------|------|
| **A** | 진성후기 | 경험 신호 2건+ & 디테일 3건+ | 3-Layer 핵심 대상 |
| **B** | 일반포스트 | 특별 플래그 없음, 브랜드 관련 | 3-Layer 분석 대상 |
| **C** | 협찬/체험단 | 협찬 마커 감지 | 3-Layer 분석 (진심 스펙트럼) |
| **D** | 나열형정보 | "총정리", "리스트", "모음" | 버즈량만 카운트 |
| **E** | 리그램/단순공유 | "리그램", 극히 짧은 텍스트 | 버즈량만 카운트 |
| **F** | 비즈니스/보도자료 | 보도자료 문구 or 비즈 신호 | 제외 또는 카운트만 |
| **G** | 노이즈 | 브랜드 키워드 미포함 | 제외 |

#### 3-2. Trust Score (0~100)

기본 100점에서 감점/가점. 70+ = 신뢰, 40~69 = 주의, ~39 = 필터 대상.

---

### STEP 4: 2-Layer 분석 (Content + Psyche)

**대상:** Content Class A + B + C

#### 4-1. Content Layer (무엇을 말했는가)

- **토픽 분석**: config의 토픽 사전 기반 키워드 빈도 → 상위 3개
- **감성 분석**: 긍정/부정/혼합/중립 4-way
- **RQL (Review Quality Level)**: Q5(서사)~Q1(간단) 5등급 + 가중치

#### 4-2. Psyche Layer (어떻게 말했는가)

- **대명사 패턴**: 1인칭/복수형/장소참조
- **Freshness Index (CLT 기반)**:
  - **한국어**: "이/가"(발견) vs "은/는"(설명) 조사 비율 — 단일 피처
  - **영어**: 7-피처 가중 합산 모델 (`freshness/freshness_en.py`)
    - Discovery verbs ×25, Temporal proximity ×20, Progressive aspect ×15,
      Proximal demonstratives ×15, Present perfect+just ×10, Exclamatory ×10, Sensory ×5
    - 보정: 극단적 근접 +5, 원거리 표지 ≥2개 -5, 내러티브 현재 +3
  - **팩토리**: `freshness/freshness_factory.py` — lang='ko'|'en' 분기
- **Authenticity (0~100)**: 기본60 + 경험/디테일 가점 - 협찬/과잉긍정 감점
- **Clout (0~100)**: 추천 표현, 조건부 추천, 정체성 선언 등

---

### STEP 5: Linguistic Layer (언어학적으로 어떻게 말했는가)

**이 단계가 기존 rxr-sns-analysis에 없는 핵심 차별화.**

**실행:** `80-r-tech/84-scripts/{브랜드명}/{브랜드명}_pipeline.py --skip-crawl`

#### 5-1. 6차원 언어학 분석

| 차원 | 측정 내용 | 심리학 연결 |
|------|----------|------------|
| **형태소 분포** | 감각어 밀도, 명사/동사/형용사 비율 | 체험 진정성 → Auth 보정 |
| **기능어 패턴** | 대명사(나/우리), 조사, 어미 (Pennebaker) | 심리 상태 추론 → Auth/Freshness |
| **확신도 스펙트럼** | 확신어 vs 완화어(헤징) 비율 | 인식론적 확실성 → 신뢰도 |
| **담화 표지** | 대조("근데"), 조건("~라면"), 인과("그래서") | ELM 정교화 경로 → RQL 보정 |
| **화용론** | 간접부정, 수사적 질문, 축소어법 | 4-way Sentiment 정밀화 |
| **문체 레지스터** | 해요체/해체/합쇼체 + 일관성 | 템플릿/PR 탐지 → Trust Score |

#### 5-2. 복합 지표

**LAI (Linguistic Authenticity Index, 0~100)**
```
LAI = (감각어밀도 × 30) + (헤징자연도 × 20) +
      (레지스터변동 × 20) + (시간근접성 × 15) + (1인칭자연도 × 15)
```

**EDS (Engagement Depth Score, 0~100)**
```
EDS = (은유밀도 × 25) + (담화복잡성 × 25) +
      (한정표지 × 25) + (구체적디테일 × 25)
```

#### 5-3. 심리학-언어학 브릿지 보정

| 언어학 피처 | 조건 | 보정 |
|------------|------|------|
| 감각어 밀도 | >3/100단어 | Auth +8 |
| 1인칭 비율 | 5~15% 자연 범위 | Auth +5 |
| 적절한 헤징 | certainty 20~60 | Auth +3~5 |
| 과잉 확신+과잉 긍정 | certainty>80 & extreme_pos>5 | Auth -5 |
| 시간근접 표지 | "오늘","방금" 존재 | Freshness +5 |
| 합쇼체 일관 | consistency>95% & formal | Trust -10 |
| 자연 레지스터 전환 | consistency 60~85% | Auth +3 |
| 대조 표지 ≥2개 | 담화 복잡성 | Auth +5 |
| discourse_score ≥40 | Q3 리뷰 | RQL Q3→Q4 승격 |
| 간접 부정 | "나쁘진 않은데" | Sentiment 중립→혼합 |
| 조건부 추천 | "~라면 추천" | Clout +10 |

#### 5-4. LAI-Auth 교차검증

| |LAI - Auth| | 해석 | 조치 |
|:---:|------|------|
| ≤10 | 일치 | 그대로 사용 |
| 11~20 | 경미한 불일치 | 참고 표시 |
| >20 | **유의미한 괴리** | 플래그 → 수동 검토 |

> **주의:** LAI v1.0은 팝업/이벤트 기준으로 설계됨. FMCG 등 일상 제품은 감각어/시간표지가 구조적으로 낮아 LAI가 낮게 나옴. 카테고리별 캘리브레이션 필요.

---

### STEP 6: HTML 시각화 리포트 생성

**R Design Guide 준수**: Pretendard Variable, 기본 보라 #6C5CE7

리포트에 포함할 섹션:

1. **KPI 헤더** — 유효건수, Auth, LAI, EDS, RQL 승격 수
2. **기존 RXR vs Linguistic Layer 비교** — Before/After 카드
3. **Linguistic Layer 발견** — Auth 보정 분포 + 문체 레지스터
4. **언어학 신규 지표** — 확신도 스펙트럼 + 감각어 밀도
5. **감성 분포 & 토픽** — 4-way 바 + 토픽 분포
6. **RQL 변화** — 담화 복잡성 기반 승격 상세
7. **Content Class & Sincerity Filter** — A~G 분포 + 협찬 Auth 비교
8. **방법론 차이 테이블** — 9개 차원 비교표
9. **LAI 캘리브레이션 노트** — v1.0 한계
10. **핵심 마케팅 인사이트** — 데이터 기반 액션 포인트

**참조 템플릿:** `10-projects/25-xylitol-sns/reports/xylitol-linguistic-report-2026-04-26.html`

HTML 생성 후 **Playwright로 PNG 스크린샷** 저장.

---

### STEP 7: 통계 요약 출력

콘솔에 핵심 수치 출력:

```
=== {브랜드명} SNS Mention Analysis ===
전체: {N}건 → 유효 A+B+C: {N}건 (유효율 {N}%)

[기존 RXR]  Auth {N} / Clout {N} / Freshness {N}
[+ Linguistic] Auth {N} (+{N}) / LAI {N} / EDS {N}

감성: 긍정 {N}% / 혼합 {N}% / 중립 {N}% / 부정 {N}%
RQL 승격: {N}건 (Q3→Q4)
문체: 해요체 {N}% / 합쇼체 {N}% / 해체 {N}%
LAI-Auth 괴리 플래그: {N}건
```

---

## 참조 파일

| 파일 | 용도 |
|------|------|
| `80-r-tech/84-scripts/xylitol/xylitol_crawl.py` | 크롤러 템플릿 (복사하여 재활용) |
| `80-r-tech/84-scripts/xylitol/xylitol_pipeline.py` | 파이프라인 템플릿 |
| `10-projects/25-xylitol-sns/config.json` | config 템플릿 |
| `10-projects/25-xylitol-sns/reports/xylitol-linguistic-report-2026-04-26.html` | HTML 리포트 템플릿 |
| `.claude/skills/rxr-sns-linguistic-layer.md` | Linguistic Layer 상세 스펙 |
| `.claude/skills/rxr-sns-analysis.md` | 기존 RXR 프레임워크 (Sincerity Filter/2-Layer 상세) |
| `80-r-tech/81-framework/function-word-analysis-research.md` | 기능어분석 리서치 |
| `30-knowledge/34-consumer-psychology/` | 소비자 심리학 62이론 |

---

## 새 브랜드 분석 시 Checklist

1. [ ] 프로젝트 폴더 생성 (`10-projects/{번호}-{브랜드}-sns/`)
2. [ ] config.json 작성 (토픽/감성 키워드를 카테고리에 맞게 커스터마이징)
3. [ ] 크롤러 스크립트 복사 및 config 경로 수정
4. [ ] `python3 {브랜드}_crawl.py --days 30` 실행
5. [ ] `python3 {브랜드}_pipeline.py --skip-crawl` 실행 (Linguistic Layer)
6. [ ] HTML 리포트 생성 (템플릿 기반)
7. [ ] Playwright 스크린샷
8. [ ] 핵심 인사이트 해석 및 마케팅 시사점 도출
