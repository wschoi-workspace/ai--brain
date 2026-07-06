#!/bin/bash
# basket-onboarding-sender.sh
# Basket 신입 온보딩 워크북을 화~토 09:00 한 개씩 운영팀에 텔레그램 발송.
# launchd: com.basket.onboarding.plist (일·월 제외)
# 진도는 .send-state 파일의 인덱스로 추적. 8개 모두 보내면 자동으로 멈춤.

set -uo pipefail
# 경로는 $HOME 기반 — 계정 이관(choi_ai→server-mini 등) 시에도 깨지지 않게 (2026-07-04)
export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.npm-global/bin:$PATH"

DIR="$HOME/do-better-workspace/20-operations/25-basket-ops-manual/onboarding-daily"
STATE="$DIR/.send-state"
LOG="$DIR/send.log"
TGCLI="$HOME/.npm-global/bin/tgcli"

# 수신자: 양은정(basket) / 준호 김 / 윤혜정
RECIPIENTS=(5953458732 5828702712 8452510149)

FILES=(
"01-써머리.pdf"
"02-Day1.pdf"
"03-Day2.pdf"
"04-Day3.pdf"
"05-Day4.pdf"
"06-Day5.pdf"
"07-Day6.pdf"
"08-2주차.pdf"
)
TITLES=(
"시작 — 교육 안내 + 절대규칙 5 + 용어집"
"Day 1 — 첫날, 매장과 친해지기"
"Day 2 — 오픈 따라하기"
"Day 3 — 커피 머신·그라인더 기본"
"Day 4 — 음료 제조 + 손님 응대"
"Day 5 — 재고·유통기한·청소"
"Day 6 — 마감 따라하기"
"2주차 — 혼자 해보기 + 보고 (졸업 체크)"
)

idx=0
[ -f "$STATE" ] && idx=$(cat "$STATE")
total=${#FILES[@]}

echo "[$(date)] run, idx=$idx/$total" >> "$LOG"

if [ "$idx" -ge "$total" ]; then
  echo "[$(date)] 모든 교육 발송 완료 ($total/$total) — 더 보내지 않음." >> "$LOG"
  exit 0
fi

n=$((idx+1))
file="$DIR/${FILES[$idx]}"
title="${TITLES[$idx]}"
caption="🧺 Basket 신입 교육 ${n}/${total} — ${title}
오늘은 이거 하나만! 천천히 따라 해보세요 🙌"

if [ ! -f "$file" ]; then
  echo "[$(date)] ERROR 파일 없음: $file" >> "$LOG"
  exit 1
fi

for r in "${RECIPIENTS[@]}"; do
  if "$TGCLI" send file --to "$r" --file "$file" --caption "$caption" >> "$LOG" 2>&1; then
    echo "[$(date)] sent ${FILES[$idx]} -> $r" >> "$LOG"
  else
    echo "[$(date)] FAIL ${FILES[$idx]} -> $r (로그 확인 후 수동 재발송)" >> "$LOG"
  fi
done

# 일부 수신자 실패해도 다음날 중복 발송을 막기 위해 진도는 넘긴다.
# 실패분은 send.log를 보고 수동 재발송한다 (수신자 3명, 소규모).
echo "$n" > "$STATE"
echo "[$(date)] idx -> $n" >> "$LOG"
