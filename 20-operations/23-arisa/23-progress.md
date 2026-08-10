# 23-arisa Progress

ARISA 운영(브리프·대시보드·봇) 작업 이력. 세션 이어가기용.

## 2026-08-09 — 직원 화면 실측 + 분장 액션 버튼 (⚠️ 재기동 대기·미커밋)

### 실측 (arisa-os.com, 직원 계정 로그인)
- **직원(member) 탭**: 내 업무 · 프로젝트 · 문서 시뮬레이터 · 오늘 Brief + HR 포털. `이번 주`·스코프 드롭다운·`회의분석 Pro`는 DOM에 있으나 `display:none`(실측 visible=false). JS 에러 0
- **내 업무**(양지혜): ⚡오늘 포커스 / ☀️오늘 선언 / ⚠️입력 누락 / ✅내 분장(진행률·완료·완료보고) / 🆕제안 / 내 프로젝트 일정. 대표창의 Decision·Risk·승인·결재 블록은 `SESS.admin` 게이트라 fetch 자체가 안 됨
- **오늘 Brief**(`/my-brief`, 김준호 08-07): 헤더 → 최근 영업일 탭 7개 → 팀 헤드라인 → 이번주 핵심칩 → 내 카드(🟢 45점 ReportScore + 항목별 상세 + ⚠이슈). 렌더 카드 1개(본인만), 💬코멘트 UI 없음
- 실측 리포트: `arisa-직원화면-실측-20260809.html`

### 확인 필요 3건
- **팀 표기가 두 소스로 갈린다** — users.json은 김준호·양지혜 모두 `기획운영`인데 브리프는 김준호=운영팀, 양지혜=기획팀(arisa-employees.json). 리더 라우팅 축 ≠ 브리프 집계 축
- **08-07 보고자 1명** — active_people 08-06=2 / 08-07=1 / 08-09=3. 화면이 아니라 제출률 문제
- **주말 배치 산출물은 화면에서 못 연다** — 08-08·08-09 브리프가 생성돼 있지만(08-09에 양지혜·양은정 포함) 날짜 탭은 영업일만, `?date=2026-08-09`도 08-07로 폴백. 월요일 브리프가 금~일 합산이라 내용 손실은 아님

### 구현 (대표 지시: "개인업무 진행률 체크·완료보고 버튼이 있어야 한다")
지시의 실체는 **버튼이 없는 게 아니라 안 보이는 것**이었다. `.st-act`가 11px·muted 텍스트 링크였다.
- **`/my-brief` 하단에 ✅내 열린 분장 패널 신설** — `MYBRIEF_TASKS_JS` + `_inject_mybrief_tasks()`. 브리프 카드는 보고 문장이라 시트 행과 매핑이 없어서, `/api/my-work`의 분장(row 보유)을 별도 블록으로 붙였다. 미착수→`▶ 진행`, 공통→진행률 셀렉트(10~90)·`✓ 완료`·`📣 완료·보고`, 완료→`⏳ 승인 대기` 배지만. 쓰기는 내 업무 탭과 동일 API(`/api/assign-status`·`/api/assign-progress`)
- **본인 세션일 때만 렌더** — 대표가 남의 my-brief를 열람할 때 대리 완료가 되지 않게(실측 panel=false, 본인 것은 7건 표시)
- **내 업무 탭 시인성** — `.st-act` 12px·padding 4/11·높이 28px, `✓ 완료`=녹색 윤곽, `📣 완료·보고`=accent 채움(87×28), `.il-pg` 라벨을 "진행률 50% · 자동"으로

### 검증 (맥미니 임시 포트 8790 + SSH 터널)
버튼 5개·셀렉트 2개 전부 핸들러 바인딩 / JS 에러 0 / 모바일 375px 가로 스크롤 없음 / 상태별 버튼 분기 정상 / 권한 경계 정상
- ⚠️ **미검증**: 클릭 시 시트 반영·텔레그램 발송. 실제 직원 분장 데이터가 바뀌어서 누르지 않았다. 페이로드는 내 업무 탭과 동일 형식임을 코드 대조로 확인

### 남은 것 (다음 세션 최우선)
1. **서비스 재기동** — 파일은 신버전(md5 43a787a3)으로 교체됐으나 프로세스는 구버전 메모리(PID 44753 그대로). `launchctl kickstart -k`·`pkill` 모두 자동 차단됨. 사용자가 직접 실행 필요. 백업 `/tmp/dashboard-server.bak-20260809-1907.py`
2. **커밋 안 됨** — `dashboard-server.py` M 상태. 다른 세션 pull/reset에 날아갈 수 있다
3. 재기동 후 실서비스에서 버튼 1건 실동작 확인

## 2026-07-28 — 카드 유실 2건 복구 + 삭제 감사·외부 파트너·중단 아카이브 (배포 완료)

### 유실 복구 — 원인이 서로 달랐다
- **병원프로젝트**: 삭제가 아니라 **맥미니 배포 미반영**. 로컬 14.9KB(브리프 18·태스크 25·이슈 8) vs 맥미니 1.6KB(7/16 백필 원본). 등록 시 `portfolio-register.py`를 거치지 않아 배포 단계가 실행되지 않았다 — 근거는 백업 파일명 형식(`.bak-20260727` = 수동 cp, 스크립트는 `-2006`까지 붙인다). 재배포 완료
- **중기 팝업스토어**(`중기-팝업스토어-jufws`): 7/18 중복 정리는 정상이었고(껍데기 `-a8ay6` 삭제 → 이 카드에 별칭 추가) 그 뒤 파일째 소실. **삭제 로그가 없어 시점 특정 불가**, git 미추적 + `/tmp/p1p2-dataops-*` 백업 소실로 사본 없음. 7/24 weekly-project 리포트 잔존 정보로 재등록(PM 배성원·~12/31·진척 70%). goal·client·KPI는 공란 유지 + 이슈로 남김
  - 7/24 리포트의 '섬 팝업 공간안' 의사결정은 **별칭 토큰 매칭 오류**로 잘못 붙은 것(여수 건) — 카드에 반영하지 않음. 23-progress 7/18 기록의 "붙임 표기 미감지" 문제와 같은 뿌리

### 재발 방지 (이번 조사에서 드러난 구멍)
- **삭제 스냅샷 + 감사 기록**: `projects/_trash/{id}.{YYYYMMDD-HHMMSS}.json` 보관 + `archive-log`에 `action=delete`(snapshot·pm·tasks·issues·assigns_deleted). `_trash`는 하위 폴더라 `glob("*.json")` 대상 아님. `_archive_log`에 `**extra` 추가(기존 archive/drop/restore 호출 무변경). ⚠️ `shutil` import 누락도 함께 수정 — 없으면 삭제 시 NameError로 터졌을 코드
- **프로젝트 데이터 21개 전량 git 커밋** — 그동안 미추적이라 과거 스냅샷 자체가 없었다
- **`aliases` 병합 지원**(`portfolio-register.py`) — 표기 변형이 카드로 매칭되는 근거라 재등록 시 함께 복원되어야 함

### 기능 추가
- **외부 파트너** `partners[]`: name·email **필수(fail로 중단, 경고 아님)**. 연락처 없는 파트너는 인수인계 시 추적 불가. 이메일 중복·형식 검증, 사내 명부 이름이면 members로 옮기라 경고. `partners` 이름은 `tasks.owner`로 인정. CLI `--partner "이름=이메일=소속=역할"`. 화면 폼(`meta-partners`)·`parsePartnersInput()`도 동일 기준
  - `/api/project/save`가 통째 덮어쓰기라 폼이 모르는 `partners`가 저장 한 번에 소실되던 함정 차단(기존 값 보존)
- **아카이브 '중단·무산'(`kind=dropped`)**: 완료 조건(납품·정산) 대신 **중단 사유 귀속(client/internal/external) + 상세** 강제. `BRIEF_STATES`에 `Dropped` 추가(Hold=보류와 구분), `DROP_CAUSES` 신설. 카드에 ⛔ 배지·사유·정산 잔여 표시. 마시로우가 첫 실사용(11:16, external)
- **카드 UI**: `desc` 없으면 `brief.summary` 폴백(21개 중 13개가 "설명 없음"이었다, 4줄 클램프) / 액션 배지 3개가 같은 좌표 절대배치라 겹치던 것 → `pc-foot` 문서 흐름 + `margin-top:auto`(Playwright 실측 12/21 카드 11.5px 겹침 → 0px) / 파트너 줄 추가
- **문서 시뮬레이터**: `⬇ HTML(편집 가능)` — 내려받는 HTML에 편집 툴바를 심어 브라우저에서 바로 수정·재저장. 재업로드는 제외(오리진 서빙 시 stored XSS, sanitizer·CSP·sandbox 전무)

### 운영 조치
- 브리프 빈 카드 15건 → PM별 1통 텔레그램 발송(전제훈4·윤혜정4·최원석5·배성원2, 중기팝업은 개별 선발송). 카드별 결손 항목·등록 업무수 명시 + "끝난 건이면 아카이브" 선택지

### 커밋
`3d76615`(삭제 감사) · `2619342`(데이터 전량) · `7d161ca`(별칭+재등록) · `fc33930`(사업 정의 보완) · `1e8b2e5`(중단 아카이브) · `74c562e`(편집 HTML) · `66b7014`(카드 겹침) · `e7fdf91`(외부 파트너)

## 2026-07-26 — RAPID 라이브 대표창 노출 + 프로젝트 주간 써머리 (배포 완료)

**① RAPID 라이브 대표창** (`dashboard-server.py` exec-attn): 두 decision 소스(open_decisions·브리프 decision_summary)에 recommender/decider 부착 → 프론트 카드에 "결정권한: 추천 A → 결정 B". **결정권자 미상 시 프로젝트 PM 폴백**(`_decision_pm`), 추론임을 "(PM)" 마커로 표시. 커밋 454968d·abb7933. scp+kickstart 재기동(HTTP 200).

**② 프로젝트 주간 써머리** (`weekly-report-aggregate.py`): `aggregate_project()` 신설 — 프로젝트별 6섹션(금주처리/예정대비[완료·미완]/차주예정/리스크/의사결정구조 RAPID+PM폴백/주요변동 status-log). 소스 재사용(assignments·주간브리프 risk·decision·decisions.jsonl·status-log). `_project_section` 렌더+CSS, 간트 아래 배치, 팀 스코프 필터. `week_range "this"` 추가. 커밋 eacf2c6.
- 실데이터 검증(읽기전용): 이번주 10개 프로젝트 활동, "중기 팝업스토어" 결정에 "추천 김도영 → 배성원(PM)" 확인.
- **자동화**: 새 launchd `com.projectrent.weekly-project`(토 09:30 `--week this`) 부트스트랩 — 금주 마감 회고를 토 10시 전 생성. 기존 월 08:30(지난주 회고)은 유지, 동일 ISO주라 충돌 없음.
- ⚠️ 첫 자동 출력은 다음 토요일. 오늘 즉시 보려면 수동 실행 필요(단 update_assignment_status_in_sheet 시트 동기화 부작용 있음 → --no-telegram 권장).

## 2026-07-25 — v1.1 평일 실데이터 검증 (가설 헤드라인·RAPID 실동작 확인)

engine_d에 실제와 유사한 보고 블록 3건(결정+승인권자 명시·리스크·질문) 투입해 맥미니 venv311로 실호출:
- **가설 헤드라인** 정상: "김도영의 섬 팝업 파도안 확정 필요 + 박서준 OECD 예산 지연 시 11월 일정 영향" — 결정·리스크 우선·고유명사 포함(요약 아닌 판단대상). *다만 날카로운 단일 가설보다 복합 종합에 가까움 — 프롬프트 추가 조임은 선택.*
- **RAPID** 정상: decision에 추천=김도영, **결정=대표**(LLM이 "대표님이 정해주셔야"에서 결정권자 추론). 근거 없으면 공란.
- **정렬** decision→risk→growth (CAT_ORDER 준수).
- carried 검증(7/22 재생성): 추천자=source_employee 자동 채움 확인.
⚠️ 검증 중 7/22 브리프(untracked 생성물)를 재생성으로 덮어씀 — 원본 보고가 시트 윈도우 만료로 복구 불가(파생물이라 영향 작음, 기록원본은 시트/decisions.jsonl). **교훈: 과거 날짜 브리프 재생성 금지.**

**헤드라인 A/B 검증(A현재 vs B단일가설 vs C하이브리드, 3시나리오×반복):** 후보들이 현재를 못 이김 → **프롬프트 변경 안 함(현 배포본 유지).** 이유: 지배 이슈 1개면 현재도 날카로운 단일 가설 산출(S2 후보와 동일), 진짜 중요한 게 2~3건이면 복합 요약이 오히려 안정·정보량 우위. 후보는 맥락 버리거나(B)·우선순위 헛짚거나(C2 S1)·몰림신호 상실(C2 S3). *재실험 불필요.*

**미반영 갭(다음 세션):** RAPID(recommender/decider)가 정적 브리프HTML(_item_card)엔 표시되나 **라이브 대표창(dashboard-server.py)엔 미렌더** — dashboard-server의 decision 렌더에 "추천 A → 결정 B" 추가 필요. 가설 헤드라인은 headline 필드라 대표창 자동 반영됨.

## 2026-07-25 — 정보 기준 v1.1: 가설 헤드라인(Day-1) + 결정권한(RAPID)

가설 주도(headline을 반증가능한 주장으로) + RAPID(decision에 recommender/decider) 채택. 프롬프트·정규화·carried·project_cards·_item_card 관통. 기준서 v1.1 §6에 검토 방법론 전체 채택/보류 기록(이슈트리·Driver·5Whys·7S는 제자리 보류). 커밋 d61061b, 맥미니 배포 완료.

## 2026-07-25 — 정보 취합·분류 기준 정립(맥킨지 × 6-Layer) + 결정론적 정렬 반영

문제: Engine D가 7범주 분류까지는 하나 범주 내부 우선순위·상위 종합이 비어 `items`가 "LLM 응답=시트 행 순서"로 나열. 정렬은 대표창 렌더링(`_prio_rank` view-zone)에서만 부분 적용 → JSON 소비자(팀 브리프·개인 카드·API)는 미정렬.

기준 정의: `arisa-info-classification-criteria-v1.md`/`.html` 신설. 맥킨지 6종(MECE·Pyramid·Impact×Urgency·80/20·SCQA/So What·Ghost Deck) × Reporting OS **6-Layer 확장 매핑**. "취합=정렬완료" 원칙. 분류축 SSOT는 `26-reporting-os` 6-Layer, 정렬 구현 SSOT는 `sort_items`.

코드 반영(`daily-brief-aggregate.py`):
1. **`sort_items()` 신설** — 결정론적 키 `(CAT_ORDER, URG_RANK, _prio_rank, -age_days)`. 기존 상수·함수 재사용, stable sort로 동률은 원순서 유지(내용 무손실).
2. **적용** — `build_brief_data`(carried 이월 직후)·`build_team_brief_data`에서 정렬 → `brief/*.json`이 소스부터 정렬, 모든 소비자 공유.
3. **BRIEF_PROMPT 보강** — items 우선순위 반환 지시 + headline=Governing Thought 명확화(보조, 신뢰는 정렬에).
4. **weekly `_open_decisions`** — 미해결 결정 impact 순(결재·금전>기한>기타) 정렬 후 top5.

검증: 실데이터+합성 케이스로 범주 단조증가·urgency/impact/age 정렬·무손실 확인. weekly 정렬 확인. **맥미니 미배포**(워크스페이스 반영까지, 배포는 별도).

## 2026-07-22 — 김준호 보고 누락 진단 + 봇 의도 감지 개선

김준호 22일간 보고 0건(메타시트 6/30 1건뿐). 원인: /report 없이 텍스트 직접 전송 → 플로우 밖이라 시트 미저장. 조치:
1. 직원봇으로 /report 사용법 텔레그램 안내 발송
2. **receive_inquiry fallback에 업무보고 의도 감지** 추가 (daily-report-bot.py): `_REPORT_INTENT_RE` 키워드 2개+ 또는 3줄+ → "보고로 저장되지 않았습니다, /report로 시작하세요" 자동 안내 + 대표에게 감지 알림. 보고 의도 아닌 일반 문의는 기존 동작 유지. 맥미니 scp→py_compile→kickstart 배포 완료(v2 started 13:53).

## 2026-07-20 — 아침 9시 이전 보고 = 전날 귀속 + 09:05 당일 재취합 (맥미니 배포 완료)

대표 지시: "각 요일 아침 9시 이전까지는 전날 자료로 추가 취합". 2단 구현:
1. **날짜 귀속(봇)**: finalize_and_send에서 제출 시각 <09:00이면 report.date=전날 — 자정 넘긴 늦은 보고가 다음날로 밀려 브리프에서 하루 늦게 잡히던 문제 해소 (7/12 stale-session fix의 정책 확장, 로그에 제출 시각 기록)
2. **09:05 당일 재취합 배치**: `com.projectrent.daily-brief-late.plist` 신규 — 매일 09:05 `daily-brief-aggregate.py --no-telegram --no-late-check` 실행해 당일 브리프 HTML/JSON을 시트 최신 상태로 재생성 (07:30 발송분과 별개, 텔레그램 재발송 없음). 07:30~09:00 사이 제출분까지 같은 날 아침 브리프에 포함
- 기존 G6(다음날 지각 재집계)은 그대로 — 09:05 이후 제출되는 진짜 지각분 커버
- 검증: py_compile·봇 재기동(Application started)·plist bootstrap 등록(exit 0)

## 2026-07-20 — 대표 브리프 카드 과축약 해소: 압축 완화 + 원문 펼쳐보기 (맥미니 배포 완료)

카드가 "8일째 미결"처럼 대상이 사라질 정도로 축약돼 상황 파악 불가하던 문제 (daily-brief-aggregate.py):
- **BRIEF_PROMPT 압축 규칙 신설**: detail을 2~4문장(배경→현재 상태(수치·날짜)→필요 액션)으로, 고유명사·수치·기한 생략 금지, "원문이 복잡하면 충분히 길게 — 길이보다 이해 우선". title도 고유명사·핵심 수치 포함 지시
- **카드 하부 "📄 보고 원문 보기" 접기**: `_card_source_html` 신설 — 카드의 source_employee를 brief JSON `people[]`에 매칭해 당일 정리 보고 전체(핵심업무 업무/산출물/이슈/의미/상세 + 메타 블로커/결정/지원/질문 + **basket 결재·매출**) 렌더. 카드 project와 일치하는 업무 블록 상단 정렬, 매칭 실패 시 생략. `.ic-src` CSS(▸/▾ 접기, 좌보더 블록)
- 검증: 렌더 단위테스트 3종 + **7/16 실데이터 재생성 e2e**(detail 104자·양은정 결정 카드에 원문 블록 부착 확인) → 검증용 재생성분은 원본 복원 (내일 07:30 cron부터 새 포맷 적용)
- ⚠️ 운영 지식 확보: 수동 재생성은 **`.venv311/bin/python`**(system python3엔 openai 없음 → engine_d 빈 결과) + gws PATH 선주입 필수. 7/17·7/18은 실제 보고 0건(수집 정상)이라 이월 결정만 표시된 것
- 범위 외: 텔레그램 발송본은 현행 유지 (HTML 브리프만)

## 2026-07-20 — 주간분장 타팀 리더 이관 (맥미니 배포 완료)

분장 등록 편집기에서 리더의 담당자 후보가 자기 팀원만이던 것을 **자기 팀원 + 타팀 리더(이관)**로 확장 — 대표→리더→팀원 위계에 "리더→타팀 리더→그 팀원" 경로 추가. 이관받은 항목은 그 리더의 팀 스코프로 기록돼 팀 홈에 잡히고, 재분장은 기존 기능 그대로.

- `/api/assignees` 리더 분기: 타팀 리더를 `leader:true` 플래그로 후보 추가 (본인·중복 제외)
- `/api/assign-commit`·`/api/assign` 검증: "자기 팀원 또는 타팀 리더(이관)" — 타팀 일반 팀원은 여전히 차단. `/api/assign-edit`는 기존(명부 확인만) 유지
- 프론트 `mwAsOpts`: 리더 후보 라벨 "(팀명 리더 · 이관)" — 일괄 담당자 드롭다운 자동 반영
- 검증: py_compile → 배포(백업 .bak-handover) → 8780 200 → **API 실검증**(윤혜정: 팀원 5+리더 2, 전제훈: 팀원 3+리더 2, leader 플래그 정상) + 검증 조건식 7케이스 시뮬레이션 전체 통과(타팀 팀원 차단 유지 포함). 쓰기 e2e는 리더 PIN 필요해 실사용에서 확인
- **받은 업무 출처 표시 (같은 날 후속)**: 주간분장 시트 **L열 '등록자'** 신설(_assign_append 12번째 원소, L1 헤더 기록 완료) + _assign_read A2:L 확장(`by` 필드) + lead-home이 출처 라벨 `src` 계산(공란·대표=대표 지시 / 본인=본인 등록 / 리더=`OOO 리더 이관`) + 받은 업무 카드가 src 표시. 과거 행(L 공란)은 종전 "대표 지시" 표기 유지
- **🐛 부수 발견·수정**: 맥미니 shared/status.py가 구버전(is_overdue·overdue_days 누락)이라 **lead-home API가 500으로 이미 깨져 있었음** — 로컬 최신본(순수 추가 2함수) 배포로 복구. shared 나머지 11모듈은 해시 일치 확인. 교훈: dashboard-server 배포 시 shared/ 동반 해시 체크
- 후속 후보: 이관 시 리더 텔레그램 DM 알림

## 2026-07-20 — 보고 채점 갭 해소: 유형별 이원 루브릭 + grace/strict 2모드 (맥미니 배포 완료)

**문제**: 같은 일일보고가 시뮬레이터 100점 vs 텔레그램 봇 60점. 원인 3중 — ①텔레그램 플로우가 decision(20)·support(10)를 안 물어 구조적 -30점 ②봇 SCORE_PROMPT만 감점 규칙 강행(시뮬레이터는 루브릭 표만) ③모델 상이(4o-mini vs 4o).

**설계 (사용자 결정)**: 봇 기준 통일 + 유예기간 순화 / **보고 유형 이원화** — 진행공유(A)·이슈(B)·의사결정(C)별 가중치 분리 (A·B는 decision 미채점 → 채널 간 구조 갭 자체가 소멸).

