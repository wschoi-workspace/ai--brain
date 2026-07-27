#!/usr/bin/env python3
"""분장 상태값 감사 — 읽기 전용 (WS2, 2026-07-27).

전이 게이트를 enforce로 넘기기 전에 "지금 시트에 무엇이 들어 있는가"를 확인한다.
norm_assign_status는 화이트리스트 검증을 하지 않으므로(빈값→미착수, 그 외 원문 통과)
어휘 밖 값이 시트에 남아 있을 수 있다 — fail-open 설계의 근거를 실측으로 확인하는 것이 목적.

실행: python3 00-system/02-scripts/migration/audit-assign-status.py
      (시트 접근 없이 이력만 보려면 --no-sheet)

아무것도 쓰지 않는다. 시트·이력·프로젝트 JSON 전부 불변.
자동 일괄 변환은 하지 않는다 — 상태는 사람의 판단 기록이므로 이상값이 나오면 개별 판단한다.
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

import shared.status as ST          # noqa: E402
import shared.status_log as SL      # noqa: E402

DAILY_SHEET = os.environ.get("DAILY_REPORT_SHEET_ID", "")


def audit_sheet():
    """H열 원문 분포 + 어휘 밖 값의 행 번호."""
    print("\n① 주간분장 H열 상태값 분포")
    if not DAILY_SHEET:
        print("   ⚠️ DAILY_REPORT_SHEET_ID 미설정 — 건너뜀")
        return
    try:
        from shared import gws
        rows = gws.values_get(DAILY_SHEET, "주간분장!A2:O5000", retries=2, timeout=30)
    except Exception as e:
        print(f"   ⚠️ 시트 읽기 실패: {str(e)[:70]}")
        return
    if not rows:
        print("   ⚠️ 빈 응답 — gws 인증 장애 의심(재인증 후 재실행)")
        return

    cnt = Counter()
    unknown = []          # (행번호, 원문, 담당자, 업무)
    blank = 0
    for i, r in enumerate(rows):
        r = list(r) + [""] * (15 - len(r))
        raw = (r[7] or "").strip()
        if not raw:
            blank += 1
            continue
        cnt[raw] += 1
        if raw not in ST.ASSIGN_STATES:
            unknown.append((i + 2, raw, (r[3] or "").strip(), (r[4] or "").strip()[:28]))

    print(f"   전체 {len(rows)}행 · 공란 {blank}행(= 미착수로 해석)")
    for st, n in cnt.most_common():
        mark = "  " if st in ST.ASSIGN_STATES else " ⚠️"
        print(f"   {mark} {st:<12} {n:>4}건")

    print(f"\n② 어휘 밖 상태값: {len(unknown)}건")
    if not unknown:
        print("   ✅ 없음 — 마이그레이션 불필요 확정")
    else:
        print("   ⚠️ fail-open으로 통과되지만 게이트가 판정하지 못하는 행이다.")
        print("   자동 변환하지 말고 아래 행을 개별 확인할 것:")
        for row, raw, who, task in unknown[:40]:
            print(f"     H{row:<5} '{raw}'  {who} — {task}")
        if len(unknown) > 40:
            print(f"     … 외 {len(unknown) - 40}건")


def audit_log_replay():
    """status_log 전 엔트리를 새 전이 테이블로 리플레이 → 위반 유형별 집계."""
    print("\n③ status_log 리플레이 (과거 전이를 새 테이블로 재판정)")
    rows = SL.load_history(limit=100000)
    if not rows:
        print("   이력 0건 — 리플레이 대상 없음")
        print("   (assign-status.jsonl이 비어 있으면 3주 정체 감지·품질 차원은 아직 착수 불가)")
        return

    total = 0
    viol = Counter()
    by_source = Counter()
    skipped = 0
    for e in rows:
        frm, to = (e.get("from") or "").strip(), (e.get("to") or "").strip()
        src = (e.get("source") or "").strip()
        if not to or to == "병합":
            skipped += 1       # 로그 전용 의사 상태 — 시트를 쓰지 않는다
            continue
        total += 1
        ok, why = ST.can_transition(frm, to, src)
        if not ok:
            viol[f"{frm} → {to} ({src})"] += 1
            by_source[src] += 1

    print(f"   판정 대상 {total}건 (의사 상태 제외 {skipped}건)")
    if not viol:
        print("   ✅ 위반 0건 — 과거 이력은 새 테이블과 모순되지 않는다")
        return
    print(f"   ⚠️ 위반 {sum(viol.values())}건")
    for k, n in viol.most_common(20):
        print(f"     {n:>4}건  {k}")
    print("\n   소스별:")
    for s, n in by_source.most_common():
        cls = ST.source_class(s)
        print(f"     {n:>4}건  {s} ({cls})")


def main():
    ap = argparse.ArgumentParser(description="분장 상태값 감사 (읽기 전용)")
    ap.add_argument("--no-sheet", action="store_true", help="시트 접근 없이 이력만 감사")
    args = ap.parse_args()

    print("=" * 60)
    print("분장 상태값 감사 — 읽기 전용 (아무것도 쓰지 않음)")
    print(f"전이 모드: {ST.transition_mode()} · enforce 예정 {ST.ENFORCE_FROM}")
    print("=" * 60)

    if not args.no_sheet:
        audit_sheet()
    audit_log_replay()

    print("\n④ '이번 주라면 몇 건이 차단됐을까'")
    print("   weekly의 드라이런을 쓴다(같은 매칭 로직을 두 번 구현하지 않는다):")
    print("   $ python3 00-system/02-scripts/weekly-report-aggregate.py \\")
    print("       --week last --no-telegram --dry-run")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
