#!/bin/bash
# deploy-dashboard-macmini.sh — 주간대시보드 + ARISA 2.0 통합 배포 (맥미니)
# 맥미니에서 실행: bash deploy-dashboard-macmini.sh
set -e

MINI_HOME="/Users/server-mini"
WS="$MINI_HOME/do-better-workspace"
ARISA2="$MINI_HOME/dev/arisa2"
PLIST_SRC="$WS/00-system/02-scripts/com.projectrent.dashboard.plist"
PLIST_DST="$MINI_HOME/Library/LaunchAgents/com.projectrent.dashboard.plist"

echo "=== Phase 0: dashboard-server.py 맥미니 가동 ==="
# git pull (최신 코드)
cd "$WS" && git pull --ff-only 2>/dev/null || echo "git pull skipped"

# plist 복사 및 등록
cp "$PLIST_SRC" "$PLIST_DST"
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
sleep 2
echo -n "  dashboard-server: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8770/dashboard
echo ""

echo ""
echo "=== Phase 1: 프록시 검증 ==="
echo -n "  /arisa2/api/health: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8770/arisa2/api/health
echo ""

echo ""
echo "=== Phase 2: users.json symlink ==="
DASHBOARD_USERS="$WS/00-system/01-templates/_data/users.json"
ARISA2_USERS="$ARISA2/data/users.json"
if [ -f "$DASHBOARD_USERS" ] && [ -d "$ARISA2/data" ]; then
  if [ -L "$ARISA2_USERS" ]; then
    echo "  symlink already exists: $(readlink "$ARISA2_USERS")"
  else
    [ -f "$ARISA2_USERS" ] && mv "$ARISA2_USERS" "$ARISA2_USERS.bak-$(date +%s)"
    ln -s "$DASHBOARD_USERS" "$ARISA2_USERS"
    echo "  created symlink: $ARISA2_USERS -> $DASHBOARD_USERS"
  fi
else
  echo "  SKIP: users.json or arisa2/data not found"
fi

echo ""
echo "=== Phase 3: Tailscale serve 설정 ==="
echo "  tailscale serve 를 8770으로 설정하려면:"
echo "    sudo tailscale serve --bg 8770"
echo "  현재 상태:"
tailscale serve status 2>/dev/null || echo "  (tailscale serve 미설정)"

echo ""
echo "=== 완료 ==="
echo "단일 URL: https://server-mini-macmini.tail7739de.ts.net/"
echo "  /dashboard  → 대표 통합 셸 (3탭: Brief / Weekly / Decision Window)"
echo "  /team       → 팀 리더 셸"
echo "  /arisa2/*   → ARISA 2.0 프록시 (localhost:8787)"
