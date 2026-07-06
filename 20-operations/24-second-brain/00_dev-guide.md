# 최원석 Second Brain — 개발 가이드 v1

## 0. 목적과 원칙

이 시스템의 목적은 **메모 저장이 아니다.**
**최원석의 사고를 조직이 이해 가능한 형태로 변환**하는 개인 사고 OS다.

생각을 빠르게 저장(capture)하고 → AI가 자동으로 분류·연결·요약하고 →
프로젝트별로 **직원에게 공유 가능한 브리프**, 주제별로 **강의 소재 정리본**으로
export 한다.

### 제1원칙 — 입력 마찰 최소화
> 생각났을 때 **5초 안에** 저장된다. 분류·정리는 시스템이 한다.

이 원칙이 모든 설계 결정에 우선한다. 사용자는 절대 "어디에 저장할지/무슨 타입인지"
고르지 않는다. 그냥 말하거나 보낸다.

---

## 1. 핵심 설계 결정 (이전 ARISA ZERO 대비)

| 항목 | ARISA ZERO (폐기) | Second Brain v1 |
|---|---|---|
| 저장 | SQLite | **Markdown 파일 + YAML frontmatter** |
| 입력 경로 | 아이폰→맥 직접 HTTP(로컬IP/Tailscale) | **Telegram 봇으로 일원화** |
| 서버 | FastAPI 상시가동 + Tailscale | **불필요** (텔레그램 polling) |
| 위치 | 별도 SQLite db | **do-better-workspace 내부**(Obsidian vault 통합) |
| 목적 | 1인칭 생각 분류 | 분류 + **조직 공유/강의 소재 변환** |

### 왜 텔레그램 일원화인가 (이전 삽질의 교훈)
단축어가 막힌 근본 원인은 "아이폰 → 맥 직접 연결"이었다(공유기 클라이언트 격리).
Tailscale로 경로는 뚫었으나 *맥 켜짐 + Tailscale ON*에 의존하는 깨지기 쉬운 구조였다.

→ **아이폰 단축어도 자체 서버가 아니라 Telegram Bot API(`api.telegram.org`)로 메시지를
쏜다.** 로컬망·Tailscale·격리·방화벽이 전부 무관해지고 LTE에서도 항상 작동한다.
단축어든 텔레그램 앱이든 **모든 입력이 봇 하나로 수렴**한다. 디버깅할 네트워크가 없다.

---

## 2. 시스템 구조

```text
[iPhone 단축어: 받아쓰기 / 공유시트(URL·클립보드)] ─┐
[Telegram 앱: 텍스트·음성·/idea·/project]          ─┴→ Telegram Bot API
                                                          ↓
                                              [Second Brain 봇 (long-polling)]
                                                          ↓ ① 5초 내 즉시 저장 + "저장됨" 응답
                                          20-operations/24-second-brain/00_inbox/2026-06-17-1432.md
                                                          ↓ ② 백그라운드 자동분류 (call_openai)
                                              frontmatter 채움(type/tags/related/summary/next)
                                                          ↓
                          /brief · /connect · /export(team|lecture)
                                  → inbox Markdown 읽어 생성 → 텔레그램 답장 / HTML
```

핵심: **봇이 모든 걸 한다.** 별도 서버·watcher 없음. 저장은 동기(즉시), 분류는
봇의 백그라운드 작업(asyncio task)으로 — 입력 마찰 0을 지킨다.

---

## 3. 저장 구조 (do-better-workspace 내부)

루트: `do-better-workspace/20-operations/24-second-brain/`

```text
24-second-brain/
  00_dev-guide.md          ← 이 문서
  00_inbox/                ← 모든 입력이 먼저 여기 (분류 후에도 머무름)
    2026-06-17-1432-디저트-오브제.md
  10_templates/
    team-brief.md.j2       ← /export team 템플릿
    lecture-note.md.j2     ← /export lecture 템플릿
  20_exports/              ← 생성된 브리프/강의노트 보관
  registry.json            ← 프로젝트·사람 canonical 사전(엔티티 정규화용)
```

MVP는 **분류 후에도 inbox에 그대로 둔다.** 프로젝트별 분리는 물리적 이동이 아니라
frontmatter `related_projects` 필터로 처리(이동·심링크는 Phase 2).

### 생각 파일 스키마 (YAML frontmatter + 본문)

```markdown
---
id: 2026-06-17-1432
created: 2026-06-17T14:32:00
source: telegram | shortcut          # 입력 채널
input_type: text | voice | url | clipboard
status: raw | classified            # 분류 전/후
type: idea                          # ↓ 여기부터 AI 자동생성 (요구사항 4)
tags: [브랜딩, 공간, 대비]
related_topics: [한국적 미감, 럭셔리 디저트]
related_projects: [리진]
possible_use: [강의소재, 제안서, 프로젝트방향]
summary: 리진은 서양식 디저트와 조선 고미술 오브제의 대비 구조로 가야 한다.
next_action: 리진 컨셉 원페이저 초안
confidence: 0.0
---

(원문 그대로 보존 — raw_text)
```

