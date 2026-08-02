#!/usr/bin/env python3
"""완료 근거 감사 — 읽기 전용 (vNext Phase 1, 2026-08).

completion.GRACE_END를 strict로 넘기기 전에 "지금 강제하면 몇 건이 막히는가"를 실측한다.
날짜를 먼저 정하고 나중에 실측하는 순서를 뒤집는 것이 이 스크립트의 존재 이유다 —
숫자를 대표에게 보고한 뒤에 GRACE_END를 확정한다.

함께 확인하는 것:
  · P~W 컬럼이 시트에 실제로 존재하는가 (없어도 코드는 안전하지만 입력이 시작됐는지 알아야 한다)
  · 진행률 실입력이 얼마나 쌓였는가 (0이면 아직 UI/봇이 안 붙은 것)
  · 완료·승인인데 산출물이 어디에도 없는 행 = strict에서 차단될 건

실행: python3 00-system/02-scripts/migration/audit-completion.py
      python3 ... --list          차단될 행을 전부 나열
      python3 ... --sheet <ID>    시트 ID 직접 지정

아무것도 쓰지 않는다. 시트·JSON 전부 불변.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
WORKSPACE = SCRIPTS.parent.parent
sys.path.insert(0, str(SCRIPTS))

ENV_PATHS = [WORKSPACE / ".env", Path.home() / "arisa-project-memory" / ".env"]


def load_env():
    for p in ENV_PATHS:
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


load_env()

import shared.assign_sheet as AS    # noqa: E402
import shared.completion as CP      # noqa: E402
import shared.status as ST          # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="차단될 행을 전부 나열")
    ap.add_argument("--sheet", default="", help="시트 ID 직접 지정")
    args = ap.parse_args()

    sheet_id = args.sheet or os.environ.get("DAILY_REPORT_SHEET_ID", "")
    print("=" * 64)
    print("완료 근거 감사 — 읽기 전용 (아무것도 쓰지 않는다)")
    print("=" * 64)
    print("현재 모드   : %s   (GRACE_END %s)" % (CP.current_mode(), CP.GRACE_END))
    print("strict 차단 : %s" % "·".join(dict(CP.FIELDS)[k] for k in CP.REQUIRED_IN_STRICT))

    if not sheet_id:
        print("\n⚠️ DAILY_REPORT_SHEET_ID 미설정 — 시트 감사를 건너뛴다")
        return 0
    try:
        from shared import gws
        rows = gws.values_get(sheet_id, AS.READ_RANGE, retries=2, timeout=30)
    except Exception as e:
        print("\n⚠️ 시트 읽기 실패: %s" % str(e)[:70])
        return 1
    if not rows:
        print("\n⚠️ 빈 응답 — gws 인증 장애 의심(재인증 후 재실행)")
        return 1

    assigns = AS.parse_all(rows, ST)
    live = [a for a in assigns if a.get("status") not in ST.ASSIGN_DROPPED_STATES]
    done = [a for a in live if a.get("status") in ST.ASSIGN_DONE_STATES]
    open_ = [a for a in live if a.get("status") in ST.ASSIGN_OPEN_STATES]

    print("\n① 규모")
    print("   전체 %d행 · 유효 %d · 완료·승인 %d · 열린 분장 %d"
          % (len(assigns), len(live), len(done), len(open_)))

    # ── P~W 실사용 여부 ────────────────────────────────────────────
    widest = max((len(r) for r in rows), default=0)
    filled = Counter()
    for a in live:
        for key in ("progress", "eta", "progress_at", "done_at", "done_by",
                    "deliverable", "report_to", "reported_at"):
            if (a.get(key) or "").strip():
                filled[key] += 1
    print("\n② P~W 확장 컬럼 실사용")
    print("   시트 최대 폭 %d칸 (%s)" % (
        widest, "P~W 입력 시작됨" if widest > 15 else "아직 15칸 — 입력 전"))
    for key, label in (("progress", "P 진행률"), ("eta", "Q ETA"),
                       ("progress_at", "R 갱신시각"), ("done_at", "S 완료일"),
                       ("done_by", "T 완료자"), ("deliverable", "U 산출물링크"),
                       ("report_to", "V 보고대상"), ("reported_at", "W 보고완료")):
        print("     %-14s %4d건" % (label, filled[key]))

    # ── 진행률 분포 ────────────────────────────────────────────────
    real = [a for a in open_ if ST.norm_progress(a.get("progress")) is not None]
    print("\n③ 진행률 — 열린 분장 %d건 중 실입력 %d건 (%.0f%%)"
          % (len(open_), len(real), (100.0 * len(real) / len(open_)) if open_ else 0))
    if not real:
        print("   실입력 0 — 전부 상태 파생 사다리로 표시되는 중(종전과 동일).")
    band = Counter(ST.progress_band(ST.effective_progress(a)) for a in open_)
    for label in ("Not Started", "Planning", "In Progress", "Review", "Done"):
        if band.get(label):
            print("     %-12s %4d건" % (label, band[label]))

    # ── strict 시뮬레이션 ──────────────────────────────────────────
    blocked = [a for a in done if CP.missing_required(a)]
    print("\n④ strict 시뮬레이션 — 지금 강제하면?")
    print("   완료·승인 %d건 중" % len(done))
    print("     통과 %d건 · **차단 %d건**" % (len(done) - len(blocked), len(blocked)))
    if done:
        print("     → 차단율 %.0f%%" % (100.0 * len(blocked) / len(done)))

    gap = Counter()
    for a in done:
        for label in CP.missing(a):
            gap[label] += 1
    print("\n⑤ 완료 5요소별 결손 (완료·승인 %d건 기준)" % len(done))
    for key, label in CP.FIELDS:
        n = gap.get(label, 0)
        mark = " ←strict 차단" if key in CP.REQUIRED_IN_STRICT else ""
        print("     %-12s %4d건 결손%s" % (label, n, mark))

    if blocked:
        print("\n⑥ 차단될 행")
        show = blocked if args.list else blocked[:15]
        for a in show:
            print("     행%-5s %-6s %-10s %s"
                  % (a.get("row"), a.get("status"), a.get("assignee") or "?",
                     (a.get("task") or "")[:34]))
        if not args.list and len(blocked) > 15:
            print("     … 외 %d건 (--list 로 전체 확인)" % (len(blocked) - 15))
        print("\n   ⚠️ 자동 채우기를 하지 마라 — 산출물은 사람이 남긴 사실이다.")
        print("      grace 동안 신규 완료분이 자동 충전되며 이 숫자는 자연히 줄어든다.")

    print("\n" + "=" * 64)
    print("판단 기준: 차단율이 충분히 낮아진 뒤 GRACE_END를 확정한다.")
    print("현재 설정값 %s — 이 숫자를 보고 대표가 조정한다." % CP.GRACE_END)
    return 0


if __name__ == "__main__":
    sys.exit(main())
