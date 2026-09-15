# 24. Second Brain — Progress

> 2026-09-16 워크스페이스 진단에서 누락이 확인되어 소급 작성. 이전 기록은 파일 구조와 산출물에서 역추적한 것이다.

> **목적** · "메모 저장이 아니다. **최원석의 사고를 조직이 이해 가능한 형태로 변환**하는 개인 사고 OS" (`00_dev-guide.md` §0)
> **제1원칙** · 입력 마찰 최소화 — 생각났을 때 **5초 안에** 저장된다. 분류·정리는 시스템이 한다
> **경로** · 텔레그램 봇 단일 입구 → `00_inbox/` Markdown + YAML frontmatter → 백그라운드 자동분류 → `/brief`·`/connect`·export
> **가이드 정본** · `00_dev-guide.md`

---

## 2026-06-17~18 — Phase 1 · 1.5 · 2 (파일 기준 추정)

### 설계 전환 (`00_dev-guide.md` §1)

이전 ARISA ZERO(SQLite + FastAPI + 아이폰→맥 직접 HTTP)에서 피벗한 배경이 가이드에 명시돼 있다.
아이폰→맥 직접 연결이 **공유기 클라이언트 격리**로 깨졌고, Tailscale은 "맥 켜짐 + Tailscale ON"에 의존하는 깨지기 쉬운 구조였다.

| 항목 | ARISA ZERO (폐기) | Second Brain v1 |
|---|---|---|
| 저장 | SQLite | **Markdown + YAML frontmatter** |
| 입력 | 아이폰→맥 직접 HTTP | **Telegram 봇으로 일원화** |
| 서버 | FastAPI 상시가동 + Tailscale | 불필요 (텔레그램 polling) |
| 위치 | 별도 db | do-better-workspace 내부 (Obsidian vault 통합) |

핵심 문장 — "**디버깅할 네트워크가 없다.**" 단축어든 앱이든 모든 입력이 Telegram Bot API 하나로 수렴한다.

### 구현 파일 (mtime 기준)

| 파일 | 최종수정 | 역할 |
|---|---|---|
| `bot.py` | 2026-07-06 11:32 | 본체 (26KB) |
| `registry.json` | 2026-06-18 00:34 | 프로젝트 별칭·설명 사전 **23개** |
| `report.py` | 2026-06-18 00:39 | `/sb-report` 스킬용 수집기 |
| `00_dev-guide.md` | 2026-06-19 08:17 | 개발 가이드 v1 |
| `run.sh` | 2026-07-06 11:34 | 런처 (키는 `arisa-project-memory/.env`에서만 읽음 — 평문 노출 0) |

`20_exports/bongeunsa-team-brief-2026-06-18.md` — export 시연 산출물 1건.

### 봇 명령 (`bot.py` 핸들러 기준)

`/start` `/idea` `/project` `/brief` `/connect` `/recall` `/ask` `/save` + 텍스트·음성 핸들러.
음성은 Whisper 전사 후 동일 경로로 들어간다. 인텐트 라우터(`route_intent`)가 저장/대화를 가른다.

`registry.json`의 설명 — "최원석이 말/음성으로 부르는 이름을 aliases에 넣을수록 분류가 정확해진다." key는 주로 `10-projects/` 폴더명이다.

---

## 2026-06-19 — mem0 2.x 직접 통합 (B단계)

`arisa_memory.py`(06-19 08:01) 헤더에 기록이 남아 있다.

- A단계의 subprocess 격리를 제거하고, 전용 venv **`.venv311`**(Python 3.11, openai 2.x + mem0 2.x 호환)에서 mem0를 직접 import해 **상주 인스턴스로 재사용**(매 호출 init 없음)
- 설계 원칙 2가지가 코드 주석에 명시:
  1. **mem0는 '의미 인덱스'로만 쓴다.** mem0 2.x가 fact를 영어로 정규화해 저장해도, 사용자에게 보여주는 재부상 텍스트는 **항상 inbox 원문의 한국어 summary**다 (원문 보존 + 한국어 UX)
  2. **보조 레이어다. 어떤 함수도 예외를 던지지 않는다** — 실패 시 add=None / recall=[]
- sqlite3 `check_same_thread` 패치로 mem0 내부 ThreadPoolExecutor + qdrant 로컬 SQLite 스레드 가드를 우회
- 롤백 경로 보존: `run.sh.venv39-backup` (구 Python 3.9 / arisa venv 경로)
- PoC 잔재: `mem0_poc.py` · `mem0_helper.py` · `.mem0-data/` · `.mem0-poc-data/` · `.poc-trash/`

---

## 2026-06-17 ~ 06-29 — 실사용 기록

`00_inbox/` 캡처 **19건**. 첫 건 06-17 12:12, 마지막 건 **06-29 08:36**.

내용 성격 — 리진 오브제·봉은사 카페·운영팀 프로젝트·세스크멘슬 계약서·서울디자인어워드 심사위원 ID·청명주 등 **프로젝트 메모와 즉석 지시가 섞여 있다.**

> ⚠️ **inbox 캡처가 2026-06-29에서 멈춰 있다.** 이후 `bot.py`·`run.sh`가 7/6에 수정된 기록은 있으나 새 캡처는 없다. 봇 가동 상태 확인 필요.

---

## 2026-07-06 — 맥미니 이관 흔적

`run.sh` 내부 경로가 전부 **`/Users/server-mini/`**로 적혀 있다. 맥미니 fleet 이관(2026-07-02, `25-basket-ops-manual` 참조) 때 함께 넘어간 것으로 보인다.
따라서 **이 폴더의 코드는 소스이고, 실제 가동 주체는 맥미니**다. 이 맥북에서 `run.sh`를 그대로 실행하면 경로가 맞지 않는다.

---

## 남은 것

- **봇이 지금도 살아 있는지 확인 필요** — inbox 마지막 캡처가 2026-06-29다. 맥미니 launchd(`com.arisa.second-brain`) 상태 점검
- `registry.json` 프로젝트 사전이 **23개에서 멈춰 있다** — 이후 추가된 프로젝트(35·37·38·41·45~52 등)가 반영돼 있지 않아 분류 정확도가 떨어진다
- `00_dev-guide.md`에 있는 `10_templates/` 폴더가 실제로는 없다 — 설계와 실물 불일치
- PoC 잔재 정리(`mem0_poc.py`·`.mem0-poc-data/`·`.poc-trash/`) 여부 결정
- export 산출물이 시연 1건(`bongeunsa-team-brief`)뿐 — `/sb-report`가 실운영에 쓰였는지 확인 필요
