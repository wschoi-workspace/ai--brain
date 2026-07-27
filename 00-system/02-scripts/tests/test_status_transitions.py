#!/usr/bin/env python3
"""상태 전이 게이트 단위 테스트 (WS2, 2026-07-27).

실행: python3 00-system/02-scripts/tests/test_status_transitions.py
의존성 없음(표준 라이브러리만) — 맥미니 3.9.6에서 그대로 돌아간다.

가장 중요한 것은 §3 승인 흐름 회귀다. 전이 게이트가 PM 클리어 7선택지나 리더 검토를
막으면 승인 흐름 전체가 죽는다 — 그 경우를 테스트로 못 박는다.
"""
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import shared.approval as AP        # noqa: E402
import shared.status as ST          # noqa: E402

FAIL = []
N = 0


def ck(cond, label):
    global N
    N += 1
    if not cond:
        FAIL.append(label)
        print(f"  ✗ {label}")
    else:
        print(f"  ✓ {label}")


def allowed(frm, to, source="dashboard", admin=False):
    return ST.can_transition(frm, to, source, admin)[0]


# 환경변수가 켜져 있으면 mode 테스트가 오염된다 — 테스트 시작 시 제거
os.environ.pop(ST.ENV_MODE_KEY, None)

print("§1 전이 허용·차단 12케이스")
ck(allowed("검토중", "진행중"), "① 검토중→진행중 (사람 반려) 허용")
ck(not allowed("검토중", "진행중", "weekly-auto"), "② 검토중→진행중 (weekly-auto) 차단")
ck(allowed("승인대기", "진행중"), "③a 승인대기→진행중 (사람 수정필요) 허용")
ck(not allowed("승인대기", "진행중", "weekly-auto"), "③b 승인대기→진행중 (auto) 차단")
ck(allowed("미착수", "완료", "daily-brief-auto"), "④ 미착수→완료 (auto 보고 완료) 허용")
ck(not allowed("보류", "진행중", "weekly-auto"), "⑤ 보류→진행중 (auto) 차단 — 대표 보류 보호")
ck(all(allowed(s, "삭제", "weekly-auto") for s in ST.ASSIGN_STATES if s != "삭제"),
   "⑥ 모든 from→삭제 허용 (일괄삭제·프로젝트 삭제 보호)")
ck(not allowed("승인", "진행중") and allowed("승인", "진행중", admin=True),
   "⑦ 승인→진행중 대표만 (ADMIN_ONLY)")
ck(allowed("완료", "완료", "weekly-auto"), "⑧ 동일 상태 no-op 통과")
ck(allowed("", "진행중", "weekly-auto"), "⑨ from 빈값 fail-open")
ck(allowed("N/A", "완료", "weekly-auto") and allowed("진행중", "알수없음", "weekly-auto"),
   "⑩ 어휘 밖 from/to fail-open")
ck(allowed("패스", "진행중") and not allowed("패스", "진행중", "weekly-auto"),
   "⑪ 종료(패스)→진행중 되살리기는 사람만")
ok, why = ST.check_transition("승인대기", "진행중", "weekly-auto", today=date(2026, 8, 1))
ck(ok and why, "⑫ shadow: 위반이어도 ok=True + 사유 채움")

print("\n§2 모드 전환")
ok_e, why_e = ST.check_transition("승인대기", "진행중", "weekly-auto", today=date(2026, 8, 17))
ck(not ok_e and why_e, "enforce 당일(08-17)부터 차단")
ck(ST.transition_mode(date(2026, 8, 16)) == "shadow", "08-16은 shadow")
ck(ST.transition_mode(date(2026, 8, 17)) == "enforce", "08-17은 enforce")
os.environ[ST.ENV_MODE_KEY] = "off"
ck(ST.check_transition("승인대기", "진행중", "weekly-auto", today=date(2026, 12, 1))[0],
   "env=off 킬스위치 — 날짜 무관 통과")
os.environ[ST.ENV_MODE_KEY] = "enforce"
ck(not ST.check_transition("보류", "진행중", "weekly-auto", today=date(2026, 7, 1))[0],
   "env=enforce — 날짜보다 우선")
os.environ.pop(ST.ENV_MODE_KEY, None)
ck(ST.transition_note("보류 → 진행중 불가", "shadow").startswith("[transition-shadow]"),
   "note 태그 고정 (집계 grep 대상)")

