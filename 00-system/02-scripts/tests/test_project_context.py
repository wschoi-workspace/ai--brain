#!/usr/bin/env python3
"""Context Delta 투영·적용 단위 테스트 (vNext P2 WS6).

실행: python3 00-system/02-scripts/tests/test_project_context.py
의존성 없음 — 맥미니 3.9.6에서 그대로 돌아간다.

가장 중요한 것은 §3 멱등이다. arisa2는 같은 회의록을 두 번 파싱해 delta 2건을
만들었다(delta_001/002, source 경로 문자열만 다름). 같은 사고가 재발하지 않음을
ref·전사지문 2중 가드로 못 박는다.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import shared.meeting_delta as MD   # noqa: E402
import shared.project_context as PC  # noqa: E402

FAIL = []
N = 0


def ck(cond, label):
    global N
    N += 1
    if not cond:
        FAIL.append(label)
        print("  ✗ %s" % label)
    else:
        print("  ✓ %s" % label)


R4_RESULT = {
    "r4SessionId": "20260730-171537-2f28",
    "meta": {"title": "아랑재 실무회의", "date": "2026-07-30"},
    "minutes": {
        "F_changes": [
            {"scope": "SCHEDULE", "what": "오픈일", "before": "9/15", "after": "9/22",
             "why": "시공 일정 변경", "impact": ["마케팅 일정", "제작 일정"]},
            {"scope": "REQUIREMENT", "what": "메뉴", "before": "없음",
             "after": "딸기요거트라떼 추가", "why": "제조 단순화"},
            {"scope": "이상한값", "what": "x", "before": "a", "after": "b"},
        ],
        "H_risks": [{"risk": "공사 지연 가능성", "severity": "HIGH", "response": "버퍼 1주"}],
        "G_open_issues": [{"issue": "예산 승인", "needed_decision": "3천 확정",
                           "decider": "대표", "deadline": "2026-08-05"}],
    },
    "decisions": [{"id": "D1", "title": "테이크아웃 중심 운영", "status": "CONFIRMED",
                   "rationale": "초기 인력 최소화", "decidedBy": ["대표"]}],
    "actions": [{"id": "A1"}, {"id": "A2"}],
    "outputs": [{"id": "O1"}],
    "routing": {"ceo": [{"item": "예산 3,000만원 확정", "why": "계약 선행", "refs": ["D1"]}],
                "lead": [], "member": []},
}

print("§1 project_delta — 결정론 투영")
d = MD.project_delta(R4_RESULT, "arangje-2026", "20260809-100000", created_at="2026-08-09T10:00:00")
ck(d["ref"] == "arangje-2026|20260809-100000", "① ref = provenance 규격(pid|ts)")
ck(len(d["changes"]) == 3 and d["changes"][0]["why"] == "시공 일정 변경",
   "② F_changes의 scope·why가 살아서 넘어온다")
ck(d["changes"][2]["scope"] == "SCOPE", "③ enum 밖 scope는 SCOPE로 정규화(fail-open)")
ck(d["actionCount"] == 2 and d["outputCount"] == 1,
   "④ 액션·산출물은 개수만 — 문서함이 SSOT(복제 저장 금지)")
d2 = MD.project_delta(R4_RESULT, "arangje-2026", "20260809-100000", created_at="2026-08-09T10:00:00")
ck(d == d2, "⑤ 같은 입력 → 같은 delta (LLM 미사용 재현성)")
ck(MD.transcript_hash("안녕  하세요\n") == MD.transcript_hash("안녕하세요"),
   "⑥ 전사 지문은 공백·개행 무시")

print("\n§2 apply_delta — 상태 누적")
d["transcriptHash"] = MD.transcript_hash("전사 원문입니다")
ctx, log = PC.apply_delta(PC.new_context("arangje-2026"), d, now="2026-08-09T10:01:00")
ck(any("요구사항 추가" in x for x in log), "① before='없음' → 요구사항 추가(추가도 변경이다)")
ck(ctx["requirements"][0]["since"] == d["ref"],
   "② 모든 항목이 since(meeting_ref)를 갖는다 — arisa2 문자열 뭉갬의 반대")
ck(ctx["risks"][0]["severity"] == "HIGH" and ctx["decisions"][0]["title"] == "테이크아웃 중심 운영",
   "③ 리스크·결정 구조 유지")
ck(ctx["decisionNeeded"][0]["content"] == "예산 3,000만원 확정",
   "④ routing.ceo → 대표 판단 필요(하드코딩 아닌 LLM 판정 유입)")
ck(ctx["timeline"][0]["changeCount"] == 3, "⑤ timeline 연대기 축적")

print("\n§3 멱등 — arisa2 delta 중복 사고의 재발 방지  ★ 가장 중요")
ctx2, log2 = PC.apply_delta(ctx, d, now="2026-08-09T11:00:00")
ck(log2[0].startswith("skip"), "① 같은 ref 재적용 → skip")
ck(ctx2 == ctx, "② 상태 불변")
d_other = dict(d, ref="arangje-2026|20260809-999999", r4SessionId="다른세션")
ctx3, log3 = PC.apply_delta(ctx, d_other, now="")
ck(log3[0].startswith("skip"),
   "③ 다른 세션 ID라도 전사 지문이 같으면 차단 — arisa2가 못 막은 정확히 그 경우")

print("\n§4 요구사항 개정 — before/after 페어링 유지")
d_rev = {"ref": "arangje-2026|20260810-090000", "transcriptHash": "sha1:rev",
         "changes": [{"scope": "REQUIREMENT", "what": "메뉴",
                      "before": "딸기요거트라떼 추가", "after": "딸기요거트라떼 + 아인슈페너",
                      "why": "메뉴 확장"}],
         "decisions": [], "risks": [], "openIssues": [], "routing": {}}
ctx4, log4 = PC.apply_delta(ctx, d_rev, now="")
req = ctx4["requirements"][0]
ck(req["text"] == "딸기요거트라떼 + 아인슈페너" and any("개정" in x for x in log4),
   "① 기존 요구사항이 개정된다(추가가 아니라)")
ck(d_rev["ref"] in req["changedBy"] and req["since"] == d["ref"],
   "② since(원출처)는 보존, changedBy에 개정 회의가 쌓인다 — 변경 연대기")

print("\n§5 revert_ref — 무승인 자동 적용의 정당화")
ctx5 = PC.revert_ref(ctx4, d_rev["ref"])
ck(d_rev["ref"] not in (ctx5["requirements"][0].get("changedBy") or []),
   "① 개정 표식 제거")
ck(d_rev["ref"] not in ctx5["appliedRefs"], "② appliedRefs에서 제거 → 재적용 가능")
ctx6 = PC.revert_ref(ctx4, d["ref"])
ck(not any(r.get("since") == d["ref"] for r in ctx6["requirements"]),
   "③ since==ref 항목은 통째로 제거")

print("\n§6 빈 입력 안전")
ctx7, log7 = PC.apply_delta(PC.new_context("x"),
                            {"ref": "x|1", "changes": [], "decisions": [], "risks": [],
                             "openIssues": [], "routing": {}}, now="")
ck("변경 없음" in log7[0] and ctx7["appliedRefs"] == ["x|1"],
   "① 빈 delta도 적용 기록은 남는다(재적용 방지)")
ck(MD.project_delta({}, "p", "t")["changes"] == [], "② 빈 result도 죽지 않는다")

print("\n" + "=" * 60)
if FAIL:
    print("실패 %d / %d" % (len(FAIL), N))
    sys.exit(1)
print("전체 통과 %d / %d" % (N, N))
