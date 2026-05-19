# 기능어분석 (Function Word Analysis) 리서치 보고서

> 작성일: 2026-03-29

---

## 1. 기능어(Function Word)의 정의

기능어(function word, functor)란 **어휘적 의미가 거의 없거나 모호하며, 문장 내 다른 단어들 사이의 문법적 관계를 표현하는 단어**를 말한다. 문장을 하나로 묶어주는 "접착제" 역할을 하며, 화자의 태도나 분위기를 나타내기도 한다.

### 기능어의 종류

| 유형 | 영어 예시 | 한국어 대응 |
|------|-----------|-------------|
| 관사 (Articles) | a, an, the | - (한국어에는 관사 없음) |
| 대명사 (Pronouns) | I, you, he, she, it, they | 나, 너, 그, 그녀 |
| 전치사 (Prepositions) | in, on, with, to, of | - (한국어에서는 조사가 대응) |
| 접속사 (Conjunctions) | and, but, whether | 그리고, 하지만 |
| 조동사 (Auxiliary verbs) | is, am, have, might | - |
| 한국어 조사 | - | 에서, 에게, 로, 와, 을/를, 이/가 |
| 한국어 어미 | - | -고, -었-, -는 |

### 기능어 vs 내용어 (Content Word)

| 구분 | 기능어 | 내용어 |
|------|--------|--------|
| 의미 | 어휘적 의미 거의 없음 | 구체적 의미를 가짐 |
| 역할 | 문법적/구조적 관계 표현 | 문장의 실질적 의미 구성 |
| 범주 | **폐쇄범주** (새 단어 추가가 거의 안 됨) | **개방범주** (새 단어 계속 생성) |
| 발음 | 약하게 발음, 강세 없음 | 뚜렷하게 발음, 강세 받음 |
| 수량 | 영어 기준 약 500개 미만 | 수만~수십만 개 |
| 사용빈도 | **일상 언어의 50% 이상 차지** | 나머지 |
| 예시 | the, a, I, you, is, to, and | dog, run, beautiful, quickly |

한국어 문법에서는 **실질형태소 = 내용어**, **형식형태소 = 기능어**에 대응된다.

### 핵심 특성

기능어는 영어에서 500개 미만이지만, **우리가 매일 말하고 듣고 읽는 단어의 절반 이상**을 차지한다. 이 "사소해 보이는" 단어들이 실제로는 화자의 심리, 사회적 관계, 성격을 드러내는 강력한 지표가 된다.

---

## 2. 기능어분석의 정의와 방법론

### 정의

기능어분석은 **텍스트 내 기능어(대명사, 관사, 전치사, 접속사, 조동사 등)의 사용 빈도와 패턴을 정량적으로 분석하여 화자의 심리 상태, 사회적 관계, 성격, 진정성 등을 파악하는 텍스트 분석 기법**이다.

### 이론적 기반: James Pennebaker의 연구

텍사스대학교 심리학과 **James W. Pennebaker** 교수가 기능어분석 분야의 선구자다.

**핵심 발견:**
- 트라우마 환자들의 회복 과정에서 결정적 차이를 만드는 것은 내용어가 아니라 **기능어의 사용 패턴**이었다
- 긍정적으로 회복하는 환자들은 "나(I)" → "그/그녀/그들(he/she/they)" → 다시 "나"로 전환하는 패턴을 보임 (다양한 관점을 고려할 수 있는 능력 반영)
- 기능어 분석을 통해 **기만(거짓말), 사회적 지위, 지능, 감정 상태, 관계의 질, 성격**을 추론 가능
- 저서: *"The Secret Life of Pronouns: What Our Words Say About Us"* (한국어: "단어의 사생활")

> **"가장 작고, 가장 흔하게 사용되며, 가장 잊히기 쉬운 단어들이 우리의 생각, 감정, 행동을 들여다보는 창문 역할을 한다."** — Pennebaker

### 분석 방법론

#### 1) 빈도 기반 분석
- 각 기능어 범주의 출현 빈도를 전체 단어 수 대비 백분율로 계산
- 1인칭 단수 대명사(I/나) 사용률, 3인칭 대명사 사용률 등을 개별 추적

#### 2) 사전(Dictionary) 기반 분석
- 미리 정의된 기능어 사전을 기반으로 텍스트를 자동 분류
- LIWC 도구가 대표적 — 80개 이상의 언어적/심리적 범주로 분류

#### 3) 스타일로메트리 (Stylometry)
- 기능어 사용 패턴을 "언어적 지문(stylometric fingerprint)"으로 활용
- 저자 식별, 텍스트 유형 분류에 활용
- 기능어가 내용과 무관하게 개인의 고유한 언어 스타일을 반영하기 때문에 효과적

#### 4) 기계학습/딥러닝 결합
- 기능어 빈도를 피처(feature)로 사용하여 SVM, Naive Bayes, CNN, RNN, Transformer 모델 학습
- 최근에는 BERT 기반 모델이 높은 성능

---

## 3. 비즈니스/마케팅 적용 사례

### 사례 1: 가짜 리뷰(Fake Review) 탐지

LIWC 기반 기능어분석으로 온라인 리뷰의 진위를 판별:

| 구분 | 가짜 리뷰 특징 | 진짜 리뷰 특징 |
|------|---------------|---------------|
| 대명사 | 1인칭 대명사 **과다** 사용 | 자연스러운 비율 |
| 감정어 | 긍정 감정어 **과잉** | 부정 감정어가 더 자연스럽게 포함 |
| 구두점 | 적음 | 더 많은 구두점 사용 |
| 특징 | 지각 과정어 빈번, 과도한 강조어 의존 | 구체적 디테일 포함 |

> 특정 대명사, 부사, 강조어에 대한 과도한 의존은 **비진정한 설득 전략의 신호**

### 사례 2: 럭셔리 브랜드 소비자 언어 분석

유튜브 럭셔리 브랜드 영상 댓글을 LIWC로 분석:
- **분석적 사고(Analytical thinking)**, **영향력(Clout)**, **진정성(Authenticity)** 차원에서 브랜드 간 유의미한 차이 발견
- 전문 브랜드(specialty brand)와 편의 브랜드(convenience brand) 간 차이가 가장 두드러짐

### 사례 3: 인스타그램 광고 텍스트 최적화

LIWC로 건강제품/화장품 인스타그램 광고의 심리언어학적 지표와 CTR 간 상관관계 분석:

| 발견 | 내용 |
|------|------|
| 전체 | **부정 감정어(negemo)**가 두 카테고리 모두에서 CTR과 가장 높은 양의 상관 |
| 건강제품 | 가격 관련 표현이 CTR과 **음의 상관** (가격 언급 피해야 함) |
| 화장품 | 가격 투명성이 CTR과 **양의 상관** (가격 포함이 유리) |

> 소비자 불안감과 위기의식을 자극하는 광고가 더 높은 참여율을 보임

### 사례 4: 기만 탐지 (Deception Detection)

Newman, Pennebaker 등(2003)의 "Lying Words" 연구:
- 언어적 스타일 패턴으로 거짓말을 예측할 수 있음을 입증
- 기능어 사용 패턴(특히 **1인칭 대명사 감소**)이 기만의 핵심 지표
- 이후 온라인 리뷰, 범죄 수사, 극단주의 그룹 모니터링 등에 확장 적용

### 사례 5: 브랜드 이미지 및 포지셔닝 분석

온라인 소비자 리뷰 텍스트를 마이닝하여 브랜드 이미지와 포지셔닝을 분석하는 연구에서 LIWC가 어휘 기반 접근법으로 활용됨.

---

## 4. 활용 분야 총정리

| 분야 | 활용 내용 |
|------|-----------|
| **심리학/정신건강** | 우울증, 자살 위험군 식별 (SNS 게시물 분석), 트라우마 회복 추적 |
| **마케팅/광고** | 광고 카피 최적화, 소비자 감정 분석, 광고 CTR 예측 |
| **소비자 분석** | 온라인 리뷰 진위 판별, 소비자 심리 파악, 브랜드 인식 분석 |
| **브랜드 분석** | 브랜드 포지셔닝, 브랜드 이미지 비교, 럭셔리 브랜드 커뮤니케이션 |
| **SNS 분석** | 소셜미디어 감성 분석, 인플루언서 진정성 평가, 위기 감지 |
| **범죄수사/포렌식** | 저자 식별(authorship attribution), 위협 평가, 범죄 예측 |
| **정치/커뮤니케이션** | 정치인 연설 분석, 미디어 편향 분석, 대중 소통 패턴 |
| **문학/인문학** | 작가 스타일 분석, 텍스트 분류, 표절 탐지 |
| **건강/의학** | 다이어트 블로그 분석으로 체중 감량 가능성 예측, 환자 커뮤니케이션 |
| **인사/조직** | 지원서/면접 텍스트 분석, 조직 내 커뮤니케이션 패턴 파악 |

