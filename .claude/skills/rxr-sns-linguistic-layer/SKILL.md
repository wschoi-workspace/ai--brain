---
description: "RXR Linguistic Layer — SNS 리뷰 텍스트의 언어학적 분석. 형태소 분포, 기능어 패턴(Pennebaker LIWC), 확신도 스펙트럼, 담화 표지, 화용론적 분석, 문체 레지스터를 추출하여 LAI(Linguistic Authenticity Index) + EDS(Engagement Depth Score) 산출. RXR Psyche Layer의 Auth/Clout/Freshness를 언어학적으로 보정."
allowed-tools: WebSearch, WebFetch, Read, Write, Edit, Bash, Agent, Grep, Glob
---

> **📌 HTML 리포트 헤더·푸터 필수 적용**
> 이 스킬이 생성하는 모든 HTML 리포트에는 반드시 `rxr-report-header-footer-guide.md`의 §2 헤더와 §3 푸터를 **수정 없이 그대로** 삽입해야 합니다.
> - 헤더: `<body>` 안 첫 `<h1>` 바로 앞
> - 푸터: `</body>` 바로 앞
> - 가이드 경로: `.claude/skills/rxr-report-header-footer-guide.md`

# RXR Linguistic Layer

RXR 2-Layer 분석(Content + Psyche)에 **언어학적 근거 레이어**를 추가하는 확장 모듈.

**핵심 철학:** Psyche Layer의 Auth/Clout/Freshness는 키워드 패턴 기반 추정이다. Linguistic Layer는 **형태소·담화·화용론 수준의 언어학적 분석**으로 이를 교차검증하고 정밀도를 높인다.

**이론적 기반:**
- James Pennebaker "기능어분석" (The Secret Life of Pronouns)
- LIWC (Linguistic Inquiry and Word Count) 프레임워크
- 해석수준이론 CLT (Trope & Liberman) — 조사 패턴
- 정교화가능성 모델 ELM (Petty & Cacioppo) — 담화 표지
- 가짜 리뷰 탐지 연구 (Newman, Pennebaker 2003)

**참조 파일:**
- `80-r-tech/81-framework/function-word-analysis-research.md`
- `30-knowledge/34-consumer-psychology/34-online-consumer-psychology.md`
- `30-knowledge/34-consumer-psychology/modules/M07-소비자-마음-읽기.md` (eWOM)

---

## 입력

RXR SNS Analysis (rxr-sns-analysis.md) STEP 5 완료 후의 분석 결과 JSON 또는 원본 리뷰 텍스트.

| 입력 | 필수 | 설명 |
|------|:---:|------|
| 분석 결과 JSON | 필수 | `analysis-results.json` (Content Class A+B+C 포스트) |
| config.json | 필수 | 브랜드별 linguistic_layer 설정 |

---

## 분석 차원 6가지

### 1. 형태소 분포 (Morphological Distribution)

리뷰 텍스트의 품사 분포를 분석하여 체험 진정성을 추정.

**추출 지표:**

| 지표 | 산출 방법 | 심리학적 의미 |
|------|----------|--------------|
| 감각어 밀도 | 감각 어휘 수 / 전체 단어 수 × 100 | 직접 체험 신호 (높을수록 Auth↑) |
| 동사 비율 | 동사 수 / 전체 단어 수 | 행동 서술 비율 (체험 후기 = 동사↑) |
| 형용사 비율 | 형용사 수 / 전체 단어 수 | 평가적 표현 (감상 후기 = 형용사↑) |
| 명사 비율 | 명사 수 / 전체 단어 수 | 정보 밀도 (설명적 리뷰 = 명사↑) |

**감각 어휘 사전** (config.json의 `linguistic_layer.sensory_vocabulary` 참조):
- **미각**: 달달, 상큼, 시원, 청량, 달콤, 씁쓸
- **촉각**: 탱글, 쫀득, 부드러, 딱딱, 씹는맛, 식감
- **후각**: 향, 냄새, 향기, 상쾌한향
- **체화**: 개운, 상쾌, 깔끔, 기분좋, 입안

> **판정 기준:** 감각어 밀도 > 3/100단어 = 직접 체험 가능성 높음 → **Auth +8**

---

### 2. 기능어 패턴 (Function Word Patterns)

Pennebaker LIWC 프레임워크의 한국어 적용.

#### 2-1. 대명사 패턴

| 패턴 | 감지 | 심리학적 해석 |
|------|------|-------------|
| 1인칭 단수 (나/내/저/제/난/전) | regex: `나는\|내가\|저는\|제가\|난\s\|전\s` | 심리적 소유감 — "나의 경험" 표현 |
| 1인칭 복수 (우리/같이/함께) | regex: `우리\|같이\|함께\|다같이` | 사회적 경험 공유 — 집단 동일시 |
| 2인칭/독자 지향 (여러분/당신) | regex: `여러분\|당신\|너희\|분들` | 설득 의도 — Clout↑ |

