# ARISA 정보 취합·분류 기준 v1.1 — 맥킨지 사고법 × 6-Layer 확장

> 작성: 2026-07-25 · v1.1 · by Project Rent
> SSOT 연계: [`26-reporting-os/reporting-os-보고체계-정의-v1.md`](../26-reporting-os/reporting-os-보고체계-정의-v1.md) (6-Layer 분류축)
> 코드 반영: `00-system/02-scripts/daily-brief-aggregate.py` (`sort_items`·`headline` 가설·decision RAPID), `weekly-report-aggregate.py` (`_open_decisions`)
> v1.1 추가: 가설 주도(Day-1 Answer) 헤드라인 · 결정권한(RAPID) 메타 · 검토 방법론 전체 기록(§6)

---

## 0. 왜 이 문서인가 — "취합됐지만 나열됐다"

ARISA는 매일 직원 보고를 취합하고, Engine D(LLM)가 **7범주로 분류**까지 한다. 그러나 각 범주 **내부의 우선순위와 조직 전체의 종합(한 문장 결론)이 비어 있어**, 대표가 보는 것은 여전히 "분류된 나열"이었다.

Reporting OS의 6-Layer 정의는 이 병을 정확히 지목한다 — Priority Layer가 빠지면 *"10가지 나열 → 그래서 중요한 게 뭐야?"* 가 된다. 이 문서는 그 Priority(우선순위)와 Context(종합)를 **맥킨지 사고법으로 규율**하고, **결정론적 정렬 규칙**으로 코드에 못박는다.

원칙 한 줄: **취합 = 정렬 완료.** 정보가 모이는 순간 이미 "무엇을 먼저 볼지"가 정해져 있어야 한다.

---

## 1. 맥킨지 방법론 큐레이션 (ARISA 적용 1:1)

정보취합·의사결정에 실제로 쓰는 것만 선별한다. 각 방법론에 "ARISA 어디에 사는가"를 붙였다.

| 방법론 | 핵심 | ARISA 적용 지점 |
|---|---|---|
| **MECE** (상호배타·전체포괄) | 겹치지도 빠지지도 않게 분류 | 7범주의 경계 규율 — 특히 `support`(직원이 뭘 원하는지 아는 상태) vs `intervention`(대표 판단·코칭 필요)를 겹치지 않게 |
| **Pyramid Principle** (결론 먼저) | 최상위 결론 → 근거 → 세부 | `headline`을 조직 전체의 **Governing Thought(한 문장 결론)**로 규정. 그 아래 범주→항목이 논리적으로 지지 |
| **Impact × Urgency 매트릭스** | 영향도 × 시급성으로 우선순위 | 항목 정렬의 2·3차 키 — `urgency`(기존) × impact 신호(결재·금전·기한) |
| **80/20 (Pareto)** | 20%가 결과의 80% | `top5`·`decision_summary`가 "오늘 볼 20%"를 뽑는 근거 |
| **SCQA / So What·Now What** | 상황→갈등→질문→답, 데이터→의미→액션 | decision 항목의 `detail`(배경→상태→액션) + `recommendation/deadline/delay_impact` 구조 |
| **Ghost Deck (액션타이틀 테스트)** | 제목만 읽어 논증이 완결되는가 | 품질 체크 — item `title`만 위→아래로 읽었을 때 조직 상황이 그려지는지 |
| **가설 주도 / Day-1 Answer** *(v1.1)* | 요약이 아닌 반증 가능한 주장을 먼저 세운다 | `headline`을 "오늘 조직 상태에 대한 가설" 한 문장으로 — 고유명사·수치를 넣어 검증 가능하게 (Governing Thought의 격상) |
| **결정권한 (RAPID)** *(v1.1)* | 결정을 "무엇"만이 아니라 "누가"까지 | decision 항목에 `recommender`(추천자)·`decider`(최종 결정권자) 부착 — R4 PM 라우팅의 방법론적 정식화. RAPID는 Bain 프레임(맥킨지도 decision-rights를 동일 강조) |

