---
description: "RXR SNS Value Analysis (EMV). BEI 4축 → EMV(Estimated Media Value) 금전적 가치 전환. 3단계 전환 체인(Sentiment→Behavioral→Monetization) + 업종별 파라미터 + Decay-adjusted 4주 누적 + ROI 산출 → HTML 시각화 리포트. '이 캠페인이 돈으로 얼마짜리인가'를 답한다."
allowed-tools: WebSearch, WebFetch, Read, Write, Edit, Bash, Agent, Grep, Glob
---

> **📌 HTML 리포트 헤더·푸터 필수 적용**
> 이 스킬이 생성하는 모든 HTML 리포트에는 반드시 `rxr-report-header-footer-guide.md`의 §2 헤더와 §3 푸터를 **수정 없이 그대로** 삽입해야 합니다.
> - 헤더: `<body>` 안 첫 `<h1>` 바로 앞
> - 푸터: `</body>` 바로 앞
> - 가이드 경로: `.claude/skills/rxr-report-header-footer-guide.md`

# RXR SNS Value Analysis (EMV)

기존 `/rxr-sns-analysis` 또는 `/rxr-sns-analysis-follow`로 생성된 BEI 데이터를 기반으로, **BEI 4축을 금전적 가치(₩)로 전환**하여 캠페인의 Estimated Media Value를 산출합니다.

**핵심 산출물:** 4축별 EMV + Decay-adjusted 4주 누적 가치 + ROI/효율 지표 + 업종별 벤치마크

> **⚠️ v3 외부 배포 용어 표준 (특허 청구항 정합)**
>
> 이 스킬이 산출하는 EMV·BEI 데이터는 특허 청구항 5(가치 환산 독립항)의 핵심 보호 대상이다. 클라이언트 배포용 HTML(`-external.html`, `-locked.html`)을 생성할 때는 반드시 v3 추상화 명칭만 사용한다.
>
> **사용**: 추정 미디어 가치 / 수용자 인게이지먼트 종합 지수 / 심리 신뢰성 지표 / 발언 강도 지표 / 정보 갱신성 지표 / 다단 정제 절차 / 1·2·3단계 정제 / 심도 1~5등급 / 이중 계층 분석
>
> **금지**: ~~EMV~~, ~~BEI~~, ~~Auth~~, ~~Clout~~, ~~Freshness~~, ~~Gate~~, ~~Sincerity Filter~~, ~~RQL~~, ~~Q1~Q5~~, ~~진정성 지수~~, ~~추천 확신도~~, ~~신선함 지수~~, ~~진심 필터~~
>
> **수치 은닉 (가장 중요)**:
> - 업종별 파라미터 테이블(F&B/패션/공간/테크의 CLV·CR·beta·gamma 등 구체값) — **완전 은닉**
> - 규모 보정 계수(×1.2~×0.6) — **완전 은닉**
> - 축별 감쇠 함수 형태(e^(-0.036t), 역상승 등) — **완전 은닉**
> - 청구항 5 진보성의 핵심은 "심리지표→행동효과 비선형 매핑"이므로 매핑 공식·중간 단위는 절대 노출 금지
>
> **노출 가능**: 최종 ₩ 결과값, ROI %, "F&B 업종 평균 대비" 같은 정성적 비교
>
> 4축 동시 노출 금지 — 최대 3개까지(관여 깊이/추천 강도/진정 비율/발견 신선도 중)
>
> 상세 변환표는 `rxr-sns-analysis.md` line 432 참조.

---

## EMV란 무엇인가

### 한 줄 정의

> **EMV(Estimated Media Value)** = BEI 4축이 만들어내는 마케팅 효과를, 같은 효과를 paid media로 사려면 얼마를 써야 하는지로 환산한 추정 가치

### 왜 필요한가

BEI는 "사람들이 얼마나 진심으로 좋아하는지"를 보여주지만, 클라이언트의 핵심 질문은 결국:

- "BEI 57.6이 **돈으로 얼마**인가?"
- "이 캠페인에 3억 썼는데 **본전은 뽑았나**?"
- "다음 분기 예산을 이 채널에 **더 써도 되나**?"

EMV는 이 질문에 답합니다.

### 전환 불가 원칙

BEI → ₩ **직접 전환은 불가능**합니다. BEI는 심리/행동 프록시이지 매출 자체가 아닙니다. 따라서 마케팅 경제학에서 검증된 중간 변수를 경유하는 **3단계 전환 체인**을 사용합니다:

