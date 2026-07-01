#!/bin/bash
# morning-telegram.sh — 매일 아침 /morning 실행 후 텔레그램 체크리스트 발송
# launchd에 의해 매일 08:00 KST 자동 실행

set -euo pipefail

# ── 설정 ──
WORKSPACE="/Users/choi_ai/do-better-workspace"
# 토큰 하드코딩 제거 — .env의 DAILY_REPORT_MANAGER_BOT_TOKEN(@brocallmebot)에서 직접 추출
# (process substitution/소싱 대신 grep+cut — launchd 환경에서도 결정론적)
BOT_TOKEN=""
[ -f "$WORKSPACE/.env" ] && BOT_TOKEN="$(grep -E '^DAILY_REPORT_MANAGER_BOT_TOKEN=' "$WORKSPACE/.env" | head -1 | cut -d= -f2-)"
CHAT_ID="8123576679"
CLAUDE="/Users/choi_ai/.npm-global/bin/claude"
LOG_DIR="$WORKSPACE/40-personal/41-daily/logs"
LOG_FILE="$LOG_DIR/morning-telegram-$(date +%Y-%m-%d).log"

# ── 로그 디렉토리 ──
mkdir -p "$LOG_DIR"

exec > "$LOG_FILE" 2>&1
echo "[$(date)] morning-telegram 시작"

# ── PATH 설정 (launchd 환경에서 필요) ──
export PATH="/usr/local/bin:/usr/bin:/bin:/Users/choi_ai/.npm-global/bin:$PATH"

# ── Claude CLI로 /morning 실행 + 텔레그램 체크리스트 생성 ──
cd "$WORKSPACE"

# 세컨드브레인에 남긴 할일(next_action) 수집 — 체크리스트에 주입 (실패해도 morning은 진행)
SB_TODOS="$(python3 "$WORKSPACE/00-system/02-scripts/morning-sb-todos.py" 2>/dev/null || true)"

PROMPT='다음을 순서대로 실행해줘:

1. /morning 스킬을 실행하여 오늘의 모닝 브리핑을 수집하고 HTML 리포트를 생성해줘.

1-1. 구글시트에서 이번 주 주간분장 현황을 읽어와줘:
SHEET_ID="$(grep "^DAILY_REPORT_SHEET_ID=" .env | cut -d= -f2-)"
gws sheets spreadsheets values get --params "{\"spreadsheetId\":\"$SHEET_ID\",\"range\":\"주간분장!A2:J200\"}"
결과에서 이번 주차(W로 시작하는 현재 ISO 주차)의 미착수/진행중 항목을 팀별로 정리해둬.
데이터가 없거나 탭이 없으면 이 단계를 건너뛰면 돼.

2. 수집된 데이터를 기반으로 텔레그램 체크리스트 메시지를 작성해줘. 형식:

☀️ *모닝 체크리스트 — {M/D} ({요일})*
━━━━━━━━━━━━━━━━━━
🔴 *긴급 처리*
□ {항목}
🟡 *회신 필요*
□ {항목}
📋 *확인/참고*
□ {항목}
📋 *주간분장 현황* (1-1에서 수집한 데이터가 있을 때만 포함)
{미착수/진행중 항목을 팀별로 정리. 형식:}
{⬜ [팀] 업무내용 — @담당 (~마감)}
{🔄 [팀] 진행중 업무 — @담당}
{✅ [팀] 완료된 업무 (완료 건수만 표시)}
🧠 *내가 남긴 할일* (세컨드브레인)
{아래 [세컨드브레인 할일] 목록의 □ 항목들을 그대로 옮겨 적기}
📅 *오늘 일정*
{시간} - {일정}
💰 *송금 알림* (있을 때만)
{내용}
━━━━━━━━━━━━━━━━━━
🤖 Claude Code · /morning

3. 작성한 메시지를 다음 curl 명령으로 텔레그램에 발송해줘:
curl -s -X POST "https://api.telegram.org/bot'"$BOT_TOKEN"'/sendMessage" -H "Content-Type: application/json" -d "{\"chat_id\": '"$CHAT_ID"', \"text\": \"(위 메시지)\", \"parse_mode\": \"Markdown\"}"

[세컨드브레인 할일 — 위 🧠 섹션에 이 □ 항목들을 그대로 포함할 것. 비어있으면 🧠 섹션 생략]
'"$SB_TODOS"'

반드시 3단계 모두 완료해줘.'

"$CLAUDE" -p \
  --dangerously-skip-permissions \
  --max-budget-usd 3.0 \
  "$PROMPT"

echo "[$(date)] morning-telegram 완료"