> **Pennebaker 발견:** 진짜 리뷰는 1인칭 단수가 자연스러운 비율로 분포. 가짜 리뷰는 1인칭 과다 사용(진정성 연출 시도) 또는 극도로 적음(개인 경험 부재).

#### 2-2. 조사 패턴 (이미 Psyche Layer에 존재 → 확장)

기존 Freshness Index(이/가 vs 은/는)에 추가:
- **"에서"** — 장소 경험 마커 ("편의점**에서** 샀는데")
- **"로/으로"** — 목적·수단 마커 ("간식**으로** 좋아요")
- **"보다"** — 비교 마커 ("다른 껌**보다**")

#### 2-3. 어미 패턴 → 문체 레지스터 (차원 6과 연결)

---

### 3. 확신도 스펙트럼 (Certainty Spectrum)

화자의 인식론적 확실성을 측정. 0(극도 불확실) ~ 100(극도 확신).

**확신 마커** (config.json `linguistic_layer.certainty_markers.high`):
- "확실히", "분명히", "무조건", "진짜", "당연히", "틀림없이"

**완화 마커/헤징** (config.json `linguistic_layer.certainty_markers.hedge`):
- "좀", "약간", "~것 같아요", "~인 듯", "~편이에요", "~느낌", "~같은데", "모르겠지만"

**산출:**
```
certainty_ratio = high_count / max(high_count + hedge_count, 1) × 100
```

**심리학적 해석:**
| certainty_ratio | 해석 | RXR 보정 |
|:---:|------|------|
| 80~100 | 강한 확신 — 열렬한 팬 OR 과잉 긍정 의심 | extreme_pos와 교차: 둘 다 높으면 Auth -5 |
| 40~79 | 적절한 확신 — 경험 기반 자신감 | Auth +3 |
| 20~39 | 균형잡힌 헤징 — 분석적 사고 (ELM 중심경로) | Auth +5 (가장 진정성 높은 구간) |
| 0~19 | 과도한 불확실 — 경험 부재 또는 회피적 표현 | Auth -3 |

---

### 4. 담화 표지 분석 (Discourse Marker Analysis)

리뷰의 논증 구조를 분석하여 인지적 깊이를 측정.

**대조 표지** (config.json `linguistic_layer.discourse_markers.contrast`):
- "근데", "그런데", "다만", "아쉬운 점은", "하지만", "반면"
- → **ELM 중심경로 처리의 핵심 신호.** 장단점 모두 고려하는 분석적 사고.

**조건 표지** (config.json `linguistic_layer.discourse_markers.conditional`):
- "~라면", "~경우에", "좋아하시면", "원하시면"
- → **높은 신뢰도 추천.** 맹목적 "강추"보다 조건부 추천이 설득력 높음.

**인과 표지** (config.json `linguistic_layer.discourse_markers.causal`):
- "그래서", "덕분에", "때문에", "그러니까"
- → **인과적 추론 능력.** 단순 감상("좋았다")이 아닌 이유 설명.

**산출: Discourse Complexity Score (0~100)**
```
discourse_score = (contrast_count × 15 + conditional_count × 12 + causal_count × 10)
                  capped at 100
```

**RXR 보정:**
- discourse_score ≥ 40: RQL Q3 → Q4 승격 고려
- discourse_score ≥ 60: Auth +5

---

### 5. 화용론적 분석 (Pragmatic Analysis)

**표면 의미와 실제 의미의 괴리**를 감지하여 4-way Sentiment를 정밀화.

| 패턴 | 감지 regex | 표면 | 실제 | 감성 재분류 |
|------|-----------|------|------|-----------|
| 간접 부정 | `나쁘진\s*않` `별로\s*안\s*좋` | 중립 | 약한 부정 | neutral → mixed |
| 축소어법 (litotes) | `안\s*나쁘` `못할\s*것도\s*없` | 이중부정 | 약한 긍정 | neutral → mixed(긍정기울) |
| 수사적 질문 | `안\s*\S+\s*수\s*있` `어떻게\s*안` | 질문 | 강한 긍정 | 유지 (intensity↑) |
| 조건부 추천 | `좋아하\S*면\s*(추천\|강추\|좋)` | 제한적 추천 | 높은 신뢰도 | Clout +10 |
| 암묵적 비교 | `다른\s*껌\S*\s*(다르\|달리\|비해)` | 비교 | 차별화 인지 | topic: 비교/추천 강화 |

**주의:** 한국어 화용론은 문맥 의존도가 높음. LLM 기반 분석 시 5건 배치로 문맥 함께 전달.

