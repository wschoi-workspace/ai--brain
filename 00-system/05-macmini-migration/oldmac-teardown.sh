#!/usr/bin/env bash
# oldmac-teardown.sh — [기존 맥에서 실행 · 컷오버 시점] 워크스페이스 launchd 잡 일괄 정지.
# ⚠️ 봇 중복 가동 방지 필수: 텔레그램 봇이 두 기기에서 동시에 폴링(getUpdates)하면 충돌·중복발송.
#    맥미니에서 잡을 로드하기 "직전"에 이 스크립트로 기존 맥 잡들을 내린다.
# 되돌리기: 각 plist를 다시 launchctl load 하면 복구.
set -euo pipefail
LABELS=(
  com.basket.ops-bot com.basket.weekly-insight com.basket.onboarding
  com.arisa.watcher com.arisa.telegram-bot com.arisa.caffeinate
  com.arisa.daily-report-bot com.arisa.daily-report-bot-restart
  com.arisa.zero-server com.arisa.second-brain
  com.dobetter.morning-telegram com.dobetter.ax-newsletter com.dobetter.ax-newsletter-purge
  com.projectrent.daily-brief com.projectrent.dashboard com.projectrent.weekly-report
)
echo "▶ 기존 맥 launchd 잡 정지(${#LABELS[@]}개)…"
for L in "${LABELS[@]}"; do
  P="$HOME/Library/LaunchAgents/$L.plist"
  if [ -f "$P" ]; then
    launchctl unload "$P" 2>/dev/null && echo "  ⏹ $L unloaded" || echo "  - $L (이미 내림/미등록)"
  fi
done
echo
echo "✅ 정지 완료. 남은 봇 프로세스 확인:"
ps aux | grep -iE "basket-ops-bot|basket-weekly|daily-report-bot|arisa|second-brain" | grep -v grep | awk '{print "  PID "$2"  "$11" "$12}' || echo "  (없음)"
echo
echo "→ 이제 맥미니에서 launchd 로드(가이드 STEP 10). 봇은 한 기기에서만 돌게."
