# 30. Basket 매장 일일보고 웹앱 — Progress (종결)

> 2026-09-16 워크스페이스 진단에서 누락이 확인되어 소급 작성. 이전 기록은 파일 구조와 산출물에서 역추적한 것이다.

> **무엇** · 낮에 직원이 봇 `/jot`으로 남긴 진행로그를, 담당자가 웹앱에서 **AI 자동 구성 → 검토 → 제출**하면 매장별 일일보고가 완성되는 시스템. MVP = Basket 1매장
> **스택** · Apps Script(HtmlService, `google.script.run` — CORS 없음) + 구글시트
> **상태** · **종결 · 아카이브 이관.** 운영 주체는 `20-operations/25-basket-ops-manual/` 체계로 이관됨
> **정본 문서** · `SETUP.md`

---

## 전체 흐름 (`SETUP.md`)

```
[낮] 직원 → 텔레그램 봇 /jot 오전 발주 완료, 사진전 대관 회신대기
        → 진행로그 탭 누적 (store_id·날짜·시간·작성자·내용)
[보고] 담당자 → 웹앱 로그인(매장코드 + PIN)
        → 오늘 진행로그 자동 표시 → [AI 자동 구성] → 12섹션 초안
        → 검토·수정 → [제출] → 일일보고 탭 append + 결재 건 매니저 알림
```

- 백엔드: `00-system/02-scripts/basket-report-webapp.gs`
- 프론트: 이 폴더의 `index.html` ("RX 매장 일일보고")
- 데이터: 구글시트 "Basket 업무보고 (봇 연동)" `18fx3jmb…` — 탭 4종(일일보고 / 진행로그 / 담당자 / TODO이행)
- `store_id` 컬럼으로 멀티매장 확장을 대비해 뒀다

---

## 2026-06-23 — 제작 · 배포 · E2E 검증

| 시각 | 파일 |
|---|---|
| 11:00 | `index-preview.html` — "RX 매장 일일보고 — 미리보기(DEMO)" |
| 16:00 | `SETUP.md` — 셋업·배포 가이드 |

### 배포 (clasp CLI)

- 계정 **ws.choi@project-rent.com** / clasp 3.3.0
- scriptId `1BuZNwVkuqCv-tpKIjjRtyFOiSSCM-9Suc5zqHjRjC4ropd-FWUKbzHwp`
- 매니페스트 `executeAs: USER_DEPLOYING` / `access: ANYONE_ANONYMOUS`, 익명접근 200 확인
- 담당자 PIN 등록 — 매장코드 `basket-00`, 양은정·김준호 `1324`(staff). 코드·PIN은 대소문자/공백 무시 비교

### ⚠️ 비밀키 주입 경로 (기록으로 남길 것)

스크립트 속성 4종(SHEET_ID · OPENAI_API_KEY · BASKET_BOT_TOKEN · MANAGER_CHAT_ID)은 **소유자가 프로젝트 설정 UI에 직접 입력**했다.
SETUP.md 기재 — "비밀키를 소스/배포물/공개엔드포인트로 주입하는 경로는 자격증명 노출 방지로 차단됨 → **UI 직접입력이 유일한 안전경로**". 소스(Code.gs/setup.gs)에 비밀값 무함유.

### E2E 검증

`basket-00` + admin PIN → 대표 대시보드 렌더 확인. 빈 상태("표시할 매장 보고가 없습니다")는 당일 제출 0건일 때 정상 동작.

### 재배포 절차 (SETUP.md)

`/tmp/basket-clasp`에서 `clasp push --force` → `clasp create-deployment`.
> ⚠️ **시트 컬럼/`SECTION_KEYS` 변경 시 봇(`basket-ops-bot.py`)과 동시 반영 필수.**

---

## 2026-06-24 — 주간 인사이트 PoC

`weekly-insight-poc.html` (22:36) — "Basket 주간 매장 인사이트 — PoC".
`index.html` 최종수정 23:05.

---

## 2026-06-24 ~ 07-07 — 인사이트 자동 산출 (`insights/`)

주간 4건 + 월간 2건이 쌓였다.

| 파일 | 생성 |
|---|---|
| `weekly-insight-260624.html` | 2026-06-24 22:59 |
| `weekly-insight-260628.html` | 2026-06-28 13:57 |
| `weekly-insight-260629.html` | 2026-06-29 09:00 |
| `weekly-insight-260706.html` | 2026-07-06 11:32 |
| `monthly-insight-2607.html` | 2026-07-07 17:59 |
| `monthly-insight-2606.html` | 2026-07-07 18:00 |

생성 스크립트는 `00-system/02-scripts/basket-weekly-insight.py` · `basket-monthly-insight.py` (+ 각 launchd plist).
**2026-07-07 이후 산출물이 없다.** 중단 시점과 사유는 파일에 기록돼 있지 않다.

---

## 종결 사유

운영 매뉴얼·봇·온보딩·업무보고가 `20-operations/25-basket-ops-manual/` 체계로 통합되면서, 본 웹앱은 별도 프로젝트로 유지할 이유가 없어져 `90-archive/`로 이관됐다.
**단, 백엔드 `.gs`와 인사이트 스크립트는 여전히 `00-system/02-scripts/`에 있고 launchd에 등록돼 있다** — 코드는 아카이브되지 않았다.

---

## 남은 것

- **웹앱이 지금도 살아 있는지 확인 필요** — 배포 URL은 남아 있으나 실사용 흔적(2026-07-07 이후 인사이트 산출 중단)이 없다. **아카이브 이관 = 서비스 종료인지, 코드만 옮긴 것인지 명확하지 않다**
- 종료하기로 했다면 정리 대상 3가지: ①Apps Script 배포 해제 ②`com.basket.weekly-insight` / `com.basket.monthly-insight` launchd 언로드 ③스크립트 속성의 OPENAI_API_KEY·BOT_TOKEN 폐기
- `SETUP.md`에 PIN(`1324`)과 관리자 비밀번호가 평문으로 적혀 있다 — 서비스 유지 시 교체, 종료 시 문서에서 제거 검토
- 인사이트 산출 중단 시점·사유 확인 필요
