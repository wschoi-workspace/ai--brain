#!/bin/bash
# send-newsletter.sh — AX 뉴스레터 주간 발송 래퍼
# launchd가 매주 월 09:00 KST 호출. send-newsletter.py로 다음 회차 발송.

set -euo pipefail

BASE="/Users/server-mini/do-better-workspace/10-projects/28-ai-education-ax/newsletter"
PY="/Users/server-mini/do-better-workspace/20-operations/24-second-brain/.venv311/bin/python"
LOG_DIR="/Users/server-mini/do-better-workspace/40-personal/41-daily/logs"
LOG_FILE="$LOG_DIR/ax-newsletter-$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"
export PATH="/usr/local/bin:/usr/bin:/bin:/Users/server-mini/.npm-global/bin:$PATH"

{
  echo "[$(date)] ax-newsletter 발송 시작"
  "$PY" "$BASE/send-newsletter.py" --audience employees
  echo "[$(date)] ax-newsletter 발송 종료"
} >> "$LOG_FILE" 2>&1