---

### 6. 문체 레지스터 분석 (Register Analysis)

한국어 문체 등급을 감지하여 협찬/템플릿 콘텐츠를 식별.

**레지스터 유형:**

| 레지스터 | 감지 패턴 (어미) | 전형적 플랫폼 | 의미 |
|---------|---------------|------------|------|
| 합쇼체 (최존칭) | -ㅂ니다, -습니다, -됩니다 | 보도자료, PR | 공식적 = 협찬/PR 의심 |
| 해요체 (보통존칭) | -어요, -아요, -에요, -거든요, -더라고요 | 블로그, 유튜브 | 표준 리뷰 레지스터 |
| 해체 (비격식) | ㅋㅋ, ㅎㅎ, ㅠㅠ, -임, -음, -함 | 인스타, 트위터 | 친밀/동료 지향 |

**레지스터 일관성 점수 (Register Consistency Score):**
```
각 문장의 레지스터를 판별 → 문장별 레지스터 분포
consistency = 최빈 레지스터 비율 (0~100%)
```

**심리학적 해석:**
- consistency 95%+ & 합쇼체: **템플릿/PR 의심** → Trust -10
- consistency 95%+ & 해요체: 표준 (중립)
- consistency 60~85%: **자연스러운 레지스터 전환** → Auth +3 (실제 사람은 문체를 자연스럽게 섞음)
- consistency < 60%: 혼란스러운 문체 (드문 케이스)

---

## 복합 지표

### LAI (Linguistic Authenticity Index) — 0~100

순수 언어학적 피처만으로 산출하는 진정성 지수. Psyche Layer의 Auth와 **독립적으로** 산출하여 교차검증.

```
LAI = (sensory_density_norm × 30) +
      (hedging_naturalness × 20) +
      (register_variability × 20) +
      (temporal_proximity × 15) +
      (first_person_naturalness × 15)
```

**각 구성요소 (0~1 정규화):**

| 구성요소 | 산출 | 0점 | 1점 |
|---------|------|-----|-----|
| sensory_density_norm | 감각어 밀도 / 10 (cap at 1.0) | 감각어 0개 | 10/100단어 이상 |
| hedging_naturalness | certainty 20~60이면 1.0, 벗어나면 감소 | 극단적 확신 or 불확실 | 자연스러운 헤징 |
| register_variability | 1 - abs(consistency - 75)/25 (cap) | 극단적 일관/불일관 | 75% 근처 자연 전환 |
| temporal_proximity | 시간근접 표지("오늘","아까","방금") 존재=1.0 | 시간 표지 없음 | 최근 체험 표지 |
| first_person_naturalness | 1인칭 비율 5~15%=1.0, 벗어나면 감소 | 0% or 30%+ | 자연스러운 자기표현 |

### EDS (Engagement Depth Score) — 0~100

리뷰어의 인지적 몰입도를 측정.

```
EDS = (metaphor_density × 25) +
      (discourse_complexity × 25) +
      (qualification_density × 25) +
      (specific_detail_density × 25)
```

| 구성요소 | 산출 | 의미 |
|---------|------|------|
| metaphor_density | 비유/은유 표현 수 / 전체문장 수 | 깊은 처리의 증거 |
| discourse_complexity | discourse_score / 100 | 논증 구조의 복잡성 |
| qualification_density | 한정 표지("개인적으로","제 입장에서") 수 / 전체문장 수 | 자기인식 수준 |
| specific_detail_density | 구체적 수치/장소/시간 표현 수 / 전체문장 수 | 정보 밀도 |

---

## LAI-Auth 교차검증

| LAI - Auth 차이 | 해석 | 조치 |
|:---:|------|------|
| |차이| ≤ 10 | 일치 — 높은 신뢰도 | 그대로 사용 |
| 10 < |차이| ≤ 20 | 경미한 불일치 — 정상 범위 | 참고 표시 |
| |차이| > 20 | **유의미한 괴리** | 🚩 플래그 → 수동 검토 |

**괴리 해석:**
- LAI >> Auth: 언어학적으로는 진정성 높은데 키워드 패턴이 낮음 → 독특한 표현 스타일 (Auth 과소평가 가능성)
- LAI << Auth: 키워드 패턴은 진정성 높아 보이는데 언어학적으로 부자연스러움 → 잘 만든 협찬 리뷰 의심

---

## Psyche Layer 보정 매핑 (최종)

Linguistic Layer 분석 후 기존 Psyche Layer 점수를 보정:

