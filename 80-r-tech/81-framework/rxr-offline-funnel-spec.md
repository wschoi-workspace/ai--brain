# RXR Offline Funnel Review Spec

> RXR Master Framework의 L0~L7 퍼널에 **오프라인 실측 데이터 + 설문 EDI + SNS 2-Layer**를 연결하는 통합 검토 프로세스 확정판
> 버전: 0.1 (초안) | 최종 수정: 2026-04-13
> 상위 참조: `rxr-master-framework.md` v1.2, `bei-value-conversion-model.md`
>
> **스테이터스**: v0 설계 완료. 실제 파일럿 데이터로 PSI/IEQ 임계값 캘리브레이션 후 v1.0으로 고정 예정.

---

## 0. 왜 이 문서가 필요한가

RXR의 두 자산이 분리돼 있다.

- **오프라인 퍼널** — L0 지나감 → L1 시선 → **L2 진입** → **L3 체류(DQS)** → **L4 구매** → L5 재방문 → L6 회원 → L7 후기(RQL). 공식은 `rxr-master-framework.md` §3에 있으나, 거리 유동인구·대기·객단가 등 **실측 데이터를 받아 KPI를 계산하는 입력 스키마가 없다.**
- **감성품질** — `rxr-survey-analysis`(EDI/VRI)와 `rxr-sns-analysis`(Auth/Clout/Freshness, Sincerity Gate)는 완성되어 있으나, **오프라인 퍼널 KPI와 연결되지 않는다.**

이 문서는 두 자산을 하나의 파이프라인으로 묶고, "매장 진입이 소비자 인식을 얼마나, 어떻게 바꿨는가"를 단일 수치(**PSI**)와 통합 점수(**IEQ**)로 답한다.

**확정 제약 (승인됨, 2026-04-13)**
1. POS↔체류 매칭은 **집계 단위** — 일자별 집계만. 개인 단위 visit_id 매칭 없음.
2. 시간 단위 = **일자별**. 시간대(1h bin)는 v1.1 범위.
3. 아키텍처 = `rxr-analysis` 명령어 **확장**. 신규 skill/command 분리 없음.
4. PSI = **PRE / DURING / POST 3시점 모두 포함**.

---

## 1. 파이프라인 개요

```
[funnel.xlsx — 6시트]
        │
        ▼
STAGE A · 오프라인 퍼널 KPI (일자별 집계)
   L0 유동인구 → L2 진입률 → 대기 → L3 DQS → L4 구매전환 → 객단가 → L5 재방문
        │
        ▼
STAGE B · 감성품질 스코어링 (기존 command 재사용)
   B1 설문  → EDI / VRI           (rxr-survey-analysis)
   B2 SNS사전 → Auth/Clout/Fresh  (rxr-sns-analysis · phase=PRE)
   B2.5 DURING → Auth/Clout/Fresh (중간 검증)
   B3 SNS사후 → Auth/Clout/Fresh  (rxr-sns-analysis · phase=POST)
        │
        ▼
STAGE C · PSI (Perception Shift Index)
   ΔExpectation→Experience / ΔExperience→Advocacy / ΔOverall
        │
        ▼
STAGE D · IEQ (Integrated Experience Quality)
   IEQ = √(FE · EQ) × (1 + 0.2·PSI_signed)
        │
        ▼
HTML 리포트 (R디자인가이드 · #6666FF · Pretendard · 16:9)
```

---

## 2. 엑셀 입력 스키마 — `funnel.xlsx`

단일 파일 · 6시트. 모든 날짜 `YYYY-MM-DD`. 빈 템플릿은 `80-r-tech/81-framework/rxr-offline-funnel-template.xlsx`.

### 2-1. 시트 `00_meta` (브랜드/이벤트 메타, 단일 행)

| 컬럼 | 예시 | 용도 |
|---|---|---|
| `brand_name` | Eclipse | 리포트 제목·조회키 |
| `event_name` | 이클립스 월드 팝업 | |
| `venue` | Bracket 성수 | |
| `period_start` | 2026-04-01 | PRE/DURING/POST 자동 분류 경계 |
| `period_end` | 2026-04-30 | |
| `content_type` | 체험형 팝업 | `expected_dwell_min` 매핑 키 (master framework §3 표 참조) |
| `industry` | F&B | BEI/EMV 업종 파라미터 조회 (bei-value-conversion-model.md) |
| `expected_dwell_min` | 5 | DQS 분모. `content_type`로 자동 매핑 or 수동 입력 |