---

## 5. 관련 도구 및 기법

### 주요 도구

| 도구 | 설명 |
|------|------|
| **LIWC-22** | Pennebaker 개발. "골드 스탠다드" 텍스트 분석 소프트웨어. 100개+ 차원 분석. 20,000건+ 학술논문에 사용. (liwc.app) |
| **K-LIWC** | LIWC의 한국어 버전. 품사/기본형/의미 수준에서 분석 가능 |
| **KoNLPy** | 한국어 자연어처리 파이썬 패키지. 형태소 분석기 포함 (꼬꼬마, 한나눔, Mecab 등) |
| **한국어 감정사전** | 군산대 Data Intelligence Lab 개발. 표준국어대사전 기반 긍/부정어 추출 |
| **KOALA** | 한국어 텍스트 분석 웹 도구 (koala4text.com) |

### 핵심 분석 기법

| 기법 | 설명 |
|------|------|
| **사전 기반 분석** | 사전 정의된 단어 목록으로 텍스트를 범주화 (LIWC 방식) |
| **스타일로메트리** | 기능어 패턴을 "언어적 지문"으로 사용하여 저자/스타일 식별 |
| **N-gram 분석** | 단어/문자의 연속 패턴 분석 (기능어 인접 네트워크 포함) |
| **감성 분석** | 감정어 + 기능어를 결합한 복합 감성 분석 |
| **기계학습 분류** | SVM, Naive Bayes, Random Forest 등으로 기능어 피처 기반 분류 |
| **딥러닝/트랜스포머** | BERT, GPT 등으로 기능어 패턴을 포함한 맥락적 텍스트 분석 |

---

## 6. 마케터를 위한 시사점

1. **소비자 리뷰의 진정성 판별**: 1인칭 대명사 과다 사용, 감정어 패턴으로 가짜 리뷰를 걸러낼 수 있다
2. **광고 카피 최적화**: 기능어 패턴에 따라 CTR이 달라진다 — 제품 카테고리별로 최적의 언어 전략이 다름
3. **브랜드 인식 모니터링**: 소비자가 브랜드에 대해 쓸 때 사용하는 대명사와 기능어 패턴이 브랜드와의 심리적 거리를 보여준다
4. **LIWC/K-LIWC를 실무 도구로 활용 가능**: 소비자 리뷰, SNS 댓글, 설문 응답 등을 대규모로 분석 가능

---

---

## 7. 마케팅/소비자 조사 관점 심화 리서치

> 추가 작성일: 2026-03-29 | 심화 리서치

---

### 7.1 소비자 리뷰 분석 사례: 기능어로 리뷰 진정성, 구매 의도, 만족도 분석

#### (1) 가짜 리뷰 탐지 - LIWC 기반 기만 탐지 연구

**연구 개요:** 다수의 연구에서 LIWC의 언어적 범주를 활용하여 온라인 허위 리뷰를 탐지하는 모델을 구축하였다.

**사용된 기능어 지표:**
| 지표 | 가짜 리뷰 패턴 | 진짜 리뷰 패턴 |
|------|---------------|---------------|
| 1인칭 대명사 (I, me, my) | 과다 사용 - 경험 조작 시 자기참조 증가 | 자연스러운 비율 |
| 감정 과정어 (affective processes) | 감정 관련 어휘 과장 | 균형 잡힌 감정 표현 |
| 긍정 감정어 (positive emotion) | 비정상적으로 높음 | 부정 감정어가 자연스럽게 혼합 |
| 지각 과정어 (perceptual processes) | 빈번 - 감각적 묘사로 신빙성 조작 | 구체적 제품 디테일에 집중 |
| 느낌표 | 조작적 리뷰에서 높은 빈도 | 상대적으로 적음 |

**핵심 결과:**
- 15개 언어적 단서만으로도 합리적 수준의 탐지 성능 달성
- 특성 선택 기법 적용 시 **4개 피처만으로 79% 정확도** 달성
- LIWC + 바이그램 조합으로 **89.8% 성능** 달성
- 단, LIWC 기반 피처는 **도메인 변화에 취약** - 제품 카테고리가 바뀌면 성능 하락

**비즈니스 활용:**
- 이커머스 플랫폼의 리뷰 품질 관리 시스템 구축
- 마케터가 경쟁사 리뷰의 진정성을 평가하는 데 활용
- 자사 리뷰 모니터링에서 의심스러운 패턴 자동 감지