| 언어학 피처 | 조건 | 보정 대상 | 보정값 |
|------------|------|----------|-------|
| 감각어 밀도 | >3/100단어 | Auth | +8 |
| 1인칭 비율 | 5~15% 자연 범위 | Auth | +5 |
| 적절한 헤징 | certainty 20~60 | Auth | +3~5 |
| 과잉 확신 + 과잉 긍정 | certainty>80 & extreme_pos>5 | Auth | -5 |
| 시간근접 표지 | "오늘","방금","아까" 존재 | Freshness | +5 |
| 합쇼체 일관 | consistency>95% & formal | Trust Score | -10 |
| 자연스러운 레지스터 전환 | consistency 60~85% | Auth | +3 |
| 대조 표지 ≥ 2개 | discourse contrast ≥ 2 | Auth | +5 |
| discourse_score ≥ 40 | 복합 담화 구조 | RQL | Q3→Q4 승격 고려 |
| 간접 부정 감지 | "나쁘진 않은데" 등 | Sentiment | neutral → mixed 재분류 |
| 조건부 추천 | "~라면 추천" | Clout | +10 |
| 은유 밀도 | ≥2 비유 표현 | EDS | +12 |

---

## 실행 방법

### 방법 1: Claude/Gemini API 배치 분석 (권장)

리뷰 텍스트를 5~10건 배치로 묶어 LLM API에 전달. 구조화된 JSON 응답 요청.

**프롬프트 템플릿:**

```
다음 한국어 리뷰 텍스트들을 언어학적으로 분석하세요.

각 리뷰에 대해 아래 JSON 형식으로 응답하세요:

{
  "review_id": "R001",
  "morphological": {
    "sensory_words": ["상쾌", "개운"],
    "sensory_density": 2.5,
    "verb_ratio": 0.18,
    "adjective_ratio": 0.12,
    "noun_ratio": 0.35
  },
  "function_words": {
    "first_person_count": 3,
    "first_person_ratio": 0.08,
    "we_count": 1,
    "reader_directed_count": 0,
    "particle_iga": 5,
    "particle_eunneun": 8,
    "particle_eseo": 2,
    "particle_boda": 1
  },
  "certainty": {
    "high_markers": ["진짜", "확실히"],
    "hedge_markers": ["것 같아요", "좀"],
    "certainty_ratio": 55
  },
  "discourse": {
    "contrast_markers": ["근데", "다만"],
    "conditional_markers": [],
    "causal_markers": ["그래서"],
    "discourse_score": 37
  },
  "pragmatics": {
    "indirect_negatives": [],
    "litotes": [],
    "rhetorical_questions": [],
    "conditional_recommendations": ["민트 좋아하시면 추천"],
    "implicit_comparisons": ["다른 껌이랑 다르게"],
    "sentiment_reclassification": null
  },
  "register": {
    "dominant": "해요체",
    "formal_ratio": 0.05,
    "polite_ratio": 0.70,
    "casual_ratio": 0.25,
    "consistency": 70,
    "template_suspect": false
  },
  "composite": {
    "LAI": 68,
    "EDS": 45,
    "lai_auth_gap": -5,
    "flag": null
  },
  "psyche_adjustments": {
    "auth_delta": +8,
    "clout_delta": +10,
    "freshness_delta": 0,
    "trust_delta": 0,
    "rql_upgrade": false,
    "sentiment_reclassify": null
  }
}

리뷰 텍스트:
---
[R001] {리뷰 텍스트}
---
[R002] {리뷰 텍스트}
---
```

### 방법 2: 로컬 Python 분석 (경량)

regex 기반으로 주요 지표만 추출. LLM 비용 절감 시 사용.
`80-r-tech/84-scripts/xylitol/xylitol_pipeline.py`의 `linguistic_analyze()` 함수 참조.

---

## 출력

| 파일 | 내용 |
|------|------|
| `linguistic-results.json` | 포스트별 6차원 분석 + LAI/EDS + 보정값 |
| `analysis-results-enhanced.json` | 기존 analysis-results.json + Linguistic Layer 보정 적용 버전 |

---

## 리포트 확장

기존 RXR HTML 리포트 (rxr-sns-analysis.md STEP 8)에 추가되는 섹션:

### 📊 Linguistic Analysis Dashboard
- 감각어 밀도 분포 히스토그램
- 확신도 스펙트럼 분포 (극불확실 ~ 극확신)
- 담화 복잡성 vs Auth 산점도
- 레지스터 분포 (해요체/해체/합쇼체 비율)

### 🔄 LAI-Auth 교차검증
- LAI vs Auth 산점도 (대각선 = 완전일치)
- 괴리 플래그 리스트 (|차이| > 20인 포스트)
- 괴리 패턴 해석 (과소평가/과대평가 유형)

### 📈 EDS 분포
- EDS 등급별 분포 (High 70+ / Mid 40~69 / Low ~39)
- EDS vs RQL 상관관계
- 인지적 몰입도 상위 포스트 하이라이트