- **`shared/report_score.py` 신설 (채점 SSOT)**: TYPE_WEIGHTS(A: ctx25/obj15/ev20/pri25/risk15 · B: +risk25/sup15 · C: decision30 포함 7항목, 각 합 100) + `GRACE_END=2026-10-20`(순화→엄격 자동 전환, 한 줄 조정) + CLASSIFY_RULES + RUBRIC_RULES_STRICT/GRACE(순화: 모호표현 60% 하한·risk 조건부 80% 상한·사실/해석 80% 하한) + `build_prompt(mode)` + `validate_scores`(int형·dict형 겸용 클램프, mode/weights 스탬프)
- **봇(daily-report-bot.py)**: SCORE_PROMPT 상수 → 공유 코어+봇 출력블록 조립(`_score_prompt()`), rubric_evaluate → validate_scores 위임, _rule_based_score 폴백도 유형 추정(C>B>A)+유형 가중치, gaps 우선순위 유형별(A: evidence→context/objective→priority / B: risk→support→evidence / C: decision→risk→evidence), score_detail JSON에 mode·weights 추가
- **시뮬레이터(dashboard-server.py)**: SIMULATOR_DAILY_PROMPT → 공유 코어+교육 출력블록(`_sim_daily_prompt()`, 안티패턴 7종 "감지 시 반드시 감점 반영" 연동), review 채점을 gpt-4o-mini temp0.3 고정(`_call_llm_json`에 openai_model/openai_only 추가, draft는 현행 유지), 결과 validate_scores+등급 재계산, UI에 유형 배지+순화 기준 배지
- **캘리브레이션 (`report-score-calibrate.py` 신설)**: 동일 내용 6샘플(A/B/C×우수/미흡)×3회×2채널 36회 채점 — **전체 합격**: 채널 갭 최대 6.7점(기준 ±10), 유형 분류 100% 일치, 변별력 유지(우수 93~100 vs 미흡 25~50). 출력블록은 소스에서 런타임 추출(SSOT 복붙 방지)
- **문서**: 정의 v1 md에 §7-1(유형별 가중치 표·2모드·모델·캘리브레이션 결과) 추가
- **배포**: 백업(/tmp/*.bak-scoregap) → scp 4파일 → py_compile OK → dashboard·daily-report-bot kickstart → 8780 200 + **실 API E2E**(decision 위주 입력 → Type C·grace·클램프 채점 확인)
- 유의: dashboard-server.py 로컬≠맥미니 4줄(HR 링크)이었음 → 맥미니본 역동기화 후 작업 (표준 패턴 재확인)
- **strict 전환 시 의사결정 질문 규칙 (같은 날 추가, 사용자 지시)**: 보고 본문에 결정 단서어(결정이 필요·의사결정·컨펌·승인·정해주·결재 등, `report_score.DECISION_CUE_RE`)가 있으면 존재 질문 대신 **구체화 질문**("무엇을 결정해야 하는지 옵션·기한과 함께"), 없으면 기존 존재 질문("정해줘야 할 것 있나요? 없으면 '없음'"). `current_mode()==strict` 게이트로 10/21 자동 활성 — grace 기간엔 기존 동작 그대로. 맥미니 재배포·기동 확인 완료
- **후속**: 지원(support) 질문 단계는 strict 전환 시점에 재검토 / 가중치 수치는 주간 대시보드 점수 분포 2~4주 관찰 후 튜닝 / 직원 공지문 별도

## 2026-07-18 — 노션 PM 시스템 갭 분석

- **리포트**: `notion-pm-gap-analysis-2026-07-18.html` — 노션 공식 문서(help/relations-and-rollups·views·projects-and-tasks·tasks-and-dependencies·sprints·database-automations·autofill) 리서치 → 효율 원리 7개 추출 → ARISA 실측 대조(프로젝트 JSON SSOT·분장 시트·브리프·decisions.jsonl 기준)
- **핵심 결론**: ARISA는 입력의 지능(LLM 코칭·결정 구조화)은 노션 우위, 데이터의 구조(명시적 Relation·자동 롤업·상태 표준) 층이 얇음. 프로젝트↔보고↔분장 연결이 `_match_project` 토큰 매칭 휴리스틱에 의존하는 것이 최대 리스크
- **갭 9건**: HIGH — G1 프로젝트 ID Relation(토큰매칭 탈피), G2 상태·우선순위 표준 enum(영문/한글 혼재 해소), G3 진행률 자동 롤업(완료 태스크 비율→프로젝트 progress) / MEDIUM — G4 타임라인 뷰, G5 상태 변경 이력(audit log), G6 이월 자동화(지각제출 사각지대 포함) / LOW — G7 태스크 히스토리 뷰, G8 칸반, G9 의존성(보류 권고)
- **이식 금지 4건**: 입력은 텔레그램 대화 유지(폼 강요 금지), 뷰 무한 증식 금지(역할별 고정 뷰 유지), Sub-task 계층 대신 프로젝트 그룹핑 유지, 자동화는 알림 추가보다 기록(로그) 우선
- **논의 지점 4개**: Q1 Phase1 묶음 vs G2 선행 / Q2 보고 시 프로젝트 확인 질문 마찰 허용 여부 / Q3 타임라인 1차 대상(대표 vs 리더) / Q4 이력 로그 범위(분장만 vs 프로젝트·결정 포함)
- **논의 결과 (2026-07-18)**: **G2(상태·우선순위 표준 enum)만 먼저 진행** — 리스크 분산 목적(무체감 내부 구조부터). G1·G3는 G2 완료 후 별도 진행

### G2 구현 완료 — shared/status.py 단일출처 (로컬, 미커밋·미배포)
- **방식 = A안(값 무변경)**: 시트 한글값(미착수/진행중/완료/승인/삭제·일반/긴급)·JSON 영문값(Not Started/In Progress/Done) 그대로 — 흩어진 판정 튜플·매핑·뱃지 클래스만 `shared/status.py`로 이동. 어휘 변경(보류·P0/P1/P2 등)은 이후 이 파일만 수정하면 됨
- **shared/status.py 신설**: ASSIGN_STATES/DONE/HIDDEN/OPEN/CLOSED, PRIORITIES, TASK_STATES/DONE("Done","완료" 혼재 보존), BRIEF_STATES, ASSIGN_TO_TASK/PROGRESS 매핑, 뱃지 클래스 + norm_assign_status/norm_priority/badge_class 등 헬퍼
- **소비자 전환 3파일**: dashboard-server.py(_ASSIGN_* 5상수 → _ST 참조, /api/assign-status 화이트리스트, brief LLM 프롬프트 상태목록, 시트 읽기 기본값) / daily-brief-aggregate.py(CLOSED·OPEN 판정, 뱃지 dict 2곳, 읽기 기본값) / weekly-report-aggregate.py(DONE 판정 2곳, 미착수 역기입 생략, 읽기 기본값)
- **검증**: py_compile 4파일 OK + 구 하드코딩 값과 1:1 동작보존 assert 전체 통과 + 애그리게이터 2종 임포트 스모크 OK. 잔존 하드코딩 grep = shared/status.py에만 존재
- **커밋·배포 완료 (2026-07-18)**: 커밋 1cfa9a6(G2 코드 4파일)+fed6007(리포트·프로그레스) — daily-report-bot.py 타 세션 수정분은 제외 유지
  - 맥미니 배포: 베이스 해시 3파일 일치 확인 → 백업(/tmp/*.bak-g2) → scp 4파일(shared/status.py 동반) → py_compile(Python 3.9.6) OK → dashboard kickstart 재시작(PID 23682)
  - 검증: localhost:8780 → 200, arisa-os.com·/brief → 200, 배포본 해시 = 커밋본 해시 일치
  - 접속 참고: LAN(192.168.219.249) ssh 타임아웃 → **macmini-ts(Tailscale)로 성공**

### G3 구현·배포 완료 — 진행률 자동 롤업 (커밋 958349a)
- **shared/status.py `task_rollup(tasks)`**: 노션 'Task completion percent' 방식 — 저장하지 않고 파생 계산. {total, done, percent}. 산식 = 상세 화면 기존 클라 롤업과 동일(Done=100, 그 외 progress 0~100 클램프 평균) → 목록·상세 수치 일치
- **표면 배선**: `/api/projects` 각 프로젝트에 `rollup` 필드 / 리더 팀 홈 projs에 `percent` 추가(기존 task_done/total 유지) + JS 표시 `업무 3/5 · 60%` / 포트폴리오 목록 카드(pfCard)에 `업무 done/total · pct%` + 청보라 진행 바(.pc-prog) — **원형+생성본 동시 패치**(pfRollup: 서버 rollup 우선, 없으면 동일 산식 JS 폴백)
- **주의**: 원형 pfCard가 생성본보다 1줄 뒤처짐 발견(본인 PM 삭제 권한 — 생성본에만 존재). 이번엔 공통부만 패치, 원형 역동기화는 별도
- **검증**: 단위 assert(빈/None/혼재 status/불량 progress/150 클램프) + 실데이터 5건 + Playwright 양쪽 HTML pfRollup·pfCard 렌더(53%·1/2·50%·pc-prog, 콘솔에러 0)
- **배포**: 베이스 해시 4파일 일치 → 백업(/tmp/*.bak-g3) → scp 4파일 → py_compile OK → kickstart 재시작 → 8780·/projects·arisa-os.com 전부 200, 맥미니 task_rollup 실행 확인, 배포본=커밋본 해시 일치
- 남은 G3 후속 후보: 대표 브리프 우선파악존 프로젝트 블록에 진행률 표기(브리프는 현재 프로젝트 JSON 미참조 — 별도 결정)

### G1a 구현·배포 완료 — 분장↔프로젝트 ID Relation (커밋 8fae53c)
- **범위 분할**: daily-report-bot.py에 타 세션 Wave3 미커밋(+19줄) 존재 → 봇을 건드리지 않는 **G1a(분장↔프로젝트)만** 진행. **G1b(보고 시 프로젝트 확인 질문)는 봇 Wave3 정리 후 별도**
- **설계**: 주간분장 시트 **K열 = 프로젝트ID** 신설(헤더 '프로젝트ID' 기록 완료). 등록 시 `_resolve_pid`로 1회 매칭 확정 → K 저장, 소비는 `_find_project_for_assign`(pid 우선 → 이름 토큰 매칭 폴백). 기존 행은 pid 빈값 → 폴백으로 동작 불변(백필 없이 안전)
- **배선(dashboard-server.py)**: _assign_read A2:K / _assign_append 11값 / 승인·삭제 포트폴리오 반영 pid 우선 / 프로젝트 상세 분장 섹션 pid 일치 우선 / 인라인 편집 시 프로젝트 변경하면 K 재확정(제거는 편집 전 구 pid 사용)
- **안전성**: 기존 쓰기 경로가 전부 셀 단위(B/E/F/H)라 K열 보존 확인. 검증: 실데이터 21프로젝트 — resolve/pid우선/이름폴백/깨진pid폴백 assert 전체 통과
- **배포**: 베이스 해시 일치 → 백업(/tmp/dashboard-server.py.bak-g1a) → scp → py_compile → 재시작 → 8780·/projects 200, 해시 일치. K1 헤더는 맥미니 shared.gws로 1회 기록(⚠️ node PATH: `~/.local/node-v24.18.0-darwin-arm64/bin` 추가 필요했음)
- [x] **기존 행 K열 백필 완료 (2026-07-18)**: 드라이런→적용 2단계, 95행 중 87건 백필·8건 프로젝트명 없음(빈값 유지)·매칭 실패 0
  - 실패 2건(LA문화원·유니원) 원인 = 맥미니 프로젝트 실명 'LA 한국문화원 글로벌 K-존'과 표기 상이 → **aliases ["LA문화원","유니원"] 추가**(백업 /tmp/la-kzone.json.bak-g1a)로 해소. ⚠️ 유니원=글로벌 K-존 입찰 건으로 동일 프로젝트 판단 — 별개 프로젝트면 aliases에서 제거할 것
  - 검증: _assign_read 95행 중 pid 87 / K-존 프로젝트 상세 분장 섹션이 pid로 실매칭 / 서버 200. 스크립트 /tmp/backfill-assign-pid.py(로컬·맥미니)
- [ ] G1b: 보고 봇 프로젝트 확인 질문(버튼 1탭) — Wave3 정리 후

### G4·G5·G6 구현·배포 완료 — MEDIUM 갭 일괄 (커밋 43960f1)
- **G5 상태 변경 이력**: `shared/status_log.py` — 분장 상태 전이 append-only JSONL(`23-arisa/status-log/assign-status.jsonl`, ts/source/by/row/date/project/pid/task/assignee/from/to). 전이 5지점 배선: dashboard(/api/assign-status·일괄삭제·프로젝트삭제) + daily-brief(보고 기반 자동완료, completed에 from·pid 추가) + weekly(키워드 자동매칭). 로깅 실패 무해(try/except+더미 폴백). 첫 줄 = source=deploy-check 테스트 엔트리
- **G6 지각 제출 재집계**: daily-brief 배치 말미 `_late_resubmission_check` — 직전 브리프(JSON glob)의 소스일을 fetch_day로 재집계, 보고인원 증가 시 해당 브리프 subprocess 재생성(`--no-telegram --no-late-check` 재귀 방지). "배치 후 지각 제출 영구 미반영" 사각지대(7/8 정예은 건) 해소. 수동 `--source` 지정 브리프는 prev_bizday_range 기준으로 재계산되는 한계 있음
- **G4 타임라인 뷰**: 포트폴리오 목록 [카드|타임라인] 토글(localStorage 기억) — 전 프로젝트 가로 막대(시작~종료/D-Day 폴백), 진행률 채움(pfRollup 재사용), 월 눈금, 오늘선, 마감 경과+미완 100% 미만 = 빨간 테두리(지연). 원형+생성본 동시 패치
- **부가**: daily-brief fetch_assignments A2:K 확장(pid 포함 — G1 정합)
- **검증**: py_compile 4파일 / G5 임시경로 기록 assert / G6 prev_bizday_range 월요일 회귀 / Playwright 타임라인(막대2·지연1·눈금4·오늘선·토글 왕복, 콘솔에러 0) 양쪽 HTML
- **배포**: 베이스 해시 5파일 일치 → 백업(/tmp/*.bak-g456) → 6파일 scp → py_compile → 재시작 → 8780·/projects·arisa-os.com 200, 맥미니 status_log 실기록 확인
- 실전 검증 예정: 내일 07:30 배치(G6 지각체크 출력 + G5 자동완료 로그), 월요일 주간 배치(G5 weekly-auto)

### G7·G8 구현·배포 완료 — LOW 갭 (커밋 d4438f3)
- **G7 태스크 이력 스레드**: status_log에 `note`(전이 근거, 200자)+`load_history`(task/assignee/pid AND 필터, 파일 역순=최신순 — ts 동초 정렬 함정 회피) → `/api/assign-history`(GET, 로그인 사용자 전체 — 팀 투명성) → 포트폴리오 상세 분장 섹션 각 행 🕘 토글 → 인라인 스레드(시각·from→to·주체·소스·자동완료 시 보고근거 문장). daily-brief 자동완료가 note=basis 기록
- **G8 칸반 뷰**: 포트폴리오 3번째 뷰 [카드|타임라인|칸반] — brief.status(컨디션) 컬럼(BRIEF_STATES 순서, 존재 컬럼만+미지정), 미니 카드(PM·D-day·업무 done/total·롤업 진행바), 클릭→상세. 드래그 상태 변경은 미구현(권한 로직 필요 — 필요 시 후속). 원형+생성본 동시 패치
- **검증**: load_history 단위 assert / Playwright 칸반(컬럼 정렬·카드3·토글 복귀)+이력(2행·note·source·최신순, http 서빙+API 목킹) / 맥미니 실 API 조회(deploy-check 엔트리 반환 — ⚠️ curl 한글 파라미터는 --data-urlencode 필요, 브라우저는 무관)
- **배포**: 베이스 5파일 일치 → 백업(/tmp/*.bak-g78) → scp → py_compile → 재시작 → 8780·arisa-os.com·/projects 200
- **갭 로드맵 종결**: G1a·G2~G8 완료. 잔여 = G1b(봇 Wave3 후) · G9 의존성(도입 비권고 유지)

### Wave 3 정리 + G1b 구현·배포 완료 (커밋 9e538e8·fc57a4a)
- **Wave 3 정리 커밋(9e538e8)**: 타 세션 미커밋 +19줄(_rule_based_gaps — Outcome 한 줄 강제 + decision_needed 공란 유도 질문) 검토 후 정리 커밋. 질문 상한·우선순위(G8) 체계 안에서 동작 확인
- **⚠️ 발견 1**: 맥미니 봇 = a27954e 시점 — **핫픽스 1b902c5(질문에 프로젝트·업무명 명시 강제)가 미배포였음** → 이번 HEAD 배포로 해소
- **⚠️ 발견 2(미해결 버그)**: 봇 `/assign`(대표 전용 간편 분장)이 **구스키마**(W라벨|팀|...|bot)로 주간분장 시트에 append — 현 신스키마(날짜|프로젝트|...|우선순위|pid)와 컬럼 불일치 = 잘못된 칸에 기록됨. 셸 분장 UI가 주 경로라 노출 낮지만 수리 필요 — 후속 항목
- **G1b(fc57a4a) — 보고↔프로젝트 ID Relation**: structure_report에서 프로젝트 SSOT 레지스트리(`_data/projects/*.json` 이름+별칭) 로드 → STRUCTURE_PROMPT `projects` 배열(core_tasks 순서, **목록에서만 선택·추측 금지**) → `_project_pid` 정규화 정확 매칭(이름+aliases)으로 pid 확정 → 핵심업무 시트 **후행 컬럼 N(project)·O(pid)** 축적(기존 행·dedup 인덱스 무영향) + 관리자 보고서 업무 라인 〔프로젝트〕 태그. **확인 버튼 질문은 미도입** — 목록 강제 선택으로 모호성 낮춰 무대화 자동 귀속, 오귀속 관찰 후 버튼 도입 판단
- **검증**: 로컬 단위 assert(레지스트리 21, 정규화/변형/미존재 매칭, 시트 15컬럼 조립, 〔태그〕, 프롬프트 스키마) + 맥미니 venv py_compile + 레지스트리 25개·별칭 매칭(LA문화원/유니원→K-존) 실검증
- **배포**: 봇 유휴(폴링만) 확인 → 백업(/tmp/daily-report-bot.py.bak-wave3-g1b) → scp → venv py_compile → kickstart(PID 24607, Application started) → 배포본=커밋본 해시 일치
- 실전 검증 예정: 다음 보고(오늘 저녁/주말)에서 ① Wave3 질문(outcome·결정 유도) 빈도 ② projects 귀속 정확도 — 핵심업무 시트 N·O열 확인
- [x] **후속 2건 완료 (커밋 4f1386c, 맥미니 배포·봇 재시작 PID 26363)**
  - 봇 /assign 신스키마 전환: 구스키마(W라벨…) append 버그 수정 → 신스키마 11컬럼(+pid), ASSIGN_PARSE_PROMPT에 project 추출 추가, 우선순위 표준화(최우선→긴급, 참고 폐기 → 긴급|일반), 파싱 결과에 프로젝트 표기
  - 브리프 귀속 소비: fetch_day 핵심업무 A2:O(N=project·O=pid) → _emp_block에 '프로젝트=' 제공 + BRIEF_PROMPT "확정 귀속 그대로 사용(추측 재귀속 금지)" 규칙 — f89b06c 오인 방지의 완결
  - 핵심업무 탭 N1·O1 헤더("프로젝트"/"프로젝트ID") 기록 완료. 검증: /assign 행 모킹 assert + _emp_block·프롬프트 assert + venv py_compile + 봇 Application started

## 2026-07-15 — 정식 도메인 확인 + 갱신 리마인드 체계

- **정식 도메인 재확인**: `https://arisa-os.com` (2026-07-12 개통). 보조 `arisa.projectrent.co.kr`(ingress 유지), tailnet 전용 `server-mini-macmini.tail7739de.ts.net`
- **도메인 갱신 주간 리마인드 트리거 2종 구축** (만료 1달 전부터 매주):
  - 주간 리마인드 `trig_01WfYyTtAqGp1TjreK1g743d`: cron `0 9 * 6,7 1` (6~7월 매주 월 09시) → 새 세션 실행 + 텔레그램(@wonseok_brain_bot)+푸시. **현재 비활성 대기**
  - 활성화 예약 `trig_013V9dGesVEGJMrcvxAYfj2R`: `run_once_at 2027-06-01` 위 트리거 자동 ON — 사용자 요청으로 2027년 6월부터 가동(올해 7월 노이즈 제거)
- ⚠️ 가비아에서 arisa-os.com 실제 만료일 확인 필요(개통 7/12 기준 추정, progress엔 "7월 초"). memory: `reference_arisa_os_domain.md`

## 2026-07-08 — "리더 공유 안 됨" 장애 조사 + 링크 정상화 착수

### 조사 결과 (리더들이 공유 안 됐다고 인식한 원인 2가지)
1. **7/5~7/7 사흘간 빈 브리프**: 타이밍 버그(7/7 수정 전)로 리더 텔레그램에 "팀 보고 없음"만 발송. 실제 콘텐츠 담긴 첫 브리프 = 7/8 아침
2. **링크 사망(현재진행형)**: 발송 링크가 구 trycloudflare quick tunnel URL → cloudflared 미가동, 응답 000. 통합 셸은 tailnet 전용인데 리더 3인은 tailnet 밖(기기 3대 전부 대표 소유)
- 텔레그램 발송 자체는 정상: 7/8 07:30 배치 4팀 모두 ✅ (공간팀→전제훈 8714627048, 사업기획→배성원 921741497, 운영·기획팀→윤혜정 8452510149 겸임)
- 7/7 보고 제출 6/10: 김예진·양지혜·김도영·배성원·양은정·윤혜정 ○ / 전제훈·김가은·김준호·정예은 ✗

### 조치 완료
- 전제훈 리더에게 직원봇 DM으로 미제출 안내 발송 (message_id 2270, 링크 교체 작업 중 맥락 포함)
- 맥미니 `.env`에 `DASHBOARD_BASE_URL=https://server-mini-macmini.tail7739de.ts.net` 추가 (잠정 — 대표 기기만 열림, 내일 아침 브리프부터 반영)
- `daily-brief-aggregate.py` 기본 URL: 죽은 trycloudflare → tailnet으로 교체 (로컬, 미커밋)
- `weekly-report-aggregate.py:830` ts.net 하드코딩 → `DASHBOARD_BASE_URL` 상수화 (체크리스트 7번 해소, 로컬, 미커밋)
- cloudflare-migration-checklist.md 맥미니 기준(8780, server-mini)으로 전면 갱신

### named tunnel 구축 완료 (2026-07-08 오후)
- [x] 도메인 projectrent.co.kr 가비아 갱신(대표) + Cloudflare 존 등록(대표, Free) + NS 변경(laura/tanner.ns.cloudflare.com — 전파 확인)
- [x] 맥미니 cloudflared 2026.6.1 설치(~/.local/bin, GitHub 바이너리 — brew 없음)
- [x] tunnel login 인증(cert.pem) → **tunnel `arisa` 생성 (UUID 312c7f9f-d19e-43d3-a041-ff8921059d22)**
- [x] `arisa.projectrent.co.kr` CNAME 라우팅 + config.yml(→localhost:8780) + launchd `com.cloudflared.arisa`(KeepAlive, 로그 /tmp/cloudflared-arisa.log) — 서울 엣지 4커넥션 등록 확인
- [x] 맥미니 .env `DASHBOARD_BASE_URL=https://arisa.projectrent.co.kr` 교체 → 내일 아침 브리프부터 이 링크로 발송
- ⚠️ 브라우저 자동화 교훈: 이 맥에서 browse 데몬은 Bash 호출 종료 시 죽음 + Chrome 쿠키에 CF 로그인 없음 + 키체인 반복 프롬프트 → CF 대시보드 UI 자동화 불가. 사용자 수동 4클릭 + cloudflared login URL 클릭 방식이 정답이었음

### 지각 제출 사각지대 발견 (2026-07-08 저녁)
- 정예은 7/7자 보고를 7/8 새벽~아침(07:30 배치 이후)에 제출 → 시트엔 정상 기록됐지만 아침 브리프 집계(6명)에서 누락. 다음날 배치는 다음 소스일만 읽으므로 **배치 이후 지각 제출은 어떤 브리프에도 영구 미반영**되는 구조
- 조치: 7/8 브리프 재생성(--source 2026-07-07 --no-telegram) → 보고인원 7명, 기획팀 항목 2건으로 수정 완료
- [ ] 개선 검토: 아침 배치 시 "전일 소스의 지각 제출분" 감지 로직 (예: 전일 브리프 보고인원 대비 시트 증가분 재생성) 또는 배치 시각 조정

### 개인별 업무 써머리 섹션 추가 (2026-07-08 밤, 커밋 25768e6)
- 브리프 하단에 "개인별 업무 써머리" — 시트 원문 그대로(LLM 미경유, fidelity): 핵심업무 ①②(Task→산출물·의미), 이슈/블로커/의사결정요청/지원요청/오늘의질문, basket 매장보고. 대표=팀별 그룹, 팀=카드 나열. `_people_summary`/`_person_card`/`_people_section` + `people` JSON 필드
- 배포: 커밋+푸시 후 맥미니는 **스크립트 2개만 `git checkout origin/main --`로 선별 배포** + 07-08 재생성 완료
- ⚠️ **맥미니 repo 분기 상태**: 로컬커밋 049fbb1 + dashboard-server.py 등 다수 로컬수정으로 merge/rebase 불가(강행 시 가동 중 대시보드 파손 위험). 당분간 스크립트 선별 checkout 배포 유지, 전체 리컨실은 별도 세션에서

### 대표 브리프 팀별 병합 + 주간분장 연동 (2026-07-08 심야, 커밋 db417f6)
- 대표 브리프 하단 = "팀별 오늘 브리프": 팀마다 headline+핵심칩(top3)+개인카드 병합 — 스코프 드롭다운 전환 불필요
- 주간분장 연동: 개인카드에 이번주 분장 항목+상태뱃지(미착수/진행중/완료), 분장만 있고 보고 없는 인원은 팀 섹션에 경고줄
- ⚠️ 주간분장 탭 실스키마 = 셸 '내 업무' AI 분장 스키마(날짜|프로젝트|팀|담당자|업무내용|일정|결과물|상태|이해관계자|우선순위) — weekly-report-aggregate.py의 fetch_assignments(W라벨)는 **구스키마라 현재 0건 매칭(고장)** → 주간 대시보드 분장 달성률 수정 필요
- 커밋 02f4f17: 개인카드에 보고원문 [상세:] 보강 + 산출물/의미 중복 제거. 6/30~7/8 7일치 맥미니 재생성 완료

### weekly 분장 달성률 복구 (커밋 692e364)
- weekly-report-aggregate.py fetch_assignments를 신스키마(날짜 기준 주간 필터)로 교체, 상태 역기입 매칭도 (날짜+업무+담당자)로 수정. W28 재생성 검증: 분장 5건, 공간팀 0/2·운영팀 0/1 게이지 복구. 맥미니 배포 완료

### 셸 계정별 브리프 뷰 완성 (커밋 6c5e8b5+8f61239, 맥미니 배포·재시작 완료)
- **단일 URL 로그인 → 직급·부서별 페이지 자동 변경**: 대표=전체 병합 브리프 / 겸임리더(윤혜정)=담당팀 병합 한 페이지(`/lead-brief?teams=`, 드롭다운 기본 '담당팀 전체') / **직원=오늘 Brief 탭 신설**(`/my-brief?name=` — 본인 카드+팀 헤드라인·핵심칩만, 동료 카드 비공개)
- 브리프 JSON 서버렌더: daily-brief-aggregate.py 카드 렌더러를 importlib(하이픈 파일명)로 재사용. ⚠️ 대시보드 서버는 launchd `com.projectrent.dashboard`가 **시스템 Python 3.9**로 구동 — 애그리게이터는 `from __future__ import annotations` 있어 임포트 OK, 재시작은 `launchctl kickstart -k gui/$(id -u)/com.projectrent.dashboard`
- **dashboard-server.py 분기 부채 청산**: 로컬본=맥미니본 동일 확인 → 운영본 커밋(6c5e8b5)으로 리컨실 완료

### 리더 홈 구축 (2026-07-09 아침, 커밋 d80fccd)
- 리더 로그인 기본 화면('내 업무'→'팀 홈' 탭명 변경): ① 팀 Todo(이번주 분장, 상태뱃지·담당자·마감) ② AI 분장 생성(기존 UI 공용화) ③ 진행중 팀 프로젝트 패널(dday·업무진행률, 클릭→프로젝트 탭) ④ 팀원 오늘 보고 카드(최신 브리프 fragment 서버렌더)
- `/api/lead-home` 신설(직원 403), 브리프 카드 CSS 셸 주입. 맥미니 배포·재시작·검증 완료
- ⚠️ 대표(admin) 계정은 리더 홈이 아닌 기존 '내 업무' — 리더 화면 미리보기는 리더 계정 필요
- **07-09 아침 정기 배치 정상**: 보고 5명, 새 포맷(팀별 병합+분장) + 고정 URL 링크로 리더 4팀 발송 확인

### '이번 주' 탭 재정의 시도 → 대표 지시로 취소 (0e533bb → revert 0cdb4f1)
- week-brief 일별 스택 + /manage 분리를 구현·배포했으나 대표가 전체 취소 지시 → git revert 후 재배포, '이번 주' 탭은 기존 주간 집계 대시보드(/weekly, /team-weekly)로 복원. 리더 홈·계정별 브리프 뷰는 유지
- 코드는 히스토리에 남아 있음(0e533bb) — 재도입 시 revert의 revert로 복구 가능

### 🎉 정식 도메인 개통 — arisa-os.com (2026-07-12)
- **projectrent.co.kr 활성화 실패 최종 결론**: 4일간 Pending. 위임·DNSSEC·whois·이메일인증·존재등록·NS왕복트릭·API activation_check 전부 시도 → 불발. 원인 추정: CF의 .kr whois 검증이 KISA 쪽에서 차단/제한 (우리 설정 문제 아님)
- **해법: Cloudflare Registrar에서 `arisa-os.com` 직접 구매(대표)** → 존 즉시 Active (12:44)
- 연결(API 토큰): 루트 `arisa-os.com`+`www` CNAME → 터널(312c7f9f, 프록시) / 맥미니 config.yml ingress 갱신(구 arisa.projectrent.co.kr도 유지) / 터널 재시작 / .env `DASHBOARD_BASE_URL=https://arisa-os.com`
- **검증: https://arisa-os.com → 200**, /brief /my-brief /lead-brief /team-brief 전부 200 — 리더·직원 공개 접근 가능. 다음 아침 브리프부터 새 링크 발송
- projectrent.co.kr 존은 파킹 유지 (활성화되면 ingress에 이미 있어 자동 보조 주소화). ⚠️ 도메인 매년 7월 초 가비아 갱신
- CF API 토큰(arisa, Zone/DNS Edit) 발급 — 추후 DNS 작업 API로 가능

- **리더 3인(전제훈·배성원·윤혜정) 새 주소 공지 발송 완료** (직원봇 DM, 화면 구성 안내 포함)

### 업무분장 프로젝트 그룹핑 (커밋 aceaf2d, 맥미니 배포 완료)
- 등록 편집기 = 프로젝트 그룹 에디터: 그룹당 프로젝트명 1회, 담당자 항목별 개별 + '일괄 담당자'(빈 칸만 채움) + 그룹별 항목추가/새 그룹
- 완료 후 리스트(직원 내 분장·리더 팀 Todo) = 프로젝트 헤더 하위 그룹 + 완전 동일 행 표시 중복 제거(시트 무변경 — 세스코 이중등록 노이즈 해소)

### 보고 시뮬레이터 AI 드래프트 비교 기능 (2026-07-13, 맥미니 배포 완료)
- **기능**: 직원이 폼을 먼저 작성 → "AI 비교 보기" 영역에 자유 텍스트 입력 → AI가 8필드(daily)/7필드(brief) 구조화 → 각 필드 옆에 비교 표시 → 선택적 "이 값으로 교체"
- **교육 철학**: 인지 증강(먼저 쓰고 비교) — 폼 1개 이상 입력 + 자유 텍스트 있을 때만 버튼 활성화
- **백엔드**: `SIMULATOR_DRAFT_PROMPT` + `POST /api/simulator/draft` (~15줄), `_call_llm_json` (Anthropic 우선 → OpenAI GPT-4o fallback)
- **프론트**: 접기 가능한 textarea + 비교 영역(보라색 배경) + 개별 교체 버튼, 모드 전환 시 자동 초기화
- **인프라**: `_call_claude` → `_call_llm_json` 리팩터, `dict | None` 타입 어노테이션 제거(Python 3.9 호환), 맥미니 `.env`에 `ANTHROPIC_API_KEY` 추가 (현재 키 만료 상태라 GPT-4o fallback으로 동작)
- **검증**: Playwright E2E — 비활성화→활성화→API 실호출→비교표시→교체→기존 리뷰 회귀 없음 전부 통과

### 브리프 최상단 우선 파악존 (커밋 939cc12, 맥미니 배포·07-12 재생성)
- 대표 브리프 맨 위 = [프로젝트 단위|팀별 단위] 토글(localStorage 기억): 진행상황+이번주 분장 할일
- 우선 정렬: 의사결정→결재·승인(키워드)→비용(키워드)→리스크→개입→보고. 프로젝트 블록=항목+할일(중복 표시 제거), 팀 블록=headline+우선항목+미보고 경고
- 기존 요약존(headline+결정카드)은 우선 파악존이 포함해 대표 브리프에서 대체 (팀 브리프는 기존 유지). project="null" 문자열 정규화(_norm_proj)

### 리더 분장 전체 반영 (커밋 b460e11, 맥미니 배포 완료)
- 팀 브리프에도 우선 파악존(프로젝트 단위 단일 뷰, 팀 스코프 분장) — 리더·대표 모두 진행 업무 확인 가능. 리더 분장 기능은 공용이라 이미 동일(팀 홈)
- /api/project + 포트폴리오 상세(원형 project-master-prototype.html + 생성본 동시 패치)에 "분장 업무(최근 2주)" 자동 섹션 — 토큰 매칭(_match_project: 정규화 포함 or 유의토큰 교집합, 일반어 스톱워드)
- ⚠️ 포트폴리오 HTML 수정 시 반드시 원형+생성본 양쪽 패치 (generate-portfolio.py 재생성 시 생성본 덮어씀)

### 분장 위계 완성 — 받은 업무 섹션 (커밋 b9a3e32, 맥미니 배포 완료)
- 위계 검토: 대표→리더(배분 후보=리더만)/리더→자기 팀원/직원=열람 — `/api/assignees`에 이미 구현되어 있었음
- 보완: 리더 팀 홈 최상단 "📥 받은 업무(대표 지시)" 섹션 분리 + [→ 팀원에게 상세 분장] 버튼(textarea 프리필) — 대표 지시→리더 상세분장→팀원 흐름의 연결 동작
- lead-home 분장 윈도우 2주로 확대 (주 바뀐 직후 미완료 소실 방지 — _project_assignments와 동일 정책)

### 대표창 지연·결재 섹션 + 플로우 구조도 (커밋 7d4d612, 맥미니 배포 완료)
- `/api/exec-attn`(admin 전용): 지연 업무(마감 경과·미완료, D+N) + 결재·확인 필요(decisions.jsonl 이월 14일 + 최신 브리프 decision_summary 병합)
- 대표 내 업무 최상단에 🧾결재·⏰지연 섹션 (0건 시 "대기 없음")
- 분장 플로우 구조도: `assignment-flow-구조도.html` (스윔레인 3단 + SSOT + 자동반영 4표면 + 권한규칙)

### 주간업무계획 업로드 → 분장 검토 초안 (커밋 c6baa6d, 맥미니 배포·E2E 검증)
- 분장 섹션(대표·리더 공용)에 "📄 주간업무계획 업로드(.xlsx)" — Dropbox 주간회의 엑셀(프로젝트명/금주/차주/계약상황/due 헤더)을 올리면 파싱→AI 항목화(max30)→프로젝트 그룹 에디터에 검토 초안 프리필 → 담당자 지정→등록
- `/api/assign-from-plan`(base64, 10MB 한도, 대표·리더 403 가드), `_parse_weekly_plan`(헤더 탐지·프로젝트명 상속·빈행 skip), openpyxl 인프로세스→venv311 subprocess 폴백
- ⚠️ 맥미니 venv311에 openpyxl 신규 설치(uv pip, 3.1.5 — venv에 pip 없음, uv 사용). 실검증: 13행→24건

### 사용 가이드 + 리더 온보딩 (커밋 2650ee0)
- 리더 3인 개별 가이드+계정 DM 발송 완료 (권한 계층이 자동발송 차단 → 대표 직접 실행 스크립트 방식, 발송 후 스크립트 삭제 안내)
- `arisa-os.com/guide-os` 사용 가이드(시작하기/역할별/분장 사용법/보고 자동반영/FAQ) + `/guide-flow`(구조도) + `/guide/template.xlsx`(주간계획 템플릿, 파서 정합 검증)
- 셸 우상단 '가이드' 링크(전 역할), 분장 업로드 UI '템플릿 받기'

### 리더 온보딩 발송 완료 (2026-07-13)
- 리더 3인: ① 개별 계정+가이드 DM ② 사용 가이드 링크 DM — 모두 대표 직접 실행 스크립트로 발송 성공 (에이전트 자동발송은 권한 계층이 일관 차단 — 앞으로 대외 발송은 스크립트 준비→대표 `!` 실행 패턴)
- ⚠️ send-leader-guide.py(PIN 포함) 아직 잔존 — **대표가 직접 삭제 필요**: `rm 20-operations/23-arisa/send-leader-guide.py`

### 남은 것
- [ ] 직원 전체 새 주소 공지 (오늘 Brief 탭 신설 안내 + /guide-os 링크 포함) — 대표가 "나중에 따로" 결정
- [ ] 주간분장 시트의 실제 중복 행 정리 여부 (표시만 제거된 상태 — 원하면 시트 정리 별도)
- [ ] 리더 실사용 피드백 수집 (분장 UI·브리프 우선파악존·가이드)
- [ ] 로컬 스크립트 수정분(daily-brief·weekly) 커밋+푸시 → 맥미니 pull (⚠️ daily-brief에 다른 세션의 Wave2 수정분 섞여 있음 — 커밋 시 확인)

## 2026-07-07 — 통합 대시보드 셸 병합 + 브리프 타이밍 근본 수정

### 통합 셸 (dashboard-server.py, 커밋 a8d61db~1358370)
- 맥미니 단일 URL `https://server-mini-macmini.tail7739de.ts.net/` = 통합 셸 (tailnet 전용, Funnel off)
- 역할별 탭: 대표 [프로젝트|Brief|이번주|Decision Window]+스코프 / 리더 3탭 / 직원 프로젝트만
- 로그인 1회 → pm_sess+brief_sess 등 프리세팅 + ARISA 2.0 토큰 자동 발급(arisa_sess/arisa_token)
- 프록시: Authorization 전달 + SPA `var API=''`→`/arisa2` 재작성, 4xx 상태 통과(401=alive)
- 계정 단일화: 대시보드 users.json → symlink → `~/dev/arisa2/data/users.json` (11명 list 스키마, load_users/set_pin 양스키마 지원)
- 포트: 맥미니 8780 / 로컬 8770. 포트폴리오에 직접 입력 생성 추가
- ⚠️ 사고: generate-portfolio.py가 맥미니 users.json 덮어씀 → 보존 가드 추가(재발 방지). 직원 PIN = arisa2 PIN으로 통일, 공지 발송 완료

### 브리프 타이밍 수정 (daily-brief-aggregate.py, 커밋 1b237d4)
- 근본 원인: 직원은 당일 저녁(20/22시 리마인드) 보고 ↔ 07:30 배치가 '오늘' 날짜를 읽어 매일 아침 0건
- 수정: 소스 = 직전 영업일~어제(`prev_bizday_range`, 월=금토일 합산), `--source` 수동 지정 가능
- 재생성 검증: 보고인원 0→6, 대표 5건·공간팀 3·운영팀 2·사업기획 2·기획팀 1
- 미제출 리마인드는 기존 가동 중(daily-report-reminder 20/22시 개별 DM + daily-checkin 22시 대표 요약) — 신규 구축 불필요
- 팀 Brief 풀데이터 시뮬레이션: brief/simulation-team-brief-{기획팀,공간팀}.html
- ⚠️ 맥미니 수동 실행 시 PATH에 `~/.npm-global/bin`(gws) + `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file` 필수

### 열린 항목
- [ ] 다른 세션에서 daily-brief-aggregate.py에 headline/decision_summary(요약존) 추가 진행 중 — 미커밋 상태로 종료됨
- [ ] 브리프 날짜 네비 7영업일 확장 반영분 맥미니 배포 여부 확인
- [ ] 리더·직원 실사용 피드백 수집 (탭 구성·PIN 변경)

## 2026-07-11 — Daily Report 2.0 고도화 Wave 1 배포

### 배경
- 대표가 "ARISA Daily Report 2.0" 정의서 공유 → 현재 봇(2.0-MVP1) 대비 갭 분석 → 설계서 작성 + Wave 1 구현·배포
- 설계서: `20-operations/23-arisa/daily-report-2.0-upgrade-design.md` (갭 G1~G10, 3-Wave 로드맵)

### Wave 1 구현 (daily-report-bot.py, 커밋 b4cb9a5)
- G1 팩트/해석 분리: SCORE_PROMPT에 분리 질문 규칙 ("직접 들은 발언인가요, 해석인가요?")
- G2 모호 표현 차단: `_VAGUE_RE` 규칙(진행 중/확인 중/거의 완료/늦어질 듯) — 산출물·이슈·블로커 검사. "~것 같다"는 오탐 방지 위해 LLM만 판단
- G3 리스크 조건부 재질문: "없음"이어도 마감 임박·회신 대기·승인/견적 미확정·일정 변경·예산 초과 단서 시 만점 금지 + 질문
- G5 다음 액션 기한 검증: `_DEADLINE_RE`+`_ABSTRACT_NEXT` — "계속 진행"류·기한 없으면 "무엇을 언제까지" 질문
- G8 피드백 우선순위: gaps 선정 = 팩트혼재 > 리스크 > 결정 > 결과 > 액션 > 지원 (문서 §7)
- 불변: 질문 최대 3개·충분하면 0개, 거울 톤, 규칙 안전망, 창작 금지, 루브릭 7항목 유지(점수 연속성)

### 배포
- 두 머신 git 이력 갈라져 있어(로컬 b4cb9a5 vs 맥미니 049fbb1) pull 대신 파일 직접 복사 방식 사용
- 베이스 해시 동일 확인(b6cb25bc) → 백업(/tmp/daily-report-bot.py.bak-wave1) → scp → 맥미니 venv py_compile OK → 진행 세션 0건 확인 → kickstart 재시작(22:08, PID 95917) 정상 기동

### 열린 항목
- [ ] Wave 1 실사용 관찰: 직원 보고에서 새 질문(모호표현·기한·팩트분리)이 과하게 나가는지 1주 모니터링
- [x] Wave 2: 보고 유형 자동분류(Type A/B/C) + 결정 요청 옵션/기한 구조 강제 + 목표(왜) 질문 → 같은 날 구현·배포 (아래)
- [ ] Wave 3: 직원별 학습 프로필(반복 오류 추적·주간 훈련 목표) + Adaptive Coaching 레벨
- [ ] 로컬↔맥미니 git 이력 분기 정리 (origin 기준 재동기화 — 별도 세션)
- [ ] `com.arisa.daily-report-reconcile` launchd 미로드 상태 — backfill 대체 여부 확인

## 2026-07-11 (심야) — Daily Report 2.0 Wave 2 배포

### 구현 (커밋 864e155: daily-report-bot.py + shared/decision.py)
- G7 보고 유형 자동분류: SCORE_PROMPT가 report_type A(일반)/B(이슈·리스크)/C(의사결정) 산출
  - 유형별 질문 상한: A=1개(경량 통과), B/C=3개 (completion_evaluate cap 분기)
  - 관리자 보고서 헤더 유형 배지(🟢/🟠/🔴), score_detail JSON에 type 기록 — 시트 스키마 불변
  - Type B는 risk 질문이 영향·원인·대응안, Type C는 decision 질문이 옵션·추천·기한·지연영향을 겨냥
- G4 결정 요청 구조: STRUCTURE_PROMPT decision에 options/recommendation/deadline/delay_impact 추가(추측 금지)
  - decisions.jsonl 엔트리에 동일 4필드 축적(shared/decision.py — 추가 필드라 기존 소비자 무해)
  - 관리자 보고서 의사결정 블록에 옵션/추천안/결정 기한/지연 시 영향 표기
- G6 업무 목표(왜): 드릴다운 안내문에 "무엇을 위한 것이었는지(목표)" 추가 + DRILLDOWN_PROMPT `goal` 추출
  - core_tasks.goal → 관리자·직원 정리본 "목표:" 표기 + 루브릭 context/objective 채점 근거
- 루브릭 8항목 전환은 보류 유지(점수 연속성) — Wave 3에서 재검토

### 배포
- 베이스 해시 2개 파일 모두 일치 확인 → 백업(/tmp/*.bak-wave2) → scp 3파일 → 맥미니 py_compile OK
- 진행 세션 0건 → kickstart 재시작 02:09 정상 기동 (PID 99638, 409 없음)

### 열린 항목
- [ ] Wave 2 실사용 관찰: Type 분류 정확도(A인데 B/C로 과분류 → 질문 과다) 1주 모니터링
- [ ] goal 필드 시트 컬럼 추가 여부 결정 (현재 메시지·raw에만 존재, 핵심업무 시트 스키마 불변 유지 중)
- [x] 대표 브리프의 decisions.jsonl 신규 4필드 표시 → Wave 2.5에서 반영 (아래). arisa2 Decision Window는 별도 후속

## 2026-07-11 (심야) — Wave 2.5: 브리프 산출물 §9 정렬 배포

### 구현 (커밋 33211d6: daily-brief-aggregate.py)
- 범주 5→7: support(지원 요청)·anomaly(이상 신호) 추가 — §9 대표 브리프 체계
  (anomaly = 활동만 나열/보고 간 충돌/업무 집중/형식적 "없음", 당일 범위·근거 필수)
- 결정 필요사항 구조(§9-3): BRIEF_PROMPT가 추천안·결정 기한·미결정 영향 추출 → 카드 표기,
  이월 결정은 decisions.jsonl 신규 4필드 표면화, 요약존 결정 카드에 ⏰기한
- 개인 카드에 보고 유형 배지(🟢/🟠/🔴)+Report Score — 시트 메타 N·O열 읽기(A2:L→A2:O)
- LLM 입력 블록에 유형·점수 제공(anomaly 판단 보조), 통계바·텔레그램에 지원·이상신호 카운트
- 호환: dashboard-server는 CAT_META.get 폴백이라 구 JSON 호환 / 모듈 캐시(_DBA) 때문에 재시작 필요

### 배포·검증
- scp → py_compile OK → dashboard 재시작(HTTP 200) → 7/11 브리프 재생성 E2E 검증
  (counts 7범주·statbar·개인 score 표기 확인. 추천안/기한은 Wave 2 이후 보고부터 채워짐)
- ⚠️ 사고·복구: ssh 세션엔 gws PATH가 없어 첫 재생성이 빈 데이터로 7/11 브리프를 덮어씀 →
  `export PATH="$HOME/.npm-global/bin:..."` 후 재생성으로 복구(소스=시트라 무손실).
  **교훈: 맥미니에서 브리프 수동 재생성 시 반드시 gws PATH 선주입**
- 로컬 git: daily-brief-aggregate.py 첫 추적 시작 (이전까지 맥미니에만 있던 운영 파일)

### 열린 항목
- [ ] 내일(7/12) 07:30 자동 브리프에서 신규 포맷 정상 생성 확인 → 7/18 검토 일정 체크리스트 3번에 포함됨
- [ ] anomaly 범주 과검출 여부 관찰 (근거 없이 생성 금지 규칙 준수 확인)
- [ ] arisa2 Decision Window에 decisions.jsonl 신규 4필드 표시 (별도 세션)

### 세션 종료 시점 확인 (7/12 02:50)
- **7/11(금) 보고 0/10 전원 미제출** — 리마인더 20:00·22:00 정상 발송, 봇 대화 0건(아카이브 로그 확인).
  Wave 1·2 새 질문 로직은 아직 실전 발화 없음 → 다음 보고(주말/월요일)에서 검증하거나
  대표 /report 테스트로 즉시 검증 가능. 금요일 전원 미제출은 팀 확인 필요(KBO 행사 추정)
- 7/18(금) 10:00 검토 캘린더 일정 등록 완료 (이벤트 bu130o7q442ilm5sv0scig90f0, 체크리스트 6개)

## 2026-07-12~15 — Daily Report 2.0 후속: 핫픽스 2건 + 실사용 검증

### 핫픽스 (모두 맥미니 배포·재시작 완료)
- **stale-session 날짜 오염** (커밋 f5ef19b): pickle 부활 세션이 과거 날짜로 저장돼 브리프 영구 누락
  → finalize 시 date=제출일 갱신. **7/15 김가은 보고에서 실제 발동 확인** (7/14→7/15 교정) ✅
- **진행 중 세션에서 /report 무반응** (커밋 a27954e): 상태 핸들러 전부 ~COMMAND + fallback=/cancel뿐이라
  미완료 세션이 있으면 /report 완전 무시 → fallback에 /report 재시작 추가. 대표가 직접 겪은 함정
- **질문·피드백에 프로젝트/업무명 명시 강제** (커밋 1b902c5): SCORE/COMPLETION/STRUCTURE 프롬프트 3곳 —
  "그 결정" 지시어 금지, "'여수 프로젝트' 계약 결정 —" 형태로 (대표 피드백 반영)

### 실사용 검증 (7/13~7/15, 12건+)
- Type 분기 작동: 대부분 A(질문 1개), 7/15 김도영 asked=3 (B/C 심화) ✅
- 보완질문 실효: 산출물을 파일명·분량 단위로 구체화 (WBS 49과업, PPT 20p 등) ✅
- 점수 분포 10~55점 — 교육 전 베이스라인대와 일치
- ⚠️ 관찰: 7/14 00:12 배성원 2초 간격 2회 채점·저장(동일 10점) — 중복 제출/핸들러 이중발화 의심,
  시트 중복 행 가능성. 7/18 검토 때 원인 확인
- 대표 /report 테스트: 무반응 함정 → 핫픽스 후 완료 (최종 로그 검증은 다음 세션)

## 2026-07-18 — 노션 팀 방법론 스터디 → Team Ops Guide v1 + 고도화 P1·P2 확정

### 배경
오전 세션(노션 기능 갭 8건 구현)의 렌즈를 바꿔 "조직이 노션을 잘 쓰는 방법론"(관행) 스터디 →
도구 중립적 조직 업무관리 가이드 제작 → ARISA 고도화 논의까지 완료.

### 산출물
- **신규**: `20-operations/27-team-ops-guide/team-ops-guide-v1.html` (Reporting OS의 자매 문서)
  - 1부 원리 8개 (출처 검증: Notion 공식 blog/help·Notion Mastery·lethain·Optemization — 수치 주장 미포함):
    ①공개 기본값 ②검색 가능성=공유 ③구조는 소수·입력은 전원 ④템플릿=품질 하한선
    ⑤문서 오너 ⑥정리는 리듬(아카이브=이동, 삭제 아님) ⑦회의=문서→액션 ⑧정착>구축
  - 2부 실천 규칙 5종 — **2026-07-18 대표 확정 (현행 규칙)**:
    ①네이밍 3종(프로젝트명 특수문자 금지·등록명=유일 공식명 / 분장 업무명 동사형+산출물 / 파일명 kebab+버전)
    ②공유 리듬 표(기존 4 리듬 + 신규: 격주 금 팀 간 다이제스트·분기 정리 리추얼)
    ③회의 3단계(아젠다→9섹션 회의록→분장·결정 연결)
    ④아카이브 기준(완료 조건 3종: 납품+정산+회고 → 30일 후 90-archive+ARISA 상태 전환)
    ⑤템플릿 사용 매핑(상황→양식 표)
  - Playwright 렌더 검증 통과(콘솔 에러 0·오버플로우 없음)

### ARISA 관행 대조 (기능이 아니라 "관행 내장" 관점)
- 이미 우위: 봇 6항목=살아있는 템플릿, 브리프=공유 리듬 자동화, 텔레그램=자연스러운 채널
- 빠진 부분: 프로젝트 아카이브 라이프사이클(숨김만 존재), 네이밍 시스템 검증(자유 입력), 직원 상호 가시성
- 변형 필요: 회의록→분장·결정 연결(수동), 문서 오너·검토 주기, guide-os 교육 연결

### 논의 결과 (대표 확정)
- **도입 확정: P1 + P2** → 별도 구현 세션 (오전 갭 구현과 같은 패턴)
  - P1 (HIGH) 프로젝트 아카이브 라이프사이클: 완료 조건 3종 체크 → 셸 "아카이브" 목록 분리(숨김 아님)
    → 90-archive 동기화. 회고 축적 + 검색 오염 방지
  - P2 (HIGH) 네이밍 시스템 검증: /assign·프로젝트 등록 시 규칙 검증(특수문자 거부)
    + 기존 프로젝트명 유사도 매칭 — G1a ID 매칭 정확도 직결
- 보류(추후 논의): P3 회의→분장·결정 자동 연결(MED), P4 guide-os 교육 페이지(MED),
  P5 팀 간 다이제스트(MED — 조직문화 결정 필요), P6 문서 오너 stale 감지(LOW)
- 2부 규칙 확정에 따라 가이드 HTML의 "제안·초안" 배지 제거 완료

### 다음 세션 (P1+P2 구현)
- [ ] P1: 프로젝트 데이터 상태 필드(완료 조건 3종·아카이브) + 셸 아카이브 목록 + 90-archive 연동
- [ ] P2: /assign·등록 폼 네이밍 검증 + 유사도 매칭 (맥미니 배포 표준 패턴 준수)
- [ ] 배포 후 1~2주 정착 관찰 (원리 8)

---

## 2026-07-16 ~ 07-18 — 대시보드 분장·포트폴리오 대확장 (17커밋, 전부 맥미니 배포)

업무분장~포트폴리오~보고가 하나의 라이프사이클로 연결됨. 모든 기능 격리 하니스(가짜 시트)+Playwright E2E 검증 후 배포.

### 분장 ↔ 프로젝트 포트폴리오 연동
- 분장 등록 시 기존 프로젝트 tasks 영구 반영(akey), 신규명은 확인 패널(신규 생성/기존 합치기) (7aca2a8)
- 기존 분장 24그룹 → 21개 카드 백필 (유사명 통합, PM=최다담당)
- aliases(별칭) 매칭 도입 + 병합 3건: 여수·섬진흥원 / 봉은사 / 세스크멘슬 — 시트 B열 정규화 37행 (022282c, 266fe4d, a7eaba8)

### 완료 라이프사이클
- 미착수→진행중→완료(승인대기)→승인(대표·팀 리더)→포트폴리오 Done 기록 / 반려·↩되돌리기 (339a3ab)
- 보고 기반 자동 완료: 일일보고에서 완료 명시 → 아침 배치가 자동 완료 처리 (4321f7c)
- [📣 완료·보고]: 완료 + 리더·대표 텔레그램 멘션 (4321f7c)
- 삭제: 상태 '삭제' 마킹(이력 보존), 대표·리더+본인(본인 삭제 시 리더·대표 알림), 개별·일괄(체크리스트)·프로젝트 통째 (40bfb99, 7978e7c, 389c321, 8b4bae1)
- ✏️ 인라인 편집: 업무·프로젝트·마감 수정, akey 정합 유지 (88bfb73)

### 브리프 코멘트 + 개인 브리프
- 오늘 Brief 항목별 💬 코멘트(대표·리더) → 시스템 기록 + 보고자 텔레그램 회신(보고 원문 그대로 인용) (75d0da2~90cffa5)
- 개인 '내 업무' 일일 브리프: ⚡오늘 포커스 / 🆕신규 할일 제안([분장 등록]=본인 등록) / 📁프로젝트 업데이트 — 07:30 배치 인당 LLM 1회 (22bad17, f89b06c)

### 포트폴리오 자료·이력
- 📎 자료(회의록) 업로드 → AI 브리프 갱신 제안(diff 선택 적용) + 변경 로그 + deliverables 필드 (335282b)
- 회의록 날짜별 아카이브 + 원문 뷰어 (ad8c4d2)
- 읽기 전용·접기 그리드 버그 수정(우측 90% 공백) (117658e) / 엑셀 저장 '인증 실패' 세션 자동복구 + PM 삭제 (b670b64)

### 교훈
- 운영 배치를 ssh로 직접 실행 시 gws PATH 누락 → 브리프 빈 내용 덮어씀 사고 1회(즉시 복구). **맥미니 수동 배치는 반드시 launchd PATH 주입 후 실행**
- LLM 상대 날짜(내일/금요일)는 기준일 미주입 시 오환산 — 프롬프트에 오늘 날짜 필수
- 배포 표준: 로컬 검증 → 커밋·push → scp → launchctl kickstart → 헬스·서빙 grep

## 2026-07-18 (밤) — P1+P2 구현·맥미니 배포 (Team Ops Guide 고도화)

### 구현
- **shared/naming.py 신설** (P2 SSOT): 프로젝트명 규칙(2부-①) — 허용문자(한글·영문·숫자·공백·-·&·×·.)
  밖은 공백 자동정리(clean) 후 검증(2~40자·한/영 필수). 규칙 변경은 이 파일만.
- **P2 네이밍 시스템 검증** (dashboard-server.py + daily-report-bot.py):
  - /api/project/save 신규 생성: 자동정리+검증(400) + 활성 프로젝트 유사매칭 중복이면 dup 반환
    → 클라이언트 confirm("기존 X와 같은 프로젝트?") 후 force 재요청 (포트폴리오 추가 모달)
  - /api/assign-commit create: 정리+검증, 정리된 이름=공식 명칭, 원문은 aliases로 보존(매칭 연속성)
  - /api/assign-project-check: 신규명에 cleaned·nameError 반환 → 분장 확인 패널에 자동정리/위반 안내 표시,
    matched에 archived 플래그(아카이브 매칭 시 경고)
  - 봇 /assign: 파싱 직후 + 시트 저장 직전 이중 정리, 파싱 결과에 "(규칙 자동정리)" 표기
- **P1 아카이브 라이프사이클** (dashboard-server.py + 포트폴리오_대시보드.html):
  - POST /api/project/archive: 완료 조건 3종(납품·정산 체크 + 회고 잘된것/아쉬운것 필수) 미충족 시 400,
    충족 시 archived 메타(date/by/retro) + brief.status=Done. 복원은 대표만(restore). 이중 아카이브 거부
  - 파일은 이동하지 않음(플래그 방식) — 활성 목록·신규 귀속(_resolve_pid)에서만 제외 (검색 오염 방지, 소비자 무해)
  - 포트폴리오 UI: 카드에 📦 아카이브 버튼(대표·PM) → 모달(체크2+회고2) / 하단 "📦 아카이브 N개" 분리 목록
    (숨김 아닌 조회 — 회고 표시, 대표 ♻️복원) / 칸반·타임라인은 활성만(pfActive)
  - DATA/archive-log.jsonl 전이 기록 + **arisa-archive-pull.sh 신설**: 맥미니→로컬 90-archive/arisa-projects/
    동기화 (분기 정리 리추얼용, ssh macmini 별칭)

### 검증 (로컬 E2E — 임시 서버 8799)
- py_compile 3파일 OK + 네이밍 단위테스트 7케이스 통과 (괄호/슬래시/언더스코어 정리, 빈값/길이 거부)
- API 시나리오 9종 전부 통과: dup 감지→force 생성, 규칙 위반 400, 아카이브 조건 미충족 400,
  아카이브→이중거부→복원, check의 archived 플래그·cleaned 안내, archive-log 기록
- Playwright UI 검증: 콘솔 에러 0, 아카이브 섹션·회고 표시·복원 버튼·모달 필드 정상

### 배포 (맥미니, 표준 패턴)
- LAN ssh 타임아웃 → macmini-ts(Tailscale) 사용. 베이스 해시 3파일 git HEAD와 원격 일치 확인
- 백업(/tmp/*.bak-p1p2-20260718-213846) → scp 4파일 → 원격 py_compile OK
- dashboard kickstart 재시작 → **8780** 헬스 OK (주의: 헬스체크 포트는 8770 아님 — 통합 셸 8780)
- 운영 /projects에 신규 UI 마커 확인 + /api/project/archive 인증 게이트 정상
- **봇은 재시작 보류**: 21:40 직원 보고 세션 1건 진행 중(state 2) → com.arisa.daily-report-bot-restart가
  매일 04:00 자동 재시작하므로 그때 반영 (P2 봇 변경은 /assign 대표 전용이라 대기 무해)

### 열린 항목
- [ ] 내일 04:00 봇 자동 재시작 후 /assign 프로젝트명 자동정리 실전 확인
- [ ] 첫 실제 아카이브 실행 시 archive-log + arisa-archive-pull.sh 동작 확인 (분기 리추얼 첫 회)
- [ ] 기존 프로젝트명 중 규칙 위반 명칭(괄호 포함 등) 정리 여부 — 별도 결정 (자동 개명은 안 함, 신규만 강제)

## 2026-07-18 (밤 2차) — P1+P2 실데이터 대조 + 데이터 정리 실행

### 영향 대조 리포트
- `27-team-ops-guide/p1p2-impact-report-2026-07-18.html` — 운영 실측(프로젝트 25 + 분장 95행):
  네이밍 위반 8/25 · 분장 표기변형 34/87행(7종) · 아카이브 후보 2건 · pid 귀속 100%(G1a 효과)
- 발견: '중기 팝업스토어' vs '중기제품팝업스토' 실존 중복 — 현행 토큰 매칭은 붙임 표기 미감지
  → **n-gram 부분문자열 매칭 보강 = 후속 개선 후보**

### 데이터 정리 (대표 지시, 맥미니 직접 실행 — 백업 /tmp/p1p2-dataops-20260718-221221)
- **중기 병합**: 중기제품팝업스토-a8ay6(업무 0건·PM명 잘림) 삭제 → 중기-팝업스토어-jufws에
  alias '중기제품팝업스토' 추가 (분장 시트 참조 0건 확인 후 진행 — K열 재지정 불필요)
- **첫 아카이브 2건**: KBO(kbo-2026-asg)·둔촌주공 — archived 메타+status=Done+archive-log 기록.
  회고는 데이터 기반 초안("초안·대표 수정 가능" 표기) — 대표가 셸에서 복원/수정 가능
- 결과: 활성 22 / 아카이브 2 / 전체 24 (25→병합 24)
- **arisa-archive-pull.sh 실전 첫 실행 OK** → 90-archive/arisa-projects/ 3파일 동기화
  (주의: LAN ssh 불가 시 `ARISA_REMOTE=macmini-ts`)

### 열린 항목
- [ ] KBO·둔촌주공 회고 초안 → 대표 실제 회고로 교체 (셸 아카이브 목록에서 확인)
- [ ] 유사도 매칭 n-gram 보강 (붙임 표기 중복 감지 — 중기 케이스 재발 방지)

## 2026-07-18 (밤 3차) — n-gram 유사도 매칭 보강 배포

### 구현
- shared/naming.py: `name_similarity()` — 문자 bigram Dice 유사도 + `SIMILARITY_DUP=0.55`
  (실데이터 캘리브레이션: 중기 쌍 0.62 vs 최고 무관 쌍 '아파트너↔BA파트너스' 0.40 — 전 325쌍 스캔)
- dashboard-server.py:
  - `_find_dup_project()` 신설: 엄격 매칭 OR n-gram 임계 초과 (활성만) → /api/project/save 중복 경고에 사용
  - `_similar_projects()`: 토큰 교집합 + n-gram(≥0.45) 결합 — 붙임 표기가 분장 확인 패널 유사 후보에 노출
- **설계 원칙 유지: 귀속(pid 확정, _resolve_pid·봇 _project_pid)은 엄격 매칭 그대로** —
  n-gram은 사람이 확인(confirm/force)하는 지점 전용 (오귀속 위험 0)

### 검증·배포
- 로컬 E2E 4/4: 붙임 표기 dup 감지 ✓ / 무관 유사명 통과(오탐 0) ✓ / 유사 후보 노출 ✓ / force 우회 ✓
- 원격 드리프트 없음 확인(오늘 배포본 md5 일치) → 백업(/tmp/dashboard-server.py.bak-ngram-20260718-221934)
  → scp 2파일 → py_compile OK → 재시작 → 8780 헬스 OK
- 열린 항목 소거: "유사도 매칭 n-gram 보강" 완료 (중기 케이스 재발 방지)

## 2026-07-19 — KBO 복원 + 둔촌주공 회고 실문안 교체 (+ toggleSec 버그 수정)

### toggleSec 잠복 버그 (커밋 f41140a — 오전)
- 포트폴리오 상세의 섹션 헤더 6곳이 toggleSec() 호출하나 정의가 전 히스토리에 부재 →
  기본 collapsed인 Finance—예산·Issue Tracker·Brief 상세가 영구히 안 열림(입력 불가처럼 보임)
- 정의 추가, E2E(펼침→예산 입력→이슈 추가→재접힘) 검증, 맥미니 무재시작 반영(HTML은 요청마다 로드)

### KBO 아카이브 성급 판정 → 복원 (대표 확정)
- 분장 시트 확인: KBO 후속 분장 4건 존재(운영계획 기획안 ~7/28·예산 보고 ~7/29·실행 확정 ~8/10,
  미착수 2건) — 종료일 기준 아카이브 후보 판정의 맹점. **교훈: 아카이브 판단은 종료일이 아니라
  열린 분장 유무를 먼저 볼 것** (P1 고도화 아이디어: 아카이브 모달에서 열린 분장 경고)
- 복원 + 종료일 7/13→8/10(후속 실행 확정 마감) 갱신, 8/10 이후 정산 완료 시 재아카이브 예정
- 90-archive의 kbo 스냅샷 git rm (복원됐으므로 스테일)
- 회고 재료 수집됨(7/1~7/9 브리프): 잘된 것=운영 가이드·체크리스트·재고 인수증 체계 구축,
  아쉬운 것=발주(유니폼·사이니지) 결재·입금 병목 반복·인력 견적 지연 → 재아카이브 때 사용

### 둔촌주공 회고 교체 (초안→실문안, 분장 실기록 기반)
- 잘된 것: "철거 프로세스·상세설계 협의까지 검토 진행 (7/16~17, 공간팀 전제훈·경영 최원석)"
- 아쉬운 것: "실행 단계 진입 없이 종료 — 분장 2건 모두 삭제 처리, 중단 사유 미기록.
  다음부터 중단 시 사유 한 줄 남길 것"
- 결과: 활성 23 / 아카이브 1. archive-log에 restore·retro-update 전이 기록, 90-archive 재동기화

### 열린 항목
- [ ] 8/10 이후 KBO 재아카이브 (정산 확인 + 수집된 회고 재료 사용)
- [ ] 아카이브 모달에 "열린 분장 N건" 경고 표시 (성급 아카이브 방지 — 소규모 개선)
- [ ] 04:00 봇 재시작 후 /assign 자동정리 실전 확인 (오늘 첫 /assign에서)

## 2026-07-19 (2차) — 아카이브 열린 분장 경고 관문 배포

### 구현 (dashboard-server.py + 포트폴리오_대시보드.html)
- `_open_assigns(p)`: 프로젝트의 열린 분장(미착수·진행중, 전 기간 — 2주 윈도우 아님).
  pid 일치 우선, 없으면 이름 매칭. 시트 실패 시 [] (안전)
- GET /api/project/open-assigns: 모달 사전 경고용 조회
- POST /api/project/archive 관문: 열린 분장 있으면 openAssigns+목록 반환 → 클라이언트
  confirm("그래도 아카이브") 후 force_open 재시도 (사람 확인 후 우회 가능)
- 모달 UX: 열자마자 "⚠️ 열린 분장 N건 + 상위 5건 목록(업무·담당·마감·상태)" 표시

### 검증
- 유닛(시트 스텁): pid 1건+이름매칭 1건 감지, 완료·타 프로젝트 제외 ✓
- 로컬 E2E: 0건 시 관문 통과 ✓ / **운영 실데이터: KBO 열린 분장 2건(미착수) 정확 감지**
  (분장 4건 중 완료 2건 제외 — KBO 성급 아카이브 사례가 이제 시스템적으로 차단됨)
- 배포: 백업→scp 2파일→py_compile→재시작→8780 헬스 OK
- 열린 항목 소거: "아카이브 모달 열린 분장 경고" 완료

### 백로그 (2026-07-19 추가)
- [ ] HR 포털 관리자 지표 연동(D안): 대표창에 미결 결제·휴가 대기 건수 + 딥링크 — HR 포털에 서비스 토큰 API 필요, **맥미니 전환 판정 후** 착수 (판정 전 fly deploy 금지)

## 2026-07-19 (추가) — 셸 HR 포털 탭
- 대표 전용 "HR 포털 ↗" 새 창 링크 탭 (5b0742d). 프록시 통합은 맥미니 SPOF·홉 추가로 기각
- 백로그의 HR 관리자 지표 연동(D안)은 맥미니 전환 판정 완료(7/19)로 착수 가능해짐

## 2026-07-20 — filament 벤치마킹 P0+P1 6종 배포 (a10e8cf)

### 배경
- filament-ops-board.vercel.app/console 실사(로그인 최원석/0000, 6개 탭 전수) → ARISA 갭 매핑
- 계획: ~/.claude/plans/https-filament-ops-board-vercel-app-cons-functional-bear.md
- 확정 범위: P0+P1 전부, 채팅 단일 입구는 제외(arisa2 Decision Window와 통합 예정)

### 구현 (dashboard-server.py + shared/status.py + daily-brief-aggregate.py + 포트폴리오_대시보드.html)
- **A1 지연 감지**: status.py `is_overdue`/`overdue_days` SSOT → `_assign_read`가 전 소비자에
  days_overdue 공급, 분장 카드 '지연 N일' 배지, 리더 홈 '⏰ 마감 임박'(지난·오늘·내일),
  모닝 텔레그램 '마감 초과 N건' 라인(`_overdue_open_count` — exec-attn과 동일 판정)
- **A2 미지정 큐**: exec-attn·lead-home `unassigned` + '◆ 담당 미지정 배정' 섹션,
  assign-edit `new_assignee`(D열+C열 팀 재산정, 부분수정 구조로 개편 — 키 생략=변경 안 함)
- **A3 완료/보관함 분리**: 분장 리스트 열린 할 일 중심 + '▸ 완료·승인 대기 N건' 접힘
- **B1 프로젝트 허브**: `/api/project`에 memory(arisa-project-memory/projects/<폴더> 매칭,
  브리프·결정·할일·전략·진행로그 + 회의록 최근 5), `/api/project/memory-doc` 원문 열람,
  포트폴리오 상세 '🗂 프로젝트 기록' 섹션
- **B2 리더 인라인 편집**: 팀 Todo 카드에 상태·담당자 셀렉트(il-sel) 즉시 시트 반영
- **B3 담당자별 보기**: 팀 Todo 개인 필터 칩(이름+열린 건수, filament 사이드바 패턴)

### 검증·배포
- 유닛: is_overdue 경계(완료·삭제 제외, 비ISO 안전) / 봉은사 memory hub 매칭 ✓
- 로컬 E2E(8999) + 맥미니 프로덕션(8780): exec-attn 지연 13·미지정 1 실감지,
  lead-home(전제훈) 24건, 봉은사 링크백 파일 5·회의록 5 ✓
- 배포: scp 4파일 → launchctl kickstart com.projectrent.dashboard → 헬스 OK

### 주의사항
- 동시 세션(주간분장 L열·타팀 리더 이관 작업)과 같은 워킹트리 병행 편집 — 커밋이 서로의
  변경을 일부 포함(5c671d4·e9f57ac·a10e8cf). 파일 상태는 병합 무결, 히스토리만 교차
- 포트폴리오_대시보드.html은 generate-portfolio.py 재생성 시 누적 기능 유실 — 직접 편집만

### 제외/후속
- [ ] 채팅 단일 입구 → arisa2 Decision Window Sprint에서
- [ ] 미러 보고서(보고자별 원문 그대로) → '거울 정확성 보정' 후속 논의와 통합
- [ ] 재무(계약·인보이스·입금) → 별도 프로젝트 규모

## 2026-07-19 (3차) — 역할별 업데이트 가이드 제작

- `arisa-update-guide-2026-07-19.html`: P1+P2+toggleSec 변경분의 사용법 가이드 (전 직원 3 / 팀 리더 +3 / 대표·PM +2)
  — 원리는 Team Ops Guide 링크, "화면에서 달라진 것"만 요약. 렌더 검증 OK
- [ ] **배포 대기**: 대표 내용 확인 후 send-guide-notice.py 패턴으로 전 직원 텔레그램 발송
- [ ] 가이드 파일 커밋 대기 (untracked)

## 2026-07-22 — 사업기획팀 2인 3주 보고 분석 리포트

- `analysis/business-team-3week-analysis-2026-07-22.html`: 배성원·김도영 7/1~7/22 시트 원본(핵심46·서브180·메타23·분장23행) 기반 실질 진행도·산출물 분석 — 배: 보고 8/16일·산출물 기재 22%·분장 미착수 14/19 (7/14 이중제출 발견), 김: 보고 12/16일·산출물 62%·결정대기 3건(파도안·현수막·로고). weekly-data W27/W28 growth 크로스체크 완료. 대표 액션 5 도출
- `analysis/deliverables-inventory-business-team-2026-07-22.html`: 산출물 인벤토리(검토용) — 김도영 파일단위 60건+ 프로젝트별 7분류(전략·협의·행정·WBS·공간·품평회·도구)+검토포인트, 배성원 기재 4건+미기재 완료 9건 확인방법 표, 검토 세션 순서 5단계 제안

## 2026-07-23 — /퇴사처리 스킬: 퇴사자 아리사 접근 즉시 차단 (구현 완료·배포 대기)

- **배경**: 퇴사 시 접근 차단 표준 절차 부재. 조나연(7/1 퇴사)이 users.json에 남아 로그인 가능 상태였음
- **차단 원리(검증 완료)**: 아리사 OS는 매 요청 users.json 재검증(web_session→load_users) — 이름 제거만으로 기존 30일 쿠키·PIN·재로그인 즉시 401, 재시작 불필요. 스크래치 서버로 입증(로그인→쿠키 200→제거→같은 쿠키 401)
- **구멍 봉합**: 봇은 명부 제거 후에도 이름 자유 입력으로 보고 가능했음 → `offboarded.json` 목록 기반 거부 추가
  - `offboard-employee.py`(신규): dry-run→백업(_data/offboard-backups/)→로컬 3파일 수정(users/employees/offboarded)→맥미니 scp→봇 재시작→arisa-os.com 401 검증까지 원샷
  - `daily-report-bot.py`: is_offboarded() + 거부 3지점(start_report tid / receive_info 이름 입력 / receive_inquiry)
  - `basket-ops-bot.py`: group=-1 선행 핸들러(log_chat)에서 ApplicationHandlerStop으로 단일 차단
  - `.claude/skills/퇴사처리/` 등록 + CLAUDE.md 표 추가. 수동 체크리스트(HR포털·구글워크스페이스·SaaS·와이파이·리더 승계) 스킬에 내장
- 검증: 킬스위치 입증·봇 로직 단위테스트 4/4(tid/이름 공백무시/재직자 미차단/파일없음 안전)·조나연 dry-run(users.json만 잔존 확인)·타직원 로그인 회귀 OK
- [x] **배포 완료(7/23, 대표 승인)**: 봇 2종 scp+재시작(PID 정상) → `offboard-employee.py 조나연` 실행 — 백업 20260723-0816, 맥미니 동기화, **arisa-os.com 차단 검증 ✅(401 등록되지 않은 이름)**. 회귀: 재직자 계정 존재·health·봇 3서비스 가동 확인

## 2026-07-23 (2차) — ⚠️ users.json 덮어쓰기 사고 및 복구 완료

- **사고**: 08:16 조나연 퇴사처리 시 offboard-employee.py가 로컬 구버전 users.json(dict·테스트PIN·배성원 등 3명 누락)을 맥미니로 scp → 맥미니 users.json이 **arisa2 SSOT(~/dev/arisa2/data/users.json) 심링크**여서 원본 훼손. 증상: 배성원 로그인 불가(첫 발견), 전 직원 PIN이 공지값과 불일치 상태 약 4시간
- **복구(12:08)**: arisa2 git 12096b7(11명 명단·역할·팀) + data/initial_credentials.txt(7/22 공지 발송 PIN 원본)로 리스트 스키마 재구성 → SSOT 복원(사고본 users.json.bak-clobbered-20260723-1208 보존). 검증: 배성원 실로그인 ✅(leader·사업기획), 김예진·김도영·최원석·윤혜정 계정 존재 ✅, 조나연 차단 유지 ✅, health OK
- **재발 방지(코드 반영 완료)**: offboard-employee.py — users.json은 절대 push하지 않고 맥미니 SSOT에서 이름만 원격 제거(원격 백업 자동), dry-run 판정도 맥미니 기준으로 변경. 스킬 문서에 SSOT 경고 명시
- **잔여 리스크**: 7/22 저녁 이후 PIN을 직접 변경한 직원이 있다면 그 변경분은 유실 — 공지받은 원래 PIN으로 로그인해야 함(문의 오면 안내). 로컬 users.json은 테스트 사본으로만 사용
- **로그인 오류 안내 발송(12:2x)**: send-login-fix-notice.py — 대표 테스트 1건 후 전 직원 10/10 성공. 내용: 오전 오류·복구 완료·7/22 안내 PIN으로 로그인·PIN 변경자는 원래 PIN으로·문제 시 봇 채팅 회신
- **미지정 큐 유령 카드 수정(7/23 오후)**: 시트 2~4행 찌꺼기(팀 칸만 있고 업무·담당자 공란)가 미지정 큐에 유입 — 업무명이 비어 삭제 API 검증(409)에 걸려 처리 불능이었음. ①시트 3행 삭제 마킹 ②서버 가드(task 공란 행은 큐 제외, exec-attn·lead-home 2곳) ③미지정 카드에 🗑 삭제 버튼 추가(향후 오등록 정리용). 실시트 검증: 미지정 0·승인 대기 8(회귀 일치)·지연 39. 맥미니 배포 완료. ⚠️ 미커밋 — 다음 커밋에 포함

## 2026-07-24 — 배성원 로그인 이슈 → PIN 재안내 전 직원 재발송

- 진단: 배성원 계정·PIN(초기값) 서버측 정상 — 프로덕션 실로그인 200 확인. 원인은 입력 단계(대소문자 10자리 오타/복사 공백/사고 시간대 실패 후 미재시도)로 판정
- 배성원 개별 재안내 발송(복사 붙여넣기 가이드 포함) → 이어서 **전 직원 PIN 재발송 10/10 성공**
- **send-pin-notice.py 결함 수정**: load_pins가 로컬 users.json(테스트 사본·구버전 PIN)을 읽던 문제 → 맥미니 SSOT(ssh cat)에서 읽도록 변경(로컬 폴백 시 경고 표시). 이 결함 그대로 썼다면 전원에게 틀린 PIN(0000~8888)이 나갈 뻔함
- 메시지 개선: "복구로 처음 안내 PIN으로 돌아감" 설명 + 대소문자/복사 가이드. SSOT에서 읽으므로 변경한 사람에겐 변경된 현재 PIN이 발송됨(정확)
- ⚠️ 미커밋: send-pin-notice.py 수정분 (+어제 미지정 큐 수정분) — 다음 커밋에 포함

## 2026-07-25 — R4 개편 4차 커밋·맥미니 배포 (프로젝트 통합 카드·주간 간트)

- 커밋 2건: `bae926f` feat(R4 4차 — daily-brief build_project_cards §9 + weekly build_gantt_rows §10, shared/project_match 별칭 SSOT 소비) / `c598e8f` chore(병행 산출물 — AX 디자이너 슬라이드·R-Europe 미팅 PDF·데일리노트·status-log)
- 배포 전 해시 대조: 맥미니의 dashboard-server.py·shared 5종·approval-rules.json은 로컬 HEAD와 **이미 일치**(R4 1~3차 기배포 확인), aggregate 2종만 HEAD 베이스와 일치 → 깨끗한 배포 조건
- 표준 패턴 수행: /tmp 백업(*.bak-r4-4) → scp 2파일 → py_compile OK → 해시 일치(94959fdc·8c8fd25f) → dashboard kickstart(신규 PID 86744, _DBA 런타임 import 캐시 갱신 목적) → 8780 200 + arisa-os.com 200
- 실전 관찰 대기: 내일 아침 브리프의 project_cards 생성·exec-attn 소비, 월 08:30 주간 리포트 간트 렌더

## 2026-07-26 — R4 5차 배포: HR 포털 다크 변환 fly.io 프로덕션 반영 (대표 승인)

- 맥미니 hr-workspace 커밋 `ecc7637`(템플릿 6종만 — .hr-service-token·완료계약아카이브(PII)·hr-contract-archive.py는 untracked로 제외, 커밋 금지 유지)
- flyctl deploy(rent-hr-portal) → 머신 683557df405178 헬스·스모크 통과, DNS 검증 OK
- 프로덕션 검증: `/` 200, `/v1`(templates/portal.html 직서빙) 신 토큰 #6C5CE7·#202020만 검출, 구 #6666FF 0건. 참고: `/`는 portal-v2/index.html(별도 UI)이라 이번 변환 스코프 밖
- **R4 1~5차 전체 종결** — 잔여는 실전 관찰(브리프 project_cards·월 간트)뿐

## 2026-07-26 (2차) — HR 포털 메인(portal-v2) 기본 테마 다크 전환 (대표 승인 배포)

- 발견: portal-v2엔 다크 토큰이 기설계돼 있었음(`[data-theme=dark][data-variant=v1]` — bg #0B0B12·surface #15151C). 색상 재정의 없이 App.jsx DEFAULTS `"theme": "light"→"dark"` 1줄로 전 직원 기본 다크 (테마는 localStorage 미저장, 매 로드 DEFAULTS 기점)
- 안전 확인: 증명서 PDF 렌더(cert_util.jsx)는 테마 변수 미사용 → 인쇄 출력 화이트 유지 / TweaksPanel(헤더 버튼)로 개인별 라이트 복귀 가능
- 맥미니 hr-workspace 커밋 `fc048e4` → flyctl deploy → 머신 헬스 통과, 프로덕션 App.jsx에서 "theme": "dark" 서빙 확인
- 참고: 템플릿 6종(5차)과 달리 portal-v2 다크는 자체 팔레트(#6666FF 유지) — ARISA 청보라(#6C5CE7) 통일은 별도 판단 사항

## 2026-07-26 (3차) — portal-v2 브랜드 컬러 청보라 통일 (⚠️ fly 배포 대기)

- 맥미니 hr-workspace 커밋 `5e61515`: #6666FF→#6C5CE7·#5353FF→#5B4BD5·#8A8AFF→#8A7DEC·#E1E1FF→#E4DFFB·#CDCEFB→#D4CDF7·rgba(102,102,255→108,92,231), styles.css+JSX 4종(Certificate/Overtime/TeamReport/UnifiedAdmin), 구색상 잔존 0건. 재직증명서 포인트 컬러 포함(용지 화이트 유지)
- **⚠️ flyctl deploy 미실행** — 권한 분류기 차단, "배포 승인" 대기 상태에서 세션 종료. 다음 세션: `ssh macmini-ts 'cd ~/hr-workspace/20-operations/21-hr/portal && ~/.fly/bin/flyctl deploy'` 실행 + 프로덕션 styles.css에서 #6C5CE7 확인만 하면 끝

## 2026-07-26 (4차) — 노션 PM 갭 분석 2차: 갭A(회의↔할 일 연결) 구현

### 배경
- 노션 템플릿 "[직장인을 위한] 업무 관리 시스템"(에그디자인 배포) 분석 — DB 3종(할 일/회의/프로젝트) + dual relation + 진행률 롤업 + '오늘 할 일' 체크박스. 7/18 1차 갭 분석에서 롤업·상태·우선순위는 이미 흡수, 남은 실질 갭 3건 도출
- **갭A(구현)** 회의가 1급 엔티티가 아님 — 회의분석이 to-do 5~12개를 뽑고도 화면 산출물로 끝나 분장과 끊김(시뮬레이터에 시트 배선 grep 0건) → "회의에서 정한 것 중 몇 %가 완료됐나"를 측정 불가
- **갭B(후속)** 출처가 L열 등록자(사람)뿐 — 무엇에서 나왔는지는 UI 문구로만 존재
- **갭C(후속)** 담당자 본인의 '오늘 선언' 계층 부재(현재는 마감·지연 기반 자동 산출 + 대표 today_focus LLM)
- 판단 보류: 중요도 3단계(노션) → 현행 2단계 유지 권고('보통'에 몰려 변별력 소실)

### 설계 — 회의 ID를 새로 만들지 않는다
- 회의 식별자 = **프로젝트 문서함의 (pid, ts)** 재사용 (`/api/simulator/submit-doc`이 생성, DOC_DIR/<pid>/<ts>.json|.md). 별도 회의 테이블·시트 탭 없음
- 주간분장 시트 **M열 출처 · N열 출처ID**(= `<pid>|<ts>`) 추가 — 헤더 라벨 반영 완료, 기존 129행 불변(뒤 컬럼이라 하위호환)

### 구현
- `shared/provenance.py`(신규): 출처 어휘 SSOT(회의·일일보고·주간계획·대표지시·본인등록), `meeting_ref`/`parse_meeting_ref`, `norm_due`, `action_rollup`
- `dashboard-server.py`: `_assign_read` A2:N(14칸)·`_assign_append(source, source_ref)`, `_meeting_actions`/`_doc_action_index`/`_meeting_todo_candidates`, **POST·GET `/api/meeting-actions`**, `/api/project`에 `docActions`, submit-doc 응답에 등록 후보(candidates), 회의 제출 후 2단계 등록 UI, 분장 카드 출처 칩(`mwSrcChip`)
- `포트폴리오_대시보드.html`: 회의록 아카이브에 실행률 배지(`실행 3/7 · 43% ⏰2`) + 클릭 시 액션 목록 펼침(`toggleMeetingActions`)
- 정책 보존: 대표=리더·본인, 리더=자기 팀원+타팀 리더, 직원=본인. **권한 밖·미매칭 담당자는 거부가 아니라 '담당 미지정 큐'로 강등**(액션 유실 방지, A2 재사용)
- `norm_due`: '미정·확인 필요·오픈 전까지'는 마감으로 승격하지 않고 빈칸 — 비ISO를 그대로 두면 `is_overdue`가 영원히 지연 판정을 못 하는 조용한 구멍이 생김

### 검증
- 유닛 38항목 ✓ (ref 조립·파싱, due 정규화, 롤업에서 취소·삭제 분모 제외, theirs 제외, 12칸 구데이터 하위호환)
- 인프로세스 E2E 30항목 ✓ (시트·데이터 전부 스텁 — 운영 무오염): 권한 강등 4종, 중복 방지, 400/403/404, GET 롤업, docActions
- 운영 시트 실데이터 읽기 회귀 ✓ 129행·열린 80·지연 47 (종전 동일)
- 배포 전 해시 대조: 맥미니 = 로컬 HEAD 완전 일치(깨끗한 조건)

### 후속
- [ ] 갭B — assign-commit/self/plan 경로에 출처 라벨 채우기(대표지시·본인등록·일일보고·주간계획)
- [ ] 갭C — 담당자 '오늘 선언' 플래그 + 저녁 보고 대조(계획 대비 실행률)
- [ ] 회의 실행률의 주간 리포트·대표창 노출(현재는 프로젝트 상세·제출 직후만)
- [ ] 마감일 월 캘린더 뷰(간트는 2주 윈도우)

## 2026-07-26 (5차) — 노션 갭B(업무 출처 일반화) · 갭C(오늘 선언) 구현

### 갭B — 업무가 '무엇에서' 나왔는가
- 어휘 확장(`shared/provenance.py`): 회의·일일보고·주간계획·**대표지시·리더분장**·본인등록 6종 + `normalize_source`/`assign_source`/`source_mix`
- 등록 경로 전부 배선:
  - `/api/assign`(단건)·`/api/assign-commit`(일괄) → 대표=대표지시 / 리더=리더분장, ref="분장 화면"
  - 주간계획 xlsx 업로드 → 클라이언트가 `MW_ORIGIN`으로 출처를 등록까지 물고 감(`origin:plan`, ref=**파일명**)
  - `/api/assign-self` → 기본 본인등록. 브리프 '🆕 제안' 수락 버튼만 `source=일일보고`+ref=**보고 날짜**(`data-src-ref`, 개인 브리프 JSON의 date)
  - 봇 `save_assignment_to_sheet` → 14칸 확장, 대표지시 + "텔레그램 /assign" (L열은 종전대로 공란 유지)
- 화면: 분장 카드 출처 칩 아이콘 6종(🎙📝📅📌📎✋), 리더 홈 팀 Todo 헤더에 **유입 분포**(`mwSrcMixHtml` — 미상만 있으면 미표시)

### 갭C — 담당자 본인의 '오늘' 계층
- `shared/today_plan.py`(신규): `<DATA>/today-plan/<날짜>.json` = {이름: [키]}, 키 = `<시트row>|<업무앞40자>`
  - **row만 같고 업무가 다르면 미매칭** — 행이 밀렸을 때 엉뚱한 업무가 선언을 물려받지 않게
  - `summarize` → planned/done/percent + **stale**(선언 후 사라진 항목은 분모에서 제외)
- `POST /api/today-plan`(본인 분장만 — 남의 하루를 대신 정하지 않음), `/api/my-work`에 today_plan·today_summary,
  `/api/lead-home`에 team_today(선언한 사람만) + 리더 본인 today_plan
- 화면: 내 분장 카드에 ☀️ 토글, 상단 "☀️ 오늘 하기로 한 일 N건 중 M건 완료 · x%" 섹션(미선언 시 안내 한 줄만 — 잔소리 안 함),
  리더 홈 "팀원이 오늘 하기로 한 일"(이름별 진행바)

### 검증
- 유닛 33항목 ✓ (출처 정규화·분포 정렬/미상 처리, 키 조립·40자 절단, 토글 추가·중복·해제·날짜/사람 분리, stale, 행 밀림 미매칭)
- E2E 31항목 ✓ (등록 경로 4종의 M·N열 실제 기록, 리더 홈 분포, 오늘 선언 403/400 방어, 완료 시 실행률 상승, team_today)
- 갭A 테스트 회귀 ✓ (유닛 38 + E2E 30 전부 통과)
- 운영 시트 실데이터 ✓ 129행·열린 80·지연 47 유지, 현재 출처 미상 94건(신규 등록분부터 채워짐)

## 2026-07-26 (6차) — 노션 가이드 대조 + 보고→상태 환류 (우선순위 1)

### 대조 리포트
- `notion-guide-comparison-2026-07-26.html` — 노션 업무관리 구축 상세가이드(10~50인) × ARISA 실측 대조
- 항목별 판정: 데이터구조/업무흐름/자동화/화면/거버넌스 5축. 아리사 우위(상태 13종·승인체인·지연감지·LLM채점)와 미비(요청접수·업무유형·마감캘린더·입력누락감시) 분리

### 실측으로 드러난 것 (2026-07-26)
- 유효 분장 94 · 열린 80 중 **미착수 78 · 진행중 2** · 지연 47
- 입력 완결성: 마감 없음 24%(23건) · 프로젝트 미연결 17%(16건) · **필수4종 중 누락 38%** · **결과물 G열 100% 공란(죽은 컬럼)** · 우선순위 '긴급' 6%
- 프로젝트 21개 전부 PM·완료조건 보유, **docs 보유 0/21**(문서함 미사용 → 갭A 회의연결이 아직 발동 못 한 이유)
- 상태 전이 23건(7/18~25) = 자동 8(daily-brief-auto 4·weekly-auto 4) + 사람 14(최원석 7·전제훈 6·정예은 1) + 테스트 1
- ⚠️ 세션 중 오보고 정정: 최초 "전이 23건 전부 대표"는 status_log 키를 actor로 잘못 조회한 오류(실제 키는 `by`)

### 근본 원인
**보고→상태 환류는 이미 있었으나 문이 너무 좁았다.** PERSON_BRIEF_PROMPT가 "진행 중·예정·부분 완료는 절대 포함 금지"로 '명시적 완료'만 추출 → **개인 브리프 57개에서 completed 2건**(같은 브리프의 new_todos는 142건). 게다가 '진행중' 전이는 설계에 아예 없어 미착수가 화석화.

### 구현
- `shared/assign_sheet.py`(신규) — 주간분장 컬럼·파싱·상태갱신 SSOT. `parse_row/parse_all/read/open_for/set_status/task_sig/verify_row`.
  dashboard-server `_assign_read`를 이 모듈 호출로 교체(3번째 사본 방지), 봇도 동일 모듈 사용
- **봇 즉시 확인 루프**(핵심): 보고 완료 직후 `_ask_status_sync` → LLM 매칭(`STATUS_SYNC_PROMPT`) → 건별 인라인 버튼 [▶진행중][✓완료][✕아님] → `on_status_sync_click`이 시트 H열 갱신 + status_log(source=`report-sync`)
  - 안전장치: callback_data에 **업무 지문 6자**(sha1) 동봉 → 행 밀림 시 오처리 차단, 갱신 전 `verify_row`로 담당자·지문 재확인, 텔레그램 ID 미학습 계정은 user_data 이름 폴백
  - 설계 의도: 자동 전이가 보수적일 수밖에 없는 건 **사람 확인이 없기 때문** → 사람이 1탭으로 확정하면 후보를 넉넉히 뽑아도 안전(오탐 비용 = 버튼 안 누름)
- **아침 자동 전이에 '진행중' 추가**: PERSON_BRIEF_PROMPT에 `in_progress` 추출 신설, `_pick()` 헬퍼로 completed/in_progress 공통 처리.
  진행중 전이는 **미착수에서만** 허용(검토중·승인대기·보류를 되돌리면 승인 흐름 역행), completed와 중복 제외

### 검증
- 유닛 28항목 ✓ (파싱 구/신행, open_for, task_sig, verify_row 타인·지문·행밀림 거부, set_status H열 한정, 매칭 필터 6종, callback_data 17B)
- 브리프 전이 12항목 ✓ (OpenAI 스텁 — 미착수만 진행중, 검토중·보류·중복·범위밖 제외)
- 기존 갭A·B·C 회귀 전부 통과, 실시트 129행·열린 80·지연 47 불변, **서버와 봇 경로가 동일 결과** 확인

## 2026-07-26 (7차) — 입력 완결성 게이트 (우선순위 2)

- `shared/assign_sheet.py`: `REQUIRED_FIELDS`(마감일·프로젝트 — 담당자는 미지정 큐가 이미 담당) + `missing_fields()` + `incomplete()`
  (열린 분장만, **마감 없는 건을 앞에** 정렬 — 마감이 없으면 `is_overdue`가 비ISO를 지연 아님으로 처리해 영원히 안 걸림)
- `/api/lead-home`·`/api/my-work` 응답에 `incomplete` 추가 → 리더 홈·개인 탭에 "⚠️ 입력 누락 N건" 섹션(최대 12건 + ✏️ 인라인 편집으로 그 자리에서 채움)
- **등록 게이트**: 분장 등록(mwCommit)에서 마감 미입력 시 등록 차단 — "마감이 없으면 지연 관리가 되지 않습니다".
  서버는 거부하지 않음(봇 `/assign`·회의 액션 등록 경로 보존 — 그것들은 누락 목록이 사후에 잡는다)
- 검증: 유닛 18 ✓ / E2E +5 ✓ / **실데이터: 열린 80건 중 누락 32건(마감 19·프로젝트 16), 담당자별 김예진 7·윤혜정 6·전제훈 6**

## 2026-07-26 (8차) — 죽은 '결과물' 칸 되살리기(3) + 업무 유형·마감 달력(4)

### 3. 결과물(G열) — 사람에게 다시 묻지 않는 방식으로
- 실측상 유효 94건 전부 공란인 죽은 컬럼. **일일보고에 이미 적힌 산출물**(core_tasks[].output)을 완료 확정 시점에 옮겨 적는 방식 채택(추가 입력 0)
- 봇: `STATUS_SYNC_PROMPT`에 `rep`(보고 업무 번호) 요구 → 매칭 항목의 output을 `context.user_data["sync_out"]`에 보관 →
  콜백에서 **완료 선택 + 기존 결과물이 비어 있을 때만** `_AS.set_result`로 G열 기록, 회신에 "📦 결과물도 함께 기록했어요"
- 수동 경로: 편집 폼(✏️)에 결과물 입력 + `/api/assign-edit` `new_result`(G열, 300자)

### 4. 업무 유형(O열) + 마감 달력
- `shared/assign_sheet.py`: `TASK_TYPES=(기획·제작·운영·영업·행정)` SSOT + `norm_type`/`type_mix`/`set_type`, READ_RANGE A2:O·COLS 15
- 시트 O1='유형' 헤더 추가(기존 행 불변, 14칸 구행은 유형 빈값으로 하위호환)
- **입력 부담 0**: `_llm_todo`가 항목화하면서 유형까지 추정 → assign-commit이 O열에 기록. 사람은 편집 폼 셀렉트로 교정
- 어휘는 서버가 `UNIFIED_SHELL.__TASK_TYPES__`에 주입(화면 하드코딩 금지 — 어휘 변경 시 모듈만 수정)
- 리더 홈 팀 Todo 헤더에 유형 분포(%), **마감 달력**(이번달+다음달 2개월 그리드, 마감 몰림을 농도로 표시, 오늘 칸 아웃라인)

### 검증
- 유닛 +16 ✓ (유형 정규화·분포·set_type O열 한정·목록밖 거부·구행 14칸 하위호환, 산출물 매칭 rep 이상값 안전, set_result G열 한정)
- 기존 6개 스위트 전부 통과(갭A E2E는 시트 칸수 기대값 14→15 갱신 — 의도된 스키마 확장)
- 실데이터 회귀: 129행·열린 80·지연 47·누락 32 불변, 유형 분포 = 미분류 94(신규 등록분부터 채워짐)

## 2026-07-27 — GitHub 스킬 채굴 이식 (WS1·WS2·WS3·WS4) · 로컬 완료, 맥미니 배포 대기

**배경**: "GitHub에 노션처럼 업무관리 특화된 스킬·솔루션이 있나" 조사 → 자체 호스팅 앱(Plane 54.7k·AppFlowy 69.4k·Huly 26.9k)은 PR 보드+ARISA 통합 대시보드와 SSOT가 쪼개져 보류. 스킬 3종에서 로직만 차용.
- [mattjoyce/kanban-skill](https://github.com/mattjoyce/kanban-skill) (Apache-2.0) — 차용은 `blocked_by` 필드가 아니라 **"게이트를 데이터 규칙으로 강제한다"는 사상**
- [rampstackco/claude-skills](https://github.com/rampstackco/claude-skills) `stakeholder-communication` (MIT) — 나쁜 소식 5항목·헤드라인 완화 금지·역피라미드
- [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) `senior-pm` — 프로젝트 헬스 파생 스코어·RAG·추세

### 실측으로 뒤집힌 전제 3건 (착수 전 가정 → 조사 결과)
1. **"매주 월요일 상태가 되돌아가고 있다" → 잠재 파손이었다.** `weekly-report-aggregate.update_assignment_status_in_sheet`의 역기입 예외가 `미착수` 하나뿐인 것은 사실이나(코드 경로 열림), 감사 결과 시트 상태 분포가 미착수 69·삭제 34·완료 17·진행중 7·승인 2로 **검토중·승인대기·보류가 0건**이었다(R4 1차 07-25 도입 상태가 아직 실사용 전). `match_assignments_to_daily`가 완료·승인을 skip하고 `fetch_assignments`가 DROPPED를 제외하므로 현재 데이터에서는 발현되지 않는다. → R4 승인 흐름이 쓰이기 시작하는 순간 터진다. **보호 대상 데이터가 아직 없는 지금이 게이트 도입에 가장 안전한 시점.**
2. **회의 의존성은 "소실"이 아니라 미추출+미연결이었다.** 시뮬레이터가 2개다 — 엔진 A(`dashboard-server.py` `block_5_todos.ours`, 시트로 실제 등록)는 dependencies 필드가 **없고**, 엔진 B(`meeting-simulator-server.py:309` `actions[].dependencies`, 8781)는 시트로 가는 경로가 **없다**. `dashboard-server.py`의 `dependencies` grep 0건이 이 때문.
3. **프로젝트 헬스 입력이 "없다"보다 나쁜 "뜻이 다르다"였다.** `end`/`dday`는 21개 중 20개가 등록 주(7/16~22) 기준 짧은 창, `tasks.progress`는 자동 생성 골격이라 대부분 0% → 이 둘로 5차원을 계산하면 **20/21이 빨강**(정보 0). budget+actual 동시 기재 1/21, brief.risk 3/21, brief.status **21/21이 "In Progress"**(= 죽은 필드), status_log 1줄.

### WS2 — 상태 전이 게이트 (최우선, shadow)
- `shared/status.py`: `TRANSITIONS`(사람 13상태) · `AUTO_TRANSITIONS`(자동 4전이만) · `ADMIN_ONLY`(승인→진행중·완료·검토중) · `AUTO_SOURCES`/`CONFIRMED_SOURCES` · `source_class`/`transition_mode`/`can_transition`/`check_transition`/`transition_note`
  - **fail-open**: 어휘 밖 from/to는 항상 통과 (구 데이터로 운영이 멈추는 사고 배제)
  - `*→삭제` 무조건 허용 (bulk-delete 200건·프로젝트 삭제 보호)
  - `report_score.current_mode()` 동형 — `ENFORCE_FROM=2026-08-17`, env `ARISA_TRANSITION_MODE`(shadow|enforce|off) 킬스위치
  - shadow는 위반이어도 쓰기를 통과시키고 사유만 `[transition-shadow]` note로 남긴다 → 호출측 분기가 `ok` 하나뿐이라 **enforce 플립에 코드 변경 없음**
- `shared/assign_sheet.py`: `set_status_guarded` (게이트→쓰기, 로깅은 호출측 — 경로별 필드가 다르고 `_log_st` 이중기록 방지)
- 연결 5경로: `/api/assign-status`(400 `code:transition`) · `_set_st` 클로저(반려·검토통과·PM클리어 7선택지 단일 초크포인트) · `daily-brief` 자동전이 루프 + `_pick`의 want_from을 **`AUTO_TRANSITIONS`에서 유도**(손으로 적으면 두 곳이 어긋난다) · `weekly` `update_assignment_status_in_sheet`(+`dry_run`, 차단 카운트 반환) · 봇 `on_status_sync_click`(승인대기·검토중이면 "리더 검토를 기다리는 중이에요")
- 게이트를 **붙이지 않은** 곳에 주석 명시: bulk-delete(`*→삭제`) · `project-merge`의 `to="병합"`(어휘 밖 의사 상태·시트 미기록 로그 전용)
- 검증: `tests/test_status_transitions.py` **51/51** — 전이 12케이스 + 모드 전환 + **PM_CLEAR_EFFECTS 7선택지 전량 회귀**(게이트가 승인 체인을 죽이면 최악) + 테이블 정합(AUTO ⊆ 사람)
- 감사: `migration/audit-assign-status.py`(읽기 전용) → **어휘 밖 값 0건 = 마이그레이션 불필요 확정**, status_log 리플레이 위반 0건

### WS1 — 회의 의존성 (표시만 · G9 엔진은 보류 유지)
- **신규 `shared/meeting_link.py`**: `load_result`/`action_index`(엔진 A·B 양쪽 스키마 수용, B의 dependencies는 ID→제목 변환)/`deps_for`(캐시 주입)/`deps_summary`/`has_blocking`
- **저장하지 않는다**: 의존성 본문은 이미 `DOC_DIR/<pid>/<ts>.json`의 `doc["result"]`에 있고 조회 키도 N열에 있다. 시트 열 추가 0·프로젝트 JSON 변경 0 — 회의록이 회의 정보의 SSOT
- `shared/provenance.py`: `meeting_ref(pid, ts, action_id="")` 3세그먼트 + `parse_meeting_ref3`. 액션ID는 `^[A-Z]\d{1,3}$`만 허용(자유 텍스트 유입 차단)
- **하위호환 필수 조치**: `_meeting_actions`의 `source_ref == ref` 문자열 동등 비교 → `parse_meeting_ref3(...)[:2]` 비교. 안 바꾸면 3세그먼트 신규 액션이 회의 실행률 롤업에서 조용히 빠진다
- 엔진 A 프롬프트 `block_5_todos.ours`에 선택 필드 2개(`depends_on`·`blocked_by`, 없으면 빈 배열/빈 문자열) · `_meeting_todo_candidates`가 엔진 B `actions[]`도 파싱 · `/api/meeting-actions`가 액션ID를 N열에 기록
- `_attach_deps` → my-work·lead-home 주입(같은 (pid,ts) 1회만 읽음) · `mwDepsChip` 칩 + `.mw-deps` CSS
- 검증: `tests/test_meeting_link.py` **35/35** — 엔진 A/B 픽스처 · 존재하지 않는 참조 무시 · **레거시 2세그먼트 왕복** · 업무명 편집 시 액션ID가 조인을 지킴 · 캐시 1회
- ⚠️ 현재 `project-docs/` 폴더 없음 = 회의 제출 이력 0건 → **첫 회의 제출 시점부터 실효**

### WS3 — 프로젝트 신호등 + ReportScore 추세
- `shared/status.py:project_signal` — **분장 이행 기준**(지연 건수·최장 경과일·미해결 이슈). 🔴 지연 3건↑/최장 14일↑ · 🟡 지연 1~2/최장 7일↑/이슈 5건↑ · 🟢 지연 없음 · ⚪ 열린 분장 0건=판정 보류(색 안 칠함). `HEALTH_WEIGHTS` 5차원은 정의로 보존(확장 슬롯), `signal_missing`이 결측 축을 회색 라벨로 노출
  - 실측 분포: **red 5 · amber 8 · green 2 · gray 6** (여수 섬 박람회 지연 14/18건이 최악)
- 대표창 ⑤ 진행상황에 신호등 칩 + **`선언 On Track ↔ 자동 🔴` 불일치 배지**(brief.status 자동 덮어쓰기 없음 — 사람의 판단을 지우지 않는다). 지연 칩은 신호등 why와 중복이라 제거
- weekly는 주간 스코프만 읽어 신호등이 오해를 만들므로 **대시보드에만 적용**(간트 컬러바·statbar 타일은 도입 안 함)
- ReportScore: 메타 읽기 `A2:L`→**`A2:O`**, `_rec`에 score/report_type/score_mode, `_score_stats`/`_prev_week_data`/`_attach_score_trend`, `_score_row` 표시(`body.is-admin` 게이트 재사용), 텔레그램은 팀 평균만
  - 결번(W29·W30) → 추세 생략 / mode 상이 → `delta=None` + "채점 기준 변경 — 비교 생략"(strict 전환 오독 방지) / |Δ|≤5 = 보합
  - **첫 실측 W30 생성**(3주 만): 채점 95건·전체 평균 44·A 50(n=50)/B 68(n=7)/C 72(n=6)·파트 평균 65~71·개인 40~78

### WS4 — 나쁜 소식 전달
- `27-team-ops-guide/team-ops-guide-v1.html` **규칙 ⑥ 신설**(2026-07-27 확정): 헤드라인 완화 금지 + 금지 완충어(=`report_score.RUBRIC_RULES_STRICT`와 **같은 목록** — 채점기와 가이드가 다른 말을 하면 학습이 안 된다) + 5항목 구조 + 에스컬레이션 임계값(`approval-rules.json`이 SSOT, 표는 반영)
- `daily-brief-aggregate.py`: `BRIEF_PROMPT` anomaly ⑤(나쁜 소식 매장 — 부정 정보가 긍정 서술 종속절에 묻힘) ⑥(완화 어휘로만 서술된 리스크) 추가 · `_stagnant_assigns` **결정론적** 정체 감지(LLM 아님 — 정체는 날짜 산수)
- `_telegram_brief` → `_brief_message` 분리 + **역피라미드**: 헤드라인(이미 `data["headline"]`에 있었으나 HTML에만 쓰였다 — 배관만 연결) → `▶ 지금 하나`(별도 랭킹 없이 `sort_items` 1순위 = 대표창과 같은 답) → 카운트(0 범주 생략) → `그 다음` top5[1:]. headline 빈값이면 L1 생략(빈 줄이 첫 줄 되는 사고 방지). `--no-telegram` 시 메시지 stdout 출력
- 검증: `tests/test_ops_guide_thresholds.py` **24/24**(문서 임계값 ↔ approval-rules.json 대조)
- `_stagnant_assigns` 실측 0건 — 코드 정상이나 지연 46건의 **최장 경과가 10일**이라 14일 임계 미달(며칠 내 발현). 마감 미기재 16건은 기존 미지정 큐가 잡는 별건

### 열린 항목
- **맥미니 배포 미실행** — 로컬만 반영. 대상: `shared/{status,assign_sheet,provenance,meeting_link}.py` + `dashboard-server.py` + `daily-brief-aggregate.py` + `weekly-report-aggregate.py` + `daily-report-bot.py`. 배포 전 **베이스 해시 대조**(로컬≠맥미니 선례) · `py_compile` 3.9.6 · dashboard+bot kickstart
- **루트 `00-system/02-scripts/status.py`(5상태 구버전) 제거 보류** — 삭제 명령이 거부됨. `import status` 참조 0건이지만 `sys.path.insert(0, SCRIPTS)` 때문에 지금도 import가 성공하므로 맥미니 배포 시 혼동 위험. 백업 = scratchpad + git 이력
- **Phase 6 (2026-08-17)**: shadow 3주 위반 실측 후 `ARISA_TRANSITION_MODE=enforce` plist env 1줄 플립(재배포 없음). report_score `GRACE_END`(10/20)와 겹치지 않게 앞으로 뺐다
- **Phase 7 (2026-08-24 트리거)**: `status_log.stalled_since` = "3주 상태 변화 없음". **선행 조건 `load_history` ≥ 200건** — 미충족 시 착수하지 않는다(지금 만들면 항상 빈 배열인 죽은 코드)
- Timeline·Budget·Quality 헬스 차원은 `brief.end` 실제 종료일 관리 + status_log 축적 후 opt-in

### ⚠️ 배포 중단 — 맥미니가 58 커밋 뒤처져 있다 (2026-07-27 확인)
전수 배포를 승인받아 착수했으나 **베이스 해시 대조 단계에서 중단**했다. 이번 변경분을 밀어 넣으면 실행 중인 봇이 깨질 수 있다.

| 확인 항목 | 결과 |
|---|---|
| 맥미니 git HEAD | `9762222` (feat(shell): 입퇴사 온보딩 바로가기) — **로컬이 58 커밋 앞섬** |
| 맥미니 미커밋 변경 | 307개 파일 (pull 안 된 상태 + 로컬 변경 혼재) |
| `shared/status.py` | 맥미니 **93줄** = R4 이전 5상태 구버전 (로컬 HEAD 133줄 13상태) |
| `dashboard-server.py` | 맥미니 **3572줄** vs 로컬 HEAD 6112줄 (2540줄 차이) |
| 최신 마커 | `ASSIGN_TERMINAL_STATES`·`PM_CLEAR_CHOICES`·`sort_items`·`project_cards` 맥미니에 **전부 없음** |
| 대시보드 서비스 | **맥미니에서 실행되지 않음** — `ps`/`launchctl`에 dashboard-server 없음 |
| 실행 중인 것 | `com.arisa.daily-report-bot`(PID 9949, 구버전 코드) · zero-server · second-brain · watcher · cloudflared · basket.ops-bot |
| LAN 접속 | `macmini`(192.168.219.249:22) 타임아웃 → `macmini-ts`(Tailscale)로만 접속됨 |

**차단 사유**: 새 `shared/status.py`(전이 게이트·신호등)는 맥미니의 구버전 소비처(`dashboard-server.py` 3572줄, `ASSIGN_TERMINAL_STATES` 없음)와 맞지 않는다. shared만 넣으면 구 소비처가, 소비처만 넣으면 shared가 깨진다. 실행 중인 봇(9949)이 직접 영향을 받는다.

**선행 작업 필요**: 이번 WS 배포가 아니라 **맥미니 58커밋 동기화**가 먼저다. 맥미니 미커밋 307개 파일의 정체 파악(맥미니 고유 작업인지 단순 dirty인지) → 커밋/스태시 판단 → pull → 서비스 재기동 순서. 별도 세션 권장.

**정합성 경고**: 기존 progress·메모리에는 R4 1~5차와 정보기준 v1이 "맥미니 배포 완료"로 기록돼 있으나 **실제 맥미니 파일에는 반영돼 있지 않다**. 어느 시점부터 배포가 끊겼는지 확인이 필요하다(대시보드가 맥미니에서 돌지 않는 것과 같은 원인일 가능성).

## 2026-07-27 — ARISA ↔ HR 포털 SSO 통합 (플랜: partitioned-beaming-turing)

### 발단
김도영님 HR 포털 로그인 불가 신고 → 조사 결과 비밀번호를 잊은 게 맞았으나 **셀프 리셋이 본인에게 도달할 수 없는 구조**였음(카카오워크 이메일 매칭 실패 → 대표 방으로만 폴백). 같은 점검에서 비밀번호 미설정 계정 2건(이메일만 알면 로그인 가능) 발견. → "HR 포털 별도 비밀번호 체계 자체가 사고 원인" 판단 → ARISA 로그인으로 통합.

### 선행 조치 (SSO 이전)
- 메신저 발송 채널 카카오워크 → **텔레그램 전환**: `messenger.provider=telegram`(settings), `TELEGRAM_BOT_TOKEN`=ARISA 일일보고봇, `OWNER_CHAT_ID` 등록
  - ⚠️ 전환 전제가 전무했음 — 봇 토큰 미설정 + `telegram_chat_id` **0/13**. ARISA `arisa-employees.json`의 `by_telegram_id`에서 재직자 11명 백필
  - 사용자 노출 문구를 provider 연동형으로 수정(`_messenger_label()`) → 토글 롤백 시 문구도 함께 되돌아감
- 비밀번호 리셋·가이드 발송: 김도영·김준호·윤혜정 3명 (미설정 2건 해소 → 재직자 11/11 비번 설정)

### SSO 아키텍처 — 서명 티켓 + 톱레벨 리다이렉트
```
ARISA 셸 "HR 포털" 탭 → window.open('/sso/hr')
  → ARISA: arisa_sid 쿠키 검증(기존 _gate) → HS256 티켓 서명(TTL 90초, jti 1회용)
  → 302 https://rent-hr-portal.fly.dev/sso/arisa?t=<jwt>   ← 톱레벨이라 SameSite=Lax 통과
  → HR: 서명·exp·iss·aud·purpose 검증 + jti 소비 → arisa_name 매핑 → 세션 발급
  → 303 /?sso=1 → SPA가 /api/me로 신원 복원
```
- **핵심 발견**: HR 탭이 원래 iframe이 아니라 `window.open` 새 탭이었음 → SameSite 우회·iframe 개조 불필요. 목적지 한 줄만 교체
- cross-site fetch·iframe 미사용 → `SameSite=None` 완화 없음

### 보안 정책 (대표 확정)
- **admin ceiling**: SSO 진입 시 `admin`→`staff`로 낮춤. 대표 본인도 예외 없음. 전 직원 급여·주민번호는 기존 이메일+비밀번호 로그인 전용
- **세션 수명**: `session.permanent=False` — 브라우저 종료 시 만료 (30일 상속 거부)
- **권한은 티켓으로 넘기지 않음** — HR role은 항상 employees.json에서만. 티켓의 `arisa_role`은 로그용
- fail-closed: 매핑 0건/중복/차단/name 누락 전부 세션 미생성 + `?sso_error=` 안내

### 변경 파일
| 위치 | 내용 |
|---|---|
| `00-system/02-scripts/shared/sso_ticket.py` | 신규 — HS256 서명기(stdlib만, `ensure_ascii=True`로 한글 sub 이스케이프) |
| `00-system/02-scripts/dashboard-server.py` | `/sso/hr` 라우트, 탭·퀵링크 SSO 경유, PIN 정책 강화 |
| HR `sso/{__init__,token,routes}.py` | 신규 블루프린트 — `onboard/token.py` 패턴 복제 |
| HR `hr-portal-server.py` | 블루프린트 등록, `_PUBLIC_ENDPOINTS` 추가, **`/api/me` 신설** |
| HR `settings.py` | `arisa_sso.secret`(마스킹) + `arisa_sso.enable`(기본 0) |
| HR `portal-v2/components/App.jsx` | 부팅 하이드레이션 — localStorage를 SSOT→**캐시**로 강등 |
| HR `Dockerfile` | `COPY sso ./sso` |
| `/data/employees.json` | `arisa_name` 11명 백필 + role 정리 |

### 실행·검증
P0 매핑(11/11, 중복·NFD 0) → P1 다크배포 → P2 프런트 → P3 티켓검증 9종 → P4 ARISA 라우트 → P5 탭 전환 → P6 PIN 정책. 각 단계 독립 롤백.
- 브라우저 실검증: 배성원·김도영·최원석 3계정 — 로그인창 없이 진입, 본인 이름 표시, 관리자 UI 미노출, 콘솔 에러 0
- 이중 킬스위치: HR `ARISA_SSO_ENABLE=0`(30초) / ARISA `.env` 한 줄 삭제(평문 URL 폴백)

### ⚠️ 사고 2건 (교훈)
1. **리플레이 방지 실패** — jti 소비 세트를 인메모리 dict로 두었는데 gunicorn `--workers 2`라 워커가 다르면 같은 티켓이 통과. `/data` 볼륨 파일 + `flock`으로 전환, 저장소 오류 시 fail-closed. **검증에서 잡지 못했으면 그대로 나갈 뻔한 구멍**
2. **맥미니 대시보드 다운(약 1분)** — 로컬 `dashboard-server.py`를 통째로 scp했는데 로컬본이 미배포 변경분(`shared/provenance`, `shared.status.is_overdue`)을 요구해 기동 실패. 백업 복원 후 **배포본에 SSO 부분만 패치**하는 방식으로 전환
   → **교훈: 맥미니는 로컬보다 뒤처져 있다. 전체 복사 금지, 부분 패치할 것**

### HR 권한 레벨 정리 (대표 지시)
staff / lead / admin 체계로 가되 lead는 후속. **대표 외 전원 staff** — 배성원·전제훈 `manager`→`staff`(7/22 승인권 회수로 이미 staff와 동일 권한이었음), 최원석만 admin.

### PIN 정책 강화
최소 8자 + 숫자전용 거부 + 반복문자 거부 + 5회 실패 시 15분 잠금. 기존 PIN은 변경 시점부터 적용(강제 무효화 시 락아웃 우려).
- 미충족 2명 중 대표 완료(11자 혼합, 옛 PIN 거부 확인) / **윤혜정 1명 잔여** → 텔레그램 안내 발송
- `com.arisa.pin-policy-check` launchd 1회성 예약(**2026-07-30 09:00**): 미충족 시 본인 리마인드 + 대표 보고, 실행 후 자체 해제

### 잔여 리스크
- **퇴사처리 갭**: `/퇴사처리`가 HR 포털을 건드리지 않아 발급된 HR SSO 세션은 독립 생존. 브라우저 종료 만료 정책이 노출 창을 좁힘. 완전 차단하려면 HR `blocked` 처리 추가 필요
- fly 머신 스케일아웃 시 jti 볼륨이 머신별 분리 → 리플레이 창 재개방 (현재 1대)

### 병렬 세션 충돌로 origin/main이 깨졌던 사건 — 복구 완료 (2026-07-27)
맥미니 동기화를 조사하다 발견. **다른 세션이 같은 시간대에 HR 포털 SSO 작업을 진행**하고 있었고, 그 세션의 커밋에 이 세션의 미커밋 `dashboard-server.py` 변경이 함께 들어갔다.

| 항목 | 내용 |
|---|---|
| 섞인 커밋 | `e16b9b2 feat(arisa): HR 포털 SSO — /sso/hr 티켓 발급 라우트 + shared/sso_ticket.py` |
| 함께 들어간 것 | dashboard-server.py의 WS 변경 전량 — `meeting_link` import · `check_transition` 2 · `_attach_deps` 3 · `project_signal` · `mwDepsChip` 2 |
| 빠진 것 | `shared/meeting_link.py`(신규) · `shared/status.py`·`assign_sheet.py`·`provenance.py`의 신규 함수 |
| 결과 | **origin/main의 dashboard-server.py가 `ModuleNotFoundError: shared.meeting_link`로 기동 불가.** HEAD를 archive해 실측 확인 |
| push 여부 | e16b9b2가 origin/main 조상 = **GitHub에 깨진 커밋이 올라가 있었다** |
| 맥미니 영향 | 없음 — 맥미니는 `9762222`에 머물러 그 커밋을 받지 않았다. 배포를 중단한 것이 결과적으로 맥미니를 보호했다 |

**복구**: `cf7c269 fix(arisa): 깨진 HEAD 정합 복구 — WS1~4 누락 모듈 커밋` → push. 커밋 전 `git add -A`를 쓰지 않고 **내 파일 13건만 명시 지정**했다(당시 워킹트리에 다른 세션의 대량 삭제 200여 건이 섞여 있었다). push 전 `git archive HEAD` 후 단독 import + 테스트 재실행으로 정합을 실측 확인(4모듈 정상 · 51/51 · 35/35).

**교훈**: 두 세션이 같은 파일을 동시에 만지면 `git add`가 남의 미커밋 변경을 삼킨다. 병렬 작업 시 커밋은 **파일을 명시 지정**하고, 커밋 후 `git archive HEAD`로 정합을 확인한다(테스트 통과 ≠ 커밋 정합).

### 맥미니 동기화 — 지금 하지 않는다 (2026-07-27 판단)
조사 중 **맥미니 파일이 실시간으로 바뀌는 것을 관측**했다. scp로 가져온 시점의 `dashboard-server.py` md5가 커밋 `9762222`와 정확히 일치했는데, 직후 맥미니에서 `git diff HEAD`를 돌리자 SSO 패치 85줄이 미커밋으로 나타났다 — 다른 세션이 그 사이에 맥미니로 SSO를 배포하고 있었다.

- 맥미니 미커밋 3종(`dashboard-server.py` M · `check-pin-policy.py` ?? · `shared/sso_ticket.py` ??)은 **모두 로컬에 이미 커밋된 내용**(e16b9b2·e769c69) = 맥미니 고유 손실 위험은 없다
- 그러나 **다른 세션이 능동적으로 조작 중인 대상에 pull/checkout/scp를 하면 그 작업을 파괴한다**
- 맥미니 실제 미커밋은 8건뿐이다(앞서 기록한 307건은 mtime 기반 초기 stat — `git status` 실행으로 인덱스가 갱신되며 정리됨). 동기화 자체는 fast-forward로 단순하다
- LAN `macmini`(192.168.219.249:22) 타임아웃 지속 → Tailscale `macmini-ts`만 가용. remote로도 등록돼 있다(`ssh://macmini-ts/...`)

→ **선행 조건: HR SSO 세션 종료 확인.** 그 뒤 맥미니에서 `git stash`(또는 미커밋 3종이 로컬 커밋과 동일함을 확인 후 `checkout`) → `git pull` → 서비스 재기동. 대시보드가 맥미니 launchctl에 아예 없는 원인도 이때 함께 확인한다.

### 맥미니 동기화 완료 (2026-07-27 19:47)
크로스체크 결과 **다른 세션이 이미 맥미니를 진행시켜 놓았다** — HEAD가 `9762222` → `f940ad5`(R4 개편 1·2·3차 반영)로 올라가 있었고 `com.arisa.pin-policy-check` 잡이 신규 등록돼 있었다. 그 위에 이어서 동기화했다.

**절차와 안전장치**
1. 무손실 검증 — 맥미니 미커밋 `dashboard-server.py`의 추가 85줄이 **전부 로컬 커밋에 존재**함을 확인(삭제 7줄 중 1건은 주석 부분문자열 매칭 오탐). `check-pin-policy.py`·`sso_ticket.py`는 md5까지 로컬 HEAD와 **완전 동일**
2. 백업 — `/tmp/dashboard-server.py.bak-presync-20260727`(5769줄)
3. `git stash push` 2회 — tracked(dashboard-server + pycache) / untracked(sso 파일 2종). `rm` 대신 stash를 써서 되돌릴 수 있게 했다
4. `git pull --ff-only` — 1차는 untracked 2종 충돌로 abort(사전 확인에서 innisfree·inbox만 보고 이 둘을 놓쳤다) → stash 후 재시도 성공
5. 검증 — 8파일 md5 **로컬과 전부 일치** · `py_compile` 3.9.6 8건 통과 · shared 5모듈 import+함수 정상 · **테스트 110개 통과**(51/35/24) · 루트 `status.py` 제거 확인 · 모드 `shadow` / enforce 2026-08-17

**보존된 맥미니 고유 파일**(untracked 3건, pull이 건드리지 않음): `10-projects/40-innisfree-sns/` · `80-r-tech/84-scripts/innisfree/` · second-brain inbox 1건

**⚠️ 앞선 기록 정정 — 대시보드는 맥미니에서 정상 가동 중이다.** 이 문서 위쪽에 "대시보드가 맥미니 launchctl에 아예 없다"고 두 번 적었으나 **사실이 아니다**. `com.projectrent.dashboard`(KeepAlive=true·RunAtLoad=true, 8780 LISTEN)로 돌고 있었고, 첫 조사에서 `launchctl list | grep ... | head -20`에 잘려 놓친 것이었다. `com.projectrent.r4meeting`(8781)도 가동 중.

**서비스 반영 상태**
| 대상 | 처리 |
|---|---|
| `com.arisa.daily-report-bot` | **04:00 자동 재시작에 맡김**(`com.arisa.daily-report-bot-restart`). 변경은 `set_status_guarded` 하나이고 shadow 모드라 동작 변화 0 — 오늘 20:00 보고를 구코드로 받아도 결과가 같다 |
| 배치(daily-brief 07:30 · weekly 월 08:30) | 재기동 불필요 — 실행 시 파일을 읽으므로 **이미 반영 완료** |
| `com.projectrent.dashboard` | **KeepAlive라 자동 재시작이 없다**(죽을 때만 작동). 프로세스가 19:12:54 시작 = pull 이전이라 구코드를 물고 있었음 → **2026-07-28 00:00 재기동 예약**(맥미니 nohup PID 19384 → `launchctl kickstart -k gui/501/com.projectrent.dashboard`, 로그 `/tmp/dash-restart-20260728.log`) |

**다음 세션 확인 항목**: ① `/tmp/dash-restart-20260728.log`에 kickstart 기록·새 PID가 남았는지 ② 대시보드 '내 업무'에 회의 출처 분장의 선행/BLOCKING 칩, 대표창 ⑤에 신호등이 뜨는지(첫 회의 제출 후) ③ `status-log/assign-status.jsonl`에 `[transition-shadow]` 위반이 쌓이는지 → 08-17 enforce 판단 근거 ④ 맥미니 stash 4건 정리 여부(pre-sync 2건은 로컬 커밋과 동일함이 검증됨 → drop 가능)

## 2026-07-27 (2차) — 산출물 소실 사고 + 재발 방지

### 사고
대시보드가 **18일 전 브리프(7/09)와 3주 전 주간(W28)** 을 서빙 중인 것을 발견. 배치는 정상이었다.
```
07:31 daily-brief-2026-07-27 정상 생성 (로그 ✅)
08:30 weekly-report-2026-W30 정상 생성 (로그 ✅ + 텔레그램 전송)
09:47 git reset --hard  → 미커밋 산출물 삭제
12:32 git pull          → 커밋에 있던 7/09·W28로 복원 (brief/ 21개 덮어씀)
```
**원인**: `brief/`·`weekly/` 산출물이 git 추적 대상. 배포할 때마다 당일 결과물이 커밋 시점으로 되돌아감.
**아무도 몰랐다** — 배치 로그는 성공, 화면은 조용히 과거를 보여줌.

### 조치 1 — 추적 해제 (근본)
- `.gitignore` 추가: `brief/daily-brief-*`, `brief/person/`, `weekly/weekly-report-*`
- `git rm --cached` 130건 (커밋 `044f5dc`). 로컬 파일 보존
- ⚠️ 다른 클론 pull 시 작업트리에서 삭제됨 → 맥미니는 `tar czf` 백업(149파일) → pull(127→13) → 복원(127) 순서로 진행
- 검증: `git reset --hard` 실제 실행 후에도 산출물 생존 확인

### 조치 2 — 복구
- `daily-brief-aggregate.py` 재실행 → 7/27 전사+팀별 4종
- `weekly-report-aggregate.py --week last` → W30 전사+팀별 4종 (384건·10명·미매칭 0)
- 대시보드 서빙 확인: `대표 Daily Brief · 2026-07-27` / `주간 업무 대시보드 · 2026년 W30`
- W29는 미복구 — 과거 날짜 재생성은 시트 윈도우 만료 위험

### 조치 3 — 감시 (원인 무관 탐지)
`arisa-artifact-guard.py` + `com.arisa.artifact-guard` (매일 **10:00·18:00** 2회, 사고가 09:47·12:32에 났으므로 오전 1회로는 부족)
1. 오늘자 브리프 존재 / 최신 브리프가 과거 날짜인지
2. 지난주 주간 리포트 존재
3. **산출물이 다시 git 추적됐는지** — 재발 방지 장치 자체를 감시
이상 시 대표 텔레그램 알림. 정상/이상 양쪽 판정 검증 완료(브리프 임시 은닉 → 탐지 → 복원 확인).

### 남은 위험 (판단 필요)
배치가 쓰는데 여전히 git 추적 중 — 되돌려지면 이력·명부가 과거로 회귀:
- `20-operations/23-arisa/status-log/assign-status.jsonl` (업무 상태 로그)
- `00-system/02-scripts/offboarded.json` (**퇴사 차단 명부** — 되돌려지면 퇴사자 접근 부활 가능)

### 조치 4 — 런타임 상태 파일도 추적 해제 (대표 지시)
같은 함정에 걸려 있던 2건 추가 처리 (커밋 `433f5ce`):
- `00-system/02-scripts/offboarded.json` — 퇴사자 차단 명부. 되돌려지면 **차단 해제된 퇴사자가 봇에 재접근** 가능
- `20-operations/23-arisa/status-log/` — 업무 상태 로그. 맥미니 1807B/5줄 vs 커밋본 340B/1줄로 이미 벌어져 있었음
두 파일 모두 어떤 스크립트도 git add/commit 하지 않는 순수 런타임 상태 → 추적 해제 안전.

⚠️ 맥미니 pull이 두 번 막혔다:
1. `assign-status.jsonl` 로컬 수정분 → `git checkout --`로 정리(백업 있었기에 안전)
2. **내가 앞서 scp한 `arisa-artifact-guard.py`가 미추적 상태로 남아 커밋과 충돌**
   → 커밋본과 동일함을 diff로 확인 후 제거하고 pull
   교훈: scp로 맥미니에 먼저 올린 파일은 나중에 같은 경로로 커밋될 때 pull을 막는다.

검증: `git reset --hard` 실행 후에도 offboarded 1명·assign-status 5줄 보존, 조나연 차단 유지 확인.

### 파수꾼 확장
`arisa-artifact-guard.py`에 상태 파일 감시 추가:
- 존재 여부 + **항목 수 비감소** (`.guard-state.json`에 기준선 보관)
- 4종 파일 재추적 감시(브리프·주간·offboarded·assign-status)
검증: 명부를 2명→1명으로 축소시켜 `⚠️ 퇴사자 차단 명부 항목 감소 2→1` 탐지 확인.

### 대시보드 재기동 검증 (2026-07-28 06:40)
예약대로 **00:00:06 kickstart 실행** — PID 28230, 이후 6시간 40분 연속 가동(재시작 루프 없음 = import 성공). 로그 `/tmp/dash-restart-20260728.log`.

"배포했다 ≠ 동작한다" 원칙에 따라 5단계로 확인했다:

| 단계 | 결과 |
|---|---|
| 에러 로그 | `/tmp/pr-dashboard.err` **최종 수정 7/27 18:51** = pull(19:40)·재기동(00:00) 이전. 재기동 후 한 줄도 안 쌓임. (로그에 보이는 `is_overdue` AttributeError·`provenance` ImportError·`주간분장!A2:L5000` 타임아웃은 전부 **pull 이전 구버전 시절의 과거 기록**) |
| HTTP | 200 · 91,882 bytes · 2.7ms |
| 서빙 코드 | `mwDepsChip` `mw-deps` `signal_why` `declared_mismatch` 등 6개 마커 전부 포함 |
| JS 문법 | 인라인 스크립트(68,815 bytes) 추출 → `node --check` **파싱 에러 0** |
| 브라우저 렌더 | SSH 포워딩(18780→8780) + headless Chromium. **콘솔 에러 0**, 로그인 게이트 렌더, 본문·탭 정상 |
| **실사용 흐름** | 로그인 시도 → `POST /api/login → 401` → 화면에 "등록되지 않은 이름입니다." 렌더. **JS 완전 정상 확정** |

⚠️ **중간에 오진할 뻔한 지점**: `browse js "typeof mwDepsChip"`이 `undefined`를 반환했다. 그런데 내가 만들지 않은 기존 함수(`mwSrcChip`)와 로그인에 필수인 `doLogin`·`SESS`도 똑같이 undefined였다 — `browse js`가 **격리 실행 컨텍스트(isolated world)**에서 돌아 페이지 전역에 접근하지 못하는 것이 원인이었다. DOM 조회(`document.querySelectorAll('script').length`=1)는 되는데 전역 변수만 안 보이는 것이 그 증거. 실제 클릭 흐름으로 교차확인해 페이지 정상을 확정했다. **`typeof X === undefined`를 배포 실패 근거로 쓰지 말 것.**

**미확인(정직하게 남김)**: 로그인 후 화면 — 내 업무 카드의 선행/BLOCKING 칩, 대표창 ⑤ 신호등은 PIN이 없어 직접 보지 못했다. 회의 의존성 칩은 애초에 `project-docs/` 회의 제출 이력이 0건이라 표시할 데이터가 없다(첫 회의 제출 후 확인 대상).

### 실화면 검증 — 신호등 작동 확인 (2026-07-28, 대표 로그인 화면)
대표창 ⑤ 진행 상황에 **`월드모드홀딩스 🟢 열린 7건 · 지연 없음`** 렌더 확인 = `shared/status.py:project_signal`의 green 판정 + `why` 문자열 그대로. 7섹션 전부 정상, JS 깨짐 없음. **배포 검증 완결.**

- ⚠️ 사전 예측 정정: "red 5·amber 8·green 2·gray 6이 화면에 뜬다"고 안내했으나 **대표창 ⑤는 `summary[:4]`(이번 주 활동 있는 상위 4개)** 필터가 걸려 1개만 노출된다. 실측치는 전체 21개 프로젝트 대상이었다 — **스코프가 다르다**. 화면 예측을 말할 때는 그 화면의 필터를 먼저 볼 것
- 월드모드홀딩스는 실측 당시 없던 신규 등록 프로젝트(/프로젝트등록 스킬 도입분)
- 아직 안 보이는 것(전부 정상): 회의 선행·BLOCKING 칩(회의 제출 0건) · 불일치 배지(green이라 해당 없음) · 🔴(화면 최장 D+11 < red 임계 14일 → **3일 뒤 전환**) · 14일 정체 anomaly(동일 사유)
- **남은 한계**: 신호등은 대표창 ⑤에만 적용. 프로젝트 탭(포트폴리오 21개 전체 목록)에는 미적용 — 전체를 신호등으로 훑으려면 별도 작업 필요

### 주간 리포트 "결번" 규명 — 자동화는 멈춘 적이 없었다 (2026-07-28)
W29 결번·브리프 17일 공백을 추적한 결과, **배치는 정상 작동 중이었고 산출물이 배포에 되돌려진 것**이었다. 이미 `044f5dc`(07-27 22:34)에서 조치 완료된 사고였다. 커밋 본문에 경위가 그대로 있다:
```
07:31 배치가 daily-brief-2026-07-27 정상 생성
09:47 git reset --hard → 미커밋 산출물 삭제
12:32 git pull → 7/09 브리프로 복원 (brief/ 21개 덮어씀)
```
산출물이 git 추적 대상이라 배포마다 마지막 커밋 시점(7/09)으로 되돌아갔다 — 그래서 파일 목록이 "7/01~7/09 + 7/27~28"로 보였다. **7/27 08:30 weekly 로그 전문에 W30 정상 생성이 남아 있다**(`/tmp/pr-weekly-report.log`). 잡 등록은 7/8, 자동로그인 켜짐, 슬립 0 — 실행 환경에는 문제가 없었다.

**044f5dc가 빠뜨린 구멍 2건 보완** (커밋 `c2ff63f`, **push 보류**):
- `decisions/decisions.jsonl` — Engine D append 로그인데 추적 중이었다. 맥미니에만 07-28 07:46 결정 1건(590B, "2차 성수 팝업 제안 가안 검토·방향 확정")이 있고 로컬엔 파일이 없는 상태였다 → gitignore + `git rm --cached`. **백업 2중**: scratchpad + 맥미니 `/tmp/decisions.jsonl.bak-20260728`
- `weekly/weekly-data-*` — 규칙이 `weekly-report-*`만 막고 있었다. 현재 미추적이라 잠재 위험이었으나 `git add -A` 한 번이면 재발
- ✅ **전이 게이트 shadow 로그는 안전 확인** — `status-log/`는 044f5dc에서 이미 ignore. 08-17 enforce 판단 근거는 배포에 지워지지 않는다
- 판단 보류: `arisa-employees.json`은 `/퇴사처리`가 수정하는 3파일 중 유일하게 추적 중이나, 실질 차단선(`users.json`·`offboarded.json`)이 이미 보호되고 명부는 형상관리 가치가 있어 그대로 둔다

### ⚠️ 구조적 문제 — 로컬과 origin이 분기했다 (push 차단)
`c2ff63f`를 push하려다 발견. **로컬 12 vs origin 11 커밋 분기.** patch-id 대조 결과:
- 9개는 origin에 **동일 패치가 이미 존재**(제목 같고 해시 다름 = 같은 작업이 양쪽에 따로 커밋됨)
- 로컬에만 있는 고유 3개 = 내 `c2ff63f` + 다른 세션 미push 2건(`965fe77` MaaS 모달, `f575345` 포트폴리오 3종 등록본)

`git rebase --autostash origin/main`은 **untracked `80-r-tech/84-scripts/innisfree/*.py`가 origin 커밋과 같은 경로**여서 checkout 단계에서 중단됐다(autostash 복원, HEAD 무손상). 더 진행하면 다른 세션의 작업물을 건드리게 되므로 멈췄다.

**뿌리는 어제 origin이 깨졌던 것과 같다** — 두 세션이 같은 워크스페이스에서 동시에 커밋·push한다. 병렬 세션이 정리된 뒤 한쪽에서 일괄 정리해야 한다.

**당장의 위험은 없다**: gitignore는 로컬에서 이미 작동(`check-ignore` 확인), 맥미니 결정 로그는 이중 백업, 배치·대시보드·봇 모두 정상 가동.

### 지연 45건 — PM별 정리 요청 발송 (2026-07-28)
"상태가 안 움직인다" 진단의 첫 실전 대응. **지연 45건 중 42건이 미착수** — 등록 후 손대지 않은 채 마감이 지난 업무가 대부분이다.

| 대상 | 건수 | 내용 |
|---|---|---|
| 윤혜정 | 24 | 여수 섬 박람회 13 · 아랑재 4 · 리진 2 외 4개 · 최장 D+11 · 중복 등록 1건 경고 포함 |
| 배성원 | 2 | 연구전담부서 등록 · D+11 |
| 전제훈 | 2 | R-LAB · D+6 |
| 대표 요약 | 17 | PM 미지정 8 + 대표가 PM인 9 (보낼 대상이 없어 대표봇으로 별도) |

전원 발송 성공(직원봇 개인 메시지 · 대표는 대표봇). 기한 7/30(수).

**메시지 설계 핵심 — "완료만 답이 아니다"**: ①하는 중이면 진행 전환 또는 마감 재설정 ②끝났으면 완료 ③안 하기로 했으면 종료 처리(패스·취소·미실행종료) + 사유. 미착수 42건이라는 숫자는 "다들 일을 안 했다"가 아니라 "접어야 할 업무가 섞여 있는데 아무도 닫지 않았다"에 가깝다고 보고, 닫는 것도 정상 업데이트임을 명시했다.

**부수 발견**: `착수 보고서 전체 내용 정리 (윤혜정)`이 같은 D+10에 진행중·미착수로 **중복 등록**돼 있었다. 같은 업무명+담당자가 2건 이상이면 메시지에 경고를 넣도록 스크립트에 반영. 초안 단계에서는 대상 프로젝트가 가나다순으로 뽑혀 실제 비중(여수 13건)을 가렸던 것도 건수 순으로 교정했다.

스크립트: scratchpad `pm_overdue_send.py` (일회성). 정례화하려면 `_overdue_open_count`를 쓰는 브리프 쪽에 붙이는 편이 낫다.

### 병렬 세션 분기 해소 + 맥미니 동기화 완료 (2026-07-28 22:20)
아리사 관련 세션 종료 후 정리. **결과: 로컬 = origin = 맥미니 = `d5088da` 3자 일치.**

**분기는 스스로 풀렸다** — 다른 세션이 종료하며 push를 마쳐 로컬↔origin이 같아졌다(앞선 0·뒤처진 0). 그 과정에서 **내 커밋 `c2ff63f`는 해시가 사라졌지만 내용은 살아남았다**: `.gitignore`의 `decisions/`·`weekly-data-*` 규칙(121·123·135행)과 `decisions.jsonl` 추적 해제가 origin 커밋본에 그대로 반영돼 있다. 커밋 생존이 아니라 **효과 생존**을 확인하는 것이 맞는 검증이었다.

**중간에 한 번 더 시도했다가 중단한 기록**: 세션 종료 전 merge를 시도했으나 충돌 4건(프로젝트 JSON 3개 — 롱블랙·유럽·현대차 POC, `portfolio-register.py` add/add)이 전부 다른 세션의 포트폴리오 작업 영역이라 `git merge --abort`. 임시 이동한 untracked 3건(innisfree)도 md5 대조로 복원 확인. HEAD 무손상.

**맥미니 동기화 절차** (39d7ac5 → d5088da, 9커밋 fast-forward):
1. pull 차단 요인 사전 판별 — untracked ∩ 원격변경 1건(`중기-팝업스토어-jufws.json`, **md5 원격과 동일** 확인 후 임시 이동), tracked M ∩ 원격변경 1건(`decisions.jsonl`)
2. `decisions.jsonl`은 추적 해제 커밋이 오면 삭제되므로 백업 확인 후 `git checkout --` → pull(`delete mode` 확인) → **백업에서 590B 복원**
3. 맥미니 고유 변경 `arangje-2026.json`(+36줄)은 원격이 건드리지 않아 무손상 보존
4. 차단 파일은 pull이 동일 내용으로 복원(md5 확인)

**재기동 불필요 판정**: 이번 pull로 바뀐 실행 코드는 `portfolio-register.py` 하나뿐이고 **CLI 스크립트라 dashboard-server·daily-report-bot이 import하지 않는다**(grep 0건). 두 서비스 파일 변경 0건. 대시보드 HTTP 200 · 2.1ms 정상.

**교훈 — 분기는 기다리는 것이 정답이었다**: 두 번의 정리 시도가 모두 다른 세션 작업에 막혔고, 세션이 끝나자 스스로 해소됐다. 병렬 세션 상황에서 git 정리는 **양쪽이 멈춘 뒤**에만 해야 한다. CLAUDE.md 「병렬 세션 git 규율」 4항(남의 미push 커밋·untracked 불가침)이 이번에 두 번 작동했다.

### 지연 정리 후속 확인 예약 (2026-07-29 09:00)
발송한 정리 요청이 실제로 반영되는지 자동 확인. **클라우드 에이전트(/schedule)는 부적합** — 확인에 필요한 gws 인증·봇 토큰·status-log가 전부 맥미니 로컬에 있다. 맥미니 launchd 일회성 잡으로 등록했다(`com.arisa.pin-policy-check` 패턴: 특정 날짜 `StartCalendarInterval` + 실행 후 `launchctl bootout` 자체 해제).

- 스크립트 `~/arisa-oneshot/overdue-followup.py` — **git 레포 밖에 둔다**(레포에 넣으면 병렬 세션 커밋과 충돌하고 일회성 스크립트가 이력에 남는다)
- 기준선 저장 완료: **45건** (윤혜정 24 · 대표 9 · 미지정 8 · 배성원 2 · 전제훈 2)
- 내일 09:00 비교 → 처리/잔존/신규 + **처리된 건이 어떤 상태로 갔는지**(완료·승인·패스·취소 분포) + 지연은 남았지만 상태가 움직인 건 → 대표 텔레그램 보고
- 잡: `com.arisa.overdue-followup` (7/29 09:00, 로그 `/tmp/arisa-overdue-followup.log`)

**중간에 잡은 것 2건**
1. **ssh 직접 실행 시 gws PATH 누락** — 첫 스냅샷이 **0건으로 잘못 저장**됐다(읽기라 피해는 없음). progress에 이미 기록된 사고 패턴(“맥미니 수동 배치는 반드시 launchd PATH 주입 후 실행”)이 그대로 재현됐다. `PATH` + `GOOGLE_WORKSPACE_CLI_KEYRING_BACKEND=file` 주입 후 45건 정상 저장. **plist에도 두 값을 넣었다**
2. **집계 숫자 불일치** — 드라이런에서 45건이 43건으로 나왔다. 중복 등록 2건이 같은 키(날짜·업무·담당자)라 집합에서 합쳐진 것. 내일 보고에 “45건(중복 2건 제외 시 43건)”으로 둘 다 표기하도록 수정. **드라이런을 안 했으면 내일 아침에 이 혼선을 그대로 받았을 것**

⚠️ 발송 메시지 **기한 요일 오기 정정**: `7/30(수)` → 실제 7/30은 **목요일**. 4명(PM 3 + 대표)에게 한 줄 정정 발송 완료. 날짜는 7/30 유지.

### 지연 후속 확인 결과 — 하루 동안 처리 0건 (2026-07-29 09:00)
예약대로 정상 실행·발송 완료. **기준 45건(고유 43) → 처리 0건(0%) · 잔존 43 · 신규 1.** PM별 잔존: 윤혜정 23 · 대표 9 · 미지정 7 · 배성원 2 · 전제훈 2.

07-28 저녁 요청 발송 후 **24시간 동안 상태 변화가 한 건도 없었다.** 기한은 7/30(목)이라 아직 남았지만, "메시지를 보내면 움직인다"는 가정이 하루로는 성립하지 않았다는 사실은 남는다. R4 승인 흐름 0건과 같은 신호 — 알림이 아니라 **동선·주체 문제**일 가능성이 크다.

⚠️ **내 오판 기록**: 종료 정리 중 `launchctl list`에 잡이 없는 것을 보고 "예약이 유실됐다"고 판단해 재등록 + nohup 이중 예약까지 걸었다. 실제로는 **스크립트가 실행 후 `launchctl bootout`으로 자체 해제**한 정상 동작이었다(내가 그렇게 설계해놓고 잊었다). 재등록분은 `.done-20260729`로 보관 해제. **일회성 잡의 "부재"는 유실이 아니라 완료 신호일 수 있다 — 로그부터 볼 것.**

중복 실행 가드(`ran-YYYY-MM-DD.mark`, 발송 성공 시에만 생성)는 이 과정에서 스크립트에 추가됐다. 이번엔 쓰이지 않았지만 이중 예약 상황에 대비한 장치로 남긴다.

### ARISA Assistant Phase 0 — 툴 카탈로그 v1 작성 (2026-08-02)
"봇 하나 + Role 여러 개"(대표 방향) 진화를 위한 선행 산출물. `assistant-tool-catalog-v1.md`.

**전제 검증**: 명세서가 요구하는 기능의 대부분이 이미 `dashboard-server.py`(6,432줄) API로 존재 — 새로 만들 게 아니라 노출할 것. 실측 40여 엔드포인트를 READ 12 / WRITE 8 / 영구제외 7로 선별.

**🔴 최대 블로커 발견 — 쓰기 API는 봇이 호출할 수 없다**: 5533-5535에 `user`+`pin` 평문 관문. `auth()`는 users.json PIN 문자열 비교(3175). 봇이 대신 쓰려면 직원 PIN 보관이 필요 → 금지. 해법=서비스 토큰 + on-behalf-of(신원은 텔레그램 ID→`by_telegram_id`에서 도출, LLM 문자열 불신뢰), 권한 함수는 그대로 재사용. **읽기는 쿠키 세션이라 지금 당장 착수 가능** — Phase 1 = 읽기 전용.

**부수 발견 3건**
1. `receive_inquiry` 로그(맥미니 `inquiries/inbox.jsonl`) **2건 중 2건이 라우팅 실패** — 7/29 김가은이 완성된 보고 전문을 자유입력으로 보냈으나 "/report 먼저 누르고 다시 입력" 안내로 반려, 7/30 정예은은 슬래시 없는 `report`가 문의로 접수. "봇 선택 부담"보다 앞선 문제가 "말 거는 법"임을 실증
2. **폐기 기록된 봇 2개가 맥미니에서 가동 중** — `com.arisa.telegram-bot`(회의록봇, PID 692)·`com.arisa.zero-server`(ARISA ZERO), 둘 다 `arisa-project-memory/.venv`. 봇 증식 진단의 실물
3. 낙관적 잠금 — `assign-edit`(5795)·`assign-status`(5862)는 row만으로 못 쓴다. read→대조→write 3단계 강제, 409 시 재시도 금지·사용자에게 되묻기

**결정 대기 3건**: ①서비스 토큰 구현 여부(안 하면 영구 읽기전용) ②브리프 읽기 API 신설 여부(현재 파일 직접읽기는 권한 구멍) ③Phase 1 범위(READ 12 전체 vs 4종 축소)

### ARISA Assistant Phase 1 — 서비스 토큰·브리프 API·Intent Router 구현 (2026-08-03)
카탈로그 §8 결정 3건 전부 "진행" 확정 → 순차 구현. 상세: `assistant-tool-catalog-v1.md` §9.

**① 서비스 토큰** — `dashboard-server.py`에 `svc_session()` 추가. 헤더 `X-Arisa-Service`(시크릿) + `X-Arisa-On-Behalf-Tg`(텔레그램 user_id). **이름을 헤더로 받지 않는다** — 서버가 `by_telegram_id`로 도출한다. 이름을 받으면 LLM이 출력한 "최원석"이 곧 대표 권한이 되기 때문. 권한은 기존 세션 dict를 그대로 만들어 `is_admin`·`can_view`·스푸핑 게이트가 무변경 적용.
- 쓰기 화이트리스트 7종(`_SVC_WRITE_PATHS`) + POST 전체 화이트리스트(`_SVC_POST_OK`)로 이중 차단. 감사 로그 `_data/assistant-audit.jsonl`.
- **§2 함정 실제로 막음**: `/api/meeting-actions`·`/api/simulator/submit-doc`은 PIN 관문보다 **위**에 있어 쿠키 세션만으로 통과한다 → `_gate` 직후 별도 차단 없이는 서비스 토큰에 그대로 열렸다.

**② 브리프 읽기 API** — `GET /api/brief?scope=exec|team|person`. HTML 페이지(4638·4642·4650)와 **같은 역할 게이트**를 재사용(새로 쓰면 진실이 둘로 갈라진다). exec glob이 팀 브리프까지 잡는 날짜 오염을 정규식 fullmatch로 차단.

**③ Phase 1 = 읽기 5 + 요약 1** — `shared/assistant_tools.py`(툴 클라이언트, TOOL_SPECS, 스펙 밖 이름 거부) + `shared/intent_router.py`(규칙→LLM→확인질문).

**🔴 라우터가 고친 것 — 현장 실패 2건이 모두 라우팅 실패였다**
- 07-29 김가은: 보고 전문 353자를 자유입력 → 구 동작 "다시 입력해주세요" 반려. 신: conf 0.92로 그 텍스트가 곧 보고 내용. (서식 정규식이 콜론을 요구해 `목표`/`진행 과정` 단독 줄을 못 잡던 것도 수정)
- 07-30 정예은: 슬래시 없는 `report` → 문의 접수. 신: conf 0.99, 슬래시 유무 동일 취급.
- **원칙 확립: 알아봤으면 실행하거나 확인을 묻는다. 재입력을 요구하지 않는다.** 확신<0.75면 원문 보관 후 확인 질문 — 사용자 글을 버리지 않는다.

**⚠️ 봇 핸들러 등록 순서 변경 (가장 위험한 변경)** — `assistant_entry`가 `conv`의 진입점이 되면서 모든 텍스트에 매칭된다. `conv`를 `mtg_conv`·`assign_conv`보다 **뒤로** 옮겨야 회의·분장 진행 중 입력을 가로채지 않는다. 대조군 테스트로 옛 순서에서 가로챔을 재현 확인.

**검증**(전부 실서버·실데이터 기동): 서비스 인증 14/14 · 브리프 권한 15/15 · 라우터 13/13 · 핸들러 순서 4/4 · 툴 권한 필터 사람별 상이 확인. 테스트 스크립트는 job tmp(`svc_e2e.py`·`brief_e2e.py`·`tools_e2e.py`·`router_test.py`·`handler_order_test.py`).

**🔴 배포 전 미해결 3건**
1. ~~계정 없는 3명~~ → **해소.** 맥미니 원본 확인 결과 11명 전원 계정 보유(list 스키마). 로컬 `_data/users.json` 사본이 낡아 생긴 착시였다. 📌 명부 대조는 맥미니 원본에서 — 로컬 `_data/`는 미러이지 SSOT가 아니다
2. 맥미니 `.env`에 `ARISA_ASSISTANT_SECRET` 미설정 (없으면 기능 꺼진 채 가동 = 기본 차단)
3. `conv`는 `persistent=True` — 부활 세션에 등록 순서 변경이 미치는 영향은 실제 재시작으로 확인

**미배포·미커밋.** 맥미니 반영은 승인 후.

**배포 완료 (2026-08-03 17:08)** — 커밋 `d625e5b` + 병합 `765684c`, 맥미니 pull·재기동 완료.
- 배포 중 **3-3 분기 발견**: 맥미니에 다른 세션 미push 커밋 3건(basket 마감보고 분리)이 `daily-report-bot.py`를 함께 건드리고 있었다. 강행하지 않고 맥미니를 읽기만 해서 로컬로 fetch → 병합 → 양쪽 보존. **마감보고 판정을 인텐트 라우터보다 먼저** 배치(마감보고는 '매출·마감' 어휘가 많아 라우터가 report_submit으로 잡는다 → 7/29에 고친 병합 버그 재발). 그쪽 커밋 3개·새 모듈 3개 전부 origin 반영.
- 실운영 검증: 신원 도출(대표/리더/직원 각각 정확) · 미등록ID·틀린시크릿 401 · 사칭 403 · 브리프 대표 200/직원 403(08-03자 읽힘) · 영구제외(project/delete·meeting-actions) 403 · my-work 실데이터 사람별 상이(최원석 12건·정예은 1건·전제훈 18건) · 화면 렌더 정상(84KB, JS에러 0, 공개경로 200, 보호경로 401)
- 배포 코드로 **실제 미처리 입력 2건 재처리 확인**: 김가은 0.92·정예은 0.99 → 둘 다 보고 플로우 자동 진입
- 봇 로그 `report conv + assistant entry registered (last — intent router)` 확인

**⚠️ 남은 것**
- **대표 계정(8123576679) 대화 세션이 상태 2(WAITING_CONFIRM)에 멈춰 있다** — 재기동 후에도 부활. 이 상태에서 자유 텍스트를 보내면 Assistant가 아니라 옛 보고의 확인 단계로 간다. `/cancel` 후 테스트할 것
- 실사용자 텔레그램 왕복은 미검증(봇 API로는 수신 메시지를 만들 수 없다) — 대표님이 직접 한 번 보내봐야 최종 확인
- 폐기 기록된 봇 2개 여전히 가동 중(`com.arisa.telegram-bot` 692·`com.arisa.zero-server` 694)

**실사용 첫 검증 → 수정 3건 (2026-08-03 18:02, `0240d18`)**
대표님이 직접 텔레그램으로 시험. `내가할일 알려줘` ✅(단 규칙 미스 → LLM 0.90이 대신 잡음) · `report` 슬래시 없이 ✅ · **`봉은사 프로젝트 어떻게 돼가?` ❌ 업무 내용으로 먹힘**.
1. **보고 중 질문이 먹힌다** — 로그에 라우터 판정이 아예 없었다. `report`로 대화가 열려 이후 텍스트를 상태 핸들러가 전부 가져간 것. ConversationHandler 정상 동작이지만 사용자에겐 "물었는데 안 듣는" 것. → `_feed_tasks`에서 **물음표로 끝나고** 조회 인텐트 conf≥0.85일 때만 답하고 흐름 유지. **보고문은 물음표로 끝나지 않는다**는 게 안전핀
2. **조사 미흡수** — `(내|나)\s*할일`이 '내가할일'의 '가'를 못 넘음. 조사(가·는·의·한테·에게) + 일정·미완·밀린 추가
3. **빈 목록 렌더** — tasks=[]일 때 "이런 느낌이네요:" 뒤가 비는 화면. 되묻기로 변경
맥미니는 arisa-vnext 세션이 미push 6커밋 작업 중이라 병합 강행 않고 `git am`으로 패치만 얹음(오프셋 263줄, 충돌 0).

**🔴 내 실수 — origin/main 일시 파손 (`a2308da` → `a093328`로 복구)**
배포 기록 커밋의 트리가 `765684c` 병합을 통째로 되감아 basket 마감보고 12개 파일이 삭제 상태로 push됐다.
- **원인: `git worktree add -f <path> main` — 같은 브랜치를 두 워크트리에 붙였다.** 워크트리에서 커밋하면 브랜치 ref는 앞서가지만 **메인 저장소 워킹트리·인덱스는 그대로**다. 그 상태로 메인에서 커밋하면 옛 트리가 그대로 커밋된다. 부모는 최신이라 `git log`상으론 정상으로 보인다
- **직접 원인: 그 커밋만 `git archive HEAD` 정합 확인을 건너뜀** (d625e5b·765684c는 확인, 정상). CLAUDE.md 규칙 2가 정확히 이 사고를 막으라고 있는 것이었다
- 서비스 영향 0 — 맥미니는 `20786c2`(765684c 포함)라 정상 가동 중이었다. origin만 손상
- **교훈: 워크트리는 같은 브랜치에 `-f`로 붙이지 말 것.** 붙였다면 메인 저장소에서 커밋 금지, 또는 커밋 전 `git status`로 HEAD와 워킹트리 일치 확인

**남은 것**: 실사용자 왕복 재확인(수정 반영본) · Phase 2는 `[router]` 로그 오분류율 관측 후(특히 확인질문 구간 0.55~0.75) · 폐기 봇 2개(`com.arisa.telegram-bot`·`com.arisa.zero-server`) 정리

### 레거시 서비스 3종 정리 (2026-08-09)
"봇을 늘리지 말자"가 Assistant 작업의 출발점이었는데 정작 폐기 기록된 것들이 살아 있었다. 실측 후 정리.

**정리 대상 — 셋 다 실사용 흔적 0**
| 서비스 | 정체 | 근거 |
|---|---|---|
| `com.arisa.telegram-bot` (692) | 회의록봇 `arisa-project-memory/scripts/telegram_bot.py` | 로그 3,263줄이 **전부 getUpdates 폴링**, 실제 메시지 처리 0건 |
| `com.arisa.zero-server` (694) | ARISA ZERO uvicorn `*:8100` | 워크스페이스 어디서도 8100 미참조. **0.0.0.0 바인딩**이라 노출 상태였음 |
| `com.arisa.watcher` (695) | meeting_logs 폴더 감시 | 감시 대상 폴더·산출물 디렉터리 **둘 다 부재** |

**방식(가역)**: plist를 `~/legacy-disabled-20260809/`에 백업 → `launchctl bootout` → `.plist.disabled`로 개명. 셋 다 `KeepAlive=True`였어서 kill만으론 되살아난다.

**검증**: PID 692·694·695 종료 · launchd 등록 해제 · 8100 해제 · 생존 서비스 6종(daily-report-bot·second-brain·basket-ops-bot·dashboard·r4meeting·cloudflared) 정상 · arisa-os.com 200 · **관리자 알림 실발송 성공**(토큰 유효 확인만으로 끝내지 않고 실제 sendMessage로 도달 확인).

**🔴 남은 보안 사안 — @brocallmebot 토큰**
- 같은 토큰이 `.env` 2곳(`TELEGRAM_BOT_TOKEN`·`DAILY_REPORT_MANAGER_BOT_TOKEN`)에 중복
- `/tmp/arisa-telegram-bot.log`에 **평문 3,268줄**(580K). 레거시 봇엔 `TokenRedactingFilter`가 없었다 — 현행 봇 3종은 0줄로 정상
- 이 토큰은 git 히스토리에도 노출돼 있다(기존 미해결). **로그 삭제로는 안 끝나고 BotFather 로테이션이 실제 해법**
- 폴링은 멈췄으므로 지금은 발신 전용 — 노출면은 줄었다

**부수 확인**: 업무보고봇의 `/meeting`이 `Meeting Engine not available`로 비활성. 회의록 기능은 R4(8781)·대시보드 시뮬레이터 경로로 이미 이관돼 있어 레거시 봇 종료의 기능 공백은 없다.
