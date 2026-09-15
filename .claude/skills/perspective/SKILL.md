---
name: perspective
description: >
  Multi-Perspective Content Framework — 리서치로 쌓인 콘텐츠 볼륨을 여러 관점(Lens)에서
  동시에 재해석·재조합하여 새로운 프로그램·전시·경험·비즈니스 가능성을 발굴하는 사고 엔진.
  분류 시스템이 아니다. 하나의 콘텐츠는 여러 관점과 동시에 연결되며,
  관점 간에는 상하 관계가 없다. AI는 태거가 아니라 해석 생성기·빈틈 탐지기로 동작한다.
  "관점 분석", "퍼스펙티브", "perspective", "렌즈 전환", "재조합", "가능성 발굴",
  "이 리서치로 뭘 만들 수 있을까", "콘텐츠 재해석", "화이트스페이스 찾아줘",
  "MPCF", "콘텐츠 사고 엔진" 등을 언급하면 자동 실행.
  ⚠️ 브랜드 전략 시뮬레이션은 /brand-thinking, SNS 멘션 분석은 /rxr-* 담당 —
  이 스킬은 "이미 확보한 콘텐츠 자산에서 새 기획 가능성을 뽑는 것"에 특화.
user-invocable: true
model: opus
context: fork
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Edit
  - Agent
  - AskUserQuestion
---

# /perspective — Multi-Perspective Content Framework

> 콘텐츠를 정리하지 않는다. **다시 본다.**
> 같은 재료를 다른 렌즈로 보면 다른 기획이 나온다. 그 전환을 시스템으로 만든다.

**사양 SSOT**: `00-system/01-templates/perspective-framework.md` — 데이터 모델·불변 규칙·판정
알고리즘은 전부 그 문서에 있다. **Phase 시작 전 반드시 읽는다.** 본 문서는 실행 절차만 담는다.

---

## 절대 원칙 (매 Phase에서 자기검증)

```
P1. 병렬성 — Perspective에 부모-자식을 만들지 않는다. 계층이 보이면 즉시 중단하고 재설계.
P2. 다중성 — 하나의 Atom은 여러 Perspective와 동시에 연결된다.
P3. 해석성 — 연결에는 as_what / so_what / forms 3단이 들어간다. 없으면 태그이지 해석이 아니다.
P4. 개방성 — Perspective는 사용자가 만든다. 시드 12종은 출발점이지 정답이 아니다.
P5. 비확정 — AI는 가능성을 넓히고 지표를 낸다. 기회/무의미 판정과 방향 선택은 인간이 한다.
P6. 반증성 — 인사이트는 반증 가능해야 한다. 어떤 데이터를 넣어도 나오는 문장은 폐기한다.
```

**AI가 하면 안 되는 것**: 빈칸을 스스로 걸러내기 / 조합에 순위 매겨 "이게 정답"이라 말하기 /
Perspective를 임의로 통폐합하기 / 해석 없이 태그만 붙이기 /
**반증 불가능한 일반론을 인사이트라고 내놓기** / 폐기된 인사이트를 감추기 /
모르는 운영 스펙을 그럴듯하게 지어내기 / **페르소나 일반론을 타겟 분석이라고 내놓기** /
가설을 조사 데이터인 것처럼 표기하기 / **Objective를 벗어난 조합을 몰래 버리기**.

---

## 10-Phase 파이프라인

```
Phase 0: VOLUME SCAN     리서치 자산 스캔 → ownership 분해 → 볼륨 판정
    ↓                     + Objective 정의 (클라이언트 요구·방향성 = 상위 조건)
    ↓                     ★ T0면 여기서 종료 (재료 부족)
Phase 1: ATOMIZE         문서 → Content Atom 추출 (출처·ownership 필수)
    ↓                     ★ 인간 게이트: 이게 진짜 콘텐츠인가
Phase 2: LENS SETUP      2 Pack 19종에서 6~10개 선택 + 커스텀 + 3단 검증
    ↓                     + Audience 정의 (렌즈 아님 — 별도 축)
Phase 3: READING         Atom × Perspective 교차 해석 (병렬 워커) × Audience(선택)
    ↓
    ├──────────────────────────────┐
    ↓                              ↓
Phase 4: DENSITY MAP          Phase 4.5: CLUSTER
[구조적 탐지]                  [의미적 탐지]
밀도 지표 + 화이트스페이스 5종    Reading을 5~8 그룹으로 + 발견 패턴
    ↓                              ↓
    └──────────────┬───────────────┘
                   ↓
Phase 4.7: INSIGHT       반증 가능한 명제 5~7개 (I1~I3 통과분만) ★함정 구간
    ↓                     ★ 인간 게이트: 어느 빈칸이 기회이고, 어느 명제가 진짜인가
Phase 5: RECOMPOSE       Insight 근거 조합 → Composition + ops + 타겟 성립/불성립
    ↓                     ▲ Objective 대조: meets / partial / deviates (이탈도 제시)
Phase 6: LENS SWITCH     대화형 렌즈 전환 (선택적, 반복)
    ↓
Phase 7: OUTPUT          JSON SSOT + 보드(흐름도) + 리포트 10섹션 + SWOT 뷰 + 산출물 매핑
```

