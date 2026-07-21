# 23-arisa Progress

ARISA 운영(브리프·대시보드·봇) 작업 이력. 세션 이어가기용.

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