> 참조 자산(신규 작성 대신 재사용): `00-system/01-templates/consulting-report-template.md`(Pyramid·SCQA·MECE 이슈트리·Ghost Deck), `00-system/01-templates/executive-report-framework.md`(So What/Now What·Rule of Three).

---

## 2. 6-Layer 확장 매핑 (핵심)

Reporting OS의 6-Layer(분류축)를 **ARISA 7범주 · 맥킨지 렌즈 · 정렬 기여**로 연결한다. 6-Layer는 "어디에 속하나"(분류), 이 매핑은 "그래서 어떤 순서로 보나"(정렬)를 더한다.

| 6-Layer | ARISA 7범주 | 맥킨지 렌즈 | 정렬 기여 |
|---|---|---|---|
| **Decision** (결정) | `decision` | Pyramid 정점 · Impact×Urgency | 최상위. 결재·승인 > 금전 > 기한 순 |
| **Priority** (우선순위) | (범주 가로지름) | 80/20 | `top5`·`decision_summary` 선정 |
| **Risk** (리스크) | `risk` / `anomaly` | MECE 리스크 분해 | urgency · 손실·기한 결부 |
| **Progress** (진행) | `project` | So What (상태변화의 의미) | 상태변화순 |
| **Thinking** (판단) | `intervention` / `growth` | 사실/의견 근거구분 | 코칭 필요도 |
| **Context** (맥락) | `headline` · project 귀속 | Governing Thought | 종합 한 문장 |

---

## 3. 정렬·종합 규칙 (코드와 1:1) — `sort_items`

취합된 `items`는 다음 **결정론적 키**로 정렬된다. LLM 응답 순서(=시트 행 순서)에 의존하지 않는다.

1. **1차 — 범주** `CAT_ORDER`: `decision → intervention → risk → support → project → growth → anomaly`
2. **2차 — 긴급도** `URG_RANK`: `high → mid → low`
3. **3차 — impact 신호** `_prio_rank`: 결재·승인 > 비용·금전 > 리스크 > 개입 > 기타
   (키워드: 승인·결재·송금·결제·계약 / 비용·지출·예산·견적·단가·금액·발주)
4. **4차 — 미결 경과** `age_days` 큰 것 우선: 오래 방치된 결정이 위로 (`carried` 이월 항목)
5. **종합 — 가설(Day-1 Answer)** *(v1.1)*: `headline`은 결정·리스크 우선의 **반증 가능한 한 문장 주장**. 고유명사·수치를 넣어 검증 가능하게. 근거 없으면 공란.
6. **결정권한(RAPID)** *(v1.1)*: decision 항목에 `recommender`(추천자) → `decider`(결정권자)를 부착. 보고에서 식별될 때만(추측 금지), 대표창 카드에 "결정권한: 추천 A → 결정 B"로 표시.

> 동률(같은 키)은 stable sort로 기존 순서를 유지 → 정렬만 바뀌고 내용은 무손실.

### 적용 지점 (JSON 출력부터 정렬)
- `build_brief_data()` — carried 이월 직후 `sort_items(items)`. 이후 `decision_summary`·`top5`·`project_cards`·JSON `items`가 모두 정렬된 배열을 공유.
- `build_team_brief_data()` — 팀 브리프도 동일.
- 효과: `20-operations/23-arisa/brief/*.json`이 **소스부터 정렬** → 대표창뿐 아니라 팀 브리프·개인 카드·API 소비자 전부 자동 정렬.

### 주간 리포트
- `weekly-report-aggregate.py` `_open_decisions()` — 미해결 결정을 impact 순(결재·금전 > 기한 명시 > 기타)으로 정렬 후 상위 5개.

---

## 4. 품질 게이트 (Ghost Deck 테스트)

취합 결과물이 "정렬됐는가"를 넘어 "논리가 서는가"를 점검한다.

- [ ] **headline만 읽어** 오늘 조직 상태에 대한 **가설**이 서는가? 반증 가능한가? (Day-1 Answer)
- [ ] **item `title`만 위→아래로 읽어** 각 프로젝트 상황이 그려지는가? (Ghost Deck)
- [ ] decision 항목에 **So What/Now What**(추천안·기한·미결영향)이 채워졌는가?
- [ ] decision 항목에 **결정권한**(추천자→결정권자)이 식별됐는가? (RAPID)
- [ ] 같은 정보가 두 범주에 중복되거나(MECE 위반), 빠진 위험이 없는가?
- [ ] Priority가 "10가지 나열"이 아니라 **top5로 압축**됐는가? (80/20)

