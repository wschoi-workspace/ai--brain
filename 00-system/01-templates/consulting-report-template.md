# 컨설팅 레포트 표준 템플릿

> **포맷 분석 기반**: McKinsey · Bain · BCG · Deloitte · Doblin
> **역할**: 클라이언트 제출용 컨설팅 리포트의 **전체 아키텍처(매크로 구조)** 표준
> **마이크로 구조**(피라미드·SCQA·So What/Now What·1페이지 작성법)는 → [`executive-report-framework.md`](./executive-report-framework.md) 참조

---

## 0. 사용 가이드 — 3개 문서의 역할 분담

이 템플릿은 단독으로 쓰지 않는다. 워크스페이스의 기존 자산과 **역할이 다르게** 맞물린다.

| 문서 | 담당 층위 | 무엇을 정의하나 |
|------|----------|----------------|
| **consulting-report-template.md** (이 문서) | **매크로** | 리포트 전체 섹션 시퀀스, 펌별 포맷 차이, Doblin 진단 모듈 |
| [`executive-report-framework.md`](./executive-report-framework.md) | **마이크로** | 한 장/한 페이지 단위: 피라미드 원칙, SCQA, So What/Now What, 액션 타이틀, 1p Exec Summary |
| [`presentation-narrative-guide.md`](../04-design/presentation-narrative-guide.md) | **서사** | 감정 곡선, 10단계 설득 공식 (B2C 감성 PT가 필요할 때) |
| [`project-rent-design-guide.md`](../04-design/project-rent-design-guide.md) | **비주얼** | 색·타이포·그리드 토큰 (HTML/슬라이드 구현 시) |

> **순서**: 분석 종료 → ① 이 템플릿으로 리포트 골격 잡기 → ② 각 슬라이드는 `executive-report-framework`로 액션타이틀화 → ③ 제출 PT면 `project-rent-design-guide`로 HTML 구현.

---

## 1. 일류 펌의 공통 골격 (MBB Standard)

McKinsey·Bain·BCG가 공유하는 4대 원칙. 펌이 달라도 이 뼈대는 같다.

```
1. Answer First (결론 먼저)
   - 덱의 첫 장 = Executive Summary = 답(governing thought)
   - CEO가 1장만 봐도 권고안 전체를 이해해야 한다
   - 근거: Minto Pyramid Principle (1987)

2. SCQA 오프닝 (Situation → Complication → Question → Answer)
   - 모든 MBB 덱의 대화 프레이밍 표준

3. Action Title (액션 타이틀)
   - 슬라이드 제목 = 그 장의 결론 한 문장
   - "2월 매출 현황"(X) → "2월 전채널 2.4억, MoM 47% 성장"(O)
   - 제목만 읽어도 스토리라인이 흐른다

4. MECE 근거
   - Mutually Exclusive, Collectively Exhaustive
   - 중복 없이, 누락 없이 (근거: Rasiel, The McKinsey Way, 1999)
```

> 상세 작성법은 [`executive-report-framework.md`](./executive-report-framework.md)에 있다. 여기서는 **이것들을 리포트 전체에 어떻게 배치하는가**(아래 2장)를 다룬다.

---

## 2. 컨설팅 리포트 표준 아키텍처

제출용 풀 리포트의 섹션 시퀀스. Deloitte의 Findings→Analysis→Recommendations 풀 구조에
MBB의 Answer-First와 So What/Now What을 결합한 형태.

```
① Cover
② Executive Summary   ← 답(answer). 이 한 장이 리포트 전체의 축약
③ Context / Objective ← SCQA의 S·C·Q (왜 이 프로젝트인가)
④ Approach / Methodology ← 어떻게 분석했나 (신뢰 확보)
⑤ Findings            ← 현황 진단 (Data)
⑥ Analysis            ← So What (인사이트)
⑦ Recommendations     ← Now What (우선순위 있는 권고)
⑧ Implementation Roadmap ← 누가·언제·무엇을 (간트)
⑨ Expected Impact     ← 정량 효과 (Before→After)
⑩ Appendix            ← 데이터·방법론 상세
```