### 2-2. 시트 `10_foottraffic` (일자별)

| 컬럼 | 필수 | 설명 |
|---|---|---|
| `date` | ✅ | YYYY-MM-DD |
| `거리_유동인구` | ✅ | L0 원자료. 매장 앞 거리 카운트 |
| `파사드_시선멈춤` | 옵션 | L1. 파사드 앞에 멈춰 선 인원. 없으면 L0→L2 직접 전환율만 계산 |

### 2-3. 시트 `20_entry_wait` (일자별)

| 컬럼 | 필수 | 설명 |
|---|---|---|
| `date` | ✅ | |
| `진입수` | ✅ | L2. 실제 매장 내부로 들어온 인원 (출입 카운터/직원 카운트) |
| `대기등록수` | 옵션 | 대기명단 등록 인원 (팝업 특성상 필수 아닐 수 있음) |
| `대기이탈수` | 옵션 | 대기 중 이탈 인원 |
| `평균대기분` | 옵션 | |

### 2-4. 시트 `30_dwell_agg` (일자별 체류 집계)

| 컬럼 | 필수 | 설명 |
|---|---|---|
| `date` | ✅ | |
| `총방문자수` | ✅ | 보통 `진입수`와 동일하나 분리 가능 |
| `평균체류분` | ✅ | DQS 핵심 입력 |
| `평균방문구역수` | 옵션 | `density_coef` 계산. 없으면 `1.0` 가정 |
| `평균인터랙션수` | 옵션 | 터치 패널·체험 부스 등. 없으면 `0` |

> 집계 버전이므로 개인별 퍼스널리티 가중 `personality_w`는 **1.0 고정**. visit_id 기반 개인 측정은 v1.1.

### 2-5. 시트 `40_pos` (일자별)

| 컬럼 | 필수 | 설명 |
|---|---|---|
| `date` | ✅ | |
| `거래건수` | ✅ | L4 원자료 |
| `총매출` | ✅ | 객단가 계산 |
| `회원거래건수` | 옵션 | L6 |
| `재방문거래건수` | 옵션 | L5. POS에서 재방문 판별 불가 시 비움 |

### 2-6. 시트 `50_survey`

**`rxr-survey-analysis` Mode 2 수집 포맷 그대로 사용.** 변환 로직 불필요. 3단계 문항(매력 포인트 / 기억 선명도 / 행동 전환) + 개방형 1~2 문항 그대로.

### 2-7. 시트 `60_sns_urls`

| 컬럼 | 필수 | 설명 |
|---|---|---|
| `url` | ✅ | 블로그/카페/인스타/X 게시글 URL |
| `게시일` | ✅ | YYYY-MM-DD |
| `phase` | 자동 | 비워두면 `meta.period_*`로 자동 분류. 수동 오버라이드 가능 |
| `비고` | 옵션 | |

**`phase` 자동 분류 규칙**
- `게시일 < period_start` → **PRE** (시작 14일 전까지만 수집 권장)
- `period_start ≤ 게시일 ≤ period_end` → **DURING**
- `period_end < 게시일 ≤ period_end + 28일` → **POST**
- 그 외 → `OUT_OF_RANGE` (분석 제외)

---

## 3. STAGE A — 단계별 KPI 공식

모두 `rxr-master-framework.md` §3의 L0~L7 퍼널에 1:1 매핑. 새 메서드 없음.

