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
echo -n "  dashboard-server(통합 셸): "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8780/
echo ""

echo ""
echo "=== Phase 1: 프록시 검증 ==="
echo -n "  /arisa2/api/health: "
curl -s -o /dev/null -w "%{http_code}" http://localhost:8780/arisa2/api/health
echo ""

echo ""
echo "=== Phase 2: users.json — 실파일이 SSOT (vNext W0-1, 2026-08-03) ==="
# 과거: arisa2/data/users.json으로 심링크를 만들었다. arisa2 폐기 결정(vNext)에 따라
# 2026-08-03 심링크를 실파일로 역전했다 — 이 블록이 심링크를 되살리면 폐기가 막히고,
# 실파일을 .bak으로 밀어내는 순간 전 직원 로그인이 죽는다. 심링크 발견 시 경고만 한다.
DASHBOARD_USERS="$WS/00-system/01-templates/_data/users.json"
if [ -L "$DASHBOARD_USERS" ]; then
  echo "  ⚠️ users.json이 아직 심링크다 — vNext W0-1 역전 절차(cp -L → mv)를 먼저 실행할 것"
elif [ -f "$DASHBOARD_USERS" ]; then
  echo "  OK: 실파일 ($(wc -c < "$DASHBOARD_USERS" | tr -d ' ')B)"
else
  echo "  ⚠️ users.json 없음 — 백업(~/plist-backups/users.json.bak-*)에서 복원할 것"
fi

echo ""
echo "=== Phase 3: Tailscale serve 전환 (443 → 8780) + Funnel off ==="
echo "  1) 기존 443 프록시(8787) 제거 후 8780으로 교체:"
echo "     sudo tailscale serve --https=443 off   # 기존 8787 제거(설정돼 있다면)"
echo "     sudo tailscale serve --bg 8780         # 443 → localhost:8780"
echo "  2) 외부 인터넷 공개(Funnel) 끄기 — tailnet 전용:"
echo "     sudo tailscale funnel --https=8443 off"
echo "     (또는 전체: sudo tailscale funnel reset)"
echo "  현재 상태:"
tailscale serve status 2>/dev/null || echo "  (tailscale serve 미설정)"
tailscale funnel status 2>/dev/null || true

echo ""
echo "=== 완료 ==="
echo "단일 URL: https://server-mini-macmini.tail7739de.ts.net/  (tailnet 전용)"
echo "  /           → 통합 셸 (역할별 탭: 프로젝트 / Brief / Weekly / Decision Window)"
echo "  /projects   → 프로젝트 포트폴리오 (셸 iframe·직접 접속 겸용)"
echo "  /dashboard·/team → /로 301 리다이렉트 (구 링크 호환)"
echo "  /arisa2/*   → ARISA 2.0 프록시 (localhost:8787)"