> **📌 직접 전환이 불가능한 행동경제학적 근거**
> - **심적 회계(Mental Accounting, Thaler)**: 소비자는 "팝업 체험"과 "제품 구매"를 다른 심리적 계좌에서 처리. 팝업에서 감동(BEI↑)해도 구매는 별도 의사결정이며, 다른 예산·맥락·동기에서 작동.
> - **현상 유지 편향(Status Quo Bias, Samuelson & Zeckhauser)**: 기존 브랜드/제품을 쓰던 관성이 새로운 브랜드로의 전환을 막음. BEI가 높아도 전환 장벽(습관, 전환 비용, 접근성)은 별개 변수.
> - **쌍곡선 할인(Hyperbolic Discounting, Ainslie)**: 팝업 직후의 구매 의도(T+0)와 1주 후 실제 구매(T+1w)는 시간 할인으로 급격히 차이남. "꼭 사야지" → "나중에" → "잊음"의 패턴. 이것이 Advocacy Rapid Decay와 연동되는 현상.

```
[Stage 1] BEI 4축 (0~100)
    ↓ 축별 행동 전환 계수
[Stage 2] 마케팅 효과 단위 (재구매율, 신규고객수, 전환율 리프트, Earned Media)
    ↓ 업종별 단가
[Stage 3] ₩ (EMV)
```

### 4축 → 경제적 경로 매핑

| BEI 축 | 경제적 경로 | 산출하는 가치 |
|--------|------------|-------------|
| **Depth** (관여 깊이) | 재구매/재방문 | 깊이 관여한 사람이 다시 오는 가치 (Retention) |
| **Advocacy** (추천 강도) | 신규 고객 획득 | 추천으로 유입되는 신규 고객 가치 (Viral Acquisition) |
| **Sincerity** (진심 비율) | 전환율 프리미엄 | 진성 리뷰가 전환율을 높이는 가치 (Conversion Lift) |
| **Discovery** (발견 신선함) | Earned Media | 자발적 공유가 광고비를 대체하는 가치 (Media Savings) |

> **📌 Sincerity → 전환율 경로의 학술적 근거**
> - **리뷰 품질 > 리뷰 양 (Ismagilova et al., 2020 메타분석)**: 69개 연구에서 논거 품질(★★★★★)이 리뷰 양(★★☆☆☆)보다 구매 의도에 압도적으로 강한 영향. Sincerity가 높다는 것 = 진성 리뷰 비율 높음 = 잠재 고객이 접하는 리뷰의 논거 품질 상승 = 전환율 프리미엄.
> - **리뷰 있는 상품 전환율 +270% (Spiegel Research Center, 2017)**: 리뷰 존재 자체가 전환율을 높이지만, 진성 리뷰의 전환 효과가 협찬/의무 리뷰보다 현저히 큼. Gate 3 통과 비율(Sincerity)이 높은 캠페인일수록 V_sincerity의 실제 정확도 상승.
> - **구매 후 합리화 골든 타이밍**: 구매 후 2-3일 시점에 작성된 리뷰는 만족감 + 인지 부조화 해소가 동시에 작동하여 Auth가 자연적으로 높아지는 경향. 이 시점의 리뷰가 Gate 3 통과율이 가장 높음.

---

## 입력 파라미터 확인

사용자 입력에서 아래 정보를 추출합니다. 누락된 항목은 질문하세요:

| 항목 | 필수 | 예시 |
|------|------|------|
| **기존 분석 파일** | 필수 | `30-knowledge/saero-popup-rxr-sns-report.html` 또는 BEI JSON/follow 리포트 |
| **브랜드명** | 필수 (기존 분석에서 추출 가능) | "새로 소주" |
| **이벤트명** | 필수 (기존 분석에서 추출 가능) | "새로중앙박물관" |
| **업종** | 필수 | F&B/주류, 패션/뷰티, 공간/팝업, 테크/SaaS |
| **규모** | 필수 | 소형(~10억), 중형(10~100억), 대형(100~1000억), 메가(1000억+) |
| **캠페인 비용** | 선택 (ROI 산출용) | 3억 원 |
| **BEI follow-up 데이터** | 선택 (Decay 적용용) | bei-tracking.json 또는 follow 리포트 |

---

## EMV 산출 공식

### 공통 모수