**Phase 4와 4.5는 병렬이다.** 하나는 매트릭스의 형태를 계산하고(없는 것 찾기),
하나는 Reading의 내용을 읽는다(있는 것 묶기). 한쪽만 돌리면 절반이 통째로 사라진다.

---

## Phase 0 — VOLUME SCAN

### 입력 받기
대상 지정: 프로젝트 폴더 경로 / 문서 묶음 / 기존 `perspective-map.json`(이어서 작업).

### Objective 정의 (사양서 §2.8) — 프로젝트당 1회
스캔과 함께 **클라이언트 요구·방향성**을 확정한다. 렌즈가 아니라 **상위 통과 조건**이다.
```
requirements   must / should 구분해서 목록화
direction      "무엇이 아닌가"까지 (예: 직영 정신문화 거점 — 임대형 수익시설 아님)
constraints_ref 법·제도·일정 제약 참조
```
문서에서 못 찾으면 **지어내지 말고 사용자에게 묻는다.** Objective 없이 Phase 5로 가면
조합이 요구를 벗어났는지 아무도 검사하지 못한다.

### 수행
1. 대상 경로의 리서치 자산 스캔 — `.md` `.html` `.json` `.txt` 및 미팅록·리포트·크롤링 데이터
2. 대략적 Atom 추출 가능량 추정 (문서당 의미 단위 개수)
3. **ownership으로 분해** (사양서 §2.2.2) — `own` / `reference` / `context` / `constraint`
4. 사양서 §3.1 볼륨 게이트로 Tier 판정 — **반드시 `own` Atom 수 기준.** 총량으로 판정하면
   레퍼런스가 많은 프로젝트를 무조건 포화로 오판한다 (봉은사 1차 가동 사례)

### 출력
```
📊 VOLUME SCAN — [프로젝트명]
스캔 문서      : 23건 (미팅록 4, 리포트 6, 크롤링 데이터 3, 기타 10)
추정 Atom      : 총 175
  ├ own        : 50   ← ★ 판정 기준
  ├ reference  : 75   (신규성 검증용, Reading 생성 안 함)
  ├ context    : 30
  └ constraint : 20
판정           : T2 (본격 가동 가능) — own 50 기준
빈약한 영역    : 공간·물리 자산 기록 부족 — Installation 렌즈가 얕게 나올 것
```

### 게이트
- **T0 (Atom < 20)**: 여기서 **중단**한다. "무엇을 더 리서치해야 하는가"만 리포트하고 종료.
  억지로 진행하면 얕은 조합이 나오고 프레임워크 신뢰도가 깨진다.
- **T3 (120+)**: 전수 해석 금지. 허브 후보 중심으로 샘플링할 것을 먼저 합의.

---

## Phase 1 — ATOMIZE

### 수행
문서를 읽고 Content Atom을 추출한다. 사양서 §2.2 스키마 준수.

**추출 원칙**
1. 🔴 **입도는 "최소 단위"가 아니라 "결정 단위"다** (사양서 §2.2.1b)
   ```
   이 프로젝트에서 서로 다른 결정·기획을 낳는가?
      Yes → 별도 Atom
      No  → 하나의 Atom. 세부는 detail 필드에 보존
   ```
   같은 대상도 프로젝트에 따라 입도가 달라진다.
   - 전시 기획 → 판전 / 현판 / 경판 = **3개 Atom** (각각 다른 전시가 나온다)
   - 공간 활용전략 → **1개 Atom** "판전군 — 관광상품화 가능한 보유 콘텐츠"

   **Phase 0의 Objective를 보고 입도를 정한다.** 목적을 모르면 입도를 정할 수 없다