`type` 분류값: `idea | memo | task | project_issue | decision | reminder |
question | reference | lecture_seed`

---

## 4. 자동 분류 (요구사항 4)

봇이 저장 직후 백그라운드로 `call_openai()`(arisa-project-memory `scripts/engine/client.py`
재사용)를 호출해 위 frontmatter 필드를 채운다.

- **엔티티 정규화**: `registry.json`(프로젝트명 + 직원 명부 `arisa-employees.json`)을
  프롬프트에 주입 → 받아쓰기 오류 교정 + 프로젝트/사람명 정식 표기.
  (사전에 있는 엔티티만 정규화, 없으면 원문 존중.)
- 분류 끝나면 `status: classified`로 갱신 + 텔레그램에 "🧠 리진 아이디어로 정리됨" 알림.
- 9분류 프롬프트는 ARISA ZERO `prompts.py`를 Markdown frontmatter 출력용으로 이식.

---

## 5. 명령어 (요구사항 1·2·5·6·7·8)

### 입력 (마찰 최소화 — 명령어 없이 그냥 보내면 capture)
| 입력 | 동작 |
|---|---|
| (그냥 텍스트/음성) | `/capture` 기본 — inbox 저장 + 자동분류 |
| `/idea <내용>` | type=idea 힌트 주고 저장 |
| `/project <이름> <내용>` | related_projects 고정 + 저장 |
| (URL/클립보드, 단축어 공유시트) | source=shortcut, input_type=url — 본문에 URL+메타 |

활용은 **두 레벨**로 나눈다 — 가벼운 조회는 텔레그램, 무거운 분석은 Claude Code.

### 활용 A — 텔레그램 (경량·즉답)
프로젝트/이슈 문의는 **짧은 써머리**로 충분. 빠른 확인 전용.
| 명령 | 동작 |
|---|---|
| `/brief <프로젝트\|이슈>` | 관련 생각 모아 **짧은 써머리** 답장 |
| `/connect <키워드>` | 연결된 생각·프로젝트·질문·강의소재 표시 |

frontmatter를 필터·집계 후 `call_openai()`로 **짧게** 합성해 텔레그램 메시지로 답장.

### 활용 B — Claude Code (심층·구조화 레포트)
프로젝트 브리프 **전체에 대한 분석과 구조화 레포트**는 텔레그램이 아니라 Claude Code 세션에서.
| 요청(자연어) | 동작 |
|---|---|
| "리진 프로젝트 브리프 분석/레포트" | inbox의 해당 프로젝트 생각 **전체 수집** → 구조화 분석 레포트 (§6) |
| "리진 team export" | 직원 공유용 **심층 브리프** (§6) |
| "한국적 미감 lecture export" | 강의 소재 **구조화 정리본** (§6) |

Claude Code는 inbox Markdown을 직접 읽어 `/consulting-report`(MBB 덱)·`/proposal-architect`
등 기존 스킬과 연계하고, 필요 시 HTML 덱으로 출력한다.

---

## 6. Export — 두 레벨 (이 시스템의 존재 이유)

### 레벨 1 — 텔레그램 써머리 (즉답·경량)
`/brief <프로젝트\|이슈>` → 관련 생각의 핵심을 **3~5줄**로 요약해 텔레그램 답장.
"지금 이 프로젝트에 대한 내 생각이 어디까지 왔나"를 1분 안에 확인하는 용도.
구조화·분석은 하지 않는다. 빠른 조회만.

### 레벨 2 — Claude Code 심층 레포트 (구조화·분석)
프로젝트 브리프 **전체를 수집해 분석·구조화**한 레포트. 이게 조직 공유의 핵심 산출물.
Claude Code가 inbox의 `related_projects=X` 생각을 모두 읽어 합성한다.

**team 레포트 (직원 공유용)** — 흩어진 생각을 직원이 바로 이해·실행 가능한 형태로
```
# {프로젝트} 브리프 레포트  (by Project Rent)
## 1. 현황 종합        — 수집된 생각 전체의 맥락 요약
## 2. 핵심 인사이트/패턴  — 생각들 사이의 반복·긴장·방향성 (분석)
## 3. 전략 방향         — 채택된 방향 + 근거
## 4. 결정 필요 사항     — decision 타입 + 옵션
## 5. 액션 플랜         — next_action + 담당 제안(assignee)
## 6. 참고/리스크
```
→ `/consulting-report`(MBB 덱) 연계 가능, HTML 덱 출력 옵션.

**lecture 레포트 (강의 소재)**
```
# {주제} 강의 소재 구조화
## 후크/문제제기   — question 타입
## 핵심 개념       — idea/reference
## 사례·비유       — related_topics 연결
## 실습/토론거리    — possible_use=강의소재 + next_action
```