| 모수 | 기호 | 설명 | 입력 방법 |
|------|------|------|-----------|
| 도달 모수 | R | 캠페인 기간 총 노출 수 | 수동 입력 또는 SNS 도구 추정 |
| 전체 게시물 수 | N | Gate 1 전체 수 | BEI 분석에서 자동 |
| Gate 3 게시물 수 | N_g3 | Sincerity 통과 수 | BEI 분석에서 자동 |
| 고객 생애 가치 | CLV | 업종 테이블 또는 수동 | 업종별 기본값 제공 |
| 고객 획득 비용 | CAC | 업종 테이블 또는 수동 | 업종별 기본값 제공 |
| 기본 전환율 | CR_base | 업종 평균 | 업종별 기본값 제공 |
| 평균 주문 금액 | AOV | 업종 평균 | 업종별 기본값 제공 |
| CPM 기준가 | CPM | 1,000 impression 단가 | 플랫폼별 시세 |
| 캠페인 비용 | C_campaign | 실제 집행 비용 | 수동 입력 |

### 업종별 파라미터 테이블

| 파라미터 | F&B/주류 | 패션/뷰티 | 공간/팝업 | 테크/SaaS | 기본값 |
|---------|:-------:|:-------:|:-------:|:-------:|:----:|
| CLV | 150,000 | 500,000 | 80,000 | 2,000,000 | 200,000 |
| CAC | 25,000 | 40,000 | 15,000 | 100,000 | 30,000 |
| CR_base | 2.5% | 1.8% | 3.5% | 1.2% | 2.0% |
| AOV | 15,000 | 80,000 | 25,000 | 200,000 | 50,000 |
| CPM | 5,000 | 8,000 | 4,000 | 12,000 | 6,000 |
| RetentionBase | 15% | 25% | 8% | 40% | 20% |
| beta_depth | 0.30 | 0.40 | 0.20 | 0.50 | 0.30 |
| K_viral | 2.5 | 3.5 | 4.0 | 1.5 | 2.5 |
| ReferralPremium | 2.0 | 2.5 | 3.0 | 1.5 | 2.0 |
| gamma | 0.50 | 0.60 | 0.40 | 0.70 | 0.50 |
| delta | 1.5 | 2.0 | 2.5 | 1.0 | 1.5 |
| EarnedPremium | 3.0 | 4.0 | 5.0 | 2.0 | 3.0 |

### 규모 보정 계수

| 규모 | 연매출 기준 | 계수 | 근거 |
|------|----------|:----:|------|
| 소형 | ~10억 | x1.2 | BEI 1점의 한계 효용 큼 (기저 인지도 낮음) |
| 중형 | 10~100억 | x1.0 | 기준 |
| 대형 | 100~1000억 | x0.8 | 인지도 높아 한계 효용 체감 |
| 메가 | 1000억+ | x0.6 | 인지도 포화 |

---

### 축1: Depth → 재구매/재방문 가치

**경제적 의미**: 깊은 관여(Auth↑ + RQL↑) = 기억의 깊이 = 재방문 확률↑

```
V_depth = N_g3 x (Depth / 100) x RetentionLift(Depth) x CLV x RetentionBase

RetentionLift(Depth) = 1 + beta_depth x (Depth - 50) / 50
```

### 축2: Advocacy → 신규 고객 획득 가치

**경제적 의미**: 추천(Clout↑ + P-01↑) = 바이럴 유입 = 신규 고객 획득

```
V_advocacy = N_g3 x (Advocacy / 100) x ViralCoeff x ReachPerPost x CR_referral x CLV

ViralCoeff = (Q5건수 / N_g3) x K_viral
ReachPerPost = R / N
CR_referral = CR_base x ReferralPremium
```

### 축3: Sincerity → 전환율 프리미엄

**경제적 의미**: 진성 리뷰 비율↑ = 잠재 고객이 보는 리뷰 품질↑ = 전환율 자체↑

```
V_sincerity = R x CR_base x SincerityPremium(Sincerity) x AOV

SincerityPremium(Sincerity) = 1 + gamma x (Sincerity - IndustryAvg) / 100
```

- IndustryAvg: 업종 평균 진성 비율 (기본값 50%)

### 축4: Discovery → Earned Media 가치

**경제적 의미**: 신선함(Freshness↑) = 자발적 공유↑ = paid media로 대체 시 고비용

