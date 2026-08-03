# ARISA Assistant — 툴 카탈로그 v1

> Phase 0 산출물. Intent Router 설계의 전제.
> 라우터는 "호출할 수 있는 것"이 확정된 뒤에야 구체적으로 설계된다.
> 작성 2026-08-02 · 근거: `00-system/02-scripts/dashboard-server.py` (6,432줄) 전수 확인

---

## 0. 이 문서가 정하는 것 / 정하지 않는 것

**정하는 것**
- Assistant가 호출할 수 있는 툴의 목록·입력·출력·권한·부작용·위험등급
- 각 데이터의 SSOT가 어디인가
- 호출 경로(HTTP API vs 모듈 직접)의 원칙
- 🔴 지금 구조로는 **쓰기 툴을 만들 수 없는 이유**와 그 해법

**정하지 않는 것**
- 인텐트 분류 규칙 (→ 다음 문서: Intent Router 설계서)
- Role 9종의 경계
- 대화 UX

---

## 1. 🔴 선결 블로커 — 쓰기 API는 지금 구조로 봇이 호출할 수 없다

`dashboard-server.py:5533-5535`에 모든 쓰기 API의 공통 관문이 있다.

```python
# 이하 쓰기: user+pin 검증
uid = b.get("user", ""); pin = b.get("pin", "")
if not auth(uid, pin): return self._send(401, {"ok": False, "error": "인증 실패"})
```

`auth()`는 `users.json`의 PIN 문자열을 그대로 비교한다(`dashboard-server.py:3175`). 즉 **쓰기 API를 호출하려면 그 직원의 PIN 평문이 필요하다.**

Assistant가 직원 대신 쓰기를 하려면 선택지는 셋뿐이다.

| 안 | 내용 | 판정 |
|---|---|---|
| A. 서비스 토큰 + on-behalf-of | 봇 전용 시크릿 헤더 + 대행 사용자명. 신원은 텔레그램 ID → `arisa-employees.json:by_telegram_id`로 확정 | ✅ **권장** |
| B. 봇이 PIN 보관 | 평문 PIN 저장. 유출 시 대시보드 + HR 포털 SSO까지 연쇄 | ❌ 금지 |
| C. 대화 중 PIN 입력받기 | 매 쓰기마다 PIN 요구. "그냥 말하면 된다"는 전제 자체가 붕괴 | ❌ |

### 안 A 구현 요건 (Phase 2 착수 전 필수)

1. `_gate` / 쓰기 관문에 서비스 인증 분기 추가
   - 헤더 `X-Arisa-Service: <secret>` + body `on_behalf_of: <직원명>`
   - 시크릿은 `.env`(`ARISA_ASSISTANT_SECRET`), 맥미니 로컬에서만 유효
2. **대행 신원은 봇이 주장하는 것이 아니라 텔레그램 ID에서 도출** — LLM이 만든 문자열을 그대로 신뢰하지 않는다
3. 권한은 기존 함수(`is_admin`/`is_leader`/`can_edit`/`can_manage`)를 **그대로 재사용** — 대행이라고 권한이 늘어나지 않는다
4. 감사: 기존 `shared/provenance.py` source에 `assistant` 추가 + `shared/status_log.py`에 대행자 기록
5. 서비스 토큰은 **쓰기 화이트리스트에 등록된 경로에서만** 유효 (아래 §5 목록)

> ⚠️ 읽기 API는 이 문제가 없다. 쿠키 세션 + `?user=` 스푸핑 방지 게이트(`dashboard-server.py:4575-4580`)로 이미 돌아간다. **그래서 Phase 1(읽기 전용)은 지금 당장 착수 가능하다.**

---

## 2. 인증 체계는 2개다 (혼동 주의)

| 체계 | 대상 | 방식 | 위치 |
|---|---|---|---|
| 쿠키 세션 | 모든 GET, 그리고 POST 중 `/api/login`·`/api/set-pin`·`/api/simulator/*`·`POST /api/meeting-actions` | `arisa_sid` 쿠키, 30일 TTL, 파일 영속 | `_gate` (4505) |
| user+pin | 그 외 모든 POST (쓰기) | body 평문 PIN | 5533 |

