# ARISA 2.0 — 정의와 설계

> **ARISA는 업무보고 시스템이 아니다. 조직의 사고를 운영하는 시스템이다.**
>
> *Adaptive Resolution & Insight System Assistant*
> *Cognitive Operations System for Project Rent*
>
> 최종 정리: 2026-06-13 · by Project Rent

---

## 이 문서를 읽는 개발자에게

ARISA를 **"보고 정리 시스템"으로 이해하는 순간 설계는 실패한다.** ARISA는 조직 구성원의
사고를 번역·구조화하여 **스스로 자신의 사고를 보게 만드는 Cognitive Reflection System**이다.
보고는 목적이 아니라 인터페이스다. 직원은 보고를 통해 자신의 생각을 정리하고, 대표는 보고를
통해 조직의 상태를 읽는다. ARISA는 그 둘을 연결하는 **사고 번역 엔진**이다.

이 문서는 흩어져 있던 아이데이션·설계·구현을 하나로 수렴한 **단일 기준(Single Source of
Truth)** 이다. 모든 기술 결정은 아래 철학을 먼저 내면화한 뒤 내린다.

---

## 목차

- Part 0. 프로젝트 정체
- Part 1. 철학 (개발 불변 원칙)
- Part 2. 해결하려는 문제
- Part 3. 시스템 구조 — 5개 엔진
- Part 4. 사용자 구조 — 2개 모드
- Part 5. 시간축 — 3개 레이어
- Part 6. 산출물 카탈로그
- Part 7. 아키텍처
- Part 8. 데이터 구조
- Part 9. MVP 로드맵
- Part 10. 현재 구현 현황
- Part 11. ARISA 3.0 비전
- 부록 A. 기존 ARISA 사고프레임 계승
- 부록 B. 용어집

---

## Part 0. 프로젝트 정체

| 항목 | 내용 |
|------|------|
| 명칭 | **ARISA 2.0** — Adaptive Resolution & Insight System Assistant |
| 분류 | Cognitive Operations System (조직 사고 운영 시스템) |
| 한 줄 정의 | Daily·Weekly·Monthly **세 개의 시간축**으로 직원의 사고를 구조화하고, 대표의 의사결정을 지원하며, 조직의 학습을 축적하는 시스템 |
| 핵심 명제 | "보고는 목적이 아니라 **인터페이스**다." |
| 구성 결합 | Reporting System + Decision Support System + Organizational Growth System |
| 연결 개념 | **사고 해상도(Thinking Resolution)** — 같은 사실을 얼마나 또렷하게 보는가 |

ARISA는 세 시스템이 하나로 결합된 것이며, 이 셋을 잇는 축이 "사고 해상도"다. 흐릿한 보고를
또렷한 사고로 끌어올리는 것이 ARISA가 하는 일이다.

---

## Part 1. 철학 (개발 불변 원칙)

이 원칙들은 기능보다 우선한다. 기능이 원칙과 충돌하면 기능을 버린다.

1. **성장 코치가 아니라 사고의 거울이다.**
   직원을 *교정*하지 않고 *가시화*한다. 직원이 "아, 내가 이런 얘길 하고 있었구나"를
   깨닫게 하는 것이 1차 목적. 성장은 강요가 아니라 거울 앞에서 스스로 일어난다.

2. **처리 순서는 `Report → Interpretation → Reflection → Coaching`.**
   성장은 출발점이 아니라 결과물이다. 처음부터 코치가 되면 "또 질문해? 또 성장하래?"라는
   피로를 부른다. 질문 폭탄은 금지.

3. **3계층 비중: Mirror 80 / Reflector 15 / Coach 5.**
   - **Layer 1 Mirror (80%)** — 직원의 생각을 번역·구조화한다.
   - **Layer 2 Reflector (15%)** — 생각하게 만드는 질문 1~2개.
   - **Layer 3 Coach (5%)** — 직원이 원할 때만 깊은 코칭.

4. **업무량이 아니라 Output·Outcome을 추적한다.**
   "얼마나 오래 일했는가"가 아니라 "무엇을 생산했고(Output), 무엇이 달라졌으며(Outcome),
   어떤 의사결정을 가능하게 했는가"를 기록한다.

5. **목표 순서: 좋은 보고(1차) → 좋은 의사결정(2차) → 좋은 성장(3차).**

