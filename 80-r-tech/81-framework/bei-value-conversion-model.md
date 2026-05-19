# BEI Value Conversion Model (EMV)

> BEI(Brand Engagement Index) 점수를 금전적 가치(₩)로 전환하는 모델

## 1. 개요

### 핵심 질문
"BEI 57.6이 돈으로 얼마인가?"

### 정의
**EMV (Estimated Media Value)** = BEI 4축이 만들어내는 마케팅 효과를 유사한 효과의 paid media 비용으로 환산한 추정 가치

### 전환 불가 원칙
BEI → ₩ 직접 전환은 불가능하다. BEI는 심리/행동 프록시이지 매출 자체가 아니다. 따라서 마케팅 경제학에서 검증된 중간 변수를 경유하는 **3단계 전환 체인**을 사용한다.

```
[BEI 4축]  →  [마케팅 효과 단위]  →  [₩(EMV)]

Stage 1: BEI Score (0~100)
         ↓ 축별 전환 계수
Stage 2: 재구매율, 신규 고객 수, 전환율 리프트, Earned Media
         ↓ 업종별 단가
Stage 3: Won 가치 (EMV)
```

---

## 2. 총 공식

```
EMV_total = V_depth + V_advocacy + V_sincerity + V_discovery
```

4축이 각각 **다른 경제적 경로**로 가치를 만드므로, BEI 가중치(0.35/0.35/0.15/0.15)와 별개로 독립 산출 후 합산한다.

---

## 3. 공통 모수 (External Parameters)

| 모수 | 기호 | 설명 | 입력 방법 |
|------|------|------|-----------|
| 도달 모수 | R | 캠페인 기간 총 노출 수 | 수동 입력 또는 SNS 도구 |
| 전체 게시물 수 | N | Gate 1 전체 수 | BEI 분석에서 자동 |
| Gate 3 게시물 수 | N_g3 | Sincerity 통과 수 | BEI 분석에서 자동 |
| 고객 생애 가치 | CLV | 업종 테이블 또는 수동 | 업종별 기본값 제공 |
| 고객 획득 비용 | CAC | 업종 테이블 또는 수동 | 업종별 기본값 제공 |
| 기본 전환율 | CR_base | 업종 평균 | 업종별 기본값 제공 |
| 평균 주문 금액 | AOV | 업종 평균 | 업종별 기본값 제공 |
| CPM 기준가 | CPM | 1,000 impression 단가 | 플랫폼별 시세 |
| 캠페인 비용 | C_campaign | 실제 집행 비용 | 수동 입력 |

---

## 4. 4축별 비용 전환 경로

### 4-1. Depth → 재구매/재방문 가치

**경제적 의미**: 깊은 관여(Auth↑ + RQL↑) = 기억의 깊이 = 재방문 확률↑

```
V_depth = N_g3 × (Depth / 100) × RetentionLift(Depth) × CLV × RetentionBase

RetentionLift(Depth) = 1 + β_depth × (Depth - 50) / 50
```

- β_depth: 업종별 재구매율 탄력성 (기본값 0.3)
- RetentionBase: 업종 기본 재구매율 (기본값 0.15)
- 근거: 높은 멘탈코스트 투자 → 인지적 일관성 효과 → 재방문 확률 상승

### 4-2. Advocacy → 신규 고객 획득 가치

**경제적 의미**: 추천(Clout↑ + P-01↑) = 바이럴 유입 = 신규 고객 획득

```
V_advocacy = N_g3 × (Advocacy / 100) × ViralCoeff × ReachPerPost × CR_referral × CLV

ViralCoeff = (Q5건수 / N_g3) × K_viral
ReachPerPost = R / N
CR_referral = CR_base × ReferralPremium
```

- K_viral: 업종별 바이럴 계수 (기본값 2.5)
- ReferralPremium: 추천 전환 프리미엄 (기본값 2.0)
- 근거: Nielsen — 소비자 92%가 지인 추천을 광고보다 신뢰

### 4-3. Sincerity → 전환율 프리미엄

**경제적 의미**: 진성 리뷰 비율↑ = 잠재 고객이 보는 리뷰 품질↑ = 전환율 자체↑