2. **출처는 파일·라인·원문 인용까지** 보존한다. 출처 없는 Atom은 등록 거부
3. **kind는 존재 형식이지 카테고리가 아니다** — kind로 해석 방향을 미리 제약하지 않는다
4. **해석을 여기서 하지 않는다** — Phase 1은 재료 정리. 판단은 Phase 3

**과분할 / 과통합 자가진단** (Phase 3 이후 역검증)
| 신호 | 진단 | 조치 |
|------|------|------|
| 걸리는 렌즈 **2개 이하** | 과분할 | 상위 결정 단위로 병합, 세부는 `detail`로 |
| **8개 이상** 렌즈에 걸리는데 해석이 서로 무관 | 과통합 | 결정이 갈리는 지점에서 분할 |
| 3~7개 렌즈 + 해석이 서로 연결됨 | 적정 | 유지 |

**병렬 처리**: 문서 10건 이상이면 Agent로 분할 추출 후 병합. 병합 시 중복 Atom은
`title` 유사도로 후보만 표시하고 **자동 병합하지 않는다** (다른 것을 같다고 뭉치면 정보 손실).

### 인간 게이트
추출 결과를 표로 제시하고 확인받는다.
```
| id | kind | title | maturity | 출처 |
확인 요청: ①빠진 것 ②Atom이 아닌 것 ③더 쪼개야 할 것
```

---

## Phase 2 — LENS SETUP

### 수행
1. 사양서 §2.3.2 시드 카탈로그 **2 Pack 19종** 제시 → 이 프로젝트에 쓸 것 선택
   - **Content Pack 11종** — 무엇을 만들 것인가 (문화·전시·브랜드)
   - **Business Pack 8종** — 실제로 굴러가는가 (Location·Asset·Revenue·Compliance·
     Competitive·Feasibility·Risk·Stakeholder)
2. 프로젝트 고유 렌즈 제안 — 리서치 내용에서 **반복 등장하는 관심축**을 근거로 3~5개 제안
   (예: 종교 공간 프로젝트 → `Ritual`, `Silence`, `Threshold`)
3. 사용자 커스텀 렌즈 자유 추가
4. **Audience 정의** — 타겟 목록을 `kind:audience` · `ownership:context` Atom으로 등록.
   Audience는 렌즈가 아니다(§2.4.1). 렌즈 풀에 섞지 않는다

### 🔴 활성화 규칙 (사양서 §2.3.3) — 전체를 켜지 않는다
```
권장   6~10개
금지   팩 통째로 켜기 — 19종 × Atom 90 = 1,710셀, 감당 불가
원칙   자료가 없는 렌즈는 켜지 않는다. 빈 렌즈는 얕은 해석만 낳는다
```
**팩은 계층이 아니라 선택 묶음이다**(P1). Content가 상위, Business가 하위인 것이 아니다.
프로젝트 성격을 보고 두 팩에서 섞어 고른다.

### 3단 검증 (사양서 §2.3.1) — 모든 렌즈에 적용
```
V1 질문 테스트 — core_question이 "무엇인가?" 형태의 열린 질문인가?
                 "어떤 종류인가?" → 분류 질문 → 거부
V2 독립 테스트 — 기존 렌즈의 하위 항목으로 읽히지 않는가?
                 예: "인터뷰"는 People의 output_form이지 렌즈가 아니다
V3 교차 테스트 — 이 렌즈로 기존 Atom 3개 이상을 서로 다르게 해석할 수 있는가?
```

**거부 시 대응**: 왜 렌즈가 아닌지 설명하고, 어디에 속하는지(다른 렌즈의 output_form인지,
Atom 속성인지) 제시한다. 그냥 버리지 않는다.

### 출력
```
✅ 채택 렌즈 8종
| Perspective | Core Question | Value Criteria | 예상 Reading 수 |

⚠️ 거부 1건: "아카이브 영상" → Archive 렌즈의 output_form입니다. 렌즈로 승격하려면
   "영상이라는 매체로 봤을 때 이것은 무엇인가?"처럼 매체 자체를 축으로 재정의해야 합니다.
```

---

## Phase 3 — READING ★ 핵심

### 수행
Atom × Perspective 매트릭스를 순회하며 해석을 생성한다.