```
V_discovery = N_g3 x (Discovery / 100) x ShareMultiplier x CPM_earned / 1000 x AvgReach

ShareMultiplier = 1 + delta x (Discovery / 100)
CPM_earned = CPM x EarnedPremium
```

### 총 EMV

```
EMV_total = (V_depth + V_advocacy + V_sincerity + V_discovery) x ScaleFactor
```

---

## 시간 가중 가치 (Decay-adjusted)

### 축별 감쇠 함수

4축의 감쇠 패턴이 다르므로 각각 독립 적용:

```
Depth:     BEI(t) = BEI(0) x e^(-0.036t)    → Slow Decay
Advocacy:  BEI(t) = BEI(0) x e^(-0.105t)    → Rapid Decay
Sincerity: BEI(t) = BEI(0) x [1 + 0.09 x (1 - e^(-0.8t))]  → Inverse (상승)
Discovery: BEI(t) = BEI(0) x e^(-0.245t)    → Sharp Decay
```

(t = 주차, 새로중앙박물관 실측 데이터 기반 피팅)

### 4주 누적 가치

```
CV_axis = V_axis(0) x AvgDecayFactor_axis

AvgDecayFactor (5주 평균):
  Depth:     0.919
  Advocacy:  0.803
  Sincerity: 1.047
  Discovery: 0.611

Total_CV = SUM(CV_axis)
```

---

## ROI 산출 공식

### 캠페인 ROI
```
BEI_ROI = (Total_CV - C_campaign) / C_campaign x 100%
```

### 효율 지표

| 지표 | 공식 | 의미 |
|------|------|------|
| **CPBP** | C_campaign / delta_BEI | BEI 1점 올리는 데 드는 비용 (낮을수록 효율적) |
| **BVE** | Total_CV / C_campaign | 1원 투입당 가치 창출 (1.0 이상이면 가치 초과) |

---

## 실행 프로세스

### STEP 1: 기존 분석 데이터 로드

기존 RXR SNS 분석 또는 BEI follow-up 결과에서 필요한 데이터를 추출:

```
참조 파일 (우선순위):
  1순위: {이벤트명}-bei-tracking.json (BEI 4축 + 시계열)
  2순위: {이벤트명}-bei-follow-report.html (follow-up 집계)
  3순위: {이벤트명}-rxr-sns-report.html (원본 분석)
  4순위: {이벤트명}-2layer-results.json (개별 포스트 데이터)

추출 항목:
  - BEI 4축 점수 (Depth, Advocacy, Sincerity, Discovery)
  - N (전체 게시물), N_g3 (Gate 3 통과)
  - Q5 건수 / Q5 비율
  - R (도달 추정 = N x 업종 평균 도달 또는 사용자 입력)
  - Decay 데이터 (있을 경우)
```

---

### STEP 2: 업종/규모 확인 및 파라미터 설정

```
사용자 확인:
  업종: {업종명}
  규모: {규모} (연매출 기준)
  규모 보정 계수: x{계수}
  캠페인 비용: {금액 또는 "미입력"}

적용 파라미터:
  CLV: {값}, CAC: {값}, CR_base: {값}%
  AOV: {값}, CPM: {값}, RetentionBase: {값}%
  beta_depth: {값}, K_viral: {값}, ReferralPremium: {값}
  gamma: {값}, delta: {값}, EarnedPremium: {값}

사용자가 개별 파라미터를 수동으로 지정하면 그 값을 우선 적용합니다.
```

---

### STEP 2.5: 데이터 품질 게이트 (EMV 산출 전 필수 확인)

> **📌 원본 데이터 품질 검증**
> EMV 산출의 정확도는 원본 분석(rxr-sns-analysis)의 데이터 완성도에 의존한다.
> 산출 전 아래 항목을 확인하고, 누락 시 해당 축의 EMV에 경고를 표기한다:
>
> | 확인 항목 | 영향 축 | 누락 시 조치 |
> |----------|---------|-------------|
> | Freshness Index 해석 존재 | Discovery EMV | "⚠️ Discovery EMV 추정 정확도 낮음 — 원본 Freshness 해석 부재" 마킹 |
> | Clout 데이터 존재 | Advocacy EMV | "⚠️ Advocacy EMV 추정 정확도 낮음 — 원본 Clout 데이터 부재" 마킹 |
> | RQL 가중 자산값 산출 | Depth EMV | "⚠️ Depth EMV 근거 약화 — 원본 RQL 가중자산값 미산출" 마킹 |
> | Gate 3 통과 건수 ≥ 10건 | 전체 EMV | "⚠️ 소규모 데이터(N건) — 전체 EMV 해석 주의" 마킹 |