### 섹션별 설계 가이드

| # | 섹션 | 목적(1줄) | 포함 요소 | 분량 | 안티패턴 |
|---|------|----------|-----------|------|----------|
| ① | Cover | 누구에게/무엇을/언제 | 프로젝트명, 클라이언트, 일자, 작성처(by Project Rent) | 1p | 부제 없는 밋밋한 제목 |
| ② | **Executive Summary** | 1장으로 끝내는 답 | 액션 타이틀 + 핵심숫자 3 + So What 3 + Now What 3 + 임팩트 차트 1 | 1p | "분석한 결과…"로 시작 |
| ③ | Context / Objective | 왜 지금 이 일인가 | SCQA(S·C·Q), 프로젝트 범위·제약 | 1~2p | 클라이언트가 다 아는 회사 소개 나열 |
| ④ | Approach / Methodology | 결론을 믿게 만들기 | 분석 프레임, 데이터 출처, 기간, 표본 | 1p | 방법론 없이 주장만 |
| ⑤ | Findings | 무엇을 발견했나 | 현황 데이터, 진단, 벤치마크 | 3~6p | So What 없는 데이터 덤프 |
| ⑥ | Analysis | 그래서 무슨 의미인가 | 인사이트(이슈 트리·MECE), 근본 원인 | 3~6p | Findings 재서술 |
| ⑦ | **Recommendations** | 그래서 무엇을 하나 | 우선순위 있는 액션, 근거-권고 연결 | 2~4p | 우선순위 없는 To-do 나열 |
| ⑧ | Roadmap | 누가·언제 실행 | 간트, 마일스톤, Quick Win vs 중장기 | 1~2p | 책임자·기한 누락 |
| ⑨ | Expected Impact | 효과의 크기 | 정량 추정, Before→After, 가정 명시 | 1p | 근거 없는 장밋빛 수치 |
| ⑩ | Appendix | 깊이 검증용 | 원자료, 상세 모델, 인터뷰 로그 | n | 본문에 있어야 할 핵심을 부록에 숨김 |

> 각 챕터(⑤⑥⑦)는 MBB 규칙대로 **하나의 주장을 증명하는 5~8장**으로 구성하고, 챕터 첫 장에 그 챕터의 governing thought를 둔다.

---

## 3. MBB 슬라이드 문법 — 제출 직전 점검

리포트 안의 개별 장을 펌 수준으로 끌어올리는 4가지.

### 3-1. Ghost Deck 먼저 (스토리라인 우선)
콘텐츠를 채우기 전에 **모든 슬라이드의 액션 타이틀만** 먼저 쓴다.
제목들을 위에서 아래로 읽었을 때 그 자체로 완결된 논증이면 통과.
→ 디자인·차트는 그 다음. (스토리가 먼저, 픽셀은 나중)

### 3-2. 1 메시지 / 1 슬라이드
한 장에 결론은 하나. 차트가 두 개여도 메시지는 하나로 수렴해야 한다.

### 3-3. Governing Thought
챕터·리포트의 최상위 주장. Exec Summary의 제목이자 피라미드 꼭대기.
모든 하위 근거는 이 한 문장을 떠받친다.

### 3-4. MECE 이슈 트리 (Issue Tree)
문제를 중복·누락 없이 분해하는 도해. Analysis(⑥)의 뼈대.

```
                    [핵심 질문]
                         │
        ┌────────────────┼────────────────┐
     [이슈 A]         [이슈 B]         [이슈 C]    ← MECE
        │                │                │
    하위이슈          하위이슈          하위이슈
```

---

## 4. 펌별 포맷 비교 — 어디서 무엇을 취하나