| 코드 | KPI | 공식 | 입력 시트 |
|---|---|---|---|
| L0 | 거리 유동인구 | `sum(거리_유동인구)` | 10 |
| L1→L0 | 시선 체류율(옵션) | `sum(파사드_시선멈춤) / sum(거리_유동인구)` | 10 |
| **L2_rate** | **진입률** | `sum(진입수) / sum(거리_유동인구)` | 10, 20 |
| L2_wait | 대기 전환율 | `(sum(대기등록) − sum(대기이탈)) / sum(대기등록)` | 20 |
| L2_churn | 대기 이탈률 | `sum(대기이탈) / sum(대기등록)` | 20 |
| **L3_DQS** | **체류 품질** | `(평균체류분 / expected_dwell_min) × density_coef × 1.0` (일자별 평균 후 기간 평균) | 30, 00 |
| └ density_coef | 밀도 계수 | `clip(0.3 + 0.1×평균방문구역수 + 0.05×평균인터랙션수, 0.3, 1.5)` | 30 |
| **L4_rate** | **구매 전환율** | `sum(거래건수) / sum(진입수)` | 20, 40 |
| L4_aov | 객단가 | `sum(총매출) / sum(거래건수)` | 40 |
| L5_rate | 재방문율 | `sum(재방문거래) / sum(거래건수)` | 40 |
| L6_rate | 회원 전환율 | `sum(회원거래) / sum(거래건수)` | 40 |
| L7 | 후기 깊이 (RQL) | `rxr-sns-analysis` 산출 평균 | 60 |

**결측 처리 규칙**
- 옵션 컬럼 누락 → 해당 KPI만 `null` 처리 후 리포트에 "데이터 미수집" 명시
- `대기등록수 = 0` → `L2_wait = N/A`, `L2_churn = 0` (패널티 없음)
- `평균방문구역수` 누락 → `density_coef = 0.4` (기본값)
- 한 시트 전체 누락 → Stage A 부분 실패. 나머지 스테이지는 계속 진행

---

## 4. STAGE B — 감성품질 스코어링 (기존 command 재사용)

| 블록 | 입력 | 호출 | 산출 |
|---|---|---|---|
| B1 | 시트 50 | `rxr-survey-analysis` Mode 2 | EDI(3~15), 레벨(L1~L5), VRI |
| B2 | 시트 60 (phase=PRE) | `rxr-sns-analysis` | Auth_pre, Clout_pre, Fresh_pre, Sentiment_pre, RQL_pre |
| B2.5 | 시트 60 (phase=DURING) | `rxr-sns-analysis` | (중간 검증용 · IEQ에는 직접 투입 안 함) |
| B3 | 시트 60 (phase=POST) | `rxr-sns-analysis` | Auth_post, Clout_post, Fresh_post, Sentiment_post, RQL_post |

**정규화 규칙 (전 지표 0~1로)**

| 원본 지표 | 정규화 공식 | 비고 |
|---|---|---|
| EDI (3~15) | `(EDI − 3) / 12` | |
| Auth (0~100) | `Auth / 100` | |
| Clout (0~100) | `Clout / 100` | |
| Freshness Index (0~100) | `Fresh / 100` | 상한 100 가정 (v1.1 재확인) |
| Sentiment (−1~+1) | `(Sentiment + 1) / 2` | |
| DQS (0~∞) | `clip(DQS / 2, 0, 1)` | DQS 2.0 이상 상한 처리 |
| RQL (평균 0.2~2.0) | `clip((RQL − 0.2) / 1.8, 0, 1)` | |
| 퍼널 전환율 | 이미 0~1 | `L2_rate`, `L4_rate`, `L5_rate`, `L6_rate` |

---

## 5. STAGE C — PSI (Perception Shift Index)

**목표 질문: "매장 진입이 소비자 인식을 얼마나, 어떻게 바꿨는가?"**

### 5-1. 3시점 5축 벡터 (모두 0~1 정규화 후)

| 축 | PRE (SNS 사전) | DURING (설문) | POST (SNS 사후) |
|---|---|---|---|
| **감성 극성** | `Sentiment_pre_n` | `survey_sentiment_n` | `Sentiment_post_n` |
| **진정성** | `Auth_pre_n` | `VRI_n` (근사) | `Auth_post_n` |
| **확신도** | `Clout_pre_n` | `EDI_행동전환_n` (Mode 2 출력 "행동전환" 문항 평균) | `Clout_post_n` |
| **신선함** | `Fresh_pre_n` | `0.5` (해당 축 없음 · 중립값 고정) | `Fresh_post_n` |
| **깊이** | `RQL_pre_n` | `EDI_n` | `RQL_post_n` |

### 5-2. 델타 & PSI 공식