### STEP 3: T+0 EMV 산출

4축별 독립 EMV를 산출하고 합산:

```
[브랜드명] T+0 EMV 산출 완료

4축별 EMV:
  Depth (재구매):    ₩{금액} ({비율}%)
  Advocacy (획득):   ₩{금액} ({비율}%)
  Sincerity (전환):  ₩{금액} ({비율}%)
  Discovery (미디어): ₩{금액} ({비율}%)

T+0 EMV 합계:      ₩{금액}
규모 보정 후:       ₩{금액} (x{계수})

각 축의 산출 과정을 단계별로 보여줍니다.
```

---

### STEP 4: Decay-adjusted 4주 누적 가치

BEI follow-up 데이터가 있으면 실측 Decay 적용, 없으면 모델 Decay 적용:

```
Decay 소스: {실측 / 모델}

축별 Decay Factor:
  Depth:     {factor}
  Advocacy:  {factor}
  Sincerity: {factor}
  Discovery: {factor}

4주 누적 가치 (Total_CV):
  Depth:     ₩{금액}
  Advocacy:  ₩{금액}
  Sincerity: ₩{금액}
  Discovery: ₩{금액}
  Total:     ₩{금액}
```

---

### STEP 5: ROI 및 효율 지표 (캠페인 비용 제공 시)

```
캠페인 비용: ₩{금액}
Total CV:    ₩{금액}

BEI ROI:     {값}%
BVE:         {값} (1원당 가치 창출)
CPBP:        ₩{금액} (BEI 1점당 비용)

해석: {ROI 의미 설명}
```

---

### STEP 6: EMV 데이터 저장

**저장 경로:** `./30-knowledge/{이벤트명}-emv-report-data.json`

```json
{
  "brand": "브랜드명",
  "event": "이벤트명",
  "created": "YYYY-MM-DD",
  "industry": "업종",
  "scale": "규모",
  "scale_factor": 0.6,
  "bei": {
    "depth": 60.5,
    "advocacy": 54.4,
    "sincerity": 72.6,
    "discovery": 43.1,
    "total": 57.6
  },
  "data_counts": {
    "n_total": 281,
    "n_g3": 204,
    "reach": 500000,
    "q5_count": 16,
    "q5_ratio": 0.08
  },
  "parameters": {
    "clv": 150000,
    "cac": 25000,
    "cr_base": 0.025,
    "aov": 15000,
    "cpm": 5000,
    "retention_base": 0.15
  },
  "emv_t0": {
    "depth": 2961456,
    "advocacy": 29707776,
    "sincerity": 21187500,
    "discovery": 3868283,
    "total_raw": 57725015,
    "total_scaled": 34635009
  },
  "emv_cv": {
    "depth": 1633347,
    "advocacy": 14307226,
    "sincerity": 13308263,
    "discovery": 1418457,
    "total": 30667293,
    "decay_source": "model"
  },
  "roi": {
    "campaign_cost": 300000000,
    "bve": 0.102,
    "bei_roi": -89.8
  }
}
```

---

### STEP 7: HTML 리포트 생성

**저장 경로:** `./30-knowledge/{이벤트명}-emv-report.html`

**R디자인가이드 적용:** #6666FF, Pretendard Variable, 반응형
**Chart.js CDN** 사용 (도넛차트, 바차트, Decay 라인차트)
**PDF 출력 패널** 포함 (가로/세로 선택)

**참고 파일:** `30-knowledge/bei-value-simulation-saero.html` — 이 시뮬레이션 HTML의 디자인과 구조를 기준으로 삼을 것

#### 필수 섹션 (순서대로):

**0. 리서치 개요**
- 분석 대상 (브랜드, 이벤트, 업종, 규모)
- 데이터 소스 (원본 분석 참조)
- 적용 파라미터 요약

**0-1. EMV란 무엇인가 (정의 섹션 — 필수)**
- 한 줄 정의
- 왜 필요한가: BEI의 "So What?" 문제 → EMV가 답하는 3가지 질문
- 3단계 전환 체인 다이어그램 (BEI → 행동 → ₩)
- 4축 → 경제적 경로 매핑 테이블
- 전환 불가 원칙 명시: "추정 가치이지 정확한 매출이 아님"
- 비전문가도 읽을 수 있도록 쉬운 언어 사용

