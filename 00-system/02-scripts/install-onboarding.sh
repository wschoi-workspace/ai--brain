#!/bin/bash
# Basket 신입 온보딩 자동발송 가동 (화~토 09:00)
set -e
SRC="$HOME/do-better-workspace/00-system/02-scripts/com.basket.onboarding.plist"
DST="$HOME/Library/LaunchAgents/com.basket.onboarding.plist"
cp "$SRC" "$DST"
launchctl unload "$DST" 2>/dev/null || true
launchctl load "$DST"
echo "✅ 온보딩 자동발송 가동 완료 (화~토 오전 9시, 8회)"
launchctl list | grep basket.onboarding || true
