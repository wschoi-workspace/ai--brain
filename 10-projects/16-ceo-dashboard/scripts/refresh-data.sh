#!/bin/bash
# CEO Dashboard 데이터 갱신 스크립트
# Usage: bash scripts/refresh-data.sh
#        bash scripts/refresh-data.sh --serve  (갱신 후 서버 시작)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_DIR/data"
SKILL_DIR="$(cd "$PROJECT_DIR/../../.claude/skills/start-day/scripts" 2>/dev/null && pwd || echo "")"

mkdir -p "$DATA_DIR"

echo "=== CEO Dashboard 데이터 갱신 ==="
echo "시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# ===== 1. Gmail/Calendar API (스킬 스크립트 존재 시) =====
if [ -n "$SKILL_DIR" ] && [ -f "$SKILL_DIR/gmail_unreplied.py" ]; then
    echo "[1/4] Gmail 미회신 메일 조회..."
    python3 "$SKILL_DIR/gmail_unreplied.py" > "$DATA_DIR/_raw_unreplied.json" 2>/dev/null || echo "  ⚠ Gmail 미회신 조회 실패 (인증 확인 필요)"

    echo "[2/4] Gmail 최근 3일 메일 조회..."
    # gmail_read.py는 search 서브커맨드 사용
    if [ -f "$SKILL_DIR/gmail_read.py" ]; then
        python3 "$SKILL_DIR/gmail_read.py" search "in:inbox" --days 3 > "$DATA_DIR/_raw_recent.json" 2>/dev/null || echo "  ⚠ Gmail 최근 메일 조회 실패"
    fi
else
    echo "[1-2/4] Gmail 스킬 없음 — 스킵 (기존 데이터 유지)"
fi

if [ -n "$SKILL_DIR" ] && [ -f "$SKILL_DIR/gcal.py" ]; then
    TODAY=$(date '+%Y-%m-%d')
    WEEK_END=$(date -v+6d '+%Y-%m-%d' 2>/dev/null || date -d '+6 days' '+%Y-%m-%d' 2>/dev/null || echo "")

    echo "[3/4] Google Calendar 오늘 일정 조회..."
    python3 "$SKILL_DIR/gcal.py" list --date "$TODAY" > "$DATA_DIR/_raw_cal_today.json" 2>/dev/null || echo "  ⚠ Calendar 오늘 조회 실패"

    if [ -n "$WEEK_END" ]; then
        echo "[3/4] Google Calendar 금주 일정 조회..."
        python3 "$SKILL_DIR/gcal.py" list --from "$TODAY" --to "$WEEK_END" > "$DATA_DIR/_raw_cal_week.json" 2>/dev/null || echo "  ⚠ Calendar 금주 조회 실패"
    fi
else
    echo "[3/4] Calendar 스킬 없음 — 스킵 (기존 데이터 유지)"
fi

# ===== 2. API 데이터 변환 =====
echo "[4/4] API 데이터 → 대시보드 JSON 변환..."
python3 "$SCRIPT_DIR/transform-api-data.py" "$DATA_DIR" 2>/dev/null || echo "  ⚠ 변환 실패 (raw 데이터 확인 필요)"

echo ""
echo "=== 갱신 완료 ==="
echo "  데이터: $DATA_DIR/"
ls -la "$DATA_DIR"/*.json 2>/dev/null | awk '{print "  " $NF " (" $5 " bytes)"}'

# ===== 3. 서버 시작 (옵션) =====
if [[ "${1:-}" == "--serve" ]]; then
    echo ""
    echo "=== 로컬 서버 시작 ==="
    # 기존 8080 서버 종료
    lsof -ti:8080 | xargs kill 2>/dev/null || true
    sleep 0.5

    python3 -m http.server 8080 --directory "$PROJECT_DIR" &
    SERVER_PID=$!
    echo "  http://localhost:8080 (PID: $SERVER_PID)"

    # macOS
    if command -v open &>/dev/null; then
        open "http://localhost:8080"
    # Linux
    elif command -v xdg-open &>/dev/null; then
        xdg-open "http://localhost:8080"
    fi

    echo "  Ctrl+C로 서버 종료"
    wait $SERVER_PID
fi