**함정**: `POST /api/meeting-actions`(회의 액션 → 분장 일괄 등록)는 쓰기인데도 쿠키 세션을 쓴다. 관문 라인(5533)보다 **위**에 있기 때문이다. 서비스 토큰 설계 시 이 예외를 놓치면 인증 구멍이 된다.

---

## 3. 데이터 SSOT 지도

| 데이터 | SSOT | 접근 경로 | 비고 |
|---|---|---|---|
| 업무(분장) | **구글시트 "주간분장" 탭** (`DAILY_SHEET`) | `shared/assign_sheet.py` | 파싱·컬럼·지연판정 전부 이 모듈이 단일 출처. **봇도 이미 같은 모듈로 읽는다** |
| 프로젝트 | `_data/projects/*.json` | `load_projects()` / `/api/projects` | 파일당 1프로젝트 |
| 회의록 원문 | `_data/project-docs/<pid>/<ts>.md` | `/api/project/doc` | JSON엔 메타만 |
| 결정 로그 | `20-operations/23-arisa/decisions/decisions.jsonl` | `shared/decision.py` | append-only. **git 추적 금지** |
| 상태 전이 이력 | `status-log/` | `shared/status_log.py` | 전이 게이트 shadow 로그 |
| 일일보고 원본 | 구글시트 3분할(핵심/서브/메타) | `shared/gws.py` | 봇이 직접 append |
| 대표·팀 브리프 | `23-arisa/brief/*.json`, `*.html` | 파일 직접 | ⚠️ API 없음. **git 추적 금지** |
| 개인 메모 | `24-second-brain/00_inbox/*.md` | `bot.py` / `report.py` | 최원석 전용 |
| 직원 명부 | `arisa-employees.json` | `shared/employee.py` | 텔레그램 ID 매핑(`by_telegram_id`) |
| 계정·PIN | `_data/users.json` | `load_users()` | arisa2와 symlink 공유 |

### 호출 경로 원칙

- **쓰기는 무조건 HTTP API 경유.** 시트에 직접 append하면 전이 게이트(`shared/status.py check_transition`)·이력·권한 검사를 전부 우회한다. `_assign_append`를 봇이 직접 부르는 것은 금지.
- **읽기도 기본은 HTTP.** 권한 필터(`can_view`)가 서버에 있다. 성능 문제가 실제로 생기면 모듈 직접 호출을 허용하되, **권한 필터를 봇 쪽에 재구현하지 않는다**(두 개의 진실이 생긴다).

---

## 4. READ 툴 12종 — Phase 1 착수 가능

> 전부 GET. 쿠키 세션으로 동작하므로 **지금 구조 그대로 붙일 수 있다.**
> 공통: `?user=<직원명>` 필수. 본인·담당팀·admin 외에는 403(4575).