6. **진짜 자산은 화면이 아니라 직원별 Thinking Data Log다.**
   완성형 SaaS·대시보드를 먼저 만들지 않는다. 데이터가 쌓이는 구조부터 만든다.

---

## Part 2. 해결하려는 문제 (현재 보고의 5대 결함)

대부분의 직원 보고는 "업무 나열"에 머문다. 다음이 빠져 있다.

| # | 결함 | 증상 | 예시 |
|---|------|------|------|
| 1 | **나열 중심** | 왜 했는지가 없다 | "경쟁사 조사 완료 / 회의 참석 / 자료 정리" |
| 2 | **Output 없음** | 무엇을 생산했는지 모른다 | "경쟁사 조사함" → 분류표·가설이 없다 |
| 3 | **Outcome 없음** | 그래서 무엇이 달라졌나 | "자료를 조사함" → 변화를 설명 못 한다 |
| 4 | **Decision 없음** | 대표가 뭘 결정해야 하나 | 보고에서 의사결정 포인트가 안 보인다 |
| 5 | **성장 미축적** | 무엇이 늘고 무엇이 반복 부족한지 | 직원 성장이 기록되지 않는다 |

ARISA 2.0은 이 다섯 결함을 보고 인터페이스 단계에서 메운다.

---

## Part 3. 시스템 구조 — 5개 엔진

```
직원 입력
  → A. Input Parser
  → B. Report Completion  (부족하면 질문)
  → C. Report Structuring (7섹션)
  → D. Decision Engine    (대표용)
  → E. Growth Engine      (직원 성장)
```

### Engine A — Input Parser
누가 보냈는지 식별(직원/대표), 프로젝트명 추출, 보고 유형 분류.
- 보고 유형: `daily_report` / `meeting_note` / `research_report` / `decision_request` /
  `support_request` / `weekly_update`

### Engine B — Report Completion (가장 중요)
보고가 "좋은 보고"인지 7기준으로 검사하고, **부족한 부분만** 질문한다.
- 7기준: Task / Output / Outcome / Decision Needed / Support Needed / Blocker / Next
- 질문 상한: **Daily ≤ 3, Weekly ≤ 5, Monthly ≤ 7** (피로 최소화)
- 충분하면 질문 0개로 즉시 통과. 코칭·평가·지적 금지, 사고를 비추는 질문만.

### Engine C — Report Structuring
보완 답변까지 반영해 최종 7섹션 보고를 생성한다.
1. **Task** — 오늘 한 일
2. **Output** — 생산한 결과물
3. **Outcome** — 그 결과물이 만든 변화·의미
4. **Decision Needed** — 대표·팀장이 결정할 것
5. **Support Needed** — 필요한 지원
6. **Next Action** — 다음 액션
7. **ARISA Reflection** — 잘된 점 / 부족한 점 / 다음 보완점 (평가가 아닌 관찰)

### Engine D — Decision Engine (대표용)
대표가 무엇을 결정해야 하는지 추출·정렬한다.
```json
{ "project": "넵킨", "decision_type": "positioning",
  "decision_needed": "넵킨 SNS를 정보형/캐릭터형 중 무엇으로 갈지",
  "urgency": "high", "owner": "최원석",
  "source_employee": "정예인", "related_output": "경쟁사 SNS 분석" }
```

### Engine E — Growth Engine (직원 성장)
직원의 사고 성장 데이터를 6지표로 축적한다.
```json
{ "employee": "정예인", "date": "2026-06-13", "project": "넵킨",
  "clarity": 3, "evidence": 2, "structure": 3,
  "output_quality": 3, "outcome_quality": 2, "decision_thinking": 2,
  "growth_note": "정보 수집은 했으나 의미·의사결정 연결이 약함" }
```

---

## Part 4. 사용자 구조 — 2개 모드

| | Employee Mode | Executive Mode |
|---|---|---|
| 목표 | 좋은 보고 · 좋은 사고 | 좋은 판단 · 좋은 개입 |
| 채널 | Telegram | (MVP) Markdown → (이후) 대시보드 |
| 기능 | 일일보고·회의록·리서치 정리 + 품질 피드백 | Daily Brief / Weekly Review / Monthly Org Intelligence |
| 본질 | 개인 사고 코치 | 조직을 읽는 창 |

대표는 "보고를 보고 싶은 게 아니라 조직을 보고 싶다." Executive Mode의 첫 화면은 업무 목록이
아니라 **"오늘 대표가 봐야 할 것 TOP 5"** (Decision / Intervention / Project / Growth / Risk).

