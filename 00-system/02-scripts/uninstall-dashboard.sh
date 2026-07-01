#!/bin/bash
# 대시보드 서버 제거 (launchd 서비스 내림). 데이터(_data)는 건드리지 않음.
LABEL="com.projectrent.dashboard"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
launchctl unload "$PLIST" 2>/dev/null || true
rm -f "$PLIST"
pkill -f dashboard-server.py 2>/dev/null || true
echo "✅ 서비스 제거 완료 (데이터 _data/ 는 보존)."