**한 Reading = 3단 필수** (사양서 §2.4)
```
as_what  이 렌즈로 보면 이것은 무엇인가        (정체 규정)
so_what  그래서 무엇이 가능한가                (잠재력)
forms    구체적으로 어떤 형태가 되는가          (실행 형태 2~4개)
```
+ `evidence`(뒷받침 Atom) + `gaps`(실행 전 확인 필요) + `confidence`

**Audience 태깅 (선택)** — 타겟에 따라 해석이 갈리는 곳에만 단다. 전부 달지 않는다.
```
audience        이 해석이 성립하는 타겟
audience_note   누구에게는 안 통하는지 ← 이게 핵심
audience_basis  data(응답 근거) / hypothesis(가설) — 가설을 데이터인 척하지 않는다
```
⚠️ **페르소나 일반론 금지**(§2.4.2). "MZ는 경험을 중시한다"류는 어느 프로젝트에나 성립한다.
audience 기술에도 I1~I3를 적용한다. 조사 응답이 없으면 전부 `hypothesis`로 표기한다.

**생성 전략**
- 전수 순회하지 않는다. Atom 수 × 렌즈 수가 400을 넘으면 다음 순으로 우선 처리:
  ① 각 Atom의 "가장 안 어울려 보이는 렌즈" 1개 — 여기서 의외의 것이 나온다
  ② kind가 다양한 Atom 우선 (person/record/place 골고루)
  ③ 사용자가 지목한 Atom
- **병렬 실행**: 렌즈별로 Agent 분할. 각 워커는 자기 렌즈의 `core_question`과
  `value_criteria`만 들고 전체 Atom을 본다 → 렌즈 일관성이 유지된다

**금지**
- as_what만 쓰고 so_what을 비우기 (= 태그, P3 위반)
- 여러 렌즈에서 같은 해석 복붙 (렌즈가 작동하지 않는다는 신호 → 렌즈 재정의)
- 근거 없는 단정 — 리서치에 없는 사실을 만들어내지 않는다. 모르면 `gaps`에 적는다

### 출력
Reading 목록 + 렌즈별 생성 수 + confidence 분포.

---

## Phase 4 — DENSITY MAP

### 수행
사양서 §3.2 지표 + §3.3 화이트스페이스 5종을 **계산**한다. 추정하지 않는다.

```
Coverage      = Reading / (Atom × Perspective)
LensBalance   = 1 - 최다 렌즈 점유율
AtomDepth     = Atom당 평균 Reading
EvidenceDepth = Reading당 평균 evidence
```

화이트스페이스 탐지:
| 유형 | 산출 |
|------|------|
| Empty Cell | Reading 0 & 해당 렌즈 활성도 상위 50% 인 (Atom, Lens) 쌍 |
| Orphan Atom | Reading ≤ 1 인 Atom |
| Hub Atom | 서로 다른 렌즈 4개 이상에 Reading 보유 |
| Triad | 같은 Atom 집합을 공유하는 서로 다른 3개 렌즈 조합 |
| Collision | value_criteria가 상충하는 두 렌즈가 같은 Atom에 Reading 보유 |
| Audience Gap | 특정 타겟 대상 Reading이 전체의 5% 미만인 렌즈 |
| Audience Monopoly | audience 태깅 Reading이 전부 동일 타겟인 Atom |

⚠️ **Audience 2종은 태깅률 20% 미만이면 계산하지 않고 "판정 불가"로 표기**한다.
없는 데이터로 공백을 발견했다고 말하지 않는다.

### 출력
```
📐 DENSITY MAP
Coverage 0.21 ✅ / LensBalance 0.71 ✅ / AtomDepth 2.8 ✅ / EvidenceDepth 1.4 ⚠️

🕳 화이트스페이스
Empty Cell        17개  ← 인간 판정 필요
Orphan Atom        6개  (at-0012 외 5)
Hub Atom           3개  (at-0007 연출가 ★7렌즈)
Triad              4쌍  (People×Archive×Interactive 외 3)
Collision          2쌍  (Revenue × Archive — 보존 vs 수익)
Audience Gap       2건  (지역주민 — Experience·Community 렌즈에 Reading 0)
Audience Monopoly  5건  (템플스테이 자산이 전부 외국인·신도에만 태깅)
                        ※ audience 태깅률 34% — 판정 유효
```

