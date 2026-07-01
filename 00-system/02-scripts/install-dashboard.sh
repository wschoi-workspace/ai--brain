#!/bin/bash
# 대시보드 서버 설치 (이관 가능) — 현재 사용자/경로/파이썬을 자동 감지해 launchd 서비스 생성·로드.
# 새 맥미니로 옮길 때: do-better-workspace 폴더(또는 00-system + _data)를 복사하고 이 스크립트 실행하면 끝.
#
#   bash install-dashboard.sh            # 설치+가동
#   DRY_RUN=1 bash install-dashboard.sh  # plist만 출력(설치 안 함)
#   DASHBOARD_PORT=9000 bash install-dashboard.sh
set -e
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
SERVER="$SCRIPTS/dashboard-server.py"
PY="$(command -v python3 || echo /usr/bin/python3)"
PORT="${DASHBOARD_PORT:-8770}"
LABEL="com.projectrent.dashboard"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

read -r -d '' PLIST_XML <<EOF || true
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$PY</string>
    <string>$SERVER</string>
    <string>$PORT</string>
  </array>
  <key>WorkingDirectory</key><string>$SCRIPTS</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/pr-dashboard.log</string>
  <key>StandardErrorPath</key><string>/tmp/pr-dashboard.err</string>
</dict>
</plist>
EOF

echo "── 감지된 설정 ──"
echo "  python : $PY"
echo "  server : $SERVER"
echo "  port   : $PORT"
echo "  plist  : $PLIST"

if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "── DRY_RUN: 생성될 plist ──"; echo "$PLIST_XML"; exit 0
fi

# 이관 시: 이미 _data가 있으면 빌드(openpyxl 필요) 실패해도 기존 데이터로 가동
if [ -n "$(ls -A "$SCRIPTS/../01-templates/_data/projects/" 2>/dev/null)" ]; then
  echo "▶ 기존 _data 발견 — 빌드 시도(실패해도 진행)..."
  bash "$SCRIPTS/build-dashboard.sh" >/dev/null 2>&1 && echo "  빌드 OK" || echo "  (빌드 생략: openpyxl 미설치 등 — 복사해온 _data로 가동)"
else
  echo "▶ 최초 빌드(openpyxl 필요)..."
  bash "$SCRIPTS/build-dashboard.sh" >/dev/null || { echo "✖ 빌드 실패 — 'pip3 install openpyxl' 후 재시도"; exit 1; }
fi
mkdir -p "$HOME/Library/LaunchAgents"
echo "$PLIST_XML" > "$PLIST"
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
sleep 1.5
if curl -s "http://127.0.0.1:$PORT/api/health" | grep -q '"ok"'; then
  echo "✅ 설치·가동 완료 → http://127.0.0.1:$PORT  (Tailscale/CF로 노출하세요)"
else
  echo "⚠ 헬스체크 실패 — /tmp/pr-dashboard.err 확인"
fi
