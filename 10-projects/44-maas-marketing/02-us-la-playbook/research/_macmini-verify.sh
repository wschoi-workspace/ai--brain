#!/usr/bin/env zsh
# ─────────────────────────────────────────────────────────────
# 맥미니 무인 최종검증(B) — 승인 없이 끝까지 자동
# 전용 worktree에서 격리 실행(arisa 크론의 브랜치 전환 충돌 회피)
# 맥미니 터미널에 그대로 붙여넣기 (인증은 이미 완료됨)
# ─────────────────────────────────────────────────────────────
set -e
command -v claude >/dev/null 2>&1 || npm i -g @anthropic-ai/claude-code

# [1] 최신 feat 브랜치를 전용 worktree로 격리 체크아웃
cd ~/do-better-workspace
git fetch origin feat/34-us-marketing
WT="$HOME/rent34-wt"
git worktree remove "$WT" --force 2>/dev/null || true
git worktree add -B feat/34-us-marketing "$WT" origin/feat/34-us-marketing

# [2] 검증 지시서를 worktree 안에 기록
DIR="$WT/10-projects/34-rent-us-marketing-playbook"
cat > "$DIR/research/verify-brief.md" <<'BRIEF'
# 최종 3중검증 재대조 브리프 (B) — 맥미니 무인

너는 프로젝트렌트 US 플레이북의 숫자 자료를 **최종 검증**한다. 승인 없이 끝까지 실행하라.
대상 파일(이 worktree 기준 상대경로):
- `10-projects/34-rent-us-marketing-playbook/research/tool-la-alternatives.md` (센터피스, 47KB)
- `10-projects/34-rent-us-marketing-playbook/us-marketing-playbook.md` (섹션 4~7)

## 원칙 (CLAUDE.md 숫자 3중검증)
1. **추출**: 두 파일의 모든 USD/₩ 수치·단위·고유명사·규정명·경쟁사 사실주장을 빠짐없이 뽑는다.
2. **크로스체크**: 각 주장을 **인용된 출처 URL을 WebFetch로 직접 열어** 대조한다(죽은 링크·
   해당 수치 부재 시 WebSearch로 재삼각검증). 다섯 축을 모두 본다:
   ⓐ수치 ⓑ단위(월/건/CPM/CPC/CPP) ⓒ귀속(누구 단가·누구 연구) ⓓ맥락(무엇에 대한 값) ⓔ출처표기.
3. **반영 후 재대조**: 오류는 파일에서 **직접 수정**하고, 수정본이 출처와 일치하는지 다시 본다.

## 우선순위 (load-bearing 먼저, 그다음 전수)
- 하중 큰 수치 먼저: FTC 가짜리뷰 벌금액(건당 $51,744 / 2025 조정액), Leap 사실
  (RaaS·2025 흑자전환·LA 100+매장), 시장규모(섹션4.1), 헤드라인 가격갭(파워페이지 3~7배·
  체험단 5~20배), PR와이어 단가(PR Newswire/Business Wire/PRWeb/EIN), 인플루언서 티어 요율.
- 그다음 A~H 표의 나머지 셀 전수. 병렬 검증 에이전트를 카테고리별로 나눠 돌려라.

## 판정·수정 규칙
- 출처가 뒷받침 → 유지(그대로).
- 출처와 불일치 → **수정** + 셀 끝에 `〔수정: 기존 X→Y, 근거 URL〕`.
- 출처에 없음/확인불가 → 과신 표현을 `[추정]` 또는 `[확인필요]`로 강등(지어내지 말 것).
- 비공개가는 RFQ 유지. 단위·귀속 오류(%↔%p, 월↔건, 공저자↔주저자)를 특히 조심.

## 산출
1. 대상 파일 2종을 **직접 수정**(인라인 반영).
2. `research/verification-report.md` 신규 작성 — 표: `항목 | 파일위치 | 기존값 | 출처확인 | 판정(OK/수정/플래그) | 근거URL`.
   맨 위에 요약(검증 N건 / 수정 M건 / 플래그 K건 / 신뢰도 총평).
3. `34-progress.md`에 "2026-07-06 최종검증(B) 완료" 로그·체크박스 갱신.

## 마무리
- `git add -A && git commit -m "verify(34): USD/규정 수치 3중검증 재대조 + verification-report"`
- `git push origin HEAD:feat/34-us-marketing` (실패 시 커밋만 남기고 progress에 기록)
- HTML 덱·PNG는 만들지 말 것.
BRIEF

# [3] 무인 검증 실행 — screen(SSH 끊겨도 유지) + 승인 스킵
BRIEFF="$DIR/research/verify-brief.md"
VLOG="$DIR/research/_verify.log"
screen -dmS rent34v zsh -lc "cd $WT && claude --dangerously-skip-permissions -p \"$(cat $BRIEFF)\" > $VLOG 2>&1"

echo "✅ 최종검증 시작됨 (worktree: $WT / screen: rent34v)"
echo "   로그:   tail -f $VLOG"
echo "   세션:   screen -r rent34v   (빠져나오기: Ctrl+A, D)"
