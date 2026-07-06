# 26-reporting-os — Project Rent Reporting OS

조직 업무보고 표준화 체계. ARISA의 **Reporting Layer** — 기존 ARISA 2.0(텔레그램 봇·주간 집계·Daily Brief)을 대체하지 않고 그 위에 조직 공통의 사고 프레임을 얹는다.

## 산출물 3종 (v1 · 2026-07-06)

| 파일 | 역할 | 용도 |
|---|---|---|
| `reporting-os-보고체계-정의-v1.md` | **SSOT** — 보고의 정의, 6-Layer 통합 매핑, 항목별 의미, Report Score 배점, Thinking Cost 프로토콜, 시트 스키마 | 다른 두 산출물의 모든 용어·배점·분류의 기준 |
| `reporting-os-표준양식-v1.xlsx` | 엑셀 표준양식 6시트 (안내/코드표/일일보고/주간보고/작성예시/ReportScore) | 직원 실작성 + 자가채점. 드롭다운·수식 내장 (수식 30개 검증 완료) |
| `reporting-os-교육가이드-v1.html` | 교육 슬라이드 22장 (project-rent 다크테마, 키보드 네비) | 직원 교육 세션 발표용. 실데이터 Before/After 사례 (익명화) |

## 관계도

```
GPT 논의 (보고 철학·6-Layer·Report Score·Thinking Cost)
        ↓
정의 문서 (md, SSOT) ──→ 엑셀 표준양식 (실작성 인터페이스)
        │                └─→ 교육 가이드 (HTML 22장)
        ↓
기존 ARISA 자산과의 동기화 지점 (아래)
```

## 23-arisa 스키마 동기화 지점 (하위호환 원칙)

기존 구글시트(`일일업무보고`, ID `1izuwjWPiJfbaJZ-Ib-U_NO0_Ln1_5yRr1SIRAum-hi4`)의 **열 순서는 변경 금지**, 확장은 우측 append만:

- 핵심업무 시트: 기존 A~L (12열) + 확장 M`프로젝트` N`목표대비%` O`근거구분` P`★최중요`
- 메타 시트: 기존 A~J (10열) + 확장 K`ReportScore(자가)` L`추가질문수(ThinkingCost)`
- 엑셀 양식의 컬럼명은 구글시트 스키마와 명칭 일치 (향후 봇 연동 대비)

## 실데이터 근거 (교육 논거)

2026 W26 (`../23-arisa/weekly/weekly-data-2026-W26.json`): 주 86건 보고 / 완료율 75% / **열린 결정 2건 / 전원 decision_thinking 0점** / 3명 outcome_quality 0점. Before/After 사례 원문 출처: 같은 파일의 blockers + `../23-arisa/brief/daily-brief-2026-06-23.json` (교육 자료에서는 익명화 — "기획팀", "운영팀" 표기).

## 후속 로드맵 (v1 범위 밖 — 설계 메모)

| 단계 | 내용 | 관련 파일 |
|---|---|---|
| ~~v1.1~~ ✅ | **완료 (2026-07-06)**: 봇 루브릭 자동 채점 + 질문 루프(최대 3라운드) + 직원·관리자 점수 회신 + 메타 N/O열 기록 (M열은 하드닝의 submitted_at) | `00-system/02-scripts/daily-report-bot.py` |
| v1.2 | 주간 집계에 ReportScore 평균·추이 축 추가 (개인·팀) | `00-system/02-scripts/weekly-report-aggregate.py` |
| v1.2 | 봇이 핵심업무 확장 컬럼(M~P) 자동 기입 — 프로젝트명 추출·목표대비% 질문 | `.claude/skills/daily-report-writer/SKILL.md` |
| v1.2 | Decision Log(`decisions.jsonl`) 축적 재가동 — Decision 항목 교육 정착이 선행 조건 | `00-system/02-scripts/shared/decision.py` |
| v1.2 | ThinkingCost 자동 측정 (관리자 후속 질문 카운트) — 그 전까지 메타 O열 수기 | — |
| v2 | Outcome·Learning Layer 연결 (Organizational Cognition Loop 완성) | — |

## Progress

### 2026-07-06 — v1.1 병합 재배포 + 윤혜정 제보 조사
- **회귀 복구**: 최초 scp 배포가 맥미니 전용 하드닝 커밋 2개(dfceedf 유실방지 P0~P3, d0a5b34 대화영속화·to_thread)를 덮어쓴 것을 발견 → 3-way 병합(git merge-file, 충돌 4곳 수동 해소)으로 하드닝+Reporting OS 통합본 재배포. 메타 시트 열 최종: M=submitted_at(하드닝) / **N=ReportScore / O=score_detail** / P=ThinkingCost(예약)
- **윤혜정 제보(7/4 "팀원 보고 공유 안 됨") 조사**: 설정(team_leads·ID매핑·팀명) 전부 정상. 유력 원인 = 7/3 gws 인증 장애로 5명 보고가 소리 없이 유실된 사고(하드닝 커밋 주석에 명시) + 로그가 재시작 시 truncate돼 7/2~7/4 증거 소실. 공유 성공이 무기록인 점도 확인 한계. 하드닝(로컬 큐+백필+정직한 안내)이 이미 대응책
- **저장소 비동기화 발견**: 맥미니에 로컬에 없는 커밋 3개(7bcdfb0·dfceedf·d0a5b34 + shared/report_queue.py 등), 로컬에도 맥미니에 없는 커밋 — 양방향 동기화 필요 (사용자 결정 대기)

### 2026-07-06 — v1.1 봇 통합 (같은 날 후속)
- `daily-report-bot.py`에 Reporting OS 채점·질문 루프 구현: `SCORE_PROMPT`(루브릭 7항목, "없음" 득점 규칙), `rubric_evaluate`/`completion_evaluate`(질문 큐 최대 3개, 규칙 안전망 유지), `receive_completion` 3라운드 루프("없음"=답변 기록, "패스"=건너뜀), `finalize_and_send` 최종 채점, 직원 회신(점수+다음 보완 한 줄)·관리자 회신(헤더 점수, 폴백 시 "간이" 표기), 메타 M(총점)/N(detail JSON) 기록
- 드라이런 검증(실보고 3케이스): 잘 쓴 보고 98 / 부실 20 / "없음" 명시 95 — 변별력·없음 득점·질문 상한·LLM 실패 폴백 모두 확인
- 교육 가이드 v1: "대표"→"관리자" 용어 변경 (실보고 인용 원문 2곳만 보존)
- 남은 것: 봇 재시작 후 라이브 1회 테스트 (텔레그램 /report)

### 2026-07-06 — v1 최초 제작
- GPT 논의(보고의 정의·6-Layer·8질문·Report Score 100점·Thinking Cost·Cognition Loop)를 기존 ARISA 자산(봇 7기준·14사고요소·시트 스키마·W26 실데이터)과 통합 설계
- 산출물 3종 완성. 검증: 엑셀 수식 30개 참조 유효·배점 합 100·드롭다운 정상 (LibreOffice 부재로 정적 검증 대체), HTML 22장 렌더링·네비·오버플로·콘솔에러 0건 (Playwright evaluate), 3종 간 용어·배점·카테고리·스키마 교차 일치, 실명 잔존 0건
- 명칭 확정: **Reporting OS** (사용자 확정 — ARISA Reporting Layer로 위치 명기, 익명화 방식·HTML 슬라이드 형식도 사용자 확정)
