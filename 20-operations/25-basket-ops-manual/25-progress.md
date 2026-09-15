# 25. Basket 상설매장 운영 매뉴얼 — Progress

> 2026-09-16 워크스페이스 진단에서 누락이 확인되어 소급 작성. 이전 기록은 파일 구조와 산출물에서 역추적한 것이다.

> **대상** · Basket — 카페 + 편의점 + 대관 복합공간
> **구성** · 운영 매뉴얼(HTML) · 업무보고 양식(xlsx) · 요일별 TO-DO(JSON/xlsx) · 신입 온보딩 워크북 · 운영봇 · 온보딩 자동발송
> **실행 코드 위치** · `00-system/02-scripts/` — `basket-ops-bot.py` · `basket-onboarding-sender.sh` · `basket-weekly-insight.py` · `basket-monthly-insight.py` + 각 `com.basket.*.plist`
> **상태** · **가동 중** — 온보딩 발송 로그가 2026-09-15까지 찍혀 있다

---

## 2026-06-21 — 기반 문서 (파일 기준 추정)

| 파일 | 내용 |
|---|---|
| `basket-daily-report-template.html` | Basket 표준 일일보고 양식 v1 |
| `basket-ops-db-schema.md` | 구글시트·노션 입력 테이블 스키마 v1 |

`basket-ops-db-schema.md` 서문 — "지금은 손으로 채워 쓰고, 이후 RX Operations Bot이 이 테이블을 읽어 '오늘 할 일'·리포트를 만든다."
출처는 **양은정 운영자료 6종**(현행 충실 통합)으로 명시. Routine Task 마스터(RT-001~) 1행=1업무, `cycle`·`weekday`·`time_slot`·`owner`·`done_criteria` 컬럼 구조.

---

## 2026-06-22~23 — 운영봇 + 요일별 TO-DO v3

### 운영봇 (`basket-ops-bot-setup.md`, 06-22 17:47)

```
운영자 → 텔레그램 자유 보고
  → OpenAI 12섹션 구조화 (지출·송금승인·특이·장비·업무·대관·스태프·구매·입점·복기)
  → 빠진 핵심 0~2개만 되물음
  → 요약 확인 [✅ 등록 / ✏️ 다시]
  → 구글 시트 일일보고 탭 1행 append
  → ③송금·승인 / ⑤장비 견적·AS / ⑩입점 건이면 매니저에게 🔔 별도 알림
```

기능 2종 — ①일일보고 구조화 ②`/todo`(요일 자동 인식 → 해당 요일 체크리스트 → `TODO이행` 탭 기록).
데이터 소스는 `basket-todo-checklist.json`(엑셀과 동일 소스). 셋업 문서에 **기존 `daily-report-bot.py`(전사 직원보고)와 별도 봇·별도 프로세스**임이 명기돼 있다(토큰·PID락·시트 전부 분리).

### TO-DO 체크리스트 v2 → v3

- `basket-요일별-todo-체크리스트-v2.xlsx` (06-22 17:43)
- `basket-todo-checklist.json` (06-23 16:08) · `basket-요일별-todo-체크리스트-v3.xlsx` (06-23 16:18) — v2 보존한 채 v3 신설
- `basket-ops-bot-운영자가이드.html` + `.pdf` (06-23 16:21/16:23) — 운영팀 배포본

---

## 2026-06-24 — 매뉴얼 통합본 + 신입 온보딩 워크북

| 파일 | 크기 | 제목 |
|---|---|---|
| `basket-업무가이드-매뉴얼-v1.html` | 95KB | Basket 업무가이드 매뉴얼 v1 — 운영팀 교육·실행 통합 |
| `basket-daily-weekly-manual-v1.html` | 33KB | Basket 상설매장 업무관리 매뉴얼 **v3** — 일일·주간 |
| `basket-weekly-task-grid-v1.html` | 13KB | Basket 주간업무 리스트 — 오전·오후 |
| `basket-신입-온보딩-워크북-v1.html` + `.pdf` | 32KB / 728KB | Basket 신입 온보딩 워크북 v1 — 2주 따라하기 |