| 펌 | 철학 | 비주얼 성향 | 시그니처 폰트 | 차용 포인트 |
|----|------|------------|--------------|-------------|
| **McKinsey** | 논리의 엄밀함 (Pyramid의 본가) | 텍스트 밀도 높음, 액션타이틀 정교 | Garamond (serif 본문) | 액션 타이틀 + 피라미드 논증 |
| **BCG** | "Smart Simplicity" | 비주얼·데이터 중심, 간결 | Univers / Frutiger (sans) | 복잡함을 한 장에 단순화하는 도식화 |
| **Bain** | 결과·실행 지향 | 현대적·실용적, answer first 동일 | Helvetica Neue (sans) | 권고-임팩트의 직접 연결 |
| **Deloitte** | 브랜드 일관성·풀 프로세스 | 템플릿 엄격, 간트·히트맵·프로세스플로우 | 브랜드 표준 | Findings→Analysis→Recommendations 풀 구조 |
| **Doblin** (Deloitte) | 혁신 진단 | Ten Types 진단 매트릭스 | — | 혁신 유형 진단 모듈(5장) |

> **우리 리포트 결론**: 구조는 **McKinsey 액션타이틀 + Deloitte 풀 시퀀스**, 비주얼은 **BCG식 단순화**를
> [`project-rent-design-guide.md`](../04-design/project-rent-design-guide.md)의 다크테마로 구현한다.
> 혁신·브랜드 진단이 필요하면 **Doblin 모듈**(아래 5장)을 ⑥ Analysis에 끼운다.

---

## 5. Doblin Ten Types 진단 모듈 (선택)

**출처**: Larry Keeley, Ryan Pikkel, Brian Quinn, Helen Walters (2013).
*Ten Types of Innovation: The Discipline of Building Breakthroughs*. Wiley.
Doblin(1981 설립, 현 Deloitte 산하)이 2,000+ 성공 혁신 사례 분석으로 도출.

**핵심 통찰**: 지속적 우위는 제품 성능 하나가 아니라 **여러 유형의 조합**에서 나온다.
특히 Configuration·Experience 영역(제품이 아닌 곳)의 혁신이 모방하기 어렵다.

### 3 클러스터 × 10 유형

| 클러스터 | # | 유형 | 정의 |
|----------|---|------|------|
| **Configuration**<br>(어떻게 구성하나) | 1 | Profit Model | 어떻게 돈을 버나 — 수익 구조 혁신 |
| | 2 | Network | 외부와 어떻게 연결·협업하나 |
| | 3 | Structure | 인재·자산을 어떻게 조직하나 |
| | 4 | Process | 어떻게 일하나 — 운영·방법 혁신 |
| **Offering**<br>(무엇을 제공하나) | 5 | Product Performance | 제품 자체의 성능·기능 |
| | 6 | Product System | 제품·서비스를 어떻게 묶나 |
| **Experience**<br>(어떻게 전달하나) | 7 | Service | 제품의 가치를 어떻게 받쳐주나 |
| | 8 | Channel | 어떻게 고객에게 닿나 |
| | 9 | Brand | 어떻게 인식·신뢰를 만드나 |
| | 10 | Customer Engagement | 어떻게 의미 있는 관계를 만드나 |

### 진단 사용법
1. 클라이언트의 현재 혁신이 **어느 유형에 쏠려 있나** 매핑 (대개 5번 Product Performance에 편중)
2. **공백 유형** 식별 — 경쟁사가 손대지 않은 영역이 차별화 기회
3. **유형 조합** 설계 — "Profit Model + Channel + Brand" 식 다중 조합으로 모방 난이도 ↑
4. Analysis(⑥)에 진단 매트릭스로, Recommendations(⑦)에 조합 제안으로 연결

> **브랜드·공간기획 적용**: 공간 프로젝트는 7(Service)·8(Channel)·9(Brand)·10(Engagement)에서
> 차별화가 갈린다. 대부분의 경쟁이 5(Product=공간 그 자체)에만 매달릴 때 경험 클러스터를 설계한다.