```
V_sincerity = R × CR_base × SincerityPremium(Sincerity) × AOV

SincerityPremium(Sincerity) = 1 + γ × (Sincerity - IndustryAvg) / 100
```

- γ: 진성 리뷰 전환율 탄력성 (기본값 0.5)
- IndustryAvg: 업종 평균 진성 비율 (기본값 50%)
- 근거: BrightLocal — 소비자 79%가 리뷰 진정성을 구매 결정 최우선 요소로 평가

### 4-4. Discovery → Earned Media 가치

**경제적 의미**: 신선함(Freshness↑) = 자발적 공유↑ = paid media로 대체 시 고비용

```
V_discovery = N_g3 × (Discovery / 100) × ShareMultiplier × CPM_earned / 1000 × AvgReach

ShareMultiplier = 1 + δ × (Discovery / 100)
CPM_earned = CPM × EarnedPremium
```

- δ: 발견 공유 탄력성 (기본값 1.5)
- EarnedPremium: Earned vs Paid CPM 프리미엄 (기본값 3.0)

---

## 5. 시간 가중 가치 (Decay-adjusted)

### 5-1. 축별 감쇠 함수

4축의 감쇠 패턴이 다르므로 각각 독립 적용:

```
Depth:     BEI(t) = BEI(0) × e^(-0.036t)    → Slow Decay
Advocacy:  BEI(t) = BEI(0) × e^(-0.105t)    → Rapid Decay
Sincerity: BEI(t) = BEI(0) × [1 + 0.09 × (1 - e^(-0.8t))]  → Inverse (상승)
Discovery: BEI(t) = BEI(0) × e^(-0.245t)    → Sharp Decay
```

(t = 주차, 새로중앙박물관 실측 데이터 기반 피팅)

### 5-2. 4주 누적 가치

```
CV_axis = V_axis(0) × AvgDecayFactor_axis

AvgDecayFactor (5주 평균):
  Depth:     0.919
  Advocacy:  0.803
  Sincerity: 1.047
  Discovery: 0.611

Total_CV = Σ CV_axis
```

---

## 6. 업종별 파라미터 테이블

| 파라미터 | F&B/주류 | 패션/뷰티 | 공간/팝업 | 테크/SaaS | 기본값 |
|---------|:-------:|:-------:|:-------:|:-------:|:----:|
| CLV | 150,000 | 500,000 | 80,000 | 2,000,000 | 200,000 |
| CAC | 25,000 | 40,000 | 15,000 | 100,000 | 30,000 |
| CR_base | 2.5% | 1.8% | 3.5% | 1.2% | 2.0% |
| AOV | 15,000 | 80,000 | 25,000 | 200,000 | 50,000 |
| CPM | 5,000 | 8,000 | 4,000 | 12,000 | 6,000 |
| RetentionBase | 15% | 25% | 8% | 40% | 20% |
| β_depth | 0.30 | 0.40 | 0.20 | 0.50 | 0.30 |
| K_viral | 2.5 | 3.5 | 4.0 | 1.5 | 2.5 |
| ReferralPremium | 2.0 | 2.5 | 3.0 | 1.5 | 2.0 |
| γ | 0.50 | 0.60 | 0.40 | 0.70 | 0.50 |
| δ | 1.5 | 2.0 | 2.5 | 1.0 | 1.5 |
| EarnedPremium | 3.0 | 4.0 | 5.0 | 2.0 | 3.0 |

### 규모 보정 계수

| 규모 | 연매출 기준 | 계수 | 근거 |
|------|----------|:----:|------|
| 소형 | ~10억 | ×1.2 | BEI 1점의 한계 효용 큼 (기저 인지도 낮음) |
| 중형 | 10~100억 | ×1.0 | 기준 |
| 대형 | 100~1000억 | ×0.8 | 인지도 높아 한계 효용 체감 |
| 메가 | 1000억+ | ×0.6 | 인지도 포화 |

---

## 7. ROI 산출 공식

### 캠페인 ROI
```
BEI_ROI = (Total_CV - C_campaign) / C_campaign × 100%
```

