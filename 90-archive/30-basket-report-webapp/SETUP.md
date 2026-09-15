# RX 매장 일일보고 웹앱 — 셋업·배포 가이드

낮에 직원이 봇 `/jot`으로 남긴 진행로그를, 담당자가 웹앱에 로그인해 **AI 자동 구성 → 검토 → 제출**하면 매장별 일일보고가 완성된다. MVP = Basket 1매장.

- 백엔드: `00-system/02-scripts/basket-report-webapp.gs`
- 프론트: `10-projects/30-basket-report-webapp/index.html`
- 데이터: 구글시트 "Basket 업무보고 (봇 연동)" `18fx3jmb…` (탭: 일일보고 / 진행로그 / 담당자 / TODO이행)

---

## 전체 흐름
```
[낮] 직원 → 텔레그램 봇  /jot 오전 발주 완료, 사진전 대관 회신대기
          → 진행로그 탭 누적 (store_id·날짜·시간·작성자·내용)
[보고] 담당자 → 웹앱 로그인(매장코드 BASKET + PIN)
          → 오늘 진행로그 자동 표시 → [AI 자동 구성] → 12섹션 초안
          → 검토·수정 → [제출] → 일일보고 탭 append + 결재 건 매니저 알림
```

## ✅ 이미 완료(자동)
- 시트 탭 생성: `진행로그`(헤더), `담당자`(헤더+Basket 시드), `일일보고`에 store_id 컬럼
- 봇 `/jot` 추가·배포(launchd 재시작 완료)

## 🙋 사용자가 할 일

### 1) 담당자 PIN 등록 (시트)
구글시트 `담당자` 탭 — 등록 완료(아래). 매장코드·PIN은 대소문자/공백 무시 비교.
| store_id | 매장명 | 매장코드 | 담당자명 | PIN | role |
|---|---|---|---|---|---|
| basket | Basket | **basket-00** | 양은정 | 1324 | staff |
| basket | Basket | **basket-00** | 김준호 | 1324 | staff |
> 로그인: 매장코드 **basket-00** + PIN. 멀티매장/매니저는 행 추가로 확장.

### 2) Apps Script 배포 — ✅ 완료 (clasp CLI, 2026-06-23)
- 계정: **ws.choi@project-rent.com** (clasp 3.3.0 로그인)
- scriptId: `1BuZNwVkuqCv-tpKIjjRtyFOiSSCM-9Suc5zqHjRjC4ropd-FWUKbzHwp`
- 에디터: https://script.google.com/d/1BuZNwVkuqCv-tpKIjjRtyFOiSSCM-9Suc5zqHjRjC4ropd-FWUKbzHwp/edit
- **운영 웹앱 URL(@1, 익명접근 200 확인)**:
  `https://script.google.com/macros/s/AKfycbxagxA-BXfGAYQEK7Ye4lUQb4MWDZvH3vOqGlIi_5uY6S8iSKiV12sU_afbusKuVwV7GA/exec`
- 매니페스트: `executeAs: USER_DEPLOYING` / `access: ANYONE_ANONYMOUS`
- 스크립트 속성 4종(SHEET_ID·OPENAI_API_KEY·BASKET_BOT_TOKEN·MANAGER_CHAT_ID): **소유자가 프로젝트 설정 > 스크립트 속성 UI에 직접 입력**(2026-06-23). 비밀키를 소스/배포물/공개엔드포인트로 주입하는 경로는 자격증명 노출 방지로 차단됨 → UI 직접입력이 유일한 안전경로. 소스(Code.gs/setup.gs)엔 비밀값 무함유.
- 권한 승인: 로그인 시도 시 SpreadsheetApp 스코프 OAuth 승인 완료.
- **E2E 검증 완료(2026-06-23)**: `basket-00`/`zxcv102324!`(admin) → 대표 대시보드 렌더 확인. 빈 상태("표시할 매장 보고가 없습니다")는 당일 제출 보고 0건일 때 정상.

> 재배포(코드 수정 후): `/tmp/basket-clasp`에서 `clasp push --force` → `clasp create-deployment`.
> ⚠️ 시트 컬럼/SECTION_KEYS 변경 시 봇(`basket-ops-bot.py`)과 **동시 반영** 필수.

### 3) 동작 테스트 (E2E)
1. 텔레그램 봇에 `/jot 오전 발주 완료` → "📝 진행 기록됨"
2. 웹앱 URL 접속 → 매장코드 `basket-00` + PIN `1324` → 로그인
3. "오늘 진행로그"에 1번 내용 표시 → **[AI 자동 구성]** → 12섹션 초안
4. 수정 후 **[제출]** → 시트 `일일보고`에 store_id 포함 행 추가
5. (장비 견적/송금/입점 포함 시) 매니저(Bro)에게 텔레그램 알림

---

## 비고
- 인증은 매장코드+PIN(내부 직원용 경량). PIN은 `담당자` 시트에 보관, Apps Script가 서버측 검증.
- AI 자동 구성은 Apps Script가 OpenAI를 직접 호출(UrlFetchApp). 키 없으면 빈 폼으로 표시.
- 멀티매장 확장: `담당자`/`진행로그`/`일일보고` 모두 store_id 기준 → 행 추가만으로 매장 늘림.
- 추후: Executive(매장간 비교) 뷰, Vercel 정적호스팅+API 이전, 봇 일일보고와 진행로그 통합.