---

## Part 5. 시간축 — 3개 레이어

| 시간축 | 목적 | 직원 산출 | 대표 산출 |
|--------|------|-----------|-----------|
| **Daily** | 좋은 보고·의사결정 | 오늘 보고 피드백 | 오늘 의사결정 요약 |
| **Weekly** (금요일 자동) | 프로젝트·맥락·성장 | 주간 리뷰 + 성장 포인트 | 프로젝트별 리뷰 + 개입 우선순위 |
| **Monthly** | 조직 학습·패턴 | 성장 리포트 | 조직 인텔리전스(패턴·성장·추천 교육) |

한 달이 지나면 ARISA는 업무 기록이 아니라 **조직 성장 데이터베이스**가 된다. Monthly는
대표가 매달 하는 조직 평가를 자동화하는 것.

---

## Part 6. 산출물 카탈로그

### 직원용
- **Daily Report** — Task / Output / Outcome / Decision / Support / Next / Reflection
- **Weekly Review** — 이번 주 프로젝트 / 주요 Output·Outcome / 부족했던 부분 /
  다음 주 집중 과제 / 추천 질문·자료·도서
- **Monthly Growth Report** — 강점 / 반복 약점 / 최근 성장 / 추천 학습 / 다음 성장 과제

### 대표용
- **Daily Executive Brief** — 조직 상태 / Decision Needed / Support Needed / Risk /
  Project Status / Employee Status
- **Weekly Executive Review** — 프로젝트별 진행 / 주요 Outcome / 반복 이슈 / 개입 필요 사항
- **Monthly Organizational Intelligence Report** — 조직 성장 분석 / 프로젝트 패턴 /
  직원 성장 분석 / 추천 교육·도서·코칭

---

## Part 7. 아키텍처

### 파이프라인
```
직원 Telegram 입력
   ↓ Engine A: Input Parser       (누가/프로젝트/보고유형)
   ↓ Engine B: Report Completion  (Output/Outcome/Decision 충분성 → 부족 시 질문)
   ↓ 직원에게 보완 질문 (Daily ≤3 / Weekly ≤5 / Monthly ≤7)
   ↓ Engine C: Report Structuring (7섹션 + Reflection)
   ↓ Thinking Data 저장 (파일 로그 + 구글시트)
   ├─ Engine D: Decision Engine   (대표용 의사결정)
   └─ Engine E: Growth Engine     (직원 성장 6지표)
   ↓
직원 피드백(거울) + 대표 리포트(Daily/Weekly/Monthly)
```

### 입력 채널
- 현재: 텔레그램 텍스트 / 음성 / 첨부파일(드라이브 업로드)
- 후속: 메일(Gmail), 회의록(meeting_note — arisa-project-memory 흡수)
- 다중 입력은 `ingest/` 어댑터로 공통 포맷 정규화 후 큐 투입

### 저장 구조
```
arisa/
├── memory/
│   ├── employees/<직원>/         ← Thinking Data Log (daily 누적, growth_log)
│   ├── projects/<프로젝트>/       ← 결정·전략·진행 (arisa-memory 구조 흡수)
│   ├── decisions/                ← Decision Engine 출력 누적
│   └── organization_patterns/    ← Monthly 패턴 분석
├── outputs/
│   ├── employee/{daily_feedback,weekly_reviews,monthly_growth}/
│   └── executive/{daily_briefs,weekly_reviews,monthly_org_reports}/
├── prompts/                      ← 엔진별 프롬프트
└── config/employees.json         ← 직원 명부 (user_id↔이름/팀/역할/모드)
```
정형 데이터(집계·시트)와 누적 사고(파일 로그)를 **병행**한다. 핵심 자산은 후자.

---

## Part 8. 데이터 구조

- **Thinking Data Log** (직원별, 누적): 일자별 7섹션 보고 + Reflection + Growth 6지표가
  한 직원 폴더에 시간순으로 쌓인다. Weekly·Monthly·3.0 개인화의 원천.
- **Decision Log**: Engine D의 JSON이 프로젝트·긴급도별로 축적 → 대표 Brief의 재료.
- **Growth Log**: Engine E의 JSON이 직원별로 축적 → 성장 곡선·반복 약점 탐지.

> 원칙: 화면을 먼저 만들지 않는다. 위 로그가 쌓이는 구조가 먼저다.