### 출력 후
Empty Cell 전체를 나열해둔다. **기회/무의미 판정은 Phase 4.7 통합 게이트에서** 받는다.
AI가 미리 걸러내지 않는다 (P5). 판정 결과는 JSON에 기록해 다음 회차에 재질문하지 않는다.

---

## Phase 4.5 — CLUSTER (의미적 탐지) ★신설

> Phase 4와 **병렬**로 실행한다. Phase 4가 매트릭스의 형태를 계산한다면,
> 여기는 Reading의 **내용을 읽어서** 같은 이야기를 하는 것끼리 묶는다.

### 수행
Reading 전체를 읽고 의미 기준으로 5~8개 그룹을 만든다. 사양서 §2.5 스키마 준수.

**각 Cluster는 `pattern` 1줄이 필수다.** 패턴 없는 그룹은 폴더이지 클러스터가 아니다.

```
C1. 그룹 수 5~8개 — 10개를 넘으면 압축이 안 된 것
C2. 한 Reading이 여러 Cluster에 속해도 된다 (M:N — 분류가 아니므로)
C3. 단일 렌즈에만 걸친 Cluster는 '약한 그룹'으로 표기 (렌즈 내부 소분류일 뿐)
C4. 어느 Cluster에도 안 들어간 Reading은 버리지 않는다 — Orphan Reading으로 별도 보관
```

### 출력
```
🧩 CLUSTER — 5개 그룹 / Orphan Reading 12건

【cl-0003】미공개 1차 사료군                      Reading 5 · 렌즈 3(Archive·People·Story)
발견 패턴 → 최고 밀도 자산은 전부 '아직 안 열린 것'이다 — 경판·노트·미공개 유물

【cl-0005】이미 돌아가는데 공간이 없는 것          Reading 4 · 렌즈 2(Experience·Business) ⚠️약한 그룹
발견 패턴 → 외국인 영어 프로그램이 상시 운영 중인데 전용 공간 기록이 0건
```

---

## Phase 4.7 — INSIGHT ★신설 · 🔴 최대 함정 구간

> Phase 4(구조적) + Phase 4.5(의미적) 결과를 합쳐 **반증 가능한 명제**로 올린다.
> 이 Phase는 AI가 가장 쉽게 실패하는 지점이다.

### 🔴 반드시 먼저 읽을 것 — 실패 모드

AI에게 인사이트를 시키면 **거의 항상** 이런 문장을 만든다.

```
❌ "강한 철학과 네트워크는 브랜드 정체성과 스토리텔링의 핵심 자산이다"
❌ "일관된 시각 언어는 브랜드 경험의 몰입도와 기억도를 높인다"
❌ "기록 자산은 전시·출판·교육으로 장기적 가치를 창출한다"

— 타겟이 들어가면 실패 모드가 하나 더 생긴다 (페르소나 일반론) —
❌ "MZ는 경험과 스토리를 중시한다"
❌ "외국인은 진정성 있는 한국 문화를 원한다"
❌ "지역주민은 접근성을 중요하게 생각한다"
```

전부 **반증 불가능**하다. 어떤 데이터를 넣어도 나오고, 프로젝트명을 바꿔 끼워도 성립한다.
발견이 아니라 컨설팅 보고서 문법이며, 가장 쉽게 생성되기 때문에 방치하면
인사이트 레이어 전체가 일반론으로 채워진다. **그러면 이 Phase는 있으나 마나다.**

```
✅ "봉은사는 경내에서 가장 오래된 건물을 콘텐츠에서 배제한 채 신축 공간을 기획해왔다"
   → 반증 가능(다른 사찰은 최고 건물을 중심에 둔다) · 고유함 · 근거 있음
```

### 통과 조건 — 3종 전부 통과해야 등록 (사양서 §2.6.1)
```
I1. 반증 테스트  — 이 명제의 반대가 성립하는 다른 프로젝트를 하나 댈 수 있는가?
I2. 고유성 테스트 — 프로젝트명을 바꿔 끼워도 말이 되면 폐기
I3. 근거 테스트  — 뒷받침 Reading을 3개 이상 지목할 수 있는가?
```

**개수 5~7개.** 그 이상 나오면 테스트를 느슨하게 적용한 것이다.
생성한 명제마다 I1~I3 판정을 **명시적으로 기록**한다. 통과 여부를 숨기지 않는다.