| # | 툴 | 엔드포인트 | 입력 | 반환 핵심 | 권한 | 라우터 힌트 |
|---|---|---|---|---|---|---|
| R1 | `my_work` | `GET /api/my-work` | user | 내 미완 분장 + 내 프로젝트 태스크 + PM 승인큐 + PM 결정큐 + 오늘 계획 + 개인 일일브리프 | 본인 | "오늘 뭐 해야 돼", "내 할 일" |
| R2 | `project_list` | `GET /api/projects` | user | 열람 가능 프로젝트 전체 + `rollup`(태스크 파생 진행률) + 편집권한 플래그 | 열람권한자 | "프로젝트 목록", "뭐가 돌아가고 있어" |
| R3 | `project_detail` | `GET /api/project` | user, id | 프로젝트 전문 + 연결 분장 + 회의별 실행률(`docActions`) + 메모리 허브 | `can_view` | "LA문화원 지금 어때" |
| R4 | `meeting_doc` | `GET /api/project/doc` | user, id, ts(`\d{8}-\d{6}`) | 회의록 원문 텍스트 + 제목·작성자 | `can_view` | "지난주 회의 내용" |
| R5 | `meeting_actions` | `GET /api/meeting-actions` | user, id, ts | 그 회의에서 나온 액션 목록 + 실행률 롤업 + 지연일수 | `can_view` | "그 회의에서 나온 거 어떻게 됐어" |
| R6 | `assign_history` | `GET /api/assign-history` | user, task/assignee/pid 중 1+ | 상태 전이 이력 최대 30건 | 로그인 전원 | "이 업무 왜 멈춰 있어" |
| R7 | `lead_home` | `GET /api/lead-home` | user | 팀 Todo(2주 윈도우) + 승인 대기 + **담당 미지정 큐** + 팀 프로젝트 + 출처 분포 + 유형 분포 | 리더만 | "우리 팀 상황" |
| R8 | `exec_attention` | `GET /api/exec-attn` | user | 대표 차례인 것만(잔여 결정·에스컬레이션·대표 승인건) | 대표만 | "내가 봐야 할 거" |
| R9 | `assignee_candidates` | `GET /api/assignees` | user | 분장 가능 대상 + `canAssign` + 위계 레벨 | 전원(결과가 다름) | 분장 쓰기의 **선행 호출** |
| R10 | `open_assigns` | `GET /api/project/open-assigns` | user, id | 열린 분장 수 + 상위 5건 | 로그인 전원 | 종료·아카이브 전 경고 |
| R11 | `brief_comments` | `GET /api/brief-comments` | user, date(YYYY-MM-DD) | 그날 브리프 코멘트 | 로그인 전원 | "그거 뭐라고 하셨더라" |
| R12 | `daily_brief` | ⚠️ **API 없음** — `23-arisa/brief/*.json` 파일 직접 | date, team? | 대표·팀 브리프 본문 | 파일 접근 = 권한 없음 | "어제 브리프" |

### R12 주의
브리프만 HTTP 엔드포인트가 없다(HTML 페이지 `/brief`·`/team-brief`만 존재, 서버측 역할 게이트). 파일을 직접 읽으면 **권한 검사가 전혀 없다** — 직원이 대표 브리프를 요구하면 그대로 나간다. 세 갈래:
1. 읽기 전용 API `GET /api/brief?date&team` 신설 + 기존 역할 게이트 재사용 ← 권장
2. 봇 쪽에서 role 체크 후 파일 읽기 (두 개의 진실 발생, 비권장)
3. Phase 1 범위에서 제외

### 제외한 GET
- `/api/health`, `/api/me` — 내부용. 봇은 텔레그램 ID로 신원을 이미 안다
- `/api/project/memory-doc` — HTML 페이지를 반환한다. 봇은 텍스트가 필요 → 쓰려면 `format=text` 파라미터 추가 필요
- `/brief`·`/my-brief`·`/weekly`·`/simulator`·`/guide*` 등 — 전부 HTML 페이지. 툴이 아니라 **링크로 전달**할 대상

---

## 5. WRITE 툴 8종 — 서비스 토큰(§1-A) 구현 후 개방

> 전부 `user`+`pin` 관문 아래. 위험등급 순으로 개방할 것.
> 공통 규칙: **실행 전 사용자 확인 필수**, 감사 로그 필수, 결과를 사람 말로 회신.

| # | 툴 | 엔드포인트 | 입력 | 권한 | 위험 | 개방 순서 |
|---|---|---|---|---|---|---|
| W1 | `today_plan_set` | `POST /api/today-plan` | row, task, on(bool) | 본인 배정 업무만(5762) | 🟢 낮음 — 선언만, 상태 불변 | 1 |
| W2 | `assign_self` | `POST /api/assign-self` | task, deadline?, priority?, project? | 본인 | 🟢 낮음 — 본인 업무 추가 | 1 |
| W3 | `brief_comment` | `POST /api/brief-comment` | date, item, src, text(≤1000자) | 대표·리더 | 🟢 낮음 | 1 |
| W4 | `assign_status` | `POST /api/assign-status` | row, task, assignee, status, reason?, notify? | 본인/승인은 대표·팀리더·PM | 🟠 중간 — **전이 게이트 통과 필요** | 2 |
| W5 | `assign_edit` | `POST /api/assign-edit` | row, task, assignee, new_* (생략 = 변경 안 함) | 본인·대표·팀리더 | 🟠 중간 | 2 |
| W6 | `decision_clear` | `POST /api/decision-clear` | logged_at, action(resolve\|escalate), resolution | 담당 PM·대표 | 🟠 중간 | 2 |
| W7 | `assign_create` | `POST /api/assign` | assignee, task, deadline?, priority? | 대표→리더·본인 / 리더→팀원·타팀리더 | 🔴 높음 — 타인에게 업무 생성 | 3 |
| W8 | `meeting_actions_commit` | `POST /api/meeting-actions` | pid, ts, items[≤30] | `can_edit`(PM·대표) | 🔴 높음 — **일괄 생성** | 3 |