레벨 2 결과는 `20_exports/`에 저장 + (요청 시) 텔레그램 전송·HTML 덱.

---

## 7. 재사용 / 신규 / 폐기

**재사용 (arisa-project-memory)**
- 텔레그램 봇 골격 `scripts/telegram_bot.py` (토큰·ALLOWED_USER_IDS 8123576679 그대로)
- `scripts/engine/client.py` `call_openai()` — 분류·brief·export 합성
- `arisa-employees.json`(do-better-workspace) — 사람 사전
- jinja2 템플릿 렌더 패턴

**신규**
- Second Brain 봇 (capture/idea/project/brief/connect/export 라우팅)
- Markdown inbox writer + frontmatter 분류기 (SQLite 대체)
- `registry.json`, team/lecture jinja2 템플릿
- iPhone 단축어: 받아쓰기 → Telegram `sendMessage`

**폐기**
- ARISA ZERO `scripts/arisa_zero/` SQLite(`db.py`)·`classifier.py`
- `com.arisa.zero-server` launchd + FastAPI `/api/thoughts` + Tailscale 의존
  (※ 봇은 launchd로 상시 가동 — 기존 `com.arisa.telegram-bot` 패턴 재사용)

---

## 8. 개발 우선순위

**Phase 1 — 캡처 파이프라인**
1. Second Brain 봇: 텍스트/음성 → `00_inbox/*.md` 즉시 저장 + "저장됨" 응답
2. 백그라운드 자동분류 → frontmatter 채움 + "정리됨" 알림
3. iPhone 단축어 → Telegram sendMessage (받아쓰기·공유시트)

**Phase 2 — 활용**
4. 텔레그램 `/brief`·`/connect` — 관련 생각 모아 **짧은 써머리** 답장
5. Claude Code 심층 레포트 — inbox 수집 → team/lecture **구조화 분석**(consulting-report 연계, HTML)

**Phase 3 — 연동 (요구사항 9)**
6. Notion / Google Drive 동기화, DB 인덱싱(검색), AX Brain·ChatGPT 액션 연동

---

## 9. 향후 연동 설계 (요구사항 9)

Markdown + frontmatter를 단일 진실원본(SoT)으로 두면 어댑터만 추가하면 된다.
- **DB**: frontmatter → SQLite/벡터DB 인덱싱(전문·의미 검색)
- **Google Drive / Notion**: inbox·exports 미러링
- **AX Brain / ChatGPT**: registry + inbox를 컨텍스트로 노출하는 read API

---

## 10. 메모리 레이어 — mem0 재부상 (2026-06-19 추가)

**무엇**: 생각을 저장하면 의미적으로 관련된 **과거 생각을 자동 재부상**(💭)한다.
"저장만 하고 끝나는 데이터"를 살아있는 연결망으로. ARISA 2.0 정의의 "재부상" 구현.

**구조 (mem0 2.x 직접 통합)**
- `arisa_memory.py` — bot이 import하는 메모리 클라이언트. mem0를 직접 import(상주 1회 init).
  - `add(text, metadata)`: **`infer=False`** 로 한국어 원문 그대로 임베딩(LLM추출 끔 → 원문보존·한국어검색·비용0)
  - `recall(query)`: 의미검색 → 노트 단위 dedup → **표시는 inbox .md의 한국어 summary**(원문보존)
  - 보조 레이어 원칙: 어떤 함수도 예외를 안 던짐(실패 시 add=None/recall=[], 봇 본흐름 무영향)
- `bot.py` 연동: `_classify_task` → `_memory_task`(분류 후 recall+add+💭) / `/recall <질의>` 명령
- 저장소: `.mem0-data/`(로컬 qdrant, git 제외). 외부 전송 없음.

**런타임**: second-brain 전용 **Python 3.11 venv `.venv311`**(uv 관리). mem0 2.x + openai 2.x 공존.
arisa `.venv`(3.9)·다른 봇은 안 건드림.

**운영 명령**
- 재시작(코드 수정 후): `launchctl kickstart -k gui/$(id -u)/com.arisa.second-brain`
- 로그: `tail -f /tmp/second-brain-bot.log`
- **롤백**(메모리 레이어 통째 비활성): `run.sh`의 python 경로를 `run.sh.venv39-backup`(arisa `.venv`)로 되돌리고 재시작 → mem0 import 실패해도 봇은 정상(저장·분류·대화 유지).
- inbox 전체를 mem0에 재적재: `.venv311/bin/python`으로 inbox `*.md` 본문을 `arisa_memory.add()` 루프(`.mem0-data` 비운 뒤).

**알려진 무해 noise**: 봇 종료/재시작 순간 `QdrantClient.__del__` "sys.meta_path is None" traceback.
mem0 2.x의 qdrant client 정리 순서 문제로, **운영 중 로그엔 안 뜨고**(종료시만) 기능 영향 0.

---

*by Project Rent — 입력은 마찰 0, 출력은 조직이 이해 가능한 형태로.*
