#!/usr/bin/env bash
# transfer-bundle.sh — [기존 맥에서 실행] 깃에 안 올라가는 시크릿·인증·plist를 한 묶음으로.
# 결과물(~/Desktop/basket-migration-bundle.tar.gz)을 맥미니로 AirDrop → bootstrap이 풀어 씀.
# ⚠️ 이 번들엔 API키·봇토큰·구글/텔레그램 인증이 들어있다. 이관 후 반드시 삭제.
set -euo pipefail
HOME_DIR="$HOME"
WS="$HOME_DIR/do-better-workspace"
OUT="$HOME_DIR/Desktop/basket-migration-bundle.tar.gz"
STAGE="$(mktemp -d)"

echo "▶ 시크릿·인증 수집 중…"
mkdir -p "$STAGE/workspace" "$STAGE/config" "$STAGE/launchagents" "$STAGE/bin"

# 1) .env (시크릿 16키)
[ -f "$WS/.env" ] && cp "$WS/.env" "$STAGE/workspace/.env" && echo "  ✓ .env"

# 2) CLI 인증 — gws(구글), tgcli(텔레그램 세션), clasp(Apps Script)
[ -d "$HOME_DIR/.config/gws" ] && cp -R "$HOME_DIR/.config/gws" "$STAGE/config/gws" && echo "  ✓ gws 인증(.config/gws)"
[ -d "$HOME_DIR/Library/Application Support/tgcli" ] && cp -R "$HOME_DIR/Library/Application Support/tgcli" "$STAGE/config/tgcli" && echo "  ✓ tgcli 세션"
[ -f "$HOME_DIR/.clasprc.json" ] && cp "$HOME_DIR/.clasprc.json" "$STAGE/config/.clasprc.json" && echo "  ✓ clasp(.clasprc.json — 만료시 재로그인)"

# 3) gws 바이너리(= npm 패키지 아님, 단독 바이너리)
[ -f "$HOME_DIR/.npm-global/bin/gws" ] && cp "$HOME_DIR/.npm-global/bin/gws" "$STAGE/bin/gws" && echo "  ✓ gws 바이너리"

# 4) 워크스페이스 launchd plist 16종
for L in com.basket.ops-bot com.basket.weekly-insight com.basket.onboarding \
         com.arisa.watcher com.arisa.telegram-bot com.arisa.caffeinate \
         com.arisa.daily-report-bot com.arisa.daily-report-bot-restart \
         com.arisa.zero-server com.arisa.second-brain \
         com.dobetter.morning-telegram com.dobetter.ax-newsletter com.dobetter.ax-newsletter-purge \
         com.projectrent.daily-brief com.projectrent.dashboard com.projectrent.weekly-report; do
  [ -f "$HOME_DIR/Library/LaunchAgents/$L.plist" ] && cp "$HOME_DIR/Library/LaunchAgents/$L.plist" "$STAGE/launchagents/" && echo "  ✓ $L"
done

tar -czf "$OUT" -C "$STAGE" .
rm -rf "$STAGE"
echo
echo "✅ 번들 생성: $OUT"
echo "   → 맥미니로 AirDrop 후, 맥미니에서 macmini-bootstrap.sh 실행"
echo "   ⚠️ 전송·이관 완료되면 이 파일 삭제: rm \"$OUT\""