---

## Part 9. MVP 로드맵

| MVP | 내용 | 상태 |
|-----|------|------|
| **MVP1** | 텔레그램 보고 → Completion 질문 → 7섹션 + **직원 회신(거울)** | ✅ 완료 |
| MVP2 | 최종보고 저장 → 직원 Daily Feedback(Reflection) 정식화 | 예정 |
| MVP3 | 여러 직원 취합 → 대표 Daily Executive Brief | 예정 |
| MVP4 | 금요일 Weekly Review 자동 생성(직원/대표) | 예정 |
| MVP5 | 직원별 Growth Log 6지표 누적 | 예정 |
| MVP6 | Monthly Organizational Intelligence Report | 예정 |
| 후속 | 회의록 `meeting_note` 채널 흡수 (arisa-project-memory 포팅) | 예정 |

원칙: **화면보다 데이터 먼저.** MVP1~5는 Markdown/JSON 산출, 대시보드는 데이터가 쌓인 뒤.

---

## Part 10. 현재 구현 현황 (2026-06-13)

ARISA 2.0은 기존 **일일업무보고봇을 진화**시켜 시작했다. (신규 창조 아님)

**MVP1 완료** — `~/do-better-workspace/00-system/02-scripts/daily-report-bot.py`
- **Engine B**: `COMPLETION_CHECK_PROMPT` + `WAITING_COMPLETION` 상태. 부족 시 ≤3개 질문.
- **Engine C**: `STRUCTURE_PROMPT`. 업무별 `outcome` + `decision_needed`/`support_needed`/
  `reflection` 채움. 7섹션.
- **직원 회신(거울)**: `format_report_for_employee()`. 직원 본인에게도 정리본 + Reflection
  회신 → "내 말이 이렇게 정리되는구나" 학습 루프.
- **시트 확장**: 핵심업무 탭 `의미(Outcome)` 12열, 메타 탭 `Decision/Support/Reflection` 추가.

**운영**
- launchd 영구 등록 `com.arisa.daily-report-bot` (RunAtLoad+KeepAlive, 재부팅 자동부활).
  주의: 텔레그램은 토큰당 polling 1개만 허용 — 수동 인스턴스 잔존 시 충돌.
- 구글시트(`1izuwjWPiJfbaJZ...`) 헤더 신규 컬럼 반영 완료.

**후속 미구현(명시)**: Engine D(대표 Brief 분리 저장), Engine E(Growth 6지표 축적),
Weekly/Monthly, 회의록 흡수, Executive 대시보드.

---

## Part 11. ARISA 3.0 — Organizational Learning Operating System

3.0은 보고 시스템이 아니라 **조직의 학습 속도를 측정·가속하는 운영체제**다.
SaaS 진화(1세대 기록 → 2세대 관리 → 3세대 자동화)의 다음, **4세대 = 학습 OS**를 지향한다.

**KPI 전환 — 이것이 3.0의 핵심**
> 업무 완료율 ❌ → **조직의 학습 속도** ✅

어떤 회사도 매출·업무량·출근은 측정하지만, **질문의 수준·사고의 성장·조직 이해도**는 측정하지 못한다. ARISA 3.0이 바로 그것을 측정한다.

**다섯 가지 진화**
1. **질문 기반 조직 (Question Report)** — "오늘 무엇을 했나" → "오늘 발견한 **가장 중요한 질문**은? / 잘못 이해했던 것은? / 생각이 바뀐 것은?"
2. **성장 해상도 측정 (Thinking Resolution)** — 같은 주제를 얼마나 또렷하게 보는가. 사고 해상도·문제 정의 수준·의사결정 수준을 추적. *(개인 학습유형: 사례형 / 질문형 / 실험형 / 독서형)*
3. **Organizational Define Cost 측정 (오해 지도)** — 대표 지시 → 팀장 이해 → 직원 이해의 **차이**를 측정. "이 지시를 어떻게 이해했나요?" → 조직 내 오해가 **어디서** 발생하는지 지도화. 처음으로 조직의 커뮤니케이션 비용을 가시화한다.
4. **집단지성 지도 (조직 사고 맵)** — 회의·보고·기획·고객응대를 수집해 "이번 달 가장 많이 고민한 문제 / 가장 성장한 영역 / 반복 실패한 영역"을 그린다. (Monthly Layer의 확장)
5. **AI 코치** — 강사가 아니라 **코치**. 정답을 주지 않고 `질문 → 실행 → 피드백 → 재정의` 루프로 성장시킨다.