---

## 6. 검토된 맥킨지·컨설팅 방법론 전체 (채택/보류 판단)

정보취합·의사결정 관련 방법론을 폭넓게 검토하고, ARISA의 실제 갭에 꽂히는 것만 채택했다. 나머지는 "왜 지금은 아닌가"를 남겨 재검토 근거로 둔다.

| 방법론 | 출처 | 채우는 갭 | 판단 | 반영처 |
|---|---|---|---|---|
| MECE | McKinsey/Minto | 분류 경계 | ✅ 채택 v1 | 7범주 규율 |
| Pyramid Principle | Minto(McKinsey) | 종합 구조 | ✅ 채택 v1 | headline·항목 지지 |
| Impact×Urgency | 컨설팅 통용 | 우선순위 | ✅ 채택 v1 | 정렬 2·3차 키 |
| 80/20 (Pareto) | Pareto | 압축 | ✅ 채택 v1 | top5·decision_summary |
| SCQA·So What | Minto(McKinsey) | 결정 서술 | ✅ 채택 v1 | decision detail |
| Ghost Deck | McKinsey | 품질검증 | ✅ 채택 v1 | title 테스트 |
| **가설 주도·Day-1 Answer** | McKinsey 핵심 | 종합이 요약에 머묾 | ✅ **채택 v1.1** | `headline` 프롬프트 |
| **결정권한(RAPID)** | Bain(개념은 통용) | 결정에 "누가"가 없음 | ✅ **채택 v1.1** | decision `recommender`/`decider` |
| **이슈 트리·로직 트리** | McKinsey/Minto | 복잡 항목 분해 | 🔸 **문서 원리만** — 데일리 자동화엔 과함, 무거운 소수 decision에 수동 적용 | (원리) |
| **Driver Tree(동인 분해)** | McKinsey | 주간 지표가 집계뿐 | 🔸 **주간 별도** — 완료율·ReportScore를 동인으로 분해, weekly-dashboard 대상 | (weekly 검토) |
| **5 Whys·근본원인** | Toyota/Lean(컨설팅 통용) | anomaly가 플래그에 머묾 | ⏭ **v2** — LLM 자동 근본원인은 지어내기 위험, 신중 도입 | — |
| **7S · Three Horizons · Where-to-Play** | McKinsey | 조직·전략 진단 | ⏭ **분기 리뷰용** — 매일 취합엔 부적합, 별도 렌즈로 분리 | — |
| **Rule of Three** | 수사학/컨설팅 | 인지 부하 | ➖ **흡수됨** — top5·압축 규칙에 이미 반영, 중복 | (기존) |

> 채택 원칙(80/20): 데일리 판단 품질을 가장 크게 올리고 구현이 가벼운 것부터. 가설 헤드라인·결정권한이 v1.1 우선. 이슈트리·Driver·5Whys는 각각 "무거운 항목·주간·v2"라는 제자리가 있어 데일리에 억지로 넣지 않는다.

---

## 7. 버전 로드맵
- **v1**: 6-Layer 확장 매핑 + `sort_items` 결정론적 정렬 + 주간 `_open_decisions` 정렬
- **v1.1** (현재): 가설 주도(Day-1) 헤드라인 + 결정권한(RAPID) 메타 + 검토 방법론 전체 기록(§6)
- **v1.2**: 이슈 트리(무거운 decision 분해) · Driver Tree(주간 지표) 실전 적용 검토
- **v2**: 5 Whys(anomaly 근본원인) + Outcome·Learning Layer 연결 — 결정 이후 결과 회수까지 정렬축 확장

---

*이 기준은 `arisa-info-classification-criteria-v1.html`로 동일 내용을 뷰 제공. 분류축 SSOT는 6-Layer 문서, 정렬 구현 SSOT는 `sort_items`.*
