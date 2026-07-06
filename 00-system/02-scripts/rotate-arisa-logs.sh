#!/bin/bash
# rotate-arisa-logs.sh — ARISA/basket/projectrent/dobetter 로그 로테이션.
# launchd: com.arisa.log-rotate (매일 03:50 — 04:00 daily-report-bot 재시작 직전)
#
# KeepAlive 데몬이 로그 FD를 연 채라 mv 불가 → copytruncate 패턴:
#   1MB 초과 로그를 ~/Library/Logs/arisa-archive/<이름>-YYYYMMDD.log.gz로 복사·압축 후
#   원본을 제자리 트렁케이트(: > file). /tmp 로그는 재부팅 시 소실되므로 아카이브가 영구 사본.
# 14일 초과 아카이브는 삭제.

set -uo pipefail

ARCHIVE_DIR="$HOME/Library/Logs/arisa-archive"
THRESHOLD=$((1024 * 1024))   # 1MB
KEEP_DAYS=14
STAMP=$(date +%Y%m%d)

mkdir -p "$ARCHIVE_DIR"

# 대상: /tmp의 ARISA 계열 로그 (glob 미매칭은 무시)
shopt -s nullglob
LOGS=(/tmp/daily-report-bot.log /tmp/arisa-telegram-bot.log /tmp/second-brain-bot.log
      /tmp/basket-ops-bot.log /tmp/arisa-zero-server.log /tmp/arisa-watcher.log
      /tmp/pr-*.log /tmp/report-backfill.log /tmp/daily-report-reminder.log
      /tmp/basket-*.log /tmp/dobetter-*.log /tmp/morning-telegram*.log /tmp/ax-newsletter*.log)

rotated=0
for f in "${LOGS[@]}"; do
  [ -f "$f" ] || continue
  size=$(stat -f%z "$f" 2>/dev/null || echo 0)
  [ "$size" -gt "$THRESHOLD" ] || continue
  base=$(basename "$f" .log)
  dest="$ARCHIVE_DIR/${base}-${STAMP}.log"
  # 같은 날 두 번 돌면 덮어쓰지 않고 이어붙임
  cat "$f" >> "$dest" && : > "$f" && gzip -f "$dest"
  echo "[$(date '+%F %T')] rotated $f ($size bytes) -> ${dest}.gz"
  rotated=$((rotated + 1))
done

# 오래된 아카이브 정리
find "$ARCHIVE_DIR" -name '*.log.gz' -mtime +"$KEEP_DAYS" -delete 2>/dev/null

echo "[$(date '+%F %T')] done — rotated=$rotated"