```
ΔE→X = survey_vec − pre_vec      # 기대→체험: 기대가 충족됐나?
ΔX→A = post_vec  − survey_vec    # 체험→옹호: 체험이 외부 옹호로 전환됐나?
ΔAll = post_vec  − pre_vec       # 순 인식 이동

PSI_total  = 0.4·‖ΔE→X‖₂ + 0.4·‖ΔX→A‖₂ + 0.2·‖ΔAll‖₂
PSI_signed = sign( ΔAll · w_dir ) × PSI_total
  where w_dir = [감성 0.3, 진정성 0.3, 확신도 0.2, 신선함 0.1, 깊이 0.1]
```

### 5-3. 판정 임계값 (v0 — 파일럿 후 캘리브레이션)

| PSI_signed | 라벨 |
|---|---|
| (−∞, −0.25) | ⚠ **기대 대비 붕괴** — 경보 |
| [−0.25, −0.10) | 약한 부정 이동 |
| [−0.10, +0.10] | 무변화 — 진입이 인식을 바꾸지 못함 |
| (+0.10, +0.25] | 약한 긍정 이동 |
| (+0.25, +0.45] | ✅ **유의한 긍정 이동** — 체험→옹호 |
| (+0.45, +∞) | ⭐ **입소문 촉발 구간** |

### 5-4. 경보 플래그 (PSI와 독립적으로 항상 검사)

| 조건 | 플래그 |
|---|---|
| `Auth_post − Auth_pre ≤ −15` AND `Clout_post ≥ Clout_pre` | 🟠 **자기방어적 후기** — 실망을 포장 |
| `Fresh_post / Fresh_pre < 0.8` | 🟡 **신선함 소진** |
| `L3_DQS_n < 0.8` AND `EDI_n ≥ 0.75` | 🔵 **설문 긍정 편향** — VRI 재검증 필요 |
| `L2_rate > 0.15` AND `L4_rate < 0.05` | 🟣 **진입은 되는데 구매 안 됨** — 매장 내 전환 설계 점검 |

---

## 6. STAGE D — IEQ (Integrated Experience Quality)

**목표: "전환율만 좋은 이벤트"와 "감성만 좋은 이벤트"를 하나의 점수로 구분.**

```
FE (Funnel Efficiency) =
    0.15·L2_rate_n + 0.25·L3_DQS_n + 0.30·L4_rate_n
  + 0.15·L5_rate_n + 0.15·(1 − L2_churn)

EQ (Emotional Quality) =
    0.35·EDI_n + 0.25·Auth_post_n + 0.20·Clout_post_n
  + 0.10·Fresh_post_n + 0.10·RQL_post_n

IEQ = √(FE · EQ) × (1 + 0.2·PSI_signed)
         └ 기하평균(한쪽만 좋으면 감점)   └ 인식 이동 보정(±20%)
```

- 모든 변수 0~1
- 기하평균 사용 → FE·EQ 중 하나가 0에 가까우면 IEQ도 0에 가까워짐 (의도한 페널티)
- `IEQ ∈ [0, ~1.2]` (PSI 보정 포함)

### 6-1. 4사분면 매트릭스 (리포트 핵심 차트)

```
           높은 EQ
              │
    ③ 감성형    │   ① 이상형 ★
    (컬트)     │   (IEQ 최고)
              │
  ────────────┼────────────  높은 FE
              │
    ④ 회피형    │   ② 효율형
    (실패)     │   (돈은 벌지만 팬 없음)
              │
```

사분면 판정: `FE_median = 0.5`, `EQ_median = 0.5` 기준. 복수 이벤트 비교 시 median을 데이터셋 기준으로 재계산.

### 6-2. 사분면별 자동 전략 제안 룰

| 사분면 | 상태 | 권장 액션 |
|---|---|---|
| ① 이상형 | 고 FE · 고 EQ | 현 구조 유지 + 재방문/회원 전환 강화로 EMV 극대화 |
| ② 효율형 | 고 FE · 저 EQ | SNS 후기 Auth 하락 원인 조사. 감성 포인트 재설계 |
| ③ 감성형 | 저 FE · 고 EQ | 팬덤은 형성, 전환 설계 부재. 결제/CTA 동선 최적화 |
| ④ 회피형 | 저 FE · 저 EQ | 기본 가설 재검토. 타깃/컨셉/공간 전면 재설계 |

---