### W4·W5의 함정 — read-then-write 강제

두 툴은 낙관적 잠금이 걸려 있다(5795, 5862):

```python
if not task or task != b.get("task") or assignee != b.get("assignee"):
    return 409 "행 내용이 달라졌습니다 — 새로고침 후 다시 시도"
```

즉 **`row` 번호만으로는 못 쓴다.** 반드시 R1/R7로 먼저 읽어 `row`+`task`+`assignee`를 확보하고, 그 3개를 함께 보내야 한다. Assistant가 "3번 업무 완료 처리해줘"를 받으면 내부적으로 read → 대조 → write 3단계다. 409가 나면 **재시도하지 말고 사용자에게 되물어야 한다**(다른 사람이 그 사이 바꿨다는 뜻).

### W4 추가 — 상태 전이 게이트

`shared/status.py check_transition(from, to, "dashboard", admin=)`을 통과해야 한다(5885). 임의 상태로 못 뛴다. Assistant는 실패 시 `code: "transition"`을 받아 **왜 안 되는지를 사람 말로 설명**해야 한다. 이것이 지금 지연 45건 문제의 급소다 — "완료"만이 답이 아니라 진행 전환·마감 재설정·종료 처리(사유 필수)가 전부 정상 경로임을 대화가 안내해야 한다.

### AI 보조 툴 (조직 상태 불변, 쿠키 세션)

| 툴 | 엔드포인트 | 용도 |
|---|---|---|
| `meeting_summarize` | `POST /api/simulator/meeting-summary` | 전사(≤6만자) → 회의 요약. R4 엔진 |
| `todo_parse` | `POST /api/assign-parse` | 자유 텍스트 → to-do 항목화 (⚠️ pin 관문 아래, 대표·리더만) |
| `doc_draft` | `POST /api/simulator/draft` | 텍스트 → 보고 초안 필드 |

`meeting_summarize`는 쿠키 세션만으로 되고 조직 상태를 바꾸지 않는다 — **Phase 1에 넣어도 안전한 유일한 생성 툴**이다. "회의록 정리해줘"의 절반이 여기서 해결된다.

---

## 6. Assistant에서 영구 제외 — 대화로 실행하지 않는다

| 엔드포인트 | 이유 |
|---|---|
| `POST /api/project/delete` | 비가역 |
| `POST /api/project/merge` | 비가역, 대표 전용, 되돌리기 없음 |
| `POST /api/project/archive` | 열린 분장을 끌고 들어간다 |
| `POST /api/assign-bulk-delete` | 최대 200건 일괄 삭제 |
| `POST /api/login`, `/api/set-pin` | 인증 자체 |
| `POST /api/project/save` | 프로젝트 전체 객체 덮어쓰기 — LLM이 필드를 흘리면 조용히 유실 |
| `POST /api/project/doc-apply`·`proposal-apply` | **사람이 diff를 고르도록 설계된 것.** 대화로 자동 적용하면 그 설계를 되돌린다 |

이 7종이 필요하면 **Assistant가 화면 링크를 던진다**: "이건 제가 못 합니다 — arisa-os.com/projects 에서 확인하세요." 이게 Role 설계의 기본 실패 모드 처리다.

---

## 7. 카탈로그 밖의 데이터 — Phase 2~3에서 붙일 것

