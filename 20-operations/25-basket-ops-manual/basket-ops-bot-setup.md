# Basket 운영 일일보고 봇 — 셋업 가이드

운영자가 텔레그램에 자유롭게 보고 → 봇이 **12섹션 구조화 + 부족분 되물음** → **구글 시트 1행 append** → **승인 필요 건은 매니저에게 강조 전송**.

- 본체: `00-system/02-scripts/basket-ops-bot.py`
- 상시가동: `00-system/02-scripts/com.basket.ops-bot.plist`
- 시트 구조: `basket-업무보고-양식.xlsx` 의 `일일보고(리스트)` 13열과 동일

---

## 기능
- **일일보고**: 자유 보고 → GPT 12섹션 구조화 → 부족분 되물음 → 구글 시트 append → 승인 건 매니저 알림
- **/todo**: 오늘 요일 자동 인식 → 해당 요일 TO-DO 체크리스트 표시 → 미완료·이슈 수집 → `TODO이행` 탭 기록(이슈는 매니저 알림). 데이터 소스 = `basket-todo-checklist.json`(엑셀 v2와 동일 소스)

## 동작 흐름
```
운영자 → (텔레그램에 자유 보고)
  → OpenAI 구조화(지출·송금승인·특이·장비·업무·대관·스태프·구매·입점·복기)
  → 빠진 핵심 0~2개만 되물음(혼합 입력)
  → 요약 확인 [✅ 등록 / ✏️ 다시]
  → 구글 시트 일일보고 탭에 1행 append
  → ③송금·승인 / ⑤장비 견적·AS / ⑩입점 이 있으면 → 매니저에게 🔔 별도 알림
```

## 사전 준비 (사용자 작업)
1. **전용 봇 생성** — 텔레그램 @BotFather → `/newbot` → 토큰 발급 → `.env`의 `BASKET_BOT_TOKEN`
2. **구글 시트 준비** — `basket-업무보고-양식.xlsx`를 구글드라이브 업로드 → **구글 시트로 변환** → URL `/d/<ID>` 를 `.env`의 `BASKET_REPORT_SHEET_ID`. 탭 이름이 `일일보고`인지 확인(아니면 `BASKET_REPORT_SHEET_TAB` 수정)
   - 탭 2개 준비: `일일보고`(일일보고 리스트) + `TODO이행`(요일별 체크 로그: 날짜·요일·담당·미완료/이슈·시각)
   - gws CLI가 이 시트에 쓰기 권한이 있어야 함(기존 daily-report-bot과 동일 계정 사용)
3. **매니저 chat_id** — 알림 받을 사람이 봇에게 아무 메시지나 보낸 뒤, chat_id 확인 → `.env`의 `BASKET_MANAGER_CHAT_ID`
4. `OPENAI_API_KEY` 는 기존 값 재사용

## 실행
```bash
# 단발 테스트
/Users/choi_ai/do-better-workspace/20-operations/24-second-brain/.venv311/bin/python \
  00-system/02-scripts/basket-ops-bot.py

# 상시가동(launchd)
cp 00-system/02-scripts/com.basket.ops-bot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.basket.ops-bot.plist
# 로그: tail -f /tmp/basket-ops-bot.log
```

## 검증
1. 봇에게 `/start` 또는 그냥 보고 입력 → 12섹션 요약이 돌아오는지
2. `✅ 등록` → 구글 시트 일일보고 탭에 행이 추가되는지
3. "장비 견적" 같은 결재 건 포함 보고 → 매니저 chat에 🔔 알림 오는지

## 비고
- 기존 `daily-report-bot.py`(전사 직원보고)와 **별도 봇·별도 프로세스**다. 토큰·PID락(`/tmp/basket-ops-bot.pid`)·시트 모두 분리.
- 매장 슬립/네트워크 끊김 대비는 기존 `caffeinate`/launchd KeepAlive와 동일하게 동작.
- 향후: 주간/월간 자동 집계, REM 복기 강화, 발주리스트 자동 생성 연계.
