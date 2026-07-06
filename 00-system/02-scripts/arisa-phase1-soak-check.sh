#!/usr/bin/env bash
# ARISA Phase 1 soak 점검 — 공유 코어 전환 후 봇/배치 무회귀 확인
# 사용: bash arisa-phase1-soak-check.sh   (언제든 재실행 가능)
#
# 확인:
#  1) 봇 3종 프로세스 생존 + 단일 인스턴스(중복 폴러 없음)
#  2) 각 봇 로그에 전환 관련 에러(import/shared/시트append/Traceback) 없는지
#     — 단, 종료 시 qdrant __del__ ImportError(무해 teardown 노이즈)는 제외
#  3) shared 패키지 import 정상
set -uo pipefail

PY=$HOME/do-better-workspace/20-operations/24-second-brain/.venv311/bin/python
SCRIPTS=$HOME/do-better-workspace/00-system/02-scripts
TODAY=$(date '+%Y-%m-%d')
PROBLEMS=0

echo "════════ ARISA Phase 1 soak 점검 ($(date '+%Y-%m-%d %H:%M')) ════════"

# 1) 프로세스 생존 + 단일 인스턴스
echo ""
echo "── ① 봇 프로세스 (1개여야 정상) ──"
check_proc() {
  local name="$1" pat="$2"
  local n; n=$(pgrep -f "$pat" | wc -l | tr -d ' ')
  if [ "$n" = "1" ]; then echo "  ✓ $name: 1개";
  elif [ "$n" = "0" ]; then echo "  ✗ $name: 미가동(!)"; PROBLEMS=$((PROBLEMS+1));
  else echo "  ⚠ $name: ${n}개 — 중복 폴러(메시지 유실 위험)"; PROBLEMS=$((PROBLEMS+1)); fi
}
check_proc "second-brain" "24-second-brain/bot.py"
check_proc "basket-ops"   "basket-ops-bot.py"
check_proc "daily-report" "daily-report-bot.py"

# 2) 로그 에러 스캔 (오늘자, 무해 노이즈 제외)
echo ""
echo "── ② 로그 에러 스캔 (오늘, qdrant teardown 노이즈 제외) ──"
scan_log() {
  local name="$1" log="$2"
  [ -f "$log" ] || { echo "  - $name: 로그 없음"; return; }
  local hits
  hits=$(grep "$TODAY" "$log" 2>/dev/null \
    | grep -iE "Traceback|ModuleNotFoundError|No module named|sheet append (fail|error)|Sheet save error|ImportError" \
    | grep -v "sys.meta_path is None" \
    | grep -vi "qdrant" | tail -5)
  if [ -z "$hits" ]; then echo "  ✓ $name: 에러 없음";
  else echo "  ✗ $name: 에러 발견 ↓"; echo "$hits" | sed 's/^/      /'; PROBLEMS=$((PROBLEMS+1)); fi
}
scan_log "second-brain" /tmp/second-brain-bot.log
scan_log "basket-ops"   /tmp/basket-ops-bot.log
scan_log "daily-report" /tmp/daily-report-bot.log

# 3) shared import 정상
echo ""
echo "── ③ shared 패키지 import ──"
if (cd "$SCRIPTS" && "$PY" -c "import sys; sys.path.insert(0,'.'); from shared import normalize,employee,gws,llm,telegram; import shared.logging" 2>/dev/null); then
  echo "  ✓ shared import OK"
else
  echo "  ✗ shared import 실패(!)"; PROBLEMS=$((PROBLEMS+1))
fi

# 4) 시트 append 라이브 흔적(보고가 실제 들어왔는지 — 참고)
echo ""
echo "── ④ 오늘 실제 시트 저장 시도 흔적(참고) ──"
appended=$(grep "$TODAY" /tmp/daily-report-bot.log /tmp/basket-ops-bot.log 2>/dev/null | grep -ic "append")
echo "  오늘 append 관련 로그: ${appended}건 (0이면 아직 실보고 미발생 — append 경로 미검증)"

echo ""
if [ "$PROBLEMS" = "0" ]; then
  echo "✅ 종합: 이상 없음 (PROBLEMS=0)"
else
  echo "🔴 종합: 점검 필요 항목 ${PROBLEMS}건 — 위 ✗/⚠ 확인"
fi
exit 0