**1. EMV Total Overview (히어로 카드)**
- T+0 EMV (큰 숫자)
- 4주 누적 EMV (큰 숫자, 강조)
- 규모 보정 계수 표시
- BEI 종합 점수 참조 표시

**2. 4축별 EMV Breakdown (4카드 + 도넛차트)**
- Depth / Advocacy / Sincerity / Discovery
- 각 카드: EMV 금액 + 비율(%) + 산출 과정 요약 + 경제적 의미
- 도넛차트: 4축 비율 시각화
- 인사이트 카드: "어떤 축이 가장 큰 가치를 만드는가"

**3. 3단계 전환 체인 시각화 (플로우 다이어그램)**
- Stage 1 → 2 → 3 흐름도
- 각 단계별 입력/출력 값 표시
- 축별 전환 경로 색상 구분

**4. Decay-adjusted 가치 (라인차트)**
- T+0 ~ T+4w 축별 EMV 변화
- 4주 누적 vs T+0 비교
- Decay Factor 표시
- 해석 카드: "어떤 가치가 오래 가고, 어떤 가치가 빨리 소멸하는가"

**5. ROI & 효율 지표 (캠페인 비용 제공 시)**
- BEI ROI (게이지)
- BVE (1원당 가치 창출)
- CPBP (BEI 1점당 비용)
- 해석 카드

**6. 업종 벤치마크 컨텍스트**
- 해당 업종의 파라미터 vs 다른 업종 비교
- "같은 BEI라도 업종에 따라 EMV가 다른 이유" 설명
- 규모 보정의 의미

**7. 산출 공식 레퍼런스**
- 4축별 전체 공식
- 적용된 파라미터 값
- Decay 함수

**8. 한계 및 주의사항**
- 유효 조건 (최소 50건, 단일 캠페인 귀속 등)
- 구조적 한계 (상관 기반 추정, 외부 변수 비통제)
- 클라이언트 커뮤니케이션 가이드: "추정 미디어 가치" 사용, "정확히 X원을 벌었다" 금지

---

### STEP 8: 요약 보고

```
[이벤트명] EMV Analysis 완료

BEI 기반:
  BEI 종합: __._ (등급)
  업종: {업종}, 규모: {규모} (x{계수})

EMV 산출:
  T+0 EMV: ₩{금액}
  4축 비율: Depth {%} / Advocacy {%} / Sincerity {%} / Discovery {%}

4주 누적 가치 (Total CV): ₩{금액}
  최대 가치 축: {축명} (₩{금액}, {%})
  최소 가치 축: {축명} (₩{금액}, {%})

ROI (캠페인 비용 제공 시):
  캠페인 비용: ₩{금액}
  BVE: {값}
  BEI ROI: {값}%

핵심 발견:
1. {가장 큰 가치를 만드는 축과 이유}
2. {Decay에서 가장 강한/약한 축}
3. {업종 특성에 따른 시사점}

파일:
  HTML: ./30-knowledge/{이벤트명}-emv-report.html
  JSON: ./30-knowledge/{이벤트명}-emv-report-data.json
```

---

## 주의사항

- EMV는 **추정 미디어 가치**이며, 실제 매출을 직접 측정한 것이 아님을 리포트에 반드시 명시
- "이 캠페인이 정확히 X원을 벌었다"는 표현 **금지** → "유사 효과의 paid media 비용으로 환산하면 약 X원"
- 업종 간 EMV 직접 비교는 무의미 → 동일 업종 내 비교 또는 전후 비교(ΔBEI→ΔEMV)가 올바른 사용법
- Advocacy가 EMV에서 지배적인 경우가 많음 → 곱셈 체인이 가장 길기 때문 (5개 항 연쇄 곱)
- Sincerity의 Decay가 역행(상승)하는 현상은 정상 → "노이즈 소멸 후 진심 잔존"
- Gate 1 기준 최소 50건 이상 필요 (이하는 신뢰도 경고 표시)
- 초기 계수는 문헌/업계 관행 기반 추정치 → Phase 3(N=20+)까지 보정 사이클 필요
- **참고 시뮬레이션:** `30-knowledge/bei-value-simulation-saero.html` — 디자인/구조 기준
- **프레임워크 문서:** `80-R_tech/81-framework/bei-value-conversion-model.md` — 전체 공식/파라미터 원본
