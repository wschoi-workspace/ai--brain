#!/bin/bash
# morning-telegram.sh — 매일 아침 /morning 실행 후 텔레그램 체크리스트 발송
# launchd에 의해 매일 08:00 KST 자동 실행

set -euo pipefail

# ── 설정 ──
WORKSPACE="/Users/choi_ai/do-better-workspace"
BOT_TOKEN="8708336649:AAH1iYv8PujNZqBcG4Fo7iXeHAhAZnpyH80"
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

PROMPT='다음을 순서대로 실행해줘:

1. /morning 스킬을 실행하여 오늘의 모닝 브리핑을 수집하고 HTML 리포트를 생성해줘.

2. 수집된 데이터를 기반으로 텔레그램 체크리스트 메시지를 작성해줘. 형식:

☀️ *모닝 체크리스트 — {M/D} ({요일})*
━━━━━━━━━━━━━━━━━━
🔴 *긴급 처리*
□ {항목}
🟡 *회신 필요*
□ {항목}
📋 *확인/참고*
□ {항목}
📅 *오늘 일정*
{시간} - {일정}
💰 *송금 알림* (있을 때만)
{내용}
━━━━━━━━━━━━━━━━━━
🤖 Claude Code · /morning

3. 작성한 메시지를 다음 curl 명령으로 텔레그램에 발송해줘:
curl -s -X POST "https://api.telegram.org/bot'"$BOT_TOKEN"'/sendMessage" -H "Content-Type: application/json" -d "{\"chat_id\": '"$CHAT_ID"', \"text\": \"(위 메시지)\", \"parse_mode\": \"Markdown\"}"

반드시 3단계 모두 완료해줘.'

"$CLAUDE" -p \
  --dangerously-skip-permissions \
  --max-budget-usd 1.0 \
  "$PROMPT"

echo "[$(date)] morning-telegram 완료"