---

## 6. 본인 업무 적용 노트 (브랜드 · 공간 · AX 컨설팅)

범용 표준은 유지하되, 최원석 업무 도메인에서 각 섹션을 채우는 힌트.

| 섹션 | 브랜드 컨설팅 | 공간기획 | AX 교육·컨설팅 |
|------|--------------|----------|----------------|
| ⑤ Findings | RXR 멘션 감성·진정성 데이터 | 입지·동선·경쟁 매장 진단 | 현 업무 프로세스·툴 사용 실태 |
| ⑥ Analysis | 포지셔닝 맵 + Doblin 9·10 진단 | Doblin 7·8·10 경험 갭 | 자동화 가능 업무 MECE 분해 |
| ⑦ Recommendations | A/B/C 브랜드 방향 | MD·운영·경험 설계안 | AX 전환 로드맵·우선순위 |
| ⑨ Impact | 인식 전환·멘션 지표 | 객단가·체류·재방문 추정 | 업무시간 절감·품질 향상 추정 |

> 브랜드 프로젝트는 [`brand-simulation-framework.md`](./brand-simulation-framework.md)의 욕망·수익 병렬 시뮬레이션과
> 함께 쓰면 ⑥⑦이 강해진다.

---

## 7. 체크리스트 & 프롬프트

### 제출 전 체크리스트
```
구조
- [ ] Exec Summary 1장만 봐도 권고 전체가 이해되나? (Answer First)
- [ ] 각 챕터가 하나의 governing thought를 증명하나?
- [ ] 슬라이드 제목들만 읽어도 논증이 흐르나? (Ghost Deck 테스트)

내용
- [ ] 모든 Findings에 So What이 붙었나?
- [ ] 모든 Recommendation이 우선순위 + 담당 + 기한을 가졌나?
- [ ] Impact 추정의 가정이 명시됐나?
- [ ] 이슈 트리가 MECE한가?

검증 (CLAUDE.md 3중 체크)
- [ ] 모든 수치·인용·출처를 추출 → 신뢰 출처로 크로스체크 → 재대조했나?
```

### 프롬프트 템플릿
```
"지금까지 분석한 내용을 @consulting-report-template.md 의 표준 아키텍처(①~⑩)로 정리해줘.
- Exec Summary는 Answer First로 (핵심숫자 3 + So What 3 + Now What 3)
- 각 챕터는 governing thought 1개를 5~8장으로 증명
- 슬라이드 제목은 전부 액션 타이틀로 (제목만 읽어도 논증이 흐르게)
- [필요시] ⑥ Analysis에 Doblin Ten Types 진단 매트릭스 삽입
- 제출용 HTML은 project-rent 다크테마로"
```

---

## 8. 출처

- Minto, B. (1987). *The Pyramid Principle: Logic in Writing and Thinking*. Pearson.
- Rasiel, E. (1999). *The McKinsey Way*. McGraw-Hill. (MECE)
- Zelazny, G. (2001). *Say It with Charts*. McGraw-Hill. (액션 타이틀)
- Keeley, L., Pikkel, R., Quinn, B., & Walters, H. (2013). *Ten Types of Innovation: The Discipline of Building Breakthroughs*. Wiley. (Doblin)
- 펌별 포맷 분석 (2026-06 웹 리서치):
  - McKinsey/MBB 슬라이드 구조: slidemodel.com/mckinsey-presentation-structure, deckary.com/blog/pillar-consulting-presentations-guide
  - BCG "Smart Simplicity" / 폰트: deckary.com/blog/bcg-presentation-style
  - Deloitte 구조: slidemodel.com/deloitte-presentation-structure
  - Doblin Ten Types: doblin.com/ten-types, deloittedigital.com/us/en/accelerators/ten-types.html

---

*by Project Rent · 컨설팅 리포트 표준 v1*