> 파일명은 `-v1`인데 문서 제목은 `v3`인 것이 있다(`basket-daily-weekly-manual-v1.html` → "매뉴얼 v3"). TO-DO v3 반영 시 **파일명은 두고 내용만 올린** 것으로 보인다. 혼동 주의.

통합본(`업무가이드-매뉴얼-v1`)이 SSOT이고, 나머지 문서들은 그 안에 흡수된 원본 자산이다.

---

## 2026-06-25~ — 온보딩 PDF 분할 자동발송 (가동 중)

워크북을 **8개 PDF로 분할**해 `onboarding-daily/`에 두고, 하루 1개씩 자동 발송한다.

```
01-써머리 / 02-Day1 / 03-Day2 / 04-Day3 / 05-Day4 / 06-Day5 / 07-Day6 / 08-2주차
```

- 스크립트 `00-system/02-scripts/basket-onboarding-sender.sh` + `com.basket.onboarding.plist`
- 진도 상태는 `.send-state` 파일 1개(현재 값 **8**) — 8개 다 보내면 자동 정지
- 로그 `send.log`

### 로그에서 읽히는 사건

| 날짜 | 기록 |
|---|---|
| 2026-07-02 09:02 | `ERROR 파일 없음: .../01-써머리.pdf` — 맥미니 이관 직후 PDF가 넘어가지 않아 실패 |
| 2026-07-04 00:46 | `idx=8/8` 로 한 번 완료 표시 |
| 2026-07-04 09:00 | `idx=4/8` → 05-Day4.pdf 발송 — 상태를 되돌려 재개 |
| ~ 2026-09-15 09:00 | 매일 실행되며 `모든 교육 발송 완료 (8/8) — 더 보내지 않음.` 로그만 남김 |

`launchd.err.log`에 남은 오류 2줄 —
`/Users/server-mini/.../basket-onboarding-sender.sh: line 43: /Users/choi_ai/.../send.log: No such file or directory`
**스크립트는 맥미니(server-mini)에서 도는데 로그 경로가 맥북(choi_ai)으로 하드코딩**돼 있던 흔적이다. 현재 `send.log`는 정상 기록 중이니 이후 고쳐진 것으로 보이나, **원인·수정 시점 기록이 없다.**

---

## 파생 자동화 (같은 계열, 코드는 `00-system/02-scripts/`)

- `basket-weekly-insight.py` + `com.basket.weekly-insight.plist` — 주간 인사이트
- `basket-monthly-insight.py` + `com.basket.monthly-insight.plist` — 월간 인사이트
- `basket-report-webapp.gs` — 매장 일일보고 웹앱 백엔드 (프론트·산출물은 `90-archive/30-basket-report-webapp/`)

---

## 남은 것

- **잡 파일 하나가 매일 헛돌고 있다** — 온보딩 발송은 `8/8`로 끝났는데 launchd가 매일 09:00에 깨어나 "더 보내지 않음"만 찍는다. 신규 입사자용으로 재사용하려면 `.send-state` 리셋 절차를, 아니면 잡 언로드를 정해야 한다
- `~$basket-업무보고-양식.xlsx` — 엑셀 임시 잠금 파일이 남아 있다. 삭제 대상
- `launchd.err.log`의 경로 하드코딩 오류: **언제 어떻게 고쳤는지 기록 없음** — 확인 필요
- 파일명 `-v1` / 문서 내용 `v3` 불일치 정리 여부
- `basket-재고상품운영-담당자작성시트.xlsx` 회수 결과가 매뉴얼 빈칸(🔶 확인필요 항목)에 반영됐는지 확인 필요
- 주간·월간 인사이트 산출물이 `90-archive/30-basket-report-webapp/insights/`에 2026-07-07까지만 있다 — 이후 중단 여부 확인 필요