### ΔBEI ROI (전후 비교)
```
ΔBEI = BEI_after - BEI_before
ΔEMV = EMV(BEI_after) - EMV(BEI_before)
ΔBEI_ROI = ΔEMV / C_campaign × 100%
```

### 효율 지표

| 지표 | 공식 | 의미 |
|------|------|------|
| **CPBP** | C_campaign / ΔBEI | BEI 1점 올리는 데 드는 비용 (낮을수록 효율적) |
| **BVE** | Total_CV / C_campaign | 1원 투입당 가치 창출 (1.0 이상이면 가치 초과) |

---

## 8. 새로중앙박물관 시뮬레이션

### 입력값
- BEI 57.6, Depth 60.5, Advocacy 54.4, Sincerity 72.6, Discovery 43.1
- N=281, N_g3=204, R=500,000, Q5비율≈8%
- 업종: F&B/주류, 규모: 메가(×0.6)

### T+0 가치 산출

| 축 | EMV | 산출 과정 |
|---|---:|---|
| Depth | 2,961,456 | 204 × 0.605 × 1.063 × 150,000 × 0.15 |
| Advocacy | 29,707,776 | 204 × 0.544 × 0.20 × 1,780 × 0.05 × 150,000 |
| Sincerity | 21,187,500 | 500,000 × 0.025 × 1.113 × 15,000 × 0.113 (프리미엄분만) |
| Discovery | 3,868,283 | 204 × 0.431 × 1.647 × 15/1 × 1,780 |
| **합계** | **57,725,015** | |
| **규모 보정 후** | **34,635,009** | ×0.6 |

### 4주 Decay-adjusted 누적

| 축 | CV (₩) |
|---|---:|
| Depth | 1,633,347 |
| Advocacy | 14,307,226 |
| Sincerity | 13,308,263 |
| Discovery | 1,418,457 |
| **Total_CV** | **30,667,293** |

### ROI
- BVE = 30,667,293 / 300,000,000 = **0.102**
- 해석: 순수 SNS BEI 가치 ≈ 캠페인 비용의 10.2%. 팝업스토어 가치는 현장 매출 + 브랜드 자산 + PR 가치를 포함해야 전체 ROI 산출 가능.

---

## 9. 검증 방법론

### Phase 1: 사후 검증 (N=1)
- 기존 BEI 사례의 실제 매출 변동과 EMV 비교
- 목표: 방향성 일치 여부

### Phase 2: 다중 비교 (N=5~10)
- 5~10개 캠페인의 BEI×EMV vs 실제 KPI 상관계수
- 목표: r > 0.5

### Phase 3: 계수 보정 (N=20+)
- 회귀분석으로 β, γ, δ 등 보정
- 목표: 예측 오차 ±30% 이내

### 보정 사이클
분기 1회 또는 10건 축적 시. OLS 회귀 + 업종 더미 변수.

---

## 10. 한계 및 전제 조건

### 유효 조건
1. Gate 1 기준 최소 50건 이상 (이하는 신뢰도 경고)
2. 단일 캠페인 귀속 가능 (동시 다수 캠페인 아닌 경우)
3. 한국 시장 / 한국어 SNS 데이터

### 구조적 한계
1. 상관 기반 추정이지 인과 증명이 아님
2. 외부 변수(날씨, 경쟁사, 시즈널리티) 통제 불가
3. 초기 계수는 문헌/업계 관행 기반 추정치
4. Advocacy의 실제 전환 경로 직접 추적 불가

### 클라이언트 커뮤니케이션
- 사용: "추정 미디어 가치(EMV)", "유사 효과의 paid media 비용 환산"
- 금지: "이 캠페인이 정확히 X원을 벌었다", "과학적으로 증명되었다"

---

## 관련 문서
- [BEI 4축 체계](../81-framework/rxr-master-framework.md)
- [BEI 시뮬레이션 — 새로](../../30-knowledge/bei-simulation-saero.html)
- [EMV 시각화 시뮬레이션](../../30-knowledge/bei-value-simulation-saero.html)

---

*v1.0 — 2026-04-12*