print("\n§3 승인 흐름 회귀 — 게이트에 걸리면 승인 체인이 죽는다")
# PM 클리어는 승인대기에서, PM이 리더 겸직·리더 공석이면 완료에서도 출발한다
for choice, eff in AP.PM_CLEAR_EFFECTS.items():
    to = eff["to"]
    if not to:
        continue   # 상태 유지 건 — 시트를 쓰지 않으므로 게이트 무관
    for frm in ("승인대기", "완료"):
        ck(allowed(frm, to), f"PM클리어 '{choice}': {frm}→{to}")
# 리더 검토 (/api/assign-review) — from은 담당자 완료 보고 상태
ck(allowed("완료", "진행중"), "검토 반려: 완료→진행중")
ck(allowed("완료", "승인대기"), "검토 통과(PM 있음): 완료→승인대기")
ck(allowed("완료", "승인"), "검토 통과(PM 부재 전결): 완료→승인")
# 봇 ✓완료 (report-sync) — 사람 취급이어야 한다
ck(ST.source_class("report-sync") == "human", "report-sync는 human 분류")
ck(allowed("검토중", "완료", "report-sync"), "봇 ✓완료: 검토중→완료 (사람 취급)")
# 종료 5종 — 어느 열린 상태에서든 사유와 함께 닫을 수 있어야 한다
for frm in ST.ASSIGN_OPEN_STATES:
    ck(all(allowed(frm, t) for t in ST.ASSIGN_TERMINAL_STATES),
       f"종료 5종 진입: {frm}→terminal")

print("\n§4 테이블 정합")
ck(set(ST.TRANSITIONS) == set(ST.ASSIGN_STATES),
   "TRANSITIONS가 ASSIGN_STATES 전체를 덮는다 (빠지면 '나갈 수 없는 상태')")
ck(all(t in ST.ASSIGN_STATES for tos in ST.TRANSITIONS.values() for t in tos),
   "TRANSITIONS의 to가 모두 어휘 내")
ck(all(t in ST.TRANSITIONS.get(f, ()) for f, tos in ST.AUTO_TRANSITIONS.items() for t in tos),
   "AUTO_TRANSITIONS ⊆ TRANSITIONS (자동이 사람보다 넓으면 안 된다)")
ck(all(f in ST.ASSIGN_STATES and t in ST.ASSIGN_STATES for f, t in ST.ADMIN_ONLY),
   "ADMIN_ONLY 쌍이 어휘 내")
ck(all(t not in ST.TRANSITIONS.get(f, ()) for f, t in ST.ADMIN_ONLY),
   "ADMIN_ONLY는 일반 테이블에 없다 (없어야 admin 분기가 의미를 갖는다)")

print("\n§5 프로젝트 신호등 (WS3a)")
_T = date(2026, 7, 27)


def _a(dl, st="진행중"):
    return {"deadline": dl, "status": st}


for label, proj, ass, want in [
    ("열린 분장 없음 → 판정 보류", {}, [], "gray"),
    ("완료만 있음 → 판정 보류", {}, [_a("2026-07-01", "완료")], "gray"),
    ("지연 없음", {}, [_a("2026-08-10")], "green"),
    ("지연 1건", {}, [_a("2026-07-20")], "amber"),
    (f"지연 {ST.SIGNAL_RED_OVERDUE}건", {}, [_a("2026-07-20")] * 3, "red"),
    (f"최장 {ST.SIGNAL_RED_DAYS}일 경과", {}, [_a("2026-07-13")], "red"),
    ("미해결 이슈 5건 — 지연 없어도 초록 아님",
     {"issues": [{"issue": "x", "status": "열림"}] * 5}, [_a("2026-08-10")], "amber"),
]:
    ck(ST.project_signal(proj, ass, _T)["grade"] == want, label)

ck(ST.project_signal({}, [], _T)["score"] is None, "판정 보류는 score None (추세 계산 제외)")
ck(ST.project_signal({}, [_a("2026-08-10")], _T)["score"] == 100, "전건 정시 → score 100")
ck(set(ST.HEALTH_WEIGHTS) == {"timeline", "budget", "scope", "quality", "risk"},
   "senior-pm 5차원 프레임은 정의로 보존(확장 슬롯)")
ck("종료일 미기재" in ST.signal_missing({"tasks": [1], "brief": {"budget": 1, "actual": 1}}),
   "결측 축은 회색 라벨로 노출 — 비어 있음을 숨기지 않는다")

print(f"\n{'─' * 52}")
if FAIL:
    print(f"실패 {len(FAIL)}/{N}")
    for f in FAIL:
        print(f"  · {f}")
    sys.exit(1)
print(f"전체 통과 {N}/{N}")