| 대상 | 현재 접근법 | 필요한 것 |
|---|---|---|
| 개인 메모(Second Brain) | `24-second-brain/` 파일 + mem0 | **owner 스코프를 툴 레이어에서 강제**. 라우터가 owner를 넘기는 구조 금지 |
| 일일보고 원본 | 구글시트 3탭 | 조회 API 없음 — 시트 read 툴 필요 |
| 캘린더 | `gws` CLI | 맥미니 keyring=file 필수 |
| 파일 검색 | 없음 | 화이트리스트 경로 + 읽기 전용부터 |
| 시스템 명령 | 없음 | **화이트리스트 액션만**(브리프 재생성·봇 재시작·상태 조회·로그 tail). 자유 셸 금지 |

---

## 8. 결정 3가지 — 2026-08-03 전부 "진행"으로 확정, 구현 완료

| # | 결정 | 결과 |
|---|---|---|
| ① 서비스 토큰(§1-A) | 구현 | ✅ `dashboard-server.py` — 헤더 인증 + 쓰기 화이트리스트 + 감사 로그 |
| ② 브리프 읽기 API(R12) | 신설 | ✅ `GET /api/brief?scope=exec\|team\|person` — HTML 페이지와 동일 역할 게이트 |
| ③ Phase 1 범위 | 읽기 5 + 요약 1 | ✅ 쓰기는 라우터 오분류율 관측 후 개방 |

---

## 9. 구현 현황 (2026-08-03)

### 새 파일
| 파일 | 역할 |
|---|---|
| `shared/assistant_tools.py` | 툴 클라이언트. 봇이 조직 데이터에 닿는 **유일한 경로**. `TOOL_SPECS`(LLM 함수호출용) + `call_tool`(스펙 밖 이름 거부) |
| `shared/intent_router.py` | 규칙 1차 → LLM 2차 → 확인 질문. Role 7종 매핑 |

### 변경 파일
| 파일 | 변경 |
|---|---|
| `dashboard-server.py` | `ASSISTANT_SECRET` · `svc_session()` · `_SVC_WRITE_PATHS`/`_SVC_POST_OK` · `_svc_audit()` · `_gate` 서비스 분기 · 쓰기 관문 분기 · `GET /api/brief` |
| `daily-report-bot.py` | `receive_inquiry` → `assistant_entry`(라우터 기반), `receive_tasks` → `_feed_tasks` 분리, `start_report`가 보관 원문 이어받음, **`conv` 등록을 맨 뒤로 이동** |

### 인증 흐름
```
텔레그램 메시지
  └ user_id (텔레그램이 붙인 값 — LLM이 만들 수 없다)
      └ X-Arisa-On-Behalf-Tg 헤더  +  X-Arisa-Service: <시크릿>
          └ 서버: by_telegram_id → 이름 도출 → users.json 계정 확인
              └ 기존 세션 dict 생성 → is_admin·lead_teams·can_view·스푸핑 게이트 그대로 적용
```
**이름을 헤더로 받지 않는 것이 설계의 핵심이다.** 이름을 받으면 LLM이 출력한 "최원석"이 곧 대표 권한이 된다.

### 검증 결과
| 항목 | 결과 |
|---|---|
| 서비스 인증 E2E (`svc_e2e.py`) | 14/14 — 무인증·틀린 시크릿·미등록 ID·계정 없는 명부·화이트리스트 밖 POST 전부 차단 |
| 사칭 차단 | 정예은 대행으로 `?user=최원석` → 403 (기존 게이트가 서비스 세션에도 적용) |
| 허용 쓰기 관문 통과 | 3/3 — 관문 통과 후 **업무 로직이 정상 거부**(`/api/assign` → "대표는 리더·본인에게만 배분") |
| 기존 동작 무손상 | 헤더 없이 같은 경로 호출 → 전부 401 (변화 없음) |
| 브리프 권한 (`brief_e2e.py`) | 15/15 — 대표/팀/개인 스코프, 타팀 리더 차단, 날짜 오염 차단 |
| 툴 클라이언트 (`tools_e2e.py`) | 사람별 프로젝트 가시성 상이 확인, 타프로젝트 403, 스펙 밖 툴 이름 거부, 시크릿 없으면 호출 자체 차단 |
| 라우터 (`router_test.py`) | 13/13 — **현장 실패 2건 모두 정상 라우팅**, 원문 353자 무손실 보존 |
| 핸들러 순서 회귀 | ✅ `/meeting`·`/assign` 진행 중 입력을 보고가 가로채지 않음. 대조군(옛 순서)에서는 가로챔을 재현 |