### 출력
```
💡 INSIGHT — 생성 11 → 통과 6 (폐기 5: I2 일반론 4, I3 근거부족 1)

【in-0002】 봉은사는 경내 최고 건물을 콘텐츠에서 배제한 채 신축 공간을 기획해왔다
근거      cl-0003 · empty_cell(at-판전 × ps-archive) · Reading 3건
So what   신축 대공간과 최고 건물 사이에 서사가 없으면 리뉴얼 결과물은 '큰 방'이 된다
검증      I1 ✓ I2 ✓ I3 ✓

【폐기】"기록 자산은 장기적 가치를 창출한다" — I2 실패(어느 프로젝트에나 성립)
```

### 인간 게이트 ★ 필수 (통합)
1. **화이트스페이스** — Empty Cell 전체 나열, 기회/무의미 판정
2. **인사이트** — 통과 6개가 실제로 새로운 이야기인지, 폐기된 것 중 살릴 게 있는지

AI는 판정하지 않는다. 나열하고, 근거를 대고, 선택은 사용자가 한다 (P5).

---

## Phase 5 — RECOMPOSE

### 수행
Phase 4.7에서 통과한 **Insight를 근거로** Composition을 생성한다.
기회로 판정된 화이트스페이스와 Cluster 패턴이 재료가 된다.
사양서 §2.7 스키마 + §3.5 규칙 R1~R6 준수.

```
R1. 최소 2개, 권장 3개의 서로 다른 렌즈를 섞는다 (단일 렌즈 조합 금지)
R2. novelty_source를 명시 — 왜 새로운지 설명 못 하면 폐기
R3. assets_have / assets_need 분리 — 지금 있는 것으로 되는지 즉시 판단 가능하게
R4. next_question을 반드시 남긴다 — 조합은 완성품이 아니라 다음 사고의 입구
R5. 최소 1개의 Insight를 근거로 지목한다 — Insight 없는 조합은 착상이지 기획이 아니다
R6. ops(규모·주기·동시성·기간·수용력)를 채운다 — 비면 '미완'으로 표기
R7. audience_fit의 works / fails를 모두 채운다 — fails가 비면 '모두를 위한 기획'이다
R8. Objective와 대조해 meets / partial / deviates를 표기한다
```

**R8 — 이탈 조합을 지우지 않는다** (사양서 §2.8.2). 클라이언트 요구가 틀렸을 수 있고,
리서치가 요구의 전제를 반박하는 경우가 실제로 있다. AI는 이탈을 **표기만** 하고
버릴지 들이밀지는 사람이 정한다(P5). 자동 폐기하면 이 엔진은 요구사항 이행 도구로 축소된다.

**ops를 채우는 이유**: "참여형 아카이브"만으로는 기획이 아니다.
몇 개를, 얼마 주기로, 몇 개씩 동시에, 얼마 동안, 하루 몇 명이 정해질 때 프로그램이 된다.
모르는 값은 지어내지 말고 `?`로 두고 next_question에 올린다.

**reference Atom 대조 (필수)**: 생성된 조합을 `ownership == reference` 풀과 대조해
"이미 남이 한 것인가"를 판정한다. 이것이 novelty_source의 실제 근거다.

**우선순위**: Triad → Collision → Empty Cell → Hub 확장 순으로 생성.
Triad는 3면이 이미 성립하므로 실현성이 높고, Collision은 긴장이 있어 차별화가 강하다.

**순위를 매기지 않는다.** 각 조합에 대해 비용·리드타임·리스크·필요 자산을 병기하여
**사용자가 비교 가능한 형태**로 제시한다.

### 출력
Composition 카드 6~12개.
```
【cp-0004】연출가의 서랍                          type: exhibition
근거 인사이트 in-0002 (최고 건물을 콘텐츠에서 배제해왔다)
렌즈 조합   Archive × Interactive × People       novelty: empty_cell
컨셉        미공개 연출 노트를 관객이 직접 열어보고 자신의 해석을 덧붙이는 참여형 아카이브
있는 자산   연출 노트 원본 / 연출가 인터뷰
필요 자산   보존 처리 / 열람 동선 / 공개 동의
운영 스펙   40권 중 12권 · 시즌제 연 2회 · 동시 4~6 병치 · 회차당 8주 · 1일 60명
타겟 성립   ○ 외국인 · MZ    ✕ 불교신도 (유작 서사가 성보의 위계를 침식)
요구 대조   partial — 요구 3건 중 2건 충족, 수익성 목표 미달
실현성      비용 중 · 3개월 · 리스크: 원본 훼손
선례 대조   reference 27케이스 중 유사 0건 (명동1898은 건축 보존형, 참여 요소 없음)
다음 질문   복제본으로 대체해도 경험이 성립하는가?
```

