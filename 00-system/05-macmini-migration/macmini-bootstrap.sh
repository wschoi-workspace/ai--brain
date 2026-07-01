#!/usr/bin/env bash
# macmini-bootstrap.sh — [맥미니에서 실행] 런타임·레포·의존성·인증·launchd 일괄 세팅.
# 전제: 맥미니 사용자명도 'choi_ai' 권장(plist가 /Users/choi_ai/... 절대경로 사용).
#       다르면 STEP 6에서 경로 치환 필요(스크립트가 감지해 안내).
# 사용: bash macmini-bootstrap.sh ~/Downloads/basket-migration-bundle.tar.gz
set -euo pipefail
BUNDLE="${1:-$HOME/Desktop/basket-migration-bundle.tar.gz}"
HOME_DIR="$HOME"
WS="$HOME_DIR/do-better-workspace"
VENV="$WS/20-operations/24-second-brain/.venv311"
export PATH="$HOME_DIR/.local/bin:$HOME_DIR/.npm-global/bin:$PATH"

say(){ echo; echo "═══ $* ═══"; }

# 0) 사용자명 확인
[ "$(whoami)" = "choi_ai" ] || echo "⚠️ 사용자명이 choi_ai가 아님($(whoami)) — plist 절대경로 치환 필요(STEP 6 참고)"

say "1. Xcode CLT / Homebrew / 런타임"
xcode-select -p >/dev/null 2>&1 || { echo "Xcode CLT 설치(팝업 확인)…"; xcode-select --install || true; }
command -v brew >/dev/null || { echo "Homebrew 설치…"; /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; }
eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || true)"
command -v node >/dev/null || brew install node
command -v git  >/dev/null || brew install git
command -v uv   >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh

say "2. npm 전역 경로 + CLI 설치"
npm config get prefix | grep -q ".npm-global" || npm config set prefix "$HOME_DIR/.npm-global"
npm install -g @google/clasp@3.3.0 @kfastov/tgcli@2.0.8 @anthropic-ai/claude-code netlify-cli || true
# gws 는 npm 패키지 아님 → 번들의 바이너리 사용(STEP 5에서 배치)

say "3. 레포 클론(2개)"
[ -d "$WS/.git" ] && (cd "$WS" && git pull) || git clone https://github.com/wschoi-workspace/ai--brain.git "$WS"
ARISA="$HOME_DIR/arisa-project-memory"
[ -d "$ARISA/.git" ] && (cd "$ARISA" && git pull) || git clone https://github.com/wschoi-workspace/arisa-project-memory.git "$ARISA"

say "4. venv 재생성 + 의존성"
uv venv --python 3.11 "$VENV"
uv pip install --python "$VENV/bin/python" -r "$WS/00-system/05-macmini-migration/requirements-venv311.txt"
# arisa 별도 venv
if [ -f "$ARISA/requirements.txt" ]; then
  uv venv --python 3.11 "$ARISA/.venv"
  uv pip install --python "$ARISA/.venv/bin/python" -r "$ARISA/requirements.txt"
else
  echo "⚠️ arisa requirements.txt 없음 — arisa venv 수동 구성 필요"
fi

say "5. 번들 풀기(.env·인증·gws바이너리·plist)"
[ -f "$BUNDLE" ] || { echo "❌ 번들 없음: $BUNDLE (기존맥 transfer-bundle.sh → AirDrop)"; exit 1; }
TMP="$(mktemp -d)"; tar -xzf "$BUNDLE" -C "$TMP"
cp "$TMP/workspace/.env" "$WS/.env" && echo "  ✓ .env"
mkdir -p "$HOME_DIR/.config" "$HOME_DIR/Library/Application Support" "$HOME_DIR/.npm-global/bin"
[ -d "$TMP/config/gws" ]   && cp -R "$TMP/config/gws" "$HOME_DIR/.config/gws" && echo "  ✓ gws 인증"
[ -d "$TMP/config/tgcli" ] && cp -R "$TMP/config/tgcli" "$HOME_DIR/Library/Application Support/tgcli" && echo "  ✓ tgcli 세션"
[ -f "$TMP/config/.clasprc.json" ] && cp "$TMP/config/.clasprc.json" "$HOME_DIR/.clasprc.json" && echo "  ✓ clasp(만료시 재로그인)"
[ -f "$TMP/bin/gws" ] && cp "$TMP/bin/gws" "$HOME_DIR/.npm-global/bin/gws" && chmod +x "$HOME_DIR/.npm-global/bin/gws" && echo "  ✓ gws 바이너리"

say "6. launchd plist 설치(경로 치환 포함)"
mkdir -p "$HOME_DIR/Library/LaunchAgents"
for f in "$TMP/launchagents/"*.plist; do
  [ -e "$f" ] || continue
  dest="$HOME_DIR/Library/LaunchAgents/$(basename "$f")"
  # 사용자명 다르면 절대경로 치환
  sed "s#/Users/choi_ai#$HOME_DIR#g" "$f" > "$dest"
  echo "  ✓ $(basename "$f")"
done
rm -rf "$TMP"

say "✅ 부트스트랩 완료 — 남은 수동 단계(가이드 STEP 7~10)"
cat <<EOF
  7. 슬립 방지:   sudo pmset -a sleep 0 disablesleep 1 displaysleep 0 womp 1
  8. 재인증 확인: gws auth status / clasp login(만료시) / tgcli auth status
  9. ⚠️ 기존 맥에서 oldmac-teardown.sh 먼저 실행(봇 중복가동 방지!) → 그다음 아래 로드
 10. launchd 로드:
     for L in \$(ls ~/Library/LaunchAgents/com.{basket,arisa,dobetter,projectrent}.*.plist); do launchctl load "\$L"; done
     launchctl list | grep -iE "basket|arisa|dobetter|projectrent"
EOF