### 라우터가 고친 것 — 현장 실패 2건
`inquiries/inbox.jsonl`의 미처리 2건이 **둘 다 라우팅 실패**였다.

| 일시 | 사람 | 입력 | 구 동작 | 신 동작 |
|---|---|---|---|---|
| 07-29 16:39 | 김가은 | 보고 전문 353자 (`목표`/`진행 과정`/`결과물` 서식) | "저장되지 않았습니다. /report 먼저 누르고 **다시 입력**" | `report_submit` conf **0.92** → 그 텍스트가 곧 보고 내용 |
| 07-30 05:40 | 정예은 | `report` (슬래시 없음) | 문의로 접수 | `report_submit` conf **0.99** — 슬래시 유무 동일 취급 |

구 규칙은 `looks_like_report: true`로 **의도를 이미 알아본 뒤에 거절했다.** 새 원칙:
> 알아봤으면 실행하거나 확인을 묻는다. 재입력을 요구하지 않는다.

확신이 낮으면(<0.75) 거절 대신 확인을 묻고, **사용자가 쓴 원문을 보관**해 `/report` 시 그대로 넣는다.

### ⚠️ 미해결 — 배포 전 확인 필요
1. ~~텔레그램 ID는 있는데 계정이 없는 3명~~ → **해소.** 맥미니 원본은 11명 전원 계정 보유(list 스키마, arisa2 symlink 공유본). 로컬 `_data/users.json` 사본이 낡아 생긴 착시였다.
   > 📌 교훈: 명부 대조는 반드시 맥미니 원본에서. 로컬 `_data/`는 미러이지 SSOT가 아니다.
2. **맥미니 `.env`에 `ARISA_ASSISTANT_SECRET` 추가 필요** — 없으면 기능이 꺼진 채로 돌아간다(폴백 없음 = 기본 차단).
3. **봇 재시작 시 진행 중 보고 세션** — `conv`는 `persistent=True`라 상태가 살아 있다. 등록 순서 변경이 부활 세션에 미치는 영향은 실제 재시작으로 확인할 것.
4. **브라우저 렌더 확인** — 이번 변경은 대시보드 화면 코드를 건드리지 않았지만 `_gate`·`do_POST` 진입부를 바꿨다. 배포 후 기존 로그인 상태로 화면이 정상 뜨는지 확인(쿠키 세션 경로 무손상 여부).

### 다음 (Phase 2 조건)
쓰기 개방은 **라우터 오분류율을 실제로 본 뒤**다. 순서: 🟢 `today_plan_set`·`assign_self`·`brief_comment` → 🟠 `assign_status`(전이 게이트)·`assign_edit`·`decision_clear` → 🔴 `assign_create`·`meeting_actions_commit`.
`_SVC_WRITE_PATHS`에는 이미 7종이 등록돼 있으나 **봇이 호출하지 않는다** — 서버는 준비됐고 봇이 안 부르는 상태다.

---

## 부록 — 확인된 사실 (근거 라인)

- 쓰기 공통 관문: `dashboard-server.py:5533-5535`
- `auth()` = users.json PIN 문자열 비교: `3175`
- GET 신원 스푸핑 방지: `4575-4580`
- 낙관적 잠금 409: `5795`(edit), `5862`(status), `5935`(review)
- 전이 게이트: `5885`
- 분장 SSOT = 시트 + `shared/assign_sheet.py`: `102-108`
- 프로젝트 SSOT = `_data/projects/`: `40-42`
- POST `/api/meeting-actions`가 pin 관문 위(쿠키 인증): `5453`