> **참고:** [Linguistic Features for Detecting Fake Reviews (NSF)](https://par.nsf.gov/servlets/purl/10282263), [What makes deceptive online reviews? - Nature](https://www.nature.com/articles/s41599-023-02295-5), [LIWC categories associated with fake reviews - ResearchGate](https://www.researchgate.net/figure/LIWC-categories-associated-with-fake-reviews_tbl2_343502585)

#### (2) 리뷰 유용성(Helpfulness) 예측

**연구 개요:** Amazon 등 플랫폼의 20,997건 리뷰(TV, 프린터)를 분석하여 어떤 언어적 특성이 리뷰 유용성을 높이는지 연구하였다.

**주요 발견:**
- **비인격적 스타일(impersonal style)**로 작성된 리뷰가 인격적 스타일보다 더 유용하다고 인식됨
- 제품 유형별로 리뷰의 심리적/언어적 특성이 다르며, 유용성에 영향을 미치는 요인도 상이
- LIWC 변인은 심리적(사고/감정 과정), 언어적(문장 구조), 메타데이터 세 그룹으로 분류하여 활용

**실무 시사점:**
- 리뷰 가이드라인 설계 시 "객관적 톤"을 권장하면 유용성 높은 리뷰가 유도됨
- 제품 카테고리별 맞춤형 리뷰 분석 프레임워크 필요

> **참고:** [Linguistic Style and Online Review Helpfulness](https://livrepository.liverpool.ac.uk/3014449/1/Wang%20and%20Karimi%20ICIS.pdf), [Predicting Helpfulness of Online Customer Reviews](https://www.mdpi.com/2071-1050/10/6/1735)

---

### 7.2 광고 카피/브랜드 메시지 최적화: 기능어 패턴이 광고 효과에 미치는 영향

#### (1) 인스타그램 광고 CTR과 LIWC 지표 상관관계 (Inoue & Yoshida, 2023)

**연구 배경:** 쓰쿠바대학교 연구팀이 일본 인스타그램 건강제품/화장품 광고 텍스트를 LIWC 일본어 버전으로 분석하여 CTR과의 상관관계를 규명하였다.

**구체적 상관계수:**

| LIWC 카테고리 | 건강제품 본문 | 건강제품 이미지 내 텍스트 | 화장품 본문 |
|--------------|-------------|----------------------|-----------|
| 부정감정 (negemo) | **+0.221** | **+0.302** | **+0.254** |
| 생물학적 과정 | +0.151 | - | **-0.308** |
| 인지적 과정 | +0.152 | - | - |
| 돈/가격 관련 | - | **-0.170** | **+0.259** |
| 정서적 과정 | - | - | +0.226 |

**핵심 인사이트:**
- **부정 감정(negemo)**이 두 카테고리 모두에서 CTR과 가장 강한 양의 상관 -- 불안/위기감 자극 광고가 높은 참여율
- **건강제품**: 가격 언급을 피하고, "피로", "체지방", "혈압" 등 건강 결핍 관련 긴급성 강조가 효과적
- **화장품**: 가격 정보 포함이 CTR에 긍정적, 한시적 오퍼 제시가 효과적
- **화장품**: "매끈한", "윤기나는" 등 감각적 묘사어는 오히려 CTR과 부적 상관

**비즈니스 의사결정:**
- 광고 카피 A/B 테스트 시 LIWC 지표를 사전 예측 변수로 활용 가능
- 제품 카테고리별 차별화된 카피 전략 수립의 과학적 근거 제공

> **참고:** [Analysis of Psychographic Indicators via LIWC and CTR for Instagram Ads - arXiv](https://arxiv.org/abs/2312.08235)

#### (2) 대명사 선택이 소비자 행동에 미치는 영향

**연구 1: "I" vs "We" - 고객 서비스 상호작용 (Packard, Moore & McFerran, 2018)**

Journal of Marketing Research에 발표된 이 연구에서:
- 기업 상담원이 **"I"(나)**를 사용하면 → 고객이 "이 상담원이 나를 위해 느끼고 행동한다"고 인식
- **"We"(우리)**를 사용하면 → 기업 전체의 비인격적 대응으로 인식
- 결과: **"I" 사용 시 고객 만족도, 구매 의도, 실제 구매 행동 모두 상승**
- 기존 CS 매뉴얼에서 "we" 사용을 권장하던 통념을 뒤집는 발견

**연구 2: 2인칭 대명사("You") 효과 (Cruz, Leonhardt & Pezzuti, 2017)**

Journal of Interactive Marketing 연구:
- 광고에서 **"you/your/yours"** 사용 → 소비자 **자기참조(self-referencing)** 증가
- 3인칭 대비 2인칭 사용 시: 광고 태도 상승, 광고 신뢰성 증가, 구매 의도 증가
- "you" 표현을 접한 참가자는 문제 해결 책임감이 **21% 더 높게** 인식

**연구 3: 글로벌 브랜드 SNS 대명사 분석 (Labrecque, 2020)**

Psychology & Marketing에서 15,788개 페이스북 브랜드 포스트 분석:
- **1인칭 단수(I)**, **1인칭 복수(we)**, **2인칭(you)**, **3인칭 단수(he/she)**, **3인칭 복수(they)** 각각이 좋아요, 댓글, 공유에 미치는 영향이 상이
- 대명사 유형별로 인게이지먼트 유형이 달라지는 패턴 발견

**비즈니스 의사결정:**
- CS 스크립트에서 "저희가(we)" 대신 **"제가(I)"** 사용으로 고객 만족도 개선
- 광고 카피에서 **"당신(you)"** 활용으로 소비자 몰입도 증가
- SNS 포스트 작성 시 목적(좋아요 vs 댓글 vs 공유)에 따라 대명사 전략 차별화

> **참고:** [Packard & Moore - JMR](https://journals.sagepub.com/doi/10.1509/jmr.16.0118), [Cruz et al. - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1094996817300348), [Labrecque - Psychology & Marketing](https://onlinelibrary.wiley.com/doi/10.1002/mar.21341)

#### (3) 주관적 vs 객관적 광고 텍스트 스타일 (2024)

PMC에 발표된 연구에서:
- **주관적 광고** → 더 높은 매력도(CTR 상승) - 상위 퍼널에서 효과적
- **객관적 광고** → 더 높은 직접 설득력(CVR 상승) - 하위 퍼널에서 효과적
- 기능어 관점에서: 주관적 텍스트는 1인칭 대명사, 감정 수식어가 많고, 객관적 텍스트는 수치/비교 표현이 풍부

> **참고:** [Subjective or objective: Text Style in Computational Advertising - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11630691/)

---

### 7.3 브랜드 포지셔닝/이미지 분석: 소비자 텍스트에서 기능어로 브랜드 인식 측정

#### (1) LIWC-22 4대 요약 변수를 활용한 브랜드 분석

LIWC-22는 다수의 기능어 지표를 조합한 **4개 요약 알고리즘**을 제공하며, 이를 브랜드 분석에 활용할 수 있다:

| 요약 변수 | 산출 방식 | 브랜드 분석 활용 |
|-----------|----------|----------------|
| **분석적 사고 (Analytical Thinking)** | 형식적, 논리적, 위계적 사고 단어 비율 | 소비자가 브랜드를 이성적/감성적 중 어떤 방식으로 인식하는지 |
| **영향력 (Clout)** | 1인칭 단수("I") 적게, 1인칭 복수("we")/2인칭("you") 많이 사용 | 소비자가 브랜드에 대해 느끼는 자신감/권위 수준 |
| **진정성 (Authenticity)** | 자기모니터링 수준 반영 | 소비자가 브랜드에 대해 솔직하게 표현하는 정도 |
| **감정 톤 (Emotional Tone)** | 긍정/부정 감정어 비율 종합 (50 이상=긍정, 미만=부정) | 전반적 브랜드 감성 평가 |

#### (2) 럭셔리 브랜드 소비자 언어 특성 (Oc et al., 2023)

Psychology & Marketing에 발표된 럭셔리 브랜드 eWOM 분석:

**주요 발견:**
- 소비자들이 **고급 브랜드**에 대해 쓸 때: **더 분석적이고, 덜 진정한 언어** 사용
- **영향력(Clout) 점수가 낮음** -- 고급 브랜드 앞에서 자신감/확신이 줄어드는 심리 반영
- 전문 브랜드(specialty)와 편의 브랜드(convenience) 간 LIWC 패턴 차이가 가장 두드러짐
- 전문 제품에 대한 댓글은 단어 수가 적지만 더 분석적이고 진정한 언어 사용

**비즈니스 시사점:**
- 럭셔리 브랜드 매니저는 소비자 언어의 "진정성 점수" 추적으로 브랜드 접근성 모니터링
- Clout 점수가 낮다면 = 소비자가 브랜드를 "범접하기 어렵다"고 느끼는 신호
- 브랜드 리포지셔닝 전후 LIWC 요약 변수 변화 추적 가능

> **참고:** [Luxury is what you say - Psychology & Marketing](https://onlinelibrary.wiley.com/doi/full/10.1002/mar.21831)

#### (3) 온라인 리뷰 텍스트 마이닝을 통한 브랜드 이미지 비교

Journal of Retailing and Consumer Services에 발표된 연구에서 LIWC를 어휘 기반 접근법으로 활용하여 온라인 소비자 리뷰에서 브랜드 이미지와 포지셔닝을 분석하는 구조화된 절차를 제안하였다.

> **참고:** [Mining online consumer reviews for brand image - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0969698922000820)

---

### 7.4 소셜미디어 마케팅 분석

#### (1) 페이스북 브랜드 페이지 감성 분석

850개 소비자 댓글(83개 페이스북 브랜드 페이지)을 LIWC2015 어휘 사전으로 분석한 연구에서:
- LIWC 어휘 기반 접근법이 기계학습 방법과 **비슷한 수준의 감정 분류 정확도** 달성
- 브랜드 모니터링에서 LIWC가 실용적 대안이 될 수 있음을 입증

#### (2) SNS 인플루언서 텍스트 분석

**마이크로 vs 매크로 인플루언서 언어 차이:**
- 소규모/중규모 인플루언서가 **인게이지먼트 유도**에 더 효과적
- 대규모 인플루언서가 **구매 의도**에 더 큰 영향
- 마이크로인플루언서 콘텐츠는 즐겨찾기에 저장되는 경향, 다른 유형은 공유되는 경향
- 스폰서 포스트가 비스폰서 포스트보다 **더 높은 인게이지먼트** (특히 마이크로인플루언서)
- 기능어 관점: 진정성 높은 인플루언서일수록 1인칭 대명사와 자기노출 표현이 자연스럽게 분포

#### (3) 브랜드 라이벌리 효과 (Berendt et al., 2024)

Journal of Marketing Research 연구에서 브랜드가 SNS에서 **라이벌 경쟁사를 언급**할 때:
- 비라이벌 경쟁사 언급 대비 **소비자 인게이지먼트가 증가** (트위터 데이터 실증)
- 이는 "라이벌 참조 효과(Rivalry Reference Effect)"로 명명

> **참고:** [The Rivalry Reference Effect - JMR](https://journals.sagepub.com/doi/10.1177/00222437241248414)

---

### 7.5 설문/FGI/인터뷰 텍스트 분석

#### (1) LIWC와 질적 분석의 상호보완

**연구 배경 (2024):** 질적 데이터(인터뷰, FGI 전사본)에 LIWC를 적용하면 주제 분석(thematic analysis)만으로는 놓칠 수 있는 인사이트를 보완적으로 제공한다.

**구체적 활용 방법:**
- 인터뷰 전사본을 LIWC에 입력 → 각 참가자별 언어적/심리적 프로필 자동 생성
- 그룹 간(예: 충성 고객 vs 이탈 고객) **기능어 사용 패턴 차이** 통계적 비교
- 주제 분석에서 발견하지 못한 **무의식적 언어 패턴** 포착 가능

**마케팅 적용 시나리오:**
| 조사 유형 | LIWC 활용법 | 기대 인사이트 |
|-----------|-----------|-------------|
| 브랜드 인식 FGI | 참가자별 Clout, Authenticity 점수 비교 | 진정한 의견 vs 사회적 바람직성 편향 구분 |
| 제품 사용 인터뷰 | 감정 톤, 인지 과정어 분석 | 명시적으로 말하지 않는 심리적 저항/열의 포착 |
| 광고 반응 설문 | 개방형 응답 LIWC 분석 | 정량적 만족도 점수와 실제 언어 표현 간 괴리 발견 |
| 고객 여정 인터뷰 | 시간적 참조어, 인과 관계어 분석 | 고객이 인식하는 핵심 전환 모멘트 식별 |

> **참고:** [Are we listening to every word? Multiple analytic methods for qualitative data - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12710751/), [LIWC In Practice - UBC](https://hecc.ubc.ca/quantitative-textual-analysis/qta-practice/liwcinpractice/)

---

### 7.6 고객 서비스/VOC 분석

#### (1) 콜센터 상담 언어 분석

**핵심 연구 결과:**
- 25,008건의 콜센터 대화 분석 결과: **긍정적(vs 부정적) 고객 감정이 만족도와 추천 의향에 더 강한 영향**
- 상담원의 언어 유형이 대화 단계별로 다르게 작용:
  - **대화 초반/후반**: 감정적(affective) 언어 사용 시 만족도 상승
  - **대화 중반(업무 처리부)**: 인지적(cognitive) 언어 사용 시 만족도 상승
  - 반대 패턴은 만족도 하락

**사용된 기능어 지표:**
| 지표 | 정의 | CS 활용 |
|------|------|---------|
| 감정어 (affective) | 따뜻함/공감 표현 | 대화 시작과 마무리에 배치 |
| 인지어 (cognitive) | 문제 해결/논리적 표현 | 업무 처리 구간에 집중 |
| "I" 대명사 | 개인적 책임감 표현 | "제가 확인해드리겠습니다" |
| "We" 대명사 | 조직 차원 대응 | "저희가 처리하겠습니다" |

**LIWC 맞춤 사전 활용:**
- 연구자들이 LIWC 사전을 커스터마이즈하여 **"relating"(따뜻함)**과 **"resolving"(역량)** 사전 개발
- CS 상담원 성과 평가에 언어 분석 지표 도입 가능

**비즈니스 의사결정:**
- CS 교육 프로그램에 "대화 단계별 언어 전략" 반영
- 상담원 성과 평가에 LIWC 기반 언어 품질 지표 도입
- VOC 대량 분석 시 감정 톤 변화 추이로 서비스 품질 모니터링

> **참고:** [Conversational Dynamics: Employee Language - CKGSB](https://www.ckgsb.edu.cn/uploads/liyangwenz.pdf), [How Concrete Language Shapes Customer Satisfaction - JCR](https://academic.oup.com/jcr/article/47/5/787/5873524), [Emotions and Communication Style in Call Centers - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0148296325000153)

---

### 7.7 경쟁사 분석: 경쟁 브랜드 간 소비자 언어 차이

#### (1) 항공사 브랜드 비교 사례

풀서비스 항공사 vs 저가 항공사의 광고 텍스트를 LIWC로 분석한 결과:
- 풀서비스 항공사 광고가 **Clout(영향력), Analytical Thinking(분석적 사고), Authenticity(진정성)** 점수 모두 높음
- 브랜드 포지셔닝 전략이 언어적 수준에서 측정 가능하다는 실증적 근거

#### (2) 경쟁사 간 소비자 리뷰 언어 비교 프레임워크

**분석 프레임:**
1. 동일 카테고리 경쟁사(A사 vs B사) 소비자 리뷰 수집
2. LIWC로 양사 리뷰의 4대 요약 변수(Analytical, Clout, Authenticity, Tone) 비교
3. 기능어 세부 지표(대명사 분포, 시간 참조, 인과 관계어) 비교
4. 통계적 유의성 검정으로 브랜드 간 차이 확인

**실무 활용 예시:**
| 비교 항목 | A 브랜드 패턴 | B 브랜드 패턴 | 해석 |
|-----------|-------------|-------------|------|
| 1인칭 대명사 높음 | "내가 사용해보니..." | - | 개인적 경험 중심 → 감정적 유대 |
| 3인칭 대명사 높음 | - | "이 제품은...그것은..." | 객관적 평가 중심 → 이성적 선택 |
| Clout 점수 높음 | 소비자가 자신감 있게 추천 | - | 강한 브랜드 옹호(advocacy) |
| Authenticity 낮음 | - | 소비자가 조심스럽게 표현 | 브랜드에 대한 불확실성/거리감 |

---

### 7.8 실무 적용 가능성: 마케터를 위한 LIWC/K-LIWC 워크플로우

#### (1) 도구 개요

| 도구 | 가격 | 한국어 지원 | 특징 |
|------|------|-----------|------|
| **LIWC-22** | $89.95 (개인), $179.90 (기관) | 영어 중심, 다국어 확장 중 | 골드 스탠다드, .txt/.csv/.xlsx 입력, 100개+ 차원 |
| **K-LIWC** | 학술 연구용 | **한국어 전용** | 39개 언어 지표 + 44개 심리 지표, 형태소 분석 내장 |
| **Receptiviti API** | API 기반 과금 | 다국어 | LIWC를 프로그래밍 방식으로 접근, 94개 카테고리 |
| **Python + KoNLPy** | 무료 | **한국어 전용** | 한국어 형태소 분석 + 커스텀 사전 구축 가능 |

#### (2) 마케터를 위한 구체적 워크플로우

**시나리오 A: 소비자 리뷰 인사이트 분석**
```
1. 데이터 수집: 자사/경쟁사 리뷰 크롤링 (네이버 쇼핑, 쿠팡, 아마존 등)
2. 전처리: 텍스트 정제, 리뷰당 하나의 행으로 CSV 정리
3. LIWC/K-LIWC 분석 실행: CSV 파일 입력 → 각 리뷰별 100개+ 지표 자동 산출
4. 핵심 지표 비교:
   - Emotional Tone: 전반적 만족도 수준
   - Authenticity: 리뷰 진정성 수준
   - 긍정/부정 감정어 비율: 세부 감성 분석
   - 1인칭 대명사 비율: 개인적 경험 기반 리뷰 비율
5. 인사이트 도출: 자사 vs 경쟁사 패턴 차이 → 전략적 시사점
```

**시나리오 B: 광고 카피 사전 테스트**
```
1. 광고 카피 후보안 3~5개 작성
2. 각 카피를 LIWC에 입력
3. 핵심 지표 확인:
   - 부정 감정어(negemo) 비율 → CTR 예측
   - 2인칭 대명사(you) 포함 여부 → 소비자 몰입도 예측
   - 분석적 사고 vs 감정적 톤 → 퍼널 단계 적합성
4. 과거 성과 데이터와 교차 검증
5. 최종 카피 선정 + A/B 테스트 설계
```

**시나리오 C: CS/VOC 모니터링 대시보드**
```
1. 주간/월간 VOC 데이터 수집 (CS 상담 기록, 고객 이메일, SNS 멘션)
2. LIWC 배치 분석 실행
3. 대시보드 핵심 KPI:
   - Emotional Tone 추이 그래프 (시계열)
   - 부정 감정어 급증 경보 (위기 감지)
   - 인지 과정어 비율 변화 (문제 복잡도 추적)
   - Authenticity 점수 변화 (고객 신뢰도 추적)
4. 이상치 탐지 → 원인 분석 → 대응 조치
```

**시나리오 D: FGI/인터뷰 보완 분석**
```
1. FGI/인터뷰 녹취록 전사(텍스트화)
2. 참가자별 발언을 개별 텍스트 파일로 분리
3. LIWC/K-LIWC 분석 → 참가자별 심리적 프로필 생성
4. 그룹 비교:
   - 충성 고객 vs 이탈 고객의 기능어 패턴 차이
   - Authenticity 점수로 "진짜 의견" vs "면접관 효과" 구분
   - 감정 톤 vs 명시적 응답 간 괴리 탐지
5. 주제 분석(thematic analysis) 결과와 교차 검증
```

---

### 7.9 한국 마케팅 연구 사례

#### (1) K-LIWC를 이용한 온라인 기만 사용후기 연구 (한국소비자학회)

**연구 개요:** K-LIWC(39개 언어 지표 + 44개 심리 지표)를 사용하여 온라인 리뷰의 기만성을 탐지한 한국 최초의 연구 중 하나.

**연구 설계:**
- 연구 1, 2: 기만 의도가 있는 리뷰 vs 진실한 리뷰 비교
- 연구 3: 긍정적 기만(불만족 제품에 긍정 리뷰) vs 부정적 기만(만족 제품에 부정 리뷰) 분석

**핵심 결과:**

| 지표 유형 | 기만 리뷰에서 일관되게 차이를 보인 변인 |
|-----------|-------------------------------------|
| 언어 지표 | 형태소, 일반 명사, 조사 |
| 심리 지표 | 감정/정서 과정, 긍정 감정, 긍정 느낌, 감각/지각 과정 |
| 기만 의도 추가 | 문장, 어절, 형태소, 일반 명사, 조사, 부사, 어미, 추정 외래 명사 |

**K-LIWC 한국어 특수성:**
- 한국어는 교착어이므로 영어 LIWC와 달리 **형태소 태깅**이 필수
- "체면"과 "한국적 정서"(한, 정 등) 관련 단어를 별도 분석 변인에 포함
- 조사, 어미 등 한국어 고유 기능어가 기만 탐지의 핵심 변인으로 작용

> **참고:** [한국어 언어분석 프로그램(KLIWC)을 이용한 온라인 기만 사용후기 연구 - KCI](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002088779), [광고정보센터](https://www.adic.or.kr/lit/paper/show.vw?ukey=134001)

#### (2) KLIWC를 이용한 광고효과 탐색연구 (디지털융복합연구)

**연구 설계:** 대학생 384명 대상, 고관여/저관여 제품의 긍정/부정 광고 평가글을 KLIWC로 분석.

**핵심 결과:**
- **17개 심리사회적 변인**과 **9개 언어학적 변인**에서 긍정/부정 광고 간 유의미한 차이
- 광고효과 변인(광고태도, 제품태도, 구매의도)과 유의미한 상관을 보인 KLIWC 변인:
  - 긍정 정서, 부정 정서
  - 제한, 확신
  - 신체 상태와 기능
  - 수면/꿈

**시사점:** 광고 평가글이 소비자의 심리적 반응을 반영하며, 전통적 자기보고식 설문을 **텍스트 분석으로 보완/대체** 가능하다는 근거.

> **참고:** [언어분석을 이용한 광고효과 탐색연구: KLIWC를 중심으로 - earticle](https://www.earticle.net/Article/A362538), [Korea Science](http://koreascience.or.kr/article/JAKO201928862524294.page)

#### (3) TV 홈쇼핑 광고 효과측정 연구

**연구 방법:** 사고발성법(think-aloud protocol) + KLIWC를 결합하여 TV 홈쇼핑 시청 중 소비자 반응 분석.

**핵심 결과:**
- 긍정/부정 광고 간 심리사회학적 변인뿐 아니라 **언어학적 변인에서도 유의미한 차이**
- KLIWC 변인들이 구매자극도, 광고태도, 제품태도, 구매의도 및 광고반응 변인과 상관

> **참고:** [사고발성법과 언어분석을 활용한 TV 홈쇼핑 광고의 효과측정 연구 - KCI](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002508807)

---

### 7.10 기능어 분석의 핵심 원리: 왜 내용어가 아닌 기능어인가?

마케터가 기능어 분석의 가치를 이해하기 위한 핵심 원리:

| 원리 | 설명 | 마케팅 함의 |
|------|------|-----------|
| **자동적 처리** | 기능어는 무의식적/자동적으로 산출되어 의도적 조작이 어려움 | 소비자의 **진짜 심리**를 포착 가능 (설문 편향 극복) |
| **자기표현 편향 불감** | 내용어는 자기표현에 의해 조작 가능하지만 기능어는 아님 | 가짜 리뷰, 허위 추천 탐지의 이론적 근거 |
| **관계성 반영** | 대명사 사용은 화자와 대상의 심리적 거리를 반영 | "I" vs "we" vs "they"로 브랜드-소비자 관계 강도 측정 |
| **인지 복잡성 지표** | 전치사, 접속사, 부사 사용은 사고의 복잡성 반영 | 소비자의 의사결정 과정 복잡도/확신도 추정 |
| **범문화적 적용** | 기능어 원리는 언어를 넘어 보편적으로 적용 | 글로벌 브랜드의 다국가 소비자 비교 분석 가능 |

---

## 8. 심화 리서치: 구체적 연구 데이터와 수치

> 추가 작성일: 2026-03-29 | 각 케이스별 논문 원문/초록 기반 수치 정리

---

### 8.1 CASE 3: 인스타그램 광고 CTR (Inoue & Yoshida, 2023)

**논문:** "Analysis of Psychographic Indicators in Ad Texts through LIWC and CTR in Instagram"
**출처:** arXiv:2312.08235 (2023.12.13)

#### 샘플 사이즈
- **건강제품 광고**: 3,555개 고유 광고 (48개 제품)
- **화장품 광고**: 3,270개 고유 광고 (45개 제품)
- 총 6,825개 인스타그램 광고 분석

#### 평균 CTR
- 건강제품: **0.75%**
- 화장품: **0.61%**

#### LIWC 카테고리별 CTR 상관계수 전체 표

**건강제품 - 본문(Body Text)**

| LIWC 카테고리 | 상관계수 (rho) | 해석 |
|--------------|-------------|------|
| Affect (정서적 과정) | -0.029 | 거의 무상관 |
| Positive emotions (긍정 감정) | **-0.130** | 긍정적 톤이 CTR을 오히려 낮춤 |
| **Negative emotions (부정 감정)** | **+0.221** | 불안/위기감이 CTR 상승 |
| Cognitive processes (인지적 과정) | +0.152 | 약한 양의 상관 |
| Biological processes (생물학적 과정) | +0.151 | 건강 관련 구체적 언급이 효과적 |
| Drives (동기) | -0.182 | 동기부여 표현은 오히려 역효과 |
| Personal concerns - money (돈) | +0.056 | 거의 무상관 |
| Personal concerns - work (일) | -0.044 | 거의 무상관 |
| Personal concerns - leisure (여가) | -0.120 | 약한 부적 상관 |
| Relativity (상대성) | +0.013 | 무상관 |

**건강제품 - 이미지 내 텍스트(In-Image Text)**

| LIWC 카테고리 | 상관계수 (rho) | 해석 |
|--------------|-------------|------|
| Affect (정서적 과정) | +0.218 | 이미지에서는 감정 표현이 효과적 |
| **Negative emotions (부정 감정)** | **+0.302** | 전체 중 가장 높은 상관계수 |
| Biological processes (생물학적 과정) | +0.022 | 거의 무상관 |
| Personal concerns - money (돈) | -0.170 | 이미지 내 가격 언급은 역효과 |
| Personal concerns - work (일) | -0.190 | 부적 상관 |

**화장품 - 본문(Body Text)**

| LIWC 카테고리 | 상관계수 (rho) | 해석 |
|--------------|-------------|------|
| Affect (정서적 과정) | +0.226 | 감정 표현이 CTR에 긍정적 |
| Positive emotions (긍정 감정) | +0.138 | 약한 양의 상관 |
| **Negative emotions (부정 감정)** | **+0.254** | 부정 감정이 여전히 강한 효과 |
| **Personal concerns - money (돈)** | **+0.259** | 가격/할인 정보가 CTR 상승에 기여 |
| Cognitive processes (인지적 과정) | +0.164 | 약한 양의 상관 |
| **Biological processes (생물학적 과정)** | **-0.308** | 감각적 묘사가 오히려 CTR 하락(전체 중 가장 강한 부적 상관) |
| Drives (동기) | +0.194 | 약한 양의 상관 |

**화장품 - 이미지 내 텍스트(In-Image Text)**

| LIWC 카테고리 | 상관계수 (rho) | 해석 |
|--------------|-------------|------|
| Biological processes (생물학적 과정) | +0.020 | 거의 무상관 |
| **Perception processes (지각 과정)** | **+0.259** | 시각적 묘사가 이미지 텍스트에서 효과적 |
| Personal concerns - money (돈) | -0.076 | 거의 무상관 |
| Relativity (상대성) | -0.192 | 부적 상관 |

#### 핵심 발견
- **부정 감정(negemo)**이 건강제품과 화장품 모두에서 CTR과 가장 일관된 양의 상관
- 건강제품 이미지 텍스트에서 부정 감정 상관계수 **rho=0.302**가 전체 최고치
- 화장품에서 생물학적 과정어(매끈한, 윤기나는 등)가 **rho=-0.308**로 강한 역효과 -- 감각적 묘사보다 문제 제기가 더 효과적

---

### 8.2 CASE 4(a): 대명사와 소비자 행동 - Packard, Moore & McFerran (2018)

**논문:** "(I'm) Happy to Help (You): The Impact of Personal Pronoun Use in Customer-Firm Interactions"
**저널:** Journal of Marketing Research, Vol. 55, No. 4, pp. 541-555 (2018)

#### 연구 설계: 5개 스터디 (실험실 실험 + 현장 데이터)

**Study 1 (현장 데이터)**
- **샘플**: 대형 온라인 리테일러의 **1,277건 고객 서비스 이메일 상호작용**, 구매 데이터와 연결
- **핵심 결과**: "I" 사용 빈도가 10% 증가하면 매출이 **0.8% 증가**
- **잠재적 효과**: 현재 "We"가 사용되는 사례의 90%를 "I"로 전환 가능 → 잠재적 **최대 7% 매출 증가**

**Study 2-3 (실험)**
- **핵심 결과**: "I" 사용 시 "We" 대비:
  - 고객 만족도 **19% 더 높음**
  - 구매 의도 **15% 더 높음**
- **매커니즘**: "I"가 공감(empathy)과 대리(agency) 인식을 높여 만족도/구매로 연결

**Study 4 (현장 데이터)**
- **샘플**: 실제 고객-기업 이메일 상호작용 **1,000건 이상**
- "I" 대명사 사용과 이후 6개월간의 **실제 구매 행동** 간 양의 관계 확인

**Study 5**
- "You" 대명사의 효과 검증: 고객을 지칭하는 "you" 사용은 만족도/구매 의도에 **유의미한 영향 없음**, 경우에 따라 **부정적 효과** 발생

#### 현업 실태 조사
- 미국 CS 매니저 중 **92%**가 "We" 표현을 사용하겠다고 응답
- 상위 40개 온라인 리테일러 중: **100%**가 "We" 사용, **97.5%**가 "You" 사용, **45%**만 "I" 사용
- 즉, 대부분의 기업이 효과가 낮은 대명사 전략을 사용 중

---

### 8.3 CASE 4(b): 2인칭 대명사 "You" 효과 - Cruz, Leonhardt & Pezzuti (2017)

**논문:** "Second Person Pronouns Enhance Consumer Involvement and Brand Attitude"
**저널:** Journal of Interactive Marketing, Vol. 39, pp. 104-116 (2017)

#### 연구 설계
- 다수의 실험(페이스북 브랜드 포스트 및 블로그 텍스트 사용)
- "you/your/yours" 포함 조건 vs 미포함 조건 비교

#### 핵심 결과
- "You" 포함 시 소비자 **자기참조(self-referencing)** 유의미하게 증가
- 자기참조 증가 → **소비자 몰입도(involvement)** 상승 → **브랜드 태도** 개선
- 자기참조가 매개변인(mediator)으로 작용함을 확인
- **책임감 21% 증가**: "you" 표현을 접한 참가자는 문제 해결 책임감을 21% 더 높게 인식 (주: 이 수치는 원논문 내 특정 실험 조건에서의 결과로, 검색 범위에서 정확한 원출처 세부 실험 번호를 확인하지 못함 -- 추가 확인 필요)

#### 조절 변인
- **집단주의(collectivism) 수준**이 조절 변인으로 작용
- 집단주의가 **낮은** 소비자에서 "you" 효과가 더 강하게 나타남
- 집단주의가 **높은** 소비자에서는 효과 감소

---

### 8.4 CASE 4(c): SNS 대명사 분석 - Labrecque, Swani & Stephen (2020)

**논문:** "The Impact of Pronoun Choices on Consumer Engagement Actions: Exploring Top Global Brands' Social Media Communications"
**저널:** Psychology & Marketing, Vol. 37, No. 6, pp. 796-814 (2020)

#### 샘플 사이즈
- **15,788개 고유 브랜드 포스트** (페이스북)
- **8개월** 기간 수집
- 글로벌 상위 브랜드들의 페이스북 페이지 대상

#### 분석 방법
- **다변량 포아송 회귀 모델 (Multivariate Poisson Regression)**
- 종속변수: 좋아요(likes), 댓글(comments), 공유(shares)

#### 분석한 5가지 대명사 유형
1. 1인칭 단수 (I)
2. 1인칭 복수 (we)
3. 2인칭 (you)
4. 3인칭 단수 (he/she)
5. 3인칭 복수 (they)

#### 핵심 결과
- **2인칭 "you"**: 댓글(comments)에 **양의 효과** 확인
- **3인칭 복수 "they"**: 좋아요, 댓글, 공유 **세 가지 인게이지먼트 모두 증가**
- 대명사 유형에 따라 유발하는 인게이지먼트 유형이 상이함

#### 브랜드 분류별 차별적 효과
- **쾌락적(hedonic) vs 실용적(utilitarian)** 브랜드에서 대명사 효과가 다르게 나타남
- **제품(goods) vs 서비스(services)** 분류에서도 차이 존재
- (구체적 IRR 값은 논문 본문 접근 필요 -- 저널 접근 제한으로 미확인)

---

### 8.5 CASE 6: 럭셔리 브랜드 - Oc, Plangger, Sands, Campbell & Pitt (2023)

**논문:** "Luxury is what you say: Analyzing electronic word-of-mouth marketing of luxury products using artificial intelligence and machine learning"
**저널:** Psychology & Marketing, Vol. 40, No. 9 (2023)

#### 샘플 사이즈
- **29,000건 이상** 소비자 댓글
- **88개 유튜브 캠페인**
- **9개 럭셔리 브랜드** 대상

#### LIWC 4대 요약 변수 분석

**분석 차원:**
| LIWC 변수 | 정의 | 럭셔리 브랜드에서의 패턴 |
|-----------|------|----------------------|
| Analytical Thinking (분석적 사고) | 형식적, 논리적, 위계적 사고 | 전문(specialty) 제품에서 더 높음 |
| Clout (영향력) | 자신감, 사회적 지위, 리더십 | 고급 브랜드에서 더 낮음 (소비자 위축) |
| Authenticity (진정성) | 자기 모니터링 수준, 솔직함 | 전문 제품에서 더 높음 |
| Emotional Tone (감정 톤) | 긍정/부정 감정어 비율 | 카테고리별 상이 |

#### 브랜드 럭셔리 등급별 비교
- **3단계 럭셔리 분류**: Premium (프리미엄) / Prestige (프레스티지) / Exquisite (최고급)
- **코플랜드 분류**: Convenience (편의품) / Shopping (선매품) / Specialty (전문품)

#### 핵심 결과
- 전문 제품(specialty)에 대한 댓글: **단어 수가 적지만** 더 **분석적(Analytical)**이고 더 **진정한(Authentic)** 언어 사용
- **Scheffe 사후검정** 결과: premium, prestige, exquisite 브랜드 간 각 제품 카테고리에서 모든 LIWC 변수에서 유의미한 차이 발견
  - **예외**: 선매품(shopping products)에서 "Tone"과 "Clout"는 유의미한 차이 없음
- 소비자 인구통계(연령, 성별, 민족)에 따라서도 LIWC 패턴 유의미하게 상이

#### 비즈니스 시사점
- Clout 점수 낮음 = 소비자가 브랜드를 "범접하기 어렵다"고 느끼는 심리적 신호
- 럭셔리 등급이 올라갈수록 소비자 언어가 더 조심스럽고 분석적으로 변화

---

### 8.6 CASE 8: 페이스북 감성 분석 - LIWC vs 기계학습

**논문:** "Social media sentiment analysis: lexicon versus machine learning"
**저널:** Journal of Consumer Marketing, Vol. 34, No. 6, pp. 480-488 (2017)

#### 샘플 사이즈
- **850개 소비자 댓글**
- **83개 페이스북 브랜드 페이지**에서 수집

#### 분석 도구
- **어휘 기반(lexicon-based)**: LIWC2015
- **기계학습(ML)**: RTextTools 패키지

#### 핵심 결과
- 두 접근법의 정확도가 **전반적으로 유사**
- 양쪽 모두 **긍정 감정 분류**에서 부정 감정 분류보다 **더 높은 정확도** 달성
- 두 접근법의 **분류 앙상블은 상당히 상이** -- 같은 댓글을 다르게 분류하는 경우 존재
- **결합 접근법(combined approach)**: 긍정 감정 분류에서 **유의미하게 향상된 성능** 달성
- **부정 감정 분류**는 두 방법 모두 상대적으로 저조 -- 추가 연구 필요

#### 실무 시사점
- LIWC는 ML 인프라 없이도 브랜드 모니터링에 **실용적 대안** 제공
- 최적 성능을 위해서는 어휘 기반 + ML **결합 접근** 권장
- (구체적 정확도 퍼센티지, precision/recall/F1 수치는 논문 본문 접근 필요)

---

### 8.7 CASE 9: 인플루언서 분석 - Cascio Rizzo, Villarroel Ordenes et al. (2024)

**논문:** "How High-Arousal Language Shapes Micro- Versus Macro-Influencers' Impact"
**저널:** Journal of Marketing, Vol. 88, No. 4, pp. 107-128 (2024, 온라인 2023.10.03)

#### 샘플 사이즈
- **20,923개 스폰서 포스트** (인스타그램)
- **1,376명 미국 기반 인플루언서**
- 팔로워 **100,000명**을 마이크로/매크로 기준선으로 설정
- 6개 스터디 (자동화 텍스트/이미지/비디오/오디오 분석 + 사전등록된 통제 실험)

#### 핵심 수치: 고각성 언어(High-Arousal Language)의 효과

**마이크로 인플루언서:**
- 각성도(arousal) 10% 증가 시 인게이지먼트 **평균 5.4% 증가**
- 구체적 예시: "great"를 "superb"로 업그레이드 시 약 **49개 추가 좋아요/댓글** 유발

**매크로 인플루언서:**
- 각성도 10% 증가 시 인게이지먼트 **평균 8.4% 감소** (역효과)
- 마이크로 인플루언서와 **정반대 패턴**

#### 매커니즘: 신뢰성(Trustworthiness)
- 고각성 언어가 마이크로 인플루언서의 신뢰성을 **높이고**, 매크로 인플루언서의 신뢰성을 **낮추는** 것으로 매개됨

#### 매크로 인플루언서의 완화 전략
- **정보적(informative) 프레이밍**: 인게이지먼트 **1.8% 증가** 효과
- "learn", "help" 등 신뢰성 단어 포함 시 각성 페널티 상쇄
- **균형 잡힌 평가(counterbalanced valence)**: 긍정+부정 평가를 함께 제시하면 역효과 완화

#### 감정 유형별 차이 (기존 연구 종합)
| 감정 유형 | 마이크로 인플루언서 | 매크로 인플루언서 |
|-----------|------------------|------------------|
| 고각성 부정 감정 (분노, 혐오) | 인게이지먼트 감소 | **인게이지먼트 증가** |
| 저각성 부정 감정 (두려움, 슬픔) | **인게이지먼트 증가** | 인게이지먼트 감소 |
| 긍정 감정 | **인게이지먼트 증가** (특히 강함) | 인게이지먼트 증가 |

#### 플랫폼 확장
- 틱톡(TikTok)에서도 **음성 피치(vocal pitch)**를 각성도 프록시로 사용하여 동일 패턴 확인

---

### 8.8 CASE 11: 콜센터 대화 분석 - Packard, Li & Berger (2024)

**논문:** "When Language Matters"
**저널:** Journal of Consumer Research, Vol. 51, No. 3, pp. 634-653 (2024)
**저자:** Grant Packard, Yang Li, Jonah Berger

#### 샘플 사이즈
- **23,958개 대화 순간** (conversational moments)
- **2개 기업**의 실제 서비스 대화 수백 건
- 추가: 4개 실험 (총 N = **1,589**)

#### 분석 방법론
- **함수적 데이터 분석(Functional Data Analysis, FDA)** + **Group-Lasso**
- 대화 데이터의 고차원성, 불규칙성, 희소성을 해결하기 위한 새로운 모델링 접근법

#### LIWC 맞춤 사전: "Relating" vs "Resolving"
- 선행 연구에서 LIWC 사전을 커스터마이즈하여 두 가지 핵심 사전 개발:
  - **Relating (따뜻함/관계)**: 감정적(affective) 언어, 공감 표현, 따뜻함 관련 어휘
  - **Resolving (역량/해결)**: 인지적(cognitive) 언어, 문제 해결, 논리적 표현 관련 어휘

#### 핵심 결과: 대화 단계별 언어 효과

| 대화 단계 | 효과적인 언어 유형 | 비효과적인 언어 유형 |
|-----------|------------------|-------------------|
| **초반 (첫 25%)** | 감정적/따뜻한(affective) 언어 | 인지적 언어 |
| **중반 (업무 처리부)** | 인지적/해결(cognitive) 언어 | 감정적 언어 |
| **후반 (마지막 25%)** | 감정적/따뜻한(affective) 언어 | 인지적 언어 |

- 기존 연구의 "따뜻함 vs 역량 트레이드오프" 가설을 부정: **두 가지 모두 중요하지만, 시점(timing)이 핵심**
- 현재 상담원들은 대화 초반에 따뜻한 언어를 **실제보다 덜** 사용하고 있음 → 개선 여지 존재
- 추가 분석: 질문하기(question asking)와 1인칭 대명사도 대화 시점에 따라 효과가 달라짐

#### 25,008건 vs 23,958건 표기 차이
- 기존 보고서에서 "25,008건"으로 기재된 수치는 관련 연구의 대화 건수로, 본 논문(Packard, Li & Berger, 2024)의 공식 수치는 **23,958개 대화 순간(conversational moments)**임
- 이 차이는 "대화 건수"와 "대화 내 분석 단위(moments)" 간의 차이에서 기인할 수 있으며, 또는 동일 연구팀의 관련 연구(예: Packard & Berger, 2021 "How Concrete Language Shapes Customer Satisfaction")의 수치가 혼합되었을 가능성이 있음

---

### 8.9 K-LIWC 한국 연구 심화 데이터

#### (1) 기만 리뷰 연구 (한국소비자학회)

**연구 설계:**
- **3개 연구(Study 1, 2, 3)**로 구성
- K-LIWC의 **39개 언어 지표** + **44개 심리 지표** 활용

**연구 1-2 (기만 의도 포함):**
기만 리뷰에서 더 높게 나타난 지표:

| 구분 | 유의미한 차이를 보인 변인 |
|------|----------------------|
| **언어 지표** | 문장, 어절, 형태소, 일반 명사, 조사, 일반 부사, 어미, 추정 외래 명사 |
| **심리 지표** | 감정/정서 과정, 긍정 감정, 긍정 느낌, 인지 과정, 확신, 감각/지각 과정, 사회적 과정, 의사소통, 가족, 가정, 신체 상태/증상 |

**연구 3 (긍정 기만 + 부정 기만):**
- 긍정 기만: 불만족 제품에 대해 긍정적 리뷰 작성
- 부정 기만: 만족 제품에 대해 부정적 리뷰 작성

**3개 연구 공통 결과:**

| 구분 | 일관된 차이 변인 |
|------|---------------|
| 언어 지표 | **형태소, 일반 명사, 조사** |
| 심리 지표 | **감정/정서 과정, 긍정 감정, 긍정 느낌, 감각/지각 과정** |

**한국어 특수성:**
- 교착어 특성상 **조사와 어미**가 기만 탐지의 핵심 변인
- 영어 LIWC에서는 관찰되지 않는 한국어 고유 패턴
- (구체적 분류 정확도 수치는 논문 본문 접근 필요 -- KCI 원문 접근 제한)

#### (2) 광고효과 탐색연구 (디지털융복합연구, 류연재, 2019)

**연구 설계:**
- **384명** 대학생 대상 온라인 실험
- **고관여/저관여 제품** x **긍정/부정 광고** = 4가지 조건
- 광고 평가글을 KLIWC로 분석

**핵심 결과:**
- **17개 심리사회적 변인**에서 긍정/부정 광고 간 유의미한 차이
- **9개 언어학적 변인**에서 긍정/부정 광고 간 유의미한 차이

**광고효과 변인과 유의미한 상관을 보인 KLIWC 변인:**

| KLIWC 변인 | 상관 대상 (광고효과 변인) |
|-----------|---------------------|
| 긍정 정서 (Positive emotions) | 광고태도, 제품태도, 구매의도 |
| 부정 정서 (Negative emotions) | 광고태도, 제품태도, 구매의도 |
| 제한 (Inhibition) | 광고효과 변인 |
| 확신 (Conviction) | 광고효과 변인 |
| 신체 상태와 기능 (Physical condition) | 광고효과 변인 |
| 수면/꿈 (Sleep/Dreams) | 광고효과 변인 |

- (구체적 상관계수 r 값은 논문 본문 접근 필요 -- 학술 DB 접근 제한)

**시사점:**
- 광고 평가글 텍스트가 소비자의 심리적 반응을 반영
- 전통적 자기보고식 설문을 텍스트 분석으로 보완/대체 가능성 실증

---

### 8.10 데이터 확보 현황 요약

| 케이스 | 수치 확보 수준 | 주요 확보 데이터 | 미확보 데이터 |
|--------|-------------|----------------|-------------|
| CASE 3 (인스타 CTR) | **상세** | 전체 상관계수 표, 샘플 사이즈 | - |
| CASE 4a (I vs We) | **상세** | 만족도 19%, 구매의도 15%, 매출 0.8%/7%, 샘플 1,277건 | 개별 스터디별 효과 크기 (Cohen's d) |
| CASE 4b (You 효과) | **중간** | 자기참조 매개효과, 집단주의 조절효과 | 정확한 평균 차이, F값, eta-squared |
| CASE 4c (SNS 대명사) | **중간** | 15,788개, 대명사별 효과 방향 | IRR 구체적 수치 |
| CASE 6 (럭셔리) | **중간** | 29,000건, 9개 브랜드, 정성적 패턴 | Table 4 구체적 LIWC 점수 |
| CASE 8 (FB 감성) | **기본** | 850건, 83개 페이지, 정성적 비교 | 정확도 %, F1 점수 |
| CASE 9 (인플루언서) | **상세** | 20,923개, 5.4%/8.4%, 1.8%, 매개효과 | - |
| CASE 11 (콜센터) | **상세** | 23,958건, 대화 단계별 효과, 사전 구조 | 베타 계수 구체값 |
| K-LIWC 기만 리뷰 | **중간** | 유의미 변인 전체 목록 | 분류 정확도 % |
| K-LIWC 광고효과 | **중간** | 384명, 유의미 변인 목록 | 상관계수 r 값 |

> **주의:** 일부 데이터는 저널의 접근 제한(paywall)으로 인해 논문 초록과 2차 소스에서 수집되었습니다. 별표(*)가 없는 수치는 논문 원문 또는 공신력 있는 2차 소스에서 직접 확인된 것입니다.

---

## 참고 자료

### 기본 참고 자료
- [Function word - Wikipedia](https://en.wikipedia.org/wiki/Function_word)
- [내용어와 기능어, 실질형태소와 형식형태소 - Brunch](https://brunch.co.kr/@saokim/46)
- [기능어와 내용어 - VOA 한국어](https://www.voakorea.com/a/6869409.html)
- [The Secret Life of Pronouns - Pennebaker](https://www.secretlifeofpronouns.com/)
- [The Psychological Functions of Function Words - ResearchGate](https://www.researchgate.net/publication/237378690)
- [LIWC-22 공식 사이트](https://www.liwc.app/)
- [LIWC and Computerized Text Analysis Methods - Tausczik & Pennebaker (2010)](https://www.cs.cmu.edu/~ylataus/files/TausczikPennebaker2010.pdf)
- [K-LIWC 개발과 검증 - 기초학문자료센터](https://www.krm.or.kr/krmts/search/detailview/research.html?dbGubun=SD&m201_id=10007382)
- [Beyond content: discriminatory power of function words - Oxford Academic](https://academic.oup.com/dsh/article/39/2/765/7634746)

### 소비자 리뷰 분석
- [Linguistic Features for Detecting Fake Reviews (NSF)](https://par.nsf.gov/servlets/purl/10282263)
- [What makes deceptive online reviews? - Nature](https://www.nature.com/articles/s41599-023-02295-5)
- [LIWC categories associated with fake reviews - ResearchGate](https://www.researchgate.net/figure/LIWC-categories-associated-with-fake-reviews_tbl2_343502585)
- [Linguistic Style and Online Review Helpfulness](https://livrepository.liverpool.ac.uk/3014449/1/Wang%20and%20Karimi%20ICIS.pdf)
- [Predicting Helpfulness of Online Customer Reviews - MDPI](https://www.mdpi.com/2071-1050/10/6/1735)

### 광고/브랜드 메시지 최적화
- [Analysis of Psychographic Indicators via LIWC and CTR for Instagram Ads - arXiv](https://arxiv.org/abs/2312.08235)
- [(I'm) Happy to Help (You): Pronoun Use in Customer-Firm Interactions - JMR](https://journals.sagepub.com/doi/10.1509/jmr.16.0118)
- [Second Person Pronouns Enhance Consumer Involvement - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1094996817300348)
- [Pronoun Choices and Consumer Engagement on Social Media - Psychology & Marketing](https://onlinelibrary.wiley.com/doi/10.1002/mar.21341)
- [Subjective or objective: Text Style in Computational Advertising - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11630691/)

### 브랜드 포지셔닝/이미지
- [Luxury is what you say: Luxury eWOM analysis - Psychology & Marketing](https://onlinelibrary.wiley.com/doi/full/10.1002/mar.21831)
- [Mining online consumer reviews for brand image - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0969698922000820)
- [Consumer insights from text analysis - JCP](https://myscp.onlinelibrary.wiley.com/doi/full/10.1002/jcpy.1383)
- [Wisdom from words: marketing insights from text - Wharton](https://faculty.wharton.upenn.edu/wp-content/uploads/2016/11/Text-Review-Marketing-Letters.pdf)

### 소셜미디어/인플루언서
- [The Rivalry Reference Effect - JMR](https://journals.sagepub.com/doi/10.1177/00222437241248414)
- [Less is more: Engagement with social media influencers - ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0148296324002509)
- [Influencer Marketing on Instagram - Taylor & Francis](https://www.tandfonline.com/doi/full/10.1080/15252019.2022.2123724)

### 고객 서비스/VOC
- [How Concrete Language Shapes Customer Satisfaction - JCR](https://academic.oup.com/jcr/article/47/5/787/5873524)
- [Emotions and Communication Style in Call Centers - ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0148296325000153)
- [LIWC Sentiment Analysis Explained - Insight7](https://insight7.io/liwc-sentiment-analysis-explained-clearly/)

### 설문/인터뷰 분석
- [Multiple analytic methods for qualitative data - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12710751/)
- [LIWC In Practice - UBC](https://hecc.ubc.ca/quantitative-textual-analysis/qta-practice/liwcinpractice/)
- [Using LIWC Software to Analyze - APA](https://www.apa.org/pubs/journals/features/gdn-gdn0000195.pdf)

### 한국 마케팅 연구
- [한국어 언어분석 프로그램(KLIWC)을 이용한 온라인 기만 사용후기 연구 - KCI](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002088779)
- [언어분석을 이용한 광고효과 탐색연구: KLIWC를 중심으로 - earticle](https://www.earticle.net/Article/A362538)
- [사고발성법과 언어분석을 활용한 TV 홈쇼핑 광고 효과측정 - KCI](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002508807)
- [K-LIWC 프로그램 개발 과정 고찰 - DBpia](https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE00986198)
- [Your Use of Pronouns Reveals Your Personality - HBR](https://hbr.org/2011/12/your-use-of-pronouns-reveals-your-personality)
- [Lying Words - Newman et al. (2003)](https://journals.sagepub.com/doi/abs/10.1177/0146167203029005010)
- [Receptiviti LIWC API](https://docs.receptiviti.com/frameworks/liwc)

### 심화 리서치 추가 소스 (Section 8)
- [Inoue & Yoshida 2023 - arXiv 전문](https://arxiv.org/html/2312.08235)
- [Packard et al. 2018 - SFU PDF](https://summit.sfu.ca/_flysystem/fedora/sfu_migrate/17767/jmr.16.0118.pdf)
- [Packard et al. 2018 - ScienceSays 요약](https://app.sciencesays.com/p/say-i-not-we-to-customers)
- [Cascio Rizzo et al. 2024 - AMA 해설](https://www.ama.org/2024/01/16/amazing-great-superb-how-influencers-high-arousal-language-can-boost-or-hurt-engagement/)
- [Cascio Rizzo et al. 2024 - Journal of Marketing](https://journals.sagepub.com/doi/10.1177/00222429231207636)
- [Packard, Li & Berger 2024 - JCR](https://academic.oup.com/jcr/article/51/3/634/7491599)
- [Oc et al. 2023 - USD Digital](https://digital.sandiego.edu/busnfaculty/20/)
- [KLIWC 광고효과 연구 - Korea Science](http://koreascience.or.kr/article/JAKO201928862524294.page)
