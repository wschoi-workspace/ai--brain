#!/usr/bin/env zsh
# ─────────────────────────────────────────────────────────────
# 맥미니 무인 리서치 실행 — 승인 없이 끝까지 자동
# 맥미니 터미널(ssh macmini-ts 또는 VNC)에 그대로 붙여넣기
# ─────────────────────────────────────────────────────────────
set -e

# [1] claude CLI 설치 (이미 있으면 스킵됨)
command -v claude >/dev/null 2>&1 || npm i -g @anthropic-ai/claude-code

# [2] 인증 — 아래 둘 중 하나 (한 번만 하면 됨)
#   (A) API 키:  export ANTHROPIC_API_KEY=sk-ant-...   ← 이 줄 채워서 실행
#   (B) 로그인:  claude   ← 실행 후 로그인 절차 마치고 Ctrl+C 로 빠져나오기
# ↓↓↓ 여기에 키를 넣거나(A), 위 (B)를 먼저 수동 실행하세요
# export ANTHROPIC_API_KEY=

# [3] 리포지토리 동기화 (foundation 브랜치로)
cd ~/do-better-workspace
git fetch origin
git stash -u -m pre34 2>/dev/null || true
git checkout -B feat/34-us-marketing origin/feat/34-us-marketing

# [4] 무인 리서치 실행 — screen 세션(SSH 끊겨도 유지) + 승인 스킵
BRIEF="10-projects/34-rent-us-marketing-playbook/research/research-brief.md"
LOG="10-projects/34-rent-us-marketing-playbook/research/_run.log"
screen -dmS rent34 zsh -lc "cd ~/do-better-workspace && claude --dangerously-skip-permissions -p \"$(cat $BRIEF)\" > $LOG 2>&1"

echo "✅ 실행 시작됨 (screen: rent34)"
echo "   진행 로그:   tail -f ~/do-better-workspace/$LOG"
echo "   세션 접속:   screen -r rent34   (빠져나오기: Ctrl+A, D)"