**최종 정의**
> ARISA 3.0 = 조직의 학습 속도를 측정하고, 질문 수준을 향상시키고, 사고 해상도를 높이며, 조직의 **Define Cost를 감소**시키는 **AI 기반 성장 운영체제(Learning OS)**.

진화 경로: **보고 시스템 → 성장 시스템 → 조직 학습 OS.** 최종적으로 조직의 **Collective Intelligence**를 구축한다. 3.0 성공의 전제는 2.0에서 직원이 ARISA를 "감시·교육"이 아니라 "내 말을 정리해주는 AI"로 받아들이는 것 — 그래서 2.0은 거울에 머문다.

> **시장 관점**: ARISA는 업무 툴 시장이 아니라 **"조직 성장 시장"**이라는 새 카테고리를 만든다. CFD·Define Cost는 뒤에 숨은 철학이고, ARISA는 그 철학이 시장에 처음 나타나는 상품이다. (상위 비전·GTM 키노트: `ARISA-상위비전-키노트-LearningOS-원본.txt`)

---

## 부록 A. 기존 ARISA 사고프레임 계승

ARISA 2.0의 정량 엔진(보고·의사결정·성장) 아래에는, 기존 ARISA GPT의 **정성 사고프레임**이
깔려 있다. (`~/arisa-project-memory/prompts/arisa-gpt-system-prompt.md`) Reflection·Decision의
질문 품질은 이 프레임에서 나온다.

- **청취 모드 / 응답 모드** — 호출될 때만 말한다. 2.0의 "질문 폭탄 금지"·Mirror 80% 원칙의 뿌리.
- **Desire Mapping Process (5단계)** — Signal → Scene → Desire → Decision → Evolution.
  Outcome·Decision을 욕망 흐름으로 해석하는 렌즈.
- **Double Layer Structure** — Layer A(욕망/브랜드) × Layer B(수익/비즈니스). 보고의 의미를
  양면으로 읽는다.
- **패턴 감지 시스템** — 자산-정체성 역설 / 아키텍처 갈림길 / 데이터→질문 전환 / 설명 과잉 /
  공간=미디어. Engine B·D가 "어떤 질문을 던질지" 고를 때의 후보 패턴.
- **데이터→질문 전환** 패턴은 2.0의 핵심 동작과 정확히 일치한다: 데이터를 해석으로 닫지 말고
  "강화할 것인가, 재조정할 것인가"의 **선택적 질문**으로 전환한다.

> 2.0은 이 프레임을 "정량 파이프라인"으로 제품화한 것이며, 프레임 자체를 대체하지 않는다.

---

## 부록 B. 용어집

| 용어 | 뜻 |
|------|-----|
| **Output** | 생산한 결과물 (예: 경쟁사 분류표, 설문 구조) |
| **Outcome** | 그 결과물이 만든 변화·의미 (예: 포지셔닝 방향 후보 확보) |
| **Decision Needed** | 대표·팀장이 내려줘야 할 의사결정 |
| **Support Needed** | 직원이 일을 진행하기 위해 필요한 지원 (≠ 막힌 것=Blocker) |
| **Reflection** | 보고 품질에 대한 *관찰*(평가 아님): 잘된 점/부족한 점/다음 보완점 |
| **Thinking Resolution** | 사고 해상도. 같은 사실을 얼마나 또렷하게 보는가 (3.0 핵심 측정축) |
| **Define Cost** | 조직 내 지시·사고가 전달되며 발생하는 오해·재학습 비용. 낮출수록 조직 학습 속도↑ (CFD에서 옴, 시장엔 단어 비노출) |
| **조직 학습 속도** | 3.0의 핵심 KPI. 업무 완료율을 대체하는 측정 기준 |
| **Thinking Data Log** | 직원별로 누적되는 사고 기록. ARISA의 진짜 자산 |
| **Mirror / Reflector / Coach** | ARISA의 3계층(80/15/5): 번역 / 질문 / 코칭 |
| **Cognitive Operations System** | 조직의 사고를 운영하는 시스템 — ARISA 2.0의 정체 |
| **Organizational Learning OS** | 조직 학습을 측정·가속하는 운영체제 — ARISA 3.0의 정체 |

---

*ARISA 2.0 — Cognitive Operations System · by Project Rent · 2026-06-13*
