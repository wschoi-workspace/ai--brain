#!/usr/bin/env python3
"""회의 액션 ↔ 분장 연결 테스트 (WS1, 2026-07-27).

실행: python3 00-system/02-scripts/tests/test_meeting_link.py

가장 중요한 것은 §3 레거시 회귀다. 출처ID를 3세그먼트로 확장했으므로, 기존 2세그먼트
참조가 그대로 해석되지 않으면 회의 실행률 롤업에서 과거 액션이 조용히 빠진다.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import shared.meeting_link as ML   # noqa: E402
import shared.provenance as PV     # noqa: E402

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


# ── 픽스처 ───────────────────────────────────────────────────────────
ENGINE_A = {"block_5_todos": {"ours": [
    {"assignee": "김OO", "task": "도면 확정", "due": "2026-08-01",
     "depends_on": [], "blocked_by": ""},
    {"assignee": "이OO", "task": "견적 3사 취합", "due": "8/5",
     "depends_on": ["도면 확정"], "blocked_by": "클라이언트 예산 승인"},
], "theirs": [{"assignee": "클라이언트", "task": "예산 승인"}]}}

ENGINE_B = {"actions": [
    {"id": "A1", "title": "도면 확정", "suggestedOwner": "김OO",
     "deadline": "2026-08-01", "dependencies": []},
    {"id": "A2", "title": "견적 3사 취합", "suggestedOwner": "이OO",
     "deadline": "2026-08-05", "dependencies": ["A1"]},
    {"id": "A3", "title": "계약서 초안", "suggestedOwner": "",
     "deadline": "", "dependencies": ["A2", "A9"]},   # A9 = 존재하지 않는 참조
], "supportRequests": [
    {"id": "S1", "actionId": "A2", "stakeholderName": "클라이언트",
     "blockingLevel": "BLOCKING", "blockedWithout": "예산 승인"},
    {"id": "S2", "actionId": "A7", "stakeholderName": "유령",   # 존재하지 않는 액션
     "blockingLevel": "BLOCKING", "blockedWithout": "무시돼야 함"},
    {"id": "S3", "actionId": "A3", "stakeholderName": "법무",
     "blockingLevel": "REFERENCE", "blockedWithout": "표준 계약서 양식"},
]}

print("§1 엔진 A (대시보드 내장 · block_5_todos)")
ia = ML.action_index(ENGINE_A)
ck(set(ia) == {"A1", "A2"}, "ours 2건 → A1·A2 (theirs 제외)")
ck(ia["A1"]["depends_on"] == [] and not ia["A1"]["blocking"], "A1 선행·차단 없음")
ck(ia["A2"]["depends_on"] == ["도면 확정"], "A2 선행 = 업무명 문구")
ck(ML.has_blocking(ia["A2"]), "A2 blocked_by → BLOCKING 등급")
ck("클라이언트 예산 승인" in ia["A2"]["blocking"][0]["without"], "차단 조건 본문 보존")

print("\n§2 엔진 B (R4 Meeting OS · actions + supportRequests)")
ib = ML.action_index(ENGINE_B)
ck(set(ib) == {"A1", "A2", "A3"}, "actions 3건 인덱싱")
ck(ib["A2"]["depends_on"] == ["도면 확정"], "dependencies 액션ID → 제목 변환")
ck(ib["A3"]["depends_on"] == ["견적 3사 취합", "A9"],
   "존재하지 않는 참조(A9)는 원문 유지 — 예외 없이 통과")
ck(ML.has_blocking(ib["A2"]) and ib["A2"]["blocking"][0]["who"] == "클라이언트",
   "supportRequests가 actionId로 조인")
ck(not any(b["who"] == "유령" for v in ib.values() for b in v["blocking"]),
   "존재하지 않는 액션(A7) 참조는 무시")
ck(not ML.has_blocking(ib["A3"]), "REFERENCE 등급은 BLOCKING이 아니다")
ck(ib["A3"]["blocking"] and ib["A3"]["blocking"][0]["level"] == "REFERENCE",
   "REFERENCE도 정보로는 보존")

print("\n§3 출처ID 왕복 — 레거시 회귀 (가장 중요)")
ck(PV.meeting_ref("p1", "20260727-101500") == "p1|20260727-101500", "2세그먼트 생성")
ck(PV.meeting_ref("p1", "20260727-101500", "A2") == "p1|20260727-101500|A2", "3세그먼트 생성")
ck(PV.meeting_ref("p1", "20260727-101500", "지연됨") == "p1|20260727-101500",
   "자유 텍스트 액션ID는 거부 — 형식 밖은 붙이지 않는다")
ck(PV.parse_meeting_ref3("p1|20260727-101500") == ("p1", "20260727-101500", ""),
   "레거시 2세그먼트 파싱 → action_id 빈값")
ck(PV.parse_meeting_ref3("p1|20260727-101500|A2") == ("p1", "20260727-101500", "A2"),
   "3세그먼트 파싱")
ck(PV.parse_meeting_ref("p1|20260727-101500|A2") == ("p1", "20260727-101500"),
   "구 시그니처가 3세그먼트에서도 (pid, ts) 반환 ← 롤업 누락 방지의 핵심")
ck(PV.parse_meeting_ref("p1|20260727-101500") == ("p1", "20260727-101500"),
   "구 시그니처 · 레거시 참조 그대로")
ck(PV.parse_meeting_ref3("이상한값") == (None, None, ""), "회의 참조 아님")
ck(PV.parse_meeting_ref3("p1|nots|A2") == (None, None, ""), "ts 형식 위반 거부")
ck(PV.parse_meeting_ref3("p1|20260727-101500|xx9") == ("p1", "20260727-101500", ""),
   "알 수 없는 3번째 세그먼트는 무시하되 참조는 유효")

print("\n§4 deps_for — 문서함 조회")
with tempfile.TemporaryDirectory() as td:
    doc_dir = Path(td)
    (doc_dir / "p1").mkdir()
    (doc_dir / "p1" / "20260727-101500.json").write_text(
        json.dumps({"ts": "20260727-101500", "result": ENGINE_B}), encoding="utf-8")

    a_id = {"source": PV.SRC_MEETING, "source_ref": "p1|20260727-101500|A2",
            "task": "견적 3사 취합"}
    d = ML.deps_for(a_id, doc_dir, PV)
    ck(d and d["depends_on"] == ["도면 확정"], "액션ID로 조인")

    a_legacy = {"source": PV.SRC_MEETING, "source_ref": "p1|20260727-101500",
                "task": "견적 3사 취합"}
    d2 = ML.deps_for(a_legacy, doc_dir, PV)
    ck(d2 and d2["depends_on"] == ["도면 확정"], "레거시 참조 — 업무명 폴백으로 조인")

    a_renamed = {"source": PV.SRC_MEETING, "source_ref": "p1|20260727-101500",
                 "task": "견적 취합 (수정됨)"}
    ck(ML.deps_for(a_renamed, doc_dir, PV) is None,
       "업무명이 편집된 레거시 행은 조인 실패 → None (그래서 신규는 액션ID를 남긴다)")

    a_renamed_id = {"source": PV.SRC_MEETING, "source_ref": "p1|20260727-101500|A2",
                    "task": "견적 취합 (수정됨)"}
    ck(ML.deps_for(a_renamed_id, doc_dir, PV) is not None,
       "액션ID가 있으면 업무명 편집에도 조인 유지")

    ck(ML.deps_for({"source": "대표지시", "source_ref": ""}, doc_dir, PV) is None,
       "회의 출처가 아니면 None")
    ck(ML.deps_for({"source": PV.SRC_MEETING, "source_ref": "p9|20260101-000000|A1",
                    "task": "x"}, doc_dir, PV) is None,
       "문서 파일 없음 → None (예외 아님)")
    a_nodep = {"source": PV.SRC_MEETING, "source_ref": "p1|20260727-101500|A1",
               "task": "도면 확정"}
    ck(ML.deps_for(a_nodep, doc_dir, PV) is None, "선행·차단이 둘 다 없으면 None")

    cache = {}
    ML.deps_for(a_id, doc_dir, PV, cache)
    ML.deps_for(a_legacy, doc_dir, PV, cache)
    ck(len(cache) == 1, "같은 (pid, ts)는 캐시 1개 — 목록에서 파일 재읽기 없음")

print("\n§5 빈 입력·표시")
ck(ML.action_index({}) == {} and ML.action_index(None) == {}, "빈 result → {}")
ck(ML.load_result(None, "", "") == {}, "경로 없음 → {}")
ck(ML.deps_summary(None) == "", "None → 빈 문자열")
s = ML.deps_summary({"depends_on": ["가", "나", "다"], "blocking": []})
ck("외 1건" in s, f"선행 2건까지 표시 + 나머지 접기 ({s})")
s2 = ML.deps_summary(ib["A2"])
ck("선행" in s2 and "🚧" in s2, f"선행 + 차단 동시 표기 ({s2})")

print(f"\n{'─' * 52}")
if FAIL:
    print(f"실패 {len(FAIL)}/{N}")
    for f in FAIL:
        print(f"  · {f}")
    sys.exit(1)
print(f"전체 통과 {N}/{N}")