---

## Phase 6 — LENS SWITCH (대화형, 선택)

하나의 Atom을 고정하고 렌즈를 갈아 끼우며 사고를 확장한다.

```
사용자: "연출가로 계속 돌려봐"

[at-0007 연출가] 고정
→ Business  : 어떤 수익이 가능한가?      → [해석]
→ Education : 어떤 워크숍이 되는가?      → [해석]
→ Archive   : 어떤 기록 전시가 되는가?   → [해석]
→ 💥 Collision 제안: Business × Archive는 충돌합니다
     (수익화 = 접근성 ↑ / 보존 = 접근성 ↓)
     이 긴장 자체를 기획으로 만들 수 있습니까?
```

전환 결과는 전부 Reading으로 저장된다. **사고 궤적이 자산이 된다.**
사용자가 "다른 렌즈로", "이건 아니고", "더 밀어봐"로 계속 굴릴 수 있게 짧게 응답한다.

---

## Phase 7 — OUTPUT

### 산출물 3종

| 파일 | 내용 |
|------|------|
| `perspective-map.json` | **SSOT** — Atom·Perspective·Reading·Composition + 판정 이력 |
| `perspective-board.html` | 인터랙티브 보드 |
| `possibility-report.html` | 가능성 리포트 |

저장 위치: `[프로젝트폴더]/perspective/`

### perspective-board.html 요구사항

**기본 뷰는 좌→우 흐름도다** (사양서 §5.2). 매트릭스는 밀도 확인용 보조 뷰.
매트릭스만으로는 "하나의 콘텐츠가 여러 렌즈에 동시에 걸린다"가 눈에 안 들어온다.

```
[Content Assets] → [Perspective Lenses] → [Cluster / Insight] → [Concepts]
   원천 콘텐츠         렌즈별 재배열+키워드      그룹·패턴·명제        컨셉 카드
        └──── 연결선으로 M:N을 시각적으로 증명 ────┘
```

1. **흐름도 뷰(기본)** — 4단 좌→우. Atom에서 여러 렌즈로 뻗는 연결선 표시.
   Atom 호버 → 그 Atom이 걸린 모든 렌즈·Cluster·Concept 경로 하이라이트
2. **매트릭스 뷰(보조)** — Atom(행) × Perspective(열), 셀 = Reading 밀도 히트맵.
   셀 클릭 → 해석 3단 표시. 빈 셀 클릭 → 해석 생성 요청 기록
3. **렌즈 스위처** — Atom 하나 선택 → 렌즈 탭 전환으로 해석 비교
4. **화이트스페이스 패널** — 5종 유형별 목록 + 기회/무의미 토글
5. **인사이트 패널** — 통과/폐기 목록 + I1~I3 판정 표시. 폐기분도 감춤 없이 노출
6. **타겟 필터** — Audience 선택 시 해당 타겟에 성립하는 Reading만 표시.
   태깅률과 data/hypothesis 비율을 항상 함께 노출 — 가설을 데이터처럼 보이게 하지 않는다
7. **조합 빌더** — Reading·Insight 다중 선택 → Composition 초안 슬롯
   (ops · audience_fit · objective_check 입력칸 포함)
8. **SWOT 뷰** — 기존 결과의 재배열. 빈 칸은 빈 채로 둔다
9. **JSON export** — 보드에서 편집한 내용을 JSON으로 되돌려 쓰기 (SSOT 유지)

⚠️ 계층 UI 금지 — 트리·폴더·아코디언 중첩으로 렌즈를 표현하지 않는다.
렌즈는 **동등한 탭 또는 동등한 열**로만 표현한다 (P1의 UI 반영).

