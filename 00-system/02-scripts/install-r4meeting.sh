#!/bin/bash
# R4 Meeting OS 시뮬레이터 설치 — 사용자/경로/파이썬 자동 감지, launchd 서비스 생성·로드.
#
#   bash install-r4meeting.sh            # 설치+가동
#   DRY_RUN=1 bash install-r4meeting.sh  # plist만 출력
#   R4_PORT=9001 bash install-r4meeting.sh
set -e
SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
SERVER="$SCRIPTS/meeting-simulator-server.py"
PY="$(command -v python3 || echo /usr/bin/python3)"
PORT="${R4_PORT:-8781}"
LABEL="com.projectrent.r4meeting"
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
  <key>StandardOutPath</key><string>/tmp/r4-meeting.log</string>
  <key>StandardErrorPath</key><string>/tmp/r4-meeting.err</string>
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

[ -f "$SERVER" ] || { echo "✖ $SERVER 없음"; exit 1; }
mkdir -p "$HOME/Library/LaunchAgents"
echo "$PLIST_XML" > "$PLIST"
launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"
sleep 1.5
if curl -s "http://127.0.0.1:$PORT/api/health" | grep -q '"ok"'; then
  echo "✅ 설치·가동 완료 → http://127.0.0.1:$PORT"
  echo "   Tailscale 노출: tailscale serve --bg --https=$PORT http://127.0.0.1:$PORT"
else
  echo "⚠ 헬스체크 실패 — /tmp/r4-meeting.err 확인"
fi
