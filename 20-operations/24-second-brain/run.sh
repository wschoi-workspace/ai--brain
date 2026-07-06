#!/bin/zsh
# Second Brain 봇 런처 — 키는 arisa-project-memory/.env에서만 읽는다(평문 노출 0).
set -a
source /Users/server-mini/arisa-project-memory/.env   # SECOND_BRAIN_BOT_TOKEN 전용 토큰 포함
set +a
# B단계(2026-06-19): mem0 2.x 직접 통합 위해 전용 Python 3.11 venv 사용.
# 롤백: 이 줄을 run.sh.venv39-backup의 arisa-project-memory/.venv 경로로 되돌리면 됨.
exec /Users/server-mini/do-better-workspace/20-operations/24-second-brain/.venv311/bin/python \
  /Users/server-mini/do-better-workspace/20-operations/24-second-brain/bot.py