**디자인**: `00-system/04-design/project-rent-design-guide.md` (R 다크 · 청보라 #6C5CE7 · SUIT)

### possibility-report.html 구성
```
0. 무엇을 요구받았는가       Objective — requirements · direction · 제약
1. 무엇을 갖고 있는가        own Atom 요약 · kind 분포 · ownership 분해 · 볼륨 Tier
2. 어떻게 보고 있는가        활성 렌즈(팩별) · 밀도 지표 · 편중 진단
3. 누구를 보고 있는가        Audience 분포 · 태깅률 · data vs hypothesis 비율
4. 무엇이 반복되는가         Cluster 5~8 + 발견 패턴          [의미적]
5. 무엇을 못 보고 있는가     화이트스페이스 7종                 [구조적] ★
6. 그래서 무엇을 알게 됐나   Insight 통과분 + 폐기분(투명 공개)
7. 무엇이 가능한가           Composition 카드 + ops + 타겟 성립/불성립 + 요구 대조
8. 무엇을 확인해야 하는가    전체 gaps 집계 → 액션 아이템
9. 다음 사고의 입구          next_question 모음
+ SWOT 뷰                   위 결과의 재배열 (아래 참조)
```

### SWOT 뷰 — 출력 포맷이지 입력 프레임이 아니다 (사양서 §5.3)

| SWOT | 자동 도출 경로 |
|------|---------------|
| **S** | Hub Atom + Reading 밀도 상위 own Atom |
| **W** | Orphan Atom + gaps 집계 + 자료 결손 렌즈 |
| **O** | 기회 판정된 Whitespace + Triad + Audience Gap |
| **T** | `ownership: constraint` Atom + Competitive/Risk 렌즈 Reading |

🔴 **역방향 금지**: SWOT 칸을 먼저 만들고 채우지 않는다. 빈 칸이 생기면
"이 프로젝트에는 해당 항목이 없다"가 정직한 결과다. 지어내는 자리가 아니다.

### Composition → 최종 산출물 매핑 (사양서 §5.1)
각 Composition에 다음 산출물 중 어디로 갈지 지정한다. **여기서 끝내지 않는다.**

| 산출물 | 연계 스킬 |
|--------|-----------|
| 프로젝트 기획안 | `/consulting-report` |
| 프로그램 구성표 · 공간 구성도 | 자체 |
| 스토리라인 | `/문체` |
| 수익 모델 | `/brand-thinking` |
| 마케팅 전략 | `/brand-analysis` |

### 검증 (CLAUDE.md 배포 규칙)
- HTML 생성 후 **브라우저로 실제 렌더 확인** — JS 에러 0, 매트릭스 표시, 클릭 동작
- 파일 존재·grep 확인만으로 완료 보고 금지
- JSON 스키마 검증: `parent` 필드 존재 여부(P1 위반), 3단 누락 Reading(P3 위반) 확인

---

## 재실행 / 증분 업데이트

리서치가 추가되면 처음부터 다시 돌리지 않는다.
```
1. 기존 perspective-map.json 로드
2. 신규 문서만 ATOMIZE → Atom 추가 (ownership 태깅 필수)
3. 신규 Atom × 기존 렌즈로 READING 생성
4. DENSITY MAP 재계산 → 화이트스페이스 변동분
5. CLUSTER 재실행 → 그룹 재편 여부 확인 (신규 Reading이 기존 그룹에 붙는가, 새 그룹인가)
6. INSIGHT 재검증 → 기존 명제가 신규 데이터로도 유지되는가. **깨진 명제를 명시적으로 보고**
7. 기존 human_verdict·판정 이력은 보존 (재질문 금지)
```

**변동분 리포트가 핵심이다** — "지난번엔 없던 Triad가 생겼습니다",
"in-0002가 신규 Reading 4건으로 반박됩니다" 같은 신호가 리서치를 계속할 이유를 만든다.
특히 **깨진 인사이트는 성과다.** 감추지 않는다.

---

## 다른 스킬과의 경계

| 상황 | 담당 |
|------|------|
| 브랜드 전략 방향 A/B/C 시뮬레이션 | `/brand-thinking` |
| SNS 멘션 감정·언어학 분석 | `/rxr-mention-analysis` |
| 이미 나온 분석을 MBB 덱으로 | `/consulting-report` |
| **확보한 콘텐츠 자산에서 새 기획 가능성 발굴** | **`/perspective`** ← 본 스킬 |

`/perspective`의 Composition 결과는 `/brand-thinking` Phase 1 입력이나
`/consulting-report`의 옵션 카드로 이어서 쓸 수 있다.

---

*Multi-Perspective Content Framework v1.0 — 사양: `00-system/01-templates/perspective-framework.md`*
