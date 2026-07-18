#!/bin/bash
# arisa-archive-pull.sh — P1 아카이브 90-archive 연동 (Team Ops Guide 2부-④)
# 맥미니(운영)에서 아카이브된 프로젝트 JSON + 아카이브 로그를 로컬 워크스페이스
# 90-archive/arisa-projects/ 로 내려받는다. 분기 정리 리추얼 때 수동 실행.
# 사용: bash arisa-archive-pull.sh   (ssh macmini 별칭 필요 — reference_macmini_ssh)
set -e

REMOTE="${ARISA_REMOTE:-macmini}"
RDATA="/Users/server-mini/do-better-workspace/00-system/01-templates/_data"
WS="$(cd "$(dirname "$0")/../.." && pwd)"
DEST="$WS/90-archive/arisa-projects"
mkdir -p "$DEST"

echo "=== 아카이브 로그 동기화 ==="
scp -q "$REMOTE:$RDATA/archive-log.jsonl" "$DEST/archive-log.jsonl" 2>/dev/null \
  && echo "  archive-log.jsonl OK" || echo "  archive-log.jsonl 없음 (아직 아카이브 0건)"

echo "=== 아카이브된 프로젝트 JSON 동기화 ==="
# 원격에서 archived 키가 있는 프로젝트 파일명만 추려 복사
FILES=$(ssh "$REMOTE" "grep -l '\"archived\"' $RDATA/projects/*.json 2>/dev/null" || true)
if [ -z "$FILES" ]; then
  echo "  아카이브된 프로젝트 없음"
else
  for f in $FILES; do
    scp -q "$REMOTE:$f" "$DEST/$(basename "$f")"
    echo "  $(basename "$f") OK"
  done
fi
echo "완료 → $DEST"