## 7. HTML 리포트 구조 (섹션 1~10)

`rxr-analysis` 명령어의 기존 리포트(`./30-knowledge/rxr-analysis-{브랜드명}-{날짜}.html`)에 섹션을 확장한다. `funnel_xlsx` 입력이 있을 때만 섹션 1~6이 활성화되고, 없으면 기존 2-Layer 리포트와 동일하게 동작.

| # | 섹션 | 내용 | 시각화 |
|---|---|---|---|
| 1 | 표지 | 브랜드/이벤트/기간, IEQ 총점 | 큰 숫자 + 반원 게이지 |
| 2 | 요약 카드 6 | L2_rate / L3_DQS / L4_rate / L4_aov / EDI / Auth_post | 카드 + mini sparkline |
| 3 | 퍼널 시각화 | L0→L5 깔때기 + 단계별 드롭 원인 주석 | Funnel chart (Chart.js) |
| 4 | 3시점 감성품질 | PRE/DURING/POST 비교 | 5축 레이더 |
| 5 | PSI 패널 | ΔE→X, ΔX→A, ΔAll + 판정 + 경보 플래그 | 막대 + 라벨 칩 |
| 6 | IEQ 사분면 | 본 이벤트 위치 + 과거 이벤트(옵션) | CSS Grid 2×2 |
| 7 | 세그먼트 교차 | Layer1 × Layer2 (기존 `rxr-analysis` §4 재사용) | Matrix table |
| 8 | Sincerity Gate | Gate 1/2/3 각 Auth·Clout·긍정률 (기존 `rxr-sns-analysis` 재사용) | 3-step chart |
| 9 | 전략 제안 | §6-2 사분면 룰 기반 자동 생성 + 경보 플래그별 구체 액션 | Insight card |
| 10 | 부록 | 시트별 로우데이터 집계 테이블 + 설문 개방형 응답 인용 | Table |

**디자인 제약 (R디자인가이드 적용 — 기본 규칙)**
- Primary `#6666FF`, Pretendard, 16:9 슬라이드형
- 비전문가 해설 박스(`.card-explain`) 모든 수치·차트에 필수
- PDF 저장 버튼(html2pdf.js) 기존 `rxr-analysis` 템플릿과 동일

---

## 8. 실행 순서 (파일럿 1회 사이클)

1. `funnel.xlsx` 빈 템플릿을 사용자에게 전달 → 사용자가 6시트 채워 반환
2. `funnel-loader` 로직(본 문서 §2~§3)대로 STAGE A KPI 계산 → 숫자 sanity check
3. `rxr-survey-analysis` Mode 2 호출 → EDI/VRI 수집
4. `rxr-sns-analysis` 호출 (phase 자동 분류) → B2/B2.5/B3 산출
5. §5 공식대로 PSI 계산 → 임계값 판정
6. §6 공식대로 IEQ 계산 → 사분면 배치
7. §7 섹션 구조로 HTML 리포트 생성
8. 파일럿 데이터로 PSI 임계값(§5-3) 캘리브레이션 → 본 문서 v1.0 고정

---

## 9. 열린 항목 (v1.1 범위)

- 개인 단위 `visit_id` 매칭 (Bracket 센서 연동) → `personality_w` 재도입
- 시간대별(1h bin) 피크/비피크 DQS 비교
- FE 내부 가중치의 업종별 분기 (`bei-value-conversion-model.md`의 업종 테이블에 `fe_weights` 컬럼 추가)
- `Fresh` 정규화 상한치(100) 실측 재확인
- PSI `w_dir` 축별 가중치 파일럿 재조정
- EMV 환산 연결 (`rxr-sns-analysis-value` skill과 IEQ 결과 파이프)

---

## 10. 교차 참조

- 퍼널 7단계·DQS·RQL 원천 정의: `rxr-master-framework.md` §2-1b, §3
- 2-Layer (Content + Psyche) 알고리즘: `rxr-2layer-analysis-algorithm.html`
- EDI/VRI 정의: `rxr-survey-analysis` command
- Auth/Clout/Freshness/Sincerity Gate: `rxr-sns-analysis` command
- BEI 4축 → EMV 전환: `bei-value-conversion-model.md`
- 분석 실행 커맨드: `.claude/commands/rxr-analysis.md`
