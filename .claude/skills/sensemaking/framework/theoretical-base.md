# Theoretical Base: AI Collaborative Interpretation

> SKILL.md에서 progressive disclosure로 참조하는 이론 요약.
> 상세: PKM `34.06-ai-collaborative-interpretation/` 4개 문서.

## 4-Layer + Metacognition 구조

```
              Metacognition (세로축)
              "내가 뭘 알고 뭘 모르는지"
                    |
=== Layer 4: Integration (통합) ===
  Schema Theory + Desirable Difficulty
                    |
=== Layer 3: Support (지원) ===
  ZPD + Scaffolding + Fading
                    |
=== Layer 2: Interpretation (해석) ===  <-- 핵심 영역
  Hermeneutic Circle + Sensemaking
                    |
=== Layer 1: Motivation (동기) ===
  Self-Determination Theory (Autonomy + Competence + Relatedness)
```

---

## Layer 1: Motivation - Self-Determination Theory

Deci & Ryan의 내적 동기 3요소. "관여도"의 정체.

| 요소 | 역할 | Skill에서의 적용 |
|------|------|-----------------|
| Autonomy | 내가 선택해서 파는 것 | 강제하지 않음, 흥미에서 시작 |
| Competence | 이해되니까 더 하고 싶다 | 용어 해소 -> 유능감 -> 심화 |
| Relatedness | 내 일/삶과 연결 | "네 프로젝트에서 이건..." |

Phase 전환 스위치: Relatedness가 낮으면 Phase 1에서 종료 (이것도 성공).

---

## Layer 2: Interpretation - Sensemaking + Hermeneutic Circle

### Sensemaking (Karl Weick, 1995)

> "정답을 찾는 게 아니라, 행동할 수 있을 만큼의 그럴듯한 이해를 만드는 것"

핵심 3속성:
- **Grounded in identity**: "내가 누구냐"가 해석을 결정
- **Focused on extracted cues**: 전부가 아닌 핵심 단서에 집중
- **Driven by plausibility**: 정확성보다 행동 가능성

### Hermeneutic Circle

텍스트 이해는 선형이 아니라 순환적:
- 부분(용어) <-> 전체(맥락) 반복 순환으로 깊어짐
- 선이해(기존 지식)가 새로운 해석의 출발점
- 지평의 융합(Gadamer): 내 관점 + 텍스트 관점 = 새로운 이해

**진입점 = 용어**. 모든 세션은 용어 해소에서 시작.

---

## Layer 3: Support - ZPD + Scaffolding + Fading

### ZPD (Vygotsky, 1930s)

```
[혼자 가능]  <-->  [도움받으면 가능 = ZPD]  <-->  [아직 불가능]
```

AI가 MKO(More Knowledgeable Other) 역할 수행.

### Scaffolding 3특성

1. **Contingency**: 사용자 현재 수준에 맞게 지원 조정
2. **Fading**: 역량 성장하면 지원 줄임
3. **Transfer of Responsibility**: 독립적 문제해결로 이전

### Cognitive Offloading vs. Augmentation

| Offloading (인지 외주화) | Augmentation (인지 증강) |
|---|---|
| "AI가 알아서 해" | "AI와 함께 이해하기" |
| 뇌가 약해짐 | 뇌가 강해짐 |
| 저장만 하고 방치 | 해석하고 내 것으로 |

이 Skill은 Augmentation을 지향.

---

## Layer 4: Integration - Schema Theory + Desirable Difficulty

### Schema Theory

기존 지식 구조(schema)에 새 정보를 연결. AI가 "다리" 역할:

```
[사용자의 기존 스키마] <--AI가 비유로 연결--> [새로운 정보]
```

### Desirable Difficulty (Bjork, 1994)

같이 해석하는 "노력"은 버그가 아니라 피처:
- 너무 쉬움(단순 요약) -> 내 것이 안 됨
- 적절히 어려움(같이 해석) -> 진짜 이해
- 너무 어려움(혼자 방치) -> 포기

---

## 세로축: Metacognition + Auto-Context

### 핵심 문제

이해도 과대평가 편향: 실제 이해 30% vs 체감 이해 70%
-> "대충 알겠네" 착각 -> 더 파지 않음 -> AI 활용 불가

### Auto-Context Tiers (노력 최소화 설계)

```
Tier 1 (노력: 제로): CLAUDE.md -> 사용자 도메인/수준/도구 자동 파악
Tier 2 (노력: 제로): 콘텐츠 분석 -> 도메인/난이도/핵심 용어 추출
Tier 3 (노력: 제로): 갭 분석 -> Tier1 vs Tier2 = 예상 막힘 지점
Tier 4 (노력: 낮음): "모르는 용어 있어?" -> 해결 안 된 것만 질문
```

### 노력 비용 원칙

높은 노력의 메타인지는 사용되지 않음:
- 역설명 요청 -> 불채택 (주관식 회피)
- 이해도 자가 평가 -> 불채택 (기준점 없음)
- 갭 탐지 질문 ("모르는 용어?") -> **채택** (대충이라도 답 가능)
- 자동 맥락 (CLAUDE.md) -> **채택** (노력 제로)

---

## Phase Model

```
Phase 0: "이게 뭔지도 모르겠어"     -> ZPD 바깥, 진입 장벽
Phase 1: "아, 대충 이런 거구나"     -> ZPD 진입, 탈신비화
Phase 2: "내 상황에선 어떻게 되지?" -> ZPD 안에서 탐색
Phase 3: "한번 써볼까"             -> 독립으로 이동
```

전환: 0->1 용어 해소 | 1->2 Relatedness 발견 | 2->3 Competence+Autonomy 축적

---

## 10가지 설계 원칙

1. 진입 장벽을 극도로 낮춰라 (Phase 0->1이 가장 높은 벽)
2. 관여도(Relatedness)를 일찍 표면화하라
3. 부분 <-> 전체 순환을 지원하라 (Hermeneutic Circle)
4. 정체성 기반 해석 (Sensemaking)
5. 적절한 어려움을 유지하라 (Desirable Difficulty)
6. 아웃풋을 강제하지 마라 (SDT가 결정)
7. Fading을 자연스럽게
8. 메타인지 노력을 최소화하라 (Auto-Context Tiers)
9. 용어에서 시작하라 (Hermeneutic Circle 진입점)
10. 환경 파일을 적극 활용하라 (CLAUDE.md = 자동 메타인지)

---

## 원본 문서

| 문서 | 내용 |
|------|------|
| `00-unified-framework.md` | 통합 프레임워크, Phase Model, 설계 원칙 |
| `01-zpd-scaffolding.md` | ZPD, MKO, Scaffolding, Fading, Offloading vs Augmentation |
| `02-sensemaking-hermeneutics.md` | Sensemaking, Hermeneutic Circle, SDT, Schema, Desirable Difficulty |
| `03-metacognition.md` | Metacognition, Cognitive Mirror, Auto-Context Tiers, 노력 비용 |
